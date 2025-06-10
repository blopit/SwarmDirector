---
task_id: task_001
subtask_id: null
title: Setup Project Skeleton with Flask and SQLite
status: pending
priority: high
parent_task: null
dependencies: []
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Initialize the project structure with Flask framework and SQLite database setup for the hierarchical AI agent system.

## 📋 Metadata
- **ID**: task_001
- **Title**: Setup Project Skeleton with Flask and SQLite
- **Status**: pending
- **Priority**: high
- **Parent Task**: null
- **Dependencies**: []
- **Subtasks**: 4
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints
- **In Scope**: Initialize the project structure with Flask framework and SQLite database setup for the hierarchical AI agent system.
- **Out of Scope**: Features not explicitly mentioned in task details
- **Assumptions**: Previous dependencies completed successfully, required tools available
- **Constraints**: Must follow project architecture and coding standards

---

## 🔍 1. Detailed Description
1. Create a new Python project with virtual environment
2. Install required packages: Flask, SQLAlchemy, Flask-Migrate, Flask-Mail, and Microsoft AutoGen
3. Set up project directory structure:
   - app.py (main Flask application)
   - config.py (configuration settings)
   - models/ (database models)
   - agents/ (agent implementations)
   - utils/ (utility functions)
   - migrations/ (database migrations)
4. Initialize SQLite database with SQLAlchemy
5. Create basic Flask application skeleton with error handling middleware
6. Implement logging configuration
7. Set up database migration support using Flask-Migrate
8. Create requirements.txt file with all dependencies

## 📁 2. Reference Artifacts & Files
- **Project Root**: `/path/to/SwarmDirector/`
- **Main Application**: `app.py`
- **Configuration**: `config.py`
- **Requirements**: `requirements.txt`
- **Database**: `instance/swarm_director.db`
- **Migrations**: `migrations/`
- **Models**: `models/`
- **Agents**: `agents/`
- **Utils**: `utils/`
- **Templates**: `templates/`
- **Static Files**: `static/`

### Complete Directory Structure
```
SwarmDirector/
├── app.py                    # Main Flask application
├── config.py                 # Configuration settings
├── requirements.txt          # Python dependencies
├── .env                      # Environment variables
├── .gitignore               # Git ignore rules
├── README.md                # Project documentation
├── instance/                # Instance-specific files
│   └── swarm_director.db    # SQLite database
├── migrations/              # Database migrations
├── models/                  # SQLAlchemy models
│   ├── __init__.py
│   └── base.py
├── agents/                  # AI agent implementations
│   └── __init__.py
├── utils/                   # Utility functions
│   ├── __init__.py
│   └── logging_config.py
├── templates/               # Jinja2 templates
│   ├── base.html
│   └── index.html
├── static/                  # Static assets
│   ├── css/
│   ├── js/
│   └── images/
└── tests/                   # Test files
    ├── __init__.py
    └── test_app.py
```

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 Main Application Structure (app.py)
```python
from flask import Flask, render_template, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
import logging
from config import Config

# Initialize extensions
db = SQLAlchemy()
migrate = Migrate()
mail = Mail()

def create_app(config_class=Config):
    """Application factory pattern for Flask app creation."""
    app = Flask(__name__)
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

    # Error handlers
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('errors/500.html'), 500

    return app

def setup_logging(app):
    """Configure application logging."""
    if not os.path.exists('logs'):
        os.mkdir('logs')

    file_handler = RotatingFileHandler('logs/swarm_director.log',
                                     maxBytes=10240, backupCount=10)
    file_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.setLevel(logging.INFO)
    app.logger.info('SwarmDirector startup')

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True)
```

### 3.2 Configuration Management (config.py)
```python
import os
from dotenv import load_dotenv

basedir = os.path.abspath(os.path.dirname(__file__))
load_dotenv(os.path.join(basedir, '.env'))

class Config:
    """Base configuration class."""
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'dev-secret-key-change-in-production'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'sqlite:///' + os.path.join(basedir, 'instance', 'swarm_director.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # Mail configuration
    MAIL_SERVER = os.environ.get('MAIL_SERVER') or 'localhost'
    MAIL_PORT = int(os.environ.get('MAIL_PORT') or 587)
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')

    # AutoGen configuration
    OPENAI_API_KEY = os.environ.get('OPENAI_API_KEY')
    ANTHROPIC_API_KEY = os.environ.get('ANTHROPIC_API_KEY')

    # Application settings
    POSTS_PER_PAGE = 25
    LANGUAGES = ['en', 'es']

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False

config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

### 3.3 Base Model Class (models/base.py)
```python
from datetime import datetime
from app import db

