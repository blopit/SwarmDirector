"""
Tests for conversation analytics functionality
"""
import unittest
import json
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

from src.swarm_director.models.base import db
from src.swarm_director.models.conversation import (
    Conversation, Message, ConversationAnalytics, 
    MessageType, ConversationStatus, OrchestrationPattern
)
from src.swarm_director.models.agent import Agent, AgentType, AgentStatus
from src.swarm_director.utils.conversation_analytics import ConversationAnalyticsEngine
from src.swarm_director.app import create_app


class TestConversationAnalytics(unittest.TestCase):
    """Test conversation analytics functionality"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        
        # Create database tables
        db.create_all()
        
        # Create test agents
        self.agent1 = Agent(
            name="TestAgent1",
            agent_type=AgentType.COORDINATOR,
            status=AgentStatus.ACTIVE
        )
        self.agent1.save()
        
        self.agent2 = Agent(
            name="TestAgent2", 
            agent_type=AgentType.WORKER,
            status=AgentStatus.ACTIVE
        )
        self.agent2.save()
        
        # Create test conversation with autogen chat history
        autogen_history = [
            {"name": "TestAgent1", "content": "Hello, let's start working on this task."},
            {"name": "TestAgent2", "content": "Sure, I'm ready to help. What do we need to do?"},
            {"name": "TestAgent1", "content": "Perfect! We've successfully completed the task."}
        ]
        
        self.conversation = Conversation(
            title="Test Conversation",
            description="Test conversation for analytics", 
            status=ConversationStatus.ACTIVE,
            initiator_agent_id=self.agent1.id,
            session_id="test_session_123",
            conversation_type="test",
            orchestration_pattern=OrchestrationPattern.EXPERTISE_BASED,
            start_time=datetime.utcnow() - timedelta(minutes=10),
            autogen_chat_history=autogen_history
        )
        self.conversation.save()
        
        # Create test messages
        self._create_test_messages()
        
        # Initialize analytics engine
        self.analytics_engine = ConversationAnalyticsEngine()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def _create_test_messages(self):
        """Create test messages for the conversation"""
        messages_data = [
            {
                "content": "Hello, let's start working on this task.",
                "sender_agent_id": self.agent1.id,
                "agent_name": "TestAgent1",
                "message_type": MessageType.AGENT_RESPONSE,
                "response_time": 1.5,
                "tokens_used": 10
            },
            {
                "content": "Sure, I'm ready to help. What do we need to do?",
                "sender_agent_id": self.agent2.id,
                "agent_name": "TestAgent2", 
                "message_type": MessageType.AGENT_RESPONSE,
                "response_time": 2.0,
                "tokens_used": 12
            },
            {
                "content": "Perfect! We've successfully completed the task.",
                "sender_agent_id": self.agent1.id,
                "agent_name": "TestAgent1",
                "message_type": MessageType.AGENT_RESPONSE,
                "response_time": 2.2,
                "tokens_used": 9
            }
        ]
        
        base_time = datetime.utcnow() - timedelta(minutes=8)
        for i, msg_data in enumerate(messages_data):
            message = Message(
                conversation_id=self.conversation.id,
                content=msg_data["content"],
                message_type=msg_data["message_type"],
                sender_agent_id=msg_data["sender_agent_id"],
                agent_name=msg_data["agent_name"],
                response_time=msg_data["response_time"],
                tokens_used=msg_data["tokens_used"],
                message_length=len(msg_data["content"]),
                created_at=base_time + timedelta(minutes=i)
            )
            message.save()
    
    def test_analyze_conversation_creates_analytics(self):
        """Test that analyzing a conversation creates analytics record"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.conversation_id, self.conversation.id)
        self.assertIsNotNone(analytics.total_duration)
        self.assertIsNotNone(analytics.total_characters)
        self.assertEqual(analytics.total_participants, 2)
    
    def test_timing_metrics_calculation(self):
        """Test timing metrics are calculated correctly"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should have timing data
        self.assertIsNotNone(analytics.total_duration)
        self.assertIsNotNone(analytics.avg_message_interval)
        self.assertIsNotNone(analytics.fastest_response)
        self.assertIsNotNone(analytics.slowest_response)
        
        # Verify response time bounds
        self.assertGreaterEqual(analytics.fastest_response, 1.5)
        self.assertLessEqual(analytics.slowest_response, 3.0)
    
    def test_content_metrics_calculation(self):
        """Test content metrics are calculated correctly"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should have content metrics
        self.assertIsNotNone(analytics.total_characters)
        self.assertIsNotNone(analytics.avg_message_length)
        self.assertIsNotNone(analytics.unique_words)
        self.assertIsNotNone(analytics.vocabulary_richness)
        
        # Verify vocabulary richness is a valid ratio
        self.assertGreaterEqual(analytics.vocabulary_richness, 0)
        self.assertLessEqual(analytics.vocabulary_richness, 1)
    
    def test_participation_metrics_calculation(self):
        """Test participation metrics are calculated correctly"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should have participation metrics
        self.assertEqual(analytics.total_participants, 2)
        self.assertIn(analytics.most_active_agent, ["TestAgent1", "TestAgent2"])
        self.assertIsNotNone(analytics.participation_balance)
        
        # Participation balance should be between 0 and 1
        self.assertGreaterEqual(analytics.participation_balance, 0)
        self.assertLessEqual(analytics.participation_balance, 1)
    
    def test_quality_metrics_calculation(self):
        """Test quality metrics are calculated correctly"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should have quality metrics
        self.assertEqual(analytics.error_count, 0)  # No error messages in test data
        self.assertIsNotNone(analytics.goal_achievement)
        self.assertEqual(analytics.completion_status, "active")
        
        # Goal achievement should be reasonable for active conversation
        self.assertGreater(analytics.goal_achievement, 0)
        self.assertLessEqual(analytics.goal_achievement, 100)
    
    def test_autogen_metrics_calculation(self):
        """Test AutoGen-specific metrics are calculated"""
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should have AutoGen metrics
        self.assertIsNotNone(analytics.group_chat_efficiency)
        self.assertIsNotNone(analytics.agent_collaboration_score)
        
        # Scores should be in valid range
        if analytics.group_chat_efficiency is not None:
            self.assertGreaterEqual(analytics.group_chat_efficiency, 0)
            self.assertLessEqual(analytics.group_chat_efficiency, 100)
    
    def test_sentiment_analysis(self):
        """Test sentiment analysis functionality"""
        # Test positive sentiment
        positive_score = self.analytics_engine._analyze_message_sentiment(
            "This is great! Excellent work and amazing results."
        )
        self.assertGreater(positive_score, 0)
        
        # Test negative sentiment
        negative_score = self.analytics_engine._analyze_message_sentiment(
            "This is terrible. Bad results and awful problems."
        )
        self.assertLess(negative_score, 0)
        
        # Test neutral sentiment
        neutral_score = self.analytics_engine._analyze_message_sentiment(
            "This is a normal message with standard content."
        )
        self.assertAlmostEqual(neutral_score, 0, places=1)
    
    def test_conversation_insights_generation(self):
        """Test conversation insights generation"""
        insights = self.analytics_engine.get_conversation_insights(self.conversation.id)
        
        self.assertIn('summary', insights)
        self.assertIn('recommendations', insights)
        self.assertIn('analytics', insights)
        
        # Summary should contain key information
        summary = insights['summary']
        self.assertIn('duration', summary)
        self.assertIn('participation', summary)
        self.assertIn('performance', summary)
        
        # Recommendations should be a list
        self.assertIsInstance(insights['recommendations'], list)
    
    def test_api_analytics_summary_endpoint(self):
        """Test the analytics summary API endpoint"""
        self.conversation.complete_conversation()
        self.analytics_engine.analyze_conversation(self.conversation.id)
        
        response = self.client.get('/api/analytics/summary')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('summary', data)
    
    def test_api_conversation_analytics_endpoint(self):
        """Test the conversation analytics API endpoint"""
        response = self.client.get('/api/analytics/conversations')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('conversations', data)
        self.assertIsInstance(data['conversations'], list)
    
    def test_api_conversation_detail_endpoint(self):
        """Test the conversation detail API endpoint"""
        response = self.client.get(f'/api/analytics/conversations/{self.conversation.id}')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('conversation', data)
        self.assertIn('insights', data)
    
    def test_api_regenerate_analytics_endpoint(self):
        """Test the regenerate analytics API endpoint"""
        response = self.client.post(f'/api/analytics/conversations/{self.conversation.id}/regenerate')
        self.assertEqual(response.status_code, 200)
        
        data = json.loads(response.data)
        self.assertEqual(data['status'], 'success')
        self.assertIn('analytics', data)
    
    def test_conversation_session_manager_integration(self):
        """Test ConversationSessionManager integration"""
        from src.swarm_director.utils.autogen_integration import ConversationSessionManager
        
        session_manager = ConversationSessionManager("test_session_456")
        
        # Start a new conversation
        conversation = session_manager.start_conversation(
            title="Integration Test",
            description="Testing session manager integration",
            orchestration_pattern=OrchestrationPattern.COLLABORATIVE
        )
        
        self.assertIsNotNone(conversation.id)
        self.assertEqual(conversation.session_id, "test_session_456")
        self.assertEqual(conversation.orchestration_pattern, OrchestrationPattern.COLLABORATIVE)
        
        # Track some messages
        message1 = session_manager.track_message(
            content="Test message 1",
            sender_name="Agent1",
            message_type="agent_response",
            response_time=1.0,
            tokens_used=10
        )
        
        message2 = session_manager.track_message(
            content="Test message 2", 
            sender_name="Agent2",
            message_type="agent_response",
            response_time=2.0,
            tokens_used=15
        )
        
        self.assertEqual(message1.conversation_id, conversation.id)
        self.assertEqual(message2.conversation_id, conversation.id)
        
        # Complete conversation and generate analytics
        analytics = session_manager.complete_conversation()
        
        self.assertIsNotNone(analytics)
        self.assertEqual(analytics.conversation_id, conversation.id)
    
    def test_analytics_with_no_messages(self):
        """Test analytics behavior with conversation that has no messages"""
        # Create conversation without messages
        empty_conversation = Conversation(
            title="Empty Conversation",
            status=ConversationStatus.ACTIVE,
            session_id="empty_session"
        )
        empty_conversation.save()
        
        analytics = self.analytics_engine.analyze_conversation(empty_conversation.id)
        
        # Should return None for conversations without messages
        self.assertIsNone(analytics)
    
    def test_analytics_with_error_messages(self):
        """Test analytics with error messages"""
        # Add an error message to the conversation
        error_message = Message(
            conversation_id=self.conversation.id,
            content="An error occurred during processing",
            message_type=MessageType.ERROR_MESSAGE,
            agent_name="SystemAgent"
        )
        error_message.save()
        
        analytics = self.analytics_engine.analyze_conversation(self.conversation.id)
        
        # Should count the error message
        self.assertEqual(analytics.error_count, 1)
        
        # Goal achievement should be penalized for errors
        self.assertLess(analytics.goal_achievement, 80)
    
    def test_conversation_completion_metrics(self):
        """Test metrics calculation when conversation is completed"""
        # Complete the conversation
        self.conversation.complete_conversation()
        
        # Verify completion metrics are set
        self.assertIsNotNone(self.conversation.end_time)
        self.assertIsNotNone(self.conversation.total_duration)
        self.assertIsNotNone(self.conversation.effectiveness_score)
        self.assertIsNotNone(self.conversation.engagement_score)
        
        # Verify metrics are reasonable
        self.assertGreater(self.conversation.effectiveness_score, 0)
        self.assertGreater(self.conversation.engagement_score, 0)


if __name__ == '__main__':
    unittest.main() 