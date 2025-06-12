"""
EmailAgent implementation for SwarmDirector
Handles email composition, validation, and delivery via SMTP
Enhanced with AutoGen ToolAgent capabilities
"""

import logging
import re
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app
from flask_mail import Message

from ..utils.autogen_integration import AutoGenToolAgent, AutoGenConfig
from ..models.agent import Agent
from ..models.task import Task
from ..models.email_message import EmailMessage, EmailStatus, EmailPriority
from ..models.draft import Draft
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class EmailAgent(AutoGenToolAgent):
    """
    AutoGen ToolAgent for email operations
    Integrates with Flask-Mail for SMTP delivery and provides tool functions for other agents
    """
    
    def __init__(self, name: str = "EmailAgent", config: Optional[AutoGenConfig] = None, 
                 db_agent: Optional[Agent] = None):
        # Configure as ToolAgent with email-specific system message
        default_config = config or AutoGenConfig(
            temperature=0.3,  # Low temperature for consistent email operations
            max_tokens=1500,
            timeout=120
        )
        
        system_message = """You are an EmailAgent specialized in email operations and SMTP delivery.

Your capabilities include:
- Sending emails via SMTP using Flask-Mail
- Email composition from templates or drafts
- Email validation and formatting
- Tracking email delivery status
- Managing email templates
- Parsing email components (recipient, subject, body)

You have access to the following tools:
- send_email: Send an email via SMTP
- compose_email: Compose email from template or manual input
- validate_email: Validate email addresses and content
- get_email_templates: List available email templates
- add_email_template: Add new email template

Always ensure email addresses are valid and content is appropriate before sending.
Provide clear feedback on email operations including success/failure status."""
        
        super().__init__(name, default_config, system_message)
        
        # Store database agent reference for compatibility
        self.db_agent = db_agent
        self.agent_id = db_agent.id if db_agent else None
        
        # Email templates
        self.email_templates = {
            'welcome': {
                'subject': 'Welcome to {service_name}!',
                'template': '''Dear {recipient_name},

Welcome to {service_name}! We're excited to have you on board.

{custom_message}

Best regards,
The {service_name} Team'''
            },
            'notification': {
                'subject': 'Notification: {notification_type}',
                'template': '''Hello {recipient_name},

{notification_message}

{additional_details}

Best regards,
{sender_name}'''
            },
            'reminder': {
                'subject': 'Reminder: {reminder_type}',
                'template': '''Dear {recipient_name},

This is a friendly reminder about: {reminder_details}

{action_required}

Thank you,
{sender_name}'''
            }
        }
        
        # Register tool functions
        self._register_email_tools()
        
        logger.info(f"EmailAgent initialized as AutoGen ToolAgent: {name}")
    
    def _register_email_tools(self):
        """Register email operation tools for AutoGen framework"""
        # This method prepares the tools that other agents can call
        self.available_tools = {
            'send_email': {
                'function': self.send_email_tool,
                'description': 'Send an email via SMTP',
                'parameters': {
                    'recipient': 'Email recipient address',
                    'subject': 'Email subject line',
                    'body': 'Email body content',
                    'sender': 'Sender email address (optional)',
                    'priority': 'Email priority (normal, high, low)',
                    'html_body': 'HTML email body content (optional)'
                }
            },
            'compose_email': {
                'function': self.compose_email_tool,
                'description': 'Compose email from template or draft',
                'parameters': {
                    'template': 'Template name (optional)',
                    'draft_id': 'Draft ID to use (optional)',
                    'data': 'Data for template substitution'
                }
            },
            'validate_email': {
                'function': self.validate_email_tool,
                'description': 'Validate email address and content',
                'parameters': {
                    'email_data': 'Email data to validate'
                }
            },
            'get_email_templates': {
                'function': self.get_email_templates,
                'description': 'Get list of available email templates',
                'parameters': {}
            },
            'add_email_template': {
                'function': self.add_email_template,
                'description': 'Add new email template',
                'parameters': {
                    'name': 'Template name',
                    'subject': 'Template subject',
                    'template': 'Template content'
                }
            }
        }
    
    def send_email_tool(self, recipient: str, subject: str, body: str, 
                       sender: str = None, priority: str = 'normal', html_body: str = None) -> Dict[str, Any]:
        """Tool function for sending emails via SMTP with HTML support"""
        log_agent_action(self.name, f"Tool call: send_email to {recipient}")
        
        email_data = {
            'recipient': recipient,
            'subject': subject,
            'body': body,
            'sender': sender,
            'priority': priority,
            'html_body': html_body,
            'operation': 'send'
        }
        
        # Validate email data
        validation_result = self._validate_email_data(email_data)
        if not validation_result['valid']:
            return {
                "status": "error",
                "error": f"Email validation failed: {validation_result['errors']}",
                "tool": "send_email"
            }
        
        try:
            # Extract email components
            sender = sender or current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com')
            
            # Create email message record if database agent is available
            email_message = None
            if self.db_agent:
                email_message = EmailMessage(
                    recipient=recipient,
                    sender=sender,
                    subject=subject,
                    body=body,
                    status=EmailStatus.QUEUED,
                    priority=EmailPriority.HIGH if priority == 'high' else EmailPriority.NORMAL,
                    sender_agent_id=self.agent_id
                )
                email_message.save()
            
            # Send email using Flask-Mail with HTML support
            success = self._send_via_flask_mail(recipient, subject, body, sender, html_body, email_message=email_message)
            
            if success:
                if email_message:
                    email_message.mark_as_sent()
                
                log_agent_action(self.name, f"Email sent successfully to {recipient}")
                
                return {
                    "status": "success",
                    "message": "Email sent successfully",
                    "email_id": email_message.id if email_message else None,
                    "recipient": recipient,
                    "has_html": bool(html_body),
                    "tool": "send_email"
                }
            else:
                if email_message:
                    email_message.mark_as_failed("SMTP delivery failed")
                return {
                    "status": "error",
                    "error": "Failed to send email via SMTP",
                    "email_id": email_message.id if email_message else None,
                    "tool": "send_email"
                }
                
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            if email_message:
                email_message.mark_as_failed(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "tool": "send_email"
            }
    
    def compose_email_tool(self, template: str = None, draft_id: int = None, 
                          data: Dict = None) -> Dict[str, Any]:
        """Tool function for composing emails from template or draft"""
        log_agent_action(self.name, "Tool call: compose_email")
        
        try:
            data = data or {}
            
            if template:
                # Use template
                composed_email = self._compose_from_template(template, data)
            elif draft_id:
                # Use existing draft
                composed_email = self._compose_from_draft(draft_id, data)
            else:
                # Manual composition
                composed_email = {
                    'subject': data.get('subject', 'No Subject'),
                    'body': data.get('body', ''),
                    'recipient': data.get('recipient', ''),
                    'sender': data.get('sender', current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com'))
                }
            
            return {
                "status": "success",
                "composed_email": composed_email,
                "tool": "compose_email"
            }
            
        except Exception as e:
            error_msg = f"Error composing email: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "tool": "compose_email"
            }
    
    def validate_email_tool(self, email_data: Dict) -> Dict[str, Any]:
        """Tool function for email validation"""
        log_agent_action(self.name, "Tool call: validate_email")
        
        validation_result = self._validate_email_data(email_data)
        
        return {
            "status": "success",
            "validation_result": validation_result,
            "tool": "validate_email"
        }

    # Legacy methods for backward compatibility with existing Task-based workflow
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute email-related task (legacy compatibility method)"""
        log_agent_action(self.name, f"Processing email task: {task.title}")
        
        try:
            # Extract email parameters from task
            email_data = task.input_data or {}
            
            # Determine email operation type
            operation = email_data.get('operation', 'send')
            
            if operation == 'send':
                return self._send_email(task, email_data)
            elif operation == 'compose':
                return self._compose_email(task, email_data)
            elif operation == 'validate':
                return self._validate_email(task, email_data)
            else:
                return {
                    "status": "error",
                    "error": f"Unknown email operation: {operation}",
                    "task_id": task.id
                }
                
        except Exception as e:
            error_msg = f"Error processing email task: {str(e)}"
            logger.error(error_msg)
            log_agent_action(self.name, error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }

    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task"""
        task_text = (task.title + " " + (task.description or "")).lower()
        email_keywords = ["email", "mail", "send", "message", "notification", "smtp"]
        return any(keyword in task_text for keyword in email_keywords)

    def _send_email(self, task: Task, email_data: Dict) -> Dict[str, Any]:
        """Send email via SMTP"""
        log_agent_action(self.name, "Sending email")
        
        # Validate required fields
        validation_result = self._validate_email_data(email_data)
        if not validation_result['valid']:
            return {
                "status": "error",
                "error": f"Email validation failed: {validation_result['errors']}",
                "task_id": task.id
            }
        
        try:
            # Extract email components
            recipient = email_data['recipient']
            subject = email_data['subject']
            body = email_data['body']
            sender = email_data.get('sender', current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com'))
            priority = email_data.get('priority', 'normal')
            
            # Create email message record
            email_message = EmailMessage(
                task_id=task.id,
                recipient=recipient,
                sender=sender,
                subject=subject,
                body=body,
                status=EmailStatus.QUEUED,
                priority=EmailPriority.HIGH if priority == 'high' else EmailPriority.NORMAL,
                sender_agent_id=self.db_agent.id
            )
            email_message.save()
            
            # Send email using Flask-Mail
            success = self._send_via_flask_mail(recipient, subject, body, sender, email_message=email_message)
            
            if success:
                email_message.mark_as_sent()
                task.complete_task(output_data={
                    'email_sent': True,
                    'recipient': recipient,
                    'subject': subject,
                    'email_id': email_message.id
                })
                
                log_agent_action(self.name, f"Email sent successfully to {recipient}")
                
                return {
                    "status": "success",
                    "message": "Email sent successfully",
                    "email_id": email_message.id,
                    "recipient": recipient,
                    "task_id": task.id
                }
            else:
                email_message.mark_as_failed("SMTP delivery failed")
                return {
                    "status": "error",
                    "error": "Failed to send email via SMTP",
                    "email_id": email_message.id,
                    "task_id": task.id
                }
                
        except Exception as e:
            error_msg = f"Error sending email: {str(e)}"
            logger.error(error_msg)
            if 'email_message' in locals():
                email_message.mark_as_failed(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _compose_email(self, task: Task, email_data: Dict) -> Dict[str, Any]:
        """Compose email from template or draft"""
        log_agent_action(self.name, "Composing email")
        
        try:
            template_name = email_data.get('template')
            draft_id = email_data.get('draft_id')
            
            if template_name:
                # Use template
                composed_email = self._compose_from_template(template_name, email_data)
            elif draft_id:
                # Use existing draft
                composed_email = self._compose_from_draft(draft_id, email_data)
            else:
                # Manual composition
                composed_email = {
                    'subject': email_data.get('subject', 'No Subject'),
                    'body': email_data.get('body', ''),
                    'recipient': email_data.get('recipient', ''),
                    'sender': email_data.get('sender', current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com'))
                }
            
            # Create draft record
            from swarm_director.models.draft import DraftType, DraftStatus
            draft = Draft(
                task_id=task.id,
                content=composed_email['body'],
                draft_type=DraftType.EMAIL,
                status=DraftStatus.DRAFT,
                version=1,
                metadata={
                    'subject': composed_email['subject'],
                    'recipient': composed_email['recipient'],
                    'sender': composed_email['sender'],
                    'composed_by': self.name,
                    'composed_at': datetime.utcnow().isoformat()
                }
            )
            draft.save()
            
            task.complete_task(output_data=composed_email)
            
            log_agent_action(self.name, f"Email composed successfully (Draft ID: {draft.id})")
            
            return {
                "status": "success",
                "message": "Email composed successfully",
                "composed_email": composed_email,
                "draft_id": draft.id,
                "task_id": task.id
            }
            
        except Exception as e:
            error_msg = f"Error composing email: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _validate_email(self, task: Task, email_data: Dict) -> Dict[str, Any]:
        """Validate email data and format"""
        log_agent_action(self.name, "Validating email")
        
        validation_result = self._validate_email_data(email_data)
        
        task.complete_task(output_data=validation_result)
        
        return {
            "status": "success",
            "validation_result": validation_result,
            "task_id": task.id
        }
    
    def _validate_email_data(self, email_data: Dict) -> Dict[str, Any]:
        """
        Validate email data structure and content.
        Now includes optional DNS/MX check if dnspython is installed.
        """
        import re
        errors = []
        warnings = []
        
        # Check required fields
        required_fields = ['recipient', 'subject', 'body']
        for field in required_fields:
            if not email_data.get(field):
                errors.append(f"Missing required field: {field}")
        
        # Validate email format
        recipient = email_data.get('recipient', '')
        if recipient and not self._is_valid_email(recipient):
            errors.append(f"Invalid email format: {recipient}")
        
        # Optional: DNS/MX check for recipient domain
        recipient_domain = recipient.split('@')[-1] if '@' in recipient else None
        if recipient_domain:
            try:
                import dns.resolver
                answers = dns.resolver.resolve(recipient_domain, 'MX')
                if not answers:
                    warnings.append(f"No MX records found for domain: {recipient_domain}")
            except ImportError:
                warnings.append("dnspython not installed, skipping MX check")
            except Exception as e:
                warnings.append(f"MX check failed for {recipient_domain}: {e}")
        
        # Validate sender if provided
        sender = email_data.get('sender', '')
        if sender and not self._is_valid_email(sender):
            errors.append(f"Invalid sender email format: {sender}")
        
        # Check subject length
        subject = email_data.get('subject', '')
        if len(subject) > 200:
            warnings.append("Subject line is very long (>200 characters)")
        elif len(subject) < 5:
            warnings.append("Subject line is very short (<5 characters)")
        
        # Check body content
        body = email_data.get('body', '')
        if len(body) < 10:
            warnings.append("Email body is very short (<10 characters)")
        elif len(body) > 10000:
            warnings.append("Email body is very long (>10000 characters)")
        
        return {
            'valid': len(errors) == 0,
            'errors': errors,
            'warnings': warnings,
            'field_count': len([k for k in email_data.keys() if email_data[k]]),
            'validated_at': datetime.utcnow().isoformat()
        }
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email address format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def _compose_from_template(self, template_name: str, data: Dict) -> Dict[str, Any]:
        """Compose email from predefined template"""
        if template_name not in self.email_templates:
            raise ValueError(f"Unknown email template: {template_name}")
        
        template = self.email_templates[template_name]
        
        # Format subject and body with provided data
        subject = template['subject'].format(**data)
        body = template['template'].format(**data)
        
        return {
            'subject': subject,
            'body': body,
            'recipient': data.get('recipient', ''),
            'sender': data.get('sender', current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com')),
            'template_used': template_name
        }
    
    def _compose_from_draft(self, draft_id: int, data: Dict) -> Dict[str, Any]:
        """Compose email from existing draft"""
        try:
            draft = Draft.query.get(draft_id)
            if not draft:
                raise ValueError(f"Draft not found: {draft_id}")
            
            metadata = draft.metadata or {}
            
            return {
                'subject': metadata.get('subject', data.get('subject', 'No Subject')),
                'body': draft.content,
                'recipient': data.get('recipient', metadata.get('recipient', '')),
                'sender': data.get('sender', metadata.get('sender', current_app.config.get('MAIL_USERNAME', 'noreply@swarmdirector.com'))),
                'draft_used': draft_id
            }
            
        except Exception as e:
            raise ValueError(f"Error loading draft {draft_id}: {str(e)}")
    
    def _send_via_flask_mail(self, recipient: str, subject: str, body: str, sender: str, 
                            html_body: str = None, retry_count: int = 3, email_message=None) -> bool:
        """
        Send email using Flask-Mail with enhanced functionality and delivery tracking.
        Updates EmailMessage status in DB for SENT, FAILED.
        """
        for attempt in range(retry_count):
            try:
                if not current_app.config.get('MAIL_SERVER'):
                    logger.warning("MAIL_SERVER not configured - simulating email send")
                    if email_message:
                        email_message.mark_as_sent()
                    return True
                from flask_mail import Mail, Message
                mail = current_app.extensions.get('mail') or Mail(current_app)
                msg = Message(
                    subject=subject,
                    sender=sender,
                    recipients=[recipient],
                    body=body,
                    html=html_body
                )
                msg.extra_headers = {
                    'X-Mailer': 'SwarmDirector-EmailAgent',
                    'X-Priority': '3',
                    'Reply-To': sender
                }
                mail.send(msg)
                logger.info(f"Email sent successfully to {recipient} (attempt {attempt + 1})")
                if email_message:
                    email_message.mark_as_sent()
                # Placeholder: Add delivery tracking hook here (e.g., webhook, tracking pixel)
                return True
            except Exception as e:
                logger.warning(f"Flask-Mail send attempt {attempt + 1} failed: {str(e)}")
                if attempt == retry_count - 1:
                    logger.error(f"Flask-Mail send failed after {retry_count} attempts: {str(e)}")
                    if email_message:
                        email_message.mark_as_failed(str(e))
                    return False
                import time
                time.sleep(2 ** attempt)
        return False

    # Placeholder for open/click tracking (to be implemented if/when email tracking is supported)
    def track_email_open(self, email_id: int):
        """Mark email as opened (to be called by tracking pixel endpoint)"""
        try:
            email_message = EmailMessage.query.get(email_id)
            if email_message:
                email_message.status = EmailStatus.OPENED
                email_message.save()
                logger.info(f"Email {email_id} marked as OPENED")
        except Exception as e:
            logger.error(f"Failed to mark email {email_id} as OPENED: {e}")

    def track_email_click(self, email_id: int):
        """Mark email as clicked (to be called by click tracking endpoint)"""
        try:
            email_message = EmailMessage.query.get(email_id)
            if email_message:
                email_message.status = EmailStatus.CLICKED
                email_message.save()
                logger.info(f"Email {email_id} marked as CLICKED")
        except Exception as e:
            logger.error(f"Failed to mark email {email_id} as CLICKED: {e}")
    
    def get_email_templates(self) -> List[str]:
        """Get list of available email templates"""
        return list(self.email_templates.keys())
    
    def add_email_template(self, name: str, subject: str, template: str) -> bool:
        """Add new email template"""
        try:
            self.email_templates[name] = {
                'subject': subject,
                'template': template
            }
            return True
        except Exception as e:
            logger.error(f"Error adding email template: {e}")
            return False
