# Agents Directory

## Purpose
Contains the complete implementation of AI agents for the SwarmDirector hierarchical management system. This directory houses the three-tier agent architecture (Director → Department → Tool) with specialized agents for intelligent task routing, content creation, email handling, and review processes.

## Structure
```
agents/
├── __init__.py                  # Agent package exports and registry
├── base_agent.py                # Abstract base agent class with common functionality
├── director.py                  # Director agent for intelligent task routing
├── supervisor_agent.py          # Supervisor agent for department management
├── worker_agent.py              # Worker agent for task execution
├── communications_dept.py       # Communications department with parallel workflows
├── email_agent.py               # Email handling with SMTP integration
├── draft_review_agent.py        # Content review and analysis agent
├── review_logic.py              # Review logic and scoring utilities
└── diff_generator.py            # Content difference analysis utilities
```

## Guidelines

### 1. Organization
- **Base Class Inheritance**: All agents must inherit from `BaseAgent` abstract class
- **Agent Registry**: Register all agents in `__init__.py` for automatic discovery
- **Capability Declaration**: Define agent capabilities in database model configuration
- **Hierarchical Structure**: Maintain clear parent-child relationships between agents
- **Department Grouping**: Group related agents into departments for better organization

### 2. Naming
- **Agent Classes**: Use descriptive names ending with "Agent" (e.g., `DirectorAgent`, `EmailAgent`)
- **Methods**: Use action-oriented names (`execute_task`, `can_handle_task`, `route_to_department`)
- **Capabilities**: Use consistent capability names across agents (`email_handling`, `content_creation`)
- **Status Values**: Use enum values for agent status (`IDLE`, `ACTIVE`, `BUSY`, `ERROR`)
- **Task Types**: Use standardized task type names (`communication`, `research`, `analysis`)

### 3. Implementation
- **Abstract Methods**: Implement all abstract methods from `BaseAgent`
- **Error Handling**: Use comprehensive error handling with proper exception types
- **Logging**: Log all significant agent actions and state changes
- **Status Management**: Update agent status appropriately during task execution
- **Resource Cleanup**: Ensure proper cleanup of resources in finally blocks

### 4. Documentation
- **Class Docstrings**: Document agent purpose, capabilities, and usage patterns
- **Method Docstrings**: Include parameters, return values, exceptions, and examples
- **Capability Documentation**: Document all supported capabilities and their requirements
- **Integration Examples**: Provide examples of agent integration and workflow

## Best Practices

### 1. Error Handling
- **Graceful Failures**: Handle errors gracefully without crashing the entire system
- **Error Recovery**: Implement retry mechanisms for transient failures
- **Error Reporting**: Provide detailed error information for debugging
- **Fallback Strategies**: Implement fallback mechanisms when primary methods fail
- **Circuit Breaker**: Use circuit breaker pattern for external service dependencies

### 2. Security
- **Input Validation**: Validate all task inputs before processing
- **Access Control**: Implement proper authorization checks for sensitive operations
- **Data Sanitization**: Sanitize all user inputs to prevent injection attacks
- **Secure Communication**: Use secure protocols for external communications
- **Audit Logging**: Log all security-relevant actions for audit trails

### 3. Performance
- **Async Operations**: Use asynchronous processing for I/O-bound operations
- **Resource Management**: Monitor and limit resource usage per agent
- **Caching**: Cache expensive computations and external API calls
- **Batch Processing**: Process multiple similar tasks in batches when possible
- **Load Balancing**: Distribute tasks across available agents efficiently

### 4. Testing
- **Unit Tests**: Test each agent method in isolation with comprehensive coverage
- **Integration Tests**: Test agent interactions and workflows
- **Mock Dependencies**: Use mocks for external services and database operations
- **Performance Tests**: Include benchmarks for critical agent operations
- **Error Scenario Tests**: Test error handling and recovery mechanisms

### 5. Documentation
- **Agent Capabilities**: Document all capabilities and their requirements
- **Workflow Diagrams**: Include visual representations of agent workflows
- **API Examples**: Provide complete examples of agent usage
- **Troubleshooting**: Include common issues and solutions

## Example

### Complete Agent Implementation

