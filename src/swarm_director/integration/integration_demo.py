"""
Agent Integration Framework Demo

Demonstrates how the various components of the Agent Integration Framework
work together to enable seamless communication and coordination between agents.
"""

import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, Any

from .communication_bus import AgentCommunicationBus, Message, MessageType
from .service_registry import ServiceRegistry, AgentService, AgentCapability, ServiceType, AgentStatus
from .event_system import EventSystem, Event, EventType, EventFilter
from ..workflows.workflow_context import WorkflowContext
from ..workflows.state_manager import WorkflowStateManager, WorkflowState
from ..workflows.orchestrator import WorkflowOrchestrator

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockEmailAgent:
    """Mock email agent for demonstration purposes."""
    
    def __init__(self, agent_id: str, communication_bus: AgentCommunicationBus, 
                 service_registry: ServiceRegistry, event_system: EventSystem):
        self.agent_id = agent_id
        self.communication_bus = communication_bus
        self.service_registry = service_registry
        self.event_system = event_system
        
    async def start(self):
        """Start the agent and register services."""
        # Register with service registry
        capabilities = [
            AgentCapability(
                name="compose_email",
                description="Compose email messages",
                service_type=ServiceType.EMAIL_COMPOSITION,
                parameters={"max_length": 5000, "supports_html": True}
            ),
            AgentCapability(
                name="send_email",
                description="Send email via SMTP",
                service_type=ServiceType.EMAIL_DELIVERY,
                parameters={"smtp_server": "smtp.example.com"}
            )
        ]
        
        service = AgentService(
            agent_id=self.agent_id,
            name="Email Agent",
            description="Handles email composition and delivery",
            capabilities=capabilities,
            tags={"email", "communication"}
        )
        
        self.service_registry.register_service(service)
        
        # Register with communication bus
        self.communication_bus.register_agent(self.agent_id, {
            "name": "Email Agent",
            "capabilities": ["compose_email", "send_email"]
        })
        
        # Subscribe to task requests
        self.communication_bus.subscribe(
            MessageType.TASK_REQUEST,
            self._handle_task_request,
            self.agent_id
        )
        
        # Subscribe to workflow events
        workflow_filter = EventFilter(
            event_types={EventType.WORKFLOW_STARTED, EventType.WORKFLOW_COMPLETED}
        )
        self.event_system.subscribe(self._handle_workflow_event, workflow_filter, self.agent_id)
        
        logger.info(f"Mock Email Agent {self.agent_id} started")
    
    async def _handle_task_request(self, message: Message):
        """Handle incoming task requests."""
        if message.recipient_id != self.agent_id:
            return
            
        task_type = message.payload.get("task_type")
        
        if task_type == "compose_email":
            # Simulate email composition
            response = {
                "status": "success",
                "result": {
                    "subject": f"Email composed at {datetime.utcnow()}",
                    "body": "This is a mock email composition result",
                    "composition_time": 2.5
                }
            }
        elif task_type == "send_email":
            # Simulate email sending
            response = {
                "status": "success",
                "result": {
                    "message_id": f"msg_{datetime.utcnow().timestamp()}",
                    "sent_at": datetime.utcnow().isoformat(),
                    "delivery_time": 1.2
                }
            }
        else:
            response = {
                "status": "error",
                "error": f"Unknown task type: {task_type}"
            }
        
        # Send response
        await self.communication_bus.send_response(message, response, self.agent_id)
        
        # Publish task completion event
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            source=self.agent_id,
            payload={"task_type": task_type, "result": response},
            correlation_id=message.correlation_id
        )
        await self.event_system.publish(event)
    
    async def _handle_workflow_event(self, event: Event):
        """Handle workflow events."""
        logger.info(f"Email Agent received workflow event: {event.event_type.value}")


class MockReviewAgent:
    """Mock review agent for demonstration purposes."""
    
    def __init__(self, agent_id: str, communication_bus: AgentCommunicationBus,
                 service_registry: ServiceRegistry, event_system: EventSystem):
        self.agent_id = agent_id
        self.communication_bus = communication_bus
        self.service_registry = service_registry
        self.event_system = event_system
    
    async def start(self):
        """Start the agent and register services."""
        # Register with service registry
        capabilities = [
            AgentCapability(
                name="review_content",
                description="Review and validate content",
                service_type=ServiceType.DRAFT_REVIEW,
                parameters={"review_types": ["grammar", "tone", "accuracy"]}
            )
        ]
        
        service = AgentService(
            agent_id=self.agent_id,
            name="Review Agent",
            description="Reviews and validates content quality",
            capabilities=capabilities,
            tags={"review", "quality"}
        )
        
        self.service_registry.register_service(service)
        
        # Register with communication bus
        self.communication_bus.register_agent(self.agent_id, {
            "name": "Review Agent",
            "capabilities": ["review_content"]
        })
        
        # Subscribe to task requests
        self.communication_bus.subscribe(
            MessageType.TASK_REQUEST,
            self._handle_task_request,
            self.agent_id
        )
        
        logger.info(f"Mock Review Agent {self.agent_id} started")
    
    async def _handle_task_request(self, message: Message):
        """Handle incoming task requests."""
        if message.recipient_id != self.agent_id:
            return
            
        task_type = message.payload.get("task_type")
        
        if task_type == "review_content":
            # Simulate content review
            response = {
                "status": "success",
                "result": {
                    "review_score": 8.5,
                    "suggestions": [
                        "Consider more formal tone",
                        "Add call-to-action"
                    ],
                    "approved": True,
                    "review_time": 3.1
                }
            }
        else:
            response = {
                "status": "error",
                "error": f"Unknown task type: {task_type}"
            }
        
        # Send response
        await self.communication_bus.send_response(message, response, self.agent_id)
        
        # Publish task completion event
        event = Event(
            event_type=EventType.TASK_COMPLETED,
            source=self.agent_id,
            payload={"task_type": task_type, "result": response},
            correlation_id=message.correlation_id
        )
        await self.event_system.publish(event)


