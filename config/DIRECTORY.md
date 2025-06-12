# Configuration Directory

## Purpose
Contains configuration files and settings for the SwarmDirector application across different environments (development, testing, production). This directory manages application configuration, environment variables, deployment settings, and infrastructure configuration for the hierarchical AI agent management system.

## Structure
```
config/
├── __init__.py                  # Configuration package initialization
├── base.py                      # Base configuration class with common settings
├── development.py               # Development environment configuration
├── testing.py                   # Testing environment configuration
├── production.py                # Production environment configuration
├── docker/                      # Docker configuration files
│   ├── Dockerfile               # Docker image definition
│   ├── docker-compose.yml       # Development Docker Compose
│   ├── docker-compose.prod.yml  # Production Docker Compose
│   └── .dockerignore            # Docker ignore patterns
├── nginx/                       # Nginx configuration files
│   ├── nginx.conf               # Main Nginx configuration
│   ├── sites-available/         # Available site configurations
│   └── ssl/                     # SSL certificate storage
├── systemd/                     # Systemd service files
│   ├── swarmdirector.service    # Main application service
│   └── swarmdirector-worker.service # Background worker service
└── templates/                   # Configuration templates
    ├── .env.template            # Environment variables template
    ├── config.yaml.template     # YAML configuration template
    └── logging.conf.template    # Logging configuration template
```

## Guidelines

### 1. Organization
- **Environment Separation**: Maintain separate configurations for each environment
- **Hierarchical Structure**: Use base configuration with environment-specific overrides
- **Secret Management**: Keep sensitive data in environment variables, not in files
- **Template Usage**: Provide templates for common configuration scenarios
- **Version Control**: Track configuration changes but exclude sensitive data

### 2. Naming
- **Environment Names**: Use standard names (development, testing, production)
- **Configuration Files**: Use descriptive names indicating purpose and environment
- **Variable Names**: Use consistent naming conventions with environment prefixes
- **Template Files**: Use .template extension for configuration templates
- **Service Names**: Use consistent naming for service configurations

### 3. Implementation
- **Configuration Classes**: Use Python classes for structured configuration management
- **Environment Variables**: Support configuration through environment variables
- **Validation**: Validate configuration values and provide meaningful error messages
- **Defaults**: Provide sensible defaults for all configuration options
- **Documentation**: Document all configuration options and their effects

### 4. Documentation
- **Configuration Guide**: Document all configuration options and their usage
- **Environment Setup**: Provide setup instructions for each environment
- **Security Guidelines**: Document security considerations for configuration
- **Troubleshooting**: Include common configuration issues and solutions

## Best Practices

### 1. Error Handling
- **Configuration Validation**: Validate all configuration values at startup
- **Missing Configuration**: Provide clear error messages for missing required configuration
- **Invalid Values**: Validate configuration value formats and ranges
- **Fallback Values**: Provide fallback values for non-critical configuration
- **Error Recovery**: Implement graceful degradation for configuration errors

### 2. Security
- **Secret Management**: Never store secrets in configuration files
- **Environment Variables**: Use environment variables for sensitive configuration
- **Access Control**: Restrict access to configuration files and directories
- **Encryption**: Encrypt sensitive configuration data at rest
- **Audit Logging**: Log configuration changes and access

### 3. Performance
- **Configuration Caching**: Cache configuration values to avoid repeated parsing
- **Lazy Loading**: Load configuration values only when needed
- **Efficient Parsing**: Use efficient configuration file formats
- **Memory Usage**: Minimize memory usage for configuration storage
- **Startup Time**: Optimize configuration loading for fast application startup

### 4. Testing
- **Configuration Testing**: Test configuration loading and validation
- **Environment Testing**: Test configuration in all target environments
- **Default Testing**: Test that default values work correctly
- **Validation Testing**: Test configuration validation and error handling
- **Integration Testing**: Test configuration with actual application components

### 5. Documentation
- **Configuration Documentation**: Document all configuration options comprehensively
- **Example Configurations**: Provide working examples for common scenarios
- **Migration Guides**: Document configuration changes between versions
- **Best Practices**: Include configuration best practices and recommendations

## Example

### Complete Configuration System