```python
"""
Example: Advanced Email Agent Implementation
Demonstrates comprehensive agent implementation following SwarmDirector patterns
"""

import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
from abc import abstractmethod

from ..models.agent import Agent, AgentStatus
from ..models.task import Task, TaskStatus
from ..models.email_message import EmailMessage
from ..utils.logging import log_agent_action
from ..utils.error_handler import handle_agent_error
from ..utils.validation import validate_email, validate_required_fields
from .base_agent import BaseAgent

class EmailAgent(BaseAgent):
    """
    Specialized agent for email operations with SMTP integration
    
    This agent handles email composition, sending, template processing,
    and email validation with comprehensive error handling and logging.
    
    Capabilities:
        - SMTP integration with multiple providers
        - Email template processing with variable substitution
        - Email validation and sanitization
        - Delivery tracking and retry mechanisms
        - Bulk email operations with rate limiting
    """
    
    def __init__(self, db_agent: Agent):
        """Initialize the email agent with database model"""
        super().__init__(db_agent)
        
        # Email configuration
        self.smtp_config = self.capabilities.get('smtp_config', {})
        self.template_engine = self.capabilities.get('template_engine', 'jinja2')
        self.max_retries = self.capabilities.get('max_retries', 3)
        self.rate_limit = self.capabilities.get('rate_limit', 10)  # emails per minute
        
        # Validation settings
        self.require_validation = self.capabilities.get('require_validation', True)
        self.allowed_domains = self.capabilities.get('allowed_domains', [])
        
    def can_handle_task(self, task: Task) -> bool:
        """
        Check if this agent can handle the given email task
        
        Args:
            task: Task to evaluate
            
        Returns:
            bool: True if agent can handle the task
        """
        # Check task type
        if task.task_type not in ['email', 'communication', 'notification']:
            return False
        
        # Check required fields
        required_fields = ['recipient', 'subject']
        if not all(field in task.input_data for field in required_fields):
            return False
        
        # Validate email addresses
        recipient = task.input_data.get('recipient')
        if not validate_email(recipient):
            return False
        
        # Check domain restrictions
        if self.allowed_domains:
            domain = recipient.split('@')[1]
            if domain not in self.allowed_domains:
                return False
        
        # Check agent availability
        return self.is_available()
    
    @handle_agent_error
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute an email task
        
        Args:
            task: Email task to execute
            
        Returns:
            Dict containing email sending results and metadata
            
        Raises:
            ValueError: If task parameters are invalid
            ConnectionError: If SMTP connection fails
            RuntimeError: If email sending fails
        """
        log_agent_action(self.name, f"Starting email task: {task.title}")
        
        try:
            # Update agent status
            self.update_status(AgentStatus.ACTIVE)
            
            # Validate task parameters
            self._validate_email_task(task)
            
            # Process email template
            email_content = self._process_template(task.input_data)
            
            # Create email message
            email_message = self._create_email_message(email_content)
            
            # Send email with retry mechanism
            delivery_result = self._send_email_with_retry(email_message)
            
            # Log email in database
            self._log_email_message(task, email_message, delivery_result)
            
            # Update task with results
            task.status = TaskStatus.COMPLETED
            task.output_data = {
                'email_sent': True,
                'message_id': delivery_result.get('message_id'),
                'delivery_status': delivery_result.get('status'),
                'recipient': email_content['recipient'],
                'subject': email_content['subject'],
                'sent_at': delivery_result.get('sent_at'),
                'retry_count': delivery_result.get('retry_count', 0)
            }
            task.save()
            
            log_agent_action(self.name, f"Email task completed: {task.title}")
            
            return {
                'status': 'completed',
                'task_id': task.id,
                'email_sent': True,
                'delivery_info': delivery_result,
                'agent_id': self.agent_id
            }
            
        except Exception as e:
            # Handle errors and update task status
            task.status = TaskStatus.FAILED
            task.error_details = str(e)
            task.save()
            
            log_agent_action(self.name, f"Email task failed: {e}")
            raise
            
        finally:
            # Reset agent status
            self.update_status(AgentStatus.IDLE)
    
    def _validate_email_task(self, task: Task) -> None:
        """Validate email task parameters"""
        required_fields = ['recipient', 'subject']
        validate_required_fields(task.input_data, required_fields)
        
        # Validate email addresses
        recipient = task.input_data['recipient']
        if not validate_email(recipient):
            raise ValueError(f"Invalid recipient email: {recipient}")
        
        # Validate sender if provided
        sender = task.input_data.get('sender')
        if sender and not validate_email(sender):
            raise ValueError(f"Invalid sender email: {sender}")
    
    def _process_template(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process email template with variable substitution"""
        template_name = input_data.get('template')
        variables = input_data.get('variables', {})
        
        if template_name:
            # Load and process template
            template_content = self._load_template(template_name)
            processed_content = self._substitute_variables(template_content, variables)
        else:
            # Use direct content
            processed_content = {
                'subject': input_data['subject'],
                'body': input_data.get('body', ''),
                'html_body': input_data.get('html_body')
            }
        
        return {
            'recipient': input_data['recipient'],
            'sender': input_data.get('sender', self.smtp_config.get('default_sender')),
            'subject': processed_content['subject'],
            'body': processed_content['body'],
            'html_body': processed_content.get('html_body'),
            'attachments': input_data.get('attachments', [])
        }
    
    def _create_email_message(self, email_content: Dict[str, Any]) -> MIMEMultipart:
        """Create email message object"""
        message = MIMEMultipart('alternative')
        message['From'] = email_content['sender']
        message['To'] = email_content['recipient']
        message['Subject'] = email_content['subject']
        
        # Add text content
        if email_content['body']:
            text_part = MIMEText(email_content['body'], 'plain')
            message.attach(text_part)
        
        # Add HTML content
        if email_content.get('html_body'):
            html_part = MIMEText(email_content['html_body'], 'html')
            message.attach(html_part)
        
        # Add attachments
        for attachment in email_content.get('attachments', []):
            self._add_attachment(message, attachment)
        
        return message
    
    def _send_email_with_retry(self, message: MIMEMultipart) -> Dict[str, Any]:
        """Send email with retry mechanism"""
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                return self._send_email(message)
            except Exception as e:
                last_error = e
                log_agent_action(self.name, f"Email send attempt {attempt + 1} failed: {e}")
                
                if attempt < self.max_retries - 1:
                    # Wait before retry (exponential backoff)
                    import time
                    time.sleep(2 ** attempt)
        
        # All retries failed
        raise ConnectionError(f"Failed to send email after {self.max_retries} attempts: {last_error}")
    
    def _send_email(self, message: MIMEMultipart) -> Dict[str, Any]:
        """Send email via SMTP"""
        smtp_server = self.smtp_config.get('server', 'localhost')
        smtp_port = self.smtp_config.get('port', 587)
        username = self.smtp_config.get('username')
        password = self.smtp_config.get('password')
        use_tls = self.smtp_config.get('use_tls', True)
        
        # Create SMTP connection
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls(context=context)
            
            if username and password:
                server.login(username, password)
            
            # Send email
            text = message.as_string()
            server.send_message(message)
            
            return {
                'status': 'sent',
                'message_id': message.get('Message-ID'),
                'sent_at': '2023-12-01T10:00:00Z',  # Would use actual timestamp
                'server': smtp_server
            }
    
    def _log_email_message(self, task: Task, message: MIMEMultipart, delivery_result: Dict[str, Any]) -> None:
        """Log email message to database"""
        email_log = EmailMessage(
            task_id=task.id,
            agent_id=self.agent_id,
            recipient=message['To'],
            sender=message['From'],
            subject=message['Subject'],
            body=self._extract_text_body(message),
            html_body=self._extract_html_body(message),
            status=delivery_result.get('status', 'unknown'),
            message_id=delivery_result.get('message_id'),
            sent_at=delivery_result.get('sent_at')
        )
        email_log.save()
    
    def _load_template(self, template_name: str) -> Dict[str, Any]:
        """Load email template from storage"""
        # Implementation would load from file system or database
        return {
            'subject': f"Template: {template_name}",
            'body': f"Template body for {template_name}",
            'html_body': f"<p>Template HTML body for {template_name}</p>"
        }
    
    def _substitute_variables(self, template: Dict[str, Any], variables: Dict[str, Any]) -> Dict[str, Any]:
        """Substitute variables in template content"""
        # Simple variable substitution (would use Jinja2 in production)
        result = {}
        for key, value in template.items():
            if isinstance(value, str):
                for var_name, var_value in variables.items():
                    value = value.replace(f"{{{var_name}}}", str(var_value))
            result[key] = value
        return result

# Agent factory function
def create_email_agent(name: str, smtp_config: Dict[str, Any]) -> EmailAgent:
    """
    Factory function to create an email agent
    
    Args:
        name: Agent name
        smtp_config: SMTP configuration
        
    Returns:
        Configured EmailAgent instance
    """
    from ..models.agent import Agent, AgentType
    
    # Create database model
    db_agent = Agent(
        name=name,
        description="Specialized agent for email operations with SMTP integration",
        agent_type=AgentType.WORKER,
        capabilities={
            'smtp_config': smtp_config,
            'template_engine': 'jinja2',
            'max_retries': 3,
            'rate_limit': 10,
            'require_validation': True
        }
    )
    db_agent.save()
    
    # Create and return agent instance
    return EmailAgent(db_agent)
```

## Related Documentation
- [Base Agent Class](../../../docs/api/agents.md#base-agent) - Abstract base class documentation
- [Agent Models](../models/DIRECTORY.md#agent-model) - Database model for agents
- [Task Processing](../../../docs/architecture/workflow_patterns.md) - Task processing patterns
- [Error Handling](../utils/DIRECTORY.md#error-handling) - Error handling utilities
- [Configuration Guide](../../../docs/deployment/local_development.md) - Agent configuration
