# Enhanced Performance Metrics Module
"""
Enhanced Performance Metrics Collection System
Provides comprehensive application and system metrics with real-time monitoring.
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from collections import deque, defaultdict
from dataclasses import dataclass
from functools import wraps
import psutil
import logging
from contextlib import contextmanager

@dataclass
class MetricDataPoint:
    """Represents a single metric data point"""
    name: str
    value: float
    unit: str
    timestamp: datetime
    tags: Dict[str, str]
    correlation_id: Optional[str] = None

class MetricAggregator:
    """Aggregates metrics over time windows"""
    
    def __init__(self, window_size: int = 3600):  # 1 hour default
        self.window_size = window_size  # seconds
        self.data = defaultdict(lambda: deque())
        self.lock = threading.Lock()
    
    def add_metric(self, metric: MetricDataPoint):
        """Add a metric data point"""
        with self.lock:
            self.data[metric.name].append(metric)
            self._cleanup_old_data(metric.name)
    
    def _cleanup_old_data(self, metric_name: str):
        """Remove data points older than window_size"""
        cutoff_time = datetime.now() - timedelta(seconds=self.window_size)
        while (self.data[metric_name] and 
               self.data[metric_name][0].timestamp < cutoff_time):
            self.data[metric_name].popleft()
    
    def get_aggregated_stats(self, metric_name: str) -> Dict[str, float]:
        """Get aggregated statistics for a metric"""
        with self.lock:
            if metric_name not in self.data or not self.data[metric_name]:
                return {}
            
            values = [point.value for point in self.data[metric_name]]
            
            return {
                'count': len(values),
                'min': min(values),
                'max': max(values),
                'avg': sum(values) / len(values),
                'latest': values[-1],
                'window_size_seconds': self.window_size
            }
    
    def get_all_metrics_summary(self) -> Dict[str, Dict[str, float]]:
        """Get summary of all tracked metrics"""
        return {
            metric_name: self.get_aggregated_stats(metric_name)
            for metric_name in self.data.keys()
        }

class EnhancedPerformanceMetrics:
    """Enhanced performance metrics collection with application-specific KPIs"""
    
    def __init__(self, aggregator: MetricAggregator = None):
        self.aggregator = aggregator or MetricAggregator()
        self.request_times = defaultdict(list)
        self.error_counts = defaultdict(int)
        self.throughput_tracker = defaultdict(lambda: {'count': 0, 'start_time': time.time()})
        self.lock = threading.Lock()
    
    def collect_system_metrics(self, correlation_id: str = None) -> Dict[str, MetricDataPoint]:
        """Collect comprehensive system metrics"""
        timestamp = datetime.now()
        metrics = {}
        
        try:
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=0.1)
            metrics['cpu_usage'] = MetricDataPoint(
                name='cpu_usage',
                value=cpu_percent,
                unit='percent',
                timestamp=timestamp,
                tags={'type': 'system'},
                correlation_id=correlation_id
            )
            
            # Memory metrics
            memory = psutil.virtual_memory()
            metrics['memory_usage'] = MetricDataPoint(
                name='memory_usage',
                value=memory.percent,
                unit='percent',
                timestamp=timestamp,
                tags={'type': 'system'},
                correlation_id=correlation_id
            )
            
            # Process metrics
            process = psutil.Process()
            metrics['process_cpu'] = MetricDataPoint(
                name='process_cpu',
                value=process.cpu_percent(),
                unit='percent',
                timestamp=timestamp,
                tags={'type': 'process'},
                correlation_id=correlation_id
            )
            
            # Add to aggregator
            for metric in metrics.values():
                self.aggregator.add_metric(metric)
                
        except Exception as e:
            logging.error(f"Failed to collect system metrics: {e}")
            
        return metrics
    
    def track_request_time(self, endpoint: str, duration: float, correlation_id: str = None):
        """Track request response time"""
        timestamp = datetime.now()
        
        with self.lock:
            self.request_times[endpoint].append(duration)
            # Keep only last 1000 entries per endpoint
            if len(self.request_times[endpoint]) > 1000:
                self.request_times[endpoint] = self.request_times[endpoint][-1000:]
        
        metric = MetricDataPoint(
            name='request_time',
            value=duration,
            unit='ms',
            timestamp=timestamp,
            tags={'endpoint': endpoint, 'type': 'application'},
            correlation_id=correlation_id
        )
        
        self.aggregator.add_metric(metric)
    
    def track_error_rate(self, endpoint: str, error_type: str, correlation_id: str = None):
        """Track error occurrences"""
        timestamp = datetime.now()
        
        with self.lock:
            self.error_counts[f"{endpoint}:{error_type}"] += 1
        
        metric = MetricDataPoint(
            name='error_count',
            value=1,
            unit='count',
            timestamp=timestamp,
            tags={'endpoint': endpoint, 'error_type': error_type, 'type': 'application'},
            correlation_id=correlation_id
        )
        
        self.aggregator.add_metric(metric)
    
    def get_endpoint_stats(self, endpoint: str) -> Dict[str, Any]:
        """Get statistics for a specific endpoint"""
        with self.lock:
            times = self.request_times.get(endpoint, [])
            
            # Calculate error count for this endpoint
            error_count = sum(
                count for key, count in self.error_counts.items()
                if key.startswith(endpoint + ':')
            )
            
            if not times:
                return {
                    'endpoint': endpoint, 
                    'no_data': True,
                    'error_count': error_count
                }
            
            return {
                'endpoint': endpoint,
                'request_count': len(times),
                'avg_response_time': sum(times) / len(times),
                'min_response_time': min(times),
                'max_response_time': max(times),
                'error_count': error_count
            }
    
    def get_all_endpoint_stats(self) -> Dict[str, Dict[str, Any]]:
        """Get statistics for all tracked endpoints"""
        endpoints = set()
        with self.lock:
            endpoints.update(self.request_times.keys())
            endpoints.update(
                key.split(':')[0] for key in self.error_counts.keys()
            )
        
        return {
            endpoint: self.get_endpoint_stats(endpoint)
            for endpoint in endpoints
        }

def track_performance_metrics(endpoint: str = None):
    """Decorator to automatically track performance metrics"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            endpoint_name = endpoint or f"{func.__module__}.{func.__name__}"
            
            correlation_id = getattr(threading.current_thread(), 'correlation_id', None)
            
            try:
                result = func(*args, **kwargs)
                execution_time = (time.time() - start_time) * 1000
                
                metrics_collector.track_request_time(endpoint_name, execution_time, correlation_id)
                return result
                
            except Exception as e:
                execution_time = (time.time() - start_time) * 1000
                metrics_collector.track_request_time(endpoint_name, execution_time, correlation_id)
                metrics_collector.track_error_rate(endpoint_name, type(e).__name__, correlation_id)
                raise
        
        return wrapper
    return decorator

# Global instances
metrics_aggregator = MetricAggregator()
metrics_collector = EnhancedPerformanceMetrics(metrics_aggregator)

def get_current_metrics_summary() -> Dict[str, Any]:
    """Get a summary of all current metrics"""
    return {
        'system_metrics': metrics_aggregator.get_all_metrics_summary(),
        'endpoint_stats': metrics_collector.get_all_endpoint_stats(),
        'timestamp': datetime.now().isoformat()
    }
