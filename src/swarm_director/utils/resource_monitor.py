"""
Resource Monitor for SwarmDirector
Provides system resource monitoring capabilities for async processing
"""

import asyncio
import psutil
import threading
import time
from typing import Dict, List, Any, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import logging

from .metrics import metrics_collector

logger = logging.getLogger(__name__)

class ResourceState(Enum):
    """Resource utilization states"""
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    OVERLOADED = "overloaded"

@dataclass
class ResourceThresholds:
    """Resource utilization thresholds"""
    cpu_high: float = 70.0      # CPU percentage
    cpu_critical: float = 85.0
    memory_high: float = 70.0   # Memory percentage
    memory_critical: float = 85.0
    disk_high: float = 80.0     # Disk percentage
    disk_critical: float = 90.0
    io_high: float = 1000.0     # IO operations per second
    io_critical: float = 2000.0
    network_high: float = 100.0  # MB/s
    network_critical: float = 200.0

@dataclass
class ResourceMetrics:
    """Current resource metrics"""
    timestamp: datetime = field(default_factory=datetime.now)
    
    # CPU metrics
    cpu_percent: float = 0.0
    cpu_count: int = 0
    load_average: tuple = field(default_factory=tuple)
    
    # Memory metrics
    memory_percent: float = 0.0
    memory_total: int = 0
    memory_available: int = 0
    memory_used: int = 0
    
    # Disk metrics
    disk_percent: float = 0.0
    disk_total: int = 0
    disk_used: int = 0
    disk_free: int = 0
    disk_io_read: int = 0
    disk_io_write: int = 0
    
    # Network metrics
    network_bytes_sent: int = 0
    network_bytes_recv: int = 0
    network_packets_sent: int = 0
    network_packets_recv: int = 0
    
    # Process metrics
    process_count: int = 0
    thread_count: int = 0
    
    # State assessment
    overall_state: ResourceState = ResourceState.NORMAL
    bottlenecks: List[str] = field(default_factory=list)

@dataclass
class ResourceMonitorConfig:
    """Configuration for resource monitoring"""
    monitoring_interval: float = 30.0
    history_retention_hours: int = 24
    enable_process_monitoring: bool = True
    enable_network_monitoring: bool = True
    enable_disk_monitoring: bool = True
    thresholds: ResourceThresholds = field(default_factory=ResourceThresholds)
    alert_callback: Optional[Callable] = None

