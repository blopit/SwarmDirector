-- ==============================================================================
-- SwarmDirector Database Schema
-- ==============================================================================
-- 
-- This file contains the SQLite database schema for the SwarmDirector 
-- hierarchical AI agent management system.
--
-- Generated: 2025-06-11
-- Database: SQLite
-- Framework: Flask-SQLAlchemy with Alembic migrations
--
-- ==============================================================================

-- AGENTS TABLE
-- Stores AI agent definitions, capabilities, and hierarchical relationships
CREATE TABLE agents (
	name VARCHAR(100) NOT NULL, 
	description TEXT, 
	agent_type VARCHAR(11) NOT NULL,  -- 'supervisor', 'coordinator', 'worker', 'specialist'
	status VARCHAR(7) NOT NULL,       -- 'active', 'idle', 'busy', 'error', 'offline'
	parent_id INTEGER,                -- Self-referencing foreign key for hierarchy
	capabilities JSON,                -- Agent capabilities as JSON
	config JSON,                      -- Agent configuration as JSON
	tasks_completed INTEGER,          -- Performance tracking
	success_rate FLOAT,              -- Performance tracking  
	average_response_time FLOAT,     -- Performance tracking
	autogen_config JSON,             -- Microsoft AutoGen configuration
	system_message TEXT,             -- System message for the agent
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(parent_id) REFERENCES agents (id)
);

-- TASKS TABLE
-- Stores work assignments, progress tracking, and task relationships
CREATE TABLE tasks (
	title VARCHAR(200) NOT NULL, 
	description TEXT, 
	status VARCHAR(11) NOT NULL,      -- 'pending', 'assigned', 'in_progress', 'completed', 'failed', 'cancelled'
	priority VARCHAR(8) NOT NULL,     -- 'low', 'medium', 'high', 'critical'
	assigned_agent_id INTEGER,        -- Agent assigned to this task
	parent_task_id INTEGER,           -- Parent task for subtask relationships
	estimated_duration INTEGER,       -- Estimated duration in minutes
	actual_duration INTEGER,          -- Actual duration in minutes
	deadline DATETIME,                -- Task deadline
	input_data JSON,                  -- Task input parameters
	output_data JSON,                 -- Task execution results
	error_details TEXT,               -- Error information if task failed
	progress_percentage INTEGER,      -- Task completion percentage (0-100)
	last_activity DATETIME,           -- Last activity timestamp
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(assigned_agent_id) REFERENCES agents (id), 
	FOREIGN KEY(parent_task_id) REFERENCES tasks (id)
);

-- CONVERSATIONS TABLE
-- Stores agent communication sessions and chat metadata
CREATE TABLE conversations (
	title VARCHAR(200), 
	description TEXT, 
	status VARCHAR(9) NOT NULL,       -- 'active', 'completed', 'paused', 'error'
	initiator_agent_id INTEGER,       -- Agent that started the conversation
	session_id VARCHAR(100),          -- Unique session identifier
	user_id VARCHAR(100),             -- User identifier if user is involved
	conversation_type VARCHAR(50),    -- Type of conversation (task, query, etc.)
	autogen_chat_history JSON,        -- Microsoft AutoGen chat history
	group_chat_config JSON,           -- Configuration for group chats
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(initiator_agent_id) REFERENCES agents (id), 
	UNIQUE (session_id)
);

-- MESSAGES TABLE
-- Stores individual messages within conversations
CREATE TABLE messages (
	content TEXT NOT NULL,            -- Message content
	message_type VARCHAR(14) NOT NULL, -- 'user_message', 'agent_response', 'system_message', 'agent_to_agent', 'error_message'
	conversation_id INTEGER NOT NULL, -- Parent conversation
	sender_agent_id INTEGER,          -- Agent that sent the message (nullable for user messages)
	message_metadata JSON,            -- Additional message metadata
	tokens_used INTEGER,              -- Token count for LLM tracking
	response_time FLOAT,              -- Response time in seconds
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(sender_agent_id) REFERENCES agents (id)
);

-- ==============================================================================
-- INDEXES AND CONSTRAINTS
-- ==============================================================================
-- 
-- Primary key indexes are automatically created for all tables
-- Foreign key relationships provide efficient joins
-- session_id has a unique constraint for conversations
--
-- Recommended additional indexes for performance:
-- CREATE INDEX idx_agents_parent_id ON agents(parent_id);
-- CREATE INDEX idx_agents_type_status ON agents(agent_type, status);
-- CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent_id);
-- CREATE INDEX idx_tasks_parent_id ON tasks(parent_task_id);
-- CREATE INDEX idx_tasks_status ON tasks(status);
-- CREATE INDEX idx_messages_conversation ON messages(conversation_id);
-- CREATE INDEX idx_messages_sender ON messages(sender_agent_id);
--
-- ============================================================================== 