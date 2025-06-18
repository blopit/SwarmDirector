---
title: API Documentation Directory
description: REST API documentation and reference materials for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [api-documentation, rest-api, openapi, endpoints]
---

# API Documentation Directory

## Purpose

The docs/api directory contains comprehensive REST API documentation for SwarmDirector, including endpoint references, request/response schemas, authentication guides, and integration examples. This directory serves as the authoritative source for API documentation and developer integration guides.

## Structure

```
docs/api/
├── README.md                    # API overview and getting started guide
├── agents.md                    # Agent management API documentation
├── tasks.md                     # Task management API documentation
├── conversations.md             # Conversation API documentation
├── analytics.md                 # Analytics API documentation
├── workflows.md                 # Workflow management API documentation
├── cost_tracking.md             # Cost tracking API documentation
├── authentication.md            # Authentication and authorization guide
├── webhooks.md                  # Webhook configuration and usage
├── rate_limiting.md             # Rate limiting and throttling documentation
├── error_handling.md            # Error codes and handling guide
├── schemas/                     # API schema definitions
│   ├── agent_schemas.json       # Agent-related schemas
│   ├── task_schemas.json        # Task-related schemas
│   ├── conversation_schemas.json # Conversation schemas
│   ├── analytics_schemas.json   # Analytics schemas
│   ├── error_schemas.json       # Error response schemas
│   └── common_schemas.json      # Common/shared schemas
├── examples/                    # API usage examples
│   ├── python/                  # Python client examples
│   │   ├── basic_usage.py       # Basic API usage examples
│   │   ├── agent_management.py  # Agent management examples
│   │   ├── task_automation.py   # Task automation examples
│   │   └── analytics_client.py  # Analytics API examples
│   ├── javascript/              # JavaScript client examples
│   │   ├── basic_usage.js       # Basic API usage examples
│   │   ├── react_integration.js # React integration examples
│   │   └── node_client.js       # Node.js client examples
│   ├── curl/                    # cURL command examples
│   │   ├── authentication.sh    # Authentication examples
│   │   ├── agent_operations.sh  # Agent operation examples
│   │   └── task_operations.sh   # Task operation examples
│   └── postman/                 # Postman collection
│       ├── SwarmDirector.postman_collection.json
│       └── SwarmDirector.postman_environment.json
├── openapi/                     # OpenAPI specifications
│   ├── openapi.yaml             # Complete OpenAPI 3.0 specification
│   ├── agents.yaml              # Agent endpoints specification
│   ├── tasks.yaml               # Task endpoints specification
│   ├── analytics.yaml           # Analytics endpoints specification
│   └── webhooks.yaml            # Webhook endpoints specification
└── guides/                      # Integration guides
    ├── getting_started.md       # Quick start guide for developers
    ├── client_libraries.md      # Official client library documentation
    ├── integration_patterns.md  # Common integration patterns
    ├── best_practices.md        # API usage best practices
    ├── troubleshooting.md       # Common issues and solutions
    └── migration_guide.md       # API version migration guide
```

## Guidelines

### 1. Organization
- **Endpoint Grouping**: Group API documentation by functional area
- **Schema Separation**: Maintain separate schema files for different domains
- **Example Organization**: Organize examples by programming language and use case
- **Version Management**: Maintain documentation for different API versions

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for all documentation files
- **Consistent Format**: Follow consistent naming conventions across all files
- **Version Indicators**: Include version information where relevant
- **Language Prefixes**: Use language prefixes for example files

### 3. Implementation
- **OpenAPI Standards**: Use OpenAPI 3.0 for formal API specifications
- **Comprehensive Examples**: Provide working examples for all endpoints
- **Error Documentation**: Document all possible error responses
- **Authentication**: Include comprehensive authentication documentation
- **Rate Limiting**: Document rate limiting and usage policies

### 4. Documentation
- **Complete Coverage**: Document all public API endpoints
- **Request/Response**: Include complete request and response examples
- **Parameter Documentation**: Document all parameters with types and constraints
- **Status Codes**: Document all HTTP status codes and their meanings
- **Integration Guides**: Provide step-by-step integration guides

## Best Practices

