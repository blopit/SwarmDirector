# SwarmDirector Main Package Directory

## Purpose
The core application package containing the complete implementation of the SwarmDirector hierarchical AI agent management system. This package provides the Flask application, configuration management, and orchestrates the three-tier architecture (Director → Department → Tool) for intelligent task routing and execution.

## Structure
```
swarm_director/
├── __init__.py                  # Package initialization, version, and main exports
├── app.py                       # Flask application factory and route definitions
├── config.py                    # Configuration classes for different environments
├── agents/                      # AI agent implementations
│   ├── __init__.py              # Agent package exports and registry
│   ├── base_agent.py            # Abstract base agent class
│   ├── director.py              # Director agent (intelligent task routing)
│   ├── supervisor_agent.py      # Supervisor agent (department management)
│   ├── worker_agent.py          # Worker agent (task execution)
│   ├── communications_dept.py   # Communications department agent
│   ├── email_agent.py           # Email handling and SMTP integration
│   ├── draft_review_agent.py    # Content review and analysis
│   ├── review_logic.py          # Review logic and scoring utilities
│   └── diff_generator.py        # Content difference analysis
├── models/                      # Database models (SQLAlchemy ORM)
│   ├── __init__.py              # Model exports and database instance
│   ├── base.py                  # Base model with common functionality
│   ├── agent.py                 # Agent model with hierarchy support
│   ├── task.py                  # Task model with dependencies
│   ├── conversation.py          # Conversation and message models
│   ├── draft.py                 # Draft content model
│   ├── email_message.py         # Email message model
│   └── agent_log.py             # Agent activity logging model
├── utils/                       # Utility functions and helpers
│   ├── __init__.py              # Utility exports with optional imports
│   ├── database.py              # Database utilities and connection management
│   ├── logging.py               # Centralized logging configuration
│   ├── migrations.py            # Database migration utilities
│   ├── autogen_helpers.py       # Legacy AutoGen integration helpers
│   ├── autogen_integration.py   # Advanced AutoGen framework integration
│   ├── autogen_config.py        # AutoGen configuration templates
│   ├── conversation_analytics.py # Conversation analysis and metrics
│   ├── error_handler.py         # Error handling and recovery utilities
│   ├── rate_limiter.py          # API rate limiting implementation
│   ├── response_formatter.py    # Response formatting utilities
│   ├── validation.py            # Input validation and sanitization
│   └── db_cli.py                # Database CLI commands and tools
├── web/                         # Web interface components
│   ├── __init__.py              # Web package initialization
│   ├── static/                  # Static assets (CSS, JS, images)
│   └── templates/               # Jinja2 HTML templates
│       └── demo/                # Demo interface templates
└── schemas/                     # API schemas and validation (if present)
```

## Guidelines

### 1. Organization
- **Application Factory**: Use Flask application factory pattern in `app.py`
- **Configuration Management**: Centralize all configuration in `config.py` with environment-specific classes
- **Package Imports**: Use relative imports within the package, expose public APIs through `__init__.py`
- **Dependency Injection**: Pass configuration and dependencies through constructors
- **Modular Design**: Keep each component focused on a single responsibility

### 2. Naming
- **Application Module**: Use `app.py` for Flask application factory
- **Configuration**: Use descriptive config class names (e.g., `DevelopmentConfig`, `ProductionConfig`)
- **Package Exports**: Export only public APIs through `__all__` in `__init__.py` files
- **Version Management**: Define version in main `__init__.py` and import from setup files
- **Environment Variables**: Use consistent naming with `SWARM_DIRECTOR_` prefix

### 3. Implementation
- **Flask Blueprints**: Organize routes using Flask blueprints for scalability
- **Database Sessions**: Use Flask-SQLAlchemy for database session management
- **Error Handling**: Implement global error handlers in the Flask application
- **Middleware**: Use Flask middleware for cross-cutting concerns (logging, authentication)
- **Configuration Loading**: Support multiple configuration sources (files, environment variables)

