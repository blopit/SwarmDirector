"""
Agent Factory

Dynamic agent instantiation system that creates new agent types based on 
task requirements and available plugins.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Type, Callable
from dataclasses import dataclass, field
import logging
import importlib
import inspect
from datetime import datetime

from .plugin_registry import PluginRegistry, PluginMetadata, PluginType
from .dependency_manager import DependencyManager
from ..agents.base_agent import BaseAgent
from ..models.agent import Agent, AgentType, AgentStatus
from ..models.task import Task

logger = logging.getLogger(__name__)


class AgentCreationStrategy(Enum):
    """Strategies for agent creation"""
    TEMPLATE_BASED = "template_based"
    PLUGIN_BASED = "plugin_based"
    HYBRID = "hybrid"
    DYNAMIC = "dynamic"


@dataclass
class AgentTemplate:
    """Template for creating new agents"""
    name: str
    description: str
    agent_type: AgentType
    base_class: str  # Fully qualified class name
    capabilities: List[str] = field(default_factory=list)
    required_plugins: List[str] = field(default_factory=list)
    config_schema: Dict[str, Any] = field(default_factory=dict)
    initialization_params: Dict[str, Any] = field(default_factory=dict)
    
    # Template metadata
    version: str = "1.0.0"
    author: str = "SwarmDirector"
    tags: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'agent_type': self.agent_type.value,
            'base_class': self.base_class,
            'capabilities': self.capabilities,
            'required_plugins': self.required_plugins,
            'config_schema': self.config_schema,
            'initialization_params': self.initialization_params,
            'version': self.version,
            'author': self.author,
            'tags': self.tags
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentTemplate':
        """Create from dictionary"""
        return cls(
            name=data['name'],
            description=data['description'],
            agent_type=AgentType(data['agent_type']),
            base_class=data['base_class'],
            capabilities=data.get('capabilities', []),
            required_plugins=data.get('required_plugins', []),
            config_schema=data.get('config_schema', {}),
            initialization_params=data.get('initialization_params', {}),
            version=data.get('version', '1.0.0'),
            author=data.get('author', 'SwarmDirector'),
            tags=data.get('tags', [])
        )


@dataclass
class AgentCreationRequest:
    """Request for creating a new agent"""
    task: Task
    required_capabilities: List[str]
    preferred_agent_type: Optional[AgentType] = None
    constraints: Dict[str, Any] = field(default_factory=dict)
    strategy: AgentCreationStrategy = AgentCreationStrategy.HYBRID
    
    # Context information
    context: Dict[str, Any] = field(default_factory=dict)
    priority: int = 1  # Lower numbers = higher priority
    timeout_seconds: int = 300


@dataclass
class AgentCreationResult:
    """Result of agent creation"""
    success: bool
    agent: Optional[BaseAgent] = None
    agent_db: Optional[Agent] = None
    template_used: Optional[AgentTemplate] = None
    plugins_installed: List[str] = field(default_factory=list)
    
    # Error information
    error_message: Optional[str] = None
    missing_capabilities: List[str] = field(default_factory=list)
    failed_dependencies: List[str] = field(default_factory=list)
    
    # Metadata
    creation_time: datetime = field(default_factory=datetime.utcnow)
    strategy_used: Optional[AgentCreationStrategy] = None


class AgentFactory:
    """
    Factory for dynamically creating agents based on requirements
    """
    
    def __init__(self, plugin_registry: PluginRegistry, 
                 dependency_manager: DependencyManager):
        self.plugin_registry = plugin_registry
        self.dependency_manager = dependency_manager
        self.templates: Dict[str, AgentTemplate] = {}
        self.creation_history: List[AgentCreationResult] = []
        
        # Load built-in templates
        self._load_builtin_templates()
    
    def _load_builtin_templates(self):
        """Load built-in agent templates"""
        builtin_templates = [
            AgentTemplate(
                name="EmailAgent",
                description="Agent for email operations",
                agent_type=AgentType.WORKER,
                base_class="swarm_director.agents.email_agent.EmailAgent",
                capabilities=["email_sending", "email_validation", "template_processing"],
                tags=["communication", "email"]
            ),
            AgentTemplate(
                name="AnalysisAgent",
                description="Agent for data analysis tasks",
                agent_type=AgentType.WORKER,
                base_class="swarm_director.agents.worker_agent.WorkerAgent",
                capabilities=["data_analysis", "report_generation", "statistics"],
                tags=["analysis", "data"]
            ),
            AgentTemplate(
                name="CoordinationAgent",
                description="Agent for task coordination",
                agent_type=AgentType.SUPERVISOR,
                base_class="swarm_director.agents.supervisor_agent.SupervisorAgent",
                capabilities=["task_coordination", "agent_management", "workflow_control"],
                tags=["coordination", "management"]
            )
        ]
        
        for template in builtin_templates:
            self.register_template(template)
    
    def register_template(self, template: AgentTemplate) -> bool:
        """Register an agent template"""
        try:
            self.templates[template.name] = template
            logger.info(f"Registered agent template: {template.name}")
            return True
        except Exception as e:
            logger.error(f"Error registering template {template.name}: {e}")
            return False
    
    def create_agent(self, request: AgentCreationRequest) -> AgentCreationResult:
        """Create an agent based on the request"""
        logger.info(f"Creating agent for task {request.task.id} with capabilities: {request.required_capabilities}")
        
        result = AgentCreationResult(
            success=False,
            strategy_used=request.strategy
        )
        
        try:
            if request.strategy == AgentCreationStrategy.TEMPLATE_BASED:
                return self._create_from_template(request, result)
            elif request.strategy == AgentCreationStrategy.PLUGIN_BASED:
                return self._create_from_plugins(request, result)
            elif request.strategy == AgentCreationStrategy.HYBRID:
                return self._create_hybrid(request, result)
            elif request.strategy == AgentCreationStrategy.DYNAMIC:
                return self._create_dynamic(request, result)
            else:
                result.error_message = f"Unknown creation strategy: {request.strategy}"
                return result
                
        except Exception as e:
            logger.error(f"Error creating agent: {e}", exc_info=True)
            result.error_message = f"Agent creation failed: {str(e)}"
            return result
        finally:
            self.creation_history.append(result)
    
    def _create_from_template(self, request: AgentCreationRequest, 
                              result: AgentCreationResult) -> AgentCreationResult:
        """Create agent from existing template"""
        # Find suitable template
        template = self._find_suitable_template(request.required_capabilities, 
                                                request.preferred_agent_type)
        
        if not template:
            result.error_message = "No suitable template found"
            result.missing_capabilities = request.required_capabilities
            return result
        
        result.template_used = template
        
        # Check and install required plugins
        if template.required_plugins:
            plugin_success = self._install_required_plugins(template.required_plugins, result)
            if not plugin_success:
                return result
        
        # Create agent instance
        agent_instance = self._instantiate_agent(template, request, result)
        if agent_instance:
            result.success = True
            result.agent = agent_instance
        
        return result
    
    def _create_from_plugins(self, request: AgentCreationRequest, 
                             result: AgentCreationResult) -> AgentCreationResult:
        """Create agent from available plugins"""
        # Find plugins that provide required capabilities
        suitable_plugins = []
        
        for capability in request.required_capabilities:
            plugins = self.plugin_registry.find_plugins_by_capability(capability)
            agent_plugins = [p for p in plugins if p.plugin_type == PluginType.AGENT]
            suitable_plugins.extend(agent_plugins)
        
        if not suitable_plugins:
            result.error_message = "No suitable plugins found"
            result.missing_capabilities = request.required_capabilities
            return result
        
        # Select best plugin (simplified selection logic)
        best_plugin = suitable_plugins[0]  # TODO: Implement better selection
        
        # Install plugin if needed
        if best_plugin.status.value != "installed":
            success = self._install_plugin(best_plugin, result)
            if not success:
                return result
        
        # Create agent from plugin
        agent_instance = self._instantiate_from_plugin(best_plugin, request, result)
        if agent_instance:
            result.success = True
            result.agent = agent_instance
        
        return result
    
    def _create_hybrid(self, request: AgentCreationRequest, 
                       result: AgentCreationResult) -> AgentCreationResult:
        """Create agent using hybrid approach (template + plugins)"""
        # Try template-based first
        template_result = self._create_from_template(request, result)
        if template_result.success:
            return template_result
        
        # Fall back to plugin-based
        logger.info("Template-based creation failed, trying plugin-based")
        return self._create_from_plugins(request, result)
    
    def _create_dynamic(self, request: AgentCreationRequest, 
                        result: AgentCreationResult) -> AgentCreationResult:
        """Create agent dynamically based on task analysis"""
        # Analyze task to determine best approach
        task_analysis = self._analyze_task_requirements(request.task)
        
        # Create dynamic template based on analysis
        dynamic_template = self._create_dynamic_template(task_analysis, request)
        
        if dynamic_template:
            # Register temporary template
            self.register_template(dynamic_template)
            result.template_used = dynamic_template
            
            # Create agent from dynamic template
            agent_instance = self._instantiate_agent(dynamic_template, request, result)
            if agent_instance:
                result.success = True
                result.agent = agent_instance
        else:
            result.error_message = "Failed to create dynamic template"
        
        return result
    
    def _find_suitable_template(self, capabilities: List[str], 
                                preferred_type: Optional[AgentType]) -> Optional[AgentTemplate]:
        """Find template that matches required capabilities"""
        best_template = None
        best_score = 0
        
        for template in self.templates.values():
            # Check agent type preference
            if preferred_type and template.agent_type != preferred_type:
                continue
            
            # Calculate capability match score
            matching_capabilities = set(capabilities) & set(template.capabilities)
            score = len(matching_capabilities) / len(capabilities) if capabilities else 0
            
            if score > best_score:
                best_score = score
                best_template = template
        
        # Require at least 50% capability match
        return best_template if best_score >= 0.5 else None
    
    def _install_required_plugins(self, plugin_names: List[str], 
                                  result: AgentCreationResult) -> bool:
        """Install required plugins for template"""
        for plugin_name in plugin_names:
            plugin = self.plugin_registry.get_plugin(plugin_name)
            if not plugin:
                result.error_message = f"Required plugin not found: {plugin_name}"
                return False
            
            if plugin.status.value != "installed":
                success = self._install_plugin(plugin, result)
                if not success:
                    return False
        
        return True
    
    def _install_plugin(self, plugin: PluginMetadata, 
                        result: AgentCreationResult) -> bool:
        """Install a single plugin"""
        try:
            # Install dependencies first
            if plugin.dependencies:
                dep_results = self.dependency_manager.install_dependencies(plugin.dependencies)
                failed_deps = [name for name, success in dep_results.items() if not success]
                
                if failed_deps:
                    result.failed_dependencies.extend(failed_deps)
                    result.error_message = f"Failed to install dependencies: {failed_deps}"
                    return False
            
            # TODO: Implement actual plugin installation
            # For now, just mark as installed
            self.plugin_registry.update_plugin_status(plugin.name, "installed")
            result.plugins_installed.append(plugin.name)
            
            logger.info(f"Installed plugin: {plugin.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing plugin {plugin.name}: {e}")
            result.error_message = f"Plugin installation failed: {str(e)}"
            return False
    
    def _instantiate_agent(self, template: AgentTemplate, 
                           request: AgentCreationRequest,
                           result: AgentCreationResult) -> Optional[BaseAgent]:
        """Instantiate agent from template"""
        try:
            # Import the agent class
            module_path, class_name = template.base_class.rsplit('.', 1)
            module = importlib.import_module(module_path)
            agent_class = getattr(module, class_name)
            
            # Create database record
            agent_db = Agent(
                name=f"{template.name}_{request.task.id}",
                description=template.description,
                agent_type=template.agent_type,
                status=AgentStatus.IDLE,
                capabilities=template.capabilities,
                config=template.initialization_params
            )
            agent_db.save()
            
            # Create agent instance
            agent_instance = agent_class(agent_db)
            
            result.agent_db = agent_db
            logger.info(f"Created agent instance: {agent_db.name}")
            
            return agent_instance
            
        except Exception as e:
            logger.error(f"Error instantiating agent from template {template.name}: {e}")
            result.error_message = f"Agent instantiation failed: {str(e)}"
            return None
    
    def _instantiate_from_plugin(self, plugin: PluginMetadata, 
                                 request: AgentCreationRequest,
                                 result: AgentCreationResult) -> Optional[BaseAgent]:
        """Instantiate agent from plugin"""
        try:
            # TODO: Implement plugin-based agent instantiation
            # This would load the agent class from the plugin
            logger.info(f"Plugin-based agent instantiation not yet implemented: {plugin.name}")
            result.error_message = "Plugin-based instantiation not implemented"
            return None
            
        except Exception as e:
            logger.error(f"Error instantiating agent from plugin {plugin.name}: {e}")
            result.error_message = f"Plugin instantiation failed: {str(e)}"
            return None
    
    def _analyze_task_requirements(self, task: Task) -> Dict[str, Any]:
        """Analyze task to determine requirements"""
        # Simplified task analysis - can be enhanced with ML
        analysis = {
            'complexity': 'medium',
            'domain': 'general',
            'required_capabilities': [],
            'suggested_agent_type': AgentType.WORKER
        }
        
        # Analyze task description for keywords
        description = (task.description or '').lower()
        
        if any(word in description for word in ['email', 'send', 'notify']):
            analysis['required_capabilities'].append('email_sending')
            analysis['domain'] = 'communication'
        
        if any(word in description for word in ['analyze', 'report', 'data']):
            analysis['required_capabilities'].append('data_analysis')
            analysis['domain'] = 'analysis'
        
        if any(word in description for word in ['coordinate', 'manage', 'assign']):
            analysis['suggested_agent_type'] = AgentType.SUPERVISOR
            analysis['domain'] = 'coordination'
        
        return analysis
    
    def _create_dynamic_template(self, analysis: Dict[str, Any], 
                                 request: AgentCreationRequest) -> Optional[AgentTemplate]:
        """Create dynamic template based on task analysis"""
        try:
            template = AgentTemplate(
                name=f"Dynamic_{request.task.id}",
                description=f"Dynamically created agent for task {request.task.id}",
                agent_type=analysis.get('suggested_agent_type', AgentType.WORKER),
                base_class="swarm_director.agents.worker_agent.WorkerAgent",
                capabilities=analysis.get('required_capabilities', []),
                tags=['dynamic', analysis.get('domain', 'general')]
            )
            
            return template
            
        except Exception as e:
            logger.error(f"Error creating dynamic template: {e}")
            return None
    
    def get_creation_history(self) -> List[AgentCreationResult]:
        """Get agent creation history"""
        return self.creation_history.copy()
    
    def get_available_templates(self) -> List[AgentTemplate]:
        """Get all available templates"""
        return list(self.templates.values())
    
    def get_factory_statistics(self) -> Dict[str, Any]:
        """Get factory statistics"""
        total_creations = len(self.creation_history)
        successful_creations = len([r for r in self.creation_history if r.success])
        
        return {
            'total_creations': total_creations,
            'successful_creations': successful_creations,
            'success_rate': successful_creations / total_creations if total_creations > 0 else 0.0,
            'available_templates': len(self.templates),
            'strategies_used': {
                strategy.value: len([r for r in self.creation_history if r.strategy_used == strategy])
                for strategy in AgentCreationStrategy
            }
        }
