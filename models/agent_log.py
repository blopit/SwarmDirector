"""
AgentLog model for tracking agent activities and logging
"""

from .base import db, BaseModel
from sqlalchemy import Enum
import enum

class LogLevel(enum.Enum):
    """Enumeration for log levels"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"

class AgentLog(BaseModel):
    """AgentLog model for tracking agent activities"""
    __tablename__ = 'agent_logs'
    
    # Foreign key to task (as specified in requirements)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=True)
    task = db.relationship('Task', backref='agent_logs')
    
    # Agent type that generated this log
    agent_type = db.Column(db.String(50), nullable=False)
    
    # Log message content
    message = db.Column(db.Text, nullable=False)
    
    # Additional fields for better logging
    log_level = db.Column(Enum(LogLevel), nullable=False, default=LogLevel.INFO)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    agent = db.relationship('Agent', backref='logs')
    
    # Context and metadata
    context = db.Column(db.JSON)  # Additional context data
    execution_time = db.Column(db.Float)  # Execution time in seconds
    memory_usage = db.Column(db.Integer)  # Memory usage in MB
    
    # Note: timestamp is inherited from BaseModel as created_at
    
    def __repr__(self):
        return f'<AgentLog {self.id} {self.agent_type} ({self.log_level.value})>'
    
    def to_dict(self):
        """Convert agent log to dictionary"""
        data = super().to_dict()
        data.update({
            'log_level': self.log_level.value,
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'agent_type': self.agent_type
        })
        return data
    
    @classmethod
    def log_agent_activity(cls, agent_id, agent_type, message, task_id=None, 
                          log_level=LogLevel.INFO, context=None, 
                          execution_time=None, memory_usage=None):
        """Convenience method to create a new agent log entry"""
        log_entry = cls(
            agent_id=agent_id,
            agent_type=agent_type,
            message=message,
            task_id=task_id,
            log_level=log_level,
            context=context,
            execution_time=execution_time,
            memory_usage=memory_usage
        )
        log_entry.save()
        return log_entry 