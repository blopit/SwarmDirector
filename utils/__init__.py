"""
Utilities package for SwarmDirector
Contains helper functions and common utilities
"""

from .database import init_db, reset_db
from .logging import setup_logging

# Legacy AutoGen helpers (backward compatibility)
from .autogen_helpers import (
    create_autogen_agent, 
    setup_group_chat, 
    create_specialized_agents,
    validate_autogen_setup,
    setup_autogen_workspace
)

# New AutoGen integration framework
from .autogen_integration import (
    AutoGenConfig,
    BaseAutoGenAgent,
    AutoGenChatAgent,
    AutoGenToolAgent,
    MultiAgentChain,
    AutoGenAgentFactory,
    create_specialized_agents as create_new_specialized_agents,
    create_multi_agent_conversation
)

# AutoGen configuration management
from .autogen_config import (
    AutoGenEnvironmentConfig,
    setup_autogen_environment,
    AGENT_TEMPLATES,
    get_agent_template,
    create_development_team_config
)

__all__ = [
    # Database utilities
    'init_db', 
    'reset_db', 
    
    # Logging utilities
    'setup_logging', 
    
    # Legacy AutoGen helpers (backward compatibility)
    'create_autogen_agent', 
    'setup_group_chat',
    'create_specialized_agents',
    'validate_autogen_setup',
    'setup_autogen_workspace',
    
    # New AutoGen framework classes
    'AutoGenConfig',
    'BaseAutoGenAgent',
    'AutoGenChatAgent', 
    'AutoGenToolAgent',
    'MultiAgentChain',
    'AutoGenAgentFactory',
    'create_new_specialized_agents',
    'create_multi_agent_conversation',
    
    # AutoGen configuration
    'AutoGenEnvironmentConfig',
    'setup_autogen_environment',
    'AGENT_TEMPLATES',
    'get_agent_template',
    'create_development_team_config'
] 