---
task_id: task_008
subtask_id: null
title: Implement Task API Endpoint
status: pending
priority: high
parent_task: null
dependencies: ['task_003']
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Create the RESTful API endpoint for task submission that accepts JSON payloads and returns standardized responses.

## 📋 Metadata
- **ID**: task_008
- **Title**: Implement Task API Endpoint
- **Status**: pending
- **Priority**: high
- **Parent Task**: null
- **Dependencies**: ['task_003']
- **Subtasks**: 3
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints
- **In Scope**: Complete RESTful API endpoint implementation with JSON schema validation, standardized responses, comprehensive error handling, rate limiting, and production-ready features
- **Out of Scope**: Authentication/authorization, task execution logic, WebSocket support, GraphQL endpoints, admin interfaces
- **Assumptions**: Python 3.8+, Flask application framework, basic REST API knowledge, JSON schema understanding, HTTP status code familiarity
- **Constraints**: Must handle 100+ concurrent requests, response time <500ms, follow OpenAPI 3.0 specification, maintain backward compatibility

---

## 🔍 1. Detailed Description

The Task API Endpoint is the primary interface for external systems and users to submit tasks to the SwarmDirector system. It provides a robust, production-ready RESTful API with comprehensive validation, error handling, and monitoring capabilities. The endpoint accepts JSON payloads, validates them against defined schemas, and returns standardized responses with appropriate HTTP status codes.

### Key Features:
- **RESTful Design**: Follows REST principles and HTTP standards
- **JSON Schema Validation**: Comprehensive input validation with detailed error messages
- **Standardized Responses**: Consistent response format across all endpoints
- **Error Handling**: Graceful error handling with informative error messages
- **Rate Limiting**: Protection against abuse and DoS attacks
- **Request Logging**: Comprehensive logging for debugging and monitoring
- **Performance Optimization**: Optimized for high-throughput scenarios

## 📁 2. Reference Artifacts & Files

### Project Structure
```
routes/
├── __init__.py
├── task_api.py              # Main task API endpoint
├── middleware.py            # Request validation middleware
└── response_formatter.py    # Response formatting utilities

schemas/
├── __init__.py
├── task_schema.py          # JSON schemas for task validation
└── response_schema.py      # Response format schemas

utils/
├── validation.py           # Validation utilities
├── rate_limiter.py        # Rate limiting implementation
├── task_id_generator.py   # Unique task ID generation
└── error_handler.py       # Error handling utilities

models/
├── task_request.py        # Task request data model
└── api_log.py            # API request logging model

tests/
├── test_task_api.py       # API endpoint tests
├── test_validation.py     # Validation tests
└── fixtures/              # Test data
    ├── valid_requests.json
    └── invalid_requests.json
```

