"""
Hierarchical Validators

Implements validators for each tier in the validation chain:
- ToolAgentValidator: Validates tool agent outputs
- DepartmentAgentValidator: Validates department agent outputs  
- DirectorAgentValidator: Validates director agent outputs
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging
import re
import json
from datetime import datetime

from .validation_result import ValidationResult, ValidationMetrics
from .quality_gate import QualityMetric
from ..models.task import Task
from ..models.agent import Agent

logger = logging.getLogger(__name__)


class BaseValidator(ABC):
    """Abstract base class for all validators"""
    
    def __init__(self, name: str, version: str = "1.0.0"):
        self.name = name
        self.version = version
        self.metrics_weights = self._get_default_metrics_weights()
    
    def _get_default_metrics_weights(self) -> Dict[str, float]:
        """Get default weights for metrics calculation"""
        return {
            'accuracy': 1.0,
            'completeness': 1.0,
            'performance': 0.5,
            'compliance': 0.8,
            'consistency': 0.7,
            'relevance': 0.9,
            'clarity': 0.6,
            'efficiency': 0.4
        }
    
    @abstractmethod
    def validate(self, task: Task, agent: Agent, output_data: Dict[str, Any], 
                 result: ValidationResult) -> None:
        """
        Validate output data and update validation result
        
        Args:
            task: The task being validated
            agent: The agent that produced the output
            output_data: The output data to validate
            result: ValidationResult to update with findings
        """
        pass
    
    def _calculate_completeness_score(self, output_data: Dict[str, Any], 
                                      required_fields: List[str]) -> float:
        """Calculate completeness score based on required fields"""
        if not required_fields:
            return 1.0
        
        present_fields = 0
        for field in required_fields:
            if self._is_field_present(output_data, field):
                present_fields += 1
        
        return present_fields / len(required_fields)
    
    def _is_field_present(self, data: Dict[str, Any], field_path: str) -> bool:
        """Check if a field is present in nested data structure"""
        try:
            keys = field_path.split('.')
            current = data
            for key in keys:
                if isinstance(current, dict) and key in current:
                    current = current[key]
                else:
                    return False
            return current is not None and current != ""
        except:
            return False
    
    def _calculate_accuracy_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate accuracy score - to be overridden by specific validators"""
        # Default implementation - can be enhanced with ML models
        return 0.8  # Placeholder
    
    def _calculate_performance_score(self, execution_time_ms: int, 
                                     expected_time_ms: int = 5000) -> float:
        """Calculate performance score based on execution time"""
        if execution_time_ms <= expected_time_ms:
            return 1.0
        elif execution_time_ms <= expected_time_ms * 2:
            return 0.8
        elif execution_time_ms <= expected_time_ms * 3:
            return 0.6
        else:
            return 0.4
    
    def _validate_data_structure(self, data: Dict[str, Any], 
                                 expected_structure: Dict[str, type]) -> List[str]:
        """Validate data structure against expected schema"""
        issues = []
        
        for field, expected_type in expected_structure.items():
            if field not in data:
                issues.append(f"Missing required field: {field}")
            elif not isinstance(data[field], expected_type):
                issues.append(f"Field {field} has incorrect type: expected {expected_type.__name__}, got {type(data[field]).__name__}")
        
        return issues


