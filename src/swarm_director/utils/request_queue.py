"""
Request Queuing System for SwarmDirector
Implements blackboard architecture for request management during high load periods
Provides coordination mechanisms using semaphores and mutexes for queue access control
"""

import asyncio
import threading
import time
import uuid
import logging
from typing import Dict, List, Any, Optional, Callable, Union, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
from contextlib import asynccontextmanager
from collections import defaultdict
from flask import request as flask_request, g, has_request_context

from .metrics import metrics_collector, track_performance_metrics
from .async_processor import TaskPriority

logger = logging.getLogger(__name__)

class RequestType(Enum):
    """Types of requests that can be queued"""
    TASK_SUBMISSION = "task_submission"
    AGENT_OPERATION = "agent_operation"
    ANALYTICS_QUERY = "analytics_query"
    STREAMING_REQUEST = "streaming_request"
    HEALTH_CHECK = "health_check"
    API_CALL = "api_call"

class RequestStatus(Enum):
    """Status of requests in the queue"""
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"
    TIMEOUT = "timeout"
    CANCELLED = "cancelled"

class QueuePriority(Enum):
    """Priority levels for request queuing"""
    CRITICAL = 1
    HIGH = 2
    NORMAL = 3
    LOW = 4

@dataclass
class RequestQueueConfig:
    """Configuration for request queue system"""
    max_queue_size: int = 1000
    max_concurrent_requests: int = 20
    request_timeout_seconds: int = 60
    queue_timeout_seconds: int = 30
    backpressure_threshold: float = 0.8
    resume_threshold: float = 0.3
    cleanup_interval_seconds: int = 300
    enable_metrics: bool = True
    enable_blackboard: bool = True
    process_groups_enabled: bool = True

@dataclass
class QueuedRequest:
    """Represents a request in the queue with metadata"""
    request_id: str
    request_type: RequestType
    priority: QueuePriority
    flask_request_data: Dict[str, Any]
    client_id: str
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    status: RequestStatus = RequestStatus.QUEUED
    result: Any = None
    error: Optional[Exception] = None
    timeout: Optional[float] = None
    process_group: Optional[str] = None
    blackboard_data: Dict[str, Any] = field(default_factory=dict)

@dataclass
class QueueMetrics:
    """Metrics for request queue performance"""
    total_requests: int = 0
    requests_queued: int = 0
    requests_processed: int = 0
    requests_failed: int = 0
    requests_timeout: int = 0
    requests_cancelled: int = 0
    peak_queue_size: int = 0
    peak_concurrent_requests: int = 0
    average_queue_time: float = 0.0
    average_processing_time: float = 0.0
    total_queue_time: float = 0.0
    total_processing_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)

class BlackboardSystem:
    """Shared knowledge space for request coordination"""
    
    def __init__(self):
        self._data: Dict[str, Any] = {}
        self._lock = threading.RLock()
        self._subscribers: Dict[str, List[Callable]] = defaultdict(list)
        
    def write(self, key: str, value: Any, notify: bool = True):
        """Write data to blackboard"""
        with self._lock:
            old_value = self._data.get(key)
            self._data[key] = value
            
            if notify and old_value != value:
                self._notify_subscribers(key, value, old_value)
    
    def read(self, key: str, default: Any = None) -> Any:
        """Read data from blackboard"""
        with self._lock:
            return self._data.get(key, default)
    
    def update(self, key: str, updater: Callable[[Any], Any], default: Any = None):
        """Atomically update data in blackboard"""
        with self._lock:
            current_value = self._data.get(key, default)
            new_value = updater(current_value)
            self._data[key] = new_value
            self._notify_subscribers(key, new_value, current_value)
    
    def subscribe(self, key: str, callback: Callable[[str, Any, Any], None]):
        """Subscribe to changes on a key"""
        with self._lock:
            self._subscribers[key].append(callback)
    
    def unsubscribe(self, key: str, callback: Callable):
        """Unsubscribe from changes on a key"""
        with self._lock:
            if callback in self._subscribers[key]:
                self._subscribers[key].remove(callback)
    
    def _notify_subscribers(self, key: str, new_value: Any, old_value: Any):
        """Notify subscribers of changes"""
        for callback in self._subscribers[key]:
            try:
                callback(key, new_value, old_value)
            except Exception as e:
                logger.error(f"Error notifying blackboard subscriber: {e}")
    
    def get_all_data(self) -> Dict[str, Any]:
        """Get all blackboard data (for monitoring)"""
        with self._lock:
            return self._data.copy()

