"""
AutoGen Integration Framework for SwarmDirector
Provides enhanced AutoGen functionality with base classes, agent types, and orchestration
"""

import autogen
import json
import asyncio
import logging
from typing import Dict, List, Optional, Union, Any, Callable
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from flask import current_app


@dataclass
class AutoGenConfig:
    """Configuration class for AutoGen agents"""
    model: str = "gpt-3.5-turbo"
    api_key: Optional[str] = None
    temperature: float = 0.7
    max_tokens: int = 1000
    timeout: int = 120
    seed: int = 42
    request_timeout: int = 600
    custom_config: Dict[str, Any] = field(default_factory=dict)

    def to_llm_config(self) -> Dict:
        """Convert to AutoGen LLM config format"""
        config = {
            "config_list": [
                {
                    "model": self.model,
                    "api_key": self.api_key or current_app.config.get("OPENAI_API_KEY"),
                }
            ],
            "timeout": self.timeout,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "seed": self.seed,
            "request_timeout": self.request_timeout,
        }
        config.update(self.custom_config)
        return config


class BaseAutoGenAgent(ABC):
    """Abstract base class for all AutoGen agent wrappers"""
    
    def __init__(self, name: str, config: AutoGenConfig, system_message: str = ""):
        self.name = name
        self.config = config
        self.system_message = system_message
        self._agent: Optional[autogen.Agent] = None
        self.conversation_history: List[Dict] = []
        self.created_at = datetime.now()
        self.logger = logging.getLogger(f"autogen.{name}")

    @abstractmethod
    def create_agent(self) -> autogen.Agent:
        """Create the underlying AutoGen agent"""
        pass

    @property
    def agent(self) -> autogen.Agent:
        """Get the underlying AutoGen agent, creating if necessary"""
        if self._agent is None:
            self._agent = self.create_agent()
        return self._agent

    def get_stats(self) -> Dict:
        """Get agent statistics"""
        return {
            "name": self.name,
            "created_at": self.created_at.isoformat(),
            "conversation_count": len(self.conversation_history),
            "config": {
                "model": self.config.model,
                "temperature": self.config.temperature
            }
        }

    def log_message(self, message: Dict):
        """Log a conversation message"""
        message["timestamp"] = datetime.now().isoformat()
        self.conversation_history.append(message)


class AutoGenChatAgent(BaseAutoGenAgent):
    """Enhanced wrapper for AutoGen AssistantAgent"""
    
    def __init__(self, name: str, config: AutoGenConfig, system_message: str = "",
                 human_input_mode: str = "NEVER", max_consecutive_auto_reply: int = 10):
        super().__init__(name, config, system_message)
        self.human_input_mode = human_input_mode
        self.max_consecutive_auto_reply = max_consecutive_auto_reply

    def create_agent(self) -> autogen.AssistantAgent:
        """Create AutoGen AssistantAgent"""
        try:
            agent = autogen.AssistantAgent(
                name=self.name,
                system_message=self.system_message,
                llm_config=self.config.to_llm_config(),
                human_input_mode=self.human_input_mode,
                max_consecutive_auto_reply=self.max_consecutive_auto_reply
            )
            self.logger.info(f"Created AutoGen AssistantAgent: {self.name}")
            return agent
        except Exception as e:
            self.logger.error(f"Error creating AssistantAgent {self.name}: {str(e)}")
            raise


class AutoGenToolAgent(BaseAutoGenAgent):
    """Specialized agent for tool usage and code execution"""
    
    def __init__(self, name: str, config: AutoGenConfig, system_message: str = "",
                 code_execution_config: Optional[Dict] = None):
        super().__init__(name, config, system_message)
        self.code_execution_config = code_execution_config or {
            "work_dir": "autogen_workspace",
            "use_docker": False,
        }

    def create_agent(self) -> autogen.UserProxyAgent:
        """Create AutoGen UserProxyAgent with tool capabilities"""
        try:
            agent = autogen.UserProxyAgent(
                name=self.name,
                system_message=self.system_message,
                human_input_mode="NEVER",
                max_consecutive_auto_reply=10,
                is_termination_msg=lambda x: x.get("content", "").rstrip().endswith("TERMINATE"),
                code_execution_config=self.code_execution_config,
            )
            self.logger.info(f"Created AutoGen UserProxyAgent: {self.name}")
            return agent
        except Exception as e:
            self.logger.error(f"Error creating UserProxyAgent {self.name}: {str(e)}")
            raise


