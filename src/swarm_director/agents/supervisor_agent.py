"""
Supervisor agent implementation for SwarmDirector
"""

from typing import Dict, List, Any
from .base_agent import BaseAgent
from ..models.task import Task, TaskStatus, TaskPriority
from ..models.agent import Agent, AgentType
from utils.logging import log_agent_action

class SupervisorAgent(BaseAgent):
    """Supervisor agent that can coordinate other agents and manage tasks"""
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        self.subordinates = []  # List of agents under supervision
        
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a supervisory task"""
        log_agent_action(self.name, f"Executing supervisory task: {task.title}")
        
        try:
            # Supervisor tasks typically involve coordination and management
            if task.title.lower().startswith("coordinate"):
                return self._coordinate_task(task)
            elif task.title.lower().startswith("assign"):
                return self._assign_task(task)
            elif task.title.lower().startswith("monitor"):
                return self._monitor_progress(task)
            else:
                return self._delegate_task(task)
                
        except Exception as e:
            error_msg = f"Error executing supervisory task: {str(e)}"
            log_agent_action(self.name, error_msg)
            return {"status": "error", "error": error_msg}
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this supervisor can handle the given task"""
        supervisory_keywords = [
            "coordinate", "assign", "monitor", "manage", "oversee", 
            "supervise", "delegate", "plan", "organize"
        ]
        
        task_text = (task.title + " " + (task.description or "")).lower()
        return any(keyword in task_text for keyword in supervisory_keywords)
    
    def _coordinate_task(self, task: Task) -> Dict[str, Any]:
        """Coordinate a multi-agent task"""
        # Break down the task and assign to subordinates
        subtasks = self._break_down_task(task)
        assignments = []
        
        for subtask in subtasks:
            best_agent = self._find_best_agent_for_task(subtask)
            if best_agent:
                subtask.assign_to_agent(best_agent)
                assignments.append({
                    "subtask_id": subtask.id,
                    "assigned_to": best_agent.name
                })
        
        return {
            "status": "coordinated",
            "assignments": assignments,
            "total_subtasks": len(subtasks)
        }
    
    def _assign_task(self, task: Task) -> Dict[str, Any]:
        """Assign a task to the most suitable subordinate"""
        best_agent = self._find_best_agent_for_task(task)
        
        if best_agent:
            task.assign_to_agent(best_agent)
            return {
                "status": "assigned",
                "assigned_to": best_agent.name,
                "agent_id": best_agent.id
            }
        else:
            return {
                "status": "unassigned",
                "reason": "No suitable agent available"
            }
    
    def _monitor_progress(self, task: Task) -> Dict[str, Any]:
        """Monitor progress of supervised tasks"""
        subordinate_tasks = []
        
        for subordinate in self.subordinates:
            tasks = subordinate.get_assigned_tasks()
            for t in tasks:
                subordinate_tasks.append({
                    "task_id": t.id,
                    "title": t.title,
                    "status": t.status.value,
                    "agent": subordinate.name,
                    "progress": t.progress_percentage
                })
        
        return {
            "status": "monitoring",
            "supervised_tasks": subordinate_tasks,
            "total_tasks": len(subordinate_tasks)
        }
    
    def _delegate_task(self, task: Task) -> Dict[str, Any]:
        """Delegate a task to a subordinate agent"""
        # Find the best agent for this task
        best_agent = self._find_best_agent_for_task(task)
        
        if best_agent:
            # Create a delegation record
            task.assign_to_agent(best_agent)
            return {
                "status": "delegated",
                "delegated_to": best_agent.name,
                "task_id": task.id
            }
        else:
            # No suitable agent, supervisor handles it directly
            return {
                "status": "handled_directly",
                "reason": "No suitable subordinate available"
            }
    
    def _break_down_task(self, task: Task) -> List[Task]:
        """Break down a complex task into subtasks"""
        # This is a simplified implementation
        # In a real system, this would use AI to intelligently break down tasks
        subtasks = []
        
        if task.description:
            # Create subtasks based on task description
            steps = task.description.split('\n')
            for i, step in enumerate(steps[:5]):  # Limit to 5 subtasks
                if step.strip():
                    subtask = Task(
                        title=f"{task.title} - Step {i+1}",
                        description=step.strip(),
                        parent_task_id=task.id,
                        priority=task.priority,
                        status=TaskStatus.PENDING
                    )
                    subtask.save()
                    subtasks.append(subtask)
        
        return subtasks
    
    def _find_best_agent_for_task(self, task: Task) -> Agent:
        """Find the best subordinate agent for a given task"""
        if not self.subordinates:
            return None
        
        # Simple scoring system based on availability and capabilities
        best_agent = None
        best_score = -1
        
        for agent in self.subordinates:
            if not agent.is_available():
                continue
                
            score = 0
            
            # Score based on workload (lower is better)
            workload = len(agent.get_active_tasks())
            score += max(0, 10 - workload)
            
            # Score based on relevant capabilities
            task_keywords = (task.title + " " + (task.description or "")).lower().split()
            for capability in agent.capabilities:
                if any(keyword in capability.lower() for keyword in task_keywords):
                    score += 5
            
            if score > best_score:
                best_score = score
                best_agent = agent
        
        return best_agent.db_agent if best_agent else None
    
    def add_subordinate(self, agent: BaseAgent):
        """Add a subordinate agent"""
        if agent not in self.subordinates:
            self.subordinates.append(agent)
            agent.db_agent.parent_id = self.agent_id
            agent.db_agent.save()
            
            log_agent_action(self.name, f"Added subordinate: {agent.name}")
    
    def remove_subordinate(self, agent: BaseAgent):
        """Remove a subordinate agent"""
        if agent in self.subordinates:
            self.subordinates.remove(agent)
            agent.db_agent.parent_id = None
            agent.db_agent.save()
            
            log_agent_action(self.name, f"Removed subordinate: {agent.name}")
    
    def get_subordinates(self) -> List[BaseAgent]:
        """Get all subordinate agents"""
        return self.subordinates.copy()
    
    def get_team_performance(self) -> Dict[str, Any]:
        """Get performance metrics for the entire team"""
        team_metrics = {
            "supervisor": self.get_performance_metrics(),
            "subordinates": [],
            "team_totals": {
                "total_agents": len(self.subordinates) + 1,
                "total_tasks": 0,
                "completed_tasks": 0
            }
        }
        
        for agent in self.subordinates:
            metrics = agent.get_performance_metrics()
            team_metrics["subordinates"].append(metrics)
            team_metrics["team_totals"]["total_tasks"] += metrics["total_tasks"]
            team_metrics["team_totals"]["completed_tasks"] += metrics["completed_tasks"]
        
        return team_metrics 