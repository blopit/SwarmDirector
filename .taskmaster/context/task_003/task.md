---
task_id: task_003
subtask_id: null
title: Develop DirectorAgent and Task Router
status: pending
priority: high
parent_task: null
dependencies: [task_001, task_002]
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Implement the DirectorAgent with routing logic to dispatch tasks to appropriate department agents based on intent classification. This creates the central orchestration system for the SwarmDirector multi-agent architecture.

## 📋 Metadata
- **ID**: task_003
- **Title**: Develop DirectorAgent and Task Router
- **Status**: pending
- **Priority**: high
- **Parent Task**: null
- **Dependencies**: [task_001, task_002]
- **Created**: 2025-06-10
- **Updated**: 2025-06-10

## 🏗️ Repository Reorganization Context

**Note**: This task context has been updated to reflect the comprehensive repository reorganization completed on 2025-06-11.

### Key Changes:
- **Source code** moved to `src/swarm_director/` package structure
- **Tests** organized in dedicated `tests/` directory
- **Documentation** structured in `docs/` with comprehensive guides
- **Database files** organized in `database/` directory
- **Utility scripts** moved to `scripts/` directory
- **Examples** placed in `examples/` directory

### New Project Benefits:
- ✅ Professional Python package structure
- ✅ Comprehensive documentation (15+ guides)
- ✅ Improved developer experience with setup tools
- ✅ Clear separation of concerns
- ✅ Industry-standard organization

### Updated References:
All file paths and import statements in this context have been updated to reflect the new structure. See `docs/PROJECT_STRUCTURE.md` for complete details.

---

## 🗒️ Scope, Assumptions & Constraints

### In Scope:
- DirectorAgent class implementation in agents/director.py
- Keyword-based intent classifier for task routing
- LLM-based routing as alternative classification method
- Flask route at /task accepting JSON payloads
- Request validation for type and args fields
- Task logging to SQLite database using models from task_002
- Routing logic to dispatch to department agents
- Error handling and response formatting
- Task status tracking and monitoring
- Utility functions for common director operations

### Out of Scope:
- Specific department agent implementations (covered in tasks 5-7)
- AutoGen integration details (covered in task_004)
- Email sending functionality (covered in task_007)
- Advanced machine learning models for intent classification

### Assumptions:
- Flask application and database models are established (tasks 001-002 completed)
- SQLAlchemy models for Task and AgentLog are available
- Basic Flask routing and JSON handling capabilities exist
- Department agents will be implemented in subsequent tasks

### Constraints:
- Must use existing database models from task_002
- Must integrate with Flask application from task_001
- Must provide both keyword and LLM-based classification options
- Must maintain comprehensive logging for all routing decisions
- Must handle errors gracefully and provide meaningful responses

---

## 🔍 1. Detailed Description

This task implements the central DirectorAgent that serves as the orchestration hub for the SwarmDirector system, routing incoming tasks to appropriate specialist agents based on intelligent intent classification.

### Technical Requirements:
- **DirectorAgent Class**: Core agent class with hierarchical control and decision-making
- **Intent Classification**: Dual-layer system (keyword + LLM) for accurate intent determination
- **Task Routing**: Decision tree mapping intents to specialist agent capabilities
- **API Endpoints**: RESTful /task endpoint for external task submission
- **Database Integration**: Task logging and status tracking using SQLAlchemy models
- **Error Handling**: Comprehensive error management with meaningful responses
- **Performance Monitoring**: Tracking and optimization of routing decisions

### Functional Requirements:
- **Task Reception**: Accept and validate incoming task requests via HTTP API
- **Intent Analysis**: Classify user requests to determine appropriate handling approach
- **Agent Dispatch**: Route tasks to specialist agents based on classification results
- **Status Tracking**: Monitor task progress and update database records
- **Response Management**: Format and return appropriate responses to clients
- **Logging**: Comprehensive activity logging for debugging and monitoring

### Implementation Components:
1. **DirectorAgent Core**: Base agent class with supervisor capabilities and decision-making cycle
2. **Intent Classification System**: Keyword-based and LLM-based classification with confidence scoring
3. **Routing Logic**: Decision tree and agent communication protocols
4. **API Integration**: HTTP endpoints with authentication and serialization
5. **Database Integration**: Task and log management using existing models
6. **Monitoring System**: Performance tracking and health monitoring

## 📁 2. Reference Artifacts & Files