class MultiAgentChain:
    """Orchestrator for parallel and sequential agent execution"""
    
    def __init__(self, name: str = "MultiAgentChain"):
        self.name = name
        self.agents: List[BaseAutoGenAgent] = []
        self.group_chat: Optional[autogen.GroupChat] = None
        self.manager: Optional[autogen.GroupChatManager] = None
        self.logger = logging.getLogger(f"autogen.chain.{name}")

    def add_agent(self, agent: BaseAutoGenAgent):
        """Add an agent to the chain"""
        self.agents.append(agent)
        self.logger.info(f"Added agent {agent.name} to chain {self.name}")

    def create_group_chat(self, max_round: int = 50, admin_name: str = "Admin") -> autogen.GroupChat:
        """Create a group chat with all agents"""
        try:
            if not self.agents:
                raise ValueError("No agents added to the chain")

            autogen_agents = [agent.agent for agent in self.agents]
            
            self.group_chat = autogen.GroupChat(
                agents=autogen_agents,
                messages=[],
                max_round=max_round,
                admin_name=admin_name
            )

            # Create manager with first agent's config
            manager_config = self.agents[0].config.to_llm_config() if self.agents else {}
            self.manager = autogen.GroupChatManager(
                groupchat=self.group_chat,
                llm_config=manager_config
            )

            self.logger.info(f"Created group chat with {len(autogen_agents)} agents")
            return self.group_chat

        except Exception as e:
            self.logger.error(f"Error creating group chat: {str(e)}")
            raise

    def initiate_chat(self, message: str, max_turns: int = 10) -> List[Dict]:
        """Initiate a conversation in the group chat"""
        try:
            if not self.manager or not self.group_chat:
                self.create_group_chat()

            # Use first agent as initiator
            initiator = self.agents[0].agent
            chat_result = initiator.initiate_chat(
                self.manager,
                message=message,
                max_turns=max_turns
            )

            # Log messages for all agents
            for agent in self.agents:
                agent.log_message({
                    "type": "group_chat",
                    "message": message,
                    "participants": [a.name for a in self.agents]
                })

            self.logger.info(f"Group chat completed with {len(self.agents)} agents")
            return chat_result.chat_history if hasattr(chat_result, 'chat_history') else []

        except Exception as e:
            self.logger.error(f"Error in group chat: {str(e)}")
            raise

    def get_chain_stats(self) -> Dict:
        """Get statistics for the entire agent chain"""
        return {
            "name": self.name,
            "agent_count": len(self.agents),
            "agents": [agent.get_stats() for agent in self.agents],
            "total_conversations": sum(len(agent.conversation_history) for agent in self.agents)
        }


class AutoGenAgentFactory:
    """Factory class for creating AutoGen agents dynamically"""
    
    @staticmethod
    def create_chat_agent(name: str, role: str, config: Optional[AutoGenConfig] = None) -> AutoGenChatAgent:
        """Create a chat agent with predefined role"""
        if config is None:
            config = AutoGenConfig()

        role_messages = {
            "assistant": "You are a helpful AI assistant.",
            "code_reviewer": "You are a senior software engineer specializing in code review. "
                           "Analyze code for bugs, performance issues, and best practices.",
            "task_planner": "You are a project manager who excels at breaking down complex "
                          "tasks into manageable subtasks and creating execution plans.",
            "qa_tester": "You are a quality assurance specialist focused on testing "
                       "strategies, test case creation, and bug identification.",
            "architect": "You are a software architect responsible for system design "
                       "and technical decision making.",
        }

        system_message = role_messages.get(role, role_messages["assistant"])
        return AutoGenChatAgent(name, config, system_message)

    @staticmethod
    def create_tool_agent(name: str, config: Optional[AutoGenConfig] = None,
                         work_dir: str = "autogen_workspace") -> AutoGenToolAgent:
        """Create a tool agent for code execution"""
        if config is None:
            config = AutoGenConfig()

        code_config = {
            "work_dir": work_dir,
            "use_docker": False,
        }

        system_message = f"You are a tool execution agent named {name}. " \
                        "You can execute code and use tools to complete tasks."

        return AutoGenToolAgent(name, config, system_message, code_config)

    @staticmethod
    def create_agent_chain(agents_config: List[Dict]) -> MultiAgentChain:
        """Create a multi-agent chain from configuration"""
        chain = MultiAgentChain()
        
        for agent_config in agents_config:
            agent_type = agent_config.get("type", "chat")
            name = agent_config["name"]
            role = agent_config.get("role", "assistant")
            
            config = AutoGenConfig(
                model=agent_config.get("model", "gpt-3.5-turbo"),
                temperature=agent_config.get("temperature", 0.7),
                max_tokens=agent_config.get("max_tokens", 1000)
            )

            if agent_type == "chat":
                agent = AutoGenAgentFactory.create_chat_agent(name, role, config)
            elif agent_type == "tool":
                agent = AutoGenAgentFactory.create_tool_agent(name, config)
            else:
                raise ValueError(f"Unknown agent type: {agent_type}")

            chain.add_agent(agent)

        return chain


# Convenience functions for backward compatibility
def create_specialized_agents(config: Optional[AutoGenConfig] = None) -> Dict[str, BaseAutoGenAgent]:
    """Create a set of specialized agents for common tasks"""
    if config is None:
        config = AutoGenConfig()

    factory = AutoGenAgentFactory()
    
    agents = {
        'code_reviewer': factory.create_chat_agent("CodeReviewer", "code_reviewer", config),
        'task_planner': factory.create_chat_agent("TaskPlanner", "task_planner", config),
        'qa_tester': factory.create_chat_agent("QATester", "qa_tester", config),
        'architect': factory.create_chat_agent("Architect", "architect", config),
        'tool_agent': factory.create_tool_agent("ToolAgent", config)
    }

    logging.info(f"Created {len(agents)} specialized agents")
    return agents


def create_multi_agent_conversation(agent_configs: List[Dict], message: str) -> List[Dict]:
    """Create and run a multi-agent conversation"""
    try:
        chain = AutoGenAgentFactory.create_agent_chain(agent_configs)
        return chain.initiate_chat(message)
    except Exception as e:
        logging.error(f"Error in multi-agent conversation: {str(e)}")
        raise 