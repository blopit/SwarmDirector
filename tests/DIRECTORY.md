# Tests Directory

## Purpose
Contains the comprehensive test suite for the SwarmDirector application, ensuring code quality, reliability, and maintainability. This directory provides unit tests, integration tests, and end-to-end tests covering all aspects of the hierarchical AI agent management system with proper fixtures, mocks, and test utilities.

## Structure
```
tests/
├── __init__.py                  # Test package initialization
├── conftest.py                  # Pytest configuration and shared fixtures
├── test_app.py                  # Flask application tests
├── test_autogen_agent_types.py  # AutoGen agent type tests
├── test_communications_dept.py  # Communications department tests
├── test_conversation_analytics.py # Conversation analytics tests
├── test_conversation_tracking_integration.py # Conversation tracking tests
├── test_database_utils.py       # Database utility tests
├── test_diff_generator.py       # Content diff generator tests
├── test_director_agent.py       # Director agent tests
├── test_draft_review_agent.py   # Draft review agent tests
├── test_email_agent.py          # Email agent tests
├── test_error_handler.py        # Error handling tests
├── test_relationships.py        # Model relationship tests
├── test_advanced_relationships.py # Advanced relationship tests
├── test_request_validation.py   # Request validation tests
├── test_response_formatter.py   # Response formatting tests
├── test_review_logic.py         # Review logic tests
├── fixtures/                    # Test data and fixtures
│   ├── sample_agents.json       # Sample agent configurations
│   ├── sample_tasks.json        # Sample task data
│   ├── sample_conversations.json # Sample conversation data
│   └── test_database.db         # Test database file
└── integration/                 # Integration and end-to-end tests
    ├── __init__.py              # Integration test package
    ├── test_workflow_integration.py # Complete workflow tests
    ├── test_api_integration.py  # API endpoint integration tests
    └── test_agent_coordination.py # Agent coordination tests
```

## Guidelines

### 1. Organization
- **Test Categories**: Organize tests by component type (agents, models, utils, integration)
- **Fixture Management**: Use shared fixtures in `conftest.py` for common test data
- **Test Isolation**: Ensure tests are independent and can run in any order
- **Mock Strategy**: Use mocks for external dependencies and slow operations
- **Test Data**: Store test data in fixtures directory with version control

### 2. Naming
- **Test Files**: Use `test_` prefix for all test files (e.g., `test_director_agent.py`)
- **Test Functions**: Use descriptive names starting with `test_` (e.g., `test_agent_can_handle_email_task`)
- **Test Classes**: Use `Test` prefix for test classes (e.g., `TestDirectorAgent`)
- **Fixtures**: Use descriptive names for fixtures (e.g., `sample_agent`, `mock_database`)
- **Parametrized Tests**: Use clear parameter names for test variations

### 3. Implementation
- **Test Framework**: Use pytest as the primary testing framework
- **Assertions**: Use descriptive assertions with clear error messages
- **Setup/Teardown**: Use fixtures for setup and teardown operations
- **Test Coverage**: Maintain >85% code coverage across all modules
- **Performance Tests**: Include performance benchmarks for critical operations

### 4. Documentation
- **Test Docstrings**: Document test purpose and expected behavior
- **Fixture Documentation**: Document fixture purpose and usage
- **Test Categories**: Use pytest markers to categorize tests
- **Coverage Reports**: Generate and maintain coverage reports

## Best Practices

### 1. Error Handling
- **Exception Testing**: Test both success and failure scenarios
- **Error Message Validation**: Verify error messages are helpful and accurate
- **Edge Case Testing**: Test boundary conditions and edge cases
- **Recovery Testing**: Test error recovery and fallback mechanisms
- **Timeout Testing**: Test timeout scenarios and resource cleanup

### 2. Security
- **Input Validation Testing**: Test all input validation scenarios
- **Authentication Testing**: Test authentication and authorization mechanisms
- **SQL Injection Testing**: Test protection against SQL injection attacks
- **XSS Testing**: Test protection against cross-site scripting
- **CSRF Testing**: Test CSRF protection mechanisms

