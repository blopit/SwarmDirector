#!/usr/bin/env python3
"""
Test script for SwarmDirector Flask application
"""

import pytest
from swarm_director.app import create_app
from swarm_director.utils.database import init_db, get_database_info
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app()
    app.config['TESTING'] = True
    
    # Initialize database tables for testing
    with app.app_context():
        from swarm_director.models.base import db
        db.create_all()
    
    return app


@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()


def test_app_creation(app):
    """Test Flask app creation"""
    assert app is not None
    assert app.config['TESTING'] is True
    print("✅ Flask app created successfully")


def test_database_operations(app):
    """Test database operations"""
    with app.app_context():
        # Test database info
        db_info = get_database_info()
        assert db_info is not None, "Database connection failed"
        print("✅ Database connection successful")
        print(f"   Database URI: {db_info['database_uri']}")
        print(f"   Tables: {[t['name'] for t in db_info['tables']]}")

        # Test creating an agent
        test_agent = Agent(
            name="Test Agent",
            description="A test agent",
            agent_type=AgentType.WORKER,
            status=AgentStatus.IDLE,
            capabilities=["testing", "validation"]
        )
        test_agent.save()
        assert test_agent.id is not None
        print("✅ Agent creation successful")

        # Test creating a task
        test_task = Task(
            title="Test Task",
            description="A test task for validation",
            status=TaskStatus.PENDING,
            priority=TaskPriority.MEDIUM
        )
        test_task.save()
        assert test_task.id is not None
        print("✅ Task creation successful")

        # Test task assignment
        test_task.assign_to_agent(test_agent)
        assert test_task.assigned_agent_id == test_agent.id
        print("✅ Task assignment successful")


def test_routes(client):
    """Test basic routes are working"""
    # Test index route
    response = client.get('/')
    assert response.status_code == 200
    print("✅ Index route working")
    
    # Test health route
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    # Check for success status instead of healthy
    assert data.get('status') == 'success'
    

def test_crud_api_endpoints(client):
    """Test basic CRUD endpoints are accessible"""
    # Test agents list endpoint
    response = client.get('/api/agents')
    assert response.status_code == 200
    data = response.get_json()
    # Check for agents in nested data structure
    assert 'agents' in data['data']


def test_dashboard_routes(client):
    """Test dashboard web interface routes"""
    # Test main dashboard
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'SwarmDirector Dashboard' in response.data
    print("✅ Dashboard route working")

    # Test agents page
    response = client.get('/dashboard/agents')
    assert response.status_code == 200
    assert b'Agent Management' in response.data
    print("✅ Agents dashboard page working")


def run_tests():
    """Run all tests - kept for backwards compatibility"""
    print("🚀 Starting SwarmDirector Flask Application Tests")
    print("=" * 50)
    
    # Test 1: App creation
    app = create_app()
    if not app:
        return False
    
    # Initialize database tables for testing
    with app.app_context():
        from swarm_director.models.base import db
        db.create_all()
    
    # Test 2: Database operations
    try:
        test_database_operations(app)
        db_success = True
    except Exception as e:
        print(f"❌ Database operations failed: {e}")
        db_success = False
    
    # Test 3: Routes
    try:
        test_routes(app.test_client())
        routes_success = True
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        routes_success = False
    
    print("=" * 50)
    if db_success and routes_success:
        print("🎉 All tests passed! SwarmDirector Flask application is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    run_tests() 