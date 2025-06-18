"""
Performance Metrics Service
Comprehensive performance monitoring and metrics collection for workflow analysis
"""

import time
import psutil
import threading
import uuid
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import statistics
import logging

logger = logging.getLogger(__name__)

class MetricType(Enum):
    """Types of metrics collected"""
    EXECUTION_TIME = "execution_time"
    THROUGHPUT = "throughput"  
    RESOURCE_USAGE = "resource_usage"
    SUCCESS_RATE = "success_rate"
    LATENCY = "latency"
    QUEUE_SIZE = "queue_size"
    AGENT_PERFORMANCE = "agent_performance"
    WORKFLOW_EFFICIENCY = "workflow_efficiency"

class PerformanceLevel(Enum):
    """Performance level classifications"""
    EXCELLENT = "excellent"  # >95th percentile
    GOOD = "good"           # >75th percentile
    AVERAGE = "average"     # 25-75th percentile  
    POOR = "poor"          # <25th percentile
    CRITICAL = "critical"   # <5th percentile

@dataclass
class MetricPoint:
    """Individual metric data point"""
    metric_id: str
    metric_type: MetricType
    value: float
    timestamp: datetime = field(default_factory=datetime.now)
    tags: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

@dataclass
class PerformanceSnapshot:
    """Complete performance snapshot at a point in time"""
    snapshot_id: str
    timestamp: datetime
    workflow_id: Optional[str]
    agent_name: Optional[str]
    phase: Optional[str]
    
    # Timing metrics
    execution_time: float
    queue_time: float
    processing_time: float
    
    # Resource metrics
    cpu_usage: float
    memory_usage: float
    thread_count: int
    
    # Performance metrics
    throughput: float
    success_rate: float
    error_rate: float
    
    # Context
    tags: Dict[str, str] = field(default_factory=dict)

@dataclass
class PerformanceTrend:
    """Performance trend analysis"""
    metric_type: MetricType
    time_window: timedelta
    average: float
    median: float
    percentile_95: float
    percentile_99: float
    min_value: float
    max_value: float
    trend_direction: str  # "improving", "degrading", "stable"
    confidence: float

class PerformanceThreshold:
    """Performance threshold configuration"""
    def __init__(self, metric_type: MetricType, warning_threshold: float, 
                 critical_threshold: float, comparison: str = "greater_than"):
        self.metric_type = metric_type
        self.warning_threshold = warning_threshold
        self.critical_threshold = critical_threshold
        self.comparison = comparison  # "greater_than", "less_than"
    
    def evaluate(self, value: float) -> Optional[str]:
        """Evaluate if threshold is breached"""
        if self.comparison == "greater_than":
            if value > self.critical_threshold:
                return "critical"
            elif value > self.warning_threshold:
                return "warning"
        else:  # less_than
            if value < self.critical_threshold:
                return "critical"
            elif value < self.warning_threshold:
                return "warning"
        return None

