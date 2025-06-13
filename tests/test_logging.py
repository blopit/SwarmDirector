"""
Unit tests for the enhanced logging and monitoring system
"""

import json
import logging
import unittest
import os
import sys

# Add the src directory to the path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.utils.logging import (
    setup_structured_logging,
    get_logger,
    set_correlation_id,
    get_correlation_id,
    StructuredFormatter,
    PerformanceMetrics,
    log_agent_action,
    log_task_update
)

class TestStructuredFormatter(unittest.TestCase):
    """Test the structured JSON formatter"""
    
    def setUp(self):
        self.formatter = StructuredFormatter()
    
    def test_basic_formatting(self):
        """Test basic log formatting produces valid JSON"""
        record = logging.LogRecord(
            name='test_logger',
            level=logging.INFO,
            pathname='test.py',
            lineno=10,
            msg='Test message',
            args=(),
            exc_info=None
        )
        
        formatted = self.formatter.format(record)
        log_data = json.loads(formatted)
        
        self.assertIn('timestamp', log_data)
        self.assertEqual(log_data['level'], 'INFO')
        self.assertEqual(log_data['logger'], 'test_logger')
        self.assertEqual(log_data['message'], 'Test message')

class TestCorrelationTracking(unittest.TestCase):
    """Test correlation ID tracking functionality"""
    
    def test_set_and_get_correlation_id(self):
        """Test setting and getting correlation IDs"""
        correlation_id = set_correlation_id('test-id-123')
        self.assertEqual(correlation_id, 'test-id-123')
        self.assertEqual(get_correlation_id(), 'test-id-123')

class TestPerformanceMetrics(unittest.TestCase):
    """Test performance metrics collection"""
    
    def test_system_metrics_collection(self):
        """Test that system metrics are collected successfully"""
        metrics = PerformanceMetrics.get_system_metrics()
        
        # Check that expected keys are present
        expected_keys = [
            'cpu_percent', 'memory_percent', 'memory_available_mb',
            'disk_percent', 'disk_free_gb', 'process_count'
        ]
        
        for key in expected_keys:
            self.assertIn(key, metrics)

if __name__ == '__main__':
    unittest.main()
