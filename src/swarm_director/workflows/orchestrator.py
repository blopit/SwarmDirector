"""
Workflow Orchestrator
Coordinates multi-agent workflows with state management and error recovery
"""

import asyncio
import threading
import uuid
from typing import Dict, List, Any, Optional, Callable, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass
from enum import Enum
import logging

from .state_manager import WorkflowStateManager, WorkflowStatus, WorkflowState
from .workflow_context import WorkflowContext, ContextScope
from ..models.task import Task, TaskStatus
from ..models.agent import Agent
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class ExecutionStrategy(Enum):
    """Workflow execution strategies"""
    SEQUENTIAL = "sequential"      # Execute agents one after another
    PARALLEL = "parallel"         # Execute compatible agents in parallel
    CONDITIONAL = "conditional"   # Execute based on conditions
    PIPELINE = "pipeline"         # Pipeline execution with data flow

@dataclass
class WorkflowStep:
    """Represents a single step in a workflow"""
    step_id: str
    agent_name: str
    task_data: Dict[str, Any]
    dependencies: List[str] = None
    conditions: List[Callable] = None
    timeout_seconds: Optional[int] = None
    retry_count: int = 0
    max_retries: int = 3
    
    def __post_init__(self):
        if self.dependencies is None:
            self.dependencies = []
        if self.conditions is None:
            self.conditions = []

@dataclass
class WorkflowDefinition:
    """Complete workflow definition with steps and configuration"""
    workflow_id: str
    name: str
    description: str
    steps: List[WorkflowStep]
    execution_strategy: ExecutionStrategy = ExecutionStrategy.SEQUENTIAL
    timeout_minutes: int = 30
    max_parallel_agents: int = 3
    enable_rollback: bool = True
    rollback_on_failure: bool = True

