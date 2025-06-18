---
title: Database Schema Directory
description: Database schema definitions and documentation for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [database-schema, sql, documentation, data-model]
---

# Database Schema Directory

## Purpose

The database/schemas directory contains database schema definitions, documentation, and reference materials for SwarmDirector. This directory serves as the authoritative source for database structure documentation, providing comprehensive schema definitions, relationships, and constraints for all database tables and views.

## Structure

```
database/schemas/
├── database_schema.sql          # Complete database schema definition
├── database_schema_documented.sql # Schema with comprehensive documentation
├── schema.sql                   # Core schema definition
├── tables/                      # Individual table definitions
│   ├── agents.sql               # Agent table schema
│   ├── tasks.sql                # Task table schema
│   ├── conversations.sql        # Conversation table schema
│   ├── analytics.sql            # Analytics table schema
│   ├── cost_tracking.sql        # Cost tracking table schema
│   ├── workflow_state.sql       # Workflow state table schema
│   └── user_management.sql      # User management table schema
├── views/                       # Database view definitions
│   ├── agent_performance.sql    # Agent performance view
│   ├── task_analytics.sql       # Task analytics view
│   ├── cost_summary.sql         # Cost summary view
│   └── conversation_metrics.sql # Conversation metrics view
├── indexes/                     # Index definitions
│   ├── performance_indexes.sql  # Performance optimization indexes
│   ├── foreign_key_indexes.sql  # Foreign key indexes
│   └── search_indexes.sql       # Full-text search indexes
├── constraints/                 # Constraint definitions
│   ├── foreign_keys.sql         # Foreign key constraints
│   ├── check_constraints.sql    # Check constraints
│   └── unique_constraints.sql   # Unique constraints
├── triggers/                    # Database trigger definitions
│   ├── audit_triggers.sql       # Audit logging triggers
│   ├── timestamp_triggers.sql   # Timestamp update triggers
│   └── validation_triggers.sql  # Data validation triggers
└── documentation/               # Schema documentation
    ├── entity_relationship.md   # Entity relationship documentation
    ├── data_dictionary.md       # Data dictionary
    ├── schema_changelog.md      # Schema change history
    └── performance_notes.md     # Performance considerations
```

## Guidelines

### 1. Organization
- **Modular Structure**: Separate schema components by type (tables, views, indexes)
- **Documentation**: Maintain comprehensive documentation for all schema elements
- **Version Control**: Track schema changes and evolution over time
- **Consistency**: Ensure consistent naming and design patterns

### 2. Naming
- **Tables**: Use singular nouns for table names (e.g., `agent`, `task`)
- **Columns**: Use descriptive names with underscores (e.g., `created_at`, `agent_id`)
- **Indexes**: Use descriptive prefixes (`idx_`, `uk_`, `fk_`)
- **Constraints**: Use descriptive constraint names with prefixes

### 3. Implementation
- **Data Types**: Use appropriate data types for each column
- **Constraints**: Implement proper constraints for data integrity
- **Indexes**: Create indexes for performance optimization
- **Documentation**: Include inline comments and external documentation
- **Standards**: Follow SQL standards and best practices

### 4. Documentation
- **Schema Documentation**: Document all tables, columns, and relationships
- **Data Dictionary**: Maintain a comprehensive data dictionary
- **Change Log**: Track all schema changes and their rationale
- **Performance Notes**: Document performance considerations and optimizations

## Best Practices

### Schema Design
```sql
-- agents.sql - Agent table schema with comprehensive documentation

-- Agents table stores information about AI agents in the system
CREATE TABLE agents (
    -- Primary key: Unique identifier for each agent
    id TEXT PRIMARY KEY,
    
    -- Agent identification and metadata
    name TEXT NOT NULL CHECK (length(name) > 0),
    type TEXT NOT NULL CHECK (type IN ('director', 'worker', 'specialist')),
    description TEXT,
    
    -- Agent configuration and capabilities
    config TEXT, -- JSON configuration data
    capabilities TEXT, -- JSON array of agent capabilities
    model_config TEXT, -- JSON model configuration
    
    -- Agent status and lifecycle
    status TEXT NOT NULL DEFAULT 'inactive' 
        CHECK (status IN ('active', 'inactive', 'maintenance', 'error')),
    version TEXT NOT NULL DEFAULT '1.0.0',
    
    -- Performance and monitoring
    performance_score REAL DEFAULT 0.0 CHECK (performance_score >= 0.0 AND performance_score <= 1.0),
    total_tasks_completed INTEGER DEFAULT 0 CHECK (total_tasks_completed >= 0),
    average_response_time REAL DEFAULT 0.0 CHECK (average_response_time >= 0.0),
    
    -- Audit and tracking
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    last_activity_at TIMESTAMP,
    
    -- Soft delete support
    deleted_at TIMESTAMP NULL,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE
);

-- Indexes for performance optimization
CREATE INDEX idx_agents_type ON agents (type);
CREATE INDEX idx_agents_status ON agents (status);
CREATE INDEX idx_agents_created_at ON agents (created_at);
CREATE INDEX idx_agents_performance ON agents (performance_score DESC);
CREATE INDEX idx_agents_active ON agents (id) WHERE status = 'active' AND is_deleted = FALSE;

-- Comments for documentation
COMMENT ON TABLE agents IS 'Stores information about AI agents in the SwarmDirector system';
COMMENT ON COLUMN agents.id IS 'Unique identifier for the agent (UUID format)';
COMMENT ON COLUMN agents.name IS 'Human-readable name for the agent';
COMMENT ON COLUMN agents.type IS 'Agent type: director (orchestrates), worker (executes), specialist (domain-specific)';
COMMENT ON COLUMN agents.config IS 'JSON configuration including model parameters, prompts, and settings';
COMMENT ON COLUMN agents.capabilities IS 'JSON array of agent capabilities and skills';
COMMENT ON COLUMN agents.performance_score IS 'Calculated performance score from 0.0 to 1.0';
```

