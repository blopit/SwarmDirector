"""
Cost tracking models for AI API usage monitoring and budget management
"""

from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, Any, Optional
from sqlalchemy import Index
from .base import BaseModel, db


class APIProvider(Enum):
    """Supported AI API providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    PERPLEXITY = "perplexity"
    GOOGLE = "google"
    AZURE_OPENAI = "azure_openai"


class UsageType(Enum):
    """Types of API usage"""
    CHAT_COMPLETION = "chat_completion"
    EMBEDDING = "embedding"
    FINE_TUNING = "fine_tuning"
    IMAGE_GENERATION = "image_generation"
    AUDIO_TRANSCRIPTION = "audio_transcription"


class BudgetPeriod(Enum):
    """Budget period types"""
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    YEARLY = "yearly"


class AlertSeverity(Enum):
    """Cost alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


class APIUsage(BaseModel):
    """Model for tracking individual API usage events"""
    __tablename__ = 'api_usage'
    
    # Request identification
    request_id = db.Column(db.String(100), unique=True, nullable=False, index=True)
    correlation_id = db.Column(db.String(100), index=True)  # Links to agent actions
    
    # API details
    provider = db.Column(db.Enum(APIProvider), nullable=False, index=True)
    model = db.Column(db.String(100), nullable=False, index=True)
    usage_type = db.Column(db.Enum(UsageType), nullable=False, default=UsageType.CHAT_COMPLETION)
    
    # Usage metrics
    input_tokens = db.Column(db.Integer, default=0)
    output_tokens = db.Column(db.Integer, default=0)
    total_tokens = db.Column(db.Integer, default=0)
    
    # Cost information
    input_cost = db.Column(db.Numeric(10, 6), default=0.0)  # Cost for input tokens
    output_cost = db.Column(db.Numeric(10, 6), default=0.0)  # Cost for output tokens
    total_cost = db.Column(db.Numeric(10, 6), default=0.0)  # Total cost in USD
    
    # Pricing rates used (for historical tracking)
    input_price_per_token = db.Column(db.Numeric(12, 8), default=0.0)
    output_price_per_token = db.Column(db.Numeric(12, 8), default=0.0)
    
    # Request metadata
    request_duration_ms = db.Column(db.Integer)  # Request duration in milliseconds
    response_status = db.Column(db.String(20), default='success')  # success, error, timeout
    error_message = db.Column(db.Text)
    
    # Context information
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), index=True)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), index=True)
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), index=True)
    
    # Additional metadata
    request_metadata = db.Column(db.JSON)  # Additional context data
    
    # Relationships
    agent = db.relationship('Agent', backref='api_usage_records')
    task = db.relationship('Task', backref='api_usage_records')
    conversation = db.relationship('Conversation', backref='api_usage_records')
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_api_usage_provider_date', 'provider', 'created_at'),
        Index('idx_api_usage_cost_date', 'total_cost', 'created_at'),
        Index('idx_api_usage_agent_date', 'agent_id', 'created_at'),
        Index('idx_api_usage_model_date', 'model', 'created_at'),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        base_dict = super().to_dict()
        base_dict.update({
            'provider': self.provider.value if self.provider else None,
            'usage_type': self.usage_type.value if self.usage_type else None,
            'input_cost': float(self.input_cost) if self.input_cost else 0.0,
            'output_cost': float(self.output_cost) if self.output_cost else 0.0,
            'total_cost': float(self.total_cost) if self.total_cost else 0.0,
            'input_price_per_token': float(self.input_price_per_token) if self.input_price_per_token else 0.0,
            'output_price_per_token': float(self.output_price_per_token) if self.output_price_per_token else 0.0,
        })
        return base_dict


