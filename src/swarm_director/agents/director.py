"""
Director agent implementation for SwarmDirector
The DirectorAgent is the main orchestrator that routes tasks to appropriate department agents
based on intent classification and manages the overall workflow.
"""

import json
import logging
import threading
from typing import Dict, List, Any, Optional, Union, Tuple
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from enum import Enum
import hashlib
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
from collections import defaultdict

from .supervisor_agent import SupervisorAgent
from ..models.task import Task, TaskStatus, TaskPriority, TaskType
from ..models.agent import Agent, AgentType, AgentStatus
from ..utils.logging import log_agent_action

# Import for LLM-based classification
try:
    import openai
    import anthropic
    HAS_LLM_SUPPORT = True
except ImportError:
    HAS_LLM_SUPPORT = False

# Import for embeddings-based similarity
try:
    import numpy as np
    from sklearn.metrics.pairwise import cosine_similarity
    HAS_EMBEDDING_SUPPORT = True
except ImportError:
    HAS_EMBEDDING_SUPPORT = False

logger = logging.getLogger(__name__)

class DirectorState(Enum):
    """Enumeration for director agent states"""
    INITIALIZING = "initializing"
    ACTIVE = "active"
    BUSY = "busy"
    MAINTENANCE = "maintenance"
    ERROR = "error"

class RoutingStrategy(Enum):
    """Enumeration for routing strategies"""
    SINGLE_AGENT = "single_agent"
    PARALLEL_AGENTS = "parallel_agents"
    SEQUENTIAL_AGENTS = "sequential_agents"
    SCATTER_GATHER = "scatter_gather"
    LOAD_BALANCED = "load_balanced"

class AgentSelectionCriteria(Enum):
    """Criteria for selecting agents"""
    AVAILABILITY = "availability"
    PERFORMANCE = "performance"
    WORKLOAD = "workload"
    EXPERTISE = "expertise"
    RANDOM = "random"

@dataclass
class RoutingDecision:
    """Represents a routing decision with metadata"""
    strategy: RoutingStrategy
    selected_agents: List[str]
    confidence: float
    reasoning: str
    expected_execution_time: Optional[float] = None
    fallback_agents: Optional[List[str]] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class TaskExecutionResult:
    """Result from task execution with detailed metadata"""
    agent_name: str
    department: str
    status: str
    result: Dict[str, Any]
    execution_time: float
    errors: Optional[List[str]] = None
    warnings: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None

@dataclass
class AggregatedResult:
    """Aggregated result from multiple agents"""
    primary_result: Dict[str, Any]
    individual_results: List[TaskExecutionResult]
    aggregation_method: str
    consensus_score: Optional[float] = None
    conflicts_detected: bool = False
    execution_summary: Optional[Dict[str, Any]] = None

@dataclass
class DirectorConfig:
    """Configuration class for DirectorAgent"""
    max_concurrent_tasks: int = 10
    enable_llm_classification: bool = False
    fallback_department: str = 'coordination'
    task_timeout_minutes: int = 30
    enable_auto_retry: bool = True
    max_retries: int = 3
    routing_confidence_threshold: float = 0.7
    # New routing configuration
    enable_parallel_execution: bool = True
    max_parallel_agents: int = 3
    parallel_timeout_seconds: int = 120
    enable_load_balancing: bool = True
    agent_selection_criteria: AgentSelectionCriteria = AgentSelectionCriteria.PERFORMANCE
    enable_result_aggregation: bool = True
    consensus_threshold: float = 0.75

