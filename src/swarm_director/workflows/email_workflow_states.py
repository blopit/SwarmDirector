"""
Email Workflow State Management
Specialized state management for email workflows with email-specific states and context
"""

import logging
from typing import Dict, Any, Optional, List, Union
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

from .state_manager import WorkflowStatus, WorkflowState, WorkflowStateManager, StateTransition

logger = logging.getLogger(__name__)

class EmailWorkflowPhase(Enum):
    """Email workflow specific phases"""
    INTENT_CLASSIFICATION = "intent_classification"
    DRAFT_CREATION = "draft_creation"
    REVIEW_PHASE = "review_phase"
    CONSENSUS_BUILDING = "consensus_building"
    FINALIZATION = "finalization"
    DELIVERY_PREPARATION = "delivery_preparation"
    SMTP_DELIVERY = "smtp_delivery"
    DELIVERY_CONFIRMATION = "delivery_confirmation"
    
class EmailWorkflowType(Enum):
    """Types of email workflows"""
    IMMEDIATE_SEND = "immediate_send"
    DRAFT_REVIEW = "draft_review"
    CONTENT_CREATION = "content_creation"
    AUTOMATED_NOTIFICATION = "automated_notification"
    BULK_EMAIL = "bulk_email"

class EmailDeliveryStatus(Enum):
    """Email delivery status"""
    QUEUED = "queued"
    PROCESSING = "processing"
    SENT = "sent"
    DELIVERED = "delivered"
    BOUNCED = "bounced"
    FAILED = "failed"
    RETRYING = "retrying"

@dataclass
class EmailContext:
    """Email-specific context data"""
    recipient: Optional[str] = None
    sender: Optional[str] = None
    subject: Optional[str] = None
    body: Optional[str] = None
    html_body: Optional[str] = None
    priority: str = "normal"
    template_name: Optional[str] = None
    template_data: Dict[str, Any] = field(default_factory=dict)
    
    # Email metadata
    message_id: Optional[str] = None
    thread_id: Optional[str] = None
    reply_to: Optional[str] = None
    cc: List[str] = field(default_factory=list)
    bcc: List[str] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    
    # Delivery tracking
    delivery_status: EmailDeliveryStatus = EmailDeliveryStatus.QUEUED
    delivery_attempts: int = 0
    last_delivery_attempt: Optional[datetime] = None
    delivery_error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'recipient': self.recipient,
            'sender': self.sender,
            'subject': self.subject,
            'body': self.body,
            'html_body': self.html_body,
            'priority': self.priority,
            'template_name': self.template_name,
            'template_data': self.template_data,
            'message_id': self.message_id,
            'thread_id': self.thread_id,
            'reply_to': self.reply_to,
            'cc': self.cc,
            'bcc': self.bcc,
            'attachments': self.attachments,
            'delivery_status': self.delivery_status.value,
            'delivery_attempts': self.delivery_attempts,
            'last_delivery_attempt': self.last_delivery_attempt.isoformat() if self.last_delivery_attempt else None,
            'delivery_error': self.delivery_error
        }

@dataclass
class ReviewContext:
    """Review process context"""
    review_agents: List[str] = field(default_factory=list)
    reviews_completed: List[Dict[str, Any]] = field(default_factory=list)
    consensus_threshold: float = 0.75
    current_consensus_score: Optional[float] = None
    review_deadline: Optional[datetime] = None
    review_round: int = 1
    max_review_rounds: int = 3
    
    # Review content tracking
    original_content: Optional[str] = None
    current_content: Optional[str] = None
    suggested_changes: List[Dict[str, Any]] = field(default_factory=list)
    approved_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'review_agents': self.review_agents,
            'reviews_completed': self.reviews_completed,
            'consensus_threshold': self.consensus_threshold,
            'current_consensus_score': self.current_consensus_score,
            'review_deadline': self.review_deadline.isoformat() if self.review_deadline else None,
            'review_round': self.review_round,
            'max_review_rounds': self.max_review_rounds,
            'original_content': self.original_content,
            'current_content': self.current_content,
            'suggested_changes': self.suggested_changes,
            'approved_changes': self.approved_changes
        }

