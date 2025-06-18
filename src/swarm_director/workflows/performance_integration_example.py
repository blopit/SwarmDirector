"""
Performance Monitoring Integration Example
Demonstrates how to integrate and use the comprehensive performance monitoring system
"""

import time
import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional

from .performance_metrics_service import (
    performance_metrics_service, MetricType
)
from .performance_dashboard import performance_dashboard
from .ab_testing_service import (
    ab_testing_service, optimization_engine, ConfigurationType
)
from .enhanced_email_workflow_coordinator import EnhancedEmailWorkflowCoordinator

class PerformanceIntegratedEmailWorkflow:
    """
    Example integration of performance monitoring with email workflow
    """
    
    def __init__(self):
        self.coordinator = EnhancedEmailWorkflowCoordinator()
        self.metrics_service = performance_metrics_service
        self.dashboard = performance_dashboard
        self.ab_testing = ab_testing_service
        self.optimizer = optimization_engine
        
        # Setup performance monitoring
        self._setup_performance_monitoring()
    
    def _setup_performance_monitoring(self):
        """Setup performance monitoring for the workflow"""
        
        # Subscribe to performance metrics for real-time alerts
        self.metrics_service.registry.subscribe(
            MetricType.EXECUTION_TIME,
            self._on_execution_time_metric
        )
        
        self.metrics_service.registry.subscribe(
            MetricType.SUCCESS_RATE,
            self._on_success_rate_metric
        )
        
        print("✅ Performance monitoring setup complete")
    
    def _on_execution_time_metric(self, metric):
        """Handle execution time metrics"""
        if metric.value > 60:  # Alert if execution takes more than 60 seconds
            print(f"⚠️ Long execution time detected: {metric.value:.2f}s for {metric.tags}")
    
    def _on_success_rate_metric(self, metric):
        """Handle success rate metrics"""
        if metric.value == 0.0:  # Alert on failures
            print(f"❌ Workflow failure detected: {metric.tags}")
    
    async def execute_workflow_with_monitoring(self, workflow_id: str, 
                                              participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute workflow with comprehensive performance monitoring"""
        
        # Start performance timer
        timer_id = f"workflow_{workflow_id}_{int(time.time())}"
        self.metrics_service.start_timer(timer_id, {
            'workflow_id': workflow_id,
            'workflow_type': 'email_workflow',
            'participant_id': participant_data.get('participant_id', 'unknown')
        })
        
        success = False
        result = {}
        
        try:
            # Check if participant is in any A/B test
            experiment_variant = self._check_ab_testing(workflow_id, participant_data)
            
            # Execute workflow with potential A/B test configuration
            start_time = time.time()
            
            if experiment_variant:
                print(f"🧪 Using A/B test variant: {experiment_variant}")
                result = await self._execute_with_variant(workflow_id, participant_data, experiment_variant)
            else:
                print("📧 Using standard workflow configuration")
                result = await self._execute_standard_workflow(workflow_id, participant_data)
            
            execution_time = time.time() - start_time
            success = result.get('success', False)
            
            # Record performance metrics
            self.metrics_service.record_workflow_performance(
                workflow_id=workflow_id,
                agent_name=result.get('agent_name', 'email_agent'),
                phase=result.get('phase', 'complete'),
                execution_time=execution_time,
                success=success,
                metadata={
                    'variant': experiment_variant,
                    'participant_id': participant_data.get('participant_id'),
                    'workflow_type': 'email_workflow'
                }
            )
            
            # Record A/B test result if applicable
            if experiment_variant:
                experiment_id = experiment_variant.split('_')[0]  # Extract experiment ID
                participant_id = participant_data.get('participant_id', 'unknown')
                
                self.ab_testing.record_experiment_result(
                    experiment_id=experiment_id,
                    participant_id=participant_id,
                    execution_time=execution_time,
                    success=success,
                    metadata=result
                )
            
            return result
            
        except Exception as e:
            print(f"❌ Workflow execution failed: {e}")
            success = False
            result = {'success': False, 'error': str(e)}
            return result
            
        finally:
            # Stop performance timer
            final_execution_time = self.metrics_service.stop_timer(timer_id)
            print(f"⏱️ Workflow completed in {final_execution_time:.2f}s (success: {success})")
    
    def _check_ab_testing(self, workflow_id: str, participant_data: Dict[str, Any]) -> Optional[str]:
        """Check if participant should be assigned to an A/B test"""
        participant_id = participant_data.get('participant_id', workflow_id)
        
        # Check all active experiments
        active_experiments = self.ab_testing.get_active_experiments()
        
        for experiment_info in active_experiments:
            experiment_id = experiment_info['experiment_id']
            variant_id = self.ab_testing.assign_participant(experiment_id, participant_id)
            
            if variant_id:
                return variant_id
        
        return None
    
    async def _execute_with_variant(self, workflow_id: str, 
                                   participant_data: Dict[str, Any], 
                                   variant_id: str) -> Dict[str, Any]:
        """Execute workflow with A/B test variant configuration"""
        
        # In a real implementation, you would apply the variant configuration
        # For this example, we'll simulate different execution paths
        
        if 'optimized' in variant_id.lower():
            # Simulate optimized variant (faster execution)
            await asyncio.sleep(0.5)  # Faster execution
            return {
                'success': True,
                'agent_name': 'optimized_email_agent',
                'phase': 'delivery',
                'variant': variant_id,
                'optimization_applied': True,
                'delivery_time': 0.5
            }
        else:
            # Control variant (standard execution)
            await asyncio.sleep(1.0)  # Standard execution time
            return {
                'success': True,
                'agent_name': 'standard_email_agent',
                'phase': 'delivery',
                'variant': variant_id,
                'optimization_applied': False,
                'delivery_time': 1.0
            }
    
    async def _execute_standard_workflow(self, workflow_id: str, 
                                        participant_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute standard workflow without A/B testing"""
        
        # Simulate standard workflow execution
        await asyncio.sleep(0.8)  # Standard execution time
        
        return {
            'success': True,
            'agent_name': 'email_agent',
            'phase': 'delivery',
            'variant': None,
            'optimization_applied': False,
            'delivery_time': 0.8
        }
    
    def generate_performance_report(self) -> Dict[str, Any]:
        """Generate comprehensive performance report"""
        
        # Get performance summary
        performance_summary = self.metrics_service.get_performance_summary(
            timedelta(hours=24)
        )
        
        # Get dashboard data
        dashboard_data = self.dashboard.get_dashboard_data()
        
        # Get optimization recommendations
        recommendations = self.optimizer.generate_recommendations(
            timedelta(hours=24)
        )
        
        # Get optimization report
        optimization_report = self.optimizer.get_optimization_report()
        
        # Get A/B test experiments
        active_experiments = self.ab_testing.get_active_experiments()
        
        # Get bottlenecks
        bottlenecks = self.metrics_service.identify_bottlenecks(
            timedelta(hours=24)
        )
        
        return {
            'timestamp': datetime.now().isoformat(),
            'performance_summary': performance_summary,
            'dashboard_data': {
                'system_status': dashboard_data.get('system_status'),
                'alerts_count': len(dashboard_data.get('alerts', [])),
                'widgets_count': len(dashboard_data.get('widgets', {}))
            },
            'optimization': {
                'recommendations_count': len(recommendations),
                'optimization_score': optimization_report.get('optimization_score'),
                'top_recommendations': optimization_report.get('top_recommendations', [])[:3]
            },
            'ab_testing': {
                'active_experiments': len(active_experiments),
                'experiments': active_experiments
            },
            'bottlenecks': {
                'count': len(bottlenecks),
                'issues': bottlenecks[:5]  # Top 5 bottlenecks
            }
        }
    
    def create_optimization_experiment(self, title: str, description: str) -> Optional[str]:
        """Create a new optimization A/B test experiment"""
        
        variants = [
            {
                'name': 'Control',
                'description': 'Current email workflow configuration',
                'configuration': {
                    'timeout_seconds': 30,
                    'max_retries': 3,
                    'parallel_processing': False
                },
                'traffic_percentage': 50.0,
                'is_control': True
            },
            {
                'name': 'Optimized',
                'description': 'Optimized email workflow configuration',
                'configuration': {
                    'timeout_seconds': 45,
                    'max_retries': 5,
                    'parallel_processing': True,
                    'cache_enabled': True
                },
                'traffic_percentage': 50.0,
                'is_control': False
            }
        ]
        
        experiment_id = self.ab_testing.create_experiment(
            name=title,
            description=description,
            configuration_type=ConfigurationType.WORKFLOW_PARAMETERS,
            primary_metric='execution_time',
            variants=variants,
            duration_days=7,
            min_sample_size=100,
            confidence_threshold=0.95
        )
        
        if experiment_id:
            success = self.ab_testing.start_experiment(experiment_id)
            if success:
                print(f"🧪 Created and started A/B test experiment: {experiment_id}")
                return experiment_id
            else:
                print(f"❌ Failed to start experiment: {experiment_id}")
        
        return None
    
    def get_experiment_results(self, experiment_id: str) -> Optional[Dict[str, Any]]:
        """Get results for an A/B test experiment"""
        results = self.ab_testing.get_experiment_results(experiment_id)
        
        if results:
            return {
                'experiment_id': results.experiment_id,
                'winning_variant': results.winning_variant_id,
                'confidence_level': results.confidence_level,
                'statistical_significance': results.statistical_significance,
                'improvement_percentage': results.improvement_percentage,
                'recommendation': results.recommendation,
                'detailed_metrics': {
                    variant_id: {
                        'sample_size': metrics.sample_size,
                        'success_rate': metrics.success_rate,
                        'avg_execution_time': metrics.average_execution_time
                    }
                    for variant_id, metrics in results.detailed_metrics.items()
                }
            }
        
        return None

# Example usage function
async def run_performance_monitoring_example():
    """Example usage of the performance monitoring system"""
    
    print("🚀 Starting Performance Monitoring Integration Example")
    print("=" * 60)
    
    # Initialize the integrated workflow
    workflow = PerformanceIntegratedEmailWorkflow()
    
    # Create an optimization experiment
    experiment_id = workflow.create_optimization_experiment(
        title="Email Workflow Optimization Test",
        description="Testing optimized configuration for better performance"
    )
    
    # Simulate multiple workflow executions
    print("\n📊 Executing workflows with performance monitoring...")
    
    for i in range(10):
        participant_data = {
            'participant_id': f'user_{i}',
            'email': f'user{i}@example.com',
            'content': f'Test email content for user {i}'
        }
        
        workflow_id = f'email_workflow_{i}'
        
        result = await workflow.execute_workflow_with_monitoring(
            workflow_id, participant_data
        )
        
        print(f"  📧 Workflow {i+1}/10: {result.get('success', False)} "
              f"(variant: {result.get('variant', 'standard')})")
        
        # Small delay between executions
        await asyncio.sleep(0.1)
    
    # Wait for metrics to be processed
    await asyncio.sleep(1)
    
    # Generate performance report
    print("\n📈 Generating Performance Report...")
    report = workflow.generate_performance_report()
    
    print(f"Performance Summary:")
    print(f"  - System Status: {report['dashboard_data']['system_status']['overall_status']}")
    print(f"  - Active Timers: {report['performance_summary']['active_timers']}")
    print(f"  - Total Snapshots: {report['performance_summary']['snapshots_count']}")
    print(f"  - Optimization Score: {report['optimization']['optimization_score']}")
    print(f"  - Active Experiments: {report['ab_testing']['active_experiments']}")
    print(f"  - Bottlenecks Found: {report['bottlenecks']['count']}")
    
    # Show optimization recommendations
    if report['optimization']['top_recommendations']:
        print(f"\n🎯 Top Optimization Recommendations:")
        for i, rec in enumerate(report['optimization']['top_recommendations'], 1):
            print(f"  {i}. {rec['title']} (Priority: {rec['priority']})")
    
    # Show experiment results if available
    if experiment_id:
        print(f"\n🧪 A/B Test Experiment Results:")
        results = workflow.get_experiment_results(experiment_id)
        if results and results['detailed_metrics']:
            print(f"  - Experiment ID: {results['experiment_id']}")
            print(f"  - Statistical Significance: {results['statistical_significance']}")
            print(f"  - Confidence Level: {results['confidence_level']:.1%}")
            print(f"  - Improvement: {results['improvement_percentage']:.1f}%")
            print(f"  - Recommendation: {results['recommendation']}")
    
    print("\n✅ Performance Monitoring Example Complete!")
    print("=" * 60)

if __name__ == "__main__":
    # Run the example
    asyncio.run(run_performance_monitoring_example())