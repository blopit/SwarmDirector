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
from enum import Enum
from collections import defaultdict

# Import models (with type checking to avoid circular imports)
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ..models.conversation import Conversation, Message, ConversationAnalytics


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


class OrchestrationPattern(Enum):
    """Different orchestration patterns for multi-agent interactions"""
    ROUND_ROBIN = "round_robin"
    EXPERTISE_BASED = "expertise_based"
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    SEQUENTIAL = "sequential"
    DEMOCRATIC = "democratic"


@dataclass
class ConversationConfig:
    """Configuration for group conversations"""
    max_round: int = 50
    pattern: OrchestrationPattern = OrchestrationPattern.EXPERTISE_BASED
    allow_repeat_speaker: bool = True
    termination_keywords: List[str] = field(default_factory=lambda: ["TERMINATE", "COMPLETE", "FINISHED"])
    min_contribution_threshold: int = 1
    max_consecutive_replies: int = 3
    enable_moderation: bool = True
    timeout_minutes: int = 30


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


# === NEW SPECIALIZED AGENT TYPES ===

class DataAnalystAgent(AutoGenChatAgent):
    """Specialized agent for data analysis and insights"""
    
    def __init__(self, name: str = "DataAnalyst", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.3, max_tokens=1500)
        system_message = """You are a Data Analyst AI agent specialized in:
- Analyzing datasets and extracting meaningful insights
- Creating data visualizations and reports
- Performing statistical analysis and pattern recognition  
- Identifying trends, anomalies, and correlations in data
- Providing actionable recommendations based on data findings
- Working with various data formats (CSV, JSON, SQL, etc.)

Always structure your analysis with clear methodology, findings, and recommendations.
Use data-driven insights to support your conclusions."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["statistics", "visualization", "pattern_recognition", "reporting"]


class TaskCoordinatorAgent(AutoGenChatAgent):
    """Specialized agent for task coordination and project management"""
    
    def __init__(self, name: str = "TaskCoordinator", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.5, max_tokens=1200)
        system_message = """You are a Task Coordinator AI agent specialized in:
- Breaking down complex projects into manageable tasks
- Identifying task dependencies and optimal sequencing
- Resource allocation and capacity planning
- Risk assessment and mitigation strategies
- Progress tracking and milestone management
- Team coordination and communication facilitation

Always provide structured project plans with clear timelines, dependencies, and deliverables.
Focus on practical, actionable task breakdowns."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["project_management", "task_breakdown", "scheduling", "coordination"]


class ResearchAgent(AutoGenChatAgent):
    """Specialized agent for research and information gathering"""
    
    def __init__(self, name: str = "Researcher", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.4, max_tokens=2000)
        system_message = """You are a Research AI agent specialized in:
- Comprehensive information gathering and analysis
- Literature reviews and academic research
- Market research and competitive analysis
- Technical documentation and best practices research  
- Fact-checking and source verification
- Synthesizing information from multiple sources into coherent reports

Always cite sources when possible and provide well-structured research summaries.
Focus on accuracy, completeness, and credible information sources."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["research", "analysis", "documentation", "fact_checking"]


class CreativeWriterAgent(AutoGenChatAgent):
    """Specialized agent for creative writing and content creation"""
    
    def __init__(self, name: str = "CreativeWriter", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.8, max_tokens=1800)
        system_message = """You are a Creative Writer AI agent specialized in:
- Creative writing and storytelling
- Marketing copy and promotional content
- Technical writing and documentation
- Blog posts, articles, and social media content
- Email campaigns and communication materials
- Editing and proofreading existing content

Always adapt your writing style to the target audience and purpose.
Focus on engaging, clear, and persuasive content that achieves the intended goals."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["creative_writing", "copywriting", "editing", "content_strategy"]