### Required Files
- **routes/task_api.py**: Main API endpoint implementation
- **schemas/task_schema.py**: JSON schema definitions
- **utils/validation.py**: Request validation logic
- **utils/rate_limiter.py**: Rate limiting implementation
- **tests/test_task_api.py**: Comprehensive test suite

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 Main Task API Endpoint (routes/task_api.py)
```python
from flask import Blueprint, request, jsonify, g
from datetime import datetime
import uuid
import logging
from functools import wraps
from schemas.task_schema import TaskRequestSchema, validate_task_request
from utils.validation import ValidationError
from utils.rate_limiter import RateLimiter
from utils.task_id_generator import generate_task_id
from utils.error_handler import APIError, handle_api_error
from models.api_log import APILog
from models.task_request import TaskRequest

# Create blueprint for task API
task_api_bp = Blueprint('task_api', __name__, url_prefix='/api/v1')

# Initialize rate limiter
rate_limiter = RateLimiter(max_requests=100, window_seconds=3600)  # 100 requests per hour

# Set up logging
logger = logging.getLogger(__name__)

def require_json(f):
    """Decorator to ensure request contains valid JSON."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not request.is_json:
            raise APIError("Content-Type must be application/json", 400)

        try:
            request.get_json(force=True)
        except Exception:
            raise APIError("Invalid JSON in request body", 400)

        return f(*args, **kwargs)
    return decorated_function

def rate_limit(f):
    """Decorator to apply rate limiting."""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        client_ip = request.environ.get('HTTP_X_FORWARDED_FOR', request.remote_addr)

        if not rate_limiter.allow_request(client_ip):
            raise APIError("Rate limit exceeded. Try again later.", 429)

        return f(*args, **kwargs)
    return decorated_function

@task_api_bp.route('/task', methods=['POST'])
@require_json
@rate_limit
def submit_task():
    """
    Submit a new task for processing.

    Expected JSON payload:
    {
        "type": "email_draft|data_analysis|report_generation",
        "args": {
            "recipient": "user@example.com",
            "subject": "Task subject",
            "content": "Task content or parameters"
        },
        "priority": "low|medium|high|urgent",
        "metadata": {
            "user_id": "optional_user_identifier",
            "source": "web|api|mobile",
            "tags": ["tag1", "tag2"]
        }
    }

    Returns:
    {
        "task_id": "unique_task_identifier",
        "status": "accepted|rejected",
        "message": "descriptive_message",
        "timestamp": "ISO_8601_timestamp",
        "estimated_completion": "ISO_8601_timestamp"
    }
    """
    try:
        # Generate unique task ID
        task_id = generate_task_id()

        # Get request data
        request_data = request.get_json()

        # Log incoming request
        log_request(task_id, request_data, request.remote_addr)

        # Validate request against schema
        validation_result = validate_task_request(request_data)
        if not validation_result.valid:
            return create_error_response(
                task_id=task_id,
                message="Request validation failed",
                errors=validation_result.errors,
                status_code=400
            )

        # Create task request object
        task_request = TaskRequest(
            task_id=task_id,
            task_type=request_data['type'],
            args=request_data['args'],
            priority=request_data.get('priority', 'medium'),
            metadata=request_data.get('metadata', {}),
            submitted_at=datetime.utcnow()
        )

        # Process task (integrate with DirectorAgent)
        processing_result = process_task_request(task_request)

        # Create success response
        response = create_success_response(
            task_id=task_id,
            status=processing_result['status'],
            message=processing_result['message'],
            estimated_completion=processing_result.get('estimated_completion')
        )

        # Log successful processing
        logger.info(f"Task {task_id} submitted successfully")

        return response, 201

    except APIError as e:
        return handle_api_error(e, task_id)
    except Exception as e:
        logger.error(f"Unexpected error processing task {task_id}: {str(e)}")
        return create_error_response(
            task_id=task_id,
            message="Internal server error",
            status_code=500
        )

@task_api_bp.route('/task/<task_id>', methods=['GET'])
def get_task_status(task_id):
    """
    Get the status of a submitted task.

    Returns:
    {
        "task_id": "task_identifier",
        "status": "pending|processing|completed|failed",
        "progress": 0-100,
        "result": "task_result_if_completed",
        "error": "error_message_if_failed",
        "created_at": "ISO_8601_timestamp",
        "updated_at": "ISO_8601_timestamp"
    }
    """
    try:
        # Validate task ID format
        if not is_valid_task_id(task_id):
            raise APIError("Invalid task ID format", 400)

        # Get task status from database/cache
        task_status = get_task_status_from_storage(task_id)

        if not task_status:
            raise APIError("Task not found", 404)

        return jsonify(task_status), 200

    except APIError as e:
        return handle_api_error(e, task_id)
    except Exception as e:
        logger.error(f"Error retrieving task status {task_id}: {str(e)}")
        return create_error_response(
            task_id=task_id,
            message="Internal server error",
            status_code=500
        )

@task_api_bp.route('/task/<task_id>', methods=['DELETE'])
def cancel_task(task_id):
    """
    Cancel a pending or processing task.

    Returns:
    {
        "task_id": "task_identifier",
        "status": "cancelled",
        "message": "Task cancelled successfully",
        "timestamp": "ISO_8601_timestamp"
    }
    """
    try:
        if not is_valid_task_id(task_id):
            raise APIError("Invalid task ID format", 400)

        # Attempt to cancel task
        cancellation_result = cancel_task_processing(task_id)

        if not cancellation_result['success']:
            raise APIError(cancellation_result['message'], 400)

        return jsonify({
            "task_id": task_id,
            "status": "cancelled",
            "message": "Task cancelled successfully",
            "timestamp": datetime.utcnow().isoformat()
        }), 200

    except APIError as e:
        return handle_api_error(e, task_id)
    except Exception as e:
        logger.error(f"Error cancelling task {task_id}: {str(e)}")
        return create_error_response(
            task_id=task_id,
            message="Internal server error",
            status_code=500
        )

def create_success_response(task_id, status, message, estimated_completion=None):
    """Create standardized success response."""
    response = {
        "task_id": task_id,
        "status": status,
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    if estimated_completion:
        response["estimated_completion"] = estimated_completion

    return jsonify(response)

def create_error_response(task_id, message, errors=None, status_code=400):
    """Create standardized error response."""
    response = {
        "task_id": task_id,
        "status": "error",
        "message": message,
        "timestamp": datetime.utcnow().isoformat()
    }

    if errors:
        response["errors"] = errors

    return jsonify(response), status_code
```

