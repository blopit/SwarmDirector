"""
Capability Discovery System

Identifies missing capabilities in the current system and suggests/installs 
appropriate plugins to fulfill task requirements.
"""

from enum import Enum
from typing import Dict, Any, List, Optional, Set, Tuple
from dataclasses import dataclass, field
import logging
import re
from datetime import datetime

from .plugin_registry import PluginRegistry, PluginMetadata, PluginType
from .agent_factory import AgentFactory
from ..models.task import Task
from ..models.agent import Agent

logger = logging.getLogger(__name__)


class CapabilityType(Enum):
    """Types of capabilities"""
    CORE = "core"
    DOMAIN_SPECIFIC = "domain_specific"
    INTEGRATION = "integration"
    UTILITY = "utility"
    ADVANCED = "advanced"


class GapSeverity(Enum):
    """Severity of capability gaps"""
    CRITICAL = "critical"  # Task cannot be completed
    HIGH = "high"         # Task quality significantly impacted
    MEDIUM = "medium"     # Task can be completed but suboptimally
    LOW = "low"          # Minor enhancement opportunity


@dataclass
class CapabilityGap:
    """Represents a missing capability"""
    name: str
    description: str
    capability_type: CapabilityType
    severity: GapSeverity
    
    # Context
    required_for_task: str
    current_alternatives: List[str] = field(default_factory=list)
    
    # Suggestions
    suggested_plugins: List[str] = field(default_factory=list)
    suggested_templates: List[str] = field(default_factory=list)
    
    # Impact assessment
    impact_score: float = 0.0  # 0.0 to 1.0
    effort_to_resolve: str = "medium"  # low, medium, high
    
    # Metadata
    discovered_at: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'name': self.name,
            'description': self.description,
            'capability_type': self.capability_type.value,
            'severity': self.severity.value,
            'required_for_task': self.required_for_task,
            'current_alternatives': self.current_alternatives,
            'suggested_plugins': self.suggested_plugins,
            'suggested_templates': self.suggested_templates,
            'impact_score': self.impact_score,
            'effort_to_resolve': self.effort_to_resolve,
            'discovered_at': self.discovered_at.isoformat()
        }


@dataclass
class CapabilityAssessment:
    """Assessment of system capabilities for a task"""
    task_id: str
    required_capabilities: List[str]
    available_capabilities: List[str]
    gaps: List[CapabilityGap] = field(default_factory=list)
    
    # Overall assessment
    completeness_score: float = 0.0  # 0.0 to 1.0
    can_complete_task: bool = False
    recommended_actions: List[str] = field(default_factory=list)
    
    # Metadata
    assessed_at: datetime = field(default_factory=datetime.utcnow)
    assessment_version: str = "1.0.0"


