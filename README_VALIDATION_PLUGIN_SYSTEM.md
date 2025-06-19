# SwarmDirector: Hierarchical Validation System & Plugin Architecture

## 🚀 Overview

SwarmDirector now includes a comprehensive **Hierarchical Validation System** and **Modular Plugin Architecture** that ensures quality control and extensibility across all agent tiers. This system implements a three-tier validation chain where work completed by lower-tier agents must be reviewed and approved by their immediate upper-tier before results are propagated up the chain.

## ✨ Key Features

### 🔗 Hierarchical Validation Chain
- **Three-tier validation**: Tool → Department → Director
- **Configurable quality gates** with custom thresholds
- **Automatic rollback** on validation failures
- **Real-time validation metrics** and reporting

### 🔌 Modular Plugin Architecture
- **Dynamic plugin discovery** and installation
- **Automatic dependency management**
- **Capability gap analysis** and resolution
- **Agent factory** for dynamic agent creation

### 🛡️ Quality Assurance
- **Tier-specific validators** with progressive strictness
- **Comprehensive metrics** (accuracy, completeness, compliance)
- **Rollback mechanisms** with detailed failure analysis
- **Audit trails** and validation history

### 🤖 Intelligent Automation
- **Auto-capability discovery** from task descriptions
- **Plugin suggestions** based on missing capabilities
- **Automatic plugin installation** when gaps are detected
- **Dynamic agent creation** based on task requirements

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Tool Agent    │───▶│ Department Agent│───▶│ Director Agent  │
│   (Worker)      │    │  (Supervisor)   │    │   (Director)    │
│                 │    │                 │    │                 │
│ • Basic output  │    │ • Quality review│    │ • Final approval│
│ • 80% threshold │    │ • 85% threshold │    │ • 95% threshold │
│ • Structure     │    │ • Consistency   │    │ • Compliance    │
│   validation    │    │   validation    │    │   validation    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│ Plugin Manager  │    │ Capability      │    │ Rollback        │
│                 │    │ Discovery       │    │ Manager         │
│ • Auto-install  │    │                 │    │                 │
│ • Dependencies  │    │ • Gap analysis  │    │ • State restore │
│ • Agent factory │    │ • Suggestions   │    │ • Cleanup       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### 1. Installation

The validation and plugin system is integrated into SwarmDirector. No additional installation required.

### 2. Configuration

Copy the sample configuration:
```bash
cp config/validation_plugin_config.yaml config/local_config.yaml
```

Edit the configuration to match your environment:
```yaml
# Enable auto-features
plugins:
  auto_install_enabled: true
  auto_discovery_enabled: true

# Configure quality thresholds
validation:
  quality_gates:
    director:
      thresholds:
        - metric: "accuracy"
          minimum_score: 0.95
          critical: true
```

### 3. Initialize the System

```python
from swarm_director.validation_plugin_integration import ValidationPluginIntegrator

# Initialize with configuration
integrator = ValidationPluginIntegrator({
    'plugin_config': {
        'auto_install_enabled': True,
        'auto_discovery_enabled': True
    }
})
```

### 4. Process Tasks with Validation

```python
# Process task through hierarchical validation
result = await integrator.process_task_with_full_validation(
    task=task,
    tool_agent=tool_agent,
    dept_agent=dept_agent,
    director_agent=director_agent
)

print(f"Validation success: {result['success']}")
print(f"Processing time: {result['processing_time_ms']}ms")
```

## 🛠️ CLI Usage

The system includes a comprehensive CLI for management:

### Initialize System
```bash
python scripts/validation_cli.py init --config config/local_config.yaml
```

### Validate a Task
```bash
python scripts/validation_cli.py validate examples/sample_task.json --agents examples/sample_agents.json
```

### List Available Plugins
```bash
python scripts/validation_cli.py list-plugins --status installed
```

### Install a Plugin
```bash
python scripts/validation_cli.py install-plugin advanced_email_plugin
```

### Get Plugin Suggestions
```bash
python scripts/validation_cli.py suggest-plugins examples/complex_task.json
```

### System Status
```bash
python scripts/validation_cli.py status
```

### Cleanup Old Data
```bash
python scripts/validation_cli.py cleanup --days 30
```

## 📋 Examples

### Basic Email Task Validation

```python
# Create task
task = Task(
    title="Send welcome email",
    description="Send personalized welcome email to new customer",
    input_data={
        'type': 'email',
        'customer_name': 'John Doe',
        'template': 'welcome_premium'
    }
)

# Create agents
tool_agent = Agent(name="EmailTool", agent_type=AgentType.WORKER)
dept_agent = Agent(name="CommsDept", agent_type=AgentType.SUPERVISOR)
director_agent = Agent(name="Director", agent_type=AgentType.SUPERVISOR)

# Process with validation
result = await integrator.process_task_with_full_validation(
    task, tool_agent, dept_agent, director_agent
)
```

### Plugin-based Capability Resolution

```python
# Task requiring ML capabilities
ml_task = Task(
    title="Customer behavior analysis",
    description="Perform ML analysis on customer data",
    input_data={'type': 'ml_analysis'}
)

# Auto-resolve missing capabilities
auto_result = await integrator.auto_resolve_capability_gaps(ml_task)

if auto_result['success']:
    print(f"Installed plugins: {auto_result['plugins_installed']}")
else:
    print(f"Recommendations: {auto_result['recommendations']}")
```

