"""
Draft model for tracking document draft versions
"""

from .base import db, BaseModel
from sqlalchemy import Enum
import enum

class DraftStatus(enum.Enum):
    """Enumeration for draft status"""
    DRAFT = "draft"
    REVIEW = "review"
    APPROVED = "approved"
    REJECTED = "rejected"
    ARCHIVED = "archived"

class DraftType(enum.Enum):
    """Enumeration for draft types"""
    EMAIL = "email"
    DOCUMENT = "document"
    RESPONSE = "response"
    REPORT = "report"
    OTHER = "other"

class Draft(BaseModel):
    """Draft model for tracking document versions"""
    __tablename__ = 'drafts'
    
    # Foreign key to task (as specified in requirements)
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'), nullable=False)
    task = db.relationship('Task', backref='drafts')
    
    # Version number (as specified in requirements)
    version = db.Column(db.Integer, nullable=False, default=1)
    
    # Content (as specified in requirements)
    content = db.Column(db.Text, nullable=False)
    
    # Additional fields for better draft management
    title = db.Column(db.String(200))
    draft_type = db.Column(Enum(DraftType), nullable=False, default=DraftType.OTHER)
    status = db.Column(Enum(DraftStatus), nullable=False, default=DraftStatus.DRAFT)
    
    # Author and reviewer tracking
    author_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    author_agent = db.relationship('Agent', foreign_keys=[author_agent_id], backref='authored_drafts')
    
    reviewer_agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=True)
    reviewer_agent = db.relationship('Agent', foreign_keys=[reviewer_agent_id], backref='reviewed_drafts')
    
    # Draft metadata
    word_count = db.Column(db.Integer)
    character_count = db.Column(db.Integer)
    
    # Review and feedback
    review_feedback = db.Column(db.Text)
    review_score = db.Column(db.Float)  # Score from 0.0 to 10.0
    
    # Parent draft relationship for version tracking
    parent_draft_id = db.Column(db.Integer, db.ForeignKey('drafts.id'), nullable=True)
    parent_draft = db.relationship('Draft', remote_side='Draft.id', backref='child_drafts')
    
    # Note: created_at is inherited from BaseModel for creation timestamp
    
    def __repr__(self):
        return f'<Draft {self.id} v{self.version} ({self.status.value})>'
    
    def to_dict(self):
        """Convert draft to dictionary"""
        data = super().to_dict()
        data.update({
            'task_id': self.task_id,
            'version': self.version,
            'draft_type': self.draft_type.value,
            'status': self.status.value,
            'author_agent_id': self.author_agent_id,
            'reviewer_agent_id': self.reviewer_agent_id,
            'parent_draft_id': self.parent_draft_id
        })
        return data
    
    def create_new_version(self, content, author_agent_id=None):
        """Create a new version of this draft"""
        new_version = Draft(
            task_id=self.task_id,
            version=self.version + 1,
            content=content,
            title=self.title,
            draft_type=self.draft_type,
            author_agent_id=author_agent_id or self.author_agent_id,
            parent_draft_id=self.id
        )
        new_version.save()
        return new_version
    
    def approve_draft(self, reviewer_agent_id, feedback=None, score=None):
        """Approve this draft"""
        self.status = DraftStatus.APPROVED
        self.reviewer_agent_id = reviewer_agent_id
        if feedback:
            self.review_feedback = feedback
        if score:
            self.review_score = score
        self.save()
    
    def reject_draft(self, reviewer_agent_id, feedback, score=None):
        """Reject this draft"""
        self.status = DraftStatus.REJECTED
        self.reviewer_agent_id = reviewer_agent_id
        self.review_feedback = feedback
        if score:
            self.review_score = score
        self.save()
    
    def get_latest_version_for_task(self, task_id):
        """Get the latest version of a draft for a specific task"""
        return Draft.query.filter_by(task_id=task_id).order_by(Draft.version.desc()).first()
    
    def calculate_content_stats(self):
        """Calculate and update word and character counts"""
        if self.content:
            self.character_count = len(self.content)
            self.word_count = len(self.content.split())
            self.save() 