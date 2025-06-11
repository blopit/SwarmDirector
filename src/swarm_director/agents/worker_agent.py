"""
Worker agent implementation for SwarmDirector
"""

from typing import Dict, List, Any
from .base_agent import BaseAgent
from ..models.task import Task, TaskStatus
from ..models.agent import Agent
from utils.logging import log_agent_action

class WorkerAgent(BaseAgent):
    """Worker agent that executes specific tasks"""
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        self.specializations = db_agent.capabilities or []
        
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute a specific task"""
        log_agent_action(self.name, f"Starting task execution: {task.title}")
        
        try:
            # Mark task as in progress
            task.start_progress()
            
            # Execute based on task type or content
            result = self._perform_task_execution(task)
            
            # Mark task as completed
            if result.get("status") == "success":
                task.complete_task(result)
                log_agent_action(self.name, f"Completed task: {task.title}")
            else:
                task.fail_task(result.get("error", "Unknown error"))
                log_agent_action(self.name, f"Failed task: {task.title}")
            
            return result
            
        except Exception as e:
            error_msg = f"Error executing task: {str(e)}"
            task.fail_task(error_msg)
            log_agent_action(self.name, error_msg)
            return {"status": "error", "error": error_msg}
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this worker can handle the given task"""
        # Check if any of the agent's capabilities match the task requirements
        task_text = (task.title + " " + (task.description or "")).lower()
        
        # If no specific capabilities, can handle general tasks
        if not self.specializations:
            return True
        
        # Check if any specialization matches the task
        for specialization in self.specializations:
            if specialization.lower() in task_text:
                return True
        
        # Check for common task types this worker can handle
        common_tasks = [
            "process", "analyze", "compute", "calculate", "generate",
            "create", "build", "develop", "implement", "execute"
        ]
        
        return any(task_type in task_text for task_type in common_tasks)
    
    def _perform_task_execution(self, task: Task) -> Dict[str, Any]:
        """Perform the actual task execution"""
        # This is a simplified implementation
        # In a real system, this would integrate with AutoGen or other AI frameworks
        
        task_type = self._identify_task_type(task)
        
        if task_type == "data_processing":
            return self._process_data_task(task)
        elif task_type == "analysis":
            return self._analyze_task(task)
        elif task_type == "generation":
            return self._generate_content_task(task)
        elif task_type == "computation":
            return self._compute_task(task)
        else:
            return self._execute_general_task(task)
    
    def _identify_task_type(self, task: Task) -> str:
        """Identify the type of task based on its content"""
        task_text = (task.title + " " + (task.description or "")).lower()
        
        if any(word in task_text for word in ["analyze", "analysis", "review", "examine"]):
            return "analysis"
        elif any(word in task_text for word in ["process", "transform", "convert", "parse"]):
            return "data_processing"
        elif any(word in task_text for word in ["generate", "create", "produce", "write"]):
            return "generation"
        elif any(word in task_text for word in ["calculate", "compute", "solve", "math"]):
            return "computation"
        else:
            return "general"
    
    def _process_data_task(self, task: Task) -> Dict[str, Any]:
        """Process a data-related task"""
        log_agent_action(self.name, "Processing data task")
        
        # Simulate data processing
        input_data = task.input_data or {}
        processed_data = {
            "processed": True,
            "input_size": len(str(input_data)),
            "processing_time": "2.5 seconds",
            "output": "Processed data result"
        }
        
        return {
            "status": "success",
            "task_type": "data_processing",
            "result": processed_data
        }
    
    def _analyze_task(self, task: Task) -> Dict[str, Any]:
        """Perform an analysis task"""
        log_agent_action(self.name, "Performing analysis task")
        
        # Simulate analysis
        analysis_result = {
            "analysis_complete": True,
            "findings": [
                "Key pattern identified",
                "Anomaly detected in data",
                "Trend shows positive growth"
            ],
            "confidence_score": 0.85,
            "recommendations": [
                "Continue current approach",
                "Monitor for changes"
            ]
        }
        
        return {
            "status": "success",
            "task_type": "analysis",
            "result": analysis_result
        }
    
    def _generate_content_task(self, task: Task) -> Dict[str, Any]:
        """Generate content for a task"""
        log_agent_action(self.name, "Generating content")
        
        # Simulate content generation
        generated_content = {
            "content_type": "text",
            "content": f"Generated content for task: {task.title}",
            "word_count": 150,
            "quality_score": 0.9
        }
        
        return {
            "status": "success",
            "task_type": "generation",
            "result": generated_content
        }
    
    def _compute_task(self, task: Task) -> Dict[str, Any]:
        """Perform a computation task"""
        log_agent_action(self.name, "Performing computation")
        
        # Simulate computation
        computation_result = {
            "calculation_complete": True,
            "result_value": 42.0,
            "computation_time": "1.2 seconds",
            "accuracy": "high"
        }
        
        return {
            "status": "success",
            "task_type": "computation",
            "result": computation_result
        }
    
    def _execute_general_task(self, task: Task) -> Dict[str, Any]:
        """Execute a general task"""
        log_agent_action(self.name, "Executing general task")
        
        # Simulate general task execution
        general_result = {
            "task_executed": True,
            "execution_method": "general_processing",
            "output": f"Completed general task: {task.title}",
            "success": True
        }
        
        return {
            "status": "success",
            "task_type": "general",
            "result": general_result
        }
    
    def add_specialization(self, specialization: str):
        """Add a new specialization to this worker"""
        if specialization not in self.specializations:
            self.specializations.append(specialization)
            self.db_agent.capabilities = self.specializations
            self.db_agent.save()
            
            log_agent_action(self.name, f"Added specialization: {specialization}")
    
    def remove_specialization(self, specialization: str):
        """Remove a specialization from this worker"""
        if specialization in self.specializations:
            self.specializations.remove(specialization)
            self.db_agent.capabilities = self.specializations
            self.db_agent.save()
            
            log_agent_action(self.name, f"Removed specialization: {specialization}")
    
    def get_specializations(self) -> List[str]:
        """Get all specializations of this worker"""
        return self.specializations.copy()
    
    def can_learn_from_task(self, task: Task) -> bool:
        """Check if this worker can learn new capabilities from a task"""
        # Simple learning mechanism - can learn if task is similar to existing capabilities
        task_text = (task.title + " " + (task.description or "")).lower()
        
        for specialization in self.specializations:
            if any(word in specialization.lower() for word in task_text.split()):
                return True
        
        return False
    
    def learn_from_completed_task(self, task: Task):
        """Learn new capabilities from a completed task"""
        if self.can_learn_from_task(task) and task.status == TaskStatus.COMPLETED:
            # Extract potential new capabilities from the task
            task_keywords = (task.title + " " + (task.description or "")).lower().split()
            
            # Add relevant keywords as new capabilities
            for keyword in task_keywords:
                if len(keyword) > 3 and keyword not in [spec.lower() for spec in self.specializations]:
                    self.add_specialization(keyword.capitalize())
                    break  # Add only one new capability per task 