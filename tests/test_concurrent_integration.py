"""Integration test for concurrent request handling"""
import pytest
import asyncio
import time
from unittest.mock import patch, MagicMock

from src.swarm_director.utils.async_processor import AsyncProcessor, AsyncProcessorConfig, TaskPriority
from src.swarm_director.utils.concurrency import ConcurrencyManager
from src.swarm_director.utils.resource_monitor import ResourceMonitorConfig, ResourceThresholds


class TestConcurrentProcessingIntegration:
    """Integration tests for concurrent processing with mocked dependencies"""
    
    @pytest.mark.asyncio
    async def test_async_processor_basic_functionality(self):
        """Test basic async processor functionality"""
        config = AsyncProcessorConfig(
            max_concurrent_tasks=5,
            max_queue_size=20,
            worker_thread_count=2,
            task_timeout_seconds=10
        )
        
        processor = AsyncProcessor(config)
        await processor.start()
        
        try:
            # Test single task
            async def simple_task():
                await asyncio.sleep(0.1)
                return {"status": "completed", "data": "test"}
            
            task_id = await processor.submit_task(simple_task)
            result = await processor.get_task_result(task_id, timeout=5.0)
            
            assert result["status"] == "completed"
            assert result["data"] == "test"
            
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_concurrent_task_handling(self):
        """Test handling multiple concurrent tasks"""
        config = AsyncProcessorConfig(
            max_concurrent_tasks=10,
            max_queue_size=50,
            worker_thread_count=4,
            task_timeout_seconds=15
        )
        
        processor = AsyncProcessor(config)
        await processor.start()
        
        try:
            async def numbered_task(num):
                await asyncio.sleep(0.05)  # Small delay
                return {"task_number": num, "status": "completed"}
            
            # Submit 8 concurrent tasks  
            tasks = []
            for i in range(8):
                task = asyncio.create_task(numbered_task(i))
                tasks.append(task)
            
            # Await all tasks
            results = await asyncio.gather(*tasks)
            
            # Validate results
            assert len(results) == 8
            for result in results:
                assert result["status"] == "completed"
                assert "task_number" in result
            
        finally:
            await processor.stop()
    
    @pytest.mark.asyncio
    async def test_performance_under_load(self):
        """Test performance characteristics under simulated load"""
        config = AsyncProcessorConfig(
            max_concurrent_tasks=10,
            max_queue_size=100,
            worker_thread_count=6,
            task_timeout_seconds=20
        )
        
        processor = AsyncProcessor(config)
        await processor.start()
        
        try:
            async def load_task(task_id):
                # Simulate work
                start = time.time()
                await asyncio.sleep(0.1)
                return {
                    "task_id": task_id,
                    "duration": time.time() - start,
                    "status": "completed"
                }
            
            # Submit 12 tasks (above concurrent limit to test queuing)
            start_time = time.time()
            
            tasks = []
            for i in range(12):
                task = asyncio.create_task(load_task(i))
                tasks.append(task)
            
            submission_time = time.time() - start_time
            
            # Collect all results
            results = await asyncio.gather(*tasks)
            
            total_time = time.time() - start_time
            
            # Performance validations
            assert len(results) == 12
            assert submission_time < 1.0  # Quick task submission
            assert total_time < 5.0  # Reasonable total completion time
            
            # All tasks should complete successfully
            for result in results:
                assert result["status"] == "completed"
                assert "duration" in result
            
            print(f"Load test: {len(results)} tasks in {total_time:.2f}s")
            
        finally:
            await processor.stop()


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 