"""
Test suite for specialized AutoGen agent types
"""

import pytest
import os
import sys
from unittest.mock import patch, MagicMock, Mock

# Add the src directory to the path so we can import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.utils.autogen_integration import (
    AutoGenConfig,
    DataAnalystAgent,
    TaskCoordinatorAgent,
    ResearchAgent,
    CreativeWriterAgent,
    ProblemSolverAgent,
    CodeReviewAgent,
    AutoGenAgentFactory,
    create_specialized_agents,
    MultiAgentChain,
    create_multi_agent_conversation,
    OrchestrationPattern,
    ConversationConfig,
    ConversationDirector,
    AdvancedMultiAgentChain,
    OrchestrationWorkflow,
    create_orchestrated_conversation
)


@pytest.fixture
def app_context():
    """Mock Flask app context"""
    with patch('swarm_director.utils.autogen_integration.current_app') as mock_app:
        mock_app.config = {'OPENAI_API_KEY': 'test-key'}
        yield mock_app


@pytest.fixture
def mock_autogen_modules():
    """Mock autogen modules"""
    with patch('swarm_director.utils.autogen_integration.autogen') as mock_autogen:
        mock_autogen.AssistantAgent = MagicMock()
        mock_autogen.UserProxyAgent = MagicMock()
        mock_autogen.GroupChat = MagicMock()
        mock_autogen.GroupChatManager = MagicMock()
        yield mock_autogen


class TestOrchestrationPattern:
    """Test orchestration pattern enum"""
    
    def test_orchestration_patterns_exist(self):
        """Test that all orchestration patterns are defined"""
        expected_patterns = [
            "round_robin", "expertise_based", "hierarchical", 
            "collaborative", "sequential", "democratic"
        ]
        
        for pattern in expected_patterns:
            assert hasattr(OrchestrationPattern, pattern.upper())
            assert OrchestrationPattern[pattern.upper()].value == pattern


class TestConversationConfig:
    """Test conversation configuration"""
    
    def test_default_config(self):
        """Test default conversation configuration"""
        config = ConversationConfig()
        
        assert config.max_round == 50
        assert config.pattern == OrchestrationPattern.EXPERTISE_BASED
        assert config.allow_repeat_speaker is True
        assert "TERMINATE" in config.termination_keywords
        assert config.min_contribution_threshold == 1
        assert config.max_consecutive_replies == 3
        assert config.enable_moderation is True
        assert config.timeout_minutes == 30

    def test_custom_config(self):
        """Test custom conversation configuration"""
        config = ConversationConfig(
            max_round=20,
            pattern=OrchestrationPattern.ROUND_ROBIN,
            termination_keywords=["DONE", "FINISHED"]
        )
        
        assert config.max_round == 20
        assert config.pattern == OrchestrationPattern.ROUND_ROBIN
        assert config.termination_keywords == ["DONE", "FINISHED"]


class TestConversationDirector:
    """Test conversation director functionality"""
    
    def test_init(self):
        """Test conversation director initialization"""
        director = ConversationDirector("TestDirector")
        
        assert director.name == "TestDirector"
        assert isinstance(director.config, AutoGenConfig)
        assert director.config.temperature == 0.3
        assert director.config.max_tokens == 800
        assert director.conversation_logs == []
        assert director.performance_metrics == {}

    def test_create_custom_speaker_selection_expertise_based(self):
        """Test expertise-based speaker selection"""
        director = ConversationDirector()
        selection_func = director.create_custom_speaker_selection(OrchestrationPattern.EXPERTISE_BASED)
        
        # Mock agents and groupchat
        data_agent = Mock()
        data_agent.name = "DataAnalyst"
        research_agent = Mock()
        research_agent.name = "Researcher"
        
        mock_groupchat = Mock()
        mock_groupchat.agents = [data_agent, research_agent]
        mock_groupchat.messages = [{"content": "We need data analysis on this dataset"}]
        
        # Test selection based on keyword
        selected = selection_func(research_agent, mock_groupchat)
        assert selected == data_agent

    def test_create_custom_speaker_selection_round_robin(self):
        """Test round-robin speaker selection"""
        director = ConversationDirector()
        selection_func = director.create_custom_speaker_selection(OrchestrationPattern.ROUND_ROBIN)
        
        # Mock agents
        agent1 = Mock()
        agent2 = Mock()
        agent3 = Mock()
        
        mock_groupchat = Mock()
        mock_groupchat.agents = [agent1, agent2, agent3]
        
        # Test round-robin selection
        selected = selection_func(agent1, mock_groupchat)
        assert selected == agent2
        
        selected = selection_func(agent2, mock_groupchat)
        assert selected == agent3

    def test_create_termination_condition(self):
        """Test custom termination condition"""
        config = ConversationConfig(termination_keywords=["TERMINATE", "DONE"])
        director = ConversationDirector()
        termination_func = director.create_termination_condition(config)
        
        # Test termination keyword
        message1 = {"content": "Task is DONE"}
        assert termination_func(message1) is True
        
        # Test completion phrase
        message2 = {"content": "Analysis complete and ready for review"}
        assert termination_func(message2) is True
        
        # Test non-termination message
        message3 = {"content": "Let's continue working on this"}
        assert termination_func(message3) is False
        
        # Test invalid message
        assert termination_func({}) is False
        assert termination_func(None) is False


