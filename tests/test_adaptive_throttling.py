"""
Tests for Adaptive Throttling System
Tests system monitoring, load prediction, and dynamic throttling
"""

import pytest
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta

from src.swarm_director.utils.system_monitor import (
    SystemResourceMonitor, MonitorConfig, ResourceType, AlertLevel,
    SystemResourceSnapshot, ResourceThresholds,
    initialize_system_monitor, shutdown_system_monitor
)
from src.swarm_director.utils.adaptive_throttling import (
    AdaptiveThrottlingManager, AdaptiveThrottlingConfig, ThrottlingThresholds,
    LoadLevel, ThrottleAction, LoadPredictor, ThrottlingMetrics,
    initialize_throttling_manager, shutdown_throttling_manager
)


class TestSystemResourceMonitor:
    """Test system resource monitoring functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.config = MonitorConfig(
            sampling_interval=0.1,  # Fast sampling for tests
            history_size=10,
            enable_alerts=True
        )
        self.monitor = SystemResourceMonitor(self.config)
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if self.monitor:
            self.monitor.stop()
    
    def test_monitor_initialization(self):
        """Test system monitor initialization"""
        assert self.monitor.config.sampling_interval == 0.1
        assert self.monitor.config.history_size == 10
        assert not self.monitor._running
    
    def test_monitor_start_stop(self):
        """Test starting and stopping the monitor"""
        assert not self.monitor._running
        
        self.monitor.start()
        assert self.monitor._running
        assert self.monitor._monitor_thread is not None
        
        self.monitor.stop()
        assert not self.monitor._running
    
    def test_get_current_snapshot(self):
        """Test getting current system snapshot"""
        snapshot = self.monitor.get_current_snapshot()
        
        assert isinstance(snapshot, SystemResourceSnapshot)
        assert isinstance(snapshot.timestamp, datetime)
        assert 0 <= snapshot.cpu_percent <= 100
        assert 0 <= snapshot.memory_percent <= 100
        assert 0 <= snapshot.disk_usage_percent <= 100
        assert snapshot.cpu_count > 0
        assert snapshot.memory_total > 0
        assert snapshot.process_count > 0
    
    def test_health_score_calculation(self):
        """Test system health score calculation"""
        health_score = self.monitor.get_system_health_score()
        
        assert 0 <= health_score <= 100
        assert isinstance(health_score, float)
    
    def test_system_overload_detection(self):
        """Test system overload detection"""
        # Mock high resource usage
        with patch.object(self.monitor, 'get_current_snapshot') as mock_snapshot:
            mock_snapshot.return_value = SystemResourceSnapshot(
                timestamp=datetime.now(),
                cpu_percent=95.0,  # High CPU
                cpu_count=4,
                cpu_freq=2400.0,
                memory_percent=95.0,  # High memory
                memory_available=1000000,
                memory_total=8000000,
                disk_usage_percent=95.0,  # High disk
                disk_read_bytes=1000,
                disk_write_bytes=1000,
                network_sent_bytes=1000,
                network_recv_bytes=1000,
                process_count=100
            )
            
            assert self.monitor.is_system_overloaded()
    
    def test_snapshot_serialization(self):
        """Test snapshot to dict conversion"""
        snapshot = self.monitor.get_current_snapshot()
        snapshot_dict = snapshot.to_dict()
        
        assert isinstance(snapshot_dict, dict)
        assert 'timestamp' in snapshot_dict
        assert 'cpu_percent' in snapshot_dict
        assert 'memory_percent' in snapshot_dict
        assert 'disk_usage_percent' in snapshot_dict


class TestLoadPredictor:
    """Test load prediction functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.predictor = LoadPredictor(window_size=5)
    
    def test_predictor_initialization(self):
        """Test load predictor initialization"""
        assert self.predictor.window_size == 5
        assert len(self.predictor._load_history) == 0
    
    def test_add_sample(self):
        """Test adding load samples"""
        self.predictor.add_sample(50.0)
        assert len(self.predictor._load_history) == 1
        
        # Add more samples
        for i in range(10):
            self.predictor.add_sample(float(i * 10))
        
        # Should only keep window_size samples
        assert len(self.predictor._load_history) == 5
    
    def test_load_prediction(self):
        """Test load prediction with trend"""
        # Add increasing load samples
        for i in range(5):
            self.predictor.add_sample(float(i * 20))  # 0, 20, 40, 60, 80
        
        predicted = self.predictor.predict_load(30)
        assert isinstance(predicted, float)
        assert 0 <= predicted <= 100
    
    def test_prediction_with_insufficient_data(self):
        """Test prediction with insufficient historical data"""
        self.predictor.add_sample(50.0)
        predicted = self.predictor.predict_load(30)
        assert predicted == 50.0  # Should return last value


