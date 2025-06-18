"""
A/B Testing Service & Optimization Engine
Advanced framework for testing workflow configurations and performance optimization
"""

import uuid
import time
import random
import threading
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Callable, Tuple
from dataclasses import dataclass, field, asdict
from collections import defaultdict, deque
from enum import Enum
import statistics
import logging
import json

from .performance_metrics_service import (
    PerformanceMetricsCollector, MetricType, performance_metrics_service
)

logger = logging.getLogger(__name__)

class ExperimentStatus(Enum):
    """A/B test experiment status"""
    DRAFT = "draft"
    ACTIVE = "active"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"

class ConfigurationType(Enum):
    """Types of configurations that can be tested"""
    AGENT_SETTINGS = "agent_settings"
    WORKFLOW_PARAMETERS = "workflow_parameters"
    RETRY_STRATEGIES = "retry_strategies"
    TIMEOUT_VALUES = "timeout_values"
    RESOURCE_LIMITS = "resource_limits"
    ROUTING_RULES = "routing_rules"

@dataclass
class ExperimentVariant:
    """A/B test variant configuration"""
    variant_id: str
    name: str
    description: str
    configuration: Dict[str, Any]
    traffic_percentage: float
    is_control: bool = False

@dataclass
class ExperimentMetrics:
    """Metrics collected for an experiment variant"""
    variant_id: str
    sample_size: int
    success_rate: float
    average_execution_time: float
    median_execution_time: float
    p95_execution_time: float
    error_rate: float
    resource_efficiency: float
    user_satisfaction_score: float = 0.0

@dataclass
class ExperimentResult:
    """Statistical result of A/B test"""
    experiment_id: str
    winning_variant_id: Optional[str]
    confidence_level: float
    statistical_significance: bool
    improvement_percentage: float
    primary_metric: str
    detailed_metrics: Dict[str, ExperimentMetrics]
    recommendation: str

@dataclass
class ABTestExperiment:
    """A/B test experiment definition"""
    experiment_id: str
    name: str
    description: str
    configuration_type: ConfigurationType
    primary_metric: str  # execution_time, success_rate, resource_usage
    variants: List[ExperimentVariant]
    status: ExperimentStatus
    
    # Experiment settings
    start_date: datetime
    end_date: Optional[datetime]
    min_sample_size: int
    confidence_threshold: float
    
    # Runtime data
    current_metrics: Dict[str, ExperimentMetrics] = field(default_factory=dict)
    participant_assignments: Dict[str, str] = field(default_factory=dict)
    
    # Metadata
    created_by: str = "system"
    tags: List[str] = field(default_factory=list)

@dataclass
class OptimizationRecommendation:
    """Performance optimization recommendation"""
    recommendation_id: str
    category: str  # "performance", "reliability", "cost", "efficiency"
    priority: str  # "critical", "high", "medium", "low"
    title: str
    description: str
    expected_improvement: Dict[str, float]  # metric -> percentage improvement
    implementation_effort: str  # "low", "medium", "high"
    configuration_changes: Dict[str, Any]
    evidence: List[str]  # Supporting evidence from metrics
    timestamp: datetime

