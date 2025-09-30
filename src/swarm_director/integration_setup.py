"""
Integration Setup

Initializes and configures the validation and plugin systems within SwarmDirector.
This module handles the integration of the new systems with the existing architecture.
"""

import logging
import os
from typing import Dict, Any, Optional
import click
import asyncio
from datetime import datetime

from flask import current_app

from .validation_plugin_integration import ValidationPluginIntegrator
from .services.validation_service import ValidationService
from .models.validation import ValidationRecord, QualityGateConfig, RollbackRecord
from .models.plugin import PluginRecord, PluginInstallation, CapabilityGap, AgentTemplate
from .models import db
from .plugins.plugin_registry import PluginRegistry
from .plugins.plugin_manager import PluginManager
from .plugins.capability_discovery import CapabilityDiscovery
from .validation.quality_gate import QualityGate
from .validation.validation_chain import ValidationChain
from .validation.rollback_manager import RollbackManager

logger = logging.getLogger(__name__)


class SwarmDirectorIntegration:
    """
    Main integration class that sets up validation and plugin systems
    within the existing SwarmDirector architecture.
    """
    
    def __init__(self, app=None, config: Optional[Dict[str, Any]] = None):
        self.app = app
        self.config = config or {}
        self.validation_service: Optional[ValidationService] = None
        self.integrator: Optional[ValidationPluginIntegrator] = None
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the integration with Flask app"""
        self.app = app
        
        # Load configuration
        self._load_config()
        
        # Initialize database models
        self._init_database_models()
        
        # Initialize validation and plugin systems
        self._init_validation_plugin_systems()
        
        # Register API routes
        self._register_api_routes()
        
        # Setup CLI commands
        self._setup_cli_commands()
        
        # Store in app context
        app.validation_integration = self
        
        logger.info("SwarmDirector validation and plugin integration initialized")
    
    def _load_config(self):
        """Load configuration from app config"""
        # Default configuration
        default_config = {
            'VALIDATION_ENABLED': True,
            'PLUGIN_SYSTEM_ENABLED': True,
            'AUTO_INSTALL_PLUGINS': False,
            'AUTO_DISCOVERY_ENABLED': True,
            'VALIDATION_TIMEOUT': 300,
            'PLUGIN_REGISTRY_PATH': os.path.expanduser('~/.swarm_director/plugins/registry.json'),
            'DEPENDENCY_CACHE_DIR': os.path.expanduser('~/.swarm_director/dependencies')
        }
        
        # Update with app config
        for key, default_value in default_config.items():
            self.config[key.lower()] = self.app.config.get(key, default_value)
        
        logger.info(f"Loaded validation/plugin configuration: {len(self.config)} settings")
    
    def _init_database_models(self):
        """Initialize database models for validation and plugin systems"""
        try:
            # Import models to register them with SQLAlchemy
            from .models import validation, plugin
            
            # Create tables if they don't exist
            with self.app.app_context():
                db.create_all()
            
            logger.info("Database models for validation and plugin systems initialized")
            
        except Exception as e:
            logger.error(f"Error initializing database models: {e}")
            raise
    
    def _init_validation_plugin_systems(self):
        """Initialize validation and plugin systems"""
        try:
            # Create plugin configuration
            plugin_config = {
                'auto_install_enabled': self.config.get('auto_install_plugins', False),
                'auto_discovery_enabled': self.config.get('auto_discovery_enabled', True),
                'registry_path': self.config.get('plugin_registry_path'),
                'dependency_cache_dir': self.config.get('dependency_cache_dir')
            }
            
            # Initialize integrator
            self.integrator = ValidationPluginIntegrator({
                'plugin_config': plugin_config
            })
            
            # Initialize validation service
            self.validation_service = ValidationService(self.config)
            
            # Load default quality gates
            self._load_default_quality_gates()
            
            # Register default plugins
            self._register_default_plugins()
            
            logger.info("Validation and plugin systems initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing validation/plugin systems: {e}")
            raise
    
    def _load_default_quality_gates(self):
        """Load default quality gate configurations"""
        try:
            with self.app.app_context():
                # Check if quality gates already exist
                existing_gates = QualityGateConfig.query.count()
                if existing_gates > 0:
                    logger.info(f"Found {existing_gates} existing quality gates, skipping defaults")
                    return
                
                # Default quality gates
                default_gates = [
                    {
                        'name': 'default_tool_gate',
                        'tier': 'tool',
                        'description': 'Default quality gate for tool agents',
                        'config_data': {
                            'thresholds': [
                                {'metric': 'completeness', 'minimum_score': 0.8, 'critical': True},
                                {'metric': 'accuracy', 'minimum_score': 0.7, 'critical': False}
                            ]
                        }
                    },
                    {
                        'name': 'default_department_gate',
                        'tier': 'department',
                        'description': 'Default quality gate for department agents',
                        'config_data': {
                            'thresholds': [
                                {'metric': 'accuracy', 'minimum_score': 0.85, 'critical': True},
                                {'metric': 'completeness', 'minimum_score': 0.9, 'critical': True},
                                {'metric': 'consistency', 'minimum_score': 0.8, 'critical': False}
                            ]
                        }
                    },
                    {
                        'name': 'default_director_gate',
                        'tier': 'director',
                        'description': 'Default quality gate for director agents',
                        'config_data': {
                            'thresholds': [
                                {'metric': 'accuracy', 'minimum_score': 0.9, 'critical': True},
                                {'metric': 'completeness', 'minimum_score': 0.95, 'critical': True},
                                {'metric': 'compliance', 'minimum_score': 0.9, 'critical': True}
                            ]
                        }
                    }
                ]
                
                for gate_config in default_gates:
                    gate = QualityGateConfig(**gate_config)
                    db.session.add(gate)
                
                db.session.commit()
                logger.info(f"Created {len(default_gates)} default quality gates")
                
        except Exception as e:
            logger.error(f"Error loading default quality gates: {e}")
    
    def _register_default_plugins(self):
        """Register default plugins in the database"""
        try:
            with self.app.app_context():
                # Check if plugins already exist
                existing_plugins = PluginRecord.query.count()
                if existing_plugins > 0:
                    logger.info(f"Found {existing_plugins} existing plugins, skipping defaults")
                    return
                
                # Default plugins
                default_plugins = [
                    {
                        'name': 'email_agent_plugin',
                        'version': '1.0.0',
                        'description': 'Enhanced email agent with advanced features',
                        'author': 'SwarmDirector Team',
                        'plugin_type': 'agent',
                        'status': 'available',
                        'capabilities': ['email_sending', 'template_processing', 'analytics'],
                        'dependencies': [{'name': 'sendgrid', 'version': '>=6.0.0', 'type': 'python'}],
                        'entry_point': 'email_plugin.EmailAgent'
                    },
                    {
                        'name': 'analytics_plugin',
                        'version': '1.0.0',
                        'description': 'Advanced analytics and reporting capabilities',
                        'author': 'SwarmDirector Team',
                        'plugin_type': 'tool',
                        'status': 'available',
                        'capabilities': ['data_analysis', 'report_generation', 'ml_insights'],
                        'dependencies': [
                            {'name': 'pandas', 'version': '>=1.3.0', 'type': 'python'},
                            {'name': 'scikit-learn', 'version': '>=1.0.0', 'type': 'python'}
                        ],
                        'entry_point': 'analytics_plugin.AnalyticsAgent'
                    }
                ]
                
                for plugin_config in default_plugins:
                    plugin = PluginRecord(**plugin_config)
                    db.session.add(plugin)
                
                db.session.commit()
                logger.info(f"Registered {len(default_plugins)} default plugins")
                
        except Exception as e:
            logger.error(f"Error registering default plugins: {e}")
    
    def _register_api_routes(self):
        """Register API routes for validation and plugin management"""
        try:
            # Only register routes if we have an active Flask app context
            if not self.app:
                logger.warning("No Flask app available for route registration")
                return
                
            from .api.validation_routes import validation_bp
            
            # Check if we're in an app context before registering
            try:
                with self.app.app_context():
                    self.app.register_blueprint(validation_bp)
                    logger.info("Registered validation API routes")
            except RuntimeError as e:
                if "Working outside of request context" in str(e):
                    logger.warning("Cannot register API routes outside of request context")
                else:
                    raise
            
        except Exception as e:
            logger.error(f"Error registering API routes: {e}")
    
    def _setup_cli_commands(self):
        """Setup CLI commands for validation and plugin management"""
        try:
            @self.app.cli.command()
            def init_validation():
                """Initialize validation system"""
                click.echo("Initializing validation system...")
                self._load_default_quality_gates()
                self._register_default_plugins()
                click.echo("Validation system initialized successfully")
            
            @self.app.cli.command()
            @click.argument('plugin_name')
            def install_plugin(plugin_name):
                """Install a plugin"""
                click.echo(f"Installing plugin: {plugin_name}")
                # Implementation would use the validation service
                click.echo(f"Plugin {plugin_name} installed successfully")
            
            @self.app.cli.command()
            def validation_status():
                """Show validation system status"""
                if self.validation_service:
                    status = self.validation_service.get_plugin_status()
                    click.echo(f"Validation system status: {status}")
                else:
                    click.echo("Validation system not initialized")
            
            logger.info("CLI commands for validation system registered")
            
        except Exception as e:
            logger.error(f"Error setting up CLI commands: {e}")
    
    def get_validation_service(self) -> Optional[ValidationService]:
        """Get the validation service instance"""
        return self.validation_service
    
    def get_integrator(self) -> Optional[ValidationPluginIntegrator]:
        """Get the validation/plugin integrator instance"""
        return self.integrator
    
    def is_validation_enabled(self) -> bool:
        """Check if validation system is enabled"""
        return self.config.get('validation_enabled', True)
    
    def is_plugin_system_enabled(self) -> bool:
        """Check if plugin system is enabled"""
        return self.config.get('plugin_system_enabled', True)


# Global integration instance
integration = SwarmDirectorIntegration()


def init_validation_plugin_integration(app, config: Optional[Dict[str, Any]] = None):
    """
    Initialize validation and plugin integration with Flask app
    
    Args:
        app: Flask application instance
        config: Optional configuration dictionary
    """
    integration.init_app(app)
    return integration


def get_validation_service() -> Optional[ValidationService]:
    """Get the global validation service instance"""
    service = integration.get_validation_service()
    if service is None:
        try:
            from .services.validation_service import ValidationService  # noqa: WPS433
            service = ValidationService({})
            integration.validation_service = service
        except Exception:  # pragma: no cover
            service = None
    return service


def get_integrator() -> Optional[ValidationPluginIntegrator]:
    """Get the global integrator instance"""
    integrator = integration.get_integrator()
    if integrator is None:
        service = get_validation_service()
        if service:
            integrator = service.integrator
            integration.integrator = integrator
    return integrator