class BaseModel(db.Model):
    """Base model class with common fields."""
    __abstract__ = True

    id = db.Column(db.Integer, primary_key=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow,
                          onupdate=datetime.utcnow, nullable=False)

    def save(self):
        """Save the model to database."""
        db.session.add(self)
        db.session.commit()

    def delete(self):
        """Delete the model from database."""
        db.session.delete(self)
        db.session.commit()

    def to_dict(self):
        """Convert model to dictionary."""
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
```

---

## 🔌 4. API Endpoints

### 4.1 Main Routes (routes/main.py)
```python
from flask import Blueprint, render_template, jsonify, request
from app import db

main_bp = Blueprint('main', __name__)

@main_bp.route('/')
def index():
    """Main application homepage."""
    return render_template('index.html', title='SwarmDirector')

@main_bp.route('/health')
def health_check():
    """Health check endpoint for monitoring."""
    try:
        # Test database connection
        db.session.execute('SELECT 1')
        return jsonify({
            'status': 'healthy',
            'database': 'connected',
            'timestamp': datetime.utcnow().isoformat()
        })
    except Exception as e:
        return jsonify({
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }), 500

@main_bp.route('/api/status')
def api_status():
    """API status endpoint."""
    return jsonify({
        'api_version': '1.0.0',
        'status': 'operational',
        'endpoints': [
            '/health',
            '/api/status',
            '/api/tasks'
        ]
    })
```

### 4.2 API Endpoint Documentation
| Method | Endpoint | Description | Response |
|--------|----------|-------------|----------|
| GET | `/` | Main homepage | HTML page |
| GET | `/health` | Health check | JSON status |
| GET | `/api/status` | API status | JSON info |
| POST | `/api/tasks` | Submit task | JSON response |

---

## 📦 5. Dependencies

### 5.1 Requirements File (requirements.txt)
```txt
# Core Flask framework
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-Mail==0.9.1

# Database
SQLAlchemy==2.0.23
alembic==1.12.1

# Environment management
python-dotenv==1.0.0

# AI/ML frameworks
pyautogen==0.2.0
openai==1.3.0
anthropic==0.7.0

# Utilities
requests==2.31.0
python-dateutil==2.8.2

# Development tools
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
black==23.9.1
flake8==6.1.0

# Production server
gunicorn==21.2.0

# Additional required packages for complete functionality
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.3
```

### 5.2 Python Version Requirements
- **Minimum Python Version**: 3.8+
- **Recommended Python Version**: 3.10+
- **Tested Python Versions**: 3.8, 3.9, 3.10, 3.11

### 5.3 System Dependencies
```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install python3-dev python3-pip python3-venv sqlite3

# macOS (using Homebrew)
brew install python sqlite

# Windows
# Install Python from python.org
# SQLite is included with Python
```

### 5.4 Environment Variables (.env)
```bash
# Flask configuration
SECRET_KEY=your-secret-key-here-minimum-32-characters-long
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Database configuration
DATABASE_URL=sqlite:///instance/swarm_director.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Mail configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Alternative SMTP configurations
# For Outlook/Hotmail:
# MAIL_SERVER=smtp-mail.outlook.com
# MAIL_PORT=587
# MAIL_USE_TLS=1

# For SendGrid:
# MAIL_SERVER=smtp.sendgrid.net
# MAIL_PORT=587
# MAIL_USE_TLS=1
# MAIL_USERNAME=apikey
# MAIL_PASSWORD=your-sendgrid-api-key

# AI API Keys
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Application settings
POSTS_PER_PAGE=25
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=16777216

# Security settings
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
```

### 5.5 Installation Verification Commands
```bash
# Verify Python version
python --version  # Should be 3.8+

# Verify pip installation
pip --version

# Verify virtual environment creation
python -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate
deactivate
rm -rf test_env

# Verify SQLite installation
sqlite3 --version

# Test package installation
pip install Flask==2.3.3
python -c "import flask; print(flask.__version__)"
```

---

## 🛠️ 6. Implementation Plan

### Step 1: Environment Setup
```bash
# Create project directory
mkdir SwarmDirector
cd SwarmDirector

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Upgrade pip
pip install --upgrade pip
```

### Step 2: Install Dependencies
```bash
# Create requirements.txt (content from section 5.1)
pip install -r requirements.txt
```

### Step 3: Create Project Structure
```bash
# Create directories
mkdir -p instance migrations models agents utils templates static/css static/js static/images tests routes

