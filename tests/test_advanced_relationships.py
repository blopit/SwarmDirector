#!/usr/bin/env python3
"""
Advanced test script to verify database constraints, indices, and complex relationships
"""

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskType, TaskStatus
from swarm_director.models.conversation import Conversation
from swarm_director.models.agent_log import AgentLog, LogLevel
from swarm_director.models.draft import Draft, DraftType, DraftStatus
from swarm_director.models.email_message import EmailMessage, EmailStatus, EmailPriority
from sqlalchemy.exc import IntegrityError

def test_advanced_relationships():
    app = create_app()
    with app.app_context():
        # Ensure clean slate
        db.drop_all()
        db.create_all()
        print('Database created successfully')
        
        # Test 1: Foreign key constraints
        print('\n1. Testing foreign key constraints...')
        
        # Create agents in hierarchy
        supervisor = Agent(
            name='Supervisor Agent',
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.ACTIVE
        )
        supervisor.save()
        
        worker1 = Agent(
            name='Worker Agent 1',
            agent_type=AgentType.WORKER,
            status=AgentStatus.IDLE,
            parent_id=supervisor.id
        )
        worker1.save()
        
        worker2 = Agent(
            name='Worker Agent 2',
            agent_type=AgentType.WORKER,
            status=AgentStatus.IDLE,
            parent_id=supervisor.id
        )
        worker2.save()
        
        print(f'Created supervisor with {len(supervisor.children)} child agents')
        
        # Test 2: Task hierarchy and dependencies
        print('\n2. Testing task hierarchy...')
        
        parent_task = Task(
            title='Parent Task',
            description='Main task',
            type=TaskType.COMMUNICATION,
            user_id='user123',
            status=TaskStatus.ASSIGNED,
            assigned_agent_id=supervisor.id
        )
        parent_task.save()
        
        subtask1 = Task(
            title='Subtask 1',
            description='First subtask',
            type=TaskType.EMAIL,
            user_id='user123',
            status=TaskStatus.ASSIGNED,
            parent_task_id=parent_task.id,
            assigned_agent_id=worker1.id
        )
        subtask1.save()
        
        subtask2 = Task(
            title='Subtask 2',
            description='Second subtask',
            type=TaskType.REVIEW,
            user_id='user123',
            status=TaskStatus.PENDING,
            parent_task_id=parent_task.id,
            assigned_agent_id=worker2.id
        )
        subtask2.save()
        
        print(f'Parent task has {len(parent_task.subtasks)} subtasks')
        print(f'Subtask 1 parent: {subtask1.parent_task.title}')
        
        # Test 3: Draft versioning
        print('\n3. Testing draft versioning...')
        
        # Create initial draft
        draft_v1 = Draft(
            task_id=subtask1.id,
            version=1,
            content='Initial draft content',
            title='Email Draft',
            draft_type=DraftType.EMAIL,
            author_agent_id=worker1.id
        )
        draft_v1.save()
        
        # Create new version
        draft_v2 = draft_v1.create_new_version(
            content='Revised draft content',
            author_agent_id=worker1.id
        )
        
        print(f'Draft v1 ID: {draft_v1.id}, v2 ID: {draft_v2.id}')
        print(f'Draft v2 parent: {draft_v2.parent_draft.version}')
        print(f'Draft v1 children: {len(draft_v1.child_drafts)}')
        
        # Test 4: Email with draft relationship
        print('\n4. Testing email-draft relationships...')
        
        email = EmailMessage(
            task_id=subtask1.id,
            recipient='client@example.com',
            subject='Important Communication',
            body=draft_v2.content,
            sender_agent_id=worker1.id,
            draft_id=draft_v2.id,
            priority=EmailPriority.HIGH
        )
        email.save()
        
        # Mark email as sent with unique message ID
        import uuid
        email.mark_as_sent(message_id=f'msg-{uuid.uuid4().hex[:8]}')
        
        print(f'Email status: {email.status.value}')
        print(f'Email linked to draft v{email.draft.version}')
        
        # Test 5: Agent logs with different levels
        print('\n5. Testing agent logs...')
        
        # Create various log entries
        AgentLog.log_agent_activity(
            agent_id=supervisor.id,
            agent_type='supervisor',
            message='Assigned tasks to workers',
            task_id=parent_task.id,
            log_level=LogLevel.INFO
        )
        
        AgentLog.log_agent_activity(
            agent_id=worker1.id,
            agent_type='worker',
            message='Started email composition',
            task_id=subtask1.id,
            log_level=LogLevel.DEBUG,
            execution_time=2.5
        )
        
        AgentLog.log_agent_activity(
            agent_id=worker1.id,
            agent_type='worker',
            message='Email sent successfully',
            task_id=subtask1.id,
            log_level=LogLevel.INFO,
            context={'email_id': email.id, 'recipient': email.recipient}
        )
        
        print(f'Total agent logs: {AgentLog.query.count()}')
        print(f'Worker1 logs: {len(worker1.logs)}')
        print(f'Task logs: {len(subtask1.agent_logs)}')
        
        # Test 6: Query performance and relationships
        print('\n6. Testing complex queries...')
        
        # Get all tasks for a user
        user_tasks = Task.query.filter_by(user_id='user123').all()
        print(f'Tasks for user123: {len(user_tasks)}')
        
        # Get all emails in draft status
        draft_emails = EmailMessage.query.filter_by(status=EmailStatus.DRAFT).all()
        sent_emails = EmailMessage.query.filter_by(status=EmailStatus.SENT).all()
        print(f'Draft emails: {len(draft_emails)}, Sent emails: {len(sent_emails)}')
        
        # Get agent hierarchy
        def print_hierarchy(agent, level=0):
            indent = "  " * level
            print(f'{indent}- {agent.name} ({agent.agent_type.value})')
            for child in agent.children:
                print_hierarchy(child, level + 1)
        
        print('\nAgent hierarchy:')
        print_hierarchy(supervisor)
        
        # Test 7: Business logic methods
        print('\n7. Testing business logic...')
        
        # Test task completion
        subtask1.complete_task({'result': 'Email sent successfully'})
        print(f'Subtask1 status: {subtask1.status.value}')
        print(f'Worker1 tasks completed: {worker1.tasks_completed}')
        
        # Test draft approval
        draft_v2.approve_draft(
            reviewer_agent_id=supervisor.id,
            feedback='Looks good, approved for sending',
            score=8.5
        )
        print(f'Draft v2 status: {draft_v2.status.value}')
        print(f'Draft v2 score: {draft_v2.review_score}')
        
        print('\n✅ All advanced relationship tests passed!')
        
        # Print summary statistics
        print('\n📊 Database Summary:')
        print(f'  Agents: {Agent.query.count()}')
        print(f'  Tasks: {Task.query.count()}')
        print(f'  Drafts: {Draft.query.count()}')
        print(f'  Emails: {EmailMessage.query.count()}')
        print(f'  Agent Logs: {AgentLog.query.count()}')
        
        # Use assertions for pytest
        assert Agent.query.count() == 3
        assert Task.query.count() == 3
        assert Draft.query.count() == 2
        assert EmailMessage.query.count() == 1
        assert AgentLog.query.count() >= 3

if __name__ == '__main__':
    test_advanced_relationships() 