@dataclass
class DirectorMetrics:
    """Metrics tracking for DirectorAgent"""
    tasks_processed: int = 0
    successful_routes: int = 0
    failed_routes: int = 0
    direct_handled: int = 0
    average_response_time: float = 0.0
    department_routing_counts: Dict[str, int] = field(default_factory=dict)
    error_counts: Dict[str, int] = field(default_factory=dict)
    # New parallel execution metrics
    parallel_executions: int = 0
    aggregated_results: int = 0
    agent_performance_scores: Dict[str, float] = field(default_factory=dict)
    routing_strategy_usage: Dict[str, int] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary"""
        return {
            'tasks_processed': self.tasks_processed,
            'successful_routes': self.successful_routes,
            'failed_routes': self.failed_routes,
            'direct_handled': self.direct_handled,
            'average_response_time': self.average_response_time,
            'department_routing_counts': dict(self.department_routing_counts),
            'error_counts': dict(self.error_counts),
            'parallel_executions': self.parallel_executions,
            'aggregated_results': self.aggregated_results,
            'agent_performance_scores': dict(self.agent_performance_scores),
            'routing_strategy_usage': dict(self.routing_strategy_usage)
        }

@dataclass 
class IntentExample:
    """Training example for intent classification"""
    text: str
    department: str
    confidence: float = 1.0
    source: str = "manual"  # manual, feedback, synthetic
    created_at: datetime = field(default_factory=datetime.utcnow)

@dataclass
class ClassificationFeedback:
    """Feedback tracking for classification accuracy"""
    task_id: int
    predicted_intent: str
    predicted_confidence: float
    actual_intent: Optional[str] = None
    correction_source: str = "manual"  # manual, outcome_based, user_feedback
    timestamp: datetime = field(default_factory=datetime.utcnow)
    classification_method: str = "keyword"  # keyword, llm, hybrid

@dataclass  
class ClassificationCache:
    """Cache for classification results to improve performance"""
    text_hash: str
    intent: str
    confidence: float
    method: str
    timestamp: datetime
    hit_count: int = 1
    
    def is_valid(self, max_age_hours: int = 24) -> bool:
        """Check if cache entry is still valid"""
        age = datetime.utcnow() - self.timestamp
        return age.total_seconds() < (max_age_hours * 3600)

class IntentDatasetManager:
    """Manages training datasets for intent classification"""
    
    def __init__(self):
        self.examples: Dict[str, List[IntentExample]] = {
            'communications': [],
            'analysis': [], 
            'automation': [],
            'coordination': []
        }
        self._load_default_training_data()
    
    def _load_default_training_data(self):
        """Load curated training examples for each department"""
        
        # Communications examples
        comm_examples = [
            "Send email to team about project status",
            "Draft newsletter for quarterly updates", 
            "Write announcement for new policy",
            "Compose follow-up message to client",
            "Create notification about system maintenance",
            "Send reminder about deadline to stakeholders",
            "Draft response to customer inquiry",
            "Write memo about process changes",
            "Compose welcome message for new employees",
            "Send alert about security incident",
            "Draft thank you letter to partners",
            "Create broadcast message for all users",
            "Write correspondence for legal matters",
            "Compose outreach email for marketing",
            "Send status update to management",
            "Draft invitation for company event",
            "Write press release for product launch",
            "Compose apology letter for service disruption",
            "Send survey request to customers",
            "Draft instructions for new procedure"
        ]
        
        # Analysis examples  
        analysis_examples = [
            "Analyze sales performance for Q3",
            "Review customer feedback data",
            "Evaluate marketing campaign effectiveness",
            "Assess project risk factors",
            "Examine user behavior patterns",
            "Study market trends and competitors", 
            "Investigate system performance issues",
            "Audit financial records for compliance",
            "Research industry best practices",
            "Compare product features with alternatives",
            "Inspect code quality and security",
            "Evaluate employee satisfaction metrics",
            "Analyze website traffic patterns",
            "Review budget allocation efficiency",
            "Assess training program outcomes",
            "Study customer retention rates",
            "Investigate operational bottlenecks",
            "Examine supply chain performance",
            "Analyze social media engagement",
            "Evaluate technology stack options"
        ]
        
        # Automation examples
        automation_examples = [
            "Automate daily report generation",
            "Schedule weekly data backups",
            "Set up recurring invoice processing",
            "Create workflow for approval processes",
            "Automate user onboarding tasks",
            "Schedule maintenance window alerts",
            "Set up monitoring for system health",
            "Automate lead qualification process",
            "Create batch processing for orders",
            "Schedule social media posts",
            "Set up automated testing pipeline",
            "Automate inventory level monitoring",
            "Create recurring task assignments",
            "Schedule performance review reminders",
            "Automate log file cleanup",
            "Set up alert triggers for errors",
            "Create systematic backup procedures",
            "Automate compliance reporting",
            "Schedule routine security scans",
            "Set up integration between systems"
        ]
        
        # Coordination examples
        coordination_examples = [
            "Coordinate project team meeting",
            "Organize cross-department collaboration",
            "Plan product launch timeline",
            "Manage stakeholder communications",
            "Oversee budget planning process",
            "Delegate tasks to team members",
            "Track project milestone progress",
            "Supervise quality assurance testing",
            "Monitor team workload distribution",
            "Plan resource allocation strategy",
            "Organize training session schedule",
            "Coordinate vendor negotiations",
            "Manage change request process",
            "Oversee system deployment plan",
            "Coordinate emergency response plan",
            "Plan capacity expansion strategy",
            "Manage customer escalation process",
            "Coordinate security audit timeline",
            "Organize knowledge sharing sessions",
            "Plan succession planning initiative"
        ]
        
        # Convert to IntentExample objects
        for text in comm_examples:
            self.examples['communications'].append(
                IntentExample(text=text, department='communications', source='curated')
            )
            
        for text in analysis_examples:
            self.examples['analysis'].append(
                IntentExample(text=text, department='analysis', source='curated')
            )
            
        for text in automation_examples:
            self.examples['automation'].append(
                IntentExample(text=text, department='automation', source='curated')
            )
            
        for text in coordination_examples:
            self.examples['coordination'].append(
                IntentExample(text=text, department='coordination', source='curated')
            )
    
    def add_example(self, example: IntentExample) -> bool:
        """Add a training example"""
        try:
            if example.department in self.examples:
                self.examples[example.department].append(example)
                return True
            return False
        except Exception:
            return False
    
    def get_examples(self, department: Optional[str] = None) -> Union[List[IntentExample], Dict[str, List[IntentExample]]]:
        """Get training examples for specified department or all departments"""
        if department:
            return self.examples.get(department, [])
        return self.examples
    
    def get_training_prompt(self, include_examples: int = 5) -> str:
        """Generate training prompt for LLM classification"""
        prompt = """You are an expert at classifying user requests into these departments:

1. COMMUNICATIONS: Email, messaging, notifications, announcements, correspondence
2. ANALYSIS: Data analysis, research, evaluation, reporting, assessment  
3. AUTOMATION: Workflow automation, scheduling, scripting, system integration
4. COORDINATION: Project management, planning, delegation, oversight, organization

Here are some examples:

"""
        
        # Add examples from each department
        for dept, examples in self.examples.items():
            prompt += f"\n{dept.upper()} examples:\n"
            # Take up to include_examples from each department
            selected_examples = examples[:include_examples]
            for example in selected_examples:
                prompt += f"- {example.text}\n"
        
        prompt += """
Please classify the following request and provide a confidence score (0.0-1.0):
Format your response as: DEPARTMENT|CONFIDENCE