# Create __init__.py files
touch models/__init__.py agents/__init__.py utils/__init__.py tests/__init__.py routes/__init__.py
```

### Step 4: Create Core Files
1. **Create app.py** (use code from section 3.1)
2. **Create config.py** (use code from section 3.2)
3. **Create .env file** (use template from section 5.2)
4. **Create models/base.py** (use code from section 3.3)
5. **Create routes/main.py** (use code from section 4.1)

### Step 5: Create Templates
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SwarmDirector{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="{{ url_for('main.index') }}">SwarmDirector</a>
        </div>
    </nav>

    <div class="container mt-4">
        {% block content %}{% endblock %}
    </div>

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
</body>
</html>

<!-- templates/index.html -->
{% extends "base.html" %}

{% block content %}
<div class="row">
    <div class="col-md-12">
        <h1>Welcome to SwarmDirector</h1>
        <p class="lead">Hierarchical AI Agent System</p>
        <div class="card">
            <div class="card-body">
                <h5 class="card-title">System Status</h5>
                <p class="card-text">The SwarmDirector system is running and ready to process tasks.</p>
                <a href="/health" class="btn btn-primary">Check Health</a>
                <a href="/api/status" class="btn btn-secondary">API Status</a>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

### Step 6: Initialize Database
```bash
# Initialize Flask-Migrate
flask db init

# Create initial migration
flask db migrate -m "Initial migration"

# Apply migration
flask db upgrade
```

### Step 7: Create Git Repository
```bash
# Initialize git
git init

# Create .gitignore
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/

# Flask
instance/
.env

# Database
*.db
*.sqlite

# IDE
.vscode/
.idea/
*.swp
*.swo

# Logs
logs/
*.log

# OS
.DS_Store
Thumbs.db
EOF

# Initial commit
git add .
git commit -m "Initial Flask application setup"
```

---

## 🧪 7. Testing & QA

### 7.1 Unit Tests (tests/test_app.py)
```python
import pytest
from app import create_app, db
from config import TestingConfig

@pytest.fixture
def app():
    """Create application for testing."""
    app = create_app(TestingConfig)
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

def test_app_creation(app):
    """Test application creation."""
    assert app is not None
    assert app.config['TESTING'] is True

def test_health_endpoint(client):
    """Test health check endpoint."""
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'healthy'

def test_api_status_endpoint(client):
    """Test API status endpoint."""
    response = client.get('/api/status')
    assert response.status_code == 200
    data = response.get_json()
    assert data['api_version'] == '1.0.0'

def test_index_page(client):
    """Test main index page."""
    response = client.get('/')
    assert response.status_code == 200
    assert b'SwarmDirector' in response.data
```

### 7.2 Manual Testing Steps
```bash
# 1. Environment verification
python --version  # Verify Python 3.8+
pip list | grep Flask  # Verify Flask installation

# 2. Start the application
export FLASK_APP=app.py
export FLASK_ENV=development
python app.py

# Alternative startup method
flask run --host=0.0.0.0 --port=5000

# 3. Test endpoints with detailed verification
# Test main page
curl -v http://localhost:5000/
# Expected: 200 status, HTML content with "SwarmDirector"

# Test health endpoint
curl -v -H "Content-Type: application/json" http://localhost:5000/health
# Expected: {"status": "healthy", "database": "connected", "timestamp": "..."}

# Test API status
curl -v -H "Content-Type: application/json" http://localhost:5000/api/status
# Expected: {"api_version": "1.0.0", "status": "operational", "endpoints": [...]}

# 4. Run automated tests with coverage
pytest tests/ -v --cov=. --cov-report=html
# Expected: All tests pass, coverage report generated

# 5. Test database operations
flask shell
>>> from app import db
>>> result = db.session.execute('SELECT 1').scalar()
>>> print(f"Database test result: {result}")  # Should print: 1
>>> from models.base import BaseModel
>>> print("BaseModel imported successfully")
>>> exit()

# 6. Test migrations thoroughly
flask db init  # Initialize migration repository
flask db migrate -m "Initial migration"  # Create migration
flask db upgrade  # Apply migration
flask db current  # Show current revision
flask db history  # Show migration history
flask db downgrade  # Test rollback