class TestAdaptiveThrottlingManager:
    """Test adaptive throttling manager functionality"""
    
    def setup_method(self):
        """Setup for each test method"""
        self.thresholds = ThrottlingThresholds(
            min_concurrency=1,
            max_concurrency=10,
            default_concurrency=5
        )
        self.config = AdaptiveThrottlingConfig(
            adjustment_interval=0.1,  # Fast adjustments for tests
            thresholds=self.thresholds,
            enable_predictive_scaling=True
        )
        
        # Mock system monitor and queue manager
        self.mock_monitor = Mock()
        self.mock_queue_manager = Mock()
        
        self.throttling_manager = AdaptiveThrottlingManager(self.config)
        self.throttling_manager._system_monitor = self.mock_monitor
        self.throttling_manager._queue_manager = self.mock_queue_manager
    
    def teardown_method(self):
        """Cleanup after each test method"""
        if self.throttling_manager:
            self.throttling_manager.stop()
    
    def test_throttling_manager_initialization(self):
        """Test throttling manager initialization"""
        assert self.throttling_manager.config.adjustment_interval == 0.1
        assert self.throttling_manager._current_concurrency == 5
        assert self.throttling_manager._target_concurrency == 5
        assert not self.throttling_manager._running
    
    def test_load_level_calculation(self):
        """Test load level calculation"""
        # Mock system snapshot
        snapshot = Mock()
        snapshot.cpu_percent = 50.0
        snapshot.memory_percent = 60.0
        
        # Test normal load
        load_level = self.throttling_manager._calculate_load_level(snapshot, 80.0)
        assert load_level == LoadLevel.NORMAL
        
        # Test high load
        snapshot.cpu_percent = 85.0
        snapshot.memory_percent = 80.0
        load_level = self.throttling_manager._calculate_load_level(snapshot, 40.0)
        assert load_level == LoadLevel.CRITICAL
        
        # Test emergency load
        snapshot.cpu_percent = 98.0
        snapshot.memory_percent = 95.0
        load_level = self.throttling_manager._calculate_load_level(snapshot, 20.0)
        assert load_level == LoadLevel.EMERGENCY
    
    def test_target_concurrency_calculation(self):
        """Test target concurrency calculation"""
        snapshot = Mock()
        snapshot.cpu_percent = 70.0
        snapshot.memory_percent = 75.0
        
        # Test scale down for high load
        target = self.throttling_manager._calculate_target_concurrency(
            snapshot, 60.0, LoadLevel.HIGH, 5, 3
        )
        assert target <= self.throttling_manager._target_concurrency
        
        # Test scale up for low load with queue
        target = self.throttling_manager._calculate_target_concurrency(
            snapshot, 90.0, LoadLevel.LOW, 10, 2
        )
        assert target >= self.throttling_manager._target_concurrency
    
    def test_throttle_action_determination(self):
        """Test throttle action determination"""
        # Scale up
        action = self.throttling_manager._determine_throttle_action(5, 8)
        assert action == ThrottleAction.SCALE_UP
        
        # Scale down
        action = self.throttling_manager._determine_throttle_action(8, 5)
        assert action == ThrottleAction.SCALE_DOWN
        
        # Maintain
        action = self.throttling_manager._determine_throttle_action(5, 5)
        assert action == ThrottleAction.MAINTAIN
        
        # Emergency stop
        action = self.throttling_manager._determine_throttle_action(5, 1)
        assert action == ThrottleAction.EMERGENCY_STOP
    
    def test_smoothing_application(self):
        """Test smoothing of target concurrency changes"""
        # Add some metrics history
        for i in range(5):
            metrics = ThrottlingMetrics(
                timestamp=datetime.now(),
                system_health_score=70.0,
                cpu_usage=50.0,
                memory_usage=60.0,
                active_requests=5,
                queue_size=2,
                current_concurrency=5,
                target_concurrency=5 + i,  # Gradually increasing
                throttle_action=ThrottleAction.SCALE_UP,
                load_level=LoadLevel.NORMAL
            )
            self.throttling_manager._store_metrics(metrics)
        
        smoothed = self.throttling_manager._apply_smoothing(10)
        assert isinstance(smoothed, int)
        assert 1 <= smoothed <= 10
    
    def test_force_adjustment(self):
        """Test forcing an immediate adjustment"""
        original_target = self.throttling_manager._target_concurrency
        
        self.throttling_manager.force_adjustment(8)
        assert self.throttling_manager._target_concurrency == 8
        
        # Test with None (should trigger normal adjustment)
        self.throttling_manager.force_adjustment(None)
        # Target should remain 8 since no new target specified
        assert self.throttling_manager._target_concurrency == 8
    
    def test_concurrency_getters(self):
        """Test concurrency getter methods"""
        assert self.throttling_manager.get_current_concurrency() == 5
        assert self.throttling_manager.get_target_concurrency() == 5
        
        self.throttling_manager._current_concurrency = 7
        self.throttling_manager._target_concurrency = 8
        
        assert self.throttling_manager.get_current_concurrency() == 7
        assert self.throttling_manager.get_target_concurrency() == 8
    
    def test_metrics_storage_and_retrieval(self):
        """Test metrics storage and retrieval"""
        # Initially no metrics
        assert self.throttling_manager.get_latest_metrics() is None
        assert len(self.throttling_manager.get_metrics_history()) == 0
        
        # Add a metric
        metrics = ThrottlingMetrics(
            timestamp=datetime.now(),
            system_health_score=80.0,
            cpu_usage=60.0,
            memory_usage=70.0,
            active_requests=5,
            queue_size=2,
            current_concurrency=5,
            target_concurrency=6,
            throttle_action=ThrottleAction.SCALE_UP,
            load_level=LoadLevel.NORMAL
        )
        self.throttling_manager._store_metrics(metrics)
        
        # Test retrieval
        latest = self.throttling_manager.get_latest_metrics()
        assert latest is not None
        assert latest.system_health_score == 80.0
        
        history = self.throttling_manager.get_metrics_history(1)
        assert len(history) == 1
        assert history[0].system_health_score == 80.0


