"""
Validation models for storing validation results and history
"""

from .base import db, BaseModel
from sqlalchemy import Enum, Index
import enum
from datetime import datetime
import json


class ValidationStatus(enum.Enum):
    """Validation status enumeration"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVISION = "requires_revision"
    ESCALATED = "escalated"
    ROLLBACK_REQUIRED = "rollback_required"


class ValidationTier(enum.Enum):
    """Validation tier enumeration"""
    TOOL = "TOOL"
    DEPARTMENT = "DEPARTMENT"
    DIRECTOR = "DIRECTOR"


class ValidationRecord(BaseModel):
    """Database model for storing validation results"""
    __tablename__ = 'validation_records'
    
    # Core validation information
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    tier = db.Column(Enum(ValidationTier), nullable=False)
    status = db.Column(Enum(ValidationStatus), nullable=False)
    
    # Validation details
    validator_name = db.Column(db.String(100), nullable=False)
    validator_version = db.Column(db.String(20), default="1.0.0")
    
    # Metrics (stored as JSON for flexibility)
    metrics = db.Column(db.JSON)  # Quality, completeness, accuracy scores
    issues = db.Column(db.JSON)  # List of validation issues
    recommendations = db.Column(db.JSON)  # List of recommendations
    
    # Timing information
    validation_timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    validation_duration_ms = db.Column(db.Integer, default=0)
    
    # Rollback information
    rollback_required = db.Column(db.Boolean, default=False)
    rollback_reason = db.Column(db.Text)
    rollback_actions = db.Column(db.JSON)
    
    # Context and metadata
    context = db.Column(db.JSON)
    input_data = db.Column(db.JSON)
    output_data = db.Column(db.JSON)
    
    # Relationships
    task = db.relationship('Task', backref='validation_records')
    agent = db.relationship('Agent', backref='validation_records')
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_validation_task_tier', 'task_id', 'tier'),
        Index('idx_validation_status_timestamp', 'status', 'validation_timestamp'),
        Index('idx_validation_agent_tier', 'agent_id', 'tier'),
        Index('idx_validation_rollback', 'rollback_required'),
    )
    
    def __repr__(self):
        return f'<ValidationRecord {self.task_id} {self.tier.value} {self.status.value}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'tier': self.tier.value,
            'status': self.status.value,
            'validation_timestamp': self.validation_timestamp.isoformat() if self.validation_timestamp else None
        })
        return data


class QualityGateConfig(BaseModel):
    """Database model for storing quality gate configurations"""
    __tablename__ = 'quality_gate_configs'
    
    # Configuration identification
    name = db.Column(db.String(100), nullable=False, unique=True)
    tier = db.Column(Enum(ValidationTier), nullable=False)
    description = db.Column(db.Text)
    
    # Configuration data
    config_data = db.Column(db.JSON, nullable=False)  # Thresholds, rules, etc.
    
    # Metadata
    version = db.Column(db.String(20), default="1.0.0")
    is_active = db.Column(db.Boolean, default=True)
    created_by = db.Column(db.String(100))
    
    def __repr__(self):
        return f'<QualityGateConfig {self.name} {self.tier.value}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'tier': self.tier.value
        })
        return data


class RollbackRecord(BaseModel):
    """Database model for storing rollback execution records"""
    __tablename__ = 'rollback_records'
    
    # Core rollback information
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    validation_record_id = db.Column(db.Integer, db.ForeignKey('validation_records.id'), nullable=True)
    
    # Rollback details
    failure_tier = db.Column(db.String(50), nullable=False)
    failure_reason = db.Column(db.Text, nullable=False)
    
    # Execution information
    executed_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    success = db.Column(db.Boolean, default=False)
    
    # Rollback steps and results
    steps_executed = db.Column(db.JSON)  # List of rollback steps
    execution_log = db.Column(db.JSON)  # Detailed execution log
    
    # Relationships
    task = db.relationship('Task', backref='rollback_records')
    validation_record = db.relationship('ValidationRecord', backref='rollback_records')
    
    # Indexes
    __table_args__ = (
        Index('idx_rollback_task_executed', 'task_id', 'executed_at'),
        Index('idx_rollback_success', 'success'),
    )
    
    def __repr__(self):
        return f'<RollbackRecord {self.task_id} {self.failure_tier}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'executed_at': self.executed_at.isoformat() if self.executed_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        })
        return data