class StatisticalAnalyzer:
    """Statistical analysis for A/B test results"""
    
    @staticmethod
    def calculate_statistical_significance(control_metrics: ExperimentMetrics,
                                         variant_metrics: ExperimentMetrics,
                                         metric_name: str,
                                         confidence_level: float = 0.95) -> Tuple[bool, float]:
        """Calculate statistical significance using t-test approximation"""
        
        # Get metric values
        if metric_name == "execution_time":
            control_value = control_metrics.average_execution_time
            variant_value = variant_metrics.average_execution_time
        elif metric_name == "success_rate":
            control_value = control_metrics.success_rate
            variant_value = variant_metrics.success_rate
        elif metric_name == "error_rate":
            control_value = control_metrics.error_rate
            variant_value = variant_metrics.error_rate
        else:
            return False, 0.0
        
        # Simple significance test (in practice, would use proper statistical libraries)
        n1, n2 = control_metrics.sample_size, variant_metrics.sample_size
        
        if n1 < 30 or n2 < 30:
            return False, 0.0  # Need larger sample sizes
        
        # Calculate pooled standard error (simplified)
        pooled_se = ((control_value * (1 - control_value) / n1) + 
                     (variant_value * (1 - variant_value) / n2)) ** 0.5
        
        if pooled_se == 0:
            return False, 0.0
        
        # Calculate z-score
        z_score = abs(variant_value - control_value) / pooled_se
        
        # Critical value for 95% confidence (2-tailed)
        critical_value = 1.96 if confidence_level == 0.95 else 2.58
        
        is_significant = z_score > critical_value
        confidence = min(0.99, z_score / critical_value * confidence_level)
        
        return is_significant, confidence
    
    @staticmethod
    def calculate_improvement_percentage(control_value: float, variant_value: float, 
                                       higher_is_better: bool = True) -> float:
        """Calculate percentage improvement"""
        if control_value == 0:
            return 0.0
        
        if higher_is_better:
            return ((variant_value - control_value) / control_value) * 100
        else:
            return ((control_value - variant_value) / control_value) * 100