class ResourceMonitor:
    """System resource monitor with alerting capabilities"""
    
    def __init__(self, config: Optional[ResourceMonitorConfig] = None):
        self.config = config or ResourceMonitorConfig()
        self.is_running = False
        self._monitor_task: Optional[asyncio.Task] = None
        self._lock = threading.RLock()
        
        # Metrics storage
        self.current_metrics = ResourceMetrics()
        self.metrics_history: List[ResourceMetrics] = []
        
        # Network baseline for calculating rates
        self._last_network_stats = None
        self._last_disk_stats = None
        self._last_check_time = None
        
        logger.info("ResourceMonitor initialized", extra={
            'monitoring_interval': self.config.monitoring_interval,
            'retention_hours': self.config.history_retention_hours
        })
    
    async def start(self):
        """Start resource monitoring"""
        if self.is_running:
            return
        
        self.is_running = True
        self._monitor_task = asyncio.create_task(self._monitoring_loop())
        logger.info("ResourceMonitor started")
    
    async def stop(self):
        """Stop resource monitoring"""
        if not self.is_running:
            return
        
        self.is_running = False
        if self._monitor_task:
            self._monitor_task.cancel()
            try:
                await self._monitor_task
            except asyncio.CancelledError:
                pass
        
        logger.info("ResourceMonitor stopped")
    
    async def _monitoring_loop(self):
        """Main monitoring loop"""
        while self.is_running:
            try:
                # Collect metrics
                metrics = await self._collect_metrics()
                
                # Update current metrics
                with self._lock:
                    self.current_metrics = metrics
                    self.metrics_history.append(metrics)
                    
                    # Cleanup old metrics
                    cutoff_time = datetime.now() - timedelta(
                        hours=self.config.history_retention_hours
                    )
                    self.metrics_history = [
                        m for m in self.metrics_history 
                        if m.timestamp > cutoff_time
                    ]
                
                # Send metrics to metrics collector
                if metrics_collector:
                    self._publish_metrics(metrics)
                
                # Check for alerts
                if self.config.alert_callback and metrics.overall_state != ResourceState.NORMAL:
                    try:
                        if asyncio.iscoroutinefunction(self.config.alert_callback):
                            await self.config.alert_callback(metrics)
                        else:
                            self.config.alert_callback(metrics)
                    except Exception as e:
                        logger.error(f"Alert callback error: {e}")
                
                # Log critical resource states
                if metrics.overall_state in [ResourceState.CRITICAL, ResourceState.OVERLOADED]:
                    logger.warning(
                        f"Critical resource state: {metrics.overall_state.value}",
                        extra={
                            'cpu_percent': metrics.cpu_percent,
                            'memory_percent': metrics.memory_percent,
                            'disk_percent': metrics.disk_percent,
                            'bottlenecks': metrics.bottlenecks
                        }
                    )
                
                await asyncio.sleep(self.config.monitoring_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Resource monitoring error: {e}")
                await asyncio.sleep(self.config.monitoring_interval)
    
    async def _collect_metrics(self) -> ResourceMetrics:
        """Collect current system resource metrics"""
        metrics = ResourceMetrics()
        current_time = time.time()
        
        try:
            # CPU metrics
            metrics.cpu_percent = psutil.cpu_percent(interval=1)
            metrics.cpu_count = psutil.cpu_count()
            if hasattr(psutil, 'getloadavg'):
                metrics.load_average = psutil.getloadavg()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics.memory_percent = memory.percent
            metrics.memory_total = memory.total
            metrics.memory_available = memory.available
            metrics.memory_used = memory.used
            
            # Disk metrics
            if self.config.enable_disk_monitoring:
                disk = psutil.disk_usage('/')
                metrics.disk_percent = disk.percent
                metrics.disk_total = disk.total
                metrics.disk_used = disk.used
                metrics.disk_free = disk.free
                
                # Disk IO rates
                disk_io = psutil.disk_io_counters()
                if disk_io and self._last_disk_stats and self._last_check_time:
                    time_delta = current_time - self._last_check_time
                    if time_delta > 0:
                        metrics.disk_io_read = int(
                            (disk_io.read_bytes - self._last_disk_stats.read_bytes) / time_delta
                        )
                        metrics.disk_io_write = int(
                            (disk_io.write_bytes - self._last_disk_stats.write_bytes) / time_delta
                        )
                
                self._last_disk_stats = disk_io
            
            # Network metrics
            if self.config.enable_network_monitoring:
                network = psutil.net_io_counters()
                if network:
                    metrics.network_bytes_sent = network.bytes_sent
                    metrics.network_bytes_recv = network.bytes_recv
                    metrics.network_packets_sent = network.packets_sent
                    metrics.network_packets_recv = network.packets_recv
                
                self._last_network_stats = network
            
            # Process metrics
            if self.config.enable_process_monitoring:
                metrics.process_count = len(psutil.pids())
                
                # Count threads for current process
                try:
                    current_process = psutil.Process()
                    metrics.thread_count = current_process.num_threads()
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    metrics.thread_count = 0
            
            # Assess overall state and identify bottlenecks
            metrics.overall_state, metrics.bottlenecks = self._assess_resource_state(metrics)
            
            self._last_check_time = current_time
            
        except Exception as e:
            logger.error(f"Error collecting metrics: {e}")
        
        return metrics
    
    def _assess_resource_state(self, metrics: ResourceMetrics) -> tuple[ResourceState, List[str]]:
        """Assess overall resource state and identify bottlenecks"""
        bottlenecks = []
        max_severity = ResourceState.NORMAL
        
        thresholds = self.config.thresholds
        
        # Check CPU
        if metrics.cpu_percent >= thresholds.cpu_critical:
            bottlenecks.append(f"CPU critical ({metrics.cpu_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.CRITICAL)
        elif metrics.cpu_percent >= thresholds.cpu_high:
            bottlenecks.append(f"CPU high ({metrics.cpu_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.HIGH)
        
        # Check Memory
        if metrics.memory_percent >= thresholds.memory_critical:
            bottlenecks.append(f"Memory critical ({metrics.memory_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.CRITICAL)
        elif metrics.memory_percent >= thresholds.memory_high:
            bottlenecks.append(f"Memory high ({metrics.memory_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.HIGH)
        
        # Check Disk
        if metrics.disk_percent >= thresholds.disk_critical:
            bottlenecks.append(f"Disk critical ({metrics.disk_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.CRITICAL)
        elif metrics.disk_percent >= thresholds.disk_high:
            bottlenecks.append(f"Disk high ({metrics.disk_percent:.1f}%)")
            max_severity = max(max_severity, ResourceState.HIGH)
        
        # Determine final state
        if len(bottlenecks) >= 3:
            max_severity = ResourceState.OVERLOADED
        
        return max_severity, bottlenecks
    
    def _publish_metrics(self, metrics: ResourceMetrics):
        """Publish metrics to the metrics collector"""
        try:
            # System metrics
            metrics_collector.track_gauge('system_cpu_percent', metrics.cpu_percent)
            metrics_collector.track_gauge('system_memory_percent', metrics.memory_percent)
            metrics_collector.track_gauge('system_disk_percent', metrics.disk_percent)
            
            # Process metrics
            if metrics.process_count > 0:
                metrics_collector.track_gauge('system_process_count', metrics.process_count)
            if metrics.thread_count > 0:
                metrics_collector.track_gauge('system_thread_count', metrics.thread_count)
            
            # Resource state
            state_value = {
                ResourceState.NORMAL: 0,
                ResourceState.HIGH: 1,
                ResourceState.CRITICAL: 2,
                ResourceState.OVERLOADED: 3
            }.get(metrics.overall_state, 0)
            
            metrics_collector.track_gauge('system_resource_state', state_value)
            
            # Bottleneck count
            metrics_collector.track_gauge('system_bottleneck_count', len(metrics.bottlenecks))
            
        except Exception as e:
            logger.error(f"Error publishing metrics: {e}")
    
    def get_current_metrics(self) -> ResourceMetrics:
        """Get current resource metrics"""
        with self._lock:
            return self.current_metrics
    
    def get_metrics_history(self, hours: int = 1) -> List[ResourceMetrics]:
        """Get metrics history for specified hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        
        with self._lock:
            return [
                m for m in self.metrics_history 
                if m.timestamp > cutoff_time
            ]
    
    def get_resource_summary(self) -> Dict[str, Any]:
        """Get resource utilization summary"""
        with self._lock:
            metrics = self.current_metrics
            
            return {
                'timestamp': metrics.timestamp.isoformat(),
                'overall_state': metrics.overall_state.value,
                'bottlenecks': metrics.bottlenecks,
                'cpu': {
                    'percent': metrics.cpu_percent,
                    'count': metrics.cpu_count,
                    'load_average': metrics.load_average
                },
                'memory': {
                    'percent': metrics.memory_percent,
                    'total_gb': round(metrics.memory_total / (1024**3), 2),
                    'used_gb': round(metrics.memory_used / (1024**3), 2),
                    'available_gb': round(metrics.memory_available / (1024**3), 2)
                },
                'disk': {
                    'percent': metrics.disk_percent,
                    'total_gb': round(metrics.disk_total / (1024**3), 2),
                    'used_gb': round(metrics.disk_used / (1024**3), 2),
                    'free_gb': round(metrics.disk_free / (1024**3), 2)
                },
                'processes': {
                    'count': metrics.process_count,
                    'threads': metrics.thread_count
                }
            }
    
    def is_resource_available_for_task(self, estimated_cpu: float = 10.0, 
                                     estimated_memory_mb: float = 100.0) -> bool:
        """Check if resources are available for a new task"""
        with self._lock:
            metrics = self.current_metrics
            
            # Check if adding the estimated load would exceed thresholds
            projected_cpu = metrics.cpu_percent + estimated_cpu
            projected_memory_mb = (metrics.memory_used / (1024**2)) + estimated_memory_mb
            projected_memory_percent = (projected_memory_mb * (1024**2) / metrics.memory_total) * 100
            
            thresholds = self.config.thresholds
            
            # Don't allow new tasks if we're already in critical state
            if metrics.overall_state in [ResourceState.CRITICAL, ResourceState.OVERLOADED]:
                return False
            
            # Check if projected usage would exceed high thresholds
            if (projected_cpu > thresholds.cpu_high or 
                projected_memory_percent > thresholds.memory_high):
                return False
            
            return True

# Global resource monitor instance
resource_monitor: Optional[ResourceMonitor] = None

def get_resource_monitor() -> Optional[ResourceMonitor]:
    """Get the global resource monitor instance"""
    return resource_monitor

def initialize_resource_monitor(config: Optional[ResourceMonitorConfig] = None) -> ResourceMonitor:
    """Initialize the global resource monitor"""
    global resource_monitor
    
    if resource_monitor is not None:
        raise ValueError("ResourceMonitor already initialized")
    
    resource_monitor = ResourceMonitor(config)
    return resource_monitor

async def shutdown_resource_monitor():
    """Shutdown the global resource monitor"""
    global resource_monitor
    
    if resource_monitor:
        await resource_monitor.stop()
        resource_monitor = None 