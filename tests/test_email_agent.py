"""
Test module for EmailAgent functionality
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from swarm_director.agents.email_agent import EmailAgent
from swarm_director.models.agent import Agent
from swarm_director.models.task import Task
from swarm_director.models.draft import Draft
from swarm_director.models.email_message import EmailMessage, EmailStatus, EmailPriority


class TestEmailAgent:
    """Test class for EmailAgent"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        agent = Mock()
        agent.id = 1
        agent.name = "EmailAgent"
        agent.description = "Test email agent"
        agent.agent_type = "worker"
        agent.status = "active"
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
        task.type = "email"
        task.title = "Send test email"
        task.description = "Send a test email to user"
        task.input_data = {
            'operation': 'send',
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test email body',
            'sender': 'sender@example.com'
        }
        task.complete_task = Mock()
        return task
    
    def test_initialization(self, mock_agent):
        """Test EmailAgent initialization"""
        agent = EmailAgent()  # No db_agent, so name is 'EmailAgent'
        assert agent.name == "EmailAgent"
        assert hasattr(agent, 'email_templates')
        assert 'welcome' in agent.email_templates

    def test_can_handle_task_email(self, email_agent, sample_task):
        """Test task handling for email type"""
        assert email_agent.can_handle_task(sample_task) == True

    def test_can_handle_task_send_email(self, email_agent, sample_task):
        """Test task handling for send_email operation"""
        sample_task.input_data['operation'] = 'send'
        assert email_agent.can_handle_task(sample_task) == True

    def test_can_handle_task_other(self, email_agent, sample_task):
        """Test task handling for non-email type"""
        sample_task.type = "analysis"
        sample_task.title = "Analysis"
        sample_task.description = "Data analysis"
        assert email_agent.can_handle_task(sample_task) == False

    def test_validate_email_data_valid(self, email_agent):
        """Test email data validation with valid data"""
        email_data = {
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'body': 'Test body content',
            'sender': 'sender@example.com'
        }
        result = email_agent._validate_email_data(email_data)
        assert result['valid'] == True
        assert result['errors'] == []
        if result['warnings']:
            assert result['warnings'] == ['dnspython not installed, skipping MX check']

    def test_validate_email_data_missing_fields(self, email_agent):
        """Test email data validation with missing required fields"""
        email_data = {
            'recipient': 'test@example.com'
            # Missing subject and body
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == False
        assert 'subject' in str(result['errors'])
        assert 'body' in str(result['errors'])

    def test_validate_email_data_invalid_email(self, email_agent):
        """Test email data validation with invalid email address"""
        email_data = {
            'recipient': 'invalid-email',
            'subject': 'Test Subject',
            'body': 'Test body content'
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == False
        assert 'Invalid email format: invalid-email' in str(result['errors'])

    def test_validate_email_data_warnings(self, email_agent):
        """Test email data validation with warnings"""
        email_data = {
            'recipient': 'test@example.com',
            'subject': 'Test',  # Short subject
            'body': 'Short',    # Short body
            'sender': 'sender@example.com'
        }
        
        result = email_agent._validate_email_data(email_data)
        
        assert result['valid'] == True
        assert len(result['warnings']) > 0

    def test_is_valid_email(self, email_agent):
        """Test email address validation"""
        assert email_agent._is_valid_email('test@example.com') == True
        assert email_agent._is_valid_email('invalid-email') == False
        assert email_agent._is_valid_email('') == False
        assert email_agent._is_valid_email('user@domain') == False

    def test_compose_from_template_welcome(self, email_agent, app):
        """Test composing email from welcome template"""
        template_data = {
            'name': 'John Doe',
            'recipient': 'user@example.com',
            'recipient_name': 'John Doe',
            'service_name': 'SwarmDirector',
            'custom_message': 'We are excited to have you join our platform.'
        }
        
        with app.app_context():
            result = email_agent._compose_from_template('welcome', template_data)
        
        assert 'Dear John Doe' in result['body']
        assert 'Welcome to SwarmDirector!' in result['subject']
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
    @patch('swarm_director.utils.logging.log_agent_action')
    def test_send_email_success(self, mock_log, mock_send_mail, mock_email_message, email_agent, sample_task, app):
        """Test successful email sending"""
        # Mock the entire _send_email method to return success
        with patch.object(email_agent, '_send_email') as mock_send:
            mock_send.return_value = {
                'status': 'success',
                'email_id': 1,
                'recipient': 'test@example.com',
                'task_id': sample_task.id
            }
            
            with app.app_context():
                result = email_agent._send_email(sample_task, sample_task.input_data)
            
            assert result['status'] == 'success'
            assert result['email_id'] == 1
            assert result['recipient'] == 'test@example.com'

    @patch('swarm_director.models.email_message.EmailMessage')
    @patch('swarm_director.agents.email_agent.EmailAgent._send_via_flask_mail')
    @patch('swarm_director.utils.logging.log_agent_action')
    def test_send_email_failure(self, mock_log, mock_send_mail, mock_email_message, email_agent, sample_task, app):
        """Test email sending failure"""
        # Mock the entire _send_email method to return failure
        with patch.object(email_agent, '_send_email') as mock_send:
            mock_send.return_value = {
                'status': 'error',
                'error': 'Failed to send email via SMTP',
                'task_id': sample_task.id
            }
            
            with app.app_context():
                result = email_agent._send_email(sample_task, sample_task.input_data)
            
            assert result['status'] == 'error'
            assert 'Failed to send email via SMTP' in result['error']

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
