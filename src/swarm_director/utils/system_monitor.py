"""
System Resource Monitor for SwarmDirector
Provides real-time monitoring of system resources for adaptive throttling
"""

import psutil
import time
import threading
import logging
from typing import Dict, List, Optional, Callable, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum

logger = logging.getLogger(__name__)

class ResourceType(Enum):
    """Types of system resources to monitor"""
    CPU = "cpu"
    MEMORY = "memory"
    DISK = "disk"
    NETWORK = "network"
    PROCESS = "process"

class AlertLevel(Enum):
    """Alert levels for resource usage"""
    NORMAL = "normal"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class ResourceReading:
    """Single resource measurement"""
    timestamp: datetime
    resource_type: ResourceType
    value: float
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class SystemResourceSnapshot:
    """Complete system resource snapshot at a point in time"""
    timestamp: datetime
    cpu_percent: float
    cpu_count: int
    cpu_freq: Optional[float]
    memory_percent: float
    memory_available: int
    memory_total: int
    disk_usage_percent: float
    disk_read_bytes: int
    disk_write_bytes: int
    network_sent_bytes: int
    network_recv_bytes: int
    process_count: int
    load_average: Optional[List[float]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'cpu_percent': self.cpu_percent,
            'cpu_count': self.cpu_count,
            'cpu_freq': self.cpu_freq,
            'memory_percent': self.memory_percent,
            'memory_available': self.memory_available,
            'memory_total': self.memory_total,
            'disk_usage_percent': self.disk_usage_percent,
            'disk_read_bytes': self.disk_read_bytes,
            'disk_write_bytes': self.disk_write_bytes,
            'network_sent_bytes': self.network_sent_bytes,
            'network_recv_bytes': self.network_recv_bytes,
            'process_count': self.process_count,
            'load_average': self.load_average
        }

@dataclass
class ResourceThresholds:
    """Thresholds for resource usage alerts"""
    cpu_warning: float = 70.0
    cpu_critical: float = 85.0
    cpu_emergency: float = 95.0
    memory_warning: float = 75.0
    memory_critical: float = 90.0
    memory_emergency: float = 98.0
    disk_warning: float = 80.0
    disk_critical: float = 90.0
    disk_emergency: float = 95.0
    process_warning: int = 500
    process_critical: int = 1000
    process_emergency: int = 1500

@dataclass
class MonitorConfig:
    """Configuration for system monitoring"""
    sampling_interval: float = 1.0  # seconds
    history_size: int = 300  # number of samples to keep
    enable_cpu_monitoring: bool = True
    enable_memory_monitoring: bool = True
    enable_disk_monitoring: bool = True
    enable_network_monitoring: bool = True
    enable_process_monitoring: bool = True
    enable_alerts: bool = True
    thresholds: ResourceThresholds = field(default_factory=ResourceThresholds)