@patch('swarm_director.utils.autogen_integration.autogen.GroupChat')
@patch('swarm_director.utils.autogen_integration.autogen.GroupChatManager')
class TestAdvancedMultiAgentChain:
    """Test advanced multi-agent chain functionality"""
    
    def test_init(self, mock_manager, mock_group_chat, app_context):
        """Test advanced chain initialization"""
        chain = AdvancedMultiAgentChain("AdvancedTestChain")
        
        assert chain.name == "AdvancedTestChain"
        assert isinstance(chain.conversation_config, ConversationConfig)
        assert isinstance(chain.conversation_director, ConversationDirector)
        assert chain.orchestration_metrics == {}
        assert chain.session_logs == []

    def test_create_enhanced_group_chat(self, mock_manager, mock_group_chat, app_context):
        """Test enhanced group chat creation"""
        # Mock autogen objects
        mock_group_chat.return_value = MagicMock()
        mock_manager.return_value = MagicMock()
        
        # Create chain and add agents
        chain = AdvancedMultiAgentChain("TestChain")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.agent = Mock()
        mock_agent.config = AutoGenConfig()
        chain.agents = [mock_agent]
        
        # Test group chat creation
        group_chat = chain.create_enhanced_group_chat()
        
        assert chain.group_chat is not None
        assert chain.manager is not None
        mock_group_chat.assert_called_once()
        mock_manager.assert_called_once()

    def test_create_enhanced_group_chat_no_agents(self, mock_manager, mock_group_chat):
        """Test enhanced group chat creation with no agents"""
        chain = AdvancedMultiAgentChain("TestChain")
        
        with pytest.raises(ValueError, match="No agents added to the chain"):
            chain.create_enhanced_group_chat()

    def test_execute_orchestrated_conversation(self, mock_manager, mock_group_chat, app_context):
        """Test orchestrated conversation execution"""
        # Mock autogen objects
        mock_group_chat_instance = MagicMock()
        mock_group_chat_instance.messages = [{"content": "test"}, {"content": "response"}]
        mock_group_chat.return_value = mock_group_chat_instance
        mock_manager.return_value = MagicMock()
        
        # Create chain and add agents
        chain = AdvancedMultiAgentChain("TestChain")
        
        # Mock agent
        mock_agent = Mock()
        mock_agent.agent = Mock()
        mock_agent.agent.initiate_chat.return_value = {"status": "success"}
        mock_agent.config = AutoGenConfig()
        mock_agent.log_message = Mock()
        chain.agents = [mock_agent]
        
        # Execute conversation
        result = chain.execute_orchestrated_conversation(
            "Test orchestration message", 
            OrchestrationPattern.EXPERTISE_BASED
        )
        
        # Verify result
        assert "session_id" in result
        assert "duration_seconds" in result
        assert result["pattern"] == "expertise_based"
        assert result["initial_message"] == "Test orchestration message"
        assert result["agent_count"] == 1
        assert len(chain.session_logs) == 1
        
        # Verify agent logging
        mock_agent.log_message.assert_called_once()

    def test_get_orchestration_analytics(self, mock_manager, mock_group_chat):
        """Test orchestration analytics"""
        chain = AdvancedMultiAgentChain("TestChain")
        
        # Test empty analytics
        analytics = chain.get_orchestration_analytics()
        assert analytics["message"] == "No orchestration sessions recorded"
        
        # Add mock session logs
        chain.session_logs = [
            {
                "duration_seconds": 10.5,
                "pattern": "expertise_based",
                "agent_count": 3
            },
            {
                "duration_seconds": 15.2,
                "pattern": "round_robin", 
                "agent_count": 3
            }
        ]
        
        analytics = chain.get_orchestration_analytics()
        assert analytics["total_sessions"] == 2
        assert analytics["total_duration_seconds"] == 25.7
        assert analytics["average_duration_seconds"] == 12.85
        assert analytics["pattern_usage"]["expertise_based"] == 1
        assert analytics["pattern_usage"]["round_robin"] == 1
        assert analytics["agent_count"] == 0  # No agents in this test setup