### 3.2 JSON Schema Validation (schemas/task_schema.py)
```python
import jsonschema
from typing import Dict, List, NamedTuple

class ValidationResult(NamedTuple):
    valid: bool
    errors: List[str]

# Task request schema
TASK_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "enum": ["email_draft", "data_analysis", "report_generation", "content_review"],
            "description": "Type of task to be processed"
        },
        "args": {
            "type": "object",
            "description": "Task-specific arguments",
            "minProperties": 1
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "urgent"],
            "default": "medium",
            "description": "Task priority level"
        },
        "metadata": {
            "type": "object",
            "properties": {
                "user_id": {"type": "string"},
                "source": {"type": "string", "enum": ["web", "api", "mobile"]},
                "tags": {"type": "array", "items": {"type": "string"}},
                "timeout": {"type": "integer", "minimum": 1, "maximum": 3600}
            },
            "additionalProperties": True
        }
    },
    "required": ["type", "args"],
    "additionalProperties": False
}

# Task-specific argument schemas
EMAIL_DRAFT_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "recipient": {"type": "string", "format": "email"},
        "subject": {"type": "string", "minLength": 1, "maxLength": 200},
        "content": {"type": "string", "minLength": 1},
        "tone": {"type": "string", "enum": ["formal", "casual", "friendly", "professional"]},
        "length": {"type": "string", "enum": ["short", "medium", "long"]}
    },
    "required": ["recipient", "subject", "content"],
    "additionalProperties": False
}

DATA_ANALYSIS_ARGS_SCHEMA = {
    "type": "object",
    "properties": {
        "data_source": {"type": "string"},
        "analysis_type": {"type": "string", "enum": ["summary", "trend", "correlation", "prediction"]},
        "parameters": {"type": "object"},
        "output_format": {"type": "string", "enum": ["json", "csv", "pdf", "html"]}
    },
    "required": ["data_source", "analysis_type"],
    "additionalProperties": False
}

def validate_task_request(request_data: Dict) -> ValidationResult:
    """
    Validate task request against JSON schema.

    Args:
        request_data: The request data to validate

    Returns:
        ValidationResult with validation status and errors
    """
    try:
        # Validate main schema
        jsonschema.validate(request_data, TASK_REQUEST_SCHEMA)

        # Validate task-specific arguments
        task_type = request_data.get('type')
        args = request_data.get('args', {})

        if task_type == 'email_draft':
            jsonschema.validate(args, EMAIL_DRAFT_ARGS_SCHEMA)
        elif task_type == 'data_analysis':
            jsonschema.validate(args, DATA_ANALYSIS_ARGS_SCHEMA)

        return ValidationResult(valid=True, errors=[])

    except jsonschema.ValidationError as e:
        error_message = f"Validation error at {'.'.join(str(p) for p in e.path)}: {e.message}"
        return ValidationResult(valid=False, errors=[error_message])
    except Exception as e:
        return ValidationResult(valid=False, errors=[f"Validation failed: {str(e)}"])
```

