-- Migration: Add cost tracking tables
-- Description: Add tables for API usage tracking, budget management, and cost alerts
-- Version: 1.0
-- Date: 2024-12-17

-- Create API usage tracking table
CREATE TABLE IF NOT EXISTS api_usage (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Request identification
    request_id VARCHAR(100) UNIQUE NOT NULL,
    correlation_id VARCHAR(100),
    
    -- API details
    provider VARCHAR(20) NOT NULL,
    model VARCHAR(100) NOT NULL,
    usage_type VARCHAR(30) NOT NULL DEFAULT 'chat_completion',
    
    -- Usage metrics
    input_tokens INTEGER DEFAULT 0,
    output_tokens INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    
    -- Cost information
    input_cost DECIMAL(10,6) DEFAULT 0.0,
    output_cost DECIMAL(10,6) DEFAULT 0.0,
    total_cost DECIMAL(10,6) DEFAULT 0.0,
    
    -- Pricing rates used (for historical tracking)
    input_price_per_token DECIMAL(12,8) DEFAULT 0.0,
    output_price_per_token DECIMAL(12,8) DEFAULT 0.0,
    
    -- Request metadata
    request_duration_ms INTEGER,
    response_status VARCHAR(20) DEFAULT 'success',
    error_message TEXT,
    
    -- Context information
    agent_id INTEGER,
    task_id INTEGER,
    conversation_id INTEGER,
    
    -- Additional metadata
    metadata JSON,
    
    -- Foreign key constraints
    FOREIGN KEY (agent_id) REFERENCES agents(id),
    FOREIGN KEY (task_id) REFERENCES tasks(id),
    FOREIGN KEY (conversation_id) REFERENCES conversations(id)
);

-- Create cost budgets table
CREATE TABLE IF NOT EXISTS cost_budgets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Budget identification
    name VARCHAR(100) NOT NULL,
    description TEXT,
    
    -- Budget scope
    provider VARCHAR(20),
    model VARCHAR(100),
    agent_id INTEGER,
    
    -- Budget limits
    period VARCHAR(20) NOT NULL DEFAULT 'monthly',
    limit_amount DECIMAL(10,2) NOT NULL,
    
    -- Alert thresholds (percentages of limit)
    warning_threshold INTEGER DEFAULT 80,
    critical_threshold INTEGER DEFAULT 95,
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    
    -- Current period tracking
    current_period_start DATETIME NOT NULL,
    current_period_end DATETIME NOT NULL,
    current_period_spent DECIMAL(10,2) DEFAULT 0.0,
    
    -- Foreign key constraints
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Create cost alerts table
CREATE TABLE IF NOT EXISTS cost_alerts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- Alert identification
    alert_type VARCHAR(50) NOT NULL,
    severity VARCHAR(20) NOT NULL DEFAULT 'info',
    
    -- Alert content
    title VARCHAR(200) NOT NULL,
    message TEXT NOT NULL,
    
    -- Related entities
    budget_id INTEGER,
    usage_id INTEGER,
    agent_id INTEGER,
    
    -- Alert status
    is_acknowledged BOOLEAN DEFAULT FALSE,
    acknowledged_at DATETIME,
    acknowledged_by VARCHAR(100),
    
    -- Notification status
    notification_sent BOOLEAN DEFAULT FALSE,
    notification_channels JSON,
    
    -- Alert metadata
    metadata JSON,
    
    -- Foreign key constraints
    FOREIGN KEY (budget_id) REFERENCES cost_budgets(id),
    FOREIGN KEY (usage_id) REFERENCES api_usage(id),
    FOREIGN KEY (agent_id) REFERENCES agents(id)
);

-- Create indexes for efficient querying

