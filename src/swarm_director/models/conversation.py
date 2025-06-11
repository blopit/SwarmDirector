"""
Conversation model for tracking agent communications and chat history
"""

from .base import db, BaseModel
from sqlalchemy import Enum
import enum

class MessageType(enum.Enum):
    """Enumeration for message types"""
    USER_MESSAGE = "user_message"
    AGENT_RESPONSE = "agent_response"
    SYSTEM_MESSAGE = "system_message"
    AGENT_TO_AGENT = "agent_to_agent"
    ERROR_MESSAGE = "error_message"

class ConversationStatus(enum.Enum):
    """Enumeration for conversation status"""
    ACTIVE = "active"
    COMPLETED = "completed"
    PAUSED = "paused"
    ERROR = "error"

class Conversation(BaseModel):
    """Conversation model for tracking multi-agent communications"""
    __tablename__ = 'conversations'
    
    # Basic conversation information
    title = db.Column(db.String(200))
    description = db.Column(db.Text)
    status = db.Column(Enum(ConversationStatus), nullable=False, default=ConversationStatus.ACTIVE)
    
    # Conversation participants
    initiator_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    initiator_agent = db.relationship('Agent', foreign_keys=[initiator_agent_id])
    
    # Conversation metadata
    session_id = db.Column(db.String(100), unique=True)  # Unique session identifier
    user_id = db.Column(db.String(100))  # User identifier if user is involved
    conversation_type = db.Column(db.String(50))  # Type of conversation (task, query, etc.)
    
    # AutoGen specific fields
    autogen_chat_history = db.Column(db.JSON)  # Store AutoGen chat history
    group_chat_config = db.Column(db.JSON)  # Configuration for group chats
    
    def __repr__(self):
        return f'<Conversation {self.id} ({self.status.value})>'
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        data = super().to_dict()
        data.update({
            'status': self.status.value,
            'initiator_agent_id': self.initiator_agent_id,
            'messages_count': len(self.messages) if self.messages else 0
        })
        return data
    
    def add_message(self, content, message_type, sender_agent_id=None, message_metadata=None):
        """Add a message to this conversation"""
        message = Message(
            conversation_id=self.id,
            content=content,
            message_type=message_type,
            sender_agent_id=sender_agent_id,
            message_metadata=message_metadata
        )
        message.save()
        return message
    
    def get_messages_by_agent(self, agent_id):
        """Get all messages from a specific agent in this conversation"""
        return Message.query.filter_by(
            conversation_id=self.id,
            sender_agent_id=agent_id
        ).order_by(Message.created_at).all()
    
    def get_recent_messages(self, limit=10):
        """Get recent messages from this conversation"""
        return Message.query.filter_by(
            conversation_id=self.id
        ).order_by(Message.created_at.desc()).limit(limit).all()
    
    def complete_conversation(self):
        """Mark conversation as completed"""
        self.status = ConversationStatus.COMPLETED
        self.save()

class Message(BaseModel):
    """Individual message within a conversation"""
    __tablename__ = 'messages'
    
    # Message content and metadata
    content = db.Column(db.Text, nullable=False)
    message_type = db.Column(Enum(MessageType), nullable=False)
    
    # Message relationships
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False)
    conversation = db.relationship('Conversation', backref='messages')
    
    sender_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    sender_agent = db.relationship('Agent', backref='sent_messages')
    
    # Message metadata
    message_metadata = db.Column(db.JSON)  # Additional message metadata
    tokens_used = db.Column(db.Integer)  # Token count for LLM tracking
    response_time = db.Column(db.Float)  # Response time in seconds
    
    def __repr__(self):
        return f'<Message {self.id} ({self.message_type.value})>'
    
    def to_dict(self):
        """Convert message to dictionary"""
        data = super().to_dict()
        data.update({
            'message_type': self.message_type.value,
            'conversation_id': self.conversation_id,
            'sender_agent_id': self.sender_agent_id
        })
        return data 