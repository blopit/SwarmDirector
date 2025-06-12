# Models Directory

## Purpose
Contains the complete database model definitions for the SwarmDirector system using SQLAlchemy ORM. This directory defines the data structures for agents, tasks, conversations, and all related entities that support the hierarchical AI agent management system with proper relationships, constraints, and business logic.

## Structure
```
models/
├── __init__.py                  # Model package exports and database instance
├── base.py                      # Base model class with common functionality
├── agent.py                     # Agent model with hierarchical relationships
├── task.py                      # Task model with dependencies and workflow
├── conversation.py              # Conversation and message models
├── draft.py                     # Draft content model for review workflows
├── email_message.py             # Email message model with delivery tracking
└── agent_log.py                 # Agent activity logging and audit trail
```

## Guidelines

### 1. Organization
- **Base Model Inheritance**: All models must inherit from `BaseModel` for common functionality
- **Relationship Definitions**: Define clear relationships between models using SQLAlchemy
- **Index Strategy**: Create appropriate database indexes for query performance
- **Migration Support**: Design models to support database migrations and schema evolution
- **Data Integrity**: Use constraints and validations to ensure data consistency

### 2. Naming
- **Model Classes**: Use singular PascalCase names (e.g., `Agent`, `Task`, `Conversation`)
- **Table Names**: Use plural snake_case for table names (e.g., `agents`, `tasks`, `conversations`)
- **Column Names**: Use snake_case for column names (e.g., `created_at`, `agent_type`)
- **Relationship Names**: Use descriptive names for relationships (e.g., `assigned_agent`, `parent_task`)
- **Enum Values**: Use UPPER_CASE for enum values (e.g., `PENDING`, `COMPLETED`, `FAILED`)

### 3. Implementation
- **Type Annotations**: Use comprehensive type hints for all model attributes
- **Validation**: Implement model-level validation using SQLAlchemy validators
- **Serialization**: Provide `to_dict()` methods for API serialization
- **Business Logic**: Include domain-specific methods in model classes
- **Audit Fields**: Include created_at, updated_at fields in all models

### 4. Documentation
- **Model Docstrings**: Document model purpose, relationships, and usage patterns
- **Field Documentation**: Document all fields with their purpose and constraints
- **Relationship Documentation**: Explain relationship semantics and usage
- **Example Usage**: Provide examples of common model operations

## Best Practices

### 1. Error Handling
- **Constraint Violations**: Handle database constraint violations gracefully
- **Validation Errors**: Provide clear error messages for validation failures
- **Transaction Management**: Use proper transaction boundaries for data consistency
- **Rollback Strategies**: Implement rollback mechanisms for failed operations
- **Integrity Checks**: Validate data integrity before and after operations

### 2. Security
- **Input Sanitization**: Sanitize all inputs before database operations
- **SQL Injection Prevention**: Use SQLAlchemy ORM exclusively for queries
- **Access Control**: Implement model-level access control where appropriate
- **Sensitive Data**: Handle sensitive data with proper encryption and masking
- **Audit Logging**: Log all data modifications for security auditing

### 3. Performance
- **Query Optimization**: Design efficient queries with proper joins and indexes
- **Lazy Loading**: Use appropriate loading strategies for relationships
- **Bulk Operations**: Implement bulk insert/update operations for large datasets
- **Connection Pooling**: Configure appropriate database connection pooling
- **Query Monitoring**: Monitor and optimize slow queries

### 4. Testing
- **Model Tests**: Test all model methods and relationships
- **Constraint Tests**: Test database constraints and validations
- **Migration Tests**: Test database migrations and schema changes
- **Performance Tests**: Include benchmarks for critical operations
- **Data Integrity Tests**: Test referential integrity and cascading operations

### 5. Documentation
- **Schema Documentation**: Maintain up-to-date database schema documentation
- **Relationship Diagrams**: Include ERD diagrams showing model relationships
- **Migration Guides**: Document database migration procedures
- **API Examples**: Provide examples of model usage in API contexts

## Example

### Complete Model Implementation with Relationships