-- API Usage indexes
CREATE INDEX IF NOT EXISTS idx_api_usage_request_id ON api_usage(request_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_correlation_id ON api_usage(correlation_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_provider ON api_usage(provider);
CREATE INDEX IF NOT EXISTS idx_api_usage_model ON api_usage(model);
CREATE INDEX IF NOT EXISTS idx_api_usage_agent_id ON api_usage(agent_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_task_id ON api_usage(task_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_conversation_id ON api_usage(conversation_id);
CREATE INDEX IF NOT EXISTS idx_api_usage_provider_date ON api_usage(provider, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_cost_date ON api_usage(total_cost, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_agent_date ON api_usage(agent_id, created_at);
CREATE INDEX IF NOT EXISTS idx_api_usage_model_date ON api_usage(model, created_at);

-- Cost Budget indexes
CREATE INDEX IF NOT EXISTS idx_cost_budget_is_active ON cost_budgets(is_active);
CREATE INDEX IF NOT EXISTS idx_cost_budget_provider ON cost_budgets(provider);
CREATE INDEX IF NOT EXISTS idx_cost_budget_agent_id ON cost_budgets(agent_id);
CREATE INDEX IF NOT EXISTS idx_cost_budget_active_period ON cost_budgets(is_active, current_period_start, current_period_end);
CREATE INDEX IF NOT EXISTS idx_cost_budget_provider_agent ON cost_budgets(provider, agent_id);

-- Cost Alert indexes
CREATE INDEX IF NOT EXISTS idx_cost_alert_alert_type ON cost_alerts(alert_type);
CREATE INDEX IF NOT EXISTS idx_cost_alert_severity ON cost_alerts(severity);
CREATE INDEX IF NOT EXISTS idx_cost_alert_is_acknowledged ON cost_alerts(is_acknowledged);
CREATE INDEX IF NOT EXISTS idx_cost_alert_budget_id ON cost_alerts(budget_id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_usage_id ON cost_alerts(usage_id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_agent_id ON cost_alerts(agent_id);
CREATE INDEX IF NOT EXISTS idx_cost_alert_type_severity ON cost_alerts(alert_type, severity);
CREATE INDEX IF NOT EXISTS idx_cost_alert_unacknowledged ON cost_alerts(is_acknowledged, created_at);

-- Create triggers for updated_at timestamps

-- API Usage trigger
CREATE TRIGGER IF NOT EXISTS update_api_usage_updated_at
    AFTER UPDATE ON api_usage
    FOR EACH ROW
BEGIN
    UPDATE api_usage SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Cost Budget trigger
CREATE TRIGGER IF NOT EXISTS update_cost_budget_updated_at
    AFTER UPDATE ON cost_budgets
    FOR EACH ROW
BEGIN
    UPDATE cost_budgets SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Cost Alert trigger
CREATE TRIGGER IF NOT EXISTS update_cost_alert_updated_at
    AFTER UPDATE ON cost_alerts
    FOR EACH ROW
BEGIN
    UPDATE cost_alerts SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

-- Insert initial data (optional)

-- Create a default monthly budget for all providers
INSERT OR IGNORE INTO cost_budgets (
    name,
    description,
    period,
    limit_amount,
    warning_threshold,
    critical_threshold,
    is_active,
    current_period_start,
    current_period_end,
    current_period_spent
) VALUES (
    'Default Monthly Budget',
    'Default budget for all AI API usage',
    'monthly',
    100.00,
    80,
    95,
    TRUE,
    date('now', 'start of month'),
    date('now', 'start of month', '+1 month'),
    0.0
);

-- Create provider-specific budgets (commented out by default)
/*
INSERT OR IGNORE INTO cost_budgets (
    name,
    description,
    provider,
    period,
    limit_amount,
    warning_threshold,
    critical_threshold,
    is_active,
    current_period_start,
    current_period_end,
    current_period_spent
) VALUES 
    ('OpenAI Monthly Budget', 'Monthly budget for OpenAI API usage', 'openai', 'monthly', 50.00, 80, 95, TRUE, date('now', 'start of month'), date('now', 'start of month', '+1 month'), 0.0),
    ('Anthropic Monthly Budget', 'Monthly budget for Anthropic API usage', 'anthropic', 'monthly', 30.00, 80, 95, TRUE, date('now', 'start of month'), date('now', 'start of month', '+1 month'), 0.0),
    ('Perplexity Monthly Budget', 'Monthly budget for Perplexity API usage', 'perplexity', 'monthly', 20.00, 80, 95, TRUE, date('now', 'start of month'), date('now', 'start of month', '+1 month'), 0.0);
*/

-- Migration complete
-- Note: This migration adds comprehensive cost tracking capabilities to SwarmDirector
-- including API usage monitoring, budget management, and alerting functionality.
