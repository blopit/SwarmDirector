"""
JSON schemas for task validation in SwarmDirector API
Defines validation rules for different task types and constraints
"""

# Base task schema that all tasks must conform to
BASE_TASK_SCHEMA = {
    "type": "object",
    "properties": {
        "type": {
            "type": "string",
            "pattern": "^[a-zA-Z0-9_-]{1,50}$",
            "description": "Task type identifier (alphanumeric, underscore, hyphen only)"
        },
        "title": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Human-readable task title"
        },
        "description": {
            "type": "string",
            "maxLength": 1000,
            "description": "Detailed task description"
        },
        "priority": {
            "type": "string",
            "enum": ["low", "medium", "high", "critical"],
            "default": "medium",
            "description": "Task priority level"
        },
        "args": {
            "type": "object",
            "description": "Task-specific arguments and parameters"
        },
        "metadata": {
            "type": "object",
            "description": "Additional metadata for the task"
        },
        "timeout": {
            "type": "integer",
            "minimum": 1,
            "maximum": 3600,
            "description": "Task timeout in seconds (1 second to 1 hour)"
        },
        "retries": {
            "type": "integer",
            "minimum": 0,
            "maximum": 5,
            "description": "Number of retries if task fails"
        }
    },
    "required": ["type"],
    "additionalProperties": True
}

# Communication task schema
COMMUNICATION_TASK_SCHEMA = {
    "allOf": [
        BASE_TASK_SCHEMA,
        {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["communication", "email", "notification", "message"]
                },
                "args": {
                    "type": "object",
                    "properties": {
                        "recipient": {
                            "type": "string",
                            "description": "Message recipient (email, phone, user ID)"
                        },
                        "subject": {
                            "type": "string",
                            "maxLength": 200,
                            "description": "Message subject line"
                        },
                        "content": {
                            "type": "string",
                            "maxLength": 5000,
                            "description": "Message content"
                        },
                        "template": {
                            "type": "string",
                            "description": "Template to use for message"
                        },
                        "channel": {
                            "type": "string",
                            "enum": ["email", "sms", "slack", "teams", "webhook"],
                            "description": "Communication channel"
                        }
                    },
                    "required": ["recipient"],
                    "additionalProperties": True
                }
            }
        }
    ]
}

# Analysis task schema
ANALYSIS_TASK_SCHEMA = {
    "allOf": [
        BASE_TASK_SCHEMA,
        {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["analysis", "report", "data_analysis", "research"]
                },
                "args": {
                    "type": "object",
                    "properties": {
                        "data_source": {
                            "type": "string",
                            "description": "Source of data to analyze"
                        },
                        "analysis_type": {
                            "type": "string",
                            "enum": ["statistical", "predictive", "descriptive", "comparative"],
                            "description": "Type of analysis to perform"
                        },
                        "filters": {
                            "type": "object",
                            "description": "Filters to apply to the data"
                        },
                        "output_format": {
                            "type": "string",
                            "enum": ["json", "csv", "pdf", "html"],
                            "default": "json",
                            "description": "Format for analysis output"
                        },
                        "parameters": {
                            "type": "object",
                            "description": "Analysis-specific parameters"
                        }
                    },
                    "required": ["data_source"],
                    "additionalProperties": True
                }
            }
        }
    ]
}

# Automation task schema
AUTOMATION_TASK_SCHEMA = {
    "allOf": [
        BASE_TASK_SCHEMA,
        {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["automation", "workflow", "process", "script"]
                },
                "args": {
                    "type": "object",
                    "properties": {
                        "workflow_id": {
                            "type": "string",
                            "description": "Identifier for the workflow to execute"
                        },
                        "steps": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "action": {"type": "string"},
                                    "parameters": {"type": "object"}
                                },
                                "required": ["action"]
                            },
                            "description": "Steps in the automation workflow"
                        },
                        "condition": {
                            "type": "object",
                            "description": "Conditions that must be met to execute"
                        },
                        "schedule": {
                            "type": "string",
                            "description": "Cron expression for scheduled execution"
                        }
                    },
                    "additionalProperties": True
                }
            }
        }
    ]
}

# Coordination task schema
COORDINATION_TASK_SCHEMA = {
    "allOf": [
        BASE_TASK_SCHEMA,
        {
            "type": "object",
            "properties": {
                "type": {
                    "enum": ["coordination", "orchestration", "delegation", "management"]
                },
                "args": {
                    "type": "object",
                    "properties": {
                        "subtasks": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "type": {"type": "string"},
                                    "args": {"type": "object"},
                                    "agent": {"type": "string"}
                                },
                                "required": ["type"]
                            },
                            "description": "Subtasks to coordinate"
                        },
                        "execution_mode": {
                            "type": "string",
                            "enum": ["sequential", "parallel", "conditional"],
                            "default": "sequential",
                            "description": "How to execute subtasks"
                        },
                        "dependencies": {
                            "type": "object",
                            "description": "Dependencies between subtasks"
                        },
                        "aggregation_strategy": {
                            "type": "string",
                            "enum": ["merge", "select_best", "consensus", "custom"],
                            "default": "merge",
                            "description": "How to combine results"
                        }
                    },
                    "additionalProperties": True
                }
            }
        }
    ]
}

# Generic task schema (fallback for unknown types)
GENERIC_TASK_SCHEMA = BASE_TASK_SCHEMA

# Schema registry mapping task types to their schemas
TASK_SCHEMAS = {
    "communication": COMMUNICATION_TASK_SCHEMA,
    "email": COMMUNICATION_TASK_SCHEMA,
    "notification": COMMUNICATION_TASK_SCHEMA,
    "message": COMMUNICATION_TASK_SCHEMA,
    
    "analysis": ANALYSIS_TASK_SCHEMA,
    "report": ANALYSIS_TASK_SCHEMA,
    "data_analysis": ANALYSIS_TASK_SCHEMA,
    "research": ANALYSIS_TASK_SCHEMA,
    
    "automation": AUTOMATION_TASK_SCHEMA,
    "workflow": AUTOMATION_TASK_SCHEMA,
    "process": AUTOMATION_TASK_SCHEMA,
    "script": AUTOMATION_TASK_SCHEMA,
    
    "coordination": COORDINATION_TASK_SCHEMA,
    "orchestration": COORDINATION_TASK_SCHEMA,
    "delegation": COORDINATION_TASK_SCHEMA,
    "management": COORDINATION_TASK_SCHEMA,
}

def get_schema_for_task_type(task_type: str) -> dict:
    """
    Get the appropriate JSON schema for a given task type
    
    Args:
        task_type: The type of task to get schema for
        
    Returns:
        JSON schema dict for validation
    """
    return TASK_SCHEMAS.get(task_type, GENERIC_TASK_SCHEMA)

def validate_task_structure(task_data: dict) -> tuple[bool, str]:
    """
    Validate basic task structure before detailed schema validation
    
    Args:
        task_data: Task data to validate
        
    Returns:
        Tuple of (is_valid, error_message)
    """
    if not isinstance(task_data, dict):
        return False, "Task data must be a JSON object"
    
    if 'type' not in task_data:
        return False, "Task must have a 'type' field"
    
    task_type = task_data.get('type')
    if not isinstance(task_type, str):
        return False, "Task 'type' must be a string"
    
    if len(task_type) == 0:
        return False, "Task 'type' cannot be empty"
    
    if len(task_type) > 50:
        return False, "Task 'type' must be 50 characters or less"
    
    return True, "" 