class TestThrottlingIntegration:
    """Test integration between components"""
    
    def setup_method(self):
        """Setup for integration tests"""
        # Shutdown any existing global instances
        shutdown_system_monitor()
        shutdown_throttling_manager()
    
    def teardown_method(self):
        """Cleanup after integration tests"""
        shutdown_system_monitor()
        shutdown_throttling_manager()
    
    def test_global_initialization(self):
        """Test global initialization functions"""
        # Test system monitor initialization
        monitor = initialize_system_monitor()
        assert monitor is not None
        
        # Test throttling manager initialization
        throttling_manager = initialize_throttling_manager()
        assert throttling_manager is not None
        
        # Test that getting the instances returns the same objects
        assert initialize_system_monitor() is monitor
        assert initialize_throttling_manager() is throttling_manager
    
    @patch('src.swarm_director.utils.adaptive_throttling.get_system_monitor')
    @patch('src.swarm_director.utils.adaptive_throttling.get_request_queue_manager')
    def test_throttling_with_mocked_dependencies(self, mock_queue, mock_monitor):
        """Test throttling manager with mocked dependencies"""
        # Setup mocks
        mock_monitor_instance = Mock()
        mock_queue_instance = Mock()
        
        mock_monitor.return_value = mock_monitor_instance
        mock_queue.return_value = mock_queue_instance
        
        # Configure mock responses
        mock_snapshot = Mock()
        mock_snapshot.cpu_percent = 60.0
        mock_snapshot.memory_percent = 70.0
        
        mock_monitor_instance.get_current_snapshot.return_value = mock_snapshot
        mock_monitor_instance.get_system_health_score.return_value = 75.0
        mock_monitor_instance.is_system_overloaded.return_value = False
        
        mock_queue_instance.get_queue_size.return_value = 5
        mock_queue_instance.get_active_request_count.return_value = 3
        
        # Initialize throttling manager
        config = AdaptiveThrottlingConfig(adjustment_interval=0.1)
        throttling_manager = AdaptiveThrottlingManager(config)
        
        # Test adjustment
        throttling_manager._system_monitor = mock_monitor_instance
        throttling_manager._queue_manager = mock_queue_instance
        
        throttling_manager._perform_adjustment()
        
        # Verify mocks were called
        mock_monitor_instance.get_current_snapshot.assert_called_once()
        mock_monitor_instance.get_system_health_score.assert_called_once()
        mock_queue_instance.get_queue_size.assert_called_once()
        mock_queue_instance.get_active_request_count.assert_called_once()


