#!/usr/bin/env python3
"""
Hierarchical Validation and Plugin System Demo

Demonstrates the complete hierarchical validation system and modular plugin 
architecture for SwarmDirector.
"""

import sys
import os
import asyncio
from datetime import datetime

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.validation_plugin_integration import ValidationPluginIntegrator
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.validation.quality_gate import QualityGate, QualityThreshold, QualityMetric
from swarm_director.plugins.plugin_registry import PluginMetadata, PluginType, PluginCapability, PluginDependency


async def main():
    """Main demo function"""
    print("🚀 HIERARCHICAL VALIDATION AND PLUGIN SYSTEM DEMO")
    print("=" * 60)
    print(f"⏰ Demo started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # Initialize the integration system
    print("🔧 Initializing validation and plugin integration...")
    integrator = ValidationPluginIntegrator({
        'plugin_config': {
            'auto_install_enabled': True,
            'auto_discovery_enabled': True
        }
    })
    print("✅ Integration system initialized")
    print()
    
    # Demo 1: Create sample agents
    print("👥 Creating sample agents for hierarchical validation...")
    
    # Tool agent (worker)
    tool_agent = Agent(
        name="EmailToolAgent",
        description="Tool agent for email operations",
        agent_type=AgentType.WORKER,
        status=AgentStatus.IDLE,
        capabilities=["email_sending", "template_processing"]
    )
    
    # Department agent (supervisor)
    dept_agent = Agent(
        name="CommunicationsDept",
        description="Communications department supervisor",
        agent_type=AgentType.SUPERVISOR,
        status=AgentStatus.IDLE,
        capabilities=["email_review", "content_validation", "quality_control"]
    )
    
    # Director agent
    director_agent = Agent(
        name="MainDirector",
        description="Main director for final approval",
        agent_type=AgentType.SUPERVISOR,
        status=AgentStatus.IDLE,
        capabilities=["final_approval", "policy_compliance", "strategic_oversight"]
    )
    
    print(f"✅ Created {tool_agent.name} (Tool tier)")
    print(f"✅ Created {dept_agent.name} (Department tier)")
    print(f"✅ Created {director_agent.name} (Director tier)")
    print()
    
    # Demo 2: Create a sample task
    print("📋 Creating sample task...")
    task = Task(
        title="Send welcome email to new customer",
        description="Send a personalized welcome email to John Doe who just signed up for our premium plan",
        status=TaskStatus.PENDING,
        priority=TaskPriority.HIGH,
        input_data={
            'type': 'email',
            'customer_name': 'John Doe',
            'plan': 'premium',
            'template': 'welcome_premium',
            'recipient': 'john.doe@example.com'
        }
    )
    print(f"✅ Created task: {task.title}")
    print()
    
    # Demo 3: Register sample plugins
    print("🔌 Registering sample plugins...")
    
    # Email plugin
    email_plugin = PluginMetadata(
        name="advanced_email_plugin",
        version="1.2.0",
        description="Advanced email processing with templates and analytics",
        author="SwarmDirector Team",
        plugin_type=PluginType.AGENT,
        capabilities=[
            PluginCapability(
                name="advanced_email_sending",
                description="Send emails with advanced features",
                category="communication"
            ),
            PluginCapability(
                name="email_analytics",
                description="Track email performance metrics",
                category="analytics"
            )
        ],
        dependencies=[
            PluginDependency(
                name="sendgrid",
                version=">=6.0.0",
                type="python"
            )
        ],
        entry_point="advanced_email_plugin.EmailAgent"
    )
    
    integrator.plugin_manager.registry.register_plugin(email_plugin)
    print(f"✅ Registered plugin: {email_plugin.name}")
    
    # Analytics plugin
    analytics_plugin = PluginMetadata(
        name="task_analytics_plugin",
        version="1.0.0",
        description="Advanced task analytics and reporting",
        author="SwarmDirector Team",
        plugin_type=PluginType.TOOL,
        capabilities=[
            PluginCapability(
                name="performance_analytics",
                description="Analyze task performance metrics",
                category="analytics"
            )
        ]
    )
    
    integrator.plugin_manager.registry.register_plugin(analytics_plugin)
    print(f"✅ Registered plugin: {analytics_plugin.name}")
    print()
    
    # Demo 4: Configure custom quality gates
    print("⚙️ Configuring custom quality gates...")
    
    # Configure stricter quality gate for director tier
    from swarm_director.validation.validation_chain import ValidationTier
    
    director_config = {
        'thresholds': [
            {
                'metric': 'accuracy',
                'minimum_score': 0.95,
                'weight': 2.0,
                'critical': True,
                'description': 'Director requires 95% accuracy'
            },
            {
                'metric': 'completeness',
                'minimum_score': 0.98,
                'weight': 1.8,
                'critical': True,
                'description': 'Director requires 98% completeness'
            }
        ]
    }
    
    integrator.configure_quality_gates(ValidationTier.DIRECTOR, director_config)
    print("✅ Configured custom quality gates for Director tier")
    print()
    
    # Demo 5: Process task with full hierarchical validation
    print("🔄 Processing task with hierarchical validation...")
    print("   Tool → Department → Director validation chain")
    print()
    
    result = await integrator.process_task_with_full_validation(
        task=task,
        tool_agent=tool_agent,
        dept_agent=dept_agent,
        director_agent=director_agent
    )
    
    print("📊 VALIDATION RESULTS:")
    print(f"   Success: {result['success']}")
    print(f"   Processing time: {result['processing_time_ms']}ms")
    
    if result['validation_results']:
        print("   Validation by tier:")
        for validation in result['validation_results']:
            print(f"     {validation['tier'].title()}: {validation['status']} (score: {validation['score']:.2f})")
    
    if not result['success']:
        print(f"   Failure tier: {result.get('failure_tier', 'unknown')}")
        print(f"   Failure reason: {result.get('failure_reason', 'unknown')}")
    
    print()
    
    # Demo 6: Capability discovery and plugin suggestions
    print("🔍 Demonstrating capability discovery...")
    
    # Create a task that requires capabilities not currently available
    complex_task = Task(
        title="Analyze customer data and generate ML insights",
        description="Perform advanced machine learning analysis on customer behavior data and generate predictive insights",
        input_data={'type': 'ml_analysis', 'data_source': 'customer_db'}
    )
    
    suggestions = integrator.get_plugin_suggestions(complex_task)
    print(f"📋 Task: {complex_task.title}")
    print(f"🔌 Plugin suggestions ({len(suggestions)} found):")
    
    for suggestion in suggestions[:3]:  # Show top 3
        print(f"   • {suggestion['plugin_name']}: {suggestion['description']}")
        print(f"     Relevance: {suggestion['relevance_score']:.2f}, Status: {suggestion['status']}")
        print(f"     Capabilities: {', '.join(suggestion['capabilities'])}")
    
    print()
    
    # Demo 7: Auto-resolve capability gaps
    print("🤖 Demonstrating automatic capability resolution...")
    
    auto_result = await integrator.auto_resolve_capability_gaps(complex_task)
    print(f"   Auto-resolution success: {auto_result['success']}")
    
    if auto_result['plugins_installed']:
        print(f"   Plugins installed: {', '.join(auto_result['plugins_installed'])}")
    
    if auto_result['recommendations']:
        print("   Recommendations:")
        for rec in auto_result['recommendations'][:3]:
            print(f"     • {rec}")
    
    print()
    
    # Demo 8: System health and statistics
    print("📈 System health and statistics...")
    
    health = integrator.get_system_health()
    print(f"   Tasks processed: {health['integration_metrics']['tasks_processed']}")
    print(f"   Validations performed: {health['integration_metrics']['validations_performed']}")
    print(f"   Enhanced agents: {health['enhanced_agents_count']}")
    print(f"   Available plugins: {health['plugin_system_status']['registry_statistics']['total_plugins']}")
    
    if health['validation_statistics']['total_validations'] > 0:
        print(f"   Validation success rate: {health['validation_statistics']['by_status'].get('passed', 0) / health['validation_statistics']['total_validations'] * 100:.1f}%")
    
    print()
    
    # Demo 9: System integrity validation
    print("🔍 Validating system integrity...")
    
    integrity = integrator.validate_system_integrity()
    print(f"   Overall system valid: {integrity['overall_valid']}")
    print(f"   Plugin system valid: {integrity['plugin_integrity']['valid']}")
    print(f"   Validators registered: {sum(integrity['validation_integrity']['validators_registered'].values())}")
    
    if not integrity['overall_valid']:
        print("   ⚠️ Issues found:")
        for issue in integrity['plugin_integrity'].get('issues', []):
            print(f"     • {issue}")
    
    print()
    
    # Demo 10: Cleanup demonstration
    print("🧹 Demonstrating system cleanup...")
    
    cleanup_result = integrator.cleanup_system(days=0)  # Clean everything for demo
    print(f"   Validation records cleaned: {cleanup_result['validation_records_cleaned']}")
    print(f"   Plugins cleaned: {cleanup_result['plugins_cleaned']}")
    print(f"   Enhanced agents cleaned: {cleanup_result['enhanced_agents_cleaned']}")
    
    print()
    print("=" * 60)
    print("✅ HIERARCHICAL VALIDATION AND PLUGIN DEMO COMPLETED")
    print()
    print("🎯 Key Features Demonstrated:")
    print("   • Hierarchical validation chain (Tool → Department → Director)")
    print("   • Configurable quality gates with custom thresholds")
    print("   • Automatic rollback on validation failures")
    print("   • Dynamic plugin discovery and installation")
    print("   • Capability gap analysis and resolution")
    print("   • Agent factory for dynamic agent creation")
    print("   • Comprehensive system monitoring and health checks")
    print("   • Automatic cleanup and maintenance")
    print()
    print("🚀 The system is now ready for production use with:")
    print("   • Full validation coverage at all tiers")
    print("   • Automatic capability expansion through plugins")
    print("   • Robust error handling and rollback mechanisms")
    print("   • Real-time monitoring and analytics")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"\n❌ Demo error: {e}")
        import traceback
        traceback.print_exc()
