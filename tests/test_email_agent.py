"""
Tests for EmailAgent
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from swarm_director.agents.email_agent import EmailAgent
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.models.email_message import EmailMessage, EmailStatus, EmailPriority
from swarm_director.models.draft import Draft


class TestEmailAgent:
    """Test suite for EmailAgent"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        agent = Mock()
        agent.id = 1
        agent.name = "EmailAgent"
        agent.agent_type = AgentType.WORKER
        agent.status = AgentStatus.ACTIVE
        return agent
    
    @pytest.fixture
    def email_agent(self, mock_agent, app):
        """Create EmailAgent instance for testing"""
        with app.app_context():
            return EmailAgent(mock_agent)
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing"""
        task = Mock()
        task.id = 1
        task.title = "Send Email"
        task.description = "Send test email"
        task.type = "email"
        task.input_data = {
            'operation': 'send',
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test email body',
            'sender': 'sender@example.com'
        }
        task.save = Mock()
        task.complete_task = Mock()
        return task
    
    def test_initialization(self, mock_agent):
        """Test EmailAgent initialization"""
        agent = EmailAgent(mock_agent)
        
        assert agent.db_agent == mock_agent
        assert 'welcome' in agent.email_templates
        assert 'notification' in agent.email_templates
        assert 'reminder' in agent.email_templates
    
    def test_can_handle_task_email(self, email_agent, sample_task):
        """Test task handling capability for email tasks"""
        sample_task.type = "email"
        assert email_agent.can_handle_task(sample_task) == True
    
    def test_can_handle_task_send_email(self, email_agent, sample_task):
        """Test task handling capability for send_email tasks"""
        sample_task.type = "send_email"
        assert email_agent.can_handle_task(sample_task) == True
    
    def test_can_handle_task_other(self, email_agent, sample_task):
        """Test task handling capability for non-email tasks"""
        sample_task.type = "calculation"
        assert email_agent.can_handle_task(sample_task) == False
    
    def test_validate_email_data_valid(self, email_agent):
        """Test email data validation with valid data"""
        email_data = {
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test email body content',
            'sender': 'sender@example.com'
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == True
        assert len(result['errors']) == 0
        assert result['field_count'] == 4
    
    def test_validate_email_data_missing_fields(self, email_agent):
        """Test email data validation with missing required fields"""
        email_data = {
            'subject': 'Test Subject'
            # Missing recipient and body
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == False
        assert 'Missing required field: recipient' in result['errors']
        assert 'Missing required field: body' in result['errors']
    
    def test_validate_email_data_invalid_email(self, email_agent):
        """Test email data validation with invalid email format"""
        email_data = {
            'recipient': 'invalid-email',
            'subject': 'Test Subject',
            'body': 'Test body',
            'sender': 'also-invalid'
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == False
        assert 'Invalid email format: invalid-email' in result['errors']
        assert 'Invalid sender email format: also-invalid' in result['errors']
    
    def test_validate_email_data_warnings(self, email_agent):
        """Test email data validation warnings"""
        email_data = {
            'recipient': 'test@example.com',
            'subject': 'Hi',  # Too short
            'body': 'Short',  # Too short
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == True  # No errors, just warnings
        assert 'Subject line is very short (<5 characters)' in result['warnings']
        assert 'Email body is very short (<10 characters)' in result['warnings']
    
    def test_is_valid_email(self, email_agent):
        """Test email format validation"""
        assert email_agent._is_valid_email('test@example.com') == True
        assert email_agent._is_valid_email('user.name+tag@domain.co.uk') == True
        assert email_agent._is_valid_email('invalid-email') == False
        assert email_agent._is_valid_email('missing@') == False
        assert email_agent._is_valid_email('@missing.com') == False
    
    def test_compose_from_template_welcome(self, email_agent, app):
        """Test composing email from welcome template"""
        data = {
            'recipient': 'user@example.com',
            'recipient_name': 'John Doe',
            'service_name': 'SwarmDirector',
            'custom_message': 'Welcome aboard!'
        }
        
        with app.app_context():
            result = email_agent._compose_from_template('welcome', data)
        
        assert result['subject'] == 'Welcome to SwarmDirector!'
        assert 'Dear John Doe' in result['body']
        assert 'Welcome aboard!' in result['body']
        assert result['recipient'] == 'user@example.com'
        assert result['template_used'] == 'welcome'
    
    def test_compose_from_template_unknown(self, email_agent):
        """Test composing email from unknown template"""
        with pytest.raises(ValueError, match="Unknown email template"):
            email_agent._compose_from_template('unknown_template', {})
    
    @patch('swarm_director.models.draft.Draft.query')
    def test_compose_from_draft(self, mock_query, email_agent, app):
        """Test composing email from existing draft"""
        # Mock draft
        mock_draft = Mock(spec=Draft)
        mock_draft.content = "Draft email content"
        mock_draft.metadata = {
            'subject': 'Draft Subject',
            'recipient': 'draft@example.com'
        }
        mock_query.get.return_value = mock_draft
        
        data = {'recipient': 'new@example.com'}
        
        with app.app_context():
            result = email_agent._compose_from_draft(1, data)
        
        assert result['body'] == "Draft email content"
        assert result['subject'] == "Draft Subject"
        assert result['recipient'] == 'new@example.com'  # Override from data
        assert result['draft_used'] == 1
    
    @patch('swarm_director.models.draft.Draft.query')
    def test_compose_from_draft_not_found(self, mock_query, email_agent, app):
        """Test composing email from non-existent draft"""
        mock_query.get.return_value = None
        
        with app.app_context():
            with pytest.raises(ValueError, match="Draft not found"):
                email_agent._compose_from_draft(999, {})
    
    @patch('swarm_director.models.email_message.EmailMessage')
    @patch('swarm_director.agents.email_agent.EmailAgent._send_via_flask_mail')
    @patch('swarm_director.models.email_message.EmailStatus')
    @patch('swarm_director.models.email_message.EmailPriority')
    def test_send_email_success(self, mock_priority, mock_status, mock_send_mail, mock_email_message, email_agent, sample_task, app):
        """Test successful email sending"""
        # Mock enum values
        mock_status.QUEUED = 'QUEUED'
        mock_priority.NORMAL = 'NORMAL'
        mock_priority.HIGH = 'HIGH'
        
        # Mock email message
        mock_msg_instance = Mock()
        mock_msg_instance.id = 1
        mock_msg_instance.save = Mock()
        mock_msg_instance.mark_as_sent = Mock()
        mock_email_message.return_value = mock_msg_instance
        
        # Mock successful sending
        mock_send_mail.return_value = True
        
        with app.app_context():
            result = email_agent._send_email(sample_task, sample_task.input_data)
        
        assert result['status'] == 'success'
        assert result['email_id'] == 1
        assert result['recipient'] == 'test@example.com'
        mock_msg_instance.mark_as_sent.assert_called_once()
        sample_task.complete_task.assert_called_once()
    
    @patch('swarm_director.models.email_message.EmailMessage')
    @patch('swarm_director.agents.email_agent.EmailAgent._send_via_flask_mail')
    @patch('swarm_director.models.email_message.EmailStatus')
    @patch('swarm_director.models.email_message.EmailPriority')
    def test_send_email_failure(self, mock_priority, mock_status, mock_send_mail, mock_email_message, email_agent, sample_task, app):
        """Test email sending failure"""
        # Mock enum values
        mock_status.QUEUED = 'QUEUED'
        mock_priority.NORMAL = 'NORMAL'
        mock_priority.HIGH = 'HIGH'
        
        # Mock email message
        mock_msg_instance = Mock()
        mock_msg_instance.id = 1
        mock_msg_instance.save = Mock()
        mock_msg_instance.mark_as_failed = Mock()
        mock_email_message.return_value = mock_msg_instance
        
        # Mock failed sending
        mock_send_mail.return_value = False
        
        with app.app_context():
            result = email_agent._send_email(sample_task, sample_task.input_data)
        
        assert result['status'] == 'error'
        assert 'Failed to send email via SMTP' in result['error']
        mock_msg_instance.mark_as_failed.assert_called_once()
    
    def test_send_email_validation_failure(self, email_agent, sample_task):
        """Test email sending with validation failure"""
        # Invalid email data
        sample_task.input_data = {
            'operation': 'send',
            'recipient': 'invalid-email',
            'subject': '',
            'body': ''
        }
        
        result = email_agent._send_email(sample_task, sample_task.input_data)
        
        assert result['status'] == 'error'
        assert 'Email validation failed' in result['error']
    
    @patch('swarm_director.models.draft.Draft')
    def test_compose_email_manual(self, mock_draft, email_agent, sample_task, app):
        """Test manual email composition"""
        # Mock draft creation
        mock_draft_instance = Mock()
        mock_draft_instance.id = 1
        mock_draft_instance.save = Mock()
        mock_draft.return_value = mock_draft_instance
        
        compose_data = {
            'operation': 'compose',
            'subject': 'Manual Subject',
            'body': 'Manual body content',
            'recipient': 'manual@example.com'
        }
        
        # Mock the Draft model imports in the _compose_email method
        with patch('swarm_director.models.draft.DraftType') as mock_draft_type, \
             patch('swarm_director.models.draft.DraftStatus') as mock_draft_status:
            mock_draft_type.EMAIL = 'EMAIL'
            mock_draft_status.DRAFT = 'DRAFT'
            
            with app.app_context():
                result = email_agent._compose_email(sample_task, compose_data)
        
        assert result['status'] == 'success'
        assert result['draft_id'] == 1
        assert result['composed_email']['subject'] == 'Manual Subject'
        assert result['composed_email']['body'] == 'Manual body content'
        sample_task.complete_task.assert_called_once()
    
    def test_validate_email_operation(self, email_agent, sample_task):
        """Test email validation operation"""
        validate_data = {
            'operation': 'validate',
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test body content'
        }
        
        result = email_agent._validate_email(sample_task, validate_data)
        
        assert result['status'] == 'success'
        assert result['validation_result']['valid'] == True
        sample_task.complete_task.assert_called_once()
    
    def test_execute_task_unknown_operation(self, email_agent, sample_task):
        """Test executing task with unknown operation"""
        sample_task.input_data = {'operation': 'unknown_operation'}
        
        result = email_agent.execute_task(sample_task)
        
        assert result['status'] == 'error'
        assert 'Unknown email operation: unknown_operation' in result['error']
    
    def test_execute_task_exception_handling(self, email_agent, sample_task):
        """Test exception handling in execute_task"""
        # Mock method to raise exception
        email_agent._send_email = Mock(side_effect=Exception("Test error"))
        
        result = email_agent.execute_task(sample_task)
        
        assert result['status'] == 'error'
        assert 'Error processing email task: Test error' in result['error']
    
    def test_get_email_templates(self, email_agent):
        """Test getting list of email templates"""
        templates = email_agent.get_email_templates()
        
        assert 'welcome' in templates
        assert 'notification' in templates
        assert 'reminder' in templates
        assert len(templates) == 3
    
    def test_add_email_template(self, email_agent):
        """Test adding new email template"""
        success = email_agent.add_email_template(
            'custom',
            'Custom Subject: {title}',
            'Custom template body: {content}'
        )
        
        assert success == True
        assert 'custom' in email_agent.email_templates
        assert email_agent.email_templates['custom']['subject'] == 'Custom Subject: {title}'
