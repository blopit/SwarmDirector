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
	orchestration_pattern VARCHAR(20), -- Orchestration pattern used ('round_robin', 'expertise_based', etc.)
	start_time DATETIME,              -- Conversation start timestamp
	end_time DATETIME,                -- Conversation end timestamp
	total_duration FLOAT,             -- Duration in seconds
	total_tokens INTEGER DEFAULT 0,   -- Total tokens used in conversation
	total_messages INTEGER DEFAULT 0, -- Total message count
	participant_count INTEGER DEFAULT 0, -- Number of participating agents
	avg_response_time FLOAT,          -- Average response time in seconds
	effectiveness_score FLOAT,        -- Effectiveness score (0-100)
	engagement_score FLOAT,           -- Engagement score (0-100)
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
	agent_name VARCHAR(100),          -- Agent name for tracking
	message_length INTEGER,           -- Character count of message
	sentiment_score FLOAT,            -- Sentiment analysis score (-1 to 1)
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id), 
	FOREIGN KEY(sender_agent_id) REFERENCES agents (id)
);

-- CONVERSATION_ANALYTICS TABLE
-- Stores detailed analytics for conversation performance and insights
CREATE TABLE conversation_analytics (
	conversation_id INTEGER NOT NULL, -- Foreign key to conversations table
	-- Timing metrics
	total_duration FLOAT,             -- Total conversation duration in seconds
	avg_message_interval FLOAT,       -- Average time between messages
	fastest_response FLOAT,           -- Fastest agent response time
	slowest_response FLOAT,           -- Slowest agent response time
	-- Content metrics
	total_characters INTEGER,         -- Total character count
	avg_message_length FLOAT,         -- Average message length
	unique_words INTEGER,             -- Unique word count
	vocabulary_richness FLOAT,        -- Unique words / total words ratio
	-- Participation metrics
	total_participants INTEGER,       -- Number of participating agents
	most_active_agent VARCHAR(100),   -- Agent with most messages
	participation_balance FLOAT,      -- Balance score (0-1)
	-- Quality metrics
	error_count INTEGER DEFAULT 0,    -- Number of error messages
	completion_status VARCHAR(20),    -- How the conversation ended
	goal_achievement FLOAT,           -- Goal achievement score (0-100)
	-- AutoGen specific metrics
	orchestration_switches INTEGER DEFAULT 0, -- Number of pattern switches
	group_chat_efficiency FLOAT,     -- Group chat efficiency score
	agent_collaboration_score FLOAT, -- Agent collaboration score
	-- Sentiment and engagement
	overall_sentiment FLOAT,          -- Average sentiment score
	sentiment_variance FLOAT,         -- Variance in sentiment
	engagement_peaks JSON,            -- Timestamps of high engagement
	id INTEGER NOT NULL, 
	created_at DATETIME NOT NULL, 
	updated_at DATETIME NOT NULL, 
	PRIMARY KEY (id), 
	FOREIGN KEY(conversation_id) REFERENCES conversations (id),
	UNIQUE (conversation_id)          -- One analytics record per conversation
);

-- ==============================================================================
-- INDEXES AND CONSTRAINTS
-- ==============================================================================
-- 
-- Primary key indexes are automatically created for all tables
-- Foreign key relationships provide efficient joins
-- session_id has a unique constraint for conversations
-- conversation_id has a unique constraint for conversation_analytics
--
-- Recommended additional indexes for performance:
-- CREATE INDEX idx_agents_parent_id ON agents(parent_id);
-- CREATE INDEX idx_agents_type_status ON agents(agent_type, status);
-- CREATE INDEX idx_tasks_assigned_agent ON tasks(assigned_agent_id);
-- CREATE INDEX idx_tasks_parent_id ON tasks(parent_task_id);
-- CREATE INDEX idx_tasks_status ON tasks(status);
-- CREATE INDEX idx_conversations_status ON conversations(status);
-- CREATE INDEX idx_conversations_pattern ON conversations(orchestration_pattern);
-- CREATE INDEX idx_messages_conversation ON messages(conversation_id);
-- CREATE INDEX idx_messages_sender ON messages(sender_agent_id);
-- CREATE INDEX idx_messages_type ON messages(message_type);
-- CREATE INDEX idx_analytics_conversation ON conversation_analytics(conversation_id);
--
-- ============================================================================== 