---
title: Schema Definitions Directory
description: Data validation schemas and API contracts for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [schemas, validation, api-contracts, data-models]
---

# Schema Definitions Directory

## Purpose

The schemas directory contains data validation schemas, API contracts, and data model definitions for SwarmDirector. This module ensures data consistency, API contract validation, and provides a single source of truth for data structures across the application.

## Structure

```
src/swarm_director/schemas/
├── __init__.py                  # Schema module initialization
├── task_schemas.py             # Task-related schema definitions
├── agent_schemas.py            # Agent-related schema definitions
├── conversation_schemas.py     # Conversation schema definitions
├── analytics_schemas.py        # Analytics data schemas
├── cost_schemas.py             # Cost tracking schemas
├── workflow_schemas.py         # Workflow state schemas
├── api/                        # API contract schemas
│   ├── request_schemas.py      # API request validation schemas
│   ├── response_schemas.py     # API response schemas
│   ├── error_schemas.py        # Error response schemas
│   └── webhook_schemas.py      # Webhook payload schemas
├── validation/                 # Custom validation logic
│   ├── validators.py           # Custom field validators
│   ├── business_rules.py       # Business logic validation
│   └── sanitizers.py           # Data sanitization utilities
└── serializers/                # Data serialization
    ├── json_serializers.py     # JSON serialization schemas
    ├── xml_serializers.py      # XML serialization schemas
    └── csv_serializers.py      # CSV export schemas
```

## Guidelines

### 1. Organization
- **Domain Separation**: Group schemas by business domain (tasks, agents, etc.)
- **API Contracts**: Separate API schemas from internal data models
- **Validation Logic**: Centralize custom validation logic
- **Serialization**: Provide consistent serialization formats

### 2. Naming
- **Schema Files**: Use `*_schemas.py` for schema definition files
- **Schema Classes**: Use descriptive names ending with `Schema` (e.g., `TaskCreateSchema`)
- **Validators**: Use `validate_*` prefix for custom validators
- **Serializers**: Use `*_serializer` suffix for serialization classes

### 3. Implementation
- **Pydantic Models**: Use Pydantic for schema definitions and validation
- **Type Hints**: Include comprehensive type hints for all fields
- **Documentation**: Document all schema fields with descriptions
- **Validation**: Implement both field-level and model-level validation
- **Backwards Compatibility**: Maintain backwards compatibility for API schemas

### 4. Documentation
- **Schema Documentation**: Document all schema fields and their purposes
- **Validation Rules**: Document validation rules and constraints
- **API Contracts**: Maintain API contract documentation
- **Migration Guides**: Document schema changes and migration paths

## Best Practices

### Error Handling
```python
from pydantic import BaseModel, validator, ValidationError
from typing import Optional, List
import logging

logger = logging.getLogger(__name__)

class TaskSchema(BaseModel):
    title: str
    description: Optional[str] = None
    priority: int
    assigned_agent_id: Optional[str] = None
    
    @validator('priority')
    def validate_priority(cls, v):
        if not 1 <= v <= 5:
            raise ValueError('Priority must be between 1 and 5')
        return v
    
    @validator('title')
    def validate_title(cls, v):
        if not v or len(v.strip()) == 0:
            raise ValueError('Title cannot be empty')
        if len(v) > 200:
            raise ValueError('Title cannot exceed 200 characters')
        return v.strip()
```

### Security
- **Input Sanitization**: Sanitize all input data to prevent injection attacks
- **Field Validation**: Validate all fields against expected formats and ranges
- **Sensitive Data**: Mark sensitive fields and handle them appropriately
- **Access Control**: Implement field-level access control where needed

### Performance
- **Lazy Validation**: Use lazy validation for expensive validation operations
- **Caching**: Cache compiled schema validators for better performance
- **Batch Validation**: Support batch validation for multiple records
- **Minimal Serialization**: Only serialize required fields

