# SwarmDirector User Guide

**Getting the most out of your Hierarchical AI Agent Management System**

---

## 📚 Table of Contents

1. [🚀 Getting Started](#-getting-started)
2. [🎯 Basic Operations](#-basic-operations)
3. [💼 Business Scenarios](#-business-scenarios)
4. [🔧 Advanced Features](#-advanced-features)
5. [❓ Troubleshooting](#-troubleshooting)
6. [📊 Quick Reference](#-quick-reference)

---

## 🚀 Getting Started

### First Time Setup

**Step 1: Access SwarmDirector**
```bash
# Start the application
python run.py

# Open your browser to:
http://localhost:5000/dashboard
```

**Step 2: Verify System Health**
- Navigate to the dashboard
- Check that all agents show "Active" status
- Verify database connectivity (green indicator)

**Step 3: Try the Interactive Demo**
```bash
# Access the demo interface
http://localhost:5000/demo
```

### Understanding the Interface

**🎭 Director Agent**: Your main orchestrator
- Routes all incoming requests
- Automatically selects the right department
- Provides intelligent task classification

**💬 Communications Department**: Content creation hub  
- Handles all written communications
- Provides parallel review workflows
- Ensures high-quality output through consensus

**📧 Email Agent**: Email automation specialist
- Manages SMTP integration
- Handles template-based communications
- Provides comprehensive email validation

---

## 🎯 Basic Operations

### Creating Your First Task

**Via Web Interface:**

1. **Navigate to Dashboard**
   - Go to `http://localhost:5000/dashboard`
   - Click "Submit New Task" button

2. **Fill Task Details**
   ```
   Title: Welcome new customer
   Description: Send personalized welcome email to John Doe
   Priority: High
   Department: communications (auto-selected)
   ```

3. **Submit and Monitor**
   - Click "Submit Task"
   - Watch real-time progress in Activity Log
   - Check results in Completed Tasks section

**Via API:**

```bash
curl -X POST http://localhost:5000/task \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Welcome new customer",
    "description": "Send personalized welcome email to John Doe",
    "type": "email",
    "priority": "high",
    "args": {
      "customer_name": "John Doe",
      "template": "welcome_standard"
    }
  }'
```

### Monitoring Task Progress

**Real-time Monitoring:**
- **Activity Log**: Live updates of all agent actions
- **System Metrics**: CPU, memory, and task processing stats
- **Agent Status**: Current workload and availability

**Task States:**
- 🔵 **Pending**: Waiting to be processed
- 🟡 **Processing**: Currently being handled by agents
- 🟢 **Completed**: Successfully finished
- 🔴 **Failed**: Encountered an error (see logs)

---

## 💼 Business Scenarios

### Scenario 1: Customer Support Automation

**Use Case**: Handle customer inquiries with intelligent routing

**Step-by-Step:**

1. **Set up Email Templates**
   ```python
   # Templates are automatically available in:
   # src/swarm_director/templates/email/
   ```

2. **Submit Support Task**
   ```json
   {
     "title": "Handle customer inquiry",
     "description": "Process billing question from customer",
     "type": "email",
     "args": {
       "customer_email": "customer@example.com",
       "inquiry_type": "billing",
       "priority": "high"
     }
   }
   ```

3. **Monitor Processing**
   - Director routes to Communications Department
   - DraftReviewAgent analyzes inquiry
   - EmailAgent crafts and sends response
   - Quality metrics tracked automatically

**Expected Results:**
- ✅ Personalized response sent within 30 seconds
- ✅ Quality score above 85%
- ✅ Customer satisfaction tracking initiated

### Scenario 2: Marketing Campaign Management

**Use Case**: Coordinate multi-channel marketing campaigns

**Step-by-Step:**

1. **Plan Campaign**
   ```json
   {
     "title": "Launch Q4 product campaign",
     "description": "Coordinate new product feature launch",
     "type": "coordinate",
     "args": {
       "campaign_name": "Q4_Product_Launch",
       "channels": ["email", "social_media", "blog"],
       "budget": "$50000"
     }
   }
   ```

2. **Execute Campaign Steps**
   - Director analyzes campaign scope
   - Communications creates content variants
   - EmailAgent schedules sends
   - Analytics tracking activated

3. **Monitor Campaign Performance**
   - Real-time metrics in dashboard
   - A/B testing results
   - Conversion tracking

### Scenario 3: Business Intelligence & Analytics

**Use Case**: Generate automated insights from business data

**Step-by-Step:**

1. **Request Analysis**
   ```json
   {
     "title": "Generate monthly revenue report",
     "description": "Analyze revenue trends and growth metrics",
     "type": "analysis",
     "args": {
       "report_type": "revenue_analysis",
       "period": "november_2024",
       "include_forecasts": true
     }
   }
   ```

2. **Automated Processing**
   - Director routes to Analytics Department
   - Data extraction and processing
   - Insight generation with visualizations
   - Report compilation and delivery

---

## 🔧 Advanced Features

### Custom Department Registration

**Creating a New Department:**

```python
from src.swarm_director.agents.base_agent import BaseAgent

class MyCustomDepartment(BaseAgent):
    def __init__(self):
        super().__init__(
            name="CustomDept",
            agent_type=AgentType.CUSTOM,
            description="My custom department logic"
        )
    
    def handle_task(self, task):
        # Your custom logic here
        return {"status": "completed", "result": "Custom processing done"}

# Register with Director
director.register_department(MyCustomDepartment())
```

### Webhook Integration

**Set up webhooks for external systems:**

```python
@app.route('/webhook/task_completed', methods=['POST'])
def handle_task_completion():
    data = request.get_json()
    # Process webhook
    return jsonify({"status": "received"})
```

---

## ❓ Troubleshooting

### Common Issues

**Problem: Tasks stuck in "Pending" status**

*Solution:*
1. Check agent status in dashboard
2. Verify database connectivity
3. Restart agent processes:
   ```bash
   # Restart application
   python run.py
   ```

**Problem: Email delivery failures**

*Solution:*
1. Verify SMTP settings in configuration
2. Check email templates exist
3. Validate recipient addresses
4. Review error logs:
   ```bash
   tail -f logs/swarm_director.log
   ```

---

## 📊 Quick Reference

### API Endpoints

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/task` | POST | Submit new task |
| `/task/<id>` | GET | Get task status |
| `/health` | GET | System health check |
| `/dashboard` | GET | Web interface |
| `/demo` | GET | Interactive demo |

### Task Types

| Type | Description | Example Use Case |
|------|-------------|------------------|
| `email` | Email communications | Customer support, marketing |
| `analysis` | Data analysis | Reports, insights |
| `coordinate` | Multi-step workflows | Campaign management |
| `automation` | Process automation | Dashboard updates |

### Common Commands

```bash
# Start application
python run.py

# Run tests
pytest tests/

# Check system health
curl http://localhost:5000/health

# View logs
tail -f logs/swarm_director.log

# Reset demo data
curl -X POST http://localhost:5000/demo/reset
```

---

## 🎯 Next Steps

1. **Explore Demo Scenarios**: Try all three business scenarios in the interactive demo
2. **Customize for Your Use Case**: Modify agents and departments for your specific needs
3. **Integration**: Connect with your existing systems via API
4. **Scale Up**: Deploy to production environment for real workloads

For more detailed technical information, see:
- [API Documentation](api/README.md)
- [Architecture Guide](architecture/overview.md)
- [Deployment Guide](deployment/local_development.md)

---

> **Need Help?** Check our [GitHub Issues](https://github.com/blopit/SwarmDirector/issues) or [Discussions](https://github.com/blopit/SwarmDirector/discussions) for community support.
