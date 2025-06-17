"""
Tests for DirectorAgent and /task endpoint functionality
"""

import json
import pytest
from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.task import Task, TaskStatus, TaskPriority
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.agents.director import DirectorAgent

class TestDirectorAgent:
    """Test suite for DirectorAgent functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    @pytest.fixture
    def director_agent(self, app):
        """Create a DirectorAgent for testing"""
        with app.app_context():
            # Create database agent
            db_agent = Agent(
                name='TestDirectorAgent',
                agent_type=AgentType.SUPERVISOR,
                status=AgentStatus.ACTIVE,
                capabilities=['routing', 'intent_classification']
            )
            db_agent.save()
            
            # Create DirectorAgent instance
            director = DirectorAgent(db_agent)
            return director
    
    def test_intent_classification_communications(self, app, director_agent):
        """Test intent classification for communications tasks"""
        with app.app_context():
            task = Task(
                title='Send email notification',
                description='Send an email to notify users about the update',
                status=TaskStatus.PENDING
            )
            task.save()
            
            intent = director_agent.classify_intent(task)
            assert intent == 'communications'
    
    def test_intent_classification_analysis(self, app, director_agent):
        """Test intent classification for analysis tasks"""
        with app.app_context():
            task = Task(
                title='Analyze sales data',
                description='Review and evaluate quarterly sales performance',
                status=TaskStatus.PENDING
            )
            task.save()
            
            intent = director_agent.classify_intent(task)
            assert intent == 'analysis'
    
    def test_intent_classification_coordination(self, app, director_agent):
        """Test intent classification for coordination tasks"""
        with app.app_context():
            task = Task(
                title='Manage project timeline',
                description='Coordinate team activities and track progress',
                status=TaskStatus.PENDING
            )
            task.save()
            
            intent = director_agent.classify_intent(task)
            assert intent == 'coordination'
    
    def test_intent_classification_default(self, app, director_agent):
        """Test intent classification defaults to coordination for unknown tasks"""
        with app.app_context():
            task = Task(
                title='Unknown task type',
                description='This task does not match any keywords',
                status=TaskStatus.PENDING
            )
            task.save()
            
            intent = director_agent.classify_intent(task)
            assert intent == 'coordination'
    
    def test_direct_task_handling(self, app, director_agent):
        """Test direct task handling when no department agent is available"""
        with app.app_context():
            task = Task(
                title='Test task',
                description='A test task for direct handling',
                status=TaskStatus.PENDING
            )
            task.save()
            
            result = director_agent.execute_task(task)
            
            assert result['status'] == 'handled_directly'
            assert 'department' in result
            assert result['task_id'] == task.id
            
            # Verify task was completed
            updated_task = Task.query.get(task.id)
            assert updated_task.status == TaskStatus.COMPLETED
    
    def test_routing_stats_update(self, app, director_agent):
        """Test that routing statistics are properly updated"""
        with app.app_context():
            initial_stats = director_agent.get_routing_stats()
            initial_total = initial_stats['total_routed']
            
            task = Task(
                title='Email task',
                description='Send email notification',
                status=TaskStatus.PENDING
            )
            task.save()
            
            director_agent.execute_task(task)
            
            updated_stats = director_agent.get_routing_stats()
            assert updated_stats['total_routed'] == initial_total + 1
            assert updated_stats['successful_routes'] >= initial_stats['successful_routes']


class TestTaskEndpoint:
    """Test suite for /task API endpoint"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask application"""
        app = create_app('testing')
        with app.app_context():
            db.create_all()
            yield app
            db.drop_all()
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_task_endpoint_valid_request(self, client):
        """Test /task endpoint with valid request"""
        payload = {
            'type': 'email',
            'title': 'Send welcome email',
            'description': 'Send welcome email to new user',
            'args': {'recipient': 'user@example.com'}
        }
        
        response = client.post('/task',
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.get_json()
        assert data['status'] == 'success'
        # Check for task_id in the nested data structure
        assert 'task_id' in data['data']
        
    def test_task_endpoint_missing_type(self, client):
        """Test /task endpoint with missing type field"""
        payload = {
            'title': 'Send welcome email',
            'description': 'Send welcome email to new user'
        }
        
        response = client.post('/task', 
            data=json.dumps(payload),
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        # Check that the error indicates the missing 'type' field
        assert data['error'].get('field') == 'type' or 'type' in data['error']['message']
    
    def test_task_endpoint_invalid_json(self, client):
        """Test /task endpoint with invalid JSON"""
        response = client.post('/task',
            data='invalid json',
            content_type='application/json'
        )
        
        assert response.status_code == 400  # Invalid JSON now properly handled
        data = response.get_json()
        assert data['status'] == 'error'
        # Check that the error message contains 'Invalid JSON'
        assert 'Invalid JSON' in data['error']['message'] or 'Invalid JSON' in str(data['error'])
    
    def test_task_endpoint_missing_content_type(self, client):
        """Test /task endpoint with missing content type"""
        response = client.post('/task',
            data=json.dumps({'type': 'test_task'}),
            content_type='text/plain'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        # Check that the error message contains 'Content-Type'
        assert 'Content-Type' in data['error']['message'] or 'Content-Type' in str(data['error'])
    
    def test_task_endpoint_empty_body(self, client):
        """Test /task endpoint with empty body"""
        response = client.post('/task',
            data='',
            content_type='application/json'
        )
        
        assert response.status_code == 400
        data = response.get_json()
        assert data['status'] == 'error'
        # Check that the error indicates invalid JSON or missing body
        assert ('Invalid JSON' in data['error']['message'] or 'Request body is required' in data['error']['message'] or 
                'Invalid JSON' in str(data['error']) or 'Request body is required' in str(data['error']))
    
    def test_task_endpoint_intent_classification(self, client):
        """Test that different task types are classified correctly"""
        test_cases = [
            ('email', 'communications'),
            ('analysis', 'analysis'),
            ('coordinate', 'coordination'),
            ('manage', 'coordination')
        ]
        for task_type, expected_dept in test_cases:
            payload = {
                'type': task_type,
                'title': f'Test {task_type} task',
                'description': f'A task involving {task_type}'
            }
            response = client.post('/task',
                data=json.dumps(payload),
                content_type='application/json'
            )
            assert response.status_code == 201
            data = response.get_json()
            # Check for routing_result in the nested data structure
            routing_result = data['data']['routing_result']
            # The routing result uses 'department' key, not 'routed_to'
            routed_to = routing_result.get('department') or routing_result.get('routed_to')
            assert routed_to == expected_dept


if __name__ == '__main__':
    pytest.main([__file__]) 