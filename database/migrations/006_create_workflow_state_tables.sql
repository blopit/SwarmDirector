-- Migration: 006_create_workflow_state_tables.sql
-- Description: Create tables for workflow state persistence
-- Date: 2025-06-17

-- Create workflow_states table
CREATE TABLE IF NOT EXISTS workflow_states (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id VARCHAR(255) UNIQUE NOT NULL,
    workflow_type VARCHAR(100) NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'pending',
    current_phase VARCHAR(100),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    started_at DATETIME,
    completed_at DATETIME,
    total_steps INTEGER DEFAULT 0,
    completed_steps INTEGER DEFAULT 0,
    input_data TEXT,
    output_data TEXT,
    error_data TEXT,
    email_context TEXT,
    review_context TEXT,
    assigned_director VARCHAR(255),
    assigned_communications_dept VARCHAR(255),
    assigned_email_agent VARCHAR(255),
    assigned_review_agents TEXT,
    review_iterations INTEGER DEFAULT 0,
    content_revisions INTEGER DEFAULT 0,
    delivery_attempts INTEGER DEFAULT 0,
    phase_history TEXT,
    phase_durations TEXT,
    state_history TEXT,
    active_agents TEXT,
    completed_tasks TEXT,
    failed_tasks TEXT
);

-- Create indexes for workflow_states
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_id ON workflow_states(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_states_workflow_type ON workflow_states(workflow_type);
CREATE INDEX IF NOT EXISTS idx_workflow_states_status ON workflow_states(status);
CREATE INDEX IF NOT EXISTS idx_workflow_states_current_phase ON workflow_states(current_phase);
CREATE INDEX IF NOT EXISTS idx_workflow_states_created_at ON workflow_states(created_at);

-- Create workflow_events table
CREATE TABLE IF NOT EXISTS workflow_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    workflow_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    from_state VARCHAR(50),
    to_state VARCHAR(50),
    from_phase VARCHAR(100),
    to_phase VARCHAR(100),
    agent_name VARCHAR(255),
    reason TEXT,
    metadata TEXT,
    workflow_state_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (workflow_state_id) REFERENCES workflow_states(id)
);

-- Create indexes for workflow_events
CREATE INDEX IF NOT EXISTS idx_workflow_events_workflow_id ON workflow_events(workflow_id);
CREATE INDEX IF NOT EXISTS idx_workflow_events_event_type ON workflow_events(event_type);
CREATE INDEX IF NOT EXISTS idx_workflow_events_created_at ON workflow_events(created_at);
CREATE INDEX IF NOT EXISTS idx_workflow_events_workflow_state_id ON workflow_events(workflow_state_id);

-- Create trigger to update updated_at timestamps
CREATE TRIGGER IF NOT EXISTS update_workflow_states_updated_at 
    AFTER UPDATE ON workflow_states
    BEGIN
        UPDATE workflow_states SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END;

CREATE TRIGGER IF NOT EXISTS update_workflow_events_updated_at 
    AFTER UPDATE ON workflow_events
    BEGIN
        UPDATE workflow_events SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
    END; 