class TestOrchestrationWorkflow:
    """Test pre-defined orchestration workflows"""
    
    def test_create_research_workflow(self, app_context):
        """Test research workflow creation"""
        with patch('src.swarm_director.utils.autogen_integration.autogen'):
            workflow = OrchestrationWorkflow.create_research_workflow()
            
            assert isinstance(workflow, AdvancedMultiAgentChain)
            assert workflow.name == "ResearchWorkflow"
            assert len(workflow.agents) == 3
            assert workflow.conversation_config.pattern == OrchestrationPattern.EXPERTISE_BASED
            assert workflow.conversation_config.max_round == 30
            
            # Verify agent types
            agent_names = [agent.name for agent in workflow.agents]
            assert "Researcher" in agent_names
            assert "DataAnalyst" in agent_names  
            assert "TaskCoordinator" in agent_names

    def test_create_development_workflow(self, app_context):
        """Test development workflow creation"""
        with patch('src.swarm_director.utils.autogen_integration.autogen'):
            workflow = OrchestrationWorkflow.create_development_workflow()
            
            assert isinstance(workflow, AdvancedMultiAgentChain)
            assert workflow.name == "DevelopmentWorkflow"
            assert len(workflow.agents) == 3
            assert workflow.conversation_config.pattern == OrchestrationPattern.HIERARCHICAL
            assert workflow.conversation_config.max_round == 40
            
            # Verify agent types
            agent_names = [agent.name for agent in workflow.agents]
            assert "TaskCoordinator" in agent_names
            assert "ProblemSolver" in agent_names
            assert "CodeReviewer" in agent_names

    def test_create_creative_workflow(self, app_context):
        """Test creative workflow creation"""
        with patch('src.swarm_director.utils.autogen_integration.autogen'):
            workflow = OrchestrationWorkflow.create_creative_workflow()
            
            assert isinstance(workflow, AdvancedMultiAgentChain)
            assert workflow.name == "CreativeWorkflow"
            assert len(workflow.agents) == 3
            assert workflow.conversation_config.pattern == OrchestrationPattern.COLLABORATIVE
            assert workflow.conversation_config.max_round == 35

    def test_create_analysis_workflow(self, app_context):
        """Test analysis workflow creation"""
        with patch('src.swarm_director.utils.autogen_integration.autogen'):
            workflow = OrchestrationWorkflow.create_analysis_workflow()
            
            assert isinstance(workflow, AdvancedMultiAgentChain)
            assert workflow.name == "AnalysisWorkflow"
            assert len(workflow.agents) == 4
            assert workflow.conversation_config.pattern == OrchestrationPattern.EXPERTISE_BASED
            assert workflow.conversation_config.max_round == 45


