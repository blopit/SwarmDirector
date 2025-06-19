"""
Plugin Manager

Central orchestrator for the plugin architecture system. Manages plugin 
lifecycle, coordinates with other components, and provides the main interface
for plugin operations.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import logging
import os
from datetime import datetime, timedelta

from .plugin_registry import PluginRegistry, PluginMetadata, PluginStatus
from .dependency_manager import DependencyManager
from .agent_factory import AgentFactory, AgentCreationRequest, AgentCreationStrategy
from .capability_discovery import CapabilityDiscovery
from ..models.task import Task
from ..models.agent import Agent, AgentType

logger = logging.getLogger(__name__)


class PluginManagerStatus(Enum):
    """Plugin manager status"""
    INITIALIZING = "initializing"
    READY = "ready"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class PluginManager:
    """
    Central plugin management system that orchestrates all plugin operations
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.status = PluginManagerStatus.INITIALIZING
        
        # Initialize components
        self.registry = PluginRegistry(
            registry_path=self.config.get('registry_path')
        )
        self.dependency_manager = DependencyManager(
            cache_dir=self.config.get('dependency_cache_dir')
        )
        self.agent_factory = AgentFactory(self.registry, self.dependency_manager)
        self.capability_discovery = CapabilityDiscovery(self.registry, self.agent_factory)
        
        # Plugin management state
        self.active_plugins: Dict[str, Any] = {}
        self.operation_history: List[Dict[str, Any]] = []
        
        # Auto-discovery settings
        self.auto_install_enabled = self.config.get('auto_install_enabled', False)
        self.auto_discovery_enabled = self.config.get('auto_discovery_enabled', True)
        
        self.status = PluginManagerStatus.READY
        logger.info("Plugin manager initialized successfully")
    
    def process_task_with_plugins(self, task: Task, 
                                  available_agents: Optional[List[Agent]] = None) -> Dict[str, Any]:
        """
        Process a task using the plugin system to fill capability gaps
        
        Returns:
            Dict containing processing results and any plugins installed
        """
        logger.info(f"Processing task {task.id} with plugin system")
        
        result = {
            'success': False,
            'task_id': str(task.id),
            'agent_created': None,
            'plugins_installed': [],
            'capabilities_satisfied': [],
            'remaining_gaps': [],
            'recommendations': []
        }
        
        try:
            self.status = PluginManagerStatus.BUSY
            
            # 1. Assess current capabilities
            assessment = self.capability_discovery.assess_task_capabilities(task, available_agents)
            
            result['capabilities_satisfied'] = [
                cap for cap in assessment.required_capabilities 
                if cap in assessment.available_capabilities
            ]
            
            # 2. If task can be completed with current capabilities, proceed
            if assessment.can_complete_task:
                logger.info(f"Task {task.id} can be completed with existing capabilities")
                result['success'] = True
                result['recommendations'] = ["Task can be completed with existing system capabilities"]
                return result
            
            # 3. Identify critical gaps that need to be filled
            critical_gaps = [gap for gap in assessment.gaps if gap.severity.value in ['critical', 'high']]
            
            if not critical_gaps:
                logger.info(f"No critical gaps found for task {task.id}")
                result['success'] = True
                result['remaining_gaps'] = [gap.name for gap in assessment.gaps]
                return result
            
            # 4. Attempt to resolve gaps through plugin installation
            if self.auto_install_enabled:
                installation_results = self._auto_install_for_gaps(critical_gaps)
                result['plugins_installed'] = installation_results['installed']
                
                # Re-assess after installation
                if installation_results['installed']:
                    updated_assessment = self.capability_discovery.assess_task_capabilities(task, available_agents)
                    if updated_assessment.can_complete_task:
                        result['success'] = True
                        logger.info(f"Task {task.id} can now be completed after plugin installation")
                        return result
            
            # 5. Attempt to create specialized agent
            agent_result = self._create_agent_for_task(task, critical_gaps)
            if agent_result['success']:
                result['agent_created'] = agent_result['agent_info']
                result['success'] = True
                logger.info(f"Created specialized agent for task {task.id}")
            else:
                result['remaining_gaps'] = [gap.name for gap in critical_gaps]
                result['recommendations'] = self._generate_resolution_recommendations(critical_gaps)
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing task {task.id} with plugins: {e}", exc_info=True)
            result['error'] = str(e)
            return result
        finally:
            self.status = PluginManagerStatus.READY
            self._log_operation('process_task', task.id, result)
    
    def _auto_install_for_gaps(self, gaps: List[Any]) -> Dict[str, Any]:
        """Automatically install plugins to fill capability gaps"""
        installation_result = {
            'installed': [],
            'failed': [],
            'skipped': []
        }
        
        for gap in gaps:
            if gap.suggested_plugins:
                plugin_name = gap.suggested_plugins[0]  # Take first suggestion
                plugin = self.registry.get_plugin(plugin_name)
                
                if plugin and plugin.status != PluginStatus.INSTALLED:
                    logger.info(f"Auto-installing plugin {plugin_name} for capability {gap.name}")
                    
                    success = self.install_plugin(plugin_name)
                    if success:
                        installation_result['installed'].append(plugin_name)
                    else:
                        installation_result['failed'].append(plugin_name)
                else:
                    installation_result['skipped'].append(plugin_name)
        
        return installation_result
    
    def _create_agent_for_task(self, task: Task, gaps: List[Any]) -> Dict[str, Any]:
        """Create a specialized agent for the task"""
        try:
            # Determine required capabilities from gaps
            required_capabilities = [gap.name for gap in gaps]
            
            # Create agent creation request
            request = AgentCreationRequest(
                task=task,
                required_capabilities=required_capabilities,
                strategy=AgentCreationStrategy.HYBRID
            )
            
            # Create agent
            creation_result = self.agent_factory.create_agent(request)
            
            if creation_result.success:
                return {
                    'success': True,
                    'agent_info': {
                        'name': creation_result.agent_db.name if creation_result.agent_db else 'Unknown',
                        'type': creation_result.agent_db.agent_type.value if creation_result.agent_db else 'Unknown',
                        'capabilities': required_capabilities,
                        'template_used': creation_result.template_used.name if creation_result.template_used else None
                    }
                }
            else:
                return {
                    'success': False,
                    'error': creation_result.error_message
                }
                
        except Exception as e:
            logger.error(f"Error creating agent for task {task.id}: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _generate_resolution_recommendations(self, gaps: List[Any]) -> List[str]:
        """Generate recommendations for resolving capability gaps"""
        recommendations = []
        
        for gap in gaps:
            if gap.suggested_plugins:
                recommendations.append(
                    f"Install plugin '{gap.suggested_plugins[0]}' to provide {gap.name} capability"
                )
            elif gap.suggested_templates:
                recommendations.append(
                    f"Use agent template '{gap.suggested_templates[0]}' for {gap.name} capability"
                )
            else:
                recommendations.append(
                    f"Develop custom solution for {gap.name} capability (effort: {gap.effort_to_resolve})"
                )
        
        return recommendations
    
    def install_plugin(self, plugin_name: str, force_reinstall: bool = False) -> bool:
        """Install a plugin and its dependencies"""
        try:
            plugin = self.registry.get_plugin(plugin_name)
            if not plugin:
                logger.error(f"Plugin {plugin_name} not found in registry")
                return False
            
            if plugin.status == PluginStatus.INSTALLED and not force_reinstall:
                logger.info(f"Plugin {plugin_name} already installed")
                return True
            
            logger.info(f"Installing plugin: {plugin_name}")
            
            # Update status to installing
            self.registry.update_plugin_status(plugin_name, PluginStatus.UPDATING)
            
            # Install dependencies
            if plugin.dependencies:
                dep_results = self.dependency_manager.install_dependencies(
                    plugin.dependencies, force_reinstall
                )
                
                failed_deps = [name for name, success in dep_results.items() if not success]
                if failed_deps:
                    logger.error(f"Failed to install dependencies for {plugin_name}: {failed_deps}")
                    self.registry.update_plugin_status(plugin_name, PluginStatus.ERROR)
                    return False
            
            # TODO: Implement actual plugin installation logic
            # This would involve downloading, extracting, and setting up the plugin
            
            # For now, just mark as installed
            self.registry.update_plugin_status(plugin_name, PluginStatus.INSTALLED)
            plugin.installed_at = datetime.utcnow()
            
            # Activate plugin
            self.active_plugins[plugin_name] = {
                'metadata': plugin,
                'activated_at': datetime.utcnow(),
                'instance': None  # Would hold actual plugin instance
            }
            
            logger.info(f"Successfully installed plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_name}: {e}")
            self.registry.update_plugin_status(plugin_name, PluginStatus.ERROR)
            return False
    
    def uninstall_plugin(self, plugin_name: str) -> bool:
        """Uninstall a plugin"""
        try:
            if plugin_name not in self.active_plugins:
                logger.warning(f"Plugin {plugin_name} not active")
                return False
            
            logger.info(f"Uninstalling plugin: {plugin_name}")
            
            # Deactivate plugin
            del self.active_plugins[plugin_name]
            
            # Update registry
            self.registry.update_plugin_status(plugin_name, PluginStatus.AVAILABLE)
            
            # TODO: Implement actual plugin cleanup
            
            logger.info(f"Successfully uninstalled plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error uninstalling plugin {plugin_name}: {e}")
            return False
    
    def discover_plugins(self, search_query: Optional[str] = None) -> List[PluginMetadata]:
        """Discover available plugins"""
        if search_query:
            return self.registry.search_plugins(search_query)
        else:
            return self.registry.list_plugins()
    
    def suggest_plugins_for_task(self, task: Task) -> List[Tuple[PluginMetadata, float]]:
        """Get plugin suggestions for a specific task"""
        return self.capability_discovery.suggest_plugins_for_task(task)
    
    def get_system_status(self) -> Dict[str, Any]:
        """Get comprehensive system status"""
        registry_stats = self.registry.get_registry_statistics()
        dependency_stats = self.dependency_manager.get_dependency_statistics()
        factory_stats = self.agent_factory.get_factory_statistics()
        capability_overview = self.capability_discovery.get_system_capability_overview()
        
        return {
            'manager_status': self.status.value,
            'active_plugins': len(self.active_plugins),
            'registry_statistics': registry_stats,
            'dependency_statistics': dependency_stats,
            'factory_statistics': factory_stats,
            'capability_overview': capability_overview,
            'auto_install_enabled': self.auto_install_enabled,
            'auto_discovery_enabled': self.auto_discovery_enabled,
            'recent_operations': len(self.operation_history)
        }
    
    def get_plugin_details(self, plugin_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a plugin"""
        plugin = self.registry.get_plugin(plugin_name)
        if not plugin:
            return None
        
        details = plugin.to_dict()
        
        # Add runtime information if active
        if plugin_name in self.active_plugins:
            details['runtime_info'] = {
                'activated_at': self.active_plugins[plugin_name]['activated_at'].isoformat(),
                'active': True
            }
        else:
            details['runtime_info'] = {'active': False}
        
        return details
    
    def enable_auto_install(self, enabled: bool = True):
        """Enable or disable automatic plugin installation"""
        self.auto_install_enabled = enabled
        logger.info(f"Auto-install {'enabled' if enabled else 'disabled'}")
    
    def enable_auto_discovery(self, enabled: bool = True):
        """Enable or disable automatic capability discovery"""
        self.auto_discovery_enabled = enabled
        logger.info(f"Auto-discovery {'enabled' if enabled else 'disabled'}")
    
    def _log_operation(self, operation: str, target: Any, result: Dict[str, Any]):
        """Log plugin manager operation"""
        log_entry = {
            'operation': operation,
            'target': str(target),
            'timestamp': datetime.utcnow().isoformat(),
            'success': result.get('success', False),
            'details': result
        }
        
        self.operation_history.append(log_entry)
        
        # Keep only last 100 operations
        if len(self.operation_history) > 100:
            self.operation_history = self.operation_history[-100:]
    
    def get_operation_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent operation history"""
        return self.operation_history[-limit:]
    
    def cleanup_inactive_plugins(self, days: int = 30):
        """Clean up plugins that haven't been used recently"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        cleaned = 0
        
        for plugin_name, plugin_info in list(self.active_plugins.items()):
            if plugin_info['activated_at'] < cutoff_date:
                if self.uninstall_plugin(plugin_name):
                    cleaned += 1
        
        logger.info(f"Cleaned up {cleaned} inactive plugins")
        return cleaned
    
    def validate_system_integrity(self) -> Dict[str, Any]:
        """Validate system integrity and plugin consistency"""
        issues = []
        
        # Check for missing dependencies
        for plugin_name, plugin_info in self.active_plugins.items():
            plugin = plugin_info['metadata']
            if plugin.dependencies:
                dep_status = self.dependency_manager.check_dependencies(plugin.dependencies)
                missing_deps = [name for name, status in dep_status.items() 
                               if status.value != 'installed']
                if missing_deps:
                    issues.append(f"Plugin {plugin_name} has missing dependencies: {missing_deps}")
        
        # Check registry consistency
        registry_plugins = self.registry.list_plugins(status=PluginStatus.INSTALLED)
        for plugin in registry_plugins:
            if plugin.name not in self.active_plugins:
                issues.append(f"Plugin {plugin.name} marked as installed but not active")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'checked_at': datetime.utcnow().isoformat()
        }