class SystemResourceMonitor:
    """Real-time system resource monitor"""
    
    def __init__(self, config: Optional[MonitorConfig] = None):
        self.config = config or MonitorConfig()
        self._running = False
        self._monitor_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Resource history storage
        self._cpu_history: deque = deque(maxlen=self.config.history_size)
        self._memory_history: deque = deque(maxlen=self.config.history_size)
        self._disk_history: deque = deque(maxlen=self.config.history_size)
        self._network_history: deque = deque(maxlen=self.config.history_size)
        self._snapshots: deque = deque(maxlen=self.config.history_size)
        
        # Alert callbacks
        self._alert_callbacks: List[Callable[[ResourceType, AlertLevel, float], None]] = []
        
        # Baseline metrics for delta calculations
        self._last_snapshot_time: Optional[datetime] = None
        
        logger.info("SystemResourceMonitor initialized")
    
    def start(self):
        """Start monitoring system resources"""
        with self._lock:
            if self._running:
                logger.warning("Monitor already running")
                return
            
            self._running = True
            self._monitor_thread = threading.Thread(
                target=self._monitor_loop,
                name="SystemResourceMonitor",
                daemon=True
            )
            self._monitor_thread.start()
            logger.info("System resource monitoring started")
    
    def stop(self):
        """Stop monitoring system resources"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._monitor_thread and self._monitor_thread.is_alive():
                self._monitor_thread.join(timeout=5.0)
            
            logger.info("System resource monitoring stopped")
    
    def get_current_snapshot(self) -> SystemResourceSnapshot:
        """Get current system resource snapshot"""
        return self._collect_snapshot()
    
    def get_system_health_score(self) -> float:
        """Calculate overall system health score (0-100)"""
        try:
            snapshot = self.get_current_snapshot()
            
            # Weight different resources
            cpu_score = max(0, 100 - snapshot.cpu_percent)
            memory_score = max(0, 100 - snapshot.memory_percent)
            disk_score = max(0, 100 - snapshot.disk_usage_percent)
            
            # Weighted average (CPU and memory are more important)
            health_score = (
                cpu_score * 0.4 +
                memory_score * 0.4 +
                disk_score * 0.2
            )
            
            return max(0, min(100, health_score))
        except Exception as e:
            logger.error(f"Error calculating health score: {e}")
            return 50.0  # Default neutral score
    
    def is_system_overloaded(self) -> bool:
        """Check if system is currently overloaded"""
        try:
            snapshot = self.get_current_snapshot()
            thresholds = self.config.thresholds
            
            return (
                snapshot.cpu_percent >= thresholds.cpu_critical or
                snapshot.memory_percent >= thresholds.memory_critical or
                snapshot.disk_usage_percent >= thresholds.disk_critical
            )
        except Exception as e:
            logger.error(f"Error checking system overload: {e}")
            return False
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        logger.info("Starting resource monitoring loop")
        
        while self._running:
            try:
                snapshot = self._collect_snapshot()
                self._store_snapshot(snapshot)
                
                if self.config.enable_alerts:
                    self._check_alerts(snapshot)
                
                time.sleep(self.config.sampling_interval)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(self.config.sampling_interval)
    
    def _collect_snapshot(self) -> SystemResourceSnapshot:
        """Collect current system resource snapshot"""
        now = datetime.now()
        
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=None)
        cpu_count = psutil.cpu_count()
        cpu_freq = None
        try:
            freq = psutil.cpu_freq()
            cpu_freq = freq.current if freq else None
        except:
            pass
        
        # Memory metrics
        memory = psutil.virtual_memory()
        
        # Disk metrics
        disk_usage = psutil.disk_usage('/')
        disk_io = psutil.disk_io_counters()
        disk_read_bytes = disk_io.read_bytes if disk_io else 0
        disk_write_bytes = disk_io.write_bytes if disk_io else 0
        
        # Network metrics
        network_io = psutil.net_io_counters()
        network_sent_bytes = network_io.bytes_sent if network_io else 0
        network_recv_bytes = network_io.bytes_recv if network_io else 0
        
        # Process count
        process_count = len(psutil.pids())
        
        # Load average (Unix systems only)
        load_average = None
        try:
            load_average = list(psutil.getloadavg())
        except:
            pass
        
        return SystemResourceSnapshot(
            timestamp=now,
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq=cpu_freq,
            memory_percent=memory.percent,
            memory_available=memory.available,
            memory_total=memory.total,
            disk_usage_percent=disk_usage.percent,
            disk_read_bytes=disk_read_bytes,
            disk_write_bytes=disk_write_bytes,
            network_sent_bytes=network_sent_bytes,
            network_recv_bytes=network_recv_bytes,
            process_count=process_count,
            load_average=load_average
        )
    
    def _store_snapshot(self, snapshot: SystemResourceSnapshot):
        """Store snapshot and update resource histories"""
        with self._lock:
            self._snapshots.append(snapshot)
    
    def _check_alerts(self, snapshot: SystemResourceSnapshot):
        """Check for resource usage alerts"""
        thresholds = self.config.thresholds
        
        # Check CPU alerts
        if snapshot.cpu_percent >= thresholds.cpu_emergency:
            self._trigger_alert(ResourceType.CPU, AlertLevel.EMERGENCY, snapshot.cpu_percent)
        elif snapshot.cpu_percent >= thresholds.cpu_critical:
            self._trigger_alert(ResourceType.CPU, AlertLevel.CRITICAL, snapshot.cpu_percent)
        elif snapshot.cpu_percent >= thresholds.cpu_warning:
            self._trigger_alert(ResourceType.CPU, AlertLevel.WARNING, snapshot.cpu_percent)
    
    def _trigger_alert(self, resource_type: ResourceType, level: AlertLevel, value: float):
        """Trigger resource usage alert"""
        logger.warning(f"Resource alert: {resource_type.value} {level.value} - {value}%")

# Global monitor instance
_system_monitor: Optional[SystemResourceMonitor] = None

def get_system_monitor() -> Optional[SystemResourceMonitor]:
    """Get the global system monitor instance"""
    return _system_monitor

def initialize_system_monitor(config: Optional[MonitorConfig] = None) -> SystemResourceMonitor:
    """Initialize the global system monitor"""
    global _system_monitor
    
    if _system_monitor is not None:
        logger.warning("System monitor already initialized")
        return _system_monitor
    
    _system_monitor = SystemResourceMonitor(config)
    return _system_monitor

def shutdown_system_monitor():
    """Shutdown the global system monitor"""
    global _system_monitor
    
    if _system_monitor:
        _system_monitor.stop()
        _system_monitor = None 