class TestOrchestrationFunctions:
    """Test orchestration utility functions"""
    
    @patch('swarm_director.utils.autogen_integration.autogen')
    def test_create_orchestrated_conversation(self, mock_autogen, app_context):
        """Test orchestrated conversation creation function"""
        # Mock AutoGen objects
        mock_autogen.AssistantAgent.return_value = Mock()
        mock_autogen.GroupChat.return_value = Mock()
        mock_autogen.GroupChatManager.return_value = Mock()
        
        agent_configs = [
            {
                "type": "chat",
                "name": "TestAgent1",
                "role": "assistant",
                "model": "gpt-3.5-turbo",
                "temperature": 0.5
            },
            {
                "type": "chat", 
                "name": "TestAgent2",
                "role": "analyst"
            }
        ]
        
        with patch.object(AdvancedMultiAgentChain, 'execute_orchestrated_conversation') as mock_execute:
            mock_execute.return_value = {"status": "success", "pattern": "expertise_based"}
            
            result = create_orchestrated_conversation(
                agent_configs, 
                "Test orchestration message",
                OrchestrationPattern.EXPERTISE_BASED
            )
            
            assert result["status"] == "success"
            assert result["pattern"] == "expertise_based"
            mock_execute.assert_called_once_with("Test orchestration message", OrchestrationPattern.EXPERTISE_BASED)

    def test_create_orchestrated_conversation_error(self, app_context):
        """Test orchestrated conversation error handling"""
        # Test with invalid config that will cause error
        agent_configs = []  # Empty configs should cause error
        
        result = create_orchestrated_conversation(agent_configs, "Test message")
        assert "error" in result


class TestAutoGenConfig:
    """Test AutoGen configuration"""
    
    def test_default_config(self):
        """Test default configuration values"""
        config = AutoGenConfig()
        assert config.model == "gpt-3.5-turbo"
        assert config.temperature == 0.7
        assert config.max_tokens == 1000
        assert config.timeout == 120
        assert config.seed == 42
        
    def test_custom_config(self):
        """Test custom configuration values"""
        config = AutoGenConfig(
            model="gpt-4",
            temperature=0.5,
            max_tokens=2000,
            timeout=60
        )
        assert config.model == "gpt-4"
        assert config.temperature == 0.5
        assert config.max_tokens == 2000
        assert config.timeout == 60
        
    def test_to_llm_config(self, app_context):
        """Test conversion to LLM config"""
        config = AutoGenConfig(model="gpt-4", temperature=0.8)
        llm_config = config.to_llm_config()
        
        assert llm_config["config_list"][0]["model"] == "gpt-4"
        assert llm_config["temperature"] == 0.8
        assert llm_config["config_list"][0]["api_key"] == "test-api-key"