class ABTestingService:
    """
    Comprehensive A/B Testing service for workflow configurations
    """
    
    def __init__(self, metrics_service: PerformanceMetricsCollector = None):
        self.metrics_service = metrics_service or performance_metrics_service
        self.experiments = {}
        self.active_experiments = {}
        self.experiment_history = deque(maxlen=1000)
        
        # Traffic routing
        self.traffic_router = {}
        self._lock = threading.RLock()
        
        # Background monitoring
        self._monitoring = True
        self._monitor_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self._monitor_thread.start()
        
        logger.info("A/B Testing Service initialized")
    
    def create_experiment(self, name: str, description: str,
                         configuration_type: ConfigurationType,
                         primary_metric: str,
                         variants: List[Dict[str, Any]],
                         duration_days: int = 7,
                         min_sample_size: int = 100,
                         confidence_threshold: float = 0.95) -> str:
        """Create a new A/B test experiment"""
        
        experiment_id = str(uuid.uuid4())
        
        # Create variants
        experiment_variants = []
        total_traffic = 0
        
        for i, variant_config in enumerate(variants):
            variant_id = f"{experiment_id}_variant_{i}"
            traffic_pct = variant_config.get('traffic_percentage', 100.0 / len(variants))
            
            variant = ExperimentVariant(
                variant_id=variant_id,
                name=variant_config.get('name', f'Variant {i+1}'),
                description=variant_config.get('description', ''),
                configuration=variant_config.get('configuration', {}),
                traffic_percentage=traffic_pct,
                is_control=variant_config.get('is_control', i == 0)
            )
            experiment_variants.append(variant)
            total_traffic += traffic_pct
        
        # Normalize traffic percentages
        if total_traffic != 100.0:
            for variant in experiment_variants:
                variant.traffic_percentage = (variant.traffic_percentage / total_traffic) * 100.0
        
        # Create experiment
        experiment = ABTestExperiment(
            experiment_id=experiment_id,
            name=name,
            description=description,
            configuration_type=configuration_type,
            primary_metric=primary_metric,
            variants=experiment_variants,
            status=ExperimentStatus.DRAFT,
            start_date=datetime.now(),
            end_date=datetime.now() + timedelta(days=duration_days),
            min_sample_size=min_sample_size,
            confidence_threshold=confidence_threshold
        )
        
        with self._lock:
            self.experiments[experiment_id] = experiment
        
        logger.info(f"Created A/B test experiment: {name} ({experiment_id})")
        return experiment_id
    
    def start_experiment(self, experiment_id: str) -> bool:
        """Start an A/B test experiment"""
        with self._lock:
            if experiment_id not in self.experiments:
                logger.error(f"Experiment {experiment_id} not found")
                return False
            
            experiment = self.experiments[experiment_id]
            if experiment.status != ExperimentStatus.DRAFT:
                logger.error(f"Experiment {experiment_id} cannot be started (status: {experiment.status})")
                return False
            
            # Initialize metrics for each variant
            for variant in experiment.variants:
                experiment.current_metrics[variant.variant_id] = ExperimentMetrics(
                    variant_id=variant.variant_id,
                    sample_size=0,
                    success_rate=0.0,
                    average_execution_time=0.0,
                    median_execution_time=0.0,
                    p95_execution_time=0.0,
                    error_rate=0.0,
                    resource_efficiency=0.0
                )
            
            experiment.status = ExperimentStatus.ACTIVE
            self.active_experiments[experiment_id] = experiment
            
            logger.info(f"Started A/B test experiment: {experiment.name}")
            return True
    
    def assign_participant(self, experiment_id: str, participant_id: str) -> Optional[str]:
        """Assign a participant to a variant"""
        with self._lock:
            if experiment_id not in self.active_experiments:
                return None
            
            experiment = self.active_experiments[experiment_id]
            
            # Check if already assigned
            if participant_id in experiment.participant_assignments:
                return experiment.participant_assignments[participant_id]
            
            # Assign based on traffic percentages using consistent hashing
            hash_value = hash(f"{experiment_id}_{participant_id}") % 10000
            cumulative_percentage = 0
            
            for variant in experiment.variants:
                cumulative_percentage += variant.traffic_percentage
                if hash_value < (cumulative_percentage * 100):
                    experiment.participant_assignments[participant_id] = variant.variant_id
                    logger.debug(f"Assigned participant {participant_id} to variant {variant.variant_id}")
                    return variant.variant_id
            
            # Fallback to control
            control_variant = next((v for v in experiment.variants if v.is_control), experiment.variants[0])
            experiment.participant_assignments[participant_id] = control_variant.variant_id
            return control_variant.variant_id
    
    def record_experiment_result(self, experiment_id: str, participant_id: str,
                               execution_time: float, success: bool,
                               metadata: Dict[str, Any] = None):
        """Record a result for an experiment participant"""
        with self._lock:
            if experiment_id not in self.active_experiments:
                return
            
            experiment = self.active_experiments[experiment_id]
            variant_id = experiment.participant_assignments.get(participant_id)
            
            if not variant_id or variant_id not in experiment.current_metrics:
                return
            
            metrics = experiment.current_metrics[variant_id]
            
            # Update sample size
            old_n = metrics.sample_size
            new_n = old_n + 1
            
            # Update running averages
            if old_n == 0:
                metrics.average_execution_time = execution_time
                metrics.success_rate = 1.0 if success else 0.0
                metrics.error_rate = 0.0 if success else 1.0
            else:
                # Running average update
                metrics.average_execution_time = (
                    (metrics.average_execution_time * old_n + execution_time) / new_n
                )
                
                old_success_count = metrics.success_rate * old_n
                new_success_count = old_success_count + (1 if success else 0)
                metrics.success_rate = new_success_count / new_n
                metrics.error_rate = 1.0 - metrics.success_rate
            
            metrics.sample_size = new_n
            
            # TODO: Update percentiles and resource efficiency
            # For now, use approximations
            metrics.median_execution_time = metrics.average_execution_time
            metrics.p95_execution_time = metrics.average_execution_time * 1.5
            metrics.resource_efficiency = metrics.success_rate / max(metrics.average_execution_time, 0.1)
    
    def get_experiment_results(self, experiment_id: str) -> Optional[ExperimentResult]:
        """Get current results for an experiment"""
        with self._lock:
            if experiment_id not in self.experiments:
                return None
            
            experiment = self.experiments[experiment_id]
            
            if not experiment.current_metrics:
                return ExperimentResult(
                    experiment_id=experiment_id,
                    winning_variant_id=None,
                    confidence_level=0.0,
                    statistical_significance=False,
                    improvement_percentage=0.0,
                    primary_metric=experiment.primary_metric,
                    detailed_metrics=experiment.current_metrics,
                    recommendation="Insufficient data for analysis"
                )
            
            # Find control variant
            control_variant = next((v for v in experiment.variants if v.is_control), None)
            if not control_variant:
                control_variant = experiment.variants[0]
            
            control_metrics = experiment.current_metrics.get(control_variant.variant_id)
            if not control_metrics or control_metrics.sample_size < experiment.min_sample_size:
                return ExperimentResult(
                    experiment_id=experiment_id,
                    winning_variant_id=None,
                    confidence_level=0.0,
                    statistical_significance=False,
                    improvement_percentage=0.0,
                    primary_metric=experiment.primary_metric,
                    detailed_metrics=experiment.current_metrics,
                    recommendation="Insufficient sample size for analysis"
                )
            
            # Compare variants to control
            best_variant_id = control_variant.variant_id
            best_improvement = 0.0
            best_confidence = 0.0
            is_significant = False
            
            for variant in experiment.variants:
                if variant.is_control:
                    continue
                
                variant_metrics = experiment.current_metrics.get(variant.variant_id)
                if not variant_metrics or variant_metrics.sample_size < experiment.min_sample_size:
                    continue
                
                # Calculate significance
                significant, confidence = StatisticalAnalyzer.calculate_statistical_significance(
                    control_metrics, variant_metrics, experiment.primary_metric, experiment.confidence_threshold
                )
                
                if significant and confidence > best_confidence:
                    # Calculate improvement
                    if experiment.primary_metric == "execution_time":
                        improvement = StatisticalAnalyzer.calculate_improvement_percentage(
                            control_metrics.average_execution_time,
                            variant_metrics.average_execution_time,
                            higher_is_better=False
                        )
                    else:  # success_rate
                        improvement = StatisticalAnalyzer.calculate_improvement_percentage(
                            control_metrics.success_rate,
                            variant_metrics.success_rate,
                            higher_is_better=True
                        )
                    
                    if improvement > best_improvement:
                        best_variant_id = variant.variant_id
                        best_improvement = improvement
                        best_confidence = confidence
                        is_significant = True
            
            # Generate recommendation
            if is_significant and best_improvement > 0:
                recommendation = f"Variant {best_variant_id} shows {best_improvement:.1f}% improvement with {best_confidence:.1%} confidence. Recommend rollout."
            elif is_significant:
                recommendation = f"No significant improvement found. Continue with control variant."
            else:
                recommendation = f"Results not yet statistically significant. Continue experiment."
            
            return ExperimentResult(
                experiment_id=experiment_id,
                winning_variant_id=best_variant_id if is_significant and best_improvement > 0 else None,
                confidence_level=best_confidence,
                statistical_significance=is_significant,
                improvement_percentage=best_improvement,
                primary_metric=experiment.primary_metric,
                detailed_metrics=experiment.current_metrics,
                recommendation=recommendation
            )
    
    def stop_experiment(self, experiment_id: str) -> bool:
        """Stop an active experiment"""
        with self._lock:
            if experiment_id not in self.active_experiments:
                return False
            
            experiment = self.active_experiments.pop(experiment_id)
            experiment.status = ExperimentStatus.COMPLETED
            experiment.end_date = datetime.now()
            
            # Store in history
            self.experiment_history.append(experiment)
            
            logger.info(f"Stopped experiment: {experiment.name}")
            return True
    
    def get_active_experiments(self) -> List[Dict[str, Any]]:
        """Get list of active experiments"""
        with self._lock:
            return [
                {
                    'experiment_id': exp.experiment_id,
                    'name': exp.name,
                    'status': exp.status.value,
                    'start_date': exp.start_date.isoformat(),
                    'variants_count': len(exp.variants),
                    'total_participants': len(exp.participant_assignments)
                }
                for exp in self.active_experiments.values()
            ]
    
    def _monitoring_loop(self):
        """Background monitoring for experiment completion"""
        while self._monitoring:
            try:
                with self._lock:
                    completed_experiments = []
                    
                    for exp_id, experiment in self.active_experiments.items():
                        # Check if experiment should be stopped
                        if (experiment.end_date and datetime.now() > experiment.end_date):
                            completed_experiments.append(exp_id)
                        
                        # Check for early stopping conditions
                        results = self.get_experiment_results(exp_id)
                        if results and results.statistical_significance and results.confidence_level > 0.95:
                            logger.info(f"Early stopping experiment {exp_id} due to statistical significance")
                            completed_experiments.append(exp_id)
                    
                    # Stop completed experiments
                    for exp_id in completed_experiments:
                        self.stop_experiment(exp_id)
                
                time.sleep(300)  # Check every 5 minutes
                
            except Exception as e:
                logger.error(f"Error in A/B test monitoring loop: {e}")
                time.sleep(60)

