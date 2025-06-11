# Local Development Deployment Guide

This guide covers setting up SwarmDirector for local development, including various configuration options and troubleshooting tips.

## 🚀 Quick Start

### Minimal Setup

```bash
# Clone and enter directory
git clone https://github.com/blopit/SwarmDirector.git
cd SwarmDirector

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run with default settings
python src/swarm_director/app.py
```

Access the application at http://localhost:5000

## 🔧 Configuration Options

### Environment Variables

Create a `.env` file in the project root:

```bash
# Basic Configuration
SECRET_KEY=your-development-secret-key
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///database/data/swarm_director_dev.db
SQLALCHEMY_ECHO=False  # Set to True for SQL query logging

# Email Configuration (optional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=True

# Agent Configuration
DEFAULT_AGENT_TIMEOUT=30
MAX_CONCURRENT_TASKS=10
```

### Configuration Classes

SwarmDirector uses different configuration classes for different environments:

```python
# src/swarm_director/config.py
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///database/data/swarm_director_dev.db'
    SQLALCHEMY_ECHO = True  # Log SQL queries
    LOG_LEVEL = 'DEBUG'
```

## 🗄️ Database Setup

### SQLite (Default)

SQLite is used by default for development - no additional setup required.

```bash
# Initialize database
python -c "from src.swarm_director.app import create_app; from src.swarm_director.models.base import db; app = create_app(); app.app_context().push(); db.create_all()"

# Or use Flask-Migrate
export FLASK_APP=src/swarm_director/app.py
flask db upgrade
```

### PostgreSQL (Optional)

For testing with PostgreSQL locally:

```bash
# Install PostgreSQL
brew install postgresql  # macOS
sudo apt-get install postgresql  # Ubuntu

# Create database
createdb swarm_director_dev

# Update .env
DATABASE_URL=postgresql://username:password@localhost/swarm_director_dev
```

### Database Migrations

```bash
# Create migration
flask db migrate -m "Description of changes"

# Apply migration
flask db upgrade

# Rollback migration
flask db downgrade
```

## 🔍 Development Tools

### Debug Mode

Enable comprehensive debugging:

```python
# In .env
FLASK_DEBUG=True
FLASK_ENV=development

# Or in code
app.run(debug=True)
```

### SQL Query Logging

Monitor database queries:

```python
# In .env
SQLALCHEMY_ECHO=True

# Or in config
app.config['SQLALCHEMY_ECHO'] = True
```

### Hot Reloading

Flask automatically reloads on code changes when debug mode is enabled.

## 🧪 Testing Setup

### Test Database

Tests use a separate in-memory database:

```python
# tests/conftest.py
@pytest.fixture
def app():
    app = create_app('testing')
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()
```

### Running Tests

```bash
# Run all tests
pytest tests/

# Run with coverage
pytest --cov=src/swarm_director tests/

# Run specific test file
pytest tests/test_app.py -v

# Run tests with database logging
pytest tests/ --log-cli-level=DEBUG
```

## 📊 Monitoring and Logging

### Application Logs

```bash
# View logs in real-time
tail -f logs/swarm_director.log

# Or use Python logging
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Health Monitoring

```bash
# Check application health
curl http://localhost:5000/health

# Check system status
curl http://localhost:5000/demo/api/system_status
```

## 🔧 Development Utilities

### Database CLI

```bash
# Access database CLI
python src/swarm_director/utils/db_cli.py

# Common operations
python -c "from src.swarm_director.utils.database import get_database_info; print(get_database_info())"
```

### Context File Management

```bash
# Update context files
python scripts/update_context_files.py

# Validate context files
python scripts/validate_context_files.py
```

## 🐛 Troubleshooting

### Common Issues

#### Port Already in Use
```bash
# Find process using port 5000
lsof -i :5000

# Kill process
kill -9 <PID>

# Or use different port
python src/swarm_director/app.py --port 5001
```

#### Database Locked
```bash
# Check for database locks
fuser database/data/swarm_director_dev.db

# Remove lock file if exists
rm database/data/swarm_director_dev.db-wal
rm database/data/swarm_director_dev.db-shm
```

#### Import Errors
```bash
# Check Python path
python -c "import sys; print(sys.path)"

# Add project root to PYTHONPATH
export PYTHONPATH="${PYTHONPATH}:$(pwd)"
```

#### Virtual Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Debug Techniques

#### Flask Debug Toolbar
```python
# Install debug toolbar
pip install flask-debugtoolbar

# Enable in config
app.config['DEBUG_TB_ENABLED'] = True
```

#### Database Debugging
```python
# Check database connection
from src.swarm_director.models.base import db
print(db.engine.url)

# Inspect tables
from sqlalchemy import inspect
inspector = inspect(db.engine)
print(inspector.get_table_names())
```

#### Agent Debugging
```python
# Enable agent logging
import logging
logging.getLogger('agents').setLevel(logging.DEBUG)
```

## 🔄 Development Workflow

### Code Changes

1. **Make changes** to source code
2. **Flask auto-reloads** (if debug mode enabled)
3. **Test changes** manually or with automated tests
4. **Check logs** for any errors

### Database Changes

1. **Modify models** in `src/swarm_director/models/`
2. **Create migration**: `flask db migrate -m "Description"`
3. **Apply migration**: `flask db upgrade`
4. **Test changes** with sample data

### Adding New Features

1. **Create feature branch**: `git checkout -b feature/new-feature`
2. **Implement feature** with tests
3. **Run test suite**: `pytest tests/`
4. **Update documentation** if needed
5. **Submit pull request**

## 📱 Mobile Development

### Responsive Testing

```bash
# Test responsive design
# Use browser dev tools or:
curl -H "User-Agent: Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)" http://localhost:5000
```

## 🔒 Security in Development

### Development Security

```bash
# Use development secret key
SECRET_KEY=dev-secret-key-not-for-production

# Disable HTTPS redirect in development
FORCE_HTTPS=False

# Enable CORS for frontend development
CORS_ENABLED=True
```

## 📈 Performance Monitoring

### Local Performance Testing

```bash
# Install performance testing tools
pip install locust

# Run performance tests
locust -f tests/performance/locustfile.py --host=http://localhost:5000
```

### Memory Profiling

```python
# Install memory profiler
pip install memory-profiler

# Profile memory usage
python -m memory_profiler src/swarm_director/app.py
```

## 🚀 Advanced Development Setup

### Docker Development

```bash
# Build development image
docker build -f Dockerfile.dev -t swarm-director-dev .

# Run with volume mounting
docker run -p 5000:5000 -v $(pwd):/app swarm-director-dev
```

### IDE Configuration

#### VS Code Settings
```json
{
  "python.defaultInterpreterPath": "./venv/bin/python",
  "python.testing.pytestEnabled": true,
  "python.testing.pytestArgs": ["tests/"],
  "python.linting.flake8Enabled": true,
  "python.formatting.provider": "black"
}
```

#### PyCharm Configuration
- Set interpreter to `./venv/bin/python`
- Configure test runner to pytest
- Enable Flask support in project settings

## 📚 Development Resources

### Documentation
- Flask: https://flask.palletsprojects.com/
- SQLAlchemy: https://docs.sqlalchemy.org/
- pytest: https://docs.pytest.org/

### Tools
- Flask-DebugToolbar: Debug information overlay
- Flask-Shell-IPython: Enhanced shell experience
- Werkzeug: WSGI utilities and debugging

This setup provides a comprehensive development environment for SwarmDirector with debugging capabilities, testing infrastructure, and development utilities.
