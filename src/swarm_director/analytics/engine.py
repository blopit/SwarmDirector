"""
Task Analytics Engine for SwarmDirector
Provides comprehensive task performance monitoring, metrics collection, and insights generation
"""

import logging
import statistics
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
from collections import Counter, defaultdict
from dataclasses import dataclass

from ..models.task import Task, TaskStatus, TaskType, TaskPriority
from ..models.analytics import TaskMetrics, TaskAnalyticsInsight, TaskPerformanceSnapshot
from ..models.agent import Agent, AgentStatus
from ..models.base import db


@dataclass
class AnalyticsMetric:
    """Data class for analytics metrics."""
    name: str
    value: float
    timestamp: datetime
    metadata: Dict = None


class TaskAnalyticsEngine:
    """Core analytics engine for task performance monitoring and insights generation"""
    
    def __init__(self, config: Dict = None):
        self.config = config or {}
        self.logger = logging.getLogger(__name__)
        self.metrics_cache = {}
        self.collectors = []
        
        # Default thresholds for insights generation
        self.thresholds = {
            'completion_rate_warning': 0.8,
            'completion_rate_critical': 0.6,
            'failure_rate_warning': 0.15,
            'failure_rate_critical': 0.25,
            'avg_processing_time_warning': 30,  # minutes
            'avg_processing_time_critical': 60,  # minutes
            'queue_time_warning': 15,  # minutes
            'queue_time_critical': 30,  # minutes
        }
        self.thresholds.update(self.config.get('thresholds', {}))
    
    def collect_task_metrics(self, time_range: Tuple[datetime, datetime] = None) -> Dict:
        """Collect comprehensive task metrics for specified time range."""
        if not time_range:
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=30)
            time_range = (start_time, end_time)
            
        start_time, end_time = time_range
        self.logger.info(f"Collecting task metrics for period {start_time} to {end_time}")
        
        metrics = {
            'time_range': {
                'start': start_time.isoformat(),
                'end': end_time.isoformat(),
                'duration_days': (end_time - start_time).days
            },
            'completion_rates': self._calculate_completion_rates(time_range),
            'performance_trends': self._analyze_performance_trends(time_range),
            'bottleneck_analysis': self._identify_bottlenecks(time_range),
            'agent_efficiency': self._measure_agent_efficiency(time_range),
            'task_distribution': self._analyze_task_distribution(time_range),
            'time_analytics': self._calculate_time_analytics(time_range),
            'quality_metrics': self._calculate_quality_metrics(time_range)
        }
        
        return metrics
    
    def _calculate_completion_rates(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Calculate task completion rates and success metrics."""
        start_time, end_time = time_range
        
        # Query tasks within time range
        total_tasks = Task.query.filter(
            Task.created_at.between(start_time, end_time)
        ).count()
        
        completed_tasks = Task.query.filter(
            Task.created_at.between(start_time, end_time),
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        failed_tasks = Task.query.filter(
            Task.created_at.between(start_time, end_time),
            Task.status == TaskStatus.FAILED
        ).count()
        
        cancelled_tasks = Task.query.filter(
            Task.created_at.between(start_time, end_time),
            Task.status == TaskStatus.CANCELLED
        ).count()
        
        in_progress_tasks = Task.query.filter(
            Task.created_at.between(start_time, end_time),
            Task.status.in_([TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
        ).count()
        
        completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
        failure_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
        cancellation_rate = cancelled_tasks / total_tasks if total_tasks > 0 else 0
        
        return {
            'total_tasks': total_tasks,
            'completed_tasks': completed_tasks,
            'failed_tasks': failed_tasks,
            'cancelled_tasks': cancelled_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completion_rate': completion_rate,
            'failure_rate': failure_rate,
            'cancellation_rate': cancellation_rate,
            'success_rate': completion_rate,
            'completed_percentage': round(completion_rate * 100, 2),
            'failed_percentage': round(failure_rate * 100, 2),
        }
    
    def _analyze_performance_trends(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Analyze performance trends over time."""
        start_time, end_time = time_range
        
        # Daily completion trends
        daily_trends = db.session.query(
            db.func.date(Task.completed_at).label('date'),
            db.func.count(Task.id).label('completed_count'),
            db.func.avg(Task.processing_time).label('avg_processing_time'),
            db.func.avg(Task.queue_time).label('avg_queue_time')
        ).filter(
            Task.completed_at.between(start_time, end_time),
            Task.status == TaskStatus.COMPLETED
        ).group_by(db.func.date(Task.completed_at)).all()
        
        trends = []
        for trend in daily_trends:
            trends.append({
                'date': str(trend.date) if trend.date else None,
                'completed_count': trend.completed_count or 0,
                'avg_processing_time': float(trend.avg_processing_time) if trend.avg_processing_time else 0,
                'avg_queue_time': float(trend.avg_queue_time) if trend.avg_queue_time else 0
            })
        
        # Calculate trend direction
        trend_analysis = self._calculate_trend_direction(trends)
        
        return {
            'daily_trends': trends,
            'trend_analysis': trend_analysis,
            'total_trend_days': len(trends)
        }
    
    def _calculate_trend_direction(self, trends: List[Dict]) -> Dict:
        """Calculate trend direction from daily trends data."""
        if len(trends) < 3:
            return {'direction': 'insufficient_data', 'confidence': 0}
        
        # Calculate trend for completion count
        completion_values = [t['completed_count'] for t in trends[-7:]]  # Last 7 days
        processing_times = [t['avg_processing_time'] for t in trends[-7:] if t['avg_processing_time'] > 0]
        
        completion_trend = 'stable'
        processing_trend = 'stable'
        
        if len(completion_values) >= 3:
            if completion_values[-1] > completion_values[0] * 1.1:
                completion_trend = 'improving'
            elif completion_values[-1] < completion_values[0] * 0.9:
                completion_trend = 'declining'
        
        if len(processing_times) >= 3:
            if processing_times[-1] > processing_times[0] * 1.2:
                processing_trend = 'slowing'
            elif processing_times[-1] < processing_times[0] * 0.8:
                processing_trend = 'improving'
        
        # Overall direction
        if completion_trend == 'improving' and processing_trend in ['improving', 'stable']:
            direction = 'improving'
        elif completion_trend == 'declining' or processing_trend == 'slowing':
            direction = 'declining'
        else:
            direction = 'stable'
        
        return {
            'direction': direction,
            'completion_trend': completion_trend,
            'processing_trend': processing_trend,
            'confidence': min(1.0, len(trends) / 7)  # Higher confidence with more data
        }
    
    def _identify_bottlenecks(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Identify bottlenecks in task processing."""
        start_time, end_time = time_range
        
        # Analyze queue times by task type
        queue_analysis = db.session.query(
            Task.type,
            db.func.avg(Task.queue_time).label('avg_queue_time'),
            db.func.max(Task.queue_time).label('max_queue_time'),
            db.func.count(Task.id).label('task_count')
        ).filter(
            Task.created_at.between(start_time, end_time),
            Task.queue_time.isnot(None)
        ).group_by(Task.type).all()
        
        # Analyze processing times by agent
        agent_analysis = db.session.query(
            Task.assigned_agent_id,
            Agent.name,
            db.func.avg(Task.processing_time).label('avg_processing_time'),
            db.func.count(Task.id).label('tasks_handled')
        ).join(Agent, Task.assigned_agent_id == Agent.id, isouter=True)\
        .filter(
            Task.created_at.between(start_time, end_time),
            Task.processing_time.isnot(None)
        ).group_by(Task.assigned_agent_id, Agent.name).all()
        
        # Identify high retry tasks
        retry_analysis = db.session.query(
            Task.type,
            db.func.avg(Task.retry_count).label('avg_retries'),
            db.func.max(Task.retry_count).label('max_retries'),
            db.func.count(Task.id).label('task_count')
        ).filter(
            Task.created_at.between(start_time, end_time),
            Task.retry_count > 0
        ).group_by(Task.type).all()
        
        return {
            'queue_bottlenecks': [
                {
                    'task_type': qa.type.value if qa.type else 'unknown',
                    'avg_queue_time': float(qa.avg_queue_time) if qa.avg_queue_time else 0,
                    'max_queue_time': float(qa.max_queue_time) if qa.max_queue_time else 0,
                    'task_count': qa.task_count,
                    'is_bottleneck': (qa.avg_queue_time or 0) > self.thresholds['queue_time_warning']
                }
                for qa in queue_analysis
            ],
            'agent_bottlenecks': [
                {
                    'agent_id': aa.assigned_agent_id,
                    'agent_name': aa.name or f'Agent {aa.assigned_agent_id}',
                    'avg_processing_time': float(aa.avg_processing_time) if aa.avg_processing_time else 0,
                    'tasks_handled': aa.tasks_handled,
                    'is_bottleneck': (aa.avg_processing_time or 0) > self.thresholds['avg_processing_time_warning']
                }
                for aa in agent_analysis
            ],
            'retry_bottlenecks': [
                {
                    'task_type': ra.type.value if ra.type else 'unknown',
                    'avg_retries': float(ra.avg_retries) if ra.avg_retries else 0,
                    'max_retries': ra.max_retries or 0,
                    'task_count': ra.task_count,
                    'is_problematic': (ra.avg_retries or 0) > 1.0
                }
                for ra in retry_analysis
            ]
        }
    
    def _measure_agent_efficiency(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Measure agent efficiency and utilization."""
        start_time, end_time = time_range
        
        agent_metrics = db.session.query(
            Agent.id,
            Agent.name,
            db.func.count(Task.id).label('total_tasks'),
            db.func.sum(db.case((Task.status == TaskStatus.COMPLETED, 1), else_=0)).label('completed_tasks'),
            db.func.sum(db.case((Task.status == TaskStatus.FAILED, 1), else_=0)).label('failed_tasks'),
            db.func.avg(Task.processing_time).label('avg_processing_time'),
            db.func.avg(Task.quality_score).label('avg_quality_score')
        ).join(Task, Agent.id == Task.assigned_agent_id, isouter=True)\
        .filter(Task.created_at.between(start_time, end_time))\
        .group_by(Agent.id, Agent.name).all()
        
        efficiency_data = []
        for agent in agent_metrics:
            total_tasks = agent.total_tasks or 0
            completed_tasks = agent.completed_tasks or 0
            failed_tasks = agent.failed_tasks or 0
            
            efficiency_score = 0
            if total_tasks > 0:
                completion_rate = completed_tasks / total_tasks
                failure_rate = failed_tasks / total_tasks
                efficiency_score = max(0, completion_rate - failure_rate)
            
            efficiency_data.append({
                'agent_id': agent.id,
                'agent_name': agent.name,
                'total_tasks': total_tasks,
                'completed_tasks': completed_tasks,
                'failed_tasks': failed_tasks,
                'completion_rate': completed_tasks / total_tasks if total_tasks > 0 else 0,
                'failure_rate': failed_tasks / total_tasks if total_tasks > 0 else 0,
                'efficiency_score': efficiency_score,
                'avg_processing_time': float(agent.avg_processing_time) if agent.avg_processing_time else 0,
                'avg_quality_score': float(agent.avg_quality_score) if agent.avg_quality_score else 0
            })
        
        # Calculate overall metrics
        total_efficiency = statistics.mean([a['efficiency_score'] for a in efficiency_data]) if efficiency_data else 0
        best_agent = max(efficiency_data, key=lambda x: x['efficiency_score']) if efficiency_data else None
        worst_agent = min(efficiency_data, key=lambda x: x['efficiency_score']) if efficiency_data else None
        
        return {
            'agent_metrics': efficiency_data,
            'overall_efficiency': total_efficiency,
            'best_performing_agent': best_agent,
            'worst_performing_agent': worst_agent,
            'total_agents': len(efficiency_data)
        }
    
    def _analyze_task_distribution(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Analyze task distribution by type, priority, and status."""
        start_time, end_time = time_range
        
        # Task type distribution
        type_distribution = db.session.query(
            Task.type,
            db.func.count(Task.id).label('count')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).group_by(Task.type).all()
        
        # Priority distribution
        priority_distribution = db.session.query(
            Task.priority,
            db.func.count(Task.id).label('count')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).group_by(Task.priority).all()
        
        # Status distribution
        status_distribution = db.session.query(
            Task.status,
            db.func.count(Task.id).label('count')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).group_by(Task.status).all()
        
        return {
            'task_types': {
                td.type.value if td.type else 'unknown': td.count 
                for td in type_distribution
            },
            'priorities': {
                pd.priority.value if pd.priority else 'unknown': pd.count 
                for pd in priority_distribution
            },
            'statuses': {
                sd.status.value if sd.status else 'unknown': sd.count 
                for sd in status_distribution
            }
        }
    
    def _calculate_time_analytics(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Calculate detailed time analytics."""
        start_time, end_time = time_range
        
        # Get time-related metrics
        time_metrics = db.session.query(
            db.func.avg(Task.queue_time).label('avg_queue_time'),
            db.func.avg(Task.processing_time).label('avg_processing_time'),
            db.func.avg(Task.actual_duration).label('avg_actual_duration'),
            db.func.avg(Task.estimated_duration).label('avg_estimated_duration'),
            db.func.max(Task.queue_time).label('max_queue_time'),
            db.func.max(Task.processing_time).label('max_processing_time')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).first()
        
        # Calculate throughput (tasks completed per hour)
        completed_tasks = Task.query.filter(
            Task.completed_at.between(start_time, end_time),
            Task.status == TaskStatus.COMPLETED
        ).count()
        
        time_span_hours = (end_time - start_time).total_seconds() / 3600
        throughput = completed_tasks / time_span_hours if time_span_hours > 0 else 0
        
        return {
            'avg_queue_time': float(time_metrics.avg_queue_time) if time_metrics.avg_queue_time else 0,
            'avg_processing_time': float(time_metrics.avg_processing_time) if time_metrics.avg_processing_time else 0,
            'avg_actual_duration': float(time_metrics.avg_actual_duration) if time_metrics.avg_actual_duration else 0,
            'avg_estimated_duration': float(time_metrics.avg_estimated_duration) if time_metrics.avg_estimated_duration else 0,
            'max_queue_time': float(time_metrics.max_queue_time) if time_metrics.max_queue_time else 0,
            'max_processing_time': float(time_metrics.max_processing_time) if time_metrics.max_processing_time else 0,
            'throughput_per_hour': throughput,
            'throughput_per_day': throughput * 24,
            'time_span_hours': time_span_hours
        }
    
    def _calculate_quality_metrics(self, time_range: Tuple[datetime, datetime]) -> Dict:
        """Calculate quality-related metrics."""
        start_time, end_time = time_range
        
        quality_metrics = db.session.query(
            db.func.avg(Task.quality_score).label('avg_quality_score'),
            db.func.avg(Task.complexity_score).label('avg_complexity_score'),
            db.func.avg(Task.retry_count).label('avg_retry_count'),
            db.func.count(db.case((Task.retry_count > 0, 1))).label('tasks_with_retries'),
            db.func.count(Task.id).label('total_tasks')
        ).filter(
            Task.created_at.between(start_time, end_time)
        ).first()
        
        retry_rate = 0
        if quality_metrics.total_tasks and quality_metrics.tasks_with_retries:
            retry_rate = quality_metrics.tasks_with_retries / quality_metrics.total_tasks
        
        return {
            'avg_quality_score': float(quality_metrics.avg_quality_score) if quality_metrics.avg_quality_score else 0,
            'avg_complexity_score': float(quality_metrics.avg_complexity_score) if quality_metrics.avg_complexity_score else 0,
            'avg_retry_count': float(quality_metrics.avg_retry_count) if quality_metrics.avg_retry_count else 0,
            'retry_rate': retry_rate,
            'tasks_with_retries': quality_metrics.tasks_with_retries or 0,
            'total_tasks_analyzed': quality_metrics.total_tasks or 0
        }
    
    def generate_insights(self, metrics: Dict) -> List[Dict]:
        """Generate actionable insights from analytics metrics."""
        insights = []
        
        # Completion rate insights
        completion_rates = metrics.get('completion_rates', {})
        completion_rate = completion_rates.get('completion_rate', 0)
        
        if completion_rate < self.thresholds['completion_rate_critical']:
            insights.append({
                'type': 'alert',
                'category': 'completion_rate',
                'priority': 'critical',
                'title': 'Critical: Very Low Task Completion Rate',
                'message': f'Current completion rate is {completion_rate:.1%}, well below acceptable levels',
                'recommendation': 'Immediate investigation required. Review task complexity, agent capacity, and system bottlenecks.',
                'action_items': [
                    'Review failed tasks for common patterns',
                    'Analyze agent workload and availability',
                    'Check system resource utilization',
                    'Consider task complexity reduction',
                    'Implement immediate process improvements'
                ],
                'threshold_violated': self.thresholds['completion_rate_critical'],
                'current_value': completion_rate
            })
        elif completion_rate < self.thresholds['completion_rate_warning']:
            insights.append({
                'type': 'warning',
                'category': 'completion_rate',
                'priority': 'high',
                'title': 'Warning: Low Task Completion Rate',
                'message': f'Current completion rate is {completion_rate:.1%}, below target of {self.thresholds["completion_rate_warning"]:.1%}',
                'recommendation': 'Review task complexity and resource allocation to improve completion rates.',
                'action_items': [
                    'Analyze failed tasks for common patterns',
                    'Review agent workload distribution',
                    'Consider breaking down complex tasks',
                    'Optimize task assignment logic'
                ],
                'threshold_violated': self.thresholds['completion_rate_warning'],
                'current_value': completion_rate
            })
        
        # Performance trend insights
        trends = metrics.get('performance_trends', {}).get('trend_analysis', {})
        if trends.get('direction') == 'declining':
            insights.append({
                'type': 'alert',
                'category': 'performance_trend',
                'priority': 'medium',
                'title': 'Declining Performance Trend Detected',
                'message': 'Task completion performance is trending downward over recent periods',
                'recommendation': 'Investigate recent changes and optimize workflows to reverse the trend.',
                'action_items': [
                    'Review recent system changes',
                    'Analyze resource utilization trends',
                    'Check for new bottlenecks in task processing',
                    'Evaluate agent performance changes',
                    'Consider workflow optimizations'
                ],
                'trend_direction': trends.get('direction'),
                'confidence': trends.get('confidence', 0)
            })
        
        # Bottleneck insights
        bottlenecks = metrics.get('bottleneck_analysis', {})
        
        # Queue bottlenecks
        queue_bottlenecks = [b for b in bottlenecks.get('queue_bottlenecks', []) if b.get('is_bottleneck')]
        if queue_bottlenecks:
            insights.append({
                'type': 'warning',
                'category': 'bottleneck',
                'priority': 'medium',
                'title': 'Queue Time Bottlenecks Detected',
                'message': f'Found {len(queue_bottlenecks)} task types with excessive queue times',
                'recommendation': 'Optimize task scheduling and resource allocation for affected task types.',
                'action_items': [
                    f'Review {", ".join([b["task_type"] for b in queue_bottlenecks])} task processing',
                    'Increase agent capacity for bottlenecked task types',
                    'Optimize task prioritization logic',
                    'Consider load balancing improvements'
                ],
                'affected_task_types': [b['task_type'] for b in queue_bottlenecks],
                'max_queue_time': max([b['avg_queue_time'] for b in queue_bottlenecks])
            })
        
        # Agent efficiency insights
        agent_efficiency = metrics.get('agent_efficiency', {})
        overall_efficiency = agent_efficiency.get('overall_efficiency', 0)
        
        if overall_efficiency < 0.7:  # 70% threshold
            insights.append({
                'type': 'warning',
                'category': 'agent_efficiency',
                'priority': 'medium',
                'title': 'Low Overall Agent Efficiency',
                'message': f'Overall agent efficiency is {overall_efficiency:.1%}, below optimal levels',
                'recommendation': 'Review agent assignments and provide additional training or support.',
                'action_items': [
                    'Analyze individual agent performance',
                    'Provide targeted training for underperforming agents',
                    'Review task assignment algorithms',
                    'Consider workload rebalancing',
                    'Implement performance improvement plans'
                ],
                'current_efficiency': overall_efficiency,
                'target_efficiency': 0.8
            })
        
        return insights
    
    def get_real_time_metrics(self) -> Dict:
        """Get real-time system metrics for live dashboards."""
        now = datetime.utcnow()
        today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
        
        # Current counters
        active_tasks = Task.query.filter(
            Task.status.in_([TaskStatus.PENDING, TaskStatus.ASSIGNED, TaskStatus.IN_PROGRESS])
        ).count()
        
        completed_today = Task.query.filter(
            Task.status == TaskStatus.COMPLETED,
            Task.completed_at >= today_start
        ).count()
        
        failed_today = Task.query.filter(
            Task.status == TaskStatus.FAILED,
            Task.completed_at >= today_start
        ).count()
        
        # Queue depth
        pending_tasks = Task.query.filter(Task.status == TaskStatus.PENDING).count()
        in_progress_tasks = Task.query.filter(Task.status == TaskStatus.IN_PROGRESS).count()
        
        # Agent status
        active_agents = Agent.query.filter(Agent.status == AgentStatus.ACTIVE).count()
        
        return {
            'timestamp': now.isoformat(),
            'active_tasks': active_tasks,
            'pending_tasks': pending_tasks,
            'in_progress_tasks': in_progress_tasks,
            'completed_today': completed_today,
            'failed_today': failed_today,
            'active_agents': active_agents,
            'completion_rate_today': (
                completed_today / (completed_today + failed_today) 
                if (completed_today + failed_today) > 0 else 0
            ),
            'system_load': min(1.0, active_tasks / max(1, active_agents * 5))  # Rough estimate
        }
    
    def create_performance_snapshot(self) -> TaskPerformanceSnapshot:
        """Create a performance snapshot for historical tracking."""
        real_time_metrics = self.get_real_time_metrics()
        
        snapshot = TaskPerformanceSnapshot(
            active_tasks=real_time_metrics['active_tasks'],
            pending_tasks=real_time_metrics['pending_tasks'],
            in_progress_tasks=real_time_metrics['in_progress_tasks'],
            completed_today=real_time_metrics['completed_today'],
            failed_today=real_time_metrics['failed_today'],
            active_agents=real_time_metrics['active_agents'],
            system_load=real_time_metrics['system_load'],
            current_error_rate=1 - real_time_metrics['completion_rate_today'],
            snapshot_metadata=real_time_metrics
        )
        
        snapshot.save()
        return snapshot


def create_analytics_engine(config: Dict = None) -> TaskAnalyticsEngine:
    """Factory function to create a configured TaskAnalyticsEngine instance."""
    return TaskAnalyticsEngine(config) 