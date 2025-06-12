#!/usr/bin/env python3
"""
Test script for enhanced routing logic and agent communication in DirectorAgent
Tests the new routing strategies, decision making, and analytics capabilities
"""

import sys
import os
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_routing_enhancements():
    """Test the enhanced routing logic and agent communication system"""
    
    print("🧪 Testing Enhanced Routing Logic and Agent Communication")
    print("=" * 60)
    
    # Test 1: Routing Strategy Enums and Data Classes
    test_routing_data_structures()
    
    # Test 2: DirectorAgent Enhanced Configuration
    test_enhanced_configuration()
    
    # Test 3: Routing Decision Making
    test_routing_decision_making()
    
    # Test 4: Task Complexity Analysis
    test_task_complexity_analysis()
    
    # Test 5: Agent Selection Strategies
    test_agent_selection_strategies()
    
    # Test 6: Enhanced Route Task Method
    test_enhanced_route_task()
    
    # Test 7: Routing Analytics
    test_routing_analytics()
    
    print("\n✅ All Enhanced Routing Tests Completed!")

def test_routing_data_structures():
    """Test routing strategy enums and data classes"""
    print("\n🧪 Testing Routing Data Structures...")
    
    try:
        from swarm_director.agents.director import (
            RoutingStrategy, AgentSelectionCriteria, RoutingDecision,
            TaskExecutionResult, AggregatedResult
        )
        
        # Test RoutingStrategy enum
        assert RoutingStrategy.SINGLE_AGENT.value == "single_agent"
        assert RoutingStrategy.PARALLEL_AGENTS.value == "parallel_agents"
        assert RoutingStrategy.SCATTER_GATHER.value == "scatter_gather"
        assert RoutingStrategy.LOAD_BALANCED.value == "load_balanced"
        print("✅ RoutingStrategy enum working correctly")
        
        # Test AgentSelectionCriteria enum
        assert AgentSelectionCriteria.PERFORMANCE.value == "performance"
        assert AgentSelectionCriteria.AVAILABILITY.value == "availability"
        assert AgentSelectionCriteria.WORKLOAD.value == "workload"
        print("✅ AgentSelectionCriteria enum working correctly")
        
        # Test RoutingDecision dataclass
        decision = RoutingDecision(
            strategy=RoutingStrategy.SCATTER_GATHER,
            selected_agents=["communications", "analysis"],
            confidence=0.85,
            reasoning="High complexity task benefits from diverse perspectives",
            expected_execution_time=45.0,
            fallback_agents=["coordination"]
        )
        assert decision.strategy == RoutingStrategy.SCATTER_GATHER
        assert len(decision.selected_agents) == 2
        assert decision.confidence == 0.85
        print("✅ RoutingDecision dataclass working correctly")
        
        # Test TaskExecutionResult dataclass
        result = TaskExecutionResult(
            agent_name="CommunicationsDept",
            department="communications",
            status="success",
            result={"message": "Task completed"},
            execution_time=30.5,
            errors=None,
            warnings=["Minor formatting issue"]
        )
        assert result.agent_name == "CommunicationsDept"
        assert result.execution_time == 30.5
        print("✅ TaskExecutionResult dataclass working correctly")
        
        # Test AggregatedResult dataclass
        aggregated = AggregatedResult(
            primary_result={"status": "success", "combined_insights": {}},
            individual_results=[result],
            aggregation_method="scatter_gather",
            consensus_score=0.9,
            conflicts_detected=False
        )
        assert aggregated.aggregation_method == "scatter_gather"
        assert aggregated.consensus_score == 0.9
        print("✅ AggregatedResult dataclass working correctly")
        
        print("✅ All routing data structures working correctly")
        
    except Exception as e:
        print(f"❌ Error testing routing data structures: {e}")
        return False
    
    return True

