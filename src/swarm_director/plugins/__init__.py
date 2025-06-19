"""
Modular Plugin Architecture for SwarmDirector

This module provides a comprehensive plugin system that allows dynamic 
installation of new agents, tools, and their dependencies when required 
capabilities don't exist in the current system.

Components:
- PluginManager: Central plugin management and loading
- AgentFactory: Dynamic agent instantiation based on requirements
- DependencyManager: Automatic dependency installation and management
- CapabilityDiscovery: Identifies missing capabilities and suggests plugins
- PluginRegistry: Plugin registration and metadata management
"""

from .plugin_manager import PluginManager, PluginStatus
from .agent_factory import AgentFactory, AgentTemplate
from .dependency_manager import DependencyManager, DependencyType
from .capability_discovery import CapabilityDiscovery, CapabilityGap
from .plugin_registry import PluginRegistry, PluginMetadata
from .plugin_loader import PluginLoader, LoaderStrategy

__all__ = [
    'PluginManager',
    'PluginStatus',
    'AgentFactory',
    'AgentTemplate',
    'DependencyManager',
    'DependencyType',
    'CapabilityDiscovery',
    'CapabilityGap',
    'PluginRegistry',
    'PluginMetadata',
    'PluginLoader',
    'LoaderStrategy'
]
