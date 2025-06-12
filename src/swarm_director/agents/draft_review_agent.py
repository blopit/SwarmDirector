"""
DraftReviewAgent implementation for SwarmDirector
Provides draft review and critique functionality with JSON diff generation
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .worker_agent import WorkerAgent
from .review_logic import ReviewLogic
from ..models.agent import Agent
from ..models.task import Task
from ..models.draft import Draft, DraftStatus, DraftType
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class DraftReviewAgent(WorkerAgent):
    """
    Agent that reviews drafts and provides structured feedback
    Uses ReviewLogic component for analysis and AutoGen capabilities for intelligent content analysis
    """
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        
        # Initialize the ReviewLogic component with default configuration
        self.review_logic = ReviewLogic()
        
        # Maintain backward compatibility with old properties
        self.review_criteria = self.review_logic.review_criteria
        self.review_weights = self.review_logic.review_weights
    
    def execute_task(self, task: Task) -> Dict[str, Any]:
        """Execute draft review task"""
        log_agent_action(self.name, f"Starting draft review for task: {task.title}")
        
        try:
            # Extract draft information from task
            draft_data = task.input_data or {}
            draft_content = draft_data.get('content', '')
            draft_type = draft_data.get('type', 'general')
            
            if not draft_content:
                return {
                    "status": "error",
                    "error": "No draft content provided for review",
                    "task_id": task.id
                }
            
            # Perform comprehensive review using ReviewLogic component
            review_result = self.review_draft(draft_content, draft_type)
            
            # Create draft record if not exists
            draft = self._create_or_update_draft(task, draft_content, draft_type, review_result)
            
            # Update task with results
            task.complete_task(output_data=review_result)
            
            log_agent_action(self.name, f"Draft review completed for task {task.id}")
            
            return {
                "status": "success",
                "review_result": review_result,
                "draft_id": draft.id if draft else None,
                "task_id": task.id
            }
            
        except Exception as e:
            error_msg = f"Error during draft review: {str(e)}"
            logger.error(error_msg)
            log_agent_action(self.name, error_msg)
            return {
                "status": "error",
                "error": error_msg,
                "task_id": task.id
            }
    
    def review_draft(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Perform comprehensive draft review using ReviewLogic component
        Returns structured feedback with scores and suggestions
        """
        log_agent_action(self.name, f"Reviewing {draft_type} draft ({len(content)} characters)")
        
        # Use ReviewLogic component for analysis
        review_result = self.review_logic.analyze_draft(
            content=content,
            draft_type=draft_type,
            reviewer_name=self.name
        )
        
        # Generate JSON diff for specific edits (DraftReviewAgent-specific feature)
        json_diff = self._generate_json_diff(content, review_result.get('suggestions', []))
        
        # Add JSON diff to the review result
        review_result['json_diff'] = json_diff
        
        return review_result
    
    def _generate_json_diff(self, original_content: str, suggestions: List[Dict]) -> List[Dict[str, Any]]:
        """
        Generate JSON diff for specific edits based on suggestions
        This method provides specific edit locations and changes
        """
        json_diff = []
        
        try:
            lines = original_content.split('\n')
            
            for i, suggestion in enumerate(suggestions[:10]):  # Limit to top 10 suggestions
                if suggestion.get('suggestion_type') == 'improvement':
                    issue = suggestion.get('issue', '')
                    category = suggestion.get('category', 'general')
                    priority = suggestion.get('priority', 'low')
                    
                    # Generate a diff entry based on the suggestion
                    if 'punctuation' in issue.lower():
                        # Find lines that might need punctuation fixes
                        for line_num, line in enumerate(lines):
                            if line.strip() and not line.strip().endswith(('.', '!', '?', ':')):
                                json_diff.append({
                                    'line': line_num + 1,
                                    'type': 'modification',
                                    'category': category,
                                    'priority': priority,
                                    'original': line,
                                    'suggested': line.rstrip() + '.',
                                    'reason': issue,
                                    'confidence': 0.8
                                })
                                break
                    
                    elif 'paragraph' in issue.lower() and 'break' in issue.lower():
                        # Suggest paragraph breaks for long content
                        for line_num, line in enumerate(lines):
                            if len(line) > 200 and '. ' in line:
                                split_point = line.find('. ') + 2
                                json_diff.append({
                                    'line': line_num + 1,
                                    'type': 'split',
                                    'category': category,
                                    'priority': priority,
                                    'original': line,
                                    'suggested': [line[:split_point].strip(), line[split_point:].strip()],
                                    'reason': issue,
                                    'confidence': 0.7
                                })
                                break
                    
                    elif 'section' in issue.lower() or 'header' in issue.lower():
                        # Suggest adding headers
                        json_diff.append({
                            'line': 1,
                            'type': 'insertion',
                            'category': category,
                            'priority': priority,
                            'suggested': '# Document Title\n\n',
                            'reason': issue,
                            'confidence': 0.6
                        })
                    
                    else:
                        # Generic suggestion
                        json_diff.append({
                            'line': 1,
                            'type': 'general',
                            'category': category,
                            'priority': priority,
                            'reason': issue,
                            'suggestion': f"Consider addressing: {issue}",
                            'confidence': 0.5
                        })
        
        except Exception as e:
            logger.error(f"Error generating JSON diff: {str(e)}")
            # Return a basic diff entry if generation fails
            json_diff.append({
                'line': 1,
                'type': 'error',
                'reason': f"Could not generate detailed diff: {str(e)}",
                'suggestion': "Manual review recommended"
            })
        
        return json_diff
    
    def _create_or_update_draft(self, task: Task, content: str, draft_type: str, 
                               review_result: Dict) -> Optional[Draft]:
        """Create or update draft record in database"""
        try:
            # Check if draft already exists for this task
            existing_draft = Draft.query.filter_by(task_id=task.id).first()
            
            if existing_draft:
                # Update existing draft
                existing_draft.content = content
                existing_draft.draft_type = DraftType(draft_type) if draft_type in [dt.value for dt in DraftType] else DraftType.GENERAL
                existing_draft.status = DraftStatus.REVIEWED
                existing_draft.review_data = review_result
                existing_draft.reviewed_at = datetime.utcnow()
                existing_draft.reviewed_by = self.name
                existing_draft.save()
                return existing_draft
            else:
                # Create new draft
                draft = Draft.create(
                    task_id=task.id,
                    content=content,
                    draft_type=DraftType(draft_type) if draft_type in [dt.value for dt in DraftType] else DraftType.GENERAL,
                    status=DraftStatus.REVIEWED,
                    review_data=review_result,
                    reviewed_at=datetime.utcnow(),
                    reviewed_by=self.name
                )
                return draft
                
        except Exception as e:
            logger.error(f"Error creating/updating draft: {str(e)}")
            return None
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task"""
        if not task:
            return False
        
        # Check both task.type and task.task_type for backward compatibility
        task_type = getattr(task, 'type', None) or getattr(task, 'task_type', None)
        if not task_type:
            return False
        
        # Can handle draft review tasks
        review_task_types = ['review', 'draft_review', 'content_review', 'document_review']
        return task_type.lower() in review_task_types
    
    def update_review_configuration(self, criteria: Optional[Dict[str, List[str]]] = None,
                                   weights: Optional[Dict[str, float]] = None) -> bool:
        """
        Update review configuration using ReviewLogic component
        
        Args:
            criteria: New review criteria
            weights: New category weights
            
        Returns:
            True if update successful, False otherwise
        """
        success = self.review_logic.update_configuration(criteria=criteria, weights=weights)
        
        if success:
            # Update backward compatibility properties
            self.review_criteria = self.review_logic.review_criteria
            self.review_weights = self.review_logic.review_weights
            log_agent_action(self.name, "Review configuration updated successfully")
        else:
            log_agent_action(self.name, "Failed to update review configuration")
        
        return success
    
    def get_review_configuration(self) -> Dict[str, Any]:
        """Get current review configuration from ReviewLogic component"""
        return self.review_logic.get_review_configuration()
    
    # Backward compatibility methods - delegate to ReviewLogic
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._analyze_content(content)
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._analyze_structure(content)
    
    def _analyze_style(self, content: str) -> Dict[str, Any]:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._analyze_style(content)
    
    def _analyze_technical(self, content: str, draft_type: str) -> Dict[str, Any]:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._analyze_technical(content, draft_type)
    
    def _generate_suggestions(self, content_analysis: Dict, structure_analysis: Dict, 
                            style_analysis: Dict, technical_analysis: Dict) -> List[Dict[str, Any]]:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._generate_suggestions(
            content_analysis, structure_analysis, style_analysis, technical_analysis
        )
    
    def _get_recommendation(self, overall_score: float) -> str:
        """Backward compatibility method - delegates to ReviewLogic"""
        return self.review_logic._get_recommendation(overall_score)
