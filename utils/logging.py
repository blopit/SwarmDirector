"""
Logging utilities for SwarmDirector
"""

import logging
import os
from datetime import datetime

def setup_logging(app=None, log_level=logging.INFO):
    """Set up logging configuration for the application"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure root logger
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(f'logs/swarm_director_{datetime.now().strftime("%Y%m%d")}.log'),
            logging.StreamHandler()
        ]
    )
    
    # Configure specific loggers
    configure_agent_logger()
    configure_task_logger()
    configure_conversation_logger()
    
    if app:
        app.logger.setLevel(log_level)
        app.logger.info("Logging configured successfully")

def configure_agent_logger():
    """Configure logging for agent-related operations"""
    agent_logger = logging.getLogger('swarm_director.agents')
    agent_logger.setLevel(logging.INFO)
    
    # Create agent-specific log file
    agent_handler = logging.FileHandler(f'logs/agents_{datetime.now().strftime("%Y%m%d")}.log')
    agent_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    agent_logger.addHandler(agent_handler)

def configure_task_logger():
    """Configure logging for task-related operations"""
    task_logger = logging.getLogger('swarm_director.tasks')
    task_logger.setLevel(logging.INFO)
    
    # Create task-specific log file
    task_handler = logging.FileHandler(f'logs/tasks_{datetime.now().strftime("%Y%m%d")}.log')
    task_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    task_logger.addHandler(task_handler)

def configure_conversation_logger():
    """Configure logging for conversation-related operations"""
    conv_logger = logging.getLogger('swarm_director.conversations')
    conv_logger.setLevel(logging.INFO)
    
    # Create conversation-specific log file
    conv_handler = logging.FileHandler(f'logs/conversations_{datetime.now().strftime("%Y%m%d")}.log')
    conv_handler.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    conv_logger.addHandler(conv_handler)

def get_logger(name):
    """Get a logger with the specified name"""
    return logging.getLogger(f'swarm_director.{name}')

# Convenience functions for common logging operations
def log_agent_action(agent_name, action, details=None):
    """Log an agent action"""
    logger = get_logger('agents')
    message = f"{agent_name}: {action}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_task_update(task_id, status, details=None):
    """Log a task status update"""
    logger = get_logger('tasks')
    message = f"Task {task_id} status changed to {status}"
    if details:
        message += f" - {details}"
    logger.info(message)

def log_conversation_event(conversation_id, event, details=None):
    """Log a conversation event"""
    logger = get_logger('conversations')
    message = f"Conversation {conversation_id}: {event}"
    if details:
        message += f" - {details}"
    logger.info(message) 