class TestThrottlingMetrics:
    """Test throttling metrics functionality"""
    
    def test_metrics_creation(self):
        """Test creating throttling metrics"""
        metrics = ThrottlingMetrics(
            timestamp=datetime.now(),
            system_health_score=85.0,
            cpu_usage=65.0,
            memory_usage=70.0,
            active_requests=8,
            queue_size=3,
            current_concurrency=10,
            target_concurrency=12,
            throttle_action=ThrottleAction.SCALE_UP,
            load_level=LoadLevel.NORMAL
        )
        
        assert metrics.system_health_score == 85.0
        assert metrics.throttle_action == ThrottleAction.SCALE_UP
        assert metrics.load_level == LoadLevel.NORMAL
    
    def test_metrics_serialization(self):
        """Test metrics to dict conversion"""
        metrics = ThrottlingMetrics(
            timestamp=datetime.now(),
            system_health_score=85.0,
            cpu_usage=65.0,
            memory_usage=70.0,
            active_requests=8,
            queue_size=3,
            current_concurrency=10,
            target_concurrency=12,
            throttle_action=ThrottleAction.SCALE_UP,
            load_level=LoadLevel.NORMAL
        )
        
        metrics_dict = metrics.to_dict()
        
        assert isinstance(metrics_dict, dict)
        assert 'timestamp' in metrics_dict
        assert 'system_health_score' in metrics_dict
        assert metrics_dict['throttle_action'] == 'scale_up'
        assert metrics_dict['load_level'] == 'normal'


class TestThrottlingConfiguration:
    """Test throttling configuration classes"""
    
    def test_throttling_thresholds_defaults(self):
        """Test default throttling thresholds"""
        thresholds = ThrottlingThresholds()
        
        assert thresholds.low_load_threshold == 30.0
        assert thresholds.normal_load_threshold == 60.0
        assert thresholds.high_load_threshold == 80.0
        assert thresholds.min_concurrency == 1
        assert thresholds.max_concurrency == 50
        assert thresholds.default_concurrency == 10
    
    def test_adaptive_throttling_config_defaults(self):
        """Test default adaptive throttling configuration"""
        config = AdaptiveThrottlingConfig()
        
        assert config.enabled is True
        assert config.adjustment_interval == 5.0
        assert config.enable_predictive_scaling is True
        assert config.enable_emergency_throttling is True
        assert config.smoothing_window == 3
    
    def test_custom_configuration(self):
        """Test custom configuration values"""
        thresholds = ThrottlingThresholds(
            min_concurrency=2,
            max_concurrency=20,
            default_concurrency=8
        )
        
        config = AdaptiveThrottlingConfig(
            enabled=False,
            adjustment_interval=2.0,
            thresholds=thresholds
        )
        
        assert config.enabled is False
        assert config.adjustment_interval == 2.0
        assert config.thresholds.min_concurrency == 2
        assert config.thresholds.max_concurrency == 20


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