class ProcessGroupManager:
    """Manages worker groups for different request types"""
    
    def __init__(self, config: RequestQueueConfig):
        self.config = config
        self._groups: Dict[str, Dict[str, Any]] = {}
        self._lock = threading.RLock()
        
        # Default process groups
        self._initialize_default_groups()
    
    def _initialize_default_groups(self):
        """Initialize default process groups"""
        default_groups = {
            'task_processing': {
                'max_workers': 8,
                'request_types': [RequestType.TASK_SUBMISSION],
                'priority_boost': 0,
                'resource_limits': {'cpu_percent': 60, 'memory_mb': 1000}
            },
            'agent_operations': {
                'max_workers': 4,
                'request_types': [RequestType.AGENT_OPERATION],
                'priority_boost': 1,
                'resource_limits': {'cpu_percent': 30, 'memory_mb': 500}
            },
            'analytics': {
                'max_workers': 3,
                'request_types': [RequestType.ANALYTICS_QUERY],
                'priority_boost': -1,
                'resource_limits': {'cpu_percent': 20, 'memory_mb': 300}
            },
            'streaming': {
                'max_workers': 6,
                'request_types': [RequestType.STREAMING_REQUEST],
                'priority_boost': 2,
                'resource_limits': {'cpu_percent': 40, 'memory_mb': 600}
            },
            'general': {
                'max_workers': 4,
                'request_types': [RequestType.API_CALL, RequestType.HEALTH_CHECK],
                'priority_boost': 0,
                'resource_limits': {'cpu_percent': 20, 'memory_mb': 200}
            }
        }
        
        with self._lock:
            for group_name, config in default_groups.items():
                self._groups[group_name] = {
                    **config,
                    'active_workers': 0,
                    'total_processed': 0,
                    'total_failed': 0
                }
    
    def get_group_for_request(self, request_type: RequestType) -> str:
        """Get appropriate process group for request type"""
        with self._lock:
            for group_name, group_config in self._groups.items():
                if request_type in group_config['request_types']:
                    return group_name
            return 'general'  # Default fallback
    
    def can_process_request(self, group_name: str) -> bool:
        """Check if group can accept more requests"""
        with self._lock:
            group = self._groups.get(group_name, {})
            max_workers = group.get('max_workers', 1)
            active_workers = group.get('active_workers', 0)
            return active_workers < max_workers
    
    def acquire_worker(self, group_name: str) -> bool:
        """Acquire a worker from the group"""
        with self._lock:
            if self.can_process_request(group_name):
                self._groups[group_name]['active_workers'] += 1
                return True
            return False
    
    def release_worker(self, group_name: str, success: bool = True):
        """Release a worker back to the group"""
        with self._lock:
            if group_name in self._groups:
                self._groups[group_name]['active_workers'] = max(0, 
                    self._groups[group_name]['active_workers'] - 1)
                
                if success:
                    self._groups[group_name]['total_processed'] += 1
                else:
                    self._groups[group_name]['total_failed'] += 1
    
    def get_group_status(self) -> Dict[str, Any]:
        """Get status of all process groups"""
        with self._lock:
            return {
                group_name: {
                    'active_workers': group['active_workers'],
                    'max_workers': group['max_workers'],
                    'utilization': group['active_workers'] / group['max_workers'],
                    'total_processed': group['total_processed'],
                    'total_failed': group['total_failed'],
                    'success_rate': (
                        group['total_processed'] / 
                        max(1, group['total_processed'] + group['total_failed'])
                    )
                }
                for group_name, group in self._groups.items()
            }

