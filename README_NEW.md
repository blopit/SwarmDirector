# SwarmDirector - Hierarchical AI Agent Management System

**A comprehensive, three-tier AI-agent framework for task orchestration and high-accuracy content delivery.**

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Flask](https://img.shields.io/badge/flask-2.3.3-green.svg)](https://flask.palletsprojects.com/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🎯 Overview

SwarmDirector is a hierarchical AI agent management system that enables sophisticated task orchestration through a three-tier architecture. The system routes user requests through specialized departments, ensuring high-accuracy content delivery and efficient task execution.

## ✨ Key Features

- **🎭 Director Agent**: Intelligent routing of user requests to specialized departments
- **💬 Communications Department**: Parallel DraftReviewAgents for consensus-driven content creation
- **📧 Email Agent**: SMTP integration via Flask-Mail for message delivery
- **🔄 Streaming Interface**: Low-latency interactions with Microsoft AutoGen
- **📊 Web Dashboard**: Real-time monitoring and management interface
- **🗄️ Database Integration**: SQLite for development, PostgreSQL-ready for production
- **🧪 Comprehensive Testing**: Full test suite with organized test structure

## 🏗️ Project Structure

```
SwarmDirector/
├── src/                          # Source code
│   └── swarm_director/          # Main application package
│       ├── agents/              # AI agent implementations
│       ├── models/              # Database models
│       ├── utils/               # Utility functions
│       └── web/                 # Web interface components
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── examples/                    # Demo applications
├── docs/                        # Documentation
├── database/                    # Database files and schemas
├── config/                      # Configuration files
└── logs/                        # Application logs
```

For detailed project structure documentation, see [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md).

## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- pip package manager
- Virtual environment (recommended)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/blopit/SwarmDirector.git
   cd SwarmDirector
   ```

2. **Set up virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Initialize the database**
   ```bash
   python -m flask db upgrade
   ```

5. **Run the application**
   ```bash
   python src/swarm_director/app.py
   ```

6. **Access the dashboard**
   - Web Interface: http://localhost:5000/dashboard
   - API Health Check: http://localhost:5000/health
   - Demo Interface: http://localhost:5000/demo

## 📚 Documentation

- **[Project Structure](docs/PROJECT_STRUCTURE.md)** - Detailed project organization
- **[API Documentation](docs/api/)** - REST API reference
- **[Architecture Guide](docs/architecture/)** - System design and components
- **[Deployment Guide](docs/deployment/)** - Production deployment instructions
- **[Development Guide](docs/development/)** - Contributing and development setup

## 🧪 Testing

Run the test suite:
```bash
# Run all tests
pytest tests/

# Run specific test categories
pytest tests/test_agents/
pytest tests/test_models/
pytest tests/test_api/

# Run with coverage
pytest --cov=src/swarm_director tests/
```

## 🛠️ Tech Stack

- **Backend**: Python 3.8+, Flask 2.3.3, SQLAlchemy 2.0+
- **AI Framework**: Microsoft AutoGen
- **Database**: SQLite (development), PostgreSQL (production)
- **Frontend**: Bootstrap 5, JavaScript
- **Testing**: pytest, coverage
- **Migration**: Flask-Migrate (Alembic)

## 🔄 Development Workflow

1. **Task Submission**: Users submit tasks via REST API or web interface
2. **Director Routing**: DirectorAgent analyzes and routes tasks to appropriate departments
3. **Department Processing**: Specialized agents process tasks with parallel review
4. **Result Delivery**: Processed results are delivered through configured channels
5. **Monitoring**: Real-time tracking via web dashboard and logging

## 🎯 Roadmap

### Current Version (v1.0)
- ✅ Core three-tier architecture
- ✅ Basic web dashboard
- ✅ SQLite database integration
- ✅ Email agent functionality

### Upcoming Features
- 🔄 LLM-based intent classification
- 🔄 Additional departments (Research, Planning, Vision)
- 🔄 PostgreSQL and Redis integration
- 🔄 Advanced monitoring and analytics
- 🔄 Docker containerization
- 🔄 API rate limiting and authentication

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guide](docs/CONTRIBUTING.md) for details on:
- Code style and standards
- Development setup
- Testing requirements
- Pull request process

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Documentation**: Check the [docs/](docs/) directory
- **Issues**: Report bugs via [GitHub Issues](https://github.com/blopit/SwarmDirector/issues)
- **Discussions**: Join conversations in [GitHub Discussions](https://github.com/blopit/SwarmDirector/discussions)

---

> **SwarmDirector** validates the core Director → Department → Tool workflow and provides the foundation for a fully extensible, hierarchical AI-agent ecosystem.