### Testing
```python
import pytest
from pydantic import ValidationError
from src.swarm_director.schemas.task_schemas import TaskCreateSchema

def test_valid_task_creation():
    # Test valid task creation
    task_data = {
        "title": "Test Task",
        "description": "A test task description",
        "priority": 3,
        "assigned_agent_id": "agent_001"
    }
    
    schema = TaskCreateSchema(**task_data)
    assert schema.title == "Test Task"
    assert schema.priority == 3

def test_invalid_priority():
    # Test invalid priority validation
    task_data = {
        "title": "Test Task",
        "priority": 10  # Invalid priority
    }
    
    with pytest.raises(ValidationError) as exc_info:
        TaskCreateSchema(**task_data)
    
    assert "Priority must be between 1 and 5" in str(exc_info.value)
```

### Documentation
- **Field Descriptions**: Include clear descriptions for all schema fields
- **Validation Rules**: Document all validation rules and constraints
- **Examples**: Provide examples of valid and invalid data
- **API Documentation**: Generate API documentation from schemas

## Examples

### Basic Schema Definition
```python
from pydantic import BaseModel, Field, validator
from typing import Optional, List
from datetime import datetime
from enum import Enum

class TaskStatus(str, Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"

class TaskSchema(BaseModel):
    """Schema for task data validation."""
    
    id: Optional[str] = Field(None, description="Unique task identifier")
    title: str = Field(..., min_length=1, max_length=200, description="Task title")
    description: Optional[str] = Field(None, max_length=1000, description="Task description")
    status: TaskStatus = Field(TaskStatus.PENDING, description="Current task status")
    priority: int = Field(..., ge=1, le=5, description="Task priority (1-5)")
    created_at: Optional[datetime] = Field(None, description="Task creation timestamp")
    updated_at: Optional[datetime] = Field(None, description="Last update timestamp")
    assigned_agent_id: Optional[str] = Field(None, description="Assigned agent ID")
    tags: List[str] = Field(default_factory=list, description="Task tags")
    
    @validator('tags')
    def validate_tags(cls, v):
        if len(v) > 10:
            raise ValueError('Maximum 10 tags allowed')
        return [tag.strip().lower() for tag in v if tag.strip()]
    
    class Config:
        use_enum_values = True
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }
```

### API Request Schema
```python
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any

class TaskCreateRequest(BaseModel):
    """Schema for task creation API requests."""
    
    title: str = Field(..., min_length=1, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)
    priority: int = Field(3, ge=1, le=5)
    assigned_agent_id: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)
    
    class Config:
        schema_extra = {
            "example": {
                "title": "Process customer inquiry",
                "description": "Handle customer inquiry about product features",
                "priority": 2,
                "assigned_agent_id": "agent_customer_service",
                "metadata": {
                    "customer_id": "cust_123",
                    "inquiry_type": "product_question"
                }
            }
        }
```

### Custom Validator
```python
from pydantic import BaseModel, validator
import re

class AgentConfigSchema(BaseModel):
    name: str
    model: str
    max_tokens: int
    temperature: float
    
    @validator('name')
    def validate_agent_name(cls, v):
        if not re.match(r'^[a-zA-Z0-9_-]+$', v):
            raise ValueError('Agent name must contain only alphanumeric characters, hyphens, and underscores')
        return v
    
    @validator('temperature')
    def validate_temperature(cls, v):
        if not 0.0 <= v <= 2.0:
            raise ValueError('Temperature must be between 0.0 and 2.0')
        return v
    
    @validator('max_tokens')
    def validate_max_tokens(cls, v):
        if v <= 0 or v > 32000:
            raise ValueError('Max tokens must be between 1 and 32000')
        return v
```

## Related Documentation

- [API Documentation](../../docs/api/README.md) - API contract documentation
- [Data Models](../models/README.md) - Database model documentation
- [Validation Guide](../../docs/development/validation.md) - Data validation guide
- [API Design Guide](../../docs/development/api_design.md) - API design principles
- [Schema Migration](../../docs/development/schema_migration.md) - Schema migration guide
- [Testing Schemas](../../docs/development/testing_schemas.md) - Schema testing guide