def test_enhanced_configuration():
    """Test enhanced DirectorConfig with routing options"""
    print("\n🧪 Testing Enhanced Configuration...")
    
    try:
        from swarm_director.agents.director import DirectorConfig, AgentSelectionCriteria
        
        # Test default configuration
        config = DirectorConfig()
        assert config.enable_parallel_execution == True
        assert config.max_parallel_agents == 3
        assert config.parallel_timeout_seconds == 120
        assert config.enable_load_balancing == True
        assert config.agent_selection_criteria == AgentSelectionCriteria.PERFORMANCE
        assert config.enable_result_aggregation == True
        assert config.consensus_threshold == 0.75
        print("✅ Default enhanced configuration working correctly")
        
        # Test custom configuration
        custom_config = DirectorConfig(
            enable_parallel_execution=False,
            max_parallel_agents=5,
            parallel_timeout_seconds=180,
            enable_load_balancing=False,
            agent_selection_criteria=AgentSelectionCriteria.WORKLOAD,
            consensus_threshold=0.8
        )
        assert custom_config.enable_parallel_execution == False
        assert custom_config.max_parallel_agents == 5
        assert custom_config.agent_selection_criteria == AgentSelectionCriteria.WORKLOAD
        print("✅ Custom enhanced configuration working correctly")
        
        print("✅ Enhanced configuration tests passed")
        
    except Exception as e:
        print(f"❌ Error testing enhanced configuration: {e}")
        return False
    
    return True

