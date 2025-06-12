# Documentation Directory

## Purpose
Contains comprehensive documentation for the SwarmDirector hierarchical AI agent management system, including API references, architecture guides, deployment instructions, and development documentation. This directory serves as the central knowledge base for users, developers, and system administrators.

## Structure
```
docs/
├── CHANGELOG.md                 # Version history and release notes
├── CONTRIBUTING.md              # Contribution guidelines and processes
├── PROJECT_STRUCTURE.md         # Detailed project organization guide
├── api/                         # API documentation
│   ├── README.md                # API overview and getting started
│   ├── agents.md                # Agent API reference
│   ├── tasks.md                 # Task API reference
│   ├── conversations.md         # Conversation API reference
│   └── authentication.md       # Authentication and authorization
├── architecture/                # System architecture documentation
│   ├── overview.md              # High-level architecture overview
│   ├── database_design.md       # Database schema and design
│   ├── agent_hierarchy.md       # Agent hierarchy and relationships
│   └── workflow_patterns.md     # Common workflow patterns
├── deployment/                  # Deployment and operations
│   ├── local_development.md     # Local development setup
│   ├── docker_deployment.md     # Docker containerization
│   ├── production_deployment.md # Production deployment guide
│   └── monitoring.md            # Monitoring and observability
├── development/                 # Development guides
│   ├── getting_started.md       # Developer onboarding
│   ├── coding_standards.md      # Code style and standards
│   ├── testing.md               # Testing strategies and practices
│   ├── test_cleanup_fix.md      # Test cleanup procedures
│   └── debugging.md             # Debugging and troubleshooting
└── tasks/                       # Task-specific documentation
    └── (task-specific context files)
```

## Guidelines

### 1. Organization
- **Logical Grouping**: Organize documentation by audience and purpose
- **Hierarchical Structure**: Use clear directory structure with descriptive names
- **Cross-References**: Link related documentation with relative paths
- **Version Control**: Track documentation changes alongside code changes
- **Searchability**: Use consistent terminology and keywords for easy searching

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for all documentation files
- **Consistent Format**: Use lowercase with underscores for file names
- **Category Prefixes**: Group related docs in subdirectories by category
- **Version Indicators**: Include version information where relevant
- **File Extensions**: Use .md for Markdown files consistently

### 3. Implementation
- **Markdown Format**: Use Markdown for all documentation with consistent formatting
- **Template Usage**: Use consistent templates for similar document types
- **Code Examples**: Include working, tested code examples
- **Diagrams**: Use diagrams and visual aids where helpful
- **Table of Contents**: Include TOC for longer documents

### 4. Documentation
- **Comprehensive Coverage**: Document all features, APIs, and processes
- **User-Focused**: Write from the user's perspective with clear use cases
- **Maintenance**: Keep documentation up-to-date with code changes
- **Review Process**: Include documentation in code review processes

## Best Practices

### 1. Error Handling
- **Troubleshooting Guides**: Include comprehensive troubleshooting sections
- **Error References**: Document common errors and their solutions
- **Recovery Procedures**: Provide step-by-step recovery instructions
- **Diagnostic Tools**: Document available diagnostic and debugging tools
- **Support Channels**: Clearly indicate where to get help

### 2. Security
- **Security Guidelines**: Document security best practices and requirements
- **Credential Management**: Provide secure credential handling instructions
- **Access Control**: Document authentication and authorization procedures
- **Vulnerability Reporting**: Include security vulnerability reporting process
- **Compliance**: Document compliance requirements and procedures

### 3. Performance
- **Performance Guidelines**: Document performance best practices
- **Optimization Guides**: Provide optimization strategies and techniques
- **Monitoring**: Document performance monitoring and metrics
- **Benchmarks**: Include performance benchmarks and expectations
- **Scaling**: Document scaling strategies and considerations