```python
"""
SwarmDirector Configuration Management System
Provides structured configuration management across environments
"""

import os
import logging
from typing import Dict, Any, Optional, List
from pathlib import Path
import yaml
import json
from dataclasses import dataclass, field

@dataclass
class DatabaseConfig:
    """Database configuration"""
    url: str = "sqlite:///database/data/swarm_director_dev.db"
    echo: bool = False
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    
    def validate(self) -> None:
        """Validate database configuration"""
        if not self.url:
            raise ValueError("Database URL is required")
        
        if self.pool_size < 1:
            raise ValueError("Pool size must be positive")
        
        if self.max_overflow < 0:
            raise ValueError("Max overflow must be non-negative")

@dataclass
class RedisConfig:
    """Redis configuration"""
    url: str = "redis://localhost:6379/0"
    password: Optional[str] = None
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    retry_on_timeout: bool = True
    health_check_interval: int = 30
    
    def validate(self) -> None:
        """Validate Redis configuration"""
        if not self.url:
            raise ValueError("Redis URL is required")

@dataclass
class EmailConfig:
    """Email configuration"""
    smtp_server: str = "localhost"
    smtp_port: int = 587
    smtp_username: Optional[str] = None
    smtp_password: Optional[str] = None
    use_tls: bool = True
    use_ssl: bool = False
    default_sender: str = "noreply@swarmdirector.com"
    timeout: int = 30
    
    def validate(self) -> None:
        """Validate email configuration"""
        if not self.smtp_server:
            raise ValueError("SMTP server is required")
        
        if not (1 <= self.smtp_port <= 65535):
            raise ValueError("SMTP port must be between 1 and 65535")
        
        if self.use_tls and self.use_ssl:
            raise ValueError("Cannot use both TLS and SSL")

@dataclass
class SwarmDirectorConfig:
    """SwarmDirector-specific configuration"""
    log_level: str = "INFO"
    max_agents: int = 100
    task_timeout: int = 300
    max_concurrent_tasks: int = 10
    agent_heartbeat_interval: int = 30
    task_retry_attempts: int = 3
    task_retry_delay: int = 5
    enable_metrics: bool = True
    metrics_port: int = 9090
    
    def validate(self) -> None:
        """Validate SwarmDirector configuration"""
        valid_log_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if self.log_level not in valid_log_levels:
            raise ValueError(f"Log level must be one of: {valid_log_levels}")
        
        if self.max_agents < 1:
            raise ValueError("Max agents must be positive")
        
        if self.task_timeout < 1:
            raise ValueError("Task timeout must be positive")

@dataclass
class SecurityConfig:
    """Security configuration"""
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_secret_key: Optional[str] = None
    jwt_expiration_hours: int = 24
    password_hash_rounds: int = 12
    session_timeout_minutes: int = 60
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    csrf_enabled: bool = True
    
    def validate(self) -> None:
        """Validate security configuration"""
        if len(self.secret_key) < 32:
            raise ValueError("Secret key must be at least 32 characters")
        
        if self.jwt_expiration_hours < 1:
            raise ValueError("JWT expiration must be positive")
        
        if self.password_hash_rounds < 4:
            raise ValueError("Password hash rounds must be at least 4")

class Config:
    """Base configuration class"""
    
    def __init__(self):
        self.DEBUG = False
        self.TESTING = False
        self.SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
        
        # Load configuration from various sources
        self._load_from_environment()
        self._load_from_files()
        
        # Initialize configuration sections
        self.database = DatabaseConfig()
        self.redis = RedisConfig()
        self.email = EmailConfig()
        self.swarm_director = SwarmDirectorConfig()
        self.security = SecurityConfig()
        
        # Apply environment-specific overrides
        self._apply_environment_overrides()
        
        # Validate configuration
        self.validate()
    
    def _load_from_environment(self) -> None:
        """Load configuration from environment variables"""
        # Flask configuration
        self.SECRET_KEY = os.environ.get('SECRET_KEY', self.SECRET_KEY)
        
        # Database configuration
        if db_url := os.environ.get('DATABASE_URL'):
            self.DATABASE_URL = db_url
        
        # Redis configuration
        if redis_url := os.environ.get('REDIS_URL'):
            self.REDIS_URL = redis_url
        
        # Email configuration
        self.SMTP_SERVER = os.environ.get('SMTP_SERVER', 'localhost')
        self.SMTP_PORT = int(os.environ.get('SMTP_PORT', '587'))
        self.SMTP_USERNAME = os.environ.get('SMTP_USERNAME')
        self.SMTP_PASSWORD = os.environ.get('SMTP_PASSWORD')
        
        # SwarmDirector configuration
        self.SWARM_DIRECTOR_LOG_LEVEL = os.environ.get('SWARM_DIRECTOR_LOG_LEVEL', 'INFO')
        self.SWARM_DIRECTOR_MAX_AGENTS = int(os.environ.get('SWARM_DIRECTOR_MAX_AGENTS', '100'))
        self.SWARM_DIRECTOR_TASK_TIMEOUT = int(os.environ.get('SWARM_DIRECTOR_TASK_TIMEOUT', '300'))
    
    def _load_from_files(self) -> None:
        """Load configuration from files"""
        config_dir = Path(__file__).parent
        
        # Load from YAML file if exists
        yaml_config = config_dir / 'config.yaml'
        if yaml_config.exists():
            with open(yaml_config, 'r') as f:
                yaml_data = yaml.safe_load(f)
                self._merge_config(yaml_data)
        
        # Load from JSON file if exists
        json_config = config_dir / 'config.json'
        if json_config.exists():
            with open(json_config, 'r') as f:
                json_data = json.load(f)
                self._merge_config(json_data)
    
    def _merge_config(self, config_data: Dict[str, Any]) -> None:
        """Merge configuration data into current config"""
        for key, value in config_data.items():
            if hasattr(self, key):
                setattr(self, key, value)
    
    def _apply_environment_overrides(self) -> None:
        """Apply environment-specific configuration overrides"""
        # Database configuration
        if hasattr(self, 'DATABASE_URL'):
            self.database.url = self.DATABASE_URL
        
        # Redis configuration
        if hasattr(self, 'REDIS_URL'):
            self.redis.url = self.REDIS_URL
        
        # Email configuration
        self.email.smtp_server = self.SMTP_SERVER
        self.email.smtp_port = self.SMTP_PORT
        self.email.smtp_username = self.SMTP_USERNAME
        self.email.smtp_password = self.SMTP_PASSWORD
        
        # SwarmDirector configuration
        self.swarm_director.log_level = self.SWARM_DIRECTOR_LOG_LEVEL
        self.swarm_director.max_agents = self.SWARM_DIRECTOR_MAX_AGENTS
        self.swarm_director.task_timeout = self.SWARM_DIRECTOR_TASK_TIMEOUT
        
        # Security configuration
        self.security.secret_key = self.SECRET_KEY
    
    def validate(self) -> None:
        """Validate all configuration sections"""
        try:
            self.database.validate()
            self.redis.validate()
            self.email.validate()
            self.swarm_director.validate()
            self.security.validate()
        except ValueError as e:
            raise ValueError(f"Configuration validation failed: {e}")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary"""
        return {
            'debug': self.DEBUG,
            'testing': self.TESTING,
            'database': self.database.__dict__,
            'redis': self.redis.__dict__,
            'email': {k: v for k, v in self.email.__dict__.items() if 'password' not in k.lower()},
            'swarm_director': self.swarm_director.__dict__,
            'security': {k: v for k, v in self.security.__dict__.items() if 'key' not in k.lower()}
        }
    
    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration"""
        return {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'detailed': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s:%(lineno)d: %(message)s'
                }
            },
            'handlers': {
                'console': {
                    'class': 'logging.StreamHandler',
                    'level': self.swarm_director.log_level,
                    'formatter': 'standard',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'class': 'logging.handlers.RotatingFileHandler',
                    'level': self.swarm_director.log_level,
                    'formatter': 'detailed',
                    'filename': 'logs/swarm_director.log',
                    'maxBytes': 10485760,  # 10MB
                    'backupCount': 5
                }
            },
            'loggers': {
                'swarm_director': {
                    'level': self.swarm_director.log_level,
                    'handlers': ['console', 'file'],
                    'propagate': False
                }
            },
            'root': {
                'level': 'WARNING',
                'handlers': ['console']
            }
        }

class DevelopmentConfig(Config):
    """Development environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = True
        self.TESTING = False
        
        # Development-specific overrides
        self.database.echo = True
        self.swarm_director.log_level = "DEBUG"
        self.security.csrf_enabled = False

class TestingConfig(Config):
    """Testing environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.TESTING = True
        
        # Testing-specific overrides
        self.database.url = "sqlite:///:memory:"
        self.redis.url = "redis://localhost:6379/1"
        self.swarm_director.log_level = "WARNING"
        self.security.csrf_enabled = False

class ProductionConfig(Config):
    """Production environment configuration"""
    
    def __init__(self):
        super().__init__()
        self.DEBUG = False
        self.TESTING = False
        
        # Production-specific overrides
        self.database.echo = False
        self.swarm_director.log_level = "INFO"
        self.security.csrf_enabled = True
        
        # Validate production requirements
        self._validate_production_config()
    
    def _validate_production_config(self) -> None:
        """Validate production-specific requirements"""
        if self.security.secret_key == "dev-secret-key":
            raise ValueError("Production secret key must be changed from default")
        
        if self.database.url.startswith("sqlite:"):
            logging.warning("Using SQLite in production is not recommended")
        
        if not self.email.smtp_username or not self.email.smtp_password:
            logging.warning("Email credentials not configured")

# Configuration registry
config_by_name = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}

def get_config(config_name: Optional[str] = None) -> Config:
    """
    Get configuration instance for specified environment
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configuration instance
    """
    config_name = config_name or os.environ.get('FLASK_ENV', 'development')
    
    if config_name not in config_by_name:
        raise ValueError(f"Unknown configuration: {config_name}")
    
    return config_by_name[config_name]()

# Configuration validation utility
def validate_config(config: Config) -> List[str]:
    """
    Validate configuration and return list of issues
    
    Args:
        config: Configuration instance to validate
        
    Returns:
        List of validation issues
    """
    issues = []
    
    try:
        config.validate()
    except ValueError as e:
        issues.append(str(e))
    
    # Additional validation checks
    if config.DEBUG and not config.TESTING:
        if config.security.secret_key == "dev-secret-key":
            issues.append("Using default secret key in debug mode")
    
    if config.database.url.startswith("sqlite:") and not config.TESTING:
        if config.swarm_director.max_agents > 50:
            issues.append("SQLite may not handle high agent counts efficiently")
    
    return issues
```