```python
"""
Example: Comprehensive Task Model Implementation
Demonstrates advanced model design with relationships, validation, and business logic
"""

from sqlalchemy import Column, Integer, String, Text, DateTime, JSON, Enum, ForeignKey, Index
from sqlalchemy.orm import relationship, validates
from sqlalchemy.ext.hybrid import hybrid_property
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import enum

from .base import BaseModel, db

class TaskStatus(enum.Enum):
    """Task status enumeration"""
    PENDING = "pending"
    ASSIGNED = "assigned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class TaskPriority(enum.Enum):
    """Task priority enumeration"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    URGENT = 4
    CRITICAL = 5

class Task(BaseModel):
    """
    Task model representing work items in the SwarmDirector system
    
    This model supports hierarchical task structures, agent assignment,
    dependency management, and comprehensive workflow tracking.
    
    Relationships:
        - assigned_agent: Agent responsible for task execution
        - parent_task: Parent task for hierarchical organization
        - subtasks: Child tasks that depend on this task
        - conversations: Communication threads related to this task
        - drafts: Content drafts created for this task
        - email_messages: Email communications for this task
        - agent_logs: Agent activity logs for this task
    
    Attributes:
        title: Short descriptive title for the task
        description: Detailed task description and requirements
        task_type: Category of task (communication, research, analysis, etc.)
        priority: Task priority level (1-5, with 5 being critical)
        status: Current task status
        estimated_duration: Estimated completion time in minutes
        actual_duration: Actual completion time in minutes
        deadline: Task deadline timestamp
        input_data: Task parameters and input data (JSON)
        output_data: Task results and output data (JSON)
        error_details: Error information if task failed
    """
    __tablename__ = 'tasks'
    
    # Basic task information
    title = Column(String(200), nullable=False, index=True)
    description = Column(Text)
    task_type = Column(String(50), nullable=False, index=True)
    priority = Column(Enum(TaskPriority), nullable=False, default=TaskPriority.NORMAL, index=True)
    status = Column(Enum(TaskStatus), nullable=False, default=TaskStatus.PENDING, index=True)
    
    # Task assignment
    assigned_agent_id = Column(Integer, ForeignKey('agents.id'), nullable=True, index=True)
    assigned_agent = relationship('Agent', backref='assigned_tasks', foreign_keys=[assigned_agent_id])
    
    # Task hierarchy and dependencies
    parent_task_id = Column(Integer, ForeignKey('tasks.id'), nullable=True, index=True)
    parent_task = relationship('Task', remote_side='Task.id', backref='subtasks')
    
    # Task timing
    estimated_duration = Column(Integer)  # In minutes
    actual_duration = Column(Integer)  # In minutes
    deadline = Column(DateTime, index=True)
    started_at = Column(DateTime)
    completed_at = Column(DateTime)
    
    # Task data
    input_data = Column(JSON)  # Input parameters for the task
    output_data = Column(JSON)  # Results of the task execution
    error_details = Column(Text)  # Error information if task failed
    
    # Metadata
    tags = Column(JSON)  # Task tags for categorization
    metadata = Column(JSON)  # Additional metadata
    
    # Database indexes for performance
    __table_args__ = (
        Index('idx_task_status_priority', 'status', 'priority'),
        Index('idx_task_type_status', 'task_type', 'status'),
        Index('idx_task_agent_status', 'assigned_agent_id', 'status'),
        Index('idx_task_deadline', 'deadline'),
    )
    
    @validates('priority')
    def validate_priority(self, key, priority):
        """Validate task priority"""
        if isinstance(priority, int):
            if 1 <= priority <= 5:
                return TaskPriority(priority)
            else:
                raise ValueError("Priority must be between 1 and 5")
        return priority
    
    @validates('estimated_duration')
    def validate_estimated_duration(self, key, duration):
        """Validate estimated duration"""
        if duration is not None and duration <= 0:
            raise ValueError("Estimated duration must be positive")
        return duration
    
    @validates('deadline')
    def validate_deadline(self, key, deadline):
        """Validate task deadline"""
        if deadline is not None and deadline <= datetime.utcnow():
            raise ValueError("Deadline must be in the future")
        return deadline
    
    @hybrid_property
    def is_overdue(self) -> bool:
        """Check if task is overdue"""
        return (
            self.deadline is not None and 
            self.deadline < datetime.utcnow() and 
            self.status not in [TaskStatus.COMPLETED, TaskStatus.CANCELLED]
        )
    
    @hybrid_property
    def is_completed(self) -> bool:
        """Check if task is completed"""
        return self.status == TaskStatus.COMPLETED
    
    @hybrid_property
    def duration_minutes(self) -> Optional[int]:
        """Get actual task duration in minutes"""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            return int(delta.total_seconds() / 60)
        return None
    
    def assign_to_agent(self, agent) -> None:
        """
        Assign task to an agent
        
        Args:
            agent: Agent instance to assign task to
            
        Raises:
            ValueError: If agent cannot handle this task type
        """
        from .agent import AgentStatus
        
        if not agent.is_available():
            raise ValueError(f"Agent {agent.name} is not available")
        
        self.assigned_agent_id = agent.id
        self.status = TaskStatus.ASSIGNED
        agent.status = AgentStatus.BUSY
        
        self.save()
        agent.save()
    
    def start_execution(self) -> None:
        """Mark task as started"""
        if self.status != TaskStatus.ASSIGNED:
            raise ValueError("Task must be assigned before starting")
        
        self.status = TaskStatus.IN_PROGRESS
        self.started_at = datetime.utcnow()
        self.save()
    
    def complete_task(self, output_data: Optional[Dict[str, Any]] = None) -> None:
        """
        Mark task as completed
        
        Args:
            output_data: Task output data
        """
        if self.status != TaskStatus.IN_PROGRESS:
            raise ValueError("Task must be in progress to complete")
        
        self.status = TaskStatus.COMPLETED
        self.completed_at = datetime.utcnow()
        
        if output_data:
            self.output_data = output_data
        
        # Calculate actual duration
        if self.started_at:
            duration = self.completed_at - self.started_at
            self.actual_duration = int(duration.total_seconds() / 60)
        
        # Free up assigned agent
        if self.assigned_agent:
            from .agent import AgentStatus
            self.assigned_agent.status = AgentStatus.IDLE
            self.assigned_agent.save()
        
        self.save()
    
    def fail_task(self, error_details: str) -> None:
        """
        Mark task as failed
        
        Args:
            error_details: Error description
        """
        self.status = TaskStatus.FAILED
        self.error_details = error_details
        self.completed_at = datetime.utcnow()
        
        # Free up assigned agent
        if self.assigned_agent:
            from .agent import AgentStatus
            self.assigned_agent.status = AgentStatus.IDLE
            self.assigned_agent.save()
        
        self.save()
    
    def add_subtask(self, subtask_data: Dict[str, Any]) -> 'Task':
        """
        Create and add a subtask
        
        Args:
            subtask_data: Subtask configuration
            
        Returns:
            Created subtask instance
        """
        subtask = Task(
            title=subtask_data['title'],
            description=subtask_data.get('description'),
            task_type=subtask_data.get('task_type', self.task_type),
            priority=subtask_data.get('priority', self.priority),
            parent_task_id=self.id,
            input_data=subtask_data.get('input_data', {}),
            estimated_duration=subtask_data.get('estimated_duration')
        )
        subtask.save()
        return subtask
    
    def get_progress_percentage(self) -> float:
        """
        Calculate task progress percentage based on subtasks
        
        Returns:
            Progress percentage (0.0 to 100.0)
        """
        if not self.subtasks:
            # No subtasks, use status-based progress
            status_progress = {
                TaskStatus.PENDING: 0.0,
                TaskStatus.ASSIGNED: 10.0,
                TaskStatus.IN_PROGRESS: 50.0,
                TaskStatus.COMPLETED: 100.0,
                TaskStatus.FAILED: 0.0,
                TaskStatus.CANCELLED: 0.0
            }
            return status_progress.get(self.status, 0.0)
        
        # Calculate based on subtask completion
        completed_subtasks = sum(1 for subtask in self.subtasks if subtask.is_completed)
        return (completed_subtasks / len(self.subtasks)) * 100.0
    
    def to_dict(self, include_relationships: bool = False) -> Dict[str, Any]:
        """
        Convert task to dictionary for API serialization
        
        Args:
            include_relationships: Whether to include related objects
            
        Returns:
            Dictionary representation of the task
        """
        result = {
            'id': self.id,
            'title': self.title,
            'description': self.description,
            'task_type': self.task_type,
            'priority': self.priority.value if self.priority else None,
            'status': self.status.value if self.status else None,
            'estimated_duration': self.estimated_duration,
            'actual_duration': self.actual_duration,
            'deadline': self.deadline.isoformat() if self.deadline else None,
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'input_data': self.input_data,
            'output_data': self.output_data,
            'error_details': self.error_details,
            'tags': self.tags,
            'metadata': self.metadata,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'is_overdue': self.is_overdue,
            'progress_percentage': self.get_progress_percentage()
        }
        
        if include_relationships:
            result.update({
                'assigned_agent': self.assigned_agent.to_dict() if self.assigned_agent else None,
                'parent_task_id': self.parent_task_id,
                'subtask_count': len(self.subtasks),
                'conversation_count': len(self.conversations) if hasattr(self, 'conversations') else 0
            })
        
        return result
    
    @classmethod
    def get_pending_tasks(cls, agent_id: Optional[int] = None) -> List['Task']:
        """
        Get pending tasks, optionally filtered by agent
        
        Args:
            agent_id: Optional agent ID to filter by
            
        Returns:
            List of pending tasks
        """
        query = cls.query.filter_by(status=TaskStatus.PENDING)
        
        if agent_id:
            query = query.filter_by(assigned_agent_id=agent_id)
        
        return query.order_by(cls.priority.desc(), cls.created_at.asc()).all()
    
    @classmethod
    def get_overdue_tasks(cls) -> List['Task']:
        """Get all overdue tasks"""
        return cls.query.filter(
            cls.deadline < datetime.utcnow(),
            cls.status.notin_([TaskStatus.COMPLETED, TaskStatus.CANCELLED])
        ).all()
    
    def __repr__(self) -> str:
        return f"<Task(id={self.id}, title='{self.title}', status='{self.status.value}')>"
```