### Custom Quality Gates

```python
from swarm_director.validation.validation_chain import ValidationTier

# Configure strict director validation
director_config = {
    'thresholds': [
        {
            'metric': 'accuracy',
            'minimum_score': 0.98,
            'critical': True
        }
    ]
}

integrator.configure_quality_gates(ValidationTier.DIRECTOR, director_config)
```

## 📊 Monitoring and Analytics

### System Health Dashboard

```python
health = integrator.get_system_health()

print(f"Tasks processed: {health['integration_metrics']['tasks_processed']}")
print(f"Validation success rate: {health['validation_statistics']['success_rate']:.1%}")
print(f"Available plugins: {health['plugin_system_status']['total_plugins']}")
```

### Validation History

```python
# Get validation history for a specific task
history = integrator.get_validation_history(task_id="12345")

for validation in history:
    print(f"Tier: {validation.tier}, Status: {validation.status}")
    print(f"Score: {validation.metrics.overall_score:.2f}")
```

### Plugin Analytics

```python
# Get plugin suggestions with relevance scores
suggestions = integrator.get_plugin_suggestions(task)

for plugin, score in suggestions:
    print(f"{plugin.name}: {score:.2f} relevance")
```

## 🔧 Configuration Options

### Validation Configuration

```yaml
validation:
  enabled: true
  parallel_processing: true
  validation_timeout: 300
  
  quality_gates:
    tool:
      thresholds:
        - metric: "completeness"
          minimum_score: 0.8
          critical: true
```

### Plugin Configuration

```yaml
plugins:
  enabled: true
  auto_install_enabled: true
  auto_discovery_enabled: true
  
  registry:
    path: "~/.swarm_director/plugins/registry.json"
  
  dependencies:
    cache_dir: "~/.swarm_director/dependencies"
    auto_cleanup_enabled: true
```

### Security Configuration

```yaml
security:
  plugin_security:
    verify_signatures: true
    sandbox_execution: false
  
  validation_security:
    encrypt_sensitive_data: true
    audit_trail: true
```

## 🧪 Testing

### Run the Demo

```bash
python examples/hierarchical_validation_demo.py
```

### Run Unit Tests

```bash
python -m pytest tests/validation/ -v
python -m pytest tests/plugins/ -v
```

### Integration Tests

```bash
python -m pytest tests/integration/test_validation_plugin_integration.py -v
```

## 📚 Documentation

- **[Hierarchical Validation System](docs/HIERARCHICAL_VALIDATION_SYSTEM.md)** - Complete system documentation
- **[Plugin Development Guide](docs/PLUGIN_DEVELOPMENT.md)** - How to create plugins
- **[API Reference](docs/API_REFERENCE.md)** - Complete API documentation
- **[Configuration Guide](docs/CONFIGURATION.md)** - Detailed configuration options

## 🤝 Contributing

1. **Fork the repository**
2. **Create a feature branch**: `git checkout -b feature/validation-enhancement`
3. **Make your changes** with tests
4. **Run the test suite**: `python -m pytest`
5. **Submit a pull request**

### Development Setup

```bash
# Install development dependencies
pip install -r requirements-dev.txt

# Run tests with coverage
python -m pytest --cov=swarm_director tests/

# Run linting
flake8 src/swarm_director/validation/
flake8 src/swarm_director/plugins/
```

## 🐛 Troubleshooting

### Common Issues

**Validation Failures**
- Check quality thresholds in configuration
- Review validation logs for specific issues
- Ensure agents have required capabilities

**Plugin Installation Failures**
- Verify internet connectivity
- Check dependency conflicts
- Review plugin registry status

**Performance Issues**
- Enable parallel processing
- Increase timeout settings
- Monitor resource usage

### Debug Mode

```python
import logging
logging.getLogger('swarm_director.validation').setLevel(logging.DEBUG)
logging.getLogger('swarm_director.plugins').setLevel(logging.DEBUG)
```

## 📈 Performance

### Benchmarks

- **Validation throughput**: 100+ tasks/minute
- **Plugin installation**: < 30 seconds average
- **Memory usage**: < 512MB for typical workloads
- **Startup time**: < 5 seconds

### Optimization Tips

1. **Enable caching** for validation results
2. **Use parallel processing** for multiple validations
3. **Configure appropriate timeouts**
4. **Regular cleanup** of old data

## 🔮 Future Roadmap

### Planned Features

- **ML-based validation** models
- **Visual validation dashboard**
- **Plugin marketplace** integration
- **Advanced analytics** and reporting
- **Multi-tenant support**
- **Cloud deployment** options

### Integration Plans

- **CI/CD pipeline** integration
- **External validation** services
- **Compliance frameworks**
- **Performance optimization**

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- SwarmDirector core team for the foundational architecture
- Contributors to the validation and plugin systems
- Community feedback and testing

---

**Ready to enhance your SwarmDirector with hierarchical validation and plugin capabilities? Start with the [Quick Start](#-quick-start) guide!**
