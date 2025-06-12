"""
Request validation utilities for SwarmDirector API
Provides comprehensive validation for incoming API requests including:
- JSON schema validation
- Input sanitization  
- Authentication verification
- Content-type validation
"""

import re
import json
import logging
from typing import Dict, Any, Optional, List, Tuple
from functools import wraps
from flask import request, jsonify, current_app
import jsonschema
from jsonschema import validate, ValidationError as JsonSchemaValidationError

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom validation error with detailed error information"""
    def __init__(self, message: str, error_code: str = "VALIDATION_ERROR", field: str = None):
        self.message = message
        self.error_code = error_code
        self.field = field
        super().__init__(self.message)

class RequestValidator:
    """Comprehensive request validation for API endpoints"""
    
    # Common validation patterns
    PATTERNS = {
        'task_type': re.compile(r'^[a-zA-Z0-9_-]{1,50}$'),
        'priority': re.compile(r'^(low|medium|high|critical)$'),
        'email': re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'),
        'alphanumeric': re.compile(r'^[a-zA-Z0-9_-]+$'),
        'safe_string': re.compile(r'^[a-zA-Z0-9\s._-]{1,200}$')
    }
    
    # Dangerous patterns to sanitize
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',   # Event handlers
        r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>',  # Iframe tags
        r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>',  # Object tags
    ]
    
    @staticmethod
    def validate_content_type(required_type: str = 'application/json') -> bool:
        """Validate request content type"""
        if not request.content_type:
            raise ValidationError("Content-Type header is required", "MISSING_CONTENT_TYPE")
        
        if not request.content_type.startswith(required_type):
            raise ValidationError(
                f"Content-Type must be {required_type}", 
                "INVALID_CONTENT_TYPE"
            )
        return True
    
    @staticmethod
    def validate_json_body() -> Dict[str, Any]:
        """Validate and parse JSON request body"""
        if not request.is_json:
            raise ValidationError("Request must contain valid JSON", "INVALID_JSON")
        
        try:
            data = request.get_json(force=True)
            if not data:
                raise ValidationError("Request body cannot be empty", "EMPTY_BODY")
            return data
        except Exception as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}", "JSON_PARSE_ERROR")
    
    @staticmethod
    def sanitize_input(value: Any) -> Any:
        """Sanitize input to prevent XSS and injection attacks"""
        if isinstance(value, str):
            # Remove dangerous patterns
            for pattern in RequestValidator.DANGEROUS_PATTERNS:
                value = re.sub(pattern, '', value, flags=re.IGNORECASE)
            
            # Escape HTML characters
            value = (value.replace('&', '&amp;')
                         .replace('<', '&lt;')
                         .replace('>', '&gt;')
                         .replace('"', '&quot;')
                         .replace("'", '&#x27;'))
            
            # Limit length
            if len(value) > 10000:  # 10KB limit
                raise ValidationError("Input too long", "INPUT_TOO_LONG")
                
        elif isinstance(value, dict):
            return {k: RequestValidator.sanitize_input(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [RequestValidator.sanitize_input(v) for v in value]
        
        return value
    
    @staticmethod
    def validate_field(value: Any, field_name: str, pattern_name: str = None, 
                      required: bool = True, max_length: int = None) -> Any:
        """Validate individual field with pattern matching"""
        if required and (value is None or value == ''):
            raise ValidationError(f"Field '{field_name}' is required", "REQUIRED_FIELD", field_name)
        
        if value is None:
            return value
        
        # Convert to string for pattern matching
        str_value = str(value)
        
        # Length validation
        if max_length and len(str_value) > max_length:
            raise ValidationError(
                f"Field '{field_name}' exceeds maximum length of {max_length}", 
                "FIELD_TOO_LONG", 
                field_name
            )
        
        # Pattern validation
        if pattern_name and pattern_name in RequestValidator.PATTERNS:
            pattern = RequestValidator.PATTERNS[pattern_name]
            if not pattern.match(str_value):
                raise ValidationError(
                    f"Field '{field_name}' has invalid format", 
                    "INVALID_FORMAT", 
                    field_name
                )
        
        return RequestValidator.sanitize_input(value)

class SchemaValidator:
    """JSON schema validation for structured request data"""
    
    # Task submission schema
    TASK_SCHEMA = {
        "type": "object",
        "properties": {
            "type": {
                "type": "string",
                "pattern": "^[a-zA-Z0-9_-]{1,50}$",
                "description": "Task type identifier"
            },
            "title": {
                "type": "string",
                "minLength": 1,
                "maxLength": 200,
                "description": "Human-readable task title"
            },
            "description": {
                "type": "string",
                "maxLength": 1000,
                "description": "Detailed task description"
            },
            "priority": {
                "type": "string",
                "enum": ["low", "medium", "high", "critical"],
                "default": "medium"
            },
            "args": {
                "type": "object",
                "description": "Task-specific arguments"
            },
            "metadata": {
                "type": "object",
                "description": "Additional metadata for task"
            }
        },
        "required": ["type"],
        "additionalProperties": True
    }
    
    @staticmethod
    def validate_schema(data: Dict[str, Any], schema: Dict[str, Any] = None) -> Dict[str, Any]:
        """Validate data against JSON schema"""
        if schema is None:
            schema = SchemaValidator.TASK_SCHEMA
        
        try:
            validate(instance=data, schema=schema)
            return data
        except JsonSchemaValidationError as e:
            # Convert jsonschema error to our custom error
            field_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
            raise ValidationError(
                f"Schema validation failed at '{field_path}': {e.message}",
                "SCHEMA_VALIDATION_ERROR",
                field_path
            )

class AuthValidator:
    """Authentication and authorization validation"""
    
    @staticmethod
    def extract_auth_token() -> Optional[str]:
        """Extract authentication token from request headers"""
        auth_header = request.headers.get('Authorization', '')
        
        if auth_header.startswith('Bearer '):
            return auth_header[7:]  # Remove 'Bearer ' prefix
        
        # Also check for API key in headers
        api_key = request.headers.get('X-API-Key', '')
        if api_key:
            return api_key
        
        return None
    
    @staticmethod
    def validate_auth_token(token: str) -> Dict[str, Any]:
        """Validate authentication token and return user info"""
        if not token:
            raise ValidationError("Authentication token is required", "MISSING_AUTH_TOKEN")
        
        # For now, implement a simple token validation
        # In production, this would validate against a proper auth service
        if len(token) < 10:
            raise ValidationError("Invalid authentication token", "INVALID_AUTH_TOKEN")
        
        # Mock user info - replace with real auth service
        return {
            "user_id": "user_123",
            "permissions": ["task:submit", "task:read"],
            "rate_limit": 100  # requests per hour
        }

def require_auth(f):
    """Decorator to require authentication for endpoint"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        try:
            token = AuthValidator.extract_auth_token()
            user_info = AuthValidator.validate_auth_token(token)
            # Add user info to request context
            request.user_info = user_info
            return f(*args, **kwargs)
        except ValidationError as e:
            return jsonify({
                'status': 'error',
                'error': e.message,
                'error_code': e.error_code
            }), 401
    return decorated_function

def validate_request(schema: Dict[str, Any] = None, require_auth: bool = False):
    """Decorator for comprehensive request validation"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # 1. Content-type validation
                RequestValidator.validate_content_type()
                
                # 2. JSON body validation
                data = RequestValidator.validate_json_body()
                
                # 3. Schema validation
                validated_data = SchemaValidator.validate_schema(data, schema)
                
                # 4. Authentication validation (if required)
                if require_auth:
                    token = AuthValidator.extract_auth_token()
                    user_info = AuthValidator.validate_auth_token(token)
                    request.user_info = user_info
                
                # 5. Add validated data to request
                request.validated_data = validated_data
                
                return f(*args, **kwargs)
                
            except ValidationError as e:
                status_code = 401 if e.error_code in ['MISSING_AUTH_TOKEN', 'INVALID_AUTH_TOKEN'] else 400
                return jsonify({
                    'status': 'error',
                    'error': e.message,
                    'error_code': e.error_code,
                    'field': e.field
                }), status_code
            except Exception as e:
                logger.error(f"Unexpected validation error: {str(e)}")
                return jsonify({
                    'status': 'error',
                    'error': 'Internal validation error',
                    'error_code': 'INTERNAL_ERROR'
                }), 500
                
        return decorated_function
    return decorator 