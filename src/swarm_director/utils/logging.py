"""
Enhanced Logging and Monitoring System for SwarmDirector
Provides structured logging, performance metrics, and monitoring capabilities.
"""

import logging
import logging.handlers
import os
import sys
import json
import uuid
import time
import threading
from datetime import datetime
from typing import Dict, Any, Optional, Union
from contextlib import contextmanager
from functools import wraps

import structlog
import psutil

# Import the new metrics system at the top
from .metrics import metrics_collector, get_current_metrics_summary, track_performance_metrics

# Global configuration
_LOG_CONFIG = {
    'structured': True,
    'console_output': True,
    'file_output': True,
    'database_output': False,
    'performance_tracking': True,
    'correlation_tracking': True
}

# Thread-local storage for correlation IDs
_thread_local = threading.local()

class StructuredFormatter(logging.Formatter):
    """Custom formatter that outputs structured JSON logs"""
    
    def format(self, record):
        log_data = {
            'timestamp': datetime.utcnow().isoformat() + 'Z',
            'level': record.levelname,
            'logger': record.name,
            'message': record.getMessage(),
            'module': record.module,
            'function': record.funcName,
            'line': record.lineno,
        }
        
        # Add correlation ID if available
        if hasattr(_thread_local, 'correlation_id'):
            log_data['correlation_id'] = _thread_local.correlation_id
            
        # Add any extra fields from the log record
        if hasattr(record, 'extra_fields'):
            log_data.update(record.extra_fields)
            
        # Add performance metrics if available
        if hasattr(record, 'performance_metrics'):
            log_data['performance'] = record.performance_metrics
            
        return json.dumps(log_data, default=str)

class PerformanceMetrics:
    """Collects and tracks system and application performance metrics"""
    
    @staticmethod
    def get_system_metrics() -> Dict[str, Any]:
        """Get current system performance metrics"""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            return {
                'cpu_percent': cpu_percent,
                'memory_percent': memory.percent,
                'memory_available_mb': memory.available / 1024 / 1024,
                'disk_percent': disk.percent,
                'disk_free_gb': disk.free / 1024 / 1024 / 1024,
                'process_count': len(psutil.pids())
            }
        except Exception as e:
            return {'error': f'Failed to collect system metrics: {str(e)}'}
    
    @staticmethod
    def get_process_metrics() -> Dict[str, Any]:
        """Get current process performance metrics"""
        try:
            process = psutil.Process()
            return {
                'pid': process.pid,
                'cpu_percent': process.cpu_percent(),
                'memory_mb': process.memory_info().rss / 1024 / 1024,
                'threads': process.num_threads(),
                'open_files': len(process.open_files()),
                'connections': len(process.connections())
            }
        except Exception as e:
            return {'error': f'Failed to collect process metrics: {str(e)}'}

class DatabaseLogger:
    """Handles database logging operations"""
    
    def __init__(self, db_session=None):
        self.db_session = db_session
        self.enabled = db_session is not None
    
    def log_to_database(self, log_data: Dict[str, Any]):
        """Log structured data to database"""
        if not self.enabled:
            return
            
        try:
            # This would need to be implemented based on your database schema
            # For now, we'll just store in a simple log table
            pass
        except Exception as e:
            # Fall back to file logging if database fails
            fallback_logger = logging.getLogger('database_fallback')
            fallback_logger.error(f"Database logging failed: {e}")

def set_correlation_id(correlation_id: str = None) -> str:
    """Set correlation ID for current thread/request"""
    if correlation_id is None:
        correlation_id = str(uuid.uuid4())
    _thread_local.correlation_id = correlation_id
    return correlation_id

def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current thread/request"""
    return getattr(_thread_local, 'correlation_id', None)

@contextmanager
def correlation_context(correlation_id: str = None):
    """Context manager for correlation ID"""
    old_id = get_correlation_id()
    new_id = set_correlation_id(correlation_id)
    try:
        yield new_id
    finally:
        if old_id:
            _thread_local.correlation_id = old_id
        elif hasattr(_thread_local, 'correlation_id'):
            delattr(_thread_local, 'correlation_id')

def performance_timer(func):
    """Decorator to automatically track function execution time"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        
        try:
            result = func(*args, **kwargs)
            execution_time = time.time() - start_time
            
            logger = get_logger('performance')
            logger.info(
                f"Function {func.__name__} completed",
                extra={'extra_fields': {
                    'function': func.__name__,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'success'
                }}
            )
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger = get_logger('performance')
            logger.error(
                f"Function {func.__name__} failed",
                extra={'extra_fields': {
                    'function': func.__name__,
                    'execution_time_ms': round(execution_time * 1000, 2),
                    'status': 'error',
                    'error': str(e)
                }}
            )
            raise
    return wrapper

