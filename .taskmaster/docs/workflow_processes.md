# SwarmDirector Workflow Processes & Automation Integration

## Overview

This document outlines the enhanced workflow processes for SwarmDirector, now integrated with Taskmaster task management and automation systems. The integration provides automated task tracking, workflow monitoring, and comprehensive reporting capabilities.

## Automation Integration Architecture

### Core Components

1. **AutomationIntegrator** (`src/swarm_director/utils/automation.py`)
   - Central hub for task management events
   - Webhook integration for external systems
   - Async event processing
   - Task synchronization capabilities

2. **Workflow Configuration** (`.taskmaster/config/workflow.yaml`)
   - Task integration settings
   - Automation triggers
   - Monitoring and alerting configurations
   - Environment-specific overrides

3. **CI/CD Pipeline** (`.github/workflows/task_management_integration.yml`)
   - Automated testing with task status updates
   - Environment-specific deployments
   - Integration with external task management systems

## Development Workflow Process

### 1. Environment Setup (`scripts/setup_development.py`)

**Automated Task Events:**
- `TASK_STARTED`: Development environment setup initiated
- `BUILD_STARTED`/`BUILD_COMPLETED`/`BUILD_FAILED`: Dependency installation
- `DEPLOYMENT_STARTED`/`DEPLOYMENT_COMPLETED`/`DEPLOYMENT_FAILED`: Database setup

**Integration Points:**
```python
# Task event triggered at start
trigger_task_event(AutomationEventType.TASK_STARTED, task_id="dev_setup", 
                  metadata={"workflow": "development_environment_setup"})

# Build events during dependency installation
trigger_task_event(AutomationEventType.BUILD_STARTED, 
                  metadata={"action": "installing_dependencies"})
```

**Make Command Integration:**
```bash
make setup  # Triggers DEPLOYMENT_STARTED/COMPLETED/FAILED events
```

### 2. Testing Workflow (`scripts/run_tests.py`)

**Automated Task Events:**
- `TASK_STARTED`: Test suite execution begins
- `TASK_COMPLETED`/`TASK_FAILED`: Individual test result reporting
- Test type tracking (pytest, standalone, coverage)

**Integration Points:**
```python
# Main test suite tracking
trigger_task_event(AutomationEventType.TASK_STARTED, task_id="test_suite", 
                  metadata={"test_runner": "main", "args": vars(args)})

# Individual pytest run tracking
trigger_task_event(AutomationEventType.TASK_STARTED, task_id="pytest_run", 
                  metadata={"test_type": "pytest", "coverage": coverage})
```

**Make Command Integration:**
```bash
make test           # All tests with task tracking
make test-verbose   # Verbose tests with tracking
make test-coverage  # Coverage tests with tracking
make test-single TEST=<file>  # Single test with tracking
```

### 3. Makefile Automation Enhancement

**Task Management Functions:**
- `task-event`: Generic task event triggering
- Automatic success/failure reporting
- Timestamped event metadata

**Example Usage:**
```make
test:
	@$(call task-event,TASK_STARTED,make_test,'{"action":"test","type":"all"}')
	@python scripts/run_tests.py && \
		$(call task-event,TASK_COMPLETED,make_test,'{"success":true}') || \
		($(call task-event,TASK_FAILED,make_test,'{"success":false}') && exit 1)
```

## Event Types and Metadata

### Event Type Categories

1. **Task Events**
   - `TASK_STARTED`: Task execution begins
   - `TASK_COMPLETED`: Task completes successfully
   - `TASK_FAILED`: Task fails or encounters errors

2. **Build Events**
   - `BUILD_STARTED`: Build process initiated
   - `BUILD_COMPLETED`: Build completes successfully
   - `BUILD_FAILED`: Build fails

3. **Deployment Events**
   - `DEPLOYMENT_STARTED`: Deployment begins
   - `DEPLOYMENT_COMPLETED`: Deployment succeeds
   - `DEPLOYMENT_FAILED`: Deployment fails

4. **Test Events**
   - `TEST_STARTED`: Test execution begins
   - `TEST_PASSED`: Tests pass
   - `TEST_FAILED`: Tests fail

### Metadata Standards

**Standard Fields:**
```json
{
  "timestamp": "2024-01-15T10:30:00.000Z",
  "workflow": "development_environment_setup",
  "action": "database_setup",
  "success": true,
  "error": "error_description_if_failed"
}
```

**Test-Specific Fields:**
```json
{
  "test_type": "pytest",
  "coverage": true,
  "specific_test": "test_file.py",
  "exit_code": 0,
  "test_passed": true
}
```

## Workflow Monitoring

### Task Status Tracking

All automation scripts now report:
- Start times and durations
- Success/failure status
- Error details and context
- Performance metrics

### Integration Hooks

**Webhook Integration:**
```python
integrator = AutomationIntegrator()
integrator.register_webhook("https://taskmanager.example.com/webhook")
```

**Custom Event Handlers:**
```python
async def custom_handler(event_type, task_id, metadata):
    # Custom processing logic
    await process_event(event_type, task_id, metadata)

integrator.register_handler(AutomationEventType.TASK_COMPLETED, custom_handler)
```

