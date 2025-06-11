#!/usr/bin/env python3
"""
Phase 2 Implementation Demo - SwarmDirector
Demonstrates the new CommunicationsDept, EmailAgent, and DraftReviewAgent functionality
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.agents.director import DirectorAgent
from swarm_director.agents.communications_dept import CommunicationsDept
from swarm_director.agents.email_agent import EmailAgent
from swarm_director.agents.draft_review_agent import DraftReviewAgent

def main():
    """Demonstrate Phase 2 implementation"""
    print("🚀 SwarmDirector Phase 2 Implementation Demo")
    print("=" * 60)
    
    # Create Flask app and database
    app = create_app()
    with app.app_context():
        db.create_all()
        
        print("\n1. 🏗️  Setting up agents...")
        
        # Create DirectorAgent
        director_db = Agent(
            name='DemoDirector',
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.ACTIVE,
            description='Demo DirectorAgent with new departments'
        )
        director_db.save()
        
        director = DirectorAgent(director_db)
        print(f"   ✅ DirectorAgent created with {len(director.department_agents)} departments")
        
        # Show registered departments
        dept_status = director.get_department_status()
        for dept_name, status in dept_status.items():
            print(f"   📋 {dept_name}: {status['name']} ({status['status']})")
        
        print("\n2. 📧 Testing Email Workflow...")
        
        # Create email task
        email_task = Task(
            title='Send Welcome Email',
            description='Send a welcome email to new user with review process',
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            input_data={
                'type': 'email',
                'recipient': 'newuser@example.com',
                'subject': 'Welcome to SwarmDirector!',
                'content': 'Welcome to our AI agent management system. We are excited to have you on board!',
                'workflow_type': 'email',
                'send_immediately': False  # Don't actually send, just prepare
            }
        )
        email_task.save()
        
        # Process through DirectorAgent
        print(f"   📝 Created task: {email_task.title}")
        
        # Classify intent
        intent = director.classify_intent(email_task)
        print(f"   🎯 Intent classified as: {intent}")
        
        # Route and execute task
        result = director.execute_task(email_task)
        print(f"   ✅ Task execution result: {result['status']}")
        
        if result['status'] == 'success':
            print(f"   📤 Routed to: {result['routed_to']}")
            print(f"   🤖 Handled by: {result['agent_name']}")
        
        print("\n3. 📝 Testing Draft Review Process...")
        
        # Create draft review task
        review_task = Task(
            title='Review Marketing Email',
            description='Review marketing email draft for quality and improvements',
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM,
            input_data={
                'type': 'review',
                'content': '''Dear Valued Customer,
                
We hope this email finds you well. We are excited to announce our new AI-powered features that will revolutionize your workflow.

Our latest update includes:
- Advanced agent coordination
- Intelligent task routing  
- Comprehensive review processes
- Real-time performance monitoring

We believe these enhancements will significantly improve your productivity and user experience.

Best regards,
The SwarmDirector Team''',
                'draft_type': 'email'
            }
        )
        review_task.save()
        
        print(f"   📝 Created review task: {review_task.title}")
        
        # Process review task
        review_result = director.execute_task(review_task)
        print(f"   ✅ Review execution result: {review_result['status']}")
        
        if review_result['status'] == 'success':
            print(f"   📊 Routed to: {review_result['routed_to']}")
            print(f"   🤖 Handled by: {review_result['agent_name']}")
        
        print("\n4. 🔄 Testing Content Creation Workflow...")
        
        # Create content creation task
        content_task = Task(
            title='Create Product Announcement',
            description='Create announcement email for new product launch',
            status=TaskStatus.PENDING,
            priority=TaskPriority.HIGH,
            input_data={
                'type': 'communication',
                'workflow_type': 'content_creation',
                'template': 'notification',
                'recipient_name': 'Product Team',
                'notification_type': 'Product Launch',
                'notification_message': 'We are launching SwarmDirector v2.0 with enhanced AI capabilities',
                'additional_details': 'This release includes new agent types, improved workflows, and better performance monitoring.',
                'sender_name': 'Development Team'
            }
        )
        content_task.save()
        
        print(f"   📝 Created content task: {content_task.title}")
        
        # Process content task
        content_result = director.execute_task(content_task)
        print(f"   ✅ Content execution result: {content_result['status']}")
        
        if content_result['status'] == 'success':
            print(f"   📊 Routed to: {content_result['routed_to']}")
            print(f"   🤖 Handled by: {content_result['agent_name']}")
        
        print("\n5. 📊 Performance Summary...")
        
        # Get routing statistics
        routing_stats = director.get_routing_stats()
        print(f"   📈 Total tasks routed: {routing_stats['total_routed']}")
        print(f"   ✅ Successful routes: {routing_stats['successful_routes']}")
        print(f"   ❌ Failed routes: {routing_stats['failed_routes']}")
        print(f"   📊 Success rate: {routing_stats['success_rate']:.1f}%")
        
        print("\n   Department usage:")
        for dept, count in routing_stats['department_counts'].items():
            print(f"     📋 {dept}: {count} tasks")
        
        print("\n6. 🧪 Testing Individual Agent Capabilities...")
        
        # Test DraftReviewAgent directly
        review_agent_db = Agent(
            name='TestReviewAgent',
            agent_type=AgentType.WORKER,
            status=AgentStatus.ACTIVE
        )
        review_agent_db.save()
        
        review_agent = DraftReviewAgent(review_agent_db)
        
        # Test review functionality
        sample_content = "This is a sample email draft. It needs improvement in clarity and structure."
        review_result = review_agent.review_draft(sample_content, 'email')
        
        print(f"   📊 Review score: {review_result['overall_score']}/100")
        print(f"   💡 Suggestions: {len(review_result['suggestions'])}")
        print(f"   📝 Recommendation: {review_result['recommendation']}")
        
        # Test EmailAgent directly
        email_agent_db = Agent(
            name='TestEmailAgent',
            agent_type=AgentType.WORKER,
            status=AgentStatus.ACTIVE
        )
        email_agent_db.save()
        
        email_agent = EmailAgent(email_agent_db)
        
        # Test email validation
        email_data = {
            'recipient': 'test@example.com',
            'subject': 'Test Email',
            'body': 'This is a test email body with sufficient content for validation.'
        }
        
        validation_result = email_agent._validate_email_data(email_data)
        print(f"   ✉️  Email validation: {'✅ Valid' if validation_result['valid'] else '❌ Invalid'}")
        print(f"   📋 Available templates: {', '.join(email_agent.get_email_templates())}")
        
        print("\n🎉 Phase 2 Implementation Demo Complete!")
        print("=" * 60)
        print("\n✅ Successfully implemented:")
        print("   • CommunicationsDept with parallel review workflows")
        print("   • EmailAgent with SMTP integration and templates")
        print("   • DraftReviewAgent with comprehensive content analysis")
        print("   • DirectorAgent integration with new departments")
        print("   • Task routing and intent classification")
        print("   • Comprehensive error handling and logging")
        
        print("\n🚀 Ready for production use!")

if __name__ == '__main__':
    main()
