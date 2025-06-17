"""
Agent Communication Bus

Provides standardized messaging infrastructure for inter-agent communication.
Implements publish-subscribe pattern with message routing and filtering.
"""

import asyncio
import json
import logging
import time
import uuid
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set
from datetime import datetime
import threading

logger = logging.getLogger(__name__)


class MessageType(Enum):
    """Types of messages that can be sent through the communication bus."""
    TASK_REQUEST = "task_request"
    TASK_RESPONSE = "task_response"
    STATUS_UPDATE = "status_update"
    ERROR_NOTIFICATION = "error_notification"
    WORKFLOW_EVENT = "workflow_event"
    AGENT_REGISTRATION = "agent_registration"
    AGENT_DISCOVERY = "agent_discovery"
    CONTEXT_SHARE = "context_share"
    HEARTBEAT = "heartbeat"


@dataclass
class Message:
    """
    Represents a message in the communication bus.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    sender_id: str = ""
    recipient_id: Optional[str] = None  # None for broadcast messages
    message_type: MessageType = MessageType.TASK_REQUEST
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    correlation_id: Optional[str] = None  # For request-response correlation
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for serialization."""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_id': self.recipient_id,
            'message_type': self.message_type.value,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'correlation_id': self.correlation_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None,
            'metadata': self.metadata
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Message':
        """Create message from dictionary."""
        return cls(
            id=data['id'],
            sender_id=data['sender_id'],
            recipient_id=data.get('recipient_id'),
            message_type=MessageType(data['message_type']),
            payload=data.get('payload', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            correlation_id=data.get('correlation_id'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None,
            metadata=data.get('metadata', {})
        )

    def is_expired(self) -> bool:
        """Check if message has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


class AgentCommunicationBus:
    """
    Central communication hub for agent messaging.
    
    Provides publish-subscribe messaging with:
    - Message routing and filtering
    - Request-response correlation
    - Message persistence and replay
    - Agent registration and discovery
    """

    def __init__(self, max_message_history: int = 1000):
        """
        Initialize the communication bus.
        
        Args:
            max_message_history: Maximum number of messages to keep in history
        """
        self.max_message_history = max_message_history
        self._subscribers: Dict[str, List[Callable]] = {}
        self._agent_registry: Dict[str, Dict[str, Any]] = {}
        self._message_history: List[Message] = []
        self._pending_responses: Dict[str, asyncio.Future] = {}
        self._lock = threading.RLock()
        self._running = False
        self._cleanup_task: Optional[asyncio.Task] = None

        logger.info("AgentCommunicationBus initialized")

    async def start(self):
        """Start the communication bus services."""
        if self._running:
            return

        self._running = True
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_messages())
        logger.info("AgentCommunicationBus started")

    async def stop(self):
        """Stop the communication bus services."""
        if not self._running:
            return

        self._running = False
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("AgentCommunicationBus stopped")

    def register_agent(self, agent_id: str, agent_info: Dict[str, Any]):
        """
        Register an agent with the communication bus.
        
        Args:
            agent_id: Unique identifier for the agent
            agent_info: Agent metadata (capabilities, endpoints, etc.)
        """
        with self._lock:
            self._agent_registry[agent_id] = {
                'info': agent_info,
                'registered_at': datetime.utcnow(),
                'last_heartbeat': datetime.utcnow()
            }

        # Broadcast agent registration
        registration_msg = Message(
            sender_id="communication_bus",
            message_type=MessageType.AGENT_REGISTRATION,
            payload={
                'agent_id': agent_id,
                'agent_info': agent_info
            }
        )
        asyncio.create_task(self.publish(registration_msg))
        
        logger.info(f"Agent {agent_id} registered with communication bus")

    def unregister_agent(self, agent_id: str):
        """Unregister an agent from the communication bus."""
        with self._lock:
            if agent_id in self._agent_registry:
                del self._agent_registry[agent_id]
                
        # Clean up subscriptions
        for message_type in list(self._subscribers.keys()):
            self._subscribers[message_type] = [
                sub for sub in self._subscribers[message_type]
                if getattr(sub, '__self__', None) != agent_id
            ]

        logger.info(f"Agent {agent_id} unregistered from communication bus")

    def subscribe(self, message_type: MessageType, callback: Callable[[Message], None], 
                  agent_id: Optional[str] = None):
        """
        Subscribe to messages of a specific type.
        
        Args:
            message_type: Type of messages to subscribe to
            callback: Function to call when message is received
            agent_id: ID of the subscribing agent (for cleanup)
        """
        with self._lock:
            if message_type.value not in self._subscribers:
                self._subscribers[message_type.value] = []
            
            # Store agent_id with callback for cleanup
            if agent_id:
                callback.__dict__['_agent_id'] = agent_id
                
            self._subscribers[message_type.value].append(callback)

        logger.debug(f"Subscribed to {message_type.value} messages" + 
                    (f" for agent {agent_id}" if agent_id else ""))

    def unsubscribe(self, message_type: MessageType, callback: Callable):
        """Unsubscribe from messages of a specific type."""
        with self._lock:
            if message_type.value in self._subscribers:
                try:
                    self._subscribers[message_type.value].remove(callback)
                except ValueError:
                    pass

    async def publish(self, message: Message) -> bool:
        """
        Publish a message to all subscribers.
        
        Args:
            message: Message to publish
            
        Returns:
            True if message was delivered to at least one subscriber
        """
        if message.is_expired():
            logger.warning(f"Attempting to publish expired message {message.id}")
            return False

        # Store in history
        with self._lock:
            self._message_history.append(message)
            if len(self._message_history) > self.max_message_history:
                self._message_history.pop(0)

        # Get subscribers for this message type
        subscribers = self._subscribers.get(message.message_type.value, [])
        
        # Filter subscribers based on recipient
        if message.recipient_id:
            # Direct message - only deliver to specific recipient
            subscribers = [
                sub for sub in subscribers 
                if getattr(sub, '_agent_id', None) == message.recipient_id
            ]

        delivered_count = 0
        for callback in subscribers:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(message)
                else:
                    callback(message)
                delivered_count += 1
            except Exception as e:
                logger.error(f"Error delivering message {message.id} to subscriber: {e}")

        logger.debug(f"Published message {message.id} to {delivered_count} subscribers")
        return delivered_count > 0

    async def send_request(self, recipient_id: str, message_type: MessageType,
                          payload: Dict[str, Any], timeout: float = 30.0,
                          sender_id: str = "system") -> Optional[Message]:
        """
        Send a request message and wait for a response.
        
        Args:
            recipient_id: ID of the agent to send request to
            message_type: Type of request message
            payload: Request payload
            timeout: Timeout in seconds
            sender_id: ID of the sending agent
            
        Returns:
            Response message or None if timeout
        """
        correlation_id = str(uuid.uuid4())
        
        # Create request message
        request_msg = Message(
            sender_id=sender_id,
            recipient_id=recipient_id,
            message_type=message_type,
            payload=payload,
            correlation_id=correlation_id
        )

        # Create future for response
        response_future = asyncio.Future()
        self._pending_responses[correlation_id] = response_future

        try:
            # Send request
            await self.publish(request_msg)
            
            # Wait for response
            response = await asyncio.wait_for(response_future, timeout=timeout)
            return response
            
        except asyncio.TimeoutError:
            logger.warning(f"Request {correlation_id} timed out after {timeout}s")
            return None
        finally:
            # Clean up
            self._pending_responses.pop(correlation_id, None)

    async def send_response(self, original_message: Message, response_payload: Dict[str, Any],
                           sender_id: str = "system"):
        """
        Send a response to a request message.
        
        Args:
            original_message: The request message to respond to
            response_payload: Response payload
            sender_id: ID of the responding agent
        """
        if not original_message.correlation_id:
            logger.error("Cannot send response - original message has no correlation_id")
            return

        response_msg = Message(
            sender_id=sender_id,
            recipient_id=original_message.sender_id,
            message_type=MessageType.TASK_RESPONSE,
            payload=response_payload,
            correlation_id=original_message.correlation_id
        )

        # Check if there's a pending response future
        if original_message.correlation_id in self._pending_responses:
            future = self._pending_responses[original_message.correlation_id]
            if not future.done():
                future.set_result(response_msg)
                return

        # Otherwise, publish as regular message
        await self.publish(response_msg)

    def get_registered_agents(self) -> Dict[str, Dict[str, Any]]:
        """Get all registered agents."""
        with self._lock:
            return self._agent_registry.copy()

    def get_message_history(self, message_type: Optional[MessageType] = None,
                           since: Optional[datetime] = None) -> List[Message]:
        """
        Get message history with optional filtering.
        
        Args:
            message_type: Filter by message type
            since: Only return messages after this timestamp
            
        Returns:
            List of messages matching criteria
        """
        with self._lock:
            messages = self._message_history.copy()

        if message_type:
            messages = [msg for msg in messages if msg.message_type == message_type]
            
        if since:
            messages = [msg for msg in messages if msg.timestamp > since]

        return messages

    async def _cleanup_expired_messages(self):
        """Background task to clean up expired messages."""
        while self._running:
            try:
                await asyncio.sleep(60)  # Run cleanup every minute
                
                current_time = datetime.utcnow()
                with self._lock:
                    # Remove expired messages from history
                    self._message_history = [
                        msg for msg in self._message_history
                        if not msg.is_expired()
                    ]

                    # Clean up stale agent registrations (no heartbeat for 5 minutes)
                    stale_agents = []
                    for agent_id, info in self._agent_registry.items():
                        if (current_time - info['last_heartbeat']).total_seconds() > 300:
                            stale_agents.append(agent_id)
                    
                    for agent_id in stale_agents:
                        logger.warning(f"Removing stale agent registration: {agent_id}")
                        self.unregister_agent(agent_id)

            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in cleanup task: {e}")

    def update_agent_heartbeat(self, agent_id: str):
        """Update the heartbeat timestamp for an agent."""
        with self._lock:
            if agent_id in self._agent_registry:
                self._agent_registry[agent_id]['last_heartbeat'] = datetime.utcnow() 