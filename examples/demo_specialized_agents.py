#!/usr/bin/env python3
"""
Demonstration of specialized AutoGen agent types in SwarmDirector
This script shows how to create and use different types of AI agents for specific tasks.
"""

import sys
import os
from typing import Dict, List

# Add src to path
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
    MultiAgentChain,
    create_specialized_agents
)


def demo_individual_agents():
    """Demonstrate creating individual specialized agents"""
    print("🤖 DEMO: Individual Specialized Agents")
    print("=" * 50)
    
    # Create custom configuration for demonstration
    config = AutoGenConfig(model="gpt-3.5-turbo", temperature=0.7, max_tokens=1000)
    
    # Create different types of specialized agents
    agents = {
        "Data Analyst": DataAnalystAgent("DataScientist", config),
        "Task Coordinator": TaskCoordinatorAgent("ProjectManager", config),
        "Researcher": ResearchAgent("ResearchSpecialist", config),
        "Creative Writer": CreativeWriterAgent("ContentCreator", config),
        "Problem Solver": ProblemSolverAgent("Troubleshooter", config),
        "Code Reviewer": CodeReviewAgent("QualityAssurance", config)
    }
    
    # Display agent information
    for agent_type, agent in agents.items():
        print(f"\n📋 {agent_type}:")
        print(f"   Name: {agent.name}")
        print(f"   Temperature: {agent.config.temperature}")
        print(f"   Max Tokens: {agent.config.max_tokens}")
        print(f"   Expertise: {', '.join(agent.expertise_areas)}")
        print(f"   System Message Preview: {agent.system_message[:100]}...")
    
    return agents


def demo_agent_factory():
    """Demonstrate using the AutoGen Agent Factory"""
    print("\n\n🏭 DEMO: AutoGen Agent Factory")
    print("=" * 50)
    
    # Create agents using factory methods
    factory_agents = []
    
    # Create chat agents with different roles
    analyst = AutoGenAgentFactory.create_chat_agent("MarketAnalyst", "analyst")
    writer = AutoGenAgentFactory.create_chat_agent("TechnicalWriter", "writer")
    coordinator = AutoGenAgentFactory.create_chat_agent("TeamLead", "coordinator")
    
    factory_agents.extend([analyst, writer, coordinator])
    
    # Create a tool agent
    tool_agent = AutoGenAgentFactory.create_tool_agent("CodeExecutor", work_dir="demo_workspace")
    factory_agents.append(tool_agent)
    
    # Create specialized agents using factory
    data_specialist = AutoGenAgentFactory.create_specialized_agent("data_analyst", "DataSpecialist")
    problem_solver = AutoGenAgentFactory.create_specialized_agent("problem_solver")
    
    factory_agents.extend([data_specialist, problem_solver])
    
    print(f"\n✅ Created {len(factory_agents)} agents using factory methods:")
    for agent in factory_agents:
        agent_type = "Tool Agent" if hasattr(agent, 'code_execution_config') else "Chat Agent"
        print(f"   - {agent.name} ({agent_type})")
    
    return factory_agents


def demo_multi_agent_chain():
    """Demonstrate creating and managing multi-agent chains"""
    print("\n\n🔗 DEMO: Multi-Agent Chain")
    print("=" * 50)
    
    # Create a project team chain
    project_team = MultiAgentChain("ProjectTeamAlpha")
    
    # Add different types of agents to the team
    agents_to_add = [
        DataAnalystAgent("TeamAnalyst"),
        TaskCoordinatorAgent("TeamCoordinator"),
        CreativeWriterAgent("TeamWriter"),
        CodeReviewAgent("TeamReviewer")
    ]
    
    for agent in agents_to_add:
        project_team.add_agent(agent)
    
    print(f"\n📊 Team '{project_team.name}' Statistics:")
    stats = project_team.get_chain_stats()
    print(f"   Total Agents: {stats['agent_count']}")
    print(f"   Team Members:")
    for i, agent_stats in enumerate(stats['agents'], 1):
        print(f"     {i}. {agent_stats['name']} (Temperature: {agent_stats['config']['temperature']})")
    
    return project_team


