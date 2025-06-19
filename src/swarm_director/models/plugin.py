"""
Plugin models for storing plugin metadata and installation records
"""

from .base import db, BaseModel
from sqlalchemy import Enum, Index
import enum
from datetime import datetime


class PluginType(enum.Enum):
    """Plugin type enumeration"""
    AGENT = "agent"
    TOOL = "tool"
    VALIDATOR = "validator"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    EXTENSION = "extension"


class PluginStatus(enum.Enum):
    """Plugin status enumeration"""
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


class PluginRecord(BaseModel):
    """Database model for storing plugin metadata"""
    __tablename__ = 'plugin_records'
    
    # Basic plugin information
    name = db.Column(db.String(100), nullable=False, unique=True)
    version = db.Column(db.String(20), nullable=False)
    description = db.Column(db.Text)
    author = db.Column(db.String(100))
    plugin_type = db.Column(Enum(PluginType), nullable=False)
    status = db.Column(Enum(PluginStatus), nullable=False, default=PluginStatus.AVAILABLE)
    
    # Plugin metadata
    capabilities = db.Column(db.JSON)  # List of capabilities provided
    dependencies = db.Column(db.JSON)  # List of dependencies
    entry_point = db.Column(db.String(200))
    config_schema = db.Column(db.JSON)
    
    # Installation information
    install_path = db.Column(db.String(500))
    installed_at = db.Column(db.DateTime)
    last_updated = db.Column(db.DateTime)
    
    # Compatibility information
    min_swarm_director_version = db.Column(db.String(20), default="1.0.0")
    max_swarm_director_version = db.Column(db.String(20))
    python_version = db.Column(db.String(20), default=">=3.8")
    
    # Additional metadata
    tags = db.Column(db.JSON)  # List of tags
    license = db.Column(db.String(50), default="MIT")
    homepage = db.Column(db.String(200))
    repository = db.Column(db.String(200))
    
    # Indexes for efficient queries
    __table_args__ = (
        Index('idx_plugin_type_status', 'plugin_type', 'status'),
        Index('idx_plugin_name_version', 'name', 'version'),
        Index('idx_plugin_installed_at', 'installed_at'),
    )
    
    def __repr__(self):
        return f'<PluginRecord {self.name} v{self.version} {self.status.value}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'plugin_type': self.plugin_type.value,
            'status': self.status.value,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        })
        return data


class PluginInstallation(BaseModel):
    """Database model for tracking plugin installation history"""
    __tablename__ = 'plugin_installations'
    
    # Installation details
    plugin_record_id = db.Column(db.Integer, db.ForeignKey('plugin_records.id'), nullable=False)
    installation_type = db.Column(db.String(50), nullable=False)  # 'install', 'update', 'uninstall'
    
    # Installation status
    status = db.Column(db.String(50), nullable=False)  # 'started', 'completed', 'failed'
    started_at = db.Column(db.DateTime, default=datetime.utcnow)
    completed_at = db.Column(db.DateTime)
    
    # Installation details
    dependencies_installed = db.Column(db.JSON)  # List of dependencies installed
    installation_log = db.Column(db.Text)  # Installation log
    error_details = db.Column(db.Text)  # Error details if failed
    
    # Relationships
    plugin_record = db.relationship('PluginRecord', backref='installations')
    
    # Indexes
    __table_args__ = (
        Index('idx_installation_plugin_started', 'plugin_record_id', 'started_at'),
        Index('idx_installation_status', 'status'),
    )
    
    def __repr__(self):
        return f'<PluginInstallation {self.plugin_record_id} {self.installation_type} {self.status}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        })
        return data


class CapabilityGap(BaseModel):
    """Database model for tracking capability gaps and resolutions"""
    __tablename__ = 'capability_gaps'
    
    # Gap identification
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    capability_name = db.Column(db.String(100), nullable=False)
    capability_type = db.Column(db.String(50), nullable=False)
    severity = db.Column(db.String(20), nullable=False)  # 'critical', 'high', 'medium', 'low'
    
    # Gap details
    description = db.Column(db.Text)
    impact_score = db.Column(db.Float, default=0.0)
    effort_to_resolve = db.Column(db.String(20), default="medium")
    
    # Resolution information
    resolved = db.Column(db.Boolean, default=False)
    resolved_at = db.Column(db.DateTime)
    resolution_method = db.Column(db.String(50))  # 'plugin_install', 'agent_creation', 'manual'
    suggested_plugins = db.Column(db.JSON)  # List of suggested plugin names
    
    # Relationships
    task = db.relationship('Task', backref='capability_gaps')
    
    # Indexes
    __table_args__ = (
        Index('idx_gap_task_capability', 'task_id', 'capability_name'),
        Index('idx_gap_severity_resolved', 'severity', 'resolved'),
        Index('idx_gap_discovered_at', 'created_at'),
    )
    
    def __repr__(self):
        return f'<CapabilityGap {self.capability_name} {self.severity}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        data.update({
            'resolved_at': self.resolved_at.isoformat() if self.resolved_at else None
        })
        return data


class AgentTemplate(BaseModel):
    """Database model for storing agent templates"""
    __tablename__ = 'agent_templates'
    
    # Template identification
    name = db.Column(db.String(100), nullable=False, unique=True)
    description = db.Column(db.Text)
    version = db.Column(db.String(20), default="1.0.0")
    author = db.Column(db.String(100))
    
    # Template configuration
    agent_type = db.Column(db.String(50), nullable=False)  # Maps to AgentType enum
    base_class = db.Column(db.String(200), nullable=False)  # Fully qualified class name
    capabilities = db.Column(db.JSON)  # List of capabilities
    required_plugins = db.Column(db.JSON)  # List of required plugin names
    config_schema = db.Column(db.JSON)  # Configuration schema
    initialization_params = db.Column(db.JSON)  # Default initialization parameters
    
    # Template metadata
    tags = db.Column(db.JSON)  # List of tags
    is_active = db.Column(db.Boolean, default=True)
    usage_count = db.Column(db.Integer, default=0)  # How many times used
    
    # Indexes
    __table_args__ = (
        Index('idx_template_name_version', 'name', 'version'),
        Index('idx_template_agent_type', 'agent_type'),
        Index('idx_template_active', 'is_active'),
    )
    
    def __repr__(self):
        return f'<AgentTemplate {self.name} v{self.version}>'
    
    def to_dict(self):
        """Convert to dictionary"""
        data = super().to_dict()
        return data