class CostBudget(BaseModel):
    """Model for managing cost budgets and limits"""
    __tablename__ = 'cost_budgets'
    
    # Budget identification
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Budget scope
    provider = db.Column(db.Enum(APIProvider), index=True)  # None = all providers
    model = db.Column(db.String(100), index=True)  # None = all models
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), index=True)  # None = all agents
    
    # Budget limits
    period = db.Column(db.Enum(BudgetPeriod), nullable=False, default=BudgetPeriod.MONTHLY)
    limit_amount = db.Column(db.Numeric(10, 2), nullable=False)  # Budget limit in USD
    
    # Alert thresholds (percentages of limit)
    warning_threshold = db.Column(db.Integer, default=80)  # 80% of limit
    critical_threshold = db.Column(db.Integer, default=95)  # 95% of limit
    
    # Status
    is_active = db.Column(db.Boolean, default=True, index=True)
    
    # Current period tracking
    current_period_start = db.Column(db.DateTime, nullable=False)
    current_period_end = db.Column(db.DateTime, nullable=False)
    current_period_spent = db.Column(db.Numeric(10, 2), default=0.0)
    
    # Relationships
    agent = db.relationship('Agent', backref='cost_budgets')
    
    # Indexes
    __table_args__ = (
        Index('idx_cost_budget_active_period', 'is_active', 'current_period_start', 'current_period_end'),
        Index('idx_cost_budget_provider_agent', 'provider', 'agent_id'),
    )
    
    def get_usage_percentage(self) -> float:
        """Get current usage as percentage of budget limit"""
        if not self.limit_amount or self.limit_amount == 0:
            return 0.0
        return float((self.current_period_spent / self.limit_amount) * 100)
    
    def is_over_threshold(self, threshold_type: str = 'warning') -> bool:
        """Check if current usage exceeds specified threshold"""
        usage_pct = self.get_usage_percentage()
        if threshold_type == 'warning':
            return usage_pct >= self.warning_threshold
        elif threshold_type == 'critical':
            return usage_pct >= self.critical_threshold
        return False
    
    def get_remaining_budget(self) -> float:
        """Get remaining budget amount"""
        return float(max(0, self.limit_amount - self.current_period_spent))
    
    def reset_period(self) -> None:
        """Reset budget for new period"""
        now = datetime.utcnow()
        
        if self.period == BudgetPeriod.DAILY:
            self.current_period_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
            self.current_period_end = self.current_period_start + timedelta(days=1)
        elif self.period == BudgetPeriod.WEEKLY:
            days_since_monday = now.weekday()
            self.current_period_start = (now - timedelta(days=days_since_monday)).replace(hour=0, minute=0, second=0, microsecond=0)
            self.current_period_end = self.current_period_start + timedelta(weeks=1)
        elif self.period == BudgetPeriod.MONTHLY:
            self.current_period_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            if now.month == 12:
                self.current_period_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            else:
                self.current_period_end = now.replace(month=now.month + 1, day=1, hour=0, minute=0, second=0, microsecond=0)
        elif self.period == BudgetPeriod.YEARLY:
            self.current_period_start = now.replace(month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
            self.current_period_end = now.replace(year=now.year + 1, month=1, day=1, hour=0, minute=0, second=0, microsecond=0)
        
        self.current_period_spent = 0.0
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        base_dict = super().to_dict()
        base_dict.update({
            'provider': self.provider.value if self.provider else None,
            'period': self.period.value if self.period else None,
            'limit_amount': float(self.limit_amount) if self.limit_amount else 0.0,
            'current_period_spent': float(self.current_period_spent) if self.current_period_spent else 0.0,
            'usage_percentage': self.get_usage_percentage(),
            'remaining_budget': self.get_remaining_budget(),
            'is_over_warning': self.is_over_threshold('warning'),
            'is_over_critical': self.is_over_threshold('critical'),
        })
        return base_dict


class CostAlert(BaseModel):
    """Model for cost-related alerts and notifications"""
    __tablename__ = 'cost_alerts'
    
    # Alert identification
    alert_type = db.Column(db.String(50), nullable=False, index=True)  # budget_warning, budget_exceeded, etc.
    severity = db.Column(db.Enum(AlertSeverity), nullable=False, default=AlertSeverity.INFO)
    
    # Alert content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    
    # Related entities
    budget_id = db.Column(db.Integer, db.ForeignKey('cost_budgets.id'), index=True)
    usage_id = db.Column(db.Integer, db.ForeignKey('api_usage.id'), index=True)
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), index=True)
    
    # Alert status
    is_acknowledged = db.Column(db.Boolean, default=False, index=True)
    acknowledged_at = db.Column(db.DateTime)
    acknowledged_by = db.Column(db.String(100))  # User who acknowledged
    
    # Notification status
    notification_sent = db.Column(db.Boolean, default=False)
    notification_channels = db.Column(db.JSON)  # List of channels where alert was sent
    
    # Alert metadata
    alert_metadata = db.Column(db.JSON)  # Additional alert data
    
    # Relationships
    budget = db.relationship('CostBudget', backref='alerts')
    usage = db.relationship('APIUsage', backref='alerts')
    agent = db.relationship('Agent', backref='cost_alerts')
    
    # Indexes
    __table_args__ = (
        Index('idx_cost_alert_type_severity', 'alert_type', 'severity'),
        Index('idx_cost_alert_unacknowledged', 'is_acknowledged', 'created_at'),
    )
    
    def acknowledge(self, acknowledged_by: str) -> None:
        """Mark alert as acknowledged"""
        self.is_acknowledged = True
        self.acknowledged_at = datetime.utcnow()
        self.acknowledged_by = acknowledged_by
        self.save()
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for API responses"""
        base_dict = super().to_dict()
        base_dict.update({
            'severity': self.severity.value if self.severity else None,
        })
        return base_dict