---

## 🔌 4. API Endpoints

### 4.1 Complete API Specification
| Method | Endpoint | Description | Request Body | Response | Status Codes |
|--------|----------|-------------|--------------|----------|--------------|
| POST | `/api/v1/task` | Submit new task | Task JSON | Task ID and status | 201, 400, 429, 500 |
| GET | `/api/v1/task/<id>` | Get task status | None | Task status | 200, 404, 500 |
| DELETE | `/api/v1/task/<id>` | Cancel task | None | Cancellation status | 200, 400, 404, 500 |
| GET | `/api/v1/tasks` | List user tasks | Query params | Task list | 200, 400, 500 |
| GET | `/api/v1/health` | Health check | None | System status | 200, 503 |

### 4.2 OpenAPI 3.0 Specification
```yaml
openapi: 3.0.0
info:
  title: SwarmDirector Task API
  version: 1.0.0
  description: RESTful API for task submission and management

paths:
  /api/v1/task:
    post:
      summary: Submit a new task
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/TaskRequest'
      responses:
        '201':
          description: Task submitted successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/TaskResponse'
        '400':
          description: Invalid request
        '429':
          description: Rate limit exceeded
        '500':
          description: Internal server error

components:
  schemas:
    TaskRequest:
      type: object
      required:
        - type
        - args
      properties:
        type:
          type: string
          enum: [email_draft, data_analysis, report_generation]
        args:
          type: object
        priority:
          type: string
          enum: [low, medium, high, urgent]
          default: medium
        metadata:
          type: object

    TaskResponse:
      type: object
      properties:
        task_id:
          type: string
        status:
          type: string
        message:
          type: string
        timestamp:
          type: string
          format: date-time
```

---

## 📦 5. Dependencies

### 5.1 Required Packages
```txt
# Core Flask framework
Flask==2.3.3
Flask-CORS==4.0.0

# JSON schema validation
jsonschema==4.19.2

# Rate limiting
Flask-Limiter==3.5.0
redis==5.0.1

# Request validation
marshmallow==3.20.1
email-validator==2.1.0

# Database (optional)
SQLAlchemy==2.0.23
Flask-SQLAlchemy==3.0.5

# Utilities
python-dateutil==2.8.2
uuid==1.30

# Testing
pytest==7.4.3
pytest-flask==1.3.0
requests==2.31.0
```

### 5.2 Installation Commands
```bash
# Install core dependencies
pip install Flask==2.3.3 Flask-CORS==4.0.0

# Install validation libraries
pip install jsonschema==4.19.2 marshmallow==3.20.1 email-validator==2.1.0

# Install rate limiting
pip install Flask-Limiter==3.5.0 redis==5.0.1

# Install database support
pip install SQLAlchemy==2.0.23 Flask-SQLAlchemy==3.0.5

# Install development dependencies
pip install pytest==7.4.3 pytest-flask==1.3.0 requests==2.31.0
```

### 5.3 Environment Configuration
```bash
# API Configuration
export API_RATE_LIMIT="100"        # requests per hour
export API_TIMEOUT="30"            # seconds
export API_MAX_PAYLOAD_SIZE="10MB"

# Redis (for rate limiting)
export REDIS_URL="redis://localhost:6379/0"

# Database (optional)
export API_LOG_DATABASE_URL="sqlite:///api_logs.db"

# Security
export API_SECRET_KEY="your-secret-key"
export CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"
```

