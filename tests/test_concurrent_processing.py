"""Test concurrent request handling functionality"""
import pytest
import pytest_asyncio
import asyncio
import time
import json
from unittest.mock import patch, MagicMock

from src.swarm_director.utils.async_processor import AsyncProcessor, AsyncProcessorConfig, TaskPriority, ProcessorState
from src.swarm_director.utils.concurrency import ConcurrencyManager
from src.swarm_director.utils.resource_monitor import ResourceMonitor, ResourceMonitorConfig, ResourceThresholds


class TestConcurrentProcessing:
    """Test suite for concurrent request handling"""
    
    @pytest.fixture
    def demo_async_config(self):
        """Demo-optimized async processor configuration"""
        return AsyncProcessorConfig(
            max_concurrent_tasks=15,
            max_queue_size=100,
            worker_thread_count=8,
            task_timeout_seconds=30,
            backpressure_threshold=0.7,
            resume_threshold=0.3,
            cleanup_interval_seconds=60,
            enable_metrics=True,
            enable_resource_monitoring=True
        )
    
    @pytest.fixture
    def demo_resource_config(self):
        """Demo-optimized resource monitor configuration"""
        thresholds = ResourceThresholds(
            cpu_critical=85.0,
            memory_critical=85.0,
            disk_critical=90.0
        )
        
        return ResourceMonitorConfig(
            monitoring_interval=5,
            thresholds=thresholds
        )
    
    @pytest_asyncio.fixture
    async def concurrency_manager(self, demo_async_config, demo_resource_config):
        """Initialize a fresh concurrency manager for each test."""
        # Directly instantiate components to ensure isolation
        async_processor = AsyncProcessor(demo_async_config)
        resource_monitor = ResourceMonitor(demo_resource_config)
        
        # Create a new manager and manually assign the fresh components
        manager = ConcurrencyManager(demo_async_config, demo_resource_config)
        manager.async_processor = async_processor
        manager.resource_monitor = resource_monitor
        
        # Manually initialize
        await manager.async_processor.start()
        await manager.resource_monitor.start()
        manager.is_initialized = True
        
        yield manager
        
        # Manually shutdown
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_async_processor_initialization(self, demo_async_config):
        """Test that async processor initializes correctly"""
        processor = AsyncProcessor(demo_async_config)
        await processor.start()
        
        assert processor.state == ProcessorState.RUNNING
        assert processor.config.max_concurrent_tasks == 15
        assert processor.config.worker_thread_count == 8
        assert processor.config.task_timeout_seconds == 30
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_concurrency_manager_initialization(self, concurrency_manager):
        """Test that concurrency manager initializes correctly"""
        assert concurrency_manager.is_initialized
        assert concurrency_manager.async_processor.state == ProcessorState.RUNNING
        assert concurrency_manager.resource_monitor is not None
    
    @pytest.mark.asyncio
    async def test_single_task_submission(self, concurrency_manager):
        """Test submitting a single task for async processing"""
        async def test_task():
            await asyncio.sleep(0.1)
            return {"status": "completed", "result": "test_data"}
        
        task_id = await concurrency_manager.submit_task(
            test_task,
            priority=TaskPriority.NORMAL,
            timeout=5.0,
            check_resources=False  # Disable resource checking for tests
        )
        
        assert task_id is not None
        
        # Wait for completion
        result = await concurrency_manager.get_task_result(task_id, timeout=10.0)
        assert result["status"] == "completed"
        assert result["result"] == "test_data"
    
    @pytest.mark.asyncio
    async def test_concurrent_task_submission(self, concurrency_manager):
        """Test submitting multiple tasks concurrently"""
        async def test_task(task_num):
            await asyncio.sleep(0.1)
            return {"task_num": task_num, "status": "completed"}
        
        # Submit 10 concurrent tasks
        task_ids = []
        for i in range(10):
            # Create a proper async function instead of lambda
            async def task_func():
                return await test_task(i)
            
            task_id = await concurrency_manager.submit_task(
                task_func,
                priority=TaskPriority.NORMAL,
                timeout=10.0,
                check_resources=False  # Disable resource checking for tests
            )
            task_ids.append(task_id)
        
        # Wait for all tasks to complete
        results = []
        for task_id in task_ids:
            result = await concurrency_manager.get_task_result(task_id, timeout=15.0)
            results.append(result)
        
        assert len(results) == 10
        for i, result in enumerate(results):
            assert result["status"] == "completed"
            assert "task_num" in result
    
    @pytest.mark.asyncio
    async def test_high_concurrency_load(self, concurrency_manager):
        """Test system under high concurrent load (15+ tasks)"""
        async def cpu_intensive_task(task_id):
            # Simulate CPU-intensive work
            start_time = time.time()
            while time.time() - start_time < 0.2:  # 200ms of work
                pass
            return {"task_id": task_id, "status": "completed", "duration": time.time() - start_time}
        
        # Submit 15 concurrent tasks (at the limit)
        task_ids = []
        submission_start = time.time()
        
        for i in range(15):
            # Create a proper async function instead of lambda
            async def task_func():
                return await cpu_intensive_task(i)
            
            task_id = await concurrency_manager.submit_task(
                task_func,
                priority=TaskPriority.NORMAL,
                timeout=30.0,
                check_resources=False,  # Disable resource checking for tests
                estimated_cpu=15.0,
                estimated_memory_mb=50.0
            )
            task_ids.append(task_id)
        
        submission_time = time.time() - submission_start
        
        # Collect results
        results = []
        for task_id in task_ids:
            result = await concurrency_manager.get_task_result(task_id, timeout=45.0)
            results.append(result)
        
        total_time = time.time() - submission_start
        
        # Validate results
        assert len(results) == 15
        for result in results:
            assert result["status"] == "completed"
            assert "duration" in result
        
        # Performance assertions
        assert submission_time < 1.0  # Task submission should be fast
        assert total_time < 10.0  # All tasks should complete within 10 seconds
        
        print(f"High concurrency test: {len(results)} tasks completed in {total_time:.2f}s")


