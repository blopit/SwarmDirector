---
task_id: task_003
subtask_id: null
title: Develop DirectorAgent and Task Router
status: pending
priority: high
parent_task: null
dependencies: ['task_001', 'task_002']
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Implement the DirectorAgent with routing logic to dispatch tasks to appropriate department agents based on intent classification.

## 📋 Metadata
- **ID**: task_003
- **Title**: Develop DirectorAgent and Task Router
- **Status**: pending
- **Priority**: high
- **Parent Task**: null
- **Dependencies**: ['task_001', 'task_002']
- **Subtasks**: 4
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints

### In Scope:
- **DirectorAgent Implementation**: Complete AutoGen-based agent with routing capabilities
- **Intent Classification System**: Dual-layer classification (keyword + LLM fallback)
- **Task Routing Logic**: Decision tree for dispatching to appropriate department agents
- **API Integration**: Flask endpoints for task submission and status tracking
- **Database Integration**: Task logging, status tracking, and conversation history
- **Error Handling**: Comprehensive error management and recovery mechanisms
- **Performance Monitoring**: Basic metrics collection and logging
- **Testing Framework**: Unit tests, integration tests, and performance benchmarks

### Out of Scope:
- **Advanced ML Models**: Complex machine learning models beyond basic classification
- **Real-time Streaming**: WebSocket or SSE implementations (handled in task_010)
- **Authentication/Authorization**: User management and security (future enhancement)
- **Advanced Analytics**: Detailed performance analytics and reporting
- **Multi-tenant Support**: Support for multiple organizations or users
- **External API Integrations**: Third-party service integrations beyond AutoGen

### Assumptions:
- **Dependencies Completed**: task_001 (Flask setup) and task_002 (database models) are complete
- **AutoGen Framework**: Microsoft AutoGen 0.2.0+ is available and functional
- **Database Access**: SQLite database is accessible and properly configured
- **Python Environment**: Python 3.8+ with all required packages installed
- **Development Environment**: Local development setup with proper permissions
- **API Keys**: OpenAI/Anthropic API keys available for LLM-based classification

### Constraints:
- **Framework Compatibility**: Must work with AutoGen 0.2.0+ framework
- **Database Technology**: Must use SQLite for prototype (PostgreSQL for production)
- **Response Time**: Task routing must complete within 5 seconds
- **Memory Usage**: Agent instances must use less than 100MB each
- **Concurrent Requests**: Must handle at least 10 concurrent task submissions
- **Error Recovery**: System must gracefully handle and recover from failures
- **Logging Requirements**: All operations must be logged for debugging and monitoring

---

## 🔍 1. Detailed Description
1. Create DirectorAgent class in agents/director.py
2. Implement keyword-based intent classifier for routing tasks
3. Add LLM-based routing as an alternative classification method
4. Create Flask route at /task that accepts JSON payloads
5. Implement request validation for type and args fields
6. Add task logging to SQLite database
7. Create routing logic to dispatch to department agents
8. Implement error handling and response formatting
9. Add support for task status tracking
10. Create utility functions for common director operations

## 📁 2. Reference Artifacts & Files

### Primary Implementation Files:
```
agents/
├── __init__.py
├── director.py              # Main DirectorAgent class
├── base_agent.py           # Base agent functionality
└── agent_registry.py       # Agent registration and discovery

utils/
├── __init__.py
├── intent_classifier.py    # Intent classification system
├── routing_logic.py        # Task routing decision engine
├── conversation_manager.py # Conversation history management
└── performance_monitor.py  # Performance metrics collection

routes/
├── __init__.py
├── task_router.py          # Flask API endpoints
└── agent_status.py         # Agent status endpoints

models/
├── __init__.py
├── task.py                 # Task model
├── conversation.py         # Conversation history model
└── agent_status.py         # Agent status tracking model

config/
├── __init__.py
├── director_config.py      # Director agent configuration
└── routing_config.py       # Routing rules configuration

tests/
├── __init__.py
├── test_director_agent.py  # Director agent tests
├── test_intent_classifier.py # Classification tests
├── test_routing_logic.py   # Routing tests
├── test_api_endpoints.py   # API endpoint tests
└── fixtures/               # Test data and mocks
    ├── sample_tasks.py
    ├── mock_agents.py
    └── test_conversations.py
```