---

## 🛠️ 6. Implementation Plan

### Step 1: Project Setup
```bash
# Create directory structure
mkdir -p routes schemas utils models tests/fixtures

# Create required files
touch routes/__init__.py routes/task_api.py routes/middleware.py
touch schemas/__init__.py schemas/task_schema.py schemas/response_schema.py
touch utils/validation.py utils/rate_limiter.py utils/task_id_generator.py utils/error_handler.py
touch models/task_request.py models/api_log.py
touch tests/test_task_api.py tests/test_validation.py
```

### Step 2: Core Utilities Implementation
```python
# utils/task_id_generator.py
import uuid
import time
from datetime import datetime

def generate_task_id() -> str:
    """Generate unique task ID with timestamp prefix."""
    timestamp = int(time.time())
    unique_id = str(uuid.uuid4())[:8]
    return f"task_{timestamp}_{unique_id}"

def is_valid_task_id(task_id: str) -> bool:
    """Validate task ID format."""
    if not task_id or not isinstance(task_id, str):
        return False

    parts = task_id.split('_')
    if len(parts) != 3 or parts[0] != 'task':
        return False

    try:
        int(parts[1])  # timestamp
        return len(parts[2]) == 8  # uuid part
    except ValueError:
        return False

# utils/rate_limiter.py
import time
import redis
from typing import Dict, Optional

class RateLimiter:
    """Redis-based rate limiter for API endpoints."""

    def __init__(self, max_requests: int = 100, window_seconds: int = 3600, redis_url: str = None):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.redis_client = redis.from_url(redis_url or "redis://localhost:6379/0")

    def allow_request(self, client_id: str) -> bool:
        """Check if request is allowed for client."""
        try:
            key = f"rate_limit:{client_id}"
            current_time = int(time.time())
            window_start = current_time - self.window_seconds

            # Remove old entries
            self.redis_client.zremrangebyscore(key, 0, window_start)

            # Count current requests
            current_requests = self.redis_client.zcard(key)

            if current_requests >= self.max_requests:
                return False

            # Add current request
            self.redis_client.zadd(key, {str(current_time): current_time})
            self.redis_client.expire(key, self.window_seconds)

            return True

        except Exception:
            # If Redis fails, allow request (fail open)
            return True

# utils/error_handler.py
from flask import jsonify
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Custom API error with status code."""

    def __init__(self, message: str, status_code: int = 400, payload: dict = None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.payload = payload

def handle_api_error(error: APIError, task_id: str = None):
    """Handle API errors with standardized response."""
    response = {
        "status": "error",
        "message": error.message,
        "timestamp": datetime.utcnow().isoformat()
    }

    if task_id:
        response["task_id"] = task_id

    if error.payload:
        response.update(error.payload)

    logger.error(f"API Error: {error.message} (Status: {error.status_code})")

    return jsonify(response), error.status_code
```

### Step 3: Data Models
```python
# models/task_request.py
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, Any, Optional

@dataclass
class TaskRequest:
    """Data model for task requests."""
    task_id: str
    task_type: str
    args: Dict[str, Any]
    priority: str = "medium"
    metadata: Dict[str, Any] = None
    submitted_at: datetime = None

    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}
        if self.submitted_at is None:
            self.submitted_at = datetime.utcnow()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "task_id": self.task_id,
            "task_type": self.task_type,
            "args": self.args,
            "priority": self.priority,
            "metadata": self.metadata,
            "submitted_at": self.submitted_at.isoformat()
        }

# models/api_log.py (optional database logging)
from sqlalchemy import Column, Integer, String, DateTime, Text, JSON
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime

Base = declarative_base()

class APILog(Base):
    """Database model for API request logging."""
    __tablename__ = 'api_logs'

    id = Column(Integer, primary_key=True)
    task_id = Column(String(50), nullable=False)
    endpoint = Column(String(100), nullable=False)
    method = Column(String(10), nullable=False)
    client_ip = Column(String(45))
    request_data = Column(JSON)
    response_status = Column(Integer)
    response_time_ms = Column(Integer)
    created_at = Column(DateTime, default=datetime.utcnow)

    def to_dict(self):
        return {
            'id': self.id,
            'task_id': self.task_id,
            'endpoint': self.endpoint,
            'method': self.method,
            'client_ip': self.client_ip,
            'response_status': self.response_status,
            'response_time_ms': self.response_time_ms,
            'created_at': self.created_at.isoformat()
        }
```

