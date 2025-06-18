# SwarmDirector Cost Tracking and Monitoring Guide

## Overview

SwarmDirector now includes comprehensive cost tracking and monitoring capabilities for AI agent operations. This system provides real-time cost calculations, budget management, and alerting for all AI service usage across OpenAI, Anthropic, and Perplexity APIs.

## Features

### 🔍 Real-time Cost Tracking
- Automatic interception of all AI API calls
- Token usage and cost calculation per request
- Historical cost data storage and analysis
- Support for multiple AI providers (OpenAI, Anthropic, Perplexity)

### 💰 Budget Management
- Flexible budget creation (daily, weekly, monthly, yearly)
- Provider-specific and model-specific budgets
- Agent-specific budget allocation
- Automatic budget period reset

### 🚨 Cost Alerting
- Configurable warning and critical thresholds
- Real-time budget violation alerts
- Multiple alert severity levels
- Alert acknowledgment system

### 📊 Analytics and Reporting
- Comprehensive cost breakdowns by provider, model, and agent
- Usage trends and efficiency metrics
- Top cost drivers identification
- Cost optimization recommendations

## Quick Start

### 1. Database Setup

Run the migration to create cost tracking tables:

```bash
# Apply the cost tracking migration
sqlite3 database/data/swarm_director_dev.db < database/migrations/add_cost_tracking_tables.sql
```

### 2. Initialize Cost Tracking

The cost tracking system is automatically initialized when the application starts. You can verify it's working by checking the logs:

```bash
# Check application logs
tail -f logs/app.log | grep "cost tracking"
```

### 3. Create Your First Budget

```bash
curl -X POST http://localhost:5000/api/cost/budgets \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Monthly AI Budget",
    "description": "Overall monthly budget for AI operations",
    "limit_amount": 100.00,
    "period": "monthly",
    "warning_threshold": 80,
    "critical_threshold": 95
  }'
```

## API Endpoints

### Cost Usage Tracking

#### Get API Usage Records
```http
GET /api/cost/usage?page=1&per_page=50&provider=openai&start_date=2024-12-01
```

#### Get Cost Summary
```http
GET /api/cost/summary?start_date=2024-12-01&end_date=2024-12-31
```

#### Get Cost Efficiency Metrics
```http
GET /api/cost/efficiency?start_date=2024-12-01
```

### Budget Management

#### Create Budget
```http
POST /api/cost/budgets
Content-Type: application/json

{
  "name": "OpenAI Monthly Budget",
  "description": "Budget for OpenAI API usage",
  "provider": "openai",
  "limit_amount": 50.00,
  "period": "monthly",
  "warning_threshold": 80,
  "critical_threshold": 95
}
```

#### Get All Budgets
```http
GET /api/cost/budgets?is_active=true
```

#### Get Budget Details
```http
GET /api/cost/budgets/{budget_id}
```

### Alert Management

#### Get Cost Alerts
```http
GET /api/cost/alerts?is_acknowledged=false&severity=warning
```

#### Acknowledge Alert
```http
POST /api/cost/alerts/{alert_id}/acknowledge
Content-Type: application/json

{
  "acknowledged_by": "admin"
}
```

### Analytics

#### Get Top Cost Drivers
```http
GET /api/cost/top-drivers?limit=10&start_date=2024-12-01
```

#### Get Cost Dashboard
```http
GET /api/cost/dashboard
```

## Configuration

### Environment Variables

Add these to your `.env` file for enhanced cost tracking:

```env
# Cost tracking configuration
COST_TRACKING_ENABLED=true
COST_TRACKING_AUTO_BUDGET_RESET=true
COST_TRACKING_DEFAULT_BUDGET_LIMIT=100.00

# Alert configuration
COST_ALERT_EMAIL_ENABLED=false
COST_ALERT_WEBHOOK_URL=https://your-webhook-url.com/alerts
```

### Budget Types

#### Global Budget
Tracks all AI usage across all providers and agents:
```json
{
  "name": "Global Monthly Budget",
  "limit_amount": 200.00,
  "period": "monthly"
}
```

#### Provider-Specific Budget
Tracks usage for a specific AI provider:
```json
{
  "name": "OpenAI Budget",
  "provider": "openai",
  "limit_amount": 100.00,
  "period": "monthly"
}
```

