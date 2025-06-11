# SwarmDirector Project Structure

This document provides a comprehensive overview of the SwarmDirector project organization, explaining the purpose and contents of each directory and key files.

## 📁 Directory Overview

```
SwarmDirector/
├── 📂 src/                          # Source code
│   └── 📂 swarm_director/          # Main application package
│       ├── 📂 agents/              # AI agent implementations
│       ├── 📂 models/              # Database models
│       ├── 📂 utils/               # Utility functions
│       └── 📂 web/                 # Web interface components
├── 📂 tests/                       # Test suite
├── 📂 scripts/                     # Utility scripts
├── 📂 examples/                    # Demo applications
├── 📂 docs/                        # Documentation
├── 📂 database/                    # Database files and schemas
├── 📂 config/                      # Configuration files
├── 📂 logs/                        # Application logs
├── 📂 venv/                        # Virtual environment (local)
├── 📄 requirements.txt             # Python dependencies
├── 📄 README.md                    # Project overview
├── 📄 LICENSE                      # License information
└── 📄 PRD.md                       # Product Requirements Document
```

## 🔍 Detailed Directory Structure

### `/src/swarm_director/` - Main Application Package

The core application code organized as a proper Python package.

```
src/swarm_director/
├── __init__.py                     # Package initialization
├── app.py                          # Flask application factory
├── config.py                       # Configuration management
├── 📂 agents/                      # AI Agent implementations
│   ├── __init__.py
│   ├── base_agent.py              # Base agent class
│   ├── director.py                # Director agent (routing)
│   ├── supervisor_agent.py        # Supervisor agent
│   └── worker_agent.py            # Worker agent
├── 📂 models/                      # Database models (SQLAlchemy)
│   ├── __init__.py
│   ├── base.py                    # Base model class
│   ├── agent.py                   # Agent model
│   ├── task.py                    # Task model
│   ├── conversation.py            # Conversation & Message models
│   ├── draft.py                   # Draft model
│   ├── email_message.py           # Email message model
│   └── agent_log.py               # Agent logging model
├── 📂 utils/                       # Utility functions
│   ├── __init__.py
│   ├── database.py                # Database utilities
│   ├── logging.py                 # Logging configuration
│   ├── migrations.py              # Migration utilities
│   ├── autogen_helpers.py         # AutoGen integration helpers
│   └── db_cli.py                  # Database CLI commands
└── 📂 web/                         # Web interface components
    ├── __init__.py
    ├── 📂 static/                  # Static assets (CSS, JS, images)
    └── 📂 templates/               # Jinja2 templates
        └── 📂 demo/                # Demo interface templates
```

### `/tests/` - Test Suite

Comprehensive test coverage organized by component.

```
tests/
├── __init__.py                     # Test package initialization
├── conftest.py                     # Pytest configuration and fixtures
├── 📂 test_agents/                 # Agent-related tests
│   ├── __init__.py
│   ├── test_base_agent.py         # Base agent tests
│   ├── test_director.py           # Director agent tests
│   ├── test_supervisor.py         # Supervisor agent tests
│   └── test_worker.py             # Worker agent tests
├── 📂 test_models/                 # Database model tests
│   ├── __init__.py
│   ├── test_agent_model.py        # Agent model tests
│   ├── test_task_model.py         # Task model tests
│   ├── test_conversation_model.py # Conversation model tests
│   └── test_relationships.py      # Model relationship tests
├── 📂 test_api/                    # API endpoint tests
│   ├── __init__.py
│   ├── test_agent_api.py          # Agent API tests
│   ├── test_task_api.py           # Task API tests
│   └── test_conversation_api.py   # Conversation API tests
├── 📂 test_utils/                  # Utility function tests
│   ├── __init__.py
│   ├── test_database_utils.py     # Database utility tests
│   └── test_logging_utils.py      # Logging utility tests
├── 📂 fixtures/                    # Test data and fixtures
│   ├── sample_agents.json         # Sample agent data
│   ├── sample_tasks.json          # Sample task data
│   └── test_database.db           # Test database
└── 📂 integration/                 # Integration tests
    ├── __init__.py
    ├── test_app_integration.py     # Full application tests
    └── test_workflow_integration.py # End-to-end workflow tests
```

### `/scripts/` - Utility Scripts

Administrative and maintenance scripts.

```
scripts/
├── comprehensive_context_updater.py # Context file updater
├── update_context_files.py         # Context file maintenance
├── validate_context_files.py       # Context file validation
├── final_verification.py           # System verification
├── setup_development.py            # Development environment setup
├── backup_database.py              # Database backup utility
└── performance_monitor.py          # Performance monitoring
```

### `/examples/` - Demo Applications

Example implementations and demonstrations.

```
examples/
├── demo_app.py                     # Interactive demo application
├── demo_director_agent.py          # Director agent demonstration
├── basic_usage.py                  # Basic usage examples
├── advanced_workflows.py           # Advanced workflow examples
└── 📂 sample_data/                 # Sample data for demos
    ├── sample_tasks.json           # Sample task definitions
    └── sample_agents.json          # Sample agent configurations
```

### `/docs/` - Documentation