class WorkflowOrchestrator:
    """
    Main orchestrator for managing multi-agent workflows
    Provides coordination, state management, and error recovery
    """
    
    def __init__(self):
        self.state_manager = WorkflowStateManager()
        self.active_contexts: Dict[str, WorkflowContext] = {}
        self.workflow_definitions: Dict[str, WorkflowDefinition] = {}
        self.agent_registry: Dict[str, Any] = {}  # Will hold agent instances
        self._execution_lock = threading.RLock()
        self._active_workflows: Dict[str, asyncio.Task] = {}
        
        # Event handlers
        self.on_workflow_started: Optional[Callable] = None
        self.on_workflow_completed: Optional[Callable] = None
        self.on_workflow_failed: Optional[Callable] = None
        self.on_step_completed: Optional[Callable] = None
        self.on_step_failed: Optional[Callable] = None
        
    def register_agent(self, agent_name: str, agent_instance: Any):
        """Register an agent instance for workflow execution"""
        self.agent_registry[agent_name] = agent_instance
        logger.info(f"Registered agent: {agent_name}")
    
    def unregister_agent(self, agent_name: str):
        """Unregister an agent instance"""
        if agent_name in self.agent_registry:
            del self.agent_registry[agent_name]
            logger.info(f"Unregistered agent: {agent_name}")
    
    def define_workflow(self, workflow_def: WorkflowDefinition):
        """Define a new workflow"""
        self.workflow_definitions[workflow_def.workflow_id] = workflow_def
        logger.info(f"Defined workflow: {workflow_def.workflow_id}")
    
    async def execute_workflow(self, workflow_id: str, input_data: Dict[str, Any] = None,
                             execution_id: str = None) -> Dict[str, Any]:
        """
        Execute a defined workflow with given input data
        Returns workflow execution results
        """
        execution_id = execution_id or f"{workflow_id}_{uuid.uuid4().hex[:8]}"
        
        # Get workflow definition
        workflow_def = self.workflow_definitions.get(workflow_id)
        if not workflow_def:
            raise ValueError(f"Workflow not found: {workflow_id}")
        
        # Create workflow state and context
        state = self.state_manager.create_workflow(
            execution_id, 
            input_data or {}, 
            len(workflow_def.steps)
        )
        context = WorkflowContext(execution_id)
        self.active_contexts[execution_id] = context
        
        # Set up context with input data
        if input_data:
            for key, value in input_data.items():
                context.set(key, value, ContextScope.WORKFLOW)
        
        try:
            logger.info(f"Starting workflow execution: {execution_id}")
            self.state_manager.update_workflow_status(
                execution_id, 
                WorkflowStatus.RUNNING,
                reason="Workflow execution started"
            )
            
            if self.on_workflow_started:
                self.on_workflow_started(execution_id, state)
            
            # Execute based on strategy
            if workflow_def.execution_strategy == ExecutionStrategy.SEQUENTIAL:
                result = await self._execute_sequential(workflow_def, execution_id, context)
            elif workflow_def.execution_strategy == ExecutionStrategy.PARALLEL:
                result = await self._execute_parallel(workflow_def, execution_id, context)
            elif workflow_def.execution_strategy == ExecutionStrategy.PIPELINE:
                result = await self._execute_pipeline(workflow_def, execution_id, context)
            else:
                raise ValueError(f"Unsupported execution strategy: {workflow_def.execution_strategy}")
            
            # Mark as completed
            self.state_manager.update_workflow_status(
                execution_id,
                WorkflowStatus.COMPLETED,
                reason="All steps completed successfully"
            )
            
            if self.on_workflow_completed:
                self.on_workflow_completed(execution_id, result)
            
            logger.info(f"Workflow completed successfully: {execution_id}")
            return {
                "status": "success",
                "execution_id": execution_id,
                "result": result,
                "execution_time": state.get_execution_duration()
            }
            
        except Exception as e:
            logger.error(f"Workflow execution failed: {execution_id}, error: {e}")
            
            # Mark as failed
            self.state_manager.update_workflow_status(
                execution_id,
                WorkflowStatus.FAILED,
                reason=f"Execution failed: {str(e)}"
            )
            
            # Attempt rollback if enabled
            if workflow_def.enable_rollback and workflow_def.rollback_on_failure:
                await self._rollback_workflow(execution_id, context)
            
            if self.on_workflow_failed:
                self.on_workflow_failed(execution_id, e)
            
            return {
                "status": "error",
                "execution_id": execution_id,
                "error": str(e),
                "execution_time": state.get_execution_duration()
            }
        
        finally:
            # Cleanup
            if execution_id in self.active_contexts:
                del self.active_contexts[execution_id]
    
    async def _execute_sequential(self, workflow_def: WorkflowDefinition, 
                                execution_id: str, context: WorkflowContext) -> Dict[str, Any]:
        """Execute workflow steps sequentially"""
        results = {}
        
        for step in workflow_def.steps:
            # Check dependencies
            if not self._check_dependencies(step, results):
                raise Exception(f"Dependencies not met for step: {step.step_id}")
            
            # Check conditions
            if not self._check_conditions(step, context, execution_id):
                logger.info(f"Conditions not met for step {step.step_id}, skipping")
                continue
            
            # Execute step
            try:
                step_result = await self._execute_step(step, execution_id, context)
                results[step.step_id] = step_result
                
                self.state_manager.complete_task(execution_id, step.step_id)
                
                if self.on_step_completed:
                    self.on_step_completed(execution_id, step.step_id, step_result)
                    
            except Exception as e:
                logger.error(f"Step failed: {step.step_id}, error: {e}")
                
                self.state_manager.fail_task(execution_id, step.step_id, {"error": str(e)})
                
                if self.on_step_failed:
                    self.on_step_failed(execution_id, step.step_id, e)
                
                # Retry if configured
                if step.retry_count < step.max_retries:
                    step.retry_count += 1
                    logger.info(f"Retrying step {step.step_id}, attempt {step.retry_count}")
                    continue
                else:
                    raise e
        
        return results
    
    async def _execute_parallel(self, workflow_def: WorkflowDefinition,
                              execution_id: str, context: WorkflowContext) -> Dict[str, Any]:
        """Execute compatible workflow steps in parallel"""
        results = {}
        completed_steps = set()
        
        while len(completed_steps) < len(workflow_def.steps):
            # Find steps that can be executed (dependencies met)
            ready_steps = []
            for step in workflow_def.steps:
                if (step.step_id not in completed_steps and 
                    self._check_dependencies(step, results) and
                    self._check_conditions(step, context, execution_id)):
                    ready_steps.append(step)
            
            if not ready_steps:
                # Check if we're deadlocked
                remaining_steps = [s for s in workflow_def.steps if s.step_id not in completed_steps]
                if remaining_steps:
                    raise Exception("Workflow deadlock: No steps can be executed")
                break
            
            # Execute ready steps in parallel (limited by max_parallel_agents)
            parallel_limit = min(len(ready_steps), workflow_def.max_parallel_agents)
            batch = ready_steps[:parallel_limit]
            
            # Create tasks for parallel execution
            tasks = []
            for step in batch:
                task = asyncio.create_task(
                    self._execute_step_with_retry(step, execution_id, context)
                )
                tasks.append((step, task))
            
            # Wait for completion
            for step, task in tasks:
                try:
                    step_result = await task
                    results[step.step_id] = step_result
                    completed_steps.add(step.step_id)
                    
                    self.state_manager.complete_task(execution_id, step.step_id)
                    
                    if self.on_step_completed:
                        self.on_step_completed(execution_id, step.step_id, step_result)
                        
                except Exception as e:
                    logger.error(f"Parallel step failed: {step.step_id}, error: {e}")
                    self.state_manager.fail_task(execution_id, step.step_id, {"error": str(e)})
                    
                    if self.on_step_failed:
                        self.on_step_failed(execution_id, step.step_id, e)
                    
                    raise e
        
        return results
    
    async def _execute_pipeline(self, workflow_def: WorkflowDefinition,
                              execution_id: str, context: WorkflowContext) -> Dict[str, Any]:
        """Execute workflow as a pipeline with data flowing between steps"""
        results = {}
        pipeline_data = context.get_all_for_agent("orchestrator", execution_id)
        
        for step in workflow_def.steps:
            # Pass previous results as input to next step
            step_input = {**step.task_data, "pipeline_data": pipeline_data}
            
            try:
                step_result = await self._execute_step_with_input(
                    step, execution_id, context, step_input
                )
                results[step.step_id] = step_result
                
                # Update pipeline data for next step
                if isinstance(step_result, dict):
                    pipeline_data.update(step_result)
                    # Store in context for next steps
                    for key, value in step_result.items():
                        context.set(f"pipeline_{key}", value, ContextScope.WORKFLOW)
                
                self.state_manager.complete_task(execution_id, step.step_id)
                
                if self.on_step_completed:
                    self.on_step_completed(execution_id, step.step_id, step_result)
                    
            except Exception as e:
                logger.error(f"Pipeline step failed: {step.step_id}, error: {e}")
                self.state_manager.fail_task(execution_id, step.step_id, {"error": str(e)})
                
                if self.on_step_failed:
                    self.on_step_failed(execution_id, step.step_id, e)
                
                raise e
        
        return results
    
    async def _execute_step(self, step: WorkflowStep, execution_id: str, 
                          context: WorkflowContext) -> Dict[str, Any]:
        """Execute a single workflow step"""
        return await self._execute_step_with_input(step, execution_id, context, step.task_data)
    
    async def _execute_step_with_input(self, step: WorkflowStep, execution_id: str,
                                     context: WorkflowContext, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a step with specific input data"""
        agent = self.agent_registry.get(step.agent_name)
        if not agent:
            raise Exception(f"Agent not found: {step.agent_name}")
        
        # Add agent to active list
        self.state_manager.add_active_agent(execution_id, step.agent_name)
        
        try:
            # Create task object for agent execution
            task = Task(
                title=f"Workflow step: {step.step_id}",
                description=f"Executing step {step.step_id} in workflow {execution_id}",
                input_data=input_data,
                status=TaskStatus.PENDING
            )
            
            # Execute with timeout if specified
            if step.timeout_seconds:
                result = await asyncio.wait_for(
                    self._execute_agent_task(agent, task, context, execution_id),
                    timeout=step.timeout_seconds
                )
            else:
                result = await self._execute_agent_task(agent, task, context, execution_id)
            
            return result
            
        finally:
            # Remove agent from active list
            self.state_manager.remove_active_agent(execution_id, step.agent_name)
    
    async def _execute_step_with_retry(self, step: WorkflowStep, execution_id: str,
                                     context: WorkflowContext) -> Dict[str, Any]:
        """Execute a step with retry logic"""
        last_exception = None
        
        for attempt in range(step.max_retries + 1):
            try:
                return await self._execute_step(step, execution_id, context)
            except Exception as e:
                last_exception = e
                step.retry_count = attempt + 1
                
                if attempt < step.max_retries:
                    logger.warning(f"Step {step.step_id} failed, retrying (attempt {attempt + 1})")
                    await asyncio.sleep(2 ** attempt)  # Exponential backoff
                else:
                    logger.error(f"Step {step.step_id} failed after {step.max_retries} retries")
        
        raise last_exception
    
    async def _execute_agent_task(self, agent: Any, task: Task, 
                                context: WorkflowContext, execution_id: str) -> Dict[str, Any]:
        """Execute task on agent with context support"""
        # Check if agent supports execute_task method
        if hasattr(agent, 'execute_task'):
            # For synchronous agents, run in thread pool
            if not asyncio.iscoroutinefunction(agent.execute_task):
                loop = asyncio.get_event_loop()
                return await loop.run_in_executor(None, agent.execute_task, task)
            else:
                return await agent.execute_task(task)
        else:
            raise Exception(f"Agent {agent.__class__.__name__} does not support execute_task method")
    
    def _check_dependencies(self, step: WorkflowStep, completed_results: Dict[str, Any]) -> bool:
        """Check if step dependencies are satisfied"""
        for dep in step.dependencies:
            if dep not in completed_results:
                return False
        return True
    
    def _check_conditions(self, step: WorkflowStep, context: WorkflowContext, execution_id: str) -> bool:
        """Check if step conditions are satisfied"""
        for condition in step.conditions:
            try:
                if not condition(context, execution_id):
                    return False
            except Exception as e:
                logger.warning(f"Condition check failed for step {step.step_id}: {e}")
                return False
        return True
    
    async def _rollback_workflow(self, execution_id: str, context: WorkflowContext):
        """Attempt to rollback workflow changes"""
        logger.info(f"Attempting rollback for workflow: {execution_id}")
        
        state = self.state_manager.get_workflow_state(execution_id)
        if not state:
            return
        
        # For now, this is a placeholder - specific rollback logic would be implemented
        # based on the types of operations performed
        rollback_data = {
            "rollback_timestamp": datetime.utcnow().isoformat(),
            "completed_tasks": state.completed_tasks,
            "rollback_reason": "Workflow execution failed"
        }
        
        context.set("rollback_info", rollback_data, ContextScope.WORKFLOW)
        logger.info(f"Rollback completed for workflow: {execution_id}")
    
    def get_workflow_status(self, execution_id: str) -> Optional[Dict[str, Any]]:
        """Get current workflow status and progress"""
        state = self.state_manager.get_workflow_state(execution_id)
        if not state:
            return None
        
        return state.to_dict()
    
    def pause_workflow(self, execution_id: str) -> bool:
        """Pause a running workflow"""
        return self.state_manager.update_workflow_status(
            execution_id, 
            WorkflowStatus.PAUSED,
            reason="Workflow paused by user request"
        )
    
    def resume_workflow(self, execution_id: str) -> bool:
        """Resume a paused workflow"""
        return self.state_manager.update_workflow_status(
            execution_id,
            WorkflowStatus.RUNNING,
            reason="Workflow resumed by user request"
        )
    
    def cancel_workflow(self, execution_id: str) -> bool:
        """Cancel a running workflow"""
        return self.state_manager.update_workflow_status(
            execution_id,
            WorkflowStatus.CANCELLED,
            reason="Workflow cancelled by user request"
        ) 