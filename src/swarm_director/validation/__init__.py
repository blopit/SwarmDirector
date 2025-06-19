"""
Hierarchical Validation System for SwarmDirector

This module implements a comprehensive validation chain where work completed by 
lower-tier agents must be reviewed and approved by their immediate upper-tier 
before results are propagated up the chain.

Components:
- ValidationChain: Manages the hierarchical validation flow
- QualityGate: Configurable quality thresholds and criteria
- ValidationResult: Standardized validation outcomes
- RollbackManager: Handles validation failures and rollbacks
"""

from .validation_chain import ValidationChain, ValidationTier
from .quality_gate import QualityGate, QualityThreshold, QualityMetric
from .validation_result import ValidationResult, ValidationStatus
from .rollback_manager import RollbackManager, RollbackAction
from .validators import (
    ToolAgentValidator,
    DepartmentAgentValidator, 
    DirectorAgentValidator,
    BaseValidator
)

__all__ = [
    'ValidationChain',
    'ValidationTier',
    'QualityGate',
    'QualityThreshold',
    'QualityMetric',
    'ValidationResult',
    'ValidationStatus',
    'RollbackManager',
    'RollbackAction',
    'ToolAgentValidator',
    'DepartmentAgentValidator',
    'DirectorAgentValidator',
    'BaseValidator'
]
