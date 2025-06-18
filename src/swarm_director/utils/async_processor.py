"""
Asynchronous Processing Manager for SwarmDirector
Provides centralized async processing capabilities with task distribution,
resource management, and performance monitoring
"""

import asyncio
import threading
import time
import uuid
from typing import Dict, List, Any, Optional, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging

from .metrics import metrics_collector, track_performance_metrics

logger = logging.getLogger(__name__)

class ProcessorState(Enum):
    """Async processor states"""
    IDLE = "idle"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPING = "stopping"
    STOPPED = "stopped"
    ERROR = "error"

class TaskPriority(Enum):
    """Task priority levels"""
    LOW = 1
    NORMAL = 2
    HIGH = 3
    CRITICAL = 4

@dataclass
class AsyncProcessorConfig:
    """Configuration for async processor"""
    max_concurrent_tasks: int = 10
    max_queue_size: int = 1000
    worker_thread_count: int = 4
    task_timeout_seconds: int = 300
    backpressure_threshold: float = 0.8
    resume_threshold: float = 0.3
    cleanup_interval_seconds: int = 300
    enable_metrics: bool = True
    enable_resource_monitoring: bool = True

@dataclass
class ProcessorMetrics:
    """Metrics for async processor performance"""
    tasks_queued: int = 0
    tasks_completed: int = 0
    tasks_failed: int = 0
    tasks_timeout: int = 0
    peak_queue_size: int = 0
    peak_concurrent_tasks: int = 0
    total_processing_time: float = 0.0
    average_task_time: float = 0.0
    start_time: Optional[datetime] = None
    last_reset: Optional[datetime] = field(default_factory=datetime.now)

@dataclass
class AsyncTask:
    """Wrapper for async task with metadata"""
    task_id: str
    function: Callable
    args: tuple = field(default_factory=tuple)
    kwargs: dict = field(default_factory=dict)
    priority: TaskPriority = TaskPriority.NORMAL
    timeout: Optional[float] = None
    callback: Optional[Callable] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    result: Any = None
    error: Optional[Exception] = None
    retry_count: int = 0
    max_retries: int = 0