### API Documentation Structure
```markdown
# Agent Management API

## Overview
The Agent Management API provides endpoints for creating, managing, and monitoring AI agents within the SwarmDirector system.

## Base URL
```
https://api.swarmdirector.com/v1
```

## Authentication
All API requests require authentication using an API key in the Authorization header:
```
Authorization: Bearer YOUR_API_KEY
```

## Endpoints

### List Agents
Retrieve a list of all agents.

**Endpoint:** `GET /agents`

**Parameters:**
- `page` (integer, optional): Page number for pagination (default: 1)
- `limit` (integer, optional): Number of items per page (default: 20, max: 100)
- `status` (string, optional): Filter by agent status (`active`, `inactive`, `maintenance`)
- `type` (string, optional): Filter by agent type (`director`, `worker`, `specialist`)

**Response:**
```json
{
  "agents": [
    {
      "id": "agent_001",
      "name": "Director Agent",
      "type": "director",
      "status": "active",
      "created_at": "2025-06-18T10:00:00Z",
      "updated_at": "2025-06-18T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 1,
    "pages": 1
  }
}
```

**Status Codes:**
- `200 OK`: Success
- `400 Bad Request`: Invalid parameters
- `401 Unauthorized`: Invalid or missing API key
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error
```

### Security
- **API Key Management**: Secure API key generation and management
- **Rate Limiting**: Implement and document rate limiting policies
- **Input Validation**: Validate all API inputs and document constraints
- **HTTPS Only**: Require HTTPS for all API communications
- **Error Information**: Limit error information to prevent information disclosure

### Performance
- **Pagination**: Implement pagination for list endpoints
- **Caching**: Document caching strategies and headers
- **Compression**: Support response compression
- **Async Operations**: Document asynchronous operation patterns

### Testing
```python
# examples/python/test_api_client.py
import pytest
import requests
from typing import Dict, Any

class SwarmDirectorAPIClient:
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        self.session.headers.update({
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        })
    
    def list_agents(self, **params) -> Dict[str, Any]:
        """List all agents with optional filtering."""
        response = self.session.get(f'{self.base_url}/agents', params=params)
        response.raise_for_status()
        return response.json()
    
    def create_agent(self, agent_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new agent."""
        response = self.session.post(f'{self.base_url}/agents', json=agent_data)
        response.raise_for_status()
        return response.json()
    
    def get_agent(self, agent_id: str) -> Dict[str, Any]:
        """Get agent details by ID."""
        response = self.session.get(f'{self.base_url}/agents/{agent_id}')
        response.raise_for_status()
        return response.json()

@pytest.fixture
def api_client():
    return SwarmDirectorAPIClient(
        base_url="https://api.swarmdirector.com/v1",
        api_key="test_api_key"
    )

def test_list_agents(api_client):
    """Test listing agents."""
    response = api_client.list_agents()
    
    assert 'agents' in response
    assert 'pagination' in response
    assert isinstance(response['agents'], list)

def test_create_agent(api_client):
    """Test creating a new agent."""
    agent_data = {
        "name": "Test Agent",
        "type": "worker",
        "description": "Test agent for API testing",
        "config": {
            "model": "gpt-3.5-turbo",
            "temperature": 0.7
        }
    }
    
    response = api_client.create_agent(agent_data)
    
    assert 'id' in response
    assert response['name'] == agent_data['name']
    assert response['type'] == agent_data['type']
```

### Documentation Standards
- **Consistent Format**: Use consistent formatting across all documentation
- **Complete Examples**: Provide complete, working examples
- **Error Scenarios**: Document error scenarios and responses
- **Version Information**: Include API version information
- **Update Procedures**: Document procedures for updating API documentation

## Examples

### OpenAPI Specification
```yaml
# openapi/agents.yaml - Agent endpoints OpenAPI specification
openapi: 3.0.3
info:
  title: SwarmDirector Agent Management API
  description: API for managing AI agents in the SwarmDirector system
  version: 1.0.0
  contact:
    name: SwarmDirector Team
    email: api-support@swarmdirector.com
  license:
    name: MIT
    url: https://opensource.org/licenses/MIT

servers:
  - url: https://api.swarmdirector.com/v1
    description: Production server
  - url: https://staging-api.swarmdirector.com/v1
    description: Staging server

paths:
  /agents:
    get:
      summary: List agents
      description: Retrieve a paginated list of agents with optional filtering
      operationId: listAgents
      tags:
        - Agents
      parameters:
        - name: page
          in: query
          description: Page number for pagination
          required: false
          schema:
            type: integer
            minimum: 1
            default: 1
        - name: limit
          in: query
          description: Number of items per page
          required: false
          schema:
            type: integer
            minimum: 1
            maximum: 100
            default: 20
        - name: status
          in: query
          description: Filter by agent status
          required: false
          schema:
            type: string
            enum: [active, inactive, maintenance]
        - name: type
          in: query
          description: Filter by agent type
          required: false
          schema:
            type: string
            enum: [director, worker, specialist]
      responses:
        '200':
          description: Successful response
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/AgentListResponse'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '429':
          description: Too many requests
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
      security:
        - ApiKeyAuth: []

    post:
      summary: Create agent
      description: Create a new agent in the system
      operationId: createAgent
      tags:
        - Agents
      requestBody:
        required: true
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/CreateAgentRequest'
      responses:
        '201':
          description: Agent created successfully
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/Agent'
        '400':
          description: Bad request
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '401':
          description: Unauthorized
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
        '422':
          description: Validation error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ValidationErrorResponse'
        '500':
          description: Internal server error
          content:
            application/json:
              schema:
                $ref: '#/components/schemas/ErrorResponse'
      security:
        - ApiKeyAuth: []

components:
  schemas:
    Agent:
      type: object
      required:
        - id
        - name
        - type
        - status
        - created_at
        - updated_at
      properties:
        id:
          type: string
          description: Unique agent identifier
          example: "agent_001"
        name:
          type: string
          description: Human-readable agent name
          example: "Director Agent"
        type:
          type: string
          enum: [director, worker, specialist]
          description: Agent type
          example: "director"
        description:
          type: string
          description: Agent description
          example: "Primary director agent for task orchestration"
        status:
          type: string
          enum: [active, inactive, maintenance, error]
          description: Current agent status
          example: "active"
        config:
          type: object
          description: Agent configuration
          example:
            model: "gpt-4"
            temperature: 0.7
            max_tokens: 2000
        capabilities:
          type: array
          items:
            type: string
          description: Agent capabilities
          example: ["task_orchestration", "agent_management"]
        performance_score:
          type: number
          minimum: 0.0
          maximum: 1.0
          description: Agent performance score
          example: 0.85
        created_at:
          type: string
          format: date-time
          description: Creation timestamp
          example: "2025-06-18T10:00:00Z"
        updated_at:
          type: string
          format: date-time
          description: Last update timestamp
          example: "2025-06-18T10:00:00Z"

    CreateAgentRequest:
      type: object
      required:
        - name
        - type
      properties:
        name:
          type: string
          minLength: 1
          maxLength: 200
          description: Agent name
          example: "New Agent"
        type:
          type: string
          enum: [director, worker, specialist]
          description: Agent type
          example: "worker"
        description:
          type: string
          maxLength: 1000
          description: Agent description
          example: "A new worker agent for task execution"
        config:
          type: object
          description: Agent configuration
          example:
            model: "gpt-3.5-turbo"
            temperature: 0.6
        capabilities:
          type: array
          items:
            type: string
          description: Agent capabilities
          example: ["text_processing", "data_extraction"]

  securitySchemes:
    ApiKeyAuth:
      type: apiKey
      in: header
      name: Authorization
      description: API key authentication using Bearer token
```

### JavaScript Client Example
```javascript
// examples/javascript/agent_client.js
class SwarmDirectorClient {
    constructor(baseUrl, apiKey) {
        this.baseUrl = baseUrl.replace(/\/$/, '');
        this.apiKey = apiKey;
        this.defaultHeaders = {
            'Authorization': `Bearer ${apiKey}`,
            'Content-Type': 'application/json'
        };
    }

    async request(method, endpoint, data = null) {
        const url = `${this.baseUrl}${endpoint}`;
        const options = {
            method,
            headers: this.defaultHeaders
        };

        if (data) {
            options.body = JSON.stringify(data);
        }

        try {
            const response = await fetch(url, options);
            
            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(`API Error ${response.status}: ${errorData.message}`);
            }

            return await response.json();
        } catch (error) {
            console.error('API request failed:', error);
            throw error;
        }
    }

    // Agent management methods
    async listAgents(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/agents${queryString ? `?${queryString}` : ''}`;
        return this.request('GET', endpoint);
    }

    async createAgent(agentData) {
        return this.request('POST', '/agents', agentData);
    }

    async getAgent(agentId) {
        return this.request('GET', `/agents/${agentId}`);
    }

    async updateAgent(agentId, updateData) {
        return this.request('PUT', `/agents/${agentId}`, updateData);
    }

    async deleteAgent(agentId) {
        return this.request('DELETE', `/agents/${agentId}`);
    }

    // Task management methods
    async listTasks(params = {}) {
        const queryString = new URLSearchParams(params).toString();
        const endpoint = `/tasks${queryString ? `?${queryString}` : ''}`;
        return this.request('GET', endpoint);
    }

    async createTask(taskData) {
        return this.request('POST', '/tasks', taskData);
    }

    async getTask(taskId) {
        return this.request('GET', `/tasks/${taskId}`);
    }
}

