"""
Response formatting utilities for SwarmDirector API
Provides standardized response structures for consistent API communication including:
- Success responses with data
- Error responses with detailed error information
- Paginated responses with metadata
- HTTP status code management
"""

from typing import Any, Dict, List, Optional, Union
from flask import jsonify, make_response
from datetime import datetime
import math

class ResponseFormatter:
    """Standardized response formatting for SwarmDirector API"""
    
    # Standard response envelope structure
    RESPONSE_ENVELOPE = {
        'status': None,      # 'success' or 'error'
        'data': None,        # Response data (for success)
        'error': None,       # Error information (for error responses)
        'metadata': None,    # Additional metadata (pagination, timestamps, etc.)
        'timestamp': None    # ISO timestamp
    }
    
    # HTTP Status Code mappings
    STATUS_CODES = {
        # Success codes
        'OK': 200,
        'CREATED': 201,
        'ACCEPTED': 202,
        'NO_CONTENT': 204,
        
        # Client error codes
        'BAD_REQUEST': 400,
        'UNAUTHORIZED': 401,
        'FORBIDDEN': 403,
        'NOT_FOUND': 404,
        'METHOD_NOT_ALLOWED': 405,
        'CONFLICT': 409,
        'UNPROCESSABLE_ENTITY': 422,
        'TOO_MANY_REQUESTS': 429,
        
        # Server error codes
        'INTERNAL_SERVER_ERROR': 500,
        'BAD_GATEWAY': 502,
        'SERVICE_UNAVAILABLE': 503,
        'GATEWAY_TIMEOUT': 504
    }
    
    @staticmethod
    def success(data: Any = None, message: str = None, status_code: int = 200, 
                metadata: Dict[str, Any] = None) -> tuple:
        """
        Create a standardized success response
        
        Args:
            data: Response data (any JSON-serializable object)
            message: Optional success message
            status_code: HTTP status code (default: 200)
            metadata: Optional metadata dictionary
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        response_data = {
            'status': 'success',
            'data': data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        # Add message to data if provided
        if message:
            if isinstance(data, dict):
                response_data['data'] = {**data, 'message': message}
            else:
                response_data['data'] = {'result': data, 'message': message}
        
        # Add metadata if provided
        if metadata:
            response_data['metadata'] = metadata
            
        return jsonify(response_data), status_code
    
    @staticmethod
    def error(message: str, error_code: str = 'UNKNOWN_ERROR', 
              status_code: int = 400, details: Dict[str, Any] = None,
              field: str = None) -> tuple:
        """
        Create a standardized error response
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            status_code: HTTP status code (default: 400)
            details: Optional additional error details
            field: Optional field name for validation errors
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        error_data = {
            'message': message,
            'code': error_code
        }
        
        # Add field information for validation errors
        if field:
            error_data['field'] = field
            
        # Add additional details if provided
        if details:
            error_data['details'] = details
            
        response_data = {
            'status': 'error',
            'error': error_data,
            'timestamp': datetime.utcnow().isoformat() + 'Z'
        }
        
        return jsonify(response_data), status_code
    
    @staticmethod
    def paginated(items: List[Any], page: int, per_page: int, total: int,
                  status_code: int = 200, metadata: Dict[str, Any] = None) -> tuple:
        """
        Create a standardized paginated response
        
        Args:
            items: List of items for current page
            page: Current page number (1-based)
            per_page: Items per page
            total: Total number of items
            status_code: HTTP status code (default: 200)
            metadata: Optional additional metadata
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        total_pages = math.ceil(total / per_page) if per_page > 0 else 0
        has_next = page < total_pages
        has_prev = page > 1
        
        pagination_metadata = {
            'pagination': {
                'page': page,
                'per_page': per_page,
                'total': total,
                'total_pages': total_pages,
                'has_next': has_next,
                'has_prev': has_prev,
                'next_page': page + 1 if has_next else None,
                'prev_page': page - 1 if has_prev else None
            }
        }
        
        # Merge with additional metadata if provided
        if metadata:
            pagination_metadata.update(metadata)
        
        return ResponseFormatter.success(
            data={'items': items, 'count': len(items)},
            status_code=status_code,
            metadata=pagination_metadata
        )
    
    @staticmethod
    def task_created(task_id: str, message: str = "Task created successfully") -> tuple:
        """
        Standardized response for task creation
        
        Args:
            task_id: Generated task ID
            message: Success message
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.success(
            data={
                'task_id': task_id,
                'message': message
            },
            status_code=201
        )
    
    @staticmethod
    def validation_error(message: str, field: str = None, 
                        details: Dict[str, Any] = None) -> tuple:
        """
        Standardized response for validation errors
        
        Args:
            message: Validation error message
            field: Field that failed validation
            details: Additional validation details
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.error(
            message=message,
            error_code='VALIDATION_ERROR',
            status_code=400,
            field=field,
            details=details
        )
    
    @staticmethod
    def not_found(resource: str = "Resource") -> tuple:
        """
        Standardized response for not found errors
        
        Args:
            resource: Name of the resource that was not found
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.error(
            message=f"{resource} not found",
            error_code='NOT_FOUND',
            status_code=404
        )
    
    @staticmethod
    def unauthorized(message: str = "Authentication required") -> tuple:
        """
        Standardized response for unauthorized access
        
        Args:
            message: Unauthorized access message
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.error(
            message=message,
            error_code='UNAUTHORIZED',
            status_code=401
        )
    
    @staticmethod
    def forbidden(message: str = "Access forbidden") -> tuple:
        """
        Standardized response for forbidden access
        
        Args:
            message: Forbidden access message
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.error(
            message=message,
            error_code='FORBIDDEN',
            status_code=403
        )
    
    @staticmethod
    def rate_limited(retry_after: int = None, message: str = "Rate limit exceeded") -> tuple:
        """
        Standardized response for rate limiting
        
        Args:
            retry_after: Seconds until retry is allowed
            message: Rate limiting message
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        details = {}
        if retry_after:
            details['retry_after'] = retry_after
            
        response, status_code = ResponseFormatter.error(
            message=message,
            error_code='RATE_LIMIT_EXCEEDED',
            status_code=429,
            details=details
        )
        
        # Add Retry-After header if specified
        if retry_after:
            response.headers['Retry-After'] = str(retry_after)
            
        return response, status_code
    
    @staticmethod
    def internal_error(message: str = "Internal server error") -> tuple:
        """
        Standardized response for internal server errors
        
        Args:
            message: Error message
            
        Returns:
            Tuple of (Flask Response, status_code)
        """
        return ResponseFormatter.error(
            message=message,
            error_code='INTERNAL_SERVER_ERROR',
            status_code=500
        )

class APIResponse:
    """Convenience class for API response creation"""
    
    @staticmethod
    def json_success(data: Any = None, **kwargs) -> tuple:
        """Shorthand for JSON success response"""
        return ResponseFormatter.success(data=data, **kwargs)
    
    @staticmethod
    def json_error(message: str, **kwargs) -> tuple:
        """Shorthand for JSON error response"""
        return ResponseFormatter.error(message=message, **kwargs)
    
    @staticmethod
    def json_paginated(items: List[Any], **kwargs) -> tuple:
        """Shorthand for JSON paginated response"""
        return ResponseFormatter.paginated(items=items, **kwargs) 