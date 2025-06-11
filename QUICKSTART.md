# SwarmDirector Quick Start Guide

Get SwarmDirector up and running in minutes with this quick start guide.

## 🚀 1-Minute Setup

### Prerequisites
- Python 3.8+ installed
- Git installed

### Quick Installation

```bash
# Clone the repository
git clone https://github.com/blopit/SwarmDirector.git
cd SwarmDirector

# Set up virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run the application
python run.py
```

That's it! SwarmDirector is now running at http://localhost:5000

## 🎯 What You Can Do Now

### 1. **Explore the Dashboard**
Visit http://localhost:5000/dashboard to see:
- Agent management interface
- Task monitoring
- System status

### 2. **Try the Demo**
Visit http://localhost:5000/demo for:
- Interactive demonstrations
- Sample workflows
- Real-time system status

### 3. **Test the API**
```bash
# Check system health
curl http://localhost:5000/health

# List agents
curl http://localhost:5000/api/agents

# Submit a task
curl -X POST http://localhost:5000/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "title": "Test Task",
    "description": "A test task for the system"
  }'
```

## 📚 Next Steps

### For Users
1. **Read the Documentation**: Check `docs/` for comprehensive guides
2. **Explore Examples**: Run `python examples/demo_app.py`
3. **API Reference**: See `docs/api/` for detailed API documentation

### For Developers
1. **Development Setup**: Run `python scripts/setup_development.py`
2. **Contributing Guide**: Read `docs/CONTRIBUTING.md`
3. **Architecture Overview**: See `docs/architecture/overview.md`

### For System Administrators
1. **Deployment Guide**: Check `docs/deployment/`
2. **Configuration**: Review `src/swarm_director/config.py`
3. **Database Setup**: See `database/` directory

## 🔧 Common Commands

```bash
# Run the application
python run.py

# Set up development environment
python scripts/setup_development.py

# Verify installation
python scripts/verify_reorganization.py

# Run tests
pytest tests/

# Access the demo
python examples/demo_app.py
```

## 🆘 Troubleshooting

### Port Already in Use
```bash
# Use a different port
FLASK_PORT=5001 python run.py
```

### Import Errors
```bash
# Make sure you're in the virtual environment
source venv/bin/activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Issues
```bash
# Reset the database
python -c "from src.swarm_director.app import create_app; from src.swarm_director.models.base import db; app = create_app(); app.app_context().push(); db.create_all()"
```

## 📖 Key Documentation

- **[README.md](README.md)** - Project overview and features
- **[PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md)** - Detailed project organization
- **[API Documentation](docs/api/README.md)** - REST API reference
- **[Contributing Guide](docs/CONTRIBUTING.md)** - How to contribute
- **[Architecture Overview](docs/architecture/overview.md)** - System design

## 🎉 You're Ready!

SwarmDirector is now set up and ready to use. The system provides:

- **Hierarchical AI agent management**
- **Task orchestration and routing**
- **Web dashboard for monitoring**
- **REST API for integration**
- **Comprehensive documentation**

Explore the features, try the examples, and start building with SwarmDirector!

---

**Need Help?** Check the documentation in `docs/` or visit the project repository for support.
