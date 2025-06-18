"""
Concurrency Utilities for SwarmDirector
Provides high-level concurrency management integrating async processing and resource monitoring
"""

import asyncio
import functools
import time
from typing import Dict, List, Any, Optional, Callable, Union, TypeVar, Awaitable
from datetime import datetime
import logging

from .async_processor import (
    AsyncProcessor, AsyncProcessorConfig, TaskPriority, 
    get_async_processor, initialize_async_processor
)
from .resource_monitor import (
    ResourceMonitor, ResourceMonitorConfig, ResourceState,
    get_resource_monitor, initialize_resource_monitor
)
from .metrics import metrics_collector

logger = logging.getLogger(__name__)

T = TypeVar('T')

class ConcurrencyManager:
    """High-level concurrency manager coordinating async processing and resource monitoring"""
    
    def __init__(self, 
                 async_config: Optional[AsyncProcessorConfig] = None,
                 resource_config: Optional[ResourceMonitorConfig] = None):
        
        self.async_processor: Optional[AsyncProcessor] = None
        self.resource_monitor: Optional[ResourceMonitor] = None
        
        self.async_config = async_config or AsyncProcessorConfig()
        self.resource_config = resource_config or ResourceMonitorConfig()
        
        self.is_initialized = False
        
        logger.info("ConcurrencyManager created")
    
    async def initialize(self):
        """Initialize all concurrency components"""
        if self.is_initialized:
            return
        
        # Initialize async processor
        self.async_processor = initialize_async_processor(self.async_config)
        await self.async_processor.start()
        
        # Initialize resource monitor
        self.resource_monitor = initialize_resource_monitor(self.resource_config)
        await self.resource_monitor.start()
        
        self.is_initialized = True
        logger.info("ConcurrencyManager initialized")
    
    async def shutdown(self):
        """Shutdown all concurrency components"""
        if not self.is_initialized:
            return
        
        if self.async_processor:
            await self.async_processor.stop()
        
        if self.resource_monitor:
            await self.resource_monitor.stop()
        
        self.is_initialized = False
        logger.info("ConcurrencyManager shutdown")
    
    async def submit_task(self, 
                         function: Callable,
                         *args,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None,
                         check_resources: bool = True,
                         estimated_cpu: float = 10.0,
                         estimated_memory_mb: float = 100.0,
                         **kwargs) -> str:
        """Submit a task with optional resource checking"""
        
        if not self.is_initialized:
            raise ValueError("ConcurrencyManager not initialized")
        
        # Check resource availability if requested
        if check_resources and self.resource_monitor:
            if not self.resource_monitor.is_resource_available_for_task(
                estimated_cpu, estimated_memory_mb
            ):
                current_metrics = self.resource_monitor.get_current_metrics()
                raise ResourceError(
                    f"Insufficient resources for task. Current state: {current_metrics.overall_state.value}"
                )
        
        # Submit to async processor
        return await self.async_processor.submit_task(
            function, *args,
            priority=priority,
            timeout=timeout,
            **kwargs
        )
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get result of a submitted task"""
        if not self.is_initialized:
            raise ValueError("ConcurrencyManager not initialized")
        
        return await self.async_processor.get_task_result(task_id, timeout)
    
    def get_status(self) -> Dict[str, Any]:
        """Get comprehensive status of concurrency system"""
        status = {
            'initialized': self.is_initialized,
            'timestamp': datetime.now().isoformat()
        }
        
        if self.async_processor:
            status['async_processor'] = self.async_processor.get_status()
        
        if self.resource_monitor:
            status['resource_monitor'] = self.resource_monitor.get_resource_summary()
        
        return status

class ResourceError(Exception):
    """Exception raised when resources are insufficient for a task"""
    pass

# Global concurrency manager instance
concurrency_manager: Optional[ConcurrencyManager] = None

def get_concurrency_manager() -> Optional[ConcurrencyManager]:
    """Get the global concurrency manager instance"""
    return concurrency_manager

def initialize_concurrency_manager(
    async_config: Optional[AsyncProcessorConfig] = None,
    resource_config: Optional[ResourceMonitorConfig] = None
) -> ConcurrencyManager:
    """Initialize the global concurrency manager"""
    global concurrency_manager
    
    if concurrency_manager is not None:
        raise ValueError("ConcurrencyManager already initialized")
    
    concurrency_manager = ConcurrencyManager(async_config, resource_config)
    return concurrency_manager

async def shutdown_concurrency_manager():
    """Shutdown the global concurrency manager"""
    global concurrency_manager
    
    if concurrency_manager:
        await concurrency_manager.shutdown()
        concurrency_manager = None

# Decorator utilities for async processing

def async_task(priority: TaskPriority = TaskPriority.NORMAL,
               timeout: Optional[float] = None,
               check_resources: bool = True,
               estimated_cpu: float = 10.0,
               estimated_memory_mb: float = 100.0):
    """Decorator to mark a function for async processing"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Awaitable[str]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> str:
            manager = get_concurrency_manager()
            if not manager:
                raise ValueError("ConcurrencyManager not initialized")
            
            return await manager.submit_task(
                func, *args,
                priority=priority,
                timeout=timeout,
                check_resources=check_resources,
                estimated_cpu=estimated_cpu,
                estimated_memory_mb=estimated_memory_mb,
                **kwargs
            )
        
        return wrapper
    
    return decorator

