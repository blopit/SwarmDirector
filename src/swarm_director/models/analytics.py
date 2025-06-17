"""
Analytics models for storing task performance metrics and insights
"""

from .base import db, BaseModel
from sqlalchemy import Index, UniqueConstraint
from datetime import datetime


class TaskMetrics(BaseModel):
    """Model for storing aggregated task metrics over time periods"""
    __tablename__ = 'task_metrics'
    
    # Time period for metrics aggregation
    period_start = db.Column(db.DateTime, nullable=False)
    period_end = db.Column(db.DateTime, nullable=False)
    period_type = db.Column(db.String(20), nullable=False)  # hourly, daily, weekly, monthly
    
    # Task completion metrics
    total_tasks = db.Column(db.Integer, default=0)
    completed_tasks = db.Column(db.Integer, default=0)
    failed_tasks = db.Column(db.Integer, default=0)
    cancelled_tasks = db.Column(db.Integer, default=0)
    completion_rate = db.Column(db.Float, default=0.0)
    failure_rate = db.Column(db.Float, default=0.0)
    
    # Performance metrics
    avg_completion_time = db.Column(db.Float, default=0.0)  # minutes
    avg_queue_time = db.Column(db.Float, default=0.0)  # minutes
    avg_processing_time = db.Column(db.Float, default=0.0)  # minutes
    throughput = db.Column(db.Float, default=0.0)  # tasks per hour
    
    # Quality metrics
    avg_quality_score = db.Column(db.Float, default=0.0)
    avg_complexity_score = db.Column(db.Float, default=0.0)
    avg_retry_count = db.Column(db.Float, default=0.0)
    
    # Resource metrics
    agent_utilization = db.Column(db.Float, default=0.0)
    peak_concurrent_tasks = db.Column(db.Integer, default=0)
    bottleneck_indicators = db.Column(db.JSON)
    
    # Task type distribution
    task_type_distribution = db.Column(db.JSON)  # {"EMAIL": 25, "ANALYSIS": 30, ...}
    priority_distribution = db.Column(db.JSON)   # {"HIGH": 15, "MEDIUM": 50, ...}
    
    # Additional metadata
    additional_metadata = db.Column(db.JSON)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_task_metrics_period', 'period_start', 'period_end'),
        Index('idx_task_metrics_type', 'period_type'),
        Index('idx_task_metrics_lookup', 'period_type', 'period_start'),
        UniqueConstraint('period_start', 'period_end', 'period_type', name='uq_task_metrics_period'),
    )

    def __repr__(self):
        return f'<TaskMetrics {self.period_type} {self.period_start} - {self.period_end}>'

    def to_dict(self):
        """Convert metrics to dictionary for API responses"""
        data = super().to_dict()
        data.update({
            'period_start': self.period_start.isoformat() if self.period_start else None,
            'period_end': self.period_end.isoformat() if self.period_end else None,
            'completion_rate_percent': round(self.completion_rate * 100, 2),
            'failure_rate_percent': round(self.failure_rate * 100, 2),
        })
        return data


