"""
Quality Gate System

Implements configurable quality thresholds and validation criteria 
for each tier in the hierarchical validation system.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, field
import json
import logging

logger = logging.getLogger(__name__)


class QualityMetric(Enum):
    """Available quality metrics"""
    ACCURACY = "accuracy"
    COMPLETENESS = "completeness"
    PERFORMANCE = "performance"
    COMPLIANCE = "compliance"
    CONSISTENCY = "consistency"
    RELEVANCE = "relevance"
    CLARITY = "clarity"
    EFFICIENCY = "efficiency"


@dataclass
class QualityThreshold:
    """Defines a quality threshold for a specific metric"""
    metric: QualityMetric
    minimum_score: float  # 0.0 to 1.0
    weight: float = 1.0  # Importance weight
    critical: bool = False  # If true, failure blocks progression
    description: str = ""
    
    def evaluate(self, score: float) -> bool:
        """Evaluate if score meets threshold"""
        return score >= self.minimum_score


@dataclass
class QualityRule:
    """Custom quality rule with validation logic"""
    name: str
    description: str
    validator_function: Callable[[Dict[str, Any]], bool]
    error_message: str
    severity: str = "major"  # 'critical', 'major', 'minor', 'warning'
    auto_fixable: bool = False
    suggested_fix: Optional[str] = None


class QualityGate:
    """
    Configurable quality gate that validates outputs against defined thresholds
    """
    
    def __init__(self, name: str, tier: str, config: Optional[Dict[str, Any]] = None):
        self.name = name
        self.tier = tier  # 'tool', 'department', 'director'
        self.thresholds: List[QualityThreshold] = []
        self.rules: List[QualityRule] = []
        self.config = config or {}
        
        # Load default configuration based on tier
        self._load_default_config()
    
    def _load_default_config(self):
        """Load default quality thresholds based on tier"""
        if self.tier == "tool":
            self._load_tool_defaults()
        elif self.tier == "department":
            self._load_department_defaults()
        elif self.tier == "director":
            self._load_director_defaults()
    
    def _load_tool_defaults(self):
        """Load default thresholds for tool-level validation"""
        self.thresholds = [
            QualityThreshold(
                metric=QualityMetric.COMPLETENESS,
                minimum_score=0.8,
                weight=1.5,
                critical=True,
                description="Output must be substantially complete"
            ),
            QualityThreshold(
                metric=QualityMetric.ACCURACY,
                minimum_score=0.7,
                weight=1.0,
                critical=False,
                description="Output should be reasonably accurate"
            ),
            QualityThreshold(
                metric=QualityMetric.PERFORMANCE,
                minimum_score=0.6,
                weight=0.5,
                critical=False,
                description="Execution should meet performance standards"
            )
        ]
    
    def _load_department_defaults(self):
        """Load default thresholds for department-level validation"""
        self.thresholds = [
            QualityThreshold(
                metric=QualityMetric.ACCURACY,
                minimum_score=0.85,
                weight=1.5,
                critical=True,
                description="Department output must be highly accurate"
            ),
            QualityThreshold(
                metric=QualityMetric.COMPLETENESS,
                minimum_score=0.9,
                weight=1.2,
                critical=True,
                description="Department output must be comprehensive"
            ),
            QualityThreshold(
                metric=QualityMetric.CONSISTENCY,
                minimum_score=0.8,
                weight=1.0,
                critical=False,
                description="Output should be consistent with standards"
            ),
            QualityThreshold(
                metric=QualityMetric.RELEVANCE,
                minimum_score=0.8,
                weight=1.0,
                critical=False,
                description="Output should be relevant to task requirements"
            )
        ]
    
    def _load_director_defaults(self):
        """Load default thresholds for director-level validation"""
        self.thresholds = [
            QualityThreshold(
                metric=QualityMetric.ACCURACY,
                minimum_score=0.9,
                weight=2.0,
                critical=True,
                description="Director validation requires high accuracy"
            ),
            QualityThreshold(
                metric=QualityMetric.COMPLETENESS,
                minimum_score=0.95,
                weight=1.8,
                critical=True,
                description="Final output must be complete"
            ),
            QualityThreshold(
                metric=QualityMetric.COMPLIANCE,
                minimum_score=0.9,
                weight=1.5,
                critical=True,
                description="Must comply with all policies and standards"
            ),
            QualityThreshold(
                metric=QualityMetric.CLARITY,
                minimum_score=0.85,
                weight=1.0,
                critical=False,
                description="Output should be clear and well-structured"
            )
        ]
    
    def add_threshold(self, threshold: QualityThreshold):
        """Add a quality threshold"""
        self.thresholds.append(threshold)
    
    def add_rule(self, rule: QualityRule):
        """Add a custom quality rule"""
        self.rules.append(rule)
    
    def evaluate(self, metrics: Dict[QualityMetric, float], 
                 output_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Evaluate quality gate against provided metrics and output data
        
        Returns:
            Dict containing evaluation results
        """
        results = {
            'passed': True,
            'overall_score': 0.0,
            'threshold_results': [],
            'rule_results': [],
            'critical_failures': [],
            'recommendations': []
        }
        
        # Evaluate thresholds
        total_weight = 0.0
        weighted_score = 0.0
        
        for threshold in self.thresholds:
            score = metrics.get(threshold.metric, 0.0)
            passed = threshold.evaluate(score)
            
            threshold_result = {
                'metric': threshold.metric.value,
                'score': score,
                'threshold': threshold.minimum_score,
                'passed': passed,
                'weight': threshold.weight,
                'critical': threshold.critical,
                'description': threshold.description
            }
            results['threshold_results'].append(threshold_result)
            
            # Update overall score
            weighted_score += score * threshold.weight
            total_weight += threshold.weight
            
            # Check for critical failures
            if not passed and threshold.critical:
                results['passed'] = False
                results['critical_failures'].append({
                    'metric': threshold.metric.value,
                    'score': score,
                    'required': threshold.minimum_score,
                    'description': threshold.description
                })
            
            # Add recommendations for failed thresholds
            if not passed:
                recommendation = f"Improve {threshold.metric.value}: current {score:.2f}, required {threshold.minimum_score:.2f}"
                results['recommendations'].append(recommendation)
        
        # Calculate overall score
        if total_weight > 0:
            results['overall_score'] = weighted_score / total_weight
        
        # Evaluate custom rules
        for rule in self.rules:
            try:
                rule_passed = rule.validator_function(output_data)
                rule_result = {
                    'name': rule.name,
                    'passed': rule_passed,
                    'severity': rule.severity,
                    'description': rule.description,
                    'auto_fixable': rule.auto_fixable,
                    'suggested_fix': rule.suggested_fix
                }
                results['rule_results'].append(rule_result)
                
                if not rule_passed:
                    if rule.severity == 'critical':
                        results['passed'] = False
                        results['critical_failures'].append({
                            'rule': rule.name,
                            'error': rule.error_message,
                            'severity': rule.severity
                        })
                    
                    if rule.suggested_fix:
                        results['recommendations'].append(rule.suggested_fix)
                        
            except Exception as e:
                logger.error(f"Error evaluating rule {rule.name}: {e}")
                rule_result = {
                    'name': rule.name,
                    'passed': False,
                    'error': str(e),
                    'severity': 'major'
                }
                results['rule_results'].append(rule_result)
        
        return results
    
    def get_minimum_overall_score(self) -> float:
        """Calculate minimum overall score based on critical thresholds"""
        critical_thresholds = [t for t in self.thresholds if t.critical]
        if not critical_thresholds:
            return 0.0
        
        total_weight = sum(t.weight for t in critical_thresholds)
        weighted_min = sum(t.minimum_score * t.weight for t in critical_thresholds)
        
        return weighted_min / total_weight if total_weight > 0 else 0.0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert quality gate to dictionary for serialization"""
        return {
            'name': self.name,
            'tier': self.tier,
            'thresholds': [
                {
                    'metric': t.metric.value,
                    'minimum_score': t.minimum_score,
                    'weight': t.weight,
                    'critical': t.critical,
                    'description': t.description
                }
                for t in self.thresholds
            ],
            'rules': [
                {
                    'name': r.name,
                    'description': r.description,
                    'error_message': r.error_message,
                    'severity': r.severity,
                    'auto_fixable': r.auto_fixable,
                    'suggested_fix': r.suggested_fix
                }
                for r in self.rules
            ],
            'config': self.config
        }
    
    @classmethod
    def from_config_file(cls, config_path: str, tier: str) -> 'QualityGate':
        """Load quality gate from configuration file"""
        try:
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            gate = cls(
                name=config.get('name', f'{tier}_quality_gate'),
                tier=tier,
                config=config
            )
            
            # Load custom thresholds if provided
            if 'thresholds' in config:
                gate.thresholds = []
                for threshold_config in config['thresholds']:
                    threshold = QualityThreshold(
                        metric=QualityMetric(threshold_config['metric']),
                        minimum_score=threshold_config['minimum_score'],
                        weight=threshold_config.get('weight', 1.0),
                        critical=threshold_config.get('critical', False),
                        description=threshold_config.get('description', '')
                    )
                    gate.add_threshold(threshold)
            
            return gate
            
        except Exception as e:
            logger.error(f"Error loading quality gate config from {config_path}: {e}")
            # Return default gate
            return cls(name=f'{tier}_quality_gate', tier=tier)
