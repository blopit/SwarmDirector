# SwarmDirector API Documentation

This directory contains comprehensive API documentation for the SwarmDirector system.

## 📚 API Overview

SwarmDirector provides a RESTful API for managing hierarchical AI agents, tasks, and conversations. The API follows standard HTTP conventions and returns JSON responses.

### Base URL
```
http://localhost:5000  # Development
https://your-domain.com  # Production
```

### Authentication
Currently, the API operates without authentication for development. Production deployments should implement proper authentication mechanisms.

### Response Format
All API responses follow a consistent format:

```json
{
  "status": "success|error",
  "message": "Human-readable message",
  "data": {
    // Response data
  },
  "error": "Error details (if status is error)"
}
```

## 🔗 API Endpoints

### Core Endpoints

| Endpoint | Description | Documentation |
|----------|-------------|---------------|
| `/health` | System health check | [Health API](health.md) |
| `/task` | Task submission and management | [Task API](tasks.md) |
| `/api/agents` | Agent management | [Agent API](agents.md) |
| `/api/tasks` | Task CRUD operations | [Task API](tasks.md) |
| `/api/conversations` | Conversation management | [Conversation API](conversations.md) |

### Dashboard Endpoints

| Endpoint | Description |
|----------|-------------|
| `/dashboard` | Main dashboard interface |
| `/dashboard/agents` | Agent management interface |
| `/dashboard/tasks` | Task management interface |

### Demo Endpoints

| Endpoint | Description |
|----------|-------------|
| `/demo` | Interactive demo interface |
| `/demo/api/submit_task` | Demo task submission |
| `/demo/api/system_status` | Demo system status |

## 📖 Detailed Documentation

- **[Agent API](agents.md)** - Complete agent management API
- **[Task API](tasks.md)** - Task creation, management, and execution
- **[Conversation API](conversations.md)** - Agent communication and chat history
- **[Authentication](authentication.md)** - Authentication and authorization (future)

## 🚀 Quick Start

### 1. Health Check
```bash
curl http://localhost:5000/health
```

### 2. Submit a Task
```bash
curl -X POST http://localhost:5000/task \
  -H "Content-Type: application/json" \
  -d '{
    "type": "email",
    "title": "Send welcome email",
    "description": "Send welcome email to new user",
    "args": {
      "recipient": "user@example.com",
      "template": "welcome"
    }
  }'
```

### 3. List Agents
```bash
curl http://localhost:5000/api/agents
```

### 4. List Tasks
```bash
curl http://localhost:5000/api/tasks
```

## 📝 Examples

### Creating an Agent
```bash
curl -X POST http://localhost:5000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Email Specialist",
    "description": "Specialized agent for email operations",
    "agent_type": "specialist",
    "capabilities": ["email_sending", "template_processing"],
    "config": {
      "max_concurrent_tasks": 5,
      "timeout": 30
    }
  }'
```

### Creating a Task
```bash
curl -X POST http://localhost:5000/api/tasks \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Process customer inquiry",
    "description": "Handle customer support request",
    "priority": "high",
    "input_data": {
      "customer_id": "12345",
      "inquiry_type": "billing"
    }
  }'
```

### Starting a Conversation
```bash
curl -X POST http://localhost:5000/api/conversations \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Customer Support Session",
    "description": "Support conversation with customer",
    "conversation_type": "support",
    "initiator_agent_id": 1
  }'
```

## 🔧 Error Handling

The API uses standard HTTP status codes:

- `200 OK` - Successful request
- `201 Created` - Resource created successfully
- `400 Bad Request` - Invalid request data
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

Error responses include detailed error information:

```json
{
  "status": "error",
  "error": "Validation failed",
  "message": "Required field 'name' is missing",
  "details": {
    "field": "name",
    "code": "REQUIRED_FIELD_MISSING"
  }
}
```

## 📊 Rate Limiting

Currently, no rate limiting is implemented. Production deployments should implement appropriate rate limiting based on usage patterns.

## 🔒 Security Considerations

- All inputs are validated and sanitized
- SQL injection protection through SQLAlchemy ORM
- XSS protection in web interfaces
- CSRF protection for state-changing operations

## 📈 Monitoring

The API provides several monitoring endpoints:

- `/health` - Basic health check
- `/api/system/status` - Detailed system status
- `/api/system/metrics` - Performance metrics

## 🐛 Debugging

Enable debug mode for detailed error information:

```python
app.config['DEBUG'] = True
```

Debug responses include stack traces and additional context for troubleshooting.

## 📞 Support

For API support and questions:
- Check the detailed endpoint documentation
- Review the examples in this directory
- Submit issues via GitHub Issues
- Join discussions in GitHub Discussions
