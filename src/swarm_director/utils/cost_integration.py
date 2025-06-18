"""
Cost tracking integration patches for existing AI service calls
Provides monkey patching and integration hooks for automatic cost tracking
"""

import logging
import functools
from typing import Any, Dict, Optional
from flask import current_app

from .api_interceptor import api_interceptor
from .budget_manager import budget_manager
from ..models.cost_tracking import APIProvider

logger = logging.getLogger(__name__)


class CostTrackingIntegration:
    """Main integration class for cost tracking"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CostTrackingIntegration")
        self._patched = False
    
    def enable_cost_tracking(self):
        """Enable cost tracking for all AI service calls"""
        if self._patched:
            self.logger.info("Cost tracking already enabled")
            return
        
        try:
            # Patch OpenAI calls
            self._patch_openai()
            
            # Patch Anthropic calls
            self._patch_anthropic()
            
            # Enable API interceptor
            api_interceptor.enable()
            
            self._patched = True
            self.logger.info("Cost tracking enabled successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to enable cost tracking: {e}")
            raise
    
    def disable_cost_tracking(self):
        """Disable cost tracking"""
        try:
            api_interceptor.disable()
            self._patched = False
            self.logger.info("Cost tracking disabled")
        except Exception as e:
            self.logger.error(f"Failed to disable cost tracking: {e}")
    
    def _patch_openai(self):
        """Patch OpenAI API calls"""
        try:
            import openai
            
            # Store original methods
            if not hasattr(openai.OpenAI, '_original_create'):
                openai.OpenAI._original_create = openai.OpenAI.chat.completions.create
            
            # Patch chat completions
            def patched_chat_create(self, **kwargs):
                model = kwargs.get('model', 'unknown')
                
                with api_interceptor.track_api_call(
                    provider=APIProvider.OPENAI,
                    model=model,
                    agent_id=getattr(current_app, '_current_agent_id', None),
                    task_id=getattr(current_app, '_current_task_id', None),
                    conversation_id=getattr(current_app, '_current_conversation_id', None)
                ) as tracker:
                    
                    import time
                    start_time = time.time()
                    
                    try:
                        response = self._original_create(**kwargs)
                        
                        # Extract usage information
                        if hasattr(response, 'usage') and response.usage:
                            tracker.record_usage(
                                input_tokens=getattr(response.usage, 'prompt_tokens', 0),
                                output_tokens=getattr(response.usage, 'completion_tokens', 0),
                                total_tokens=getattr(response.usage, 'total_tokens', 0)
                            )
                        
                        tracker.record_success(int((time.time() - start_time) * 1000))
                        
                        # Update budgets
                        usage_record = tracker.save()
                        if usage_record:
                            budget_manager.update_budget_usage(usage_record)
                        
                        return response
                        
                    except Exception as e:
                        tracker.record_error(str(e))
                        raise
            
            # Apply patch
            openai.OpenAI.chat.completions.create = patched_chat_create
            
            self.logger.info("OpenAI API patched for cost tracking")
            
        except ImportError:
            self.logger.warning("OpenAI not available, skipping patch")
        except Exception as e:
            self.logger.error(f"Failed to patch OpenAI: {e}")
    
    def _patch_anthropic(self):
        """Patch Anthropic API calls"""
        try:
            import anthropic
            
            # Store original methods
            if not hasattr(anthropic.Anthropic, '_original_create'):
                anthropic.Anthropic._original_create = anthropic.Anthropic.messages.create
            
            # Patch message creation
            def patched_messages_create(self, **kwargs):
                model = kwargs.get('model', 'unknown')
                
                with api_interceptor.track_api_call(
                    provider=APIProvider.ANTHROPIC,
                    model=model,
                    agent_id=getattr(current_app, '_current_agent_id', None),
                    task_id=getattr(current_app, '_current_task_id', None),
                    conversation_id=getattr(current_app, '_current_conversation_id', None)
                ) as tracker:
                    
                    import time
                    start_time = time.time()
                    
                    try:
                        response = self._original_create(**kwargs)
                        
                        # Extract usage information
                        if hasattr(response, 'usage') and response.usage:
                            tracker.record_usage(
                                input_tokens=getattr(response.usage, 'input_tokens', 0),
                                output_tokens=getattr(response.usage, 'output_tokens', 0)
                            )
                        
                        tracker.record_success(int((time.time() - start_time) * 1000))
                        
                        # Update budgets
                        usage_record = tracker.save()
                        if usage_record:
                            budget_manager.update_budget_usage(usage_record)
                        
                        return response
                        
                    except Exception as e:
                        tracker.record_error(str(e))
                        raise
            
            # Apply patch
            anthropic.Anthropic.messages.create = patched_messages_create
            
            self.logger.info("Anthropic API patched for cost tracking")
            
        except ImportError:
            self.logger.warning("Anthropic not available, skipping patch")
        except Exception as e:
            self.logger.error(f"Failed to patch Anthropic: {e}")


def track_agent_context(agent_id: Optional[int] = None, task_id: Optional[int] = None, 
                       conversation_id: Optional[int] = None):
    """Decorator to set context for cost tracking"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Store context in current_app for access during API calls
            if current_app:
                current_app._current_agent_id = agent_id
                current_app._current_task_id = task_id
                current_app._current_conversation_id = conversation_id
            
            try:
                return func(*args, **kwargs)
            finally:
                # Clean up context
                if current_app:
                    current_app._current_agent_id = None
                    current_app._current_task_id = None
                    current_app._current_conversation_id = None
        
        return wrapper
    return decorator


def manual_track_api_call(
    provider: str,
    model: str,
    input_tokens: int,
    output_tokens: int,
    request_duration_ms: Optional[int] = None,
    agent_id: Optional[int] = None,
    task_id: Optional[int] = None,
    conversation_id: Optional[int] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Manually track an API call (for cases where automatic patching doesn't work)"""
    try:
        # Convert provider string to enum
        provider_enum = APIProvider(provider.lower())
        
        with api_interceptor.track_api_call(
            provider=provider_enum,
            model=model,
            agent_id=agent_id,
            task_id=task_id,
            conversation_id=conversation_id,
            metadata=metadata
        ) as tracker:
            
            tracker.record_usage(
                input_tokens=input_tokens,
                output_tokens=output_tokens
            )
            
            if request_duration_ms:
                tracker.record_success(request_duration_ms)
            else:
                tracker.record_success(0)  # Unknown duration
            
            # Update budgets
            usage_record = tracker.save()
            if usage_record:
                budget_manager.update_budget_usage(usage_record)
            
            return usage_record
            
    except Exception as e:
        logger.error(f"Failed to manually track API call: {e}")
        return None


def get_cost_tracking_status() -> Dict[str, Any]:
    """Get current cost tracking system status"""
    try:
        integration = CostTrackingIntegration()
        
        return {
            'enabled': integration._patched,
            'interceptor_enabled': api_interceptor._enabled,
            'supported_providers': [provider.value for provider in APIProvider],
            'status': 'operational' if integration._patched else 'disabled'
        }
        
    except Exception as e:
        logger.error(f"Failed to get cost tracking status: {e}")
        return {
            'enabled': False,
            'status': 'error',
            'error': str(e)
        }


# Global integration instance
cost_integration = CostTrackingIntegration()


def initialize_cost_tracking():
    """Initialize cost tracking system"""
    try:
        # Enable cost tracking
        cost_integration.enable_cost_tracking()
        
        logger.info("Cost tracking system initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize cost tracking: {e}")
        return False