### Primary Implementation Files:
```
SwarmDirector/
├── src/                          # Source code
│   └── swarm_director/          # Main application package
│       ├── __init__.py          # Package initialization
│       ├── app.py               # Flask application
│       ├── config.py            # Configuration
│       ├── agents/              # AI agent implementations
│       ├── models/              # Database models
│       ├── utils/               # Utility functions
│       └── web/                 # Web interface
│           ├── static/          # Static assets
│           └── templates/       # Jinja2 templates
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── examples/                    # Demo applications
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── architecture/            # System architecture
│   ├── deployment/              # Deployment guides
│   └── development/             # Development guides
├── database/                    # Database files and schemas
│   ├── schemas/                 # Schema definitions
│   ├── migrations/              # Alembic migrations
│   └── data/                    # Database files
├── reports/                     # Generated reports
└── logs/                        # Application logs
```

### Configuration Files:
- **src/swarm_director/config.py**: Application configuration classes
- **.env**: Environment variables (create from template)
- **requirements.txt**: Python dependencies
- **run.py**: Application launcher script

### Key Documentation:
- **README.md**: Project overview and quick start
- **docs/PROJECT_STRUCTURE.md**: Detailed project organization
- **docs/api/README.md**: API documentation
- **docs/architecture/overview.md**: System architecture
- **docs/development/getting_started.md**: Developer guide
- **QUICKSTART.md**: 1-minute setup guide
### Configuration Files:
- **src/swarm_director/src/swarm_director/config.py**: Application configuration
- **.env**: Environment variables
- **requirements.txt**: Python dependencies

### Related Task Files:
- **Source Task**: `.taskmaster/tasks/task_003.txt`
- **Context File**: `.taskmaster/context/task_003/task.md`

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 DirectorAgent Core Implementation
```python
# src/swarm_director/agents/director.py
from src.swarm_director.app import db
from src.swarm_director.models.task import Task, TaskType, TaskStatus
from src.swarm_director.models.agent_log import AgentLog, LogLevel
from datetime import datetime
import json
import re

class DirectorAgent:
    """Central orchestration agent for task routing and management."""

    def __init__(self):
        self.agent_type = "director"
        self.intent_keywords = {
            'email_draft': ['email', 'draft', 'compose', 'write', 'send'],
            'document_review': ['review', 'check', 'analyze', 'feedback'],
            'communication': ['communicate', 'message', 'contact', 'reach'],
            'analysis': ['analyze', 'study', 'examine', 'investigate']
        }

    def process_task(self, task_data):
        """Main entry point for task processing."""
        try:
            # Validate input
            if not self._validate_task_data(task_data):
                return self._error_response("Invalid task data")

            # Classify intent
            intent = self._classify_intent(task_data.get('description', ''))

            # Create task record
            task = self._create_task_record(task_data, intent)

            # Route to appropriate agent
            result = self._route_task(task, intent)

            # Log the operation
            self._log_operation(task.id, f"Task routed to {intent} handler", LogLevel.INFO)

            return self._success_response(task.id, result)

        except Exception as e:
            self._log_operation(None, f"Error processing task: {str(e)}", LogLevel.ERROR)
            return self._error_response(f"Processing failed: {str(e)}")

    def _validate_task_data(self, task_data):
        """Validate incoming task data."""
        required_fields = ['type', 'description']
        return all(field in task_data for field in required_fields)

    def _classify_intent(self, description):
        """Classify task intent using keyword matching."""
        description_lower = description.lower()

        # Score each intent category
        scores = {}
        for intent, keywords in self.intent_keywords.items():
            score = sum(1 for keyword in keywords if keyword in description_lower)
            if score > 0:
                scores[intent] = score

        # Return highest scoring intent or default
        if scores:
            return max(scores, key=scores.get)
        return 'analysis'  # Default intent

    def _create_task_record(self, task_data, intent):
        """Create database record for the task."""
        task = Task(
            type=TaskType(intent),
            title=task_data.get('title', 'Untitled Task'),
            description=task_data.get('description', ''),
            user_id=task_data.get('user_id'),
            status=TaskStatus.PENDING,
            priority=task_data.get('priority', 'medium')
        )

        db.session.add(task)
        db.session.commit()
        return task

    def _route_task(self, task, intent):
        """Route task to appropriate specialist agent."""
        routing_map = {
            'email_draft': 'CommunicationsDept',
            'document_review': 'DraftReviewAgent',
            'communication': 'CommunicationsDept',
            'analysis': 'AnalysisAgent'
        }

        target_agent = routing_map.get(intent, 'AnalysisAgent')

        # Update task status
        task.status = TaskStatus.IN_PROGRESS
        db.session.commit()

        # For now, return routing information
        # In future tasks, this will actually dispatch to agents
        return {
            'routed_to': target_agent,
            'intent': intent,
            'task_id': task.id
        }

    def _log_operation(self, task_id, message, level):
        """Log agent operation to database."""
        log_entry = AgentLog(
            task_id=task_id,
            agent_type=self.agent_type,
            message=message,
            log_level=level
        )
        db.session.add(log_entry)
        db.session.commit()

    def _success_response(self, task_id, result):
        """Format successful response."""
        return {
            'status': 'success',
            'task_id': task_id,
            'result': result,
            'timestamp': datetime.utcnow().isoformat()
        }

    def _error_response(self, error_message):
        """Format error response."""
        return {
            'status': 'error',
            'error': error_message,
            'timestamp': datetime.utcnow().isoformat()
        }
```