#### Model-Specific Budget
Tracks usage for a specific model:
```json
{
  "name": "GPT-4 Budget",
  "provider": "openai",
  "model": "gpt-4",
  "limit_amount": 50.00,
  "period": "weekly"
}
```

#### Agent-Specific Budget
Tracks usage for a specific agent:
```json
{
  "name": "Research Agent Budget",
  "agent_id": 123,
  "limit_amount": 25.00,
  "period": "daily"
}
```

## Current API Pricing (Built-in)

The system includes current pricing for all supported providers:

### OpenAI
- GPT-4: $30/$60 per 1M tokens (input/output)
- GPT-4 Turbo: $10/$30 per 1M tokens
- GPT-4o: $5/$15 per 1M tokens
- GPT-4o Mini: $0.15/$0.60 per 1M tokens
- GPT-3.5 Turbo: $0.50/$1.50 per 1M tokens

### Anthropic
- Claude-3 Opus: $15/$75 per 1M tokens
- Claude-3.5 Sonnet: $3/$15 per 1M tokens
- Claude-3 Haiku: $0.25/$1.25 per 1M tokens

### Perplexity
- Sonar Pro: $1/$3 per 1M tokens (estimated)
- Sonar Small: $0.20/$0.60 per 1M tokens (estimated)

## Usage Examples

### Manual Cost Tracking

For cases where automatic interception doesn't work:

```python
from swarm_director.utils.cost_integration import manual_track_api_call

# Manually track an API call
usage_record = manual_track_api_call(
    provider="openai",
    model="gpt-4",
    input_tokens=1000,
    output_tokens=500,
    request_duration_ms=2500,
    agent_id=123,
    task_id=456
)
```

### Context Tracking

Track costs within specific agent contexts:

```python
from swarm_director.utils.cost_integration import track_agent_context

@track_agent_context(agent_id=123, task_id=456)
def process_with_ai():
    # AI API calls here will be automatically tracked
    # with the specified agent and task context
    response = openai_client.chat.completions.create(...)
    return response
```

### Cost Estimation

Estimate costs before making API calls:

```bash
curl -X POST http://localhost:5000/api/cost/estimate \
  -H "Content-Type: application/json" \
  -d '{
    "provider": "openai",
    "model": "gpt-4",
    "estimated_input_tokens": 1000,
    "estimated_output_tokens": 500
  }'
```

## Monitoring and Alerts

### Alert Types

1. **Budget Warning**: Triggered at 80% of budget limit (configurable)
2. **Budget Critical**: Triggered at 95% of budget limit (configurable)
3. **Budget Exceeded**: Triggered when budget limit is exceeded

### Alert Channels

- **Console**: Logged to application logs
- **Email**: Send email notifications (requires configuration)
- **Webhook**: HTTP POST to configured webhook URL

### Dashboard

Access the cost dashboard at:
```
GET /api/cost/dashboard
```

This provides:
- Current month cost summary
- Active budget status
- Recent alerts
- Top cost drivers
- Efficiency metrics

## Best Practices

### 1. Budget Strategy
- Start with conservative budgets and adjust based on usage patterns
- Use multiple budget levels (global, provider, agent-specific)
- Set warning thresholds to get early notifications

### 2. Cost Optimization
- Monitor the efficiency metrics regularly
- Review top cost drivers monthly
- Consider using more cost-effective models for appropriate tasks

### 3. Alert Management
- Acknowledge alerts promptly to avoid notification spam
- Review alert patterns to identify optimization opportunities
- Set up webhook notifications for critical alerts

### 4. Regular Review
- Weekly review of cost trends
- Monthly budget adjustments
- Quarterly cost optimization analysis

## Troubleshooting

### Cost Tracking Not Working
1. Check if cost tracking is enabled in logs
2. Verify API interceptors are properly patched
3. Ensure database tables are created

### Missing Cost Data
1. Verify API calls are going through the interceptor
2. Check for errors in the application logs
3. Ensure proper context is set for agent/task tracking

### Budget Alerts Not Firing
1. Check budget configuration and thresholds
2. Verify alerting system is initialized
3. Check alert history for previous notifications

## Support

For issues or questions about cost tracking:

1. Check the application logs for error messages
2. Verify your configuration matches the examples
3. Review the API documentation for correct usage
4. Check the database for cost tracking tables and data

The cost tracking system is designed to be robust and provide comprehensive monitoring of your AI operations costs while helping you optimize usage and stay within budget.
