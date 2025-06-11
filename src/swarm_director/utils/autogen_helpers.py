"""
AutoGen integration helpers for SwarmDirector
Enhanced with streaming capabilities and integration with the new framework
"""

import autogen
from typing import Dict, List, Optional, Callable, Generator, Any
from flask import current_app
import json
import asyncio
from datetime import datetime

# Import new framework components
from .autogen_integration import (
    AutoGenConfig, AutoGenChatAgent, AutoGenToolAgent, 
    MultiAgentChain, AutoGenAgentFactory
)
from .autogen_config import AutoGenEnvironmentConfig, setup_autogen_environment


class StreamingHandler:
    """Handle streaming responses from AutoGen agents"""
    
    def __init__(self, callback: Optional[Callable] = None):
        self.callback = callback
        self.messages: List[Dict] = []
        self.is_streaming = False

    def on_message(self, message: Dict):
        """Handle incoming message during streaming"""
        self.messages.append({
            "timestamp": datetime.now().isoformat(),
            "content": message.get("content", ""),
            "sender": message.get("name", "unknown"),
            "role": message.get("role", "assistant")
        })
        
        if self.callback:
            self.callback(message)

    def start_streaming(self):
        """Start streaming mode"""
        self.is_streaming = True
        self.messages = []

    def stop_streaming(self):
        """Stop streaming mode"""
        self.is_streaming = False

    def get_conversation_history(self) -> List[Dict]:
        """Get complete conversation history"""
        return self.messages.copy()


