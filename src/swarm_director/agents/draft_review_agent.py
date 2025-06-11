"""
DraftReviewAgent implementation for SwarmDirector
Provides draft review and critique functionality with JSON diff generation
"""

import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from .worker_agent import WorkerAgent
from ..models.agent import Agent
from ..models.task import Task
from ..models.draft import Draft, DraftStatus, DraftType
from ..utils.logging import log_agent_action

logger = logging.getLogger(__name__)

class DraftReviewAgent(WorkerAgent):
    """
    Agent that reviews drafts and provides structured feedback
    Uses AutoGen capabilities for intelligent content analysis
    """
    
    def __init__(self, db_agent: Agent):
        super().__init__(db_agent)
        self.review_criteria = {
            'content': ['clarity', 'accuracy', 'completeness', 'relevance'],
            'structure': ['organization', 'flow', 'coherence', 'formatting'],
            'style': ['tone', 'voice', 'grammar', 'readability'],
            'technical': ['terminology', 'facts', 'references', 'compliance']
        }
        self.review_weights = {
            'content': 0.4,
            'structure': 0.25,
            'style': 0.25,
            'technical': 0.1
        }
    
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
            
            # Perform comprehensive review
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
        Perform comprehensive draft review
        Returns structured feedback with scores and suggestions
        """
        log_agent_action(self.name, f"Reviewing {draft_type} draft ({len(content)} characters)")
        
        # Analyze content across different criteria
        content_analysis = self._analyze_content(content)
        structure_analysis = self._analyze_structure(content)
        style_analysis = self._analyze_style(content)
        technical_analysis = self._analyze_technical(content, draft_type)
        
        # Generate overall scores
        scores = {
            'content': content_analysis['score'],
            'structure': structure_analysis['score'],
            'style': style_analysis['score'],
            'technical': technical_analysis['score']
        }
        
        # Calculate weighted overall score
        overall_score = sum(
            scores[category] * self.review_weights[category]
            for category in scores
        )
        
        # Generate suggestions and improvements
        suggestions = self._generate_suggestions(
            content_analysis, structure_analysis, style_analysis, technical_analysis
        )
        
        # Create JSON diff for specific edits
        json_diff = self._generate_json_diff(content, suggestions)
        
        review_result = {
            'overall_score': round(overall_score, 2),
            'category_scores': scores,
            'analysis': {
                'content': content_analysis,
                'structure': structure_analysis,
                'style': style_analysis,
                'technical': technical_analysis
            },
            'suggestions': suggestions,
            'json_diff': json_diff,
            'recommendation': self._get_recommendation(overall_score),
            'reviewed_at': datetime.utcnow().isoformat(),
            'reviewer': self.name,
            'draft_type': draft_type
        }
        
        return review_result
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content quality"""
        word_count = len(content.split())
        char_count = len(content)
        
        # Basic content analysis
        clarity_score = min(100, max(0, 100 - (word_count / 50)))  # Penalize overly long content
        completeness_score = min(100, word_count * 2)  # Reward adequate length
        
        issues = []
        if word_count < 10:
            issues.append("Content appears too brief")
        if word_count > 500:
            issues.append("Content may be too lengthy")
        if not content.strip():
            issues.append("No content provided")
        
        return {
            'score': (clarity_score + completeness_score) / 2,
            'word_count': word_count,
            'char_count': char_count,
            'issues': issues,
            'strengths': ["Content provided"] if content.strip() else []
        }
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze structural quality"""
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        structure_score = 75  # Base score
        issues = []
        strengths = []
        
        if len(paragraphs) > 1:
            strengths.append("Well-structured with multiple paragraphs")
            structure_score += 15
        elif len(paragraphs) == 1 and len(content) > 100:
            issues.append("Consider breaking into multiple paragraphs")
            structure_score -= 10
        
        if any(line.strip().endswith(':') for line in lines):
            strengths.append("Uses clear section headers")
            structure_score += 10
        
        return {
            'score': min(100, structure_score),
            'paragraph_count': len(paragraphs),
            'line_count': len(lines),
            'issues': issues,
            'strengths': strengths
        }
    
    def _analyze_style(self, content: str) -> Dict[str, Any]:
        """Analyze writing style"""
        style_score = 80  # Base score
        issues = []
        strengths = []
        
        # Check for basic style elements
        if content.strip().endswith('.'):
            strengths.append("Proper sentence ending")
        else:
            issues.append("Consider proper sentence endings")
            style_score -= 5
        
        # Check for varied sentence length
        sentences = content.split('.')
        if len(sentences) > 2:
            strengths.append("Multiple sentences for better flow")
            style_score += 10
        
        return {
            'score': min(100, style_score),
            'sentence_count': len(sentences),
            'issues': issues,
            'strengths': strengths
        }
    
    def _analyze_technical(self, content: str, draft_type: str) -> Dict[str, Any]:
        """Analyze technical accuracy"""
        technical_score = 85  # Base score
        issues = []
        strengths = []
        
        # Type-specific analysis
        if draft_type == 'email':
            if '@' in content:
                strengths.append("Contains email references")
            if any(word in content.lower() for word in ['subject:', 'dear', 'sincerely', 'regards']):
                strengths.append("Proper email formatting elements")
                technical_score += 10
        
        elif draft_type == 'technical':
            if any(word in content.lower() for word in ['api', 'database', 'system', 'implementation']):
                strengths.append("Contains technical terminology")
                technical_score += 5
        
        return {
            'score': min(100, technical_score),
            'draft_type': draft_type,
            'issues': issues,
            'strengths': strengths
        }
    
    def _generate_suggestions(self, content_analysis: Dict, structure_analysis: Dict, 
                            style_analysis: Dict, technical_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate actionable suggestions based on analysis"""
        suggestions = []
        
        # Collect all issues and convert to suggestions
        all_analyses = [content_analysis, structure_analysis, style_analysis, technical_analysis]
        categories = ['content', 'structure', 'style', 'technical']
        
        for i, analysis in enumerate(all_analyses):
            for issue in analysis.get('issues', []):
                suggestions.append({
                    'category': categories[i],
                    'type': 'improvement',
                    'description': issue,
                    'priority': 'medium',
                    'suggested_action': f"Address {categories[i]} issue: {issue}"
                })
        
        # Add positive reinforcement
        for i, analysis in enumerate(all_analyses):
            for strength in analysis.get('strengths', []):
                suggestions.append({
                    'category': categories[i],
                    'type': 'strength',
                    'description': strength,
                    'priority': 'low',
                    'suggested_action': f"Continue {categories[i]} strength: {strength}"
                })
        
        return suggestions
    
    def _generate_json_diff(self, original_content: str, suggestions: List[Dict]) -> List[Dict[str, Any]]:
        """Generate JSON diff with specific edit suggestions"""
        diffs = []
        
        # Generate specific edits based on suggestions
        for suggestion in suggestions:
            if suggestion['type'] == 'improvement':
                diff_entry = {
                    'operation': 'modify',
                    'category': suggestion['category'],
                    'description': suggestion['description'],
                    'suggested_change': suggestion['suggested_action'],
                    'line_number': 1,  # Simplified - in real implementation would be more specific
                    'original': original_content[:50] + "..." if len(original_content) > 50 else original_content,
                    'suggested': f"[Improved] {original_content[:50]}..." if len(original_content) > 50 else f"[Improved] {original_content}"
                }
                diffs.append(diff_entry)
        
        return diffs
    
    def _get_recommendation(self, overall_score: float) -> str:
        """Get overall recommendation based on score"""
        if overall_score >= 90:
            return "Excellent draft - ready for publication"
        elif overall_score >= 80:
            return "Good draft - minor improvements suggested"
        elif overall_score >= 70:
            return "Acceptable draft - some improvements needed"
        elif overall_score >= 60:
            return "Draft needs significant improvement"
        else:
            return "Draft requires major revision"
    
    def _create_or_update_draft(self, task: Task, content: str, draft_type: str, 
                               review_result: Dict) -> Optional[Draft]:
        """Create or update draft record"""
        try:
            draft = Draft(
                task_id=task.id,
                content=content,
                draft_type=DraftType.EMAIL if draft_type == 'email' else DraftType.DOCUMENT,
                status=DraftStatus.REVIEW,
                version=1,
                metadata={
                    'review_score': review_result['overall_score'],
                    'reviewer_agent': self.name,
                    'review_date': datetime.utcnow().isoformat()
                }
            )
            draft.save()
            return draft
        except Exception as e:
            logger.error(f"Error creating draft record: {e}")
            return None
    
    def can_handle_task(self, task: Task) -> bool:
        """Check if this agent can handle the given task"""
        task_type = task.type.value if hasattr(task.type, 'value') else str(task.type)
        return task_type.lower() in ['review', 'draft_review', 'content_review']
