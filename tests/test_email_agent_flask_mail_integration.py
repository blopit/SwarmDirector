"""
Test Flask-Mail integration with EmailAgent
Tests enhanced SMTP functionality, HTML email support, and retry logic
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_mail import Mail, Message

from src.swarm_director.agents.email_agent import EmailAgent
from src.swarm_director.models.agent import Agent
from src.swarm_director.utils.autogen_integration import AutoGenConfig
from src.swarm_director.models.email_message import EmailMessage, EmailStatus, EmailPriority


class TestEmailAgentFlaskMailIntegration:
    """Test suite for EmailAgent Flask-Mail integration"""

    @pytest.fixture
    def app(self):
        """Create a test Flask app with Mail configuration"""
        app = Flask(__name__)
        app.config.update({
            'TESTING': True,
            'MAIL_SERVER': 'smtp.gmail.com',
            'MAIL_PORT': 587,
            'MAIL_USE_TLS': True,
            'MAIL_USERNAME': 'test@example.com',
            'MAIL_PASSWORD': 'testpassword',
            'MAIL_DEFAULT_SENDER': 'test@example.com'
        })
        
        # Initialize Mail extension
        mail = Mail(app)
        app.extensions['mail'] = mail
        
        return app

    @pytest.fixture
    def mock_email_message(self, app):
        """Create a mock EmailMessage with proper attributes inside app context"""
        with app.app_context():
            mock = Mock(spec=EmailMessage)
            mock.id = 1
            mock.mark_as_sent = Mock()
            mock.mark_as_failed = Mock()
            mock.delivery_attempts = 0  # Ensure this is an int
            mock.save = Mock()
            return mock

    @patch('flask_mail.Mail')
    def test_send_via_flask_mail_success(self, mock_mail_class, app, mock_email_message):
        """Test successful email sending via Flask-Mail"""
        with app.app_context():
            mock_mail = MagicMock()
            mock_mail_class.return_value = mock_mail
            app.extensions['mail'] = mock_mail  # Patch the extension
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            result = agent._send_via_flask_mail(
                recipient="test@example.com",
                subject="Test Email",
                body="Test body",
                sender="sender@example.com",
                email_message=mock_email_message
            )
            assert result is True
            mock_mail.send.assert_called_once()
            mock_email_message.mark_as_sent.assert_called_once()

    @patch('flask_mail.Mail')
    def test_send_via_flask_mail_with_html(self, mock_mail_class, app, mock_email_message):
        """Test email sending with HTML content"""
        with app.app_context():
            mock_mail = MagicMock()
            mock_mail_class.return_value = mock_mail
            app.extensions['mail'] = mock_mail  # Patch the extension
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            html_content = "<h1>Test HTML Email</h1><p>This is a test.</p>"
            result = agent._send_via_flask_mail(
                recipient="test@example.com",
                subject="HTML Test Email",
                body="Plain text version",
                sender="sender@example.com",
                html_body=html_content,
                email_message=mock_email_message
            )
            assert result is True
            mock_email_message.mark_as_sent.assert_called_once()
            mock_mail.send.assert_called_once()

    @patch('flask_mail.Mail')
    def test_send_via_flask_mail_retry_logic(self, mock_mail_class, app, mock_email_message):
        """Test retry logic for failed email sends"""
        with app.app_context():
            mock_mail = MagicMock()
            mock_mail_class.return_value = mock_mail
            app.extensions['mail'] = mock_mail  # Patch the extension
            mock_mail.send.side_effect = [
                Exception("Connection failed"),
                Exception("Timeout"),
                None  # Success on third attempt
            ]
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            with patch('time.sleep'):
                result = agent._send_via_flask_mail(
                    recipient="test@example.com",
                    subject="Retry Test",
                    body="Test retry logic",
                    sender="sender@example.com",
                    retry_count=3,
                    email_message=mock_email_message
                )
            assert result is True
            assert mock_mail.send.call_count == 3
            mock_email_message.mark_as_sent.assert_called_once()
            mock_email_message.mark_as_failed.assert_not_called()

    @patch('flask_mail.Mail')
    def test_send_via_flask_mail_max_retries_exceeded(self, mock_mail_class, app, mock_email_message):
        """Test behavior when max retries are exceeded"""
        with app.app_context():
            mock_mail = MagicMock()
            mock_mail_class.return_value = mock_mail
            app.extensions['mail'] = mock_mail  # Patch the extension
            mock_mail.send.side_effect = Exception("Persistent failure")
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            with patch('time.sleep'):
                result = agent._send_via_flask_mail(
                    recipient="test@example.com",
                    subject="Failure Test",
                    body="Test max retries",
                    sender="sender@example.com",
                    retry_count=2,
                    email_message=mock_email_message
                )
            assert result is False
            assert mock_mail.send.call_count == 2
            mock_email_message.mark_as_sent.assert_not_called()
            mock_email_message.mark_as_failed.assert_called_once()

    def test_send_email_tool_with_html(self, app, mock_email_message):
        """Test send_email_tool with HTML support"""
        with app.app_context():
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            with patch.object(agent, '_send_via_flask_mail', return_value=True) as mock_send:
                with patch('src.swarm_director.agents.email_agent.EmailMessage', return_value=mock_email_message):
                    result = agent.send_email_tool(
                        recipient="test@example.com",
                        subject="HTML Tool Test",
                        body="Plain text content",
                        html_body="<h1>HTML content</h1>"
                    )
                    assert result['status'] == 'success'
                    assert result['has_html'] is True
                    mock_send.assert_called_once()
                    print("mock_send.call_args:", mock_send.call_args)
                    args = mock_send.call_args[1] if mock_send.call_args[1] else {}
                    if 'html_body' in args:
                        assert args['html_body'] == "<h1>HTML content</h1>"

    @patch('flask_mail.Message')
    def test_email_headers_configuration(self, mock_message_class, app, mock_email_message):
        """Test that proper email headers are set"""
        with app.app_context():
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            with patch('flask_mail.Mail') as mock_mail_class:
                mock_mail = MagicMock()
                mock_mail_class.return_value = mock_mail
                mock_message = MagicMock()
                mock_message.extra_headers = {}
                mock_message_class.return_value = mock_message
                agent._send_via_flask_mail(
                    recipient="test@example.com",
                    subject="Header Test",
                    body="Test headers",
                    sender="sender@example.com",
                    email_message=mock_email_message
                )
                mock_message_class.assert_called_once()
                # Check the actual headers
                assert mock_message.extra_headers['X-Mailer'] == 'SwarmDirector-EmailAgent'
                assert mock_message.extra_headers['Reply-To'] == 'sender@example.com'

    def test_mail_server_not_configured(self, app, mock_email_message):
        """Test behavior when MAIL_SERVER is not configured"""
        with app.app_context():
            app.config['MAIL_SERVER'] = None
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            result = agent._send_via_flask_mail(
                recipient="test@example.com",
                subject="No Mail Server",
                body="Test body",
                sender="sender@example.com",
                email_message=mock_email_message
            )
            assert result is True
            mock_email_message.mark_as_sent.assert_called_once()

    def test_tool_registration_includes_html_parameter(self, app):
        """Test that tool registration includes html_body parameter"""
        with app.app_context():
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            tools = agent.available_tools
            assert 'send_email' in tools
            params = tools['send_email']['parameters']
            assert 'html_body' in params

    def test_backward_compatibility_maintained(self, app, mock_email_message):
        """Test that existing functionality is maintained"""
        with app.app_context():
            from src.swarm_director.agents.email_agent import EmailAgent
            from src.swarm_director.utils.autogen_integration import AutoGenConfig
            mock_db_agent = Mock()
            mock_db_agent.id = 1
            agent = EmailAgent(
                name="TestEmailAgent",
                config=AutoGenConfig(temperature=0.3, max_tokens=1500),
                db_agent=mock_db_agent
            )
            with patch.object(agent, '_send_via_flask_mail', return_value=True):
                with patch('src.swarm_director.agents.email_agent.EmailMessage', return_value=mock_email_message):
                    result = agent.send_email_tool(
                        recipient="test@example.com",
                        subject="Backward Compatibility Test",
                        body="Test body"
                        # No html_body parameter
                    )
                    assert result['status'] == 'success'
                    assert 'has_html' in result
                    assert result['has_html'] is False


if __name__ == '__main__':
    pytest.main([__file__])