class TestSpecializedAgents:
    """Test specialized agent implementations"""
    
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_data_analyst_agent(self, mock_assistant, app_context):
        """Test DataAnalyst agent creation"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = DataAnalystAgent()
        
        assert agent.name == "DataAnalyst"
        assert agent.config.temperature == 0.3
        assert agent.config.max_tokens == 1500
        assert "data analyst" in agent.system_message.lower()
        assert "statistics" in agent.expertise_areas
        
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_task_coordinator_agent(self, mock_assistant, app_context):
        """Test TaskCoordinator agent creation"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = TaskCoordinatorAgent("CustomCoordinator")
        
        assert agent.name == "CustomCoordinator"
        assert agent.config.temperature == 0.5
        assert agent.config.max_tokens == 1200
        assert "task coordinator" in agent.system_message.lower()
        assert "project_management" in agent.expertise_areas
        
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_research_agent(self, mock_assistant, app_context):
        """Test Research agent creation"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = ResearchAgent()
        
        assert agent.name == "Researcher"
        assert agent.config.temperature == 0.4
        assert agent.config.max_tokens == 2000
        assert "research" in agent.system_message.lower()
        assert "research" in agent.expertise_areas
        
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_creative_writer_agent(self, mock_assistant, app_context):
        """Test CreativeWriter agent creation"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = CreativeWriterAgent()
        
        assert agent.name == "CreativeWriter"
        assert agent.config.temperature == 0.8  # Higher temperature for creativity
        assert agent.config.max_tokens == 1800
        assert "creative writer" in agent.system_message.lower()
        assert "creative_writing" in agent.expertise_areas
        
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_problem_solver_agent(self, mock_assistant, app_context):
        """Test ProblemSolver agent creation"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = ProblemSolverAgent()
        
        assert agent.name == "ProblemSolver"
        assert agent.config.temperature == 0.6
        assert agent.config.max_tokens == 1500
        assert "problem solver" in agent.system_message.lower()
        assert "problem_solving" in agent.expertise_areas
        
    @patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent')
    def test_code_review_agent(self, mock_proxy, app_context):
        """Test CodeReview agent creation"""
        mock_agent = MagicMock()
        mock_proxy.return_value = mock_agent
        
        agent = CodeReviewAgent()
        
        assert agent.name == "CodeReviewer"
        assert agent.config.temperature == 0.2  # Lower temperature for precision
        assert agent.config.max_tokens == 1500
        assert "code review" in agent.system_message.lower()
        assert "code_review" in agent.expertise_areas


class TestAutoGenAgentFactory:
    """Test the AutoGen agent factory"""
    
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_create_chat_agent(self, mock_assistant, app_context):
        """Test creating a chat agent via factory"""
        mock_agent = MagicMock()
        mock_assistant.return_value = mock_agent
        
        agent = AutoGenAgentFactory.create_chat_agent("TestAgent", "analyst")
        
        assert agent.name == "TestAgent"
        assert "data analyst" in agent.system_message.lower()
        
    @patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent')
    def test_create_tool_agent(self, mock_proxy, app_context):
        """Test creating a tool agent via factory"""
        mock_agent = MagicMock()
        mock_proxy.return_value = mock_agent
        
        agent = AutoGenAgentFactory.create_tool_agent("ToolAgent")
        
        assert agent.name == "ToolAgent"
        assert "helpful assistant" in agent.system_message.lower()
        
    def test_create_specialized_agent(self, app_context):
        """Test creating specialized agents via factory"""
        with patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent'):
            # Test creating data analyst
            agent = AutoGenAgentFactory.create_specialized_agent("data_analyst", "CustomAnalyst")
            assert isinstance(agent, DataAnalystAgent)
            assert agent.name == "CustomAnalyst"
            
            # Test creating task coordinator with default name
            agent = AutoGenAgentFactory.create_specialized_agent("task_coordinator")
            assert isinstance(agent, TaskCoordinatorAgent)
            assert agent.name == "TaskCoordinator"
            
        with patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent'):
            # Test creating code reviewer
            agent = AutoGenAgentFactory.create_specialized_agent("code_reviewer")
            assert isinstance(agent, CodeReviewAgent)
            assert agent.name == "CodeReviewer"
            
    def test_create_specialized_agent_invalid_type(self):
        """Test creating specialized agent with invalid type"""
        with pytest.raises(ValueError, match="Unknown specialized agent type"):
            AutoGenAgentFactory.create_specialized_agent("invalid_type")
            
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    @patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent')
    def test_create_agent_chain(self, mock_proxy, mock_assistant, app_context):
        """Test creating an agent chain"""
        mock_assistant.return_value = MagicMock()
        mock_proxy.return_value = MagicMock()
        
        agents_config = [
            {"name": "Analyst", "role": "analyst", "type": "chat"},
            {"name": "ToolAgent", "type": "tool"},
            {"name": "Writer", "role": "writer"}  # Default to chat type
        ]
        
        chain = AutoGenAgentFactory.create_agent_chain(agents_config)
        
        assert isinstance(chain, MultiAgentChain)
        assert len(chain.agents) == 3
        assert chain.agents[0].name == "Analyst"
        assert chain.agents[1].name == "ToolAgent"
        assert chain.agents[2].name == "Writer"


class TestMultiAgentChain:
    """Test multi-agent chain functionality"""
    
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_add_agent(self, mock_assistant, app_context):
        """Test adding agents to chain"""
        mock_assistant.return_value = MagicMock()
        
        chain = MultiAgentChain("TestChain")
        agent = DataAnalystAgent()
        
        chain.add_agent(agent)
        
        assert len(chain.agents) == 1
        assert chain.agents[0] == agent
        
    @patch('swarm_director.utils.autogen_integration.autogen.GroupChat')
    @patch('swarm_director.utils.autogen_integration.autogen.GroupChatManager')
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_create_group_chat(self, mock_assistant, mock_manager, mock_group_chat, app_context):
        """Test creating group chat"""
        mock_assistant.return_value = MagicMock()
        mock_group_chat.return_value = MagicMock()
        mock_manager.return_value = MagicMock()
        
        chain = MultiAgentChain()
        agent1 = DataAnalystAgent()
        agent2 = TaskCoordinatorAgent()
        
        chain.add_agent(agent1)
        chain.add_agent(agent2)
        
        group_chat = chain.create_group_chat()
        
        assert chain.group_chat is not None
        assert chain.manager is not None
        mock_group_chat.assert_called_once()
        mock_manager.assert_called_once()
        
    def test_create_group_chat_no_agents(self):
        """Test creating group chat with no agents raises error"""
        chain = MultiAgentChain()
        
        with pytest.raises(ValueError, match="No agents added to the chain"):
            chain.create_group_chat()
            
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_get_chain_stats(self, mock_assistant, app_context):
        """Test getting chain statistics"""
        mock_assistant.return_value = MagicMock()
        
        chain = MultiAgentChain("TestChain")
        agent = DataAnalystAgent()
        chain.add_agent(agent)
        
        stats = chain.get_chain_stats()
        
        assert stats["name"] == "TestChain"
        assert stats["agent_count"] == 1
        assert len(stats["agents"]) == 1
        assert "created_at" in stats


class TestUtilityFunctions:
    """Test utility functions"""
    
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    @patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent')
    def test_create_specialized_agents(self, mock_proxy, mock_assistant, app_context):
        """Test creating specialized agents utility function"""
        mock_assistant.return_value = MagicMock()
        mock_proxy.return_value = MagicMock()
        
        agents = create_specialized_agents()
        
        # Should create all specialized agent types
        expected_types = [
            'data_analyst', 'task_coordinator', 'researcher',
            'creative_writer', 'problem_solver', 'code_reviewer'
        ]
        
        for agent_type in expected_types:
            assert agent_type in agents
            
        assert len(agents) == len(expected_types)
        
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    def test_create_specialized_agents_with_config(self, mock_assistant, app_context):
        """Test creating specialized agents with custom config"""
        mock_assistant.return_value = MagicMock()
        
        custom_config = AutoGenConfig(model="gpt-4", temperature=0.9)
        agents = create_specialized_agents(custom_config)
        
        # Check that agents use the custom config
        for agent in agents.values():
            if hasattr(agent, 'config'):
                assert agent.config.model == "gpt-4"


class TestIntegrationScenarios:
    """Test real-world integration scenarios"""
    
    @patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent')
    @patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent')
    def test_mixed_agent_chain_scenario(self, mock_proxy, mock_assistant, app_context):
        """Test creating a mixed chain with different agent types"""
        mock_assistant.return_value = MagicMock()
        mock_proxy.return_value = MagicMock()
        
        # Create a chain with data analyst, code reviewer, and task coordinator
        chain = MultiAgentChain("ProjectTeam")
        
        analyst = DataAnalystAgent("DataExpert")
        reviewer = CodeReviewAgent("CodeExpert")
        coordinator = TaskCoordinatorAgent("ProjectManager")
        
        chain.add_agent(analyst)
        chain.add_agent(reviewer)
        chain.add_agent(coordinator)
        
        assert len(chain.agents) == 3
        
        # Verify each agent has different expertise
        assert "statistics" in analyst.expertise_areas
        assert "code_review" in reviewer.expertise_areas
        assert "project_management" in coordinator.expertise_areas
        
        # Verify different configurations
        assert analyst.config.temperature == 0.3  # Low for analysis
        assert reviewer.config.temperature == 0.2  # Lowest for precision
        assert coordinator.config.temperature == 0.5  # Medium for coordination
        
    def test_agent_expertise_mapping(self, app_context):
        """Test that agents have appropriate expertise areas"""
        with patch('swarm_director.utils.autogen_integration.autogen.AssistantAgent'), \
             patch('swarm_director.utils.autogen_integration.autogen.UserProxyAgent'):
            
            agents = create_specialized_agents()
            
            # Verify expertise mappings
            assert "statistics" in agents['data_analyst'].expertise_areas
            assert "project_management" in agents['task_coordinator'].expertise_areas
            assert "research" in agents['researcher'].expertise_areas
            assert "creative_writing" in agents['creative_writer'].expertise_areas
            assert "problem_solving" in agents['problem_solver'].expertise_areas
            assert "code_review" in agents['code_reviewer'].expertise_areas


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"]) 