def concurrent_task(priority: TaskPriority = TaskPriority.NORMAL,
                   timeout: Optional[float] = None):
    """Decorator to automatically submit function to async processor and return result"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., Awaitable[T]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            manager = get_concurrency_manager()
            if not manager:
                # Fall back to direct execution if manager not available
                if asyncio.iscoroutinefunction(func):
                    return await func(*args, **kwargs)
                else:
                    return func(*args, **kwargs)
            
            task_id = await manager.submit_task(
                func, *args,
                priority=priority,
                timeout=timeout,
                **kwargs
            )
            
            return await manager.get_task_result(task_id, timeout)
        
        return wrapper
    
    return decorator

def resource_aware(estimated_cpu: float = 10.0, 
                  estimated_memory_mb: float = 100.0):
    """Decorator to add resource awareness to a function"""
    
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> T:
            monitor = get_resource_monitor()
            if monitor:
                if not monitor.is_resource_available_for_task(estimated_cpu, estimated_memory_mb):
                    current_metrics = monitor.get_current_metrics()
                    raise ResourceError(
                        f"Insufficient resources for {func.__name__}. "
                        f"Current state: {current_metrics.overall_state.value}"
                    )
            
            return func(*args, **kwargs)
        
        return wrapper
    
    return decorator

# Utility functions for concurrent execution

async def run_concurrent_tasks(tasks: List[Callable], 
                              priority: TaskPriority = TaskPriority.NORMAL,
                              timeout: Optional[float] = None,
                              max_concurrent: Optional[int] = None) -> List[Any]:
    """Run multiple tasks concurrently and return results"""
    
    manager = get_concurrency_manager()
    if not manager:
        raise ValueError("ConcurrencyManager not initialized")
    
    # Submit all tasks
    task_ids = []
    for task in tasks:
        if callable(task):
            task_id = await manager.submit_task(
                task,
                priority=priority,
                timeout=timeout
            )
            task_ids.append(task_id)
        else:
            raise ValueError("All items in tasks list must be callable")
    
    # Collect results
    results = []
    for task_id in task_ids:
        result = await manager.get_task_result(task_id, timeout)
        results.append(result)
    
    return results

async def run_with_resource_limits(func: Callable, 
                                  *args,
                                  max_cpu: float = 50.0,
                                  max_memory_mb: float = 500.0,
                                  **kwargs) -> Any:
    """Run a function with resource limit checks"""
    
    monitor = get_resource_monitor()
    if monitor:
        if not monitor.is_resource_available_for_task(max_cpu, max_memory_mb):
            current_metrics = monitor.get_current_metrics()
            raise ResourceError(
                f"Resource limits exceeded. Current state: {current_metrics.overall_state.value}"
            )
    
    start_time = time.time()
    
    try:
        if asyncio.iscoroutinefunction(func):
            result = await func(*args, **kwargs)
        else:
            result = func(*args, **kwargs)
        
        execution_time = time.time() - start_time
        
        # Track metrics
        if metrics_collector:
            metrics_collector.track_request_time(
                f'concurrent_execution_{func.__name__}',
                execution_time * 1000
            )
        
        return result
    
    except Exception as e:
        execution_time = time.time() - start_time
        
        # Track error metrics
        if metrics_collector:
            metrics_collector.track_error_rate(
                f'concurrent_execution_{func.__name__}',
                type(e).__name__
            )
        
        raise

# Context managers for resource management

class ResourceContext:
    """Context manager for resource-aware execution"""
    
    def __init__(self, estimated_cpu: float = 10.0, estimated_memory_mb: float = 100.0):
        self.estimated_cpu = estimated_cpu
        self.estimated_memory_mb = estimated_memory_mb
        self.start_time = None
    
    def __enter__(self):
        monitor = get_resource_monitor()
        if monitor:
            if not monitor.is_resource_available_for_task(
                self.estimated_cpu, self.estimated_memory_mb
            ):
                current_metrics = monitor.get_current_metrics()
                raise ResourceError(
                    f"Insufficient resources. Current state: {current_metrics.overall_state.value}"
                )
        
        self.start_time = time.time()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            execution_time = time.time() - self.start_time
            
            # Track metrics
            if metrics_collector:
                metrics_collector.track_request_time(
                    'resource_context_execution',
                    execution_time * 1000
                )

class AsyncBatch:
    """Context manager for batching async operations"""
    
    def __init__(self, batch_size: int = 10, priority: TaskPriority = TaskPriority.NORMAL):
        self.batch_size = batch_size
        self.priority = priority
        self.tasks = []
        self.task_ids = []
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        # Submit any remaining tasks
        if self.tasks:
            await self._submit_batch()
    
    async def add_task(self, func: Callable, *args, **kwargs):
        """Add a task to the batch"""
        self.tasks.append((func, args, kwargs))
        
        if len(self.tasks) >= self.batch_size:
            await self._submit_batch()
    
    async def _submit_batch(self):
        """Submit current batch of tasks"""
        manager = get_concurrency_manager()
        if not manager:
            raise ValueError("ConcurrencyManager not initialized")
        
        for func, args, kwargs in self.tasks:
            task_id = await manager.submit_task(
                func, *args,
                priority=self.priority,
                **kwargs
            )
            self.task_ids.append(task_id)
        
        self.tasks.clear()
    
    async def get_results(self, timeout: Optional[float] = None) -> List[Any]:
        """Get results of all submitted tasks"""
        manager = get_concurrency_manager()
        if not manager:
            raise ValueError("ConcurrencyManager not initialized")
        
        results = []
        for task_id in self.task_ids:
            result = await manager.get_task_result(task_id, timeout)
            results.append(result)
        
        return results 