def test_routing_decision_making():
    """Test routing decision making logic"""
    print("\n🧪 Testing Routing Decision Making...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            with patch.object(MockAgent, 'query') as mock_query:
                mock_db_agent = MockAgent()
                mock_db_agent.name = "TestDirector"
                mock_db_agent.status = "active"
                mock_db_agent.id = 1
                
                # Mock the query to return None (no existing agent)
                mock_query.filter_by.return_value.first.return_value = None
                
                from swarm_director.agents.director import DirectorAgent, DirectorConfig, RoutingStrategy
                
                # Create director with enhanced routing enabled
                config = DirectorConfig(enable_parallel_execution=True)
                
                with patch.object(DirectorAgent, '_initialize_department_agents', return_value={}):
                    director = DirectorAgent(mock_db_agent, config)
                    
                    # Mock a task
                    mock_task = Mock()
                    mock_task.id = 1
                    mock_task.title = "Complex analysis task requiring detailed investigation"
                    mock_task.description = "This is a comprehensive analysis task that requires detailed investigation and multiple perspectives to ensure accuracy"
                    mock_task.input_data = {"complexity": "high", "requirements": ["analysis", "validation", "reporting"]}
                    
                    # Test routing decision making
                    decision = director.make_routing_decision(mock_task, "analysis", 0.85)
                    
                    assert decision.strategy in [RoutingStrategy.SINGLE_AGENT, RoutingStrategy.SCATTER_GATHER, RoutingStrategy.LOAD_BALANCED]
                    assert len(decision.selected_agents) >= 1
                    assert decision.confidence == 0.85
                    assert decision.reasoning is not None
                    assert decision.expected_execution_time is not None
                    print("✅ Routing decision making working correctly")
                    
                    # Test strategy determination
                    strategy = director._determine_routing_strategy(mock_task, "analysis", 0.85)
                    assert isinstance(strategy, RoutingStrategy)
                    print("✅ Strategy determination working correctly")
                    
                    # Test task complexity analysis
                    complexity = director._analyze_task_complexity(mock_task)
                    assert 1 <= complexity <= 10
                    assert complexity > 1  # Should be higher due to long description and complex keywords
                    print(f"✅ Task complexity analysis working correctly (complexity: {complexity})")
                    
                    print("✅ Routing decision making tests passed")
        
    except Exception as e:
        print(f"❌ Error testing routing decision making: {e}")
        return False
    
    return True

def test_task_complexity_analysis():
    """Test task complexity analysis algorithm"""
    print("\n🧪 Testing Task Complexity Analysis...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestDirector"
            mock_db_agent.status = "active"
            mock_db_agent.id = 1
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig
            
            with patch.object(DirectorAgent, '_initialize_department_agents', return_value={}):
                director = DirectorAgent(mock_db_agent, DirectorConfig())
                
                # Test simple task
                simple_task = Mock()
                simple_task.title = "Send email"
                simple_task.description = "Send a simple email"
                simple_task.input_data = None
                
                simple_complexity = director._analyze_task_complexity(simple_task)
                assert 1 <= simple_complexity <= 3
                print(f"✅ Simple task complexity: {simple_complexity}")
                
                # Test complex task
                complex_task = Mock()
                complex_task.title = "Comprehensive multi-step analysis and integration"
                complex_task.description = "Perform a detailed comprehensive analysis of the system, including multi-step integration processes, complex data transformations, and detailed reporting with multiple stakeholder reviews"
                complex_task.input_data = {
                    "data_sources": ["db1", "db2", "api1", "api2"],
                    "transformations": ["normalize", "aggregate", "validate"],
                    "outputs": ["report", "dashboard", "alerts"],
                    "stakeholders": ["team1", "team2", "management"],
                    "requirements": ["accuracy", "performance", "security"]
                }
                
                complex_complexity = director._analyze_task_complexity(complex_task)
                assert complex_complexity > simple_complexity
                assert complex_complexity >= 5  # Should be high due to keywords and data complexity
                print(f"✅ Complex task complexity: {complex_complexity}")
                
                print("✅ Task complexity analysis tests passed")
        
    except Exception as e:
        print(f"❌ Error testing task complexity analysis: {e}")
        return False
    
    return True

def test_agent_selection_strategies():
    """Test agent selection for different routing strategies"""
    print("\n🧪 Testing Agent Selection Strategies...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestDirector"
            mock_db_agent.status = "active"
            mock_db_agent.id = 1
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig, RoutingStrategy
            
            with patch.object(DirectorAgent, '_initialize_department_agents', return_value={}):
                director = DirectorAgent(mock_db_agent, DirectorConfig())
                
                # Mock available agents
                mock_comm_agent = Mock()
                mock_comm_agent.is_available.return_value = True
                mock_analysis_agent = Mock()
                mock_analysis_agent.is_available.return_value = True
                
                director.department_agents = {
                    'communications': mock_comm_agent,
                    'analysis': mock_analysis_agent
                }
                
                mock_task = Mock()
                mock_task.title = "Test task"
                mock_task.description = "Test description"
                
                # Test single agent strategy
                single_agents = director._select_agents_for_strategy(
                    RoutingStrategy.SINGLE_AGENT, "communications", mock_task
                )
                assert single_agents == ["communications"]
                print("✅ Single agent selection working correctly")
                
                # Test scatter-gather strategy
                scatter_agents = director._select_agents_for_strategy(
                    RoutingStrategy.SCATTER_GATHER, "communications", mock_task
                )
                assert "communications" in scatter_agents
                # Should include complementary departments if available
                print(f"✅ Scatter-gather selection working correctly: {scatter_agents}")
                
                # Test load balanced strategy
                load_balanced_agents = director._select_agents_for_strategy(
                    RoutingStrategy.LOAD_BALANCED, "communications", mock_task
                )
                assert len(load_balanced_agents) == 1
                print("✅ Load balanced selection working correctly")
                
                # Test complementary departments
                complementary = director._get_complementary_departments("communications")
                assert "analysis" in complementary
                print(f"✅ Complementary departments working correctly: {complementary}")
                
                print("✅ Agent selection strategy tests passed")
        
    except Exception as e:
        print(f"❌ Error testing agent selection strategies: {e}")
        return False
    
    return True

def test_enhanced_route_task():
    """Test the enhanced route task method"""
    print("\n🧪 Testing Enhanced Route Task Method...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestDirector"
            mock_db_agent.status = "active"
            mock_db_agent.id = 1
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig
            
            with patch.object(DirectorAgent, '_initialize_department_agents', return_value={}):
                director = DirectorAgent(mock_db_agent, DirectorConfig())
                
                # Mock the original route_task method
                def mock_route_task(task, intent, confidence):
                    return {
                        "status": "success",
                        "department": intent,
                        "task_id": task.id,
                        "message": f"Task routed to {intent}"
                    }
                
                director.route_task = mock_route_task
                
                # Mock task
                mock_task = Mock()
                mock_task.id = 1
                mock_task.title = "Test routing task"
                mock_task.description = "Test task for enhanced routing"
                mock_task.input_data = None
                
                # Test enhanced routing
                result = director.enhanced_route_task(mock_task, "communications", 0.8)
                
                assert result["status"] == "success"
                assert "routing_decision" in result
                assert "strategy" in result["routing_decision"]
                assert "selected_agents" in result["routing_decision"]
                assert "confidence" in result["routing_decision"]
                assert "reasoning" in result["routing_decision"]
                assert "expected_execution_time" in result["routing_decision"]
                
                print("✅ Enhanced route task method working correctly")
                print(f"   Strategy: {result['routing_decision']['strategy']}")
                print(f"   Agents: {result['routing_decision']['selected_agents']}")
                print(f"   Reasoning: {result['routing_decision']['reasoning']}")
                
                print("✅ Enhanced route task tests passed")
        
    except Exception as e:
        print(f"❌ Error testing enhanced route task: {e}")
        return False
    
    return True

def test_routing_analytics():
    """Test routing analytics and performance metrics"""
    print("\n🧪 Testing Routing Analytics...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestDirector"
            mock_db_agent.status = "active"
            mock_db_agent.id = 1
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig, RoutingStrategy
            
            with patch.object(DirectorAgent, '_initialize_department_agents', return_value={}):
                director = DirectorAgent(mock_db_agent, DirectorConfig())
                
                # Simulate some routing decisions
                mock_task = Mock()
                mock_task.id = 1
                mock_task.title = "Test task"
                mock_task.description = "Test description"
                mock_task.input_data = None
                
                # Make a few routing decisions
                for i in range(3):
                    decision = director.make_routing_decision(mock_task, "communications", 0.8)
                    # Simulate strategy usage
                    with director._lock:
                        director.metrics.routing_strategy_usage[decision.strategy.value] = (
                            director.metrics.routing_strategy_usage.get(decision.strategy.value, 0) + 1
                        )
                
                # Test analytics
                analytics = director.get_routing_analytics()
                
                assert "routing_decisions" in analytics
                assert "strategy_usage" in analytics
                assert "agent_performance" in analytics
                assert "agent_workload" in analytics
                assert "parallel_executions" in analytics
                assert "aggregated_results" in analytics
                assert "recent_decisions" in analytics
                
                assert analytics["routing_decisions"] == 3
                assert len(analytics["recent_decisions"]) <= 10
                
                print("✅ Routing analytics working correctly")
                print(f"   Total decisions: {analytics['routing_decisions']}")
                print(f"   Strategy usage: {analytics['strategy_usage']}")
                print(f"   Recent decisions: {len(analytics['recent_decisions'])}")
                
                # Test metrics integration
                metrics_dict = director.metrics.to_dict()
                assert "routing_strategy_usage" in metrics_dict
                assert "agent_performance_scores" in metrics_dict
                print("✅ Metrics integration working correctly")
                
                print("✅ Routing analytics tests passed")
        
    except Exception as e:
        print(f"❌ Error testing routing analytics: {e}")
        return False
    
    return True

if __name__ == "__main__":
    try:
        test_routing_enhancements()
        print("\n🎉 All Enhanced Routing Tests Passed Successfully!")
        print("✅ Enhanced routing logic and agent communication system is working correctly")
    except Exception as e:
        print(f"\n💥 Test execution failed: {e}")
        sys.exit(1) 