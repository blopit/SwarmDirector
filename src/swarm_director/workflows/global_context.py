"""
Global Context Access Utilities
Provides global access to workflow state and context for tools and functions
"""

import logging
from typing import Dict, Any, Optional, Callable, List
from functools import wraps
from contextlib import contextmanager
import threading

from .persistent_state_manager import PersistentEmailWorkflowStateManager
from .email_workflow_states import EmailWorkflowState, EmailWorkflowType, EmailWorkflowPhase

logger = logging.getLogger(__name__)

class GlobalWorkflowContext:
    """
    Singleton class providing global access to workflow state and context
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        
        self._initialized = True
        self._state_manager: Optional[PersistentEmailWorkflowStateManager] = None
        self._current_workflow_id: Optional[str] = None
        self._context_stack: list = []
        self._local = threading.local()
        
        # Context listeners
        self._context_listeners: Dict[str, list] = {
            'workflow_created': [],
            'workflow_started': [],
            'workflow_completed': [],
            'phase_changed': [],
            'context_updated': []
        }
    
    def initialize(self, state_manager: PersistentEmailWorkflowStateManager):
        """Initialize the global context with a state manager"""
        self._state_manager = state_manager
        logger.info("Global workflow context initialized")
    
    def get_state_manager(self) -> Optional[PersistentEmailWorkflowStateManager]:
        """Get the state manager instance"""
        return self._state_manager
    
    def set_current_workflow(self, workflow_id: str):
        """Set the current workflow ID for the current thread"""
        if not hasattr(self._local, 'workflow_id'):
            self._local.workflow_id = None
        self._local.workflow_id = workflow_id
    
    def get_current_workflow_id(self) -> Optional[str]:
        """Get the current workflow ID for the current thread"""
        return getattr(self._local, 'workflow_id', None)
    
    def get_current_workflow_state(self) -> Optional[EmailWorkflowState]:
        """Get the current workflow state for the current thread"""
        workflow_id = self.get_current_workflow_id()
        if not workflow_id or not self._state_manager:
            return None
        return self._state_manager.get_email_workflow(workflow_id)
    
    def get_workflow_state(self, workflow_id: str) -> Optional[EmailWorkflowState]:
        """Get workflow state by ID"""
        if not self._state_manager:
            return None
        return self._state_manager.get_email_workflow(workflow_id)
    
    def create_workflow(self, workflow_id: str, workflow_type: EmailWorkflowType, 
                       **kwargs) -> Optional[EmailWorkflowState]:
        """Create a new workflow and set it as current"""
        if not self._state_manager:
            logger.error("State manager not initialized")
            return None
        
        state = self._state_manager.create_email_workflow(workflow_id, workflow_type, **kwargs)
        self.set_current_workflow(workflow_id)
        
        # Notify listeners
        self._notify_listeners('workflow_created', workflow_id, state)
        
        return state
    
    def update_context(self, workflow_id: str = None, **updates) -> bool:
        """Update workflow context"""
        workflow_id = workflow_id or self.get_current_workflow_id()
        if not workflow_id or not self._state_manager:
            return False
        
        success = self._state_manager.update_email_context(workflow_id, **updates)
        if success:
            state = self.get_workflow_state(workflow_id)
            self._notify_listeners('context_updated', workflow_id, state)
        
        return success
    
    def advance_phase(self, new_phase: EmailWorkflowPhase, agent_name: str = None,
                     notes: str = None, workflow_id: str = None) -> bool:
        """Advance workflow phase"""
        workflow_id = workflow_id or self.get_current_workflow_id()
        if not workflow_id or not self._state_manager:
            return False
        
        success = self._state_manager.advance_workflow_phase(workflow_id, new_phase, agent_name, notes)
        if success:
            state = self.get_workflow_state(workflow_id)
            self._notify_listeners('phase_changed', workflow_id, state)
        
        return success
    
    def get_context_value(self, key: str, workflow_id: str = None, default=None):
        """Get a specific value from workflow context"""
        state = self.get_workflow_state(workflow_id or self.get_current_workflow_id())
        if not state:
            return default
        
        # Check in email context first
        if hasattr(state.email_context, key):
            return getattr(state.email_context, key)
        
        # Check in input data
        if key in state.input_data:
            return state.input_data[key]
        
        # Check in output data
        if key in state.output_data:
            return state.output_data[key]
        
        return default
    
    def set_context_value(self, key: str, value: Any, workflow_id: str = None) -> bool:
        """Set a specific value in workflow context"""
        workflow_id = workflow_id or self.get_current_workflow_id()
        state = self.get_workflow_state(workflow_id)
        if not state:
            return False
        
        # Try to set in email context if the attribute exists
        if hasattr(state.email_context, key):
            setattr(state.email_context, key, value)
            return self.update_context(workflow_id)
        
        # Otherwise, set in input data
        state.input_data[key] = value
        return self.update_context(workflow_id)
    
    def add_listener(self, event_type: str, listener: Callable):
        """Add a context event listener"""
        if event_type in self._context_listeners:
            self._context_listeners[event_type].append(listener)
    
    def remove_listener(self, event_type: str, listener: Callable):
        """Remove a context event listener"""
        if event_type in self._context_listeners and listener in self._context_listeners[event_type]:
            self._context_listeners[event_type].remove(listener)
    
    def _notify_listeners(self, event_type: str, workflow_id: str, state: EmailWorkflowState):
        """Notify event listeners"""
        for listener in self._context_listeners.get(event_type, []):
            try:
                listener(workflow_id, state)
            except Exception as e:
                logger.error(f"Error in context listener {listener}: {e}")
    
    @contextmanager
    def workflow_context(self, workflow_id: str):
        """Context manager for setting current workflow"""
        old_workflow_id = self.get_current_workflow_id()
        self.set_current_workflow(workflow_id)
        try:
            yield self.get_current_workflow_state()
        finally:
            if old_workflow_id:
                self.set_current_workflow(old_workflow_id)
            else:
                self._local.workflow_id = None

# Global instance
global_context = GlobalWorkflowContext()

# Convenience functions
def get_current_workflow() -> Optional[EmailWorkflowState]:
    """Get the current workflow state"""
    return global_context.get_current_workflow_state()

def get_workflow(workflow_id: str) -> Optional[EmailWorkflowState]:
    """Get workflow state by ID"""
    return global_context.get_workflow_state(workflow_id)

def get_context_value(key: str, default=None):
    """Get a value from current workflow context"""
    return global_context.get_context_value(key, default=default)

def set_context_value(key: str, value: Any) -> bool:
    """Set a value in current workflow context"""
    return global_context.set_context_value(key, value)

def update_workflow_context(**updates) -> bool:
    """Update current workflow context"""
    return global_context.update_context(**updates)

def advance_workflow_phase(new_phase: EmailWorkflowPhase, agent_name: str = None, notes: str = None) -> bool:
    """Advance current workflow phase"""
    return global_context.advance_phase(new_phase, agent_name, notes)

# Decorators
def with_workflow_context(workflow_id_param: str = 'workflow_id'):
    """Decorator to set workflow context for a function"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Extract workflow_id from kwargs
            workflow_id = kwargs.get(workflow_id_param)
            if not workflow_id:
                # Try to get from args based on function signature
                import inspect
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                if workflow_id_param in param_names:
                    param_index = param_names.index(workflow_id_param)
                    if param_index < len(args):
                        workflow_id = args[param_index]
            
            if workflow_id:
                with global_context.workflow_context(workflow_id):
                    return func(*args, **kwargs)
            else:
                return func(*args, **kwargs)
        return wrapper
    return decorator

