"""
Workflow State Management
Manages workflow states, transitions, and state persistence
"""

import threading
import json
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class WorkflowStatus(Enum):
    """Standard workflow status values"""
    PENDING = "pending"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    
class StateTransitionError(Exception):
    """Exception raised when an invalid state transition is attempted"""
    pass

@dataclass
class StateTransition:
    """Represents a state transition with metadata"""
    from_state: WorkflowStatus
    to_state: WorkflowStatus
    timestamp: datetime
    agent_name: Optional[str] = None
    reason: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class WorkflowState:
    """
    Represents the complete state of a workflow including status, 
    agent states, and execution context
    """
    workflow_id: str
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    
    # Agent and task tracking
    active_agents: List[str] = field(default_factory=list)
    completed_tasks: List[str] = field(default_factory=list)
    failed_tasks: List[str] = field(default_factory=list)
    
    # Execution context
    input_data: Dict[str, Any] = field(default_factory=dict)
    output_data: Dict[str, Any] = field(default_factory=dict)
    error_data: Dict[str, Any] = field(default_factory=dict)
    
    # State history
    state_history: List[StateTransition] = field(default_factory=list)
    
    # Progress tracking
    total_steps: int = 0
    completed_steps: int = 0
    
    def get_progress_percentage(self) -> float:
        """Calculate workflow completion percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    def add_transition(self, to_state: WorkflowStatus, agent_name: str = None, 
                      reason: str = None, metadata: Dict[str, Any] = None):
        """Add a state transition to the history"""
        transition = StateTransition(
            from_state=self.status,
            to_state=to_state,
            timestamp=datetime.utcnow(),
            agent_name=agent_name,
            reason=reason,
            metadata=metadata or {}
        )
        self.state_history.append(transition)
        self.status = to_state
        self.updated_at = datetime.utcnow()
        
        # Update timestamps based on status
        if to_state == WorkflowStatus.RUNNING and self.started_at is None:
            self.started_at = datetime.utcnow()
        elif to_state in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED]:
            self.completed_at = datetime.utcnow()
    
    def get_execution_duration(self) -> Optional[float]:
        """Get workflow execution duration in seconds"""
        if self.started_at is None:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert workflow state to dictionary for serialization"""
        return {
            'workflow_id': self.workflow_id,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'active_agents': self.active_agents,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_data': self.error_data,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'progress_percentage': self.get_progress_percentage(),
            'execution_duration': self.get_execution_duration(),
            'state_history': [
                {
                    'from_state': t.from_state.value,
                    'to_state': t.to_state.value,
                    'timestamp': t.timestamp.isoformat(),
                    'agent_name': t.agent_name,
                    'reason': t.reason,
                    'metadata': t.metadata
                }
                for t in self.state_history
            ]
        }

