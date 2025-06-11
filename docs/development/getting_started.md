# SwarmDirector Development Guide

This guide will help you set up a development environment and start contributing to SwarmDirector.

## 🚀 Quick Setup

### Prerequisites

- **Python 3.8+** (3.9+ recommended)
- **Git** for version control
- **Virtual environment** tool (venv, virtualenv, or conda)
- **Code editor** (VS Code, PyCharm, or similar)

### 1. Clone the Repository

```bash
git clone https://github.com/blopit/SwarmDirector.git
cd SwarmDirector
```

### 2. Set Up Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
# Install all dependencies
pip install -r requirements.txt

# Install development dependencies (if available)
pip install -r requirements-dev.txt
```

### 4. Set Up Environment Variables

Create a `.env` file in the project root:

```bash
# Copy example environment file
cp .env.example .env

# Edit .env with your settings
# Required variables:
SECRET_KEY=your-secret-key-here
FLASK_ENV=development
DATABASE_URL=sqlite:///database/data/swarm_director_dev.db
```

### 5. Initialize Database

```bash
# Initialize database with migrations
python -m flask db upgrade

# Or run the database setup script
python scripts/setup_database.py
```

### 6. Run the Application

```bash
# Start the development server
python src/swarm_director/app.py

# Or use Flask CLI
export FLASK_APP=src/swarm_director/app.py
flask run
```

### 7. Verify Installation

Visit these URLs to verify everything is working:

- **Main Application**: http://localhost:5000
- **Health Check**: http://localhost:5000/health
- **Dashboard**: http://localhost:5000/dashboard
- **Demo Interface**: http://localhost:5000/demo

## 🧪 Running Tests

### Run All Tests
```bash
# Run the complete test suite
pytest tests/

# Run with coverage report
pytest --cov=src/swarm_director tests/

# Run with verbose output
pytest -v tests/
```

### Run Specific Test Categories
```bash
# Test specific modules
pytest tests/test_agents/
pytest tests/test_models/
pytest tests/test_api/

# Test specific files
pytest tests/test_app.py
pytest tests/test_database_utils.py
```

### Test Configuration

Tests use a separate test database and configuration:

```python
# tests/conftest.py
@pytest.fixture
def app():
    app = create_app('testing')
    return app
```

## 🏗️ Project Structure for Developers

### Key Directories

```
src/swarm_director/          # Main application code
├── agents/                  # Agent implementations
├── models/                  # Database models
├── utils/                   # Utility functions
└── web/                     # Web interface

tests/                       # Test suite
├── test_agents/            # Agent tests
├── test_models/            # Model tests
└── fixtures/               # Test data

docs/                       # Documentation
scripts/                    # Utility scripts
examples/                   # Example code
```

### Important Files

- **`src/swarm_director/app.py`**: Main Flask application
- **`src/swarm_director/config.py`**: Configuration management
- **`src/swarm_director/models/base.py`**: Base model class
- **`requirements.txt`**: Python dependencies

## 🔧 Development Workflow

### 1. Create a Feature Branch

```bash
git checkout -b feature/your-feature-name
```

### 2. Make Changes

Follow the coding standards and patterns established in the codebase:

- Use type hints where appropriate
- Follow PEP 8 style guidelines
- Write docstrings for functions and classes
- Add tests for new functionality

### 3. Run Tests

```bash
# Run tests before committing
pytest tests/

# Check code style
flake8 src/
black --check src/
```

### 4. Commit Changes

```bash
git add .
git commit -m "feat: add new feature description"
```

### 5. Push and Create Pull Request

```bash
git push origin feature/your-feature-name
# Create pull request on GitHub
```

## 🛠️ Development Tools

### Recommended VS Code Extensions

```json
{
  "recommendations": [
    "ms-python.python",
    "ms-python.flake8",
    "ms-python.black-formatter",
    "ms-python.isort",
    "ms-vscode.vscode-json",
    "redhat.vscode-yaml"
  ]
}
```

### Code Formatting

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Check style with flake8
flake8 src/ tests/
```

### Database Management

```bash
# Create new migration
flask db migrate -m "Description of changes"

# Apply migrations
flask db upgrade

# Downgrade migration
flask db downgrade

# View migration history
flask db history
```

## 🐛 Debugging

### Enable Debug Mode

```python
# In src/swarm_director/app.py
app.config['DEBUG'] = True
```

### Database Debugging

```python
# Enable SQL query logging
app.config['SQLALCHEMY_ECHO'] = True
```

### Logging Configuration

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Issues

1. **Import Errors**: Check PYTHONPATH and virtual environment
2. **Database Errors**: Verify database file permissions and migrations
3. **Port Conflicts**: Change port in app.run(port=5001)

## 📝 Code Style Guidelines

### Python Style

- Follow PEP 8 conventions
- Use type hints for function parameters and return values
- Maximum line length: 88 characters (Black default)
- Use descriptive variable and function names

### Documentation

- Write docstrings for all public functions and classes
- Use Google-style docstrings
- Include examples in docstrings where helpful

### Testing

- Write tests for all new functionality
- Use descriptive test names
- Follow AAA pattern (Arrange, Act, Assert)
- Mock external dependencies

## 🔄 Git Workflow

### Commit Message Format

```
type(scope): description

Types:
- feat: New feature
- fix: Bug fix
- docs: Documentation changes
- style: Code style changes
- refactor: Code refactoring
- test: Test additions/changes
- chore: Maintenance tasks
```

### Branch Naming

```
feature/feature-name
bugfix/bug-description
hotfix/critical-fix
docs/documentation-update
```

## 🚀 Deployment for Development

### Local Docker Development

```bash
# Build Docker image
docker build -t swarm-director .

# Run container
docker run -p 5000:5000 swarm-director
```

### Environment-Specific Configuration

```python
# config/development.py
class DevelopmentConfig(Config):
    DEBUG = True
    SQLALCHEMY_ECHO = True
    LOG_LEVEL = 'DEBUG'
```

## 📚 Learning Resources

### Flask Development
- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-SQLAlchemy](https://flask-sqlalchemy.palletsprojects.com/)
- [Flask-Migrate](https://flask-migrate.readthedocs.io/)

### Testing
- [pytest Documentation](https://docs.pytest.org/)
- [Testing Flask Applications](https://flask.palletsprojects.com/testing/)

### AI/ML Integration
- [Microsoft AutoGen](https://microsoft.github.io/autogen/)
- [OpenAI API](https://platform.openai.com/docs)

## 🆘 Getting Help

### Documentation
- Check the `docs/` directory for detailed documentation
- Review existing code for patterns and examples

### Community
- GitHub Issues for bug reports
- GitHub Discussions for questions
- Code reviews for learning

### Debugging Resources
- Use the Flask debugger for runtime issues
- Check logs in the `logs/` directory
- Use pytest for test debugging

## 🎯 Next Steps

1. **Explore the Codebase**: Start with `src/swarm_director/app.py`
2. **Run the Tests**: Understand the test structure
3. **Try the Examples**: Run code in `examples/`
4. **Read the Documentation**: Review architecture and API docs
5. **Start Contributing**: Pick an issue and submit a PR

Happy coding! 🚀