class OptimizationEngine:
    """
    Performance optimization recommendation engine
    """
    
    def __init__(self, metrics_service: PerformanceMetricsCollector = None,
                 ab_testing_service: ABTestingService = None):
        self.metrics_service = metrics_service or performance_metrics_service
        self.ab_testing_service = ab_testing_service
        self.recommendations = deque(maxlen=100)
        self.optimization_rules = self._load_optimization_rules()
        
        logger.info("Optimization Engine initialized")
    
    def _load_optimization_rules(self) -> List[Dict[str, Any]]:
        """Load optimization rules and patterns"""
        return [
            {
                'name': 'high_execution_time',
                'condition': lambda metrics: metrics.get('execution_time', {}).get('average', 0) > 30,
                'category': 'performance', 
                'priority': 'high',
                'title': 'Reduce Execution Time',
                'description': 'Workflow execution time is above optimal threshold',
                'recommendations': [
                    'Implement parallel processing for independent tasks',
                    'Optimize database queries and reduce I/O operations',
                    'Consider caching frequently accessed data',
                    'Review and optimize slow code paths'
                ],
                'config_changes': {
                    'parallel_processing': True,
                    'cache_enabled': True,
                    'query_optimization': True
                }
            },
            {
                'name': 'low_success_rate',
                'condition': lambda metrics: metrics.get('success_rate', {}).get('average', 1.0) < 0.9,
                'category': 'reliability',
                'priority': 'critical',
                'title': 'Improve Success Rate',
                'description': 'Workflow success rate is below acceptable threshold',
                'recommendations': [
                    'Implement more robust error handling',
                    'Add retry mechanisms with exponential backoff',
                    'Improve input validation and sanitization',
                    'Add circuit breaker patterns for external dependencies'
                ],
                'config_changes': {
                    'max_retries': 3,
                    'retry_backoff_multiplier': 2.0,
                    'circuit_breaker_enabled': True,
                    'input_validation_strict': True
                }
            },
            {
                'name': 'high_resource_usage',
                'condition': lambda metrics: metrics.get('resource_usage', {}).get('average', 0) > 80,
                'category': 'efficiency',
                'priority': 'medium',
                'title': 'Optimize Resource Usage',
                'description': 'System resource usage is high',
                'recommendations': [
                    'Implement resource pooling and reuse',
                    'Optimize memory usage and garbage collection',
                    'Consider workload distribution across multiple instances',
                    'Profile and optimize CPU-intensive operations'
                ],
                'config_changes': {
                    'resource_pool_size': 20,
                    'memory_optimization': True,
                    'load_balancing': True
                }
            },
            {
                'name': 'degrading_performance_trend',
                'condition': lambda metrics: any(
                    trend.get('direction') == 'degrading' and trend.get('confidence', 0) > 0.7
                    for trend in metrics.get('trends', {}).values()
                ),
                'category': 'performance',
                'priority': 'high', 
                'title': 'Address Performance Degradation',
                'description': 'Performance metrics show degrading trend',
                'recommendations': [
                    'Analyze recent changes for performance impact',
                    'Review system logs for error patterns',
                    'Consider scaling resources if needed',
                    'Implement performance monitoring alerts'
                ],
                'config_changes': {
                    'performance_monitoring_enabled': True,
                    'alert_thresholds_stricter': True,
                    'automatic_scaling': True
                }
            }
        ]
    
    def generate_recommendations(self, time_window: timedelta = None) -> List[OptimizationRecommendation]:
        """Generate optimization recommendations based on current metrics"""
        if time_window is None:
            time_window = timedelta(hours=24)
        
        # Get performance summary
        performance_summary = self.metrics_service.get_performance_summary(time_window)
        
        # Get bottlenecks
        bottlenecks = self.metrics_service.identify_bottlenecks(time_window)
        
        recommendations = []
        
        # Apply optimization rules
        for rule in self.optimization_rules:
            try:
                if rule['condition'](performance_summary):
                    # Calculate expected improvement based on historical data
                    expected_improvement = self._estimate_improvement(rule, performance_summary)
                    
                    recommendation = OptimizationRecommendation(
                        recommendation_id=str(uuid.uuid4()),
                        category=rule['category'],
                        priority=rule['priority'],
                        title=rule['title'],
                        description=rule['description'],
                        expected_improvement=expected_improvement,
                        implementation_effort=rule.get('effort', 'medium'),
                        configuration_changes=rule['config_changes'],
                        evidence=self._gather_evidence(rule, performance_summary, bottlenecks),
                        timestamp=datetime.now()
                    )
                    recommendations.append(recommendation)
                    
            except Exception as e:
                logger.error(f"Error applying optimization rule {rule['name']}: {e}")
        
        # Add bottleneck-specific recommendations
        for bottleneck in bottlenecks:
            if bottleneck['type'] not in [r.title for r in recommendations]:
                recommendation = OptimizationRecommendation(
                    recommendation_id=str(uuid.uuid4()),
                    category='performance',
                    priority=bottleneck['severity'],
                    title=f"Address {bottleneck['type'].replace('_', ' ').title()}",
                    description=bottleneck['description'],
                    expected_improvement={'primary_metric': bottleneck.get('expected_improvement', 15.0)},
                    implementation_effort='medium',
                    configuration_changes={},
                    evidence=[bottleneck['recommendation']],
                    timestamp=datetime.now()
                )
                recommendations.append(recommendation)
        
        # Store recommendations
        self.recommendations.extend(recommendations)
        
        return sorted(recommendations, key=lambda x: self._priority_score(x.priority), reverse=True)
    
    def _estimate_improvement(self, rule: Dict[str, Any], 
                            performance_summary: Dict[str, Any]) -> Dict[str, float]:
        """Estimate expected improvement from applying a rule"""
        improvements = {}
        
        if rule['name'] == 'high_execution_time':
            improvements['execution_time'] = 25.0  # 25% improvement
            improvements['throughput'] = 20.0
        elif rule['name'] == 'low_success_rate':
            improvements['success_rate'] = 15.0
            improvements['error_rate'] = -50.0  # 50% reduction
        elif rule['name'] == 'high_resource_usage':
            improvements['resource_usage'] = -30.0  # 30% reduction
            improvements['cost'] = -20.0
        
        return improvements
    
    def _gather_evidence(self, rule: Dict[str, Any], 
                        performance_summary: Dict[str, Any],
                        bottlenecks: List[Dict[str, Any]]) -> List[str]:
        """Gather supporting evidence for a recommendation"""
        evidence = []
        
        # Add metric-based evidence
        for metric_name, metric_data in performance_summary.get('metrics', {}).items():
            if isinstance(metric_data, dict) and 'average' in metric_data:
                evidence.append(f"{metric_name.replace('_', ' ').title()}: {metric_data['average']:.2f}")
        
        # Add trend evidence
        for metric_name, trend_data in performance_summary.get('trends', {}).items():
            if isinstance(trend_data, dict) and trend_data.get('direction') != 'stable':
                evidence.append(f"{metric_name.replace('_', ' ').title()} trend: {trend_data['direction']}")
        
        # Add bottleneck evidence
        relevant_bottlenecks = [b for b in bottlenecks if rule['name'] in b['type']]
        for bottleneck in relevant_bottlenecks:
            evidence.append(f"Bottleneck detected: {bottleneck['description']}")
        
        return evidence
    
    def _priority_score(self, priority: str) -> int:
        """Convert priority to numeric score"""
        priority_scores = {
            'critical': 4,
            'high': 3, 
            'medium': 2,
            'low': 1
        }
        return priority_scores.get(priority.lower(), 1)
    
    def create_optimization_experiment(self, recommendation: OptimizationRecommendation) -> Optional[str]:
        """Create an A/B test experiment for an optimization recommendation"""
        if not self.ab_testing_service:
            logger.warning("A/B testing service not available for optimization experiments")
            return None
        
        # Create control and treatment variants
        variants = [
            {
                'name': 'Control',
                'description': 'Current configuration',
                'configuration': {},
                'traffic_percentage': 50.0,
                'is_control': True
            },
            {
                'name': 'Optimized',
                'description': f'Optimized configuration: {recommendation.title}',
                'configuration': recommendation.configuration_changes,
                'traffic_percentage': 50.0,
                'is_control': False
            }
        ]
        
        # Determine primary metric based on recommendation category
        primary_metric = 'execution_time' if recommendation.category == 'performance' else 'success_rate'
        
        experiment_id = self.ab_testing_service.create_experiment(
            name=f"Optimization: {recommendation.title}",
            description=f"Testing optimization recommendation: {recommendation.description}",
            configuration_type=ConfigurationType.WORKFLOW_PARAMETERS,
            primary_metric=primary_metric,
            variants=variants,
            duration_days=3,  # Shorter duration for optimization tests
            min_sample_size=50,
            confidence_threshold=0.9
        )
        
        if experiment_id:
            self.ab_testing_service.start_experiment(experiment_id)
            logger.info(f"Created optimization experiment: {experiment_id}")
        
        return experiment_id
    
    def get_optimization_report(self) -> Dict[str, Any]:
        """Generate comprehensive optimization report"""
        recent_recommendations = [
            r for r in self.recommendations 
            if (datetime.now() - r.timestamp) < timedelta(days=7)
        ]
        
        # Group by category and priority
        by_category = defaultdict(list)
        by_priority = defaultdict(list)
        
        for rec in recent_recommendations:
            by_category[rec.category].append(rec)
            by_priority[rec.priority].append(rec)
        
        return {
            'timestamp': datetime.now().isoformat(),
            'total_recommendations': len(recent_recommendations),
            'by_category': {cat: len(recs) for cat, recs in by_category.items()},
            'by_priority': {pri: len(recs) for pri, recs in by_priority.items()},
            'top_recommendations': [
                {
                    'title': rec.title,
                    'category': rec.category,
                    'priority': rec.priority,
                    'expected_improvement': rec.expected_improvement,
                    'implementation_effort': rec.implementation_effort
                }
                for rec in sorted(recent_recommendations, 
                                key=lambda x: self._priority_score(x.priority), reverse=True)[:5]
            ],
            'optimization_score': self._calculate_optimization_score(recent_recommendations)
        }
    
    def _calculate_optimization_score(self, recommendations: List[OptimizationRecommendation]) -> float:
        """Calculate overall optimization score (0-100)"""
        if not recommendations:
            return 100.0  # Perfect if no optimizations needed
        
        # Weight by priority
        total_weight = sum(self._priority_score(r.priority) for r in recommendations)
        max_possible_weight = len(recommendations) * 4  # Max priority score
        
        # Score is inverse of recommendation density
        score = max(0, 100 - (total_weight / max_possible_weight * 100))
        return round(score, 1)

# Global optimization services
ab_testing_service = ABTestingService()
optimization_engine = OptimizationEngine(ab_testing_service=ab_testing_service) 