### 4. Documentation
- **Package Docstring**: Include comprehensive package description and usage examples
- **API Documentation**: Document all public functions and classes
- **Configuration Documentation**: Document all configuration options and their effects
- **Integration Examples**: Provide examples of integrating with external systems

## Best Practices

### 1. Error Handling
- **Global Error Handlers**: Register Flask error handlers for common HTTP errors
- **Exception Logging**: Log all exceptions with full context and stack traces
- **User-Friendly Errors**: Return appropriate HTTP status codes with helpful error messages
- **Graceful Degradation**: Handle optional dependencies (AutoGen) gracefully
- **Circuit Breaker**: Implement circuit breaker pattern for external service calls

### 2. Security
- **Input Validation**: Validate all inputs at the application boundary
- **CSRF Protection**: Enable CSRF protection for web forms
- **SQL Injection Prevention**: Use SQLAlchemy ORM exclusively for database operations
- **Secrets Management**: Use environment variables for sensitive configuration
- **Rate Limiting**: Implement rate limiting for API endpoints

### 3. Performance
- **Database Connection Pooling**: Configure appropriate connection pool settings
- **Query Optimization**: Use efficient database queries with proper indexing
- **Caching**: Implement caching for expensive operations and frequently accessed data
- **Async Processing**: Use background tasks for long-running operations
- **Resource Monitoring**: Monitor memory and CPU usage in production

### 4. Testing
- **Application Context**: Use Flask application context in tests
- **Test Configuration**: Use separate test configuration with in-memory database
- **Mock External Services**: Mock external dependencies in unit tests
- **Integration Testing**: Test complete request/response cycles
- **Performance Testing**: Include load testing for critical endpoints

### 5. Documentation
- **API Documentation**: Generate OpenAPI/Swagger documentation
- **Configuration Guide**: Document all configuration options and examples
- **Deployment Guide**: Provide deployment instructions for different environments
- **Troubleshooting**: Include common issues and solutions

## Example

### Complete Flask Application Setup

