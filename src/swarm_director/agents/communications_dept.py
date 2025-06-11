"""
CommunicationsDept implementation for SwarmDirector
Manages message drafting workflows with parallel review processes
"""

import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

from .supervisor_agent import SupervisorAgent
from .draft_review_agent import DraftReviewAgent
from .email_agent import EmailAgent
from ..models.agent import Agent, AgentType, AgentStatus
from ..models.task import Task, TaskStatus
from ..models.draft import Draft, DraftStatus, DraftType
from ..models.conversation import Conversation, Message, MessageType
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class CommunicationsDept(SupervisorAgent):
    """
    Communications Department agent that manages message drafting workflows
    Coordinates parallel DraftReviewAgents for consensus-driven content creation
    """
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        self.department_name = "communications"
        self.review_agents = []
        self.email_agent = None
        self.min_reviewers = 2
        self.consensus_threshold = 0.75  # 75% agreement required
        
        # Initialize subordinate agents
        self._initialize_subordinate_agents()
    
    def _initialize_subordinate_agents(self):
        """Initialize review agents and email agent"""
        try:
            # Create or find review agents
            for i in range(self.min_reviewers):
                agent_name = f"DraftReviewer_{i+1}"
                review_agent_db = self._get_or_create_agent(
                    name=agent_name,
                    agent_type=AgentType.WORKER,
                    description=f"Draft review agent #{i+1} for communications department"
                )
                review_agent = DraftReviewAgent(review_agent_db)
                self.review_agents.append(review_agent)
            
            # Create or find email agent
            email_agent_db = self._get_or_create_agent(
                name="EmailAgent",
                agent_type=AgentType.WORKER,
                description="Email composition and delivery agent"
            )
            self.email_agent = EmailAgent(email_agent_db)
            
            log_agent_action(self.name, f"Initialized {len(self.review_agents)} review agents and email agent")
            
        except Exception as e:
            logger.error(f"Error initializing subordinate agents: {e}")
    
    def _get_or_create_agent(self, name: str, agent_type: AgentType, description: str) -> Agent:
        """Get existing agent or create new one"""
        agent = Agent.query.filter_by(name=name).first()
        if not agent:
            agent = Agent(
                name=name,
                agent_type=agent_type,
                status=AgentStatus.ACTIVE,
                description=description,
                parent_id=self.db_agent.id
            )
            agent.save()
        return agent
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute communications task with parallel review workflow"""
        log_agent_action(self.name, f"Processing communications task: {task.title}")
        
        try:
            # Determine communication type and workflow
            comm_type = self._determine_communication_type(task)
            
            if comm_type == 'email':
                return self._handle_email_workflow(task)
            elif comm_type == 'draft_review':
                return self._handle_draft_review_workflow(task)
            elif comm_type == 'content_creation':
                return self._handle_content_creation_workflow(task)
            else:
                return self._handle_general_communication(task)
                
        except Exception as e:
            error_msg = f"Error in communications workflow: {str(e)}"
            logger.error(error_msg)
            log_agent_action(self.name, error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _determine_communication_type(self, task: Task) -> str:
        """Determine the type of communication workflow needed"""
        task_data = task.input_data or {}
        task_type = task.type.value if hasattr(task.type, 'value') else str(task.type)
        
        # Check explicit workflow type
        if 'workflow_type' in task_data:
            return task_data['workflow_type']
        
        # Infer from task type and content
        if task_type.lower() in ['email', 'send_email']:
            return 'email'
        elif 'review' in task.title.lower() or 'review' in task.description.lower():
            return 'draft_review'
        elif 'create' in task.title.lower() or 'compose' in task.title.lower():
            return 'content_creation'
        else:
            return 'general'
    
    def _handle_email_workflow(self, task: Task) -> Dict[str, Any]:
        """Handle email-specific workflow with review and sending"""
        log_agent_action(self.name, "Starting email workflow")
        
        try:
            # Step 1: Create initial draft
            draft_result = self._create_initial_draft(task)
            if draft_result['status'] != 'success':
                return draft_result
            
            # Step 2: Parallel review process
            review_result = self._conduct_parallel_review(task, draft_result['draft_content'])
            if review_result['status'] != 'success':
                return review_result
            
            # Step 3: Reconcile feedback and finalize
            final_draft = self._reconcile_feedback_and_finalize(task, review_result)
            if final_draft['status'] != 'success':
                return final_draft
            
            # Step 4: Send email if requested
            task_data = task.input_data or {}
            if task_data.get('send_immediately', False):
                send_result = self._send_final_email(task, final_draft['final_content'])
                return send_result
            else:
                task.complete_task(output_data=final_draft)
                return {
                    "status": "success",
                    "message": "Email workflow completed - draft ready for sending",
                    "workflow_result": final_draft,
                    "task_id": task.id
                }
                
        except Exception as e:
            error_msg = f"Error in email workflow: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _handle_draft_review_workflow(self, task: Task) -> Dict[str, Any]:
        """Handle draft review workflow"""
        log_agent_action(self.name, "Starting draft review workflow")
        
        try:
            task_data = task.input_data or {}
            content = task_data.get('content', task.description)
            
            # Conduct parallel review
            review_result = self._conduct_parallel_review(task, content)
            
            if review_result['status'] == 'success':
                task.complete_task(output_data=review_result)
            
            return review_result
            
        except Exception as e:
            error_msg = f"Error in draft review workflow: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _handle_content_creation_workflow(self, task: Task) -> Dict[str, Any]:
        """Handle content creation workflow"""
        log_agent_action(self.name, "Starting content creation workflow")
        
        try:
            # Create initial content
            draft_result = self._create_initial_draft(task)
            if draft_result['status'] != 'success':
                return draft_result
            
            # Review and refine
            review_result = self._conduct_parallel_review(task, draft_result['draft_content'])
            if review_result['status'] != 'success':
                return review_result
            
            # Finalize content
            final_result = self._reconcile_feedback_and_finalize(task, review_result)
            
            if final_result['status'] == 'success':
                task.complete_task(output_data=final_result)
            
            return final_result
            
        except Exception as e:
            error_msg = f"Error in content creation workflow: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def _handle_general_communication(self, task: Task) -> Dict[str, Any]:
        """Handle general communication tasks"""
        log_agent_action(self.name, "Handling general communication task")
        
        # Simple delegation to appropriate agent
        if self.email_agent and self.email_agent.can_handle_task(task):
            return self.email_agent.execute_task(task)
        else:
            # Handle directly
            task.complete_task(output_data={
                "message": "General communication task handled by CommunicationsDept",
                "handled_by": self.name,
                "timestamp": datetime.utcnow().isoformat()
            })
            
            return {
                "status": "success",
                "message": "General communication task completed",
                "task_id": task.id
            }
    
    def _create_initial_draft(self, task: Task) -> Dict[str, Any]:
        """Create initial draft content"""
        try:
            task_data = task.input_data or {}
            
            # Use provided content or generate from task description
            if 'content' in task_data:
                draft_content = task_data['content']
            elif 'template' in task_data:
                # Use email agent to compose from template
                compose_result = self.email_agent._compose_email(task, task_data)
                if compose_result['status'] == 'success':
                    draft_content = compose_result['composed_email']['body']
                else:
                    return compose_result
            else:
                # Generate basic content from task
                draft_content = f"Subject: {task.title}\n\n{task.description}"
            
            return {
                "status": "success",
                "draft_content": draft_content,
                "created_at": datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            return {
                "status": "error",
                "error": f"Error creating initial draft: {str(e)}"
            }
    
    def _conduct_parallel_review(self, task: Task, content: str) -> Dict[str, Any]:
        """Conduct parallel review using multiple DraftReviewAgents"""
        log_agent_action(self.name, f"Starting parallel review with {len(self.review_agents)} agents")
        
        try:
            reviews = []
            
            # Create review tasks for each agent
            with ThreadPoolExecutor(max_workers=len(self.review_agents)) as executor:
                # Submit review tasks
                future_to_agent = {}
                for i, review_agent in enumerate(self.review_agents):
                    # Create a review task
                    review_task = Task(
                        title=f"Review: {task.title}",
                        description=f"Review content for task {task.id}",
                        type=task.type,
                        user_id=task.user_id,
                        status=TaskStatus.PENDING,
                        input_data={
                            'content': content,
                            'type': 'general',
                            'parent_task_id': task.id
                        }
                    )
                    review_task.save()
                    
                    # Submit to thread pool
                    future = executor.submit(review_agent.execute_task, review_task)
                    future_to_agent[future] = (review_agent, review_task)
                
                # Collect results
                for future in as_completed(future_to_agent):
                    review_agent, review_task = future_to_agent[future]
                    try:
                        result = future.result(timeout=30)  # 30 second timeout per review
                        if result['status'] == 'success':
                            reviews.append({
                                'agent': review_agent.name,
                                'task_id': review_task.id,
                                'review': result.get('review_result', {}),
                                'timestamp': datetime.utcnow().isoformat()
                            })
                        else:
                            logger.warning(f"Review failed from {review_agent.name}: {result.get('error')}")
                    except Exception as e:
                        logger.error(f"Review agent {review_agent.name} failed: {str(e)}")
            
            if len(reviews) < self.min_reviewers:
                return {
                    "status": "error",
                    "error": f"Insufficient reviews received ({len(reviews)}/{self.min_reviewers})"
                }
            
            log_agent_action(self.name, f"Collected {len(reviews)} reviews")
            
            return {
                "status": "success",
                "reviews": reviews,
                "review_count": len(reviews),
                "content_reviewed": content
            }
            
        except Exception as e:
            error_msg = f"Error in parallel review: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def _reconcile_feedback_and_finalize(self, task: Task, review_result: Dict) -> Dict[str, Any]:
        """Reconcile feedback from multiple reviewers and create final version"""
        log_agent_action(self.name, "Reconciling feedback and finalizing content")
        
        try:
            reviews = review_result.get('reviews', [])
            original_content = review_result.get('content_reviewed', '')
            
            # Analyze consensus
            consensus_analysis = self._analyze_consensus(reviews)
            
            # Apply improvements based on consensus
            final_content = self._apply_consensus_improvements(original_content, consensus_analysis)
            
            # Create final draft record
            final_draft = Draft(
                task_id=task.id,
                content=final_content,
                draft_type=DraftType.DOCUMENT,
                status=DraftStatus.FINAL,
                version=2,  # Version 2 after review
                metadata={
                    'review_count': len(reviews),
                    'consensus_score': consensus_analysis['consensus_score'],
                    'improvements_applied': len(consensus_analysis['agreed_improvements']),
                    'finalized_by': self.name,
                    'finalized_at': datetime.utcnow().isoformat()
                }
            )
            final_draft.save()
            
            return {
                "status": "success",
                "final_content": final_content,
                "draft_id": final_draft.id,
                "consensus_analysis": consensus_analysis,
                "improvements_applied": len(consensus_analysis['agreed_improvements'])
            }
            
        except Exception as e:
            error_msg = f"Error reconciling feedback: {str(e)}"
            logger.error(error_msg)
            return {
                "status": "error",
                "error": error_msg
            }
    
    def _analyze_consensus(self, reviews: List[Dict]) -> Dict[str, Any]:
        """Analyze consensus among reviewers"""
        if not reviews:
            return {'consensus_score': 0, 'agreed_improvements': [], 'conflicting_suggestions': []}
        
        # Collect all suggestions
        all_suggestions = []
        scores = []
        
        for review in reviews:
            review_data = review.get('review', {})
            if 'overall_score' in review_data:
                scores.append(review_data['overall_score'])
            if 'suggestions' in review_data:
                all_suggestions.extend(review_data['suggestions'])
        
        # Find common suggestions (simplified consensus)
        suggestion_counts = {}
        for suggestion in all_suggestions:
            key = suggestion.get('description', '')
            if key:
                suggestion_counts[key] = suggestion_counts.get(key, 0) + 1
        
        # Suggestions agreed upon by majority
        min_agreement = max(1, len(reviews) * self.consensus_threshold)
        agreed_improvements = [
            suggestion for suggestion, count in suggestion_counts.items()
            if count >= min_agreement
        ]
        
        # Calculate consensus score
        avg_score = sum(scores) / len(scores) if scores else 0
        agreement_ratio = len(agreed_improvements) / max(1, len(suggestion_counts))
        consensus_score = (avg_score / 100) * 0.7 + agreement_ratio * 0.3
        
        return {
            'consensus_score': round(consensus_score, 3),
            'average_score': round(avg_score, 2),
            'agreed_improvements': agreed_improvements,
            'total_suggestions': len(all_suggestions),
            'reviewer_count': len(reviews)
        }
    
    def _apply_consensus_improvements(self, original_content: str, consensus: Dict) -> str:
        """Apply consensus improvements to content"""
        # Simplified improvement application
        # In a real implementation, this would be more sophisticated
        improved_content = original_content
        
        improvements = consensus.get('agreed_improvements', [])
        if improvements:
            # Add improvement note
            improvement_note = f"\n\n[Improved based on {len(improvements)} consensus suggestions]"
            improved_content += improvement_note
        
        return improved_content
    
    def _send_final_email(self, task: Task, final_content: str) -> Dict[str, Any]:
        """Send the finalized email"""
        if not self.email_agent:
            return {
                "status": "error",
                "error": "Email agent not available"
            }
        
        # Prepare email data
        task_data = task.input_data or {}
        email_data = {
            'operation': 'send',
            'recipient': task_data.get('recipient', ''),
            'subject': task_data.get('subject', task.title),
            'body': final_content,
            'sender': task_data.get('sender', '')
        }
        
        # Create email task
        email_task = Task(
            title=f"Send: {task.title}",
            description="Send finalized email",
            type=task.type,
            user_id=task.user_id,
            status=TaskStatus.PENDING,
            input_data=email_data
        )
        email_task.save()
        
        # Execute email sending
        return self.email_agent.execute_task(email_task)
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this department can handle the given task"""
        task_type = task.type.value if hasattr(task.type, 'value') else str(task.type)
        communication_types = ['email', 'communication', 'draft', 'review', 'compose', 'message']
        
        return any(comm_type in task_type.lower() for comm_type in communication_types)
