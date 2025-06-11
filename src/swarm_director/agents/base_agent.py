"""
Base agent class for SwarmDirector
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any
from ..models.agent import Agent, AgentStatus
from ..models.task import Task
from ..utils.logging import log_agent_action

class BaseAgent(ABC):
    """Abstract base class for all agents in the swarm"""
    
    def __init__(self, db_agent: Agent):
        """Initialize the agent with database model"""
        self.db_agent = db_agent
        self.agent_id = db_agent.id
        self.name = db_agent.name
        self.status = db_agent.status
        self.capabilities = db_agent.capabilities or []
        
    @abstractmethod
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a given task and return results"""
        pass
    
    @abstractmethod
    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task"""
        pass
    
    def update_status(self, new_status: AgentStatus):
        """Update the agent's status"""
        old_status = self.status
        self.status = new_status
        self.db_agent.status = new_status
        self.db_agent.save()
        
        log_agent_action(self.name, f"Status changed from {old_status.value} to {new_status.value}")
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get performance metrics for this agent"""
        total_tasks = len(self.get_assigned_tasks())
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': self.db_agent.tasks_completed,
            'success_rate': self.db_agent.success_rate,
            'current_status': self.status.value,
            'capabilities': self.capabilities
        }
    
    def get_assigned_tasks(self) -> List[Task]:
        """Get all tasks assigned to this agent"""
        return Task.query.filter_by(assigned_agent_id=self.agent_id).all()
    
    def is_available(self) -> bool:
        """Check if the agent is available for new tasks"""
        return self.status in [AgentStatus.IDLE, AgentStatus.ACTIVE] 