```python
"""
SwarmDirector Flask Application Factory
Demonstrates proper application initialization and configuration
"""

from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from typing import Optional
import os
import logging

from .config import config_by_name
from .models.base import db
from .utils.logging import setup_logging
from .utils.error_handler import register_error_handlers
from .agents.director import DirectorAgent
from .models.agent import Agent, AgentType

def create_app(config_name: Optional[str] = None) -> Flask:
    """
    Flask application factory
    
    Args:
        config_name: Configuration environment name
        
    Returns:
        Configured Flask application instance
    """
    # Determine configuration
    config_name = config_name or os.getenv('FLASK_ENV', 'development')
    
    # Create Flask application
    app = Flask(__name__)
    
    # Load configuration
    app.config.from_object(config_by_name[config_name])
    
    # Initialize extensions
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # Setup logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints
    register_blueprints(app)
    
    # Initialize agents
    with app.app_context():
        initialize_agents()
    
    return app

def register_blueprints(app: Flask) -> None:
    """Register Flask blueprints"""
    from .web.api import api_bp
    from .web.dashboard import dashboard_bp
    
    app.register_blueprint(api_bp, url_prefix='/api/v1')
    app.register_blueprint(dashboard_bp, url_prefix='/dashboard')

def initialize_agents() -> None:
    """Initialize core agents if they don't exist"""
    try:
        # Check if director agent exists
        director_agent = Agent.query.filter_by(
            name="MainDirector",
            agent_type=AgentType.SUPERVISOR
        ).first()
        
        if not director_agent:
            # Create director agent
            director_agent = Agent(
                name="MainDirector",
                description="Primary director agent for intelligent task routing",
                agent_type=AgentType.SUPERVISOR,
                capabilities={
                    "routing": True,
                    "department_management": True,
                    "intent_classification": True
                }
            )
            director_agent.save()
            
            app.logger.info("Created MainDirector agent")
        
        # Initialize other core agents as needed
        initialize_department_agents()
        
    except Exception as e:
        app.logger.error(f"Failed to initialize agents: {e}")

def initialize_department_agents() -> None:
    """Initialize department agents"""
    departments = [
        {
            "name": "CommunicationsDept",
            "description": "Communications department for content creation and review",
            "capabilities": {
                "content_creation": True,
                "email_handling": True,
                "draft_review": True,
                "parallel_processing": True
            }
        },
        {
            "name": "EmailAgent",
            "description": "Specialized agent for email operations",
            "capabilities": {
                "smtp_integration": True,
                "template_processing": True,
                "email_validation": True
            }
        }
    ]
    
    for dept_config in departments:
        existing_agent = Agent.query.filter_by(name=dept_config["name"]).first()
        if not existing_agent:
            agent = Agent(
                name=dept_config["name"],
                description=dept_config["description"],
                agent_type=AgentType.WORKER,
                capabilities=dept_config["capabilities"]
            )
            agent.save()

# Health check endpoint
@app.route('/health')
def health_check():
    """Application health check endpoint"""
    try:
        # Check database connectivity
        db.session.execute('SELECT 1')
        
        # Check agent availability
        agent_count = Agent.query.count()
        
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'agents': agent_count,
            'version': app.config.get('VERSION', '1.0.0')
        }), 200
        
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e)
        }), 503

# Main task processing endpoint
@app.route('/api/v1/tasks', methods=['POST'])
def process_task():
    """Process a task through the SwarmDirector system"""
    try:
        # Validate request
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400
        
        task_data = request.get_json()
        
        # Get director agent
        director_db = Agent.query.filter_by(
            name="MainDirector",
            agent_type=AgentType.SUPERVISOR
        ).first()
        
        if not director_db:
            return jsonify({'error': 'Director agent not available'}), 503
        
        director = DirectorAgent(director_db)
        
        # Create task
        from .models.task import Task, TaskStatus
        task = Task(
            title=task_data.get('title'),
            description=task_data.get('description'),
            task_type=task_data.get('type', 'general'),
            priority=task_data.get('priority', 1),
            status=TaskStatus.PENDING,
            input_data=task_data.get('data', {})
        )
        task.save()
        
        # Process task
        if director.can_handle_task(task):
            result = director.execute_task(task)
            return jsonify(result), 200
        else:
            return jsonify({'error': 'Task cannot be processed'}), 400
            
    except Exception as e:
        app.logger.error(f"Task processing error: {e}")
        return jsonify({'error': 'Internal server error'}), 500

if __name__ == '__main__':
    # Development server
    app = create_app('development')
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Configuration Management

```python
"""
Configuration classes for different environments
"""

import os
from typing import Type, Dict

class Config:
    """Base configuration class"""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True
    
    # SwarmDirector specific settings
    SWARM_DIRECTOR_LOG_LEVEL = os.environ.get('SWARM_DIRECTOR_LOG_LEVEL', 'INFO')
    SWARM_DIRECTOR_MAX_AGENTS = int(os.environ.get('SWARM_DIRECTOR_MAX_AGENTS', '100'))
    SWARM_DIRECTOR_TASK_TIMEOUT = int(os.environ.get('SWARM_DIRECTOR_TASK_TIMEOUT', '300'))
    
    # AutoGen settings (optional)
    AUTOGEN_API_KEY = os.environ.get('AUTOGEN_API_KEY')
    AUTOGEN_MODEL = os.environ.get('AUTOGEN_MODEL', 'gpt-3.5-turbo')

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///swarm_director_dev.db'

class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False

class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://user:pass@localhost/swarm_director'

# Configuration registry
config_by_name: Dict[str, Type[Config]] = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig
}
```

## Related Documentation
- [Agent Implementation Guide](agents/DIRECTORY.md) - AI agent development patterns
- [Database Models Guide](models/DIRECTORY.md) - Database model design and usage
- [Utility Functions Guide](utils/DIRECTORY.md) - Utility development standards
- [Web Interface Guide](web/DIRECTORY.md) - Web component development
- [API Documentation](../../docs/api/README.md) - REST API reference
- [Configuration Guide](../../docs/deployment/local_development.md) - Environment setup
