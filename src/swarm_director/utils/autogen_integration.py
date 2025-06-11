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
    """Enhanced multi-agent chain with advanced orchestration capabilities"""
    
    def __init__(self, name: str = "AdvancedMultiAgentChain", 
                 conversation_config: Optional[ConversationConfig] = None):
        super().__init__(name)
        self.conversation_config = conversation_config or ConversationConfig()
        self.conversation_director = ConversationDirector(f"{name}_Director")
        self.orchestration_metrics: Dict[str, Any] = {}
        self.session_logs: List[Dict] = []

    def create_enhanced_group_chat(self, conversation_config: Optional[ConversationConfig] = None) -> autogen.GroupChat:
        """Create an enhanced group chat with advanced orchestration"""
        config = conversation_config or self.conversation_config
        
        try:
            if not self.agents:
                raise ValueError("No agents added to the chain")

            autogen_agents = [agent.agent for agent in self.agents]
            
            # Create custom speaker selection function
            speaker_selection_func = self.conversation_director.create_custom_speaker_selection(
                config.pattern
            )
            
            # Create enhanced termination condition
            termination_func = self.conversation_director.create_termination_condition(config)
            
            self.group_chat = autogen.GroupChat(
                agents=autogen_agents,
                messages=[],
                max_round=config.max_round,
                speaker_selection_method=speaker_selection_func,
                allow_repeat_speaker=config.allow_repeat_speaker
            )

            # Create manager with enhanced config
            manager_config = self.agents[0].config.to_llm_config() if self.agents else {}
            self.manager = autogen.GroupChatManager(
                groupchat=self.group_chat,
                llm_config=manager_config,
                is_termination_msg=termination_func
            )

            self.logger.info(f"Created enhanced group chat with {len(autogen_agents)} agents using {config.pattern.value} pattern")
            return self.group_chat

        except Exception as e:
            self.logger.error(f"Error creating enhanced group chat: {str(e)}")
            raise

    def execute_orchestrated_conversation(self, message: str, pattern: Optional[OrchestrationPattern] = None) -> Dict:
        """Execute a conversation with specific orchestration pattern"""
        start_time = datetime.now()
        pattern = pattern or self.conversation_config.pattern
        
        try:
            # Update pattern if different from current
            if pattern != self.conversation_config.pattern:
                self.conversation_config.pattern = pattern
                self.create_enhanced_group_chat()
            
            # Ensure group chat is created
            if not self.manager or not self.group_chat:
                self.create_enhanced_group_chat()

            # Execute conversation
            initiator = self.agents[0].agent
            chat_result = initiator.initiate_chat(
                self.manager,
                message=message,
                max_turns=self.conversation_config.max_round
            )

            # Calculate metrics
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            session_log = {
                "session_id": f"session_{start_time.timestamp()}",
                "start_time": start_time.isoformat(),
                "end_time": end_time.isoformat(),
                "duration_seconds": duration,
                "pattern": pattern.value,
                "initial_message": message,
                "agent_count": len(self.agents),
                "message_count": len(self.group_chat.messages) if self.group_chat else 0,
                "result": chat_result
            }
            
            self.session_logs.append(session_log)
            
            # Log for all agents
            for agent in self.agents:
                agent.log_message({
                    "type": "orchestrated_group_chat",
                    "pattern": pattern.value,
                    "message": message,
                    "session_id": session_log["session_id"],
                    "duration": duration
                })

            return session_log

        except Exception as e:
            self.logger.error(f"Error in orchestrated conversation: {str(e)}")
            raise

    def get_orchestration_analytics(self) -> Dict:
        """Get detailed analytics on orchestration performance"""
        if not self.session_logs:
            return {"message": "No orchestration sessions recorded"}
        
        total_sessions = len(self.session_logs)
        total_duration = sum(log["duration_seconds"] for log in self.session_logs)
        avg_duration = total_duration / total_sessions
        
        pattern_usage = {}
        for log in self.session_logs:
            pattern = log["pattern"]
            pattern_usage[pattern] = pattern_usage.get(pattern, 0) + 1
        
        return {
            "total_sessions": total_sessions,
            "total_duration_seconds": total_duration,
            "average_duration_seconds": avg_duration,
            "pattern_usage": pattern_usage,
            "agent_count": len(self.agents),
            "recent_sessions": self.session_logs[-5:] if len(self.session_logs) > 5 else self.session_logs
        }


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