class CapabilityDiscovery:
    """
    System for discovering capability gaps and suggesting solutions
    """
    
    def __init__(self, plugin_registry: PluginRegistry, agent_factory: AgentFactory):
        self.plugin_registry = plugin_registry
        self.agent_factory = agent_factory
        self.capability_patterns: Dict[str, List[str]] = {}
        self.assessment_history: List[CapabilityAssessment] = []
        
        # Load capability patterns
        self._load_capability_patterns()
    
    def _load_capability_patterns(self):
        """Load patterns for identifying required capabilities from tasks"""
        self.capability_patterns = {
            'email_sending': [
                r'send.*email', r'email.*notification', r'notify.*email',
                r'mail.*delivery', r'smtp', r'email.*campaign'
            ],
            'data_analysis': [
                r'analyz.*data', r'data.*analysis', r'statistical.*analysis',
                r'report.*generation', r'metrics.*calculation', r'trend.*analysis'
            ],
            'file_processing': [
                r'process.*file', r'file.*conversion', r'document.*processing',
                r'pdf.*generation', r'excel.*processing', r'csv.*handling'
            ],
            'web_scraping': [
                r'scrape.*web', r'web.*scraping', r'extract.*website',
                r'crawl.*site', r'harvest.*data', r'web.*data.*extraction'
            ],
            'api_integration': [
                r'api.*integration', r'rest.*api', r'webhook.*handling',
                r'third.*party.*integration', r'external.*service'
            ],
            'image_processing': [
                r'image.*processing', r'photo.*editing', r'image.*analysis',
                r'computer.*vision', r'ocr', r'image.*recognition'
            ],
            'natural_language_processing': [
                r'text.*analysis', r'nlp', r'sentiment.*analysis',
                r'language.*processing', r'text.*classification', r'summarization'
            ],
            'database_operations': [
                r'database.*query', r'sql.*operations', r'data.*storage',
                r'crud.*operations', r'database.*management'
            ],
            'workflow_automation': [
                r'automate.*workflow', r'process.*automation', r'task.*scheduling',
                r'workflow.*orchestration', r'batch.*processing'
            ],
            'monitoring_alerting': [
                r'monitor.*system', r'alert.*notification', r'health.*check',
                r'performance.*monitoring', r'log.*analysis'
            ]
        }
    
    def assess_task_capabilities(self, task: Task, 
                                 available_agents: Optional[List[Agent]] = None) -> CapabilityAssessment:
        """Assess capability requirements and gaps for a task"""
        logger.info(f"Assessing capabilities for task {task.id}")
        
        # Identify required capabilities
        required_capabilities = self._identify_required_capabilities(task)
        
        # Get available capabilities
        available_capabilities = self._get_available_capabilities(available_agents)
        
        # Create assessment
        assessment = CapabilityAssessment(
            task_id=str(task.id),
            required_capabilities=required_capabilities,
            available_capabilities=available_capabilities
        )
        
        # Identify gaps
        assessment.gaps = self._identify_capability_gaps(
            required_capabilities, available_capabilities, task
        )
        
        # Calculate completeness score
        assessment.completeness_score = self._calculate_completeness_score(
            required_capabilities, available_capabilities
        )
        
        # Determine if task can be completed
        critical_gaps = [gap for gap in assessment.gaps if gap.severity == GapSeverity.CRITICAL]
        assessment.can_complete_task = len(critical_gaps) == 0
        
        # Generate recommendations
        assessment.recommended_actions = self._generate_recommendations(assessment)
        
        # Store assessment
        self.assessment_history.append(assessment)
        
        logger.info(f"Assessment complete: {len(assessment.gaps)} gaps found, "
                   f"completeness: {assessment.completeness_score:.2f}")
        
        return assessment
    
    def _identify_required_capabilities(self, task: Task) -> List[str]:
        """Identify required capabilities from task description"""
        required = []
        task_text = f"{task.title} {task.description or ''}".lower()
        
        for capability, patterns in self.capability_patterns.items():
            for pattern in patterns:
                if re.search(pattern, task_text):
                    required.append(capability)
                    break
        
        # Add capabilities from task input data if available
        if task.input_data:
            task_type = task.input_data.get('type', '').lower()
            if task_type in self.capability_patterns:
                if task_type not in required:
                    required.append(task_type)
        
        # If no specific capabilities identified, add general ones
        if not required:
            required.extend(['task_execution', 'basic_processing'])
        
        logger.debug(f"Identified required capabilities: {required}")
        return required
    
    def _get_available_capabilities(self, available_agents: Optional[List[Agent]] = None) -> List[str]:
        """Get capabilities available in the current system"""
        capabilities = set()
        
        # Get capabilities from available agents
        if available_agents:
            for agent in available_agents:
                if agent.capabilities:
                    capabilities.update(agent.capabilities)
        else:
            # Get capabilities from all registered agents
            # This would query the database for all agents
            pass
        
        # Get capabilities from installed plugins
        installed_plugins = self.plugin_registry.list_plugins(status="installed")
        for plugin in installed_plugins:
            for capability in plugin.capabilities:
                capabilities.add(capability.name)
        
        # Get capabilities from available templates
        templates = self.agent_factory.get_available_templates()
        for template in templates:
            capabilities.update(template.capabilities)
        
        return list(capabilities)
    
    def _identify_capability_gaps(self, required: List[str], available: List[str], 
                                  task: Task) -> List[CapabilityGap]:
        """Identify gaps between required and available capabilities"""
        gaps = []
        available_set = set(available)
        
        for capability in required:
            if capability not in available_set:
                gap = self._create_capability_gap(capability, task)
                gaps.append(gap)
        
        return gaps
    
    def _create_capability_gap(self, capability: str, task: Task) -> CapabilityGap:
        """Create a capability gap with suggestions"""
        gap = CapabilityGap(
            name=capability,
            description=f"Missing capability: {capability}",
            capability_type=self._classify_capability_type(capability),
            severity=self._assess_gap_severity(capability, task),
            required_for_task=str(task.id)
        )
        
        # Find alternatives
        gap.current_alternatives = self._find_capability_alternatives(capability)
        
        # Find suggested plugins
        gap.suggested_plugins = self._find_plugins_for_capability(capability)
        
        # Find suggested templates
        gap.suggested_templates = self._find_templates_for_capability(capability)
        
        # Calculate impact and effort
        gap.impact_score = self._calculate_impact_score(capability, task)
        gap.effort_to_resolve = self._estimate_resolution_effort(capability)
        
        return gap
    
    def _classify_capability_type(self, capability: str) -> CapabilityType:
        """Classify capability type"""
        core_capabilities = ['task_execution', 'basic_processing', 'error_handling']
        domain_capabilities = ['email_sending', 'data_analysis', 'file_processing']
        integration_capabilities = ['api_integration', 'database_operations', 'web_scraping']
        utility_capabilities = ['monitoring_alerting', 'workflow_automation']
        
        if capability in core_capabilities:
            return CapabilityType.CORE
        elif capability in domain_capabilities:
            return CapabilityType.DOMAIN_SPECIFIC
        elif capability in integration_capabilities:
            return CapabilityType.INTEGRATION
        elif capability in utility_capabilities:
            return CapabilityType.UTILITY
        else:
            return CapabilityType.ADVANCED
    
    def _assess_gap_severity(self, capability: str, task: Task) -> GapSeverity:
        """Assess severity of capability gap"""
        # Core capabilities are critical
        if self._classify_capability_type(capability) == CapabilityType.CORE:
            return GapSeverity.CRITICAL
        
        # Check if capability is explicitly mentioned in task
        task_text = f"{task.title} {task.description or ''}".lower()
        if capability.replace('_', ' ') in task_text:
            return GapSeverity.HIGH
        
        # Domain-specific capabilities are usually high priority
        if self._classify_capability_type(capability) == CapabilityType.DOMAIN_SPECIFIC:
            return GapSeverity.HIGH
        
        # Others are medium by default
        return GapSeverity.MEDIUM
    
    def _find_capability_alternatives(self, capability: str) -> List[str]:
        """Find alternative capabilities that might substitute"""
        alternatives_map = {
            'email_sending': ['notification_sending', 'message_delivery'],
            'data_analysis': ['basic_processing', 'report_generation'],
            'file_processing': ['basic_processing', 'data_handling'],
            'web_scraping': ['api_integration', 'data_extraction'],
            'image_processing': ['file_processing', 'data_analysis']
        }
        
        return alternatives_map.get(capability, [])
    
    def _find_plugins_for_capability(self, capability: str) -> List[str]:
        """Find plugins that provide the capability"""
        plugins = self.plugin_registry.find_plugins_by_capability(capability)
        return [plugin.name for plugin in plugins]
    
    def _find_templates_for_capability(self, capability: str) -> List[str]:
        """Find templates that provide the capability"""
        templates = self.agent_factory.get_available_templates()
        matching_templates = [
            template.name for template in templates
            if capability in template.capabilities
        ]
        return matching_templates
    
    def _calculate_impact_score(self, capability: str, task: Task) -> float:
        """Calculate impact score of missing capability"""
        base_score = 0.5
        
        # Higher impact for core capabilities
        if self._classify_capability_type(capability) == CapabilityType.CORE:
            base_score = 0.9
        elif self._classify_capability_type(capability) == CapabilityType.DOMAIN_SPECIFIC:
            base_score = 0.7
        
        # Increase score if capability is mentioned in task
        task_text = f"{task.title} {task.description or ''}".lower()
        if capability.replace('_', ' ') in task_text:
            base_score += 0.2
        
        return min(base_score, 1.0)
    
    def _estimate_resolution_effort(self, capability: str) -> str:
        """Estimate effort required to resolve capability gap"""
        # Check if plugins are available
        plugins = self._find_plugins_for_capability(capability)
        templates = self._find_templates_for_capability(capability)
        
        if plugins or templates:
            return "low"
        
        # Check capability type
        capability_type = self._classify_capability_type(capability)
        if capability_type in [CapabilityType.CORE, CapabilityType.UTILITY]:
            return "medium"
        else:
            return "high"
    
    def _calculate_completeness_score(self, required: List[str], available: List[str]) -> float:
        """Calculate capability completeness score"""
        if not required:
            return 1.0
        
        available_set = set(available)
        satisfied = sum(1 for cap in required if cap in available_set)
        
        return satisfied / len(required)
    
    def _generate_recommendations(self, assessment: CapabilityAssessment) -> List[str]:
        """Generate recommendations for addressing capability gaps"""
        recommendations = []
        
        # Critical gaps first
        critical_gaps = [gap for gap in assessment.gaps if gap.severity == GapSeverity.CRITICAL]
        if critical_gaps:
            recommendations.append("Address critical capability gaps immediately:")
            for gap in critical_gaps:
                if gap.suggested_plugins:
                    recommendations.append(f"  - Install plugin: {gap.suggested_plugins[0]} for {gap.name}")
                elif gap.suggested_templates:
                    recommendations.append(f"  - Use template: {gap.suggested_templates[0]} for {gap.name}")
                else:
                    recommendations.append(f"  - Develop custom solution for {gap.name}")
        
        # High priority gaps
        high_gaps = [gap for gap in assessment.gaps if gap.severity == GapSeverity.HIGH]
        if high_gaps:
            recommendations.append("Consider addressing high-priority gaps:")
            for gap in high_gaps[:3]:  # Limit to top 3
                if gap.suggested_plugins:
                    recommendations.append(f"  - Install plugin: {gap.suggested_plugins[0]} for {gap.name}")
        
        # General recommendations
        if assessment.completeness_score < 0.7:
            recommendations.append("System capability coverage is below 70% - consider capability expansion")
        
        if not assessment.can_complete_task:
            recommendations.append("Task cannot be completed with current capabilities - install required plugins")
        
        return recommendations
    
    def suggest_plugins_for_task(self, task: Task) -> List[Tuple[PluginMetadata, float]]:
        """Suggest plugins for a specific task with relevance scores"""
        assessment = self.assess_task_capabilities(task)
        suggestions = []
        
        for gap in assessment.gaps:
            for plugin_name in gap.suggested_plugins:
                plugin = self.plugin_registry.get_plugin(plugin_name)
                if plugin:
                    # Calculate relevance score
                    relevance = gap.impact_score * (1.0 if gap.severity == GapSeverity.CRITICAL else 0.8)
                    suggestions.append((plugin, relevance))
        
        # Sort by relevance score
        suggestions.sort(key=lambda x: x[1], reverse=True)
        
        return suggestions
    
    def get_system_capability_overview(self) -> Dict[str, Any]:
        """Get overview of system capabilities"""
        available_capabilities = self._get_available_capabilities()
        
        # Categorize capabilities
        by_type = {}
        for capability in available_capabilities:
            cap_type = self._classify_capability_type(capability)
            if cap_type.value not in by_type:
                by_type[cap_type.value] = []
            by_type[cap_type.value].append(capability)
        
        # Get gap statistics
        recent_assessments = self.assessment_history[-10:]  # Last 10 assessments
        common_gaps = {}
        for assessment in recent_assessments:
            for gap in assessment.gaps:
                if gap.name not in common_gaps:
                    common_gaps[gap.name] = 0
                common_gaps[gap.name] += 1
        
        return {
            'total_capabilities': len(available_capabilities),
            'capabilities_by_type': by_type,
            'common_gaps': dict(sorted(common_gaps.items(), key=lambda x: x[1], reverse=True)[:5]),
            'recent_assessments': len(recent_assessments),
            'average_completeness': sum(a.completeness_score for a in recent_assessments) / len(recent_assessments) if recent_assessments else 0.0
        }
    
    def get_assessment_history(self, task_id: Optional[str] = None) -> List[CapabilityAssessment]:
        """Get assessment history with optional filtering"""
        if task_id:
            return [a for a in self.assessment_history if a.task_id == task_id]
        return self.assessment_history.copy()