### 3.2 Flask API Endpoint Implementation
```python
# src/swarm_director/web/routes.py (addition to existing routes)
from flask import Blueprint, request, jsonify
from src.swarm_director.agents.director import DirectorAgent

main = Blueprint('main', __name__)
director = DirectorAgent()

@main.route('/task', methods=['POST'])
def submit_task():
    """API endpoint for task submission."""
    try:
        # Validate JSON payload
        if not request.is_json:
            return jsonify({'error': 'Content-Type must be application/json'}), 400

        task_data = request.get_json()

        # Validate required fields
        if not task_data or 'type' not in task_data:
            return jsonify({'error': 'Missing required field: type'}), 400

        # Process task through DirectorAgent
        result = director.process_task(task_data)

        # Return appropriate HTTP status
        if result['status'] == 'success':
            return jsonify(result), 200
        else:
            return jsonify(result), 400

    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': f'Internal server error: {str(e)}'
        }), 500

@main.route('/task/<int:task_id>/status', methods=['GET'])
def get_task_status(task_id):
    """Get status of a specific task."""
    try:
        task = Task.query.get_or_404(task_id)
        return jsonify({
            'task_id': task_id,
            'status': task.status.value,
            'type': task.type.value,
            'created_at': task.created_at.isoformat(),
            'updated_at': task.updated_at.isoformat()
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
```

## 📦 4. Dependencies

### 4.1 Core Dependencies
```txt
# Exact versions for reproducibility
Flask==2.3.3
SQLAlchemy==2.0.23
python-dotenv==1.0.0
```

---

## 🛠️ 5. Implementation Plan

### Step 1: Environment Setup
```bash
# Activate virtual environment
source venv/bin/activate
# Install dependencies
pip install -r requirements.txt
```

### Step 2: Core Implementation
1. **Create main module**: Implement core functionality
2. **Add configuration**: Set up configuration management
3. **Implement tests**: Create comprehensive test suite

---

## 🧪 6. Testing & QA

### 6.1 Unit Tests
```python
def test_main_functionality():
    """Test main functionality."""
    # Test implementation
    assert result == expected
```

---

## 🔗 7. Integration & Related Tasks

### 7.1 Dependencies
- **Prerequisite tasks**: List of required completed tasks

### 7.2 Integration Points
- **System integration**: Description of integration requirements

---

## ⚠️ 8. Risks & Mitigations

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| Technical complexity | High | Medium | Detailed planning and testing |
| Integration issues | Medium | Low | Comprehensive integration testing |

---

## ✅ 9. Success Criteria

### 9.1 Functional Requirements
- [ ] All specified functionality implemented and tested
- [ ] Integration with existing systems verified
- [ ] Performance requirements met

### 9.2 Quality Requirements
- [ ] Code coverage above 80%
- [ ] All tests passing
- [ ] Code review completed

---

## 🚀 10. Next Steps

### 10.1 Immediate Actions
1. **Complete implementation**: Follow the implementation plan
2. **Run tests**: Execute comprehensive test suite
3. **Verify integration**: Test integration with dependent systems

### 10.2 Follow-up Tasks
1. **Documentation**: Update project documentation
2. **Deployment**: Prepare for deployment if applicable
3. **Monitoring**: Set up monitoring and alerting

