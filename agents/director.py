"""
Director agent implementation for SwarmDirector
The DirectorAgent is the main orchestrator that routes tasks to appropriate department agents
based on intent classification and manages the overall workflow.
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .supervisor_agent import SupervisorAgent
from models.task import Task, TaskStatus, TaskPriority
from models.agent import Agent, AgentType, AgentStatus
from utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class DirectorAgent(SupervisorAgent):
    """
    Director agent that routes tasks to appropriate department agents
    based on intent classification and manages the overall workflow
    """
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        self.department_agents = {}  # Maps department names to agent instances
        self.intent_keywords = self._initialize_intent_keywords()
        self.routing_stats = {
            'total_routed': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'department_counts': {}
        }
        
    def _initialize_intent_keywords(self) -> Dict[str, List[str]]:
        """Initialize keyword mappings for intent classification"""
        return {
            'communications': [
                'email', 'message', 'communication', 'send', 'draft', 'write',
                'compose', 'letter', 'memo', 'notification', 'announce',
                'contact', 'reply', 'response', 'correspondence'
            ],
            'analysis': [
                'analyze', 'analysis', 'review', 'evaluate', 'assess', 'examine', 'study',
                'research', 'investigate', 'compare', 'audit', 'inspect',
                'critique', 'feedback', 'opinion', 'recommendation'
            ],
            'automation': [
                'automate', 'schedule', 'trigger', 'batch', 'process',
                'workflow', 'pipeline', 'routine', 'recurring', 'systematic'
            ],
            'coordination': [
                'coordinate', 'manage', 'organize', 'plan', 'delegate',
                'assign', 'supervise', 'oversee', 'monitor', 'track'
            ]
        }
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task by routing it to the appropriate department agent
        or handling it directly if no suitable agent is found
        """
        log_agent_action(self.name, f"Processing task: {task.title}")
        
        try:
            # Classify the intent
            intent = self.classify_intent(task)
            
            # Route to appropriate department
            result = self.route_task(task, intent)
            
            # Update routing statistics
            self._update_routing_stats(intent, result['status'] == 'success')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing task: {str(e)}"
            logger.error(error_msg)
            log_agent_action(self.name, error_msg)
            self._update_routing_stats('error', False)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def classify_intent(self, task: Task) -> str:
        """
        Classify the intent of a task using keyword-based classification
        Returns the department name that should handle this task
        """
        task_text = (task.title + " " + (task.description or "")).lower()
        
        # Also include input_data type if available
        if hasattr(task, 'input_data') and task.input_data and 'type' in task.input_data:
            task_text += " " + task.input_data['type'].lower()
        
        intent_scores = {}
        
        # Score each department based on keyword matches
        for department, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in task_text:
                    score += 1
            intent_scores[department] = score
        
        # Find the department with the highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        # If no keywords match, default to coordination
        if best_intent[1] == 0:
            return 'coordination'
        
        log_agent_action(self.name, f"Classified intent as '{best_intent[0]}' (score: {best_intent[1]})")
        return best_intent[0]
    
    def route_task(self, task: Task, intent: str) -> Dict[str, Any]:
        """
        Route a task to the appropriate department agent based on intent
        """
        # Check if we have an agent for this department
        if intent in self.department_agents:
            agent = self.department_agents[intent]
            
            # Check if the agent is available
            if agent.is_available():
                try:
                    # Assign the task to the agent
                    task.assign_to_agent(agent.db_agent)
                    
                    # Execute the task through the agent
                    result = agent.execute_task(task)
                    
                    log_agent_action(self.name, f"Successfully routed task {task.id} to {intent} department")
                    
                    return {
                        "status": "success",
                        "routed_to": intent,
                        "agent_name": agent.name,
                        "task_id": task.id,
                        "result": result
                    }
                    
                except Exception as e:
                    error_msg = f"Error executing task through {intent} agent: {str(e)}"
                    logger.error(error_msg)
                    return {
                        "status": "execution_error",
                        "department": intent,
                        "error": error_msg,
                        "task_id": task.id
                    }
            else:
                # Agent is not available, handle directly or queue
                return self._handle_unavailable_agent(task, intent)
        else:
            # No agent available for this department, handle directly
            return self._handle_directly(task, intent)
    
    def _handle_unavailable_agent(self, task: Task, department: str) -> Dict[str, Any]:
        """Handle cases where the department agent is unavailable"""
        log_agent_action(self.name, f"Department agent '{department}' is unavailable, handling directly")
        
        # For now, handle directly. In future, could implement queuing
        return self._handle_directly(task, department)
    
    def _handle_directly(self, task: Task, intended_department: str) -> Dict[str, Any]:
        """Handle a task directly when no suitable agent is available"""
        log_agent_action(self.name, f"Handling task directly (intended for {intended_department})")
        
        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        task.save()
        
        # Simple direct handling - in a real system this would be more sophisticated
        result = {
            "message": f"Task handled directly by DirectorAgent",
            "intended_department": intended_department,
            "handling_method": "direct",
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Mark task as completed
        task.complete_task(output_data=result)
        
        return {
            "status": "handled_directly",
            "department": intended_department,
            "task_id": task.id,
            "result": result
        }
    
    def register_department_agent(self, department: str, agent):
        """Register a department agent for routing"""
        self.department_agents[department] = agent
        log_agent_action(self.name, f"Registered {department} department agent: {agent.name}")
        
        # Initialize stats for this department
        if department not in self.routing_stats['department_counts']:
            self.routing_stats['department_counts'][department] = 0
    
    def unregister_department_agent(self, department: str):
        """Unregister a department agent"""
        if department in self.department_agents:
            agent_name = self.department_agents[department].name
            del self.department_agents[department]
            log_agent_action(self.name, f"Unregistered {department} department agent: {agent_name}")
    
    def _update_routing_stats(self, department: str, success: bool):
        """Update routing statistics"""
        self.routing_stats['total_routed'] += 1
        
        if success:
            self.routing_stats['successful_routes'] += 1
        else:
            self.routing_stats['failed_routes'] += 1
        
        if department in self.routing_stats['department_counts']:
            self.routing_stats['department_counts'][department] += 1
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            **self.routing_stats,
            'success_rate': (
                self.routing_stats['successful_routes'] / 
                max(1, self.routing_stats['total_routed'])
            ) * 100,
            'registered_departments': list(self.department_agents.keys())
        }
    
    def can_handle_task(self, task: Task) -> bool:
        """Director agent can handle any task by routing or direct handling"""
        return True
    
    def get_department_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered department agents"""
        status = {}
        
        for dept, agent in self.department_agents.items():
            status[dept] = {
                'name': agent.name,
                'status': agent.status.value,
                'available': agent.is_available(),
                'active_tasks': len(agent.get_assigned_tasks()),
                'performance': agent.get_performance_metrics()
            }
        
        return status 