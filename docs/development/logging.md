# Enhanced Logging and Monitoring System

## Overview

SwarmDirector now includes a comprehensive structured logging and monitoring system that provides:

- **Structured JSON Logging**: All logs are output in consistent JSON format
- **Correlation Tracking**: Unique identifiers to track requests across components
- **Performance Metrics**: Automatic collection of system and application metrics
- **Flexible Configuration**: Support for multiple output destinations
- **Backward Compatibility**: Existing logging calls continue to work

## Quick Start

```python
from swarm_director.utils.logging import setup_structured_logging, log_agent_action

# Initialize enhanced logging
setup_structured_logging(log_level=logging.INFO)

# Log agent actions with automatic metrics
log_agent_action('MyAgent', 'process_request', {'user_id': '123'})
```

## Key Features

### 1. Structured JSON Output

All logs are formatted as JSON with consistent fields:

```json
{
  "timestamp": "2025-06-13T04:41:28.520838Z",
  "level": "INFO",
  "logger": "swarm_director.agents",
  "message": "TestAgent: integration_test",
  "module": "logging",
  "function": "log_agent_action",
  "line": 303,
  "correlation_id": "test-integration-123",
  "event_type": "agent_action",
  "system_metrics": {
    "cpu_percent": 35.4,
    "memory_percent": 68.1,
    "memory_available_mb": 5234.26
  }
}
```

### 2. Correlation ID Tracking

Track related operations across your application:

```python
from swarm_director.utils.logging import set_correlation_id, correlation_context

# Set correlation ID for current thread
correlation_id = set_correlation_id('user-session-123')

# Use context manager for scoped correlation
with correlation_context('request-456') as corr_id:
    log_agent_action('Agent', 'process', {'data': 'value'})
```

### 3. Performance Monitoring

Automatic performance timing with decorator:

```python
from swarm_director.utils.logging import performance_timer

@performance_timer
def slow_operation():
    # This function's execution time will be automatically logged
    time.sleep(1)
    return "result"
```

### 4. Enhanced Logging Functions

#### Agent Actions
```python
log_agent_action(
    agent_name='DataProcessor',
    action='process_file',
    details={'file_size': 1024, 'format': 'json'},
    include_metrics=True  # Include system metrics
)
```

#### Task Updates
```python
log_task_update(
    task_id='task-123',
    status='completed',
    details={'duration_ms': 1500, 'items_processed': 42}
)
```

#### Conversation Events
```python
log_conversation_event(
    conversation_id='conv-789',
    event='message_received',
    details={'message_type': 'text', 'participant_count': 2}
)
```

#### Performance Metrics
```python
log_performance_metric(
    metric_name='response_time',
    value=250.5,
    unit='ms',
    context={'endpoint': '/api/agents', 'method': 'POST'}
)
```

#### Error Logging with Context
```python
try:
    risky_operation()
except Exception as e:
    log_error_with_context(
        error=e,
        context={'user_id': 'user-123', 'operation': 'data_processing'}
    )
```

## Configuration

### Basic Setup

```python
from swarm_director.utils.logging import setup_structured_logging
import logging

# Basic configuration
setup_structured_logging(
    app=flask_app,  # Optional Flask app
    log_level=logging.INFO,
    enable_database_logging=False,  # Enable for DB logging
    db_session=None  # Database session for DB logging
)
```

### File Output

Logs are automatically written to:
- `logs/swarm_director.log` (rotating, 10MB max, 5 backups)
- Console output (structured JSON)

### Performance Metrics

The system automatically collects:

**System Metrics:**
- CPU percentage
- Memory usage and availability
- Disk usage and free space
- Process count

**Process Metrics:**
- Current process CPU usage
- Memory consumption
- Thread count
- Open file handles
- Network connections

## Integration with Existing Code

### Backward Compatibility

All existing logging calls continue to work:

```python
# These still work as before
from swarm_director.utils.logging import log_agent_action, log_task_update

log_agent_action('Agent', 'action')  # Works with new features
log_task_update('task-1', 'done')    # Automatically enhanced
```

### Migration Guide

1. **Update imports** (optional):
   ```python
   # Old way (still works)
   from swarm_director.utils.logging import setup_logging
   
   # New way (recommended)
   from swarm_director.utils.logging import setup_structured_logging
   ```

2. **Initialize enhanced logging**:
   ```python
   # Replace setup_logging() with setup_structured_logging()
   setup_structured_logging(app, log_level=logging.INFO)
   ```

3. **Add correlation tracking** where needed:
   ```python
   # At request boundaries
   set_correlation_id(request.headers.get('X-Correlation-ID'))
   ```

## Best Practices

1. **Use correlation IDs** for tracking related operations
2. **Include relevant context** in log details
3. **Use appropriate log levels** (DEBUG, INFO, WARNING, ERROR)
4. **Leverage performance timing** for critical operations
5. **Structure your log data** consistently across the application

## Troubleshooting

### Common Issues

1. **Import errors**: Ensure `structlog` and `psutil` are installed
2. **Performance impact**: Disable metrics collection if needed
3. **Log file permissions**: Ensure `logs/` directory is writable

### Debugging

Enable debug logging to see detailed information:

```python
setup_structured_logging(log_level=logging.DEBUG)
```

## Next Steps

This implementation provides the foundation for:
- Dashboard visualization (Task 11.2)
- Alerting systems (Task 11.3)
- Database integration
- Advanced analytics and reporting 