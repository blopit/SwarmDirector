# Agent API Documentation

This document provides comprehensive documentation for the SwarmDirector Agent API endpoints.

## 📋 Overview

The Agent API allows you to manage AI agents in the SwarmDirector system. Agents are the core components that execute tasks and coordinate with each other in a hierarchical structure.

### Base URL
```
http://localhost:5000/api/agents
```

### Agent Types
- **`supervisor`**: High-level agents that coordinate other agents
- **`coordinator`**: Mid-level agents that manage specific departments
- **`worker`**: Task-executing agents
- **`specialist`**: Specialized agents for specific domains

### Agent Status
- **`active`**: Agent is running and available
- **`idle`**: Agent is available but not currently processing
- **`busy`**: Agent is currently processing tasks
- **`error`**: Agent encountered an error
- **`offline`**: Agent is not available

## 🔗 Endpoints

### 1. List All Agents

Get a list of all agents in the system.

```http
GET /api/agents
```

#### Query Parameters

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| `type` | string | Filter by agent type | `?type=worker` |
| `status` | string | Filter by agent status | `?status=active` |
| `parent_id` | integer | Filter by parent agent ID | `?parent_id=1` |

#### Response

```json
{
  "status": "success",
  "agents": [
    {
      "id": 1,
      "name": "DirectorAgent",
      "description": "Main director agent for task routing",
      "agent_type": "supervisor",
      "status": "active",
      "parent_id": null,
      "capabilities": ["routing", "intent_classification"],
      "config": {
        "max_concurrent_tasks": 10,
        "timeout": 30
      },
      "tasks_completed": 45,
      "success_rate": 0.96,
      "average_response_time": 1.2,
      "created_at": "2024-12-19T10:00:00Z",
      "updated_at": "2024-12-19T15:30:00Z"
    }
  ],
  "count": 1
}
```

#### Example Requests

```bash
# Get all agents
curl http://localhost:5000/api/agents

# Get only worker agents
curl "http://localhost:5000/api/agents?type=worker"

# Get active agents
curl "http://localhost:5000/api/agents?status=active"

# Get agents under a specific parent
curl "http://localhost:5000/api/agents?parent_id=1"
```

### 2. Get Specific Agent

Retrieve details for a specific agent by ID.

```http
GET /api/agents/{agent_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | integer | Unique agent identifier |

#### Response

```json
{
  "status": "success",
  "agent": {
    "id": 1,
    "name": "EmailAgent",
    "description": "Specialized agent for email operations",
    "agent_type": "specialist",
    "status": "idle",
    "parent_id": 2,
    "capabilities": ["email_sending", "template_processing"],
    "config": {
      "smtp_server": "smtp.gmail.com",
      "smtp_port": 587,
      "max_emails_per_hour": 100
    },
    "autogen_config": {
      "model": "gpt-4",
      "temperature": 0.7
    },
    "system_message": "You are an email specialist agent...",
    "tasks_completed": 23,
    "success_rate": 0.98,
    "average_response_time": 0.8,
    "created_at": "2024-12-19T10:00:00Z",
    "updated_at": "2024-12-19T15:30:00Z"
  }
}
```

#### Example Request

```bash
curl http://localhost:5000/api/agents/1
```

### 3. Create New Agent

Create a new agent in the system.

```http
POST /api/agents
```

#### Request Body

```json
{
  "name": "ResearchAgent",
  "description": "Agent specialized in research and data gathering",
  "agent_type": "specialist",
  "status": "idle",
  "parent_id": 2,
  "capabilities": ["web_search", "data_analysis", "report_generation"],
  "config": {
    "max_search_results": 50,
    "timeout": 60,
    "preferred_sources": ["academic", "news", "official"]
  },
  "autogen_config": {
    "model": "gpt-4",
    "temperature": 0.3,
    "max_tokens": 2000
  },
  "system_message": "You are a research specialist agent focused on gathering accurate information from reliable sources."
}
```

#### Required Fields

- `name`: Agent name (string, max 100 characters)
- `agent_type`: Agent type (enum: supervisor, coordinator, worker, specialist)

#### Optional Fields

- `description`: Agent description (string)
- `status`: Initial status (enum, default: idle)
- `parent_id`: Parent agent ID for hierarchy (integer)
- `capabilities`: List of agent capabilities (array)
- `config`: Agent-specific configuration (object)
- `autogen_config`: AutoGen framework configuration (object)
- `system_message`: System message for the agent (string)

#### Response

```json
{
  "status": "success",
  "message": "Agent created successfully",
  "agent": {
    "id": 4,
    "name": "ResearchAgent",
    "description": "Agent specialized in research and data gathering",
    "agent_type": "specialist",
    "status": "idle",
    "parent_id": 2,
    "capabilities": ["web_search", "data_analysis", "report_generation"],
    "config": {
      "max_search_results": 50,
      "timeout": 60,
      "preferred_sources": ["academic", "news", "official"]
    },
    "autogen_config": {
      "model": "gpt-4",
      "temperature": 0.3,
      "max_tokens": 2000
    },
    "system_message": "You are a research specialist agent...",
    "tasks_completed": 0,
    "success_rate": null,
    "average_response_time": null,
    "created_at": "2024-12-19T16:00:00Z",
    "updated_at": "2024-12-19T16:00:00Z"
  }
}
```

#### Example Request

```bash
curl -X POST http://localhost:5000/api/agents \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ResearchAgent",
    "description": "Agent specialized in research and data gathering",
    "agent_type": "specialist",
    "capabilities": ["web_search", "data_analysis"]
  }'