### Step 4: Flask Application Integration
```python
# app.py (integration with main Flask app)
from flask import Flask
from flask_cors import CORS
from routes.task_api import task_api_bp
import logging

def create_app():
    app = Flask(__name__)

    # Configure CORS
    CORS(app, origins=["http://localhost:3000", "https://yourdomain.com"])

    # Register blueprints
    app.register_blueprint(task_api_bp)

    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    return app

if __name__ == '__main__':
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000)
```

### Step 5: Testing Implementation
```python
# tests/test_task_api.py
import pytest
import json
from app import create_app

@pytest.fixture
def app():
    """Create test application."""
    app = create_app()
    app.config['TESTING'] = True
    return app

@pytest.fixture
def client(app):
    """Create test client."""
    return app.test_client()

class TestTaskAPI:

    def test_submit_valid_task(self, client):
        """Test submitting a valid task."""
        payload = {
            "type": "email_draft",
            "args": {
                "recipient": "test@example.com",
                "subject": "Test Subject",
                "content": "Test content"
            },
            "priority": "medium"
        }

        response = client.post('/api/v1/task',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 201
        data = response.get_json()
        assert 'task_id' in data
        assert data['status'] == 'accepted'
        assert 'timestamp' in data

    def test_submit_invalid_task_missing_type(self, client):
        """Test submitting task without required type field."""
        payload = {
            "args": {
                "recipient": "test@example.com",
                "subject": "Test Subject"
            }
        }

        response = client.post('/api/v1/task',
                             data=json.dumps(payload),
                             content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        assert 'validation' in data['message'].lower()

    def test_submit_invalid_json(self, client):
        """Test submitting invalid JSON."""
        response = client.post('/api/v1/task',
                             data='invalid json',
                             content_type='application/json')

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_get_task_status_valid(self, client):
        """Test getting status of valid task."""
        # First submit a task
        payload = {
            "type": "email_draft",
            "args": {
                "recipient": "test@example.com",
                "subject": "Test Subject",
                "content": "Test content"
            }
        }

        submit_response = client.post('/api/v1/task',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        task_id = submit_response.get_json()['task_id']

        # Get task status
        status_response = client.get(f'/api/v1/task/{task_id}')

        assert status_response.status_code == 200
        data = status_response.get_json()
        assert data['task_id'] == task_id
        assert 'status' in data

    def test_get_task_status_invalid_id(self, client):
        """Test getting status with invalid task ID."""
        response = client.get('/api/v1/task/invalid_id')

        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'

    def test_cancel_task(self, client):
        """Test cancelling a task."""
        # Submit task first
        payload = {
            "type": "email_draft",
            "args": {
                "recipient": "test@example.com",
                "subject": "Test Subject",
                "content": "Test content"
            }
        }

        submit_response = client.post('/api/v1/task',
                                    data=json.dumps(payload),
                                    content_type='application/json')

        task_id = submit_response.get_json()['task_id']

        # Cancel task
        cancel_response = client.delete(f'/api/v1/task/{task_id}')

        assert cancel_response.status_code == 200
        data = cancel_response.get_json()
        assert data['status'] == 'cancelled'
```

---

## 🧪 7. Testing & QA

