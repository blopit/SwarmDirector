"""
Task model for tracking work assignments and progress
"""

from .base import db, BaseModel
from sqlalchemy import Enum, Index
import enum
from datetime import datetime

class TaskStatus(enum.Enum):
    """Enumeration for task status"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    """Enumeration for task priority"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class TaskType(enum.Enum):
    """Enumeration for task types"""
    EMAIL = "email"
    COMMUNICATION = "communication"
    ANALYSIS = "analysis"
    REVIEW = "review"
    RESEARCH = "research"
    DEVELOPMENT = "development"
    OTHER = "other"

class Task(BaseModel):
    """Task model representing work assignments"""
    __tablename__ = 'tasks'
    
    # Basic task information (as specified in requirements: id, type, user_id, status, created_at, updated_at)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text)
    type = db.Column(Enum(TaskType), nullable=False, default=TaskType.OTHER)  # Required field from task spec
    user_id = db.Column(db.String(100), nullable=True)  # Required field from task spec
    status = db.Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING)
    priority = db.Column(Enum(TaskPriority), nullable=False, default=TaskPriority.MEDIUM)
    
    # Task assignment
    assigned_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    assigned_agent = db.relationship('Agent', backref='assigned_tasks')
    
    # Task hierarchy and dependencies
    parent_task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    parent_task = db.relationship('Task', remote_side='Task.id', backref='subtasks')
    
    # Task metadata
    estimated_duration = db.Column(db.Integer)  # In minutes
    actual_duration = db.Column(db.Integer)  # In minutes
    deadline = db.Column(db.DateTime)
    
    # Task data and results
    input_data = db.Column(db.JSON)  # Input parameters for the task
    output_data = db.Column(db.JSON)  # Results of the task execution
    error_details = db.Column(db.Text)  # Error information if task failed
    
    # Progress tracking
    progress_percentage = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime)
    
    # Analytics and performance tracking fields
    complexity_score = db.Column(db.Integer)  # 1-10 scale for task complexity
    performance_metrics = db.Column(db.JSON)  # Detailed performance data
    queue_time = db.Column(db.Integer)  # Time spent in queue (minutes)
    processing_time = db.Column(db.Integer)  # Time spent processing (minutes)
    retry_count = db.Column(db.Integer, default=0)  # Number of retry attempts
    quality_score = db.Column(db.Float)  # Quality assessment score (0-1)
    
    # Timing analytics
    started_at = db.Column(db.DateTime)  # When task processing started
    completed_at = db.Column(db.DateTime)  # When task was completed
    first_response_time = db.Column(db.Float)  # Time to first response (seconds)
    
    # Indexes for efficient analytics queries
    __table_args__ = (
        Index('idx_task_status_created', 'status', 'created_at'),
        Index('idx_task_type_priority', 'type', 'priority'),
        Index('idx_task_assigned_agent', 'assigned_agent_id'),
        Index('idx_task_completed_at', 'completed_at'),
        Index('idx_task_analytics_lookup', 'status', 'type', 'created_at'),
    )
    
    def __repr__(self):
        return f'<Task {self.title} ({self.status.value})>'
    
    def to_dict(self):
        """Convert task to dictionary with relationships"""
        data = super().to_dict()
        data.update({
            'type': self.type.value,
            'user_id': self.user_id,
            'status': self.status.value,
            'priority': self.priority.value,
            'assigned_agent_id': self.assigned_agent_id,
            'parent_task_id': self.parent_task_id,
            'subtasks_count': len(self.subtasks) if self.subtasks else 0
        })
        return data
    
    def assign_to_agent(self, agent):
        """Assign this task to an agent"""
        self.assigned_agent_id = agent.id
        self.status = TaskStatus.ASSIGNED
        self.save()
    
    def start_progress(self):
        """Mark task as in progress"""
        if not self.started_at:
            self.started_at = datetime.utcnow()
            if self.created_at:
                self.queue_time = int((self.started_at - self.created_at).total_seconds() / 60)
        
        self.status = TaskStatus.IN_PROGRESS
        self.last_activity = datetime.utcnow()
        self.save()
    
    def complete_task(self, output_data=None):
        """Mark task as completed"""
        completion_time = datetime.utcnow()
        self.completed_at = completion_time
        self.status = TaskStatus.COMPLETED
        self.progress_percentage = 100
        
        # Calculate processing time
        if self.started_at:
            self.processing_time = int((completion_time - self.started_at).total_seconds() / 60)
            self.actual_duration = self.processing_time
        
        if output_data:
            self.output_data = output_data
        
        self.save()
        
        # Update agent statistics
        if self.assigned_agent:
            self.assigned_agent.tasks_completed += 1
            self.assigned_agent.save()
    
    def fail_task(self, error_details=None):
        """Mark task as failed"""
        self.status = TaskStatus.FAILED
        self.completed_at = datetime.utcnow()
        self.retry_count += 1
        
        if error_details:
            self.error_details = error_details
        
        # Calculate partial processing time
        if self.started_at:
            self.processing_time = int((self.completed_at - self.started_at).total_seconds() / 60)
        
        self.save()
    
    def add_subtask(self, subtask):
        """Add a subtask to this task"""
        subtask.parent_task_id = self.id
        subtask.save()
    
    def get_dependency_chain(self):
        """Get the chain of parent tasks"""
        chain = []
        current = self
        while current.parent_task_id:
            current = Task.query.get(current.parent_task_id)
            chain.append(current)
        return chain
    
    def can_be_started(self):
        """Check if task can be started (no blocking dependencies)"""
        if self.status != TaskStatus.ASSIGNED:
            return False
        
        # Check if parent task is completed (if exists)
        if self.parent_task and self.parent_task.status != TaskStatus.COMPLETED:
            return False
            
        return True

    def calculate_analytics(self):
        """Calculate task performance analytics."""
        analytics = {
            'completion_rate': self.progress_percentage,
            'time_efficiency': None,
            'status_transitions': self.retry_count,
            'queue_efficiency': None,
            'quality_metrics': {
                'complexity_score': self.complexity_score,
                'quality_score': self.quality_score,
                'retry_rate': self.retry_count
            }
        }
        
        # Calculate time efficiency
        if self.estimated_duration and self.actual_duration:
            analytics['time_efficiency'] = min(1.0, self.estimated_duration / self.actual_duration)
        
        # Calculate queue efficiency
        if self.queue_time and self.processing_time:
            total_time = self.queue_time + self.processing_time
            analytics['queue_efficiency'] = self.processing_time / total_time if total_time > 0 else 0
        
        return analytics 