## Configuration Management

### Workflow Configuration (`.taskmaster/config/workflow.yaml`)

Key sections:
- **task_integration**: Core task management settings
- **automation_triggers**: Event-based automation rules
- **monitoring**: Alerting and notification settings
- **environments**: Environment-specific configurations

### Environment Variables

Required for external integrations:
- `TASKMASTER_WEBHOOK_URL`: External task management webhook
- `AUTOMATION_SECRET_KEY`: Security key for webhook authentication
- `WORKFLOW_ENVIRONMENT`: Current environment (dev/staging/prod)

## CI/CD Integration

### GitHub Actions Workflow

The task management integration workflow:
1. Runs on push/PR events
2. Executes test suite with task tracking
3. Reports status to external systems
4. Handles environment-specific deployments

### Pipeline Stages

1. **Setup**: Environment preparation with task events
2. **Test**: Comprehensive testing with result reporting
3. **Build**: Application building with status tracking
4. **Deploy**: Environment-specific deployment

## Best Practices

### Error Handling

1. **Graceful Degradation**: Scripts continue if task integration fails
2. **Detailed Logging**: All events include comprehensive metadata
3. **Retry Logic**: Automatic retry for transient failures

### Performance Considerations

1. **Async Processing**: Events processed asynchronously to avoid blocking
2. **Batch Processing**: Multiple events can be batched for efficiency
3. **Caching**: Configuration and integrator instances are cached

### Security

1. **Webhook Authentication**: Secure authentication for external webhooks
2. **Metadata Sanitization**: Sensitive data filtered from event metadata
3. **Access Control**: Role-based access to automation controls

## Troubleshooting

### Common Issues

1. **Task Integration Not Available**
   - Check if `automation.py` module is accessible
   - Verify Python path includes `src` directory
   - Ensure dependencies are installed

2. **Webhook Failures**
   - Verify webhook URL configuration
   - Check network connectivity
   - Validate authentication credentials

3. **Event Processing Delays**
   - Monitor async task queues
   - Check system resource availability
   - Review event batching settings

### Debug Commands

```bash
# Test task integration
python -c "from swarm_director.utils.automation import AutomationIntegrator; print('Integration available')"

# Test webhook connectivity
curl -X POST $TASKMASTER_WEBHOOK_URL -H "Content-Type: application/json" -d '{"test": true}'

# Validate workflow configuration
python -c "import yaml; print(yaml.safe_load(open('.taskmaster/config/workflow.yaml')))"
```

## Migration Guide

### Updating Existing Scripts

To add task integration to existing scripts:

1. **Import Integration Module**:
   ```python
   try:
       from swarm_director.utils.automation import AutomationIntegrator, AutomationEventType
       TASK_INTEGRATION_AVAILABLE = True
   except ImportError:
       TASK_INTEGRATION_AVAILABLE = False
   ```

2. **Add Event Trigger Function**:
   ```python
   def trigger_task_event(event_type, task_id=None, status=None, metadata=None):
       if not TASK_INTEGRATION_AVAILABLE:
           return
       try:
           integrator = AutomationIntegrator()
           integrator.trigger_event(event_type, task_id=task_id, status=status, metadata=metadata)
       except Exception as e:
           print(f"⚠️  Task event trigger failed: {e}")
   ```

3. **Add Event Calls**:
   ```python
   # At function start
   trigger_task_event(AutomationEventType.TASK_STARTED, task_id="unique_id")
   
   # On success
   trigger_task_event(AutomationEventType.TASK_COMPLETED, task_id="unique_id")
   
   # On failure
   trigger_task_event(AutomationEventType.TASK_FAILED, task_id="unique_id")
   ```

### Updating Makefile Targets

To add task integration to Makefile:

1. **Add Task Integration Script**:
   ```make
   TASK_INTEGRATION_SCRIPT := python -c "import sys; sys.path.insert(0, 'src'); \
       try: \
           from swarm_director.utils.automation import AutomationIntegrator, AutomationEventType; \
           integrator = AutomationIntegrator(); \
           integrator.trigger_event(AutomationEventType.$(EVENT_TYPE), task_id='$(TASK_ID)', metadata=$(METADATA)); \
       except: pass;"
   ```

2. **Add Event Helper**:
   ```make
   define task-event
       @EVENT_TYPE=$(1) TASK_ID=$(2) METADATA=$(3) $(TASK_INTEGRATION_SCRIPT)
   endef
   ```

3. **Update Targets**:
   ```make
   target:
       @$(call task-event,TASK_STARTED,target_name,'{"action":"target"}')
       @command && \
           $(call task-event,TASK_COMPLETED,target_name,'{"success":true}') || \
           ($(call task-event,TASK_FAILED,target_name,'{"success":false}') && exit 1)
   ```

## Conclusion

The enhanced workflow processes provide comprehensive task management integration while maintaining backward compatibility. The automation system enables better visibility into development workflows, improved error tracking, and seamless integration with external task management systems.

For additional support or questions, refer to the [automation integration documentation](automation_integration.md) or contact the development team. 