"""
Tests for the ReviewLogic component
"""

import pytest
from src.swarm_director.agents.review_logic import ReviewLogic

class TestReviewLogic:
    """Test suite for ReviewLogic component"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.review_logic = ReviewLogic()
    
    def test_initialization_default(self):
        """Test ReviewLogic initialization with default values"""
        rl = ReviewLogic()
        
        assert rl.review_criteria is not None
        assert 'content' in rl.review_criteria
        assert 'structure' in rl.review_criteria
        assert 'style' in rl.review_criteria
        assert 'technical' in rl.review_criteria
        
        assert rl.review_weights is not None
        assert abs(sum(rl.review_weights.values()) - 1.0) < 0.01
    
    def test_initialization_custom(self):
        """Test ReviewLogic initialization with custom values"""
        custom_criteria = {
            'content': ['clarity', 'accuracy'],
            'style': ['tone', 'grammar']
        }
        custom_weights = {
            'content': 0.7,
            'style': 0.3
        }
        
        rl = ReviewLogic(criteria=custom_criteria, weights=custom_weights)
        
        assert rl.review_criteria == custom_criteria
        assert rl.review_weights == custom_weights
    
    def test_weight_normalization(self):
        """Test that weights are normalized if they don't sum to 1.0"""
        invalid_weights = {
            'content': 0.6,
            'structure': 0.6,  # Total = 1.2, should be normalized
            'style': 0.0,
            'technical': 0.0
        }
        
        rl = ReviewLogic(weights=invalid_weights)
        
        # Weights should be normalized
        assert abs(sum(rl.review_weights.values()) - 1.0) < 0.01
        assert rl.review_weights['content'] == 0.5  # 0.6/1.2
        assert rl.review_weights['structure'] == 0.5  # 0.6/1.2
    
    def test_analyze_draft_basic(self):
        """Test basic draft analysis functionality"""
        test_content = "This is a test draft. It contains multiple sentences and provides good content for analysis."
        
        result = self.review_logic.analyze_draft(test_content)
        
        assert 'overall_score' in result
        assert 'category_scores' in result
        assert 'analysis' in result
        assert 'suggestions' in result
        assert 'recommendation' in result
        assert 'reviewed_at' in result
        assert result['draft_type'] == 'general'
        assert result['reviewer'] == 'ReviewLogic'
    
    def test_analyze_draft_empty_content(self):
        """Test analysis of empty content"""
        result = self.review_logic.analyze_draft("")
        
        assert result['overall_score'] == 0.0
        assert 'No content provided' in result['recommendation']
    
    def test_analyze_draft_technical_type(self):
        """Test analysis with technical draft type"""
        test_content = "This technical document describes the algorithm implementation methodology."
        
        result = self.review_logic.analyze_draft(test_content, draft_type='technical')
        
        assert result['draft_type'] == 'technical'
        # Technical drafts should have different scoring
        assert 'analysis' in result
        assert 'technical' in result['analysis']
    
    def test_content_analysis(self):
        """Test content analysis component"""
        test_content = "This is a well-structured test content with multiple sentences. It provides adequate length for meaningful analysis."
        
        analysis = self.review_logic._analyze_content(test_content)
        
        assert 'score' in analysis
        assert 'word_count' in analysis
        assert 'char_count' in analysis
        assert 'sentence_count' in analysis
        assert 'issues' in analysis
        assert 'strengths' in analysis
        assert analysis['word_count'] > 0
        assert analysis['char_count'] > 0
    
    def test_content_analysis_short_content(self):
        """Test content analysis with very short content"""
        short_content = "Too short"
        
        analysis = self.review_logic._analyze_content(short_content)
        
        assert analysis['word_count'] == 2
        assert any('too brief' in issue.lower() or 'too short' in issue.lower() for issue in analysis['issues'])
    
    def test_structure_analysis(self):
        """Test structure analysis component"""
        test_content = """First paragraph with some content.

Second paragraph that demonstrates structure.

Third paragraph for better organization."""
        
        analysis = self.review_logic._analyze_structure(test_content)
        
        assert 'score' in analysis
        assert 'paragraph_count' in analysis
        assert 'line_count' in analysis
        assert analysis['paragraph_count'] == 3
        assert any('multiple paragraphs' in strength.lower() for strength in analysis['strengths'])
    
    def test_structure_analysis_single_paragraph(self):
        """Test structure analysis with single long paragraph"""
        long_single_paragraph = "This is a very long single paragraph that should be broken into multiple paragraphs for better readability and structure. " * 10
        
        analysis = self.review_logic._analyze_structure(long_single_paragraph)
        
        assert analysis['paragraph_count'] == 1
        assert any('breaking into multiple paragraphs' in issue.lower() for issue in analysis['issues'])
    
    def test_style_analysis(self):
        """Test style analysis component"""
        test_content = "This is well-written content with proper punctuation."
        
        analysis = self.review_logic._analyze_style(test_content)
        
        assert 'score' in analysis
        assert 'issues' in analysis
        assert 'strengths' in analysis
        assert any('proper' in strength.lower() for strength in analysis['strengths'])
    
    def test_technical_analysis_general(self):
        """Test technical analysis for general content"""
        test_content = "This is general content without technical elements."
        
        analysis = self.review_logic._analyze_technical(test_content, 'general')
        
        assert 'score' in analysis
        assert analysis['draft_type'] == 'general'
        assert 'issues' in analysis
        assert 'strengths' in analysis
    
    def test_technical_analysis_technical(self):
        """Test technical analysis for technical content"""
        test_content = "This technical document describes the algorithm implementation with proper references and citations."
        
        analysis = self.review_logic._analyze_technical(test_content, 'technical')
        
        assert analysis['draft_type'] == 'technical'
        # Should detect references
        assert any('references' in strength.lower() or 'citations' in strength.lower() for strength in analysis['strengths'])
    
    def test_suggestion_generation(self):
        """Test suggestion generation"""
        # Create mock analyses with various score levels
        content_analysis = {'score': 50, 'issues': ['Content too brief'], 'strengths': []}
        structure_analysis = {'score': 85, 'issues': [], 'strengths': ['Good structure']}
        style_analysis = {'score': 70, 'issues': ['Minor style issues'], 'strengths': []}
        technical_analysis = {'score': 90, 'issues': [], 'strengths': ['Technical accuracy']}
        
        suggestions = self.review_logic._generate_suggestions(
            content_analysis, structure_analysis, style_analysis, technical_analysis
        )
        
        assert isinstance(suggestions, list)
        # Should have suggestions for issues and strengths
        improvement_suggestions = [s for s in suggestions if s['suggestion_type'] == 'improvement']
        strength_suggestions = [s for s in suggestions if s['suggestion_type'] == 'strength']
        
        assert len(improvement_suggestions) > 0
        assert len(strength_suggestions) > 0
        
        # Check priority assignment
        high_priority = [s for s in suggestions if s['priority'] == 'high']
        assert len(high_priority) > 0  # Content score of 50 should generate high priority
    
    def test_recommendation_generation(self):
        """Test recommendation generation based on scores"""
        assert "Excellent" in self.review_logic._get_recommendation(95)
        assert "Strong" in self.review_logic._get_recommendation(85)
        assert "Good" in self.review_logic._get_recommendation(75)
        assert "improvement" in self.review_logic._get_recommendation(65)
        assert "Major revision" in self.review_logic._get_recommendation(45)
        assert "Substantial" in self.review_logic._get_recommendation(25)
    
    def test_error_handling(self):
        """Test error handling in analysis"""
        # Mock a scenario that might cause an error
        rl = ReviewLogic()
        
        # Override a method to cause an error
        original_method = rl._analyze_content
        rl._analyze_content = lambda x: 1/0  # This will cause ZeroDivisionError
        
        result = rl.analyze_draft("test content")
        
        # Restore original method
        rl._analyze_content = original_method
        
        assert result['overall_score'] == 0.0
        assert 'error' in result
        assert 'Review failed' in result['recommendation']
    
    def test_configuration_methods(self):
        """Test configuration getter and setter methods"""
        rl = ReviewLogic()
        
        # Test getter
        config = rl.get_review_configuration()
        assert 'criteria' in config
        assert 'weights' in config
        assert 'categories' in config
        
        # Test setter
        new_criteria = {'content': ['clarity'], 'style': ['tone']}
        new_weights = {'content': 0.8, 'style': 0.2}
        
        success = rl.update_configuration(criteria=new_criteria, weights=new_weights)
        assert success
        assert rl.review_criteria == new_criteria
        assert rl.review_weights == new_weights
    
    def test_integration_with_custom_reviewer_name(self):
        """Test integration with custom reviewer name"""
        result = self.review_logic.analyze_draft(
            "Test content for analysis", 
            reviewer_name="TestReviewer"
        )
        
        assert result['reviewer'] == "TestReviewer"
    
    def test_comprehensive_analysis_workflow(self):
        """Test complete analysis workflow with realistic content"""
        realistic_content = """
        # Project Analysis Report

        This document provides a comprehensive analysis of the current project status. 
        
        ## Executive Summary
        
        The project has made significant progress in the past quarter. Key achievements include implementation of core features and successful testing phases.
        
        ## Technical Details
        
        The system architecture follows industry best practices with proper separation of concerns. The implementation utilizes modern frameworks and maintains high code quality standards.
        
        ## Recommendations
        
        Based on the analysis, we recommend proceeding with the deployment phase while monitoring performance metrics closely.
        """
        
        result = self.review_logic.analyze_draft(realistic_content, draft_type='technical')
        
        # Verify comprehensive analysis
        assert result['overall_score'] > 0
        assert len(result['analysis']) == 4  # All four categories analyzed
        assert len(result['suggestions']) > 0
        assert result['recommendation'] is not None
        assert result['draft_type'] == 'technical'
        
        # Verify detailed analysis components
        content_analysis = result['analysis']['content']
        assert content_analysis['word_count'] > 50
        assert content_analysis['sentence_count'] > 5
        
        structure_analysis = result['analysis']['structure']
        assert structure_analysis['paragraph_count'] >= 2  # Adjusted expectation
        assert structure_analysis['header_count'] > 0
        
        # Should recognize good structure and headers
        assert any('header' in strength.lower() for strength in structure_analysis['strengths'])

if __name__ == '__main__':
    pytest.main([__file__]) 