### 7.1 Comprehensive Test Suite
```bash
# Run all tests
pytest tests/ -v --cov=routes --cov=schemas --cov=utils

# Run specific test categories
pytest tests/test_task_api.py -v          # API endpoint tests
pytest tests/test_validation.py -v       # Validation tests
pytest tests/test_rate_limiting.py -v    # Rate limiting tests

# Performance testing
pytest tests/test_performance.py -v      # Load testing
```

### 7.2 Manual Testing with curl
```bash
# Test valid task submission
curl -X POST http://localhost:5000/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email_draft",
    "args": {
      "recipient": "test@example.com",
      "subject": "Test Subject",
      "content": "Test content"
    },
    "priority": "medium"
  }'

# Test invalid request
curl -X POST http://localhost:5000/api/v1/task \
  -H "Content-Type: application/json" \
  -d '{"invalid": "request"}'

# Test task status
curl -X GET http://localhost:5000/api/v1/task/task_1234567890_abcd1234

# Test rate limiting (send multiple requests quickly)
for i in {1..10}; do
  curl -X POST http://localhost:5000/api/v1/task \
    -H "Content-Type: application/json" \
    -d '{"type": "email_draft", "args": {"recipient": "test@example.com", "subject": "Test", "content": "Test"}}'
done
```

### 7.3 Load Testing
```python
# tests/test_performance.py
import pytest
import requests
import threading
import time
from concurrent.futures import ThreadPoolExecutor

def test_concurrent_requests():
    """Test API performance under concurrent load."""
    base_url = "http://localhost:5000/api/v1/task"

    def send_request(request_id):
        payload = {
            "type": "email_draft",
            "args": {
                "recipient": f"test{request_id}@example.com",
                "subject": f"Test Subject {request_id}",
                "content": f"Test content {request_id}"
            }
        }

        start_time = time.time()
        response = requests.post(base_url, json=payload)
        duration = time.time() - start_time

        return {
            "status_code": response.status_code,
            "duration": duration,
            "request_id": request_id
        }

    # Send 50 concurrent requests
    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(send_request, i) for i in range(50)]
        results = [future.result() for future in futures]

    # Analyze results
    successful_requests = [r for r in results if r["status_code"] == 201]
    avg_duration = sum(r["duration"] for r in results) / len(results)

    assert len(successful_requests) >= 45  # At least 90% success rate
    assert avg_duration < 1.0  # Average response time under 1 second
```

---

## 🔗 8. Integration & Related Tasks

### 8.1 Standalone Implementation
This Task API Endpoint is designed to be completely self-contained and requires:
- **Flask Framework**: For web server functionality
- **Redis**: For rate limiting (optional, falls back gracefully)
- **JSON Schema**: For request validation
- **Database**: For logging (optional)

### 8.2 Integration with DirectorAgent
```python
# Integration point with DirectorAgent
def process_task_request(task_request: TaskRequest) -> Dict:
    """
    Process task request through DirectorAgent.
    This function would integrate with the DirectorAgent implementation.
    """
    try:
        # Import DirectorAgent (when available)
        # from agents.director import DirectorAgent

        # For now, return mock response
        return {
            "status": "accepted",
            "message": "Task queued for processing",
            "estimated_completion": (datetime.utcnow() + timedelta(minutes=30)).isoformat()
        }

        # Future implementation:
        # director = DirectorAgent()
        # result = director.route_task(task_request.to_dict())
        # return result

    except Exception as e:
        return {
            "status": "rejected",
            "message": f"Task processing failed: {str(e)}"
        }
```

### 8.3 API Documentation Generation
```python
# Generate OpenAPI documentation
from flask import Flask
from flask_restx import Api, Resource, fields

api = Api(app, doc='/docs/', title='SwarmDirector Task API')

task_model = api.model('Task', {
    'type': fields.String(required=True, enum=['email_draft', 'data_analysis']),
    'args': fields.Raw(required=True),
    'priority': fields.String(enum=['low', 'medium', 'high', 'urgent']),
    'metadata': fields.Raw()
})

@api.route('/task')
class TaskSubmission(Resource):
    @api.expect(task_model)
    def post(self):
        """Submit a new task for processing"""
        pass
```

