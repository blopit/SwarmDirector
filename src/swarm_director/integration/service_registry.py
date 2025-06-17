"""
Service Registry

Provides agent discovery and registration capabilities.
Maintains a registry of available agents and their capabilities.
"""

import logging
import threading
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional, Set
import uuid

logger = logging.getLogger(__name__)


class AgentStatus(Enum):
    """Status of an agent in the registry."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    BUSY = "busy"
    ERROR = "error"
    MAINTENANCE = "maintenance"


class ServiceType(Enum):
    """Types of services that agents can provide."""
    EMAIL_COMPOSITION = "email_composition"
    EMAIL_DELIVERY = "email_delivery"
    DRAFT_REVIEW = "draft_review"
    CONTENT_GENERATION = "content_generation"
    WORKFLOW_ORCHESTRATION = "workflow_orchestration"
    TASK_MANAGEMENT = "task_management"
    COMMUNICATION_ROUTING = "communication_routing"
    DATA_PROCESSING = "data_processing"
    VALIDATION = "validation"
    MONITORING = "monitoring"


@dataclass
class AgentCapability:
    """Represents a capability that an agent provides."""
    name: str
    description: str
    service_type: ServiceType
    parameters: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AgentService:
    """
    Represents a registered agent service.
    """
    agent_id: str
    name: str
    description: str
    capabilities: List[AgentCapability]
    status: AgentStatus = AgentStatus.ACTIVE
    endpoint: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    registered_at: datetime = field(default_factory=datetime.utcnow)
    last_heartbeat: datetime = field(default_factory=datetime.utcnow)
    health_check_url: Optional[str] = None
    tags: Set[str] = field(default_factory=set)

    def to_dict(self) -> Dict[str, Any]:
        """Convert service to dictionary for serialization."""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'description': self.description,
            'capabilities': [
                {
                    'name': cap.name,
                    'description': cap.description,
                    'service_type': cap.service_type.value,
                    'parameters': cap.parameters,
                    'metadata': cap.metadata
                }
                for cap in self.capabilities
            ],
            'status': self.status.value,
            'endpoint': self.endpoint,
            'metadata': self.metadata,
            'registered_at': self.registered_at.isoformat(),
            'last_heartbeat': self.last_heartbeat.isoformat(),
            'health_check_url': self.health_check_url,
            'tags': list(self.tags)
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AgentService':
        """Create service from dictionary."""
        capabilities = []
        for cap_data in data.get('capabilities', []):
            capability = AgentCapability(
                name=cap_data['name'],
                description=cap_data['description'],
                service_type=ServiceType(cap_data['service_type']),
                parameters=cap_data.get('parameters', {}),
                metadata=cap_data.get('metadata', {})
            )
            capabilities.append(capability)

        return cls(
            agent_id=data['agent_id'],
            name=data['name'],
            description=data['description'],
            capabilities=capabilities,
            status=AgentStatus(data.get('status', 'active')),
            endpoint=data.get('endpoint'),
            metadata=data.get('metadata', {}),
            registered_at=datetime.fromisoformat(data['registered_at']),
            last_heartbeat=datetime.fromisoformat(data['last_heartbeat']),
            health_check_url=data.get('health_check_url'),
            tags=set(data.get('tags', []))
        )


class ServiceRegistry:
    """
    Central registry for agent services and capabilities.
    
    Provides:
    - Agent registration and discovery
    - Capability-based service lookup
    - Health monitoring and status tracking
    - Load balancing and service selection
    """

    def __init__(self, heartbeat_timeout: int = 300):
        """
        Initialize the service registry.
        
        Args:
            heartbeat_timeout: Seconds after which an agent is considered inactive
        """
        self.heartbeat_timeout = heartbeat_timeout
        self._services: Dict[str, AgentService] = {}
        self._capability_index: Dict[ServiceType, Set[str]] = {}
        self._tag_index: Dict[str, Set[str]] = {}
        self._lock = threading.RLock()

        logger.info("ServiceRegistry initialized")

    def register_service(self, service: AgentService) -> bool:
        """
        Register a new agent service.
        
        Args:
            service: The agent service to register
            
        Returns:
            True if registration was successful
        """
        try:
            with self._lock:
                # Store service
                self._services[service.agent_id] = service
                
                # Update capability index
                for capability in service.capabilities:
                    if capability.service_type not in self._capability_index:
                        self._capability_index[capability.service_type] = set()
                    self._capability_index[capability.service_type].add(service.agent_id)
                
                # Update tag index
                for tag in service.tags:
                    if tag not in self._tag_index:
                        self._tag_index[tag] = set()
                    self._tag_index[tag].add(service.agent_id)

            logger.info(f"Registered service: {service.name} (agent_id: {service.agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to register service {service.agent_id}: {e}")
            return False

    def unregister_service(self, agent_id: str) -> bool:
        """
        Unregister an agent service.
        
        Args:
            agent_id: ID of the agent to unregister
            
        Returns:
            True if unregistration was successful
        """
        try:
            with self._lock:
                if agent_id not in self._services:
                    logger.warning(f"Attempted to unregister unknown service: {agent_id}")
                    return False

                service = self._services[agent_id]
                
                # Remove from capability index
                for capability in service.capabilities:
                    if capability.service_type in self._capability_index:
                        self._capability_index[capability.service_type].discard(agent_id)
                        if not self._capability_index[capability.service_type]:
                            del self._capability_index[capability.service_type]
                
                # Remove from tag index
                for tag in service.tags:
                    if tag in self._tag_index:
                        self._tag_index[tag].discard(agent_id)
                        if not self._tag_index[tag]:
                            del self._tag_index[tag]
                
                # Remove service
                del self._services[agent_id]

            logger.info(f"Unregistered service: {service.name} (agent_id: {agent_id})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to unregister service {agent_id}: {e}")
            return False

    def update_service_status(self, agent_id: str, status: AgentStatus, 
                             metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Update the status of a registered service.
        
        Args:
            agent_id: ID of the agent
            status: New status
            metadata: Optional metadata to update
            
        Returns:
            True if update was successful
        """
        try:
            with self._lock:
                if agent_id not in self._services:
                    logger.warning(f"Attempted to update unknown service: {agent_id}")
                    return False

                service = self._services[agent_id]
                service.status = status
                service.last_heartbeat = datetime.utcnow()
                
                if metadata:
                    service.metadata.update(metadata)

            logger.debug(f"Updated service status: {agent_id} -> {status.value}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update service status {agent_id}: {e}")
            return False

    def heartbeat(self, agent_id: str) -> bool:
        """
        Update the heartbeat timestamp for an agent.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            True if heartbeat was successful
        """
        try:
            with self._lock:
                if agent_id not in self._services:
                    return False

                self._services[agent_id].last_heartbeat = datetime.utcnow()
                
                # Update status to active if it was inactive due to missed heartbeat
                if self._services[agent_id].status == AgentStatus.INACTIVE:
                    self._services[agent_id].status = AgentStatus.ACTIVE

            return True
            
        except Exception as e:
            logger.error(f"Failed to update heartbeat for {agent_id}: {e}")
            return False

    def discover_services(self, service_type: Optional[ServiceType] = None,
                         status: Optional[AgentStatus] = None,
                         tags: Optional[Set[str]] = None,
                         exclude_agent_ids: Optional[Set[str]] = None) -> List[AgentService]:
        """
        Discover services based on criteria.
        
        Args:
            service_type: Filter by service type
            status: Filter by agent status
            tags: Filter by tags (must have all specified tags)
            exclude_agent_ids: Exclude specific agent IDs
            
        Returns:
            List of matching services
        """
        with self._lock:
            services = list(self._services.values())

        # Apply filters
        if service_type:
            services = [
                service for service in services
                if any(cap.service_type == service_type for cap in service.capabilities)
            ]

        if status:
            services = [service for service in services if service.status == status]

        if tags:
            services = [
                service for service in services
                if tags.issubset(service.tags)
            ]

        if exclude_agent_ids:
            services = [
                service for service in services
                if service.agent_id not in exclude_agent_ids
            ]

        # Check for stale services (missed heartbeat)
        current_time = datetime.utcnow()
        active_services = []
        
        for service in services:
            time_since_heartbeat = (current_time - service.last_heartbeat).total_seconds()
            if time_since_heartbeat > self.heartbeat_timeout:
                # Mark as inactive
                with self._lock:
                    if service.agent_id in self._services:
                        self._services[service.agent_id].status = AgentStatus.INACTIVE
                continue
            
            active_services.append(service)

        return active_services

    def get_service(self, agent_id: str) -> Optional[AgentService]:
        """
        Get a specific service by agent ID.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            AgentService if found, None otherwise
        """
        with self._lock:
            return self._services.get(agent_id)

    def get_all_services(self) -> List[AgentService]:
        """Get all registered services."""
        with self._lock:
            return list(self._services.values())

    def find_best_service(self, service_type: ServiceType,
                         exclude_agent_ids: Optional[Set[str]] = None) -> Optional[AgentService]:
        """
        Find the best available service for a given service type.
        
        Uses load balancing and health-based selection.
        
        Args:
            service_type: Type of service needed
            exclude_agent_ids: Exclude specific agent IDs
            
        Returns:
            Best available service or None
        """
        available_services = self.discover_services(
            service_type=service_type,
            status=AgentStatus.ACTIVE,
            exclude_agent_ids=exclude_agent_ids
        )

        if not available_services:
            return None

        # Simple load balancing - prefer services with less recent activity
        # In a real implementation, you might track actual load metrics
        best_service = min(available_services, key=lambda s: s.last_heartbeat)
        
        return best_service

    def get_service_capabilities(self, agent_id: str) -> List[AgentCapability]:
        """
        Get capabilities for a specific service.
        
        Args:
            agent_id: ID of the agent
            
        Returns:
            List of capabilities or empty list if not found
        """
        service = self.get_service(agent_id)
        return service.capabilities if service else []

    def get_services_by_capability(self, capability_name: str) -> List[AgentService]:
        """
        Get all services that provide a specific capability.
        
        Args:
            capability_name: Name of the capability
            
        Returns:
            List of services with the capability
        """
        with self._lock:
            matching_services = []
            for service in self._services.values():
                for capability in service.capabilities:
                    if capability.name == capability_name:
                        matching_services.append(service)
                        break
            
            return matching_services

    def get_registry_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the service registry.
        
        Returns:
            Dictionary with registry statistics
        """
        with self._lock:
            total_services = len(self._services)
            status_counts = {}
            capability_counts = {}
            
            for service in self._services.values():
                # Count by status
                status = service.status.value
                status_counts[status] = status_counts.get(status, 0) + 1
                
                # Count by capability type
                for capability in service.capabilities:
                    cap_type = capability.service_type.value
                    capability_counts[cap_type] = capability_counts.get(cap_type, 0) + 1

            return {
                'total_services': total_services,
                'status_distribution': status_counts,
                'capability_distribution': capability_counts,
                'unique_capability_types': len(self._capability_index),
                'unique_tags': len(self._tag_index)
            } 