# 7. Test configuration loading
python -c "from config import Config; print('Config loaded:', Config.SECRET_KEY[:10] + '...')"

# 8. Test logging functionality
python -c "
import logging
from utils.logging_config import setup_logging
logger = logging.getLogger('test')
logger.info('Test log message')
print('Logging test completed')
"

# 9. Performance testing
curl -w "@curl-format.txt" -o /dev/null -s http://localhost:5000/health
# Create curl-format.txt with timing information
```

### 7.3 Automated Test Suite Enhancement
```python
# tests/test_comprehensive.py
import pytest
import os
import tempfile
from app import create_app, db
from config import TestingConfig

class TestComprehensiveSetup:
    """Comprehensive test suite for project setup validation."""

    @pytest.fixture
    def app(self):
        """Create test application with temporary database."""
        db_fd, db_path = tempfile.mkstemp()

        class TestConfig(TestingConfig):
            SQLALCHEMY_DATABASE_URI = f'sqlite:///{db_path}'

        app = create_app(TestConfig)

        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()

        os.close(db_fd)
        os.unlink(db_path)

    @pytest.fixture
    def client(self, app):
        return app.test_client()

    def test_environment_setup(self):
        """Test that all required environment components are available."""
        import sys
        assert sys.version_info >= (3, 8), "Python 3.8+ required"

        # Test required packages
        import flask
        import sqlalchemy
        import flask_migrate
        import flask_mail

        assert flask.__version__.startswith('2.3'), f"Flask 2.3.x required, got {flask.__version__}"

    def test_configuration_loading(self, app):
        """Test configuration loading and validation."""
        assert app.config['TESTING'] is True
        assert app.config['SQLALCHEMY_DATABASE_URI'] is not None
        assert 'SECRET_KEY' in app.config

    def test_database_operations(self, app):
        """Test database connectivity and operations."""
        with app.app_context():
            # Test basic query
            result = db.session.execute('SELECT 1').scalar()
            assert result == 1

            # Test table creation
            db.create_all()

            # Test BaseModel functionality
            from models.base import BaseModel
            assert hasattr(BaseModel, 'id')
            assert hasattr(BaseModel, 'created_at')
            assert hasattr(BaseModel, 'updated_at')

    def test_all_endpoints_accessible(self, client):
        """Test that all defined endpoints are accessible."""
        endpoints = [
            ('/', 200),
            ('/health', 200),
            ('/api/status', 200),
        ]

        for endpoint, expected_status in endpoints:
            response = client.get(endpoint)
            assert response.status_code == expected_status, f"Endpoint {endpoint} failed"

    def test_error_handling(self, client):
        """Test error handling for non-existent endpoints."""
        response = client.get('/nonexistent')
        assert response.status_code == 404

    def test_logging_configuration(self, app):
        """Test logging setup and functionality."""
        import logging

        with app.app_context():
            logger = app.logger
            assert logger.level <= logging.INFO

            # Test log message
            logger.info("Test log message")