---

## ⚠️ 9. Risks & Mitigations

| Risk | Mitigation |
|------|------------|
| High request volume overwhelming system | Implement rate limiting and request queuing |
| Invalid JSON causing server errors | Comprehensive input validation and error handling |
| Memory leaks from large payloads | Set payload size limits and implement cleanup |
| Security vulnerabilities from malicious input | Input sanitization and JSON schema validation |
| Database connection failures | Graceful degradation and connection pooling |
| Redis unavailability affecting rate limiting | Fail-open strategy when Redis is unavailable |

### 9.1 Security Considerations
- **Input Validation**: All inputs validated against JSON schemas
- **Rate Limiting**: Prevent DoS attacks and abuse
- **CORS Configuration**: Restrict cross-origin requests
- **Error Information**: Don't expose internal system details
- **Logging**: Log security events without sensitive data

### 9.2 Performance Optimization
- **Connection Pooling**: Reuse database connections
- **Caching**: Cache validation schemas and frequent queries
- **Async Processing**: Use background tasks for heavy operations
- **Compression**: Enable gzip compression for responses
- **CDN**: Use CDN for static documentation assets

---

## ✅ 10. Success Criteria

### 10.1 Functional Requirements
- [ ] POST /api/v1/task endpoint accepts valid JSON requests
- [ ] JSON schema validation rejects invalid requests with clear errors
- [ ] Unique task IDs generated for each request
- [ ] Standardized JSON responses for all scenarios
- [ ] Rate limiting prevents abuse (configurable limits)
- [ ] Error handling provides informative messages
- [ ] Task status retrieval works correctly
- [ ] Task cancellation functionality operational

### 10.2 Performance Requirements
- [ ] Response time <500ms for 95% of requests
- [ ] Handles 100+ concurrent requests without degradation
- [ ] Memory usage remains stable under load
- [ ] Rate limiting accurately enforces limits
- [ ] Database operations complete within timeout

### 10.3 Quality Requirements
- [ ] Unit test coverage >90%
- [ ] Integration tests cover all endpoints
- [ ] Load testing validates performance requirements
- [ ] Security testing finds no vulnerabilities
- [ ] Code follows PEP 8 style guidelines
- [ ] API documentation is complete and accurate

### 10.4 Integration Requirements
- [ ] Flask application integration successful
- [ ] CORS configuration allows intended origins
- [ ] Redis integration works (with graceful fallback)
- [ ] Database logging operational (if enabled)
- [ ] OpenAPI documentation generates correctly

---

## 🚀 11. Next Steps

### 11.1 Immediate Actions
1. **Complete Implementation**: Follow step-by-step implementation plan
2. **Set Up Testing**: Configure test environment and run test suite
3. **Configure Rate Limiting**: Set up Redis and configure limits
4. **Test Integration**: Verify Flask application integration

### 11.2 Production Readiness
1. **Security Audit**: Review input validation and error handling
2. **Performance Testing**: Conduct load testing with expected traffic
3. **Monitoring Setup**: Implement logging and metrics collection
4. **Documentation**: Complete API documentation and usage examples

### 11.3 Future Enhancements
1. **Authentication**: Add API key or OAuth authentication
2. **Webhooks**: Implement callback URLs for task completion
3. **Batch Operations**: Support multiple task submission
4. **Advanced Filtering**: Add query parameters for task listing
5. **Real-time Updates**: WebSocket support for live status updates

### 11.4 Resources & Documentation
- **Flask Documentation**: https://flask.palletsprojects.com/
- **JSON Schema**: https://json-schema.org/
- **OpenAPI Specification**: https://swagger.io/specification/
- **Redis Documentation**: https://redis.io/documentation
- **REST API Best Practices**: Industry standard guidelines