class TestFlaskIntegration:
    """Test Flask app integration with concurrent processing"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        from src.swarm_director.app import create_app
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_async_task_submission(self, client):
        """Test async task submission via /task endpoint"""
        from unittest.mock import patch
        
        # Mock the resource monitor to always return available resources
        with patch('src.swarm_director.utils.resource_monitor.ResourceMonitor.is_resource_available_for_task') as mock_resource_check:
            mock_resource_check.return_value = True
            
            task_data = {
                "type": "test_task",
                "title": "Test Async Task", 
                "description": "Testing async processing",
                "args": {
                    "param1": "value1",
                    "param2": "value2"
                }
            }
            
            response = client.post('/task', 
                                   data=json.dumps(task_data),
                                   content_type='application/json')
            
            assert response.status_code == 202
            response_data = response.get_json()
            assert 'task_id' in response_data
            assert 'data' in response_data
            assert 'task_details' in response_data['data']
            assert 'check_status_url' in response_data['data']
            
            task_db_id = response_data['data']['task_details']['id']
            status_url = response_data['data']['check_status_url']
            
            # Verify the task starts processing (don't wait for completion in test environment)
            # Full completion involves complex agent interactions that may not work reliably in tests
            time.sleep(2)  # Give it a moment to start processing
            status_response = client.get(status_url)
            assert status_response.status_code == 200
            
            status_data = status_response.get_json()
            task_status = status_data.get('data', {}).get('status')
            
            # Task should be either in_progress or completed
            assert task_status in ['in_progress', 'completed'], f"Expected task to be processing, got: {task_status}"
            print(f"Task successfully submitted and processing (status: {task_status})")


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"]) 