### Configuration Files:
- **config/director_config.py**: DirectorAgent configuration settings
- **config/routing_config.py**: Intent classification and routing rules
- **.env**: Environment variables for API keys and settings

### Database Models:
- **models/task.py**: Task submission and tracking
- **models/conversation.py**: Agent conversation history
- **models/agent_status.py**: Agent availability and performance

### Documentation Files:
- **docs/director_agent_api.md**: API documentation
- **docs/intent_classification.md**: Classification system documentation
- **docs/routing_logic.md**: Routing decision documentation

### Related Task Files:
- **Source Task**: `.taskmaster/tasks/task_003.txt`
- **Parent Context**: `.taskmaster/context/task_003/task.md`
- **Dependency**: `.taskmaster/context/task_001/task.md` (Flask setup)
- **Dependency**: `.taskmaster/context/task_002/task.md` (Database models)

---

## 🔧 3. Interfaces & Code Snippets
### 3.1 DirectorAgent Class
```python
class DirectorAgent:
    def __init__(self, db_session, logger):
        self.db = db_session
        self.logger = logger
        self.intent_classifier = IntentClassifier()

    def route_task(self, task_data):
        intent = self.intent_classifier.classify(task_data)
        return self.dispatch_to_agent(intent, task_data)
```

### 3.2 Intent Classification
```python
class IntentClassifier:
    def classify(self, task_data):
        # Keyword-based classification first
        intent = self.keyword_classify(task_data)
        if intent.confidence < 0.8:
            # Fall back to LLM classification
            intent = self.llm_classify(task_data)
        return intent
```

---

## 🔌 4. API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/task` | Submit task for routing |
| GET | `/task/:id/status` | Get task status |
| GET | `/agents/status` | Get agent availability |

---

## 📦 5. Dependencies

### 5.1 Core Framework Dependencies
```txt
# AutoGen framework (primary dependency)
pyautogen==0.2.0

# Flask web framework
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5

# Database
SQLAlchemy==2.0.23
alembic==1.12.1

# AI/ML libraries
openai==1.3.0
anthropic==0.7.0
scikit-learn==1.3.2
numpy==1.24.3
pandas==2.0.3

# Text processing and classification
nltk==3.8.1
spacy==3.7.2
transformers==4.35.2
torch==2.1.1

# Utilities
python-dotenv==1.0.0
requests==2.31.0
python-dateutil==2.8.2
pydantic==2.5.0
```

### 5.2 Development and Testing Dependencies
```txt
# Testing framework
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
pytest-mock==3.12.0
pytest-asyncio==0.21.1

# Code quality
black==23.9.1
flake8==6.1.0
mypy==1.7.1
isort==5.12.0

# Performance testing
locust==2.17.0
memory-profiler==0.61.0
```

### 5.3 System Requirements
- **Python Version**: 3.8+ (recommended 3.10+)
- **Memory**: Minimum 2GB RAM (4GB recommended)
- **Disk Space**: 1GB for dependencies and models
- **Network**: Internet access for AI API calls
- **Operating System**: Linux, macOS, or Windows

### 5.4 External Service Dependencies
- **OpenAI API**: For LLM-based intent classification (optional)
- **Anthropic API**: Alternative LLM provider (optional)
- **Local LLM**: Ollama or similar for offline operation (optional)

