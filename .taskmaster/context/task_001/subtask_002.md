---
task_id: task_001
subtask_id: subtask_002
title: Core Flask Application Configuration
status: pending
priority: high
parent_task: task_001
dependencies: ['task_001/subtask_001']
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Subtask Overview

Create and configure the core Flask application using the application factory pattern, implement essential configuration management, set up basic routing structure, and establish error handling middleware. This subtask builds the foundation for all Flask-based functionality in the SwarmDirector system.

## 📋 Metadata
- **ID**: task_001 / subtask_002
- **Title**: Core Flask Application Configuration
- **Status**: pending
- **Priority**: high
- **Parent Task**: task_001
- **Dependencies**: ['task_001/subtask_001']
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints

### In Scope:
- **Flask Application Factory**: Create app.py with factory pattern implementation
- **Configuration Management**: Set up config.py with environment-specific settings
- **Basic Routing**: Implement main blueprint with essential endpoints
- **Error Handling**: Configure 404, 500, and other HTTP error handlers
- **Logging Configuration**: Set up structured logging for the application
- **Extension Initialization**: Configure Flask-SQLAlchemy, Flask-Migrate, Flask-Mail
- **Development Server**: Set up development server with debug capabilities
- **Environment Loading**: Integrate python-dotenv for environment variables

### Out of Scope:
- **Database Models**: Handled in subtask_003
- **CRUD Operations**: Handled in subtask_004
- **Authentication/Authorization**: Future enhancement
- **API Documentation**: Future enhancement
- **Production Deployment**: Future enhancement
- **Advanced Middleware**: Future enhancement

### Assumptions:
- **Environment Setup**: subtask_001 completed with virtual environment and dependencies
- **Python Version**: Python 3.8+ available and activated
- **Dependencies Installed**: Flask==2.3.3, Flask-SQLAlchemy==3.0.5, python-dotenv==1.0.0
- **Directory Structure**: Project structure from subtask_001 exists
- **Configuration Files**: .env.template available for environment setup

### Constraints:
- **Flask Version**: Must use Flask 2.3.3 for compatibility
- **Application Pattern**: Must use application factory pattern for scalability
- **Configuration**: Must support development, testing, and production environments
- **Error Handling**: Must provide user-friendly error pages
- **Logging**: Must log all significant events for debugging
- **Performance**: Application startup must complete within 10 seconds

---

## 🔍 1. Detailed Description

This subtask implements the core Flask application infrastructure using modern Flask best practices. The implementation follows the application factory pattern to enable flexible configuration and testing, establishes a robust configuration management system, and sets up essential application components.

### Key Components:

1. **Application Factory (app.py)**:
   - Implements create_app() function for flexible app creation
   - Configures all Flask extensions (SQLAlchemy, Migrate, Mail)
   - Sets up error handlers for common HTTP errors
   - Configures logging for development and production
   - Registers blueprints for modular routing

2. **Configuration Management (config.py)**:
   - Base configuration class with common settings
   - Environment-specific configurations (Development, Testing, Production)
   - Secure handling of sensitive configuration data
   - Database URI configuration for different environments
   - Mail server configuration with multiple provider support

3. **Main Blueprint (routes/main.py)**:
   - Homepage route with basic template rendering
   - Health check endpoint for monitoring
   - API status endpoint for service discovery
   - Error handling for blueprint-specific errors

4. **Error Handling**:
   - Custom 404 error page with helpful navigation
   - Custom 500 error page with error reporting
   - Graceful handling of database connection errors
   - Logging of all errors for debugging

5. **Logging Configuration**:
   - Structured logging with timestamps and levels
   - File-based logging with rotation
   - Console logging for development
   - Error-specific logging for troubleshooting

## 📁 2. Reference Artifacts & Files

### Primary Implementation Files:
```
SwarmDirector/
├── app.py                    # Main Flask application factory
├── config.py                 # Configuration management
├── .env                      # Environment variables (created from template)
├── routes/
│   ├── __init__.py
│   └── main.py              # Main blueprint with core routes
├── templates/
│   ├── base.html            # Base template with Bootstrap
│   ├── index.html           # Homepage template
│   └── errors/
│       ├── 404.html         # Custom 404 error page
│       └── 500.html         # Custom 500 error page
├── static/
│   ├── css/
│   │   └── main.css         # Custom CSS styles
│   ├── js/
│   │   └── main.js          # Custom JavaScript
│   └── images/
│       └── logo.png         # Application logo
└── logs/                    # Application logs (created at runtime)
    └── swarm_director.log
```

### Configuration Files:
- **config.py**: Environment-specific Flask configuration
- **.env**: Environment variables for sensitive data
- **requirements.txt**: Python dependencies (from subtask_001)

### Template Files:
- **templates/base.html**: Base template with Bootstrap CSS framework
- **templates/index.html**: Homepage with system status display
- **templates/errors/404.html**: Custom 404 error page
- **templates/errors/500.html**: Custom 500 error page

### Static Assets:
- **static/css/main.css**: Custom CSS for application styling
- **static/js/main.js**: Custom JavaScript for interactive features
- **static/images/logo.png**: SwarmDirector application logo

