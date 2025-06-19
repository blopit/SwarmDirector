"""
Dependency Manager

Handles automatic installation and management of plugin dependencies,
including Python packages, system libraries, and other plugins.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Tuple
import subprocess
import sys
import os
import logging
import json
import shutil
from pathlib import Path
import importlib.util
import pkg_resources
from packaging import version
from datetime import datetime

from .plugin_registry import PluginDependency

logger = logging.getLogger(__name__)


class DependencyType(Enum):
    """Types of dependencies"""
    PYTHON_PACKAGE = "python"
    SYSTEM_PACKAGE = "system"
    PLUGIN = "plugin"
    BINARY = "binary"
    LIBRARY = "library"


class InstallationStatus(Enum):
    """Installation status"""
    NOT_INSTALLED = "not_installed"
    INSTALLED = "installed"
    OUTDATED = "outdated"
    FAILED = "failed"
    UNKNOWN = "unknown"


class DependencyManager:
    """
    Manages automatic installation and verification of plugin dependencies
    """
    
    def __init__(self, cache_dir: Optional[str] = None):
        self.cache_dir = cache_dir or os.path.join(
            os.path.expanduser("~"), ".swarm_director", "dependencies"
        )
        os.makedirs(self.cache_dir, exist_ok=True)
        
        self.installation_log: List[Dict[str, Any]] = []
        self.dependency_cache: Dict[str, Dict[str, Any]] = {}
        
        # Load dependency cache
        self._load_dependency_cache()
    
    def check_dependencies(self, dependencies: List[PluginDependency]) -> Dict[str, InstallationStatus]:
        """Check status of all dependencies"""
        status_map = {}
        
        for dependency in dependencies:
            status = self._check_single_dependency(dependency)
            status_map[dependency.name] = status
            
            logger.debug(f"Dependency {dependency.name}: {status.value}")
        
        return status_map
    
    def install_dependencies(self, dependencies: List[PluginDependency], 
                           force_reinstall: bool = False) -> Dict[str, bool]:
        """Install all dependencies"""
        results = {}
        
        for dependency in dependencies:
            if dependency.optional:
                logger.info(f"Installing optional dependency: {dependency.name}")
            else:
                logger.info(f"Installing required dependency: {dependency.name}")
            
            try:
                success = self._install_single_dependency(dependency, force_reinstall)
                results[dependency.name] = success
                
                # Log installation
                self.installation_log.append({
                    'dependency': dependency.name,
                    'version': dependency.version,
                    'type': dependency.type,
                    'success': success,
                    'timestamp': datetime.utcnow().isoformat(),
                    'optional': dependency.optional
                })
                
                if not success and not dependency.optional:
                    logger.error(f"Failed to install required dependency: {dependency.name}")
                    break
                    
            except Exception as e:
                logger.error(f"Error installing dependency {dependency.name}: {e}")
                results[dependency.name] = False
                
                if not dependency.optional:
                    break
        
        # Update cache
        self._save_dependency_cache()
        
        return results
    
    def _check_single_dependency(self, dependency: PluginDependency) -> InstallationStatus:
        """Check status of a single dependency"""
        try:
            if dependency.type == DependencyType.PYTHON_PACKAGE.value:
                return self._check_python_package(dependency)
            elif dependency.type == DependencyType.SYSTEM_PACKAGE.value:
                return self._check_system_package(dependency)
            elif dependency.type == DependencyType.PLUGIN.value:
                return self._check_plugin_dependency(dependency)
            elif dependency.type == DependencyType.BINARY.value:
                return self._check_binary_dependency(dependency)
            else:
                logger.warning(f"Unknown dependency type: {dependency.type}")
                return InstallationStatus.UNKNOWN
                
        except Exception as e:
            logger.error(f"Error checking dependency {dependency.name}: {e}")
            return InstallationStatus.UNKNOWN
    
    def _check_python_package(self, dependency: PluginDependency) -> InstallationStatus:
        """Check Python package dependency"""
        try:
            # Try to get installed version
            installed_version = pkg_resources.get_distribution(dependency.name).version
            
            # Compare versions
            if self._version_satisfies(installed_version, dependency.version):
                return InstallationStatus.INSTALLED
            else:
                return InstallationStatus.OUTDATED
                
        except pkg_resources.DistributionNotFound:
            return InstallationStatus.NOT_INSTALLED
        except Exception as e:
            logger.error(f"Error checking Python package {dependency.name}: {e}")
            return InstallationStatus.UNKNOWN
    
    def _check_system_package(self, dependency: PluginDependency) -> InstallationStatus:
        """Check system package dependency"""
        # This is platform-specific and simplified
        # In production, would need more sophisticated detection
        
        if sys.platform.startswith('linux'):
            return self._check_linux_package(dependency)
        elif sys.platform == 'darwin':
            return self._check_macos_package(dependency)
        elif sys.platform.startswith('win'):
            return self._check_windows_package(dependency)
        else:
            logger.warning(f"Unsupported platform for system packages: {sys.platform}")
            return InstallationStatus.UNKNOWN
    
    def _check_linux_package(self, dependency: PluginDependency) -> InstallationStatus:
        """Check Linux system package"""
        try:
            # Try dpkg first (Debian/Ubuntu)
            result = subprocess.run(
                ['dpkg', '-l', dependency.name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return InstallationStatus.INSTALLED
            
            # Try rpm (RedHat/CentOS)
            result = subprocess.run(
                ['rpm', '-q', dependency.name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return InstallationStatus.INSTALLED
            
            return InstallationStatus.NOT_INSTALLED
            
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return InstallationStatus.UNKNOWN
    
    def _check_macos_package(self, dependency: PluginDependency) -> InstallationStatus:
        """Check macOS system package"""
        try:
            # Check with brew
            result = subprocess.run(
                ['brew', 'list', dependency.name],
                capture_output=True, text=True, timeout=10
            )
            if result.returncode == 0:
                return InstallationStatus.INSTALLED
            else:
                return InstallationStatus.NOT_INSTALLED
                
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return InstallationStatus.UNKNOWN
    
    def _check_windows_package(self, dependency: PluginDependency) -> InstallationStatus:
        """Check Windows system package"""
        # Simplified - would need more sophisticated detection
        return InstallationStatus.UNKNOWN
    
    def _check_plugin_dependency(self, dependency: PluginDependency) -> InstallationStatus:
        """Check plugin dependency"""
        # This would integrate with the plugin registry
        # For now, simplified implementation
        return InstallationStatus.UNKNOWN
    
    def _check_binary_dependency(self, dependency: PluginDependency) -> InstallationStatus:
        """Check binary dependency"""
        try:
            # Check if binary is in PATH
            if shutil.which(dependency.name):
                return InstallationStatus.INSTALLED
            else:
                return InstallationStatus.NOT_INSTALLED
                
        except Exception as e:
            logger.error(f"Error checking binary {dependency.name}: {e}")
            return InstallationStatus.UNKNOWN
    
    def _install_single_dependency(self, dependency: PluginDependency, 
                                   force_reinstall: bool = False) -> bool:
        """Install a single dependency"""
        try:
            # Check if already installed (unless force reinstall)
            if not force_reinstall:
                status = self._check_single_dependency(dependency)
                if status == InstallationStatus.INSTALLED:
                    logger.info(f"Dependency {dependency.name} already installed")
                    return True
            
            if dependency.type == DependencyType.PYTHON_PACKAGE.value:
                return self._install_python_package(dependency)
            elif dependency.type == DependencyType.SYSTEM_PACKAGE.value:
                return self._install_system_package(dependency)
            elif dependency.type == DependencyType.PLUGIN.value:
                return self._install_plugin_dependency(dependency)
            elif dependency.type == DependencyType.BINARY.value:
                return self._install_binary_dependency(dependency)
            else:
                logger.error(f"Unknown dependency type: {dependency.type}")
                return False
                
        except Exception as e:
            logger.error(f"Error installing dependency {dependency.name}: {e}")
            return False
    
    def _install_python_package(self, dependency: PluginDependency) -> bool:
        """Install Python package dependency"""
        try:
            # Use custom install command if provided
            if dependency.install_command:
                cmd = dependency.install_command.split()
            else:
                # Default pip install
                package_spec = f"{dependency.name}{dependency.version}"
                cmd = [sys.executable, '-m', 'pip', 'install', package_spec]
            
            logger.info(f"Installing Python package: {' '.join(cmd)}")
            
            result = subprocess.run(
                cmd, capture_output=True, text=True, timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Successfully installed Python package: {dependency.name}")
                return True
            else:
                logger.error(f"Failed to install Python package {dependency.name}: {result.stderr}")
                return False
                
        except subprocess.TimeoutExpired:
            logger.error(f"Timeout installing Python package: {dependency.name}")
            return False
        except Exception as e:
            logger.error(f"Error installing Python package {dependency.name}: {e}")
            return False
    
    def _install_system_package(self, dependency: PluginDependency) -> bool:
        """Install system package dependency"""
        if dependency.install_command:
            try:
                cmd = dependency.install_command.split()
                logger.info(f"Installing system package: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed system package: {dependency.name}")
                    return True
                else:
                    logger.error(f"Failed to install system package {dependency.name}: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout installing system package: {dependency.name}")
                return False
            except Exception as e:
                logger.error(f"Error installing system package {dependency.name}: {e}")
                return False
        else:
            logger.error(f"No install command provided for system package: {dependency.name}")
            return False
    
    def _install_plugin_dependency(self, dependency: PluginDependency) -> bool:
        """Install plugin dependency"""
        # This would integrate with the plugin manager
        logger.info(f"Plugin dependency installation not yet implemented: {dependency.name}")
        return False
    
    def _install_binary_dependency(self, dependency: PluginDependency) -> bool:
        """Install binary dependency"""
        if dependency.install_command:
            try:
                cmd = dependency.install_command.split()
                logger.info(f"Installing binary: {' '.join(cmd)}")
                
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=300
                )
                
                if result.returncode == 0:
                    logger.info(f"Successfully installed binary: {dependency.name}")
                    return True
                else:
                    logger.error(f"Failed to install binary {dependency.name}: {result.stderr}")
                    return False
                    
            except subprocess.TimeoutExpired:
                logger.error(f"Timeout installing binary: {dependency.name}")
                return False
            except Exception as e:
                logger.error(f"Error installing binary {dependency.name}: {e}")
                return False
        else:
            logger.error(f"No install command provided for binary: {dependency.name}")
            return False
    
    def _version_satisfies(self, installed_version: str, required_version: str) -> bool:
        """Check if installed version satisfies requirement"""
        try:
            # Handle version specifiers like ">=1.0.0", "==2.1.0", etc.
            if required_version.startswith('>='):
                return version.parse(installed_version) >= version.parse(required_version[2:])
            elif required_version.startswith('<='):
                return version.parse(installed_version) <= version.parse(required_version[2:])
            elif required_version.startswith('>'):
                return version.parse(installed_version) > version.parse(required_version[1:])
            elif required_version.startswith('<'):
                return version.parse(installed_version) < version.parse(required_version[1:])
            elif required_version.startswith('=='):
                return version.parse(installed_version) == version.parse(required_version[2:])
            else:
                # Default to exact match
                return version.parse(installed_version) == version.parse(required_version)
                
        except Exception as e:
            logger.error(f"Error comparing versions {installed_version} vs {required_version}: {e}")
            return False
    
    def _load_dependency_cache(self):
        """Load dependency cache from file"""
        cache_file = os.path.join(self.cache_dir, "dependency_cache.json")
        try:
            if os.path.exists(cache_file):
                with open(cache_file, 'r') as f:
                    self.dependency_cache = json.load(f)
                logger.debug(f"Loaded dependency cache with {len(self.dependency_cache)} entries")
        except Exception as e:
            logger.error(f"Error loading dependency cache: {e}")
            self.dependency_cache = {}
    
    def _save_dependency_cache(self):
        """Save dependency cache to file"""
        cache_file = os.path.join(self.cache_dir, "dependency_cache.json")
        try:
            with open(cache_file, 'w') as f:
                json.dump(self.dependency_cache, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving dependency cache: {e}")
    
    def get_installation_log(self) -> List[Dict[str, Any]]:
        """Get installation log"""
        return self.installation_log.copy()
    
    def clear_cache(self):
        """Clear dependency cache"""
        self.dependency_cache = {}
        self._save_dependency_cache()
        logger.info("Dependency cache cleared")
    
    def get_dependency_statistics(self) -> Dict[str, Any]:
        """Get dependency statistics"""
        total_installations = len(self.installation_log)
        successful_installations = len([log for log in self.installation_log if log['success']])
        
        return {
            'total_installations': total_installations,
            'successful_installations': successful_installations,
            'success_rate': successful_installations / total_installations if total_installations > 0 else 0.0,
            'cache_entries': len(self.dependency_cache)
        }
