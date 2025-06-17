"""
Error Recovery Service
Comprehensive error handling and recovery mechanisms for workflow resilience
"""

import logging
import time
import uuid
from enum import Enum
from typing import Dict, Any, Optional, List, Callable, Union
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import defaultdict
import asyncio
import threading
from contextlib import contextmanager

logger = logging.getLogger(__name__)

class ErrorType(Enum):
    """Classification of error types for appropriate handling"""
    TRANSIENT = "transient"  # Temporary errors that may resolve
    PERSISTENT = "persistent"  # Errors that require intervention
    CONFIGURATION = "configuration"  # Configuration or setup errors
    NETWORK = "network"  # Network connectivity issues
    AUTHENTICATION = "authentication"  # Authentication/authorization errors
    RESOURCE_EXHAUSTION = "resource_exhaustion"  # System resource issues
    DATA_CORRUPTION = "data_corruption"  # Data integrity issues
    AGENT_FAILURE = "agent_failure"  # AI agent failures
    SMTP_ERROR = "smtp_error"  # Email delivery errors
    DATABASE_ERROR = "database_error"  # Database operation errors
    VALIDATION_ERROR = "validation_error"  # Input validation errors
    TIMEOUT = "timeout"  # Operation timeout errors
    UNKNOWN = "unknown"  # Unclassified errors

