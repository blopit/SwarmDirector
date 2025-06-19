"""
Plugin Registry

Manages plugin registration, metadata, and discovery for the SwarmDirector
plugin architecture.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime
import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)


class PluginType(Enum):
    """Types of plugins"""
    AGENT = "agent"
    TOOL = "tool"
    VALIDATOR = "validator"
    INTEGRATION = "integration"
    WORKFLOW = "workflow"
    EXTENSION = "extension"


class PluginStatus(Enum):
    """Plugin status"""
    AVAILABLE = "available"
    INSTALLED = "installed"
    ACTIVE = "active"
    DISABLED = "disabled"
    ERROR = "error"
    UPDATING = "updating"


@dataclass
class PluginDependency:
    """Plugin dependency specification"""
    name: str
    version: str
    type: str  # 'python', 'system', 'plugin'
    optional: bool = False
    install_command: Optional[str] = None


@dataclass
class PluginCapability:
    """Plugin capability specification"""
    name: str
    description: str
    category: str
    parameters: Dict[str, Any] = field(default_factory=dict)
    requirements: List[str] = field(default_factory=list)


@dataclass
class PluginMetadata:
    """Complete plugin metadata"""
    # Basic information
    name: str
    version: str
    description: str
    author: str
    plugin_type: PluginType
    
    # Capabilities and dependencies
    capabilities: List[PluginCapability] = field(default_factory=list)
    dependencies: List[PluginDependency] = field(default_factory=list)
    
    # Installation and configuration
    entry_point: str = ""
    config_schema: Dict[str, Any] = field(default_factory=dict)
    install_script: Optional[str] = None
    
    # Metadata
    tags: List[str] = field(default_factory=list)
    license: str = "MIT"
    homepage: Optional[str] = None
    repository: Optional[str] = None
    
    # Runtime information
    status: PluginStatus = PluginStatus.AVAILABLE
    install_path: Optional[str] = None
    installed_at: Optional[datetime] = None
    last_updated: Optional[datetime] = None
    
    # Compatibility
    min_swarm_director_version: str = "1.0.0"
    max_swarm_director_version: Optional[str] = None
    python_version: str = ">=3.8"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'name': self.name,
            'version': self.version,
            'description': self.description,
            'author': self.author,
            'plugin_type': self.plugin_type.value,
            'capabilities': [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'category': cap.category,
                    'parameters': cap.parameters,
                    'requirements': cap.requirements
                }
                for cap in self.capabilities
            ],
            'dependencies': [
                {
                    'name': dep.name,
                    'version': dep.version,
                    'type': dep.type,
                    'optional': dep.optional,
                    'install_command': dep.install_command
                }
                for dep in self.dependencies
            ],
            'entry_point': self.entry_point,
            'config_schema': self.config_schema,
            'install_script': self.install_script,
            'tags': self.tags,
            'license': self.license,
            'homepage': self.homepage,
            'repository': self.repository,
            'status': self.status.value,
            'install_path': self.install_path,
            'installed_at': self.installed_at.isoformat() if self.installed_at else None,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None,
            'min_swarm_director_version': self.min_swarm_director_version,
            'max_swarm_director_version': self.max_swarm_director_version,
            'python_version': self.python_version
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'PluginMetadata':
        """Create from dictionary"""
        metadata = cls(
            name=data['name'],
            version=data['version'],
            description=data['description'],
            author=data['author'],
            plugin_type=PluginType(data['plugin_type'])
        )
        
        # Set capabilities
        for cap_data in data.get('capabilities', []):
            capability = PluginCapability(
                name=cap_data['name'],
                description=cap_data['description'],
                category=cap_data['category'],
                parameters=cap_data.get('parameters', {}),
                requirements=cap_data.get('requirements', [])
            )
            metadata.capabilities.append(capability)
        
        # Set dependencies
        for dep_data in data.get('dependencies', []):
            dependency = PluginDependency(
                name=dep_data['name'],
                version=dep_data['version'],
                type=dep_data['type'],
                optional=dep_data.get('optional', False),
                install_command=dep_data.get('install_command')
            )
            metadata.dependencies.append(dependency)
        
        # Set other fields
        metadata.entry_point = data.get('entry_point', '')
        metadata.config_schema = data.get('config_schema', {})
        metadata.install_script = data.get('install_script')
        metadata.tags = data.get('tags', [])
        metadata.license = data.get('license', 'MIT')
        metadata.homepage = data.get('homepage')
        metadata.repository = data.get('repository')
        metadata.status = PluginStatus(data.get('status', 'available'))
        metadata.install_path = data.get('install_path')
        metadata.min_swarm_director_version = data.get('min_swarm_director_version', '1.0.0')
        metadata.max_swarm_director_version = data.get('max_swarm_director_version')
        metadata.python_version = data.get('python_version', '>=3.8')
        
        # Parse timestamps
        if data.get('installed_at'):
            metadata.installed_at = datetime.fromisoformat(data['installed_at'])
        if data.get('last_updated'):
            metadata.last_updated = datetime.fromisoformat(data['last_updated'])
        
        return metadata


class PluginRegistry:
    """
    Central registry for managing plugin metadata and discovery
    """
    
    def __init__(self, registry_path: Optional[str] = None):
        self.registry_path = registry_path or os.path.join(
            os.path.expanduser("~"), ".swarm_director", "plugins", "registry.json"
        )
        self.plugins: Dict[str, PluginMetadata] = {}
        self.capability_index: Dict[str, List[str]] = {}  # capability -> plugin names
        self.tag_index: Dict[str, List[str]] = {}  # tag -> plugin names
        
        # Ensure registry directory exists
        os.makedirs(os.path.dirname(self.registry_path), exist_ok=True)
        
        # Load existing registry
        self.load_registry()
    
    def register_plugin(self, metadata: PluginMetadata) -> bool:
        """Register a plugin in the registry"""
        try:
            # Validate metadata
            if not self._validate_metadata(metadata):
                return False
            
            # Check for conflicts
            if metadata.name in self.plugins:
                existing = self.plugins[metadata.name]
                if existing.version == metadata.version:
                    logger.warning(f"Plugin {metadata.name} v{metadata.version} already registered")
                    return False
            
            # Register plugin
            self.plugins[metadata.name] = metadata
            
            # Update indexes
            self._update_capability_index(metadata)
            self._update_tag_index(metadata)
            
            # Save registry
            self.save_registry()
            
            logger.info(f"Registered plugin: {metadata.name} v{metadata.version}")
            return True
            
        except Exception as e:
            logger.error(f"Error registering plugin {metadata.name}: {e}")
            return False
    
    def unregister_plugin(self, plugin_name: str) -> bool:
        """Unregister a plugin from the registry"""
        try:
            if plugin_name not in self.plugins:
                logger.warning(f"Plugin {plugin_name} not found in registry")
                return False
            
            metadata = self.plugins[plugin_name]
            
            # Remove from indexes
            self._remove_from_capability_index(metadata)
            self._remove_from_tag_index(metadata)
            
            # Remove from registry
            del self.plugins[plugin_name]
            
            # Save registry
            self.save_registry()
            
            logger.info(f"Unregistered plugin: {plugin_name}")
            return True
            
        except Exception as e:
            logger.error(f"Error unregistering plugin {plugin_name}: {e}")
            return False
    
    def get_plugin(self, plugin_name: str) -> Optional[PluginMetadata]:
        """Get plugin metadata by name"""
        return self.plugins.get(plugin_name)
    
    def list_plugins(self, plugin_type: Optional[PluginType] = None,
                     status: Optional[PluginStatus] = None,
                     tags: Optional[List[str]] = None) -> List[PluginMetadata]:
        """List plugins with optional filtering"""
        plugins = list(self.plugins.values())
        
        if plugin_type:
            plugins = [p for p in plugins if p.plugin_type == plugin_type]
        
        if status:
            plugins = [p for p in plugins if p.status == status]
        
        if tags:
            plugins = [p for p in plugins if any(tag in p.tags for tag in tags)]
        
        return plugins
    
    def find_plugins_by_capability(self, capability_name: str) -> List[PluginMetadata]:
        """Find plugins that provide a specific capability"""
        plugin_names = self.capability_index.get(capability_name, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def find_plugins_by_tag(self, tag: str) -> List[PluginMetadata]:
        """Find plugins with a specific tag"""
        plugin_names = self.tag_index.get(tag, [])
        return [self.plugins[name] for name in plugin_names if name in self.plugins]
    
    def search_plugins(self, query: str) -> List[PluginMetadata]:
        """Search plugins by name, description, or tags"""
        query_lower = query.lower()
        results = []
        
        for plugin in self.plugins.values():
            if (query_lower in plugin.name.lower() or
                query_lower in plugin.description.lower() or
                any(query_lower in tag.lower() for tag in plugin.tags)):
                results.append(plugin)
        
        return results
    
    def get_capability_providers(self, capability_name: str) -> Dict[str, List[str]]:
        """Get all plugins that provide capabilities matching the pattern"""
        providers = {}
        
        for plugin_name, plugin in self.plugins.items():
            matching_capabilities = [
                cap.name for cap in plugin.capabilities
                if capability_name.lower() in cap.name.lower()
            ]
            
            if matching_capabilities:
                providers[plugin_name] = matching_capabilities
        
        return providers
    
    def update_plugin_status(self, plugin_name: str, status: PluginStatus) -> bool:
        """Update plugin status"""
        if plugin_name not in self.plugins:
            return False
        
        self.plugins[plugin_name].status = status
        self.plugins[plugin_name].last_updated = datetime.utcnow()
        
        self.save_registry()
        return True
    
    def load_registry(self):
        """Load registry from file"""
        try:
            if os.path.exists(self.registry_path):
                with open(self.registry_path, 'r') as f:
                    data = json.load(f)
                
                for plugin_data in data.get('plugins', []):
                    metadata = PluginMetadata.from_dict(plugin_data)
                    self.plugins[metadata.name] = metadata
                    self._update_capability_index(metadata)
                    self._update_tag_index(metadata)
                
                logger.info(f"Loaded {len(self.plugins)} plugins from registry")
            else:
                logger.info("No existing registry found, starting with empty registry")
                
        except Exception as e:
            logger.error(f"Error loading plugin registry: {e}")
    
    def save_registry(self):
        """Save registry to file"""
        try:
            data = {
                'version': '1.0.0',
                'updated_at': datetime.utcnow().isoformat(),
                'plugins': [plugin.to_dict() for plugin in self.plugins.values()]
            }
            
            with open(self.registry_path, 'w') as f:
                json.dump(data, f, indent=2)
                
        except Exception as e:
            logger.error(f"Error saving plugin registry: {e}")
    
    def _validate_metadata(self, metadata: PluginMetadata) -> bool:
        """Validate plugin metadata"""
        if not metadata.name or not metadata.version:
            logger.error("Plugin name and version are required")
            return False
        
        if not metadata.entry_point and metadata.plugin_type != PluginType.EXTENSION:
            logger.error("Entry point is required for non-extension plugins")
            return False
        
        return True
    
    def _update_capability_index(self, metadata: PluginMetadata):
        """Update capability index for a plugin"""
        for capability in metadata.capabilities:
            if capability.name not in self.capability_index:
                self.capability_index[capability.name] = []
            
            if metadata.name not in self.capability_index[capability.name]:
                self.capability_index[capability.name].append(metadata.name)
    
    def _update_tag_index(self, metadata: PluginMetadata):
        """Update tag index for a plugin"""
        for tag in metadata.tags:
            if tag not in self.tag_index:
                self.tag_index[tag] = []
            
            if metadata.name not in self.tag_index[tag]:
                self.tag_index[tag].append(metadata.name)
    
    def _remove_from_capability_index(self, metadata: PluginMetadata):
        """Remove plugin from capability index"""
        for capability in metadata.capabilities:
            if capability.name in self.capability_index:
                if metadata.name in self.capability_index[capability.name]:
                    self.capability_index[capability.name].remove(metadata.name)
                
                # Clean up empty entries
                if not self.capability_index[capability.name]:
                    del self.capability_index[capability.name]
    
    def _remove_from_tag_index(self, metadata: PluginMetadata):
        """Remove plugin from tag index"""
        for tag in metadata.tags:
            if tag in self.tag_index:
                if metadata.name in self.tag_index[tag]:
                    self.tag_index[tag].remove(metadata.name)
                
                # Clean up empty entries
                if not self.tag_index[tag]:
                    del self.tag_index[tag]
    
    def get_registry_statistics(self) -> Dict[str, Any]:
        """Get registry statistics"""
        stats = {
            'total_plugins': len(self.plugins),
            'by_type': {},
            'by_status': {},
            'total_capabilities': len(self.capability_index),
            'total_tags': len(self.tag_index)
        }
        
        # Count by type
        for plugin_type in PluginType:
            count = len([p for p in self.plugins.values() if p.plugin_type == plugin_type])
            stats['by_type'][plugin_type.value] = count
        
        # Count by status
        for status in PluginStatus:
            count = len([p for p in self.plugins.values() if p.status == status])
            stats['by_status'][status.value] = count
        
        return stats
