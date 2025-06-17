"""
Email Workflow Coordinator
Integrates all email workflow agents with the state management system
"""

import logging
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from ..agents.director import DirectorAgent
from ..agents.communications_dept import CommunicationsDept
from ..agents.email_agent import EmailAgent
from ..agents.draft_review_agent import DraftReviewAgent
from ..models.task import Task, TaskType
from ..models.email_message import EmailMessage

# Import the new state management system
from .persistent_state_manager import PersistentEmailWorkflowStateManager
from .email_workflow_states import (
    EmailWorkflowType, EmailWorkflowPhase, EmailContext, ReviewContext, EmailDeliveryStatus
)
from .global_context import (
    global_context, get_workflow_logger, with_workflow_context, auto_advance_phase,
    advance_workflow_phase, update_workflow_context, get_current_workflow, workflow_utils
)
from .state_manager import WorkflowStatus

logger = get_workflow_logger(__name__)

class EmailWorkflowCoordinator:
    """
    Coordinates the complete email workflow using the state management system
    Integrates DirectorAgent, CommunicationsDept, EmailAgent, and DraftReviewAgent
    """
    
    def __init__(self, director_agent: DirectorAgent = None):
        self.director_agent = director_agent
        self.state_manager = PersistentEmailWorkflowStateManager()
        
        # Initialize global context
        global_context.initialize(self.state_manager)
        
        # Agent references (will be set via director agent)
        self.communications_dept: Optional[CommunicationsDept] = None
        self.email_agent: Optional[EmailAgent] = None
        self.review_agents: List[DraftReviewAgent] = []
        
        # Workflow configuration
        self.default_review_threshold = 0.75
        self.max_review_rounds = 3
        self.auto_finalize_on_consensus = True
        
        logger.info("Email Workflow Coordinator initialized")
    
    def set_agents(self, communications_dept: CommunicationsDept = None,
                   email_agent: EmailAgent = None, review_agents: List[DraftReviewAgent] = None):
        """Set agent references for the coordinator"""
        self.communications_dept = communications_dept
        self.email_agent = email_agent
        self.review_agents = review_agents or []
        
        logger.info(f"Configured agents: CommDept={bool(communications_dept)}, EmailAgent={bool(email_agent)}, ReviewAgents={len(self.review_agents)}")
    
    @with_workflow_context('workflow_id')
    def execute_email_workflow(self, task: Task, workflow_type: EmailWorkflowType = EmailWorkflowType.DRAFT_REVIEW) -> Dict[str, Any]:
        """
        Execute complete email workflow from task to delivery
        """
        # Generate unique workflow ID
        workflow_id = f"email_workflow_{uuid.uuid4().hex[:8]}_{int(datetime.now().timestamp())}"
        
        try:
            # Phase 1: Intent Classification & Workflow Initialization
            result = self._phase_1_intent_classification(workflow_id, task, workflow_type)
            if not result['success']:
                return result
            
            # Phase 2: Draft Creation
            result = self._phase_2_draft_creation(workflow_id, task)
            if not result['success']:
                return result
            
            # Phase 3-4: Review Process (if needed)
            if workflow_type in [EmailWorkflowType.DRAFT_REVIEW, EmailWorkflowType.CONTENT_CREATION]:
                result = self._phase_3_4_review_process(workflow_id)
                if not result['success']:
                    return result
            
            # Phase 5: Finalization
            result = self._phase_5_finalization(workflow_id)
            if not result['success']:
                return result
            
            # Phase 6-7: Delivery
            result = self._phase_6_7_delivery(workflow_id)
            if not result['success']:
                return result
            
            # Phase 8: Delivery Confirmation
            result = self._phase_8_delivery_confirmation(workflow_id)
            
            return {
                'success': True,
                'workflow_id': workflow_id,
                'message': 'Email workflow completed successfully',
                'final_phase': EmailWorkflowPhase.DELIVERY_CONFIRMATION.value,
                'result': result
            }
            
        except Exception as e:
            logger.error(f"Email workflow failed: {e}")
            self._handle_workflow_error(workflow_id, str(e))
            return {
                'success': False,
                'workflow_id': workflow_id,
                'error': str(e),
                'message': 'Email workflow failed'
            }
    
    @auto_advance_phase(EmailWorkflowPhase.DRAFT_CREATION, "EmailWorkflowCoordinator")
    def _phase_1_intent_classification(self, workflow_id: str, task: Task, workflow_type: EmailWorkflowType) -> Dict[str, Any]:
        """Phase 1: Intent Classification & Workflow Initialization"""
        logger.info("Starting Phase 1: Intent Classification")
        
        # Create email context from task
        email_context = EmailContext(
            subject=task.title or "Email Task",
            priority="normal"
        )
        
        # Extract email details from task if available
        if hasattr(task, 'email_recipient'):
            email_context.recipient = task.email_recipient
        if hasattr(task, 'email_sender'):
            email_context.sender = task.email_sender
        
        # Create workflow state
        workflow_state = self.state_manager.create_email_workflow(
            workflow_id=workflow_id,
            workflow_type=workflow_type,
            email_context=email_context,
            input_data={
                'task_id': task.id if hasattr(task, 'id') else None,
                'task_title': task.title,
                'task_description': task.description,
                'task_type': task.task_type.value if hasattr(task, 'task_type') else 'email',
                'created_at': datetime.now().isoformat()
            }
        )
        
        # Use director agent for intent classification if available
        if self.director_agent:
            try:
                intent_result = self.director_agent.classify_intent_with_confidence(task)
                intent, confidence = intent_result
                
                # Update workflow context with classification results
                update_workflow_context(
                    classified_intent=intent,
                    classification_confidence=confidence,
                    director_agent=self.director_agent.agent.name if hasattr(self.director_agent, 'agent') else 'DirectorAgent'
                )
                
                logger.info(f"Intent classified as '{intent}' with confidence {confidence}")
                
            except Exception as e:
                logger.warning(f"Intent classification failed, using default: {e}")
                update_workflow_context(
                    classified_intent='communications',
                    classification_confidence=0.5,
                    classification_error=str(e)
                )
        
        # Set workflow as running
        self.state_manager.update_workflow_status(
            workflow_id, WorkflowStatus.RUNNING, 
            agent_name="EmailWorkflowCoordinator", 
            reason="Workflow started"
        )
        
        return {'success': True, 'phase': 'intent_classification_complete'}
    
    @auto_advance_phase(EmailWorkflowPhase.REVIEW_PHASE, "CommunicationsDept")
    def _phase_2_draft_creation(self, workflow_id: str, task: Task) -> Dict[str, Any]:
        """Phase 2: Draft Creation"""
        logger.info("Starting Phase 2: Draft Creation")
        
        workflow_state = get_current_workflow()
        if not workflow_state:
            return {'success': False, 'error': 'No workflow state available'}
        
        # Use CommunicationsDept for draft creation
        if self.communications_dept:
            try:
                # Execute draft creation task
                draft_result = self.communications_dept.execute_task(task)
                
                if draft_result.get('status') == 'success':
                    # Extract email content from result
                    email_content = draft_result.get('result', {})
                    
                    # Update email context with draft content
                    update_workflow_context(
                        body=email_content.get('body', ''),
                        html_body=email_content.get('html_body', ''),
                        subject=email_content.get('subject', workflow_state.email_context.subject),
                        template_name=email_content.get('template_name'),
                        template_data=email_content.get('template_data', {}),
                        assigned_communications_dept=self.communications_dept.agent.name if hasattr(self.communications_dept, 'agent') else 'CommunicationsDept'
                    )
                    
                    # Track content creation
                    workflow_state.update_email_content(
                        email_content.get('body', ''), 
                        agent_name="CommunicationsDept",
                        content_type="body"
                    )
                    
                    if email_content.get('subject'):
                        workflow_state.update_email_content(
                            email_content.get('subject'), 
                            agent_name="CommunicationsDept",
                            content_type="subject"
                        )
                    
                    logger.info("Draft creation completed successfully")
                    return {'success': True, 'phase': 'draft_creation_complete', 'content': email_content}
                else:
                    error_msg = draft_result.get('error', 'Draft creation failed')
                    logger.error(f"Draft creation failed: {error_msg}")
                    return {'success': False, 'error': error_msg}
                    
            except Exception as e:
                logger.error(f"Error in draft creation: {e}")
                return {'success': False, 'error': str(e)}
        else:
            # Fallback: create basic draft
            logger.warning("No CommunicationsDept available, creating basic draft")
            basic_content = {
                'subject': task.title or 'Email Subject',
                'body': task.description or 'Email content',
                'html_body': f'<p>{task.description or "Email content"}</p>'
            }
            
            update_workflow_context(**basic_content)
            return {'success': True, 'phase': 'draft_creation_complete', 'content': basic_content}
    
    @auto_advance_phase(EmailWorkflowPhase.CONSENSUS_BUILDING, "ReviewProcess")
    def _phase_3_4_review_process(self, workflow_id: str) -> Dict[str, Any]:
        """Phase 3-4: Review Phase & Consensus Building"""
        logger.info("Starting Phase 3-4: Review Process")
        
        workflow_state = get_current_workflow()
        if not workflow_state:
            return {'success': False, 'error': 'No workflow state available'}
        
        # Initialize review context if not exists
        if not workflow_state.review_context:
            workflow_state.review_context = ReviewContext(
                consensus_threshold=self.default_review_threshold,
                max_review_rounds=self.max_review_rounds,
                original_content=workflow_state.email_context.body,
                current_content=workflow_state.email_context.body
            )
        
        # Set review agents
        review_agent_names = [agent.agent.name if hasattr(agent, 'agent') else f'ReviewAgent_{i}' 
                             for i, agent in enumerate(self.review_agents)]
        workflow_state.review_context.review_agents = review_agent_names
        
        # Conduct review rounds
        for round_num in range(1, self.max_review_rounds + 1):
            workflow_state.review_context.review_round = round_num
            
            logger.info(f"Starting review round {round_num}")
            
            # Collect reviews from all review agents
            round_reviews = []
            for review_agent in self.review_agents:
                try:
                    # Create task for review
                    review_task = Task(
                        title=f"Review Email Draft - Round {round_num}",
                        description=f"Review the current email draft:\n\nSubject: {workflow_state.email_context.subject}\n\nBody:\n{workflow_state.email_context.body}",
                        task_type=TaskType.COMMUNICATION
                    )
                    
                    review_result = review_agent.execute_task(review_task)
                    
                    if review_result.get('status') == 'success':
                        review_data = review_result.get('result', {})
                        round_reviews.append({
                            'agent': review_agent.agent.name if hasattr(review_agent, 'agent') else 'ReviewAgent',
                            'approved': review_data.get('approved', False),
                            'score': review_data.get('score', 0.5),
                            'feedback': review_data.get('feedback', ''),
                            'suggested_changes': review_data.get('suggested_changes', [])
                        })
                    
                except Exception as e:
                    logger.error(f"Review agent error: {e}")
                    round_reviews.append({
                        'agent': 'ErrorAgent',
                        'approved': False,
                        'score': 0.0,
                        'feedback': f'Review failed: {e}',
                        'suggested_changes': []
                    })
            
            # Calculate consensus score
            if round_reviews:
                consensus_score = sum(review['score'] for review in round_reviews) / len(round_reviews)
                workflow_state.review_context.current_consensus_score = consensus_score
                
                # Add reviews to workflow state
                for review in round_reviews:
                    self.state_manager.add_review_result(workflow_id, review['agent'], review)
                
                logger.info(f"Round {round_num} consensus score: {consensus_score}")
                
                # Check if consensus achieved
                if consensus_score >= self.default_review_threshold:
                    logger.info(f"Consensus achieved with score {consensus_score}")
                    break
                
                # Apply suggested changes if below threshold and not final round
                if round_num < self.max_review_rounds:
                    self._apply_review_suggestions(workflow_state, round_reviews)
            else:
                logger.warning("No review results collected")
                break
        
        # Finalize review process
        final_consensus = workflow_state.review_context.current_consensus_score or 0.0
        
        if final_consensus >= self.default_review_threshold:
            logger.info("Review process completed with consensus")
            return {'success': True, 'phase': 'review_complete', 'consensus_score': final_consensus}
        else:
            logger.warning(f"Review process completed without consensus (score: {final_consensus})")
            if self.auto_finalize_on_consensus:
                return {'success': True, 'phase': 'review_complete', 'consensus_score': final_consensus, 'warning': 'No consensus achieved'}
            else:
                return {'success': False, 'error': 'Review consensus not achieved', 'consensus_score': final_consensus}
    
    def _apply_review_suggestions(self, workflow_state, reviews: List[Dict[str, Any]]):
        """Apply review suggestions to improve content"""
        logger.info("Applying review suggestions")
        
        # Simple implementation: concatenate all feedback
        all_feedback = []
        all_suggestions = []
        
        for review in reviews:
            if review['feedback']:
                all_feedback.append(f"- {review['feedback']}")
            all_suggestions.extend(review.get('suggested_changes', []))
        
        # Update workflow context with feedback
        update_workflow_context(
            review_feedback='\n'.join(all_feedback),
            suggested_changes=all_suggestions,
            review_round=workflow_state.review_context.review_round
        )
        
        # In a real implementation, this would use AI to apply suggestions
        # For now, we just log them
        logger.info(f"Collected feedback: {all_feedback}")
        logger.info(f"Collected suggestions: {all_suggestions}")
    
    @auto_advance_phase(EmailWorkflowPhase.DELIVERY_PREPARATION, "EmailWorkflowCoordinator")
    def _phase_5_finalization(self, workflow_id: str) -> Dict[str, Any]:
        """Phase 5: Finalization"""
        logger.info("Starting Phase 5: Finalization")
        
        workflow_state = get_current_workflow()
        if not workflow_state:
            return {'success': False, 'error': 'No workflow state available'}
        
        # Validate email content
        if not workflow_state.email_context.body:
            return {'success': False, 'error': 'No email body content available'}
        
        if not workflow_state.email_context.subject:
            return {'success': False, 'error': 'No email subject available'}
        
        # Set final email properties
        update_workflow_context(
            finalized_at=datetime.now().isoformat(),
            delivery_status=EmailDeliveryStatus.QUEUED.value
        )
        
        logger.info("Email finalization completed")
        return {'success': True, 'phase': 'finalization_complete'}
    
    @auto_advance_phase(EmailWorkflowPhase.SMTP_DELIVERY, "EmailAgent")
    def _phase_6_7_delivery(self, workflow_id: str) -> Dict[str, Any]:
        """Phase 6-7: Delivery Preparation & SMTP Delivery"""
        logger.info("Starting Phase 6-7: Delivery")
        
        workflow_state = get_current_workflow()
        if not workflow_state:
            return {'success': False, 'error': 'No workflow state available'}
        
        # Update delivery status
        workflow_state.update_delivery_status(EmailDeliveryStatus.PROCESSING)
        
        # Use EmailAgent for delivery
        if self.email_agent:
            try:
                # Prepare email message
                email_data = {
                    'recipient': workflow_state.email_context.recipient,
                    'sender': workflow_state.email_context.sender,
                    'subject': workflow_state.email_context.subject,
                    'body': workflow_state.email_context.body,
                    'html_body': workflow_state.email_context.html_body,
                    'cc': workflow_state.email_context.cc,
                    'bcc': workflow_state.email_context.bcc,
                    'priority': workflow_state.email_context.priority
                }
                
                # Create task for email agent
                delivery_task = Task(
                    title="Email Delivery",
                    description=f"Deliver email: {workflow_state.email_context.subject}",
                    task_type=TaskType.COMMUNICATION
                )
                
                # Execute delivery
                delivery_result = self.email_agent.execute_task(delivery_task)
                
                if delivery_result.get('status') == 'success':
                    # Update delivery status and context
                    workflow_state.update_delivery_status(EmailDeliveryStatus.SENT)
                    
                    delivery_data = delivery_result.get('result', {})
                    update_workflow_context(
                        message_id=delivery_data.get('message_id'),
                        delivery_timestamp=datetime.now().isoformat(),
                        assigned_email_agent=self.email_agent.agent.name if hasattr(self.email_agent, 'agent') else 'EmailAgent'
                    )
                    
                    logger.info("Email delivered successfully")
                    return {'success': True, 'phase': 'delivery_complete', 'message_id': delivery_data.get('message_id')}
                else:
                    error_msg = delivery_result.get('error', 'Email delivery failed')
                    workflow_state.update_delivery_status(EmailDeliveryStatus.FAILED, error_msg)
                    logger.error(f"Email delivery failed: {error_msg}")
                    return {'success': False, 'error': error_msg}
                    
            except Exception as e:
                workflow_state.update_delivery_status(EmailDeliveryStatus.FAILED, str(e))
                logger.error(f"Error in email delivery: {e}")
                return {'success': False, 'error': str(e)}
        else:
            # Simulation mode
            logger.warning("No EmailAgent available, simulating delivery")
            workflow_state.update_delivery_status(EmailDeliveryStatus.SENT)
            
            simulated_message_id = f"sim_{uuid.uuid4().hex[:8]}"
            update_workflow_context(
                message_id=simulated_message_id,
                delivery_timestamp=datetime.now().isoformat(),
                delivery_mode='simulation'
            )
            
            return {'success': True, 'phase': 'delivery_complete', 'message_id': simulated_message_id, 'mode': 'simulation'}
    
    def _phase_8_delivery_confirmation(self, workflow_id: str) -> Dict[str, Any]:
        """Phase 8: Delivery Confirmation"""
        logger.info("Starting Phase 8: Delivery Confirmation")
        
        workflow_state = get_current_workflow()
        if not workflow_state:
            return {'success': False, 'error': 'No workflow state available'}
        
        # Advance to final phase
        advance_workflow_phase(EmailWorkflowPhase.DELIVERY_CONFIRMATION, "EmailWorkflowCoordinator", "Workflow completed")
        
        # Update final workflow status
        self.state_manager.update_workflow_status(
            workflow_id, WorkflowStatus.COMPLETED,
            agent_name="EmailWorkflowCoordinator",
            reason="Email workflow completed successfully"
        )
        
        # Set completion data
        update_workflow_context(
            completed_at=datetime.now().isoformat(),
            final_status='completed'
        )
        
        # Get final statistics
        workflow_progress = workflow_state.get_workflow_progress()
        
        logger.info("Email workflow completed successfully")
        return {
            'success': True, 
            'phase': 'delivery_confirmation_complete',
            'workflow_id': workflow_id,
            'progress': workflow_progress,
            'delivery_status': workflow_state.email_context.delivery_status.value,
            'total_revisions': workflow_state.content_revisions,
            'review_iterations': workflow_state.review_iterations
        }
    
    def _handle_workflow_error(self, workflow_id: str, error_msg: str):
        """Handle workflow errors"""
        logger.error(f"Workflow error: {error_msg}")
        
        try:
            # Update workflow status to failed
            self.state_manager.update_workflow_status(
                workflow_id, WorkflowStatus.FAILED,
                agent_name="EmailWorkflowCoordinator",
                reason=f"Workflow failed: {error_msg}"
            )
            
            # Update context with error information
            update_workflow_context(
                error_message=error_msg,
                failed_at=datetime.now().isoformat(),
                final_status='failed'
            )
            
        except Exception as e:
            logger.error(f"Error handling workflow error: {e}")
    
    def get_workflow_status(self, workflow_id: str) -> Dict[str, Any]:
        """Get comprehensive workflow status"""
        workflow_state = self.state_manager.get_email_workflow(workflow_id)
        if not workflow_state:
            return {'error': 'Workflow not found'}
        
        return {
            'workflow_id': workflow_id,
            'status': workflow_state.status.value,
            'current_phase': workflow_state.current_phase.value,
            'workflow_type': workflow_state.workflow_type.value,
            'progress': workflow_state.get_workflow_progress(),
            'email_context': workflow_state.email_context.to_dict(),
            'review_context': workflow_state.review_context.to_dict() if workflow_state.review_context else None,
            'created_at': workflow_state.created_at.isoformat() if workflow_state.created_at else None,
            'updated_at': workflow_state.updated_at.isoformat() if workflow_state.updated_at else None,
            'agent_assignments': {
                'director': workflow_state.assigned_director,
                'communications_dept': workflow_state.assigned_communications_dept,
                'email_agent': workflow_state.assigned_email_agent,
                'review_agents': workflow_state.assigned_review_agents
            },
            'metrics': {
                'review_iterations': workflow_state.review_iterations,
                'content_revisions': workflow_state.content_revisions,
                'delivery_attempts': workflow_state.delivery_attempts
            }
        }
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        active_workflows = []
        
        for workflow_id, state in self.state_manager._email_workflows.items():
            if state.status in [WorkflowStatus.PENDING, WorkflowStatus.RUNNING, WorkflowStatus.PAUSED]:
                active_workflows.append(self.get_workflow_status(workflow_id))
        
        return active_workflows
    
    def get_workflow_statistics(self) -> Dict[str, Any]:
        """Get comprehensive workflow statistics"""
        base_stats = self.state_manager.get_email_workflow_statistics()
        db_stats = self.state_manager.get_database_statistics()
        
        return {
            'workflow_statistics': base_stats,
            'database_statistics': db_stats,
            'coordinator_info': {
                'director_agent_available': bool(self.director_agent),
                'communications_dept_available': bool(self.communications_dept),
                'email_agent_available': bool(self.email_agent),
                'review_agents_count': len(self.review_agents),
                'default_review_threshold': self.default_review_threshold,
                'max_review_rounds': self.max_review_rounds,
                'auto_finalize_on_consensus': self.auto_finalize_on_consensus
            }
        }