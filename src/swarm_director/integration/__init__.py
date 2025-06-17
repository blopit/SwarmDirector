"""
Agent Integration Framework

This package provides the integration layer for SwarmDirector agents,
enabling seamless communication and coordination between different agents.
"""

from .communication_bus import AgentCommunicationBus, Message, MessageType
from .service_registry import ServiceRegistry, AgentService
from .event_system import EventSystem, Event, EventType

__all__ = [
    'AgentCommunicationBus',
    'Message', 
    'MessageType',
    'ServiceRegistry',
    'AgentService',
    'EventSystem',
    'Event',
    'EventType'
] 