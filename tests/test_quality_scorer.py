"""
Test suite for QualityScorer component
"""

import pytest
from src.swarm_director.agents.quality_scorer import QualityScorer


def test_quality_scorer_initialization():
    """Test basic QualityScorer initialization"""
    scorer = QualityScorer()
    assert scorer is not None
    assert scorer.scoring_config is not None
    assert 'dimensions' in scorer.scoring_config


def test_quality_scorer_content_scoring():
    """Test content scoring functionality"""
    scorer = QualityScorer()
    
    content = "This is a well-structured document with good content."
    result = scorer.score_content(content)
    
    assert 'score' in result
    assert 'dimension' in result
    assert result['dimension'] == 'content'
    assert isinstance(result['score'], float)
    assert 0 <= result['score'] <= 100


def test_quality_scorer_comprehensive_scoring():
    """Test comprehensive scoring functionality"""
    scorer = QualityScorer()
    
    content = """This is a comprehensive test document.
    
    It has multiple paragraphs and good structure.
    The content demonstrates various quality aspects.
    """
    
    result = scorer.score_draft_comprehensive(content)
    
    assert 'overall_score' in result
    assert 'dimension_scores' in result
    assert 'overall_grade' in result
    assert isinstance(result['overall_score'], float)
    assert 0 <= result['overall_score'] <= 100


def test_quality_scorer_empty_content():
    """Test scoring with empty content"""
    scorer = QualityScorer()
    
    result = scorer.score_content("")
    assert result['score'] == 0.0
    assert 'error' in result


def test_quality_scorer_config_management():
    """Test configuration management"""
    scorer = QualityScorer()
    
    config = scorer.get_scoring_config()
    assert isinstance(config, dict)
    assert 'dimensions' in config
    
    # Test updating config
    new_config = {'dimensions': {'content': {'weight': 0.5}}}
    success = scorer.update_scoring_config(new_config)
    assert success is True
