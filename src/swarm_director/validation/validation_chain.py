"""
Hierarchical Validation Chain

Manages the validation flow from Tool → Department → Director tiers,
ensuring each tier validates outputs from the tier below before 
propagating results upward.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Type
from datetime import datetime, timedelta
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor

from .validation_result import ValidationResult, ValidationStatus
from .quality_gate import QualityGate
from .rollback_manager import RollbackManager
from ..models.task import Task
from ..models.agent import Agent

logger = logging.getLogger(__name__)


class ValidationTier(Enum):
    """Validation tiers in the hierarchy"""
    TOOL = "TOOL"
    DEPARTMENT = "DEPARTMENT" 
    DIRECTOR = "DIRECTOR"


class ValidationChain:
    """
    Manages hierarchical validation flow with quality gates and rollback capabilities
    """
    
    def __init__(self, rollback_manager: Optional[RollbackManager] = None):
        self.rollback_manager = rollback_manager or RollbackManager()
        self.quality_gates: Dict[ValidationTier, QualityGate] = {}
        self.validators: Dict[ValidationTier, List[Any]] = {
            ValidationTier.TOOL: [],
            ValidationTier.DEPARTMENT: [],
            ValidationTier.DIRECTOR: []
        }
        self.validation_history: List[ValidationResult] = []
        self.executor = ThreadPoolExecutor(max_workers=4)
        
        # Initialize default quality gates
        self._initialize_quality_gates()
    
    def _initialize_quality_gates(self):
        """Initialize default quality gates for each tier"""
        self.quality_gates[ValidationTier.TOOL] = QualityGate("tool_gate", "tool")
        self.quality_gates[ValidationTier.DEPARTMENT] = QualityGate("department_gate", "department")
        self.quality_gates[ValidationTier.DIRECTOR] = QualityGate("director_gate", "director")
    
    def register_validator(self, tier: ValidationTier, validator):
        """Register a validator for a specific tier"""
        self.validators[tier].append(validator)
        logger.info(f"Registered validator {validator.__class__.__name__} for tier {tier.value}")
    
    def set_quality_gate(self, tier: ValidationTier, quality_gate: QualityGate):
        """Set custom quality gate for a tier"""
        self.quality_gates[tier] = quality_gate
        logger.info(f"Set custom quality gate for tier {tier.value}")
    
    async def validate_task_output(self, task: Task, agent: Agent, 
                                   output_data: Dict[str, Any],
                                   tier: ValidationTier) -> ValidationResult:
        """
        Validate task output at specified tier
        
        Args:
            task: The task being validated
            agent: The agent that produced the output
            output_data: The output data to validate
            tier: The validation tier
            
        Returns:
            ValidationResult with validation outcome
        """
        start_time = datetime.utcnow()
        
        # Create initial validation result
        result = ValidationResult(
            status=ValidationStatus.PENDING,
            tier=tier.value,
            validator_name=f"{tier.value}_validator",
            task_id=str(task.id),
            agent_id=str(agent.id),
            input_data=task.input_data,
            output_data=output_data
        )
        
        try:
            # Run validators for this tier
            validators = self.validators.get(tier, [])
            if not validators:
                logger.warning(f"No validators registered for tier {tier.value}")
                result.status = ValidationStatus.PASSED
                result.add_recommendation(f"No validators configured for {tier.value} tier")
            else:
                # Run all validators for this tier
                validation_tasks = []
                for validator in validators:
                    validation_tasks.append(
                        self._run_validator_async(validator, task, agent, output_data, result)
                    )
                
                # Wait for all validations to complete
                await asyncio.gather(*validation_tasks, return_exceptions=True)
            
            # Apply quality gate
            quality_gate = self.quality_gates.get(tier)
            if quality_gate:
                gate_result = quality_gate.evaluate(
                    {metric: getattr(result.metrics, metric.value + '_score', 0.0) 
                     for metric in quality_gate.thresholds},
                    output_data
                )
                
                # Update result based on quality gate
                if not gate_result['passed']:
                    if gate_result['critical_failures']:
                        result.status = ValidationStatus.FAILED
                        result.rollback_required = True
                        result.rollback_reason = "Critical quality gate failures"
                    else:
                        result.status = ValidationStatus.REQUIRES_REVISION
                    
                    # Add quality gate issues
                    for failure in gate_result['critical_failures']:
                        result.add_issue(
                            severity='critical' if 'critical' in failure else 'major',
                            category='quality',
                            message=failure.get('description', 'Quality gate failure'),
                            suggested_fix=failure.get('suggested_fix')
                        )
                    
                    # Add recommendations
                    result.recommendations.extend(gate_result['recommendations'])
                else:
                    if result.status == ValidationStatus.PENDING:
                        result.status = ValidationStatus.PASSED
                
                # Update overall score
                result.metrics.overall_score = gate_result['overall_score']
            
            # Calculate validation duration
            end_time = datetime.utcnow()
            result.validation_duration_ms = int((end_time - start_time).total_seconds() * 1000)
            
            # Store in history
            self.validation_history.append(result)
            
            logger.info(f"Validation completed for task {task.id} at tier {tier.value}: {result.status.value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Error during validation at tier {tier.value}: {e}", exc_info=True)
            result.status = ValidationStatus.FAILED
            result.add_issue(
                severity='critical',
                category='system',
                message=f"Validation system error: {str(e)}"
            )
            result.rollback_required = True
            result.rollback_reason = f"Validation system error: {str(e)}"
            
            return result
    
    async def _run_validator_async(self, validator, task: Task, agent: Agent, 
                                   output_data: Dict[str, Any], result: ValidationResult):
        """Run a single validator asynchronously"""
        try:
            # Run validator in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                self.executor,
                validator.validate,
                task, agent, output_data, result
            )
        except Exception as e:
            logger.error(f"Error in validator {validator.__class__.__name__}: {e}")
            result.add_issue(
                severity='major',
                category='validation',
                message=f"Validator error: {str(e)}"
            )
    
    async def validate_hierarchical_flow(self, task: Task, 
                                         tool_agent: Agent, tool_output: Dict[str, Any],
                                         dept_agent: Agent, dept_output: Dict[str, Any],
                                         director_agent: Agent, director_output: Dict[str, Any]) -> List[ValidationResult]:
        """
        Validate complete hierarchical flow: Tool → Department → Director
        
        Returns:
            List of ValidationResult objects for each tier
        """
        results = []
        
        try:
            # 1. Validate tool output
            logger.info(f"Starting hierarchical validation for task {task.id}")
            
            tool_result = await self.validate_task_output(
                task, tool_agent, tool_output, ValidationTier.TOOL
            )
            results.append(tool_result)
            
            # Check if tool validation passed
            if tool_result.status == ValidationStatus.FAILED:
                logger.warning(f"Tool validation failed for task {task.id}, stopping chain")
                await self._handle_validation_failure(tool_result, task)
                return results
            
            # 2. Validate department output (includes tool output review)
            dept_result = await self.validate_task_output(
                task, dept_agent, dept_output, ValidationTier.DEPARTMENT
            )
            dept_result.context['tool_validation'] = tool_result.to_dict()
            results.append(dept_result)
            
            # Check if department validation passed
            if dept_result.status == ValidationStatus.FAILED:
                logger.warning(f"Department validation failed for task {task.id}, stopping chain")
                await self._handle_validation_failure(dept_result, task)
                return results
            
            # 3. Validate director output (includes department output review)
            director_result = await self.validate_task_output(
                task, director_agent, director_output, ValidationTier.DIRECTOR
            )
            director_result.context['department_validation'] = dept_result.to_dict()
            director_result.context['tool_validation'] = tool_result.to_dict()
            results.append(director_result)
            
            # Check final validation
            if director_result.status == ValidationStatus.FAILED:
                logger.warning(f"Director validation failed for task {task.id}")
                await self._handle_validation_failure(director_result, task)
            else:
                logger.info(f"Hierarchical validation completed successfully for task {task.id}")
            
            return results
            
        except Exception as e:
            logger.error(f"Error in hierarchical validation for task {task.id}: {e}", exc_info=True)
            
            # Create error result
            error_result = ValidationResult(
                status=ValidationStatus.FAILED,
                tier="system",
                validator_name="hierarchical_validator",
                task_id=str(task.id),
                agent_id="system"
            )
            error_result.add_issue(
                severity='critical',
                category='system',
                message=f"Hierarchical validation system error: {str(e)}"
            )
            error_result.rollback_required = True
            error_result.rollback_reason = f"System error: {str(e)}"
            
            results.append(error_result)
            return results
    
    async def _handle_validation_failure(self, result: ValidationResult, task: Task):
        """Handle validation failure with appropriate rollback actions"""
        if result.rollback_required:
            logger.info(f"Initiating rollback for task {task.id} due to validation failure")
            
            try:
                await self.rollback_manager.execute_rollback(
                    task_id=str(task.id),
                    reason=result.rollback_reason or "Validation failure",
                    validation_result=result
                )
            except Exception as e:
                logger.error(f"Error during rollback for task {task.id}: {e}")
    
    def get_validation_history(self, task_id: Optional[str] = None, 
                               tier: Optional[ValidationTier] = None) -> List[ValidationResult]:
        """Get validation history with optional filtering"""
        history = self.validation_history
        
        if task_id:
            history = [r for r in history if r.task_id == task_id]
        
        if tier:
            history = [r for r in history if r.tier == tier.value]
        
        return history
    
    def get_validation_statistics(self) -> Dict[str, Any]:
        """Get validation statistics across all tiers"""
        stats = {
            'total_validations': len(self.validation_history),
            'by_tier': {},
            'by_status': {},
            'average_scores': {},
            'rollback_rate': 0.0
        }
        
        # Calculate statistics by tier
        for tier in ValidationTier:
            tier_results = [r for r in self.validation_history if r.tier == tier.value]
            stats['by_tier'][tier.value] = {
                'count': len(tier_results),
                'passed': len([r for r in tier_results if r.status == ValidationStatus.PASSED]),
                'failed': len([r for r in tier_results if r.status == ValidationStatus.FAILED]),
                'avg_score': sum(r.metrics.overall_score for r in tier_results) / len(tier_results) if tier_results else 0.0
            }
        
        # Calculate statistics by status
        for status in ValidationStatus:
            count = len([r for r in self.validation_history if r.status == status])
            stats['by_status'][status.value] = count
        
        # Calculate rollback rate
        rollbacks = len([r for r in self.validation_history if r.rollback_required])
        stats['rollback_rate'] = rollbacks / len(self.validation_history) if self.validation_history else 0.0
        
        return stats
    
    def cleanup_old_history(self, days: int = 30):
        """Clean up validation history older than specified days"""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        initial_count = len(self.validation_history)
        
        self.validation_history = [
            r for r in self.validation_history 
            if r.validation_timestamp > cutoff_date
        ]
        
        cleaned_count = initial_count - len(self.validation_history)
        logger.info(f"Cleaned up {cleaned_count} old validation records")
        
        return cleaned_count
