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

class OrchestrationPattern(enum.Enum):
    """Orchestration patterns for analytics tracking"""
    ROUND_ROBIN = "round_robin"
    EXPERTISE_BASED = "expertise_based"
    HIERARCHICAL = "hierarchical"
    COLLABORATIVE = "collaborative"
    SEQUENTIAL = "sequential"
    DEMOCRATIC = "democratic"

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
    orchestration_pattern = db.Column(Enum(OrchestrationPattern))  # Pattern used
    
    # Enhanced tracking fields
    start_time = db.Column(db.DateTime)
    end_time = db.Column(db.DateTime)
    total_duration = db.Column(db.Float)  # Duration in seconds
    total_tokens = db.Column(db.Integer, default=0)
    total_messages = db.Column(db.Integer, default=0)
    participant_count = db.Column(db.Integer, default=0)
    
    # Performance metrics
    avg_response_time = db.Column(db.Float)
    effectiveness_score = db.Column(db.Float)  # 0-100 score
    engagement_score = db.Column(db.Float)  # 0-100 score
    
    def __repr__(self):
        return f'<Conversation {self.id} ({self.status.value})>'
    
    def to_dict(self):
        """Convert conversation to dictionary"""
        data = super().to_dict()
        data.update({
            'status': self.status.value if self.status else None,
            'orchestration_pattern': self.orchestration_pattern.value if self.orchestration_pattern else None,
            'initiator_agent_id': self.initiator_agent_id,
            'messages_count': len(self.messages) if hasattr(self, 'messages') and self.messages else 0,
            'total_duration': self.total_duration,
            'effectiveness_score': self.effectiveness_score,
            'engagement_score': self.engagement_score
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
        # Update message count
        self.total_messages = len(self.messages)
        self.save()
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
        """Mark conversation as completed and calculate final metrics"""
        from datetime import datetime
        self.status = ConversationStatus.COMPLETED
        self.end_time = datetime.utcnow()
        if self.start_time:
            self.total_duration = (self.end_time - self.start_time).total_seconds()
        self._calculate_performance_metrics()
        self.save()
    
    def _calculate_performance_metrics(self):
        """Calculate performance metrics for this conversation"""
        if not self.messages:
            return
            
        # Calculate average response time
        response_times = [msg.response_time for msg in self.messages if msg.response_time]
        if response_times:
            self.avg_response_time = sum(response_times) / len(response_times)
        
        # Calculate total tokens
        self.total_tokens = sum(msg.tokens_used or 0 for msg in self.messages)
        
        # Simple effectiveness score based on conversation completion and message variety
        agent_participation = len(set(msg.sender_agent_id for msg in self.messages if msg.sender_agent_id))
        self.participant_count = agent_participation
        
        # Effectiveness: 60% completion + 40% participation diversity
        completion_score = 60 if self.status == ConversationStatus.COMPLETED else 30
        participation_score = min(40, agent_participation * 10)  # Max 40 points for participation
        self.effectiveness_score = completion_score + participation_score
        
        # Engagement: Based on message frequency and response times
        if self.total_duration and self.total_duration > 0:
            message_frequency = self.total_messages / (self.total_duration / 60)  # messages per minute
            engagement_base = min(70, message_frequency * 20)  # Up to 70 points for frequency
            response_bonus = 30 if self.avg_response_time and self.avg_response_time < 10 else 15
            self.engagement_score = engagement_base + response_bonus
        else:
            self.engagement_score = 50  # Default score

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
    
    # Enhanced tracking fields
    agent_name = db.Column(db.String(100))  # Agent name for tracking
    message_length = db.Column(db.Integer)  # Character count
    sentiment_score = db.Column(db.Float)  # -1 to 1 sentiment analysis
    
    def __repr__(self):
        return f'<Message {self.id} ({self.message_type.value})>'
    
    def to_dict(self):
        """Convert message to dictionary"""
        data = super().to_dict()
        data.update({
            'message_type': self.message_type.value if self.message_type else None,
            'conversation_id': self.conversation_id,
            'sender_agent_id': self.sender_agent_id,
            'agent_name': self.agent_name,
            'message_length': self.message_length,
            'sentiment_score': self.sentiment_score
        })
        return data


class ConversationAnalytics(BaseModel):
    """Detailed analytics for conversation performance and insights"""
    __tablename__ = 'conversation_analytics'
    
    # Link to conversation
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'), nullable=False, unique=True)
    conversation = db.relationship('Conversation', backref='analytics')
    
    # Timing metrics
    total_duration = db.Column(db.Float)  # Total conversation duration in seconds
    avg_message_interval = db.Column(db.Float)  # Average time between messages
    fastest_response = db.Column(db.Float)  # Fastest agent response time
    slowest_response = db.Column(db.Float)  # Slowest agent response time
    
    # Content metrics
    total_characters = db.Column(db.Integer)  # Total character count
    avg_message_length = db.Column(db.Float)  # Average message length
    unique_words = db.Column(db.Integer)  # Unique word count
    vocabulary_richness = db.Column(db.Float)  # Unique words / total words
    
    # Participation metrics
    total_participants = db.Column(db.Integer)  # Number of participating agents
    most_active_agent = db.Column(db.String(100))  # Agent with most messages
    participation_balance = db.Column(db.Float)  # 0-1 score for balanced participation
    
    # Quality metrics
    error_count = db.Column(db.Integer, default=0)  # Number of error messages
    completion_status = db.Column(db.String(20))  # How the conversation ended
    goal_achievement = db.Column(db.Float)  # 0-100 score for goal achievement
    
    # AutoGen specific metrics
    orchestration_switches = db.Column(db.Integer, default=0)  # Number of pattern switches
    group_chat_efficiency = db.Column(db.Float)  # Efficiency score for group chats
    agent_collaboration_score = db.Column(db.Float)  # How well agents collaborated
    
    # Sentiment and engagement
    overall_sentiment = db.Column(db.Float)  # Average sentiment score
    sentiment_variance = db.Column(db.Float)  # Variance in sentiment
    engagement_peaks = db.Column(db.JSON)  # Timestamps of high engagement
    
    def __repr__(self):
        return f'<ConversationAnalytics {self.id} for conversation {self.conversation_id}>'
    
    def to_dict(self):
        """Convert analytics to dictionary"""
        data = super().to_dict()
        data.update({
            'conversation_id': self.conversation_id,
            'efficiency_score': self.calculate_efficiency_score(),
            'quality_score': self.calculate_quality_score()
        })
        return data
    
    def calculate_efficiency_score(self):
        """Calculate overall efficiency score (0-100)"""
        scores = []
        
        # Time efficiency (30%)
        if self.avg_message_interval and self.avg_message_interval > 0:
            time_score = min(100, 60 / self.avg_message_interval)  # Better if faster
            scores.append(time_score * 0.3)
        
        # Participation balance (25%)
        if self.participation_balance:
            scores.append(self.participation_balance * 100 * 0.25)
        
        # Goal achievement (45%)
        if self.goal_achievement:
            scores.append(self.goal_achievement * 0.45)
        
        return sum(scores) if scores else 0
    
    def calculate_quality_score(self):
        """Calculate overall quality score (0-100)"""
        scores = []
        
        # Error rate (30%)
        if self.error_count is not None and hasattr(self.conversation, 'total_messages'):
            error_rate = self.error_count / max(1, self.conversation.total_messages)
            error_score = max(0, 100 - (error_rate * 200))  # Penalize errors heavily
            scores.append(error_score * 0.3)
        
        # Vocabulary richness (20%)
        if self.vocabulary_richness:
            vocab_score = min(100, self.vocabulary_richness * 200)  # Rich vocabulary is good
            scores.append(vocab_score * 0.2)
        
        # Collaboration score (30%)
        if self.agent_collaboration_score:
            scores.append(self.agent_collaboration_score * 0.3)
        
        # Sentiment stability (20%)
        if self.overall_sentiment is not None and self.sentiment_variance is not None:
            sentiment_score = (self.overall_sentiment + 1) * 50  # Convert -1,1 to 0,100
            stability_penalty = self.sentiment_variance * 20  # Penalize high variance
            sentiment_final = max(0, sentiment_score - stability_penalty)
            scores.append(sentiment_final * 0.2)
        
        return sum(scores) if scores else 0 