def requires_workflow_context(func):
    """Decorator that requires an active workflow context"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not global_context.get_current_workflow_id():
            raise RuntimeError(f"Function {func.__name__} requires an active workflow context")
        return func(*args, **kwargs)
    return wrapper

def auto_advance_phase(target_phase: EmailWorkflowPhase, agent_name: str = None):
    """Decorator to automatically advance workflow phase after function execution"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            
            # Only advance phase if function executed successfully
            if result and not isinstance(result, dict) or (isinstance(result, dict) and result.get('status') == 'success'):
                advance_workflow_phase(target_phase, agent_name or func.__name__)
            
            return result
        return wrapper
    return decorator

# Context-aware logging
class WorkflowLogger:
    """Logger that includes workflow context in messages"""
    
    def __init__(self, name: str):
        self.logger = logging.getLogger(name)
    
    def _format_message(self, msg: str) -> str:
        """Format message with workflow context"""
        workflow_id = global_context.get_current_workflow_id()
        if workflow_id:
            state = global_context.get_current_workflow_state()
            if state:
                return f"[Workflow: {workflow_id}, Phase: {state.current_phase.value}] {msg}"
            else:
                return f"[Workflow: {workflow_id}] {msg}"
        return msg
    
    def debug(self, msg: str, *args, **kwargs):
        self.logger.debug(self._format_message(msg), *args, **kwargs)
    
    def info(self, msg: str, *args, **kwargs):
        self.logger.info(self._format_message(msg), *args, **kwargs)
    
    def warning(self, msg: str, *args, **kwargs):
        self.logger.warning(self._format_message(msg), *args, **kwargs)
    
    def error(self, msg: str, *args, **kwargs):
        self.logger.error(self._format_message(msg), *args, **kwargs)
    
    def critical(self, msg: str, *args, **kwargs):
        self.logger.critical(self._format_message(msg), *args, **kwargs)

def get_workflow_logger(name: str) -> WorkflowLogger:
    """Get a workflow-aware logger"""
    return WorkflowLogger(name)

# Workflow utilities
class WorkflowUtils:
    """Utility functions for workflow management"""
    
    @staticmethod
    def get_workflow_progress() -> Dict[str, Any]:
        """Get current workflow progress information"""
        state = get_current_workflow()
        if not state:
            return {'error': 'No active workflow'}
        return state.get_workflow_progress()
    
    @staticmethod
    def get_workflow_stats() -> Dict[str, Any]:
        """Get workflow statistics"""
        state_manager = global_context.get_state_manager()
        if not state_manager:
            return {'error': 'No state manager available'}
        return state_manager.get_email_workflow_statistics()
    
    @staticmethod
    def get_active_workflows() -> Dict[str, Dict[str, Any]]:
        """Get all active workflows with their progress"""
        state_manager = global_context.get_state_manager()
        if not state_manager:
            return {}
        
        active_workflows = {}
        for workflow_id, state in state_manager._email_workflows.items():
            if state.status.value in ['pending', 'running', 'paused']:
                active_workflows[workflow_id] = {
                    'type': state.workflow_type.value,
                    'phase': state.current_phase.value,
                    'status': state.status.value,
                    'progress': state.get_workflow_progress()
                }
        
        return active_workflows
    
    @staticmethod
    def get_workflow_history(workflow_id: str = None) -> List[Dict[str, Any]]:
        """Get workflow history"""
        workflow_id = workflow_id or global_context.get_current_workflow_id()
        state_manager = global_context.get_state_manager()
        
        if not workflow_id or not state_manager:
            return []
        
        return state_manager.get_workflow_events(workflow_id)

# Initialize utilities
workflow_utils = WorkflowUtils()