async def demo_integration_framework():
    """
    Comprehensive demonstration of the Agent Integration Framework.
    """
    logger.info("=== Agent Integration Framework Demo ===")
    
    # Initialize core components
    communication_bus = AgentCommunicationBus()
    service_registry = ServiceRegistry()
    event_system = EventSystem()
    
    # Create a demo workflow context (we'll create specific workflows later)
    demo_workflow_id = "demo_workflow_001"
    workflow_context = WorkflowContext(demo_workflow_id)
    workflow_state_manager = WorkflowStateManager()
    
    # Start services
    await communication_bus.start()
    await event_system.start()
    
    # Create mock agents
    email_agent = MockEmailAgent("email_agent_1", communication_bus, service_registry, event_system)
    review_agent = MockReviewAgent("review_agent_1", communication_bus, service_registry, event_system)
    
    # Start agents
    await email_agent.start()
    await review_agent.start()
    
    # Wait for agents to register
    await asyncio.sleep(1)
    
    # Demonstrate service discovery
    logger.info("\n=== Service Discovery Demo ===")
    email_services = service_registry.discover_services(
        service_type=ServiceType.EMAIL_COMPOSITION,
        status=AgentStatus.ACTIVE
    )
    logger.info(f"Found {len(email_services)} email composition services")
    
    review_services = service_registry.discover_services(
        service_type=ServiceType.DRAFT_REVIEW,
        status=AgentStatus.ACTIVE
    )
    logger.info(f"Found {len(review_services)} draft review services")
    
    # Demonstrate direct messaging
    logger.info("\n=== Direct Messaging Demo ===")
    
    # Send task request to email agent
    compose_request = Message(
        sender_id="demo_orchestrator",
        recipient_id="email_agent_1",
        message_type=MessageType.TASK_REQUEST,
        payload={
            "task_type": "compose_email",
            "subject": "Demo Email",
            "content": "This is a demo email composition request"
        }
    )
    
    response = await communication_bus.send_request(
        "email_agent_1",
        MessageType.TASK_REQUEST,
        compose_request.payload,
        timeout=10.0,
        sender_id="demo_orchestrator"
    )
    
    if response:
        logger.info(f"Email composition response: {response.payload}")
    else:
        logger.error("No response received from email agent")
    
    # Send task request to review agent
    review_request = Message(
        sender_id="demo_orchestrator",
        recipient_id="review_agent_1",
        message_type=MessageType.TASK_REQUEST,
        payload={
            "task_type": "review_content",
            "content": "Sample content for review",
            "review_type": "grammar"
        }
    )
    
    response = await communication_bus.send_request(
        "review_agent_1",
        MessageType.TASK_REQUEST,
        review_request.payload,
        timeout=10.0,
        sender_id="demo_orchestrator"
    )
    
    if response:
        logger.info(f"Review response: {response.payload}")
    else:
        logger.error("No response received from review agent")
    
    # Demonstrate workflow events
    logger.info("\n=== Workflow Events Demo ===")
    
    # Use the existing workflow context
    workflow_id = demo_workflow_id
    
    # Set some workflow context
    workflow_context.set("email_draft", {
        "subject": "Demo Workflow Email",
        "recipient": "demo@example.com"
    }, agent_name="demo_orchestrator")
    
    # Publish workflow started event
    workflow_event = Event(
        event_type=EventType.WORKFLOW_STARTED,
        source="demo_orchestrator",
        payload={
            "workflow_name": "Email Composition Workflow",
            "steps": ["compose", "review", "send"]
        },
        correlation_id=workflow_id,
        metadata={"workflow_id": workflow_id}
    )
    
    await event_system.publish(workflow_event)
    
    # Wait for event processing
    await asyncio.sleep(2)
    
    # Publish workflow completed event
    completion_event = Event(
        event_type=EventType.WORKFLOW_COMPLETED,
        source="demo_orchestrator",
        payload={
            "workflow_name": "Email Composition Workflow",
            "duration": 15.5,
            "steps_completed": 3
        },
        correlation_id=workflow_id,
        metadata={"workflow_id": workflow_id}
    )
    
    await event_system.publish(completion_event)
    
    # Demonstrate registry statistics
    logger.info("\n=== Registry Statistics ===")
    stats = service_registry.get_registry_stats()
    logger.info(f"Registry stats: {stats}")
    
    # Demonstrate event system statistics
    event_stats = event_system.get_statistics()
    logger.info(f"Event system stats: {event_stats}")
    
    # Demonstrate message history
    logger.info("\n=== Message History ===")
    recent_messages = communication_bus.get_message_history(
        since=datetime.utcnow() - timedelta(minutes=5)
    )
    logger.info(f"Recent messages: {len(recent_messages)}")
    
    # Demonstrate event history
    recent_events = event_system.get_event_history(limit=5)
    logger.info(f"Recent events: {len(recent_events)}")
    for event in recent_events:
        logger.info(f"  - {event.event_type.value} from {event.source}")
    
    # Wait a bit more for any pending operations
    await asyncio.sleep(2)
    
    # Cleanup
    logger.info("\n=== Cleanup ===")
    await communication_bus.stop()
    await event_system.stop()
    
    logger.info("Demo completed successfully!")


if __name__ == "__main__":
    asyncio.run(demo_integration_framework()) 