"""
Database models for workflow state persistence
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, Optional

from ..utils.database import db, BaseMixin

class WorkflowStateDB(BaseMixin, db.Model):
    """Database model for workflow states"""
    __tablename__ = 'workflow_states'
    
    # Core identification
    workflow_id = db.Column(db.String(255), unique=True, nullable=False, index=True)
    workflow_type = db.Column(db.String(100), nullable=False, index=True)
    
    # Status and phase tracking
    status = db.Column(db.String(50), nullable=False, default='pending', index=True)
    current_phase = db.Column(db.String(100), nullable=True, index=True)
    
    # Timestamps
    started_at = db.Column(db.DateTime, nullable=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    
    # Progress tracking
    total_steps = db.Column(db.Integer, default=0)
    completed_steps = db.Column(db.Integer, default=0)
    
    # Context data (stored as JSON)
    input_data = db.Column(db.Text, nullable=True)  # JSON string
    output_data = db.Column(db.Text, nullable=True)  # JSON string
    error_data = db.Column(db.Text, nullable=True)  # JSON string
    
    # Email-specific context (stored as JSON)
    email_context = db.Column(db.Text, nullable=True)  # JSON string
    review_context = db.Column(db.Text, nullable=True)  # JSON string
    
    # Agent assignments
    assigned_director = db.Column(db.String(255), nullable=True)
    assigned_communications_dept = db.Column(db.String(255), nullable=True)
    assigned_email_agent = db.Column(db.String(255), nullable=True)
    assigned_review_agents = db.Column(db.Text, nullable=True)  # JSON array
    
    # Metrics
    review_iterations = db.Column(db.Integer, default=0)
    content_revisions = db.Column(db.Integer, default=0)
    delivery_attempts = db.Column(db.Integer, default=0)
    
    # Phase and state history (stored as JSON)
    phase_history = db.Column(db.Text, nullable=True)  # JSON string
    phase_durations = db.Column(db.Text, nullable=True)  # JSON string
    state_history = db.Column(db.Text, nullable=True)  # JSON string
    
    # Active agents tracking (stored as JSON)
    active_agents = db.Column(db.Text, nullable=True)  # JSON array
    completed_tasks = db.Column(db.Text, nullable=True)  # JSON array
    failed_tasks = db.Column(db.Text, nullable=True)  # JSON array
    
    def __init__(self, workflow_id: str, workflow_type: str = 'general', **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
        self.workflow_type = workflow_type
    
    def set_input_data(self, data: Dict[str, Any]):
        """Set input data as JSON"""
        self.input_data = json.dumps(data) if data else None
    
    def get_input_data(self) -> Dict[str, Any]:
        """Get input data from JSON"""
        return json.loads(self.input_data) if self.input_data else {}
    
    def set_output_data(self, data: Dict[str, Any]):
        """Set output data as JSON"""
        self.output_data = json.dumps(data) if data else None
    
    def get_output_data(self) -> Dict[str, Any]:
        """Get output data from JSON"""
        return json.loads(self.output_data) if self.output_data else {}
    
    def set_error_data(self, data: Dict[str, Any]):
        """Set error data as JSON"""
        self.error_data = json.dumps(data) if data else None
    
    def get_error_data(self) -> Dict[str, Any]:
        """Get error data from JSON"""
        return json.loads(self.error_data) if self.error_data else {}
    
    def set_email_context(self, context: Dict[str, Any]):
        """Set email context as JSON"""
        self.email_context = json.dumps(context) if context else None
    
    def get_email_context(self) -> Dict[str, Any]:
        """Get email context from JSON"""
        return json.loads(self.email_context) if self.email_context else {}
    
    def set_review_context(self, context: Dict[str, Any]):
        """Set review context as JSON"""
        self.review_context = json.dumps(context) if context else None
    
    def get_review_context(self) -> Dict[str, Any]:
        """Get review context from JSON"""
        return json.loads(self.review_context) if self.review_context else {}
    
    def set_assigned_review_agents(self, agents: list):
        """Set assigned review agents as JSON"""
        self.assigned_review_agents = json.dumps(agents) if agents else None
    
    def get_assigned_review_agents(self) -> list:
        """Get assigned review agents from JSON"""
        return json.loads(self.assigned_review_agents) if self.assigned_review_agents else []
    
    def set_phase_history(self, history: list):
        """Set phase history as JSON"""
        self.phase_history = json.dumps(history) if history else None
    
    def get_phase_history(self) -> list:
        """Get phase history from JSON"""
        return json.loads(self.phase_history) if self.phase_history else []
    
    def set_phase_durations(self, durations: Dict[str, float]):
        """Set phase durations as JSON"""
        self.phase_durations = json.dumps(durations) if durations else None
    
    def get_phase_durations(self) -> Dict[str, float]:
        """Get phase durations from JSON"""
        return json.loads(self.phase_durations) if self.phase_durations else {}
    
    def set_state_history(self, history: list):
        """Set state history as JSON"""
        self.state_history = json.dumps(history) if history else None
    
    def get_state_history(self) -> list:
        """Get state history from JSON"""
        return json.loads(self.state_history) if self.state_history else []
    
    def set_active_agents(self, agents: list):
        """Set active agents as JSON"""
        self.active_agents = json.dumps(agents) if agents else None
    
    def get_active_agents(self) -> list:
        """Get active agents from JSON"""
        return json.loads(self.active_agents) if self.active_agents else []
    
    def set_completed_tasks(self, tasks: list):
        """Set completed tasks as JSON"""
        self.completed_tasks = json.dumps(tasks) if tasks else None
    
    def get_completed_tasks(self) -> list:
        """Get completed tasks from JSON"""
        return json.loads(self.completed_tasks) if self.completed_tasks else []
    
    def set_failed_tasks(self, tasks: list):
        """Set failed tasks as JSON"""
        self.failed_tasks = json.dumps(tasks) if tasks else None
    
    def get_failed_tasks(self) -> list:
        """Get failed tasks from JSON"""
        return json.loads(self.failed_tasks) if self.failed_tasks else []
    
    def get_progress_percentage(self) -> float:
        """Calculate progress percentage"""
        if self.total_steps == 0:
            return 0.0
        return (self.completed_steps / self.total_steps) * 100.0
    
    def get_execution_duration(self) -> Optional[float]:
        """Get execution duration in seconds"""
        if not self.started_at:
            return None
        
        end_time = self.completed_at or datetime.utcnow()
        return (end_time - self.started_at).total_seconds()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'workflow_type': self.workflow_type,
            'status': self.status,
            'current_phase': self.current_phase,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'total_steps': self.total_steps,
            'completed_steps': self.completed_steps,
            'progress_percentage': self.get_progress_percentage(),
            'execution_duration': self.get_execution_duration(),
            'input_data': self.get_input_data(),
            'output_data': self.get_output_data(),
            'error_data': self.get_error_data(),
            'email_context': self.get_email_context(),
            'review_context': self.get_review_context(),
            'assigned_director': self.assigned_director,
            'assigned_communications_dept': self.assigned_communications_dept,
            'assigned_email_agent': self.assigned_email_agent,
            'assigned_review_agents': self.get_assigned_review_agents(),
            'review_iterations': self.review_iterations,
            'content_revisions': self.content_revisions,
            'delivery_attempts': self.delivery_attempts,
            'phase_history': self.get_phase_history(),
            'phase_durations': self.get_phase_durations(),
            'state_history': self.get_state_history(),
            'active_agents': self.get_active_agents(),
            'completed_tasks': self.get_completed_tasks(),
            'failed_tasks': self.get_failed_tasks()
        }
    
    @classmethod
    def find_by_workflow_id(cls, workflow_id: str):
        """Find workflow state by workflow ID"""
        return cls.query.filter_by(workflow_id=workflow_id).first()
    
    @classmethod
    def find_by_status(cls, status: str):
        """Find workflow states by status"""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def find_by_workflow_type(cls, workflow_type: str):
        """Find workflow states by type"""
        return cls.query.filter_by(workflow_type=workflow_type).all()
    
    @classmethod
    def find_by_phase(cls, phase: str):
        """Find workflow states by current phase"""
        return cls.query.filter_by(current_phase=phase).all()
    
    @classmethod
    def find_active_workflows(cls):
        """Find all active (running or paused) workflows"""
        return cls.query.filter(cls.status.in_(['running', 'paused'])).all()
    
    @classmethod
    def cleanup_old_workflows(cls, days_old: int = 30):
        """Cleanup completed workflows older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days_old)
        old_workflows = cls.query.filter(
            cls.status.in_(['completed', 'failed', 'cancelled']),
            cls.completed_at < cutoff_date
        ).all()
        
        count = len(old_workflows)
        for workflow in old_workflows:
            db.session.delete(workflow)
        
        db.session.commit()
        return count

