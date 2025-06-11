"""
Utilities package for SwarmDirector
Contains helper functions and common utilities
"""

from .database import init_db, reset_db
from .logging import setup_logging

# AutoGen imports are optional to prevent dependency issues during testing
try:
    # Legacy AutoGen helpers (backward compatibility)
    from .autogen_helpers import (
        create_autogen_agent,
        setup_group_chat,
        create_specialized_agents,
        validate_autogen_setup,
        setup_autogen_workspace
    )
    AUTOGEN_HELPERS_AVAILABLE = True
except ImportError:
    # Create stub functions if autogen is not available
    def create_autogen_agent(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def setup_group_chat(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def create_specialized_agents(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def validate_autogen_setup(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def setup_autogen_workspace(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    AUTOGEN_HELPERS_AVAILABLE = False

try:
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
    AUTOGEN_INTEGRATION_AVAILABLE = True
except ImportError:
    # Create stub classes if autogen integration is not available
    class AutoGenConfig:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    class BaseAutoGenAgent:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    class AutoGenChatAgent:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    class AutoGenToolAgent:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    class MultiAgentChain:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    class AutoGenAgentFactory:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def create_new_specialized_agents(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def create_multi_agent_conversation(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    AUTOGEN_INTEGRATION_AVAILABLE = False

try:
    # AutoGen configuration management
    from .autogen_config import (
        AutoGenEnvironmentConfig,
        setup_autogen_environment,
        AGENT_TEMPLATES,
        get_agent_template,
        create_development_team_config
    )
    AUTOGEN_CONFIG_AVAILABLE = True
except ImportError:
    # Create stub functions if autogen config is not available
    class AutoGenEnvironmentConfig:
        def __init__(self, *args, **kwargs):
            raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def setup_autogen_environment(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    AGENT_TEMPLATES = {}

    def get_agent_template(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    def create_development_team_config(*args, **kwargs):
        raise ImportError("AutoGen not available - install pyautogen to use this feature")

    AUTOGEN_CONFIG_AVAILABLE = False

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
    'create_development_team_config',

    # Availability flags
    'AUTOGEN_HELPERS_AVAILABLE',
    'AUTOGEN_INTEGRATION_AVAILABLE',
    'AUTOGEN_CONFIG_AVAILABLE'
]