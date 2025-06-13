"""
Unit tests for the enhanced performance metrics collection system
"""

import unittest
import time
import threading
from datetime import datetime, timedelta
import sys
import os

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.utils.metrics import (
    MetricDataPoint,
    MetricAggregator,
    EnhancedPerformanceMetrics,
    track_performance_metrics,
    get_current_metrics_summary,
    metrics_collector,
    metrics_aggregator
)

class TestMetricDataPoint(unittest.TestCase):
    """Test the MetricDataPoint dataclass"""
    
    def test_metric_data_point_creation(self):
        """Test basic metric data point creation"""
        timestamp = datetime.now()
        metric = MetricDataPoint(
            name='test_metric',
            value=42.5,
            unit='ms',
            timestamp=timestamp,
            tags={'type': 'test'},
            correlation_id='test-123'
        )
        
        self.assertEqual(metric.name, 'test_metric')
        self.assertEqual(metric.value, 42.5)
        self.assertEqual(metric.unit, 'ms')
        self.assertEqual(metric.timestamp, timestamp)
        self.assertEqual(metric.tags, {'type': 'test'})
        self.assertEqual(metric.correlation_id, 'test-123')

class TestMetricAggregator(unittest.TestCase):
    """Test the MetricAggregator class"""
    
    def setUp(self):
        self.aggregator = MetricAggregator(window_size=3600)  # 1 hour
    
    def test_add_metric(self):
        """Test adding metrics to aggregator"""
        metric = MetricDataPoint(
            name='cpu_usage',
            value=50.0,
            unit='percent',
            timestamp=datetime.now(),
            tags={'type': 'system'}
        )
        
        self.aggregator.add_metric(metric)
        
        # Check that metric was added
        self.assertIn('cpu_usage', self.aggregator.data)
        self.assertEqual(len(self.aggregator.data['cpu_usage']), 1)
    
    def test_aggregated_stats(self):
        """Test aggregated statistics calculation"""
        timestamp = datetime.now()
        
        # Add multiple metrics
        for i, value in enumerate([10, 20, 30, 40, 50]):
            metric = MetricDataPoint(
                name='test_metric',
                value=value,
                unit='count',
                timestamp=timestamp + timedelta(seconds=i),
                tags={'type': 'test'}
            )
            self.aggregator.add_metric(metric)
        
        stats = self.aggregator.get_aggregated_stats('test_metric')
        
        self.assertEqual(stats['count'], 5)
        self.assertEqual(stats['min'], 10)
        self.assertEqual(stats['max'], 50)
        self.assertEqual(stats['avg'], 30)
        self.assertEqual(stats['latest'], 50)
    
    def test_old_data_cleanup(self):
        """Test that old data is cleaned up"""
        # Create aggregator with very short window
        short_aggregator = MetricAggregator(window_size=1)  # 1 second
        
        # Add old metric
        old_metric = MetricDataPoint(
            name='old_metric',
            value=100,
            unit='count',
            timestamp=datetime.now() - timedelta(seconds=5),
            tags={'type': 'test'}
        )
        short_aggregator.add_metric(old_metric)
        
        # Add recent metric
        recent_metric = MetricDataPoint(
            name='old_metric',
            value=200,
            unit='count',
            timestamp=datetime.now(),
            tags={'type': 'test'}
        )
        short_aggregator.add_metric(recent_metric)
        
        # Check that only recent metric remains
        stats = short_aggregator.get_aggregated_stats('old_metric')
        self.assertEqual(stats['count'], 1)
        self.assertEqual(stats['latest'], 200)

