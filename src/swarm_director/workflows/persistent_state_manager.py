"""
Persistent Email Workflow State Management
Combines in-memory state management with database persistence
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta

from .email_workflow_states import (
    EmailWorkflowStateManager, EmailWorkflowState, EmailWorkflowType, 
    EmailWorkflowPhase, EmailContext, ReviewContext, EmailDeliveryStatus
)
from .state_manager import WorkflowStatus
from ..models.workflow_state import WorkflowStateDB, WorkflowEventDB
from ..utils.database import db

logger = logging.getLogger(__name__)

class PersistentEmailWorkflowStateManager(EmailWorkflowStateManager):
    """
    Email workflow state manager with database persistence
    Extends EmailWorkflowStateManager to add persistence capabilities
    """
    
    def __init__(self, auto_persist: bool = True, auto_restore: bool = True):
        super().__init__()
        self.auto_persist = auto_persist
        self.auto_restore = auto_restore
        
        # Load existing workflows from database if auto_restore is enabled
        if self.auto_restore:
            self._restore_workflows_from_db()
    
    def _restore_workflows_from_db(self):
        """Restore workflows from database to in-memory state"""
        try:
            # Get all active workflows from database
            active_workflows = WorkflowStateDB.find_active_workflows()
            
            for db_workflow in active_workflows:
                # Convert database model to EmailWorkflowState
                email_state = self._db_to_email_workflow_state(db_workflow)
                
                # Add to in-memory storage
                self._states[email_state.workflow_id] = email_state
                self._email_workflows[email_state.workflow_id] = email_state
                
                logger.info(f"Restored workflow from database: {email_state.workflow_id}")
            
            logger.info(f"Restored {len(active_workflows)} workflows from database")
            
        except Exception as e:
            logger.error(f"Error restoring workflows from database: {e}")
    
    def _db_to_email_workflow_state(self, db_workflow: WorkflowStateDB) -> EmailWorkflowState:
        """Convert database model to EmailWorkflowState"""
        # Create email context
        email_context_data = db_workflow.get_email_context()
        email_context = EmailContext()
        if email_context_data:
            for key, value in email_context_data.items():
                if hasattr(email_context, key):
                    if key == 'delivery_status':
                        setattr(email_context, key, EmailDeliveryStatus(value))
                    elif key == 'last_delivery_attempt' and value:
                        setattr(email_context, key, datetime.fromisoformat(value))
                    else:
                        setattr(email_context, key, value)
        
        # Create review context if exists
        review_context = None
        review_context_data = db_workflow.get_review_context()
        if review_context_data:
            review_context = ReviewContext()
            for key, value in review_context_data.items():
                if hasattr(review_context, key):
                    if key == 'review_deadline' and value:
                        setattr(review_context, key, datetime.fromisoformat(value))
                    else:
                        setattr(review_context, key, value)
        
        # Create EmailWorkflowState
        email_state = EmailWorkflowState(
            workflow_id=db_workflow.workflow_id,
            status=WorkflowStatus(db_workflow.status),
            created_at=db_workflow.created_at,
            updated_at=db_workflow.updated_at,
            started_at=db_workflow.started_at,
            completed_at=db_workflow.completed_at,
            workflow_type=EmailWorkflowType(db_workflow.workflow_type),
            current_phase=EmailWorkflowPhase(db_workflow.current_phase) if db_workflow.current_phase else EmailWorkflowPhase.INTENT_CLASSIFICATION,
            email_context=email_context,
            review_context=review_context,
            assigned_director=db_workflow.assigned_director,
            assigned_communications_dept=db_workflow.assigned_communications_dept,
            assigned_email_agent=db_workflow.assigned_email_agent,
            assigned_review_agents=db_workflow.get_assigned_review_agents(),
            phase_history=db_workflow.get_phase_history(),
            phase_durations=db_workflow.get_phase_durations(),
            review_iterations=db_workflow.review_iterations,
            content_revisions=db_workflow.content_revisions,
            delivery_attempts=db_workflow.delivery_attempts,
            active_agents=db_workflow.get_active_agents(),
            completed_tasks=db_workflow.get_completed_tasks(),
            failed_tasks=db_workflow.get_failed_tasks(),
            input_data=db_workflow.get_input_data(),
            output_data=db_workflow.get_output_data(),
            error_data=db_workflow.get_error_data(),
            total_steps=db_workflow.total_steps,
            completed_steps=db_workflow.completed_steps,
            state_history=[self._convert_state_history_item(item) for item in db_workflow.get_state_history()]
        )
        
        return email_state
    
    def _convert_state_history_item(self, item: Dict[str, Any]):
        """Convert state history item from database format"""
        from .state_manager import StateTransition
        return StateTransition(
            from_state=WorkflowStatus(item['from_state']),
            to_state=WorkflowStatus(item['to_state']),
            timestamp=datetime.fromisoformat(item['timestamp']),
            agent_name=item.get('agent_name'),
            reason=item.get('reason'),
            metadata=item.get('metadata', {})
        )
    
    def _email_workflow_state_to_db(self, email_state: EmailWorkflowState) -> WorkflowStateDB:
        """Convert EmailWorkflowState to database model"""
        # Find existing database record or create new one
        db_workflow = WorkflowStateDB.find_by_workflow_id(email_state.workflow_id)
        if not db_workflow:
            db_workflow = WorkflowStateDB(
                workflow_id=email_state.workflow_id,
                workflow_type=email_state.workflow_type.value
            )
        
        # Update basic fields
        db_workflow.status = email_state.status.value
        db_workflow.current_phase = email_state.current_phase.value
        db_workflow.started_at = email_state.started_at
        db_workflow.completed_at = email_state.completed_at
        db_workflow.total_steps = email_state.total_steps
        db_workflow.completed_steps = email_state.completed_steps
        
        # Update context data
        db_workflow.set_input_data(email_state.input_data)
        db_workflow.set_output_data(email_state.output_data)
        db_workflow.set_error_data(email_state.error_data)
        
        # Update email context
        db_workflow.set_email_context(email_state.email_context.to_dict())
        
        # Update review context
        if email_state.review_context:
            db_workflow.set_review_context(email_state.review_context.to_dict())
        
        # Update agent assignments
        db_workflow.assigned_director = email_state.assigned_director
        db_workflow.assigned_communications_dept = email_state.assigned_communications_dept
        db_workflow.assigned_email_agent = email_state.assigned_email_agent
        db_workflow.set_assigned_review_agents(email_state.assigned_review_agents)
        
        # Update metrics
        db_workflow.review_iterations = email_state.review_iterations
        db_workflow.content_revisions = email_state.content_revisions
        db_workflow.delivery_attempts = email_state.delivery_attempts
        
        # Update history and tracking
        db_workflow.set_phase_history(email_state.phase_history)
        db_workflow.set_phase_durations(email_state.phase_durations)
        db_workflow.set_active_agents(email_state.active_agents)
        db_workflow.set_completed_tasks(email_state.completed_tasks)
        db_workflow.set_failed_tasks(email_state.failed_tasks)
        
        # Convert state history
        state_history_data = []
        for transition in email_state.state_history:
            state_history_data.append({
                'from_state': transition.from_state.value,
                'to_state': transition.to_state.value,
                'timestamp': transition.timestamp.isoformat(),
                'agent_name': transition.agent_name,
                'reason': transition.reason,
                'metadata': transition.metadata
            })
        db_workflow.set_state_history(state_history_data)
        
        return db_workflow
    
    def _persist_to_database(self, email_state: EmailWorkflowState):
        """Persist workflow state to database"""
        if not self.auto_persist:
            return
        
        try:
            db_workflow = self._email_workflow_state_to_db(email_state)
            db_workflow.save()
            logger.debug(f"Persisted workflow state to database: {email_state.workflow_id}")
        except Exception as e:
            logger.error(f"Error persisting workflow state to database: {e}")
    
    def _log_event_to_database(self, workflow_id: str, event_type: str, **event_data):
        """Log workflow event to database"""
        try:
            event = WorkflowEventDB(
                workflow_id=workflow_id,
                event_type=event_type,
                **{k: v for k, v in event_data.items() if k in ['from_state', 'to_state', 'from_phase', 'to_phase', 'agent_name', 'reason']}
            )
            
            # Set metadata
            metadata = event_data.get('metadata', {})
            event.set_metadata(metadata)
            
            event.save()
            logger.debug(f"Logged event to database: {event_type} for workflow {workflow_id}")
        except Exception as e:
            logger.error(f"Error logging event to database: {e}")
    
    # Override parent methods to add persistence
    
    def create_email_workflow(self, workflow_id: str, workflow_type: EmailWorkflowType,
                             email_context: EmailContext = None, 
                             input_data: Dict[str, Any] = None) -> EmailWorkflowState:
        """Create email workflow with database persistence"""
        email_state = super().create_email_workflow(workflow_id, workflow_type, email_context, input_data)
        
        # Persist to database
        self._persist_to_database(email_state)
        
        # Log creation event
        self._log_event_to_database(
            workflow_id=workflow_id,
            event_type='workflow_created',
            metadata={'workflow_type': workflow_type.value}
        )
        
        return email_state
    
    def advance_workflow_phase(self, workflow_id: str, new_phase: EmailWorkflowPhase,
                              agent_name: str = None, notes: str = None,
                              metadata: Dict[str, Any] = None) -> bool:
        """Advance workflow phase with database persistence"""
        # Get current phase for logging
        email_state = self._email_workflows.get(workflow_id)
        if not email_state:
            return False
        
        current_phase = email_state.current_phase
        
        # Perform phase advancement
        success = super().advance_workflow_phase(workflow_id, new_phase, agent_name, notes, metadata)
        
        if success:
            # Persist to database
            self._persist_to_database(email_state)
            
            # Log phase change event
            self._log_event_to_database(
                workflow_id=workflow_id,
                event_type='phase_change',
                from_phase=current_phase.value,
                to_phase=new_phase.value,
                agent_name=agent_name,
                reason=notes,
                metadata=metadata or {}
            )
        
        return success
    
    def update_workflow_status(self, workflow_id: str, new_status: WorkflowStatus,
                             agent_name: str = None, reason: str = None,
                             metadata: Dict[str, Any] = None) -> bool:
        """Update workflow status with database persistence"""
        # Get current status for logging
        state = self._states.get(workflow_id)
        if not state:
            return False
        
        current_status = state.status
        
        # Perform status update
        success = super().update_workflow_status(workflow_id, new_status, agent_name, reason, metadata)
        
        if success:
            # Persist to database
            if workflow_id in self._email_workflows:
                self._persist_to_database(self._email_workflows[workflow_id])
            
            # Log state transition event
            self._log_event_to_database(
                workflow_id=workflow_id,
                event_type='state_transition',
                from_state=current_status.value,
                to_state=new_status.value,
                agent_name=agent_name,
                reason=reason,
                metadata=metadata or {}
            )
        
        return success
    
    def update_email_context(self, workflow_id: str, **email_updates) -> bool:
        """Update email context with database persistence"""
        success = super().update_email_context(workflow_id, **email_updates)
        
        if success:
            email_state = self._email_workflows.get(workflow_id)
            if email_state:
                # Persist to database
                self._persist_to_database(email_state)
                
                # Log context update event
                self._log_event_to_database(
                    workflow_id=workflow_id,
                    event_type='context_update',
                    metadata={'updated_fields': list(email_updates.keys())}
                )
        
        return success
    
    def add_review_result(self, workflow_id: str, agent_name: str, 
                         review_result: Dict[str, Any]) -> bool:
        """Add review result with database persistence"""
        success = super().add_review_result(workflow_id, agent_name, review_result)
        
        if success:
            email_state = self._email_workflows.get(workflow_id)
            if email_state:
                # Persist to database
                self._persist_to_database(email_state)
                
                # Log review event
                self._log_event_to_database(
                    workflow_id=workflow_id,
                    event_type='review_completed',
                    agent_name=agent_name,
                    metadata={'review_result': review_result}
                )
        
        return success
    
    # Additional persistence methods
    
    def persist_workflow(self, workflow_id: str) -> bool:
        """Manually persist a workflow to database"""
        email_state = self._email_workflows.get(workflow_id)
        if not email_state:
            return False
        
        try:
            self._persist_to_database(email_state)
            return True
        except Exception as e:
            logger.error(f"Error persisting workflow {workflow_id}: {e}")
            return False
    
    def persist_all_workflows(self) -> int:
        """Persist all in-memory workflows to database"""
        persisted_count = 0
        
        for workflow_id in self._email_workflows.keys():
            if self.persist_workflow(workflow_id):
                persisted_count += 1
        
        logger.info(f"Persisted {persisted_count} workflows to database")
        return persisted_count
    
    def delete_workflow(self, workflow_id: str) -> bool:
        """Delete workflow from both memory and database"""
        # Remove from memory
        if workflow_id in self._states:
            del self._states[workflow_id]
        if workflow_id in self._email_workflows:
            del self._email_workflows[workflow_id]
        
        # Remove from database
        try:
            db_workflow = WorkflowStateDB.find_by_workflow_id(workflow_id)
            if db_workflow:
                db.session.delete(db_workflow)
                db.session.commit()
            
            # Also delete related events
            events = WorkflowEventDB.find_by_workflow(workflow_id)
            for event in events:
                db.session.delete(event)
            db.session.commit()
            
            logger.info(f"Deleted workflow {workflow_id} from database")
            return True
            
        except Exception as e:
            logger.error(f"Error deleting workflow {workflow_id} from database: {e}")
            return False
    
    def get_workflow_events(self, workflow_id: str) -> List[Dict[str, Any]]:
        """Get all events for a workflow from database"""
        try:
            events = WorkflowEventDB.find_by_workflow(workflow_id)
            return [event.to_dict() for event in events]
        except Exception as e:
            logger.error(f"Error retrieving events for workflow {workflow_id}: {e}")
            return []
    
    def cleanup_old_workflows(self, days_old: int = 30) -> int:
        """Cleanup old completed workflows from database"""
        try:
            # Clean up database
            db_count = WorkflowStateDB.cleanup_old_workflows(days_old)
            
            # Clean up in-memory workflows that are completed/failed/cancelled
            cutoff_date = datetime.utcnow() - timedelta(days=days_old)
            memory_count = 0
            
            workflows_to_remove = []
            for workflow_id, state in self._email_workflows.items():
                if (state.status in [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED, WorkflowStatus.CANCELLED] and
                    state.completed_at and state.completed_at < cutoff_date):
                    workflows_to_remove.append(workflow_id)
            
            for workflow_id in workflows_to_remove:
                if workflow_id in self._states:
                    del self._states[workflow_id]
                if workflow_id in self._email_workflows:
                    del self._email_workflows[workflow_id]
                memory_count += 1
            
            logger.info(f"Cleaned up {db_count} workflows from database and {memory_count} from memory")
            return db_count + memory_count
            
        except Exception as e:
            logger.error(f"Error cleaning up old workflows: {e}")
            return 0
    
    def get_database_statistics(self) -> Dict[str, Any]:
        """Get statistics from database"""
        try:
            total_workflows = db.session.query(WorkflowStateDB).count()
            total_events = db.session.query(WorkflowEventDB).count()
            
            # Count by status
            status_counts = {}
            for status in WorkflowStatus:
                count = db.session.query(WorkflowStateDB).filter_by(status=status.value).count()
                status_counts[status.value] = count
            
            # Count by workflow type
            type_counts = {}
            for workflow_type in EmailWorkflowType:
                count = db.session.query(WorkflowStateDB).filter_by(workflow_type=workflow_type.value).count()
                type_counts[workflow_type.value] = count
            
            # Count by phase
            phase_counts = {}
            for phase in EmailWorkflowPhase:
                count = db.session.query(WorkflowStateDB).filter_by(current_phase=phase.value).count()
                phase_counts[phase.value] = count
            
            return {
                'total_workflows': total_workflows,
                'total_events': total_events,
                'status_distribution': status_counts,
                'type_distribution': type_counts,
                'phase_distribution': phase_counts,
                'in_memory_workflows': len(self._email_workflows)
            }
            
        except Exception as e:
            logger.error(f"Error getting database statistics: {e}")
            return {'error': str(e)}
    
    def sync_with_database(self, direction: str = 'both') -> Dict[str, int]:
        """Synchronize in-memory state with database"""
        if direction not in ['to_db', 'from_db', 'both']:
            raise ValueError("Direction must be 'to_db', 'from_db', or 'both'")
        
        results = {'persisted': 0, 'restored': 0}
        
        if direction in ['to_db', 'both']:
            results['persisted'] = self.persist_all_workflows()
        
        if direction in ['from_db', 'both']:
            # Clear current in-memory state
            old_count = len(self._email_workflows)
            self._states.clear()
            self._email_workflows.clear()
            
            # Restore from database
            self._restore_workflows_from_db()
            results['restored'] = len(self._email_workflows)
            
            logger.info(f"Sync: removed {old_count} in-memory workflows, restored {results['restored']}")
        
        return results