// Usage example
const client = new SwarmDirectorClient(
    'https://api.swarmdirector.com/v1',
    'your-api-key-here'
);

// Example usage
async function demonstrateAPI() {
    try {
        // List all agents
        const agents = await client.listAgents({ status: 'active' });
        console.log('Active agents:', agents);

        // Create a new agent
        const newAgent = await client.createAgent({
            name: 'Demo Agent',
            type: 'worker',
            description: 'A demo agent for testing',
            config: {
                model: 'gpt-3.5-turbo',
                temperature: 0.7
            }
        });
        console.log('Created agent:', newAgent);

        // Create a task for the agent
        const newTask = await client.createTask({
            title: 'Demo Task',
            description: 'A demo task for testing',
            assigned_agent_id: newAgent.id,
            priority: 3
        });
        console.log('Created task:', newTask);

    } catch (error) {
        console.error('API demonstration failed:', error);
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = SwarmDirectorClient;
}
```

## Related Documentation

- [Authentication Guide](authentication.md) - API authentication and authorization
- [Rate Limiting](rate_limiting.md) - API rate limiting and usage policies
- [Error Handling](error_handling.md) - Error codes and handling strategies
- [Webhooks](webhooks.md) - Webhook configuration and usage
- [Client Libraries](guides/client_libraries.md) - Official client library documentation
- [Integration Patterns](guides/integration_patterns.md) - Common integration patterns and best practices
