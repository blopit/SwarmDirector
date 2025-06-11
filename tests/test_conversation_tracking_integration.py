"""
Integration tests for the complete conversation tracking workflow
"""
import unittest
import json

from src.swarm_director.models.base import db
from src.swarm_director.models.conversation import OrchestrationPattern
from src.swarm_director.utils.autogen_integration import ConversationSessionManager
from src.swarm_director.app import create_app


class TestConversationTrackingIntegration(unittest.TestCase):
    """Integration tests for complete conversation tracking workflow"""
    
    def setUp(self):
        """Set up test environment"""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = self.app.test_client()
        db.create_all()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_complete_conversation_workflow(self):
        """Test the complete conversation tracking workflow"""
        # Initialize session manager
        session_manager = ConversationSessionManager("integration_test_session")
        
        # Start conversation with tracking
        conversation = session_manager.start_conversation(
            title="Integration Test Conversation",
            description="Testing complete workflow",
            conversation_type="integration_test",
            orchestration_pattern=OrchestrationPattern.COLLABORATIVE
        )
        
        self.assertIsNotNone(conversation.id)
        
        # Simulate conversation with messages
        message = session_manager.track_message(
            content="Hello team, let's collaborate!",
            sender_name="CoordinatorAgent",
            message_type="agent_response",
            response_time=1.2,
            tokens_used=15
        )
        
        self.assertEqual(message.conversation_id, conversation.id)
        
        # Complete conversation and generate analytics
        analytics = session_manager.complete_conversation()
        self.assertIsNotNone(analytics)
        
        # Test API endpoints
        response = self.client.get('/api/analytics/conversations')
        self.assertEqual(response.status_code, 200)
        
        print("✅ Complete conversation tracking workflow test passed!")
    
    def test_analytics_dashboard_functionality(self):
        """Test analytics dashboard loads correctly"""
        response = self.client.get('/dashboard/analytics')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Conversation Analytics', response.data)


if __name__ == '__main__':
    unittest.main() 