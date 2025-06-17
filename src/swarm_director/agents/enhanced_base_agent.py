"""
Enhanced Base Agent

Extends the existing BaseAgent with integration framework capabilities.
Provides seamless integration with the WorkflowOrchestrator, CommunicationBus,
ServiceRegistry, and EventSystem.
"""

import asyncio
import logging
import uuid
from abc import ABC, abstractmethod
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Set

from ..agents.base_agent import BaseAgent
from ..integration.communication_bus import AgentCommunicationBus, Message, MessageType
from ..integration.service_registry import ServiceRegistry, AgentService, AgentCapability, AgentStatus, ServiceType
from ..integration.event_system import EventSystem, Event, EventType, EventFilter
from ..workflows.workflow_context import WorkflowContext
from ..workflows.state_manager import WorkflowStateManager

logger = logging.getLogger(__name__)


class EnhancedBaseAgent(BaseAgent):
    """
    Enhanced base agent with integration framework capabilities.
    
    Provides:
    - Integration with communication bus
    - Service registry participation
    - Event-driven communication
    - Workflow context sharing
    - Health monitoring and heartbeat
    """

    def __init__(self, agent_id: str, name: str, description: str,
                 capabilities: List[AgentCapability],
                 communication_bus: Optional[AgentCommunicationBus] = None,
                 service_registry: Optional[ServiceRegistry] = None,
                 event_system: Optional[EventSystem] = None,
                 workflow_context: Optional[WorkflowContext] = None,
                 **kwargs):
        """
        Initialize the enhanced agent.
        
        Args:
            agent_id: Unique identifier for the agent
            name: Human-readable name
            description: Agent description
            capabilities: List of agent capabilities
            communication_bus: Communication bus instance
            service_registry: Service registry instance
            event_system: Event system instance
            workflow_context: Workflow context instance
            **kwargs: Additional arguments for BaseAgent
        """
        super().__init__(**kwargs)
        
        self.agent_id = agent_id
        self.name = name
        self.description = description
        self.capabilities = capabilities
        
        # Integration components
        self.communication_bus = communication_bus
        self.service_registry = service_registry
        self.event_system = event_system
        self.workflow_context = workflow_context
        
        # Agent state
        self.status = AgentStatus.INACTIVE
        self.metadata: Dict[str, Any] = {}
        self.tags: Set[str] = set()
        
        # Internal state
        self._running = False
        self._heartbeat_task: Optional[asyncio.Task] = None
        self._subscription_ids: List[str] = []
        self._current_workflow_id: Optional[str] = None
        
        logger.info(f"EnhancedBaseAgent {self.agent_id} initialized")

    async def start(self):
        """Start the agent and register with integration services."""
        if self._running:
            return

        try:
            self._running = True
            self.status = AgentStatus.ACTIVE
            
            # Register with service registry
            if self.service_registry:
                await self._register_with_service_registry()
            
            # Subscribe to events
            if self.event_system:
                await self._setup_event_subscriptions()
            
            # Subscribe to communication bus messages
            if self.communication_bus:
                await self._setup_message_subscriptions()
            
            # Start heartbeat
            self._heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # Publish agent started event
            if self.event_system:
                event = Event(
                    event_type=EventType.AGENT_REGISTERED,
                    source=self.agent_id,
                    payload={
                        'name': self.name,
                        'capabilities': [cap.name for cap in self.capabilities],
                        'status': self.status.value
                    },
                    tags={'agent', 'lifecycle'}
                )
                await self.event_system.publish(event)
            
            logger.info(f"Agent {self.agent_id} started successfully")
            
        except Exception as e:
            logger.error(f"Failed to start agent {self.agent_id}: {e}")
            self.status = AgentStatus.ERROR
            raise

    async def stop(self):
        """Stop the agent and cleanup resources."""
        if not self._running:
            return

        try:
            self._running = False
            self.status = AgentStatus.INACTIVE
            
            # Stop heartbeat
            if self._heartbeat_task:
                self._heartbeat_task.cancel()
                try:
                    await self._heartbeat_task
                except asyncio.CancelledError:
                    pass
            
            # Unsubscribe from events
            if self.event_system:
                for subscription_id in self._subscription_ids:
                    self.event_system.unsubscribe(subscription_id, self.agent_id)
                self._subscription_ids.clear()
            
            # Unregister from service registry
            if self.service_registry:
                self.service_registry.unregister_service(self.agent_id)
            
            # Unregister from communication bus
            if self.communication_bus:
                self.communication_bus.unregister_agent(self.agent_id)
            
            # Publish agent stopped event
            if self.event_system:
                event = Event(
                    event_type=EventType.AGENT_UNREGISTERED,
                    source=self.agent_id,
                    payload={'name': self.name, 'status': self.status.value},
                    tags={'agent', 'lifecycle'}
                )
                await self.event_system.publish(event)
            
            logger.info(f"Agent {self.agent_id} stopped successfully")
            
        except Exception as e:
            logger.error(f"Error stopping agent {self.agent_id}: {e}")

    async def _register_with_service_registry(self):
        """Register this agent with the service registry."""
        service = AgentService(
            agent_id=self.agent_id,
            name=self.name,
            description=self.description,
            capabilities=self.capabilities,
            status=self.status,
            metadata=self.metadata,
            tags=self.tags
        )
        
        success = self.service_registry.register_service(service)
        if not success:
            raise RuntimeError(f"Failed to register agent {self.agent_id} with service registry")

    async def _setup_event_subscriptions(self):
        """Setup event subscriptions for this agent."""
        # Subscribe to workflow events
        workflow_filter = EventFilter(
            event_types={
                EventType.WORKFLOW_STARTED,
                EventType.WORKFLOW_COMPLETED,
                EventType.WORKFLOW_FAILED,
                EventType.WORKFLOW_PAUSED,
                EventType.WORKFLOW_RESUMED
            }
        )
        
        subscription_id = self.event_system.subscribe(
            self._handle_workflow_event,
            workflow_filter,
            self.agent_id
        )
        self._subscription_ids.append(subscription_id)
        
        # Subscribe to system events
        system_filter = EventFilter(
            event_types={
                EventType.SYSTEM_STARTUP,
                EventType.SYSTEM_SHUTDOWN,
                EventType.SYSTEM_ERROR
            }
        )
        
        subscription_id = self.event_system.subscribe(
            self._handle_system_event,
            system_filter,
            self.agent_id
        )
        self._subscription_ids.append(subscription_id)

    async def _setup_message_subscriptions(self):
        """Setup message subscriptions for communication bus."""
        # Register agent
        self.communication_bus.register_agent(self.agent_id, {
            'name': self.name,
            'capabilities': [cap.name for cap in self.capabilities],
            'status': self.status.value
        })
        
        # Subscribe to task requests
        self.communication_bus.subscribe(
            MessageType.TASK_REQUEST,
            self._handle_task_request,
            self.agent_id
        )
        
        # Subscribe to status updates
        self.communication_bus.subscribe(
            MessageType.STATUS_UPDATE,
            self._handle_status_update,
            self.agent_id
        )

    async def _heartbeat_loop(self):
        """Background heartbeat loop."""
        while self._running:
            try:
                await asyncio.sleep(30)  # Heartbeat every 30 seconds
                
                # Update service registry heartbeat
                if self.service_registry:
                    self.service_registry.heartbeat(self.agent_id)
                
                # Update communication bus heartbeat
                if self.communication_bus:
                    self.communication_bus.update_agent_heartbeat(self.agent_id)
                
                # Publish heartbeat event
                if self.event_system:
                    event = Event(
                        event_type=EventType.AGENT_STATUS_CHANGED,
                        source=self.agent_id,
                        payload={
                            'status': self.status.value,
                            'heartbeat': datetime.utcnow().isoformat()
                        },
                        tags={'agent', 'heartbeat'}
                    )
                    await self.event_system.publish(event)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in heartbeat loop for {self.agent_id}: {e}")

    async def _handle_workflow_event(self, event: Event):
        """Handle workflow-related events."""
        try:
            if event.event_type == EventType.WORKFLOW_STARTED:
                workflow_id = event.metadata.get('workflow_id')
                if workflow_id:
                    self._current_workflow_id = workflow_id
                    await self.on_workflow_started(workflow_id, event.payload)
                    
            elif event.event_type == EventType.WORKFLOW_COMPLETED:
                workflow_id = event.metadata.get('workflow_id')
                if workflow_id == self._current_workflow_id:
                    await self.on_workflow_completed(workflow_id, event.payload)
                    self._current_workflow_id = None
                    
            elif event.event_type == EventType.WORKFLOW_FAILED:
                workflow_id = event.metadata.get('workflow_id')
                if workflow_id == self._current_workflow_id:
                    await self.on_workflow_failed(workflow_id, event.payload)
                    self._current_workflow_id = None
                    
        except Exception as e:
            logger.error(f"Error handling workflow event in {self.agent_id}: {e}")

    async def _handle_system_event(self, event: Event):
        """Handle system-wide events."""
        try:
            if event.event_type == EventType.SYSTEM_SHUTDOWN:
                logger.info(f"Agent {self.agent_id} received system shutdown event")
                await self.stop()
                
        except Exception as e:
            logger.error(f"Error handling system event in {self.agent_id}: {e}")

    async def _handle_task_request(self, message: Message):
        """Handle task request messages."""
        try:
            # Only process messages directed to this agent
            if message.recipient_id and message.recipient_id != self.agent_id:
                return
                
            # Process the task request
            response_payload = await self.process_task_request(message.payload)
            
            # Send response
            if self.communication_bus:
                await self.communication_bus.send_response(
                    message, 
                    response_payload,
                    self.agent_id
                )
                
        except Exception as e:
            logger.error(f"Error handling task request in {self.agent_id}: {e}")
            
            # Send error response
            error_payload = {
                'error': str(e),
                'status': 'failed'
            }
            
            if self.communication_bus:
                await self.communication_bus.send_response(
                    message,
                    error_payload,
                    self.agent_id
                )

    async def _handle_status_update(self, message: Message):
        """Handle status update messages."""
        try:
            if message.payload.get('target_agent_id') == self.agent_id:
                new_status = message.payload.get('status')
                if new_status:
                    await self.update_status(AgentStatus(new_status))
                    
        except Exception as e:
            logger.error(f"Error handling status update in {self.agent_id}: {e}")

    async def update_status(self, new_status: AgentStatus, metadata: Optional[Dict[str, Any]] = None):
        """
        Update agent status and notify integration services.
        
        Args:
            new_status: New status for the agent
            metadata: Optional metadata to include
        """
        old_status = self.status
        self.status = new_status
        
        # Update service registry
        if self.service_registry:
            self.service_registry.update_service_status(self.agent_id, new_status, metadata)
        
        # Publish status change event
        if self.event_system:
            event = Event(
                event_type=EventType.AGENT_STATUS_CHANGED,
                source=self.agent_id,
                payload={
                    'old_status': old_status.value,
                    'new_status': new_status.value,
                    'metadata': metadata or {}
                },
                tags={'agent', 'status'}
            )
            await self.event_system.publish(event)
        
        logger.info(f"Agent {self.agent_id} status changed: {old_status.value} -> {new_status.value}")

    async def send_message(self, recipient_id: str, message_type: MessageType,
                          payload: Dict[str, Any], timeout: float = 30.0) -> Optional[Message]:
        """
        Send a message to another agent.
        
        Args:
            recipient_id: ID of the recipient agent
            message_type: Type of message
            payload: Message payload
            timeout: Response timeout in seconds
            
        Returns:
            Response message or None
        """
        if not self.communication_bus:
            logger.error(f"Agent {self.agent_id} has no communication bus configured")
            return None
            
        return await self.communication_bus.send_request(
            recipient_id,
            message_type,
            payload,
            timeout,
            self.agent_id
        )

    async def publish_event(self, event_type: EventType, payload: Optional[Dict[str, Any]] = None,
                           tags: Optional[Set[str]] = None):
        """
        Publish an event to the event system.
        
        Args:
            event_type: Type of event
            payload: Event payload
            tags: Event tags
        """
        if not self.event_system:
            logger.error(f"Agent {self.agent_id} has no event system configured")
            return
            
        event = Event(
            event_type=event_type,
            source=self.agent_id,
            payload=payload or {},
            tags=tags or {'agent'}
        )
        
        await self.event_system.publish(event)

    def get_workflow_context(self, scope: str = "workflow") -> Optional[Dict[str, Any]]:
        """
        Get context data from the workflow context.
        
        Args:
            scope: Context scope to retrieve
            
        Returns:
            Context data or None
        """
        if not self.workflow_context or not self._current_workflow_id:
            return None
            
        return self.workflow_context.get_context(self._current_workflow_id, scope)

    def set_workflow_context(self, key: str, value: Any, scope: str = "workflow"):
        """
        Set context data in the workflow context.
        
        Args:
            key: Context key
            value: Context value
            scope: Context scope
        """
        if not self.workflow_context or not self._current_workflow_id:
            logger.warning(f"Agent {self.agent_id} has no workflow context available")
            return
            
        self.workflow_context.set_context(self._current_workflow_id, key, value, scope)

    # Abstract methods that subclasses should implement
    @abstractmethod
    async def process_task_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a task request from another agent.
        
        Args:
            payload: Task request payload
            
        Returns:
            Response payload
        """
        pass

    async def on_workflow_started(self, workflow_id: str, payload: Dict[str, Any]):
        """Called when a workflow starts."""
        pass

    async def on_workflow_completed(self, workflow_id: str, payload: Dict[str, Any]):
        """Called when a workflow completes."""
        pass

    async def on_workflow_failed(self, workflow_id: str, payload: Dict[str, Any]):
        """Called when a workflow fails."""
        pass 