Comprehensive project documentation.

```
docs/
├── PROJECT_STRUCTURE.md            # This file
├── CONTRIBUTING.md                 # Contribution guidelines
├── CHANGELOG.md                    # Version history
├── 📂 api/                         # API documentation
│   ├── README.md                   # API overview
│   ├── agents.md                   # Agent API reference
│   ├── tasks.md                    # Task API reference
│   ├── conversations.md            # Conversation API reference
│   └── authentication.md          # Authentication guide
├── 📂 architecture/                # System architecture
│   ├── overview.md                 # Architecture overview
│   ├── database_design.md          # Database schema design
│   ├── agent_hierarchy.md          # Agent hierarchy design
│   └── workflow_patterns.md        # Common workflow patterns
├── 📂 deployment/                  # Deployment guides
│   ├── local_development.md        # Local setup guide
│   ├── docker_deployment.md        # Docker deployment
│   ├── production_deployment.md    # Production deployment
│   └── monitoring.md               # Monitoring and logging
├── 📂 development/                 # Development guides
│   ├── getting_started.md          # Developer onboarding
│   ├── coding_standards.md         # Code style guidelines
│   ├── testing_guide.md            # Testing best practices
│   └── debugging.md                # Debugging techniques
└── 📂 tasks/                       # Task-specific documentation
    └── (task-specific context files)
```

### `/database/` - Database Files and Schemas

Database-related files organized by purpose.

```
database/
├── 📂 schemas/                     # Database schema definitions
│   ├── database_schema.sql         # Main schema definition
│   ├── database_schema_documented.sql # Documented schema
│   └── schema_migrations.sql       # Migration scripts
├── 📂 migrations/                  # Alembic migration files
│   ├── README                      # Migration documentation
│   ├── alembic.ini                 # Alembic configuration
│   ├── env.py                      # Migration environment
│   ├── script.py.mako              # Migration template
│   └── 📂 versions/                # Migration versions
├── 📂 data/                        # Database files
│   ├── swarm_director_dev.db       # Development database
│   ├── swarm_director_dev_backup.db # Development backup
│   └── 📂 backups/                 # Database backups
└── 📂 seeds/                       # Seed data
    ├── initial_agents.sql          # Initial agent data
    └── sample_tasks.sql            # Sample task data
```

### `/config/` - Configuration Files

Environment-specific configuration files.

```
config/
├── __init__.py                     # Configuration package
├── base.py                         # Base configuration
├── development.py                  # Development settings
├── testing.py                      # Testing configuration
├── production.py                   # Production settings
├── 📂 docker/                      # Docker configurations
│   ├── Dockerfile                  # Docker image definition
│   ├── docker-compose.yml          # Docker Compose setup
│   └── docker-compose.prod.yml     # Production Docker setup
└── 📂 nginx/                       # Nginx configurations
    ├── nginx.conf                  # Nginx configuration
    └── ssl/                        # SSL certificates
```

## 📋 Key Files Description

### Root Level Files

- **`requirements.txt`**: Python package dependencies with pinned versions
- **`README.md`**: Project overview, quick start guide, and basic documentation
- **`LICENSE`**: MIT license for the project
- **`PRD.md`**: Product Requirements Document outlining system specifications
- **`.gitignore`**: Git ignore patterns for Python projects
- **`setup.py`**: Python package setup configuration (if needed)

### Configuration Files

- **`src/swarm_director/config.py`**: Flask application configuration classes
- **`config/base.py`**: Base configuration shared across environments
- **`config/development.py`**: Development-specific settings
- **`config/production.py`**: Production-specific settings

### Core Application Files

- **`src/swarm_director/app.py`**: Flask application factory and route definitions
- **`src/swarm_director/models/base.py`**: SQLAlchemy base model with common functionality
- **`src/swarm_director/agents/base_agent.py`**: Base class for all AI agents
- **`src/swarm_director/utils/database.py`**: Database connection and utility functions

## 🔄 File Organization Principles

### 1. **Separation of Concerns**
- Source code separated from tests, documentation, and configuration
- Clear boundaries between different types of files

### 2. **Logical Grouping**
- Related files grouped in appropriate directories
- Consistent naming conventions throughout

### 3. **Scalability**
- Structure supports adding new components without reorganization
- Clear patterns for extending functionality

### 4. **Standard Compliance**
- Follows Python packaging best practices
- Adheres to Flask application structure conventions

### 5. **Development Workflow**
- Easy navigation for developers
- Clear separation of development vs. production concerns

## 🚀 Navigation Tips

### For New Developers
1. Start with `README.md` for project overview
2. Review `docs/development/getting_started.md` for setup
3. Examine `src/swarm_director/` for core functionality
4. Check `tests/` for usage examples

### For API Users
1. Review `docs/api/README.md` for API overview
2. Check specific API documentation in `docs/api/`
3. Use `examples/` for implementation examples

### For System Administrators
1. Review `docs/deployment/` for deployment guides
2. Check `config/` for configuration options
3. Examine `database/` for database setup

This structure provides a solid foundation for the SwarmDirector project, supporting both current functionality and future growth while maintaining clarity and organization.
