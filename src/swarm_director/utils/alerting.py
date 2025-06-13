"""
Alerting System Module

This module provides a comprehensive alerting engine that monitors system metrics,
application performance, and logs to trigger notifications when thresholds are exceeded.

Features:
- Configurable alert thresholds
- Multiple notification channels (email, webhook, console)
- Alert state management (active, resolved, acknowledged)
- Integration with structured logging and metrics systems
"""

import time
import json
import logging
import threading
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
from typing import Dict, List, Optional, Callable, Any
from enum import Enum
import requests

# Optional email imports - gracefully handle if not available
try:
    import smtplib
    from email.mime.text import MimeText
    from email.mime.multipart import MimeMultipart
    EMAIL_AVAILABLE = True
except ImportError:
    EMAIL_AVAILABLE = False

from .logging import get_structured_logger
from .metrics import metrics_collector

logger = get_structured_logger(__name__)


class AlertLevel(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertState(Enum):
    """Alert states"""
    ACTIVE = "active"
    RESOLVED = "resolved"
    ACKNOWLEDGED = "acknowledged"


@dataclass
class AlertThreshold:
    """Configuration for alert thresholds"""
    metric_name: str
    threshold_value: float
    comparison: str  # 'gt', 'lt', 'eq', 'gte', 'lte'
    level: AlertLevel
    cooldown_minutes: int = 5
    description: str = ""


@dataclass
class Alert:
    """Represents an active or historical alert"""
    id: str
    threshold: AlertThreshold
    current_value: float
    timestamp: datetime
    state: AlertState
    level: AlertLevel
    message: str
    correlation_id: Optional[str] = None
    acknowledged_by: Optional[str] = None
    resolved_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert alert to dictionary for serialization"""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['resolved_at'] = self.resolved_at.isoformat() if self.resolved_at else None
        data['level'] = self.level.value
        data['state'] = self.state.value
        data['threshold'] = asdict(self.threshold)
        data['threshold']['level'] = self.threshold.level.value
        return data


class NotificationChannel:
    """Base class for notification channels"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config
        self.enabled = config.get('enabled', True)
    
    async def send(self, alert: Alert) -> bool:
        """Send alert notification"""
        raise NotImplementedError
    
    def format_message(self, alert: Alert) -> str:
        """Format alert message for this channel"""
        return f"""
🚨 ALERT: {alert.level.value.upper()}

Metric: {alert.threshold.metric_name}
Current Value: {alert.current_value}
Threshold: {alert.threshold.threshold_value}
Status: {alert.state.value.upper()}
Time: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}

{alert.message}

Correlation ID: {alert.correlation_id or 'N/A'}
        """.strip()


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("email", config)
        self.smtp_server = config.get('smtp_server', 'localhost')
        self.smtp_port = config.get('smtp_port', 587)
        self.username = config.get('username', '')
        self.password = config.get('password', '')
        self.from_address = config.get('from_address', 'alerts@swarmdirector.local')
        self.to_addresses = config.get('to_addresses', [])
        self.use_tls = config.get('use_tls', True)
    
    async def send(self, alert: Alert) -> bool:
        """Send email notification"""
        if not self.enabled or not self.to_addresses or not EMAIL_AVAILABLE:
            if not EMAIL_AVAILABLE:
                logger.warning("Email notification unavailable - email modules not installed")
            return False
        
        try:
            msg = MimeMultipart()
            msg['From'] = self.from_address
            msg['To'] = ', '.join(self.to_addresses)
            msg['Subject'] = f"[SwarmDirector] {alert.level.value.upper()} Alert: {alert.threshold.metric_name}"
            
            body = self.format_message(alert)
            msg.attach(MimeText(body, 'plain'))
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            
            if self.username and self.password:
                server.login(self.username, self.password)
            
            server.send_message(msg)
            server.quit()
            
            logger.info("Email alert sent successfully", extra={
                'alert_id': alert.id,
                'to_addresses': self.to_addresses
            })
            return True
            
        except Exception as e:
            logger.error("Failed to send email alert", extra={
                'alert_id': alert.id,
                'error': str(e)
            })
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Webhook notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("webhook", config)
        self.url = config.get('url', '')
        self.method = config.get('method', 'POST')
        self.headers = config.get('headers', {'Content-Type': 'application/json'})
        self.timeout = config.get('timeout', 10)
    
    async def send(self, alert: Alert) -> bool:
        """Send webhook notification"""
        if not self.enabled or not self.url:
            return False
        
        try:
            payload = {
                'alert': alert.to_dict(),
                'message': self.format_message(alert),
                'timestamp': datetime.utcnow().isoformat()
            }
            
            response = requests.request(
                method=self.method,
                url=self.url,
                json=payload,
                headers=self.headers,
                timeout=self.timeout
            )
            
            response.raise_for_status()
            
            logger.info("Webhook alert sent successfully", extra={
                'alert_id': alert.id,
                'webhook_url': self.url,
                'status_code': response.status_code
            })
            return True
            
        except Exception as e:
            logger.error("Failed to send webhook alert", extra={
                'alert_id': alert.id,
                'webhook_url': self.url,
                'error': str(e)
            })
            return False


class ConsoleNotificationChannel(NotificationChannel):
    """Console/logging notification channel"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__("console", config)
    
    async def send(self, alert: Alert) -> bool:
        """Log alert to console"""
        if not self.enabled:
            return False
        
        try:
            log_level = {
                AlertLevel.INFO: logging.INFO,
                AlertLevel.WARNING: logging.WARNING,
                AlertLevel.ERROR: logging.ERROR,
                AlertLevel.CRITICAL: logging.CRITICAL
            }.get(alert.level, logging.WARNING)
            
            logger.log(log_level, f"ALERT: {alert.message}", extra={
                'alert_id': alert.id,
                'metric_name': alert.threshold.metric_name,
                'current_value': alert.current_value,
                'threshold_value': alert.threshold.threshold_value,
                'alert_level': alert.level.value,
                'alert_state': alert.state.value
            })
            return True
            
        except Exception as e:
            logger.error("Failed to send console alert", extra={
                'alert_id': alert.id,
                'error': str(e)
            })
            return False


class AlertingEngine:
    """Main alerting engine that monitors metrics and triggers alerts"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or self._get_default_config()
        self.thresholds: Dict[str, AlertThreshold] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self.notification_channels: List[NotificationChannel] = []
        self.lock = threading.Lock()
        self.running = False
        self.monitor_thread: Optional[threading.Thread] = None
        
        self._setup_thresholds()
        self._setup_notification_channels()
        
        logger.info("Alerting engine initialized", extra={
            'threshold_count': len(self.thresholds),
            'channel_count': len(self.notification_channels)
        })
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default alerting configuration"""
        return {
            'check_interval_seconds': 30,
            'max_history_size': 1000,
            'thresholds': {
                'cpu_usage': {
                    'threshold_value': 80.0,
                    'comparison': 'gt',
                    'level': 'warning',
                    'cooldown_minutes': 5,
                    'description': 'High CPU usage detected'
                },
                'memory_usage': {
                    'threshold_value': 85.0,
                    'comparison': 'gt',
                    'level': 'warning',
                    'cooldown_minutes': 5,
                    'description': 'High memory usage detected'
                },
                'disk_usage': {
                    'threshold_value': 90.0,
                    'comparison': 'gt',
                    'level': 'error',
                    'cooldown_minutes': 10,
                    'description': 'Critical disk usage detected'
                },
                'error_rate': {
                    'threshold_value': 5.0,
                    'comparison': 'gt',
                    'level': 'error',
                    'cooldown_minutes': 3,
                    'description': 'High error rate detected'
                }
            },
            'notifications': {
                'console': {
                    'enabled': True
                },
                'email': {
                    'enabled': False,
                    'smtp_server': 'localhost',
                    'smtp_port': 587,
                    'username': '',
                    'password': '',
                    'from_address': 'alerts@swarmdirector.local',
                    'to_addresses': [],
                    'use_tls': True
                },
                'webhook': {
                    'enabled': False,
                    'url': '',
                    'method': 'POST',
                    'headers': {'Content-Type': 'application/json'},
                    'timeout': 10
                }
            }
        }
    
    def _setup_thresholds(self):
        """Setup alert thresholds from configuration"""
        threshold_configs = self.config.get('thresholds', {})
        
        for metric_name, config in threshold_configs.items():
            threshold = AlertThreshold(
                metric_name=metric_name,
                threshold_value=config['threshold_value'],
                comparison=config['comparison'],
                level=AlertLevel(config['level']),
                cooldown_minutes=config.get('cooldown_minutes', 5),
                description=config.get('description', f'Alert for {metric_name}')
            )
            self.thresholds[metric_name] = threshold
    
    def _setup_notification_channels(self):
        """Setup notification channels from configuration"""
        notification_configs = self.config.get('notifications', {})
        
        # Console channel
        if 'console' in notification_configs:
            self.notification_channels.append(
                ConsoleNotificationChannel(notification_configs['console'])
            )
        
        # Email channel
        if 'email' in notification_configs:
            self.notification_channels.append(
                EmailNotificationChannel(notification_configs['email'])
            )
        
        # Webhook channel
        if 'webhook' in notification_configs:
            self.notification_channels.append(
                WebhookNotificationChannel(notification_configs['webhook'])
            )
    
    def add_threshold(self, threshold: AlertThreshold):
        """Add or update an alert threshold"""
        with self.lock:
            self.thresholds[threshold.metric_name] = threshold
            
        logger.info("Alert threshold added/updated", extra={
            'metric_name': threshold.metric_name,
            'threshold_value': threshold.threshold_value,
            'level': threshold.level.value
        })
    
    def remove_threshold(self, metric_name: str) -> bool:
        """Remove an alert threshold"""
        with self.lock:
            if metric_name in self.thresholds:
                del self.thresholds[metric_name]
                logger.info("Alert threshold removed", extra={'metric_name': metric_name})
                return True
            return False
    
    def update_threshold_value(self, metric_name: str, new_value: float) -> bool:
        """Update the threshold value for a specific metric"""
        with self.lock:
            if metric_name in self.thresholds:
                old_value = self.thresholds[metric_name].threshold_value
                self.thresholds[metric_name].threshold_value = new_value
                
                logger.info("Alert threshold value updated", extra={
                    'metric_name': metric_name,
                    'old_value': old_value,
                    'new_value': new_value
                })
                return True
            return False
    
    def check_metrics(self) -> List[Alert]:
        """Check current metrics against thresholds and generate alerts"""
        new_alerts = []
        
        try:
            # Get current system metrics
            system_metrics = metrics_collector.collect_system_metrics()
            
            # Get endpoint metrics summary
            endpoint_stats = metrics_collector.get_all_endpoint_stats()
            
            # Check each threshold
            for metric_name, threshold in self.thresholds.items():
                current_value = None
                
                # Extract metric value based on metric name
                if metric_name in system_metrics:
                    current_value = system_metrics[metric_name].value
                elif metric_name == 'error_rate':
                    # Calculate overall error rate from endpoint stats
                    total_requests = sum(stats.get('request_count', 0) for stats in endpoint_stats.values())
                    total_errors = sum(stats.get('error_count', 0) for stats in endpoint_stats.values())
                    current_value = (total_errors / total_requests * 100) if total_requests > 0 else 0
                
                if current_value is not None:
                    alert = self._evaluate_threshold(threshold, current_value)
                    if alert:
                        new_alerts.append(alert)
        
        except Exception as e:
            logger.error("Error checking metrics for alerts", extra={'error': str(e)})
        
        return new_alerts
    
    def _evaluate_threshold(self, threshold: AlertThreshold, current_value: float) -> Optional[Alert]:
        """Evaluate a single threshold against current value"""
        alert_id = f"{threshold.metric_name}_{threshold.comparison}_{threshold.threshold_value}"
        
        # Check if alert should trigger
        should_alert = False
        
        if threshold.comparison == 'gt':
            should_alert = current_value > threshold.threshold_value
        elif threshold.comparison == 'gte':
            should_alert = current_value >= threshold.threshold_value
        elif threshold.comparison == 'lt':
            should_alert = current_value < threshold.threshold_value
        elif threshold.comparison == 'lte':
            should_alert = current_value <= threshold.threshold_value
        elif threshold.comparison == 'eq':
            should_alert = current_value == threshold.threshold_value
        
        with self.lock:
            existing_alert = self.active_alerts.get(alert_id)
            
            if should_alert and not existing_alert:
                # New alert condition
                alert = Alert(
                    id=alert_id,
                    threshold=threshold,
                    current_value=current_value,
                    timestamp=datetime.utcnow(),
                    state=AlertState.ACTIVE,
                    level=threshold.level,
                    message=f"{threshold.description} - Current: {current_value}, Threshold: {threshold.threshold_value}",
                    correlation_id=getattr(threading.current_thread(), 'correlation_id', None)
                )
                
                self.active_alerts[alert_id] = alert
                self.alert_history.append(alert)
                
                # Trim history if needed
                if len(self.alert_history) > self.config.get('max_history_size', 1000):
                    self.alert_history = self.alert_history[-self.config.get('max_history_size', 1000):]
                
                return alert
                
            elif not should_alert and existing_alert:
                # Alert condition resolved
                existing_alert.state = AlertState.RESOLVED
                existing_alert.resolved_at = datetime.utcnow()
                del self.active_alerts[alert_id]
                
                logger.info("Alert resolved", extra={
                    'alert_id': alert_id,
                    'metric_name': threshold.metric_name,
                    'current_value': current_value
                })
        
        return None
    
    async def send_alert(self, alert: Alert):
        """Send alert through all enabled notification channels"""
        for channel in self.notification_channels:
            if channel.enabled:
                try:
                    success = await channel.send(alert)
                    if success:
                        logger.debug("Alert sent successfully", extra={
                            'alert_id': alert.id,
                            'channel': channel.name
                        })
                    else:
                        logger.warning("Failed to send alert", extra={
                            'alert_id': alert.id,
                            'channel': channel.name
                        })
                except Exception as e:
                    logger.error("Error sending alert", extra={
                        'alert_id': alert.id,
                        'channel': channel.name,
                        'error': str(e)
                    })
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an active alert"""
        with self.lock:
            if alert_id in self.active_alerts:
                self.active_alerts[alert_id].state = AlertState.ACKNOWLEDGED
                self.active_alerts[alert_id].acknowledged_by = acknowledged_by
                
                logger.info("Alert acknowledged", extra={
                    'alert_id': alert_id,
                    'acknowledged_by': acknowledged_by
                })
                return True
            return False
    
    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active alerts"""
        with self.lock:
            return [alert.to_dict() for alert in self.active_alerts.values()]
    
    def get_alert_history(self, limit: int = 100) -> List[Dict[str, Any]]:
        """Get alert history"""
        with self.lock:
            recent_alerts = self.alert_history[-limit:] if self.alert_history else []
            return [alert.to_dict() for alert in reversed(recent_alerts)]
    
    def start_monitoring(self):
        """Start the alert monitoring thread"""
        if self.running:
            return
        
        self.running = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        
        logger.info("Alert monitoring started", extra={
            'check_interval': self.config.get('check_interval_seconds', 30)
        })
    
    def stop_monitoring(self):
        """Stop the alert monitoring thread"""
        self.running = False
        if self.monitor_thread and self.monitor_thread.is_alive():
            self.monitor_thread.join(timeout=5)
        
        logger.info("Alert monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        import asyncio
        
        while self.running:
            try:
                # Check metrics and generate alerts
                new_alerts = self.check_metrics()
                
                # Send notifications for new alerts
                for alert in new_alerts:
                    asyncio.run(self.send_alert(alert))
                
                # Sleep until next check
                time.sleep(self.config.get('check_interval_seconds', 30))
                
            except Exception as e:
                logger.error("Error in alert monitoring loop", extra={'error': str(e)})
                time.sleep(5)  # Short sleep before retry


# Global alerting engine instance
alerting_engine: Optional[AlertingEngine] = None


def get_alerting_engine() -> AlertingEngine:
    """Get or create the global alerting engine instance"""
    global alerting_engine
    if alerting_engine is None:
        alerting_engine = AlertingEngine()
    return alerting_engine


def setup_alerting(config: Optional[Dict[str, Any]] = None):
    """Setup and start the alerting system"""
    global alerting_engine
    alerting_engine = AlertingEngine(config)
    alerting_engine.start_monitoring()
    return alerting_engine


def shutdown_alerting():
    """Shutdown the alerting system"""
    global alerting_engine
    if alerting_engine:
        alerting_engine.stop_monitoring()
        alerting_engine = None