class MetricsRegistry:
    """Registry for organizing and managing different metric types"""
    
    def __init__(self, max_points_per_metric: int = 10000):
        self.metrics = defaultdict(lambda: deque(maxlen=max_points_per_metric))
        self.thresholds = {}
        self.aggregators = {}
        self.subscribers = defaultdict(list)
        self._lock = threading.RLock()
    
    def add_metric(self, metric: MetricPoint):
        """Add a metric point"""
        with self._lock:
            self.metrics[metric.metric_type].append(metric)
            
            # Notify subscribers
            for callback in self.subscribers[metric.metric_type]:
                try:
                    callback(metric)
                except Exception as e:
                    logger.error(f"Error in metric subscriber: {e}")
    
    def get_metrics(self, metric_type: MetricType, 
                   time_window: Optional[timedelta] = None) -> List[MetricPoint]:
        """Get metrics for a specific type and time window"""
        with self._lock:
            metrics = list(self.metrics[metric_type])
            
            if time_window:
                cutoff = datetime.now() - time_window
                metrics = [m for m in metrics if m.timestamp >= cutoff]
            
            return metrics
    
    def set_threshold(self, threshold: PerformanceThreshold):
        """Set performance threshold"""
        self.thresholds[threshold.metric_type] = threshold
    
    def check_thresholds(self, metric: MetricPoint) -> Optional[str]:
        """Check if metric breaches any thresholds"""
        threshold = self.thresholds.get(metric.metric_type)
        if threshold:
            return threshold.evaluate(metric.value)
        return None
    
    def subscribe(self, metric_type: MetricType, callback: Callable[[MetricPoint], None]):
        """Subscribe to metric updates"""
        self.subscribers[metric_type].append(callback)
    
    def calculate_trend(self, metric_type: MetricType, 
                       time_window: timedelta) -> Optional[PerformanceTrend]:
        """Calculate performance trend for a metric type"""
        metrics = self.get_metrics(metric_type, time_window)
        if len(metrics) < 5:  # Need minimum data points
            return None
        
        values = [m.value for m in metrics]
        
        # Calculate statistics
        avg = statistics.mean(values)
        median = statistics.median(values)
        
        # Calculate percentiles
        sorted_values = sorted(values)
        n = len(sorted_values)
        p95_idx = int(0.95 * n)
        p99_idx = int(0.99 * n)
        
        p95 = sorted_values[min(p95_idx, n-1)]
        p99 = sorted_values[min(p99_idx, n-1)]
        
        # Calculate trend direction
        if len(values) >= 10:
            first_half = values[:len(values)//2]
            second_half = values[len(values)//2:]
            
            first_avg = statistics.mean(first_half)
            second_avg = statistics.mean(second_half)
            
            change_pct = (second_avg - first_avg) / first_avg * 100
            
            if abs(change_pct) < 5:
                trend_direction = "stable"
                confidence = 0.8
            elif change_pct > 0:
                trend_direction = "degrading"  # Assuming higher values are worse
                confidence = min(0.9, abs(change_pct) / 20)
            else:
                trend_direction = "improving"
                confidence = min(0.9, abs(change_pct) / 20)
        else:
            trend_direction = "stable"
            confidence = 0.5
        
        return PerformanceTrend(
            metric_type=metric_type,
            time_window=time_window,
            average=avg,
            median=median,
            percentile_95=p95,
            percentile_99=p99,
            min_value=min(values),
            max_value=max(values),
            trend_direction=trend_direction,
            confidence=confidence
        )

class PerformanceMetricsCollector:
    """
    Comprehensive performance metrics collection system
    """
    
    def __init__(self, collection_interval: float = 1.0):
        self.collection_interval = collection_interval
        self.registry = MetricsRegistry()
        self.active_timers = {}
        self.snapshots = deque(maxlen=1000)
        
        # Resource monitoring
        self._collecting = True
        self._collection_thread = threading.Thread(target=self._collection_loop, daemon=True)
        self._collection_thread.start()
        
        # Setup default thresholds
        self._setup_default_thresholds()
        
        logger.info("Performance Metrics Collector initialized")
    
    def _setup_default_thresholds(self):
        """Setup default performance thresholds"""
        # Execution time thresholds (in seconds)
        self.registry.set_threshold(PerformanceThreshold(
            MetricType.EXECUTION_TIME, 
            warning_threshold=30.0, 
            critical_threshold=60.0,
            comparison="greater_than"
        ))
        
        # Success rate thresholds (percentage)
        self.registry.set_threshold(PerformanceThreshold(
            MetricType.SUCCESS_RATE, 
            warning_threshold=90.0, 
            critical_threshold=80.0,
            comparison="less_than"
        ))
        
        # CPU usage thresholds (percentage)
        self.registry.set_threshold(PerformanceThreshold(
            MetricType.RESOURCE_USAGE, 
            warning_threshold=80.0, 
            critical_threshold=95.0,
            comparison="greater_than"
        ))
        
        # Throughput thresholds (operations per minute)
        self.registry.set_threshold(PerformanceThreshold(
            MetricType.THROUGHPUT, 
            warning_threshold=10.0, 
            critical_threshold=5.0,
            comparison="less_than"
        ))
    
    def _collection_loop(self):
        """Background collection loop for system metrics"""
        while self._collecting:
            try:
                # Collect system resource metrics
                cpu_percent = psutil.cpu_percent(interval=None)
                memory = psutil.virtual_memory()
                
                # CPU usage metric
                self.record_metric(
                    MetricType.RESOURCE_USAGE,
                    cpu_percent,
                    tags={"resource": "cpu", "type": "usage_percent"}
                )
                
                # Memory usage metric  
                self.record_metric(
                    MetricType.RESOURCE_USAGE,
                    memory.percent,
                    tags={"resource": "memory", "type": "usage_percent"}
                )
                
                # Thread count
                thread_count = threading.active_count()
                self.record_metric(
                    MetricType.RESOURCE_USAGE,
                    thread_count,
                    tags={"resource": "threads", "type": "count"}
                )
                
                time.sleep(self.collection_interval)
                
            except Exception as e:
                logger.error(f"Error in metrics collection loop: {e}")
                time.sleep(5)  # Wait longer on error
    
    def record_metric(self, metric_type: MetricType, value: float, 
                     tags: Dict[str, str] = None, metadata: Dict[str, Any] = None):
        """Record a performance metric"""
        metric = MetricPoint(
            metric_id=str(uuid.uuid4()),
            metric_type=metric_type,
            value=value,
            tags=tags or {},
            metadata=metadata or {}
        )
        
        self.registry.add_metric(metric)
        
        # Check thresholds
        breach_level = self.registry.check_thresholds(metric)
        if breach_level:
            logger.warning(f"Performance threshold breached: {metric_type.value} = {value} ({breach_level})")
    
    def start_timer(self, timer_id: str, tags: Dict[str, str] = None) -> str:
        """Start a performance timer"""
        timer_data = {
            'start_time': time.time(),
            'tags': tags or {}
        }
        self.active_timers[timer_id] = timer_data
        return timer_id
    
    def stop_timer(self, timer_id: str, metric_type: MetricType = MetricType.EXECUTION_TIME) -> float:
        """Stop a performance timer and record the metric"""
        if timer_id not in self.active_timers:
            logger.warning(f"Timer {timer_id} not found")
            return 0.0
        
        timer_data = self.active_timers.pop(timer_id)
        execution_time = time.time() - timer_data['start_time']
        
        self.record_metric(
            metric_type,
            execution_time,
            tags=timer_data['tags'],
            metadata={'timer_id': timer_id}
        )
        
        return execution_time
    
    def record_workflow_performance(self, workflow_id: str, agent_name: str, 
                                  phase: str, execution_time: float, 
                                  success: bool, metadata: Dict[str, Any] = None):
        """Record comprehensive workflow performance metrics"""
        tags = {
            'workflow_id': workflow_id,
            'agent_name': agent_name,
            'phase': phase
        }
        
        # Record execution time
        self.record_metric(
            MetricType.EXECUTION_TIME,
            execution_time,
            tags=tags,
            metadata=metadata
        )
        
        # Record success/failure
        success_value = 1.0 if success else 0.0
        self.record_metric(
            MetricType.SUCCESS_RATE,
            success_value,
            tags=tags,
            metadata=metadata
        )
        
        # Create performance snapshot
        snapshot = self._create_performance_snapshot(
            workflow_id, agent_name, phase, execution_time, success
        )
        self.snapshots.append(snapshot)
    
    def _create_performance_snapshot(self, workflow_id: str, agent_name: str,
                                   phase: str, execution_time: float, 
                                   success: bool) -> PerformanceSnapshot:
        """Create a comprehensive performance snapshot"""
        current_time = datetime.now()
        
        # Get current resource usage
        cpu_usage = psutil.cpu_percent(interval=None)
        memory = psutil.virtual_memory()
        thread_count = threading.active_count()
        
        # Calculate recent success rate
        recent_metrics = self.registry.get_metrics(
            MetricType.SUCCESS_RATE, 
            timedelta(minutes=5)
        )
        
        if recent_metrics:
            success_values = [m.value for m in recent_metrics]
            success_rate = statistics.mean(success_values) * 100
            error_rate = 100 - success_rate
        else:
            success_rate = 100.0 if success else 0.0
            error_rate = 0.0 if success else 100.0
        
        # Calculate throughput (operations per minute)
        throughput_metrics = self.registry.get_metrics(
            MetricType.EXECUTION_TIME,
            timedelta(minutes=1)
        )
        throughput = len(throughput_metrics)
        
        return PerformanceSnapshot(
            snapshot_id=str(uuid.uuid4()),
            timestamp=current_time,
            workflow_id=workflow_id,
            agent_name=agent_name,
            phase=phase,
            execution_time=execution_time,
            queue_time=0.0,  # TODO: Implement queue time tracking
            processing_time=execution_time,
            cpu_usage=cpu_usage,
            memory_usage=memory.percent,
            thread_count=thread_count,
            throughput=throughput,
            success_rate=success_rate,
            error_rate=error_rate,
            tags={'snapshot_type': 'workflow_completion'}
        )
    
    def get_performance_summary(self, time_window: timedelta = None) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        if time_window is None:
            time_window = timedelta(hours=1)
        
        summary = {
            'time_window': str(time_window),
            'timestamp': datetime.now().isoformat(),
            'metrics': {},
            'trends': {},
            'snapshots_count': len(self.snapshots),
            'active_timers': len(self.active_timers)
        }
        
        # Get metrics for each type
        for metric_type in MetricType:
            metrics = self.registry.get_metrics(metric_type, time_window)
            
            if metrics:
                values = [m.value for m in metrics]
                summary['metrics'][metric_type.value] = {
                    'count': len(values),
                    'average': statistics.mean(values),
                    'median': statistics.median(values),
                    'min': min(values),
                    'max': max(values),
                    'latest': values[-1] if values else None
                }
                
                # Calculate trend
                trend = self.registry.calculate_trend(metric_type, time_window)
                if trend:
                    summary['trends'][metric_type.value] = {
                        'direction': trend.trend_direction,
                        'confidence': trend.confidence,
                        'percentile_95': trend.percentile_95,
                        'percentile_99': trend.percentile_99
                    }
        
        return summary
    
    def get_agent_performance(self, agent_name: str, 
                            time_window: timedelta = None) -> Dict[str, Any]:
        """Get performance metrics for a specific agent"""
        if time_window is None:
            time_window = timedelta(hours=1)
        
        # Filter snapshots for this agent
        cutoff = datetime.now() - time_window
        agent_snapshots = [
            s for s in self.snapshots 
            if s.agent_name == agent_name and s.timestamp >= cutoff
        ]
        
        if not agent_snapshots:
            return {
                'agent_name': agent_name,
                'snapshots_count': 0,
                'message': 'No performance data available'
            }
        
        # Calculate agent-specific metrics
        execution_times = [s.execution_time for s in agent_snapshots]
        success_rates = [s.success_rate for s in agent_snapshots]
        cpu_usages = [s.cpu_usage for s in agent_snapshots]
        
        return {
            'agent_name': agent_name,
            'time_window': str(time_window),
            'snapshots_count': len(agent_snapshots),
            'performance': {
                'average_execution_time': statistics.mean(execution_times),
                'median_execution_time': statistics.median(execution_times),
                'max_execution_time': max(execution_times),
                'min_execution_time': min(execution_times),
                'average_success_rate': statistics.mean(success_rates),
                'average_cpu_usage': statistics.mean(cpu_usages),
                'total_operations': len(agent_snapshots)
            },
            'recent_snapshots': [
                {
                    'timestamp': s.timestamp.isoformat(),
                    'execution_time': s.execution_time,
                    'success_rate': s.success_rate,
                    'phase': s.phase
                }
                for s in sorted(agent_snapshots, key=lambda x: x.timestamp, reverse=True)[:5]
            ]
        }
    
    def identify_bottlenecks(self, time_window: timedelta = None) -> List[Dict[str, Any]]:
        """Identify performance bottlenecks"""
        if time_window is None:
            time_window = timedelta(hours=1)
        
        bottlenecks = []
        
        # Check execution time trends
        execution_trend = self.registry.calculate_trend(
            MetricType.EXECUTION_TIME, time_window
        )
        
        if execution_trend and execution_trend.trend_direction == "degrading":
            bottlenecks.append({
                'type': 'execution_time_degradation',
                'severity': 'high' if execution_trend.confidence > 0.8 else 'medium',
                'description': f"Execution times degrading by {execution_trend.confidence:.1%}",
                'metric': execution_trend.average,
                'recommendation': 'Review recent changes and resource utilization'
            })
        
        # Check resource usage
        resource_metrics = self.registry.get_metrics(
            MetricType.RESOURCE_USAGE, time_window
        )
        
        cpu_metrics = [m for m in resource_metrics if m.tags.get('resource') == 'cpu']
        if cpu_metrics:
            avg_cpu = statistics.mean([m.value for m in cpu_metrics])
            if avg_cpu > 80:
                bottlenecks.append({
                    'type': 'high_cpu_usage',
                    'severity': 'critical' if avg_cpu > 95 else 'high',
                    'description': f"High CPU usage: {avg_cpu:.1f}%",
                    'metric': avg_cpu,
                    'recommendation': 'Consider scaling or optimizing CPU-intensive operations'
                })
        
        # Check success rate trends
        success_trend = self.registry.calculate_trend(
            MetricType.SUCCESS_RATE, time_window
        )
        
        if success_trend and success_trend.trend_direction == "degrading":
            bottlenecks.append({
                'type': 'success_rate_degradation',
                'severity': 'critical' if success_trend.average < 0.8 else 'high',
                'description': f"Success rate degrading: {success_trend.average:.1%}",
                'metric': success_trend.average,
                'recommendation': 'Investigate error patterns and failure causes'
            })
        
        return bottlenecks
    
    def stop_collection(self):
        """Stop the metrics collection"""
        self._collecting = False
        if self._collection_thread.is_alive():
            self._collection_thread.join(timeout=5)
        logger.info("Performance metrics collection stopped")

# Global performance metrics service instance
performance_metrics_service = PerformanceMetricsCollector()