class ProblemSolverAgent(AutoGenChatAgent):
    """Specialized agent for complex problem solving and troubleshooting"""
    
    def __init__(self, name: str = "ProblemSolver", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.6, max_tokens=1500)
        system_message = """You are a Problem Solver AI agent specialized in:
- Systematic problem analysis and root cause identification
- Solution design and alternative evaluation
- Troubleshooting technical and operational issues
- Process optimization and improvement recommendations
- Risk analysis and contingency planning
- Decision support and trade-off analysis

Always use structured problem-solving methodologies and provide multiple solution options.
Focus on practical, implementable solutions with clear action steps."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["problem_solving", "troubleshooting", "optimization", "decision_support"]


class CodeReviewAgent(AutoGenToolAgent):
    """Specialized agent for code review and software quality assessment"""
    
    def __init__(self, name: str = "CodeReviewer", config: Optional[AutoGenConfig] = None):
        default_config = config or AutoGenConfig(temperature=0.2, max_tokens=1500)
        system_message = """You are a Code Review AI agent specialized in:
- Comprehensive code review and quality assessment
- Security vulnerability identification
- Performance optimization recommendations
- Code style and best practices enforcement
- Documentation and maintainability improvements
- Test coverage analysis and suggestions

Always provide constructive feedback with specific examples and improvement suggestions.
Focus on code quality, security, performance, and maintainability."""
        
        super().__init__(name, default_config, system_message)
        self.expertise_areas = ["code_review", "security", "performance", "testing"]


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

            # Log the conversation for all agents
            if hasattr(chat_result, 'chat_history'):
                for agent in self.agents:
                    agent.log_message({
                        "type": "group_chat",
                        "message": message,
                        "result": chat_result
                    })

            return chat_result
        except Exception as e:
            self.logger.error(f"Error in group chat: {str(e)}")
            raise

    def get_chain_stats(self) -> Dict:
        """Get statistics for the entire chain"""
        return {
            "name": self.name,
            "agent_count": len(self.agents),
            "agents": [agent.get_stats() for agent in self.agents],
            "created_at": self.agents[0].created_at.isoformat() if self.agents else None
        }


class AutoGenAgentFactory:
    """Factory class for creating different types of AutoGen agents"""
    
    @staticmethod
    def create_chat_agent(name: str, role: str, config: Optional[AutoGenConfig] = None) -> AutoGenChatAgent:
        """Create a chat agent with specified role"""
        role_templates = {
            'assistant': "You are a helpful AI assistant.",
            'analyst': "You are a data analyst specialized in extracting insights from data.",
            'writer': "You are a professional writer focused on clear, engaging content.",
            'researcher': "You are a researcher focused on gathering and analyzing information.",
            'coordinator': "You are a project coordinator focused on organization and planning."
        }
        
        system_message = role_templates.get(role.lower(), role_templates['assistant'])
        return AutoGenChatAgent(name, config or AutoGenConfig(), system_message)
    
    @staticmethod
    def create_tool_agent(name: str, config: Optional[AutoGenConfig] = None,
                         work_dir: str = "autogen_workspace") -> AutoGenToolAgent:
        """Create a tool agent with code execution capabilities"""
        code_config = {
            "work_dir": work_dir,
            "use_docker": False,
        }
        return AutoGenToolAgent(name, config or AutoGenConfig(), 
                               "You are a helpful assistant with code execution capabilities.",
                               code_config)
    
    @staticmethod
    def create_agent_chain(agents_config: List[Dict]) -> MultiAgentChain:
        """Create a multi-agent chain from configuration"""
        chain = MultiAgentChain()
        
        for agent_config in agents_config:
            agent_type = agent_config.get('type', 'chat')
            name = agent_config.get('name', 'Agent')
            role = agent_config.get('role', 'assistant')
            
            config = AutoGenConfig(
                model=agent_config.get('model', 'gpt-3.5-turbo'),
                temperature=agent_config.get('temperature', 0.7),
                max_tokens=agent_config.get('max_tokens', 1000)
            )
            
            if agent_type == 'tool':
                agent = AutoGenAgentFactory.create_tool_agent(name, config)
            else:
                agent = AutoGenAgentFactory.create_chat_agent(name, role, config)
            
            chain.add_agent(agent)
        
        return chain

    @staticmethod
    def create_specialized_agent(agent_type: str, name: Optional[str] = None, 
                                config: Optional[AutoGenConfig] = None) -> BaseAutoGenAgent:
        """Create specialized agent types"""
        agent_types = {
            'data_analyst': DataAnalystAgent,
            'task_coordinator': TaskCoordinatorAgent,
            'researcher': ResearchAgent,
            'creative_writer': CreativeWriterAgent,
            'problem_solver': ProblemSolverAgent,
            'code_reviewer': CodeReviewAgent
        }
        
        agent_class = agent_types.get(agent_type.lower())
        if not agent_class:
            raise ValueError(f"Unknown specialized agent type: {agent_type}")
        
        if name:
            return agent_class(name, config)
        else:
            return agent_class(config=config)


def create_specialized_agents(config: Optional[AutoGenConfig] = None) -> Dict[str, BaseAutoGenAgent]:
    """Create a set of commonly used specialized agents"""
    agents = {}
    specialized_types = [
        'data_analyst', 'task_coordinator', 'researcher', 
        'creative_writer', 'problem_solver', 'code_reviewer'
    ]
    
    for agent_type in specialized_types:
        try:
            agent = AutoGenAgentFactory.create_specialized_agent(agent_type, config=config)
            agents[agent_type] = agent
        except Exception as e:
            logging.error(f"Failed to create {agent_type} agent: {e}")
    
    return agents


def create_multi_agent_conversation(agent_configs: List[Dict], message: str) -> List[Dict]:
    """Create and run a multi-agent conversation"""
    try:
        chain = AutoGenAgentFactory.create_agent_chain(agent_configs)
        return chain.initiate_chat(message)
    except Exception as e:
        logging.error(f"Error in multi-agent conversation: {e}")
        return [{"error": str(e)}]


def create_orchestrated_conversation(agent_configs: List[Dict], message: str, 
                                   pattern: OrchestrationPattern = OrchestrationPattern.EXPERTISE_BASED) -> Dict:
    """Create and run an orchestrated multi-agent conversation with advanced patterns"""
    try:
        # Create advanced chain
        chain = AdvancedMultiAgentChain(f"OrchestrationSession_{datetime.now().timestamp()}")
        
        # Add agents from config
        for agent_config in agent_configs:
            agent_type = agent_config.get('type', 'chat')
            name = agent_config.get('name', 'Agent')
            role = agent_config.get('role', 'assistant')
            
            config = AutoGenConfig(
                model=agent_config.get('model', 'gpt-3.5-turbo'),
                temperature=agent_config.get('temperature', 0.7),
                max_tokens=agent_config.get('max_tokens', 1000)
            )
            
            if agent_type == 'tool':
                agent = AutoGenAgentFactory.create_tool_agent(name, config)
            else:
                agent = AutoGenAgentFactory.create_chat_agent(name, role, config)
            
            chain.add_agent(agent)
        
        # Execute orchestrated conversation
        return chain.execute_orchestrated_conversation(message, pattern)
        
    except Exception as e:
        logging.error(f"Error in orchestrated conversation: {e}")
        return {"error": str(e)}


class ConversationDirector:
    """Advanced director for managing multi-agent conversations"""
    
    def __init__(self, name: str = "ConversationDirector", config: Optional[AutoGenConfig] = None):
        self.name = name
        self.config = config or AutoGenConfig(temperature=0.3, max_tokens=800)
        self.conversation_logs: List[Dict] = []
        self.performance_metrics: Dict[str, Any] = {}
        self.logger = logging.getLogger(f"autogen.director.{name}")

    def create_custom_speaker_selection(self, pattern: OrchestrationPattern) -> Callable:
        """Create custom speaker selection function based on orchestration pattern"""
        
        def expertise_based_selection(last_speaker, groupchat):
            """Select speaker based on expertise relevance"""
            messages = groupchat.messages
            if not messages:
                return groupchat.agents[0]
            
            last_message = messages[-1]['content'].lower()
            
            # Map keywords to agent types
            expertise_map = {
                'data': ['DataAnalyst', 'data_analyst'],
                'analysis': ['DataAnalyst', 'data_analyst'],
                'research': ['Researcher', 'researcher'],
                'code': ['CodeReviewer', 'code_reviewer'],
                'review': ['CodeReviewer', 'code_reviewer'],
                'problem': ['ProblemSolver', 'problem_solver'],
                'coordinate': ['TaskCoordinator', 'task_coordinator'],
                'manage': ['TaskCoordinator', 'task_coordinator'],
                'write': ['CreativeWriter', 'creative_writer'],
                'creative': ['CreativeWriter', 'creative_writer']
            }
            
            for keyword, agent_types in expertise_map.items():
                if keyword in last_message:
                    for agent in groupchat.agents:
                        if any(agent_type in agent.name for agent_type in agent_types):
                            return agent
            
            # Default to next agent if no expertise match
            try:
                current_idx = groupchat.agents.index(last_speaker)
                return groupchat.agents[(current_idx + 1) % len(groupchat.agents)]
            except ValueError:
                return groupchat.agents[0]

        def round_robin_selection(last_speaker, groupchat):
            """Simple round-robin speaker selection"""
            try:
                current_idx = groupchat.agents.index(last_speaker)
                return groupchat.agents[(current_idx + 1) % len(groupchat.agents)]
            except ValueError:
                return groupchat.agents[0]

        def hierarchical_selection(last_speaker, groupchat):
            """Hierarchical selection based on agent priorities"""
            # TaskCoordinator leads, then specialists based on need
            coordinator_agents = [a for a in groupchat.agents if 'Coordinator' in a.name]
            if coordinator_agents and last_speaker not in coordinator_agents:
                return coordinator_agents[0]
            return expertise_based_selection(last_speaker, groupchat)

        # Return appropriate selection function
        if pattern == OrchestrationPattern.EXPERTISE_BASED:
            return expertise_based_selection
        elif pattern == OrchestrationPattern.ROUND_ROBIN:
            return round_robin_selection
        elif pattern == OrchestrationPattern.HIERARCHICAL:
            return hierarchical_selection
        else:
            return expertise_based_selection

    def create_termination_condition(self, config: ConversationConfig) -> Callable:
        """Create custom termination condition"""
        
        def enhanced_termination(message):
            """Enhanced termination logic"""
            if not message or 'content' not in message:
                return False
                
            content = message['content'].lower().strip()
            
            # Check for termination keywords
            for keyword in config.termination_keywords:
                if keyword.lower() in content:
                    return True
            
            # Check for completion phrases
            completion_phrases = [
                'task completed', 'all done', 'work finished',
                'analysis complete', 'review finished', 'implementation ready'
            ]
            
            for phrase in completion_phrases:
                if phrase in content:
                    return True
            
            return False
        
        return enhanced_termination


class AdvancedMultiAgentChain(MultiAgentChain):
    """Enhanced multi-agent chain with orchestration and analytics tracking"""
    
    def __init__(self, name: str = "AdvancedMultiAgentChain", 
                 conversation_config: Optional[ConversationConfig] = None):
        super().__init__(name)
        self.conversation_config = conversation_config or ConversationConfig()
        self.session_manager: Optional[ConversationSessionManager] = None
        self.orchestration_analytics = {
            'pattern_usage': defaultdict(int),
            'session_start': None,
            'conversation_count': 0,
            'total_duration': 0
        }
    
    def create_enhanced_group_chat(self, conversation_config: Optional[ConversationConfig] = None) -> autogen.GroupChat:
        """Create an enhanced group chat with custom orchestration"""
        config = conversation_config or self.conversation_config
        
        if not self.agents:
            raise ValueError("No agents available for group chat")
        
        # Create conversation director for speaker selection
        director = ConversationDirector()
        speaker_selection_func = director.create_custom_speaker_selection(config.pattern)
        termination_func = director.create_termination_condition(config)
        
        # Get AutoGen agents
        autogen_agents = [agent.agent for agent in self.agents]
        
        group_chat = autogen.GroupChat(
            agents=autogen_agents,
            messages=[],
            max_round=config.max_round,
            speaker_selection_method=speaker_selection_func,
            allow_repeat_speaker=config.allow_repeat_speaker
        )
        
        # Create group chat manager with enhanced termination
        manager = autogen.GroupChatManager(
            groupchat=group_chat,
            llm_config=self.agents[0].config.to_llm_config(),
            is_termination_msg=termination_func
        )
        
        return group_chat, manager
    
    def execute_orchestrated_conversation(self, message: str, pattern: Optional[OrchestrationPattern] = None) -> Dict:
        """Execute a conversation with orchestration and full tracking"""
        start_time = datetime.now()
        self.orchestration_analytics['session_start'] = start_time
        
        # Set pattern for this conversation
        if pattern:
            self.conversation_config.pattern = pattern
        
        # Initialize session manager
        self.session_manager = ConversationSessionManager()
        conversation = self.session_manager.start_conversation(
            title=f"{self.name} Orchestrated Chat",
            description=f"Multi-agent conversation with {self.conversation_config.pattern.value} orchestration",
            conversation_type="autogen_orchestrated",
            orchestration_pattern=self.conversation_config.pattern
        )
        
        try:
            # Create enhanced group chat
            group_chat, manager = self.create_enhanced_group_chat()
            
            # Track initial message
            initial_message = self.session_manager.track_message(
                content=message,
                sender_name="User",
                message_type="user_message"
            )
            
            # Execute conversation
            response_start = datetime.now()
            
            # Get the first agent to start the conversation
            if self.agents:
                initiator = self.agents[0].agent
                chat_result = initiator.initiate_chat(
                    manager,
                    message=message,
                    max_turns=self.conversation_config.max_round
                )
                
                # Track all messages from the chat
                if hasattr(chat_result, 'chat_history') and chat_result.chat_history:
                    self._track_chat_messages(chat_result.chat_history, response_start)
                    self.session_manager.update_autogen_history(chat_result.chat_history)
                elif hasattr(group_chat, 'messages') and group_chat.messages:
                    self._track_chat_messages(group_chat.messages, response_start)
                    self.session_manager.update_autogen_history(group_chat.messages)
            
            # Complete conversation and generate analytics
            analytics = self.session_manager.complete_conversation()
            
            # Update orchestration analytics
            self.orchestration_analytics['pattern_usage'][self.conversation_config.pattern.value] += 1
            self.orchestration_analytics['conversation_count'] += 1
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            self.orchestration_analytics['total_duration'] += duration
            
            return {
                "status": "completed",
                "conversation_id": conversation.id,
                "session_id": self.session_manager.session_id,
                "pattern_used": self.conversation_config.pattern.value,
                "duration": duration,
                "message_count": len(group_chat.messages) if hasattr(group_chat, 'messages') else 0,
                "analytics": analytics.to_dict() if analytics else None,
                "orchestration_analytics": self.get_orchestration_analytics()
            }
            
        except Exception as e:
            # Track error
            if self.session_manager:
                self.session_manager.track_message(
                    content=f"Error occurred: {str(e)}",
                    sender_name="System",
                    message_type="error_message"
                )
                self.session_manager.complete_conversation()
            
            return {
                "status": "error",
                "error": str(e),
                "conversation_id": conversation.id if conversation else None,
                "session_id": self.session_manager.session_id if self.session_manager else None
            }
    
    def _track_chat_messages(self, chat_messages: List[Dict], start_time: datetime):
        """Track messages from AutoGen chat history"""
        if not self.session_manager:
            return
        
        for i, msg in enumerate(chat_messages):
            if isinstance(msg, dict):
                content = msg.get('content', '')
                sender = msg.get('name', msg.get('role', 'Unknown'))
                
                # Estimate response time (simple approximation)
                response_time = (datetime.now() - start_time).total_seconds() / len(chat_messages) * (i + 1)
                
                # Determine message type
                if sender.lower() in ['user', 'human']:
                    msg_type = "user_message"
                elif 'error' in content.lower() or 'exception' in content.lower():
                    msg_type = "error_message"
                else:
                    msg_type = "agent_response"
                
                self.session_manager.track_message(
                    content=content,
                    sender_name=sender,
                    message_type=msg_type,
                    response_time=response_time,
                    metadata=msg
                )
    
    def get_orchestration_analytics(self) -> Dict:
        """Get comprehensive orchestration analytics"""
        base_analytics = super().get_chain_stats()
        
        enhanced_analytics = {
            **base_analytics,
            "orchestration_metrics": {
                "pattern_usage": dict(self.orchestration_analytics['pattern_usage']),
                "conversation_count": self.orchestration_analytics['conversation_count'],
                "total_duration": self.orchestration_analytics['total_duration'],
                "avg_conversation_duration": (
                    self.orchestration_analytics['total_duration'] / 
                    max(1, self.orchestration_analytics['conversation_count'])
                ),
                "current_pattern": self.conversation_config.pattern.value,
                "session_info": {
                    "current_session": self.session_manager.session_id if self.session_manager else None,
                    "current_conversation": self.session_manager.conversation.id if self.session_manager and self.session_manager.conversation else None
                }
            }
        }
        
        return enhanced_analytics


class OrchestrationWorkflow:
    """Pre-defined workflows for common orchestration patterns"""
    
    @staticmethod
    def create_research_workflow(config: Optional[AutoGenConfig] = None) -> AdvancedMultiAgentChain:
        """Create a research-focused workflow"""
        chain = AdvancedMultiAgentChain("ResearchWorkflow")
        
        # Add research-focused agents
        chain.add_agent(ResearchAgent(config=config))
        chain.add_agent(DataAnalystAgent(config=config))
        chain.add_agent(TaskCoordinatorAgent(config=config))
        
        # Configure for research pattern
        chain.conversation_config.pattern = OrchestrationPattern.EXPERTISE_BASED
        chain.conversation_config.max_round = 30
        
        return chain

    @staticmethod
    def create_development_workflow(config: Optional[AutoGenConfig] = None) -> AdvancedMultiAgentChain:
        """Create a development-focused workflow"""
        chain = AdvancedMultiAgentChain("DevelopmentWorkflow")
        
        # Add development-focused agents
        chain.add_agent(TaskCoordinatorAgent(config=config))
        chain.add_agent(ProblemSolverAgent(config=config))
        chain.add_agent(CodeReviewAgent(config=config))
        
        # Configure for hierarchical pattern with coordinator leading
        chain.conversation_config.pattern = OrchestrationPattern.HIERARCHICAL
        chain.conversation_config.max_round = 40
        
        return chain

    @staticmethod
    def create_creative_workflow(config: Optional[AutoGenConfig] = None) -> AdvancedMultiAgentChain:
        """Create a creative-focused workflow"""
        chain = AdvancedMultiAgentChain("CreativeWorkflow")
        
        # Add creative-focused agents
        chain.add_agent(CreativeWriterAgent(config=config))
        chain.add_agent(ResearchAgent(config=config))
        chain.add_agent(TaskCoordinatorAgent(config=config))
        
        # Configure for collaborative pattern
        chain.conversation_config.pattern = OrchestrationPattern.COLLABORATIVE
        chain.conversation_config.max_round = 35
        
        return chain

    @staticmethod
    def create_analysis_workflow(config: Optional[AutoGenConfig] = None) -> AdvancedMultiAgentChain:
        """Create an analysis-focused workflow"""
        chain = AdvancedMultiAgentChain("AnalysisWorkflow")
        
        # Add analysis-focused agents
        chain.add_agent(DataAnalystAgent(config=config))
        chain.add_agent(ResearchAgent(config=config))
        chain.add_agent(ProblemSolverAgent(config=config))
        chain.add_agent(TaskCoordinatorAgent(config=config))
        
        # Configure for expertise-based pattern
        chain.conversation_config.pattern = OrchestrationPattern.EXPERTISE_BASED
        chain.conversation_config.max_round = 45
        
        return chain 

class ConversationSessionManager:
    """Manages AutoGen conversation sessions with database integration"""
    
    def __init__(self, session_id: Optional[str] = None):
        self.session_id = session_id or f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.conversation: Optional['Conversation'] = None
        self.analytics_engine = None
        self.logger = logging.getLogger(f"autogen.session.{self.session_id}")
    
    def start_conversation(self, title: str = "AutoGen Conversation", 
                         description: str = "", conversation_type: str = "autogen",
                         orchestration_pattern: Optional[OrchestrationPattern] = None) -> 'Conversation':
        """Start a new tracked conversation"""
        from ..models.conversation import Conversation
        from datetime import datetime
        
        self.conversation = Conversation(
            title=title,
            description=description,
            session_id=self.session_id,
            conversation_type=conversation_type,
            start_time=datetime.utcnow(),
            orchestration_pattern=orchestration_pattern
        )
        self.conversation.save()
        self.logger.info(f"Started conversation {self.conversation.id} with session {self.session_id}")
        return self.conversation
    
    def track_message(self, content: str, sender_name: str, message_type: str = "agent_response",
                     sender_agent_id: Optional[int] = None, response_time: Optional[float] = None,
                     tokens_used: Optional[int] = None, metadata: Optional[Dict] = None) -> 'Message':
        """Track a message in the current conversation"""
        if not self.conversation:
            raise ValueError("No active conversation. Call start_conversation() first.")
        
        from ..models.conversation import Message, MessageType
        
        # Map string message type to enum
        try:
            msg_type = MessageType(message_type)
        except ValueError:
            msg_type = MessageType.AGENT_RESPONSE
        
        message = Message(
            conversation_id=self.conversation.id,
            content=content,
            message_type=msg_type,
            sender_agent_id=sender_agent_id,
            agent_name=sender_name,
            response_time=response_time,
            tokens_used=tokens_used,
            message_metadata=metadata,
            message_length=len(content)
        )
        message.save()
        
        # Update conversation totals
        self.conversation.total_messages = len(self.conversation.messages)
        if tokens_used:
            self.conversation.total_tokens = (self.conversation.total_tokens or 0) + tokens_used
        self.conversation.save()
        
        return message
    
    def update_autogen_history(self, autogen_chat_history: List[Dict]):
        """Update the conversation with AutoGen chat history"""
        if not self.conversation:
            return
        
        self.conversation.autogen_chat_history = autogen_chat_history
        self.conversation.save()
    
    def complete_conversation(self) -> 'ConversationAnalytics':
        """Complete the conversation and generate analytics"""
        if not self.conversation:
            raise ValueError("No active conversation to complete.")
        
        self.conversation.complete_conversation()
        
        # Generate analytics
        if not self.analytics_engine:
            from .conversation_analytics import create_analytics_engine
            self.analytics_engine = create_analytics_engine()
        
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        self.logger.info(f"Completed conversation {self.conversation.id} with analytics")
        return analytics
    
    def get_conversation_summary(self) -> Dict[str, Any]:
        """Get a summary of the current conversation"""
        if not self.conversation:
            return {"error": "No active conversation"}
        
        if not self.analytics_engine:
            from .conversation_analytics import create_analytics_engine
            self.analytics_engine = create_analytics_engine()
        
        return self.analytics_engine.get_conversation_insights(self.conversation.id) 