### 4. Testing
- **Testing Documentation**: Document testing strategies and procedures
- **Test Coverage**: Include information about test coverage requirements
- **Test Data**: Document test data requirements and setup
- **Continuous Integration**: Document CI/CD processes and requirements
- **Quality Assurance**: Include QA processes and standards

### 5. Documentation
- **Documentation Standards**: Follow consistent documentation standards
- **Review Process**: Include documentation in review processes
- **Update Procedures**: Document how to update and maintain documentation
- **Style Guide**: Maintain a consistent style guide for all documentation
- **Accessibility**: Ensure documentation is accessible to all users

## Example

### Complete API Documentation Template

```markdown
# SwarmDirector Agent API Reference

## Overview

The SwarmDirector Agent API provides comprehensive endpoints for managing AI agents within the hierarchical agent management system. This API supports agent creation, configuration, task assignment, and monitoring operations.

### Base URL
```
https://api.swarmdirector.com/v1
```

### Authentication
All API requests require authentication using API keys. Include your API key in the request header:

```http
Authorization: Bearer YOUR_API_KEY
```

### Rate Limiting
API requests are limited to 1000 requests per hour per API key. Rate limit information is included in response headers:

```http
X-RateLimit-Limit: 1000
X-RateLimit-Remaining: 999
X-RateLimit-Reset: 1640995200
```

## Agent Management

### Create Agent

Create a new agent in the SwarmDirector system.

**Endpoint:** `POST /agents`

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "agent_type": "supervisor|worker",
  "capabilities": {
    "key": "value"
  },
  "parent_id": "integer|null"
}
```

**Response:**
```json
{
  "id": 123,
  "name": "EmailAgent",
  "description": "Specialized agent for email operations",
  "agent_type": "worker",
  "status": "idle",
  "capabilities": {
    "email_handling": true,
    "smtp_integration": true
  },
  "parent_id": null,
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-01T10:00:00Z"
}
```

**Example Request:**
```bash
curl -X POST https://api.swarmdirector.com/v1/agents \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "EmailAgent",
    "description": "Specialized agent for email operations",
    "agent_type": "worker",
    "capabilities": {
      "email_handling": true,
      "smtp_integration": true
    }
  }'
```

**Python Example:**
```python
import requests

url = "https://api.swarmdirector.com/v1/agents"
headers = {
    "Authorization": "Bearer YOUR_API_KEY",
    "Content-Type": "application/json"
}
data = {
    "name": "EmailAgent",
    "description": "Specialized agent for email operations",
    "agent_type": "worker",
    "capabilities": {
        "email_handling": True,
        "smtp_integration": True
    }
}

response = requests.post(url, headers=headers, json=data)
agent = response.json()
print(f"Created agent: {agent['name']} (ID: {agent['id']})")
```

### Get Agent

Retrieve information about a specific agent.

**Endpoint:** `GET /agents/{agent_id}`

**Parameters:**
- `agent_id` (integer, required): The unique identifier of the agent

**Response:**
```json
{
  "id": 123,
  "name": "EmailAgent",
  "description": "Specialized agent for email operations",
  "agent_type": "worker",
  "status": "active",
  "capabilities": {
    "email_handling": true,
    "smtp_integration": true
  },
  "parent_id": null,
  "children": [],
  "assigned_tasks": [
    {
      "id": 456,
      "title": "Send Welcome Email",
      "status": "in_progress"
    }
  ],
  "performance_metrics": {
    "total_tasks": 25,
    "completed_tasks": 23,
    "success_rate": 0.92,
    "average_completion_time": 45.2
  },
  "created_at": "2023-12-01T10:00:00Z",
  "updated_at": "2023-12-01T10:30:00Z"
}
```

### List Agents

Retrieve a list of all agents with optional filtering.

**Endpoint:** `GET /agents`

**Query Parameters:**
- `agent_type` (string, optional): Filter by agent type (`supervisor`, `worker`)
- `status` (string, optional): Filter by status (`idle`, `active`, `busy`, `error`)
- `parent_id` (integer, optional): Filter by parent agent ID
- `page` (integer, optional): Page number for pagination (default: 1)
- `per_page` (integer, optional): Number of items per page (default: 20, max: 100)