class WorkflowEventDB(BaseMixin, db.Model):
    """Database model for workflow events and transitions"""
    __tablename__ = 'workflow_events'
    
    workflow_id = db.Column(db.String(255), nullable=False, index=True)
    event_type = db.Column(db.String(100), nullable=False, index=True)  # state_transition, phase_change, error, etc.
    
    # Event details
    from_state = db.Column(db.String(50), nullable=True)
    to_state = db.Column(db.String(50), nullable=True)
    from_phase = db.Column(db.String(100), nullable=True)
    to_phase = db.Column(db.String(100), nullable=True)
    
    # Agent and reason
    agent_name = db.Column(db.String(255), nullable=True)
    reason = db.Column(db.Text, nullable=True)
    
    # Event metadata (stored as JSON)
    metadata = db.Column(db.Text, nullable=True)  # JSON string
    
    # Foreign key to workflow state
    workflow_state_id = db.Column(db.Integer, db.ForeignKey('workflow_states.id'), nullable=True)
    
    def __init__(self, workflow_id: str, event_type: str, **kwargs):
        super().__init__(**kwargs)
        self.workflow_id = workflow_id
        self.event_type = event_type
    
    def set_metadata(self, data: Dict[str, Any]):
        """Set metadata as JSON"""
        self.metadata = json.dumps(data) if data else None
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get metadata from JSON"""
        return json.loads(self.metadata) if self.metadata else {}
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'workflow_id': self.workflow_id,
            'event_type': self.event_type,
            'from_state': self.from_state,
            'to_state': self.to_state,
            'from_phase': self.from_phase,
            'to_phase': self.to_phase,
            'agent_name': self.agent_name,
            'reason': self.reason,
            'metadata': self.get_metadata(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def find_by_workflow(cls, workflow_id: str):
        """Find all events for a workflow"""
        return cls.query.filter_by(workflow_id=workflow_id).order_by(cls.created_at.asc()).all()
    
    @classmethod
    def find_by_event_type(cls, event_type: str):
        """Find events by type"""
        return cls.query.filter_by(event_type=event_type).all()