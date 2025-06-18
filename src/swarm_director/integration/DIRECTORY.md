---
title: Integration Services Directory
description: Integration and communication services for SwarmDirector
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [integration, communication, events, services]
---

# Integration Services Directory

## Purpose

The integration directory contains services and utilities for integrating SwarmDirector with external systems, managing inter-service communication, and handling event-driven architecture. This module provides the foundation for scalable, loosely-coupled system integration.

## Structure

```
src/swarm_director/integration/
├── __init__.py                  # Integration module initialization
├── communication_bus.py         # Inter-service communication bus
├── event_system.py             # Event-driven architecture system
├── service_registry.py         # Service discovery and registration
├── integration_demo.py         # Integration demonstration examples
├── adapters/                   # External system adapters
│   ├── autogen_adapter.py      # AutoGen framework integration
│   ├── webhook_adapter.py      # Webhook integration adapter
│   ├── api_adapter.py          # REST API integration adapter
│   └── message_queue_adapter.py # Message queue integration
├── protocols/                  # Communication protocols
│   ├── http_protocol.py        # HTTP communication protocol
│   ├── websocket_protocol.py   # WebSocket communication protocol
│   ├── grpc_protocol.py        # gRPC communication protocol
│   └── message_protocol.py     # Message-based communication
└── middleware/                 # Integration middleware
    ├── authentication.py       # Authentication middleware
    ├── rate_limiting.py        # Rate limiting middleware
    ├── logging_middleware.py   # Request/response logging
    └── error_handling.py       # Error handling middleware
```

## Guidelines

### 1. Organization
- **Modular Architecture**: Separate adapters, protocols, and middleware
- **Loose Coupling**: Design for minimal dependencies between components
- **Event-Driven**: Use event-driven patterns for asynchronous communication
- **Service Discovery**: Implement service registry for dynamic service discovery

### 2. Naming
- **Adapters**: Use `*_adapter.py` for external system integrations
- **Protocols**: Use `*_protocol.py` for communication protocol implementations
- **Middleware**: Use descriptive names for middleware components
- **Events**: Use clear, descriptive event names (e.g., `agent.task.completed`)

### 3. Implementation
- **Async/Await**: Use async patterns for non-blocking operations
- **Error Resilience**: Implement circuit breakers and retry mechanisms
- **Configuration**: Use configuration files for integration settings
- **Monitoring**: Include comprehensive logging and metrics
- **Security**: Implement proper authentication and authorization

### 4. Documentation
- **Integration Guides**: Document how to integrate with external systems
- **Protocol Documentation**: Document communication protocols and message formats
- **API Documentation**: Document integration APIs and endpoints
- **Configuration Reference**: Document all configuration options

## Best Practices

### Error Handling
```python
import logging
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)

class IntegrationAdapter:
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=4, max=10)
    )
    async def send_request(self, endpoint: str, data: Dict[str, Any]) -> Optional[Dict]:
        try:
            response = await self._make_request(endpoint, data)
            return response
        except ConnectionError as e:
            logger.error(f"Connection failed to {endpoint}: {e}")
            raise
        except TimeoutError as e:
            logger.warning(f"Request timeout to {endpoint}: {e}")
            raise
```

### Security
- **Authentication**: Implement proper authentication for all integrations
- **Authorization**: Use role-based access control for integration endpoints
- **Encryption**: Encrypt sensitive data in transit and at rest
- **Input Validation**: Validate all incoming data from external systems

### Performance
- **Connection Pooling**: Use connection pools for external API calls
- **Caching**: Cache frequently accessed integration data
- **Async Processing**: Use async processing for non-blocking operations
- **Load Balancing**: Implement load balancing for high-availability integrations

### Testing
```python
import pytest
from unittest.mock import AsyncMock, patch
from src.swarm_director.integration.communication_bus import CommunicationBus

@pytest.fixture
async def communication_bus():
    bus = CommunicationBus()
    await bus.initialize()
    yield bus
    await bus.shutdown()

@pytest.mark.asyncio
async def test_event_publishing(communication_bus):
    # Test event publishing
    event_data = {"agent_id": "test_agent", "status": "completed"}
    await communication_bus.publish("agent.task.completed", event_data)
    
    # Verify event was published
    published_events = await communication_bus.get_published_events()
    assert len(published_events) == 1
    assert published_events[0]["event_type"] == "agent.task.completed"
```

### Documentation
- **Integration Patterns**: Document common integration patterns
- **Error Handling**: Document error handling strategies
- **Configuration Examples**: Provide configuration examples
- **Troubleshooting**: Include troubleshooting guides

## Examples

### Event System Usage
```python
from src.swarm_director.integration.event_system import EventSystem

# Initialize event system
event_system = EventSystem()

# Subscribe to events
@event_system.subscribe("agent.task.completed")
async def handle_task_completion(event_data):
    agent_id = event_data["agent_id"]
    task_id = event_data["task_id"]
    logger.info(f"Agent {agent_id} completed task {task_id}")

# Publish events
await event_system.publish("agent.task.completed", {
    "agent_id": "agent_001",
    "task_id": "task_123",
    "completion_time": datetime.utcnow().isoformat()
})
```

### Service Registry Usage
```python
from src.swarm_director.integration.service_registry import ServiceRegistry

# Register a service
registry = ServiceRegistry()
await registry.register_service(
    service_name="analytics_service",
    endpoint="http://localhost:8001",
    health_check_url="http://localhost:8001/health",
    metadata={"version": "1.0.0", "capabilities": ["metrics", "reporting"]}
)

# Discover services
analytics_service = await registry.discover_service("analytics_service")
if analytics_service:
    endpoint = analytics_service["endpoint"]
    # Use the service endpoint
```

### External API Integration
```python
from src.swarm_director.integration.adapters.api_adapter import APIAdapter

class ExternalServiceAdapter(APIAdapter):
    def __init__(self, base_url: str, api_key: str):
        super().__init__(base_url)
        self.api_key = api_key
    
    async def send_notification(self, message: str, recipient: str) -> bool:
        payload = {
            "message": message,
            "recipient": recipient,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        headers = {"Authorization": f"Bearer {self.api_key}"}
        
        try:
            response = await self.post("/notifications", payload, headers=headers)
            return response.get("success", False)
        except Exception as e:
            logger.error(f"Failed to send notification: {e}")
            return False
```

## Related Documentation

- [Integration API Documentation](../../docs/api/integration.md) - Integration API reference
- [Event System Guide](../../docs/architecture/events.md) - Event-driven architecture guide
- [Service Discovery](../../docs/architecture/service_discovery.md) - Service discovery documentation
- [External Integrations](../../docs/development/integrations.md) - External integration guide
- [Communication Protocols](../../docs/architecture/protocols.md) - Communication protocol documentation
- [Configuration Guide](../../config/integration.yaml) - Integration configuration options
