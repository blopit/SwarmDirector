# Examples Directory

## Purpose
Contains demonstration applications, usage examples, and sample implementations for the SwarmDirector hierarchical AI agent management system. This directory provides practical examples of how to use the system, integrate with external services, and implement custom workflows for various use cases.

## Structure
```
examples/
├── demo_app.py                  # Interactive demo application
├── demo_orchestration.py       # Agent orchestration demonstration
├── demo_specialized_agents.py  # Specialized agent examples
├── phase2_demo.py              # Phase 2 feature demonstrations
├── sample_data/                # Sample data for demonstrations
│   ├── sample_agents.json      # Sample agent configurations
│   ├── sample_tasks.json       # Sample task definitions
│   ├── sample_workflows.json   # Sample workflow configurations
│   └── sample_conversations.json # Sample conversation data
├── integrations/               # Integration examples
│   ├── autogen_integration.py  # AutoGen framework integration
│   ├── email_integration.py    # Email service integration
│   ├── slack_integration.py    # Slack bot integration
│   └── webhook_integration.py  # Webhook handling examples
├── workflows/                  # Workflow examples
│   ├── content_creation.py     # Content creation workflow
│   ├── customer_support.py     # Customer support workflow
│   ├── research_workflow.py    # Research and analysis workflow
│   └── approval_workflow.py    # Multi-stage approval workflow
└── tutorials/                  # Step-by-step tutorials
    ├── getting_started.py      # Basic usage tutorial
    ├── custom_agents.py        # Creating custom agents
    ├── advanced_routing.py     # Advanced task routing
    └── monitoring_setup.py     # Monitoring and analytics setup
```

## Guidelines

### 1. Organization
- **Self-Contained Examples**: Each example should be complete and runnable independently
- **Progressive Complexity**: Organize examples from simple to advanced use cases
- **Clear Documentation**: Include comprehensive documentation and comments
- **Sample Data**: Provide realistic sample data for demonstrations
- **Error Handling**: Include proper error handling and edge case management

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names indicating example purpose
- **Consistent Format**: Use snake_case for Python files, descriptive directory names
- **Version Indicators**: Include version or phase information where relevant
- **Category Prefixes**: Use prefixes to indicate example category (demo_, tutorial_, etc.)
- **File Extensions**: Use appropriate extensions (.py, .json, .md)

### 3. Implementation
- **Complete Examples**: Provide working, executable examples
- **Configuration**: Support configuration through command-line arguments
- **Logging**: Include appropriate logging for demonstration purposes
- **Documentation**: Include inline documentation and usage instructions
- **Best Practices**: Demonstrate SwarmDirector best practices and patterns

### 4. Documentation
- **Usage Instructions**: Provide clear instructions for running examples
- **Prerequisites**: Document required dependencies and setup steps
- **Expected Output**: Describe expected behavior and output
- **Customization**: Explain how to customize examples for different use cases

## Best Practices

### 1. Error Handling
- **Graceful Failures**: Handle errors gracefully with informative messages
- **Validation**: Validate inputs and configuration before execution
- **Recovery Examples**: Show how to handle and recover from failures
- **Edge Cases**: Include examples of handling edge cases and unusual scenarios
- **User Feedback**: Provide clear feedback about what's happening during execution

### 2. Security
- **Safe Defaults**: Use safe default configurations in examples
- **Input Validation**: Validate all user inputs and external data
- **Credential Handling**: Show secure credential handling practices
- **Permission Checks**: Include appropriate permission and access checks
- **Data Sanitization**: Demonstrate proper data sanitization techniques

### 3. Performance
- **Efficient Examples**: Use efficient algorithms and patterns
- **Resource Management**: Demonstrate proper resource management
- **Scalability**: Show how examples can scale with larger datasets
- **Monitoring**: Include performance monitoring and metrics
- **Optimization**: Demonstrate optimization techniques where relevant

### 4. Testing
- **Example Testing**: Include tests for complex examples
- **Mock Data**: Use mock data for external service demonstrations
- **Validation**: Validate example outputs and behavior
- **Error Scenarios**: Test error handling and edge cases
- **Documentation Testing**: Ensure documentation matches actual behavior

