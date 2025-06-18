"""
API interceptor for tracking AI service usage and costs
Provides middleware to capture API calls and calculate costs in real-time
"""

import time
import uuid
import logging
import functools
from datetime import datetime
from typing import Dict, Any, Optional, Callable, Union
from contextlib import contextmanager
from flask import g, has_request_context

from ..models.base import db
from ..models.cost_tracking import APIUsage, APIProvider, UsageType
from .cost_calculator import cost_calculator
from .logging import get_correlation_id

logger = logging.getLogger(__name__)


class APIInterceptor:
    """Main API interceptor class for tracking usage and costs"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.APIInterceptor")
        self._enabled = True
    
    def enable(self):
        """Enable API interception"""
        self._enabled = True
        self.logger.info("API interception enabled")
    
    def disable(self):
        """Disable API interception"""
        self._enabled = False
        self.logger.info("API interception disabled")
    
    @contextmanager
    def track_api_call(
        self,
        provider: Union[str, APIProvider],
        model: str,
        usage_type: Union[str, UsageType] = UsageType.CHAT_COMPLETION,
        agent_id: Optional[int] = None,
        task_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """
        Context manager for tracking API calls
        
        Usage:
            with api_interceptor.track_api_call("openai", "gpt-4") as tracker:
                response = openai_client.chat.completions.create(...)
                tracker.record_usage(
                    input_tokens=response.usage.prompt_tokens,
                    output_tokens=response.usage.completion_tokens
                )
        """
        if not self._enabled:
            yield _DummyTracker()
            return
        
        # Convert string enums to enum objects
        if isinstance(provider, str):
            try:
                provider = APIProvider(provider.lower())
            except ValueError:
                self.logger.warning(f"Unknown provider: {provider}, using OPENAI as default")
                provider = APIProvider.OPENAI
        
        if isinstance(usage_type, str):
            try:
                usage_type = UsageType(usage_type.lower())
            except ValueError:
                self.logger.warning(f"Unknown usage type: {usage_type}, using CHAT_COMPLETION as default")
                usage_type = UsageType.CHAT_COMPLETION
        
        # Generate unique request ID
        request_id = str(uuid.uuid4())
        correlation_id = get_correlation_id() if has_request_context() else None
        
        # Create tracker
        tracker = _APICallTracker(
            request_id=request_id,
            correlation_id=correlation_id,
            provider=provider,
            model=model,
            usage_type=usage_type,
            agent_id=agent_id,
            task_id=task_id,
            conversation_id=conversation_id,
            metadata=metadata or {}
        )
        
        try:
            yield tracker
        except Exception as e:
            # Record the error
            tracker.record_error(str(e))
            raise
        finally:
            # Save the usage record
            tracker.save()
    
    def track_openai_call(self, original_func: Callable) -> Callable:
        """Decorator for OpenAI API calls"""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            # Extract model from kwargs or args
            model = kwargs.get('model') or (args[0] if args else 'unknown')
            
            with self.track_api_call(APIProvider.OPENAI, model) as tracker:
                start_time = time.time()
                try:
                    response = original_func(*args, **kwargs)
                    
                    # Extract usage information from response
                    if hasattr(response, 'usage') and response.usage:
                        tracker.record_usage(
                            input_tokens=getattr(response.usage, 'prompt_tokens', 0),
                            output_tokens=getattr(response.usage, 'completion_tokens', 0),
                            total_tokens=getattr(response.usage, 'total_tokens', 0)
                        )
                    
                    tracker.record_success(int((time.time() - start_time) * 1000))
                    return response
                    
                except Exception as e:
                    tracker.record_error(str(e))
                    raise
        
        return wrapper
    
    def track_anthropic_call(self, original_func: Callable) -> Callable:
        """Decorator for Anthropic API calls"""
        @functools.wraps(original_func)
        def wrapper(*args, **kwargs):
            # Extract model from kwargs
            model = kwargs.get('model', 'unknown')
            
            with self.track_api_call(APIProvider.ANTHROPIC, model) as tracker:
                start_time = time.time()
                try:
                    response = original_func(*args, **kwargs)
                    
                    # Extract usage information from response
                    if hasattr(response, 'usage') and response.usage:
                        tracker.record_usage(
                            input_tokens=getattr(response.usage, 'input_tokens', 0),
                            output_tokens=getattr(response.usage, 'output_tokens', 0)
                        )
                    
                    tracker.record_success(int((time.time() - start_time) * 1000))
                    return response
                    
                except Exception as e:
                    tracker.record_error(str(e))
                    raise
        
        return wrapper


class _APICallTracker:
    """Internal tracker for individual API calls"""
    
    def __init__(
        self,
        request_id: str,
        correlation_id: Optional[str],
        provider: APIProvider,
        model: str,
        usage_type: UsageType,
        agent_id: Optional[int] = None,
        task_id: Optional[int] = None,
        conversation_id: Optional[int] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        self.request_id = request_id
        self.correlation_id = correlation_id
        self.provider = provider
        self.model = model
        self.usage_type = usage_type
        self.agent_id = agent_id
        self.task_id = task_id
        self.conversation_id = conversation_id
        self.metadata = metadata or {}
        
        # Usage tracking
        self.input_tokens = 0
        self.output_tokens = 0
        self.total_tokens = 0
        
        # Status tracking
        self.request_duration_ms = None
        self.response_status = 'pending'
        self.error_message = None
        
        self.logger = logging.getLogger(f"{__name__}._APICallTracker")
    
    def record_usage(
        self,
        input_tokens: int = 0,
        output_tokens: int = 0,
        total_tokens: Optional[int] = None
    ):
        """Record token usage for the API call"""
        self.input_tokens = input_tokens
        self.output_tokens = output_tokens
        self.total_tokens = total_tokens or (input_tokens + output_tokens)
        
        self.logger.debug(
            f"Recorded usage for {self.request_id}: "
            f"input={input_tokens}, output={output_tokens}, total={self.total_tokens}"
        )
    
    def record_success(self, duration_ms: int):
        """Record successful API call"""
        self.request_duration_ms = duration_ms
        self.response_status = 'success'
        
        self.logger.debug(f"API call {self.request_id} completed successfully in {duration_ms}ms")
    
    def record_error(self, error_message: str):
        """Record failed API call"""
        self.response_status = 'error'
        self.error_message = error_message
        
        self.logger.warning(f"API call {self.request_id} failed: {error_message}")
    
    def save(self):
        """Save the usage record to database"""
        try:
            # Calculate costs
            input_cost, output_cost, total_cost, input_price, output_price = cost_calculator.calculate_cost(
                provider=self.provider,
                model=self.model,
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
                usage_type=self.usage_type
            )
            
            # Create usage record
            usage_record = APIUsage(
                request_id=self.request_id,
                correlation_id=self.correlation_id,
                provider=self.provider,
                model=self.model,
                usage_type=self.usage_type,
                input_tokens=self.input_tokens,
                output_tokens=self.output_tokens,
                total_tokens=self.total_tokens,
                input_cost=input_cost,
                output_cost=output_cost,
                total_cost=total_cost,
                input_price_per_token=input_price,
                output_price_per_token=output_price,
                request_duration_ms=self.request_duration_ms,
                response_status=self.response_status,
                error_message=self.error_message,
                agent_id=self.agent_id,
                task_id=self.task_id,
                conversation_id=self.conversation_id,
                metadata=self.metadata
            )
            
            # Save to database
            usage_record.save()
            
            self.logger.info(
                f"Saved API usage record {self.request_id}: "
                f"{self.provider.value}/{self.model} - "
                f"${float(total_cost):.6f} ({self.total_tokens} tokens)"
            )
            
            return usage_record
            
        except Exception as e:
            self.logger.error(f"Failed to save API usage record {self.request_id}: {e}")
            return None


class _DummyTracker:
    """Dummy tracker for when interception is disabled"""
    
    def record_usage(self, *args, **kwargs):
        pass
    
    def record_success(self, *args, **kwargs):
        pass
    
    def record_error(self, *args, **kwargs):
        pass
    
    def save(self):
        pass


# Global API interceptor instance
api_interceptor = APIInterceptor()
