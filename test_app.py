#!/usr/bin/env python3
"""
Test script for SwarmDirector Flask application
"""

import pytest
from app import create_app
from utils.database import init_db, get_database_info
from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus, TaskPriority


@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app()
    app.config['TESTING'] = True
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
    """Test Flask routes"""
    # Test index route
    response = client.get('/')
    assert response.status_code == 200
    print("✅ Index route working")

    # Test health route
    response = client.get('/health')
    assert response.status_code == 200
    data = response.get_json()
    assert data.get('status') == 'healthy'
    print("✅ Health route working")
    print(f"   Status: {data.get('status')}")
    print(f"   Database: {data.get('database')}")


def test_crud_api_endpoints(client):
    """Test the new CRUD API endpoints"""
    # Test agents endpoint
    response = client.get('/api/agents')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'agents' in data
    assert 'count' in data
    print("✅ Agents API endpoint working")

    # Test tasks endpoint
    response = client.get('/api/tasks')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'tasks' in data
    assert 'count' in data
    print("✅ Tasks API endpoint working")

    # Test conversations endpoint
    response = client.get('/api/conversations')
    assert response.status_code == 200
    data = response.get_json()
    assert data['status'] == 'success'
    assert 'conversations' in data
    assert 'count' in data
    print("✅ Conversations API endpoint working")


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