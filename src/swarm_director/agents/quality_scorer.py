"""
QualityScorer component for SwarmDirector
Provides standalone quantitative assessment of draft quality with configurable rubrics
"""

import logging
from typing import Dict, List, Any, Optional, Union
from datetime import datetime

logger = logging.getLogger(__name__)


class QualityScorer:
    """
    Standalone component for quantitative assessment of draft quality
    Provides configurable scoring algorithms across multiple quality dimensions
    """
    
    def __init__(self, scoring_config: Optional[Dict[str, Any]] = None):
        """
        Initialize QualityScorer with configurable scoring parameters
        
        Args:
            scoring_config: Dictionary containing scoring configuration
        """
        self.scoring_config = scoring_config or self._get_default_config()
        self.validate_config()
        
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default scoring configuration"""
        return {
            'dimensions': {
                'content': {
                    'weight': 0.4,
                    'criteria': ['clarity', 'accuracy', 'completeness', 'relevance'],
                    'thresholds': {
                        'excellent': 90,
                        'good': 80,
                        'acceptable': 70,
                        'needs_improvement': 60
                    }
                },
                'structure': {
                    'weight': 0.25,
                    'criteria': ['organization', 'flow', 'coherence', 'formatting'],
                    'thresholds': {
                        'excellent': 90,
                        'good': 80,
                        'acceptable': 70,
                        'needs_improvement': 60
                    }
                },
                'style': {
                    'weight': 0.25,
                    'criteria': ['tone', 'voice', 'grammar', 'readability'],
                    'thresholds': {
                        'excellent': 90,
                        'good': 80,
                        'acceptable': 70,
                        'needs_improvement': 60
                    }
                },
                'technical': {
                    'weight': 0.1,
                    'criteria': ['terminology', 'facts', 'references', 'compliance'],
                    'thresholds': {
                        'excellent': 90,
                        'good': 80,
                        'acceptable': 70,
                        'needs_improvement': 60
                    }
                }
            },
            'score_range': {'min': 0, 'max': 100},
            'default_draft_type': 'general'
        }
    
    def validate_config(self) -> None:
        """Validate scoring configuration"""
        dimensions = self.scoring_config.get('dimensions', {})
        
        # Check weights sum to approximately 1.0
        total_weight = sum(dim.get('weight', 0) for dim in dimensions.values())
        if abs(total_weight - 1.0) > 0.01:
            logger.warning(f"Dimension weights sum to {total_weight}, not 1.0. Normalizing.")
            for dim_name, dim_config in dimensions.items():
                dim_config['weight'] = dim_config.get('weight', 0) / total_weight
    
    def score_content(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Score content quality and completeness
        
        Args:
            content: The content to score
            draft_type: Type of draft for context-aware scoring
            
        Returns:
            Dictionary containing content scores and analysis
        """
        if not content or not content.strip():
            return self._create_empty_score_result('content')
        
        word_count = len(content.split())
        char_count = len(content)
        sentence_count = len([s for s in content.split('.') if s.strip()])
        
        # Calculate component scores
        clarity_score = self._calculate_clarity_score(content, word_count)
        completeness_score = self._calculate_completeness_score(word_count, draft_type)
        relevance_score = self._calculate_relevance_score(content, draft_type)
        accuracy_score = self._calculate_accuracy_score(content, draft_type)
        
        # Aggregate content score
        content_score = (clarity_score + completeness_score + relevance_score + accuracy_score) / 4
        
        return {
            'dimension': 'content',
            'score': round(content_score, 1),
            'component_scores': {
                'clarity': clarity_score,
                'completeness': completeness_score,
                'relevance': relevance_score,
                'accuracy': accuracy_score
            },
            'metrics': {
                'word_count': word_count,
                'char_count': char_count,
                'sentence_count': sentence_count
            },
            'grade': self._get_score_grade(content_score, 'content'),
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def score_structure(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Score structural quality and organization
        
        Args:
            content: The content to score
            draft_type: Type of draft for context-aware scoring
            
        Returns:
            Dictionary containing structure scores and analysis
        """
        if not content or not content.strip():
            return self._create_empty_score_result('structure')
        
        lines = content.split('\n')
        paragraphs = [p for p in content.split('\n\n') if p.strip()]
        
        # Calculate structure score based on organization patterns
        organization_score = self._calculate_organization_score(paragraphs, lines)
        flow_score = self._calculate_flow_score(content, paragraphs)
        coherence_score = self._calculate_coherence_score(content, paragraphs)
        formatting_score = self._calculate_formatting_score(lines, content)
        
        # Aggregate structure score
        structure_score = (organization_score + flow_score + coherence_score + formatting_score) / 4
        
        return {
            'dimension': 'structure',
            'score': round(structure_score, 1),
            'component_scores': {
                'organization': organization_score,
                'flow': flow_score,
                'coherence': coherence_score,
                'formatting': formatting_score
            },
            'metrics': {
                'paragraph_count': len(paragraphs),
                'line_count': len(lines),
                'has_headers': any(line.strip().endswith(':') or line.strip().startswith('#') 
                                for line in lines)
            },
            'grade': self._get_score_grade(structure_score, 'structure'),
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def score_style(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Score writing style and readability
        
        Args:
            content: The content to score
            draft_type: Type of draft for context-aware scoring
            
        Returns:
            Dictionary containing style scores and analysis
        """
        if not content or not content.strip():
            return self._create_empty_score_result('style')
        
        # Calculate style component scores
        tone_score = self._calculate_tone_score(content, draft_type)
        voice_score = self._calculate_voice_score(content, draft_type)
        grammar_score = self._calculate_grammar_score(content)
        readability_score = self._calculate_readability_score(content)
        
        # Aggregate style score
        style_score = (tone_score + voice_score + grammar_score + readability_score) / 4
        
        return {
            'dimension': 'style',
            'score': round(style_score, 1),
            'component_scores': {
                'tone': tone_score,
                'voice': voice_score,
                'grammar': grammar_score,
                'readability': readability_score
            },
            'metrics': {
                'avg_sentence_length': len(content.split()) / max(1, len([s for s in content.split('.') if s.strip()])),
                'exclamation_count': content.count('!'),
                'question_count': content.count('?')
            },
            'grade': self._get_score_grade(style_score, 'style'),
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def score_technical(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Score technical accuracy and compliance
        
        Args:
            content: The content to score
            draft_type: Type of draft for context-aware scoring
            
        Returns:
            Dictionary containing technical scores and analysis
        """
        if not content or not content.strip():
            return self._create_empty_score_result('technical')
        
        # Calculate technical component scores
        terminology_score = self._calculate_terminology_score(content, draft_type)
        facts_score = self._calculate_facts_score(content, draft_type)
        references_score = self._calculate_references_score(content)
        compliance_score = self._calculate_compliance_score(content, draft_type)
        
        # Aggregate technical score
        technical_score = (terminology_score + facts_score + references_score + compliance_score) / 4
        
        return {
            'dimension': 'technical',
            'score': round(technical_score, 1),
            'component_scores': {
                'terminology': terminology_score,
                'facts': facts_score,
                'references': references_score,
                'compliance': compliance_score
            },
            'metrics': {
                'has_links': 'http' in content.lower() or 'www.' in content.lower(),
                'has_references': any(marker in content.lower() for marker in ['ref:', 'source:', 'see:', 'cf.']),
                'technical_terms': len([word for word in content.split() if len(word) > 8])
            },
            'grade': self._get_score_grade(technical_score, 'technical'),
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def calculate_overall_score(self, dimension_scores: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate weighted overall score from dimension scores
        
        Args:
            dimension_scores: Dictionary of dimension scoring results
            
        Returns:
            Dictionary containing overall score and metadata
        """
        dimensions = self.scoring_config['dimensions']
        total_score = 0.0
        total_weight = 0.0
        
        for dimension_name, score_data in dimension_scores.items():
            if dimension_name in dimensions:
                weight = dimensions[dimension_name]['weight']
                score = score_data.get('score', 0)
                total_score += score * weight
                total_weight += weight
        
        overall_score = total_score / max(total_weight, 0.01)  # Prevent division by zero
        
        return {
            'overall_score': round(overall_score, 2),
            'weighted_calculation': {
                'total_weighted_score': round(total_score, 2),
                'total_weight': round(total_weight, 2)
            },
            'dimension_contributions': {
                dim: {
                    'score': dimension_scores[dim].get('score', 0),
                    'weight': dimensions[dim]['weight'],
                    'contribution': round(dimension_scores[dim].get('score', 0) * dimensions[dim]['weight'], 2)
                }
                for dim in dimension_scores if dim in dimensions
            },
            'grade': self._get_overall_grade(overall_score),
            'recommendation': self._get_score_recommendation(overall_score),
            'calculated_at': datetime.utcnow().isoformat()
        }
    
    def score_draft_comprehensive(self, content: str, draft_type: str = 'general') -> Dict[str, Any]:
        """
        Perform comprehensive scoring across all dimensions
        
        Args:
            content: The content to score
            draft_type: Type of draft for context-aware scoring
            
        Returns:
            Complete scoring analysis with overall score
        """
        logger.info(f"Performing comprehensive quality scoring for {draft_type} draft ({len(content)} characters)")
        
        if not content or not content.strip():
            return self._create_empty_comprehensive_result(draft_type)
        
        try:
            # Score all dimensions
            dimension_scores = {
                'content': self.score_content(content, draft_type),
                'structure': self.score_structure(content, draft_type),
                'style': self.score_style(content, draft_type),
                'technical': self.score_technical(content, draft_type)
            }
            
            # Calculate overall score
            overall_result = self.calculate_overall_score(dimension_scores)
            
            # Compile comprehensive result
            comprehensive_result = {
                'draft_type': draft_type,
                'content_length': len(content),
                'scoring_config': self.scoring_config,
                'dimension_scores': dimension_scores,
                'overall_score': overall_result['overall_score'],
                'overall_grade': overall_result['grade'],
                'recommendation': overall_result['recommendation'],
                'detailed_calculation': overall_result,
                'scored_at': datetime.utcnow().isoformat()
            }
            
            logger.info(f"Comprehensive scoring completed with overall score: {overall_result['overall_score']}")
            return comprehensive_result
            
        except Exception as e:
            logger.error(f"Error during comprehensive scoring: {str(e)}")
            return self._create_error_result(str(e), draft_type)
    
    def compare_scores(self, score1: Dict[str, Any], score2: Dict[str, Any]) -> Dict[str, Any]:
        """
        Compare two scoring results
        
        Args:
            score1: First scoring result
            score2: Second scoring result
            
        Returns:
            Comparison analysis
        """
        overall1 = score1.get('overall_score', 0)
        overall2 = score2.get('overall_score', 0)
        
        return {
            'score_difference': round(overall2 - overall1, 2),
            'percentage_change': round(((overall2 - overall1) / max(overall1, 0.01)) * 100, 2),
            'winner': 'score2' if overall2 > overall1 else 'score1' if overall1 > overall2 else 'tie',
            'dimension_comparisons': self._compare_dimensions(score1, score2),
            'compared_at': datetime.utcnow().isoformat()
        }
    
    def update_scoring_config(self, new_config: Dict[str, Any]) -> bool:
        """
        Update scoring configuration
        
        Args:
            new_config: New configuration to apply
            
        Returns:
            True if update successful, False otherwise
        """
        try:
            # Backup current config
            backup_config = self.scoring_config.copy()
            
            # Apply new config
            self.scoring_config.update(new_config)
            
            # Validate new config
            self.validate_config()
            
            logger.info("Scoring configuration updated successfully")
            return True
            
        except Exception as e:
            # Restore backup on error
            self.scoring_config = backup_config
            logger.error(f"Failed to update scoring configuration: {str(e)}")
            return False
    
    def get_scoring_config(self) -> Dict[str, Any]:
        """Get current scoring configuration"""
        return self.scoring_config.copy()
    
    # Private helper methods for scoring calculations
    
    def _calculate_clarity_score(self, content: str, word_count: int) -> float:
        """Calculate clarity score based on content characteristics"""
        base_score = 85
        
        # Penalize overly long content
        if word_count > 1000:
            base_score -= 20
        elif word_count > 500:
            base_score -= 10
        
        # Penalize overly short content
        if word_count < 10:
            base_score -= 40
        elif word_count < 25:
            base_score -= 20
        
        return max(0, min(100, base_score))
    
    def _calculate_completeness_score(self, word_count: int, draft_type: str) -> float:
        """Calculate completeness score based on expected length"""
        if draft_type == 'technical':
            target_range = (100, 500)
        elif draft_type == 'creative':
            target_range = (50, 300)
        else:
            target_range = (50, 400)
        
        min_words, max_words = target_range
        
        if min_words <= word_count <= max_words:
            return 95
        elif word_count < min_words:
            return max(20, 95 - ((min_words - word_count) / min_words) * 60)
        else:
            return max(60, 95 - ((word_count - max_words) / max_words) * 25)
    
    def _calculate_relevance_score(self, content: str, draft_type: str) -> float:
        """Calculate relevance score (placeholder for future AI enhancement)"""
        # Base score - would be enhanced with AI analysis
        return 85
    
    def _calculate_accuracy_score(self, content: str, draft_type: str) -> float:
        """Calculate accuracy score (placeholder for future fact-checking)"""
        # Base score - would be enhanced with fact-checking
        return 80
    
    def _calculate_organization_score(self, paragraphs: List[str], lines: List[str]) -> float:
        """Calculate organization score based on structure"""
        base_score = 75
        
        if len(paragraphs) > 1:
            base_score += 15
        elif len(paragraphs) == 1 and len('\n\n'.join(paragraphs)) > 200:
            base_score -= 15
        elif len(paragraphs) == 0:
            base_score -= 25
        
        # Check for headers and organizational elements
        has_structure = any(line.strip().endswith(':') or line.strip().startswith('#') 
                          for line in lines)
        if has_structure:
            base_score += 10
        
        return max(0, min(100, base_score))
    
    def _calculate_flow_score(self, content: str, paragraphs: List[str]) -> float:
        """Calculate flow score based on transition and continuity"""
        base_score = 80
        
        # Simple heuristics for flow analysis
        transition_words = ['however', 'therefore', 'furthermore', 'additionally', 'meanwhile', 'consequently']
        has_transitions = any(word in content.lower() for word in transition_words)
        
        if has_transitions:
            base_score += 10
        
        return max(0, min(100, base_score))
    
    def _calculate_coherence_score(self, content: str, paragraphs: List[str]) -> float:
        """Calculate coherence score based on consistency"""
        base_score = 85
        
        # Basic coherence checks
        if len(paragraphs) > 3:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_formatting_score(self, lines: List[str], content: str) -> float:
        """Calculate formatting score based on presentation"""
        base_score = 80
        
        # Check for proper line breaks
        if len(lines) > 1:
            base_score += 10
        
        # Check for consistent formatting
        has_formatting = any(char in content for char in ['*', '-', '•', '1.', '2.'])
        if has_formatting:
            base_score += 5
        
        return max(0, min(100, base_score))
    
    def _calculate_tone_score(self, content: str, draft_type: str) -> float:
        """Calculate tone appropriateness score"""
        base_score = 80
        
        # Basic tone analysis
        exclamation_count = content.count('!')
        if draft_type == 'technical' and exclamation_count > 2:
            base_score -= 10
        elif draft_type == 'creative' and exclamation_count == 0:
            base_score -= 5
        
        return max(0, min(100, base_score))
    
    def _calculate_voice_score(self, content: str, draft_type: str) -> float:
        """Calculate voice consistency score"""
        return 85  # Placeholder for future voice analysis
    
    def _calculate_grammar_score(self, content: str) -> float:
        """Calculate basic grammar score"""
        base_score = 85
        
        # Basic grammar checks
        sentences = [s.strip() for s in content.split('.') if s.strip()]
        incomplete_sentences = sum(1 for s in sentences if len(s.split()) < 3)
        
        if incomplete_sentences > len(sentences) * 0.3:
            base_score -= 15
        
        return max(0, min(100, base_score))
    
    def _calculate_readability_score(self, content: str) -> float:
        """Calculate readability score"""
        words = content.split()
        sentences = [s for s in content.split('.') if s.strip()]
        
        if not sentences:
            return 50
        
        avg_words_per_sentence = len(words) / len(sentences)
        
        # Optimal range: 15-25 words per sentence
        if 15 <= avg_words_per_sentence <= 25:
            return 90
        elif avg_words_per_sentence < 15:
            return max(70, 90 - (15 - avg_words_per_sentence) * 2)
        else:
            return max(60, 90 - (avg_words_per_sentence - 25))
    
    def _calculate_terminology_score(self, content: str, draft_type: str) -> float:
        """Calculate terminology appropriateness score"""
        base_score = 85
        
        if draft_type == 'technical':
            # Expect more technical terms
            technical_indicators = ['API', 'database', 'algorithm', 'implementation', 'configuration']
            has_technical = any(term.lower() in content.lower() for term in technical_indicators)
            if has_technical:
                base_score += 10
            else:
                base_score -= 15
        
        return max(0, min(100, base_score))
    
    def _calculate_facts_score(self, content: str, draft_type: str) -> float:
        """Calculate factual accuracy score (placeholder)"""
        return 80  # Would be enhanced with fact-checking services
    
    def _calculate_references_score(self, content: str) -> float:
        """Calculate references and citations score"""
        base_score = 75
        
        # Check for references
        has_links = 'http' in content.lower() or 'www.' in content.lower()
        has_citations = any(marker in content.lower() for marker in ['ref:', 'source:', 'see:', 'cf.'])
        
        if has_links or has_citations:
            base_score += 20
        
        return max(0, min(100, base_score))
    
    def _calculate_compliance_score(self, content: str, draft_type: str) -> float:
        """Calculate compliance score"""
        return 85  # Placeholder for compliance checking
    
    def _get_score_grade(self, score: float, dimension: str) -> str:
        """Get letter grade for a score"""
        thresholds = self.scoring_config['dimensions'][dimension]['thresholds']
        
        if score >= thresholds['excellent']:
            return 'A'
        elif score >= thresholds['good']:
            return 'B'
        elif score >= thresholds['acceptable']:
            return 'C'
        elif score >= thresholds['needs_improvement']:
            return 'D'
        else:
            return 'F'
    
    def _get_overall_grade(self, score: float) -> str:
        """Get overall letter grade"""
        if score >= 90:
            return 'A'
        elif score >= 80:
            return 'B'
        elif score >= 70:
            return 'C'
        elif score >= 60:
            return 'D'
        else:
            return 'F'
    
    def _get_score_recommendation(self, score: float) -> str:
        """Get recommendation based on score"""
        if score >= 90:
            return "Excellent quality - ready for publication"
        elif score >= 80:
            return "Good quality - minor revisions recommended"
        elif score >= 70:
            return "Acceptable quality - moderate revisions needed"
        elif score >= 60:
            return "Needs improvement - significant revisions required"
        elif score >= 40:
            return "Poor quality - major revision or rewrite needed"
        else:
            return "Unacceptable quality - complete rewrite recommended"
    
    def _create_empty_score_result(self, dimension: str) -> Dict[str, Any]:
        """Create empty score result for missing content"""
        return {
            'dimension': dimension,
            'score': 0.0,
            'component_scores': {},
            'metrics': {},
            'grade': 'F',
            'scored_at': datetime.utcnow().isoformat(),
            'error': 'No content provided for scoring'
        }
    
    def _create_empty_comprehensive_result(self, draft_type: str) -> Dict[str, Any]:
        """Create empty comprehensive result"""
        return {
            'draft_type': draft_type,
            'content_length': 0,
            'overall_score': 0.0,
            'overall_grade': 'F',
            'recommendation': 'No content provided for scoring',
            'dimension_scores': {},
            'error': 'No content provided for comprehensive scoring',
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def _create_error_result(self, error_msg: str, draft_type: str) -> Dict[str, Any]:
        """Create error result"""
        return {
            'draft_type': draft_type,
            'overall_score': 0.0,
            'overall_grade': 'F',
            'error': error_msg,
            'scored_at': datetime.utcnow().isoformat()
        }
    
    def _compare_dimensions(self, score1: Dict[str, Any], score2: Dict[str, Any]) -> Dict[str, Any]:
        """Compare dimension scores between two results"""
        dimensions1 = score1.get('dimension_scores', {})
        dimensions2 = score2.get('dimension_scores', {})
        
        comparisons = {}
        for dimension in set(dimensions1.keys()) | set(dimensions2.keys()):
            score_1 = dimensions1.get(dimension, {}).get('score', 0)
            score_2 = dimensions2.get(dimension, {}).get('score', 0)
            
            comparisons[dimension] = {
                'score1': score_1,
                'score2': score_2,
                'difference': round(score_2 - score_1, 2),
                'improvement': score_2 > score_1
            }
        
        return comparisons 