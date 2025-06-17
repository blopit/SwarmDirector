"""
Enhanced Email Workflow Coordinator
Integrates error recovery service with email workflow coordination
"""

import logging
import time
import asyncio
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps

from .email_workflow_coordinator import EmailWorkflowCoordinator
from .error_recovery_service import (
    error_recovery_service, ErrorType, ErrorSeverity, RecoveryAction,
    CircuitBreakerConfig, RetryStrategy
)
from .email_workflow_states import EmailWorkflowType, EmailWorkflowPhase
from .state_manager import WorkflowStatus
from ..models.task import Task

logger = logging.getLogger(__name__)

def with_error_recovery(phase_name: str = None, service_name: str = None):
    """Decorator to add error recovery to workflow methods"""
    def decorator(func: Callable):
        @wraps(func)
        def wrapper(self, *args, **kwargs):
            # Extract workflow_id from args if available
            workflow_id = None
            if args and isinstance(args[0], str):
                workflow_id = args[0]
            elif hasattr(self, '_current_workflow_id'):
                workflow_id = self._current_workflow_id
            
            service = service_name or func.__name__
            
            # Apply circuit breaker protection if service specified
            if service_name:
                try:
                    with error_recovery_service.circuit_breaker_protection(service):
                        return self._execute_with_recovery(
                            func, workflow_id, phase_name, service, *args, **kwargs
                        )
                except Exception as e:
                    logger.error(f"Circuit breaker protection failed for {service}: {e}")
                    # Fall back to normal execution with recovery
                    return self._execute_with_recovery(
                        func, workflow_id, phase_name, service, *args, **kwargs
                    )
            else:
                return self._execute_with_recovery(
                    func, workflow_id, phase_name, service, *args, **kwargs
                )
        
        return wrapper
    return decorator

