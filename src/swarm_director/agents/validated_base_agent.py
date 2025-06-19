"""
Validated Base Agent

Enhanced base agent that integrates with the hierarchical validation system
and plugin architecture.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
from datetime import datetime

from .base_agent import BaseAgent
from ..validation.validation_chain import ValidationChain, ValidationTier
from ..validation.validation_result import ValidationResult, ValidationStatus
from ..plugins.plugin_manager import PluginManager
from ..models.task import Task
from ..models.agent import Agent

logger = logging.getLogger(__name__)


class ValidatedBaseAgent(BaseAgent):
    """
    Enhanced base agent with validation and plugin integration
    """
    
    def __init__(self, db_agent: Agent, validation_chain: Optional[ValidationChain] = None,
                 plugin_manager: Optional[PluginManager] = None):
        super().__init__(db_agent)
        self.validation_chain = validation_chain
        self.plugin_manager = plugin_manager
        self.validation_tier = self._determine_validation_tier()
        self.execution_history: List[Dict[str, Any]] = []
        
    def _determine_validation_tier(self) -> ValidationTier:
        """Determine validation tier based on agent type"""
        if self.db_agent.agent_type.value == 'worker':
            return ValidationTier.TOOL
        elif self.db_agent.agent_type.value in ['coordinator', 'supervisor']:
            return ValidationTier.DEPARTMENT
        else:
            return ValidationTier.DIRECTOR
    
    async def execute_task_with_validation(self, task: Task) -> Dict[str, Any]:
        """
        Execute task with full validation chain integration
        """
        start_time = datetime.utcnow()
        execution_id = f"{task.id}_{self.agent_id}_{int(start_time.timestamp())}"
        
        logger.info(f"Starting validated execution for task {task.id} by agent {self.name}")
        
        try:
            # 1. Pre-execution validation
            pre_validation = await self._pre_execution_validation(task)
            if not pre_validation['valid']:
                return self._create_validation_failure_response(
                    task, "Pre-execution validation failed", pre_validation
                )
            
            # 2. Check capabilities and install plugins if needed
            capability_check = await self._check_and_resolve_capabilities(task)
            if not capability_check['sufficient']:
                if self.plugin_manager and self.plugin_manager.auto_install_enabled:
                    plugin_result = self.plugin_manager.process_task_with_plugins(task)
                    if not plugin_result['success']:
                        return self._create_capability_failure_response(task, plugin_result)
                else:
                    return self._create_capability_failure_response(task, capability_check)
            
            # 3. Execute the actual task
            execution_result = await self._execute_task_implementation(task)
            
            # 4. Post-execution validation
            if self.validation_chain:
                validation_result = await self.validation_chain.validate_task_output(
                    task, self.db_agent, execution_result, self.validation_tier
                )
                
                # Handle validation results
                if validation_result.status == ValidationStatus.FAILED:
                    return await self._handle_validation_failure(task, validation_result, execution_result)
                elif validation_result.status == ValidationStatus.REQUIRES_REVISION:
                    return await self._handle_validation_revision(task, validation_result, execution_result)
            
            # 5. Create success response
            response = self._create_success_response(task, execution_result, validation_result if self.validation_chain else None)
            
            # Log execution
            self._log_execution(execution_id, task, response, start_time)
            
            return response
            
        except Exception as e:
            logger.error(f"Error in validated execution for task {task.id}: {e}", exc_info=True)
            error_response = self._create_error_response(task, str(e))
            self._log_execution(execution_id, task, error_response, start_time)
            return error_response
    
    async def _pre_execution_validation(self, task: Task) -> Dict[str, Any]:
        """Validate task before execution"""
        validation_result = {
            'valid': True,
            'issues': [],
            'warnings': []
        }
        
        # Check if agent can handle this task type
        if not self.can_handle_task(task):
            validation_result['valid'] = False
            validation_result['issues'].append(f"Agent {self.name} cannot handle task type")
        
        # Check agent status
        if self.status.value not in ['idle', 'active']:
            validation_result['valid'] = False
            validation_result['issues'].append(f"Agent {self.name} is not available (status: {self.status.value})")
        
        # Validate task data
        if not task.title or not task.description:
            validation_result['warnings'].append("Task has incomplete information")
        
        return validation_result
    
    async def _check_and_resolve_capabilities(self, task: Task) -> Dict[str, Any]:
        """Check if agent has required capabilities for task"""
        result = {
            'sufficient': True,
            'missing_capabilities': [],
            'available_alternatives': []
        }
        
        # Get required capabilities (simplified - would use more sophisticated analysis)
        required_capabilities = self._analyze_required_capabilities(task)
        
        # Check against agent capabilities
        agent_capabilities = set(self.capabilities or [])
        missing = [cap for cap in required_capabilities if cap not in agent_capabilities]
        
        if missing:
            result['sufficient'] = False
            result['missing_capabilities'] = missing
            
            # Look for alternatives in agent capabilities
            alternatives = self._find_capability_alternatives(missing, agent_capabilities)
            result['available_alternatives'] = alternatives
            
            if not alternatives:
                logger.warning(f"Agent {self.name} missing capabilities: {missing}")
        
        return result
    
    def _analyze_required_capabilities(self, task: Task) -> List[str]:
        """Analyze task to determine required capabilities"""
        # Simplified implementation - would use more sophisticated analysis
        required = []
        
        task_text = f"{task.title} {task.description or ''}".lower()
        
        # Basic capability mapping
        capability_keywords = {
            'email_sending': ['email', 'send', 'notify', 'mail'],
            'data_analysis': ['analyze', 'data', 'report', 'statistics'],
            'file_processing': ['file', 'document', 'process', 'convert'],
            'web_integration': ['web', 'api', 'http', 'url'],
            'database_operations': ['database', 'sql', 'query', 'store']
        }
        
        for capability, keywords in capability_keywords.items():
            if any(keyword in task_text for keyword in keywords):
                required.append(capability)
        
        # Always require basic task execution
        if not required:
            required.append('task_execution')
        
        return required
    
    def _find_capability_alternatives(self, missing: List[str], available: set) -> List[str]:
        """Find alternative capabilities that might substitute for missing ones"""
        alternatives = []
        
        # Define capability substitutions
        substitutions = {
            'email_sending': ['notification_sending', 'message_delivery'],
            'data_analysis': ['basic_processing', 'report_generation'],
            'file_processing': ['basic_processing', 'data_handling']
        }
        
        for missing_cap in missing:
            if missing_cap in substitutions:
                for alt in substitutions[missing_cap]:
                    if alt in available:
                        alternatives.append(alt)
                        break
        
        return alternatives
    
    async def _execute_task_implementation(self, task: Task) -> Dict[str, Any]:
        """Execute the actual task - to be implemented by subclasses"""
        # Call the original execute_task method
        return self.execute_task(task)
    
    async def _handle_validation_failure(self, task: Task, validation_result: ValidationResult, 
                                         execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation failure with rollback"""
        logger.warning(f"Validation failed for task {task.id}: {validation_result.rollback_reason}")
        
        # The validation chain should handle rollback automatically
        # Here we just create the failure response
        
        return {
            'status': 'validation_failed',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'validation_result': validation_result.to_dict(),
            'original_result': execution_result,
            'rollback_initiated': validation_result.rollback_required,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _handle_validation_revision(self, task: Task, validation_result: ValidationResult,
                                          execution_result: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation requiring revision"""
        logger.info(f"Task {task.id} requires revision based on validation feedback")
        
        # Check if we can auto-fix issues
        auto_fixable_issues = validation_result.get_auto_fixable_issues()
        
        if auto_fixable_issues:
            logger.info(f"Attempting auto-fix for {len(auto_fixable_issues)} issues")
            # TODO: Implement auto-fix logic
            
        return {
            'status': 'requires_revision',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'validation_result': validation_result.to_dict(),
            'original_result': execution_result,
            'auto_fixable_issues': len(auto_fixable_issues),
            'recommendations': validation_result.recommendations,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_success_response(self, task: Task, execution_result: Dict[str, Any],
                                 validation_result: Optional[ValidationResult]) -> Dict[str, Any]:
        """Create success response with validation information"""
        response = {
            'status': 'success',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'agent_name': self.name,
            'result': execution_result,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if validation_result:
            response['validation'] = {
                'status': validation_result.status.value,
                'tier': validation_result.tier,
                'overall_score': validation_result.metrics.overall_score,
                'issues_count': len(validation_result.issues),
                'recommendations_count': len(validation_result.recommendations)
            }
        
        return response
    
    def _create_validation_failure_response(self, task: Task, reason: str, 
                                            validation_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create response for validation failure"""
        return {
            'status': 'validation_failed',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'reason': reason,
            'validation_details': validation_details,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_capability_failure_response(self, task: Task, 
                                            capability_details: Dict[str, Any]) -> Dict[str, Any]:
        """Create response for capability failure"""
        return {
            'status': 'capability_insufficient',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'capability_details': capability_details,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _create_error_response(self, task: Task, error_message: str) -> Dict[str, Any]:
        """Create error response"""
        return {
            'status': 'error',
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def _log_execution(self, execution_id: str, task: Task, response: Dict[str, Any], 
                       start_time: datetime):
        """Log execution details"""
        end_time = datetime.utcnow()
        duration_ms = int((end_time - start_time).total_seconds() * 1000)
        
        log_entry = {
            'execution_id': execution_id,
            'task_id': str(task.id),
            'agent_id': str(self.agent_id),
            'status': response['status'],
            'duration_ms': duration_ms,
            'start_time': start_time.isoformat(),
            'end_time': end_time.isoformat(),
            'validation_tier': self.validation_tier.value
        }
        
        self.execution_history.append(log_entry)
        
        # Keep only last 100 executions
        if len(self.execution_history) > 100:
            self.execution_history = self.execution_history[-100:]
        
        logger.info(f"Execution {execution_id} completed: {response['status']} in {duration_ms}ms")
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.execution_history[-limit:]
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics for this agent"""
        if not self.execution_history:
            return {'total_executions': 0}
        
        total = len(self.execution_history)
        successful = len([e for e in self.execution_history if e['status'] == 'success'])
        validation_failed = len([e for e in self.execution_history if e['status'] == 'validation_failed'])
        capability_failed = len([e for e in self.execution_history if e['status'] == 'capability_insufficient'])
        
        avg_duration = sum(e['duration_ms'] for e in self.execution_history) / total
        
        return {
            'total_executions': total,
            'successful_executions': successful,
            'validation_failures': validation_failed,
            'capability_failures': capability_failed,
            'success_rate': successful / total,
            'average_duration_ms': avg_duration,
            'validation_tier': self.validation_tier.value
        }
