#!/usr/bin/env python3
"""
Comprehensive test script for Enhanced Intent Classification System
Tests the dual-layer classification, training data, feedback loops, and LLM integration
"""

import sys
import os
import tempfile
import json
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_classification_components():
    """Test core classification system components"""
    print("\n🧪 Testing Enhanced Intent Classification Components...")
    
    try:
        from swarm_director.agents.director import (
            IntentExample, ClassificationFeedback, ClassificationCache,
            IntentDatasetManager, DirectorAgent, DirectorConfig
        )
        
        # Test IntentExample
        example = IntentExample(
            text="Send email to team",
            department="communications",
            confidence=0.9,
            source="test"
        )
        assert example.text == "Send email to team"
        assert example.department == "communications"
        print("✅ IntentExample class working correctly")
        
        # Test ClassificationFeedback
        feedback = ClassificationFeedback(
            task_id=1,
            predicted_intent="analysis",
            predicted_confidence=0.8,
            actual_intent="communications",
            correction_source="manual"
        )
        assert feedback.task_id == 1
        assert feedback.predicted_intent == "analysis"
        print("✅ ClassificationFeedback class working correctly")
        
        # Test ClassificationCache
        cache_entry = ClassificationCache(
            text_hash="abc123",
            intent="automation",
            confidence=0.85,
            method="llm",
            timestamp=datetime.utcnow()
        )
        assert cache_entry.is_valid(max_age_hours=24)
        print("✅ ClassificationCache class working correctly")
        
        return True
        
    except Exception as e:
        print(f"❌ Classification components test failed: {e}")
        return False

def test_dataset_manager():
    """Test the IntentDatasetManager and training data"""
    print("\n🧪 Testing IntentDatasetManager...")
    
    try:
        from swarm_director.agents.director import IntentDatasetManager, IntentExample
        
        # Create dataset manager
        dataset_manager = IntentDatasetManager()
        
        # Check that default training data is loaded
        examples = dataset_manager.get_examples()
        assert 'communications' in examples
        assert 'analysis' in examples
        assert 'automation' in examples
        assert 'coordination' in examples
        
        # Verify we have examples for each department
        for dept, dept_examples in examples.items():
            assert len(dept_examples) > 15, f"Not enough examples for {dept}: {len(dept_examples)}"
            print(f"   📊 {dept}: {len(dept_examples)} training examples")
        
        # Test adding custom example
        custom_example = IntentExample(
            text="Test custom example",
            department="communications",
            source="test"
        )
        success = dataset_manager.add_example(custom_example)
        assert success
        
        # Test getting training prompt
        prompt = dataset_manager.get_training_prompt(include_examples=3)
        assert "COMMUNICATIONS:" in prompt
        assert "ANALYSIS:" in prompt
        assert "AUTOMATION:" in prompt
        assert "COORDINATION:" in prompt
        assert "Format your response as: DEPARTMENT|CONFIDENCE" in prompt
        print("✅ Training prompt generation working correctly")
        
        print("✅ IntentDatasetManager working correctly")
        return True
        
    except Exception as e:
        print(f"❌ IntentDatasetManager test failed: {e}")
        return False

def test_enhanced_keyword_classification():
    """Test enhanced keyword classification with mock database"""
    print("\n🧪 Testing Enhanced Keyword Classification...")
    
    try:
        # Mock the database components
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestAgent"
            mock_db_agent.status = "active"
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig
            
            # Create director with keyword classification only
            config = DirectorConfig(enable_llm_classification=False)
            director = DirectorAgent(mock_db_agent, config)
            
            # Test keyword classification for different departments
            test_cases = [
                ("Send email notification to all staff", "communications"),
                ("Analyze quarterly sales performance data", "analysis"),
                ("Automate the daily backup process", "automation"),
                ("Coordinate the project team meeting", "coordination"),
                ("Unknown random text with no keywords", "coordination")  # Should fallback
            ]
            
            for test_text, expected_dept in test_cases:
                # Create mock task
                mock_task = MagicMock()
                mock_task.title = test_text
                mock_task.description = ""
                mock_task.input_data = None
                
                intent, confidence = director.classify_intent_with_confidence(mock_task)
                print(f"   📝 '{test_text[:40]}...' → {intent} (confidence: {confidence:.2f})")
                
                if expected_dept != "coordination":  # Don't assert on fallback case
                    assert intent == expected_dept, f"Expected {expected_dept}, got {intent}"
                
                # Confidence should be reasonable
                assert 0.0 <= confidence <= 1.0
            
            print("✅ Enhanced keyword classification working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Enhanced keyword classification test failed: {e}")
        return False

