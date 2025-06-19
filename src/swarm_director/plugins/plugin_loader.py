"""
Plugin Loader

Dynamic plugin loading system that handles loading, instantiation, and 
management of plugin instances at runtime.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Type, Callable, Union
import importlib
import importlib.util
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from .plugin_registry import PluginMetadata, PluginStatus

logger = logging.getLogger(__name__)


class LoaderStrategy(Enum):
    """Strategies for loading plugins"""
    DIRECT_IMPORT = "direct_import"
    FILE_IMPORT = "file_import"
    PACKAGE_IMPORT = "package_import"
    DYNAMIC_IMPORT = "dynamic_import"


class PluginLoadResult:
    """Result of plugin loading operation"""
    
    def __init__(self):
        self.success = False
        self.plugin_instance = None
        self.plugin_class = None
        self.metadata = None
        self.error_message = None
        self.load_time = None
        self.strategy_used = None


class PluginLoader:
    """
    Dynamic plugin loading system that handles loading and instantiation
    of plugins at runtime using various loading strategies.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.loaded_plugins: Dict[str, Any] = {}
        self.plugin_modules: Dict[str, Any] = {}
        self.load_history: List[Dict[str, Any]] = []
        
        # Default loading strategy
        self.default_strategy = LoaderStrategy(
            self.config.get('default_strategy', 'direct_import')
        )
        
        # Plugin search paths
        self.search_paths = self.config.get('search_paths', [])
        self._add_default_search_paths()
        
        logger.info("Plugin loader initialized successfully")
    
    def _add_default_search_paths(self):
        """Add default plugin search paths"""
        # Add current directory plugins folder
        current_dir = Path(__file__).parent.parent
        plugin_dir = current_dir / "plugins"
        if plugin_dir.exists():
            self.search_paths.append(str(plugin_dir))
        
        # Add user plugins directory
        user_plugins = Path.home() / ".swarm_director" / "plugins"
        if user_plugins.exists():
            self.search_paths.append(str(user_plugins))
    
    def load_plugin(self, plugin_metadata: PluginMetadata, 
                    strategy: Optional[LoaderStrategy] = None,
                    config: Optional[Dict[str, Any]] = None) -> PluginLoadResult:
        """
        Load a plugin based on its metadata
        
        Args:
            plugin_metadata: Plugin metadata containing loading information
            strategy: Loading strategy to use (defaults to configured strategy)
            config: Optional configuration for the plugin
            
        Returns:
            PluginLoadResult with loading outcome
        """
        result = PluginLoadResult()
        result.metadata = plugin_metadata
        result.strategy_used = strategy or self.default_strategy
        
        start_time = datetime.utcnow()
        
        try:
            logger.info(f"Loading plugin: {plugin_metadata.name} v{plugin_metadata.version}")
            
            # Check if already loaded
            if plugin_metadata.name in self.loaded_plugins:
                logger.info(f"Plugin {plugin_metadata.name} already loaded")
                result.success = True
                result.plugin_instance = self.loaded_plugins[plugin_metadata.name]
                return result
            
            # Load based on strategy
            if result.strategy_used == LoaderStrategy.DIRECT_IMPORT:
                success = self._load_direct_import(plugin_metadata, result)
            elif result.strategy_used == LoaderStrategy.FILE_IMPORT:
                success = self._load_file_import(plugin_metadata, result)
            elif result.strategy_used == LoaderStrategy.PACKAGE_IMPORT:
                success = self._load_package_import(plugin_metadata, result)
            elif result.strategy_used == LoaderStrategy.DYNAMIC_IMPORT:
                success = self._load_dynamic_import(plugin_metadata, result)
            else:
                result.error_message = f"Unknown loading strategy: {result.strategy_used}"
                success = False
            
            if success:
                # Initialize plugin instance
                if result.plugin_class:
                    result.plugin_instance = self._instantiate_plugin(
                        result.plugin_class, config or {}
                    )
                    
                    if result.plugin_instance:
                        # Store loaded plugin
                        self.loaded_plugins[plugin_metadata.name] = result.plugin_instance
                        result.success = True
                        logger.info(f"Successfully loaded plugin: {plugin_metadata.name}")
                    else:
                        result.error_message = "Failed to instantiate plugin"
                        result.success = False
                else:
                    result.error_message = "Plugin class not found after loading"
                    result.success = False
            
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_metadata.name}: {e}", exc_info=True)
            result.error_message = f"Loading failed: {str(e)}"
            result.success = False
        
        finally:
            result.load_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Record in history
            self.load_history.append({
                'plugin_name': plugin_metadata.name,
                'strategy': result.strategy_used.value,
                'success': result.success,
                'load_time': result.load_time,
                'error': result.error_message,
                'timestamp': datetime.utcnow().isoformat()
            })
        
        return result
    
    def _load_direct_import(self, metadata: PluginMetadata, result: PluginLoadResult) -> bool:
        """Load plugin using direct import"""
        try:
            if not metadata.entry_point:
                result.error_message = "No entry point specified for direct import"
                return False
            
            # Parse entry point (format: "module.submodule:ClassName")
            if ':' not in metadata.entry_point:
                result.error_message = "Invalid entry point format"
                return False
            
            module_path, class_name = metadata.entry_point.split(':', 1)
            
            # Import module
            module = importlib.import_module(module_path)
            self.plugin_modules[metadata.name] = module
            
            # Get plugin class
            if hasattr(module, class_name):
                result.plugin_class = getattr(module, class_name)
                return True
            else:
                result.error_message = f"Class {class_name} not found in module {module_path}"
                return False
                
        except ImportError as e:
            result.error_message = f"Import error: {str(e)}"
            return False
        except Exception as e:
            result.error_message = f"Direct import failed: {str(e)}"
            return False
    
    def _load_file_import(self, metadata: PluginMetadata, result: PluginLoadResult) -> bool:
        """Load plugin from file"""
        try:
            if not metadata.install_path:
                result.error_message = "No install path specified for file import"
                return False
            
            plugin_file = Path(metadata.install_path)
            if not plugin_file.exists():
                result.error_message = f"Plugin file not found: {plugin_file}"
                return False
            
            # Load module from file
            spec = importlib.util.spec_from_file_location(metadata.name, plugin_file)
            if not spec or not spec.loader:
                result.error_message = "Failed to create module spec"
                return False
            
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
            self.plugin_modules[metadata.name] = module
            
            # Find plugin class
            plugin_class = self._find_plugin_class(module, metadata)
            if plugin_class:
                result.plugin_class = plugin_class
                return True
            else:
                result.error_message = "No suitable plugin class found in module"
                return False
                
        except Exception as e:
            result.error_message = f"File import failed: {str(e)}"
            return False
    
    def _load_package_import(self, metadata: PluginMetadata, result: PluginLoadResult) -> bool:
        """Load plugin from package"""
        try:
            # Add plugin path to sys.path if needed
            if metadata.install_path:
                plugin_path = Path(metadata.install_path).parent
                if str(plugin_path) not in sys.path:
                    sys.path.insert(0, str(plugin_path))
            
            # Import package
            package_name = metadata.name
            package = importlib.import_module(package_name)
            self.plugin_modules[metadata.name] = package
            
            # Find plugin class
            plugin_class = self._find_plugin_class(package, metadata)
            if plugin_class:
                result.plugin_class = plugin_class
                return True
            else:
                result.error_message = "No suitable plugin class found in package"
                return False
                
        except ImportError as e:
            result.error_message = f"Package import error: {str(e)}"
            return False
        except Exception as e:
            result.error_message = f"Package import failed: {str(e)}"
            return False
    
    def _load_dynamic_import(self, metadata: PluginMetadata, result: PluginLoadResult) -> bool:
        """Load plugin using dynamic discovery"""
        try:
            # Search for plugin in search paths
            for search_path in self.search_paths:
                plugin_path = Path(search_path) / metadata.name
                
                # Check for Python file
                py_file = plugin_path.with_suffix('.py')
                if py_file.exists():
                    metadata.install_path = str(py_file)
                    return self._load_file_import(metadata, result)
                
                # Check for package directory
                if plugin_path.is_dir():
                    init_file = plugin_path / '__init__.py'
                    if init_file.exists():
                        metadata.install_path = str(init_file)
                        return self._load_package_import(metadata, result)
            
            result.error_message = f"Plugin {metadata.name} not found in search paths"
            return False
            
        except Exception as e:
            result.error_message = f"Dynamic import failed: {str(e)}"
            return False
    
    def _find_plugin_class(self, module: Any, metadata: PluginMetadata) -> Optional[Type]:
        """Find the main plugin class in a module"""
        # Look for class with plugin name
        class_name = metadata.name.replace('_', '').replace('-', '') + 'Plugin'
        if hasattr(module, class_name):
            return getattr(module, class_name)
        
        # Look for class ending with 'Plugin'
        for attr_name in dir(module):
            if attr_name.endswith('Plugin') and not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if isinstance(attr, type):
                    return attr
        
        # Look for main class
        if hasattr(module, 'Plugin'):
            return getattr(module, 'Plugin')
        
        # Look for any class that looks like a plugin
        for attr_name in dir(module):
            if not attr_name.startswith('_'):
                attr = getattr(module, attr_name)
                if isinstance(attr, type) and hasattr(attr, '__init__'):
                    # Check if it has plugin-like methods
                    if any(method in dir(attr) for method in ['execute', 'run', 'process']):
                        return attr
        
        return None
    
    def _instantiate_plugin(self, plugin_class: Type, config: Dict[str, Any]) -> Optional[Any]:
        """Instantiate a plugin class"""
        try:
            # Try to instantiate with config
            try:
                return plugin_class(config)
            except TypeError:
                # Try without config
                return plugin_class()
                
        except Exception as e:
            logger.error(f"Error instantiating plugin class {plugin_class.__name__}: {e}")
            return None
    
    def unload_plugin(self, plugin_name: str) -> bool:
        """Unload a plugin"""
        try:
            if plugin_name in self.loaded_plugins:
                # Call cleanup if available
                plugin_instance = self.loaded_plugins[plugin_name]
                if hasattr(plugin_instance, 'cleanup'):
                    plugin_instance.cleanup()
                
                # Remove from loaded plugins
                del self.loaded_plugins[plugin_name]
                
                # Remove module if loaded
                if plugin_name in self.plugin_modules:
                    del self.plugin_modules[plugin_name]
                
                logger.info(f"Unloaded plugin: {plugin_name}")
                return True
            else:
                logger.warning(f"Plugin {plugin_name} not loaded")
                return False
                
        except Exception as e:
            logger.error(f"Error unloading plugin {plugin_name}: {e}")
            return False
    
    def get_loaded_plugins(self) -> Dict[str, Any]:
        """Get all loaded plugins"""
        return self.loaded_plugins.copy()
    
    def is_plugin_loaded(self, plugin_name: str) -> bool:
        """Check if a plugin is loaded"""
        return plugin_name in self.loaded_plugins
    
    def reload_plugin(self, plugin_name: str, metadata: PluginMetadata) -> PluginLoadResult:
        """Reload a plugin"""
        # Unload first
        self.unload_plugin(plugin_name)
        
        # Load again
        return self.load_plugin(metadata)
    
    def get_load_statistics(self) -> Dict[str, Any]:
        """Get loading statistics"""
        total_loads = len(self.load_history)
        successful_loads = len([h for h in self.load_history if h['success']])
        
        return {
            'total_loads': total_loads,
            'successful_loads': successful_loads,
            'failed_loads': total_loads - successful_loads,
            'success_rate': successful_loads / total_loads if total_loads > 0 else 0,
            'currently_loaded': len(self.loaded_plugins),
            'load_history': self.load_history[-10:]  # Last 10 loads
        } 