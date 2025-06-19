"""
Validation and Plugin Integration Module

Integrates the hierarchical validation system with the plugin architecture
and provides a unified interface for the SwarmDirector system.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from .validation.validation_chain import ValidationChain, ValidationTier
from .validation.validators import ToolAgentValidator, DepartmentAgentValidator, DirectorAgentValidator
from .validation.rollback_manager import RollbackManager
from .plugins.plugin_manager import PluginManager
from .agents.validated_base_agent import ValidatedBaseAgent
from .models.task import Task
from .models.agent import Agent

logger = logging.getLogger(__name__)


class ValidationPluginIntegrator:
    """
    Central integrator that coordinates validation and plugin systems
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        
        # Initialize validation system
        self.rollback_manager = RollbackManager()
        self.validation_chain = ValidationChain(self.rollback_manager)
        
        # Register validators
        self._setup_validators()
        
        # Initialize plugin system
        self.plugin_manager = PluginManager(self.config.get('plugin_config', {}))
        
        # Initialize capability discovery
        from .plugins.capability_discovery import CapabilityDiscovery
        from .plugins.agent_factory import AgentFactory
        from .plugins.dependency_manager import DependencyManager
        
        # Create dependency manager
        dependency_manager = DependencyManager(
            cache_dir=self.config.get('dependency_cache_dir', './plugin_cache')
        )
        
        self.agent_factory = AgentFactory(self.plugin_manager.registry, dependency_manager)
        self.capability_discovery = CapabilityDiscovery(self.plugin_manager.registry, self.agent_factory)
        
        # Integration state
        self.enhanced_agents: Dict[str, ValidatedBaseAgent] = {}
        self.integration_metrics = {
            'tasks_processed': 0,
            'validations_performed': 0,
            'plugins_auto_installed': 0,
            'rollbacks_executed': 0
        }
        
        logger.info("Validation and plugin integration initialized")
    
    def _setup_validators(self):
        """Setup validators for each tier"""
        # Register validators for each tier
        self.validation_chain.register_validator(ValidationTier.TOOL, ToolAgentValidator())
        self.validation_chain.register_validator(ValidationTier.DEPARTMENT, DepartmentAgentValidator())
        self.validation_chain.register_validator(ValidationTier.DIRECTOR, DirectorAgentValidator())
        
        logger.info("Validation chain configured with tier-specific validators")
    
    def enhance_agent(self, agent: Agent) -> ValidatedBaseAgent:
        """
        Enhance an existing agent with validation and plugin capabilities
        """
        if str(agent.id) in self.enhanced_agents:
            return self.enhanced_agents[str(agent.id)]
        
        # Create enhanced agent based on agent type
        if agent.agent_type.value == 'worker':
            from .agents.worker_agent import WorkerAgent
            base_agent = WorkerAgent(agent)
        elif agent.agent_type.value in ['coordinator', 'supervisor']:
            from .agents.supervisor_agent import SupervisorAgent
            base_agent = SupervisorAgent(agent)
        else:
            from .agents.director import DirectorAgent
            base_agent = DirectorAgent(agent)
        
        # Create validated agent
        enhanced_agent = ValidatedBaseAgent(
            agent, 
            self.validation_chain, 
            self.plugin_manager
        )
        
        # Copy methods from base agent
        enhanced_agent.execute_task = base_agent.execute_task
        enhanced_agent.can_handle_task = base_agent.can_handle_task
        
        self.enhanced_agents[str(agent.id)] = enhanced_agent
        
        logger.info(f"Enhanced agent {agent.name} with validation and plugin capabilities")
        return enhanced_agent
    
    async def process_task_with_full_validation(self, task: Task, 
                                                tool_agent: Agent,
                                                dept_agent: Optional[Agent] = None,
                                                director_agent: Optional[Agent] = None) -> Dict[str, Any]:
        """
        Process task through complete hierarchical validation flow
        """
        logger.info(f"Processing task {task.id} with full hierarchical validation")
        
        start_time = datetime.utcnow()
        result = {
            'task_id': str(task.id),
            'success': False,
            'validation_results': [],
            'plugins_installed': [],
            'rollbacks_performed': [],
            'processing_time_ms': 0
        }
        
        try:
            # 1. Enhance agents
            enhanced_tool = self.enhance_agent(tool_agent)
            enhanced_dept = self.enhance_agent(dept_agent) if dept_agent else None
            enhanced_director = self.enhance_agent(director_agent) if director_agent else None
            
            # 2. Execute at tool level
            tool_result = await enhanced_tool.execute_task_with_validation(task)
            result['tool_result'] = tool_result
            
            if tool_result['status'] != 'success':
                result['failure_tier'] = 'tool'
                result['failure_reason'] = tool_result.get('reason', 'Tool execution failed')
                return result
            
            # 3. Execute at department level (if provided)
            if enhanced_dept:
                # Department agent reviews tool output
                dept_task = self._create_review_task(task, tool_result, 'department')
                dept_result = await enhanced_dept.execute_task_with_validation(dept_task)
                result['department_result'] = dept_result
                
                if dept_result['status'] != 'success':
                    result['failure_tier'] = 'department'
                    result['failure_reason'] = dept_result.get('reason', 'Department validation failed')
                    return result
            
            # 4. Execute at director level (if provided)
            if enhanced_director:
                # Director agent performs final validation
                director_task = self._create_review_task(task, 
                                                         dept_result if enhanced_dept else tool_result, 
                                                         'director')
                director_result = await enhanced_director.execute_task_with_validation(director_task)
                result['director_result'] = director_result
                
                if director_result['status'] != 'success':
                    result['failure_tier'] = 'director'
                    result['failure_reason'] = director_result.get('reason', 'Director validation failed')
                    return result
            
            # 5. Collect validation results
            validation_results = []
            if 'validation' in tool_result:
                validation_results.append({
                    'tier': 'tool',
                    'status': tool_result['validation']['status'],
                    'score': tool_result['validation']['overall_score']
                })
            
            if enhanced_dept and 'validation' in dept_result:
                validation_results.append({
                    'tier': 'department',
                    'status': dept_result['validation']['status'],
                    'score': dept_result['validation']['overall_score']
                })
            
            if enhanced_director and 'validation' in director_result:
                validation_results.append({
                    'tier': 'director',
                    'status': director_result['validation']['status'],
                    'score': director_result['validation']['overall_score']
                })
            
            result['validation_results'] = validation_results
            result['success'] = True
            
            # Update metrics
            self.integration_metrics['tasks_processed'] += 1
            self.integration_metrics['validations_performed'] += len(validation_results)
            
            logger.info(f"Task {task.id} processed successfully through hierarchical validation")
            
        except Exception as e:
            logger.error(f"Error in hierarchical validation for task {task.id}: {e}", exc_info=True)
            result['error'] = str(e)
            result['failure_tier'] = 'system'
            result['failure_reason'] = f"System error: {str(e)}"
        
        finally:
            end_time = datetime.utcnow()
            result['processing_time_ms'] = int((end_time - start_time).total_seconds() * 1000)
        
        return result
    
    def _create_review_task(self, original_task: Task, previous_result: Dict[str, Any], 
                            review_tier: str) -> Task:
        """Create a review task for higher-tier validation"""
        review_task = Task(
            title=f"{review_tier.title()} Review: {original_task.title}",
            description=f"Review and validate output from {review_tier} tier for task: {original_task.description}",
            input_data={
                'original_task_id': str(original_task.id),
                'previous_result': previous_result,
                'review_tier': review_tier,
                'validation_required': True
            }
        )
        review_task.save()
        return review_task
    
    async def auto_resolve_capability_gaps(self, task: Task) -> Dict[str, Any]:
        """
        Automatically resolve capability gaps using the plugin system
        """
        logger.info(f"Auto-resolving capability gaps for task {task.id}")
        
        # Use plugin manager to process task and install required plugins
        plugin_result = self.plugin_manager.process_task_with_plugins(task)
        
        if plugin_result['success']:
            self.integration_metrics['plugins_auto_installed'] += len(plugin_result['plugins_installed'])
        
        return plugin_result
    
    def get_system_health(self) -> Dict[str, Any]:
        """Get comprehensive system health status"""
        validation_stats = self.validation_chain.get_validation_statistics()
        plugin_status = self.plugin_manager.get_system_status()
        rollback_stats = self.rollback_manager.get_rollback_statistics()
        
        return {
            'integration_metrics': self.integration_metrics,
            'validation_statistics': validation_stats,
            'plugin_system_status': plugin_status,
            'rollback_statistics': rollback_stats,
            'enhanced_agents_count': len(self.enhanced_agents),
            'system_timestamp': datetime.utcnow().isoformat()
        }
    
    def configure_quality_gates(self, tier: ValidationTier, config: Dict[str, Any]):
        """Configure quality gates for a specific tier"""
        from .validation.quality_gate import QualityGate
        
        quality_gate = QualityGate(
            name=f"{tier.value}_custom_gate",
            tier=tier.value,
            config=config
        )
        
        self.validation_chain.set_quality_gate(tier, quality_gate)
        logger.info(f"Configured custom quality gate for tier {tier.value}")
    
    def enable_auto_features(self, auto_install: bool = True, auto_discovery: bool = True):
        """Enable or disable automatic features"""
        self.plugin_manager.enable_auto_install(auto_install)
        self.plugin_manager.enable_auto_discovery(auto_discovery)
        
        logger.info(f"Auto features configured: install={auto_install}, discovery={auto_discovery}")
    
    def get_validation_history(self, task_id: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get validation history with optional filtering"""
        return self.validation_chain.get_validation_history(task_id=task_id)
    
    def get_plugin_suggestions(self, task: Task) -> List[Dict[str, Any]]:
        """Get plugin suggestions for a task"""
        suggestions = self.plugin_manager.suggest_plugins_for_task(task)
        
        return [
            {
                'plugin_name': plugin.name,
                'description': plugin.description,
                'relevance_score': score,
                'capabilities': [cap.name for cap in plugin.capabilities],
                'status': plugin.status.value
            }
            for plugin, score in suggestions
        ]
    
    def cleanup_system(self, days: int = 30):
        """Cleanup old data and inactive components"""
        # Cleanup validation history
        validation_cleaned = self.validation_chain.cleanup_old_history(days)
        
        # Cleanup inactive plugins
        plugins_cleaned = self.plugin_manager.cleanup_inactive_plugins(days)
        
        # Cleanup enhanced agents that haven't been used
        agents_cleaned = 0
        for agent_id, enhanced_agent in list(self.enhanced_agents.items()):
            history = enhanced_agent.get_execution_history()
            if not history:  # No execution history
                del self.enhanced_agents[agent_id]
                agents_cleaned += 1
        
        logger.info(f"System cleanup completed: {validation_cleaned} validation records, "
                   f"{plugins_cleaned} plugins, {agents_cleaned} enhanced agents")
        
        return {
            'validation_records_cleaned': validation_cleaned,
            'plugins_cleaned': plugins_cleaned,
            'enhanced_agents_cleaned': agents_cleaned
        }
    
    def validate_system_integrity(self) -> Dict[str, Any]:
        """Validate overall system integrity"""
        plugin_integrity = self.plugin_manager.validate_system_integrity()
        
        # Check validation chain integrity
        validation_integrity = {
            'validators_registered': {
                tier.value: len(self.validation_chain.validators[tier])
                for tier in ValidationTier
            },
            'quality_gates_configured': len(self.validation_chain.quality_gates)
        }
        
        # Check enhanced agents
        agent_integrity = {
            'enhanced_agents_count': len(self.enhanced_agents),
            'agents_with_history': len([
                agent for agent in self.enhanced_agents.values()
                if agent.get_execution_history()
            ])
        }
        
        overall_valid = (
            plugin_integrity['valid'] and
            all(count > 0 for count in validation_integrity['validators_registered'].values())
        )
        
        return {
            'overall_valid': overall_valid,
            'plugin_integrity': plugin_integrity,
            'validation_integrity': validation_integrity,
            'agent_integrity': agent_integrity,
            'checked_at': datetime.utcnow().isoformat()
        }