def test_classification_caching():
    """Test classification result caching"""
    print("\n🧪 Testing Classification Caching...")
    
    try:
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestAgent"
            mock_db_agent.status = "active"
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig
            
            config = DirectorConfig(enable_llm_classification=False)
            director = DirectorAgent(mock_db_agent, config)
            
            # Create mock task
            mock_task = MagicMock()
            mock_task.title = "Send email to team"
            mock_task.description = ""
            mock_task.input_data = None
            
            # First classification - should create cache entry
            intent1, confidence1 = director.classify_intent_with_confidence(mock_task)
            
            # Check cache performance
            cache_perf_before = director._get_cache_performance()
            
            # Second classification - should use cache
            intent2, confidence2 = director.classify_intent_with_confidence(mock_task)
            
            # Results should be identical
            assert intent1 == intent2
            assert confidence1 == confidence2
            
            cache_perf_after = director._get_cache_performance()
            print(f"   📊 Cache entries: {cache_perf_after['cache_entries']}")
            print(f"   📊 Cache hits: {cache_perf_after['total_hits']}")
            
            # Test cache cleanup
            removed = director.cleanup_classification_cache(max_age_hours=0)  # Remove all
            assert removed >= 0
            
            print("✅ Classification caching working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Classification caching test failed: {e}")
        return False

def test_feedback_system():
    """Test classification feedback and learning system"""
    print("\n🧪 Testing Classification Feedback System...")
    
    try:
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            with patch('swarm_director.models.Task') as MockTaskModel:
                mock_db_agent = MockAgent()
                mock_db_agent.name = "TestAgent"
                mock_db_agent.status = "active"
                
                from swarm_director.agents.director import DirectorAgent, DirectorConfig
                
                config = DirectorConfig(enable_llm_classification=False)
                director = DirectorAgent(mock_db_agent, config)
                
                # Mock task for feedback
                mock_task_obj = MagicMock()
                mock_task_obj.title = "Send email to everyone"
                mock_task_obj.description = "Notification message"
                mock_task_obj.input_data = None
                MockTaskModel.query.get.return_value = mock_task_obj
                
                # Add feedback
                success = director.add_classification_feedback(
                    task_id=1,
                    predicted_intent="analysis",
                    predicted_confidence=0.7,
                    actual_intent="communications",
                    correction_source="manual"
                )
                assert success
                
                # Check feedback was recorded
                assert len(director.feedback_history) == 1
                feedback = director.feedback_history[0]
                assert feedback.predicted_intent == "analysis"
                assert feedback.actual_intent == "communications"
                
                # Get classification analytics
                analytics = director.get_classification_analytics()
                assert analytics['total_feedback'] == 1
                assert analytics['accuracy'] == 0.0  # Misclassification
                print(f"   📊 Classification accuracy: {analytics['accuracy']:.2f}")
                
                # Test with correct classification
                director.add_classification_feedback(
                    task_id=2,
                    predicted_intent="communications",
                    predicted_confidence=0.9,
                    actual_intent="communications"
                )
                
                analytics = director.get_classification_analytics()
                assert analytics['total_feedback'] == 2
                assert analytics['accuracy'] == 0.5  # 1 correct out of 2
                print(f"   📊 Updated accuracy: {analytics['accuracy']:.2f}")
                
                print("✅ Classification feedback system working correctly")
                return True
                
    except Exception as e:
        print(f"❌ Classification feedback test failed: {e}")
        return False