```

### 7.4 Validation Checklist
- [ ] **Environment Setup**
  - [ ] Python 3.8+ installed and accessible
  - [ ] Virtual environment created and activated
  - [ ] All dependencies installed without conflicts
  - [ ] SQLite3 available and functional
- [ ] **Application Startup**
  - [ ] Flask application starts without errors
  - [ ] Application accessible on localhost:5000
  - [ ] No import errors or missing modules
  - [ ] Configuration loads correctly
- [ ] **Endpoint Testing**
  - [ ] GET / returns 200 with HTML content
  - [ ] GET /health returns 200 with JSON status
  - [ ] GET /api/status returns 200 with API info
  - [ ] 404 errors handled gracefully
  - [ ] 500 errors handled gracefully
- [ ] **Database Operations**
  - [ ] Database file created in instance/ directory
  - [ ] Database connection established
  - [ ] Basic queries execute successfully
  - [ ] BaseModel class functional
- [ ] **Migration System**
  - [ ] Flask-Migrate initialized
  - [ ] Migration files generated
  - [ ] Migrations apply successfully
  - [ ] Rollback functionality works
- [ ] **Configuration Management**
  - [ ] Environment variables load correctly
  - [ ] Multiple environment configs work
  - [ ] Secret key properly configured
  - [ ] Database URI correctly formatted
- [ ] **Logging System**
  - [ ] Log files created in logs/ directory
  - [ ] Log messages captured correctly
  - [ ] Log rotation configured
  - [ ] Different log levels work
- [ ] **Static Assets**
  - [ ] Static files serve properly
  - [ ] CSS/JS files accessible
  - [ ] Templates render correctly
  - [ ] Bootstrap styling loads
- [ ] **Testing Framework**
  - [ ] Unit tests run successfully
  - [ ] Test coverage above 80%
  - [ ] Integration tests pass
  - [ ] Performance tests meet criteria

---

## 🔗 8. Integration & Related Tasks

### 8.1 Standalone Implementation
This task is completely self-contained and requires no external dependencies from other tasks. It establishes the foundation that other tasks will build upon.

### 8.2 Outputs for Future Tasks
- **Flask Application**: Ready for agent integration
- **Database Layer**: Prepared for model definitions
- **Configuration System**: Ready for additional settings
- **Logging Framework**: Available for all components
- **Project Structure**: Organized for scalable development

---

## ⚠️ 9. Risks & Mitigations

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Python version compatibility | High | Medium | Use Python 3.8+ and test with versions 3.8, 3.9, 3.10, 3.11 |
| Package dependency conflicts | High | Medium | Use virtual environment, pin specific versions, test installation |
| Database file permissions | Medium | Low | Ensure proper directory permissions, document setup steps |
| Secret key security | High | Medium | Use environment variables, generate strong keys, never commit secrets |
| Port conflicts during development | Low | Medium | Use configurable port settings, check availability, document alternatives |
| Migration failures | Medium | Low | Test migrations thoroughly, maintain rollback procedures, backup data |
| SMTP configuration errors | Medium | Medium | Provide multiple provider examples, validate settings, test email sending |
| Memory/performance issues | Medium | Low | Monitor resource usage, implement proper logging, optimize queries |

### 9.1 Detailed Issue Resolution Guide

**Issue**: `ModuleNotFoundError: No module named 'flask'`
**Symptoms**: Import errors when starting application
**Root Cause**: Virtual environment not activated or packages not installed
**Solution**:
```bash
# Verify virtual environment
which python  # Should point to venv/bin/python
pip list | grep Flask  # Should show Flask==2.3.3

# If not found, reinstall
pip install -r requirements.txt
```

**Issue**: Database permission errors
**Symptoms**: `PermissionError: [Errno 13] Permission denied`
**Root Cause**: Insufficient permissions for instance directory
**Solution**:
```bash
# Create directory with proper permissions
mkdir -p instance
chmod 755 instance
chown $USER:$USER instance

# Verify permissions
ls -la instance/
```

**Issue**: Environment variables not loading
**Symptoms**: Default values used instead of .env values
**Root Cause**: .env file missing or python-dotenv not installed
**Solution**:
```bash
# Verify .env file exists
ls -la .env

# Verify python-dotenv installed
pip show python-dotenv

# Test environment loading
python -c "
import os
from dotenv import load_dotenv
load_dotenv()
print('SECRET_KEY loaded:', bool(os.getenv('SECRET_KEY')))
"
```

**Issue**: Flask application won't start
**Symptoms**: Various startup errors
**Root Cause**: Configuration or import issues
**Solution**:
```bash
# Test configuration
python -c "from config import Config; print('Config OK')"

# Test imports
python -c "from app import create_app; print('App creation OK')"

# Check for syntax errors
python -m py_compile app.py
python -m py_compile config.py
```

**Issue**: Database migration errors
**Symptoms**: Migration commands fail
**Root Cause**: Database schema conflicts or migration state issues
**Solution**:
```bash
# Reset migration state
rm -rf migrations/
flask db init
flask db migrate -m "Initial migration"
flask db upgrade

# If database exists, backup and recreate
cp instance/swarm_director.db instance/swarm_director.db.backup
rm instance/swarm_director.db
flask db upgrade
```

### 9.2 Performance Optimization Guidelines

**Memory Usage Optimization**:
```python
# config.py additions for production
class ProductionConfig(Config):
    # Optimize SQLAlchemy
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20
    }

    # Optimize Flask
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max file size
```

**Database Performance**:
```python
# Add to models/base.py
class BaseModel(db.Model):
    __abstract__ = True

    # Add indexes for common queries
    id = db.Column(db.Integer, primary_key=True, index=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow,
                          nullable=False, index=True)