### 5.5 Installation Commands
```bash
# Install core dependencies
pip install pyautogen==0.2.0 Flask==2.3.3 SQLAlchemy==2.0.23

# Install ML dependencies
pip install scikit-learn==1.3.2 numpy==1.24.3 pandas==2.0.3

# Install NLP dependencies
pip install nltk==3.8.1 spacy==3.7.2
python -m spacy download en_core_web_sm

# Install AI API clients
pip install openai==1.3.0 anthropic==0.7.0

# Install development tools
pip install pytest==7.4.3 black==23.9.1 flake8==6.1.0
```

### 5.6 Dependency Verification Script
```python
#!/usr/bin/env python3
"""Verify all dependencies for DirectorAgent implementation."""

import sys
import importlib.util

def check_dependency(package_name, min_version=None):
    """Check if a package is installed and optionally verify version."""
    try:
        spec = importlib.util.find_spec(package_name)
        if spec is None:
            return False, f"{package_name} not found"

        module = importlib.import_module(package_name)
        version = getattr(module, '__version__', 'unknown')

        if min_version and version != 'unknown':
            # Simple version comparison (works for most cases)
            if version < min_version:
                return False, f"{package_name} {version} < {min_version}"

        return True, f"{package_name} {version}"
    except ImportError as e:
        return False, f"{package_name} import error: {e}"

def main():
    """Check all required dependencies."""
    dependencies = [
        ('autogen', '0.2.0'),
        ('flask', '2.3.0'),
        ('sqlalchemy', '2.0.0'),
        ('sklearn', '1.3.0'),
        ('numpy', '1.24.0'),
        ('openai', '1.0.0'),
        ('anthropic', '0.7.0'),
        ('nltk', '3.8.0'),
        ('pytest', '7.4.0'),
    ]

    print("DirectorAgent Dependency Check")
    print("=" * 40)

    all_good = True
    for package, min_version in dependencies:
        success, message = check_dependency(package, min_version)
        status = "✓" if success else "✗"
        print(f"{status} {message}")
        if not success:
            all_good = False

    print("=" * 40)
    if all_good:
        print("✓ All dependencies satisfied")
        return 0
    else:
        print("✗ Some dependencies missing or outdated")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

---

## 🛠️ 6. Implementation Plan
1. **Core Agent Setup**: Implement DirectorAgent base class with initialization
2. **Intent Classification**: Build dual-layer classification system (keyword + LLM)
3. **Routing Logic**: Create decision tree for agent dispatch
4. **API Integration**: Implement Flask routes with validation
5. **Database Integration**: Add task logging and status tracking
6. **Error Handling**: Implement comprehensive error management
7. **Testing Framework**: Create unit and integration tests
8. **Performance Optimization**: Add monitoring and benchmarking

---

## 🧪 7. Testing & QA
1. Unit test intent classifier with various input types
2. Test routing logic with mock department agents
3. Verify correct HTTP responses for valid and invalid requests
4. Validate database logging of tasks
5. Test error handling for edge cases
6. Benchmark routing performance under load

---

## 🔗 8. Integration & Related Tasks
- **Dependencies**: ['task_001', 'task_002']
- **Subtasks**: ['subtask_001', 'subtask_002', 'subtask_003', 'subtask_004']

---

## ⚠️ 9. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Intent classification accuracy issues | Implement confidence scoring and fallback mechanisms |
| Agent routing failures | Create robust error handling and retry logic |
| Performance bottlenecks under load | Implement async processing and connection pooling |
| Integration complexity with AutoGen | Use well-defined interfaces and comprehensive testing |

---

## ✅ 10. Success Criteria
- [ ] DirectorAgent routes tasks correctly (>95% accuracy)
- [ ] Intent classification confidence scoring works
- [ ] API endpoints handle 10+ concurrent requests
- [ ] Database logging captures all task activities
- [ ] Error handling prevents system crashes
- [ ] Integration with AutoGen framework complete
- [ ] Performance benchmarks meet requirements

---

## 🚀 11. Next Steps
1. Complete all subtasks in dependency order
2. Perform integration testing
3. Update documentation and examples
