"""
SwarmDirector Automation Integration Utilities

This module provides the core automation integration layer for SwarmDirector's
enhanced task management system. It handles workflow processes, automation hooks,
and integration with CI/CD pipelines.
"""

from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from enum import Enum
import logging
import json
import asyncio
from pathlib import Path

from ..models.task import Task, TaskType, TaskStatus, TaskPriority
from ..utils.database import db
from ..utils.logging import get_logger

logger = get_logger(__name__)


class AutomationEventType(Enum):
    """Types of automation events that can trigger workflows."""
    TASK_CREATED = "task_created"
    TASK_STATUS_CHANGED = "task_status_changed"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    DEPLOYMENT_STARTED = "deployment_started"
    DEPLOYMENT_COMPLETED = "deployment_completed"
    DEPLOYMENT_FAILED = "deployment_failed"
    WORKFLOW_TRIGGERED = "workflow_triggered"
    SCHEDULE_TRIGGERED = "schedule_triggered"
    ALERT_TRIGGERED = "alert_triggered"


class WorkflowStatus(Enum):
    """Workflow execution status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class AutomationIntegrator:
    """
    Core automation integration layer for SwarmDirector.
    
    This class provides the main interface for integrating automation workflows
    with the enhanced task management system, handling event triggers, webhook
    processing, and workflow orchestration.
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the automation integrator."""
        self.config = config or {}
        self.webhook_handlers: Dict[str, List[Callable]] = {}
        self.workflow_registry: Dict[str, Dict] = {}
        self.active_workflows: Dict[str, Dict] = {}
        self.event_history: List[Dict] = []
        
        # Configuration defaults
        self.max_retry_attempts = self.config.get('max_retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 5)  # seconds
        self.webhook_timeout = self.config.get('webhook_timeout', 30)  # seconds
        self.max_concurrent_workflows = self.config.get('max_concurrent_workflows', 10)
        
        logger.info("AutomationIntegrator initialized with config: %s", self.config)
    
    def register_workflow_hook(self, event_type: AutomationEventType, handler_func: Callable):
        """
        Register a workflow hook for specific automation events.
        
        Args:
            event_type: The type of event to listen for
            handler_func: Function to call when event occurs
        """
        event_key = event_type.value
        if event_key not in self.webhook_handlers:
            self.webhook_handlers[event_key] = []
        
        self.webhook_handlers[event_key].append(handler_func)
        logger.info("Registered webhook handler for event: %s", event_key)
    
    def unregister_workflow_hook(self, event_type: AutomationEventType, handler_func: Callable):
        """Unregister a workflow hook."""
        event_key = event_type.value
        if event_key in self.webhook_handlers:
            try:
                self.webhook_handlers[event_key].remove(handler_func)
                logger.info("Unregistered webhook handler for event: %s", event_key)
            except ValueError:
                logger.warning("Handler not found for event: %s", event_key)
    
    async def trigger_automation(self, event_type: AutomationEventType, payload: Dict) -> List[Dict]:
        """
        Trigger automation workflows based on task events.
        
        Args:
            event_type: The type of event that occurred
            payload: Event data and context
            
        Returns:
            List of handler execution results
        """
        event_key = event_type.value
        handlers = self.webhook_handlers.get(event_key, [])
        results = []
        
        # Record event in history
        event_record = {
            'event_type': event_key,
            'payload': payload,
            'timestamp': datetime.utcnow().isoformat(),
            'handler_count': len(handlers)
        }
        self.event_history.append(event_record)
        
        # Limit event history size
        if len(self.event_history) > 1000:
            self.event_history = self.event_history[-1000:]
        
        logger.info("Triggering automation for event: %s with %d handlers", event_key, len(handlers))
        
        for handler in handlers:
            handler_name = getattr(handler, '__name__', str(handler))
            
            try:
                # Execute handler with timeout
                if asyncio.iscoroutinefunction(handler):
                    result = await asyncio.wait_for(
                        handler(payload), 
                        timeout=self.webhook_timeout
                    )
                else:
                    result = handler(payload)
                
                result_record = {
                    'handler': handler_name,
                    'status': 'success',
                    'result': result,
                    'timestamp': datetime.utcnow().isoformat(),
                    'execution_time': None  # Could add timing if needed
                }
                results.append(result_record)
                
                logger.info("Handler %s executed successfully for event %s", handler_name, event_key)
                
            except asyncio.TimeoutError:
                error_msg = f"Handler {handler_name} timed out after {self.webhook_timeout}s"
                logger.error(error_msg)
                results.append({
                    'handler': handler_name,
                    'status': 'timeout',
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat()
                })
                
            except Exception as e:
                error_msg = f"Handler {handler_name} failed: {str(e)}"
                logger.error(error_msg, exc_info=True)
                results.append({
                    'handler': handler_name,
                    'status': 'error',
                    'error': error_msg,
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return results
    
    def sync_task_status(self, task_id: int, status: TaskStatus, metadata: Optional[Dict] = None) -> Dict:
        """
        Synchronize task status with external automation systems.
        
        Args:
            task_id: ID of the task to update
            status: New task status
            metadata: Additional metadata for the status update
            
        Returns:
            Synchronization result
        """
        try:
            # Get the task
            task = Task.query.get(task_id)
            if not task:
                raise ValueError(f"Task {task_id} not found")
            
            old_status = task.status
            task.status = status
            task.last_activity = datetime.utcnow()
            
            # Add metadata if provided
            if metadata:
                if not task.metadata:
                    task.metadata = {}
                task.metadata.update(metadata)
            
            db.session.commit()
            
            # Create sync payload
            sync_payload = {
                'task_id': task_id,
                'old_status': old_status.value if old_status else None,
                'new_status': status.value,
                'timestamp': datetime.utcnow().isoformat(),
                'metadata': metadata or {}
            }
            
            # Trigger status sync automation asynchronously
            asyncio.create_task(
                self.trigger_automation(AutomationEventType.TASK_STATUS_CHANGED, sync_payload)
            )
            
            logger.info("Task %d status updated from %s to %s", task_id, old_status, status)
            
            return {
                'status': 'success',
                'task_id': task_id,
                'old_status': old_status.value if old_status else None,
                'new_status': status.value,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error("Failed to sync task status for task %d: %s", task_id, str(e))
            return {
                'status': 'error',
                'task_id': task_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def create_automation_task(self, workflow_name: str, parameters: Dict, **kwargs) -> Task:
        """
        Create a task from an automation workflow.
        
        Args:
            workflow_name: Name of the workflow triggering the task
            parameters: Workflow parameters and context
            **kwargs: Additional task attributes
            
        Returns:
            Created task instance
        """
        try:
            # Create task with automation defaults
            task = Task(
                title=kwargs.get('title', f"Automation: {workflow_name}"),
                description=kwargs.get('description', f"Automated task created by workflow: {workflow_name}"),
                type=kwargs.get('type', TaskType.AUTOMATION),
                status=kwargs.get('status', TaskStatus.PENDING),
                priority=kwargs.get('priority', TaskPriority.MEDIUM),
                user_id=kwargs.get('user_id', "automation_system"),
                metadata={
                    'workflow_name': workflow_name,
                    'automation_parameters': parameters,
                    'created_by_automation': True,
                    'automation_timestamp': datetime.utcnow().isoformat()
                }
            )
            
            # Add any additional metadata
            if 'metadata' in kwargs:
                task.metadata.update(kwargs['metadata'])
            
            db.session.add(task)
            db.session.commit()
            
            # Trigger task creation hooks asynchronously
            creation_payload = {
                'task_id': task.id,
                'workflow_name': workflow_name,
                'parameters': parameters,
                'task_data': {
                    'title': task.title,
                    'description': task.description,
                    'type': task.type.value,
                    'status': task.status.value,
                    'priority': task.priority.value
                }
            }
            
            asyncio.create_task(
                self.trigger_automation(AutomationEventType.TASK_CREATED, creation_payload)
            )
            
            logger.info("Created automation task %d for workflow: %s", task.id, workflow_name)
            return task
            
        except Exception as e:
            logger.error("Failed to create automation task for workflow %s: %s", workflow_name, str(e))
            raise
    
    def register_workflow(self, workflow_name: str, workflow_config: Dict):
        """
        Register a workflow configuration.
        
        Args:
            workflow_name: Unique name for the workflow
            workflow_config: Workflow configuration and metadata
        """
        self.workflow_registry[workflow_name] = {
            **workflow_config,
            'registered_at': datetime.utcnow().isoformat(),
            'execution_count': 0,
            'last_execution': None
        }
        
        logger.info("Registered workflow: %s", workflow_name)
    
    def execute_workflow(self, workflow_name: str, context: Dict) -> str:
        """
        Execute a registered workflow.
        
        Args:
            workflow_name: Name of the workflow to execute
            context: Execution context and parameters
            
        Returns:
            Workflow execution ID
        """
        if workflow_name not in self.workflow_registry:
            raise ValueError(f"Workflow {workflow_name} not registered")
        
        execution_id = f"{workflow_name}_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        workflow_execution = {
            'execution_id': execution_id,
            'workflow_name': workflow_name,
            'status': WorkflowStatus.PENDING,
            'context': context,
            'started_at': datetime.utcnow().isoformat(),
            'completed_at': None,
            'result': None,
            'error': None
        }
        
        self.active_workflows[execution_id] = workflow_execution
        
        # Update workflow registry
        self.workflow_registry[workflow_name]['execution_count'] += 1
        self.workflow_registry[workflow_name]['last_execution'] = execution_id
        
        logger.info("Started workflow execution: %s", execution_id)
        
        # Trigger workflow execution asynchronously
        asyncio.create_task(self._execute_workflow_async(execution_id))
        
        return execution_id
    
    async def _execute_workflow_async(self, execution_id: str):
        """Execute workflow asynchronously."""
        workflow_execution = self.active_workflows[execution_id]
        workflow_name = workflow_execution['workflow_name']
        workflow_config = self.workflow_registry[workflow_name]
        
        try:
            workflow_execution['status'] = WorkflowStatus.RUNNING
            
            # Trigger workflow started event
            await self.trigger_automation(AutomationEventType.WORKFLOW_TRIGGERED, {
                'execution_id': execution_id,
                'workflow_name': workflow_name,
                'context': workflow_execution['context']
            })
            
            # Execute workflow steps (placeholder for actual implementation)
            # This would be expanded based on specific workflow requirements
            result = await self._process_workflow_steps(workflow_config, workflow_execution['context'])
            
            workflow_execution['status'] = WorkflowStatus.COMPLETED
            workflow_execution['result'] = result
            workflow_execution['completed_at'] = datetime.utcnow().isoformat()
            
            logger.info("Workflow execution completed: %s", execution_id)
            
        except Exception as e:
            workflow_execution['status'] = WorkflowStatus.FAILED
            workflow_execution['error'] = str(e)
            workflow_execution['completed_at'] = datetime.utcnow().isoformat()
            
            logger.error("Workflow execution failed: %s - %s", execution_id, str(e))
    
    async def _process_workflow_steps(self, workflow_config: Dict, context: Dict) -> Dict:
        """Process individual workflow steps."""
        # Placeholder for workflow step processing
        # This would be implemented based on specific workflow requirements
        return {
            'status': 'completed',
            'steps_executed': len(workflow_config.get('steps', [])),
            'context': context
        }
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict]:
        """Get the status of a workflow execution."""
        return self.active_workflows.get(execution_id)
    
    def get_automation_metrics(self) -> Dict:
        """Get automation system metrics."""
        active_count = len([w for w in self.active_workflows.values() 
                           if w['status'] in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING]])
        
        completed_count = len([w for w in self.active_workflows.values() 
                              if w['status'] == WorkflowStatus.COMPLETED])
        
        failed_count = len([w for w in self.active_workflows.values() 
                           if w['status'] == WorkflowStatus.FAILED])
        
        return {
            'total_workflows': len(self.workflow_registry),
            'active_executions': active_count,
            'completed_executions': completed_count,
            'failed_executions': failed_count,
            'total_events': len(self.event_history),
            'registered_handlers': sum(len(handlers) for handlers in self.webhook_handlers.values()),
            'last_event': self.event_history[-1] if self.event_history else None
        }


# Global automation integrator instance
automation_integrator = AutomationIntegrator()


# Convenience functions for common automation tasks
def trigger_task_automation(event_type: AutomationEventType, task_id: int, metadata: Optional[Dict] = None):
    """Trigger automation for a task event."""
    payload = {
        'task_id': task_id,
        'timestamp': datetime.utcnow().isoformat(),
        'metadata': metadata or {}
    }
    
    try:
        loop = asyncio.get_event_loop()
        loop.create_task(automation_integrator.trigger_automation(event_type, payload))
    except RuntimeError:
        # If no event loop is running, create a new one
        asyncio.run(automation_integrator.trigger_automation(event_type, payload))


def create_deployment_task(deployment_info: Dict) -> Task:
    """Create a task for deployment tracking."""
    return automation_integrator.create_automation_task(
        workflow_name="deployment",
        parameters=deployment_info,
        title=f"Deployment: {deployment_info.get('environment', 'unknown')}",
        description=f"Automated deployment to {deployment_info.get('environment', 'unknown')} environment",
        type=TaskType.DEPLOYMENT
    )


def register_ci_cd_hooks():
    """Register standard CI/CD automation hooks."""
    
    def deployment_completed_handler(payload: Dict):
        """Handle deployment completion."""
        task_id = payload.get('task_id')
        if task_id:
            automation_integrator.sync_task_status(
                task_id, 
                TaskStatus.DONE,
                {'deployment_completed': True, 'completion_time': datetime.utcnow().isoformat()}
            )
    
    def deployment_failed_handler(payload: Dict):
        """Handle deployment failure."""
        task_id = payload.get('task_id')
        if task_id:
            automation_integrator.sync_task_status(
                task_id, 
                TaskStatus.FAILED,
                {'deployment_failed': True, 'failure_time': datetime.utcnow().isoformat()}
            )
    
    # Register handlers
    automation_integrator.register_workflow_hook(
        AutomationEventType.DEPLOYMENT_COMPLETED, 
        deployment_completed_handler
    )
    
    automation_integrator.register_workflow_hook(
        AutomationEventType.DEPLOYMENT_FAILED, 
        deployment_failed_handler
    )
    
    logger.info("CI/CD automation hooks registered")


# Initialize default hooks when module is imported
register_ci_cd_hooks() 