### 5. Documentation
- **Complete Documentation**: Provide comprehensive documentation for each example
- **Usage Examples**: Include multiple usage scenarios
- **Troubleshooting**: Document common issues and solutions
- **Integration Guides**: Explain how to integrate examples into real applications

## Example

### Complete Demo Application

```python
#!/usr/bin/env python3
"""
SwarmDirector Interactive Demo Application

This demo showcases the complete SwarmDirector workflow including:
- Agent creation and registration
- Task submission and routing
- Real-time monitoring and feedback
- Error handling and recovery

Usage:
    python demo_app.py [options]

Examples:
    # Basic demo
    python demo_app.py

    # Demo with custom configuration
    python demo_app.py --config custom_config.json

    # Interactive mode
    python demo_app.py --interactive

    # Batch processing demo
    python demo_app.py --batch sample_data/sample_tasks.json

Requirements:
    - SwarmDirector installed and configured
    - Development database initialized
    - Optional: Email server for email demonstrations

Author: SwarmDirector Team
Version: 2.0.0
Last Updated: 2023-12-01
"""

import argparse
import asyncio
import json
import logging
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add src to path for development
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.agents.director import DirectorAgent
from swarm_director.agents.email_agent import EmailAgent
from swarm_director.agents.communications_dept import CommunicationsDept

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class SwarmDirectorDemo:
    """
    Interactive demonstration of SwarmDirector capabilities
    
    This class provides a comprehensive demo of the SwarmDirector system,
    showcasing agent creation, task routing, and workflow execution.
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.app = None
        self.director = None
        self.agents = {}
        self.tasks = []
        self.demo_stats = {
            'tasks_created': 0,
            'tasks_completed': 0,
            'tasks_failed': 0,
            'agents_created': 0,
            'start_time': datetime.utcnow()
        }
    
    def run_demo(self) -> bool:
        """
        Run the complete SwarmDirector demonstration
        
        Returns:
            bool: True if demo completed successfully
        """
        try:
            logger.info("🚀 Starting SwarmDirector Demo")
            
            # Initialize application
            if not self._initialize_application():
                return False
            
            # Setup agents
            if not self._setup_agents():
                return False
            
            # Run demonstration scenarios
            if self.config.get('interactive', False):
                return self._run_interactive_demo()
            elif self.config.get('batch_file'):
                return self._run_batch_demo()
            else:
                return self._run_standard_demo()
                
        except KeyboardInterrupt:
            logger.info("🛑 Demo interrupted by user")
            return True
        except Exception as e:
            logger.error(f"❌ Demo failed: {e}")
            return False
        finally:
            self._print_demo_summary()
    
    def _initialize_application(self) -> bool:
        """Initialize Flask application and database"""
        logger.info("🔧 Initializing application")
        
        try:
            self.app = create_app('development')
            
            with self.app.app_context():
                # Ensure database is initialized
                db.create_all()
                logger.info("✅ Database initialized")
                
            return True
            
        except Exception as e:
            logger.error(f"❌ Application initialization failed: {e}")
            return False
    
    def _setup_agents(self) -> bool:
        """Setup demonstration agents"""
        logger.info("🤖 Setting up demonstration agents")
        
        with self.app.app_context():
            try:
                # Create director agent
                director_db = self._create_or_get_agent(
                    name="DemoDirector",
                    description="Director agent for demonstration",
                    agent_type=AgentType.SUPERVISOR,
                    capabilities={
                        "routing": True,
                        "department_management": True,
                        "intent_classification": True,
                        "demo_mode": True
                    }
                )
                
                self.director = DirectorAgent(director_db)
                self.agents['director'] = self.director
                logger.info("✅ Director agent created")
                
                # Create email agent
                email_db = self._create_or_get_agent(
                    name="DemoEmailAgent",
                    description="Email agent for demonstration",
                    agent_type=AgentType.WORKER,
                    capabilities={
                        "email_handling": True,
                        "smtp_integration": True,
                        "template_processing": True,
                        "demo_mode": True
                    }
                )
                
                email_agent = EmailAgent(email_db)
                self.agents['email'] = email_agent
                self.director.register_department(email_db)
                logger.info("✅ Email agent created and registered")
                
                # Create communications department
                comm_db = self._create_or_get_agent(
                    name="DemoCommunicationsDept",
                    description="Communications department for demonstration",
                    agent_type=AgentType.WORKER,
                    capabilities={
                        "content_creation": True,
                        "review_workflows": True,
                        "parallel_processing": True,
                        "demo_mode": True
                    }
                )
                
                comm_dept = CommunicationsDept(comm_db)
                self.agents['communications'] = comm_dept
                self.director.register_department(comm_db)
                logger.info("✅ Communications department created and registered")
                
                return True
                
            except Exception as e:
                logger.error(f"❌ Agent setup failed: {e}")
                return False
    
    def _run_standard_demo(self) -> bool:
        """Run standard demonstration scenarios"""
        logger.info("🎭 Running standard demonstration scenarios")
        
        scenarios = [
            self._demo_email_workflow,
            self._demo_content_creation,
            self._demo_error_handling,
            self._demo_concurrent_processing
        ]
        
        for i, scenario in enumerate(scenarios, 1):
            logger.info(f"📋 Running scenario {i}/{len(scenarios)}: {scenario.__name__}")
            
            try:
                if not scenario():
                    logger.warning(f"⚠️  Scenario {scenario.__name__} failed")
                else:
                    logger.info(f"✅ Scenario {scenario.__name__} completed")
                
                # Pause between scenarios
                if i < len(scenarios):
                    time.sleep(2)
                    
            except Exception as e:
                logger.error(f"❌ Scenario {scenario.__name__} error: {e}")
        
        return True
    
    def _demo_email_workflow(self) -> bool:
        """Demonstrate email workflow"""
        logger.info("📧 Demonstrating email workflow")
        
        with self.app.app_context():
            # Create email task
            task = Task(
                title="Demo Email Task",
                description="Send a demonstration email",
                task_type="email",
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={
                    "recipient": "demo@example.com",
                    "subject": "SwarmDirector Demo Email",
                    "body": "This is a demonstration email from SwarmDirector!",
                    "template": "demo_template",
                    "variables": {
                        "user_name": "Demo User",
                        "demo_date": datetime.utcnow().strftime("%Y-%m-%d")
                    }
                }
            )
            task.save()
            self.tasks.append(task)
            self.demo_stats['tasks_created'] += 1
            
            # Execute task through director
            try:
                result = self.director.execute_task(task)
                
                if result.get('status') == 'completed':
                    self.demo_stats['tasks_completed'] += 1
                    logger.info(f"✅ Email task completed: {result}")
                    return True
                else:
                    self.demo_stats['tasks_failed'] += 1
                    logger.warning(f"⚠️  Email task failed: {result}")
                    return False
                    
            except Exception as e:
                self.demo_stats['tasks_failed'] += 1
                logger.error(f"❌ Email workflow error: {e}")
                return False
    
    def _demo_content_creation(self) -> bool:
        """Demonstrate content creation workflow"""
        logger.info("📝 Demonstrating content creation workflow")
        
        with self.app.app_context():
            # Create content creation task
            task = Task(
                title="Demo Content Creation",
                description="Create demonstration content with review",
                task_type="content_creation",
                priority=TaskPriority.HIGH,
                status=TaskStatus.PENDING,
                input_data={
                    "content_type": "blog_post",
                    "topic": "SwarmDirector AI Agent Management",
                    "target_audience": "developers",
                    "word_count": 500,
                    "tone": "professional",
                    "review_required": True,
                    "approval_workflow": True
                }
            )
            task.save()
            self.tasks.append(task)
            self.demo_stats['tasks_created'] += 1
            
            # Execute task
            try:
                result = self.director.execute_task(task)
                
                if result.get('status') == 'completed':
                    self.demo_stats['tasks_completed'] += 1
                    logger.info(f"✅ Content creation completed: {result}")
                    
                    # Show generated content summary
                    if 'content_summary' in result:
                        logger.info(f"📄 Generated content: {result['content_summary']}")
                    
                    return True
                else:
                    self.demo_stats['tasks_failed'] += 1
                    logger.warning(f"⚠️  Content creation failed: {result}")
                    return False
                    
            except Exception as e:
                self.demo_stats['tasks_failed'] += 1
                logger.error(f"❌ Content creation error: {e}")
                return False
    
    def _demo_error_handling(self) -> bool:
        """Demonstrate error handling and recovery"""
        logger.info("🚨 Demonstrating error handling and recovery")
        
        with self.app.app_context():
            # Create task with invalid data to trigger error handling
            task = Task(
                title="Demo Error Handling",
                description="Task designed to test error handling",
                task_type="invalid_type",  # Invalid task type
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={
                    "invalid_field": "This should cause an error",
                    "missing_required_field": None
                }
            )
            task.save()
            self.tasks.append(task)
            self.demo_stats['tasks_created'] += 1
            
            # Execute task and expect graceful error handling
            try:
                result = self.director.execute_task(task)
                
                # Should fail gracefully
                if result.get('status') == 'failed':
                    self.demo_stats['tasks_failed'] += 1
                    logger.info(f"✅ Error handled gracefully: {result.get('error', 'Unknown error')}")
                    return True
                else:
                    logger.warning(f"⚠️  Expected failure but got: {result}")
                    return False
                    
            except Exception as e:
                # Even exceptions should be handled gracefully
                self.demo_stats['tasks_failed'] += 1
                logger.info(f"✅ Exception handled gracefully: {e}")
                return True
    
    def _demo_concurrent_processing(self) -> bool:
        """Demonstrate concurrent task processing"""
        logger.info("⚡ Demonstrating concurrent task processing")
        
        import threading
        import concurrent.futures
        
        with self.app.app_context():
            # Create multiple tasks for concurrent processing
            tasks = []
            for i in range(3):
                task = Task(
                    title=f"Concurrent Demo Task {i+1}",
                    description=f"Concurrent processing demonstration task {i+1}",
                    task_type="communication",
                    priority=TaskPriority.NORMAL,
                    status=TaskStatus.PENDING,
                    input_data={
                        "task_number": i+1,
                        "concurrent": True,
                        "processing_time": 2  # Simulate 2 second processing
                    }
                )
                task.save()
                tasks.append(task)
                self.tasks.append(task)
                self.demo_stats['tasks_created'] += 1
            
            # Execute tasks concurrently
            start_time = time.time()
            results = []
            
            def execute_task(task):
                with self.app.app_context():
                    return self.director.execute_task(task)
            
            with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
                future_to_task = {executor.submit(execute_task, task): task for task in tasks}
                
                for future in concurrent.futures.as_completed(future_to_task):
                    task = future_to_task[future]
                    try:
                        result = future.result()
                        results.append(result)
                        
                        if result.get('status') == 'completed':
                            self.demo_stats['tasks_completed'] += 1
                        else:
                            self.demo_stats['tasks_failed'] += 1
                            
                    except Exception as e:
                        logger.error(f"❌ Concurrent task {task.title} failed: {e}")
                        self.demo_stats['tasks_failed'] += 1
            
            end_time = time.time()
            total_time = end_time - start_time
            
            logger.info(f"✅ Processed {len(tasks)} tasks concurrently in {total_time:.2f} seconds")
            logger.info(f"📊 Success rate: {len([r for r in results if r.get('status') == 'completed'])}/{len(results)}")
            
            return len(results) == len(tasks)
    
    def _run_interactive_demo(self) -> bool:
        """Run interactive demonstration"""
        logger.info("🎮 Starting interactive demonstration mode")
        
        print("\n" + "="*60)
        print("🎭 SwarmDirector Interactive Demo")
        print("="*60)
        print("\nAvailable commands:")
        print("  1. Create email task")
        print("  2. Create content task")
        print("  3. Show agent status")
        print("  4. Show task history")
        print("  5. Show demo statistics")
        print("  q. Quit")
        print("\n")
        
        while True:
            try:
                choice = input("Enter command (1-5, q): ").strip().lower()
                
                if choice == 'q':
                    break
                elif choice == '1':
                    self._interactive_create_email_task()
                elif choice == '2':
                    self._interactive_create_content_task()
                elif choice == '3':
                    self._show_agent_status()
                elif choice == '4':
                    self._show_task_history()
                elif choice == '5':
                    self._show_demo_statistics()
                else:
                    print("❌ Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"❌ Interactive demo error: {e}")
        
        return True
    
    def _interactive_create_email_task(self):
        """Interactive email task creation"""
        print("\n📧 Creating Email Task")
        print("-" * 30)
        
        recipient = input("Recipient email: ").strip()
        subject = input("Email subject: ").strip()
        body = input("Email body: ").strip()
        
        if not all([recipient, subject, body]):
            print("❌ All fields are required")
            return
        
        with self.app.app_context():
            task = Task(
                title=f"Interactive Email: {subject}",
                description="Interactive email task",
                task_type="email",
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={
                    "recipient": recipient,
                    "subject": subject,
                    "body": body
                }
            )
            task.save()
            self.tasks.append(task)
            self.demo_stats['tasks_created'] += 1
            
            print(f"📝 Task created with ID: {task.id}")
            
            # Execute task
            try:
                result = self.director.execute_task(task)
                
                if result.get('status') == 'completed':
                    self.demo_stats['tasks_completed'] += 1
                    print(f"✅ Email sent successfully!")
                else:
                    self.demo_stats['tasks_failed'] += 1
                    print(f"❌ Email failed: {result.get('error', 'Unknown error')}")
                    
            except Exception as e:
                self.demo_stats['tasks_failed'] += 1
                print(f"❌ Task execution failed: {e}")
    
    def _create_or_get_agent(self, name: str, description: str, agent_type: AgentType, capabilities: Dict) -> Agent:
        """Create or get existing agent"""
        existing_agent = Agent.query.filter_by(name=name).first()
        
        if existing_agent:
            logger.info(f"🔄 Using existing agent: {name}")
            return existing_agent
        
        agent = Agent(
            name=name,
            description=description,
            agent_type=agent_type,
            status=AgentStatus.IDLE,
            capabilities=capabilities
        )
        agent.save()
        self.demo_stats['agents_created'] += 1
        
        logger.info(f"✨ Created new agent: {name}")
        return agent
    
    def _print_demo_summary(self):
        """Print demonstration summary"""
        duration = datetime.utcnow() - self.demo_stats['start_time']
        
        print("\n" + "="*60)
        print("📊 SwarmDirector Demo Summary")
        print("="*60)
        print(f"⏱️  Duration: {duration}")
        print(f"🤖 Agents created: {self.demo_stats['agents_created']}")
        print(f"📝 Tasks created: {self.demo_stats['tasks_created']}")
        print(f"✅ Tasks completed: {self.demo_stats['tasks_completed']}")
        print(f"❌ Tasks failed: {self.demo_stats['tasks_failed']}")
        
        if self.demo_stats['tasks_created'] > 0:
            success_rate = (self.demo_stats['tasks_completed'] / self.demo_stats['tasks_created']) * 100
            print(f"📈 Success rate: {success_rate:.1f}%")
        
        print("\n🎉 Thank you for trying SwarmDirector!")
        print("📚 For more information, visit: https://github.com/blopit/SwarmDirector")
        print("="*60)

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="SwarmDirector Interactive Demo",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        '--config',
        help='Configuration file path'
    )
    
    parser.add_argument(
        '--interactive',
        action='store_true',
        help='Run in interactive mode'
    )
    
    parser.add_argument(
        '--batch',
        dest='batch_file',
        help='Run batch processing with task file'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Load configuration
    config = {}
    if args.config:
        with open(args.config, 'r') as f:
            config = json.load(f)
    
    config.update({
        'interactive': args.interactive,
        'batch_file': args.batch_file
    })
    
    # Run demo
    demo = SwarmDirectorDemo(config)
    success = demo.run_demo()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## Related Documentation
- [Getting Started Guide](../docs/development/getting_started.md) - Basic usage examples
- [API Documentation](../docs/api/README.md) - API usage examples
- [Integration Guide](../docs/architecture/overview.md) - Integration patterns
- [Workflow Patterns](../docs/architecture/workflow_patterns.md) - Common workflow examples
- [Deployment Examples](../docs/deployment/local_development.md) - Deployment scenarios
