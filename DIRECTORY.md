# SwarmDirector Root Directory

## Purpose
The root directory of SwarmDirector, a comprehensive three-tier AI agent management system for task orchestration and high-accuracy content delivery. This directory contains the main project configuration, entry points, and top-level organization for the hierarchical AI agent framework.

## Structure
```
SwarmDirector/
├── src/                          # Source code directory
│   └── swarm_director/          # Main application package
├── tests/                       # Test suite with comprehensive coverage
├── scripts/                     # Utility and maintenance scripts
├── examples/                    # Demo applications and usage examples
├── docs/                        # Project documentation
├── database/                    # Database schemas, migrations, and data
├── config/                      # Configuration files for different environments
├── logs/                        # Application logs and monitoring data
├── venv/                        # Virtual environment (local development)
├── requirements.txt             # Python dependencies with pinned versions
├── run.py                       # Application entry point
├── Makefile                     # Build and development commands
├── README.md                    # Project overview and quick start guide
├── PRD.md                       # Product Requirements Document
├── QUICKSTART.md               # Quick start guide for developers
└── LICENSE                      # MIT license file
```

## Guidelines

### 1. Organization
- **Source Separation**: Keep source code in `src/` directory following Python packaging best practices
- **Environment Isolation**: Use virtual environments for dependency management
- **Configuration Management**: Store environment-specific configs in `config/` directory
- **Documentation First**: Maintain comprehensive documentation in `docs/` directory
- **Test Coverage**: Ensure all functionality is covered by tests in `tests/` directory

### 2. Naming
- **Files**: Use lowercase with underscores (snake_case) for Python files
- **Directories**: Use lowercase with underscores or hyphens for consistency
- **Scripts**: Use descriptive names indicating their purpose (e.g., `setup_development.py`)
- **Documentation**: Use UPPERCASE for important files (README.md, LICENSE)

### 3. Implementation
- **Entry Point**: Use `run.py` as the main application entry point
- **Dependencies**: Pin exact versions in `requirements.txt` for reproducibility
- **Environment Variables**: Use `.env` files for local development (not committed)
- **Logging**: Configure centralized logging to `logs/` directory
- **Database**: Store development database in `database/data/` directory

### 4. Documentation
- **README First**: Maintain comprehensive README.md with quick start instructions
- **API Documentation**: Keep API docs in `docs/api/` directory
- **Architecture**: Document system design in `docs/architecture/` directory
- **Change Tracking**: Maintain CHANGELOG.md for version history

## Best Practices

### 1. Error Handling
- **Graceful Degradation**: Handle missing dependencies gracefully (e.g., AutoGen optional imports)
- **Comprehensive Logging**: Log all errors with context and stack traces
- **User-Friendly Messages**: Provide clear error messages for common issues
- **Recovery Mechanisms**: Implement fallback strategies for critical failures

### 2. Security
- **Dependency Management**: Regularly update dependencies and check for vulnerabilities
- **Environment Variables**: Never commit sensitive data to version control
- **Database Security**: Use parameterized queries and proper access controls
- **API Security**: Implement authentication and rate limiting for production

### 3. Performance
- **Database Optimization**: Use proper indexing and query optimization
- **Caching**: Implement caching strategies for frequently accessed data
- **Resource Management**: Monitor memory and CPU usage in production
- **Async Operations**: Use asynchronous processing for long-running tasks

### 4. Testing
- **Comprehensive Coverage**: Maintain >85% test coverage across all modules
- **Test Isolation**: Use temporary directories and cleanup procedures
- **Integration Tests**: Test complete workflows end-to-end
- **Performance Tests**: Include benchmarks for critical operations

### 5. Documentation
- **Self-Documenting Code**: Use clear variable names and comprehensive docstrings
- **API Documentation**: Maintain up-to-date API documentation with examples
- **Architecture Diagrams**: Include visual representations of system design
- **Deployment Guides**: Provide clear instructions for different environments

## Example

### Complete Project Setup and Basic Usage

```python
#!/usr/bin/env python3
"""
SwarmDirector Project Setup and Basic Usage Example
Demonstrates proper project initialization and basic agent workflow
"""

import os
import sys
from pathlib import Path

# Add src to Python path for development
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root / "src"))

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType
from swarm_director.models.task import Task, TaskStatus
from swarm_director.agents.director import DirectorAgent

def setup_project():
    """Initialize the SwarmDirector project"""
    # Create Flask application
    app = create_app()
    
    with app.app_context():
        # Initialize database
        db.create_all()
        print("✅ Database initialized successfully")
        
        # Create director agent
        director_db = Agent(
            name="MainDirector",
            description="Primary director agent for task routing",
            agent_type=AgentType.SUPERVISOR
        )
        director_db.save()
        
        director = DirectorAgent(director_db)
        print(f"✅ Director agent created: {director.name}")
        
        return app, director

def demonstrate_workflow(director):
    """Demonstrate basic SwarmDirector workflow"""
    # Create a sample task
    task = Task(
        title="Generate Email Response",
        description="Create a professional email response to customer inquiry",
        task_type="communication",
        priority=1,
        status=TaskStatus.PENDING,
        input_data={
            "customer_message": "I need help with my account",
            "tone": "professional",
            "urgency": "normal"
        }
    )
    task.save()
    
    print(f"📝 Created task: {task.title}")
    
    # Route task through director
    if director.can_handle_task(task):
        result = director.execute_task(task)
        print(f"✅ Task completed: {result['status']}")
        return result
    else:
        print("❌ Director cannot handle this task type")
        return None

if __name__ == "__main__":
    try:
        # Setup project
        app, director = setup_project()
        
        # Demonstrate workflow
        with app.app_context():
            result = demonstrate_workflow(director)
            
        print("\n🎉 SwarmDirector setup and demo completed successfully!")
        print("🌐 Start the web interface with: python run.py")
        print("📊 Access dashboard at: http://localhost:5000/dashboard")
        
    except Exception as e:
        print(f"❌ Error during setup: {e}")
        sys.exit(1)
```

### Development Workflow

```bash
# 1. Project Setup
git clone https://github.com/blopit/SwarmDirector.git
cd SwarmDirector
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# 2. Install Dependencies
pip install -r requirements.txt

# 3. Initialize Database
python -c "
import sys; sys.path.insert(0, 'src')
from swarm_director.app import create_app
from swarm_director.models.base import db
app = create_app()
with app.app_context(): db.create_all()
"

# 4. Run Tests
pytest tests/ --cov=src/swarm_director

# 5. Start Application
python run.py

# 6. Development Commands
make test          # Run test suite
make lint          # Code quality checks
make docs          # Generate documentation
make clean         # Clean build artifacts
```

## Related Documentation
- [Project Structure](docs/PROJECT_STRUCTURE.md) - Detailed project organization
- [Quick Start Guide](QUICKSTART.md) - Fast setup instructions
- [API Documentation](docs/api/README.md) - REST API reference
- [Architecture Overview](docs/architecture/overview.md) - System design
- [Development Guide](docs/development/getting_started.md) - Developer onboarding
- [Deployment Guide](docs/deployment/local_development.md) - Deployment instructions
- [Contributing Guidelines](docs/CONTRIBUTING.md) - Contribution process