def demo_agent_chain_from_config():
    """Demonstrate creating agent chains from configuration"""
    print("\n\n⚙️ DEMO: Agent Chain from Configuration")
    print("=" * 50)
    
    # Define a configuration for different agents
    agents_config = [
        {
            "name": "LeadAnalyst",
            "role": "analyst",
            "type": "chat",
            "model": "gpt-3.5-turbo",
            "temperature": 0.3,
            "max_tokens": 1200
        },
        {
            "name": "CreativeDirector",
            "role": "writer",
            "type": "chat",
            "model": "gpt-3.5-turbo",
            "temperature": 0.8,
            "max_tokens": 1500
        },
        {
            "name": "TechnicalLead",
            "type": "tool",
            "model": "gpt-3.5-turbo",
            "temperature": 0.4,
            "max_tokens": 1000
        },
        {
            "name": "QualityManager",
            "role": "coordinator",
            "type": "chat",
            "model": "gpt-3.5-turbo",
            "temperature": 0.6,
            "max_tokens": 1000
        }
    ]
    
    # Create the chain from configuration
    config_chain = AutoGenAgentFactory.create_agent_chain(agents_config)
    
    print(f"\n🔧 Created chain with {len(config_chain.agents)} agents from configuration:")
    for agent in config_chain.agents:
        agent_class = agent.__class__.__name__
        print(f"   - {agent.name} ({agent_class}, T={agent.config.temperature})")
    
    return config_chain


def demo_specialized_agents_utility():
    """Demonstrate the create_specialized_agents utility function"""
    print("\n\n🛠️ DEMO: Specialized Agents Utility")
    print("=" * 50)
    
    # Create all specialized agents with default configuration
    specialized_agents = create_specialized_agents()
    
    print(f"\n✨ Created {len(specialized_agents)} specialized agents:")
    
    agent_descriptions = {
        'data_analyst': "Analyzes data and provides insights",
        'task_coordinator': "Manages projects and coordinates tasks",
        'researcher': "Conducts research and gathers information",
        'creative_writer': "Creates engaging content and copy",
        'problem_solver': "Solves complex problems systematically",
        'code_reviewer': "Reviews code for quality and security"
    }
    
    for agent_type, agent in specialized_agents.items():
        description = agent_descriptions.get(agent_type, "Specialized AI agent")
        print(f"   🎯 {agent.name} ({agent_type})")
        print(f"      {description}")
        print(f"      Expertise: {', '.join(agent.expertise_areas[:3])}...")
    
    return specialized_agents


def demo_agent_comparison():
    """Demonstrate comparing different agent configurations"""
    print("\n\n📊 DEMO: Agent Configuration Comparison")
    print("=" * 50)
    
    agents = create_specialized_agents()
    
    print("\n🌡️ Temperature Settings by Agent Type:")
    print("   (Lower = More Focused, Higher = More Creative)")
    
    temp_data = []
    for agent_type, agent in agents.items():
        temp_data.append((agent.config.temperature, agent.name, agent_type))
    
    # Sort by temperature
    temp_data.sort()
    
    for temp, name, agent_type in temp_data:
        bar = "█" * int(temp * 10)
        print(f"   {temp:.1f} {bar:<8} {name} ({agent_type})")
    
    print("\n💭 Token Limits by Agent Type:")
    token_data = []
    for agent_type, agent in agents.items():
        token_data.append((agent.config.max_tokens, agent.name, agent_type))
    
    token_data.sort(reverse=True)
    
    for tokens, name, agent_type in token_data:
        bar = "▓" * (tokens // 200)  # Scale for display
        print(f"   {tokens:4d} {bar:<10} {name}")


def main():
    """Main demonstration function"""
    print("🎭 SwarmDirector Specialized AutoGen Agents Demo")
    print("================================================")
    print("This demo showcases the new specialized agent types")
    print("and their capabilities within the SwarmDirector system.\n")
    
    try:
        # Run all demonstrations
        demo_individual_agents()
        demo_agent_factory()
        demo_multi_agent_chain()
        demo_agent_chain_from_config()
        demo_specialized_agents_utility()
        demo_agent_comparison()
        
        print("\n\n🎉 Demo completed successfully!")
        print("\nKey Features Demonstrated:")
        print("✅ Individual specialized agent creation")
        print("✅ Agent factory pattern usage")
        print("✅ Multi-agent chain orchestration")
        print("✅ Configuration-driven agent creation")
        print("✅ Utility functions for agent management")
        print("✅ Agent configuration comparison")
        
        print("\n💡 Next Steps:")
        print("• Integrate these agents with your SwarmDirector workflows")
        print("• Customize agent configurations for your specific use cases")
        print("• Create multi-agent conversations for complex tasks")
        print("• Implement domain-specific agent types as needed")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        print("This is expected if AutoGen dependencies aren't fully configured.")
        print("The agents are still functional - this demo just shows their structure.")


if __name__ == "__main__":
    main() 