def create_autogen_agent(agent_name: str, system_message: str, config: Dict) -> autogen.AssistantAgent:
    """Create an AutoGen agent with the specified configuration (legacy compatibility)"""
    try:
        # Convert legacy config to new format
        autogen_config = AutoGenConfig(
            model=config.get("model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.7),
            max_tokens=config.get("max_tokens", 1000),
            timeout=config.get("timeout", 120)
        )
        
        # Create using new framework
        chat_agent = AutoGenChatAgent(agent_name, autogen_config, system_message)
        
        current_app.logger.info(f"Created AutoGen agent: {agent_name} (legacy compatibility)")
        return chat_agent.agent
        
    except Exception as e:
        current_app.logger.error(f"Error creating AutoGen agent {agent_name}: {str(e)}")
        raise


def create_user_proxy_agent(agent_name: str, config: Dict) -> autogen.UserProxyAgent:
    """Create an AutoGen UserProxy agent (legacy compatibility)"""
    try:
        # Convert legacy config to new format
        autogen_config = AutoGenConfig(
            model=config.get("model", "gpt-3.5-turbo"),
            temperature=config.get("temperature", 0.7)
        )
        
        # Create using new framework
        tool_agent = AutoGenToolAgent(
            agent_name, 
            autogen_config, 
            system_message=config.get("system_message", ""),
            code_execution_config=config.get("code_execution_config", {
                "work_dir": "autogen_workspace",
                "use_docker": False,
            })
        )
        
        current_app.logger.info(f"Created AutoGen UserProxy agent: {agent_name} (legacy compatibility)")
        return tool_agent.agent
        
    except Exception as e:
        current_app.logger.error(f"Error creating AutoGen UserProxy agent {agent_name}: {str(e)}")
        raise


def setup_group_chat(agents: List[autogen.Agent], admin_name: str = "Admin") -> tuple:
    """Set up a group chat with multiple AutoGen agents (legacy compatibility)"""
    try:
        # Create group chat
        groupchat = autogen.GroupChat(
            agents=agents,
            messages=[],
            max_round=50,
            admin_name=admin_name
        )
        
        # Create group chat manager
        manager = autogen.GroupChatManager(
            groupchat=groupchat,
            llm_config={"config_list": []}  # Configure as needed
        )
        
        current_app.logger.info(f"Created group chat with {len(agents)} agents (legacy compatibility)")
        return groupchat, manager
        
    except Exception as e:
        current_app.logger.error(f"Error setting up group chat: {str(e)}")
        raise


def initiate_chat_with_agent(initiator_agent, recipient_agent, message: str, 
                           max_turns: int = 10, streaming_handler: Optional[StreamingHandler] = None) -> List[Dict]:
    """Initiate a chat between two AutoGen agents with optional streaming"""
    try:
        if streaming_handler:
            streaming_handler.start_streaming()

        # Start the conversation
        chat_result = initiator_agent.initiate_chat(
            recipient_agent,
            message=message,
            max_turns=max_turns
        )
        
        # Handle streaming if enabled
        if streaming_handler:
            # Process chat history for streaming
            if hasattr(chat_result, 'chat_history'):
                for msg in chat_result.chat_history:
                    streaming_handler.on_message(msg)
            streaming_handler.stop_streaming()

        current_app.logger.info(f"Chat completed between {initiator_agent.name} and {recipient_agent.name}")
        return chat_result.chat_history if hasattr(chat_result, 'chat_history') else []
        
    except Exception as e:
        current_app.logger.error(f"Error in agent chat: {str(e)}")
        if streaming_handler:
            streaming_handler.stop_streaming()
        raise


def get_default_llm_config(api_key: Optional[str] = None) -> Dict:
    """Get default LLM configuration for AutoGen agents (legacy compatibility)"""
    return {
        "config_list": [
            {
                "model": "gpt-3.5-turbo",
                "api_key": api_key or current_app.config.get("OPENAI_API_KEY"),
            }
        ],
        "timeout": 120,
    }


def agent_to_database_mapping(autogen_agent, db_agent):
    """Map AutoGen agent properties to database agent model (legacy compatibility)"""
    try:
        # Update database agent with AutoGen agent information
        autogen_config = {
            "name": autogen_agent.name,
            "system_message": getattr(autogen_agent, 'system_message', ''),
            "llm_config": getattr(autogen_agent, 'llm_config', {}),
        }
        
        db_agent.autogen_config = autogen_config
        db_agent.system_message = getattr(autogen_agent, 'system_message', '')
        db_agent.save()
        
        current_app.logger.info(f"Mapped AutoGen agent {autogen_agent.name} to database")
        
    except Exception as e:
        current_app.logger.error(f"Error mapping agent to database: {str(e)}")
        raise


def create_specialized_agents() -> Dict[str, autogen.Agent]:
    """Create a set of specialized agents for common tasks (legacy compatibility)"""
    try:
        # Use new framework to create agents
        env_config = AutoGenEnvironmentConfig.from_environment()
        config = AutoGenConfig()
        
        # Use factory to create agents
        factory = AutoGenAgentFactory()
        
        agents = {
            'code_reviewer': factory.create_chat_agent("CodeReviewer", "code_reviewer", config).agent,
            'task_planner': factory.create_chat_agent("TaskPlanner", "task_planner", config).agent,
            'qa_tester': factory.create_chat_agent("QATester", "qa_tester", config).agent,
            'architect': factory.create_chat_agent("Architect", "architect", config).agent,
            'tool_agent': factory.create_tool_agent("ToolAgent", config).agent
        }
        
        current_app.logger.info(f"Created {len(agents)} specialized agents (legacy compatibility)")
        return agents
        
    except Exception as e:
        current_app.logger.error(f"Error creating specialized agents: {str(e)}")
        raise


# New enhanced functions using the framework

def create_streaming_conversation(agent_configs: List[Dict], message: str, 
                                callback: Optional[Callable] = None) -> Generator[Dict, None, None]:
    """Create a streaming multi-agent conversation"""
    try:
        # Setup streaming handler
        streaming_handler = StreamingHandler(callback)
        
        # Create agent chain
        chain = AutoGenAgentFactory.create_agent_chain(agent_configs)
        
        # Start conversation with streaming
        streaming_handler.start_streaming()
        
        # Note: This is a simplified streaming simulation
        # Real streaming would require AutoGen library streaming support
        chat_history = chain.initiate_chat(message)
        
        # Yield messages as they would stream
        for message in chat_history:
            streaming_handler.on_message(message)
            yield message
            
        streaming_handler.stop_streaming()
        
    except Exception as e:
        current_app.logger.error(f"Error in streaming conversation: {str(e)}")
        raise


def create_enhanced_agent_chain(config_name: str = "development_team") -> MultiAgentChain:
    """Create predefined agent chains for common scenarios"""
    from .autogen_config import create_development_team_config, get_agent_template
    
    try:
        if config_name == "development_team":
            agent_configs = create_development_team_config()
        elif config_name == "code_review_team":
            agent_configs = [
                get_agent_template("architect"),
                get_agent_template("code_reviewer"),
                get_agent_template("qa_tester")
            ]
        elif config_name == "planning_team":
            agent_configs = [
                get_agent_template("task_planner"),
                get_agent_template("architect")
            ]
        else:
            raise ValueError(f"Unknown config name: {config_name}")
        
        chain = AutoGenAgentFactory.create_agent_chain(agent_configs)
        current_app.logger.info(f"Created enhanced agent chain: {config_name}")
        return chain
        
    except Exception as e:
        current_app.logger.error(f"Error creating enhanced agent chain: {str(e)}")
        raise


def setup_autogen_workspace() -> str:
    """Setup AutoGen workspace directory and return path"""
    try:
        env_config = setup_autogen_environment()
        current_app.logger.info(f"AutoGen workspace setup: {env_config.workspace_dir}")
        return env_config.workspace_dir
    except Exception as e:
        current_app.logger.error(f"Error setting up AutoGen workspace: {str(e)}")
        raise


def validate_autogen_setup() -> Dict[str, Any]:
    """Validate AutoGen setup and return status"""
    try:
        # Test imports
        import autogen
        
        # Test configuration
        env_config = AutoGenEnvironmentConfig.from_environment()
        
        # Check API keys
        has_api_keys = any([
            env_config.openai_api_key,
            env_config.azure_openai_api_key,
            env_config.anthropic_api_key,
            env_config.google_api_key
        ])
        
        # Test agent creation
        config = AutoGenConfig()
        factory = AutoGenAgentFactory()
        test_agent = factory.create_chat_agent("TestAgent", "assistant", config)
        
        status = {
            "autogen_available": True,
            "api_keys_configured": has_api_keys,
            "workspace_ready": True,
            "agent_creation": True,
            "workspace_path": env_config.workspace_dir,
            "available_models": env_config.get_config_list() if has_api_keys else []
        }
        
        current_app.logger.info("AutoGen setup validation completed successfully")
        return status
        
    except Exception as e:
        current_app.logger.error(f"AutoGen setup validation failed: {str(e)}")
        return {
            "autogen_available": False,
            "error": str(e),
            "api_keys_configured": False,
            "workspace_ready": False,
            "agent_creation": False
        } 