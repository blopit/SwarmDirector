#!/usr/bin/env python3
"""
Validation and Plugin System CLI

Command-line interface for managing the hierarchical validation system
and plugin architecture.
"""

import sys
import os
import asyncio
import argparse
import json
import yaml
from datetime import datetime
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.validation_plugin_integration import ValidationPluginIntegrator
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.models.agent import Agent, AgentType, AgentStatus


class ValidationCLI:
    """Command-line interface for validation and plugin system"""
    
    def __init__(self):
        self.integrator = None
        self.config_path = None
    
    def load_config(self, config_path: str = None):
        """Load configuration from file"""
        if config_path:
            self.config_path = config_path
        else:
            # Try default locations
            default_paths = [
                'config/validation_plugin_config.yaml',
                '../config/validation_plugin_config.yaml',
                os.path.expanduser('~/.swarm_director/config.yaml')
            ]
            
            for path in default_paths:
                if os.path.exists(path):
                    self.config_path = path
                    break
        
        if self.config_path and os.path.exists(self.config_path):
            with open(self.config_path, 'r') as f:
                config = yaml.safe_load(f)
            print(f"✅ Loaded configuration from {self.config_path}")
            return config
        else:
            print("⚠️ No configuration file found, using defaults")
            return {}
    
    def initialize_system(self, config_path: str = None):
        """Initialize the validation and plugin system"""
        config = self.load_config(config_path)
        
        # Extract plugin config
        plugin_config = config.get('plugins', {})
        
        self.integrator = ValidationPluginIntegrator({
            'plugin_config': plugin_config
        })
        
        print("✅ Validation and plugin system initialized")
    
    async def validate_task(self, task_file: str, agents_file: str = None):
        """Validate a task using the hierarchical validation system"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        # Load task from file
        with open(task_file, 'r') as f:
            task_data = json.load(f)
        
        task = Task(
            title=task_data['title'],
            description=task_data['description'],
            status=TaskStatus.PENDING,
            priority=TaskPriority(task_data.get('priority', 'medium')),
            input_data=task_data.get('input_data', {})
        )
        
        print(f"📋 Validating task: {task.title}")
        
        # Load or create agents
        if agents_file and os.path.exists(agents_file):
            with open(agents_file, 'r') as f:
                agents_data = json.load(f)
            
            tool_agent = Agent(
                name=agents_data['tool']['name'],
                description=agents_data['tool']['description'],
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities=agents_data['tool'].get('capabilities', [])
            )
            
            dept_agent = Agent(
                name=agents_data['department']['name'],
                description=agents_data['department']['description'],
                agent_type=AgentType.SUPERVISOR,
                status=AgentStatus.IDLE,
                capabilities=agents_data['department'].get('capabilities', [])
            ) if 'department' in agents_data else None
            
            director_agent = Agent(
                name=agents_data['director']['name'],
                description=agents_data['director']['description'],
                agent_type=AgentType.SUPERVISOR,
                status=AgentStatus.IDLE,
                capabilities=agents_data['director'].get('capabilities', [])
            ) if 'director' in agents_data else None
        else:
            # Create default agents
            tool_agent = Agent(
                name="DefaultToolAgent",
                description="Default tool agent",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities=["basic_processing"]
            )
            dept_agent = None
            director_agent = None
        
        # Process task with validation
        result = await self.integrator.process_task_with_full_validation(
            task=task,
            tool_agent=tool_agent,
            dept_agent=dept_agent,
            director_agent=director_agent
        )
        
        # Display results
        print("\n📊 VALIDATION RESULTS:")
        print(f"   Success: {'✅' if result['success'] else '❌'} {result['success']}")
        print(f"   Processing time: {result['processing_time_ms']}ms")
        
        if result['validation_results']:
            print("   Validation by tier:")
            for validation in result['validation_results']:
                status_icon = "✅" if validation['status'] == 'passed' else "❌"
                print(f"     {status_icon} {validation['tier'].title()}: {validation['status']} (score: {validation['score']:.2f})")
        
        if not result['success']:
            print(f"   ❌ Failure tier: {result.get('failure_tier', 'unknown')}")
            print(f"   📝 Reason: {result.get('failure_reason', 'unknown')}")
    
    def list_plugins(self, status: str = None):
        """List available plugins"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        plugins = self.integrator.plugin_manager.discover_plugins()
        
        if status:
            plugins = [p for p in plugins if p.status.value == status]
        
        print(f"\n🔌 PLUGINS ({len(plugins)} found):")
        for plugin in plugins:
            status_icon = "✅" if plugin.status.value == "installed" else "📦"
            print(f"   {status_icon} {plugin.name} v{plugin.version}")
            print(f"      {plugin.description}")
            print(f"      Type: {plugin.plugin_type.value}, Status: {plugin.status.value}")
            if plugin.capabilities:
                caps = [cap.name for cap in plugin.capabilities]
                print(f"      Capabilities: {', '.join(caps)}")
            print()
    
    async def install_plugin(self, plugin_name: str):
        """Install a plugin"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        print(f"🔌 Installing plugin: {plugin_name}")
        
        success = self.integrator.plugin_manager.install_plugin(plugin_name)
        
        if success:
            print(f"✅ Plugin {plugin_name} installed successfully")
        else:
            print(f"❌ Failed to install plugin {plugin_name}")
    
    def system_status(self):
        """Show system status"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        health = self.integrator.get_system_health()
        
        print("\n🏥 SYSTEM HEALTH:")
        print(f"   Tasks processed: {health['integration_metrics']['tasks_processed']}")
        print(f"   Validations performed: {health['integration_metrics']['validations_performed']}")
        print(f"   Enhanced agents: {health['enhanced_agents_count']}")
        print(f"   Available plugins: {health['plugin_system_status']['registry_statistics']['total_plugins']}")
        
        if health['validation_statistics']['total_validations'] > 0:
            passed = health['validation_statistics']['by_status'].get('passed', 0)
            total = health['validation_statistics']['total_validations']
            success_rate = passed / total * 100
            print(f"   Validation success rate: {success_rate:.1f}%")
        
        print(f"   Auto-install enabled: {health['plugin_system_status']['auto_install_enabled']}")
        print(f"   Auto-discovery enabled: {health['plugin_system_status']['auto_discovery_enabled']}")
    
    async def suggest_plugins(self, task_file: str):
        """Suggest plugins for a task"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        # Load task from file
        with open(task_file, 'r') as f:
            task_data = json.load(f)
        
        task = Task(
            title=task_data['title'],
            description=task_data['description'],
            input_data=task_data.get('input_data', {})
        )
        
        suggestions = self.integrator.get_plugin_suggestions(task)
        
        print(f"\n💡 PLUGIN SUGGESTIONS for '{task.title}':")
        if suggestions:
            for suggestion in suggestions[:5]:  # Show top 5
                print(f"   🔌 {suggestion['plugin_name']}")
                print(f"      {suggestion['description']}")
                print(f"      Relevance: {suggestion['relevance_score']:.2f}")
                print(f"      Status: {suggestion['status']}")
                print(f"      Capabilities: {', '.join(suggestion['capabilities'])}")
                print()
        else:
            print("   No plugin suggestions found for this task.")
    
    def cleanup_system(self, days: int = 30):
        """Clean up old data"""
        if not self.integrator:
            print("❌ System not initialized. Run 'init' command first.")
            return
        
        print(f"🧹 Cleaning up data older than {days} days...")
        
        result = self.integrator.cleanup_system(days)
        
        print(f"✅ Cleanup completed:")
        print(f"   Validation records cleaned: {result['validation_records_cleaned']}")
        print(f"   Plugins cleaned: {result['plugins_cleaned']}")
        print(f"   Enhanced agents cleaned: {result['enhanced_agents_cleaned']}")


def main():
    """Main CLI function"""
    parser = argparse.ArgumentParser(description="SwarmDirector Validation & Plugin CLI")
    parser.add_argument('--config', '-c', help='Configuration file path')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Init command
    init_parser = subparsers.add_parser('init', help='Initialize the system')
    init_parser.add_argument('--config', '-c', help='Configuration file path')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate a task')
    validate_parser.add_argument('task_file', help='Task JSON file')
    validate_parser.add_argument('--agents', '-a', help='Agents JSON file')
    
    # List plugins command
    list_parser = subparsers.add_parser('list-plugins', help='List plugins')
    list_parser.add_argument('--status', '-s', help='Filter by status')
    
    # Install plugin command
    install_parser = subparsers.add_parser('install-plugin', help='Install a plugin')
    install_parser.add_argument('plugin_name', help='Plugin name to install')
    
    # Status command
    subparsers.add_parser('status', help='Show system status')
    
    # Suggest plugins command
    suggest_parser = subparsers.add_parser('suggest-plugins', help='Suggest plugins for a task')
    suggest_parser.add_argument('task_file', help='Task JSON file')
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser('cleanup', help='Clean up old data')
    cleanup_parser.add_argument('--days', '-d', type=int, default=30, help='Days to keep (default: 30)')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    cli = ValidationCLI()
    
    try:
        if args.command == 'init':
            cli.initialize_system(args.config)
        
        elif args.command == 'validate':
            cli.initialize_system(args.config)
            asyncio.run(cli.validate_task(args.task_file, args.agents))
        
        elif args.command == 'list-plugins':
            cli.initialize_system(args.config)
            cli.list_plugins(args.status)
        
        elif args.command == 'install-plugin':
            cli.initialize_system(args.config)
            asyncio.run(cli.install_plugin(args.plugin_name))
        
        elif args.command == 'status':
            cli.initialize_system(args.config)
            cli.system_status()
        
        elif args.command == 'suggest-plugins':
            cli.initialize_system(args.config)
            asyncio.run(cli.suggest_plugins(args.task_file))
        
        elif args.command == 'cleanup':
            cli.initialize_system(args.config)
            cli.cleanup_system(args.days)
        
    except KeyboardInterrupt:
        print("\n👋 Operation cancelled by user")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        if args.config:  # Show more details in debug mode
            import traceback
            traceback.print_exc()


if __name__ == "__main__":
    main()
