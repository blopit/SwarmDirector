"""
ReviewLogic component for SwarmDirector
Provides modular draft analysis and review functionality that can be used independently
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ReviewLogic:
    """
    Standalone component for draft review and analysis
    Handles content, structure, style, and technical analysis independently
    """
    
    def __init__(self, criteria: Optional[Dict[str, List[str]]] = None, 
                 weights: Optional[Dict[str, float]] = None):
        """
        Initialize ReviewLogic with configurable criteria and weights
        
        Args:
            criteria: Dictionary defining review criteria for each category
            weights: Dictionary defining weights for each review category
        """
        self.review_criteria = criteria or {
            'content': ['clarity', 'accuracy', 'completeness', 'relevance'],
            'structure': ['organization', 'flow', 'coherence', 'formatting'],
            'style': ['tone', 'voice', 'grammar', 'readability'],
            'technical': ['terminology', 'facts', 'references', 'compliance']
        }
        
        self.review_weights = weights or {
            'content': 0.4,
            'structure': 0.25,
            'style': 0.25,
            'technical': 0.1
        }
        
        # Validate weights sum to 1.0
        weight_sum = sum(self.review_weights.values())
        if abs(weight_sum - 1.0) > 0.01:
            logger.warning(f"Review weights sum to {weight_sum}, not 1.0. Normalizing.")
            self.review_weights = {k: v/weight_sum for k, v in self.review_weights.items()}
    
    def analyze_draft(self, content: str, draft_type: str = 'general', 
                     reviewer_name: str = 'ReviewLogic') -> Dict[str, Any]:
        """
        Perform comprehensive draft analysis
        
        Args:
            content: The draft content to analyze
            draft_type: Type of draft (general, technical, creative, etc.)
            reviewer_name: Name of the reviewer for logging purposes
            
        Returns:
            Dictionary containing complete review analysis and recommendations
        """
        logger.info(f"Analyzing {draft_type} draft ({len(content)} characters)")
        
        if not content or not content.strip():
            return self._create_empty_review_result(draft_type, reviewer_name)
        
        try:
            # Perform analysis across all categories
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
                'recommendation': self._get_recommendation(overall_score),
                'reviewed_at': datetime.utcnow().isoformat(),
                'reviewer': reviewer_name,
                'draft_type': draft_type,
                'review_criteria': self.review_criteria,
                'review_weights': self.review_weights
            }
            
            logger.info(f"Review completed with overall score: {overall_score}")
            return review_result
            
        except Exception as e:
            logger.error(f"Error during draft analysis: {str(e)}")
            return self._create_error_review_result(str(e), draft_type, reviewer_name)
    
    def _analyze_content(self, content: str) -> Dict[str, Any]:
        """Analyze content quality and completeness"""
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Calculate scores based on content metrics
        clarity_score = min(100, max(0, 100 - (word_count / 50)))  # Penalize overly long content
        completeness_score = min(100, word_count * 2)  # Reward adequate length
        relevance_score = 85  # Base relevance score (would need AI analysis for true relevance)
        accuracy_score = 80   # Base accuracy score (would need fact-checking for true accuracy)
        
        issues = []
        strengths = []
        
        # Identify content issues
        if word_count < 10:
            issues.append("Content appears too brief for meaningful analysis")
            completeness_score = max(0, completeness_score - 40)
        elif word_count < 25:
            issues.append("Content may be too short")
            completeness_score = max(0, completeness_score - 20)
        
        if word_count > 1000:
            issues.append("Content may be too lengthy for effective review")
            clarity_score = max(0, clarity_score - 20)
        elif word_count > 500:
            issues.append("Consider breaking into smaller sections")
            clarity_score = max(0, clarity_score - 10)
        
        if sentence_count < 2 and word_count > 20:
            issues.append("Consider breaking into multiple sentences")
            clarity_score = max(0, clarity_score - 15)
        
        # Identify content strengths
        if content.strip():
            strengths.append("Content provided for analysis")
        if 50 <= word_count <= 300:
            strengths.append("Appropriate length for clear communication")
        if sentence_count >= 3:
            strengths.append("Well-structured with multiple sentences")
        
        # Calculate final content score
        content_score = (clarity_score + completeness_score + relevance_score + accuracy_score) / 4
        
        return {
            'score': round(content_score, 1),
            'word_count': word_count,
            'char_count': char_count,
            'sentence_count': sentence_count,
            'component_scores': {
                'clarity': clarity_score,
                'completeness': completeness_score,
                'relevance': relevance_score,
                'accuracy': accuracy_score
            },
            'issues': issues,
            'strengths': strengths
        }
    
    def _analyze_structure(self, content: str) -> Dict[str, Any]:
        """Analyze structural quality and organization"""
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        structure_score = 75  # Base score
        issues = []
        strengths = []
        
        # Analyze paragraph structure
        if len(paragraphs) > 1:
            strengths.append("Well-structured with multiple paragraphs")
            structure_score += 15
        elif len(paragraphs) == 1 and len(content) > 200:
            issues.append("Consider breaking into multiple paragraphs for better readability")
            structure_score -= 15
        elif len(paragraphs) == 0:
            issues.append("No clear paragraph structure detected")
            structure_score -= 25
        
        # Check for headers and organization markers
        headers = [line for line in lines if line.strip().endswith(':') or 
                  line.strip().startswith('#') or line.strip().isupper()]
        if headers:
            strengths.append("Uses clear section headers or organizational elements")
            structure_score += 10
        
        # Check for lists or structured elements
        list_items = [line for line in lines if line.strip().startswith(('-', '*', '•', '1.', '2.'))]
        if list_items:
            strengths.append("Includes structured lists or enumeration")
            structure_score += 5
        
        # Check for flow and coherence indicators
        transitions = ['however', 'therefore', 'furthermore', 'additionally', 'in conclusion']
        has_transitions = any(trans in content.lower() for trans in transitions)
        if has_transitions:
            strengths.append("Uses transitional phrases for better flow")
            structure_score += 5
        
        # Penalize very long paragraphs
        long_paragraphs = [p for p in paragraphs if len(p.split()) > 100]
        if long_paragraphs:
            issues.append("Some paragraphs may be too long")
            structure_score -= 10
        
        return {
            'score': min(100, max(0, structure_score)),
            'paragraph_count': len(paragraphs),
            'line_count': len(lines),
            'header_count': len(headers),
            'list_item_count': len(list_items),
            'has_transitions': has_transitions,
            'issues': issues,
            'strengths': strengths
        }
    
    def _analyze_style(self, content: str) -> Dict[str, Any]:
        """Analyze writing style and readability"""
        style_score = 80  # Base score
        issues = []
        strengths = []
        
        # Check basic style elements
        if content.strip().endswith('.'):
            strengths.append("Proper sentence ending punctuation")
        elif content.strip() and not content.strip().endswith(('.', '!', '?')):
            issues.append("Consider adding proper ending punctuation")
            style_score -= 5
        
        # Check for capitalization
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        capitalized_sentences = [s for s in sentences if s and s[0].isupper()]
        if len(capitalized_sentences) == len(sentences) and sentences:
            strengths.append("Consistent sentence capitalization")
        elif sentences and len(capitalized_sentences) < len(sentences):
            issues.append("Some sentences may need proper capitalization")
            style_score -= 10
        
        # Check for tone consistency (basic analysis)
        word_count = len(content.split())
        exclamation_count = content.count('!')
        question_count = content.count('?')
        
        if exclamation_count > word_count / 20:  # Too many exclamations
            issues.append("Consider reducing exclamation marks for professional tone")
            style_score -= 5
        
        # Check for readability indicators
        avg_word_length = sum(len(word) for word in content.split()) / max(1, len(content.split()))
        if avg_word_length > 7:
            issues.append("Consider using simpler vocabulary for better readability")
            style_score -= 10
        elif 4 <= avg_word_length <= 6:
            strengths.append("Good balance of vocabulary complexity")
        
        # Check for repetitive words
        words = content.lower().split()
        word_freq = {}
        for word in words:
            if len(word) > 3:  # Only count significant words
                word_freq[word] = word_freq.get(word, 0) + 1
        
        repetitive_words = [word for word, freq in word_freq.items() if freq > len(words) / 20]
        if repetitive_words:
            issues.append(f"Consider varying vocabulary (repetitive: {', '.join(repetitive_words[:3])})")
            style_score -= 5
        
        return {
            'score': min(100, max(0, style_score)),
            'avg_word_length': round(avg_word_length, 1),
            'exclamation_count': exclamation_count,
            'question_count': question_count,
            'repetitive_words': repetitive_words[:5],  # Top 5 most repetitive
            'issues': issues,
            'strengths': strengths
        }
    
    def _analyze_technical(self, content: str, draft_type: str) -> Dict[str, Any]:
        """Analyze technical accuracy and compliance"""
        technical_score = 85  # Base score for general content
        issues = []
        strengths = []
        
        # Adjust scoring based on draft type
        if draft_type in ['technical', 'scientific', 'academic']:
            technical_score = 70  # Higher standards for technical content
            
            # Check for technical elements
            has_references = any(marker in content.lower() for marker in ['ref', 'citation', 'source'])
            if has_references:
                strengths.append("Includes references or citations")
                technical_score += 10
            else:
                issues.append("Consider adding references for technical claims")
                technical_score -= 15
            
            # Check for technical terminology consistency
            technical_indicators = ['algorithm', 'implementation', 'methodology', 'analysis', 'framework']
            tech_term_count = sum(1 for term in technical_indicators if term in content.lower())
            if tech_term_count > 0:
                strengths.append("Uses appropriate technical terminology")
                technical_score += 5
        
        # Check for factual consistency indicators (basic analysis)
        fact_indicators = ['according to', 'studies show', 'research indicates', 'data suggests']
        factual_claims = sum(1 for indicator in fact_indicators if indicator in content.lower())
        if factual_claims > 0:
            strengths.append("Includes factual claims with indicators")
            technical_score += 5
        
        # Check for compliance elements (depending on context)
        if draft_type == 'legal':
            legal_indicators = ['pursuant to', 'in accordance with', 'section', 'clause']
            legal_terms = sum(1 for term in legal_indicators if term in content.lower())
            if legal_terms > 0:
                strengths.append("Uses appropriate legal terminology")
                technical_score += 10
        
        return {
            'score': min(100, max(0, technical_score)),
            'draft_type': draft_type,
            'factual_claims': factual_claims,
            'issues': issues,
            'strengths': strengths
        }
    
    def _generate_suggestions(self, content_analysis: Dict, structure_analysis: Dict, 
                            style_analysis: Dict, technical_analysis: Dict) -> List[Dict[str, Any]]:
        """Generate actionable suggestions based on all analyses"""
        suggestions = []
        
        # Priority levels: high (score < 60), medium (60-80), low (80+)
        analyses = {
            'content': content_analysis,
            'structure': structure_analysis,
            'style': style_analysis,
            'technical': technical_analysis
        }
        
        for category, analysis in analyses.items():
            score = analysis['score']
            issues = analysis.get('issues', [])
            
            # Determine priority based on score
            if score < 60:
                priority = 'high'
            elif score < 80:
                priority = 'medium'
            else:
                priority = 'low'
            
            # Create suggestions for each issue
            for issue in issues:
                suggestions.append({
                    'category': category,
                    'priority': priority,
                    'issue': issue,
                    'score_impact': score,
                    'suggestion_type': 'improvement'
                })
        
        # Add positive reinforcement for strengths
        for category, analysis in analyses.items():
            strengths = analysis.get('strengths', [])
            for strength in strengths[:2]:  # Limit to top 2 strengths per category
                suggestions.append({
                    'category': category,
                    'priority': 'positive',
                    'issue': strength,
                    'score_impact': analysis['score'],
                    'suggestion_type': 'strength'
                })
        
        # Sort suggestions by priority (high, medium, low, positive)
        priority_order = {'high': 0, 'medium': 1, 'low': 2, 'positive': 3}
        suggestions.sort(key=lambda x: priority_order.get(x['priority'], 4))
        
        return suggestions
    
    def _get_recommendation(self, overall_score: float) -> str:
        """Generate overall recommendation based on score"""
        if overall_score >= 90:
            return "Excellent draft - ready for publication with minimal revisions"
        elif overall_score >= 80:
            return "Strong draft - consider minor improvements before finalizing"
        elif overall_score >= 70:
            return "Good foundation - address moderate issues before submission"
        elif overall_score >= 60:
            return "Needs improvement - significant revisions recommended"
        elif overall_score >= 40:
            return "Major revision required - consider restructuring content"
        else:
            return "Substantial work needed - recommend starting fresh or major overhaul"
    
    def _create_empty_review_result(self, draft_type: str, reviewer_name: str) -> Dict[str, Any]:
        """Create review result for empty content"""
        return {
            'overall_score': 0.0,
            'category_scores': {'content': 0, 'structure': 0, 'style': 0, 'technical': 0},
            'analysis': {
                'content': {'score': 0, 'issues': ['No content provided'], 'strengths': []},
                'structure': {'score': 0, 'issues': ['No structure to analyze'], 'strengths': []},
                'style': {'score': 0, 'issues': ['No style to evaluate'], 'strengths': []},
                'technical': {'score': 0, 'issues': ['No technical content'], 'strengths': []}
            },
            'suggestions': [{'category': 'content', 'priority': 'high', 'issue': 'Add content to enable review', 'suggestion_type': 'improvement'}],
            'recommendation': 'No content provided - unable to perform review',
            'reviewed_at': datetime.utcnow().isoformat(),
            'reviewer': reviewer_name,
            'draft_type': draft_type,
            'review_criteria': self.review_criteria,
            'review_weights': self.review_weights
        }
    
    def _create_error_review_result(self, error_msg: str, draft_type: str, reviewer_name: str) -> Dict[str, Any]:
        """Create review result for error cases"""
        return {
            'overall_score': 0.0,
            'category_scores': {'content': 0, 'structure': 0, 'style': 0, 'technical': 0},
            'analysis': {},
            'suggestions': [],
            'recommendation': f'Review failed due to error: {error_msg}',
            'reviewed_at': datetime.utcnow().isoformat(),
            'reviewer': reviewer_name,
            'draft_type': draft_type,
            'error': error_msg,
            'review_criteria': self.review_criteria,
            'review_weights': self.review_weights
        }
    
    def get_review_configuration(self) -> Dict[str, Any]:
        """Get current review configuration"""
        return {
            'criteria': self.review_criteria,
            'weights': self.review_weights,
            'categories': list(self.review_weights.keys())
        }
    
    def update_configuration(self, criteria: Optional[Dict[str, List[str]]] = None,
                           weights: Optional[Dict[str, float]] = None) -> bool:
        """
        Update review configuration
        
        Args:
            criteria: New review criteria
            weights: New category weights
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            if criteria:
                self.review_criteria = criteria
            
            if weights:
                # Validate weights
                weight_sum = sum(weights.values())
                if abs(weight_sum - 1.0) > 0.01:
                    # Normalize weights
                    weights = {k: v/weight_sum for k, v in weights.items()}
                self.review_weights = weights
            
            logger.info("Review configuration updated successfully")
            return True
            
        except Exception as e:
            logger.error(f"Failed to update review configuration: {str(e)}")
            return False 