def setup_structured_logging(
    app=None, 
    log_level=logging.INFO,
    enable_database_logging=False,
    db_session=None
):
    """Set up enhanced structured logging configuration"""
    
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Configure structlog
    structlog.configure(
        processors=[
            structlog.stdlib.filter_by_level,
            structlog.stdlib.add_logger_name,
            structlog.stdlib.add_log_level,
            structlog.stdlib.PositionalArgumentsFormatter(),
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.processors.UnicodeDecoder(),
            structlog.processors.JSONRenderer()
        ],
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    root_logger.handlers.clear()
    
    # Console handler with structured formatting
    if _LOG_CONFIG['console_output']:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(console_handler)
    
    # File handler with rotation
    if _LOG_CONFIG['file_output']:
        file_handler = logging.handlers.RotatingFileHandler(
            f'logs/swarm_director.log',
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5
        )
        file_handler.setFormatter(StructuredFormatter())
        root_logger.addHandler(file_handler)
    
    # Setup database logging if enabled
    if enable_database_logging:
        _LOG_CONFIG['database_output'] = True
        # Initialize database logger
        global _db_logger
        _db_logger = DatabaseLogger(db_session)
    
    # Configure specific loggers
    configure_agent_logger()
    configure_task_logger()
    configure_conversation_logger()
    configure_performance_logger()
    
    if app:
        app.logger.setLevel(log_level)
        app.logger.info("Enhanced structured logging configured successfully")

def configure_agent_logger():
    """Configure logging for agent-related operations"""
    agent_logger = logging.getLogger('swarm_director.agents')
    agent_logger.setLevel(logging.INFO)

def configure_task_logger():
    """Configure logging for task-related operations"""
    task_logger = logging.getLogger('swarm_director.tasks')
    task_logger.setLevel(logging.INFO)

def configure_conversation_logger():
    """Configure logging for conversation-related operations"""
    conv_logger = logging.getLogger('swarm_director.conversations')
    conv_logger.setLevel(logging.INFO)

def configure_performance_logger():
    """Configure logging for performance metrics"""
    perf_logger = logging.getLogger('swarm_director.performance')
    perf_logger.setLevel(logging.INFO)

def get_logger(name: str) -> logging.Logger:
    """Get a logger with the specified name"""
    return logging.getLogger(f'swarm_director.{name}')

def get_structured_logger(name: str):
    """Get a structured logger with the specified name"""
    return structlog.get_logger(f'swarm_director.{name}')

# Enhanced convenience functions for common logging operations
def log_agent_action(
    agent_name: str, 
    action: str, 
    details: Optional[Dict[str, Any]] = None,
    include_metrics: bool = True
):
    """Log an agent action with optional performance metrics"""
    logger = get_logger('agents')
    
    extra_fields = {
        'agent_name': agent_name,
        'action': action,
        'event_type': 'agent_action'
    }
    
    if details:
        extra_fields.update(details)
    
    if include_metrics and _LOG_CONFIG['performance_tracking']:
        extra_fields['system_metrics'] = PerformanceMetrics.get_system_metrics()
    
    message = f"{agent_name}: {action}"
    logger.info(message, extra={'extra_fields': extra_fields})

def log_task_update(
    task_id: Union[str, int], 
    status: str, 
    details: Optional[Dict[str, Any]] = None
):
    """Log a task status update"""
    logger = get_logger('tasks')
    
    extra_fields = {
        'task_id': str(task_id),
        'status': status,
        'event_type': 'task_update'
    }
    
    if details:
        extra_fields.update(details)
    
    message = f"Task {task_id} status changed to {status}"
    logger.info(message, extra={'extra_fields': extra_fields})

def log_conversation_event(
    conversation_id: Union[str, int], 
    event: str, 
    details: Optional[Dict[str, Any]] = None
):
    """Log a conversation event"""
    logger = get_logger('conversations')
    
    extra_fields = {
        'conversation_id': str(conversation_id),
        'event': event,
        'event_type': 'conversation_event'
    }
    
    if details:
        extra_fields.update(details)
    
    message = f"Conversation {conversation_id}: {event}"
    logger.info(message, extra={'extra_fields': extra_fields})

def log_performance_metric(
    metric_name: str, 
    value: Union[int, float], 
    unit: str = None,
    context: Optional[Dict[str, Any]] = None
):
    """Log a specific performance metric"""
    logger = get_logger('performance')
    
    extra_fields = {
        'metric_name': metric_name,
        'metric_value': value,
        'event_type': 'performance_metric'
    }
    
    if unit:
        extra_fields['unit'] = unit
    
    if context:
        extra_fields.update(context)
    
    message = f"Performance metric: {metric_name} = {value}"
    if unit:
        message += f" {unit}"
    
    logger.info(message, extra={'extra_fields': extra_fields})

def log_error_with_context(
    error: Exception, 
    context: Optional[Dict[str, Any]] = None,
    logger_name: str = 'errors'
):
    """Log an error with rich contextual information"""
    logger = get_logger(logger_name)
    
    extra_fields = {
        'error_type': type(error).__name__,
        'error_message': str(error),
        'event_type': 'error',
        'system_metrics': PerformanceMetrics.get_system_metrics()
    }
    
    if context:
        extra_fields.update(context)
    
    logger.error(f"Error occurred: {str(error)}", extra={'extra_fields': extra_fields}, exc_info=True)

# Backward compatibility aliases
setup_logging = setup_structured_logging 

def log_with_metrics(
    logger_name: str,
    level: str,
    message: str,
    include_system_metrics: bool = True,
    include_endpoint_stats: bool = False,
    **extra_fields
):
    """Enhanced logging function that includes performance metrics"""
    logger = get_logger(logger_name)
    
    # Get correlation ID
    correlation_id = get_correlation_id()
    
    # Collect metrics if requested
    log_data = {}
    
    if include_system_metrics:
        try:
            system_metrics = metrics_collector.collect_system_metrics(correlation_id)
            log_data['system_metrics'] = {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'tags': metric.tags
                } for name, metric in system_metrics.items()
            }
        except Exception as e:
            log_data['metrics_error'] = f"Failed to collect system metrics: {e}"
    
    if include_endpoint_stats:
        try:
            log_data['endpoint_stats'] = metrics_collector.get_all_endpoint_stats()
        except Exception as e:
            log_data['endpoint_stats_error'] = f"Failed to collect endpoint stats: {e}"
    
    # Add extra fields
    log_data.update(extra_fields)
    
    # Log with appropriate level
    if level.upper() == 'DEBUG':
        logger.debug(message, extra={'extra_fields': log_data})
    elif level.upper() == 'INFO':
        logger.info(message, extra={'extra_fields': log_data})
    elif level.upper() == 'WARNING':
        logger.warning(message, extra={'extra_fields': log_data})
    elif level.upper() == 'ERROR':
        logger.error(message, extra={'extra_fields': log_data})
    else:
        logger.info(message, extra={'extra_fields': log_data})

def log_performance_summary(logger_name: str = 'performance'):
    """Log a comprehensive performance summary"""
    logger = get_logger(logger_name)
    
    try:
        summary = get_current_metrics_summary()
        logger.info(
            "Performance metrics summary",
            extra={'extra_fields': {
                'metrics_summary': summary,
                'summary_type': 'comprehensive_performance'
            }}
        )
    except Exception as e:
        logger.error(f"Failed to log performance summary: {e}")

def setup_metrics_integration():
    """Set up integration between metrics and logging systems"""
    # Configure periodic metrics collection
    import threading
    import time
    
    def periodic_metrics_collection():
        """Periodically collect and log system metrics"""
        while True:
            try:
                correlation_id = set_correlation_id()
                metrics_collector.collect_system_metrics(correlation_id)
                
                # Log summary every 5 minutes
                log_performance_summary()
                
            except Exception as e:
                logger = get_logger('metrics_integration')
                logger.error(f"Periodic metrics collection failed: {e}")
            
            time.sleep(300)  # 5 minutes
    
    # Start background thread for periodic collection
    metrics_thread = threading.Thread(target=periodic_metrics_collection, daemon=True)
    metrics_thread.start() 