**Response:**
```json
{
  "agents": [
    {
      "id": 123,
      "name": "EmailAgent",
      "agent_type": "worker",
      "status": "active"
    }
  ],
  "pagination": {
    "page": 1,
    "per_page": 20,
    "total": 1,
    "pages": 1
  }
}
```

### Update Agent

Update an existing agent's configuration.

**Endpoint:** `PUT /agents/{agent_id}`

**Request Body:**
```json
{
  "name": "string",
  "description": "string",
  "capabilities": {
    "key": "value"
  }
}
```

### Delete Agent

Delete an agent from the system.

**Endpoint:** `DELETE /agents/{agent_id}`

**Response:** `204 No Content`

## Task Assignment

### Assign Task to Agent

Assign a task to a specific agent.

**Endpoint:** `POST /agents/{agent_id}/tasks`

**Request Body:**
```json
{
  "task_id": 456
}
```

**Response:**
```json
{
  "message": "Task assigned successfully",
  "task_id": 456,
  "agent_id": 123,
  "assigned_at": "2023-12-01T10:45:00Z"
}
```

## Error Handling

The API uses standard HTTP status codes to indicate success or failure:

- `200 OK`: Request successful
- `201 Created`: Resource created successfully
- `204 No Content`: Request successful, no content returned
- `400 Bad Request`: Invalid request parameters
- `401 Unauthorized`: Authentication required
- `403 Forbidden`: Insufficient permissions
- `404 Not Found`: Resource not found
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

**Error Response Format:**
```json
{
  "error": {
    "code": "INVALID_AGENT_TYPE",
    "message": "Agent type must be 'supervisor' or 'worker'",
    "details": {
      "field": "agent_type",
      "provided_value": "invalid_type"
    }
  }
}
```

## SDK Examples

### Python SDK

```python
from swarm_director_sdk import SwarmDirectorClient

# Initialize client
client = SwarmDirectorClient(api_key="YOUR_API_KEY")

# Create agent
agent = client.agents.create(
    name="EmailAgent",
    description="Email handling agent",
    agent_type="worker",
    capabilities={
        "email_handling": True,
        "smtp_integration": True
    }
)

# Get agent
agent = client.agents.get(agent.id)

# List agents
agents = client.agents.list(agent_type="worker", status="active")

# Assign task
client.agents.assign_task(agent.id, task_id=456)
```

### JavaScript SDK

```javascript
import { SwarmDirectorClient } from 'swarmdirector-js';

// Initialize client
const client = new SwarmDirectorClient({ apiKey: 'YOUR_API_KEY' });

// Create agent
const agent = await client.agents.create({
  name: 'EmailAgent',
  description: 'Email handling agent',
  agentType: 'worker',
  capabilities: {
    emailHandling: true,
    smtpIntegration: true
  }
});

// Get agent
const retrievedAgent = await client.agents.get(agent.id);

// List agents
const agents = await client.agents.list({
  agentType: 'worker',
  status: 'active'
});
```

## Webhooks

SwarmDirector supports webhooks for real-time notifications of agent and task events.

### Webhook Events

- `agent.created`: Agent created
- `agent.updated`: Agent configuration updated
- `agent.status_changed`: Agent status changed
- `task.assigned`: Task assigned to agent
- `task.completed`: Task completed by agent
- `task.failed`: Task failed

### Webhook Payload

```json
{
  "event": "task.completed",
  "timestamp": "2023-12-01T10:45:00Z",
  "data": {
    "task_id": 456,
    "agent_id": 123,
    "status": "completed",
    "completion_time": 45.2
  }
}
```

## Rate Limits and Quotas

