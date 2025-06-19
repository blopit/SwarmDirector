"""
Integrated Agent

Combines the existing EnhancedBaseAgent with the new ValidatedBaseAgent
to provide both integration framework capabilities and validation/plugin support.
"""

import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime

from .enhanced_base_agent import EnhancedBaseAgent
from .validated_base_agent import ValidatedBaseAgent
from ..models.agent import Agent
from ..models.task import Task
from ..validation.validation_chain import ValidationChain, ValidationTier
from ..plugins.plugin_manager import PluginManager
from ..integration.communication_bus import AgentCommunicationBus, Message, MessageType
from ..integration.service_registry import ServiceRegistry, AgentCapability
from ..integration.event_system import EventSystem, Event, EventType

logger = logging.getLogger(__name__)


class IntegratedAgent(EnhancedBaseAgent):
    """
    Fully integrated agent that combines:
    - Integration framework capabilities (communication, events, service registry)
    - Validation system integration (hierarchical validation)
    - Plugin system support (dynamic capabilities)
    """
    
    def __init__(self, db_agent: Agent,
                 validation_chain: Optional[ValidationChain] = None,
                 plugin_manager: Optional[PluginManager] = None,
                 communication_bus: Optional[AgentCommunicationBus] = None,
                 service_registry: Optional[ServiceRegistry] = None,
                 event_system: Optional[EventSystem] = None,
                 **kwargs):
        """
        Initialize the integrated agent.
        
        Args:
            db_agent: Database agent model
            validation_chain: Validation chain for hierarchical validation
            plugin_manager: Plugin manager for dynamic capabilities
            communication_bus: Communication bus instance
            service_registry: Service registry instance
            event_system: Event system instance
            **kwargs: Additional arguments
        """
        # Convert agent capabilities to AgentCapability objects
        capabilities = []
        if db_agent.capabilities:
            for cap_name in db_agent.capabilities:
                capabilities.append(AgentCapability(
                    name=cap_name,
                    description=f"Capability: {cap_name}",
                    version="1.0.0"
                ))
        
        # Initialize EnhancedBaseAgent
        super().__init__(
            agent_id=str(db_agent.id),
            name=db_agent.name,
            description=db_agent.description or "",
            capabilities=capabilities,
            communication_bus=communication_bus,
            service_registry=service_registry,
            event_system=event_system,
            **kwargs
        )
        
        # Store database agent
        self.db_agent = db_agent
        
        # Validation and plugin components
        self.validation_chain = validation_chain
        self.plugin_manager = plugin_manager
        self.validation_tier = self._determine_validation_tier()
        
        # Validation history
        self.validation_history: List[Dict[str, Any]] = []
        
        # Create ValidatedBaseAgent instance for validation methods
        self._validated_agent = ValidatedBaseAgent(
            db_agent, validation_chain, plugin_manager
        )
        
        logger.info(f"IntegratedAgent {self.agent_id} initialized with validation tier: {self.validation_tier.value}")
    
    def _determine_validation_tier(self) -> ValidationTier:
        """Determine validation tier based on agent type"""
        if self.db_agent.agent_type.value == 'worker':
            return ValidationTier.TOOL
        elif self.db_agent.agent_type.value in ['coordinator', 'supervisor']:
            return ValidationTier.DEPARTMENT
        else:
            return ValidationTier.DIRECTOR
    
    async def start(self):
        """Start the integrated agent with all systems"""
        await super().start()
        
        # Publish validation system ready event
        if self.event_system:
            await self.publish_event(
                EventType.AGENT_STATUS_CHANGED,
                {
                    'validation_tier': self.validation_tier.value,
                    'validation_enabled': self.validation_chain is not None,
                    'plugin_support': self.plugin_manager is not None
                },
                {'agent', 'validation', 'plugins'}
            )
    
    async def execute_task_with_full_integration(self, task: Task) -> Dict[str, Any]:
        """
        Execute task with full integration: validation, plugins, and communication
        """
        start_time = datetime.utcnow()
        execution_id = f"{task.id}_{self.agent_id}_{int(start_time.timestamp())}"
        
        logger.info(f"Starting integrated execution for task {task.id} by agent {self.name}")
        
        try:
            # 1. Publish task started event
            if self.event_system:
                await self.publish_event(
                    EventType.TASK_STARTED,
                    {
                        'task_id': str(task.id),
                        'task_title': task.title,
                        'agent_id': self.agent_id,
                        'validation_tier': self.validation_tier.value
                    },
                    {'task', 'execution', 'validation'}
                )
            
            # 2. Update agent status
            from ..integration.service_registry import AgentStatus
            await self.update_status(AgentStatus.BUSY, {
                'current_task': str(task.id),
                'execution_id': execution_id
            })
            
            # 3. Execute with validation (delegate to ValidatedBaseAgent)
            result = await self._validated_agent.execute_task_with_validation(task)
            
            # 4. Store validation history
            self.validation_history.append({
                'execution_id': execution_id,
                'task_id': str(task.id),
                'result': result,
                'timestamp': start_time.isoformat()
            })
            
            # 5. Publish task completed event
            if self.event_system:
                await self.publish_event(
                    EventType.TASK_COMPLETED,
                    {
                        'task_id': str(task.id),
                        'execution_id': execution_id,
                        'status': result['status'],
                        'validation_tier': self.validation_tier.value,
                        'duration_ms': result.get('processing_time_ms', 0)
                    },
                    {'task', 'execution', 'validation'}
                )
            
            # 6. Update agent status back to active
            await self.update_status(AgentStatus.ACTIVE)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in integrated execution for task {task.id}: {e}", exc_info=True)
            
            # Publish task failed event
            if self.event_system:
                await self.publish_event(
                    EventType.TASK_FAILED,
                    {
                        'task_id': str(task.id),
                        'execution_id': execution_id,
                        'error': str(e),
                        'agent_id': self.agent_id
                    },
                    {'task', 'execution', 'error'}
                )
            
            # Update agent status
            await self.update_status(AgentStatus.ERROR, {'error': str(e)})
            
            return {
                'status': 'error',
                'task_id': str(task.id),
                'agent_id': self.agent_id,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def process_task_request(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process task request from communication bus
        """
        try:
            # Extract task information from payload
            task_data = payload.get('task', {})
            
            # Create task object (simplified - in production would load from DB)
            task = Task(
                title=task_data.get('title', 'Communication Bus Task'),
                description=task_data.get('description', ''),
                input_data=task_data.get('input_data', {})
            )
            
            # Execute with full integration
            result = await self.execute_task_with_full_integration(task)
            
            return {
                'status': 'success',
                'result': result,
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error processing task request: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'agent_id': self.agent_id,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def request_capability_enhancement(self, required_capabilities: List[str]) -> Dict[str, Any]:
        """
        Request capability enhancement through plugin system
        """
        if not self.plugin_manager:
            return {
                'success': False,
                'error': 'No plugin manager available'
            }
        
        try:
            # Create a dummy task for capability analysis
            dummy_task = Task(
                title="Capability Enhancement Request",
                description=f"Request for capabilities: {', '.join(required_capabilities)}",
                input_data={'required_capabilities': required_capabilities}
            )
            
            # Use plugin manager to resolve capabilities
            result = self.plugin_manager.process_task_with_plugins(dummy_task)
            
            # Publish capability enhancement event
            if self.event_system:
                await self.publish_event(
                    EventType.AGENT_STATUS_CHANGED,
                    {
                        'capability_enhancement': True,
                        'required_capabilities': required_capabilities,
                        'enhancement_result': result,
                        'agent_id': self.agent_id
                    },
                    {'agent', 'capabilities', 'plugins'}
                )
            
            return result
            
        except Exception as e:
            logger.error(f"Error requesting capability enhancement: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics for this agent"""
        return self._validated_agent.get_validation_statistics()
    
    def get_execution_history(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get execution history"""
        return self.validation_history[-limit:]
    
    def get_integration_status(self) -> Dict[str, Any]:
        """Get comprehensive integration status"""
        return {
            'agent_id': self.agent_id,
            'name': self.name,
            'status': self.status.value,
            'validation_tier': self.validation_tier.value,
            'capabilities': [cap.name for cap in self.capabilities],
            'validation_enabled': self.validation_chain is not None,
            'plugin_support': self.plugin_manager is not None,
            'communication_enabled': self.communication_bus is not None,
            'event_system_enabled': self.event_system is not None,
            'service_registry_enabled': self.service_registry is not None,
            'current_workflow': self._current_workflow_id,
            'execution_count': len(self.validation_history),
            'last_activity': self.validation_history[-1]['timestamp'] if self.validation_history else None
        }
    
    async def handle_validation_failure(self, task: Task, validation_result: Dict[str, Any]):
        """Handle validation failure with communication"""
        # Publish validation failure event
        if self.event_system:
            await self.publish_event(
                EventType.TASK_FAILED,
                {
                    'task_id': str(task.id),
                    'validation_failure': True,
                    'validation_result': validation_result,
                    'tier': self.validation_tier.value,
                    'agent_id': self.agent_id
                },
                {'validation', 'failure', 'task'}
            )
        
        # Notify supervisor if this is a tool-level agent
        if (self.validation_tier == ValidationTier.TOOL and 
            self.communication_bus and 
            self.db_agent.parent_id):
            
            await self.send_message(
                str(self.db_agent.parent_id),
                MessageType.STATUS_UPDATE,
                {
                    'validation_failure': True,
                    'task_id': str(task.id),
                    'failure_details': validation_result,
                    'requires_intervention': True
                }
            )
    
    async def coordinate_hierarchical_validation(self, task: Task, 
                                                 dept_agent_id: Optional[str] = None,
                                                 director_agent_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Coordinate hierarchical validation across multiple agents
        """
        if not self.communication_bus:
            return await self.execute_task_with_full_integration(task)
        
        try:
            # Execute at current tier
            result = await self.execute_task_with_full_integration(task)
            
            if result['status'] != 'success':
                return result
            
            # If this is a tool agent and we have a department agent, forward for validation
            if (self.validation_tier == ValidationTier.TOOL and dept_agent_id):
                dept_response = await self.send_message(
                    dept_agent_id,
                    MessageType.TASK_REQUEST,
                    {
                        'task': task.to_dict(),
                        'previous_result': result,
                        'validation_request': True,
                        'tier': 'department'
                    }
                )
                
                if dept_response and dept_response.payload.get('status') == 'success':
                    result = dept_response.payload['result']
                else:
                    return {
                        'status': 'validation_failed',
                        'tier': 'department',
                        'error': 'Department validation failed'
                    }
            
            # If we have a director agent, forward for final validation
            if director_agent_id:
                director_response = await self.send_message(
                    director_agent_id,
                    MessageType.TASK_REQUEST,
                    {
                        'task': task.to_dict(),
                        'previous_result': result,
                        'validation_request': True,
                        'tier': 'director'
                    }
                )
                
                if director_response and director_response.payload.get('status') == 'success':
                    result = director_response.payload['result']
                else:
                    return {
                        'status': 'validation_failed',
                        'tier': 'director',
                        'error': 'Director validation failed'
                    }
            
            return result
            
        except Exception as e:
            logger.error(f"Error in hierarchical validation coordination: {e}")
            return {
                'status': 'error',
                'error': str(e),
                'tier': self.validation_tier.value
            }