class WorkflowStateManager:
    """
    Manages workflow states with thread-safe operations and state persistence
    """
    
    # Valid state transitions
    VALID_TRANSITIONS = {
        WorkflowStatus.PENDING: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
        WorkflowStatus.RUNNING: [WorkflowStatus.PAUSED, WorkflowStatus.COMPLETED, 
                               WorkflowStatus.FAILED, WorkflowStatus.CANCELLED],
        WorkflowStatus.PAUSED: [WorkflowStatus.RUNNING, WorkflowStatus.CANCELLED],
        WorkflowStatus.COMPLETED: [],
        WorkflowStatus.FAILED: [WorkflowStatus.RUNNING],  # Allow retry
        WorkflowStatus.CANCELLED: []
    }
    
    def __init__(self):
        self._states: Dict[str, WorkflowState] = {}
        self._lock = threading.RLock()
        self._state_listeners: Dict[str, List[Callable]] = {}
        
    def create_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None,
                       total_steps: int = 0) -> WorkflowState:
        """Create a new workflow state"""
        with self._lock:
            if workflow_id in self._states:
                raise ValueError(f"Workflow {workflow_id} already exists")
            
            state = WorkflowState(
                workflow_id=workflow_id,
                input_data=input_data or {},
                total_steps=total_steps
            )
            self._states[workflow_id] = state
            
            logger.info(f"Created workflow state: {workflow_id}")
            self._notify_listeners(workflow_id, state)
            return state
    
    def get_workflow_state(self, workflow_id: str) -> Optional[WorkflowState]:
        """Get workflow state by ID"""
        with self._lock:
            return self._states.get(workflow_id)
    
    def update_workflow_status(self, workflow_id: str, new_status: WorkflowStatus,
                             agent_name: str = None, reason: str = None,
                             metadata: Dict[str, Any] = None) -> bool:
        """Update workflow status with validation"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            # Validate transition
            if new_status not in self.VALID_TRANSITIONS.get(state.status, []):
                raise StateTransitionError(
                    f"Invalid transition from {state.status.value} to {new_status.value}"
                )
            
            state.add_transition(new_status, agent_name, reason, metadata)
            logger.info(f"Workflow {workflow_id} status updated to {new_status.value}")
            
            self._notify_listeners(workflow_id, state)
            return True
    
    def add_active_agent(self, workflow_id: str, agent_name: str) -> bool:
        """Add an agent to the active agents list"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            if agent_name not in state.active_agents:
                state.active_agents.append(agent_name)
                state.updated_at = datetime.utcnow()
                self._notify_listeners(workflow_id, state)
            
            return True
    
    def remove_active_agent(self, workflow_id: str, agent_name: str) -> bool:
        """Remove an agent from the active agents list"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            if agent_name in state.active_agents:
                state.active_agents.remove(agent_name)
                state.updated_at = datetime.utcnow()
                self._notify_listeners(workflow_id, state)
            
            return True
    
    def complete_task(self, workflow_id: str, task_id: str) -> bool:
        """Mark a task as completed and update progress"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            if task_id not in state.completed_tasks:
                state.completed_tasks.append(task_id)
                state.completed_steps += 1
                state.updated_at = datetime.utcnow()
                
                # Check if workflow is complete
                if state.completed_steps >= state.total_steps and state.status == WorkflowStatus.RUNNING:
                    state.add_transition(WorkflowStatus.COMPLETED, reason="All tasks completed")
                
                self._notify_listeners(workflow_id, state)
            
            return True
    
    def fail_task(self, workflow_id: str, task_id: str, error_info: Dict[str, Any] = None) -> bool:
        """Mark a task as failed"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            if task_id not in state.failed_tasks:
                state.failed_tasks.append(task_id)
                if error_info:
                    state.error_data[task_id] = error_info
                state.updated_at = datetime.utcnow()
                self._notify_listeners(workflow_id, state)
            
            return True
    
    def update_workflow_data(self, workflow_id: str, output_data: Dict[str, Any] = None,
                           error_data: Dict[str, Any] = None) -> bool:
        """Update workflow output or error data"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return False
            
            if output_data:
                state.output_data.update(output_data)
            if error_data:
                state.error_data.update(error_data)
            
            state.updated_at = datetime.utcnow()
            self._notify_listeners(workflow_id, state)
            return True
    
    def add_state_listener(self, workflow_id: str, listener: Callable[[WorkflowState], None]):
        """Add a listener for state changes"""
        with self._lock:
            if workflow_id not in self._state_listeners:
                self._state_listeners[workflow_id] = []
            self._state_listeners[workflow_id].append(listener)
    
    def remove_state_listener(self, workflow_id: str, listener: Callable[[WorkflowState], None]):
        """Remove a state listener"""
        with self._lock:
            if workflow_id in self._state_listeners:
                try:
                    self._state_listeners[workflow_id].remove(listener)
                except ValueError:
                    pass  # Listener not found
    
    def _notify_listeners(self, workflow_id: str, state: WorkflowState):
        """Notify all listeners of state changes"""
        listeners = self._state_listeners.get(workflow_id, [])
        for listener in listeners:
            try:
                listener(state)
            except Exception as e:
                logger.error(f"Error notifying state listener: {e}")
    
    def get_all_workflows(self) -> Dict[str, WorkflowState]:
        """Get all workflow states"""
        with self._lock:
            return self._states.copy()
    
    def cleanup_completed_workflows(self, max_age_hours: int = 24) -> int:
        """Remove completed workflows older than specified age"""
        removed_count = 0
        cutoff_time = datetime.utcnow().timestamp() - (max_age_hours * 3600)
        
        with self._lock:
            workflows_to_remove = []
            for workflow_id, state in self._states.items():
                if (state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                    state.completed_at and state.completed_at.timestamp() < cutoff_time):
                    workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                del self._states[workflow_id]
                # Clean up listeners
                if workflow_id in self._state_listeners:
                    del self._state_listeners[workflow_id]
                removed_count += 1
        
        logger.info(f"Cleaned up {removed_count} completed workflows")
        return removed_count
    
    def export_workflow_history(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Export complete workflow history for analysis"""
        with self._lock:
            state = self._states.get(workflow_id)
            if not state:
                return None
            
            return state.to_dict() 