class TaskQueue:
    """Priority-based async task queue with backpressure"""
    
    def __init__(self, config: AsyncProcessorConfig):
        self.config = config
        self._size = 0
        # Initialize as None - will be set during async initialization
        self._queues = None
        self._lock = None
        self._not_empty = None
        self._initialized = False
        self._init_lock = None  # Will be created in async context
        
    async def initialize(self):
        """Initialize asyncio objects when called from async context"""
        if self._initialized:
            return
            
        # Create initialization lock if not exists (in current event loop)
        if self._init_lock is None:
            self._init_lock = asyncio.Lock()
            
        async with self._init_lock:
            if self._initialized:  # Double-check in case another coroutine initialized
                return
                
            # Create all asyncio objects in the current event loop
            self._queues = {
                TaskPriority.CRITICAL: asyncio.Queue(maxsize=self.config.max_queue_size // 4),
                TaskPriority.HIGH: asyncio.Queue(maxsize=self.config.max_queue_size // 4),
                TaskPriority.NORMAL: asyncio.Queue(maxsize=self.config.max_queue_size // 2),
                TaskPriority.LOW: asyncio.Queue(maxsize=self.config.max_queue_size // 4),
            }
            
            # Create lock and event in the same loop atomically  
            loop = asyncio.get_running_loop()
            self._lock = asyncio.Lock()
            self._not_empty = asyncio.Event()  # Use Event instead of Condition
            self._initialized = True

    async def _ensure_initialized(self):
        """Ensure the queue is initialized - alias for initialize()"""
        await self.initialize()
        
    async def put(self, task: AsyncTask) -> bool:
        """Add task to appropriate priority queue"""
        await self._ensure_initialized()
        async with self._lock:
            queue = self._queues[task.priority]
            
            # Check backpressure
            if self._size >= self.config.max_queue_size * self.config.backpressure_threshold:
                return False
            
            try:
                queue.put_nowait(task)
                self._size += 1
                self._not_empty.set()  # Signal that queue is not empty
                return True
            except asyncio.QueueFull:
                return False
    
    async def get(self) -> Optional[AsyncTask]:
        """Get highest priority task from queue"""
        await self._ensure_initialized()
        
        while True:
            async with self._lock:
                if self._size > 0:
                    # Check queues in priority order
                    for priority in [TaskPriority.CRITICAL, TaskPriority.HIGH, 
                                   TaskPriority.NORMAL, TaskPriority.LOW]:
                        queue = self._queues[priority]
                        try:
                            task = queue.get_nowait()
                            self._size -= 1
                            if self._size == 0:
                                self._not_empty.clear()  # Clear event when queue is empty
                            return task
                        except asyncio.QueueEmpty:
                            continue
                    
                    # If we reach here, no tasks were found but size > 0 (shouldn't happen)
                    self._size = 0
                    self._not_empty.clear()
                    return None
                else:
                    # Queue is empty, clear the event and wait
                    self._not_empty.clear()
            
            # Wait for tasks to be added
            await self._not_empty.wait()
    
    def size(self) -> int:
        """Get current queue size"""
        return self._size
    
    def is_backpressure_active(self) -> bool:
        """Check if backpressure is active"""
        return self._size >= self.config.max_queue_size * self.config.backpressure_threshold
    
    def should_resume(self) -> bool:
        """Check if processing should resume"""
        return self._size <= self.config.max_queue_size * self.config.resume_threshold

class AsyncProcessor:
    """Central asynchronous processing manager"""
    
    def __init__(self, config: Optional[AsyncProcessorConfig] = None):
        self.config = config or AsyncProcessorConfig()
        self.state = ProcessorState.IDLE
        self.metrics = ProcessorMetrics()
        
        # Core components
        self.task_queue = TaskQueue(self.config)
        self.active_tasks: Dict[str, AsyncTask] = {}
        self.completed_tasks: Dict[str, AsyncTask] = {}
        
        # Synchronization
        self._lock = threading.RLock()
        self._shutdown_event = threading.Event()
        
        # Thread pool for CPU-bound tasks
        self.thread_pool = ThreadPoolExecutor(
            max_workers=self.config.worker_thread_count,
            thread_name_prefix="AsyncProcessor"
        )
        
        # Background tasks
        self._worker_tasks: List[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("AsyncProcessor initialized", extra={
            'config': {
                'max_concurrent_tasks': self.config.max_concurrent_tasks,
                'max_queue_size': self.config.max_queue_size,
                'worker_threads': self.config.worker_thread_count
            }
        })
    
    async def start(self):
        """Start the async processor"""
        if self.state != ProcessorState.IDLE:
            raise ValueError(f"Cannot start processor in state: {self.state}")
        
        self.state = ProcessorState.RUNNING
        self.metrics.start_time = datetime.now()
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_tasks):
            worker_task = asyncio.create_task(
                self._worker_loop(f"worker-{i}")
            )
            self._worker_tasks.append(worker_task)
        
        # Start background tasks
        if self.config.enable_resource_monitoring:
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        
        logger.info("AsyncProcessor started", extra={
            'worker_count': len(self._worker_tasks),
            'monitoring_enabled': self.config.enable_resource_monitoring
        })
    
    async def stop(self, timeout: float = 30.0):
        """Stop the async processor gracefully"""
        if self.state == ProcessorState.STOPPED:
            return
        
        logger.info("Stopping AsyncProcessor...")
        self.state = ProcessorState.STOPPING
        
        # Cancel background tasks
        if self._cleanup_task:
            self._cleanup_task.cancel()
        if self._monitor_task:
            self._monitor_task.cancel()
        
        # Cancel worker tasks
        for task in self._worker_tasks:
            task.cancel()
        
        # Wait for tasks to complete
        if self._worker_tasks:
            await asyncio.wait(self._worker_tasks, timeout=timeout)
        
        # Shutdown thread pool
        self.thread_pool.shutdown(wait=True)
        
        self.state = ProcessorState.STOPPED
        logger.info("AsyncProcessor stopped")
    
    async def submit_task(self, 
                         function: Callable,
                         *args,
                         priority: TaskPriority = TaskPriority.NORMAL,
                         timeout: Optional[float] = None,
                         callback: Optional[Callable] = None,
                         max_retries: int = 0,
                         **kwargs) -> str:
        """Submit a task for async processing"""
        
        if self.state not in [ProcessorState.RUNNING, ProcessorState.PAUSED]:
            raise ValueError(f"Cannot submit task in state: {self.state}")
        
        task_id = str(uuid.uuid4())
        task = AsyncTask(
            task_id=task_id,
            function=function,
            args=args,
            kwargs=kwargs,
            priority=priority,
            timeout=timeout or self.config.task_timeout_seconds,
            callback=callback,
            max_retries=max_retries
        )
        
        success = await self.task_queue.put(task)
        if not success:
            raise ValueError("Task queue is full (backpressure active)")
        
        with self._lock:
            self.metrics.tasks_queued += 1
            self.metrics.peak_queue_size = max(
                self.metrics.peak_queue_size, 
                self.task_queue.size()
            )
        
        if self.config.enable_metrics:
            metrics_collector.track_request_time(
                'async_processor_tasks_queued',
                1.0  # Count as a metric
            )
        
        logger.debug(f"Task {task_id} queued with priority {priority.name}")
        return task_id
    
    async def get_task_result(self, task_id: str, timeout: Optional[float] = None) -> Any:
        """Get result of a submitted task"""
        start_time = time.time()
        
        while True:
            # Check completed tasks
            with self._lock:
                if task_id in self.completed_tasks:
                    task = self.completed_tasks[task_id]
                    if task.error:
                        raise task.error
                    return task.result
            
            # Check timeout
            if timeout and (time.time() - start_time) > timeout:
                raise TimeoutError(f"Task {task_id} result timeout")
            
            await asyncio.sleep(0.1)
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing tasks"""
        logger.debug(f"Worker {worker_name} started")
        
        while self.state == ProcessorState.RUNNING:
            try:
                # Get next task
                task = await self.task_queue.get()
                if not task:
                    continue
                
                # Process the task
                await self._process_task(task, worker_name)
                
            except asyncio.CancelledError:
                logger.debug(f"Worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Worker {worker_name} stopped")
    
    async def _process_task(self, task: AsyncTask, worker_name: str):
        """Process a single task"""
        task.started_at = datetime.now()
        
        with self._lock:
            self.active_tasks[task.task_id] = task
            self.metrics.peak_concurrent_tasks = max(
                self.metrics.peak_concurrent_tasks,
                len(self.active_tasks)
            )
        
        logger.debug(f"Worker {worker_name} processing task {task.task_id}")
        
        try:
            # Execute the task
            if asyncio.iscoroutinefunction(task.function):
                result = await asyncio.wait_for(
                    task.function(*task.args, **task.kwargs),
                    timeout=task.timeout
                )
            else:
                # Run in thread pool for CPU-bound tasks
                loop = asyncio.get_event_loop()
                result = await asyncio.wait_for(
                    loop.run_in_executor(
                        self.thread_pool,
                        lambda: task.function(*task.args, **task.kwargs)
                    ),
                    timeout=task.timeout
                )
            
            task.result = result
            task.completed_at = datetime.now()
            
            # Execute callback if provided
            if task.callback:
                try:
                    if asyncio.iscoroutinefunction(task.callback):
                        await task.callback(task.result)
                    else:
                        task.callback(task.result)
                except Exception as e:
                    logger.error(f"Task {task.task_id} callback error: {e}")
            
            # Update metrics
            with self._lock:
                self.metrics.tasks_completed += 1
                processing_time = (task.completed_at - task.started_at).total_seconds()
                self.metrics.total_processing_time += processing_time
                self.metrics.average_task_time = (
                    self.metrics.total_processing_time / self.metrics.tasks_completed
                )
            
            if self.config.enable_metrics:
                metrics_collector.track_request_time(
                    'async_processor_tasks_completed',
                    1.0  # Count as a metric
                )
                metrics_collector.track_request_time(
                    'async_processor_task_duration',
                    processing_time * 1000  # Convert to milliseconds
                )
            
            logger.debug(f"Task {task.task_id} completed successfully")
        
        except asyncio.TimeoutError:
            task.error = TimeoutError(f"Task {task.task_id} timeout")
            task.completed_at = datetime.now()
            
            with self._lock:
                self.metrics.tasks_timeout += 1
            
            if self.config.enable_metrics:
                metrics_collector.increment_counter(
                    'async_processor_tasks_timeout_total',
                    {'priority': task.priority.name.lower()}
                )
            
            logger.warning(f"Task {task.task_id} timeout")
        
        except Exception as e:
            task.error = e
            task.completed_at = datetime.now()
            
            # Retry logic
            if task.retry_count < task.max_retries:
                task.retry_count += 1
                task.started_at = None
                task.completed_at = None
                task.error = None
                
                # Re-queue the task
                await self.task_queue.put(task)
                logger.info(f"Task {task.task_id} retrying (attempt {task.retry_count})")
                return
            
            with self._lock:
                self.metrics.tasks_failed += 1
            
            if self.config.enable_metrics:
                metrics_collector.increment_counter(
                    'async_processor_tasks_failed_total',
                    {'priority': task.priority.name.lower(), 'error_type': type(e).__name__}
                )
            
            logger.error(f"Task {task.task_id} failed: {e}")
        
        finally:
            # Move task to completed
            with self._lock:
                if task.task_id in self.active_tasks:
                    del self.active_tasks[task.task_id]
                self.completed_tasks[task.task_id] = task
    
    async def _cleanup_loop(self):
        """Background cleanup of completed tasks"""
        while self.state == ProcessorState.RUNNING:
            try:
                cutoff_time = datetime.now() - timedelta(
                    seconds=self.config.cleanup_interval_seconds
                )
                
                with self._lock:
                    # Remove old completed tasks
                    to_remove = [
                        task_id for task_id, task in self.completed_tasks.items()
                        if task.completed_at and task.completed_at < cutoff_time
                    ]
                    
                    for task_id in to_remove:
                        del self.completed_tasks[task_id]
                
                if to_remove:
                    logger.debug(f"Cleaned up {len(to_remove)} completed tasks")
                
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Background monitoring and metrics collection"""
        while self.state == ProcessorState.RUNNING:
            try:
                # Collect current state metrics
                with self._lock:
                    current_metrics = {
                        'queue_size': self.task_queue.size(),
                        'active_tasks': len(self.active_tasks),
                        'completed_tasks': len(self.completed_tasks),
                        'tasks_queued': self.metrics.tasks_queued,
                        'tasks_completed': self.metrics.tasks_completed,
                        'tasks_failed': self.metrics.tasks_failed,
                        'average_task_time': self.metrics.average_task_time
                    }
                
                if self.config.enable_metrics:
                    metrics_collector.track_gauge(
                        'async_processor_queue_size', 
                        current_metrics['queue_size']
                    )
                    metrics_collector.track_gauge(
                        'async_processor_active_tasks', 
                        current_metrics['active_tasks']
                    )
                
                # Check for backpressure
                if self.task_queue.is_backpressure_active():
                    logger.warning("AsyncProcessor backpressure active")
                    if self.config.enable_metrics:
                        metrics_collector.increment_counter(
                            'async_processor_backpressure_events_total'
                        )
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def get_status(self) -> Dict[str, Any]:
        """Get current processor status"""
        with self._lock:
            return {
                'state': self.state.value,
                'queue_size': self.task_queue.size(),
                'active_tasks': len(self.active_tasks),
                'completed_tasks': len(self.completed_tasks),
                'metrics': {
                    'tasks_queued': self.metrics.tasks_queued,
                    'tasks_completed': self.metrics.tasks_completed,
                    'tasks_failed': self.metrics.tasks_failed,
                    'tasks_timeout': self.metrics.tasks_timeout,
                    'peak_queue_size': self.metrics.peak_queue_size,
                    'peak_concurrent_tasks': self.metrics.peak_concurrent_tasks,
                    'average_task_time': self.metrics.average_task_time,
                    'uptime_seconds': (
                        datetime.now() - self.metrics.start_time
                    ).total_seconds() if self.metrics.start_time else 0
                },
                'config': {
                    'max_concurrent_tasks': self.config.max_concurrent_tasks,
                    'max_queue_size': self.config.max_queue_size,
                    'worker_thread_count': self.config.worker_thread_count,
                    'backpressure_threshold': self.config.backpressure_threshold
                }
            }

# Global async processor instance
async_processor: Optional[AsyncProcessor] = None

def get_async_processor() -> Optional[AsyncProcessor]:
    """Get the global async processor instance"""
    return async_processor

def initialize_async_processor(config: Optional[AsyncProcessorConfig] = None) -> AsyncProcessor:
    """Initialize the global async processor"""
    global async_processor
    
    if async_processor is not None:
        raise ValueError("AsyncProcessor already initialized")
    
    async_processor = AsyncProcessor(config)
    return async_processor

async def shutdown_async_processor():
    """Shutdown the global async processor"""
    global async_processor
    
    if async_processor:
        await async_processor.stop()
        async_processor = None 