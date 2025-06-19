"""
Tests for application initialization
"""

import pytest
from src.swarm_director.app import create_app
from src.swarm_director.models import db as _db

def test_app_creation(app):
    """Test that the application can be created"""
    assert app is not None

def test_database_creation(db):
    """Test that the database can be created"""
    assert db is not None 