"""
Enhanced error handling utilities for SwarmDirector API
Provides comprehensive error management with custom exceptions and detailed logging
"""

import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional
from flask import request, current_app
from functools import wraps


class SwarmDirectorError(Exception):
    """Base exception class for SwarmDirector-specific errors"""
    
    def __init__(self, message: str, error_code: str = None, status_code: int = 500, 
                 details: Dict = None, correlation_id: str = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.status_code = status_code
        self.details = details or {}
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.timestamp = datetime.utcnow().isoformat()


class ValidationError(SwarmDirectorError):
    """Error raised when input validation fails"""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(message, error_code='VALIDATION_ERROR', status_code=400, **kwargs)
        if field:
            self.details['field'] = field
        if value is not None:
            self.details['rejected_value'] = str(value)


class AuthenticationError(SwarmDirectorError):
    """Error raised when authentication fails"""
    
    def __init__(self, message: str = "Authentication required", **kwargs):
        super().__init__(message, error_code='AUTHENTICATION_ERROR', status_code=401, **kwargs)


class ResourceNotFoundError(SwarmDirectorError):
    """Error raised when requested resource is not found"""
    
    def __init__(self, message: str = "Resource not found", resource_type: str = None, 
                 resource_id: Any = None, **kwargs):
        super().__init__(message, error_code='RESOURCE_NOT_FOUND', status_code=404, **kwargs)
        if resource_type:
            self.details['resource_type'] = resource_type
        if resource_id is not None:
            self.details['resource_id'] = str(resource_id)


class RateLimitError(SwarmDirectorError):
    """Error raised when rate limits are exceeded"""
    
    def __init__(self, message: str = "Rate limit exceeded", retry_after: int = None, **kwargs):
        super().__init__(message, error_code='RATE_LIMIT_EXCEEDED', status_code=429, **kwargs)
        if retry_after:
            self.details['retry_after'] = retry_after


class DatabaseError(SwarmDirectorError):
    """Error raised when database operations fail"""
    
    def __init__(self, message: str = "Database operation failed", **kwargs):
        super().__init__(message, error_code='DATABASE_ERROR', status_code=500, **kwargs)


class ErrorHandler:
    """Centralized error handling and logging utility"""
    
    def __init__(self, app=None):
        self.app = app
        self.logger = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize the error handler with Flask app"""
        self.app = app
        self.logger = app.logger
        self._setup_error_handlers()
        app.extensions['error_handler'] = self
    
    def _setup_error_handlers(self):
        """Set up comprehensive error handlers"""
        
        @self.app.errorhandler(SwarmDirectorError)
        def handle_swarm_director_error(error):
            return self._format_error_response(error)
        
        @self.app.errorhandler(ValidationError)
        def handle_validation_error(error):
            return self._format_error_response(error)
        
        @self.app.errorhandler(500)
        def handle_internal_server_error(error):
            self.log_error(error, severity='critical')
            return self._format_generic_error(500, "Internal Server Error", 
                                            "An unexpected error occurred")
    
    def _format_error_response(self, error: SwarmDirectorError):
        """Format SwarmDirector error into standardized response"""
        from .response_formatter import ResponseFormatter
        
        self.log_error(error, severity=self._get_error_severity(error.status_code))
        
        response_data = {
            'error_code': error.error_code,
            'message': error.message,
            'correlation_id': error.correlation_id,
            'timestamp': error.timestamp
        }
        
        if error.details:
            response_data['details'] = error.details
        
        # Extract field for ValidationError to ensure proper response format
        field = None
        if isinstance(error, ValidationError) and error.details and 'field' in error.details:
            field = error.details['field']
        
        return ResponseFormatter.error(
            message=error.message,
            error_code=error.error_code,
            status_code=error.status_code,
            field=field,
            details=response_data
        )
    
    def _format_generic_error(self, status_code: int, error_type: str, message: str):
        """Format generic HTTP error into standardized response"""
        from .response_formatter import ResponseFormatter
        
        correlation_id = str(uuid.uuid4())
        
        response_data = {
            'error_code': error_type.upper().replace(' ', '_'),
            'message': message,
            'correlation_id': correlation_id,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return ResponseFormatter.error(
            message=message,
            error_code=response_data['error_code'],
            status_code=status_code,
            details=response_data
        )
    
    def _get_error_severity(self, status_code: int) -> str:
        """Determine log severity based on HTTP status code"""
        if status_code >= 500:
            return 'error'
        elif status_code >= 400:
            return 'warning'
        else:
            return 'info'
    
    def log_error(self, error: Exception, severity: str = 'error', 
                  include_traceback: bool = False, extra_context: Dict = None):
        """Enhanced error logging with context"""
        
        context = {
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if request:
            context.update({
                'method': request.method,
                'url': request.url,
                'remote_addr': request.remote_addr,
                'user_agent': request.headers.get('User-Agent', 'Unknown')
            })
        
        if isinstance(error, SwarmDirectorError):
            context.update({
                'error_code': error.error_code,
                'status_code': error.status_code,
                'correlation_id': error.correlation_id,
                'details': error.details
            })
        
        if extra_context:
            context.update(extra_context)
        
        if include_traceback:
            context['traceback'] = traceback.format_exc()
        
        log_message = f"Error occurred: {context['error_message']}"
        
        if self.logger:
            if severity == 'critical':
                self.logger.critical(log_message, extra=context)
            elif severity == 'error':
                self.logger.error(log_message, extra=context)
            elif severity == 'warning':
                self.logger.warning(log_message, extra=context)
            else:
                self.logger.info(log_message, extra=context)
        
        return context


def require_error_handling(f):
    """Decorator to wrap functions with comprehensive error handling"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        except SwarmDirectorError:
            raise
        except Exception as e:
            error_handler = current_app.extensions.get('error_handler')
            if error_handler:
                error_handler.log_error(e, severity='error', include_traceback=True)
            
            raise SwarmDirectorError(
                message="An unexpected error occurred",
                error_code='UNEXPECTED_ERROR',
                status_code=500,
                details={'original_error': str(e)}
            )
    
    return decorated_function