class ToolAgentValidator(BaseValidator):
    """Validator for tool agent outputs"""
    
    def __init__(self):
        super().__init__("ToolAgentValidator", "1.0.0")
        self.required_fields = ["status", "output", "execution_time"]
        self.expected_structure = {
            "status": str,
            "output": (str, dict, list),
            "execution_time": (int, float)
        }
    
    def validate(self, task: Task, agent: Agent, output_data: Dict[str, Any], 
                 result: ValidationResult) -> None:
        """Validate tool agent output"""
        logger.debug(f"Validating tool agent output for task {task.id}")
        
        # Validate basic structure
        structure_issues = self._validate_data_structure(output_data, self.expected_structure)
        for issue in structure_issues:
            result.add_issue(
                severity='major',
                category='structure',
                message=issue,
                auto_fixable=False
            )
        
        # Calculate metrics
        metrics = ValidationMetrics()
        
        # Completeness score
        metrics.completeness_score = self._calculate_completeness_score(
            output_data, self.required_fields
        )
        
        # Accuracy score (tool-specific logic)
        metrics.accuracy_score = self._calculate_tool_accuracy_score(output_data, task)
        
        # Performance score
        execution_time = output_data.get('execution_time', 0)
        metrics.performance_score = self._calculate_performance_score(execution_time)
        
        # Compliance score (check for required tool outputs)
        metrics.compliance_score = self._calculate_tool_compliance_score(output_data, agent)
        
        # Update result metrics
        result.metrics = metrics
        
        # Add specific validations
        self._validate_tool_output_content(output_data, result)
        self._validate_tool_error_handling(output_data, result)
    
    def _calculate_tool_accuracy_score(self, output_data: Dict[str, Any], task: Task) -> float:
        """Calculate accuracy score for tool output"""
        # Check if output status indicates success
        status = output_data.get('status', '').lower()
        if status in ['success', 'completed', 'done']:
            base_score = 0.9
        elif status in ['partial', 'warning']:
            base_score = 0.7
        elif status in ['error', 'failed']:
            base_score = 0.3
        else:
            base_score = 0.5
        
        # Check if output is present and non-empty
        output = output_data.get('output')
        if output and (isinstance(output, str) and len(output.strip()) > 0) or \
           (isinstance(output, (dict, list)) and len(output) > 0):
            base_score += 0.1
        
        return min(base_score, 1.0)
    
    def _calculate_tool_compliance_score(self, output_data: Dict[str, Any], agent: Agent) -> float:
        """Calculate compliance score for tool output"""
        score = 1.0
        
        # Check if agent capabilities are properly utilized
        capabilities = agent.capabilities or []
        if not capabilities:
            score -= 0.1
        
        # Check for proper error reporting
        if 'error' in output_data and not output_data.get('error_details'):
            score -= 0.2
        
        return max(score, 0.0)
    
    def _validate_tool_output_content(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate tool output content"""
        output = output_data.get('output')
        
        if not output:
            result.add_issue(
                severity='major',
                category='content',
                message="Tool output is empty or missing",
                suggested_fix="Ensure tool produces meaningful output"
            )
        
        # Check for common error patterns
        if isinstance(output, str):
            error_patterns = [
                r'error|exception|failed|traceback',
                r'null|undefined|none',
                r'todo|fixme|placeholder'
            ]
            
            for pattern in error_patterns:
                if re.search(pattern, output.lower()):
                    result.add_issue(
                        severity='minor',
                        category='content',
                        message=f"Output contains potential error indicator: {pattern}",
                        suggested_fix="Review output for errors or incomplete content"
                    )
    
    def _validate_tool_error_handling(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate tool error handling"""
        status = output_data.get('status', '').lower()
        
        if status in ['error', 'failed']:
            if not output_data.get('error_details'):
                result.add_issue(
                    severity='major',
                    category='error_handling',
                    message="Error status without detailed error information",
                    suggested_fix="Include error_details field with specific error information"
                )
            
            if not output_data.get('recovery_suggestions'):
                result.add_issue(
                    severity='minor',
                    category='error_handling',
                    message="No recovery suggestions provided for error",
                    suggested_fix="Include recovery_suggestions for error scenarios",
                    auto_fixable=True
                )


class DepartmentAgentValidator(BaseValidator):
    """Validator for department agent outputs"""
    
    def __init__(self):
        super().__init__("DepartmentAgentValidator", "1.0.0")
        self.required_fields = ["status", "result", "review_summary", "quality_assessment"]
        self.expected_structure = {
            "status": str,
            "result": dict,
            "review_summary": str,
            "quality_assessment": dict
        }
    
    def validate(self, task: Task, agent: Agent, output_data: Dict[str, Any], 
                 result: ValidationResult) -> None:
        """Validate department agent output"""
        logger.debug(f"Validating department agent output for task {task.id}")
        
        # Validate structure
        structure_issues = self._validate_data_structure(output_data, self.expected_structure)
        for issue in structure_issues:
            result.add_issue(
                severity='major',
                category='structure',
                message=issue
            )
        
        # Calculate metrics
        metrics = ValidationMetrics()
        
        # Completeness score
        metrics.completeness_score = self._calculate_completeness_score(
            output_data, self.required_fields
        )
        
        # Accuracy score
        metrics.accuracy_score = self._calculate_department_accuracy_score(output_data)
        
        # Consistency score
        metrics.consistency_score = self._calculate_consistency_score(output_data)
        
        # Relevance score
        metrics.relevance_score = self._calculate_relevance_score(output_data, task)
        
        # Compliance score
        metrics.compliance_score = self._calculate_department_compliance_score(output_data)
        
        result.metrics = metrics
        
        # Department-specific validations
        self._validate_review_quality(output_data, result)
        self._validate_consensus_process(output_data, result)
    
    def _calculate_department_accuracy_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate accuracy score for department output"""
        quality_assessment = output_data.get('quality_assessment', {})
        
        # Use quality assessment scores if available
        if isinstance(quality_assessment, dict):
            scores = []
            for key, value in quality_assessment.items():
                if isinstance(value, (int, float)) and 0 <= value <= 1:
                    scores.append(value)
            
            if scores:
                return sum(scores) / len(scores)
        
        # Fallback to status-based scoring
        status = output_data.get('status', '').lower()
        if status in ['approved', 'completed', 'consensus_reached']:
            return 0.9
        elif status in ['needs_revision', 'partial_approval']:
            return 0.7
        else:
            return 0.5
    
    def _calculate_consistency_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate consistency score"""
        # Check consistency between review summary and quality assessment
        review_summary = output_data.get('review_summary', '')
        quality_assessment = output_data.get('quality_assessment', {})
        
        if not review_summary or not quality_assessment:
            return 0.5
        
        # Simple consistency check - can be enhanced with NLP
        positive_words = ['good', 'excellent', 'approved', 'satisfactory']
        negative_words = ['poor', 'inadequate', 'rejected', 'unsatisfactory']
        
        summary_sentiment = 0
        for word in positive_words:
            if word in review_summary.lower():
                summary_sentiment += 1
        for word in negative_words:
            if word in review_summary.lower():
                summary_sentiment -= 1
        
        # Compare with quality scores
        avg_quality = sum(v for v in quality_assessment.values() if isinstance(v, (int, float))) / len(quality_assessment) if quality_assessment else 0.5
        
        # Check alignment
        if (summary_sentiment > 0 and avg_quality > 0.7) or (summary_sentiment < 0 and avg_quality < 0.5):
            return 0.9
        elif summary_sentiment == 0 or (0.5 <= avg_quality <= 0.7):
            return 0.7
        else:
            return 0.4
    
    def _calculate_relevance_score(self, output_data: Dict[str, Any], task: Task) -> float:
        """Calculate relevance score"""
        # Check if output addresses task requirements
        result_data = output_data.get('result', {})
        task_description = task.description or ''
        
        if not result_data or not task_description:
            return 0.5
        
        # Simple keyword matching - can be enhanced with semantic analysis
        task_keywords = set(task_description.lower().split())
        result_text = str(result_data).lower()
        
        matching_keywords = sum(1 for keyword in task_keywords if keyword in result_text)
        relevance = matching_keywords / len(task_keywords) if task_keywords else 0.5
        
        return min(relevance + 0.3, 1.0)  # Add base score
    
    def _calculate_department_compliance_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate compliance score for department output"""
        score = 1.0
        
        # Check for required review process indicators
        if not output_data.get('review_summary'):
            score -= 0.3
        
        if not output_data.get('quality_assessment'):
            score -= 0.3
        
        # Check for proper status reporting
        status = output_data.get('status', '').lower()
        valid_statuses = ['approved', 'rejected', 'needs_revision', 'consensus_reached', 'partial_approval']
        if status not in valid_statuses:
            score -= 0.2
        
        return max(score, 0.0)
    
    def _validate_review_quality(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate quality of review process"""
        review_summary = output_data.get('review_summary', '')
        
        if len(review_summary) < 50:
            result.add_issue(
                severity='minor',
                category='review_quality',
                message="Review summary is too brief",
                suggested_fix="Provide more detailed review summary (minimum 50 characters)"
            )
        
        quality_assessment = output_data.get('quality_assessment', {})
        if not isinstance(quality_assessment, dict) or len(quality_assessment) < 2:
            result.add_issue(
                severity='major',
                category='review_quality',
                message="Quality assessment is incomplete",
                suggested_fix="Provide comprehensive quality assessment with multiple criteria"
            )
    
    def _validate_consensus_process(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate consensus process indicators"""
        status = output_data.get('status', '').lower()
        
        if 'consensus' in status:
            if not output_data.get('consensus_details'):
                result.add_issue(
                    severity='minor',
                    category='consensus',
                    message="Consensus status without details",
                    suggested_fix="Include consensus_details explaining how consensus was reached"
                )


class DirectorAgentValidator(BaseValidator):
    """Validator for director agent outputs"""
    
    def __init__(self):
        super().__init__("DirectorAgentValidator", "1.0.0")
        self.required_fields = ["status", "final_result", "validation_summary", "approval_status"]
        self.expected_structure = {
            "status": str,
            "final_result": dict,
            "validation_summary": str,
            "approval_status": str
        }
    
    def validate(self, task: Task, agent: Agent, output_data: Dict[str, Any], 
                 result: ValidationResult) -> None:
        """Validate director agent output"""
        logger.debug(f"Validating director agent output for task {task.id}")
        
        # Validate structure
        structure_issues = self._validate_data_structure(output_data, self.expected_structure)
        for issue in structure_issues:
            result.add_issue(
                severity='critical',
                category='structure',
                message=issue
            )
        
        # Calculate metrics with higher standards
        metrics = ValidationMetrics()
        
        # Completeness score (higher threshold)
        metrics.completeness_score = self._calculate_completeness_score(
            output_data, self.required_fields
        )
        
        # Accuracy score (director-level)
        metrics.accuracy_score = self._calculate_director_accuracy_score(output_data)
        
        # Compliance score (strict)
        metrics.compliance_score = self._calculate_director_compliance_score(output_data)
        
        # Clarity score
        metrics.clarity_score = self._calculate_clarity_score(output_data)
        
        result.metrics = metrics
        
        # Director-specific validations
        self._validate_final_approval(output_data, result)
        self._validate_validation_summary(output_data, result)
        self._validate_completeness_standards(output_data, result)
    
    def _calculate_director_accuracy_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate accuracy score for director output with high standards"""
        approval_status = output_data.get('approval_status', '').lower()
        
        if approval_status == 'approved':
            base_score = 0.95
        elif approval_status == 'conditionally_approved':
            base_score = 0.8
        elif approval_status == 'rejected':
            base_score = 0.6  # Rejection can be accurate
        else:
            base_score = 0.4
        
        # Check for comprehensive validation summary
        validation_summary = output_data.get('validation_summary', '')
        if len(validation_summary) > 100:
            base_score += 0.05
        
        return min(base_score, 1.0)
    
    def _calculate_director_compliance_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate compliance score with strict director standards"""
        score = 1.0
        
        # All required fields must be present
        for field in self.required_fields:
            if not output_data.get(field):
                score -= 0.25
        
        # Approval status must be valid
        approval_status = output_data.get('approval_status', '').lower()
        valid_approvals = ['approved', 'rejected', 'conditionally_approved', 'needs_revision']
        if approval_status not in valid_approvals:
            score -= 0.3
        
        return max(score, 0.0)
    
    def _calculate_clarity_score(self, output_data: Dict[str, Any]) -> float:
        """Calculate clarity score for director output"""
        validation_summary = output_data.get('validation_summary', '')
        
        if len(validation_summary) < 50:
            return 0.3
        elif len(validation_summary) < 100:
            return 0.6
        else:
            return 0.9
    
    def _validate_final_approval(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate final approval process"""
        approval_status = output_data.get('approval_status', '').lower()
        
        if not approval_status:
            result.add_issue(
                severity='critical',
                category='approval',
                message="Missing approval status in director output"
            )
        
        if approval_status == 'approved':
            if not output_data.get('final_result'):
                result.add_issue(
                    severity='critical',
                    category='approval',
                    message="Approved status without final result"
                )
    
    def _validate_validation_summary(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate validation summary quality"""
        validation_summary = output_data.get('validation_summary', '')
        
        if len(validation_summary) < 100:
            result.add_issue(
                severity='major',
                category='documentation',
                message="Validation summary is insufficient for director level",
                suggested_fix="Provide comprehensive validation summary (minimum 100 characters)"
            )
        
        # Check for key validation elements
        required_elements = ['quality', 'compliance', 'completeness']
        missing_elements = [elem for elem in required_elements 
                           if elem not in validation_summary.lower()]
        
        if missing_elements:
            result.add_issue(
                severity='minor',
                category='documentation',
                message=f"Validation summary missing key elements: {', '.join(missing_elements)}",
                suggested_fix=f"Include discussion of: {', '.join(missing_elements)}"
            )
    
    def _validate_completeness_standards(self, output_data: Dict[str, Any], result: ValidationResult):
        """Validate director-level completeness standards"""
        final_result = output_data.get('final_result', {})
        
        if not isinstance(final_result, dict) or len(final_result) < 3:
            result.add_issue(
                severity='major',
                category='completeness',
                message="Final result lacks sufficient detail for director approval",
                suggested_fix="Ensure final result contains comprehensive output data"
            )
