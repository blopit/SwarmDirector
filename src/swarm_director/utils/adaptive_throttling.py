"""
Adaptive Throttling System for SwarmDirector
Dynamically adjusts processing based on system load and resource availability
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Optional, Callable, Any, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import deque
from enum import Enum
import math

from .system_monitor import (
    SystemResourceMonitor, MonitorConfig, ResourceType, AlertLevel,
    get_system_monitor, initialize_system_monitor
)
from .request_queue import (
    RequestQueueManager, QueuePriority, RequestType,
    get_request_queue_manager
)

logger = logging.getLogger(__name__)

class ThrottleAction(Enum):
    """Types of throttling actions"""
    SCALE_UP = "scale_up"
    SCALE_DOWN = "scale_down"
    MAINTAIN = "maintain"
    EMERGENCY_STOP = "emergency_stop"

class LoadLevel(Enum):
    """System load levels"""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

@dataclass
class ThrottlingMetrics:
    """Metrics for throttling decisions"""
    timestamp: datetime
    system_health_score: float
    cpu_usage: float
    memory_usage: float
    active_requests: int
    queue_size: int
    current_concurrency: int
    target_concurrency: int
    throttle_action: ThrottleAction
    load_level: LoadLevel
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'timestamp': self.timestamp.isoformat(),
            'system_health_score': self.system_health_score,
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'active_requests': self.active_requests,
            'queue_size': self.queue_size,
            'current_concurrency': self.current_concurrency,
            'target_concurrency': self.target_concurrency,
            'throttle_action': self.throttle_action.value,
            'load_level': self.load_level.value
        }

@dataclass
class ThrottlingThresholds:
    """Thresholds for throttling decisions"""
    # Load level thresholds
    low_load_threshold: float = 30.0  # Below this is low load
    normal_load_threshold: float = 60.0  # Below this is normal load
    high_load_threshold: float = 80.0  # Below this is high load
    critical_load_threshold: float = 95.0  # Above this is emergency
    
    # Concurrency limits
    min_concurrency: int = 1
    max_concurrency: int = 50
    default_concurrency: int = 10
    
    # Scaling factors
    scale_up_factor: float = 1.5
    scale_down_factor: float = 0.7
    emergency_scale_down: float = 0.3
    
    # Health score thresholds
    healthy_threshold: float = 70.0
    warning_threshold: float = 50.0
    critical_threshold: float = 30.0

@dataclass
class AdaptiveThrottlingConfig:
    """Configuration for adaptive throttling"""
    enabled: bool = True
    adjustment_interval: float = 5.0  # seconds
    metrics_history_size: int = 100
    thresholds: ThrottlingThresholds = field(default_factory=ThrottlingThresholds)
    enable_predictive_scaling: bool = True
    enable_emergency_throttling: bool = True
    smoothing_window: int = 3  # Number of samples for smoothing
    
    # Integration settings
    monitor_config: Optional[MonitorConfig] = None

class LoadPredictor:
    """Predicts future load based on historical data"""
    
    def __init__(self, window_size: int = 10):
        self.window_size = window_size
        self._load_history: deque = deque(maxlen=window_size)
        self._trend_history: deque = deque(maxlen=5)
    
    def add_sample(self, load_value: float):
        """Add a load sample"""
        self._load_history.append((datetime.now(), load_value))
    
    def predict_load(self, horizon_seconds: int = 30) -> float:
        """Predict load for the next horizon_seconds"""
        if len(self._load_history) < 3:
            return self._load_history[-1][1] if self._load_history else 50.0
        
        # Simple linear trend prediction
        values = [sample[1] for sample in self._load_history]
        times = [(sample[0] - self._load_history[0][0]).total_seconds() 
                for sample in self._load_history]
        
        # Calculate linear trend
        n = len(values)
        sum_t = sum(times)
        sum_v = sum(values)
        sum_tv = sum(t * v for t, v in zip(times, values))
        sum_t2 = sum(t * t for t in times)
        
        if sum_t2 == 0:
            return values[-1]
        
        # Linear regression: v = a + b*t
        b = (n * sum_tv - sum_t * sum_v) / (n * sum_t2 - sum_t * sum_t)
        a = (sum_v - b * sum_t) / n
        
        # Predict for horizon
        future_time = times[-1] + horizon_seconds
        predicted = a + b * future_time
        
        # Clamp to reasonable bounds
        return max(0, min(100, predicted))

class AdaptiveThrottlingManager:
    """Main adaptive throttling manager"""
    
    def __init__(self, config: Optional[AdaptiveThrottlingConfig] = None):
        self.config = config or AdaptiveThrottlingConfig()
        self._running = False
        self._adjustment_thread: Optional[threading.Thread] = None
        self._lock = threading.RLock()
        
        # Components
        self._system_monitor: Optional[SystemResourceMonitor] = None
        self._queue_manager: Optional[RequestQueueManager] = None
        self._load_predictor = LoadPredictor()
        
        # State
        self._current_concurrency = self.config.thresholds.default_concurrency
        self._target_concurrency = self.config.thresholds.default_concurrency
        self._last_adjustment_time = datetime.now()
        
        # Metrics
        self._metrics_history: deque = deque(maxlen=self.config.metrics_history_size)
        self._adjustment_callbacks: List[Callable[[ThrottlingMetrics], None]] = []
        
        logger.info("AdaptiveThrottlingManager initialized")
    
    def start(self):
        """Start the adaptive throttling system"""
        with self._lock:
            if self._running:
                logger.warning("Throttling manager already running")
                return
            
            # Initialize system monitor if not already done
            if not self._system_monitor:
                self._system_monitor = get_system_monitor()
                if not self._system_monitor:
                    self._system_monitor = initialize_system_monitor(self.config.monitor_config)
                    self._system_monitor.start()
            
            # Get queue manager
            self._queue_manager = get_request_queue_manager()
            if not self._queue_manager:
                logger.error("Request queue manager not available")
                return
            
            self._running = True
            self._adjustment_thread = threading.Thread(
                target=self._adjustment_loop,
                name="AdaptiveThrottling",
                daemon=True
            )
            self._adjustment_thread.start()
            
            logger.info("Adaptive throttling started")
    
    def stop(self):
        """Stop the adaptive throttling system"""
        with self._lock:
            if not self._running:
                return
            
            self._running = False
            if self._adjustment_thread and self._adjustment_thread.is_alive():
                self._adjustment_thread.join(timeout=5.0)
            
            logger.info("Adaptive throttling stopped")
    
    def add_adjustment_callback(self, callback: Callable[[ThrottlingMetrics], None]):
        """Add callback for throttling adjustments"""
        with self._lock:
            self._adjustment_callbacks.append(callback)
    
    def get_current_concurrency(self) -> int:
        """Get current concurrency limit"""
        return self._current_concurrency
    
    def get_target_concurrency(self) -> int:
        """Get target concurrency limit"""
        return self._target_concurrency
    
    def get_latest_metrics(self) -> Optional[ThrottlingMetrics]:
        """Get the latest throttling metrics"""
        with self._lock:
            return self._metrics_history[-1] if self._metrics_history else None
    
    def get_metrics_history(self, duration_minutes: int = 10) -> List[ThrottlingMetrics]:
        """Get throttling metrics history"""
        with self._lock:
            cutoff_time = datetime.now() - timedelta(minutes=duration_minutes)
            return [m for m in self._metrics_history if m.timestamp >= cutoff_time]
    
    def force_adjustment(self, target_concurrency: Optional[int] = None):
        """Force an immediate throttling adjustment"""
        if target_concurrency is not None:
            self._target_concurrency = max(
                self.config.thresholds.min_concurrency,
                min(self.config.thresholds.max_concurrency, target_concurrency)
            )
        
        self._perform_adjustment()
    
    def _adjustment_loop(self):
        """Main adjustment loop"""
        logger.info("Starting adaptive throttling adjustment loop")
        
        while self._running:
            try:
                self._perform_adjustment()
                time.sleep(self.config.adjustment_interval)
            except Exception as e:
                logger.error(f"Error in adjustment loop: {e}")
                time.sleep(self.config.adjustment_interval)
    
    def _perform_adjustment(self):
        """Perform throttling adjustment based on current conditions"""
        if not self._system_monitor or not self._queue_manager:
            return
        
        try:
            # Get current system state
            snapshot = self._system_monitor.get_current_snapshot()
            health_score = self._system_monitor.get_system_health_score()
            is_overloaded = self._system_monitor.is_system_overloaded()
            
            # Get queue state
            queue_size = self._queue_manager.get_queue_size()
            active_requests = self._queue_manager.get_active_request_count()
            
            # Determine load level
            load_level = self._calculate_load_level(snapshot, health_score)
            
            # Calculate target concurrency
            old_target = self._target_concurrency
            self._target_concurrency = self._calculate_target_concurrency(
                snapshot, health_score, load_level, queue_size, active_requests
            )
            
            # Determine throttle action
            throttle_action = self._determine_throttle_action(old_target, self._target_concurrency)
            
            # Apply smoothing if enabled
            if self.config.smoothing_window > 1:
                self._target_concurrency = self._apply_smoothing(self._target_concurrency)
            
            # Update current concurrency gradually
            self._update_current_concurrency()
            
            # Create metrics
            metrics = ThrottlingMetrics(
                timestamp=datetime.now(),
                system_health_score=health_score,
                cpu_usage=snapshot.cpu_percent,
                memory_usage=snapshot.memory_percent,
                active_requests=active_requests,
                queue_size=queue_size,
                current_concurrency=self._current_concurrency,
                target_concurrency=self._target_concurrency,
                throttle_action=throttle_action,
                load_level=load_level
            )
            
            # Store metrics and notify callbacks
            self._store_metrics(metrics)
            self._notify_callbacks(metrics)
            
            # Update load predictor
            combined_load = (snapshot.cpu_percent + snapshot.memory_percent) / 2
            self._load_predictor.add_sample(combined_load)
            
            logger.debug(f"Throttling adjustment: {throttle_action.value}, "
                        f"concurrency: {self._current_concurrency} -> {self._target_concurrency}, "
                        f"health: {health_score:.1f}")
            
        except Exception as e:
            logger.error(f"Error performing throttling adjustment: {e}")
    
    def _calculate_load_level(self, snapshot, health_score: float) -> LoadLevel:
        """Calculate current system load level"""
        thresholds = self.config.thresholds
        
        # Use combined metric of CPU, memory, and health score
        combined_load = (snapshot.cpu_percent + snapshot.memory_percent) / 2
        
        if health_score < thresholds.critical_threshold or combined_load >= thresholds.critical_load_threshold:
            return LoadLevel.EMERGENCY
        elif health_score < thresholds.warning_threshold or combined_load >= thresholds.high_load_threshold:
            return LoadLevel.CRITICAL
        elif combined_load >= thresholds.normal_load_threshold:
            return LoadLevel.HIGH
        elif combined_load >= thresholds.low_load_threshold:
            return LoadLevel.NORMAL
        else:
            return LoadLevel.LOW
    
    def _calculate_target_concurrency(self, snapshot, health_score: float, 
                                    load_level: LoadLevel, queue_size: int, 
                                    active_requests: int) -> int:
        """Calculate target concurrency based on system state"""
        thresholds = self.config.thresholds
        current = self._target_concurrency
        
        # Base adjustment based on load level
        if load_level == LoadLevel.EMERGENCY:
            target = max(thresholds.min_concurrency, 
                        int(current * thresholds.emergency_scale_down))
        elif load_level == LoadLevel.CRITICAL:
            target = max(thresholds.min_concurrency,
                        int(current * thresholds.scale_down_factor))
        elif load_level == LoadLevel.HIGH:
            # Slight reduction or maintain
            target = max(thresholds.min_concurrency,
                        int(current * 0.9))
        elif load_level == LoadLevel.LOW and queue_size > 0:
            # Scale up if there's work waiting
            target = min(thresholds.max_concurrency,
                        int(current * thresholds.scale_up_factor))
        else:
            target = current
        
        # Predictive scaling if enabled
        if self.config.enable_predictive_scaling:
            predicted_load = self._load_predictor.predict_load(30)
            if predicted_load > thresholds.high_load_threshold:
                target = int(target * 0.8)  # Preemptive scaling down
        
        # Queue-based adjustments
        if queue_size > current * 2:  # Queue building up
            target = min(thresholds.max_concurrency, target + 2)
        elif queue_size == 0 and active_requests < current * 0.5:  # Underutilized
            target = max(thresholds.min_concurrency, target - 1)
        
        return max(thresholds.min_concurrency, 
                  min(thresholds.max_concurrency, target))
    
    def _determine_throttle_action(self, old_target: int, new_target: int) -> ThrottleAction:
        """Determine the type of throttling action"""
        if new_target > old_target:
            return ThrottleAction.SCALE_UP
        elif new_target < old_target:
            if new_target <= self.config.thresholds.min_concurrency:
                return ThrottleAction.EMERGENCY_STOP
            else:
                return ThrottleAction.SCALE_DOWN
        else:
            return ThrottleAction.MAINTAIN
    
    def _apply_smoothing(self, target: int) -> int:
        """Apply smoothing to target concurrency changes"""
        if len(self._metrics_history) < self.config.smoothing_window:
            return target
        
        # Get recent targets
        recent_targets = [m.target_concurrency for m in 
                         list(self._metrics_history)[-self.config.smoothing_window:]]
        recent_targets.append(target)
        
        # Use weighted average (more weight on recent values)
        weights = [i + 1 for i in range(len(recent_targets))]
        weighted_sum = sum(t * w for t, w in zip(recent_targets, weights))
        weight_sum = sum(weights)
        
        smoothed = int(weighted_sum / weight_sum)
        return max(self.config.thresholds.min_concurrency,
                  min(self.config.thresholds.max_concurrency, smoothed))
    
    def _update_current_concurrency(self):
        """Update current concurrency towards target gradually"""
        diff = self._target_concurrency - self._current_concurrency
        
        if diff == 0:
            return
        
        # Gradual adjustment (max 2 steps per adjustment)
        step = max(1, min(2, abs(diff)))
        if diff > 0:
            self._current_concurrency = min(self._target_concurrency,
                                          self._current_concurrency + step)
        else:
            self._current_concurrency = max(self._target_concurrency,
                                          self._current_concurrency - step)
        
        # Update queue manager if available
        if self._queue_manager and hasattr(self._queue_manager, 'update_concurrency_limit'):
            try:
                self._queue_manager.update_concurrency_limit(self._current_concurrency)
            except Exception as e:
                logger.error(f"Error updating queue manager concurrency: {e}")
    
    def _store_metrics(self, metrics: ThrottlingMetrics):
        """Store throttling metrics"""
        with self._lock:
            self._metrics_history.append(metrics)
    
    def _notify_callbacks(self, metrics: ThrottlingMetrics):
        """Notify adjustment callbacks"""
        for callback in self._adjustment_callbacks:
            try:
                callback(metrics)
            except Exception as e:
                logger.error(f"Error in throttling callback: {e}")

# Global throttling manager instance
_throttling_manager: Optional[AdaptiveThrottlingManager] = None

def get_throttling_manager() -> Optional[AdaptiveThrottlingManager]:
    """Get the global throttling manager instance"""
    return _throttling_manager

def initialize_throttling_manager(config: Optional[AdaptiveThrottlingConfig] = None) -> AdaptiveThrottlingManager:
    """Initialize the global throttling manager"""
    global _throttling_manager
    
    if _throttling_manager is not None:
        logger.warning("Throttling manager already initialized")
        return _throttling_manager
    
    _throttling_manager = AdaptiveThrottlingManager(config)
    return _throttling_manager

def shutdown_throttling_manager():
    """Shutdown the global throttling manager"""
    global _throttling_manager
    
    if _throttling_manager:
        _throttling_manager.stop()
        _throttling_manager = None
