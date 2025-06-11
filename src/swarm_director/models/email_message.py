"""
EmailMessage model for tracking email communications
"""

from .base import db, BaseModel
from sqlalchemy import Enum
import enum

class EmailStatus(enum.Enum):
    """Enumeration for email status"""
    DRAFT = "draft"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"

class EmailPriority(enum.Enum):
    """Enumeration for email priority"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class EmailMessage(BaseModel):
    """EmailMessage model for tracking email communications"""
    __tablename__ = 'email_messages'
    
    # Foreign key to task (as specified in requirements)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = db.relationship('Task', backref='email_messages')
    
    # Email addressing (as specified in requirements)
    recipient = db.Column(db.String(255), nullable=False)
    sender = db.Column(db.String(255))
    cc = db.Column(db.Text)  # Comma-separated list
    bcc = db.Column(db.Text)  # Comma-separated list
    
    # Email content (as specified in requirements)
    subject = db.Column(db.String(255), nullable=False)
    body = db.Column(db.Text, nullable=False)
    
    # Email status and metadata (as specified in requirements)
    status = db.Column(Enum(EmailStatus), nullable=False, default=EmailStatus.DRAFT)
    sent_at = db.Column(db.DateTime)
    
    # Additional fields for comprehensive email tracking
    priority = db.Column(Enum(EmailPriority), nullable=False, default=EmailPriority.NORMAL)
    
    # Agent that created/sent the email
    sender_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    sender_agent = db.relationship('Agent', backref='sent_emails')
    
    # Email template and draft relationships
    draft_id = db.Column(db.Integer, db.ForeignKey('drafts.id'), nullable=True)
    draft = db.relationship('Draft', backref='email_messages')
    
    # Technical email metadata
    message_id = db.Column(db.String(255), unique=True)  # SMTP message ID
    headers = db.Column(db.JSON)  # Additional email headers
    attachments = db.Column(db.JSON)  # Attachment metadata
    
    # Delivery tracking
    delivery_attempts = db.Column(db.Integer, default=0)
    last_attempt_at = db.Column(db.DateTime)
    error_message = db.Column(db.Text)
    bounce_reason = db.Column(db.Text)
    
    # Engagement tracking
    opened_at = db.Column(db.DateTime)
    clicked_at = db.Column(db.DateTime)
    replied_at = db.Column(db.DateTime)
    
    def __repr__(self):
        return f'<EmailMessage {self.id} to {self.recipient} ({self.status.value})>'
    
    def to_dict(self):
        """Convert email message to dictionary"""
        data = super().to_dict()
        data.update({
            'task_id': self.task_id,
            'status': self.status.value,
            'priority': self.priority.value,
            'sender_agent_id': self.sender_agent_id,
            'draft_id': self.draft_id
        })
        return data
    
    def mark_as_sent(self, message_id=None):
        """Mark email as sent"""
        from datetime import datetime
        self.status = EmailStatus.SENT
        self.sent_at = datetime.utcnow()
        if message_id:
            self.message_id = message_id
        self.save()
    
    def mark_as_failed(self, error_message=None):
        """Mark email as failed"""
        from datetime import datetime
        self.status = EmailStatus.FAILED
        self.last_attempt_at = datetime.utcnow()
        self.delivery_attempts += 1
        if error_message:
            self.error_message = error_message
        self.save()
    
    def mark_as_delivered(self):
        """Mark email as delivered"""
        self.status = EmailStatus.DELIVERED
        self.save()
    
    def mark_as_bounced(self, bounce_reason=None):
        """Mark email as bounced"""
        self.status = EmailStatus.BOUNCED
        if bounce_reason:
            self.bounce_reason = bounce_reason
        self.save()
    
    def mark_as_opened(self):
        """Mark email as opened"""
        from datetime import datetime
        if not self.opened_at:
            self.opened_at = datetime.utcnow()
            self.save()
    
    def mark_as_clicked(self):
        """Mark email as clicked"""
        from datetime import datetime
        if not self.clicked_at:
            self.clicked_at = datetime.utcnow()
            self.save()
    
    def mark_as_replied(self):
        """Mark email as replied to"""
        from datetime import datetime
        if not self.replied_at:
            self.replied_at = datetime.utcnow()
            self.save()
    
    def can_retry(self, max_attempts=3):
        """Check if email can be retried"""
        return (self.status == EmailStatus.FAILED and 
                self.delivery_attempts < max_attempts)
    
    @classmethod
    def get_emails_by_status(cls, status):
        """Get all emails with a specific status"""
        return cls.query.filter_by(status=status).all()
    
    @classmethod
    def get_failed_emails_for_retry(cls, max_attempts=3):
        """Get failed emails that can be retried"""
        return cls.query.filter(
            cls.status == EmailStatus.FAILED,
            cls.delivery_attempts < max_attempts
        ).all() 