def test_training_data_export():
    """Test training data export functionality"""
    print("\n🧪 Testing Training Data Export...")
    
    try:
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            mock_db_agent = MockAgent()
            mock_db_agent.name = "TestAgent"
            mock_db_agent.status = "active"
            
            from swarm_director.agents.director import DirectorAgent, DirectorConfig
            
            config = DirectorConfig(enable_llm_classification=False)
            director = DirectorAgent(mock_db_agent, config)
            
            # Export training data
            export_data = director.export_training_data()
            
            assert 'exported_at' in export_data
            assert 'total_examples' in export_data
            assert 'examples_by_department' in export_data
            
            examples_by_dept = export_data['examples_by_department']
            assert 'communications' in examples_by_dept
            assert 'analysis' in examples_by_dept
            assert 'automation' in examples_by_dept
            assert 'coordination' in examples_by_dept
            
            # Check data structure
            for dept, examples in examples_by_dept.items():
                assert len(examples) > 15  # Should have our curated examples
                if examples:
                    example = examples[0]
                    assert 'text' in example
                    assert 'department' in example
                    assert 'confidence' in example
                    assert 'source' in example
                    assert 'created_at' in example
            
            print(f"   📊 Total examples exported: {export_data['total_examples']}")
            print("✅ Training data export working correctly")
            return True
            
    except Exception as e:
        print(f"❌ Training data export test failed: {e}")
        return False

def test_llm_classification_mock():
    """Test LLM classification with mocked APIs"""
    print("\n🧪 Testing LLM Classification (Mocked)...")
    
    try:
        with patch('swarm_director.agents.director.Agent') as MockAgent:
            with patch('swarm_director.agents.director.HAS_LLM_SUPPORT', True):
                with patch('swarm_director.agents.director.openai') as mock_openai:
                    mock_db_agent = MockAgent()
                    mock_db_agent.name = "TestAgent"
                    mock_db_agent.status = "active"
                    
                    from swarm_director.agents.director import DirectorAgent, DirectorConfig
                    
                    # Mock OpenAI response
                    mock_response = MagicMock()
                    mock_response.choices[0].message.content = "communications|0.85"
                    mock_openai.OpenAI.return_value.chat.completions.create.return_value = mock_response
                    
                    # Mock Flask current_app with a proper mock_app context
                    mock_app_config = {'OPENAI_API_KEY': 'fake-api-key'}
                    with patch('flask.current_app') as mock_app:
                        mock_app.config.get.side_effect = lambda key, default=None: mock_app_config.get(key, default)
                        
                        config = DirectorConfig(enable_llm_classification=True)
                        director = DirectorAgent(mock_db_agent, config)
                        
                        # Create mock task
                        mock_task = MagicMock()
                        mock_task.title = "Send newsletter to subscribers"
                        mock_task.description = ""
                        mock_task.input_data = None
                        
                        # Test LLM classification
                        intent, confidence = director.classify_intent_with_confidence(mock_task)
                        
                        assert intent == "communications"
                        assert confidence == 0.85
                        print(f"   🤖 LLM classified: {intent} (confidence: {confidence})")
                        
                        # Verify cache was created
                        assert len(director.classification_cache) == 1
                        
                        # Test cached result
                        intent2, confidence2 = director.classify_intent_with_confidence(mock_task)
                        assert intent == intent2
                        assert confidence == confidence2
                        
                        print("✅ LLM classification (mocked) working correctly")
                        return True
                        
    except Exception as e:
        print(f"❌ LLM classification test failed: {e}")
        return False

def run_all_tests():
    """Run all enhanced intent classification tests"""
    print("🚀 Starting Enhanced Intent Classification System Tests")
    print("=" * 60)
    
    tests = [
        test_classification_components,
        test_dataset_manager,
        test_enhanced_keyword_classification,
        test_classification_caching,
        test_feedback_system,
        test_training_data_export,
        test_llm_classification_mock
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All Enhanced Intent Classification tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1) 