@dataclass
class EmailWorkflowState(WorkflowState):
    """
    Extended workflow state for email workflows with email-specific context
    """
    # Email workflow specific fields
    workflow_type: EmailWorkflowType = EmailWorkflowType.IMMEDIATE_SEND
    current_phase: EmailWorkflowPhase = EmailWorkflowPhase.INTENT_CLASSIFICATION
    
    # Email context
    email_context: EmailContext = field(default_factory=EmailContext)
    review_context: Optional[ReviewContext] = None
    
    # Agent assignments
    assigned_director: Optional[str] = None
    assigned_communications_dept: Optional[str] = None
    assigned_email_agent: Optional[str] = None
    assigned_review_agents: List[str] = field(default_factory=list)
    
    # Phase tracking
    phase_history: List[Dict[str, Any]] = field(default_factory=list)
    phase_durations: Dict[str, float] = field(default_factory=dict)
    
    # Email workflow metrics
    review_iterations: int = 0
    content_revisions: int = 0
    delivery_attempts: int = 0
    
    def advance_phase(self, new_phase: EmailWorkflowPhase, agent_name: str = None, 
                     notes: str = None, metadata: Dict[str, Any] = None):
        """Advance to next workflow phase"""
        phase_transition = {
            'from_phase': self.current_phase.value,
            'to_phase': new_phase.value,
            'timestamp': datetime.utcnow().isoformat(),
            'agent_name': agent_name,
            'notes': notes,
            'metadata': metadata or {}
        }
        
        self.phase_history.append(phase_transition)
        
        # Calculate phase duration
        if self.phase_history:
            prev_phase_start = datetime.fromisoformat(self.phase_history[-2]['timestamp']) if len(self.phase_history) > 1 else self.created_at
            phase_duration = (datetime.utcnow() - prev_phase_start).total_seconds()
            self.phase_durations[self.current_phase.value] = phase_duration
        
        self.current_phase = new_phase
        self.updated_at = datetime.utcnow()
        
        logger.info(f"Email workflow {self.workflow_id} advanced to phase {new_phase.value}")
    
    def add_review_result(self, agent_name: str, review_result: Dict[str, Any]):
        """Add review result to the review context"""
        if not self.review_context:
            self.review_context = ReviewContext()
        
        review_data = {
            'agent_name': agent_name,
            'timestamp': datetime.utcnow().isoformat(),
            'result': review_result
        }
        
        self.review_context.reviews_completed.append(review_data)
        self.review_iterations += 1
    
    def update_email_content(self, new_content: str, agent_name: str = None, 
                           content_type: str = "body"):
        """Update email content and track revisions"""
        if content_type == "body":
            self.email_context.body = new_content
        elif content_type == "html_body":
            self.email_context.html_body = new_content
        elif content_type == "subject":
            self.email_context.subject = new_content
        
        self.content_revisions += 1
        self.updated_at = datetime.utcnow()
        
        # Log content change
        self.add_transition(
            self.status,
            agent_name=agent_name,
            reason=f"Content updated: {content_type}",
            metadata={'content_type': content_type, 'revision': self.content_revisions}
        )
    
    def update_delivery_status(self, status: EmailDeliveryStatus, error_msg: str = None):
        """Update email delivery status"""
        self.email_context.delivery_status = status
        self.email_context.last_delivery_attempt = datetime.utcnow()
        
        if status in [EmailDeliveryStatus.FAILED, EmailDeliveryStatus.BOUNCED, EmailDeliveryStatus.RETRYING]:
            self.email_context.delivery_attempts += 1
            if error_msg:
                self.email_context.delivery_error = error_msg
        
        self.delivery_attempts = self.email_context.delivery_attempts
        self.updated_at = datetime.utcnow()
    
    def get_workflow_progress(self) -> Dict[str, Any]:
        """Get detailed workflow progress information"""
        total_phases = len(EmailWorkflowPhase)
        current_phase_index = list(EmailWorkflowPhase).index(self.current_phase)
        progress_percentage = (current_phase_index / total_phases) * 100
        
        return {
            'current_phase': self.current_phase.value,
            'phase_index': current_phase_index,
            'total_phases': total_phases,
            'progress_percentage': progress_percentage,
            'phases_completed': current_phase_index,
            'phases_remaining': total_phases - current_phase_index,
            'workflow_type': self.workflow_type.value,
            'delivery_status': self.email_context.delivery_status.value,
            'review_iterations': self.review_iterations,
            'content_revisions': self.content_revisions,
            'delivery_attempts': self.delivery_attempts
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary including email-specific data"""
        base_dict = super().to_dict()
        
        email_specific = {
            'workflow_type': self.workflow_type.value,
            'current_phase': self.current_phase.value,
            'email_context': self.email_context.to_dict(),
            'review_context': self.review_context.to_dict() if self.review_context else None,
            'assigned_director': self.assigned_director,
            'assigned_communications_dept': self.assigned_communications_dept,
            'assigned_email_agent': self.assigned_email_agent,
            'assigned_review_agents': self.assigned_review_agents,
            'phase_history': self.phase_history,
            'phase_durations': self.phase_durations,
            'review_iterations': self.review_iterations,
            'content_revisions': self.content_revisions,
            'delivery_attempts': self.delivery_attempts,
            'workflow_progress': self.get_workflow_progress()
        }
        
        base_dict.update(email_specific)
        return base_dict

class EmailWorkflowStateManager(WorkflowStateManager):
    """
    Specialized state manager for email workflows
    """
    
    # Valid phase transitions for email workflows
    VALID_PHASE_TRANSITIONS = {
        EmailWorkflowPhase.INTENT_CLASSIFICATION: [
            EmailWorkflowPhase.DRAFT_CREATION,
            EmailWorkflowPhase.DELIVERY_PREPARATION  # For simple automated emails
        ],
        EmailWorkflowPhase.DRAFT_CREATION: [
            EmailWorkflowPhase.REVIEW_PHASE,
            EmailWorkflowPhase.FINALIZATION  # For immediate send workflows
        ],
        EmailWorkflowPhase.REVIEW_PHASE: [
            EmailWorkflowPhase.CONSENSUS_BUILDING,
            EmailWorkflowPhase.DRAFT_CREATION  # Back to draft if major issues
        ],
        EmailWorkflowPhase.CONSENSUS_BUILDING: [
            EmailWorkflowPhase.FINALIZATION,
            EmailWorkflowPhase.REVIEW_PHASE  # Another review round
        ],
        EmailWorkflowPhase.FINALIZATION: [
            EmailWorkflowPhase.DELIVERY_PREPARATION
        ],
        EmailWorkflowPhase.DELIVERY_PREPARATION: [
            EmailWorkflowPhase.SMTP_DELIVERY
        ],
        EmailWorkflowPhase.SMTP_DELIVERY: [
            EmailWorkflowPhase.DELIVERY_CONFIRMATION,
            EmailWorkflowPhase.DELIVERY_PREPARATION  # Retry on failure
        ],
        EmailWorkflowPhase.DELIVERY_CONFIRMATION: []  # Terminal state
    }
    
    def __init__(self):
        super().__init__()
        self._email_workflows: Dict[str, EmailWorkflowState] = {}
    
    def create_email_workflow(self, workflow_id: str, workflow_type: EmailWorkflowType,
                             email_context: EmailContext = None, 
                             input_data: Dict[str, Any] = None) -> EmailWorkflowState:
        """Create a new email workflow state"""
        with self._lock:
            if workflow_id in self._states:
                raise ValueError(f"Workflow {workflow_id} already exists")
            
            # Calculate total steps based on workflow type
            total_steps = self._calculate_total_steps(workflow_type)
            
            email_state = EmailWorkflowState(
                workflow_id=workflow_id,
                workflow_type=workflow_type,
                email_context=email_context or EmailContext(),
                input_data=input_data or {},
                total_steps=total_steps
            )
            
            self._states[workflow_id] = email_state
            self._email_workflows[workflow_id] = email_state
            
            logger.info(f"Created email workflow: {workflow_id} (type: {workflow_type.value})")
            self._notify_listeners(workflow_id, email_state)
            return email_state
    
    def _calculate_total_steps(self, workflow_type: EmailWorkflowType) -> int:
        """Calculate total steps based on workflow type"""
        base_steps = len(EmailWorkflowPhase)
        
        if workflow_type == EmailWorkflowType.IMMEDIATE_SEND:
            return base_steps - 2  # Skip review phases
        elif workflow_type == EmailWorkflowType.DRAFT_REVIEW:
            return base_steps  # All phases
        elif workflow_type == EmailWorkflowType.CONTENT_CREATION:
            return base_steps - 1  # Skip delivery confirmation
        elif workflow_type == EmailWorkflowType.AUTOMATED_NOTIFICATION:
            return base_steps - 3  # Skip review and consensus phases
        else:
            return base_steps
    
    def advance_workflow_phase(self, workflow_id: str, new_phase: EmailWorkflowPhase,
                              agent_name: str = None, notes: str = None,
                              metadata: Dict[str, Any] = None) -> bool:
        """Advance workflow to next phase with validation"""
        with self._lock:
            email_state = self._email_workflows.get(workflow_id)
            if not email_state:
                return False
            
            # Validate phase transition
            current_phase = email_state.current_phase
            if new_phase not in self.VALID_PHASE_TRANSITIONS.get(current_phase, []):
                logger.warning(f"Invalid phase transition from {current_phase.value} to {new_phase.value}")
                return False
            
            email_state.advance_phase(new_phase, agent_name, notes, metadata)
            
            # Update completed steps
            phase_index = list(EmailWorkflowPhase).index(new_phase)
            email_state.completed_steps = phase_index
            
            self._notify_listeners(workflow_id, email_state)
            return True
    
    def get_email_workflow(self, workflow_id: str) -> Optional[EmailWorkflowState]:
        """Get email workflow state"""
        return self._email_workflows.get(workflow_id)
    
    def update_email_context(self, workflow_id: str, **email_updates) -> bool:
        """Update email context data"""
        with self._lock:
            email_state = self._email_workflows.get(workflow_id)
            if not email_state:
                return False
            
            # Update email context fields
            for field, value in email_updates.items():
                if hasattr(email_state.email_context, field):
                    setattr(email_state.email_context, field, value)
            
            email_state.updated_at = datetime.utcnow()
            self._notify_listeners(workflow_id, email_state)
            return True
    
    def add_review_result(self, workflow_id: str, agent_name: str, 
                         review_result: Dict[str, Any]) -> bool:
        """Add review result to email workflow"""
        with self._lock:
            email_state = self._email_workflows.get(workflow_id)
            if not email_state:
                return False
            
            email_state.add_review_result(agent_name, review_result)
            self._notify_listeners(workflow_id, email_state)
            return True
    
    def get_workflows_by_phase(self, phase: EmailWorkflowPhase) -> List[EmailWorkflowState]:
        """Get all workflows in a specific phase"""
        with self._lock:
            return [state for state in self._email_workflows.values() 
                   if state.current_phase == phase]
    
    def get_workflows_by_type(self, workflow_type: EmailWorkflowType) -> List[EmailWorkflowState]:
        """Get all workflows of a specific type"""
        with self._lock:
            return [state for state in self._email_workflows.values() 
                   if state.workflow_type == workflow_type]
    
    def get_email_workflow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive email workflow statistics"""
        with self._lock:
            total_workflows = len(self._email_workflows)
            
            if total_workflows == 0:
                return {'total_workflows': 0}
            
            # Count by workflow type
            type_counts = {}
            for workflow_type in EmailWorkflowType:
                type_counts[workflow_type.value] = len(self.get_workflows_by_type(workflow_type))
            
            # Count by phase
            phase_counts = {}
            for phase in EmailWorkflowPhase:
                phase_counts[phase.value] = len(self.get_workflows_by_phase(phase))
            
            # Count by status
            status_counts = {}
            for status in WorkflowStatus:
                status_counts[status.value] = len([w for w in self._email_workflows.values() 
                                                 if w.status == status])
            
            # Calculate averages
            total_revisions = sum(w.content_revisions for w in self._email_workflows.values())
            total_review_iterations = sum(w.review_iterations for w in self._email_workflows.values())
            total_delivery_attempts = sum(w.delivery_attempts for w in self._email_workflows.values())
            
            avg_revisions = total_revisions / total_workflows if total_workflows > 0 else 0
            avg_review_iterations = total_review_iterations / total_workflows if total_workflows > 0 else 0
            avg_delivery_attempts = total_delivery_attempts / total_workflows if total_workflows > 0 else 0
            
            return {
                'total_workflows': total_workflows,
                'type_distribution': type_counts,
                'phase_distribution': phase_counts,
                'status_distribution': status_counts,
                'averages': {
                    'content_revisions': avg_revisions,
                    'review_iterations': avg_review_iterations,
                    'delivery_attempts': avg_delivery_attempts
                },
                'totals': {
                    'content_revisions': total_revisions,
                    'review_iterations': total_review_iterations,
                    'delivery_attempts': total_delivery_attempts
                }
            }