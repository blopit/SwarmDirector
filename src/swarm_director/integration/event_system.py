"""
Event System

Provides event-driven communication infrastructure for agents.
Implements publisher-subscriber pattern with event filtering and routing.
"""

import asyncio
import logging
import threading
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set, Union
import json

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Types of events in the system."""
    WORKFLOW_STARTED = "workflow_started"
    WORKFLOW_COMPLETED = "workflow_completed"
    WORKFLOW_FAILED = "workflow_failed"
    WORKFLOW_PAUSED = "workflow_paused"
    WORKFLOW_RESUMED = "workflow_resumed"
    
    TASK_CREATED = "task_created"
    TASK_STARTED = "task_started"
    TASK_COMPLETED = "task_completed"
    TASK_FAILED = "task_failed"
    TASK_CANCELLED = "task_cancelled"
    
    AGENT_REGISTERED = "agent_registered"
    AGENT_UNREGISTERED = "agent_unregistered"
    AGENT_STATUS_CHANGED = "agent_status_changed"
    AGENT_ERROR = "agent_error"
    
    MESSAGE_SENT = "message_sent"
    MESSAGE_RECEIVED = "message_received"
    MESSAGE_FAILED = "message_failed"
    
    STATE_CHANGED = "state_changed"
    CONTEXT_UPDATED = "context_updated"
    
    SYSTEM_STARTUP = "system_startup"
    SYSTEM_SHUTDOWN = "system_shutdown"
    SYSTEM_ERROR = "system_error"


class EventPriority(Enum):
    """Priority levels for events."""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4


@dataclass
class Event:
    """
    Represents an event in the system.
    """
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = EventType.STATE_CHANGED
    source: str = ""  # ID of the component that generated the event
    payload: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    priority: EventPriority = EventPriority.NORMAL
    tags: Set[str] = field(default_factory=set)
    metadata: Dict[str, Any] = field(default_factory=dict)
    correlation_id: Optional[str] = None
    expires_at: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            'id': self.id,
            'event_type': self.event_type.value,
            'source': self.source,
            'payload': self.payload,
            'timestamp': self.timestamp.isoformat(),
            'priority': self.priority.value,
            'tags': list(self.tags),
            'metadata': self.metadata,
            'correlation_id': self.correlation_id,
            'expires_at': self.expires_at.isoformat() if self.expires_at else None
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            id=data['id'],
            event_type=EventType(data['event_type']),
            source=data['source'],
            payload=data.get('payload', {}),
            timestamp=datetime.fromisoformat(data['timestamp']),
            priority=EventPriority(data.get('priority', 2)),
            tags=set(data.get('tags', [])),
            metadata=data.get('metadata', {}),
            correlation_id=data.get('correlation_id'),
            expires_at=datetime.fromisoformat(data['expires_at']) if data.get('expires_at') else None
        )

    def is_expired(self) -> bool:
        """Check if event has expired."""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at


@dataclass
class EventFilter:
    """Filter criteria for event subscriptions."""
    event_types: Optional[Set[EventType]] = None
    sources: Optional[Set[str]] = None
    tags: Optional[Set[str]] = None
    priority_min: Optional[EventPriority] = None
    metadata_filters: Optional[Dict[str, Any]] = None

    def matches(self, event: Event) -> bool:
        """Check if an event matches this filter."""
        if self.event_types and event.event_type not in self.event_types:
            return False
            
        if self.sources and event.source not in self.sources:
            return False
            
        if self.tags and not self.tags.issubset(event.tags):
            return False
            
        if self.priority_min and event.priority.value < self.priority_min.value:
            return False
            
        if self.metadata_filters:
            for key, value in self.metadata_filters.items():
                if key not in event.metadata or event.metadata[key] != value:
                    return False
                    
        return True


class EventSystem:
    """
    Event-driven communication system for agents.
    
    Provides:
    - Event publishing and subscription
    - Event filtering and routing
    - Event persistence and replay
    - Priority-based event processing
    - Event correlation and tracing
    """

    def __init__(self, max_event_history: int = 5000, enable_persistence: bool = False):
        """
        Initialize the event system.
        
        Args:
            max_event_history: Maximum number of events to keep in memory
            enable_persistence: Whether to persist events to storage
        """
        self.max_event_history = max_event_history
        self.enable_persistence = enable_persistence
        
        self._subscribers: Dict[str, List[Dict[str, Any]]] = {}
        self._event_history: List[Event] = []
        self._event_queue: asyncio.Queue = asyncio.Queue()
        self._lock = threading.RLock()
        self._running = False
        self._processor_task: Optional[asyncio.Task] = None
        self._cleanup_task: Optional[asyncio.Task] = None
        
        # Statistics
        self._stats = {
            'events_published': 0,
            'events_processed': 0,
            'events_dropped': 0,
            'subscribers_count': 0
        }

        logger.info("EventSystem initialized")

    async def start(self):
        """Start the event system."""
        if self._running:
            return

        self._running = True
        self._processor_task = asyncio.create_task(self._process_events())
        self._cleanup_task = asyncio.create_task(self._cleanup_expired_events())
        
        # Publish system startup event
        startup_event = Event(
            event_type=EventType.SYSTEM_STARTUP,
            source="event_system",
            payload={'timestamp': datetime.utcnow().isoformat()}
        )
        await self.publish(startup_event)
        
        logger.info("EventSystem started")

    async def stop(self):
        """Stop the event system."""
        if not self._running:
            return

        self._running = False
        
        # Publish shutdown event
        shutdown_event = Event(
            event_type=EventType.SYSTEM_SHUTDOWN,
            source="event_system",
            payload={'timestamp': datetime.utcnow().isoformat()}
        )
        await self.publish(shutdown_event)
        
        # Cancel tasks
        if self._processor_task:
            self._processor_task.cancel()
            try:
                await self._processor_task
            except asyncio.CancelledError:
                pass
                
        if self._cleanup_task:
            self._cleanup_task.cancel()
            try:
                await self._cleanup_task
            except asyncio.CancelledError:
                pass

        logger.info("EventSystem stopped")

    def subscribe(self, callback: Callable[[Event], Any], 
                  event_filter: Optional[EventFilter] = None,
                  subscriber_id: Optional[str] = None) -> str:
        """
        Subscribe to events with optional filtering.
        
        Args:
            callback: Function to call when matching event occurs
            event_filter: Filter criteria for events
            subscriber_id: Optional ID for the subscriber
            
        Returns:
            Subscription ID for later unsubscription
        """
        subscription_id = str(uuid.uuid4())
        subscriber_id = subscriber_id or f"subscriber_{subscription_id[:8]}"
        
        subscription = {
            'id': subscription_id,
            'subscriber_id': subscriber_id,
            'callback': callback,
            'filter': event_filter,
            'created_at': datetime.utcnow(),
            'event_count': 0
        }

        with self._lock:
            if subscriber_id not in self._subscribers:
                self._subscribers[subscriber_id] = []
            self._subscribers[subscriber_id].append(subscription)
            self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())

        logger.debug(f"New subscription: {subscription_id} for {subscriber_id}")
        return subscription_id

    def unsubscribe(self, subscription_id: str, subscriber_id: Optional[str] = None) -> bool:
        """
        Unsubscribe from events.
        
        Args:
            subscription_id: ID of the subscription to remove
            subscriber_id: Optional subscriber ID to narrow search
            
        Returns:
            True if subscription was found and removed
        """
        with self._lock:
            if subscriber_id:
                # Search only for specific subscriber
                if subscriber_id in self._subscribers:
                    self._subscribers[subscriber_id] = [
                        sub for sub in self._subscribers[subscriber_id]
                        if sub['id'] != subscription_id
                    ]
                    if not self._subscribers[subscriber_id]:
                        del self._subscribers[subscriber_id]
                    self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
                    return True
            else:
                # Search all subscribers
                for sub_id, subscriptions in list(self._subscribers.items()):
                    original_len = len(subscriptions)
                    self._subscribers[sub_id] = [
                        sub for sub in subscriptions
                        if sub['id'] != subscription_id
                    ]
                    if len(self._subscribers[sub_id]) < original_len:
                        if not self._subscribers[sub_id]:
                            del self._subscribers[sub_id]
                        self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
                        return True

        return False

    def unsubscribe_all(self, subscriber_id: str) -> int:
        """
        Remove all subscriptions for a subscriber.
        
        Args:
            subscriber_id: ID of the subscriber
            
        Returns:
            Number of subscriptions removed
        """
        with self._lock:
            if subscriber_id in self._subscribers:
                count = len(self._subscribers[subscriber_id])
                del self._subscribers[subscriber_id]
                self._stats['subscribers_count'] = sum(len(subs) for subs in self._subscribers.values())
                logger.debug(f"Removed {count} subscriptions for {subscriber_id}")
                return count
        return 0

    async def publish(self, event: Event, priority_override: Optional[EventPriority] = None):
        """
        Publish an event to all matching subscribers.
        
        Args:
            event: Event to publish
            priority_override: Override event priority
        """
        if event.is_expired():
            logger.warning(f"Attempting to publish expired event {event.id}")
            return

        if priority_override:
            event.priority = priority_override

        # Add to history
        with self._lock:
            self._event_history.append(event)
            if len(self._event_history) > self.max_event_history:
                self._event_history.pop(0)
            self._stats['events_published'] += 1

        # Queue for processing
        try:
            await self._event_queue.put(event)
        except Exception as e:
            logger.error(f"Failed to queue event {event.id}: {e}")
            with self._lock:
                self._stats['events_dropped'] += 1

    async def _process_events(self):
        """Background task to process events from the queue."""
        while self._running:
            try:
                # Get event from queue with timeout
                event = await asyncio.wait_for(self._event_queue.get(), timeout=1.0)
                await self._deliver_event(event)
                
                with self._lock:
                    self._stats['events_processed'] += 1
                    
            except asyncio.TimeoutError:
                continue
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error processing event: {e}")

    async def _deliver_event(self, event: Event):
        """Deliver an event to matching subscribers."""
        matching_subscriptions = []
        
        with self._lock:
            for subscriber_id, subscriptions in self._subscribers.items():
                for subscription in subscriptions:
                    event_filter = subscription['filter']
                    if event_filter is None or event_filter.matches(event):
                        matching_subscriptions.append(subscription)

        # Deliver to subscribers (sorted by event priority)
        matching_subscriptions.sort(key=lambda s: event.priority.value, reverse=True)
        
        for subscription in matching_subscriptions:
            try:
                callback = subscription['callback']
                if asyncio.iscoroutinefunction(callback):
                    await callback(event)
                else:
                    callback(event)
                    
                # Update subscription stats
                subscription['event_count'] += 1
                
            except Exception as e:
                logger.error(f"Error delivering event {event.id} to {subscription['subscriber_id']}: {e}")

    async def _cleanup_expired_events(self):
        """Background task to clean up expired events."""
        while self._running:
            try:
                await asyncio.sleep(300)  # Run cleanup every 5 minutes
                
                with self._lock:
                    original_count = len(self._event_history)
                    self._event_history = [
                        event for event in self._event_history
                        if not event.is_expired()
                    ]
                    cleaned_count = original_count - len(self._event_history)
                    
                    if cleaned_count > 0:
                        logger.debug(f"Cleaned up {cleaned_count} expired events")
                        
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in event cleanup: {e}")

    def get_event_history(self, 
                         event_filter: Optional[EventFilter] = None,
                         limit: Optional[int] = None,
                         since: Optional[datetime] = None) -> List[Event]:
        """
        Get event history with optional filtering.
        
        Args:
            event_filter: Filter criteria
            limit: Maximum number of events to return
            since: Only return events after this timestamp
            
        Returns:
            List of matching events
        """
        with self._lock:
            events = self._event_history.copy()

        # Apply filters
        if since:
            events = [event for event in events if event.timestamp > since]
            
        if event_filter:
            events = [event for event in events if event_filter.matches(event)]

        # Sort by timestamp (newest first)
        events.sort(key=lambda e: e.timestamp, reverse=True)
        
        if limit:
            events = events[:limit]

        return events

    def get_statistics(self) -> Dict[str, Any]:
        """Get event system statistics."""
        with self._lock:
            stats = self._stats.copy()
            stats.update({
                'events_in_history': len(self._event_history),
                'queue_size': self._event_queue.qsize() if hasattr(self._event_queue, 'qsize') else 0,
                'running': self._running
            })
            return stats

    def create_workflow_event(self, workflow_id: str, event_type: EventType,
                            payload: Optional[Dict[str, Any]] = None) -> Event:
        """
        Create a workflow-related event.
        
        Args:
            workflow_id: ID of the workflow
            event_type: Type of workflow event
            payload: Optional event payload
            
        Returns:
            Created event
        """
        return Event(
            event_type=event_type,
            source=f"workflow_{workflow_id}",
            payload=payload or {},
            correlation_id=workflow_id,
            tags={'workflow', 'system'},
            metadata={'workflow_id': workflow_id}
        )

    def create_agent_event(self, agent_id: str, event_type: EventType,
                          payload: Optional[Dict[str, Any]] = None) -> Event:
        """
        Create an agent-related event.
        
        Args:
            agent_id: ID of the agent
            event_type: Type of agent event
            payload: Optional event payload
            
        Returns:
            Created event
        """
        return Event(
            event_type=event_type,
            source=agent_id,
            payload=payload or {},
            tags={'agent', 'system'},
            metadata={'agent_id': agent_id}
        ) 