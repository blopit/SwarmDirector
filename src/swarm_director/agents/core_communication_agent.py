"""
Core Communication Agent implementation for SwarmDirector
Provides the foundation for message queue management, connection handling,
reply tracking, logging, and threading support using AutoGen's ConversableAgent
"""

import logging
import asyncio
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from queue import Queue, Empty
from collections import defaultdict
import hashlib
import uuid

import autogen

from ..models.agent import Agent, AgentType, AgentStatus
from ..models.task import Task, TaskStatus
from ..models.conversation import Conversation, Message, MessageType
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class CoreCommunicationAgent(autogen.ConversableAgent):
    """
    Core Communication Agent that extends AutoGen's ConversableAgent
    Provides foundational messaging and connection handling capabilities
    """
    
    def __init__(self, 
                 name: str,
                 db_agent: Agent,
                 system_message: Optional[str] = None,
                 human_input_mode: str = "NEVER",
                 max_consecutive_auto_reply: int = 10,
                 **kwargs):
        """Initialize the Core Communication Agent"""
        
        # Default system message for communication management
        if system_message is None:
            system_message = (
                "You are a Core Communication Agent responsible for managing "
                "message workflows, routing communications between agents, and "
                "maintaining communication logs. You coordinate with other agents "
                "to ensure smooth information flow and proper message handling."
            )
        
        # Initialize AutoGen ConversableAgent
        super().__init__(
            name=name,
            system_message=system_message,
            human_input_mode=human_input_mode,
            max_consecutive_auto_reply=max_consecutive_auto_reply,
            **kwargs
        )
        
        # Database integration
        self.db_agent = db_agent
        self.agent_id = db_agent.id
        
        # Message queue management
        self.incoming_queue = Queue()
        self.outgoing_queue = Queue()
        self.priority_queue = Queue()
        self.message_handlers: Dict[str, Callable] = {}
        
        # Connection handling
        self.active_connections: Dict[str, Dict] = {}
        self.connection_registry: Dict[str, Agent] = {}
        self.heartbeat_interval = 30  # seconds
        
        # Reply tracking with hash tables
        self.message_tracking: Dict[str, Dict] = {}
        self.conversation_threads: Dict[str, List] = defaultdict(list)
        self.pending_replies: Dict[str, Dict] = {}
        
        # Logging facilities
        self.operation_log: List[Dict] = []
        self.performance_metrics: Dict[str, Any] = {
            'messages_processed': 0,
            'connections_managed': 0,
            'errors_handled': 0,
            'avg_response_time': 0.0
        }
        
        # Threading support
        self.thread_pool = ThreadPoolExecutor(max_workers=10, thread_name_prefix="CommAgent")
        self.background_threads: List[threading.Thread] = []
        self.shutdown_event = threading.Event()
        
        # Start background processes
        self._start_background_processes()
        
        log_agent_action(self.name, "Core Communication Agent initialized")
    
    def _start_background_processes(self):
        """Start background threads for message processing and connection management"""
        
        # Message processing thread
        msg_thread = threading.Thread(
            target=self._message_processing_loop,
            name=f"{self.name}_MessageProcessor",
            daemon=True
        )
        msg_thread.start()
        self.background_threads.append(msg_thread)
        
        # Connection monitoring thread
        conn_thread = threading.Thread(
            target=self._connection_monitoring_loop,
            name=f"{self.name}_ConnectionMonitor",
            daemon=True
        )
        conn_thread.start()
        self.background_threads.append(conn_thread)
        
        logger.info(f"Started {len(self.background_threads)} background processes")
    
    def send_message(self, recipient: str, content: str, message_type: str = 'general', 
                    priority: bool = False) -> str:
        """Send a message to another agent with tracking"""
        
        message_id = str(uuid.uuid4())
        message = {
            'id': message_id,
            'sender': self.name,
            'recipient': recipient,
            'content': content,
            'type': message_type,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Queue the message
        if priority:
            self.priority_queue.put(message)
        else:
            self.outgoing_queue.put(message)
        
        # Create tracking entry
        tracking_hash = self._create_message_hash(message_id, self.name, recipient)
        self.message_tracking[tracking_hash] = {
            'message_id': message_id,
            'sender': self.name,
            'recipient': recipient,
            'timestamp': datetime.utcnow(),
            'status': 'queued',
            'priority': priority
        }
        
        log_agent_action(self.name, f"Queued message {message_id} to {recipient}")
        return message_id
    
    def register_connection(self, agent_name: str, agent: Agent, 
                          connection_info: Optional[Dict] = None):
        """Register a new agent connection"""
        
        connection_id = f"{agent_name}_{int(time.time())}"
        self.active_connections[connection_id] = {
            'agent_name': agent_name,
            'agent': agent,
            'connected_at': datetime.utcnow(),
            'last_heartbeat': datetime.utcnow(),
            'connection_info': connection_info or {},
            'status': 'active'
        }
        
        self.connection_registry[agent_name] = agent
        self.performance_metrics['connections_managed'] += 1
        
        log_agent_action(self.name, f"Registered connection for agent: {agent_name}")
        return connection_id
    
    def get_performance_metrics(self) -> Dict[str, Any]:
        """Get current performance metrics"""
        return {
            **self.performance_metrics,
            'active_connections': len(self.active_connections),
            'queued_messages': {
                'incoming': self.incoming_queue.qsize(),
                'outgoing': self.outgoing_queue.qsize(),
                'priority': self.priority_queue.qsize()
            },
            'operation_log_size': len(self.operation_log),
            'conversation_threads': len(self.conversation_threads),
            'tracked_messages': len(self.message_tracking)
        }
    
    def _create_message_hash(self, message_id: str, sender: str, recipient: str) -> str:
        """Create a unique hash for message tracking"""
        hash_input = f"{message_id}_{sender}_{recipient}_{time.time()}"
        return hashlib.md5(hash_input.encode()).hexdigest()
    
    def _message_processing_loop(self):
        """Background loop for processing incoming messages"""
        logger.info("Message processing loop started")
        
        while not self.shutdown_event.is_set():
            try:
                time.sleep(0.1)  # Brief sleep to prevent busy waiting
            except Exception as e:
                logger.error(f"Error in message processing loop: {e}")
    
    def _connection_monitoring_loop(self):
        """Background loop for monitoring agent connections"""
        logger.info("Connection monitoring loop started")
        
        while not self.shutdown_event.is_set():
            try:
                time.sleep(self.heartbeat_interval)
            except Exception as e:
                logger.error(f"Error in connection monitoring: {e}")
    
    def shutdown(self):
        """Gracefully shutdown the agent and cleanup resources"""
        logger.info(f"Shutting down {self.name}")
        
        # Signal shutdown to background threads
        self.shutdown_event.set()
        
        # Wait for background threads to finish
        for thread in self.background_threads:
            thread.join(timeout=5.0)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        # Close all connections
        for conn_id in list(self.active_connections.keys()):
            self.unregister_connection(conn_id)
        
        log_agent_action(self.name, "Core Communication Agent shutdown completed")
    
    def unregister_connection(self, connection_id: str):
        """Unregister an agent connection"""
        
        if connection_id in self.active_connections:
            connection = self.active_connections[connection_id]
            agent_name = connection['agent_name']
            
            # Remove from registries
            del self.active_connections[connection_id]
            if agent_name in self.connection_registry:
                del self.connection_registry[agent_name]
            
            log_agent_action(self.name, f"Unregistered connection: {connection_id}")
            return True
        
        return False
