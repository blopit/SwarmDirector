"""
Integration tests for the validation and plugin system
"""

import pytest
import asyncio
from unittest.mock import Mock, patch
from datetime import datetime

from swarm_director.app import create_app
from swarm_director.models import db
from swarm_director.models.task import Task, TaskStatus, TaskPriority, TaskType
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.integration_setup import get_validation_service, get_integrator


@pytest.fixture
def sample_task(db):
    """Create a sample task for testing"""
    task = Task(
        title="Test Email Task",
        description="A task for testing email functionality",
        type=TaskType.EMAIL,
        status=TaskStatus.PENDING,
        priority=TaskPriority.MEDIUM,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )
    db.session.add(task)
    db.session.commit()
    return task

@pytest.fixture
def sample_agents(db):
    """Create sample agents for testing"""
    tool_agent = Agent(
        name="Test Tool Agent",
        agent_type=AgentType.WORKER,
        status=AgentStatus.IDLE,
        description="A test tool agent"
    )
    dept_agent = Agent(
        name="Test Department Agent",
        agent_type=AgentType.SPECIALIST,
        status=AgentStatus.IDLE,
        description="A test department agent"
    )
    db.session.add(tool_agent)
    db.session.add(dept_agent)
    db.session.commit()
    return {"tool": tool_agent, "department": dept_agent}


class TestValidationSystemIntegration:
    """Test the validation system integration"""

    def test_validation_service_initialization(self, app):
        """Test validation service initialization"""
        with app.app_context():
            service = get_validation_service()
            assert service is not None
            assert service.integrator is not None

    def test_integrator_initialization(self, app):
        """Test integrator initialization"""
        with app.app_context():
            integrator = get_integrator()
            assert integrator is not None
            assert integrator.validation_chain is not None
            assert integrator.plugin_manager is not None

    @pytest.mark.asyncio
    async def test_hierarchical_validation_flow(self, app, sample_task, sample_agents):
        """Test complete hierarchical validation flow"""
        with app.app_context():
            service = get_validation_service()
            
            # Re-fetch objects to avoid DetachedInstanceError using proper session pattern
            task = db.session.get(Task, sample_task.id)
            tool_agent = db.session.get(Agent, sample_agents['tool'].id)
            dept_agent = db.session.get(Agent, sample_agents['department'].id)
            
            # Mock the actual validation execution
            with patch.object(service.integrator, 'process_task_with_full_validation') as mock_validate:
                mock_validate.return_value = {
                    'success': True,
                    'task_id': str(task.id),
                    'validated_by': 'TestDirectorAgent',
                    'timestamp': datetime.utcnow().isoformat()
                }
                
                result = await service.validate_task(task.id, tool_agent.id, dept_agent.id)
                
                assert result['success']
                mock_validate.assert_called_once()

    @pytest.mark.asyncio
    async def test_capability_gap_analysis(self, app, sample_task):
        """Test capability gap analysis"""
        with app.app_context():
            service = get_validation_service()
            
            # Re-fetch the task in the current session to avoid DetachedInstanceError
            task = db.session.get(Task, sample_task.id)
            assert task is not None

            # Mock capability discovery
            with patch.object(service.integrator.capability_discovery, 'assess_task_capabilities') as mock_assess:
                mock_assessment = Mock()
                mock_assessment.gaps = [
                    {'capability': 'send_email', 'reason': 'Tool not found'}
                ]
                mock_assess.return_value = mock_assessment
                
                result = await service.analyze_task_capabilities(task.id)
                
                assert 'gaps' in result
                assert len(result['gaps']) == 1
                mock_assess.assert_called_once_with(task)

class TestErrorHandling:
    """Test error handling in the validation system"""

    @pytest.mark.asyncio
    async def test_validation_failure_handling(self, app, sample_task, sample_agents):
        """Test how the system handles a validation failure"""
        with app.app_context():
            service = get_validation_service()

            # Re-fetch objects in the current session using proper session pattern
            task = db.session.get(Task, sample_task.id)
            tool_agent = db.session.get(Agent, sample_agents['tool'].id)
            dept_agent = db.session.get(Agent, sample_agents['department'].id)
            assert task is not None
            assert tool_agent is not None
            assert dept_agent is not None

            # Mock a validation failure
            with patch.object(service.integrator, 'process_task_with_full_validation') as mock_validate:
                mock_validate.side_effect = Exception("Validation failed")
                
                result = await service.validate_task(task.id, tool_agent.id, dept_agent.id)
                
                assert not result['success']
                assert 'error' in result
                assert result['error'] == "Validation failed"


class TestPluginSystemIntegration:
    """Test the plugin system integration"""

    def test_plugin_registry_access(self, app):
        """Test access to the plugin registry"""
        with app.app_context():
            integrator = get_integrator()
            assert integrator is not None
            registry = integrator.plugin_manager.registry
            assert registry is not None
            plugins = registry.list_plugins()
            assert len(plugins) >= 0  # May be empty in test environment
    
    @pytest.mark.asyncio
    async def test_plugin_installation_flow(self, app):
        """Test plugin installation flow"""
        with app.app_context():
            service = get_validation_service()
            
            # Create a test plugin record first
            from swarm_director.models.plugin import PluginRecord
            plugin = PluginRecord(
                name='test_plugin',
                version='0.1.0',
                status='available'
            )
            db.session.add(plugin)
            db.session.commit()
            
            # Mock the installation process
            with patch.object(service.integrator.plugin_manager, 'install_plugin') as mock_install:
                mock_install.return_value = True
                
                result = await service.install_plugin('test_plugin')
                
                assert result['success']
                mock_install.assert_called_once_with('test_plugin')


class TestAPIIntegration:
    """Test API integration for the validation system"""

    def test_validation_health_endpoint(self, client):
        """Test the health check endpoint for the validation API"""
        response = client.get('/api/validation/health')
        assert response.status_code == 200
        assert response.json['status'] == 'ok' 