"""
EmailAgent implementation for SwarmDirector
Handles email composition, validation, and delivery via SMTP
"""

import logging
import re
from typing import Dict, List, Any, Optional
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from flask import current_app
from flask_mail import Message

from .worker_agent import WorkerAgent
from ..models.agent import Agent
from ..models.task import Task
from ..models.email_message import EmailMessage, EmailStatus, EmailPriority
from ..models.draft import Draft
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class EmailAgent(WorkerAgent):
    """
    Specialized agent for email operations
    Integrates with Flask-Mail for SMTP delivery
    """
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
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
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute email-related task"""
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
            success = self._send_via_flask_mail(recipient, subject, body, sender)
            
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
        """Validate email data structure and content"""
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
    
    def _send_via_flask_mail(self, recipient: str, subject: str, body: str, sender: str) -> bool:
        """Send email using Flask-Mail"""
        try:
            # Check if Flask-Mail is configured
            if not current_app.config.get('MAIL_SERVER'):
                logger.warning("MAIL_SERVER not configured - simulating email send")
                return True  # Simulate success for development
            
            from flask_mail import Mail, Message
            
            mail = Mail(current_app)
            
            msg = Message(
                subject=subject,
                sender=sender,
                recipients=[recipient],
                body=body
            )
            
            mail.send(msg)
            return True
            
        except Exception as e:
            logger.error(f"Flask-Mail send failed: {str(e)}")
            return False
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task"""
        task_type = task.type.value if hasattr(task.type, 'value') else str(task.type)
        return task_type.lower() in ['email', 'send_email', 'compose_email', 'email_notification']
    
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
