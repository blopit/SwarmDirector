"""Test concurrent request handling functionality"""
import pytest
import asyncio
import time
import json
from unittest.mock import patch, MagicMock

from src.swarm_director.utils.async_processor import AsyncProcessor, AsyncProcessorConfig, TaskPriority
from src.swarm_director.utils.concurrency import ConcurrencyManager, initialize_concurrency_manager
from src.swarm_director.utils.resource_monitor import ResourceMonitorConfig


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
        from src.swarm_director.utils.resource_monitor import ResourceThresholds
        
        thresholds = ResourceThresholds(
            cpu_critical=85.0,
            memory_critical=85.0,
            disk_critical=90.0
        )
        
        return ResourceMonitorConfig(
            monitoring_interval=5,
            thresholds=thresholds
        )
    
    @pytest.fixture
    async def concurrency_manager(self, demo_async_config, demo_resource_config):
        """Initialize concurrency manager for testing"""
        manager = initialize_concurrency_manager(demo_async_config, demo_resource_config)
        await manager.initialize()
        yield manager
        await manager.shutdown()
    
    @pytest.mark.asyncio
    async def test_async_processor_initialization(self, demo_async_config):
        """Test that async processor initializes correctly"""
        processor = AsyncProcessor(demo_async_config)
        await processor.start()
        
        assert processor.state.value == 'running'
        assert processor.config.max_concurrent_tasks == 15
        assert processor.config.worker_thread_count == 8
        assert processor.config.task_timeout_seconds == 30
        
        await processor.stop()
    
    @pytest.mark.asyncio
    async def test_concurrency_manager_initialization(self, concurrency_manager):
        """Test that concurrency manager initializes correctly"""
        assert concurrency_manager.is_initialized
        assert concurrency_manager.async_processor.state.value == 'running'
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
            timeout=5.0
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
            task_id = await concurrency_manager.submit_task(
                lambda i=i: test_task(i),
                priority=TaskPriority.NORMAL,
                timeout=10.0
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
            task_id = await concurrency_manager.submit_task(
                lambda i=i: cpu_intensive_task(i),
                priority=TaskPriority.NORMAL,
                timeout=30.0,
                check_resources=True,
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
        
        assert response.status_code in [201, 202]  # Either sync (201) or async (202)
        
        data = json.loads(response.data)
        assert data['success'] is True
        assert 'task_id' in data['data']
        
        if response.status_code == 202:  # Async processing
            assert 'async_task_id' in data['data']
            assert 'check_status_url' in data['data']
            assert 'get_result_url' in data['data']


if __name__ == "__main__":
    # Run basic tests
    pytest.main([__file__, "-v"]) 