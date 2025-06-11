#!/usr/bin/env python3
"""
Test script for SwarmDirector Flask application
"""

from app import create_app
from utils.database import init_db, get_database_info
from models.agent import Agent, AgentType, AgentStatus
from models.task import Task, TaskStatus, TaskPriority

def test_app_creation():
    """Test Flask app creation"""
    try:
        app = create_app()
        print("✅ Flask app created successfully")
        return app
    except Exception as e:
        print(f"❌ Flask app creation failed: {e}")
        return None

def test_database_operations(app):
    """Test database operations"""
    with app.app_context():
        try:
            # Test database info
            db_info = get_database_info()
            if db_info:
                print("✅ Database connection successful")
                print(f"   Database URI: {db_info['database_uri']}")
                print(f"   Tables: {[t['name'] for t in db_info['tables']]}")
            else:
                print("❌ Database connection failed")
                return False

            # Test creating an agent
            test_agent = Agent(
                name="Test Agent",
                description="A test agent",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities=["testing", "validation"]
            )
            test_agent.save()
            print("✅ Agent creation successful")

            # Test creating a task
            test_task = Task(
                title="Test Task",
                description="A test task for validation",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM
            )
            test_task.save()
            print("✅ Task creation successful")

            # Test task assignment
            test_task.assign_to_agent(test_agent)
            print("✅ Task assignment successful")

            return True
        except Exception as e:
            print(f"❌ Database operations failed: {e}")
            return False

def test_routes(app):
    """Test Flask routes"""
    try:
        with app.test_client() as client:
            # Test index route
            response = client.get('/')
            if response.status_code == 200:
                print("✅ Index route working")
            else:
                print(f"❌ Index route failed: {response.status_code}")

            # Test health route
            response = client.get('/health')
            if response.status_code == 200:
                data = response.get_json()
                print("✅ Health route working")
                print(f"   Status: {data.get('status')}")
                print(f"   Database: {data.get('database')}")
            else:
                print(f"❌ Health route failed: {response.status_code}")

        return True
    except Exception as e:
        print(f"❌ Route testing failed: {e}")
        return False

def run_tests():
    """Run all tests"""
    print("🚀 Starting SwarmDirector Flask Application Tests")
    print("=" * 50)
    
    # Test 1: App creation
    app = test_app_creation()
    if not app:
        return False
    
    # Test 2: Database operations
    db_success = test_database_operations(app)
    
    # Test 3: Routes
    routes_success = test_routes(app)
    
    print("=" * 50)
    if db_success and routes_success:
        print("🎉 All tests passed! SwarmDirector Flask application is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False

if __name__ == "__main__":
    run_tests() 