### Environment Configuration Template

```bash
# SwarmDirector Environment Configuration Template
# Copy this file to .env and customize for your environment

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=your-secret-key-here

# Database Configuration
DATABASE_URL=sqlite:///database/data/swarm_director_dev.db
# For PostgreSQL: postgresql://username:password@localhost/swarm_director

# Redis Configuration (optional)
REDIS_URL=redis://localhost:6379/0

# Email Configuration
SMTP_SERVER=localhost
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-email-password
SMTP_USE_TLS=true
DEFAULT_SENDER=noreply@swarmdirector.com

# SwarmDirector Configuration
SWARM_DIRECTOR_LOG_LEVEL=INFO
SWARM_DIRECTOR_MAX_AGENTS=100
SWARM_DIRECTOR_TASK_TIMEOUT=300
SWARM_DIRECTOR_MAX_CONCURRENT_TASKS=10
SWARM_DIRECTOR_ENABLE_METRICS=true

# Security Configuration
JWT_SECRET_KEY=your-jwt-secret-key
JWT_EXPIRATION_HOURS=24
PASSWORD_HASH_ROUNDS=12
SESSION_TIMEOUT_MINUTES=60

# AutoGen Configuration (optional)
AUTOGEN_API_KEY=your-autogen-api-key
AUTOGEN_MODEL=gpt-3.5-turbo
AUTOGEN_MAX_TOKENS=2048

# Monitoring Configuration
ENABLE_PROMETHEUS_METRICS=true
PROMETHEUS_PORT=9090
ENABLE_HEALTH_CHECKS=true
HEALTH_CHECK_INTERVAL=30

# Development Tools
ENABLE_PROFILING=false
ENABLE_DEBUG_TOOLBAR=false
SQLALCHEMY_ECHO=false
```

## Related Documentation
- [Environment Setup](../docs/deployment/local_development.md) - Environment configuration guide
- [Production Deployment](../docs/deployment/production_deployment.md) - Production configuration
- [Security Guidelines](../docs/development/coding_standards.md#security) - Security configuration practices
- [Docker Configuration](../docs/deployment/docker_deployment.md) - Container configuration
- [Monitoring Setup](../docs/deployment/monitoring.md) - Monitoring configuration