Request: """
        
        return prompt

class DirectorAgent(SupervisorAgent):
    """
    Enhanced Director agent that routes tasks to appropriate department agents
    based on intent classification and manages the overall workflow with comprehensive
    error handling, state management, and performance monitoring.
    """
    
    def __init__(self, db_agent: Agent, config: Optional[DirectorConfig] = None):
        """
        Initialize DirectorAgent with enhanced classification and state management
        """
        super().__init__(db_agent)
        
        # Configuration and state management
        self.config = config or DirectorConfig()
        self._state = DirectorState.INITIALIZING
        self._lock = threading.RLock()  # Thread safety for concurrent operations
        self._active_tasks: Dict[int, Task] = {}
        self.created_at = datetime.utcnow()
        self.last_heartbeat = datetime.utcnow()
        
        # Enhanced classification system
        self.dataset_manager = IntentDatasetManager()
        self.classification_cache: Dict[str, ClassificationCache] = {}
        self.feedback_history: List[ClassificationFeedback] = []
        
        # Routing infrastructure for parallel execution and advanced strategies
        self.thread_pool = ThreadPoolExecutor(max_workers=self.config.max_parallel_agents)
        self.routing_decisions: List[RoutingDecision] = []
        self.agent_workload: Dict[str, int] = defaultdict(int)
        
        # Metrics and performance tracking  
        self.metrics = DirectorMetrics()
        
        # Initialize core components
        try:
            self.intent_keywords = self._initialize_intent_keywords()
            self.department_agents = {}  # Initialize as empty dict first
            self._initialize_department_agents()  # Then populate it
            self.routing_stats = self._initialize_routing_stats()
            
            # Set state to active after successful initialization
            self._state = DirectorState.ACTIVE
            log_agent_action(self.name, "DirectorAgent initialized successfully")
            
        except Exception as e:
            self._state = DirectorState.ERROR
            logger.error(f"Failed to initialize DirectorAgent: {e}")
            raise

    def _initialize_department_agents(self):
        """Initialize and register department agents with enhanced error handling"""
        try:
            # Import here to avoid circular imports
            from .communications_dept import CommunicationsDept

            # Create or find communications department agent
            comm_dept_db = self._get_or_create_department_agent(
                name="CommunicationsDept",
                description="Communications department for message drafting and email workflows"
            )

            # Create and register communications department
            comm_dept = CommunicationsDept(comm_dept_db)
            self.register_department_agent('communications', comm_dept)

            log_agent_action(self.name, "Department agents initialized successfully")

        except ImportError as e:
            logger.warning(f"Could not import CommunicationsDept: {e}")
            log_agent_action(self.name, f"Warning: CommunicationsDept not available: {e}")
        except Exception as e:
            logger.error(f"Error initializing department agents: {e}")
            log_agent_action(self.name, f"Error: Could not initialize department agents: {e}")
            # Don't re-raise - continue without department agents

    def _get_or_create_department_agent(self, name: str, description: str) -> Agent:
        """Get existing department agent or create new one with validation"""
        try:
            from ..models.agent import AgentType, AgentStatus

            # Validate inputs
            if not name or not isinstance(name, str):
                raise ValueError("Agent name must be a non-empty string")
            if not description or not isinstance(description, str):
                raise ValueError("Agent description must be a non-empty string")

            agent = Agent.query.filter_by(name=name).first()
            if not agent:
                agent = Agent(
                    name=name,
                    agent_type=AgentType.SUPERVISOR,
                    status=AgentStatus.ACTIVE,
                    description=description,
                    parent_id=self.db_agent.id
                )
                agent.save()
                log_agent_action(self.name, f"Created new department agent: {name}")
            else:
                log_agent_action(self.name, f"Found existing department agent: {name}")
            
            return agent
            
        except Exception as e:
            logger.error(f"Error creating/getting department agent {name}: {e}")
            raise

    def _initialize_intent_keywords(self) -> Dict[str, List[str]]:
        """Initialize keyword mappings for intent classification with enhanced categories"""
        return {
            'communications': [
                'email', 'message', 'communication', 'send', 'draft', 'write',
                'compose', 'letter', 'memo', 'notification', 'announce',
                'contact', 'reply', 'response', 'correspondence', 'outreach',
                'newsletter', 'broadcast', 'alert', 'reminder'
            ],
            'analysis': [
                'analyze', 'analysis', 'review', 'evaluate', 'assess', 'examine', 'study',
                'research', 'investigate', 'compare', 'audit', 'inspect',
                'critique', 'feedback', 'opinion', 'recommendation', 'report',
                'metrics', 'performance', 'statistics', 'data'
            ],
            'automation': [
                'automate', 'schedule', 'trigger', 'batch', 'process',
                'workflow', 'pipeline', 'routine', 'recurring', 'systematic',
                'script', 'tool', 'integration', 'api'
            ],
            'coordination': [
                'coordinate', 'manage', 'organize', 'plan', 'delegate',
                'assign', 'supervise', 'oversee', 'monitor', 'track',
                'schedule', 'timeline', 'project', 'meeting', 'collaboration'
            ]
        }
    
    def _initialize_routing_stats(self) -> Dict[str, Any]:
        """Initialize legacy routing statistics for backward compatibility"""
        return {
            'total_routed': 0,
            'successful_routes': 0,
            'failed_routes': 0,
            'department_counts': {}
        }

    def execute_task(self, task: Task) -> Dict[str, Any]:
        """
        Execute a task with comprehensive error handling, state management, and metrics tracking
        """
        start_time = datetime.utcnow()
        task_id = task.id
        
        # Validate task and agent state
        validation_result = self._validate_task_execution(task)
        if not validation_result['valid']:
            return validation_result
            
        with self._lock:
            # Check concurrent task limit
            if len(self._active_tasks) >= self.config.max_concurrent_tasks:
                error_msg = f"Maximum concurrent tasks ({self.config.max_concurrent_tasks}) exceeded"
                log_agent_action(self.name, error_msg)
                return self._create_error_response(error_msg, task_id)
            
            # Add to active tasks
            self._active_tasks[task_id] = task
            self._state = DirectorState.BUSY
            
        log_agent_action(self.name, f"Processing task: {task.title} (ID: {task_id})")
        
        try:
            # Classify the intent
            intent, confidence = self.classify_intent_with_confidence(task)
            
            # Route to appropriate department
            result = self.route_task(task, intent, confidence)
            
            # Update metrics
            self._update_metrics(intent, result['status'] == 'success', start_time)
            
            # Update legacy routing statistics for backward compatibility
            self._update_routing_stats(intent, result['status'] == 'success')
            
            return result
            
        except Exception as e:
            error_msg = f"Error processing task {task_id}: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_agent_action(self.name, error_msg)
            
            # Update metrics for error
            self._update_metrics('error', False, start_time)
            self._update_routing_stats('error', False)
            
            return self._create_error_response(error_msg, task_id)
            
        finally:
            with self._lock:
                # Remove from active tasks
                self._active_tasks.pop(task_id, None)
                if not self._active_tasks:
                    self._state = DirectorState.ACTIVE

    def _validate_task_execution(self, task: Task) -> Dict[str, Any]:
        """Comprehensive task and state validation"""
        # Check if agent is in proper state
        if self._state == DirectorState.ERROR:
            return self._create_error_response("DirectorAgent is in error state", task.id)
        
        if self._state == DirectorState.MAINTENANCE:
            return self._create_error_response("DirectorAgent is in maintenance mode", task.id)
        
        # Validate task object
        if not task:
            return self._create_error_response("Task object is None", None)
        
        if not hasattr(task, 'id') or task.id is None:
            return self._create_error_response("Task has no valid ID", None)
        
        if not hasattr(task, 'title') or not task.title:
            return self._create_error_response("Task has no title", task.id)
        
        # Check task status
        if task.status in [TaskStatus.COMPLETED, TaskStatus.FAILED, TaskStatus.CANCELLED]:
            return self._create_error_response(f"Task is already {task.status.value}", task.id)
        
        return {'valid': True}

    def _create_error_response(self, error_msg: str, task_id: Optional[int]) -> Dict[str, Any]:
        """Create standardized error response"""
        return {
            "status": "error",
            "error": error_msg,
            "task_id": task_id,
            "timestamp": datetime.utcnow().isoformat(),
            "agent": self.name
        }

    def _create_success_response(self, routed_to: str, agent_name: str, 
                                task_id: int, result: Dict[str, Any]) -> Dict[str, Any]:
        """Create standardized success response"""
        return {
            "status": "success",
            "routed_to": routed_to,
            "agent_name": agent_name,
            "task_id": task_id,
            "result": result,
            "timestamp": datetime.utcnow().isoformat(),
            "director_agent": self.name
        }

    def classify_intent_with_confidence(self, task: Task) -> tuple[str, float]:
        """
        Enhanced intent classification with confidence scoring
        Returns tuple of (intent, confidence_score)
        """
        try:
            task_text = self._extract_task_text(task)
            
            if self.config.enable_llm_classification:
                # Future: implement LLM-based classification
                return self._classify_intent_llm(task_text)
            else:
                return self._classify_intent_keyword(task_text)
                
        except Exception as e:
            logger.error(f"Error in intent classification: {e}")
            # Fallback to default department
            return self.config.fallback_department, 0.0

    def _extract_task_text(self, task: Task) -> str:
        """Extract and normalize text from task for classification"""
        text_parts = []
        
        # Add title
        if hasattr(task, 'title') and task.title:
            text_parts.append(task.title)
        
        # Add description
        if hasattr(task, 'description') and task.description:
            text_parts.append(task.description)
        
        # Add input_data type if available
        if hasattr(task, 'input_data') and task.input_data:
            if isinstance(task.input_data, dict) and 'type' in task.input_data:
                text_parts.append(task.input_data['type'])
        
        return " ".join(text_parts).lower()

    def _classify_intent_keyword(self, task_text: str) -> tuple[str, float]:
        """
        Classify intent using keyword matching with confidence scoring
        """
        intent_scores = {}
        total_keywords_matched = 0
        
        # Score each department based on keyword matches
        for department, keywords in self.intent_keywords.items():
            score = 0
            for keyword in keywords:
                if keyword in task_text:
                    score += 1
                    total_keywords_matched += 1
            intent_scores[department] = score
        
        # Find the department with the highest score
        best_intent = max(intent_scores.items(), key=lambda x: x[1])
        
        # Calculate confidence score
        if best_intent[1] == 0:
            # No keywords matched
            intent = self.config.fallback_department
            confidence = 0.0
        else:
            intent = best_intent[0]
            # Confidence based on score relative to total matches
            confidence = min(1.0, best_intent[1] / max(1, total_keywords_matched))
        
        log_agent_action(self.name, 
                        f"Classified intent as '{intent}' (score: {best_intent[1]}, confidence: {confidence:.2f})")
        return intent, confidence

    def _classify_intent_llm(self, task_text: str) -> tuple[str, float]:
        """
        LLM-based intent classification with caching and multiple provider support
        """
        # Check cache first
        text_hash = hashlib.md5(task_text.encode()).hexdigest()
        if text_hash in self.classification_cache:
            cache_entry = self.classification_cache[text_hash]
            if cache_entry.is_valid():
                cache_entry.hit_count += 1
                log_agent_action(self.name, f"Using cached LLM classification for task")
                return cache_entry.intent, cache_entry.confidence
        
        # Check if LLM support is available
        if not HAS_LLM_SUPPORT:
            logger.warning("LLM libraries not available, falling back to keyword classification")
            return self._classify_intent_keyword(task_text)
        
        try:
            # Get training prompt
            prompt = self.dataset_manager.get_training_prompt(include_examples=3)
            full_prompt = prompt + task_text
            
            # Try different LLM providers in order of preference
            result = None
            providers_tried = []
            
            # Try OpenAI first
            try:
                from flask import current_app
                api_key = current_app.config.get('OPENAI_API_KEY')
                if api_key:
                    result = self._classify_with_openai(full_prompt, api_key)
                    providers_tried.append('openai')
            except Exception as e:
                logger.debug(f"OpenAI classification failed: {e}")
            
            # Try Anthropic if OpenAI failed
            if not result:
                try:
                    from flask import current_app
                    api_key = current_app.config.get('ANTHROPIC_API_KEY')
                    if api_key:
                        result = self._classify_with_anthropic(full_prompt, api_key)
                        providers_tried.append('anthropic')
                except Exception as e:
                    logger.debug(f"Anthropic classification failed: {e}")
            
            # Parse result
            if result:
                intent, confidence = self._parse_llm_response(result)
                
                # Validate and normalize
                if intent not in ['communications', 'analysis', 'automation', 'coordination']:
                    logger.warning(f"LLM returned invalid intent '{intent}', falling back to keyword")
                    return self._classify_intent_keyword(task_text)
                
                # Cache the result
                cache_entry = ClassificationCache(
                    text_hash=text_hash,
                    intent=intent,
                    confidence=confidence,
                    method='llm',
                    timestamp=datetime.utcnow()
                )
                self.classification_cache[text_hash] = cache_entry
                
                log_agent_action(self.name, 
                               f"LLM classified intent as '{intent}' (confidence: {confidence:.2f}, providers: {providers_tried})")
                return intent, confidence
            
        except Exception as e:
            logger.error(f"LLM classification error: {e}")
        
        # Fallback to keyword classification
        logger.info("LLM classification failed, falling back to keyword classification")
        return self._classify_intent_keyword(task_text)
    
    def _classify_with_openai(self, prompt: str, api_key: str) -> Optional[str]:
        """Classify using OpenAI API"""
        try:
            client = openai.OpenAI(api_key=api_key)
            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": "You are an expert task classifier. Respond with only DEPARTMENT|CONFIDENCE format."},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=50,
                temperature=0.1
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.debug(f"OpenAI API error: {e}")
            return None
    
    def _classify_with_anthropic(self, prompt: str, api_key: str) -> Optional[str]:
        """Classify using Anthropic API"""
        try:
            client = anthropic.Anthropic(api_key=api_key)
            response = client.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=50,
                temperature=0.1,
                messages=[
                    {"role": "user", "content": f"You are an expert task classifier. Respond with only DEPARTMENT|CONFIDENCE format.\n\n{prompt}"}
                ]
            )
            return response.content[0].text.strip()
        except Exception as e:
            logger.debug(f"Anthropic API error: {e}")
            return None
    
    def _parse_llm_response(self, response: str) -> tuple[str, float]:
        """Parse LLM response in DEPARTMENT|CONFIDENCE format"""
        try:
            parts = response.strip().split('|')
            if len(parts) >= 2:
                department = parts[0].lower().strip()
                confidence = float(parts[1].strip())
                confidence = max(0.0, min(1.0, confidence))  # Clamp to [0,1]
                return department, confidence
        except Exception as e:
            logger.debug(f"Error parsing LLM response '{response}': {e}")
        
        # Fallback parsing
        response_lower = response.lower()
        for dept in ['communications', 'analysis', 'automation', 'coordination']:
            if dept in response_lower:
                return dept, 0.7  # Default confidence for fallback parsing
        
        return self.config.fallback_department, 0.0

    # Keep the original classify_intent method for backward compatibility
    def classify_intent(self, task: Task) -> str:
        """Legacy method for backward compatibility"""
        intent, _ = self.classify_intent_with_confidence(task)
        return intent

    def route_task(self, task: Task, intent: str, confidence: float = 1.0) -> Dict[str, Any]:
        """
        Enhanced task routing with confidence-based decision making
        """
        try:
            # Check confidence threshold
            if confidence < self.config.routing_confidence_threshold:
                log_agent_action(self.name, 
                               f"Low confidence ({confidence:.2f}) for routing, using fallback")
                intent = self.config.fallback_department
            
            # Check if we have an agent for this department
            if intent in self.department_agents:
                agent = self.department_agents[intent]
                
                # Check if the agent is available
                if agent.is_available():
                    return self._execute_through_agent(task, intent, agent)
                else:
                    # Agent is not available, handle with retry or fallback
                    return self._handle_unavailable_agent(task, intent)
            else:
                # No agent available for this department, handle directly
                return self._handle_directly(task, intent)
                
        except Exception as e:
            error_msg = f"Error in task routing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_agent_action(self.name, error_msg)
            return self._create_error_response(error_msg, task.id)

    def _execute_through_agent(self, task: Task, intent: str, agent) -> Dict[str, Any]:
        """Execute task through department agent with enhanced error handling"""
        try:
            # Assign the task to the agent
            task.assign_to_agent(agent.db_agent)
            
            # Execute the task through the agent
            result = agent.execute_task(task)
            
            log_agent_action(self.name, f"Successfully routed task {task.id} to {intent} department")
            
            return self._create_success_response(intent, agent.name, task.id, result)
            
        except Exception as e:
            error_msg = f"Error executing task through {intent} agent: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_agent_action(self.name, error_msg)
            
            # Attempt retry if configured
            if self.config.enable_auto_retry:
                return self._retry_task_execution(task, intent, agent)
            
            return {
                "status": "execution_error",
                "department": intent,
                "error": error_msg,
                "task_id": task.id,
                "timestamp": datetime.utcnow().isoformat()
            }

    def _retry_task_execution(self, task: Task, intent: str, agent, 
                             retry_count: int = 0) -> Dict[str, Any]:
        """Retry task execution with exponential backoff"""
        if retry_count >= self.config.max_retries:
            error_msg = f"Max retries ({self.config.max_retries}) exceeded for task {task.id}"
            log_agent_action(self.name, error_msg)
            return self._create_error_response(error_msg, task.id)
        
        try:
            # Simple retry without backoff for now
            log_agent_action(self.name, f"Retrying task {task.id} (attempt {retry_count + 1})")
            result = agent.execute_task(task)
            
            log_agent_action(self.name, f"Task {task.id} succeeded on retry {retry_count + 1}")
            return self._create_success_response(intent, agent.name, task.id, result)
            
        except Exception as e:
            return self._retry_task_execution(task, intent, agent, retry_count + 1)

    def _handle_unavailable_agent(self, task: Task, department: str) -> Dict[str, Any]:
        """Enhanced handling for unavailable agents with fallback strategies"""
        log_agent_action(self.name, f"Department agent '{department}' is unavailable")
        
        # Strategy 1: Try to find an alternative agent in the same domain
        alternative_agent = self._find_alternative_agent(department)
        if alternative_agent:
            log_agent_action(self.name, f"Using alternative agent for {department}")
            return self._execute_through_agent(task, department, alternative_agent)
        
        # Strategy 2: Check if we can delegate to a parent or sibling agent
        if department != self.config.fallback_department:
            log_agent_action(self.name, f"Trying fallback department: {self.config.fallback_department}")
            return self.route_task(task, self.config.fallback_department, 1.0)
        
        # Strategy 3: Handle directly as last resort
        log_agent_action(self.name, "No alternatives available, handling directly")
        return self._handle_directly(task, department)

    def _find_alternative_agent(self, department: str) -> Optional[object]:
        """Find alternative agent for the given department"""
        # Simple implementation - in production this could be more sophisticated
        # For now, return None (no alternatives available)
        return None

    def _handle_directly(self, task: Task, intended_department: str) -> Dict[str, Any]:
        """Enhanced direct task handling with comprehensive processing"""
        log_agent_action(self.name, f"Handling task directly (intended for {intended_department})")
        
        try:
            # Update task status
            task.status = TaskStatus.IN_PROGRESS
            task.save()
            
            # Process based on intended department
            if intended_department == 'communications':
                result = self._handle_communication_task_directly(task)
            elif intended_department == 'analysis':
                result = self._handle_analysis_task_directly(task)
            elif intended_department == 'automation':
                result = self._handle_automation_task_directly(task)
            else:
                result = self._handle_generic_task_directly(task, intended_department)
            
            # Mark task as completed
            task.complete_task(output_data=result)
            
            # Update metrics
            with self._lock:
                self.metrics.direct_handled += 1
            
            return {
                "status": "handled_directly",
                "department": intended_department,
                "task_id": task.id,
                "result": result,
                "timestamp": datetime.utcnow().isoformat(),
                "handler": self.name
            }
            
        except Exception as e:
            error_msg = f"Error handling task directly: {str(e)}"
            logger.error(error_msg, exc_info=True)
            task.fail_task(error_msg)
            return self._create_error_response(error_msg, task.id)

    def _handle_communication_task_directly(self, task: Task) -> Dict[str, Any]:
        """Direct handling for communication tasks"""
        return {
            "message": "Communication task processed by DirectorAgent",
            "method": "direct_communication_handling",
            "recommendations": [
                "Task requires human review for communication content",
                "Consider setting up CommunicationsDept agent for better handling"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_analysis_task_directly(self, task: Task) -> Dict[str, Any]:
        """Direct handling for analysis tasks"""
        return {
            "message": "Analysis task processed by DirectorAgent",
            "method": "direct_analysis_handling",
            "recommendations": [
                "Basic analysis completed",
                "Consider specialized analysis agents for complex tasks"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_automation_task_directly(self, task: Task) -> Dict[str, Any]:
        """Direct handling for automation tasks"""
        return {
            "message": "Automation task processed by DirectorAgent",
            "method": "direct_automation_handling",
            "recommendations": [
                "Automation task scheduled for future implementation",
                "Consider dedicated automation agents for complex workflows"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    def _handle_generic_task_directly(self, task: Task, department: str) -> Dict[str, Any]:
        """Generic direct task handling"""
        return {
            "message": f"Generic task for {department} processed by DirectorAgent",
            "method": "direct_generic_handling",
            "intended_department": department,
            "recommendations": [
                f"Task completed with basic {department} handling",
                f"Consider implementing specialized {department} agent"
            ],
            "timestamp": datetime.utcnow().isoformat()
        }

    def _update_metrics(self, department: str, success: bool, start_time: datetime):
        """Update comprehensive metrics"""
        with self._lock:
            self.metrics.tasks_processed += 1
            
            if success:
                self.metrics.successful_routes += 1
            else:
                self.metrics.failed_routes += 1
                # Track error types
                self.metrics.error_counts[department] = self.metrics.error_counts.get(department, 0) + 1
            
            # Update department routing counts
            if department != 'error':
                self.metrics.department_routing_counts[department] = (
                    self.metrics.department_routing_counts.get(department, 0) + 1
                )
            
            # Calculate response time
            response_time = (datetime.utcnow() - start_time).total_seconds()
            
            # Update running average
            if self.metrics.tasks_processed == 1:
                self.metrics.average_response_time = response_time
            else:
                self.metrics.average_response_time = (
                    (self.metrics.average_response_time * (self.metrics.tasks_processed - 1) + response_time) 
                    / self.metrics.tasks_processed
                )

    def register_department_agent(self, department: str, agent):
        """Register a department agent for routing"""
        self.department_agents[department] = agent
        log_agent_action(self.name, f"Registered {department} department agent: {agent.name}")
        
        # Initialize stats for this department
        if department not in self.routing_stats['department_counts']:
            self.routing_stats['department_counts'][department] = 0
    
    def unregister_department_agent(self, department: str):
        """Unregister a department agent"""
        if department in self.department_agents:
            agent_name = self.department_agents[department].name
            del self.department_agents[department]
            log_agent_action(self.name, f"Unregistered {department} department agent: {agent_name}")
    
    def _update_routing_stats(self, department: str, success: bool):
        """Update routing statistics"""
        self.routing_stats['total_routed'] += 1
        
        if success:
            self.routing_stats['successful_routes'] += 1
        else:
            self.routing_stats['failed_routes'] += 1
        
        if department in self.routing_stats['department_counts']:
            self.routing_stats['department_counts'][department] += 1
    
    def get_routing_stats(self) -> Dict[str, Any]:
        """Get routing statistics"""
        return {
            **self.routing_stats,
            'success_rate': (
                self.routing_stats['successful_routes'] / 
                max(1, self.routing_stats['total_routed'])
            ) * 100,
            'registered_departments': list(self.department_agents.keys())
        }
    
    def can_handle_task(self, task: Task) -> bool:
        """Director agent can handle any task by routing or direct handling"""
        return True
    
    def get_department_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered department agents"""
        status = {}
        
        for dept, agent in self.department_agents.items():
            status[dept] = {
                'name': agent.name,
                'status': agent.status.value,
                'available': agent.is_available(),
                'active_tasks': len(agent.get_assigned_tasks()),
                'performance': agent.get_performance_metrics()
            }
        
        return status 

    # Enhanced state and configuration management methods
    def get_state(self) -> DirectorState:
        """Get current director state"""
        return self._state

    def set_state(self, new_state: DirectorState) -> bool:
        """Set director state with validation"""
        try:
            with self._lock:
                old_state = self._state
                self._state = new_state
                log_agent_action(self.name, f"State changed from {old_state.value} to {new_state.value}")
                return True
        except Exception as e:
            logger.error(f"Error setting state: {e}")
            return False

    def enter_maintenance_mode(self) -> bool:
        """Enter maintenance mode - stops accepting new tasks"""
        if self._state == DirectorState.ERROR:
            return False
        
        # Wait for active tasks to complete or timeout
        timeout_seconds = 30
        start_time = datetime.utcnow()
        
        while self._active_tasks and (datetime.utcnow() - start_time).total_seconds() < timeout_seconds:
            # Brief wait for tasks to complete
            time.sleep(0.1)
        
        return self.set_state(DirectorState.MAINTENANCE)

    def exit_maintenance_mode(self) -> bool:
        """Exit maintenance mode and return to active state"""
        if self._state == DirectorState.MAINTENANCE:
            return self.set_state(DirectorState.ACTIVE)
        return False

    def update_config(self, new_config: DirectorConfig) -> bool:
        """Update director configuration"""
        try:
            with self._lock:
                old_config = self.config
                self.config = new_config
                log_agent_action(self.name, "Configuration updated successfully")
                return True
        except Exception as e:
            logger.error(f"Error updating configuration: {e}")
            return False

    def get_health_status(self) -> Dict[str, Any]:
        """Get comprehensive health status"""
        uptime = (datetime.utcnow() - self.created_at).total_seconds()
        
        return {
            "state": self._state.value,
            "uptime_seconds": uptime,
            "active_tasks": len(self._active_tasks),
            "max_concurrent_tasks": self.config.max_concurrent_tasks,
            "department_agents_count": len(self.department_agents),
            "metrics": self.metrics.to_dict(),
            "configuration": {
                "enable_llm_classification": self.config.enable_llm_classification,
                "fallback_department": self.config.fallback_department,
                "enable_auto_retry": self.config.enable_auto_retry,
                "max_retries": self.config.max_retries,
                "routing_confidence_threshold": self.config.routing_confidence_threshold
            },
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get performance summary with key metrics"""
        if self.metrics.tasks_processed == 0:
            success_rate = 0.0
        else:
            success_rate = (self.metrics.successful_routes / self.metrics.tasks_processed) * 100
        
        return {
            "success_rate_percentage": round(success_rate, 2),
            "average_response_time_seconds": round(self.metrics.average_response_time, 3),
            "total_tasks_processed": self.metrics.tasks_processed,
            "tasks_handled_directly": self.metrics.direct_handled,
            "most_used_department": max(self.metrics.department_routing_counts.items(), 
                                      key=lambda x: x[1]) if self.metrics.department_routing_counts else None,
            "error_count": self.metrics.failed_routes
        }

    def add_classification_feedback(self, task_id: int, predicted_intent: str, 
                                  predicted_confidence: float, actual_intent: str,
                                  correction_source: str = "manual") -> bool:
        """
        Add feedback about classification accuracy for continuous learning
        """
        try:
            feedback = ClassificationFeedback(
                task_id=task_id,
                predicted_intent=predicted_intent,
                predicted_confidence=predicted_confidence,
                actual_intent=actual_intent,
                correction_source=correction_source,
                classification_method='llm' if self.config.enable_llm_classification else 'keyword'
            )
            
            self.feedback_history.append(feedback)
            
            # Add corrected example to training data if significantly different
            if predicted_intent != actual_intent:
                # Get the task text for training
                try:
                    from ..models import Task as TaskModel
                    task = TaskModel.query.get(task_id)
                    if task:
                        task_text = self._extract_task_text(task)
                        
                        # Add as training example
                        training_example = IntentExample(
                            text=task_text,
                            department=actual_intent,
                            confidence=1.0,  # High confidence for manually corrected examples
                            source='feedback'
                        )
                        self.dataset_manager.add_example(training_example)
                        
                        # Clear cache for this text to force reclassification
                        text_hash = hashlib.md5(task_text.encode()).hexdigest()
                        if text_hash in self.classification_cache:
                            del self.classification_cache[text_hash]
                        
                        log_agent_action(self.name, 
                                       f"Added feedback: {predicted_intent} -> {actual_intent} for task {task_id}")
                        
                except Exception as e:
                    logger.error(f"Error processing classification feedback: {e}")
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to add classification feedback: {e}")
            return False
    
    def get_classification_analytics(self) -> Dict[str, Any]:
        """
        Get comprehensive analytics about classification performance
        """
        if not self.feedback_history:
            return {
                "total_feedback": 0,
                "accuracy": None,
                "method_performance": {},
                "common_misclassifications": [],
                "cache_performance": self._get_cache_performance()
            }
        
        total_feedback = len(self.feedback_history)
        correct_classifications = sum(1 for f in self.feedback_history 
                                    if f.predicted_intent == f.actual_intent)
        
        accuracy = correct_classifications / total_feedback if total_feedback > 0 else 0
        
        # Analyze performance by method
        method_performance = {}
        for method in ['keyword', 'llm', 'hybrid']:
            method_feedback = [f for f in self.feedback_history if f.classification_method == method]
            if method_feedback:
                method_correct = sum(1 for f in method_feedback if f.predicted_intent == f.actual_intent)
                method_performance[method] = {
                    'accuracy': method_correct / len(method_feedback),
                    'total_samples': len(method_feedback)
                }
        
        # Find common misclassifications
        misclassifications = {}
        for f in self.feedback_history:
            if f.predicted_intent != f.actual_intent:
                key = f"{f.predicted_intent} -> {f.actual_intent}"
                misclassifications[key] = misclassifications.get(key, 0) + 1
        
        common_misclassifications = sorted(misclassifications.items(), 
                                         key=lambda x: x[1], reverse=True)[:5]
        
        return {
            "total_feedback": total_feedback,
            "accuracy": accuracy,
            "correct_classifications": correct_classifications,
            "method_performance": method_performance,
            "common_misclassifications": common_misclassifications,
            "training_examples": {
                dept: len(examples) for dept, examples in self.dataset_manager.get_examples().items()
            },
            "cache_performance": self._get_cache_performance()
        }
    
    def _get_cache_performance(self) -> Dict[str, Any]:
        """Get cache hit/miss statistics"""
        if not self.classification_cache:
            return {"cache_entries": 0, "total_hits": 0, "cache_efficiency": 0}
        
        total_hits = sum(entry.hit_count - 1 for entry in self.classification_cache.values())  # -1 because first access isn't a hit
        cache_entries = len(self.classification_cache)
        
        # Calculate cache efficiency (hits per entry)
        cache_efficiency = total_hits / cache_entries if cache_entries > 0 else 0
        
        return {
            "cache_entries": cache_entries,
            "total_hits": total_hits,
            "cache_efficiency": cache_efficiency,
            "valid_entries": sum(1 for entry in self.classification_cache.values() if entry.is_valid())
        }
    
    def cleanup_classification_cache(self, max_age_hours: int = 24) -> int:
        """
        Clean up expired cache entries
        Returns number of entries removed
        """
        removed_count = 0
        expired_keys = []
        
        for key, entry in self.classification_cache.items():
            if not entry.is_valid(max_age_hours):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self.classification_cache[key]
            removed_count += 1
        
        if removed_count > 0:
            log_agent_action(self.name, f"Cleaned up {removed_count} expired cache entries")
        
        return removed_count
    
    def export_training_data(self) -> Dict[str, Any]:
        """Export current training dataset for analysis or backup"""
        try:
            return {
                "exported_at": datetime.utcnow().isoformat(),
                "total_examples": sum(len(examples) for examples in self.dataset_manager.get_examples().values()),
                "examples_by_department": {
                    dept: [
                        {
                            "text": ex.text,
                            "department": ex.department,
                            "confidence": ex.confidence,
                            "source": ex.source,
                            "created_at": ex.created_at.isoformat()
                        }
                        for ex in examples
                    ]
                    for dept, examples in self.dataset_manager.get_examples().items()
                }
            }
        except Exception as e:
            logger.error(f"Error exporting training data: {e}")
            return {"error": str(e)}

    # ===== ENHANCED ROUTING LOGIC AND AGENT COMMUNICATION =====

    def make_routing_decision(self, task: Task, intent: str, confidence: float) -> RoutingDecision:
        """
        Make intelligent routing decision based on task complexity, agent availability, and performance
        """
        try:
            # Determine optimal routing strategy
            strategy = self._determine_routing_strategy(task, intent, confidence)
            
            # Select agents based on strategy and criteria
            selected_agents = self._select_agents_for_strategy(strategy, intent, task)
            
            # Calculate expected execution time
            expected_time = self._estimate_execution_time(strategy, selected_agents, task)
            
            # Identify fallback agents
            fallback_agents = self._identify_fallback_agents(intent, selected_agents)
            
            # Create routing decision with reasoning
            reasoning = self._generate_routing_reasoning(strategy, selected_agents, intent, confidence)
            
            decision = RoutingDecision(
                strategy=strategy,
                selected_agents=selected_agents,
                confidence=confidence,
                reasoning=reasoning,
                expected_execution_time=expected_time,
                fallback_agents=fallback_agents
            )
            
            # Store decision for analytics
            self.routing_decisions.append(decision)
            
            # Update strategy usage metrics
            with self._lock:
                self.metrics.routing_strategy_usage[strategy.value] = (
                    self.metrics.routing_strategy_usage.get(strategy.value, 0) + 1
                )
            
            log_agent_action(self.name, f"Routing decision: {strategy.value} for {intent} with {len(selected_agents)} agents")
            
            return decision
            
        except Exception as e:
            logger.error(f"Error making routing decision: {e}")
            # Fallback to single agent strategy
            return RoutingDecision(
                strategy=RoutingStrategy.SINGLE_AGENT,
                selected_agents=[intent],
                confidence=confidence,
                reasoning=f"Fallback due to error: {str(e)}"
            )

    def _determine_routing_strategy(self, task: Task, intent: str, confidence: float) -> RoutingStrategy:
        """Determine the optimal routing strategy based on task characteristics"""
        
        # Check if parallel execution is enabled
        if not self.config.enable_parallel_execution:
            return RoutingStrategy.SINGLE_AGENT
        
        # Analyze task complexity
        task_complexity = self._analyze_task_complexity(task)
        
        # Check available agents for the intent
        available_agents = self._get_available_agents_for_intent(intent)
        
        # Strategy selection logic
        if task_complexity >= 8 and len(available_agents) >= 2:
            # High complexity tasks benefit from multiple perspectives
            return RoutingStrategy.SCATTER_GATHER
        elif confidence < self.config.routing_confidence_threshold and len(available_agents) >= 2:
            # Low confidence benefits from consensus
            return RoutingStrategy.PARALLEL_AGENTS
        elif self.config.enable_load_balancing and len(available_agents) >= 2:
            # Load balancing when multiple agents available
            return RoutingStrategy.LOAD_BALANCED
        else:
            # Default to single agent
            return RoutingStrategy.SINGLE_AGENT

    def _analyze_task_complexity(self, task: Task) -> int:
        """Analyze task complexity on a scale of 1-10"""
        complexity_score = 1
        
        # Analyze task description length
        description_length = len(task.description or "")
        if description_length > 500:
            complexity_score += 2
        elif description_length > 200:
            complexity_score += 1
        
        # Analyze input data complexity
        if task.input_data:
            if isinstance(task.input_data, dict) and len(task.input_data) > 5:
                complexity_score += 2
            elif isinstance(task.input_data, (list, dict)) and len(str(task.input_data)) > 1000:
                complexity_score += 3
        
        # Analyze task priority
        if hasattr(task, 'priority') and task.priority == TaskPriority.HIGH:
            complexity_score += 1
        
        # Check for keywords indicating complexity
        complex_keywords = ['analyze', 'comprehensive', 'detailed', 'complex', 'multi-step', 'integration']
        task_text = f"{task.title} {task.description}".lower()
        for keyword in complex_keywords:
            if keyword in task_text:
                complexity_score += 1
        
        return min(complexity_score, 10)  # Cap at 10

    def _get_available_agents_for_intent(self, intent: str) -> List[str]:
        """Get list of available agents that can handle the given intent"""
        available_agents = []
        
        # Check primary department agent
        if intent in self.department_agents:
            agent = self.department_agents[intent]
            if agent.is_available():
                available_agents.append(intent)
        
        # Check for alternative agents (future enhancement)
        # This could include agents from related departments or multi-skilled agents
        
        return available_agents

    def _select_agents_for_strategy(self, strategy: RoutingStrategy, intent: str, task: Task) -> List[str]:
        """Select specific agents based on routing strategy"""
        
        if strategy == RoutingStrategy.SINGLE_AGENT:
            return [intent]
        
        elif strategy == RoutingStrategy.PARALLEL_AGENTS:
            # Select up to max_parallel_agents for parallel execution
            available_agents = self._get_available_agents_for_intent(intent)
            return available_agents[:self.config.max_parallel_agents]
        
        elif strategy == RoutingStrategy.SCATTER_GATHER:
            # Select agents from different departments for diverse perspectives
            selected = [intent]
            
            # Add complementary departments
            complementary_depts = self._get_complementary_departments(intent)
            for dept in complementary_depts:
                if dept in self.department_agents and self.department_agents[dept].is_available():
                    selected.append(dept)
                    if len(selected) >= self.config.max_parallel_agents:
                        break
            
            return selected
        
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            # Select agent with lowest current workload
            available_agents = self._get_available_agents_for_intent(intent)
            if available_agents:
                # Sort by workload (ascending)
                sorted_agents = sorted(available_agents, key=lambda a: self.agent_workload.get(a, 0))
                return [sorted_agents[0]]
            
        return [intent]  # Fallback

    def _get_complementary_departments(self, primary_intent: str) -> List[str]:
        """Get departments that complement the primary intent"""
        complementary_map = {
            'communications': ['analysis'],  # Analysis can help improve communications
            'analysis': ['communications'],  # Communications can help present analysis
            'automation': ['analysis', 'coordination'],  # Analysis and coordination support automation
            'coordination': ['communications', 'analysis']  # Communications and analysis support coordination
        }
        
        return complementary_map.get(primary_intent, [])

    def _estimate_execution_time(self, strategy: RoutingStrategy, selected_agents: List[str], task: Task) -> float:
        """Estimate execution time based on strategy and agents"""
        
        base_time = 30.0  # Base execution time in seconds
        
        # Adjust based on task complexity
        complexity = self._analyze_task_complexity(task)
        time_multiplier = 1.0 + (complexity - 1) * 0.2  # 20% increase per complexity point
        
        # Adjust based on strategy
        if strategy == RoutingStrategy.PARALLEL_AGENTS:
            # Parallel execution is faster but has coordination overhead
            return base_time * time_multiplier * 0.7 + 10  # 30% faster + 10s overhead
        elif strategy == RoutingStrategy.SCATTER_GATHER:
            # Scatter-gather takes longer due to aggregation
            return base_time * time_multiplier * 1.3 + 20  # 30% slower + 20s overhead
        else:
            return base_time * time_multiplier

    def _identify_fallback_agents(self, intent: str, selected_agents: List[str]) -> List[str]:
        """Identify fallback agents in case primary agents fail"""
        fallback_agents = []
        
        # Add fallback department if not already selected
        if self.config.fallback_department not in selected_agents:
            fallback_agents.append(self.config.fallback_department)
        
        # Add alternative agents from the same domain
        available_agents = self._get_available_agents_for_intent(intent)
        for agent in available_agents:
            if agent not in selected_agents and agent not in fallback_agents:
                fallback_agents.append(agent)
        
        return fallback_agents

    def _generate_routing_reasoning(self, strategy: RoutingStrategy, selected_agents: List[str], 
                                  intent: str, confidence: float) -> str:
        """Generate human-readable reasoning for the routing decision"""
        
        reasoning_parts = [
            f"Selected {strategy.value} strategy for {intent} intent"
        ]
        
        if confidence < self.config.routing_confidence_threshold:
            reasoning_parts.append(f"Low confidence ({confidence:.2f}) suggests multiple agent validation")
        
        if len(selected_agents) > 1:
            reasoning_parts.append(f"Using {len(selected_agents)} agents for enhanced quality")
        
        if strategy == RoutingStrategy.SCATTER_GATHER:
            reasoning_parts.append("High complexity task benefits from diverse perspectives")
        elif strategy == RoutingStrategy.LOAD_BALANCED:
            reasoning_parts.append("Load balancing to optimize resource utilization")
        
        return "; ".join(reasoning_parts)

    def enhanced_route_task(self, task: Task, intent: str, confidence: float = 1.0) -> Dict[str, Any]:
        """
        Enhanced task routing with intelligent decision making and parallel execution
        """
        try:
            # Make routing decision
            decision = self.make_routing_decision(task, intent, confidence)
            
            # For now, use existing routing logic but with enhanced decision metadata
            # Future enhancement: implement full parallel execution
            result = self.route_task(task, intent, confidence)
            
            # Add routing metadata to result
            result["routing_decision"] = {
                "strategy": decision.strategy.value,
                "selected_agents": decision.selected_agents,
                "confidence": decision.confidence,
                "reasoning": decision.reasoning,
                "expected_execution_time": decision.expected_execution_time
            }
            
            return result
            
        except Exception as e:
            error_msg = f"Error in enhanced task routing: {str(e)}"
            logger.error(error_msg, exc_info=True)
            log_agent_action(self.name, error_msg)
            return self._create_error_response(error_msg, task.id)

    def get_routing_analytics(self) -> Dict[str, Any]:
        """Get comprehensive routing analytics and performance metrics"""
        
        with self._lock:
            analytics = {
                "routing_decisions": len(self.routing_decisions),
                "strategy_usage": dict(self.metrics.routing_strategy_usage),
                "agent_performance": dict(self.metrics.agent_performance_scores),
                "agent_workload": dict(self.agent_workload),
                "parallel_executions": self.metrics.parallel_executions,
                "aggregated_results": self.metrics.aggregated_results,
                "recent_decisions": [
                    {
                        "strategy": d.strategy.value,
                        "agents": d.selected_agents,
                        "confidence": d.confidence,
                        "reasoning": d.reasoning,
                        "timestamp": d.created_at.isoformat()
                    }
                    for d in self.routing_decisions[-10:]  # Last 10 decisions
                ]
            }
        
        return analytics 