### Related Task Files:
- **Parent Task**: `.taskmaster/context/task_001/task.md`
- **Dependency**: `.taskmaster/context/task_001/subtask_001.md`
- **Source Task**: `.taskmaster/tasks/task_001.txt`

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 Flask Application Factory (app.py)
```python
import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from config import Config, DevelopmentConfig, TestingConfig, ProductionConfig

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app(config_class=None):
    """
    Application factory function for creating Flask app instances.

    Args:
        config_class: Configuration class to use (defaults to environment-based)

    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)

    # Determine configuration class
    if config_class is None:
        config_name = os.environ.get('FLASK_ENV', 'development')
        config_mapping = {
            'development': DevelopmentConfig,
            'testing': TestingConfig,
            'production': ProductionConfig
        }
        config_class = config_mapping.get(config_name, DevelopmentConfig)

    # Load configuration
    app.config.from_object(config_class)

    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)

    # Configure logging
    if not app.debug and not app.testing:
        setup_logging(app)

    # Register blueprints
    from routes.main import main_bp
    app.register_blueprint(main_bp)

    # Register error handlers
    register_error_handlers(app)

    # Add context processors
    register_context_processors(app)

    return app

def setup_logging(app):
    """Configure application logging for production."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    # File handler with rotation
    file_handler = RotatingFileHandler(
        'logs/swarm_director.log',
        maxBytes=10240000,  # 10MB
        backupCount=10
    )
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    ))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    app.logger.setLevel(logging.INFO)
    app.logger.info('SwarmDirector application startup')

def register_error_handlers(app):
    """Register custom error handlers."""

    @app.errorhandler(404)
    def not_found_error(error):
        """Handle 404 errors with custom page."""
        app.logger.warning(f'404 error: {error}')
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        """Handle 500 errors with custom page."""
        app.logger.error(f'500 error: {error}')
        db.session.rollback()
        return render_template('errors/500.html'), 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        """Handle unexpected exceptions."""
        app.logger.error(f'Unhandled exception: {error}', exc_info=True)
        db.session.rollback()
        return render_template('errors/500.html'), 500

def register_context_processors(app):
    """Register template context processors."""

    @app.context_processor
    def inject_config():
        """Inject configuration variables into templates."""
        return {
            'app_name': 'SwarmDirector',
            'app_version': '1.0.0',
            'debug_mode': app.debug
        }

if __name__ == '__main__':
    # Create app instance for development
    app = create_app()

    # Run development server
    app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 5000)),
        debug=True
    )
```

### 3.2 Configuration Management (config.py)
```python
import os
from dotenv import load_dotenv

# Load environment variables from .env file
basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class with common settings."""

    # Flask core settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'

    # Database configuration
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'swarm_director.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_RECORD_QUERIES = True

    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # AI API configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

    # Application settings
    POSTS_PER_PAGE = int(os.environ.get('POSTS_PER_PAGE') or 25)
    LANGUAGES = ['en', 'es']
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size

    # Security settings
    SESSION_COOKIE_SECURE = os.environ.get('SESSION_COOKIE_SECURE', 'false').lower() == 'true'
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')

    @staticmethod
    def init_app(app):
        """Initialize application with configuration."""
        pass

class DevelopmentConfig(Config):
    """Development environment configuration."""

    DEBUG = True
    TESTING = False

    # Development-specific database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'swarm_director_dev.db')

    # Development logging
    LOG_LEVEL = 'DEBUG'

    # Mail settings for development
    MAIL_SUPPRESS_SEND = os.environ.get('MAIL_SUPPRESS_SEND', 'false').lower() == 'true'

class TestingConfig(Config):
    """Testing environment configuration."""

    TESTING = True
    DEBUG = False

    # In-memory database for testing
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

    # Disable CSRF for testing
    WTF_CSRF_ENABLED = False

    # Suppress mail sending during tests
    MAIL_SUPPRESS_SEND = True

    # Testing-specific settings
    SERVER_NAME = 'localhost.localdomain'

class ProductionConfig(Config):
    """Production environment configuration."""

    DEBUG = False
    TESTING = False

    # Production database (PostgreSQL recommended)
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'swarm_director.db')

    # Production security settings
    SESSION_COOKIE_SECURE = True

    # Production logging
    LOG_LEVEL = 'WARNING'

    # Database optimization for production
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }

    @classmethod
    def init_app(cls, app):
        """Production-specific initialization."""
        Config.init_app(app)

        # Log to syslog in production
        import logging
        from logging.handlers import SysLogHandler
        syslog_handler = SysLogHandler()
        syslog_handler.setLevel(logging.WARNING)
        app.logger.addHandler(syslog_handler)

# Configuration mapping
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

---

## 🧪 7. Testing & QA
- **Unit Tests**: Test individual components
- **Integration**: Verify integration with parent task
- **Edge Cases**: Handle error conditions
- **Manual Verification**: Confirm functionality works as expected

---

## 🔗 8. Integration & Related Tasks
- **Parent**: task_001 (Setup Project Skeleton with Flask and SQLite)
- **Dependencies**: ['task_001/subtask_001']
- **Enables**: Subsequent subtasks in task_001

---

## ⚠️ 9. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Implementation complexity | Follow established patterns |
| Integration issues | Coordinate with dependent subtasks |
| Testing challenges | Implement comprehensive test coverage |

---

## ✅ 10. Success Criteria
- [ ] Subtask functionality implemented
- [ ] Unit tests pass
- [ ] Integration with parent task verified
- [ ] Code review completed
- [ ] Documentation updated

---

## 🚀 11. Next Steps
1. Complete implementation according to plan
2. Run comprehensive tests
3. Integrate with parent task components