### 3. Performance
- **Load Testing**: Test system behavior under load
- **Memory Testing**: Test for memory leaks and resource usage
- **Database Performance**: Test database query performance
- **Concurrent Testing**: Test concurrent operations and race conditions
- **Benchmark Testing**: Maintain performance benchmarks

### 4. Testing
- **Test Isolation**: Use temporary directories and cleanup procedures
- **Mock External Services**: Mock all external API calls and services
- **Database Testing**: Use in-memory or temporary databases for tests
- **Parallel Execution**: Ensure tests can run in parallel safely
- **Continuous Integration**: Integrate with CI/CD pipelines

### 5. Documentation
- **Test Documentation**: Document testing strategies and patterns
- **Coverage Reports**: Maintain up-to-date coverage reports
- **Test Data Documentation**: Document test data structure and usage
- **Troubleshooting**: Include common testing issues and solutions

## Example

### Comprehensive Agent Test Implementation

```python
"""
Example: Comprehensive Director Agent Test Suite
Demonstrates advanced testing patterns with fixtures, mocks, and edge cases
"""

import pytest
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.swarm_director.agents.director import DirectorAgent
from src.swarm_director.models.agent import Agent, AgentType, AgentStatus
from src.swarm_director.models.task import Task, TaskStatus, TaskPriority
from src.swarm_director.utils.error_handler import AgentError
from src.swarm_director.app import create_app
from src.swarm_director.models.base import db

class TestDirectorAgent:
    """
    Comprehensive test suite for DirectorAgent
    
    Tests all aspects of director agent functionality including:
    - Task routing and assignment
    - Department management
    - Error handling and recovery
    - Performance and scalability
    """
    
    @pytest.fixture(autouse=True)
    def setup_test_environment(self, app_context, temp_database):
        """Setup test environment for each test"""
        self.temp_dir = tempfile.mkdtemp()
        self.app = app_context
        self.db = temp_database
        
        # Create test director agent
        self.director_db = Agent(
            name="TestDirector",
            description="Test director agent",
            agent_type=AgentType.SUPERVISOR,
            status=AgentStatus.IDLE,
            capabilities={
                "routing": True,
                "department_management": True,
                "intent_classification": True,
                "max_concurrent_tasks": 10
            }
        )
        self.director_db.save()
        
        self.director = DirectorAgent(self.director_db)
        
        yield
        
        # Cleanup
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.fixture
    def sample_task(self) -> Task:
        """Create a sample task for testing"""
        return Task(
            title="Test Email Task",
            description="Send a test email to customer",
            task_type="communication",
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            input_data={
                "recipient": "test@example.com",
                "subject": "Test Subject",
                "body": "Test message body"
            }
        )
    
    @pytest.fixture
    def sample_agents(self) -> List[Agent]:
        """Create sample department agents"""
        agents = [
            Agent(
                name="EmailAgent",
                description="Email handling agent",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities={"email_handling": True, "smtp_integration": True}
            ),
            Agent(
                name="CommunicationsDept",
                description="Communications department",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities={"content_creation": True, "review_workflows": True}
            )
        ]
        
        for agent in agents:
            agent.save()
        
        return agents
    
    def test_director_initialization(self):
        """Test director agent initialization"""
        assert self.director.name == "TestDirector"
        assert self.director.agent_id == self.director_db.id
        assert self.director.status == AgentStatus.IDLE
        assert self.director.capabilities["routing"] is True
    
    def test_can_handle_task_valid_task(self, sample_task):
        """Test director can handle valid tasks"""
        sample_task.save()
        
        assert self.director.can_handle_task(sample_task) is True
    
    def test_can_handle_task_invalid_task(self):
        """Test director rejects invalid tasks"""
        invalid_task = Task(
            title="",  # Empty title
            description="Invalid task",
            task_type="unknown_type",
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING
        )
        invalid_task.save()
        
        assert self.director.can_handle_task(invalid_task) is False
    
    def test_can_handle_task_when_busy(self, sample_task):
        """Test director behavior when at capacity"""
        sample_task.save()
        
        # Set director to busy status
        self.director.update_status(AgentStatus.BUSY)
        
        # Should still be able to handle tasks (routing doesn't require full availability)
        assert self.director.can_handle_task(sample_task) is True
    
    @patch('src.swarm_director.agents.director.DirectorAgent._route_to_department')
    def test_execute_task_success(self, mock_route, sample_task, sample_agents):
        """Test successful task execution"""
        sample_task.save()
        
        # Mock successful routing
        mock_route.return_value = {
            'status': 'completed',
            'task_id': sample_task.id,
            'assigned_agent': 'EmailAgent',
            'execution_time': 5.2
        }
        
        result = self.director.execute_task(sample_task)
        
        assert result['status'] == 'completed'
        assert result['task_id'] == sample_task.id
        assert 'assigned_agent' in result
        mock_route.assert_called_once_with(sample_task)
    
    def test_execute_task_routing_failure(self, sample_task):
        """Test task execution when routing fails"""
        sample_task.save()
        
        # No available agents for this task type
        with pytest.raises(AgentError) as exc_info:
            self.director.execute_task(sample_task)
        
        assert "No suitable agent found" in str(exc_info.value)
        assert sample_task.status == TaskStatus.FAILED
    
    @patch('src.swarm_director.agents.director.DirectorAgent._classify_intent')
    def test_intent_classification(self, mock_classify, sample_task):
        """Test intent classification functionality"""
        sample_task.save()
        
        mock_classify.return_value = {
            'intent': 'email_communication',
            'confidence': 0.95,
            'department': 'communications',
            'required_capabilities': ['email_handling']
        }
        
        intent = self.director._classify_intent(sample_task)
        
        assert intent['intent'] == 'email_communication'
        assert intent['confidence'] > 0.9
        assert intent['department'] == 'communications'
        mock_classify.assert_called_once_with(sample_task)
    
    def test_department_registration(self, sample_agents):
        """Test department agent registration"""
        # Register departments
        for agent in sample_agents:
            self.director.register_department(agent)
        
        # Verify registration
        departments = self.director.get_available_departments()
        assert len(departments) == 2
        assert any(dept.name == "EmailAgent" for dept in departments)
        assert any(dept.name == "CommunicationsDept" for dept in departments)
    
    def test_load_balancing(self, sample_agents):
        """Test load balancing across agents"""
        # Create multiple tasks
        tasks = []
        for i in range(5):
            task = Task(
                title=f"Test Task {i}",
                description=f"Test task number {i}",
                task_type="communication",
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={"test": f"data_{i}"}
            )
            task.save()
            tasks.append(task)
        
        # Register agents
        for agent in sample_agents:
            self.director.register_department(agent)
        
        # Track assignments
        assignments = {}
        
        with patch.object(self.director, '_execute_on_agent') as mock_execute:
            mock_execute.return_value = {'status': 'completed'}
            
            for task in tasks:
                result = self.director.execute_task(task)
                assigned_agent = mock_execute.call_args[0][1].name
                assignments[assigned_agent] = assignments.get(assigned_agent, 0) + 1
        
        # Verify load distribution
        assert len(assignments) > 1  # Tasks distributed across multiple agents
        assert all(count > 0 for count in assignments.values())  # All agents got tasks
    
    def test_error_recovery(self, sample_task, sample_agents):
        """Test error recovery mechanisms"""
        sample_task.save()
        
        # Register agents
        for agent in sample_agents:
            self.director.register_department(agent)
        
        # Mock agent failure and recovery
        with patch.object(self.director, '_execute_on_agent') as mock_execute:
            # First call fails, second succeeds
            mock_execute.side_effect = [
                AgentError("Agent temporarily unavailable"),
                {'status': 'completed', 'task_id': sample_task.id}
            ]
            
            result = self.director.execute_task(sample_task)
            
            # Should have retried and succeeded
            assert result['status'] == 'completed'
            assert mock_execute.call_count == 2
    
    def test_concurrent_task_handling(self, sample_agents):
        """Test handling multiple concurrent tasks"""
        import threading
        import time
        
        # Create multiple tasks
        tasks = []
        for i in range(3):
            task = Task(
                title=f"Concurrent Task {i}",
                description=f"Concurrent test task {i}",
                task_type="communication",
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={"concurrent": True, "task_id": i}
            )
            task.save()
            tasks.append(task)
        
        # Register agents
        for agent in sample_agents:
            self.director.register_department(agent)
        
        results = []
        threads = []
        
        def execute_task(task):
            with patch.object(self.director, '_execute_on_agent') as mock_execute:
                mock_execute.return_value = {
                    'status': 'completed',
                    'task_id': task.id,
                    'thread_id': threading.current_thread().ident
                }
                result = self.director.execute_task(task)
                results.append(result)
        
        # Execute tasks concurrently
        for task in tasks:
            thread = threading.Thread(target=execute_task, args=(task,))
            threads.append(thread)
            thread.start()
        
        # Wait for completion
        for thread in threads:
            thread.join(timeout=5.0)
        
        # Verify all tasks completed
        assert len(results) == 3
        assert all(result['status'] == 'completed' for result in results)
    
    def test_performance_metrics(self, sample_task, sample_agents):
        """Test performance metrics collection"""
        sample_task.save()
        
        # Register agents
        for agent in sample_agents:
            self.director.register_department(agent)
        
        start_time = datetime.utcnow()
        
        with patch.object(self.director, '_execute_on_agent') as mock_execute:
            mock_execute.return_value = {
                'status': 'completed',
                'task_id': sample_task.id,
                'execution_time': 2.5
            }
            
            result = self.director.execute_task(sample_task)
        
        end_time = datetime.utcnow()
        
        # Verify performance metrics
        metrics = self.director.get_performance_metrics()
        assert 'total_tasks' in metrics
        assert 'average_routing_time' in metrics
        assert 'success_rate' in metrics
        
        # Verify timing
        total_time = (end_time - start_time).total_seconds()
        assert total_time < 1.0  # Should be fast for mocked execution
    
    @pytest.mark.parametrize("task_type,expected_department", [
        ("communication", "communications"),
        ("email", "communications"),
        ("research", "research"),
        ("analysis", "analytics")
    ])
    def test_task_type_routing(self, task_type, expected_department):
        """Test routing based on task type"""
        task = Task(
            title=f"Test {task_type} Task",
            description=f"Test task for {task_type}",
            task_type=task_type,
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            input_data={"type": task_type}
        )
        task.save()
        
        with patch.object(self.director, '_classify_intent') as mock_classify:
            mock_classify.return_value = {
                'intent': f'{task_type}_task',
                'confidence': 0.9,
                'department': expected_department,
                'required_capabilities': [f'{task_type}_handling']
            }
            
            intent = self.director._classify_intent(task)
            assert intent['department'] == expected_department
    
    def test_memory_cleanup(self, sample_task):
        """Test memory cleanup after task execution"""
        import gc
        import psutil
        import os
        
        sample_task.save()
        
        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Execute multiple tasks to test memory cleanup
        for i in range(10):
            task = Task(
                title=f"Memory Test Task {i}",
                description="Task for memory testing",
                task_type="communication",
                priority=TaskPriority.NORMAL,
                status=TaskStatus.PENDING,
                input_data={"memory_test": True}
            )
            task.save()
            
            with patch.object(self.director, '_execute_on_agent') as mock_execute:
                mock_execute.return_value = {'status': 'completed'}
                self.director.execute_task(task)
        
        # Force garbage collection
        gc.collect()
        
        # Check memory usage hasn't grown significantly
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Allow for some growth but not excessive (< 10MB)
        assert memory_growth < 10 * 1024 * 1024, f"Memory grew by {memory_growth} bytes"

# Integration test example
class TestDirectorIntegration:
    """Integration tests for director agent with real components"""
    
    @pytest.fixture(autouse=True)
    def setup_integration_environment(self, app_context, temp_database):
        """Setup integration test environment"""
        self.app = app_context
        self.db = temp_database
        
        # Create real agents and departments
        self.setup_real_agents()
    
    def setup_real_agents(self):
        """Setup real agent instances for integration testing"""
        # Create director
        director_db = Agent(
            name="IntegrationDirector",
            description="Director for integration testing",
            agent_type=AgentType.SUPERVISOR,
            capabilities={"routing": True, "department_management": True}
        )
        director_db.save()
        self.director = DirectorAgent(director_db)
        
        # Create email agent
        email_db = Agent(
            name="IntegrationEmailAgent",
            description="Email agent for integration testing",
            agent_type=AgentType.WORKER,
            capabilities={"email_handling": True}
        )
        email_db.save()
        
        # Register with director
        self.director.register_department(email_db)
    
    def test_end_to_end_email_workflow(self):
        """Test complete email workflow from task creation to completion"""
        # Create email task
        task = Task(
            title="Integration Email Test",
            description="End-to-end email test",
            task_type="email",
            priority=TaskPriority.NORMAL,
            status=TaskStatus.PENDING,
            input_data={
                "recipient": "integration@test.com",
                "subject": "Integration Test",
                "body": "This is an integration test email"
            }
        )
        task.save()
        
        # Mock email sending
        with patch('smtplib.SMTP') as mock_smtp:
            mock_smtp.return_value.__enter__.return_value.send_message.return_value = {}
            
            # Execute task
            result = self.director.execute_task(task)
            
            # Verify results
            assert result['status'] == 'completed'
            assert task.status == TaskStatus.COMPLETED
            assert task.output_data is not None
```