class TestEnhancedPerformanceMetrics(unittest.TestCase):
    """Test the EnhancedPerformanceMetrics class"""
    
    def setUp(self):
        self.aggregator = MetricAggregator()
        self.metrics = EnhancedPerformanceMetrics(self.aggregator)
    
    def test_system_metrics_collection(self):
        """Test system metrics collection"""
        system_metrics = self.metrics.collect_system_metrics('test-correlation-123')
        
        # Check that expected metrics are present
        expected_metrics = ['cpu_usage', 'memory_usage', 'process_cpu']
        for metric_name in expected_metrics:
            self.assertIn(metric_name, system_metrics)
            
            metric = system_metrics[metric_name]
            self.assertIsInstance(metric.value, (int, float))
            self.assertIsInstance(metric.unit, str)
            self.assertEqual(metric.correlation_id, 'test-correlation-123')
    
    def test_request_time_tracking(self):
        """Test request time tracking"""
        endpoint = '/api/test'
        duration = 150.5
        
        self.metrics.track_request_time(endpoint, duration, 'test-123')
        
        # Check endpoint stats
        stats = self.metrics.get_endpoint_stats(endpoint)
        
        self.assertEqual(stats['endpoint'], endpoint)
        self.assertEqual(stats['request_count'], 1)
        self.assertEqual(stats['avg_response_time'], duration)
        self.assertEqual(stats['min_response_time'], duration)
        self.assertEqual(stats['max_response_time'], duration)
    
    def test_error_tracking(self):
        """Test error rate tracking"""
        endpoint = '/api/test'
        error_type = 'ValueError'
        
        self.metrics.track_error_rate(endpoint, error_type, 'test-123')
        
        # Check that error was recorded
        error_key = f"{endpoint}:{error_type}"
        self.assertEqual(self.metrics.error_counts[error_key], 1)
        
        # Check endpoint stats
        stats = self.metrics.get_endpoint_stats(endpoint)
        self.assertEqual(stats['error_count'], 1)
    
    def test_multiple_endpoint_stats(self):
        """Test tracking multiple endpoints"""
        # Track multiple requests
        self.metrics.track_request_time('/api/users', 100.0)
        self.metrics.track_request_time('/api/tasks', 200.0)
        self.metrics.track_request_time('/api/users', 150.0)
        
        all_stats = self.metrics.get_all_endpoint_stats()
        
        self.assertIn('/api/users', all_stats)
        self.assertIn('/api/tasks', all_stats)
        
        users_stats = all_stats['/api/users']
        self.assertEqual(users_stats['request_count'], 2)
        self.assertEqual(users_stats['avg_response_time'], 125.0)

class TestPerformanceDecorator(unittest.TestCase):
    """Test the track_performance_metrics decorator"""
    
    def test_decorator_tracks_successful_execution(self):
        """Test that decorator tracks successful function execution"""
        
        @track_performance_metrics(endpoint='/test/function')
        def test_function():
            time.sleep(0.1)  # Simulate work
            return 'success'
        
        result = test_function()
        
        self.assertEqual(result, 'success')
        
        # Check that metrics were recorded
        stats = metrics_collector.get_endpoint_stats('/test/function')
        self.assertEqual(stats['request_count'], 1)
        self.assertGreater(stats['avg_response_time'], 90)  # Should be > 100ms
    
    def test_decorator_tracks_errors(self):
        """Test that decorator tracks function errors"""
        
        @track_performance_metrics(endpoint='/test/error_function')
        def error_function():
            raise ValueError('Test error')
        
        with self.assertRaises(ValueError):
            error_function()
        
        # Check that error was tracked
        stats = metrics_collector.get_endpoint_stats('/test/error_function')
        self.assertEqual(stats['error_count'], 1)

class TestMetricsIntegration(unittest.TestCase):
    """Test integration functionality"""
    
    def test_current_metrics_summary(self):
        """Test getting current metrics summary"""
        # Generate some metrics
        metrics_collector.track_request_time('/api/test', 100.0)
        metrics_collector.collect_system_metrics('test-123')
        
        summary = get_current_metrics_summary()
        
        self.assertIn('system_metrics', summary)
        self.assertIn('endpoint_stats', summary)
        self.assertIn('timestamp', summary)
        
        # Check timestamp format
        timestamp = datetime.fromisoformat(summary['timestamp'])
        self.assertIsInstance(timestamp, datetime)

if __name__ == '__main__':
    unittest.main() 