class EnhancedEmailWorkflowCoordinator(EmailWorkflowCoordinator):
    """
    Enhanced email workflow coordinator with comprehensive error recovery
    """
    
    def __init__(self, director_agent=None):
        super().__init__(director_agent)
        self.error_recovery = error_recovery_service
        self._current_workflow_id = None
        self._fallback_handlers = {}
        self._recovery_callbacks = {}
        
        # Configure circuit breakers for different services
        self._setup_circuit_breakers()
        
        # Configure custom retry strategies
        self._setup_custom_retry_strategies()
        
        logger.info("Enhanced Email Workflow Coordinator initialized with error recovery")
    
    def _setup_circuit_breakers(self):
        """Setup circuit breakers for different services"""
        # AI Agent services
        agent_config = CircuitBreakerConfig(
            failure_threshold=3,
            recovery_timeout=120.0,
            half_open_max_calls=2,
            success_threshold=1
        )
        
        self.error_recovery.get_circuit_breaker("director_agent", agent_config)
        self.error_recovery.get_circuit_breaker("communications_dept", agent_config)
        self.error_recovery.get_circuit_breaker("email_agent", agent_config)
        self.error_recovery.get_circuit_breaker("review_agents", agent_config)
        
        # Database services
        db_config = CircuitBreakerConfig(
            failure_threshold=5,
            recovery_timeout=60.0,
            half_open_max_calls=3,
            success_threshold=2
        )
        self.error_recovery.get_circuit_breaker("database", db_config)
        
        # SMTP service
        smtp_config = CircuitBreakerConfig(
            failure_threshold=2,
            recovery_timeout=300.0,  # 5 minutes for SMTP recovery
            half_open_max_calls=1,
            success_threshold=1
        )
        self.error_recovery.get_circuit_breaker("smtp_service", smtp_config)
    
    def _setup_custom_retry_strategies(self):
        """Setup custom retry strategies for workflow-specific errors"""
        # Custom strategy for email delivery
        self.error_recovery.retry_strategies[ErrorType.SMTP_ERROR] = RetryStrategy(
            max_attempts=3,
            base_delay=10.0,
            max_delay=300.0,
            exponential_backoff=True,
            jitter=True
        )
        
        # Custom strategy for agent failures
        self.error_recovery.retry_strategies[ErrorType.AGENT_FAILURE] = RetryStrategy(
            max_attempts=2,
            base_delay=5.0,
            max_delay=60.0,
            exponential_backoff=True,
            jitter=True
        )
    
    def _execute_with_recovery(self, func: Callable, workflow_id: str, 
                             phase_name: str, service_name: str, *args, **kwargs):
        """Execute a function with comprehensive error recovery"""
        max_recovery_attempts = 3
        recovery_attempt = 0
        
        while recovery_attempt <= max_recovery_attempts:
            try:
                result = func(self, *args, **kwargs)
                
                # If we had previous failures and now succeeded, log recovery
                if recovery_attempt > 0:
                    logger.info(f"Function {func.__name__} recovered after {recovery_attempt} attempts")
                
                return result
                
            except Exception as e:
                recovery_attempt += 1
                
                # Record the error
                context = {
                    'phase': phase_name,
                    'service': service_name,
                    'function': func.__name__,
                    'attempt': recovery_attempt,
                    'args': str(args)[:200],  # Truncate for logging
                }
                
                error_record = self.error_recovery.record_error(
                    workflow_id or 'unknown',
                    e,
                    context
                )
                
                # Attempt recovery
                recovery_result = self.error_recovery.attempt_recovery(error_record)
                
                if recovery_result.action_taken == RecoveryAction.RETRY:
                    if recovery_attempt <= max_recovery_attempts:
                        retry_delay = recovery_result.retry_after or 1.0
                        logger.info(f"Retrying {func.__name__} in {retry_delay:.1f}s (attempt {recovery_attempt})")
                        time.sleep(retry_delay)
                        continue
                
                elif recovery_result.action_taken == RecoveryAction.FALLBACK:
                    fallback_result = self._attempt_fallback(func.__name__, workflow_id, *args, **kwargs)
                    if fallback_result is not None:
                        logger.info(f"Fallback successful for {func.__name__}")
                        return fallback_result
                
                elif recovery_result.action_taken == RecoveryAction.ROLLBACK:
                    self._attempt_rollback(workflow_id, phase_name)
                    logger.info(f"Rollback initiated for workflow {workflow_id}")
                
                # If we've exhausted recovery attempts, re-raise the exception
                if recovery_attempt > max_recovery_attempts:
                    logger.error(f"All recovery attempts exhausted for {func.__name__}")
                    raise
        
        # Should not reach here, but if it does, raise the last exception
        raise Exception(f"Function {func.__name__} failed after all recovery attempts")
    
    def _attempt_fallback(self, function_name: str, workflow_id: str, *args, **kwargs):
        """Attempt fallback mechanism for failed functions"""
        fallback_handler = self._fallback_handlers.get(function_name)
        if fallback_handler:
            try:
                logger.info(f"Executing fallback handler for {function_name}")
                return fallback_handler(workflow_id, *args, **kwargs)
            except Exception as e:
                logger.error(f"Fallback handler failed for {function_name}: {e}")
        
        # Default fallback strategies
        if 'delivery' in function_name.lower():
            return self._fallback_email_delivery(workflow_id)
        elif 'review' in function_name.lower():
            return self._fallback_review_process(workflow_id)
        elif 'draft' in function_name.lower():
            return self._fallback_draft_creation(workflow_id)
        
        return None
    
    def _fallback_email_delivery(self, workflow_id: str) -> Dict[str, Any]:
        """Fallback for email delivery failures"""
        logger.warning(f"Using email delivery fallback for workflow {workflow_id}")
        
        # Mark as queued for later retry
        workflow_state = self.state_manager.get_email_workflow(workflow_id)
        if workflow_state:
            workflow_state.update_delivery_status(
                workflow_state.email_context.delivery_status.__class__.QUEUED
            )
        
        return {
            'success': True,
            'phase': 'delivery_fallback',
            'message': 'Email queued for retry',
            'fallback_mode': True
        }
    
    def _fallback_review_process(self, workflow_id: str) -> Dict[str, Any]:
        """Fallback for review process failures"""
        logger.warning(f"Using review process fallback for workflow {workflow_id}")
        
        # Skip review and proceed to finalization
        return {
            'success': True,
            'phase': 'review_skipped',
            'message': 'Review process skipped due to failures',
            'fallback_mode': True,
            'reviews_completed': True
        }
    
    def _fallback_draft_creation(self, workflow_id: str) -> Dict[str, Any]:
        """Fallback for draft creation failures"""
        logger.warning(f"Using draft creation fallback for workflow {workflow_id}")
        
        # Create basic draft
        workflow_state = self.state_manager.get_email_workflow(workflow_id)
        if workflow_state:
            basic_content = f"Email regarding: {workflow_state.email_context.subject}"
            workflow_state.email_context.body = basic_content
        
        return {
            'success': True,
            'phase': 'draft_fallback',
            'message': 'Basic draft created as fallback',
            'fallback_mode': True
        }
    
    def _attempt_rollback(self, workflow_id: str, current_phase: str):
        """Attempt to rollback workflow to previous safe state"""
        try:
            workflow_state = self.state_manager.get_email_workflow(workflow_id)
            if not workflow_state:
                logger.error(f"Cannot rollback - workflow state not found: {workflow_id}")
                return
            
            # Find previous safe phase
            phase_history = getattr(workflow_state, 'phase_history', [])
            if len(phase_history) < 2:
                logger.warning(f"Cannot rollback - insufficient phase history for workflow {workflow_id}")
                return
            
            # Get previous phase
            previous_phase = phase_history[-2]
            logger.info(f"Rolling back workflow {workflow_id} from {current_phase} to {previous_phase}")
            
            # Reset to previous phase
            self.state_manager.advance_workflow_phase(
                workflow_id,
                EmailWorkflowPhase(previous_phase),
                agent_name="ErrorRecoverySystem",
                notes=f"Rollback from failed phase: {current_phase}"
            )
            
        except Exception as e:
            logger.error(f"Rollback failed for workflow {workflow_id}: {e}")
    
    def register_fallback_handler(self, function_name: str, handler: Callable):
        """Register a custom fallback handler for a function"""
        self._fallback_handlers[function_name] = handler
        logger.info(f"Registered fallback handler for {function_name}")
    
    def register_recovery_callback(self, error_type: ErrorType, callback: Callable):
        """Register a callback for specific error types"""
        self._recovery_callbacks[error_type] = callback
        logger.info(f"Registered recovery callback for {error_type}")
    
    # Override methods with error recovery
    @with_error_recovery(phase_name="intent_classification", service_name="director_agent")
    def _phase_1_intent_classification(self, workflow_id: str, task: Task, workflow_type: EmailWorkflowType):
        self._current_workflow_id = workflow_id
        return super()._phase_1_intent_classification(workflow_id, task, workflow_type)
    
    @with_error_recovery(phase_name="draft_creation", service_name="communications_dept")
    def _phase_2_draft_creation(self, workflow_id: str, task: Task):
        self._current_workflow_id = workflow_id
        return super()._phase_2_draft_creation(workflow_id, task)
    
    @with_error_recovery(phase_name="review_process", service_name="review_agents")
    def _phase_3_4_review_process(self, workflow_id: str):
        self._current_workflow_id = workflow_id
        return super()._phase_3_4_review_process(workflow_id)
    
    @with_error_recovery(phase_name="finalization")
    def _phase_5_finalization(self, workflow_id: str):
        self._current_workflow_id = workflow_id
        return super()._phase_5_finalization(workflow_id)
    
    @with_error_recovery(phase_name="delivery", service_name="smtp_service")
    def _phase_6_7_delivery(self, workflow_id: str):
        self._current_workflow_id = workflow_id
        return super()._phase_6_7_delivery(workflow_id)
    
    @with_error_recovery(phase_name="delivery_confirmation")
    def _phase_8_delivery_confirmation(self, workflow_id: str):
        self._current_workflow_id = workflow_id
        return super()._phase_8_delivery_confirmation(workflow_id)
    
    def get_error_recovery_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error recovery statistics"""
        base_stats = self.get_workflow_statistics()
        error_stats = self.error_recovery.get_error_statistics()
        
        return {
            'workflow_statistics': base_stats,
            'error_recovery_statistics': error_stats,
            'fallback_handlers': list(self._fallback_handlers.keys()),
            'recovery_callbacks': list(self._recovery_callbacks.keys()),
            'circuit_breaker_status': {
                name: {
                    'state': cb.state.value,
                    'failure_count': cb.failure_count,
                    'success_count': cb.success_count
                }
                for name, cb in self.error_recovery.circuit_breakers.items()
            }
        }
    
    def retry_failed_workflows(self) -> Dict[str, Any]:
        """Retry workflows from dead letter queue"""
        retry_eligible = self.error_recovery.dead_letter_queue.get_retry_eligible_workflows()
        results = {
            'total_eligible': len(retry_eligible),
            'retry_attempts': [],
            'successes': 0,
            'failures': 0
        }
        
        for workflow_item in retry_eligible:
            workflow_id = workflow_item['workflow_id']
            error_record = workflow_item['error_record']
            
            try:
                # Mark as retried
                self.error_recovery.dead_letter_queue.mark_workflow_retried(workflow_id)
                
                # Attempt to restart workflow from last safe state
                workflow_state = self.state_manager.get_email_workflow(workflow_id)
                if workflow_state:
                    # Reset status to pending and try again
                    self.state_manager.update_workflow_status(
                        workflow_id, WorkflowStatus.PENDING,
                        agent_name="ErrorRecoverySystem",
                        reason="Retry from dead letter queue"
                    )
                    
                    results['retry_attempts'].append({
                        'workflow_id': workflow_id,
                        'status': 'retry_scheduled',
                        'original_error': error_record.message
                    })
                    results['successes'] += 1
                    
                    logger.info(f"Scheduled retry for workflow {workflow_id}")
                else:
                    results['retry_attempts'].append({
                        'workflow_id': workflow_id,
                        'status': 'failed_no_state',
                        'error': 'Workflow state not found'
                    })
                    results['failures'] += 1
                    
            except Exception as e:
                results['retry_attempts'].append({
                    'workflow_id': workflow_id,
                    'status': 'retry_failed',
                    'error': str(e)
                })
                results['failures'] += 1
                logger.error(f"Failed to retry workflow {workflow_id}: {e}")
        
        return results
    
    def force_circuit_breaker_reset(self, service_name: str) -> bool:
        """Force reset a circuit breaker"""
        if service_name in self.error_recovery.circuit_breakers:
            cb = self.error_recovery.circuit_breakers[service_name]
            cb.state = cb.state.__class__.CLOSED
            cb.failure_count = 0
            cb.last_failure_time = None
            cb.success_count = 0
            logger.info(f"Force reset circuit breaker for {service_name}")
            return True
        return False