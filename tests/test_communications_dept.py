"""
Tests for CommunicationsDept agent
"""

import pytest
from unittest.mock import Mock, patch
from datetime import datetime

from swarm_director.agents.communications_dept import CommunicationsDept
from swarm_director.agents.draft_review_agent import DraftReviewAgent
from swarm_director.agents.email_agent import EmailAgent
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.models.draft import Draft, DraftStatus, DraftType


class TestCommunicationsDept:
    """Test suite for CommunicationsDept agent"""
    
    @pytest.fixture
    def mock_agent(self):
        """Create a mock agent for testing"""
        agent = Mock()
        agent.id = 1
        agent.name = "CommunicationsDept"
        agent.agent_type = AgentType.SUPERVISOR
        agent.status = AgentStatus.ACTIVE
        return agent
    
    @pytest.fixture
    def communications_dept(self, mock_agent, app):
        """Create CommunicationsDept instance for testing"""
        with app.app_context():
            with patch.object(CommunicationsDept, '_initialize_subordinate_agents'):
                dept = CommunicationsDept(mock_agent)
                # Manually set up mock subordinate agents with proper name attributes
                mock_review_agent1 = Mock(spec=DraftReviewAgent)
                mock_review_agent1.name = "MockReviewer1"
                mock_review_agent2 = Mock(spec=DraftReviewAgent)
                mock_review_agent2.name = "MockReviewer2"
                dept.review_agents = [mock_review_agent1, mock_review_agent2]
                dept.email_agent = Mock(spec=EmailAgent)
                return dept
    
    @pytest.fixture
    def sample_task(self):
        """Create a sample task for testing"""
        task = Mock()
        task.id = 1
        task.user_id = 1  # Explicitly set user_id to avoid Mock object
        task.title = "Test Email Task"
        task.description = "Send a test email"
        from swarm_director.models.task import TaskType
        task.type = TaskType.EMAIL
        task.input_data = {
            'type': 'email',
            'recipient': 'test@example.com',
            'subject': 'Test Subject',
            'content': 'Test email content'
        }
        task.save = Mock()
        task.complete_task = Mock()
        return task
    
    def test_initialization(self, mock_agent):
        """Test CommunicationsDept initialization"""
        with patch.object(CommunicationsDept, '_initialize_subordinate_agents') as mock_init:
            dept = CommunicationsDept(mock_agent)
            
            assert dept.department_name == "communications"
            assert dept.min_reviewers == 2
            assert dept.consensus_threshold == 0.75
            mock_init.assert_called_once()
    
    def test_determine_communication_type_email(self, communications_dept, sample_task):
        """Test communication type determination for email tasks"""
        sample_task.type = "email"
        comm_type = communications_dept._determine_communication_type(sample_task)
        assert comm_type == "email"
    
    def test_determine_communication_type_review(self, communications_dept, sample_task):
        """Test communication type determination for review tasks"""
        sample_task.title = "Review this draft"
        sample_task.type = "general"
        comm_type = communications_dept._determine_communication_type(sample_task)
        assert comm_type == "draft_review"
    
    def test_determine_communication_type_content_creation(self, communications_dept, sample_task):
        """Test communication type determination for content creation"""
        sample_task.title = "Create new content"
        sample_task.type = "general"
        comm_type = communications_dept._determine_communication_type(sample_task)
        assert comm_type == "content_creation"
    
    def test_create_initial_draft_with_content(self, communications_dept, sample_task):
        """Test creating initial draft with provided content"""
        sample_task.input_data = {'content': 'Test content'}
        
        result = communications_dept._create_initial_draft(sample_task)
        
        assert result['status'] == 'success'
        assert result['draft_content'] == 'Test content'
        assert 'created_at' in result
    
    def test_create_initial_draft_from_task(self, communications_dept, sample_task):
        """Test creating initial draft from task description"""
        sample_task.input_data = {}
        sample_task.title = "Test Title"
        sample_task.description = "Test Description"
        
        result = communications_dept._create_initial_draft(sample_task)
        
        assert result['status'] == 'success'
        assert "Test Title" in result['draft_content']
        assert "Test Description" in result['draft_content']
    
    @patch('swarm_director.agents.communications_dept.ThreadPoolExecutor')
    def test_conduct_parallel_review_success(self, mock_executor, communications_dept, sample_task, app):
        """Test successful parallel review process"""
        # Mock the thread pool executor
        mock_future = Mock()
        mock_future.result.return_value = {
            'status': 'success',
            'review_result': {
                'overall_score': 85,
                'suggestions': [{'description': 'Good content'}]
            }
        }
        
        mock_executor_instance = Mock()
        mock_executor_instance.__enter__ = Mock(return_value=mock_executor_instance)
        mock_executor_instance.__exit__ = Mock(return_value=None)
        mock_executor_instance.submit.return_value = mock_future
        mock_executor.return_value = mock_executor_instance
        
        # Mock as_completed to return our future
        with patch('swarm_director.agents.communications_dept.as_completed', return_value=[mock_future]):
            # Mock Task creation and save to avoid database operations
            with patch('swarm_director.models.task.Task') as mock_task_class:
                mock_task_instance = Mock()
                mock_task_instance.id = 123
                mock_task_instance.save = Mock()
                mock_task_class.return_value = mock_task_instance
                
                # Mock the review agents to ensure we have some
                mock_review_agent = Mock()
                mock_review_agent.name = "TestReviewAgent"
                communications_dept.review_agents = [mock_review_agent]
                communications_dept.min_reviewers = 1  # Ensure we meet minimum requirements
                
                with app.app_context():
                    result = communications_dept._conduct_parallel_review(sample_task, "test content")
        
        assert result['status'] == 'success'
        assert len(result['reviews']) >= 1
        assert result['content_reviewed'] == "test content"
    
    def test_analyze_consensus_with_reviews(self, communications_dept):
        """Test consensus analysis with multiple reviews"""
        reviews = [
            {
                'agent': 'Reviewer1',
                'review': {
                    'overall_score': 80,
                    'suggestions': [
                        {'description': 'Improve clarity'},
                        {'description': 'Add more details'}
                    ]
                }
            },
            {
                'agent': 'Reviewer2', 
                'review': {
                    'overall_score': 90,
                    'suggestions': [
                        {'description': 'Improve clarity'},
                        {'description': 'Good structure'}
                    ]
                }
            }
        ]
        
        consensus = communications_dept._analyze_consensus(reviews)
        
        assert consensus['reviewer_count'] == 2
        assert consensus['average_score'] == 85
        assert 'Improve clarity' in consensus['agreed_improvements']
        assert consensus['consensus_score'] > 0
    
    def test_analyze_consensus_empty_reviews(self, communications_dept):
        """Test consensus analysis with no reviews"""
        consensus = communications_dept._analyze_consensus([])
        
        assert consensus['consensus_score'] == 0
        assert consensus['agreed_improvements'] == []
        assert consensus['conflicting_suggestions'] == []
    
    def test_apply_consensus_improvements(self, communications_dept):
        """Test applying consensus improvements to content"""
        original_content = "Original content"
        consensus = {
            'agreed_improvements': ['Improve clarity', 'Add details'],
            'consensus_score': 0.8
        }
        
        improved_content = communications_dept._apply_consensus_improvements(original_content, consensus)
        
        assert "Original content" in improved_content
        assert "Improved based on 2 consensus suggestions" in improved_content
    
    def test_can_handle_task_email(self, communications_dept, sample_task):
        """Test task handling capability for email tasks"""
        sample_task.type = "email"
        assert communications_dept.can_handle_task(sample_task) == True
    
    def test_can_handle_task_communication(self, communications_dept, sample_task):
        """Test task handling capability for communication tasks"""
        sample_task.type = "communication"
        assert communications_dept.can_handle_task(sample_task) == True
    
    def test_can_handle_task_other(self, communications_dept, sample_task):
        """Test task handling capability for non-communication tasks"""
        sample_task.type = "calculation"
        assert communications_dept.can_handle_task(sample_task) == False
    
    def test_handle_general_communication_with_email_agent(self, communications_dept, sample_task):
        """Test handling general communication when email agent can handle it"""
        communications_dept.email_agent.can_handle_task.return_value = True
        communications_dept.email_agent.execute_task.return_value = {
            'status': 'success',
            'message': 'Email sent'
        }
        
        result = communications_dept._handle_general_communication(sample_task)
        
        assert result['status'] == 'success'
        assert result['message'] == 'Email sent'
        communications_dept.email_agent.execute_task.assert_called_once_with(sample_task)
    
    def test_handle_general_communication_direct(self, communications_dept, sample_task):
        """Test handling general communication directly"""
        communications_dept.email_agent.can_handle_task.return_value = False
        sample_task.complete_task = Mock()
        
        result = communications_dept._handle_general_communication(sample_task)
        
        assert result['status'] == 'success'
        assert result['message'] == 'General communication task completed'
        sample_task.complete_task.assert_called_once()
    
    def test_execute_task_email_workflow(self, communications_dept, sample_task):
        """Test executing email workflow task"""
        sample_task.type = "email"
        
        # Mock the workflow methods
        communications_dept._handle_email_workflow = Mock(return_value={
            'status': 'success',
            'message': 'Email workflow completed'
        })
        
        result = communications_dept.execute_task(sample_task)
        
        assert result['status'] == 'success'
        communications_dept._handle_email_workflow.assert_called_once_with(sample_task)
    
    def test_execute_task_error_handling(self, communications_dept, sample_task):
        """Test error handling in execute_task"""
        sample_task.type = "email"
        
        # Mock method to raise exception
        communications_dept._determine_communication_type = Mock(side_effect=Exception("Test error"))
        
        result = communications_dept.execute_task(sample_task)
        
        assert result['status'] == 'error'
        assert 'Test error' in result['error']
        assert result['task_id'] == sample_task.id
