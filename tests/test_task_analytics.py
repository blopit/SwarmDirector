"""
Test suite for Task Analytics functionality

This module tests the comprehensive task analytics system including:
- Analytics models and TaskAnalyticsEngine functionality
- Task analytics API endpoints
- Integration with existing task management
"""

import pytest
import json
from datetime import datetime, timedelta
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.task import Task, TaskStatus, TaskType, TaskPriority
from swarm_director.analytics.engine import TaskAnalyticsEngine


@pytest.fixture
def app():
    """Create test Flask application"""
    app = create_app('testing')
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'
    
    with app.app_context():
        db.create_all()
        yield app
        db.drop_all()


@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()


@pytest.fixture
def sample_tasks(app):
    """Create sample tasks for testing"""
    with app.app_context():
        tasks = []
        
        # Create tasks with different statuses and types
        task_data = [
            {
                'title': 'Test Task 1',
                'description': 'First test task',
                'type': TaskType.DEVELOPMENT,
                'status': TaskStatus.COMPLETED,
                'priority': TaskPriority.HIGH,
                'complexity_score': 8.5,
                'queue_time': 300.0,
                'processing_time': 1800.0,
                'quality_score': 9.2,
                'retry_count': 0
            },
            {
                'title': 'Test Task 2', 
                'description': 'Second test task',
                'type': TaskType.ANALYSIS,
                'status': TaskStatus.IN_PROGRESS,
                'priority': TaskPriority.MEDIUM,
                'complexity_score': 6.0,
                'queue_time': 120.0,
                'processing_time': 900.0,
                'quality_score': 8.5,
                'retry_count': 1
            },
            {
                'title': 'Test Task 3',
                'description': 'Third test task',
                'type': TaskType.OTHER,
                'status': TaskStatus.PENDING,
                'priority': TaskPriority.LOW,
                'complexity_score': 4.2,
                'queue_time': 0.0,
                'processing_time': 0.0,
                'quality_score': 0.0,
                'retry_count': 0
            }
        ]
        
        for data in task_data:
            task = Task(**data)
            if data['status'] == TaskStatus.COMPLETED:
                task.started_at = datetime.utcnow() - timedelta(hours=2)
                task.completed_at = datetime.utcnow() - timedelta(hours=1)
                task.first_response_time = 60.0
            elif data['status'] == TaskStatus.IN_PROGRESS:
                task.started_at = datetime.utcnow() - timedelta(minutes=30)
                task.first_response_time = 45.0
            
            db.session.add(task)
            tasks.append(task)
        
        db.session.commit()
        return tasks


class TestTaskAnalyticsEngine:
    """Test TaskAnalyticsEngine functionality"""
    
    def test_engine_initialization(self, app):
        """Test analytics engine initialization"""
        with app.app_context():
            engine = TaskAnalyticsEngine()
            assert engine is not None
            assert hasattr(engine, 'collect_task_metrics')
            assert hasattr(engine, 'generate_insights')
    
    def test_collect_metrics(self, app, sample_tasks):
        """Test metrics collection functionality"""
        with app.app_context():
            engine = TaskAnalyticsEngine()
            
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=1)
            
            metrics = engine.collect_task_metrics((start_date, end_date))
            
            assert metrics is not None
            assert 'completion_rates' in metrics
            assert 'performance_trends' in metrics
            assert 'bottleneck_analysis' in metrics
            assert 'agent_efficiency' in metrics
            assert metrics['completion_rates']['total_tasks'] >= 3


class TestTaskAnalyticsAPI:
    """Test task analytics API endpoints"""
    
    def test_get_task_analytics_summary(self, client):
        """Test /api/analytics/tasks/summary endpoint"""
        response = client.get('/api/analytics/tasks/summary')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'summary' in data
    
    def test_get_task_analytics_metrics(self, client):
        """Test /api/analytics/tasks/metrics endpoint"""
        response = client.get('/api/analytics/tasks/metrics')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'metrics' in data
    
    def test_get_task_analytics_insights(self, client, sample_tasks):
        """Test /api/analytics/tasks/insights endpoint"""
        response = client.get('/api/analytics/tasks/insights')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'insights' in data
    
    def test_get_task_real_time_metrics(self, client, sample_tasks):
        """Test /api/analytics/tasks/real-time endpoint"""
        response = client.get('/api/analytics/tasks/real-time')
        
        assert response.status_code == 200
        data = json.loads(response.data)
        assert data['status'] == 'success'
        assert 'real_time_metrics' in data


class TestTaskModelEnhancements:
    """Test enhanced Task model with analytics fields"""
    
    def test_task_analytics_fields(self, app):
        """Test that Task model has all required analytics fields"""
        with app.app_context():
            task = Task(
                title='Analytics Test Task',
                description='Testing analytics fields',
                type=TaskType.ANALYSIS,
                complexity_score=7.5,
                queue_time=180.0,
                processing_time=600.0,
                quality_score=8.8,
                retry_count=1
            )
            
            db.session.add(task)
            db.session.commit()
            
            saved_task = Task.query.first()
            assert saved_task.complexity_score == 7.5
            assert saved_task.queue_time == 180.0
            assert saved_task.processing_time == 600.0
            assert saved_task.quality_score == 8.8
            assert saved_task.retry_count == 1
    
    def test_task_calculate_analytics(self, app):
        """Test task analytics calculation method"""
        with app.app_context():
            task = Task(
                title='Analytics Calculation Test',
                description='Testing analytics calculation',
                type=TaskType.DEVELOPMENT,
                status=TaskStatus.IN_PROGRESS
            )
            task.started_at = datetime.utcnow() - timedelta(minutes=30)
            
            db.session.add(task)
            db.session.commit()
            
            analytics = task.calculate_analytics()
            
            assert analytics is not None
            assert 'completion_rate' in analytics
            assert 'time_efficiency' in analytics
            assert 'quality_metrics' in analytics


if __name__ == '__main__':
    pytest.main([__file__, '-v']) 