class RequestCoordinator:
    """Coordination mechanisms using semaphores and mutexes"""
    
    def __init__(self, config: RequestQueueConfig):
        self.config = config
        
        # Semaphores for controlling concurrent access
        self._queue_semaphore = threading.Semaphore(config.max_concurrent_requests)
        self._processing_semaphore = threading.Semaphore(config.max_concurrent_requests)
        
        # Mutexes for critical sections
        self._queue_mutex = threading.RLock()
        self._metrics_mutex = threading.RLock()
        self._blackboard_mutex = threading.RLock()
        
        # Coordination events
        self._shutdown_event = threading.Event()
        self._backpressure_event = threading.Event()
        
        # Request tracking
        self._active_requests: Set[str] = set()
        self._request_futures: Dict[str, asyncio.Future] = {}
    
    @asynccontextmanager
    async def acquire_processing_slot(self, request_id: str):
        """Acquire a processing slot with timeout"""
        acquired = False
        try:
            # Try to acquire semaphore with timeout
            acquired = self._processing_semaphore.acquire(timeout=self.config.queue_timeout_seconds)
            if not acquired:
                raise TimeoutError("Could not acquire processing slot")
            
            with self._queue_mutex:
                self._active_requests.add(request_id)
            
            yield
            
        finally:
            if acquired:
                self._processing_semaphore.release()
                with self._queue_mutex:
                    self._active_requests.discard(request_id)
    
    def is_backpressure_active(self, queue_size: int) -> bool:
        """Check if backpressure should be activated"""
        threshold = self.config.max_queue_size * self.config.backpressure_threshold
        return queue_size >= threshold
    
    def should_resume_processing(self, queue_size: int) -> bool:
        """Check if processing should resume after backpressure"""
        threshold = self.config.max_queue_size * self.config.resume_threshold
        return queue_size <= threshold
    
    def get_active_request_count(self) -> int:
        """Get number of currently active requests"""
        with self._queue_mutex:
            return len(self._active_requests)