### Security
- **Access Control**: Implement proper access controls for schema objects
- **Data Encryption**: Use encryption for sensitive data columns
- **Audit Trails**: Implement audit trails for schema changes
- **Input Validation**: Use constraints and triggers for data validation

### Performance
- **Indexing Strategy**: Create appropriate indexes for query patterns
- **Partitioning**: Consider partitioning for large tables
- **Query Optimization**: Design schema for optimal query performance
- **Statistics**: Maintain up-to-date table statistics

### Testing
```sql
-- Test data validation constraints
-- This would be part of a test suite

-- Test valid agent creation
INSERT INTO agents (id, name, type, status) 
VALUES ('test-agent-001', 'Test Agent', 'worker', 'active');

-- Test constraint violations
-- This should fail due to invalid type
INSERT INTO agents (id, name, type) 
VALUES ('test-agent-002', 'Invalid Agent', 'invalid_type');

-- Test check constraints
-- This should fail due to negative performance score
UPDATE agents 
SET performance_score = -0.5 
WHERE id = 'test-agent-001';

-- Clean up test data
DELETE FROM agents WHERE id LIKE 'test-agent-%';
```

### Documentation Standards
- **Table Documentation**: Document purpose and usage of each table
- **Column Documentation**: Document data types, constraints, and business rules
- **Relationship Documentation**: Document foreign key relationships and dependencies
- **Index Documentation**: Document index purposes and performance impact

## Examples

### Complete Table Definition
```sql
-- tasks.sql - Task table with full documentation and constraints

CREATE TABLE tasks (
    -- Primary identification
    id TEXT PRIMARY KEY,
    
    -- Task content and metadata
    title TEXT NOT NULL CHECK (length(trim(title)) > 0),
    description TEXT,
    instructions TEXT, -- Detailed instructions for task execution
    
    -- Task classification and priority
    category TEXT DEFAULT 'general' CHECK (category IN ('general', 'analysis', 'communication', 'processing')),
    priority INTEGER NOT NULL DEFAULT 3 CHECK (priority >= 1 AND priority <= 5),
    complexity_score REAL DEFAULT 1.0 CHECK (complexity_score >= 0.1 AND complexity_score <= 10.0),
    
    -- Task status and lifecycle
    status TEXT NOT NULL DEFAULT 'pending' 
        CHECK (status IN ('pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled')),
    progress_percentage INTEGER DEFAULT 0 CHECK (progress_percentage >= 0 AND progress_percentage <= 100),
    
    -- Assignment and execution
    assigned_agent_id TEXT,
    assigned_at TIMESTAMP,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    
    -- Task results and output
    result TEXT, -- JSON result data
    output_data TEXT, -- JSON output data
    error_message TEXT,
    
    -- Performance metrics
    estimated_duration INTEGER, -- Estimated duration in seconds
    actual_duration INTEGER, -- Actual duration in seconds
    retry_count INTEGER DEFAULT 0 CHECK (retry_count >= 0),
    max_retries INTEGER DEFAULT 3 CHECK (max_retries >= 0),
    
    -- Dependencies and relationships
    parent_task_id TEXT,
    workflow_id TEXT,
    conversation_id TEXT,
    
    -- Audit and tracking
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    created_by TEXT,
    
    -- Soft delete
    deleted_at TIMESTAMP,
    is_deleted BOOLEAN NOT NULL DEFAULT FALSE,
    
    -- Foreign key constraints
    FOREIGN KEY (assigned_agent_id) REFERENCES agents (id),
    FOREIGN KEY (parent_task_id) REFERENCES tasks (id),
    FOREIGN KEY (conversation_id) REFERENCES conversations (id),
    
    -- Check constraints for business logic
    CHECK (
        (status = 'completed' AND completed_at IS NOT NULL) OR 
        (status != 'completed')
    ),
    CHECK (
        (assigned_agent_id IS NOT NULL AND assigned_at IS NOT NULL) OR 
        (assigned_agent_id IS NULL AND assigned_at IS NULL)
    ),
    CHECK (started_at IS NULL OR assigned_at IS NULL OR started_at >= assigned_at),
    CHECK (completed_at IS NULL OR started_at IS NULL OR completed_at >= started_at)
);

-- Performance indexes
CREATE INDEX idx_tasks_status ON tasks (status) WHERE is_deleted = FALSE;
CREATE INDEX idx_tasks_priority ON tasks (priority DESC) WHERE status = 'pending';
CREATE INDEX idx_tasks_assigned_agent ON tasks (assigned_agent_id, status);
CREATE INDEX idx_tasks_created_at ON tasks (created_at DESC);
CREATE INDEX idx_tasks_workflow ON tasks (workflow_id) WHERE workflow_id IS NOT NULL;
CREATE INDEX idx_tasks_parent ON tasks (parent_task_id) WHERE parent_task_id IS NOT NULL;

-- Composite indexes for common queries
CREATE INDEX idx_tasks_agent_status_priority ON tasks (assigned_agent_id, status, priority DESC);
CREATE INDEX idx_tasks_status_created ON tasks (status, created_at DESC) WHERE is_deleted = FALSE;
```

