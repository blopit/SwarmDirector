"""
Workflow management module
Provides orchestration, state management, and context management for SwarmDirector workflows
"""

from .workflow_context import WorkflowContext, ContextScope
from .state_manager import WorkflowStateManager, WorkflowStatus, WorkflowState, StateTransition
from .orchestrator import WorkflowOrchestrator, ExecutionStrategy, WorkflowExecutionResult

# Email workflow state management
from .email_workflow_states import (
    EmailWorkflowStateManager, EmailWorkflowState, EmailWorkflowType, 
    EmailWorkflowPhase, EmailContext, ReviewContext, EmailDeliveryStatus
)

# Persistent state management
from .persistent_state_manager import PersistentEmailWorkflowStateManager

# Global context access
from .global_context import (
    GlobalWorkflowContext, global_context,
    get_current_workflow, get_workflow, get_context_value, set_context_value,
    update_workflow_context, advance_workflow_phase,
    with_workflow_context, requires_workflow_context, auto_advance_phase,
    get_workflow_logger, WorkflowUtils, workflow_utils
)

# Email workflow coordination
from .email_workflow_coordinator import EmailWorkflowCoordinator

# Error recovery system
from .error_recovery_service import (
    error_recovery_service, ErrorRecoveryService, ErrorType, ErrorSeverity, 
    RecoveryAction, RetryStrategy, CircuitBreakerConfig, CircuitBreakerState,
    ErrorRecord, RecoveryResult, CircuitBreaker, DeadLetterQueue
)

# Enhanced coordinator with error recovery
from .enhanced_email_workflow_coordinator import EnhancedEmailWorkflowCoordinator

# Error monitoring and alerting
from .error_monitoring_service import (
    error_monitoring_service, ErrorMonitoringService, AlertSeverity, AlertChannel,
    AlertRule, Alert, ErrorPattern
)

# Performance Monitoring System (Task 9.4)
from .performance_metrics_service import (
    PerformanceMetricsCollector, MetricType, PerformanceSnapshot, 
    PerformanceTrend, PerformanceThreshold, MetricsRegistry,
    performance_metrics_service
)
from .performance_dashboard import (
    PerformanceDashboard, DashboardWidget, DashboardAlert,
    PerformanceChart, performance_dashboard
)
from .ab_testing_service import (
    ABTestingService, OptimizationEngine, ABTestExperiment,
    ExperimentVariant, OptimizationRecommendation, ExperimentStatus,
    ConfigurationType, ab_testing_service, optimization_engine
)

__all__ = [
    # Core workflow components
    'WorkflowContext',
    'ContextScope', 
    'WorkflowStateManager',
    'WorkflowStatus',
    'WorkflowState',
    'StateTransition',
    'WorkflowOrchestrator',
    'ExecutionStrategy',
    'WorkflowExecutionResult',
    
    # Email workflow components
    'EmailWorkflowStateManager',
    'EmailWorkflowState',
    'EmailWorkflowType',
    'EmailWorkflowPhase',
    'EmailContext',
    'ReviewContext',
    'EmailDeliveryStatus',
    
    # Persistent state management
    'PersistentEmailWorkflowStateManager',
    
    # Global context access
    'GlobalWorkflowContext',
    'global_context',
    'get_current_workflow',
    'get_workflow',
    'get_context_value',
    'set_context_value',
    'update_workflow_context',
    'advance_workflow_phase',
    'with_workflow_context',
    'requires_workflow_context',
    'auto_advance_phase',
    'get_workflow_logger',
    'WorkflowUtils',
    'workflow_utils',
    
    # Email workflow coordination
    'EmailWorkflowCoordinator',
    'EnhancedEmailWorkflowCoordinator',
    
    # Error recovery system
    'error_recovery_service',
    'ErrorRecoveryService',
    'ErrorType',
    'ErrorSeverity',
    'RecoveryAction',
    'RetryStrategy',
    'CircuitBreakerConfig',
    'CircuitBreakerState',
    'ErrorRecord',
    'RecoveryResult',
    'CircuitBreaker',
    'DeadLetterQueue',
    
    # Error monitoring and alerting
    'error_monitoring_service',
    'ErrorMonitoringService',
    'AlertSeverity',
    'AlertChannel',
    'AlertRule',
    'Alert',
    'ErrorPattern',
    
    # Performance Monitoring System
    'PerformanceMetricsCollector',
    'MetricType',
    'PerformanceSnapshot',
    'PerformanceTrend',
    'PerformanceThreshold',
    'MetricsRegistry',
    'performance_metrics_service',
    'PerformanceDashboard',
    'DashboardWidget',
    'DashboardAlert',
    'PerformanceChart',
    'performance_dashboard',
    'ABTestingService',
    'OptimizationEngine',
    'ABTestExperiment',
    'ExperimentVariant',
    'OptimizationRecommendation',
    'ExperimentStatus',
    'ConfigurationType',
    'ab_testing_service',
    'optimization_engine'
] 