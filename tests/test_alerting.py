"""
Tests for the alerting system

This module contains comprehensive tests for the alerting engine, notification channels,
and integration with the metrics system.
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from src.swarm_director.utils.alerting import (
    AlertLevel, AlertState, AlertThreshold, Alert, AlertingEngine,
    EmailNotificationChannel, WebhookNotificationChannel, ConsoleNotificationChannel,
    get_alerting_engine, setup_alerting, shutdown_alerting
)


class TestAlertLevel:
    """Test alert level enumeration"""
    
    def test_alert_level_values(self):
        """Test that alert levels have correct values"""
        assert AlertLevel.INFO.value == "info"
        assert AlertLevel.WARNING.value == "warning"
        assert AlertLevel.ERROR.value == "error"
        assert AlertLevel.CRITICAL.value == "critical"


class TestAlertState:
    """Test alert state enumeration"""
    
    def test_alert_state_values(self):
        """Test that alert states have correct values"""
        assert AlertState.ACTIVE.value == "active"
        assert AlertState.RESOLVED.value == "resolved"
        assert AlertState.ACKNOWLEDGED.value == "acknowledged"


class TestAlertThreshold:
    """Test alert threshold configuration"""
    
    def test_alert_threshold_creation(self):
        """Test creating an alert threshold"""
        threshold = AlertThreshold(
            metric_name="cpu_usage",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING,
            cooldown_minutes=5,
            description="High CPU usage"
        )
        
        assert threshold.metric_name == "cpu_usage"
        assert threshold.threshold_value == 80.0
        assert threshold.comparison == "gt"
        assert threshold.level == AlertLevel.WARNING
        assert threshold.cooldown_minutes == 5
        assert threshold.description == "High CPU usage"
    
    def test_alert_threshold_defaults(self):
        """Test alert threshold default values"""
        threshold = AlertThreshold(
            metric_name="test_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.INFO
        )
        
        assert threshold.cooldown_minutes == 5
        assert threshold.description == ""


class TestAlert:
    """Test alert data structure"""
    
    def test_alert_creation(self):
        """Test creating an alert"""
        threshold = AlertThreshold(
            metric_name="cpu_usage",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        alert = Alert(
            id="test_alert_1",
            threshold=threshold,
            current_value=85.0,
            timestamp=datetime.utcnow(),
            state=AlertState.ACTIVE,
            level=AlertLevel.WARNING,
            message="Test alert message"
        )
        
        assert alert.id == "test_alert_1"
        assert alert.threshold == threshold
        assert alert.current_value == 85.0
        assert alert.state == AlertState.ACTIVE
        assert alert.level == AlertLevel.WARNING
        assert alert.message == "Test alert message"
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary"""
        threshold = AlertThreshold(
            metric_name="memory_usage",
            threshold_value=75.0,
            comparison="gt",
            level=AlertLevel.ERROR
        )
        
        timestamp = datetime.utcnow()
        alert = Alert(
            id="test_alert_2",
            threshold=threshold,
            current_value=80.0,
            timestamp=timestamp,
            state=AlertState.ACTIVE,
            level=AlertLevel.ERROR,
            message="Memory alert",
            correlation_id="corr-123"
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict['id'] == "test_alert_2"
        assert alert_dict['current_value'] == 80.0
        assert alert_dict['timestamp'] == timestamp.isoformat()
        assert alert_dict['state'] == "active"
        assert alert_dict['level'] == "error"
        assert alert_dict['message'] == "Memory alert"
        assert alert_dict['correlation_id'] == "corr-123"
        assert alert_dict['threshold']['metric_name'] == "memory_usage"


class TestConsoleNotificationChannel:
    """Test console notification channel"""
    
    def test_console_channel_creation(self):
        """Test creating console notification channel"""
        config = {'enabled': True}
        channel = ConsoleNotificationChannel(config)
        
        assert channel.name == "console"
        assert channel.enabled is True
    
    @pytest.mark.asyncio
    async def test_console_send_success(self):
        """Test successful console notification"""
        config = {'enabled': True}
        channel = ConsoleNotificationChannel(config)
        
        threshold = AlertThreshold(
            metric_name="test_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        alert = Alert(
            id="console_test",
            threshold=threshold,
            current_value=60.0,
            timestamp=datetime.utcnow(),
            state=AlertState.ACTIVE,
            level=AlertLevel.WARNING,
            message="Console test alert"
        )
        
        with patch('src.swarm_director.utils.alerting.logger') as mock_logger:
            result = await channel.send(alert)
            assert result is True
            mock_logger.log.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_console_send_disabled(self):
        """Test console notification when disabled"""
        config = {'enabled': False}
        channel = ConsoleNotificationChannel(config)
        
        threshold = AlertThreshold(
            metric_name="test_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        alert = Alert(
            id="console_test_disabled",
            threshold=threshold,
            current_value=60.0,
            timestamp=datetime.utcnow(),
            state=AlertState.ACTIVE,
            level=AlertLevel.WARNING,
            message="Disabled console test"
        )
        
        result = await channel.send(alert)
        assert result is False


class TestEmailNotificationChannel:
    """Test email notification channel"""
    
    def test_email_channel_creation(self):
        """Test creating email notification channel"""
        config = {
            'enabled': True,
            'smtp_server': 'smtp.test.com',
            'smtp_port': 587,
            'username': 'test@example.com',
            'password': 'password',
            'from_address': 'alerts@test.com',
            'to_addresses': ['user@test.com'],
            'use_tls': True
        }
        
        channel = EmailNotificationChannel(config)
        
        assert channel.name == "email"
        assert channel.enabled is True
        assert channel.smtp_server == 'smtp.test.com'
        assert channel.to_addresses == ['user@test.com']
    
    @pytest.mark.asyncio
    async def test_email_send_no_addresses(self):
        """Test email notification with no addresses"""
        config = {
            'enabled': True,
            'to_addresses': []
        }
        
        channel = EmailNotificationChannel(config)
        
        threshold = AlertThreshold(
            metric_name="test_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        alert = Alert(
            id="email_test",
            threshold=threshold,
            current_value=60.0,
            timestamp=datetime.utcnow(),
            state=AlertState.ACTIVE,
            level=AlertLevel.WARNING,
            message="Email test alert"
        )
        
        result = await channel.send(alert)
        assert result is False


class TestWebhookNotificationChannel:
    """Test webhook notification channel"""
    
    def test_webhook_channel_creation(self):
        """Test creating webhook notification channel"""
        config = {
            'enabled': True,
            'url': 'https://webhook.test.com/alerts',
            'method': 'POST',
            'headers': {'Content-Type': 'application/json'},
            'timeout': 10
        }
        
        channel = WebhookNotificationChannel(config)
        
        assert channel.name == "webhook"
        assert channel.enabled is True
        assert channel.url == 'https://webhook.test.com/alerts'
        assert channel.method == 'POST'
    
    @pytest.mark.asyncio
    async def test_webhook_send_no_url(self):
        """Test webhook notification with no URL"""
        config = {
            'enabled': True,
            'url': ''
        }
        
        channel = WebhookNotificationChannel(config)
        
        threshold = AlertThreshold(
            metric_name="test_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        alert = Alert(
            id="webhook_test",
            threshold=threshold,
            current_value=60.0,
            timestamp=datetime.utcnow(),
            state=AlertState.ACTIVE,
            level=AlertLevel.WARNING,
            message="Webhook test alert"
        )
        
        result = await channel.send(alert)
        assert result is False


class TestAlertingEngine:
    """Test alerting engine functionality"""
    
    def test_alerting_engine_creation(self):
        """Test creating alerting engine with default config"""
        engine = AlertingEngine()
        
        assert engine.config is not None
        assert len(engine.thresholds) > 0
        assert len(engine.notification_channels) > 0
        assert engine.running is False
    
    def test_alerting_engine_custom_config(self):
        """Test creating alerting engine with custom config"""
        config = {
            'check_interval_seconds': 60,
            'max_history_size': 500,
            'thresholds': {
                'custom_metric': {
                    'threshold_value': 100.0,
                    'comparison': 'gt',
                    'level': 'critical',
                    'cooldown_minutes': 10,
                    'description': 'Custom threshold'
                }
            },
            'notifications': {
                'console': {'enabled': True}
            }
        }
        
        engine = AlertingEngine(config)
        
        assert engine.config['check_interval_seconds'] == 60
        assert engine.config['max_history_size'] == 500
        assert 'custom_metric' in engine.thresholds
        assert engine.thresholds['custom_metric'].threshold_value == 100.0
    
    def test_add_threshold(self):
        """Test adding a new threshold"""
        engine = AlertingEngine()
        initial_count = len(engine.thresholds)
        
        threshold = AlertThreshold(
            metric_name="new_metric",
            threshold_value=90.0,
            comparison="gte",
            level=AlertLevel.CRITICAL,
            description="New threshold"
        )
        
        engine.add_threshold(threshold)
        
        assert len(engine.thresholds) == initial_count + 1
        assert "new_metric" in engine.thresholds
        assert engine.thresholds["new_metric"].threshold_value == 90.0
    
    def test_remove_threshold(self):
        """Test removing a threshold"""
        engine = AlertingEngine()
        
        # Add a threshold first
        threshold = AlertThreshold(
            metric_name="temp_metric",
            threshold_value=50.0,
            comparison="gt",
            level=AlertLevel.INFO
        )
        engine.add_threshold(threshold)
        
        # Verify it was added
        assert "temp_metric" in engine.thresholds
        
        # Remove it
        result = engine.remove_threshold("temp_metric")
        
        assert result is True
        assert "temp_metric" not in engine.thresholds
    
    def test_remove_nonexistent_threshold(self):
        """Test removing a threshold that doesn't exist"""
        engine = AlertingEngine()
        result = engine.remove_threshold("nonexistent_metric")
        assert result is False
    
    def test_update_threshold_value(self):
        """Test updating threshold value"""
        engine = AlertingEngine()
        
        # Add a threshold first
        threshold = AlertThreshold(
            metric_name="update_test",
            threshold_value=70.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        engine.add_threshold(threshold)
        
        # Update the value
        result = engine.update_threshold_value("update_test", 85.0)
        
        assert result is True
        assert engine.thresholds["update_test"].threshold_value == 85.0
    
    def test_update_nonexistent_threshold_value(self):
        """Test updating value for non-existent threshold"""
        engine = AlertingEngine()
        result = engine.update_threshold_value("nonexistent", 100.0)
        assert result is False
    
    def test_evaluate_threshold_gt_trigger(self):
        """Test threshold evaluation with greater than trigger"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="gt_test",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING,
            description="GT test"
        )
        
        # Should trigger alert (85 > 80)
        alert = engine._evaluate_threshold(threshold, 85.0)
        
        assert alert is not None
        assert alert.current_value == 85.0
        assert alert.state == AlertState.ACTIVE
        assert alert.level == AlertLevel.WARNING
    
    def test_evaluate_threshold_gt_no_trigger(self):
        """Test threshold evaluation with greater than no trigger"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="gt_no_trigger",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        # Should not trigger alert (75 <= 80)
        alert = engine._evaluate_threshold(threshold, 75.0)
        
        assert alert is None
    
    def test_evaluate_threshold_lt_trigger(self):
        """Test threshold evaluation with less than trigger"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="lt_test",
            threshold_value=20.0,
            comparison="lt",
            level=AlertLevel.ERROR,
            description="LT test"
        )
        
        # Should trigger alert (15 < 20)
        alert = engine._evaluate_threshold(threshold, 15.0)
        
        assert alert is not None
        assert alert.current_value == 15.0
        assert alert.level == AlertLevel.ERROR
    
    def test_evaluate_threshold_eq_trigger(self):
        """Test threshold evaluation with equals trigger"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="eq_test",
            threshold_value=100.0,
            comparison="eq",
            level=AlertLevel.CRITICAL
        )
        
        # Should trigger alert (100 == 100)
        alert = engine._evaluate_threshold(threshold, 100.0)
        
        assert alert is not None
        assert alert.current_value == 100.0
        assert alert.level == AlertLevel.CRITICAL
    
    def test_acknowledge_alert(self):
        """Test acknowledging an alert"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="ack_test",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        # Create an alert
        alert = engine._evaluate_threshold(threshold, 85.0)
        assert alert is not None
        
        # Acknowledge it
        result = engine.acknowledge_alert(alert.id, "test_user")
        
        assert result is True
        assert engine.active_alerts[alert.id].state == AlertState.ACKNOWLEDGED
        assert engine.active_alerts[alert.id].acknowledged_by == "test_user"
    
    def test_acknowledge_nonexistent_alert(self):
        """Test acknowledging non-existent alert"""
        engine = AlertingEngine()
        result = engine.acknowledge_alert("nonexistent", "test_user")
        assert result is False
    
    def test_get_active_alerts(self):
        """Test getting active alerts"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="active_test",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        # Create an alert
        alert = engine._evaluate_threshold(threshold, 85.0)
        assert alert is not None
        
        # Get active alerts
        active_alerts = engine.get_active_alerts()
        
        assert len(active_alerts) == 1
        assert active_alerts[0]['id'] == alert.id
        assert active_alerts[0]['state'] == 'active'
    
    def test_get_alert_history(self):
        """Test getting alert history"""
        engine = AlertingEngine()
        
        threshold = AlertThreshold(
            metric_name="history_test",
            threshold_value=80.0,
            comparison="gt",
            level=AlertLevel.WARNING
        )
        
        # Create and resolve an alert
        alert = engine._evaluate_threshold(threshold, 85.0)
        assert alert is not None
        
        # Resolve the alert by evaluating with value below threshold
        resolved_alert = engine._evaluate_threshold(threshold, 75.0)
        assert resolved_alert is None  # No new alert returned
        
        # Get alert history
        history = engine.get_alert_history()
        
        assert len(history) >= 1
        # The resolved alert should still be in history
        assert any(h['id'] == alert.id for h in history)


class TestAlertingEngineMonitoring:
    """Test alerting engine monitoring functionality"""
    
    def test_start_stop_monitoring(self):
        """Test starting and stopping monitoring"""
        engine = AlertingEngine()
        
        assert engine.running is False
        assert engine.monitor_thread is None
        
        engine.start_monitoring()
        
        assert engine.running is True
        assert engine.monitor_thread is not None
        
        # Give it a moment to start
        time.sleep(0.1)
        
        engine.stop_monitoring()
        
        assert engine.running is False
    
    @patch('src.swarm_director.utils.alerting.metrics_collector')
    def test_check_metrics_with_mock_data(self, mock_metrics_collector):
        """Test checking metrics with mocked data"""
        # Setup mock metrics
        mock_system_metrics = {
            'cpu_usage': Mock(value=85.0),
            'memory_usage': Mock(value=90.0)
        }
        mock_endpoint_stats = {
            'api/test': {
                'request_count': 100,
                'error_count': 6
            }
        }
        
        mock_metrics_collector.collect_system_metrics.return_value = mock_system_metrics
        mock_metrics_collector.get_all_endpoint_stats.return_value = mock_endpoint_stats
        
        engine = AlertingEngine()
        
        # Check metrics
        new_alerts = engine.check_metrics()
        
        # Should have alerts for cpu_usage, memory_usage, and error_rate
        assert len(new_alerts) >= 2  # At least CPU and memory
        
        # Verify CPU alert
        cpu_alert = next((a for a in new_alerts if 'cpu_usage' in a.id), None)
        assert cpu_alert is not None
        assert cpu_alert.current_value == 85.0
        
        # Verify memory alert
        memory_alert = next((a for a in new_alerts if 'memory_usage' in a.id), None)
        assert memory_alert is not None
        assert memory_alert.current_value == 90.0


class TestGlobalFunctions:
    """Test global alerting functions"""
    
    def test_get_alerting_engine(self):
        """Test getting global alerting engine"""
        # Reset global instance
        from src.swarm_director.utils import alerting
        alerting.alerting_engine = None
        
        engine1 = get_alerting_engine()
        engine2 = get_alerting_engine()
        
        assert engine1 is not None
        assert engine1 is engine2  # Should be same instance
    
    def test_setup_alerting(self):
        """Test setup alerting function"""
        config = {
            'check_interval_seconds': 45,
            'thresholds': {
                'test_metric': {
                    'threshold_value': 50.0,
                    'comparison': 'gt',
                    'level': 'warning'
                }
            }
        }
        
        engine = setup_alerting(config)
        
        assert engine is not None
        assert engine.config['check_interval_seconds'] == 45
        assert 'test_metric' in engine.thresholds
        assert engine.running is True
        
        # Cleanup
        engine.stop_monitoring()
    
    def test_shutdown_alerting(self):
        """Test shutdown alerting function"""
        # Setup alerting first
        engine = setup_alerting()
        assert engine.running is True
        
        # Shutdown
        shutdown_alerting()
        
        # Check that global instance is cleared
        from src.swarm_director.utils import alerting
        assert alerting.alerting_engine is None


if __name__ == '__main__':
    pytest.main([__file__])