### Test Configuration and Fixtures

```python
# conftest.py
"""
Pytest configuration and shared fixtures for SwarmDirector tests
"""

import pytest
import tempfile
import os
from unittest.mock import patch

from src.swarm_director.app import create_app
from src.swarm_director.models.base import db
from src.swarm_director.models.agent import Agent, AgentType, AgentStatus
from src.swarm_director.models.task import Task, TaskStatus, TaskPriority

@pytest.fixture(scope='session')
def app():
    """Create application for testing"""
    app = create_app('testing')
    return app

@pytest.fixture
def app_context(app):
    """Create application context for tests"""
    with app.app_context():
        yield app

@pytest.fixture
def temp_database(app_context):
    """Create temporary database for tests"""
    db.create_all()
    yield db
    db.session.remove()
    db.drop_all()

@pytest.fixture
def client(app):
    """Create test client"""
    return app.test_client()

@pytest.fixture
def sample_agent():
    """Create sample agent for testing"""
    agent = Agent(
        name="TestAgent",
        description="Agent for testing",
        agent_type=AgentType.WORKER,
        status=AgentStatus.IDLE,
        capabilities={"test": True}
    )
    agent.save()
    return agent

@pytest.fixture
def sample_task():
    """Create sample task for testing"""
    task = Task(
        title="Test Task",
        description="Task for testing",
        task_type="test",
        priority=TaskPriority.NORMAL,
        status=TaskStatus.PENDING,
        input_data={"test": "data"}
    )
    task.save()
    return task

# Pytest configuration
def pytest_configure(config):
    """Configure pytest"""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )

def pytest_collection_modifyitems(config, items):
    """Modify test collection"""
    for item in items:
        # Add unit marker to all tests by default
        if not any(marker.name in ['integration', 'slow'] for marker in item.iter_markers()):
            item.add_marker(pytest.mark.unit)
```

## Related Documentation
- [Testing Guide](../../docs/development/testing.md) - Comprehensive testing documentation
- [Pytest Configuration](../../docs/development/getting_started.md#testing) - Test setup and configuration
- [Coverage Reports](../../reports/coverage/) - Test coverage reports
- [CI/CD Integration](../../docs/deployment/local_development.md#continuous-integration) - Automated testing
- [Mock Strategies](../../docs/development/debugging.md#testing-strategies) - Mocking and test doubles
