"""
Agent model for the hierarchical AI agent system
"""

from .base import db, BaseModel
from sqlalchemy import Enum
import enum

class AgentType(enum.Enum):
    """Enumeration for agent types in the hierarchy"""
    SUPERVISOR = "supervisor"
    COORDINATOR = "coordinator" 
    WORKER = "worker"
    SPECIALIST = "specialist"

class AgentStatus(enum.Enum):
    """Enumeration for agent status"""
    ACTIVE = "active"
    IDLE = "idle"
    BUSY = "busy"
    ERROR = "error"
    OFFLINE = "offline"

class Agent(BaseModel):
    """Agent model representing an AI agent in the swarm"""
    __tablename__ = 'agents'
    
    # Basic agent information
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    agent_type = db.Column(Enum(AgentType), nullable=False, default=AgentType.WORKER)
    status = db.Column(Enum(AgentStatus), nullable=False, default=AgentStatus.IDLE)
    
    # Hierarchical relationships
    parent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    parent = db.relationship('Agent', remote_side='Agent.id', backref='children')
    
    # Agent capabilities and configuration
    capabilities = db.Column(db.JSON)  # Store agent capabilities as JSON
    config = db.Column(db.JSON)  # Store agent configuration as JSON
    
    # Performance metrics
    tasks_completed = db.Column(db.Integer, default=0)
    success_rate = db.Column(db.Float, default=0.0)
    average_response_time = db.Column(db.Float, default=0.0)
    
    # AutoGen specific fields
    autogen_config = db.Column(db.JSON)  # Store AutoGen agent configuration
    system_message = db.Column(db.Text)  # System message for the agent
    
    def __repr__(self):
        return f'<Agent {self.name} ({self.agent_type.value})>'
    
    def to_dict(self):
        """Convert agent to dictionary with relationships"""
        data = super().to_dict()
        data.update({
            'agent_type': self.agent_type.value,
            'status': self.status.value,
            'parent_id': self.parent_id,
            'children_count': len(self.children) if self.children else 0
        })
        return data
    
    def add_child(self, child_agent):
        """Add a child agent to this agent"""
        child_agent.parent_id = self.id
        child_agent.save()
    
    def get_hierarchy_level(self):
        """Get the level of this agent in the hierarchy (0 = root)"""
        level = 0
        current = self
        while current.parent_id:
            level += 1
            current = Agent.query.get(current.parent_id)
        return level
    
    def is_supervisor(self):
        """Check if this agent is a supervisor"""
        return self.agent_type == AgentType.SUPERVISOR
    
    def can_manage(self, other_agent):
        """Check if this agent can manage another agent"""
        if not self.is_supervisor():
            return False
        return other_agent.parent_id == self.id 