```

---

## ✅ 10. Success Criteria

### 10.1 Functional Requirements
- [ ] Flask application starts successfully on localhost:5000
- [ ] Health endpoint returns 200 status with database connectivity
- [ ] API status endpoint returns version information
- [ ] Index page renders with Bootstrap styling
- [ ] SQLite database file created in instance/ directory
- [ ] Database migrations system functional (init, migrate, upgrade)
- [ ] Logging system captures application events to logs/ directory
- [ ] All required packages install without conflicts
- [ ] Virtual environment isolates project dependencies

### 10.2 Technical Requirements
- [ ] Application follows Flask application factory pattern
- [ ] Configuration management supports multiple environments
- [ ] Database models use BaseModel with common fields
- [ ] Error handling includes 404 and 500 pages
- [ ] Project structure follows Flask best practices
- [ ] Git repository initialized with proper .gitignore
- [ ] Environment variables properly configured
- [ ] Unit tests achieve 80%+ coverage

### 10.3 Quality Requirements
- [ ] Code follows PEP 8 style guidelines
- [ ] No security vulnerabilities in dependencies
- [ ] Application starts in under 5 seconds
- [ ] Memory usage under 100MB for basic operations
- [ ] All endpoints respond in under 1 second

---

## 🚀 11. Next Steps

### 11.1 Immediate Actions
1. **Verify Installation**: Run all test commands to ensure setup is correct
2. **Customize Configuration**: Update .env file with actual values
3. **Test Deployment**: Ensure application works in different environments
4. **Documentation**: Add any project-specific notes to README.md

### 11.2 Future Development
1. **Database Models**: Ready to implement specific data models
2. **Agent Integration**: Framework prepared for AI agent components
3. **API Expansion**: Foundation ready for additional endpoints
4. **Security Enhancements**: Authentication and authorization can be added
5. **Performance Optimization**: Monitoring and caching can be implemented

### 11.3 Complete Reference Documentation

**Essential Documentation Links**:
- **Flask Documentation**: https://flask.palletsprojects.com/
- **SQLAlchemy Documentation**: https://docs.sqlalchemy.org/
- **Flask-Migrate Documentation**: https://flask-migrate.readthedocs.io/
- **Flask-Mail Documentation**: https://flask-mail.readthedocs.io/
- **Python Virtual Environments**: https://docs.python.org/3/tutorial/venv.html
- **AutoGen Documentation**: https://microsoft.github.io/autogen/

**Configuration Examples**:
```python
# Complete production configuration template
class ProductionConfig(Config):
    DEBUG = False
    TESTING = False

    # Security settings
    SECRET_KEY = os.environ.get('SECRET_KEY')
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'

    # Database optimization
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_recycle': 300,
        'pool_size': 10,
        'max_overflow': 20,
        'echo': False
    }

    # Logging configuration
    LOG_LEVEL = 'INFO'
    LOG_FILE = 'logs/swarm_director.log'

    # Email configuration with error handling
    MAIL_SUPPRESS_SEND = False
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER')

    # Performance settings
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024
    SEND_FILE_MAX_AGE_DEFAULT = 31536000  # 1 year
```

**Deployment Checklist**:
- [ ] Environment variables configured
- [ ] Database migrations applied
- [ ] Static files collected
- [ ] Logging configured
- [ ] Error monitoring setup
- [ ] Security headers configured
- [ ] SSL/TLS certificates installed
- [ ] Backup procedures established
- [ ] Monitoring and alerting configured
- [ ] Performance testing completed

**Security Hardening**:
```python
# Additional security headers
@app.after_request
def security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'DENY'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
    return response
```

**Monitoring and Health Checks**:
```python
# Enhanced health check endpoint
@main_bp.route('/health/detailed')
def detailed_health_check():
    health_status = {
        'status': 'healthy',
        'timestamp': datetime.utcnow().isoformat(),
        'version': '1.0.0',
        'checks': {}
    }

    # Database check
    try:
        db.session.execute('SELECT 1')
        health_status['checks']['database'] = 'healthy'
    except Exception as e:
        health_status['checks']['database'] = f'unhealthy: {str(e)}'
        health_status['status'] = 'unhealthy'

    # Disk space check
    import shutil
    total, used, free = shutil.disk_usage('/')
    health_status['checks']['disk_space'] = {
        'free_gb': free // (1024**3),
        'used_percent': (used / total) * 100
    }

    # Memory check
    import psutil
    memory = psutil.virtual_memory()
    health_status['checks']['memory'] = {
        'available_gb': memory.available // (1024**3),
        'used_percent': memory.percent
    }

    return jsonify(health_status)
```