class TaskAnalyticsInsight(BaseModel):
    """Model for storing generated analytics insights and recommendations"""
    __tablename__ = 'task_analytics_insights'
    
    # Insight metadata
    insight_type = db.Column(db.String(50), nullable=False)  # warning, alert, info, recommendation
    category = db.Column(db.String(50), nullable=False)      # completion_rate, performance, bottleneck, etc.
    priority = db.Column(db.String(20), nullable=False)      # low, medium, high, critical
    
    # Insight content
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    recommendation = db.Column(db.Text)
    action_items = db.Column(db.JSON)  # List of actionable steps
    
    # Metrics that triggered the insight
    trigger_metrics = db.Column(db.JSON)
    threshold_values = db.Column(db.JSON)  # Values that triggered thresholds
    
    # Status tracking
    status = db.Column(db.String(20), default='active')  # active, resolved, dismissed, expired
    resolved_at = db.Column(db.DateTime)
    resolved_by = db.Column(db.String(100))
    resolution_notes = db.Column(db.Text)
    
    # Validity period
    expires_at = db.Column(db.DateTime)
    auto_resolve = db.Column(db.Boolean, default=False)
    
    # Impact assessment
    impact_score = db.Column(db.Float)  # 0-1 scale of potential impact
    confidence_level = db.Column(db.Float)  # 0-1 scale of insight confidence
    
    # Related entities
    related_tasks = db.Column(db.JSON)    # List of task IDs related to this insight
    related_agents = db.Column(db.JSON)   # List of agent IDs related to this insight
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_insights_status', 'status'),
        Index('idx_insights_priority', 'priority'),
        Index('idx_insights_category', 'category'),
        Index('idx_insights_type', 'insight_type'),
        Index('idx_insights_active', 'status', 'created_at'),
        Index('idx_insights_expires', 'expires_at'),
    )

    def __repr__(self):
        return f'<TaskAnalyticsInsight {self.title} ({self.priority})>'

    def to_dict(self):
        """Convert insight to dictionary for API responses"""
        data = super().to_dict()
        data.update({
            'is_active': self.status == 'active',
            'is_expired': self.expires_at and datetime.utcnow() > self.expires_at,
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
        })
        return data

    def resolve(self, resolved_by=None, notes=None):
        """Mark insight as resolved"""
        self.status = 'resolved'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = resolved_by
        if notes:
            self.resolution_notes = notes
        self.save()

    def dismiss(self, dismissed_by=None):
        """Dismiss insight without resolution"""
        self.status = 'dismissed'
        self.resolved_at = datetime.utcnow()
        self.resolved_by = dismissed_by
        self.save()

    def is_expired(self):
        """Check if insight has expired"""
        return self.expires_at and datetime.utcnow() > self.expires_at


class TaskPerformanceSnapshot(BaseModel):
    """Model for storing point-in-time performance snapshots"""
    __tablename__ = 'task_performance_snapshots'
    
    # Snapshot metadata
    snapshot_timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    snapshot_type = db.Column(db.String(20), nullable=False, default='scheduled')  # scheduled, triggered, manual
    
    # Real-time counters
    active_tasks = db.Column(db.Integer, default=0)
    pending_tasks = db.Column(db.Integer, default=0)
    in_progress_tasks = db.Column(db.Integer, default=0)
    completed_today = db.Column(db.Integer, default=0)
    failed_today = db.Column(db.Integer, default=0)
    
    # System performance indicators
    avg_response_time = db.Column(db.Float, default=0.0)  # seconds
    system_load = db.Column(db.Float, default=0.0)       # 0-1 scale
    queue_depth = db.Column(db.Integer, default=0)
    processing_capacity = db.Column(db.Float, default=0.0)  # tasks per minute
    
    # Agent metrics
    active_agents = db.Column(db.Integer, default=0)
    agent_utilization_avg = db.Column(db.Float, default=0.0)
    most_utilized_agent = db.Column(db.String(100))
    least_utilized_agent = db.Column(db.String(100))
    
    # Quality indicators
    current_error_rate = db.Column(db.Float, default=0.0)
    avg_retry_rate = db.Column(db.Float, default=0.0)
    satisfaction_score = db.Column(db.Float)  # if available
    
    # Additional snapshot data
    snapshot_data = db.Column(db.JSON)
    
    # Indexes for time-series queries
    __table_args__ = (
        Index('idx_snapshots_timestamp', 'snapshot_timestamp'),
        Index('idx_snapshots_type', 'snapshot_type'),
        Index('idx_snapshots_time_type', 'snapshot_timestamp', 'snapshot_type'),
    )

    def __repr__(self):
        return f'<TaskPerformanceSnapshot {self.snapshot_timestamp}>'

    def to_dict(self):
        """Convert snapshot to dictionary for API responses"""
        data = super().to_dict()
        data.update({
            'snapshot_timestamp': self.snapshot_timestamp.isoformat(),
            'total_active': self.active_tasks + self.pending_tasks + self.in_progress_tasks,
            'completion_rate_today': (
                self.completed_today / (self.completed_today + self.failed_today) 
                if (self.completed_today + self.failed_today) > 0 else 0
            ),
        })
        return data 