class RequestQueueManager:
    """Main request queuing system with blackboard architecture"""
    
    def __init__(self, config: Optional[RequestQueueConfig] = None):
        self.config = config or RequestQueueConfig()
        self.metrics = QueueMetrics()
        
        # Core components
        self.blackboard = BlackboardSystem() if self.config.enable_blackboard else None
        self.process_groups = ProcessGroupManager(self.config) if self.config.process_groups_enabled else None
        self.coordinator = RequestCoordinator(self.config)
        
        # Queue storage
        self._request_queues: Dict[QueuePriority, asyncio.Queue] = {}
        self._active_requests: Dict[str, QueuedRequest] = {}
        self._completed_requests: Dict[str, QueuedRequest] = {}
        
        # Synchronization
        self._lock = threading.RLock()
        self._initialized = False
        self._running = False
        
        # Background tasks
        self._worker_tasks: List[asyncio.Task] = []
        self._cleanup_task: Optional[asyncio.Task] = None
        self._monitor_task: Optional[asyncio.Task] = None
        
        logger.info("RequestQueueManager initialized", extra={
            'config': {
                'max_queue_size': self.config.max_queue_size,
                'max_concurrent_requests': self.config.max_concurrent_requests,
                'backpressure_threshold': self.config.backpressure_threshold
            }
        })
    
    async def initialize(self):
        """Initialize the request queue system"""
        if self._initialized:
            return
        
        # Initialize priority queues
        for priority in QueuePriority:
            self._request_queues[priority] = asyncio.Queue(
                maxsize=self.config.max_queue_size // len(QueuePriority)
            )
        
        # Initialize blackboard data
        if self.blackboard:
            self.blackboard.write('queue_status', 'initialized')
            self.blackboard.write('active_requests', 0)
            self.blackboard.write('queue_size', 0)
            self.blackboard.write('backpressure_active', False)
        
        self._initialized = True
        logger.info("RequestQueueManager initialized successfully")
    
    async def start(self):
        """Start the request queue processing"""
        if not self._initialized:
            await self.initialize()
        
        if self._running:
            return
        
        self._running = True
        
        # Start worker tasks
        for i in range(self.config.max_concurrent_requests):
            worker_task = asyncio.create_task(
                self._worker_loop(f"request-worker-{i}")
            )
            self._worker_tasks.append(worker_task)
        
        # Start background tasks
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        if self.config.enable_metrics:
            self._monitor_task = asyncio.create_task(self._monitoring_loop())
        
        # Update blackboard
        if self.blackboard:
            self.blackboard.write('queue_status', 'running')
        
        logger.info("RequestQueueManager started", extra={
            'worker_count': len(self._worker_tasks)
        })
    
    async def stop(self, timeout: float = 30.0):
        """Stop the request queue processing"""
        if not self._running:
            return
        
        logger.info("Stopping RequestQueueManager...")
        self._running = False
        
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
        
        # Update blackboard
        if self.blackboard:
            self.blackboard.write('queue_status', 'stopped')
        
        logger.info("RequestQueueManager stopped")
    
    async def queue_request(self, 
                           request_type: RequestType,
                           flask_request_data: Dict[str, Any],
                           priority: QueuePriority = QueuePriority.NORMAL,
                           timeout: Optional[float] = None,
                           client_id: Optional[str] = None) -> str:
        """Queue a request for processing"""
        
        if not self._running:
            raise ValueError("RequestQueueManager is not running")
        
        # Generate request ID
        request_id = str(uuid.uuid4())
        
        # Determine client ID
        if not client_id and has_request_context():
            client_id = flask_request.remote_addr or 'unknown'
        client_id = client_id or 'system'
        
        # Determine process group
        process_group = None
        if self.process_groups:
            process_group = self.process_groups.get_group_for_request(request_type)
        
        # Create queued request
        queued_request = QueuedRequest(
            request_id=request_id,
            request_type=request_type,
            priority=priority,
            flask_request_data=flask_request_data,
            client_id=client_id,
            timeout=timeout or self.config.request_timeout_seconds,
            process_group=process_group
        )
        
        # Check backpressure
        current_queue_size = self._get_total_queue_size()
        if self.coordinator.is_backpressure_active(current_queue_size):
            if self.blackboard:
                self.blackboard.write('backpressure_active', True)
            raise ValueError("Request queue is full (backpressure active)")
        
        # Add to appropriate priority queue
        queue = self._request_queues[priority]
        try:
            queue.put_nowait(queued_request)
        except asyncio.QueueFull:
            raise ValueError(f"Priority queue {priority.name} is full")
        
        # Update metrics and blackboard
        with self._lock:
            self.metrics.total_requests += 1
            self.metrics.requests_queued += 1
            self.metrics.peak_queue_size = max(
                self.metrics.peak_queue_size,
                current_queue_size + 1
            )
        
        if self.blackboard:
            self.blackboard.write('queue_size', current_queue_size + 1)
            self.blackboard.write('last_request_queued', datetime.now().isoformat())
        
        if self.config.enable_metrics:
            metrics_collector.track_request_time(
                'request_queue_requests_queued',
                1.0
            )
        
        logger.debug(f"Request {request_id} queued with priority {priority.name}")
        return request_id
    
    async def get_request_result(self, request_id: str, timeout: Optional[float] = None) -> Any:
        """Get result of a queued request"""
        start_time = time.time()
        timeout = timeout or self.config.request_timeout_seconds
        
        while True:
            # Check completed requests
            with self._lock:
                if request_id in self._completed_requests:
                    request = self._completed_requests[request_id]
                    if request.error:
                        raise request.error
                    return request.result
            
            # Check timeout
            if (time.time() - start_time) > timeout:
                # Cancel request if still active
                with self._lock:
                    if request_id in self._active_requests:
                        self._active_requests[request_id].status = RequestStatus.TIMEOUT
                raise TimeoutError(f"Request {request_id} result timeout")
            
            await asyncio.sleep(0.1)
    
    async def _worker_loop(self, worker_name: str):
        """Main worker loop for processing requests"""
        logger.debug(f"Request worker {worker_name} started")
        
        while self._running:
            try:
                # Get next request from highest priority queue
                request = await self._get_next_request()
                if not request:
                    await asyncio.sleep(0.1)
                    continue
                
                # Process the request
                await self._process_request(request, worker_name)
                
            except asyncio.CancelledError:
                logger.debug(f"Request worker {worker_name} cancelled")
                break
            except Exception as e:
                logger.error(f"Request worker {worker_name} error: {e}")
                await asyncio.sleep(1)
        
        logger.debug(f"Request worker {worker_name} stopped")
    
    async def _process_request(self, request: QueuedRequest, worker_name: str):
        """Process a single request"""
        request.started_at = datetime.now()
        request.status = RequestStatus.PROCESSING
        
        # Check process group availability
        if self.process_groups and request.process_group:
            if not self.process_groups.acquire_worker(request.process_group):
                # Re-queue if no workers available
                queue = self._request_queues[request.priority]
                await queue.put(request)
                return
        
        with self._lock:
            self._active_requests[request.request_id] = request
            self.metrics.peak_concurrent_requests = max(
                self.metrics.peak_concurrent_requests,
                len(self._active_requests)
            )
        
        # Update blackboard
        if self.blackboard:
            self.blackboard.write('active_requests', len(self._active_requests))
            self.blackboard.write(f'request_{request.request_id}', {
                'status': request.status.value,
                'type': request.request_type.value,
                'started_at': request.started_at.isoformat(),
                'worker': worker_name
            })
        
        logger.debug(f"Worker {worker_name} processing request {request.request_id}")
        
        try:
            # Use coordinator to manage processing
            async with self.coordinator.acquire_processing_slot(request.request_id):
                # Process the request (this would integrate with existing Flask request handling)
                result = await self._execute_request(request)
                
                request.result = result
                request.status = RequestStatus.COMPLETED
                request.completed_at = datetime.now()
            
            # Update metrics
            with self._lock:
                self.metrics.requests_processed += 1
                
                # Calculate timing metrics
                queue_time = (request.started_at - request.created_at).total_seconds()
                processing_time = (request.completed_at - request.started_at).total_seconds()
                
                self.metrics.total_queue_time += queue_time
                self.metrics.total_processing_time += processing_time
                self.metrics.average_queue_time = (
                    self.metrics.total_queue_time / self.metrics.requests_processed
                )
                self.metrics.average_processing_time = (
                    self.metrics.total_processing_time / self.metrics.requests_processed
                )
            
            if self.config.enable_metrics:
                metrics_collector.track_request_time(
                    'request_queue_requests_processed',
                    1.0
                )
                metrics_collector.track_request_time(
                    'request_queue_processing_time',
                    processing_time * 1000  # Convert to milliseconds
                )
            
            logger.debug(f"Request {request.request_id} completed successfully")
        
        except asyncio.TimeoutError:
            request.error = TimeoutError(f"Request {request.request_id} timeout")
            request.status = RequestStatus.TIMEOUT
            request.completed_at = datetime.now()
            
            with self._lock:
                self.metrics.requests_timeout += 1
            
            logger.warning(f"Request {request.request_id} timeout")
        
        except Exception as e:
            request.error = e
            request.status = RequestStatus.FAILED
            request.completed_at = datetime.now()
            
            with self._lock:
                self.metrics.requests_failed += 1
            
            if self.config.enable_metrics:
                metrics_collector.increment_counter(
                    'request_queue_requests_failed_total',
                    {'type': request.request_type.value, 'error_type': type(e).__name__}
                )
            
            logger.error(f"Request {request.request_id} failed: {e}")
        
        finally:
            # Release process group worker
            if self.process_groups and request.process_group:
                success = request.status == RequestStatus.COMPLETED
                self.process_groups.release_worker(request.process_group, success)
            
            # Move request to completed
            with self._lock:
                if request.request_id in self._active_requests:
                    del self._active_requests[request.request_id]
                self._completed_requests[request.request_id] = request
            
            # Update blackboard
            if self.blackboard:
                self.blackboard.write('active_requests', len(self._active_requests))
                self.blackboard.write(f'request_{request.request_id}', {
                    'status': request.status.value,
                    'completed_at': request.completed_at.isoformat() if request.completed_at else None,
                    'error': str(request.error) if request.error else None
                })
    
    async def _cleanup_loop(self):
        """Background cleanup of completed requests"""
        while self._running:
            try:
                cutoff_time = datetime.now() - timedelta(
                    seconds=self.config.cleanup_interval_seconds
                )
                
                with self._lock:
                    # Remove old completed requests
                    to_remove = [
                        request_id for request_id, request in self._completed_requests.items()
                        if request.completed_at and request.completed_at < cutoff_time
                    ]
                    
                    for request_id in to_remove:
                        del self._completed_requests[request_id]
                        # Clean up blackboard data
                        if self.blackboard:
                            self.blackboard.write(f'request_{request_id}', None)
                
                if to_remove:
                    logger.debug(f"Cleaned up {len(to_remove)} completed requests")
                
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Background monitoring and metrics collection"""
        while self._running:
            try:
                # Update blackboard with current metrics
                if self.blackboard:
                    current_metrics = {
                        'queue_size': self._get_total_queue_size(),
                        'active_requests': len(self._active_requests),
                        'completed_requests': len(self._completed_requests),
                        'metrics': {
                            'total_requests': self.metrics.total_requests,
                            'requests_processed': self.metrics.requests_processed,
                            'requests_failed': self.metrics.requests_failed,
                            'average_processing_time': self.metrics.average_processing_time
                        }
                    }
                    self.blackboard.write('current_metrics', current_metrics)
                
                # Check for backpressure resolution
                current_queue_size = self._get_total_queue_size()
                if self.coordinator.should_resume_processing(current_queue_size):
                    if self.blackboard:
                        self.blackboard.write('backpressure_active', False)
                
                if self.config.enable_metrics:
                    metrics_collector.track_gauge(
                        'request_queue_size', 
                        current_queue_size
                    )
                    metrics_collector.track_gauge(
                        'request_queue_active_requests', 
                        len(self._active_requests)
                    )
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    async def _get_next_request(self) -> Optional[QueuedRequest]:
        """Get next request from highest priority queue"""
        # Check queues in priority order
        for priority in [QueuePriority.CRITICAL, QueuePriority.HIGH, 
                        QueuePriority.NORMAL, QueuePriority.LOW]:
            queue = self._request_queues[priority]
            try:
                request = queue.get_nowait()
                return request
            except asyncio.QueueEmpty:
                continue
        
        return None
    
    async def _process_request(self, request: QueuedRequest, worker_name: str):
        """Process a single request"""
        request.started_at = datetime.now()
        request.status = RequestStatus.PROCESSING
        
        # Check process group availability
        if self.process_groups and request.process_group:
            if not self.process_groups.acquire_worker(request.process_group):
                # Re-queue if no workers available
                queue = self._request_queues[request.priority]
                await queue.put(request)
                return
        
        with self._lock:
            self._active_requests[request.request_id] = request
            self.metrics.peak_concurrent_requests = max(
                self.metrics.peak_concurrent_requests,
                len(self._active_requests)
            )
        
        # Update blackboard
        if self.blackboard:
            self.blackboard.write('active_requests', len(self._active_requests))
            self.blackboard.write(f'request_{request.request_id}', {
                'status': request.status.value,
                'type': request.request_type.value,
                'started_at': request.started_at.isoformat(),
                'worker': worker_name
            })
        
        logger.debug(f"Worker {worker_name} processing request {request.request_id}")
        
        try:
            # Use coordinator to manage processing
            async with self.coordinator.acquire_processing_slot(request.request_id):
                # Process the request (this would integrate with existing Flask request handling)
                result = await self._execute_request(request)
                
                request.result = result
                request.status = RequestStatus.COMPLETED
                request.completed_at = datetime.now()
            
            # Update metrics
            with self._lock:
                self.metrics.requests_processed += 1
                
                # Calculate timing metrics
                queue_time = (request.started_at - request.created_at).total_seconds()
                processing_time = (request.completed_at - request.started_at).total_seconds()
                
                self.metrics.total_queue_time += queue_time
                self.metrics.total_processing_time += processing_time
                self.metrics.average_queue_time = (
                    self.metrics.total_queue_time / self.metrics.requests_processed
                )
                self.metrics.average_processing_time = (
                    self.metrics.total_processing_time / self.metrics.requests_processed
                )
            
            if self.config.enable_metrics:
                metrics_collector.track_request_time(
                    'request_queue_requests_processed',
                    1.0
                )
                metrics_collector.track_request_time(
                    'request_queue_processing_time',
                    processing_time * 1000  # Convert to milliseconds
                )
            
            logger.debug(f"Request {request.request_id} completed successfully")
        
        except asyncio.TimeoutError:
            request.error = TimeoutError(f"Request {request.request_id} timeout")
            request.status = RequestStatus.TIMEOUT
            request.completed_at = datetime.now()
            
            with self._lock:
                self.metrics.requests_timeout += 1
            
            logger.warning(f"Request {request.request_id} timeout")
        
        except Exception as e:
            request.error = e
            request.status = RequestStatus.FAILED
            request.completed_at = datetime.now()
            
            with self._lock:
                self.metrics.requests_failed += 1
            
            if self.config.enable_metrics:
                metrics_collector.increment_counter(
                    'request_queue_requests_failed_total',
                    {'type': request.request_type.value, 'error_type': type(e).__name__}
                )
            
            logger.error(f"Request {request.request_id} failed: {e}")
        
        finally:
            # Release process group worker
            if self.process_groups and request.process_group:
                success = request.status == RequestStatus.COMPLETED
                self.process_groups.release_worker(request.process_group, success)
            
            # Move request to completed
            with self._lock:
                if request.request_id in self._active_requests:
                    del self._active_requests[request.request_id]
                self._completed_requests[request.request_id] = request
            
            # Update blackboard
            if self.blackboard:
                self.blackboard.write('active_requests', len(self._active_requests))
                self.blackboard.write(f'request_{request.request_id}', {
                    'status': request.status.value,
                    'completed_at': request.completed_at.isoformat() if request.completed_at else None,
                    'error': str(request.error) if request.error else None
                })
    
    async def _execute_request(self, request: QueuedRequest) -> Any:
        """Execute the actual request (placeholder for integration)"""
        # This is where we would integrate with the existing Flask request processing
        # For now, return a placeholder result
        await asyncio.sleep(0.1)  # Simulate processing time
        return {
            'request_id': request.request_id,
            'type': request.request_type.value,
            'status': 'processed',
            'timestamp': datetime.now().isoformat()
        }
    
    async def _cleanup_loop(self):
        """Background cleanup of completed requests"""
        while self._running:
            try:
                cutoff_time = datetime.now() - timedelta(
                    seconds=self.config.cleanup_interval_seconds
                )
                
                with self._lock:
                    # Remove old completed requests
                    to_remove = [
                        request_id for request_id, request in self._completed_requests.items()
                        if request.completed_at and request.completed_at < cutoff_time
                    ]
                    
                    for request_id in to_remove:
                        del self._completed_requests[request_id]
                        # Clean up blackboard data
                        if self.blackboard:
                            self.blackboard.write(f'request_{request_id}', None)
                
                if to_remove:
                    logger.debug(f"Cleaned up {len(to_remove)} completed requests")
                
                await asyncio.sleep(self.config.cleanup_interval_seconds)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Cleanup loop error: {e}")
                await asyncio.sleep(60)
    
    async def _monitoring_loop(self):
        """Background monitoring and metrics collection"""
        while self._running:
            try:
                # Update blackboard with current metrics
                if self.blackboard:
                    current_metrics = {
                        'queue_size': self._get_total_queue_size(),
                        'active_requests': len(self._active_requests),
                        'completed_requests': len(self._completed_requests),
                        'metrics': {
                            'total_requests': self.metrics.total_requests,
                            'requests_processed': self.metrics.requests_processed,
                            'requests_failed': self.metrics.requests_failed,
                            'average_processing_time': self.metrics.average_processing_time
                        }
                    }
                    self.blackboard.write('current_metrics', current_metrics)
                
                # Check for backpressure resolution
                current_queue_size = self._get_total_queue_size()
                if self.coordinator.should_resume_processing(current_queue_size):
                    if self.blackboard:
                        self.blackboard.write('backpressure_active', False)
                
                if self.config.enable_metrics:
                    metrics_collector.track_gauge(
                        'request_queue_size', 
                        current_queue_size
                    )
                    metrics_collector.track_gauge(
                        'request_queue_active_requests', 
                        len(self._active_requests)
                    )
                
                await asyncio.sleep(30)  # Monitor every 30 seconds
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Monitoring loop error: {e}")
                await asyncio.sleep(60)
    
    def _get_total_queue_size(self) -> int:
        """Get total size across all priority queues"""
        return sum(queue.qsize() for queue in self._request_queues.values())
    
    def get_status(self) -> Dict[str, Any]:
        """Get current queue status"""
        with self._lock:
            status = {
                'running': self._running,
                'queue_size': self._get_total_queue_size(),
                'active_requests': len(self._active_requests),
                'completed_requests': len(self._completed_requests),
                'metrics': {
                    'total_requests': self.metrics.total_requests,
                    'requests_queued': self.metrics.requests_queued,
                    'requests_processed': self.metrics.requests_processed,
                    'requests_failed': self.metrics.requests_failed,
                    'requests_timeout': self.metrics.requests_timeout,
                    'peak_queue_size': self.metrics.peak_queue_size,
                    'peak_concurrent_requests': self.metrics.peak_concurrent_requests,
                    'average_queue_time': self.metrics.average_queue_time,
                    'average_processing_time': self.metrics.average_processing_time
                },
                'config': {
                    'max_queue_size': self.config.max_queue_size,
                    'max_concurrent_requests': self.config.max_concurrent_requests,
                    'backpressure_threshold': self.config.backpressure_threshold
                }
            }
            
            # Add process group status if enabled
            if self.process_groups:
                status['process_groups'] = self.process_groups.get_group_status()
            
            # Add blackboard data if enabled
            if self.blackboard:
                status['blackboard'] = self.blackboard.get_all_data()
            
            return status

# Global request queue manager instance
request_queue_manager: Optional[RequestQueueManager] = None

def get_request_queue_manager() -> Optional[RequestQueueManager]:
    """Get the global request queue manager instance"""
    return request_queue_manager

def initialize_request_queue_manager(config: Optional[RequestQueueConfig] = None) -> RequestQueueManager:
    """Initialize the global request queue manager"""
    global request_queue_manager
    
    if request_queue_manager is not None:
        raise ValueError("RequestQueueManager already initialized")
    
    request_queue_manager = RequestQueueManager(config)
    return request_queue_manager

async def shutdown_request_queue_manager():
    """Shutdown the global request queue manager"""
    global request_queue_manager
    
    if request_queue_manager:
        await request_queue_manager.stop()
        request_queue_manager = None 