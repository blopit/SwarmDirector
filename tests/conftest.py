"""
Pytest configuration and fixtures for SwarmDirector tests
"""

import sys
import os
import shutil
import glob
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from unittest.mock import Mock
from src.swarm_director.app import create_app
from src.swarm_director.models import (
    db as _db,
    Agent,
    Task,
    Conversation,
    Message,
    ConversationAnalytics,
    AgentLog,
    Draft,
    EmailMessage,
    APIUsage,
    CostBudget,
    CostAlert,
    ValidationRecord,
    QualityGateConfig,
    RollbackRecord,
    PluginRecord,
    PluginInstallation,
    CapabilityGap,
    AgentTemplate,
)
from swarm_director.utils.concurrency import reset_concurrency_manager
from swarm_director.utils.async_processor import reset_async_processor

@pytest.fixture(scope='function')
def app():
    """
    Create a new application instance for each test.
    This uses an in-memory SQLite database for isolation and speed.
    """
    app = create_app('testing')
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    with app.app_context():
        _db.create_all()
        yield app
        _db.session.remove()
        _db.drop_all()

@pytest.fixture(scope='function')
def db(app):
    """
    Provides the database instance for a test.
    Relies on the `app` fixture to handle creation and teardown.
    """
    with app.app_context():
        yield _db

@pytest.fixture
def client(app):
    """Create a test client for the app."""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for the app's Click commands."""
    return app.test_cli_runner()

@pytest.fixture(autouse=True)
def cleanup_singletons():
    """
    Resets all singleton managers after each test to ensure isolation.
    """
    yield
    # Clean up concurrency and async processor managers
    try:
        reset_concurrency_manager()
        reset_async_processor()
    except Exception as e:
        print(f"⚠️  Error during singleton cleanup: {e}")

@pytest.fixture
def mock_openai_client():
    """Mock OpenAI client for testing."""
    return Mock()

@pytest.fixture
def mock_agent():
    """Mock agent for testing."""
    agent = Mock()
    agent.id = 1
    agent.name = "TestAgent"
    agent.agent_type = "test"
    return agent

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts_session():
    """
    Automatically clean up leftover test artifacts at the end of the session.
    This targets files that might not have been cleaned up if tests errored out.
    """
    yield

    # Clean up any test backup/migration directories from previous runs
    project_root = Path(__file__).parent.parent

    print("\n🧹 Cleaning up test artifacts from session...")

    # Remove timestamped test directories
    for pattern in ['pytest_backups_*', 'pytest_migrations_*', 'test_backups_*', 'test_migrations_*']:
        for path in glob.glob(str(project_root / pattern)):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"🧹 Removed test artifact directory: {path}")
            except (OSError, PermissionError) as e:
                print(f"⚠️  Could not remove {path}: {e}")

    # Clean up test database files in instance directory
    instance_dir = project_root / "instance"
    if instance_dir.exists():
        for pattern in ['*_pytest_*.db', '*_pytest_*.db-*', '*_test_*.db', '*_test_*.db-*']:
            for db_file in instance_dir.glob(pattern):
                try:
                    db_file.unlink()
                    print(f"🧹 Removed test artifact database: {db_file}")
                except (OSError, PermissionError) as e:
                    print(f"⚠️  Could not remove {db_file}: {e}")

    print("✅ Session artifact cleanup completed") 