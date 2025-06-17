"""
Error Monitoring and Alerting Service
Comprehensive monitoring, alerting, and reporting for error recovery
"""

import logging
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict, deque
from enum import Enum
import json

from .error_recovery_service import error_recovery_service, ErrorType, ErrorSeverity

logger = logging.getLogger(__name__)

class AlertSeverity(Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"
    EMERGENCY = "emergency"

class AlertChannel(Enum):
    """Alert delivery channels"""
    LOG = "log"
    EMAIL = "email" 
    WEBHOOK = "webhook"
    DATABASE = "database"

@dataclass
class AlertRule:
    """Configuration for alert triggers"""
    name: str
    description: str
    condition: Callable[[Dict[str, Any]], bool]
    severity: AlertSeverity
    channels: List[AlertChannel] = field(default_factory=list)
    cooldown_minutes: int = 15  # Prevent alert spam
    enabled: bool = True
    last_triggered: Optional[datetime] = None

@dataclass
class Alert:
    """Alert instance"""
    alert_id: str
    rule_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime = field(default_factory=datetime.now)
    context: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False

@dataclass
class ErrorPattern:
    """Detected error pattern"""
    pattern_id: str
    error_type: ErrorType
    frequency: int
    time_window: timedelta
    services_affected: List[str]
    first_occurrence: datetime
    last_occurrence: datetime
    impact_level: str

class ErrorMonitoringService:
    """
    Comprehensive error monitoring and alerting service
    """
    
    def __init__(self, monitoring_window_minutes: int = 60):
        self.monitoring_window = timedelta(minutes=monitoring_window_minutes)
        self.error_history = deque(maxlen=10000)  # Sliding window of recent errors
        self.alert_rules = {}
        self.active_alerts = {}
        self.alert_handlers = defaultdict(list)
        self.error_patterns = {}
        
        # Statistics tracking
        self.error_rates = defaultdict(lambda: deque(maxlen=100))
        self.service_health = defaultdict(lambda: {"status": "healthy", "last_check": datetime.now()})
        self.pattern_detection_stats = {"patterns_detected": 0, "false_positives": 0}
        
        # Background monitoring thread
        self._monitoring_active = True
        self._monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitoring_thread.start()
        
        # Setup default alert rules
        self._setup_default_alert_rules()
        
        logger.info("Error Monitoring Service initialized")
    
    def _setup_default_alert_rules(self):
        """Setup default alert rules for common error scenarios"""
        
        # High error rate alert
        self.add_alert_rule(AlertRule(
            name="high_error_rate",
            description="High error rate detected",
            condition=lambda stats: stats.get('error_rate_per_minute', 0) > 10,
            severity=AlertSeverity.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.DATABASE],
            cooldown_minutes=10
        ))
        
        # Circuit breaker activation
        self.add_alert_rule(AlertRule(
            name="circuit_breaker_open",
            description="Circuit breaker opened",
            condition=lambda stats: any(
                cb.get('state') == 'open' 
                for cb in stats.get('circuit_breakers', {}).values()
            ),
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.LOG, AlertChannel.DATABASE],
            cooldown_minutes=5
        ))
        
        # Dead letter queue growing
        self.add_alert_rule(AlertRule(
            name="dead_letter_queue_growing",
            description="Dead letter queue size increasing",
            condition=lambda stats: stats.get('dead_letter_queue_size', 0) > 50,
            severity=AlertSeverity.WARNING,
            channels=[AlertChannel.LOG, AlertChannel.DATABASE],
            cooldown_minutes=30
        ))
        
        # Critical error spike
        self.add_alert_rule(AlertRule(
            name="critical_error_spike",
            description="Critical error spike detected",
            condition=lambda stats: stats.get('critical_error_count', 0) > 5,
            severity=AlertSeverity.EMERGENCY,
            channels=[AlertChannel.LOG, AlertChannel.DATABASE],
            cooldown_minutes=5
        ))
        
        # Service degradation
        self.add_alert_rule(AlertRule(
            name="service_degradation",
            description="Service degradation detected",
            condition=lambda stats: stats.get('success_rate', 100) < 80,
            severity=AlertSeverity.CRITICAL,
            channels=[AlertChannel.LOG, AlertChannel.DATABASE],
            cooldown_minutes=15
        ))
    
    def add_alert_rule(self, rule: AlertRule):
        """Add an alert rule"""
        self.alert_rules[rule.name] = rule
        logger.info(f"Added alert rule: {rule.name}")
    
    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        if rule_name in self.alert_rules:
            del self.alert_rules[rule_name]
            logger.info(f"Removed alert rule: {rule_name}")
    
    def add_alert_handler(self, channel: AlertChannel, handler: Callable[[Alert], None]):
        """Add an alert handler for a specific channel"""
        self.alert_handlers[channel].append(handler)
        logger.info(f"Added alert handler for channel: {channel}")
    
    def record_error_event(self, error_record, context: Dict[str, Any] = None):
        """Record an error event for monitoring"""
        event = {
            'timestamp': datetime.now(),
            'error_id': error_record.error_id,
            'workflow_id': error_record.workflow_id,
            'error_type': error_record.error_type,
            'severity': error_record.severity,
            'message': error_record.message,
            'agent_name': error_record.agent_name,
            'phase': error_record.phase,
            'context': context or {}
        }
        
        self.error_history.append(event)
        
        # Update error rate tracking
        current_minute = datetime.now().replace(second=0, microsecond=0)
        self.error_rates[current_minute].append(event)
        
        # Check for patterns
        self._analyze_error_patterns(event)
    
    def _analyze_error_patterns(self, error_event: Dict[str, Any]):
        """Analyze incoming error for patterns"""
        error_type = error_event['error_type']
        timestamp = error_event['timestamp']
        
        # Look for similar errors in recent history
        recent_errors = [
            e for e in self.error_history 
            if e['error_type'] == error_type and 
               (timestamp - e['timestamp']).total_seconds() < 300  # 5 minutes
        ]
        
        if len(recent_errors) >= 3:  # Pattern threshold
            pattern_id = f"{error_type.value}_{int(timestamp.timestamp())}"
            
            if pattern_id not in self.error_patterns:
                services_affected = list(set(e.get('agent_name', 'unknown') for e in recent_errors))
                
                pattern = ErrorPattern(
                    pattern_id=pattern_id,
                    error_type=error_type,
                    frequency=len(recent_errors),
                    time_window=timedelta(minutes=5),
                    services_affected=services_affected,
                    first_occurrence=recent_errors[0]['timestamp'],
                    last_occurrence=timestamp,
                    impact_level=self._calculate_impact_level(recent_errors)
                )
                
                self.error_patterns[pattern_id] = pattern
                self.pattern_detection_stats["patterns_detected"] += 1
                
                logger.warning(f"Error pattern detected: {pattern_id} - {error_type.value} ({len(recent_errors)} occurrences)")
    
    def _calculate_impact_level(self, error_events: List[Dict[str, Any]]) -> str:
        """Calculate impact level of error pattern"""
        critical_count = len([e for e in error_events if e['severity'] == ErrorSeverity.CRITICAL])
        high_count = len([e for e in error_events if e['severity'] == ErrorSeverity.HIGH])
        
        if critical_count > 0:
            return "critical"
        elif high_count >= 2:
            return "high"
        elif len(error_events) >= 5:
            return "medium"
        else:
            return "low"
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while self._monitoring_active:
            try:
                # Collect current statistics
                stats = self._collect_statistics()
                
                # Check alert rules
                self._check_alert_rules(stats)
                
                # Update service health
                self._update_service_health(stats)
                
                # Cleanup old data
                self._cleanup_old_data()
                
                # Sleep for monitoring interval
                time.sleep(30)  # Check every 30 seconds
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(60)  # Longer sleep on error
    
    def _collect_statistics(self) -> Dict[str, Any]:
        """Collect current error and system statistics"""
        now = datetime.now()
        recent_window = now - self.monitoring_window
        
        # Filter recent errors
        recent_errors = [e for e in self.error_history if e['timestamp'] >= recent_window]
        
        # Calculate error rates
        error_count = len(recent_errors)
        error_rate_per_minute = error_count / self.monitoring_window.total_seconds() * 60
        
        # Error breakdown by type
        errors_by_type = defaultdict(int)
        errors_by_severity = defaultdict(int)
        errors_by_service = defaultdict(int)
        
        for error in recent_errors:
            errors_by_type[error['error_type'].value] += 1
            errors_by_severity[error['severity'].value] += 1
            errors_by_service[error.get('agent_name', 'unknown')] += 1
        
        # Get error recovery statistics
        recovery_stats = error_recovery_service.get_error_statistics()
        
        stats = {
            'timestamp': now,
            'monitoring_window_minutes': self.monitoring_window.total_seconds() / 60,
            'total_errors': error_count,
            'error_rate_per_minute': error_rate_per_minute,
            'errors_by_type': dict(errors_by_type),
            'errors_by_severity': dict(errors_by_severity),
            'errors_by_service': dict(errors_by_service),
            'critical_error_count': errors_by_severity.get('critical', 0),
            'dead_letter_queue_size': recovery_stats.get('dead_letter_queue_size', 0),
            'circuit_breakers': recovery_stats.get('active_circuit_breakers', {}),
            'recovery_actions': recovery_stats.get('recovery_actions', {}),
            'error_patterns': len(self.error_patterns),
            'success_rate': self._calculate_success_rate(recent_errors),
            'service_health': dict(self.service_health)
        }
        
        return stats
    
    def _calculate_success_rate(self, recent_errors: List[Dict[str, Any]]) -> float:
        """Calculate approximate success rate based on error patterns"""
        # This is a simplified calculation - in production you'd track successes too
        if not recent_errors:
            return 100.0
        
        # Estimate based on error rate and typical workflow volume
        estimated_total_operations = max(100, len(recent_errors) * 10)  # Rough estimate
        success_rate = max(0, (1 - len(recent_errors) / estimated_total_operations)) * 100
        return round(success_rate, 2)
    
    def _check_alert_rules(self, stats: Dict[str, Any]):
        """Check all alert rules against current statistics"""
        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue
            
            # Check cooldown
            if rule.last_triggered:
                time_since_last = datetime.now() - rule.last_triggered
                if time_since_last.total_seconds() < rule.cooldown_minutes * 60:
                    continue
            
            # Check condition
            try:
                if rule.condition(stats):
                    self._trigger_alert(rule, stats)
            except Exception as e:
                logger.error(f"Error checking alert rule {rule_name}: {e}")
    
    def _trigger_alert(self, rule: AlertRule, stats: Dict[str, Any]):
        """Trigger an alert"""
        alert_id = f"{rule.name}_{int(time.time())}"
        
        alert = Alert(
            alert_id=alert_id,
            rule_name=rule.name,
            severity=rule.severity,
            message=self._generate_alert_message(rule, stats),
            context=stats
        )
        
        self.active_alerts[alert_id] = alert
        rule.last_triggered = datetime.now()
        
        # Send alert through configured channels
        for channel in rule.channels:
            self._send_alert(alert, channel)
        
        logger.warning(f"Alert triggered: {rule.name} - {alert.message}")
    
    def _generate_alert_message(self, rule: AlertRule, stats: Dict[str, Any]) -> str:
        """Generate alert message with context"""
        base_message = f"ALERT: {rule.description}"
        
        # Add relevant statistics
        context_info = []
        if 'error_rate_per_minute' in stats:
            context_info.append(f"Error rate: {stats['error_rate_per_minute']:.1f}/min")
        if 'critical_error_count' in stats:
            context_info.append(f"Critical errors: {stats['critical_error_count']}")
        if 'dead_letter_queue_size' in stats:
            context_info.append(f"Dead letter queue: {stats['dead_letter_queue_size']}")
        
        if context_info:
            base_message += f" | {' | '.join(context_info)}"
        
        return base_message
    
    def _send_alert(self, alert: Alert, channel: AlertChannel):
        """Send alert through specified channel"""
        try:
            if channel == AlertChannel.LOG:
                log_level = {
                    AlertSeverity.INFO: logging.INFO,
                    AlertSeverity.WARNING: logging.WARNING,
                    AlertSeverity.CRITICAL: logging.ERROR,
                    AlertSeverity.EMERGENCY: logging.CRITICAL
                }.get(alert.severity, logging.WARNING)
                
                logger.log(log_level, f"[{alert.severity.value.upper()}] {alert.message}")
            
            # Execute custom handlers
            for handler in self.alert_handlers[channel]:
                handler(alert)
                
        except Exception as e:
            logger.error(f"Failed to send alert via {channel}: {e}")
    
    def _update_service_health(self, stats: Dict[str, Any]):
        """Update service health status"""
        current_time = datetime.now()
        
        # Update based on recent errors
        for service, error_count in stats.get('errors_by_service', {}).items():
            if error_count > 5:
                self.service_health[service]["status"] = "degraded"
            elif error_count > 10:
                self.service_health[service]["status"] = "unhealthy"
            else:
                self.service_health[service]["status"] = "healthy"
            
            self.service_health[service]["last_check"] = current_time
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_time = datetime.now() - timedelta(hours=24)
        
        # Clean up old error patterns
        old_patterns = [
            pattern_id for pattern_id, pattern in self.error_patterns.items()
            if pattern.last_occurrence < cutoff_time
        ]
        
        for pattern_id in old_patterns:
            del self.error_patterns[pattern_id]
        
        # Clean up resolved alerts older than 1 hour
        alert_cutoff = datetime.now() - timedelta(hours=1)
        old_alerts = [
            alert_id for alert_id, alert in self.active_alerts.items()
            if alert.resolved and alert.timestamp < alert_cutoff
        ]
        
        for alert_id in old_alerts:
            del self.active_alerts[alert_id]
    
    def acknowledge_alert(self, alert_id: str, user: str = "system") -> bool:
        """Acknowledge an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].acknowledged = True
            logger.info(f"Alert {alert_id} acknowledged by {user}")
            return True
        return False
    
    def resolve_alert(self, alert_id: str, user: str = "system") -> bool:
        """Resolve an alert"""
        if alert_id in self.active_alerts:
            self.active_alerts[alert_id].resolved = True
            logger.info(f"Alert {alert_id} resolved by {user}")
            return True
        return False
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        return [alert for alert in self.active_alerts.values() if not alert.resolved]
    
    def get_monitoring_dashboard(self) -> Dict[str, Any]:
        """Get comprehensive monitoring dashboard data"""
        stats = self._collect_statistics()
        
        return {
            'current_statistics': stats,
            'active_alerts': len(self.get_active_alerts()),
            'error_patterns': {
                pattern_id: {
                    'error_type': pattern.error_type.value,
                    'frequency': pattern.frequency,
                    'impact_level': pattern.impact_level,
                    'services_affected': pattern.services_affected,
                    'duration': str(pattern.last_occurrence - pattern.first_occurrence)
                }
                for pattern_id, pattern in self.error_patterns.items()
            },
            'service_health': dict(self.service_health),
            'alert_rules': {
                rule_name: {
                    'description': rule.description,
                    'severity': rule.severity.value,
                    'enabled': rule.enabled,
                    'last_triggered': rule.last_triggered.isoformat() if rule.last_triggered else None
                }
                for rule_name, rule in self.alert_rules.items()
            },
            'pattern_detection_stats': self.pattern_detection_stats
        }
    
    def generate_error_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive error report"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        period_errors = [e for e in self.error_history if e['timestamp'] >= cutoff_time]
        
        # Group errors by various dimensions
        by_type = defaultdict(list)
        by_severity = defaultdict(list)
        by_service = defaultdict(list)
        by_hour = defaultdict(list)
        
        for error in period_errors:
            by_type[error['error_type'].value].append(error)
            by_severity[error['severity'].value].append(error)
            by_service[error.get('agent_name', 'unknown')].append(error)
            hour_key = error['timestamp'].replace(minute=0, second=0, microsecond=0)
            by_hour[hour_key].append(error)
        
        # Calculate trends
        error_trend = []
        for hour_key in sorted(by_hour.keys()):
            error_trend.append({
                'hour': hour_key.isoformat(),
                'count': len(by_hour[hour_key])
            })
        
        return {
            'report_period': f"{hours} hours",
            'total_errors': len(period_errors),
            'error_breakdown': {
                'by_type': {k: len(v) for k, v in by_type.items()},
                'by_severity': {k: len(v) for k, v in by_severity.items()},
                'by_service': {k: len(v) for k, v in by_service.items()}
            },
            'error_trend': error_trend,
            'top_error_messages': self._get_top_error_messages(period_errors),
            'patterns_detected': len([p for p in self.error_patterns.values() 
                                   if p.first_occurrence >= cutoff_time]),
            'recovery_effectiveness': self._calculate_recovery_effectiveness(period_errors),
            'recommendations': self._generate_recommendations(period_errors)
        }
    
    def _get_top_error_messages(self, errors: List[Dict[str, Any]], limit: int = 10) -> List[Dict[str, Any]]:
        """Get most common error messages"""
        message_counts = defaultdict(int)
        message_details = {}
        
        for error in errors:
            message = error['message'][:100]  # Truncate for grouping
            message_counts[message] += 1
            if message not in message_details:
                message_details[message] = {
                    'first_seen': error['timestamp'],
                    'error_type': error['error_type'].value,
                    'services': set()
                }
            message_details[message]['services'].add(error.get('agent_name', 'unknown'))
        
        top_messages = sorted(message_counts.items(), key=lambda x: x[1], reverse=True)[:limit]
        
        return [
            {
                'message': message,
                'count': count,
                'first_seen': message_details[message]['first_seen'].isoformat(),
                'error_type': message_details[message]['error_type'],
                'services_affected': list(message_details[message]['services'])
            }
            for message, count in top_messages
        ]
    
    def _calculate_recovery_effectiveness(self, errors: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate how effective the recovery mechanisms are"""
        recovery_stats = error_recovery_service.get_error_statistics()
        
        total_recovery_attempts = sum(recovery_stats.get('recovery_actions', {}).values())
        retry_attempts = recovery_stats.get('recovery_actions', {}).get('retry', 0)
        
        return {
            'total_recovery_attempts': total_recovery_attempts,
            'retry_success_rate': f"{(retry_attempts / max(total_recovery_attempts, 1)) * 100:.1f}%",
            'circuit_breaker_activations': sum(recovery_stats.get('circuit_breaker_activations', {}).values()),
            'dead_letter_queue_usage': recovery_stats.get('dead_letter_queue_size', 0)
        }
    
    def _generate_recommendations(self, errors: List[Dict[str, Any]]) -> List[str]:
        """Generate recommendations based on error patterns"""
        recommendations = []
        
        # Analyze error types
        error_types = defaultdict(int)
        for error in errors:
            error_types[error['error_type'].value] += 1
        
        # High network errors
        if error_types.get('network', 0) > 10:
            recommendations.append("Consider implementing connection pooling and retry logic for network operations")
        
        # High agent failures
        if error_types.get('agent_failure', 0) > 5:
            recommendations.append("Review AI agent configurations and consider implementing fallback models")
        
        # High SMTP errors
        if error_types.get('smtp_error', 0) > 5:
            recommendations.append("Review SMTP configuration and consider backup email providers")
        
        # High database errors
        if error_types.get('database_error', 0) > 5:
            recommendations.append("Review database connection settings and consider connection pooling")
        
        # General high error rate
        if len(errors) > 100:
            recommendations.append("Overall error rate is high - consider system capacity and resource allocation")
        
        return recommendations
    
    def stop_monitoring(self):
        """Stop the monitoring service"""
        self._monitoring_active = False
        if self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)
        logger.info("Error monitoring service stopped")

# Global error monitoring service instance
error_monitoring_service = ErrorMonitoringService()