| Plan | Requests/Hour | Agents | Tasks/Day |
|------|---------------|--------|-----------|
| Free | 1,000 | 10 | 100 |
| Pro | 10,000 | 100 | 1,000 |
| Enterprise | 100,000 | Unlimited | Unlimited |

## Support

- **Documentation**: [https://docs.swarmdirector.com](https://docs.swarmdirector.com)
- **API Status**: [https://status.swarmdirector.com](https://status.swarmdirector.com)
- **Support Email**: support@swarmdirector.com
- **GitHub Issues**: [https://github.com/blopit/SwarmDirector/issues](https://github.com/blopit/SwarmDirector/issues)

## Changelog

### v2.0.0 (2023-12-01)
- Added hierarchical agent management
- Improved task routing algorithms
- Enhanced error handling and recovery
- Added webhook support

### v1.5.0 (2023-11-01)
- Added agent performance metrics
- Improved API rate limiting
- Enhanced authentication system

For complete changelog, see [CHANGELOG.md](../CHANGELOG.md).
```

### Documentation Maintenance Script

```python
#!/usr/bin/env python3
"""
Documentation maintenance and validation script
Ensures all documentation is up-to-date and follows standards
"""

import os
import re
import sys
from pathlib import Path
from typing import List, Dict, Set
import yaml
import markdown

class DocumentationValidator:
    """Validates and maintains documentation quality"""
    
    def __init__(self, docs_dir: Path):
        self.docs_dir = docs_dir
        self.errors = []
        self.warnings = []
    
    def validate_all(self) -> bool:
        """Validate all documentation"""
        print("🔍 Validating documentation...")
        
        # Check file structure
        self._validate_structure()
        
        # Check markdown files
        self._validate_markdown_files()
        
        # Check links
        self._validate_links()
        
        # Check code examples
        self._validate_code_examples()
        
        # Print results
        self._print_results()
        
        return len(self.errors) == 0
    
    def _validate_structure(self):
        """Validate documentation structure"""
        required_files = [
            'README.md',
            'CHANGELOG.md',
            'CONTRIBUTING.md',
            'PROJECT_STRUCTURE.md'
        ]
        
        for file in required_files:
            if not (self.docs_dir.parent / file).exists():
                self.errors.append(f"Missing required file: {file}")
    
    def _validate_markdown_files(self):
        """Validate markdown file format and content"""
        for md_file in self.docs_dir.rglob('*.md'):
            self._validate_markdown_file(md_file)
    
    def _validate_markdown_file(self, file_path: Path):
        """Validate individual markdown file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Check for required sections
            if file_path.name == 'README.md':
                required_sections = ['## Overview', '## Installation', '## Usage']
                for section in required_sections:
                    if section not in content:
                        self.warnings.append(f"{file_path}: Missing section {section}")
            
            # Check for broken markdown syntax
            try:
                markdown.markdown(content)
            except Exception as e:
                self.errors.append(f"{file_path}: Markdown syntax error: {e}")
                
        except Exception as e:
            self.errors.append(f"{file_path}: Could not read file: {e}")
    
    def _print_results(self):
        """Print validation results"""
        if self.errors:
            print(f"❌ Found {len(self.errors)} errors:")
            for error in self.errors:
                print(f"  - {error}")
        
        if self.warnings:
            print(f"⚠️  Found {len(self.warnings)} warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")
        
        if not self.errors and not self.warnings:
            print("✅ All documentation validation passed!")

if __name__ == '__main__':
    docs_dir = Path(__file__).parent
    validator = DocumentationValidator(docs_dir)
    success = validator.validate_all()
    sys.exit(0 if success else 1)
```

## Related Documentation
- [Project Structure](PROJECT_STRUCTURE.md) - Complete project organization
- [Contributing Guidelines](CONTRIBUTING.md) - How to contribute to documentation
- [API Documentation](api/README.md) - Complete API reference
- [Architecture Guide](architecture/overview.md) - System architecture overview
- [Development Guide](development/getting_started.md) - Developer documentation