```

### 4. Update Agent

Update an existing agent's properties.

```http
PUT /api/agents/{agent_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | integer | Unique agent identifier |

#### Request Body

```json
{
  "description": "Updated agent description",
  "status": "active",
  "capabilities": ["email_sending", "template_processing", "analytics"],
  "config": {
    "max_emails_per_hour": 150,
    "enable_analytics": true
  }
}
```

#### Response

```json
{
  "status": "success",
  "message": "Agent updated successfully",
  "agent": {
    "id": 1,
    "name": "EmailAgent",
    "description": "Updated agent description",
    "agent_type": "specialist",
    "status": "active",
    "capabilities": ["email_sending", "template_processing", "analytics"],
    "config": {
      "max_emails_per_hour": 150,
      "enable_analytics": true
    },
    "updated_at": "2024-12-19T16:30:00Z"
  }
}
```

#### Example Request

```bash
curl -X PUT http://localhost:5000/api/agents/1 \
  -H "Content-Type: application/json" \
  -d '{
    "status": "active",
    "config": {
      "max_emails_per_hour": 150
    }
  }'
```

### 5. Delete Agent

Remove an agent from the system.

```http
DELETE /api/agents/{agent_id}
```

#### Path Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `agent_id` | integer | Unique agent identifier |

#### Response

```json
{
  "status": "success",
  "message": "Agent deleted successfully"
}
```

#### Example Request

```bash
curl -X DELETE http://localhost:5000/api/agents/4
```

## 🔧 Error Handling

### Error Response Format

```json
{
  "status": "error",
  "error": "Error type",
  "message": "Human-readable error message",
  "details": {
    "field": "field_name",
    "code": "ERROR_CODE"
  }
}
```

### Common Error Codes

| Status Code | Error Type | Description |
|-------------|------------|-------------|
| 400 | Bad Request | Invalid request data or missing required fields |
| 404 | Not Found | Agent with specified ID not found |
| 409 | Conflict | Agent name already exists |
| 422 | Validation Error | Invalid field values or constraints |
| 500 | Internal Server Error | Server-side error |

### Example Error Responses

#### Missing Required Field
```json
{
  "status": "error",
  "error": "Validation failed",
  "message": "Agent name is required",
  "details": {
    "field": "name",
    "code": "REQUIRED_FIELD_MISSING"
  }
}
```

#### Agent Not Found
```json
{
  "status": "error",
  "error": "Resource not found",
  "message": "Agent with ID 999 not found"
}
```

#### Invalid Agent Type
```json
{
  "status": "error",
  "error": "Validation failed",
  "message": "Invalid agent type 'invalid_type'",
  "details": {
    "field": "agent_type",
    "code": "INVALID_ENUM_VALUE",
    "valid_values": ["supervisor", "coordinator", "worker", "specialist"]
  }
}
```

## 📊 Agent Hierarchy

Agents can be organized in a hierarchical structure using the `parent_id` field:

```
DirectorAgent (id: 1, parent_id: null)
├── CommunicationsCoordinator (id: 2, parent_id: 1)
│   ├── EmailAgent (id: 3, parent_id: 2)
│   └── NotificationAgent (id: 4, parent_id: 2)
└── ResearchCoordinator (id: 5, parent_id: 1)
    ├── WebSearchAgent (id: 6, parent_id: 5)
    └── DataAnalysisAgent (id: 7, parent_id: 5)
```

## 🔍 Filtering and Querying

### Complex Queries

```bash
# Get all specialist agents that are currently active
curl "http://localhost:5000/api/agents?type=specialist&status=active"

# Get all agents under the communications coordinator
curl "http://localhost:5000/api/agents?parent_id=2"
```

### Performance Considerations

- Use specific filters to reduce response size
- Consider pagination for large agent lists (future feature)
- Cache frequently accessed agent data

## 🚀 Best Practices

### Agent Naming
- Use descriptive, unique names
- Follow consistent naming conventions
- Include the agent's primary function

### Configuration Management
- Store environment-specific settings in `config`
- Use `autogen_config` for AI model parameters
- Keep sensitive data in environment variables

### Hierarchy Design
- Design logical hierarchies based on functionality
- Avoid deep nesting (max 3-4 levels recommended)
- Consider load balancing across coordinators

### Status Management
- Update agent status based on actual state
- Use appropriate status for monitoring
- Handle status transitions gracefully

This API provides comprehensive agent management capabilities for the SwarmDirector system, enabling dynamic agent creation, configuration, and hierarchical organization.
