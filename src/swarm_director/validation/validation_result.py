"""
Validation Result Classes

Defines standardized validation outcomes and status tracking for the 
hierarchical validation system.
"""

from enum import Enum
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, field


class ValidationStatus(Enum):
    """Status of validation process"""
    PENDING = "pending"
    PASSED = "passed"
    FAILED = "failed"
    REQUIRES_REVISION = "requires_revision"
    ESCALATED = "escalated"
    ROLLBACK_REQUIRED = "rollback_required"


@dataclass
class ValidationIssue:
    """Represents a specific validation issue"""
    severity: str  # 'critical', 'major', 'minor', 'warning'
    category: str  # 'quality', 'compliance', 'performance', 'security'
    message: str
    field: Optional[str] = None
    suggested_fix: Optional[str] = None
    auto_fixable: bool = False


@dataclass
class ValidationMetrics:
    """Metrics collected during validation"""
    quality_score: float = 0.0
    completeness_score: float = 0.0
    accuracy_score: float = 0.0
    performance_score: float = 0.0
    compliance_score: float = 0.0
    overall_score: float = 0.0
    
    def calculate_overall_score(self, weights: Optional[Dict[str, float]] = None) -> float:
        """Calculate weighted overall score"""
        if weights is None:
            weights = {
                'quality': 0.3,
                'completeness': 0.25,
                'accuracy': 0.25,
                'performance': 0.1,
                'compliance': 0.1
            }
        
        self.overall_score = (
            self.quality_score * weights.get('quality', 0.3) +
            self.completeness_score * weights.get('completeness', 0.25) +
            self.accuracy_score * weights.get('accuracy', 0.25) +
            self.performance_score * weights.get('performance', 0.1) +
            self.compliance_score * weights.get('compliance', 0.1)
        )
        return self.overall_score


@dataclass
class ValidationResult:
    """Comprehensive validation result"""
    status: ValidationStatus
    tier: str  # 'tool', 'department', 'director'
    validator_name: str
    task_id: str
    agent_id: str
    
    # Validation details
    metrics: ValidationMetrics = field(default_factory=ValidationMetrics)
    issues: List[ValidationIssue] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    
    # Metadata
    validation_timestamp: datetime = field(default_factory=datetime.utcnow)
    validation_duration_ms: int = 0
    validator_version: str = "1.0.0"
    
    # Context
    input_data: Optional[Dict[str, Any]] = None
    output_data: Optional[Dict[str, Any]] = None
    context: Dict[str, Any] = field(default_factory=dict)
    
    # Rollback information
    rollback_required: bool = False
    rollback_reason: Optional[str] = None
    rollback_actions: List[str] = field(default_factory=list)
    
    def add_issue(self, severity: str, category: str, message: str, 
                  field: Optional[str] = None, suggested_fix: Optional[str] = None,
                  auto_fixable: bool = False):
        """Add a validation issue"""
        issue = ValidationIssue(
            severity=severity,
            category=category,
            message=message,
            field=field,
            suggested_fix=suggested_fix,
            auto_fixable=auto_fixable
        )
        self.issues.append(issue)
        
        # Update status based on issue severity
        if severity == 'critical':
            self.status = ValidationStatus.FAILED
            self.rollback_required = True
        elif severity == 'major' and self.status == ValidationStatus.PENDING:
            self.status = ValidationStatus.REQUIRES_REVISION
    
    def add_recommendation(self, recommendation: str):
        """Add a validation recommendation"""
        self.recommendations.append(recommendation)
    
    def has_critical_issues(self) -> bool:
        """Check if there are any critical issues"""
        return any(issue.severity == 'critical' for issue in self.issues)
    
    def has_blocking_issues(self) -> bool:
        """Check if there are issues that block progression"""
        return any(issue.severity in ['critical', 'major'] for issue in self.issues)
    
    def get_auto_fixable_issues(self) -> List[ValidationIssue]:
        """Get issues that can be automatically fixed"""
        return [issue for issue in self.issues if issue.auto_fixable]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return {
            'status': self.status.value,
            'tier': self.tier,
            'validator_name': self.validator_name,
            'task_id': self.task_id,
            'agent_id': self.agent_id,
            'metrics': {
                'quality_score': self.metrics.quality_score,
                'completeness_score': self.metrics.completeness_score,
                'accuracy_score': self.metrics.accuracy_score,
                'performance_score': self.metrics.performance_score,
                'compliance_score': self.metrics.compliance_score,
                'overall_score': self.metrics.overall_score
            },
            'issues': [
                {
                    'severity': issue.severity,
                    'category': issue.category,
                    'message': issue.message,
                    'field': issue.field,
                    'suggested_fix': issue.suggested_fix,
                    'auto_fixable': issue.auto_fixable
                }
                for issue in self.issues
            ],
            'recommendations': self.recommendations,
            'validation_timestamp': self.validation_timestamp.isoformat(),
            'validation_duration_ms': self.validation_duration_ms,
            'validator_version': self.validator_version,
            'rollback_required': self.rollback_required,
            'rollback_reason': self.rollback_reason,
            'rollback_actions': self.rollback_actions,
            'context': self.context
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ValidationResult':
        """Create ValidationResult from dictionary"""
        result = cls(
            status=ValidationStatus(data['status']),
            tier=data['tier'],
            validator_name=data['validator_name'],
            task_id=data['task_id'],
            agent_id=data['agent_id']
        )
        
        # Set metrics
        metrics_data = data.get('metrics', {})
        result.metrics = ValidationMetrics(
            quality_score=metrics_data.get('quality_score', 0.0),
            completeness_score=metrics_data.get('completeness_score', 0.0),
            accuracy_score=metrics_data.get('accuracy_score', 0.0),
            performance_score=metrics_data.get('performance_score', 0.0),
            compliance_score=metrics_data.get('compliance_score', 0.0),
            overall_score=metrics_data.get('overall_score', 0.0)
        )
        
        # Set issues
        for issue_data in data.get('issues', []):
            result.add_issue(
                severity=issue_data['severity'],
                category=issue_data['category'],
                message=issue_data['message'],
                field=issue_data.get('field'),
                suggested_fix=issue_data.get('suggested_fix'),
                auto_fixable=issue_data.get('auto_fixable', False)
            )
        
        # Set other fields
        result.recommendations = data.get('recommendations', [])
        result.validation_duration_ms = data.get('validation_duration_ms', 0)
        result.validator_version = data.get('validator_version', '1.0.0')
        result.rollback_required = data.get('rollback_required', False)
        result.rollback_reason = data.get('rollback_reason')
        result.rollback_actions = data.get('rollback_actions', [])
        result.context = data.get('context', {})
        
        if 'validation_timestamp' in data:
            result.validation_timestamp = datetime.fromisoformat(data['validation_timestamp'])
        
        return result
