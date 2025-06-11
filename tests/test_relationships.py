#!/usr/bin/env python3
"""
Test script to verify database relationships work correctly
"""

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskType, TaskStatus
from swarm_director.models.conversation import Conversation
from swarm_director.models.agent_log import AgentLog, LogLevel
from swarm_director.models.draft import Draft, DraftType, DraftStatus
from swarm_director.models.email_message import EmailMessage, EmailStatus, EmailPriority

def test_relationships():
    app = create_app()
    with app.app_context():
        # Ensure clean slate  
        db.drop_all()
        db.create_all()
        print('All database tables created successfully')
        
        # Test relationships by creating sample data
        print('Testing model relationships...')
        
        # Create a test agent
        agent = Agent(
            name='Test Agent',
            description='Test agent for relationship testing',
            agent_type=AgentType.WORKER,
            status=AgentStatus.IDLE
        )
        agent.save()
        print(f'Created agent: {agent}')
        
        # Create a test task with the new required fields
        task = Task(
            title='Test Task',
            description='Test task for relationship testing',
            type=TaskType.EMAIL,
            user_id='test_user_123',
            status=TaskStatus.PENDING
        )
        task.save()
        print(f'Created task: {task}')
        
        # Create an agent log
        agent_log = AgentLog.log_agent_activity(
            agent_id=agent.id,
            agent_type='worker',
            message='Test log message',
            task_id=task.id,
            log_level=LogLevel.INFO
        )
        print(f'Created agent log: {agent_log}')
        
        # Create a draft
        draft = Draft(
            task_id=task.id,
            version=1,
            content='Test draft content',
            title='Test Draft',
            draft_type=DraftType.EMAIL,
            author_agent_id=agent.id
        )
        draft.save()
        print(f'Created draft: {draft}')
        
        # Create an email message
        email = EmailMessage(
            task_id=task.id,
            recipient='test@example.com',
            subject='Test Email',
            body='Test email body',
            sender_agent_id=agent.id,
            draft_id=draft.id
        )
        email.save()
        print(f'Created email: {email}')
        
        # Test relationships
        print('\nTesting relationships:')
        print(f'Task agent logs: {len(task.agent_logs)} logs')
        print(f'Task drafts: {len(task.drafts)} drafts')
        print(f'Task emails: {len(task.email_messages)} emails')
        print(f'Agent logs: {len(agent.logs)} logs')
        print(f'Agent authored drafts: {len(agent.authored_drafts)} drafts')
        print(f'Agent sent emails: {len(agent.sent_emails)} emails')
        print(f'Draft email messages: {len(draft.email_messages)} emails')
        
        # Test enum access
        print('\nTesting enum values:')
        print(f'Task type: {task.type.value}')
        print(f'Agent log level: {agent_log.log_level.value}')
        print(f'Draft status: {draft.status.value}')
        print(f'Email status: {email.status.value}')
        
        print('\nAll relationships working correctly!')
        
        # Use assertions for pytest
        assert len(task.agent_logs) == 1
        assert len(task.drafts) == 1
        assert len(task.email_messages) == 1
        assert len(agent.logs) == 1
        assert len(agent.authored_drafts) == 1
        assert len(agent.sent_emails) == 1
        assert len(draft.email_messages) == 1

if __name__ == '__main__':
    test_relationships() 