"""
Pytest configuration and fixtures for SwarmDirector tests
"""

import sys
import os
import tempfile
import shutil
import glob
from pathlib import Path

# Add src directory to Python path for imports
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

import pytest
from swarm_director.app import create_app
from swarm_director.models.base import db

@pytest.fixture
def app():
    """Create and configure a test app instance"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

@pytest.fixture
def client(app):
    """Create a test client for the app"""
    return app.test_client()

@pytest.fixture
def runner(app):
    """Create a test runner for CLI commands"""
    return app.test_cli_runner()

@pytest.fixture(scope="session", autouse=True)
def cleanup_test_artifacts():
    """Automatically clean up test artifacts after all tests complete"""
    yield

    # Clean up any test backup/migration directories
    project_root = Path(__file__).parent.parent

    print("\n🧹 Cleaning up test artifacts...")

    # Remove timestamped test directories
    for pattern in ['test_backups_*', 'test_migrations_*']:
        for path in glob.glob(str(project_root / pattern)):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"🧹 Removed test directory: {path}")
            except (OSError, PermissionError) as e:
                print(f"⚠️  Could not remove {path}: {e}")

    # Clean up test database files in instance directory
    instance_dir = project_root / "instance"
    if instance_dir.exists():
        for pattern in ['*_test_*.db', '*_test_*.db-*']:
            for db_file in instance_dir.glob(pattern):
                try:
                    db_file.unlink()
                    print(f"🧹 Removed test database: {db_file}")
                except (OSError, PermissionError) as e:
                    print(f"⚠️  Could not remove {db_file}: {e}")

    print("✅ Test artifact cleanup completed")

@pytest.fixture
def temp_test_app():
    """Create a test app with proper temporary directories for database tests"""
    import time
    timestamp = str(int(time.time() * 1000))

    # Create temporary directories
    backup_temp_dir = tempfile.mkdtemp(prefix=f'pytest_backups_{timestamp}_')
    migrations_temp_dir = tempfile.mkdtemp(prefix=f'pytest_migrations_{timestamp}_')

    # Create temporary database file
    db_temp_file = tempfile.NamedTemporaryFile(
        suffix=f'_pytest_{timestamp}.db',
        delete=False
    )
    db_temp_file.close()

    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_temp_file.name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['DATABASE_PATH'] = db_temp_file.name
    app.config['BACKUP_DIR'] = backup_temp_dir
    app.config['MIGRATIONS_DIR'] = migrations_temp_dir

    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()

    # Cleanup temporary files and directories
    try:
        os.unlink(db_temp_file.name)
        shutil.rmtree(backup_temp_dir)
        shutil.rmtree(migrations_temp_dir)
    except (OSError, PermissionError):
        pass