### Model Factory and Utilities

```python
"""
Task model utilities and factory functions
"""

from typing import Dict, Any, List
from datetime import datetime, timedelta

def create_task(
    title: str,
    description: str,
    task_type: str,
    priority: int = 2,
    deadline_hours: Optional[int] = None,
    input_data: Optional[Dict[str, Any]] = None,
    assigned_agent_id: Optional[int] = None
) -> Task:
    """
    Factory function to create a task with validation
    
    Args:
        title: Task title
        description: Task description
        task_type: Type of task
        priority: Task priority (1-5)
        deadline_hours: Hours from now for deadline
        input_data: Task input data
        assigned_agent_id: Agent to assign task to
        
    Returns:
        Created task instance
    """
    deadline = None
    if deadline_hours:
        deadline = datetime.utcnow() + timedelta(hours=deadline_hours)
    
    task = Task(
        title=title,
        description=description,
        task_type=task_type,
        priority=TaskPriority(priority),
        deadline=deadline,
        input_data=input_data or {},
        assigned_agent_id=assigned_agent_id
    )
    
    task.save()
    return task

def bulk_create_tasks(task_configs: List[Dict[str, Any]]) -> List[Task]:
    """
    Create multiple tasks efficiently
    
    Args:
        task_configs: List of task configuration dictionaries
        
    Returns:
        List of created task instances
    """
    tasks = []
    
    for config in task_configs:
        task = Task(**config)
        tasks.append(task)
    
    # Bulk insert
    db.session.add_all(tasks)
    db.session.commit()
    
    return tasks
```

## Related Documentation
- [Base Model Class](../../../docs/api/models.md#base-model) - Common model functionality
- [Database Schema](../../../database/schemas/database_schema_documented.sql) - Complete schema documentation
- [Agent Model](../../../docs/api/agents.md#agent-model) - Agent model documentation
- [Migration Guide](../../../docs/deployment/local_development.md#database-migrations) - Database migration procedures
- [API Serialization](../../../docs/api/README.md#response-format) - Model serialization patterns
