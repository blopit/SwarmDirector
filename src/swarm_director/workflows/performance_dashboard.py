"""
Performance Dashboard
Real-time performance visualization and monitoring dashboard system
"""

import json
import time
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import statistics
import logging

from .performance_metrics_service import (
    PerformanceMetricsCollector, MetricType, PerformanceSnapshot,
    PerformanceTrend, performance_metrics_service
)

logger = logging.getLogger(__name__)

@dataclass
class DashboardMetric:
    """Dashboard metric representation"""
    name: str
    value: float
    unit: str
    trend: str  # "up", "down", "stable"
    change_percentage: float
    status: str  # "good", "warning", "critical"
    timestamp: datetime

@dataclass
class DashboardAlert:
    """Dashboard alert representation"""
    alert_id: str
    metric_name: str
    alert_type: str  # "threshold", "trend", "anomaly"
    severity: str   # "info", "warning", "critical"
    message: str
    timestamp: datetime
    acknowledged: bool = False

@dataclass
class DashboardWidget:
    """Dashboard widget configuration"""
    widget_id: str
    widget_type: str  # "metric", "chart", "table", "gauge"
    title: str
    metric_type: MetricType
    time_window: timedelta
    refresh_interval: int  # seconds
    config: Dict[str, Any]

class PerformanceChart:
    """Performance chart data generator"""
    
    def __init__(self, metrics_service: PerformanceMetricsCollector):
        self.metrics_service = metrics_service
    
    def generate_time_series(self, metric_type: MetricType, 
                           time_window: timedelta, 
                           granularity: timedelta = None) -> List[Dict[str, Any]]:
        """Generate time series data for charts"""
        if granularity is None:
            granularity = time_window / 50  # Default to 50 data points
        
        metrics = self.metrics_service.registry.get_metrics(metric_type, time_window)
        if not metrics:
            return []
        
        # Group metrics by time buckets
        buckets = defaultdict(list)
        start_time = datetime.now() - time_window
        
        for metric in metrics:
            bucket_time = start_time + (
                ((metric.timestamp - start_time) // granularity) * granularity
            )
            buckets[bucket_time].append(metric.value)
        
        # Generate time series points
        time_series = []
        for bucket_time in sorted(buckets.keys()):
            values = buckets[bucket_time]
            time_series.append({
                'timestamp': bucket_time.isoformat(),
                'value': statistics.mean(values),
                'min': min(values),
                'max': max(values),
                'count': len(values)
            })
        
        return time_series
    
    def generate_agent_comparison(self, time_window: timedelta) -> List[Dict[str, Any]]:
        """Generate agent performance comparison data"""
        # Get all snapshots within time window
        cutoff = datetime.now() - time_window
        snapshots = [s for s in self.metrics_service.snapshots if s.timestamp >= cutoff]
        
        # Group by agent
        agent_data = defaultdict(list)
        for snapshot in snapshots:
            if snapshot.agent_name:
                agent_data[snapshot.agent_name].append(snapshot)
        
        # Calculate metrics for each agent
        comparison_data = []
        for agent_name, agent_snapshots in agent_data.items():
            if not agent_snapshots:
                continue
                
            execution_times = [s.execution_time for s in agent_snapshots]
            success_rates = [s.success_rate for s in agent_snapshots]
            
            comparison_data.append({
                'agent_name': agent_name,
                'total_operations': len(agent_snapshots),
                'average_execution_time': statistics.mean(execution_times),
                'median_execution_time': statistics.median(execution_times),
                'average_success_rate': statistics.mean(success_rates),
                'performance_score': self._calculate_performance_score(
                    statistics.mean(execution_times),
                    statistics.mean(success_rates)
                )
            })
        
        return sorted(comparison_data, key=lambda x: x['performance_score'], reverse=True)
    
    def _calculate_performance_score(self, execution_time: float, success_rate: float) -> float:
        """Calculate normalized performance score (0-100)"""
        # Normalize execution time (lower is better, cap at 60 seconds)
        time_score = max(0, (60 - min(execution_time, 60)) / 60) * 50
        
        # Success rate score (higher is better)
        success_score = (success_rate / 100) * 50
        
        return time_score + success_score

class PerformanceDashboard:
    """
    Comprehensive performance monitoring dashboard
    """
    
    def __init__(self, metrics_service: PerformanceMetricsCollector = None):
        self.metrics_service = metrics_service or performance_metrics_service
        self.chart_generator = PerformanceChart(self.metrics_service)
        self.widgets = {}
        self.alerts = []
        self.dashboard_config = {
            'refresh_interval': 5,  # seconds
            'max_alerts': 100,
            'default_time_window': timedelta(hours=1)
        }
        
        # Auto-refresh thread
        self._running = True
        self._refresh_thread = threading.Thread(target=self._refresh_loop, daemon=True)
        self._refresh_thread.start()
        
        # Setup default widgets
        self._setup_default_widgets()
        
        logger.info("Performance Dashboard initialized")
    
    def _setup_default_widgets(self):
        """Setup default dashboard widgets"""
        # System overview metrics
        self.add_widget(DashboardWidget(
            widget_id="system_cpu",
            widget_type="gauge",
            title="CPU Usage",
            metric_type=MetricType.RESOURCE_USAGE,
            time_window=timedelta(minutes=5),
            refresh_interval=5,
            config={'max_value': 100, 'unit': '%', 'filter_tag': 'cpu'}
        ))
        
        self.add_widget(DashboardWidget(
            widget_id="system_memory",
            widget_type="gauge",
            title="Memory Usage",
            metric_type=MetricType.RESOURCE_USAGE,
            time_window=timedelta(minutes=5),
            refresh_interval=5,
            config={'max_value': 100, 'unit': '%', 'filter_tag': 'memory'}
        ))
        
        # Workflow performance
        self.add_widget(DashboardWidget(
            widget_id="execution_time_trend",
            widget_type="chart",
            title="Execution Time Trend",
            metric_type=MetricType.EXECUTION_TIME,
            time_window=timedelta(hours=1),
            refresh_interval=30,
            config={'chart_type': 'line', 'unit': 'seconds'}
        ))
        
        self.add_widget(DashboardWidget(
            widget_id="success_rate_trend",
            widget_type="chart",
            title="Success Rate Trend",
            metric_type=MetricType.SUCCESS_RATE,
            time_window=timedelta(hours=1),
            refresh_interval=30,
            config={'chart_type': 'line', 'unit': '%'}
        ))
        
        # Agent comparison
        self.add_widget(DashboardWidget(
            widget_id="agent_comparison",
            widget_type="table",
            title="Agent Performance Comparison",
            metric_type=MetricType.AGENT_PERFORMANCE,
            time_window=timedelta(hours=1),
            refresh_interval=60,
            config={'sort_by': 'performance_score'}
        ))
    
    def add_widget(self, widget: DashboardWidget):
        """Add a widget to the dashboard"""
        self.widgets[widget.widget_id] = widget
        logger.info(f"Added dashboard widget: {widget.title}")
    
    def remove_widget(self, widget_id: str):
        """Remove a widget from the dashboard"""
        if widget_id in self.widgets:
            del self.widgets[widget_id]
            logger.info(f"Removed dashboard widget: {widget_id}")
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get complete dashboard data"""
        dashboard_data = {
            'timestamp': datetime.now().isoformat(),
            'widgets': {},
            'alerts': [asdict(alert) for alert in self.alerts[-10:]],  # Last 10 alerts
            'system_status': self._get_system_status(),
            'performance_summary': self._get_performance_summary()
        }
        
        # Generate data for each widget
        for widget_id, widget in self.widgets.items():
            try:
                widget_data = self._generate_widget_data(widget)
                dashboard_data['widgets'][widget_id] = widget_data
            except Exception as e:
                logger.error(f"Error generating widget data for {widget_id}: {e}")
                dashboard_data['widgets'][widget_id] = {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
        
        return dashboard_data
    
    def _generate_widget_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate data for a specific widget"""
        base_data = {
            'widget_id': widget.widget_id,
            'title': widget.title,
            'type': widget.widget_type,
            'timestamp': datetime.now().isoformat(),
            'time_window': str(widget.time_window)
        }
        
        if widget.widget_type == "gauge":
            return {**base_data, **self._generate_gauge_data(widget)}
        elif widget.widget_type == "chart":
            return {**base_data, **self._generate_chart_data(widget)}
        elif widget.widget_type == "table":
            return {**base_data, **self._generate_table_data(widget)}
        elif widget.widget_type == "metric":
            return {**base_data, **self._generate_metric_data(widget)}
        else:
            return base_data
    
    def _generate_gauge_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate gauge widget data"""
        metrics = self.metrics_service.registry.get_metrics(
            widget.metric_type, widget.time_window
        )
        
        # Filter by tag if specified
        filter_tag = widget.config.get('filter_tag')
        if filter_tag:
            metrics = [m for m in metrics if filter_tag in m.tags.get('resource', '')]
        
        if not metrics:
            return {
                'value': 0,
                'status': 'no_data',
                'unit': widget.config.get('unit', ''),
                'max_value': widget.config.get('max_value', 100)
            }
        
        # Get latest value
        latest_value = metrics[-1].value
        max_value = widget.config.get('max_value', 100)
        
        # Determine status
        if latest_value > max_value * 0.9:
            status = 'critical'
        elif latest_value > max_value * 0.7:
            status = 'warning'
        else:
            status = 'good'
        
        return {
            'value': latest_value,
            'status': status,
            'unit': widget.config.get('unit', ''),
            'max_value': max_value,
            'average': statistics.mean([m.value for m in metrics]),
            'trend': self._calculate_trend_direction(metrics)
        }
    
    def _generate_chart_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate chart widget data"""
        time_series = self.chart_generator.generate_time_series(
            widget.metric_type, widget.time_window
        )
        
        return {
            'chart_type': widget.config.get('chart_type', 'line'),
            'unit': widget.config.get('unit', ''),
            'data': time_series,
            'data_points': len(time_series)
        }
    
    def _generate_table_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate table widget data"""
        if widget.metric_type == MetricType.AGENT_PERFORMANCE:
            data = self.chart_generator.generate_agent_comparison(widget.time_window)
            sort_by = widget.config.get('sort_by', 'performance_score')
            
            return {
                'headers': [
                    'Agent Name', 'Operations', 'Avg Execution Time', 
                    'Success Rate', 'Performance Score'
                ],
                'rows': data,
                'sort_by': sort_by
            }
        else:
            # Generic table for other metrics
            metrics = self.metrics_service.registry.get_metrics(
                widget.metric_type, widget.time_window
            )
            
            return {
                'headers': ['Timestamp', 'Value', 'Tags'],
                'rows': [
                    {
                        'timestamp': m.timestamp.isoformat(),
                        'value': m.value,
                        'tags': json.dumps(m.tags)
                    }
                    for m in metrics[-20:]  # Last 20 metrics
                ]
            }
    
    def _generate_metric_data(self, widget: DashboardWidget) -> Dict[str, Any]:
        """Generate metric widget data"""
        metrics = self.metrics_service.registry.get_metrics(
            widget.metric_type, widget.time_window
        )
        
        if not metrics:
            return {
                'value': 0,
                'unit': widget.config.get('unit', ''),
                'status': 'no_data'
            }
        
        values = [m.value for m in metrics]
        current_value = values[-1]
        
        return {
            'value': current_value,
            'unit': widget.config.get('unit', ''),
            'average': statistics.mean(values),
            'trend': self._calculate_trend_direction(metrics),
            'status': 'good'  # TODO: Implement status logic
        }
    
    def _calculate_trend_direction(self, metrics: List) -> str:
        """Calculate trend direction from metrics"""
        if len(metrics) < 2:
            return 'stable'
        
        values = [m.value for m in metrics]
        recent_avg = statistics.mean(values[-10:]) if len(values) >= 10 else values[-1]
        older_avg = statistics.mean(values[:-10]) if len(values) >= 20 else values[0]
        
        if recent_avg > older_avg * 1.05:
            return 'up'
        elif recent_avg < older_avg * 0.95:
            return 'down'
        else:
            return 'stable'
    
    def _get_system_status(self) -> Dict[str, Any]:
        """Get overall system status"""
        # Get recent metrics
        recent_window = timedelta(minutes=5)
        
        # CPU usage
        cpu_metrics = self.metrics_service.registry.get_metrics(
            MetricType.RESOURCE_USAGE, recent_window
        )
        cpu_metrics = [m for m in cpu_metrics if m.tags.get('resource') == 'cpu']
        
        # Success rate
        success_metrics = self.metrics_service.registry.get_metrics(
            MetricType.SUCCESS_RATE, recent_window
        )
        
        # Determine overall status
        overall_status = 'good'
        
        if cpu_metrics:
            avg_cpu = statistics.mean([m.value for m in cpu_metrics])
            if avg_cpu > 90:
                overall_status = 'critical'
            elif avg_cpu > 80:
                overall_status = 'warning'
        
        if success_metrics:
            avg_success = statistics.mean([m.value for m in success_metrics])
            if avg_success < 0.8:
                overall_status = 'critical'
            elif avg_success < 0.9:
                overall_status = 'warning'
        
        return {
            'overall_status': overall_status,
            'cpu_usage': statistics.mean([m.value for m in cpu_metrics]) if cpu_metrics else 0,
            'success_rate': statistics.mean([m.value for m in success_metrics]) * 100 if success_metrics else 100,
            'active_timers': len(self.metrics_service.active_timers),
            'total_snapshots': len(self.metrics_service.snapshots)
        }
    
    def _get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary for the dashboard"""
        return self.metrics_service.get_performance_summary(
            self.dashboard_config['default_time_window']
        )
    
    def add_alert(self, alert: DashboardAlert):
        """Add an alert to the dashboard"""
        self.alerts.append(alert)
        
        # Keep only the most recent alerts
        if len(self.alerts) > self.dashboard_config['max_alerts']:
            self.alerts = self.alerts[-self.dashboard_config['max_alerts']:]
        
        logger.info(f"Dashboard alert added: {alert.message}")
    
    def acknowledge_alert(self, alert_id: str):
        """Acknowledge an alert"""
        for alert in self.alerts:
            if alert.alert_id == alert_id:
                alert.acknowledged = True
                logger.info(f"Alert acknowledged: {alert_id}")
                break
    
    def get_real_time_metrics(self) -> Dict[str, Any]:
        """Get real-time metrics for live dashboard updates"""
        return {
            'timestamp': datetime.now().isoformat(),
            'cpu_usage': self._get_latest_metric_value(MetricType.RESOURCE_USAGE, 'cpu'),
            'memory_usage': self._get_latest_metric_value(MetricType.RESOURCE_USAGE, 'memory'),
            'active_operations': len(self.metrics_service.active_timers),
            'recent_errors': self._count_recent_errors(),
            'throughput': self._calculate_current_throughput()
        }
    
    def _get_latest_metric_value(self, metric_type: MetricType, resource_tag: str) -> float:
        """Get the latest value for a specific metric"""
        metrics = self.metrics_service.registry.get_metrics(
            metric_type, timedelta(minutes=1)
        )
        
        filtered_metrics = [
            m for m in metrics 
            if m.tags.get('resource') == resource_tag
        ]
        
        return filtered_metrics[-1].value if filtered_metrics else 0.0
    
    def _count_recent_errors(self) -> int:
        """Count recent errors (failed operations)"""
        success_metrics = self.metrics_service.registry.get_metrics(
            MetricType.SUCCESS_RATE, timedelta(minutes=5)
        )
        
        return len([m for m in success_metrics if m.value == 0.0])
    
    def _calculate_current_throughput(self) -> float:
        """Calculate current throughput (operations per minute)"""
        execution_metrics = self.metrics_service.registry.get_metrics(
            MetricType.EXECUTION_TIME, timedelta(minutes=1)
        )
        
        return len(execution_metrics)
    
    def _refresh_loop(self):
        """Background refresh loop for dashboard updates"""
        while self._running:
            try:
                # Check for performance issues and generate alerts
                bottlenecks = self.metrics_service.identify_bottlenecks()
                
                for bottleneck in bottlenecks:
                    alert = DashboardAlert(
                        alert_id=f"bottleneck_{int(time.time())}",
                        metric_name=bottleneck['type'],
                        alert_type="bottleneck",
                        severity=bottleneck['severity'],
                        message=bottleneck['description'],
                        timestamp=datetime.now()
                    )
                    self.add_alert(alert)
                
                time.sleep(self.dashboard_config['refresh_interval'])
                
            except Exception as e:
                logger.error(f"Error in dashboard refresh loop: {e}")
                time.sleep(10)
    
    def export_dashboard_config(self) -> Dict[str, Any]:
        """Export dashboard configuration"""
        return {
            'widgets': {
                widget_id: {
                    'widget_type': widget.widget_type,
                    'title': widget.title,
                    'metric_type': widget.metric_type.value,
                    'time_window': str(widget.time_window),
                    'refresh_interval': widget.refresh_interval,
                    'config': widget.config
                }
                for widget_id, widget in self.widgets.items()
            },
            'dashboard_config': self.dashboard_config
        }
    
    def import_dashboard_config(self, config: Dict[str, Any]):
        """Import dashboard configuration"""
        self.dashboard_config.update(config.get('dashboard_config', {}))
        
        # Clear existing widgets
        self.widgets.clear()
        
        # Import widgets
        for widget_id, widget_config in config.get('widgets', {}).items():
            widget = DashboardWidget(
                widget_id=widget_id,
                widget_type=widget_config['widget_type'],
                title=widget_config['title'],
                metric_type=MetricType(widget_config['metric_type']),
                time_window=timedelta(seconds=int(widget_config['time_window'].split(':')[-1])),
                refresh_interval=widget_config['refresh_interval'],
                config=widget_config['config']
            )
            self.add_widget(widget)
    
    def stop_dashboard(self):
        """Stop the dashboard"""
        self._running = False
        if self._refresh_thread.is_alive():
            self._refresh_thread.join(timeout=5)
        logger.info("Performance dashboard stopped")

# Global performance dashboard instance
performance_dashboard = PerformanceDashboard()