class ErrorSeverity(Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

class RecoveryAction(Enum):
    """Types of recovery actions"""
    RETRY = "retry"
    FALLBACK = "fallback"
    ROLLBACK = "rollback"
    ESCALATE = "escalate"
    IGNORE = "ignore"
    MANUAL_INTERVENTION = "manual_intervention"

@dataclass
class RetryStrategy:
    """Configuration for retry strategies"""
    max_attempts: int = 3
    base_delay: float = 1.0  # Base delay in seconds
    max_delay: float = 60.0  # Maximum delay in seconds
    exponential_backoff: bool = True
    jitter: bool = True  # Add randomization to prevent thundering herd
    error_types: List[ErrorType] = field(default_factory=list)

@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker pattern"""
    failure_threshold: int = 5  # Number of failures before opening circuit
    recovery_timeout: float = 60.0  # Time to wait before attempting recovery
    half_open_max_calls: int = 3  # Max calls to test in half-open state
    success_threshold: int = 2  # Successes needed to close circuit

class CircuitBreakerState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Blocking calls due to failures
    HALF_OPEN = "half_open"  # Testing if service has recovered

@dataclass
class ErrorRecord:
    """Record of an error occurrence"""
    error_id: str
    workflow_id: str
    error_type: ErrorType
    severity: ErrorSeverity
    message: str
    exception: Optional[Exception] = None
    context: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    agent_name: Optional[str] = None
    phase: Optional[str] = None
    retry_count: int = 0
    recovery_attempts: List[Dict[str, Any]] = field(default_factory=list)

@dataclass
class RecoveryResult:
    """Result of a recovery attempt"""
    success: bool
    action_taken: RecoveryAction
    message: str
    retry_after: Optional[float] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

class CircuitBreaker:
    """Circuit breaker implementation for preventing cascading failures"""
    
    def __init__(self, config: CircuitBreakerConfig):
        self.config = config
        self.state = CircuitBreakerState.CLOSED
        self.failure_count = 0
        self.last_failure_time = None
        self.half_open_calls = 0
        self.success_count = 0
        self._lock = threading.Lock()
    
    def call(self, func: Callable, *args, **kwargs):
        """Execute a function call through the circuit breaker"""
        with self._lock:
            if self.state == CircuitBreakerState.OPEN:
                if self._should_attempt_reset():
                    self.state = CircuitBreakerState.HALF_OPEN
                    self.half_open_calls = 0
                    self.success_count = 0
                else:
                    raise Exception("Circuit breaker is OPEN - service unavailable")
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                if self.half_open_calls >= self.config.half_open_max_calls:
                    raise Exception("Circuit breaker HALF_OPEN - max calls exceeded")
                self.half_open_calls += 1
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset"""
        if self.last_failure_time is None:
            return False
        return (datetime.now() - self.last_failure_time).total_seconds() >= self.config.recovery_timeout
    
    def _on_success(self):
        """Handle successful call"""
        with self._lock:
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.success_count += 1
                if self.success_count >= self.config.success_threshold:
                    self.state = CircuitBreakerState.CLOSED
                    self.failure_count = 0
                    self.last_failure_time = None
    
    def _on_failure(self):
        """Handle failed call"""
        with self._lock:
            self.failure_count += 1
            self.last_failure_time = datetime.now()
            
            if self.state == CircuitBreakerState.HALF_OPEN:
                self.state = CircuitBreakerState.OPEN
            elif self.failure_count >= self.config.failure_threshold:
                self.state = CircuitBreakerState.OPEN

class DeadLetterQueue:
    """Handle permanently failed workflows"""
    
    def __init__(self, max_size: int = 1000):
        self.max_size = max_size
        self.queue: List[Dict[str, Any]] = []
        self._lock = threading.Lock()
    
    def add_failed_workflow(self, workflow_id: str, error_record: ErrorRecord,
                          final_attempt: bool = True):
        """Add a failed workflow to the dead letter queue"""
        with self._lock:
            if len(self.queue) >= self.max_size:
                # Remove oldest entry
                self.queue.pop(0)
            
            self.queue.append({
                'workflow_id': workflow_id,
                'error_record': error_record,
                'added_at': datetime.now(),
                'final_attempt': final_attempt,
                'retry_eligible': not final_attempt
            })
            
            logger.warning(f"Workflow {workflow_id} added to dead letter queue: {error_record.message}")
    
    def get_retry_eligible_workflows(self) -> List[Dict[str, Any]]:
        """Get workflows eligible for retry"""
        with self._lock:
            return [item for item in self.queue if item.get('retry_eligible', False)]
    
    def mark_workflow_retried(self, workflow_id: str):
        """Mark a workflow as retried"""
        with self._lock:
            for item in self.queue:
                if item['workflow_id'] == workflow_id:
                    item['retry_eligible'] = False
                    item['retried_at'] = datetime.now()
                    break

class ErrorRecoveryService:
    """
    Centralized error recovery service for workflow resilience
    """
    
    def __init__(self):
        self.error_records: Dict[str, ErrorRecord] = {}
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.dead_letter_queue = DeadLetterQueue()
        self.retry_strategies: Dict[ErrorType, RetryStrategy] = {}
        self.recovery_handlers: Dict[ErrorType, Callable] = {}
        self.error_classifiers: List[Callable] = []
        self._setup_default_configurations()
        
        # Statistics
        self.error_count_by_type = defaultdict(int)
        self.recovery_count_by_action = defaultdict(int)
        self.circuit_breaker_activations = defaultdict(int)
        
        logger.info("Error Recovery Service initialized")
    
    def _setup_default_configurations(self):
        """Setup default retry strategies and error handlers"""
        # Default retry strategies
        self.retry_strategies = {
            ErrorType.TRANSIENT: RetryStrategy(max_attempts=3, base_delay=1.0, exponential_backoff=True),
            ErrorType.NETWORK: RetryStrategy(max_attempts=5, base_delay=2.0, max_delay=30.0),
            ErrorType.SMTP_ERROR: RetryStrategy(max_attempts=3, base_delay=5.0, max_delay=60.0),
            ErrorType.DATABASE_ERROR: RetryStrategy(max_attempts=2, base_delay=1.0, exponential_backoff=True),
            ErrorType.TIMEOUT: RetryStrategy(max_attempts=2, base_delay=5.0, max_delay=30.0),
            ErrorType.AGENT_FAILURE: RetryStrategy(max_attempts=2, base_delay=3.0, max_delay=20.0),
        }
        
        # Default error classifiers
        self.error_classifiers.extend([
            self._classify_network_errors,
            self._classify_database_errors,
            self._classify_smtp_errors,
            self._classify_timeout_errors,
            self._classify_agent_errors,
            self._classify_validation_errors
        ])
    
    def classify_error(self, exception: Exception, context: Dict[str, Any] = None) -> tuple[ErrorType, ErrorSeverity]:
        """Classify an error to determine appropriate handling strategy"""
        context = context or {}
        
        # Apply error classifiers
        for classifier in self.error_classifiers:
            result = classifier(exception, context)
            if result != (ErrorType.UNKNOWN, ErrorSeverity.MEDIUM):
                return result
        
        # Default classification
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_network_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify network-related errors"""
        error_msg = str(exception).lower()
        
        if any(keyword in error_msg for keyword in ['connection', 'network', 'timeout', 'dns', 'socket']):
            if 'timeout' in error_msg:
                return ErrorType.TIMEOUT, ErrorSeverity.MEDIUM
            return ErrorType.NETWORK, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_database_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify database-related errors"""
        error_msg = str(exception).lower()
        
        if any(keyword in error_msg for keyword in ['database', 'sql', 'connection', 'deadlock', 'constraint']):
            if 'deadlock' in error_msg or 'lock' in error_msg:
                return ErrorType.TRANSIENT, ErrorSeverity.MEDIUM
            if 'constraint' in error_msg or 'integrity' in error_msg:
                return ErrorType.DATA_CORRUPTION, ErrorSeverity.HIGH
            return ErrorType.DATABASE_ERROR, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_smtp_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify SMTP/email-related errors"""
        error_msg = str(exception).lower()
        
        if any(keyword in error_msg for keyword in ['smtp', 'email', 'mail', 'authentication failed']):
            if 'authentication' in error_msg:
                return ErrorType.AUTHENTICATION, ErrorSeverity.HIGH
            if any(code in error_msg for code in ['4', '421', '450', '451', '452']):  # Temporary SMTP errors
                return ErrorType.TRANSIENT, ErrorSeverity.MEDIUM
            return ErrorType.SMTP_ERROR, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_timeout_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify timeout-related errors"""
        error_msg = str(exception).lower()
        
        if 'timeout' in error_msg or isinstance(exception, asyncio.TimeoutError):
            return ErrorType.TIMEOUT, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_agent_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify AI agent-related errors"""
        error_msg = str(exception).lower()
        agent_name = context.get('agent_name', '').lower()
        
        if 'agent' in error_msg or agent_name:
            if 'rate limit' in error_msg or 'quota' in error_msg:
                return ErrorType.RESOURCE_EXHAUSTION, ErrorSeverity.MEDIUM
            if 'api key' in error_msg or 'unauthorized' in error_msg:
                return ErrorType.AUTHENTICATION, ErrorSeverity.HIGH
            return ErrorType.AGENT_FAILURE, ErrorSeverity.MEDIUM
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def _classify_validation_errors(self, exception: Exception, context: Dict[str, Any]) -> tuple[ErrorType, ErrorSeverity]:
        """Classify validation-related errors"""
        error_msg = str(exception).lower()
        
        if any(keyword in error_msg for keyword in ['validation', 'invalid', 'required', 'missing']):
            return ErrorType.VALIDATION_ERROR, ErrorSeverity.LOW
        
        return ErrorType.UNKNOWN, ErrorSeverity.MEDIUM
    
    def record_error(self, workflow_id: str, exception: Exception, 
                    context: Dict[str, Any] = None) -> ErrorRecord:
        """Record an error occurrence"""
        context = context or {}
        error_type, severity = self.classify_error(exception, context)
        
        error_record = ErrorRecord(
            error_id=f"err_{uuid.uuid4().hex[:8]}_{int(time.time())}",
            workflow_id=workflow_id,
            error_type=error_type,
            severity=severity,
            message=str(exception),
            exception=exception,
            context=context,
            agent_name=context.get('agent_name'),
            phase=context.get('phase')
        )
        
        self.error_records[error_record.error_id] = error_record
        self.error_count_by_type[error_type] += 1
        
        logger.error(f"Error recorded: {error_record.error_id} - {error_record.message}")
        return error_record
    
    def get_circuit_breaker(self, service_name: str, config: CircuitBreakerConfig = None) -> CircuitBreaker:
        """Get or create a circuit breaker for a service"""
        if service_name not in self.circuit_breakers:
            config = config or CircuitBreakerConfig()
            self.circuit_breakers[service_name] = CircuitBreaker(config)
        return self.circuit_breakers[service_name]
    
    @contextmanager
    def circuit_breaker_protection(self, service_name: str, config: CircuitBreakerConfig = None):
        """Context manager for circuit breaker protection"""
        circuit_breaker = self.get_circuit_breaker(service_name, config)
        try:
            if circuit_breaker.state == CircuitBreakerState.OPEN:
                raise Exception(f"Circuit breaker OPEN for service: {service_name}")
            yield circuit_breaker
        except Exception:
            self.circuit_breaker_activations[service_name] += 1
            raise
    
    def attempt_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt to recover from an error"""
        error_type = error_record.error_type
        retry_strategy = self.retry_strategies.get(error_type)
        
        # Determine recovery action
        if retry_strategy and error_record.retry_count < retry_strategy.max_attempts:
            return self._attempt_retry_recovery(error_record, retry_strategy)
        elif error_type in [ErrorType.PERSISTENT, ErrorType.CONFIGURATION, ErrorType.AUTHENTICATION]:
            return self._attempt_escalation_recovery(error_record)
        elif error_type == ErrorType.DATA_CORRUPTION:
            return self._attempt_rollback_recovery(error_record)
        else:
            return self._attempt_fallback_recovery(error_record)
    
    def _attempt_retry_recovery(self, error_record: ErrorRecord, retry_strategy: RetryStrategy) -> RecoveryResult:
        """Attempt retry-based recovery"""
        error_record.retry_count += 1
        
        # Calculate delay
        delay = retry_strategy.base_delay * (2 ** (error_record.retry_count - 1)) if retry_strategy.exponential_backoff else retry_strategy.base_delay
        delay = min(delay, retry_strategy.max_delay)
        
        # Add jitter
        if retry_strategy.jitter:
            import random
            delay *= (0.5 + random.random() * 0.5)
        
        self.recovery_count_by_action[RecoveryAction.RETRY] += 1
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.RETRY,
            message=f"Scheduled retry #{error_record.retry_count} after {delay:.1f}s",
            retry_after=delay,
            metadata={'delay': delay, 'attempt': error_record.retry_count}
        )
    
    def _attempt_escalation_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt escalation-based recovery"""
        self.recovery_count_by_action[RecoveryAction.ESCALATE] += 1
        
        # Add to dead letter queue for manual intervention
        self.dead_letter_queue.add_failed_workflow(error_record.workflow_id, error_record, final_attempt=True)
        
        return RecoveryResult(
            success=False,
            action_taken=RecoveryAction.ESCALATE,
            message="Error escalated for manual intervention",
            metadata={'requires_manual_intervention': True}
        )
    
    def _attempt_rollback_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt rollback-based recovery"""
        self.recovery_count_by_action[RecoveryAction.ROLLBACK] += 1
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.ROLLBACK,
            message="Workflow marked for rollback to previous state",
            metadata={'rollback_required': True}
        )
    
    def _attempt_fallback_recovery(self, error_record: ErrorRecord) -> RecoveryResult:
        """Attempt fallback-based recovery"""
        self.recovery_count_by_action[RecoveryAction.FALLBACK] += 1
        
        return RecoveryResult(
            success=True,
            action_taken=RecoveryAction.FALLBACK,
            message="Using fallback mechanism",
            metadata={'fallback_mode': True}
        )
    
    def get_error_statistics(self) -> Dict[str, Any]:
        """Get comprehensive error statistics"""
        return {
            'total_errors': len(self.error_records),
            'errors_by_type': dict(self.error_count_by_type),
            'recovery_actions': dict(self.recovery_count_by_action),
            'circuit_breaker_activations': dict(self.circuit_breaker_activations),
            'dead_letter_queue_size': len(self.dead_letter_queue.queue),
            'active_circuit_breakers': {
                name: {
                    'state': cb.state.value,
                    'failure_count': cb.failure_count,
                    'last_failure': cb.last_failure_time.isoformat() if cb.last_failure_time else None
                }
                for name, cb in self.circuit_breakers.items()
            }
        }
    
    def cleanup_old_errors(self, days_old: int = 7) -> int:
        """Clean up old error records"""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        old_errors = [
            error_id for error_id, record in self.error_records.items()
            if record.timestamp < cutoff_date
        ]
        
        for error_id in old_errors:
            del self.error_records[error_id]
        
        logger.info(f"Cleaned up {len(old_errors)} old error records")
        return len(old_errors)

# Global error recovery service instance
error_recovery_service = ErrorRecoveryService() 