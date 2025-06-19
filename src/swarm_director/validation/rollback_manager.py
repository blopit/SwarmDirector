"""
Rollback Manager

Handles validation failures and provides rollback procedures to restore
system state when validation fails at any tier.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime
from dataclasses import dataclass, field
import logging
import json
import asyncio

logger = logging.getLogger(__name__)


class RollbackAction(Enum):
    """Types of rollback actions"""
    REVERT_DATA = "revert_data"
    RESTORE_STATE = "restore_state"
    CANCEL_TASK = "cancel_task"
    NOTIFY_STAKEHOLDERS = "notify_stakeholders"
    CLEANUP_RESOURCES = "cleanup_resources"
    RESET_AGENT_STATE = "reset_agent_state"
    INVALIDATE_CACHE = "invalidate_cache"
    LOG_INCIDENT = "log_incident"


@dataclass
class RollbackStep:
    """Individual rollback step"""
    action: RollbackAction
    description: str
    handler: Callable[[Dict[str, Any]], bool]
    priority: int = 1  # Lower numbers execute first
    required: bool = True  # If false, failure doesn't stop rollback
    timeout_seconds: int = 30
    retry_count: int = 3
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RollbackPlan:
    """Complete rollback plan for a validation failure"""
    task_id: str
    failure_tier: str
    failure_reason: str
    steps: List[RollbackStep] = field(default_factory=list)
    created_at: datetime = field(default_factory=datetime.utcnow)
    executed_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    success: bool = False
    execution_log: List[str] = field(default_factory=list)


class RollbackManager:
    """
    Manages rollback procedures for validation failures
    """
    
    def __init__(self):
        self.rollback_handlers: Dict[RollbackAction, Callable] = {}
        self.rollback_history: List[RollbackPlan] = []
        self.default_handlers_registered = False
        
        # Register default rollback handlers
        self._register_default_handlers()
    
    def _register_default_handlers(self):
        """Register default rollback handlers"""
        if self.default_handlers_registered:
            return
        
        self.register_handler(RollbackAction.REVERT_DATA, self._revert_data_handler)
        self.register_handler(RollbackAction.RESTORE_STATE, self._restore_state_handler)
        self.register_handler(RollbackAction.CANCEL_TASK, self._cancel_task_handler)
        self.register_handler(RollbackAction.NOTIFY_STAKEHOLDERS, self._notify_stakeholders_handler)
        self.register_handler(RollbackAction.CLEANUP_RESOURCES, self._cleanup_resources_handler)
        self.register_handler(RollbackAction.RESET_AGENT_STATE, self._reset_agent_state_handler)
        self.register_handler(RollbackAction.INVALIDATE_CACHE, self._invalidate_cache_handler)
        self.register_handler(RollbackAction.LOG_INCIDENT, self._log_incident_handler)
        
        self.default_handlers_registered = True
    
    def register_handler(self, action: RollbackAction, handler: Callable[[Dict[str, Any]], bool]):
        """Register a custom rollback handler"""
        self.rollback_handlers[action] = handler
        logger.info(f"Registered rollback handler for action: {action.value}")
    
    def create_rollback_plan(self, task_id: str, failure_tier: str, 
                             failure_reason: str, validation_result=None) -> RollbackPlan:
        """Create a rollback plan based on failure context"""
        plan = RollbackPlan(
            task_id=task_id,
            failure_tier=failure_tier,
            failure_reason=failure_reason
        )
        
        # Add steps based on failure tier and context
        if failure_tier == "tool":
            plan.steps.extend(self._create_tool_rollback_steps(validation_result))
        elif failure_tier == "department":
            plan.steps.extend(self._create_department_rollback_steps(validation_result))
        elif failure_tier == "director":
            plan.steps.extend(self._create_director_rollback_steps(validation_result))
        
        # Add common rollback steps
        plan.steps.extend(self._create_common_rollback_steps(validation_result))
        
        # Sort steps by priority
        plan.steps.sort(key=lambda x: x.priority)
        
        logger.info(f"Created rollback plan for task {task_id} with {len(plan.steps)} steps")
        return plan
    
    def _create_tool_rollback_steps(self, validation_result) -> List[RollbackStep]:
        """Create rollback steps for tool-level failures"""
        steps = [
            RollbackStep(
                action=RollbackAction.RESET_AGENT_STATE,
                description="Reset tool agent state",
                handler=self.rollback_handlers[RollbackAction.RESET_AGENT_STATE],
                priority=1,
                context={'agent_type': 'tool'}
            ),
            RollbackStep(
                action=RollbackAction.REVERT_DATA,
                description="Revert tool output data",
                handler=self.rollback_handlers[RollbackAction.REVERT_DATA],
                priority=2,
                context={'data_type': 'tool_output'}
            )
        ]
        return steps
    
    def _create_department_rollback_steps(self, validation_result) -> List[RollbackStep]:
        """Create rollback steps for department-level failures"""
        steps = [
            RollbackStep(
                action=RollbackAction.RESET_AGENT_STATE,
                description="Reset department agent state",
                handler=self.rollback_handlers[RollbackAction.RESET_AGENT_STATE],
                priority=1,
                context={'agent_type': 'department'}
            ),
            RollbackStep(
                action=RollbackAction.REVERT_DATA,
                description="Revert department output data",
                handler=self.rollback_handlers[RollbackAction.REVERT_DATA],
                priority=2,
                context={'data_type': 'department_output'}
            ),
            RollbackStep(
                action=RollbackAction.INVALIDATE_CACHE,
                description="Invalidate department cache",
                handler=self.rollback_handlers[RollbackAction.INVALIDATE_CACHE],
                priority=3,
                required=False,
                context={'cache_type': 'department'}
            )
        ]
        return steps
    
    def _create_director_rollback_steps(self, validation_result) -> List[RollbackStep]:
        """Create rollback steps for director-level failures"""
        steps = [
            RollbackStep(
                action=RollbackAction.CANCEL_TASK,
                description="Cancel task due to director validation failure",
                handler=self.rollback_handlers[RollbackAction.CANCEL_TASK],
                priority=1,
                context={'cancellation_reason': 'director_validation_failure'}
            ),
            RollbackStep(
                action=RollbackAction.NOTIFY_STAKEHOLDERS,
                description="Notify stakeholders of task failure",
                handler=self.rollback_handlers[RollbackAction.NOTIFY_STAKEHOLDERS],
                priority=2,
                required=False,
                context={'notification_type': 'task_failure'}
            ),
            RollbackStep(
                action=RollbackAction.RESTORE_STATE,
                description="Restore system state",
                handler=self.rollback_handlers[RollbackAction.RESTORE_STATE],
                priority=3,
                context={'state_type': 'system'}
            )
        ]
        return steps
    
    def _create_common_rollback_steps(self, validation_result) -> List[RollbackStep]:
        """Create common rollback steps for all failure types"""
        steps = [
            RollbackStep(
                action=RollbackAction.LOG_INCIDENT,
                description="Log validation failure incident",
                handler=self.rollback_handlers[RollbackAction.LOG_INCIDENT],
                priority=10,
                required=False,
                context={'incident_type': 'validation_failure'}
            ),
            RollbackStep(
                action=RollbackAction.CLEANUP_RESOURCES,
                description="Clean up allocated resources",
                handler=self.rollback_handlers[RollbackAction.CLEANUP_RESOURCES],
                priority=11,
                required=False,
                context={'cleanup_type': 'validation_failure'}
            )
        ]
        return steps
    
    async def execute_rollback(self, task_id: str, reason: str, validation_result=None) -> bool:
        """Execute rollback procedure"""
        logger.info(f"Starting rollback for task {task_id}: {reason}")
        
        # Determine failure tier from validation result
        failure_tier = "unknown"
        if validation_result:
            failure_tier = validation_result.tier
        
        # Create rollback plan
        plan = self.create_rollback_plan(task_id, failure_tier, reason, validation_result)
        plan.executed_at = datetime.utcnow()
        
        success = True
        
        try:
            for step in plan.steps:
                step_success = await self._execute_rollback_step(step, plan)
                
                if not step_success and step.required:
                    success = False
                    plan.execution_log.append(f"FAILED (required): {step.description}")
                    logger.error(f"Required rollback step failed: {step.description}")
                    break
                elif not step_success:
                    plan.execution_log.append(f"FAILED (optional): {step.description}")
                    logger.warning(f"Optional rollback step failed: {step.description}")
                else:
                    plan.execution_log.append(f"SUCCESS: {step.description}")
                    logger.info(f"Rollback step completed: {step.description}")
            
            plan.success = success
            plan.completed_at = datetime.utcnow()
            
            # Store in history
            self.rollback_history.append(plan)
            
            if success:
                logger.info(f"Rollback completed successfully for task {task_id}")
            else:
                logger.error(f"Rollback failed for task {task_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error during rollback execution for task {task_id}: {e}", exc_info=True)
            plan.success = False
            plan.completed_at = datetime.utcnow()
            plan.execution_log.append(f"SYSTEM ERROR: {str(e)}")
            self.rollback_history.append(plan)
            return False
    
    async def _execute_rollback_step(self, step: RollbackStep, plan: RollbackPlan) -> bool:
        """Execute a single rollback step with retry logic"""
        for attempt in range(step.retry_count):
            try:
                # Execute with timeout
                result = await asyncio.wait_for(
                    asyncio.get_event_loop().run_in_executor(
                        None, step.handler, step.context
                    ),
                    timeout=step.timeout_seconds
                )
                
                if result:
                    return True
                else:
                    logger.warning(f"Rollback step returned False: {step.description} (attempt {attempt + 1})")
                    
            except asyncio.TimeoutError:
                logger.warning(f"Rollback step timed out: {step.description} (attempt {attempt + 1})")
            except Exception as e:
                logger.error(f"Error in rollback step: {step.description} (attempt {attempt + 1}): {e}")
            
            # Wait before retry (exponential backoff)
            if attempt < step.retry_count - 1:
                await asyncio.sleep(2 ** attempt)
        
        return False
    
    # Default rollback handlers
    def _revert_data_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for reverting data"""
        try:
            data_type = context.get('data_type', 'unknown')
            logger.info(f"Reverting data of type: {data_type}")
            # Implementation would depend on data storage system
            return True
        except Exception as e:
            logger.error(f"Error reverting data: {e}")
            return False
    
    def _restore_state_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for restoring state"""
        try:
            state_type = context.get('state_type', 'unknown')
            logger.info(f"Restoring state of type: {state_type}")
            # Implementation would depend on state management system
            return True
        except Exception as e:
            logger.error(f"Error restoring state: {e}")
            return False
    
    def _cancel_task_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for canceling tasks"""
        try:
            reason = context.get('cancellation_reason', 'validation_failure')
            logger.info(f"Canceling task due to: {reason}")
            # Implementation would update task status in database
            return True
        except Exception as e:
            logger.error(f"Error canceling task: {e}")
            return False
    
    def _notify_stakeholders_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for notifying stakeholders"""
        try:
            notification_type = context.get('notification_type', 'general')
            logger.info(f"Sending notification of type: {notification_type}")
            # Implementation would send notifications via email, webhook, etc.
            return True
        except Exception as e:
            logger.error(f"Error sending notifications: {e}")
            return False
    
    def _cleanup_resources_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for cleaning up resources"""
        try:
            cleanup_type = context.get('cleanup_type', 'general')
            logger.info(f"Cleaning up resources of type: {cleanup_type}")
            # Implementation would clean up temporary files, connections, etc.
            return True
        except Exception as e:
            logger.error(f"Error cleaning up resources: {e}")
            return False
    
    def _reset_agent_state_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for resetting agent state"""
        try:
            agent_type = context.get('agent_type', 'unknown')
            logger.info(f"Resetting agent state for type: {agent_type}")
            # Implementation would reset agent state in database/memory
            return True
        except Exception as e:
            logger.error(f"Error resetting agent state: {e}")
            return False
    
    def _invalidate_cache_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for invalidating cache"""
        try:
            cache_type = context.get('cache_type', 'general')
            logger.info(f"Invalidating cache of type: {cache_type}")
            # Implementation would clear relevant caches
            return True
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")
            return False
    
    def _log_incident_handler(self, context: Dict[str, Any]) -> bool:
        """Default handler for logging incidents"""
        try:
            incident_type = context.get('incident_type', 'general')
            logger.info(f"Logging incident of type: {incident_type}")
            # Implementation would log to incident management system
            return True
        except Exception as e:
            logger.error(f"Error logging incident: {e}")
            return False
    
    def get_rollback_history(self, task_id: Optional[str] = None) -> List[RollbackPlan]:
        """Get rollback history with optional filtering"""
        if task_id:
            return [plan for plan in self.rollback_history if plan.task_id == task_id]
        return self.rollback_history
    
    def get_rollback_statistics(self) -> Dict[str, Any]:
        """Get rollback statistics"""
        total = len(self.rollback_history)
        successful = len([plan for plan in self.rollback_history if plan.success])
        
        return {
            'total_rollbacks': total,
            'successful_rollbacks': successful,
            'success_rate': successful / total if total > 0 else 0.0,
            'by_tier': {
                tier: len([plan for plan in self.rollback_history if plan.failure_tier == tier])
                for tier in ['tool', 'department', 'director', 'unknown']
            }
        }
