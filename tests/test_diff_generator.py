"""
Tests for DiffGenerator component
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from swarm_director.agents.diff_generator import DiffGenerator


class TestDiffGenerator:
    """Test suite for DiffGenerator component"""
    
    @pytest.fixture
    def diff_generator(self):
        """Create DiffGenerator instance for testing"""
        return DiffGenerator()
    
    @pytest.fixture
    def diff_generator_custom_config(self):
        """Create DiffGenerator with custom configuration"""
        config = {
            'min_confidence': 0.5,
            'max_diffs': 20,
            'context_lines': 3,
            'word_diff_threshold': 0.7
        }
        return DiffGenerator(config)
    
    @pytest.fixture
    def sample_suggestions(self):
        """Create sample suggestions for testing"""
        return [
            {
                'issue': 'Missing proper ending punctuation',
                'category': 'style',
                'priority': 'medium',
                'suggestion_type': 'improvement'
            },
            {
                'issue': 'Consider breaking long paragraphs for better readability',
                'category': 'structure',
                'priority': 'high',
                'suggestion_type': 'improvement'
            },
            {
                'issue': 'Add section headers for better organization',
                'category': 'structure',
                'priority': 'medium',
                'suggestion_type': 'improvement'
            }
        ]
    
    def test_initialization_default_config(self, diff_generator):
        """Test DiffGenerator initialization with default configuration"""
        assert diff_generator.min_confidence == 0.3
        assert diff_generator.max_diffs == 50
        assert diff_generator.context_lines == 2
        assert diff_generator.word_diff_threshold == 0.6
    
    def test_initialization_custom_config(self, diff_generator_custom_config):
        """Test DiffGenerator initialization with custom configuration"""
        assert diff_generator_custom_config.min_confidence == 0.5
        assert diff_generator_custom_config.max_diffs == 20
        assert diff_generator_custom_config.context_lines == 3
        assert diff_generator_custom_config.word_diff_threshold == 0.7
    
    def test_generate_diff_empty_original(self, diff_generator):
        """Test diff generation with empty original content"""
        result = diff_generator.generate_diff("")
        
        assert len(result) == 1
        assert result[0]['type'] == 'info'
        assert 'No original content provided' in result[0]['reason']
        assert result[0]['confidence'] == 1.0
    
    def test_generate_diff_from_suggestions(self, diff_generator, sample_suggestions):
        """Test diff generation from review suggestions"""
        original = "This is a test sentence without proper ending"
        
        result = diff_generator.generate_diff(
            original=original,
            suggestions=sample_suggestions
        )
        
        assert len(result) > 0
        assert all('type' in diff for diff in result)
        assert all('confidence' in diff for diff in result)
        assert all('reason' in diff for diff in result)
        
        # Check that at least one diff addresses punctuation
        punctuation_diffs = [d for d in result if 'punctuation' in d.get('reason', '').lower()]
        assert len(punctuation_diffs) > 0
    
    def test_generate_diff_text_comparison(self, diff_generator):
        """Test diff generation from text comparison"""
        original = "This is the original text.\nWith multiple lines."
        modified = "This is the modified text.\nWith multiple lines.\nAnd an additional line."
        
        result = diff_generator.generate_diff(
            original=original,
            modified=modified
        )
        
        assert len(result) > 0
        assert any(diff['type'] == 'insertion' for diff in result)
        
        # Check that diffs have proper metadata
        for diff in result:
            assert 'type' in diff
            assert 'line' in diff
            assert 'confidence' in diff
            assert 'timestamp' in diff
            assert 'category' in diff
    
    def test_target_punctuation_issues(self, diff_generator):
        """Test targeting punctuation-related issues"""
        original = "This sentence has no period"
        suggestions = [{
            'issue': 'Missing proper ending punctuation',
            'category': 'style',
            'priority': 'medium',
            'suggestion_type': 'improvement'
        }]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # Should find punctuation issue
        punct_diff = next((d for d in result if 'punctuation' in d.get('reason', '').lower()), None)
        assert punct_diff is not None
        assert punct_diff['type'] == 'modification'
        assert 'original' in punct_diff
        assert 'suggested' in punct_diff
        assert punct_diff['suggested'].endswith('.')
    
    def test_target_structure_issues(self, diff_generator):
        """Test targeting structure-related issues"""
        original = "This is a very long line that should probably be broken into multiple paragraphs for better readability and user experience. It contains multiple sentences and ideas that could be separated."
        suggestions = [{
            'issue': 'Consider breaking long paragraphs for better readability',
            'category': 'structure',
            'priority': 'high',
            'suggestion_type': 'improvement'
        }]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # Should find structure issue
        structure_diff = next((d for d in result if 'paragraph' in d.get('reason', '').lower()), None)
        assert structure_diff is not None
        assert structure_diff['type'] in ['split', 'insertion', 'general']
    
    def test_target_organization_issues(self, diff_generator):
        """Test targeting organization-related issues"""
        original = "Some content without headers"
        suggestions = [{
            'issue': 'Add section headers for better organization',
            'category': 'structure',
            'priority': 'medium',
            'suggestion_type': 'improvement'
        }]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # Should find organization issue
        org_diff = next((d for d in result if 'header' in d.get('reason', '').lower()), None)
        assert org_diff is not None
        assert org_diff['type'] in ['insertion', 'general']
    
    def test_word_level_diff(self, diff_generator):
        """Test word-level diff generation"""
        original = "The quick brown fox"
        modified = "The slow brown fox"
        
        result = diff_generator.generate_diff(original=original, modified=modified)
        
        # Should have word-level changes for single-line modifications
        modification_diff = next((d for d in result if d['type'] == 'modification'), None)
        if modification_diff and 'word_changes' in modification_diff:
            word_changes = modification_diff['word_changes']
            assert len(word_changes) > 0
            assert any(change['type'] == 'modification' for change in word_changes)
    
    def test_confidence_calculation(self, diff_generator):
        """Test confidence score calculation"""
        original = "Test content"
        suggestions = [
            {
                'issue': 'High priority grammar issue',
                'category': 'grammar',
                'priority': 'high',
                'suggestion_type': 'improvement'
            },
            {
                'issue': 'Low priority style issue',
                'category': 'style',
                'priority': 'low',
                'suggestion_type': 'improvement'
            }
        ]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # High priority suggestions should have higher confidence
        high_priority_diff = next((d for d in result if 'high priority' in d.get('reason', '').lower()), None)
        low_priority_diff = next((d for d in result if 'low priority' in d.get('reason', '').lower()), None)
        
        if high_priority_diff and low_priority_diff:
            assert high_priority_diff['confidence'] > low_priority_diff['confidence']
    
    def test_diff_sorting_and_limiting(self, diff_generator):
        """Test diff sorting by confidence and limiting"""
        original = "Test content"
        suggestions = [
            {
                'issue': f'Issue {i}',
                'category': 'general',
                'priority': 'medium' if i % 2 == 0 else 'low',
                'suggestion_type': 'improvement'
            }
            for i in range(10)
        ]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # Results should be sorted by confidence (descending)
        confidences = [diff['confidence'] for diff in result if 'confidence' in diff]
        assert confidences == sorted(confidences, reverse=True)
        
        # Should not exceed max_diffs
        assert len(result) <= diff_generator.max_diffs
    
    def test_error_handling(self, diff_generator):
        """Test error handling in diff generation"""
        original = "Test content"
        
        # Test with malformed suggestions
        malformed_suggestions = [
            {'invalid': 'suggestion'},
            None,
            {}
        ]
        
        result = diff_generator.generate_diff(original=original, suggestions=malformed_suggestions)
        
        # Should handle errors gracefully and still return results
        assert isinstance(result, list)
        
    def test_informational_diff(self, diff_generator):
        """Test informational diff when no changes or suggestions"""
        original = "This is test content for analysis."
        
        result = diff_generator.generate_diff(original=original)
        
        assert len(result) == 1
        assert result[0]['type'] == 'info'
        assert 'analyzed' in result[0]['reason'].lower()
        assert 'metadata' in result[0]
        assert result[0]['metadata']['word_count'] > 0
        assert result[0]['metadata']['line_count'] > 0
        assert result[0]['metadata']['char_count'] > 0
    
    def test_config_update(self, diff_generator):
        """Test configuration update"""
        new_config = {
            'min_confidence': 0.8,
            'max_diffs': 10
        }
        
        success = diff_generator.update_config(new_config)
        
        assert success is True
        assert diff_generator.min_confidence == 0.8
        assert diff_generator.max_diffs == 10
    
    def test_get_config(self, diff_generator):
        """Test getting current configuration"""
        config = diff_generator.get_config()
        
        assert 'min_confidence' in config
        assert 'max_diffs' in config
        assert 'context_lines' in config
        assert 'word_diff_threshold' in config
        
        assert config['min_confidence'] == diff_generator.min_confidence
        assert config['max_diffs'] == diff_generator.max_diffs
    
    def test_suggestion_type_determination(self, diff_generator):
        """Test suggestion type determination"""
        original = "Test content"
        
        suggestions = [
            {
                'issue': 'Add more details',
                'suggestion_type': 'improvement'
            },
            {
                'issue': 'Remove unnecessary content',
                'suggestion_type': 'improvement'
            },
            {
                'issue': 'Change the wording',
                'suggestion_type': 'improvement'
            }
        ]
        
        result = diff_generator.generate_diff(original=original, suggestions=suggestions)
        
        # Should categorize different types of suggestions appropriately
        types = {diff['type'] for diff in result}
        
        # Should include various diff types based on suggestion content
        assert len(types) > 0
        assert all(t in ['insertion', 'deletion', 'modification', 'general'] for t in types)
    
    def test_context_preservation(self, diff_generator):
        """Test that context information is preserved in diffs"""
        original = "Test content"
        suggestions = [{
            'issue': 'Test issue',
            'category': 'test_category',
            'priority': 'high'
        }]
        context = {
            'draft_type': 'email',
            'reviewer': 'TestReviewer'
        }
        
        result = diff_generator.generate_diff(
            original=original,
            suggestions=suggestions,
            context=context
        )
        
        # Context should be available in the generation process
        assert len(result) > 0
        
        # Check that category and priority from suggestions are preserved
        for diff in result:
            if diff.get('category') and diff.get('priority'):
                assert diff['category'] == 'test_category'
                assert diff['priority'] == 'high' 