### Database View Definition
```sql
-- views/agent_performance.sql - Agent performance analytics view

CREATE VIEW agent_performance AS
SELECT 
    a.id,
    a.name,
    a.type,
    a.status,
    
    -- Task statistics
    COUNT(t.id) as total_tasks,
    COUNT(CASE WHEN t.status = 'completed' THEN 1 END) as completed_tasks,
    COUNT(CASE WHEN t.status = 'failed' THEN 1 END) as failed_tasks,
    
    -- Performance metrics
    ROUND(
        CAST(COUNT(CASE WHEN t.status = 'completed' THEN 1 END) AS REAL) / 
        NULLIF(COUNT(t.id), 0) * 100, 2
    ) as success_rate_percentage,
    
    AVG(t.actual_duration) as avg_task_duration,
    MIN(t.actual_duration) as min_task_duration,
    MAX(t.actual_duration) as max_task_duration,
    
    -- Recent activity
    MAX(t.completed_at) as last_completed_task,
    COUNT(CASE WHEN t.created_at >= datetime('now', '-7 days') THEN 1 END) as tasks_last_7_days,
    COUNT(CASE WHEN t.created_at >= datetime('now', '-30 days') THEN 1 END) as tasks_last_30_days,
    
    -- Quality metrics
    AVG(CASE WHEN t.status = 'completed' THEN t.complexity_score END) as avg_complexity_handled,
    AVG(t.retry_count) as avg_retry_count,
    
    a.created_at as agent_created_at,
    a.last_activity_at

FROM agents a
LEFT JOIN tasks t ON a.id = t.assigned_agent_id 
    AND t.is_deleted = FALSE
WHERE a.is_deleted = FALSE
GROUP BY a.id, a.name, a.type, a.status, a.created_at, a.last_activity_at;

-- Add comments for view documentation
COMMENT ON VIEW agent_performance IS 'Comprehensive agent performance metrics and statistics';
```

### Trigger Definition
```sql
-- triggers/timestamp_triggers.sql - Automatic timestamp updates

-- Update timestamp trigger for agents table
CREATE TRIGGER update_agents_timestamp 
    AFTER UPDATE ON agents
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE agents 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Update timestamp trigger for tasks table
CREATE TRIGGER update_tasks_timestamp 
    AFTER UPDATE ON tasks
    FOR EACH ROW
    WHEN NEW.updated_at = OLD.updated_at
BEGIN
    UPDATE tasks 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Audit trigger for sensitive operations
CREATE TRIGGER audit_agent_changes
    AFTER UPDATE ON agents
    FOR EACH ROW
    WHEN OLD.status != NEW.status OR OLD.config != NEW.config
BEGIN
    INSERT INTO audit_log (
        table_name, record_id, operation, old_values, new_values, 
        changed_at, changed_by
    ) VALUES (
        'agents', 
        NEW.id, 
        'UPDATE',
        json_object('status', OLD.status, 'config', OLD.config),
        json_object('status', NEW.status, 'config', NEW.config),
        CURRENT_TIMESTAMP,
        'system' -- This would be replaced with actual user context
    );
END;
```

## Related Documentation

- [Database Migrations](../migrations/README.md) - Database migration procedures
- [Data Models](../../src/swarm_director/models/README.md) - Application data models
- [API Schemas](../../src/swarm_director/schemas/README.md) - API validation schemas
- [Performance Tuning](../../docs/development/database_performance.md) - Database performance optimization
- [Security Guide](../../docs/development/database_security.md) - Database security best practices
- [Backup Procedures](../data/README.md) - Database backup and recovery
