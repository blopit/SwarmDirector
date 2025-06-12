# Utils Directory

## Purpose
Contains utility functions, helper classes, and shared components that support the SwarmDirector application. This directory provides cross-cutting functionality including database management, logging, error handling, validation, AutoGen integration, and various operational utilities used throughout the system.

## Structure
```
utils/
├── __init__.py                  # Utility package exports with optional imports
├── database.py                  # Database utilities and connection management
├── logging.py                   # Centralized logging configuration
├── migrations.py                # Database migration utilities
├── autogen_helpers.py           # Legacy AutoGen integration helpers
├── autogen_integration.py       # Advanced AutoGen framework integration
├── autogen_config.py            # AutoGen configuration templates
├── conversation_analytics.py    # Conversation analysis and metrics
├── error_handler.py             # Error handling and recovery utilities
├── rate_limiter.py              # API rate limiting implementation
├── response_formatter.py        # Response formatting utilities
├── validation.py                # Input validation and sanitization
└── db_cli.py                    # Database CLI commands and tools
```

## Guidelines

### 1. Organization
- **Functional Grouping**: Group related utilities in single modules (e.g., all validation in `validation.py`)
- **Optional Dependencies**: Handle optional dependencies gracefully with try/except imports
- **Shared Constants**: Define shared constants and configurations in appropriate modules
- **Utility Registration**: Export all public utilities through `__init__.py` with clear naming
- **Cross-Module Dependencies**: Minimize dependencies between utility modules

### 2. Naming
- **Module Names**: Use descriptive names indicating functionality (e.g., `error_handler.py`, `rate_limiter.py`)
- **Function Names**: Use action-oriented names (e.g., `validate_email`, `setup_logging`, `handle_error`)
- **Class Names**: Use descriptive PascalCase names (e.g., `RateLimiter`, `ErrorHandler`)
- **Constants**: Use UPPER_CASE for module-level constants (e.g., `DEFAULT_TIMEOUT`, `MAX_RETRIES`)
- **Private Functions**: Use underscore prefix for internal functions (e.g., `_validate_config`)

### 3. Implementation
- **Pure Functions**: Prefer pure functions without side effects when possible
- **Error Handling**: Implement comprehensive error handling with appropriate exception types
- **Type Annotations**: Use complete type hints for all public functions
- **Documentation**: Provide comprehensive docstrings with examples
- **Configuration**: Support configuration through parameters and environment variables

### 4. Documentation
- **Module Docstrings**: Document module purpose and main functionality
- **Function Docstrings**: Include parameters, return values, exceptions, and usage examples
- **Configuration Documentation**: Document all configuration options and their effects
- **Integration Examples**: Provide examples of utility usage in different contexts

## Best Practices

### 1. Error Handling
- **Graceful Degradation**: Handle missing dependencies without crashing the application
- **Informative Errors**: Provide clear, actionable error messages
- **Error Recovery**: Implement retry mechanisms and fallback strategies
- **Exception Chaining**: Use `raise ... from ...` to preserve error context
- **Logging Integration**: Log errors with appropriate levels and context

### 2. Security
- **Input Sanitization**: Validate and sanitize all external inputs
- **Secure Defaults**: Use secure default configurations
- **Sensitive Data**: Never log or expose sensitive information
- **Injection Prevention**: Prevent injection attacks in all input processing
- **Access Control**: Implement proper authorization checks where applicable

### 3. Performance
- **Efficient Algorithms**: Use efficient algorithms and data structures
- **Caching**: Cache expensive computations and external API calls
- **Resource Management**: Properly manage resources (connections, files, memory)
- **Async Support**: Provide async versions of I/O-bound utilities
- **Monitoring**: Include performance monitoring and metrics

### 4. Testing
- **Unit Tests**: Test each utility function in isolation
- **Mock Dependencies**: Use mocks for external services and resources
- **Edge Cases**: Test error conditions and edge cases thoroughly
- **Performance Tests**: Include benchmarks for critical utilities
- **Integration Tests**: Test utilities in realistic usage scenarios

### 5. Documentation
- **Usage Examples**: Provide complete, working examples
- **Configuration Guides**: Document all configuration options
- **Best Practices**: Include recommendations for optimal usage
- **Troubleshooting**: Document common issues and solutions

## Example

### Complete Utility Module Implementation

```python
"""
Example: Comprehensive Validation Utility Module
Demonstrates advanced utility implementation with error handling and extensibility
"""

import re
import json
import ipaddress
from typing import Any, Dict, List, Optional, Union, Callable
from urllib.parse import urlparse
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class ValidationError(Exception):
    """Custom exception for validation errors"""
    def __init__(self, message: str, field: Optional[str] = None, value: Any = None):
        self.message = message
        self.field = field
        self.value = value
        super().__init__(self.format_message())
    
    def format_message(self) -> str:
        """Format error message with field and value context"""
        if self.field:
            return f"Validation error for field '{self.field}': {self.message}"
        return f"Validation error: {self.message}"

class Validator:
    """
    Comprehensive validation utility class
    
    Provides validation methods for common data types and formats
    with extensible validation rules and clear error reporting.
    """
    
    # Email validation regex (RFC 5322 compliant)
    EMAIL_REGEX = re.compile(
        r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    )
    
    # Phone number regex (international format)
    PHONE_REGEX = re.compile(
        r'^\+?1?[-.\s]?\(?[0-9]{3}\)?[-.\s]?[0-9]{3}[-.\s]?[0-9]{4}$'
    )
    
    # URL validation regex
    URL_REGEX = re.compile(
        r'^https?://(?:[-\w.])+(?:\:[0-9]+)?(?:/(?:[\w/_.])*(?:\?(?:[\w&=%.])*)?(?:\#(?:[\w.])*)?)?$'
    )
    
    @staticmethod
    def validate_email(email: str, required: bool = True) -> bool:
        """
        Validate email address format
        
        Args:
            email: Email address to validate
            required: Whether email is required (affects empty string handling)
            
        Returns:
            bool: True if email is valid
            
        Raises:
            ValidationError: If email format is invalid
        """
        if not email:
            if required:
                raise ValidationError("Email address is required", "email", email)
            return True
        
        if not isinstance(email, str):
            raise ValidationError("Email must be a string", "email", email)
        
        if len(email) > 254:  # RFC 5321 limit
            raise ValidationError("Email address is too long (max 254 characters)", "email", email)
        
        if not Validator.EMAIL_REGEX.match(email):
            raise ValidationError("Invalid email address format", "email", email)
        
        return True
    
    @staticmethod
    def validate_phone(phone: str, required: bool = True) -> bool:
        """
        Validate phone number format
        
        Args:
            phone: Phone number to validate
            required: Whether phone is required
            
        Returns:
            bool: True if phone is valid
            
        Raises:
            ValidationError: If phone format is invalid
        """
        if not phone:
            if required:
                raise ValidationError("Phone number is required", "phone", phone)
            return True
        
        if not isinstance(phone, str):
            raise ValidationError("Phone number must be a string", "phone", phone)
        
        # Remove common formatting characters for validation
        cleaned_phone = re.sub(r'[-.\s()]', '', phone)
        
        if not cleaned_phone.replace('+', '').isdigit():
            raise ValidationError("Phone number must contain only digits and formatting characters", "phone", phone)
        
        if not Validator.PHONE_REGEX.match(phone):
            raise ValidationError("Invalid phone number format", "phone", phone)
        
        return True
    
    @staticmethod
    def validate_url(url: str, required: bool = True, allowed_schemes: Optional[List[str]] = None) -> bool:
        """
        Validate URL format and scheme
        
        Args:
            url: URL to validate
            required: Whether URL is required
            allowed_schemes: List of allowed URL schemes (default: ['http', 'https'])
            
        Returns:
            bool: True if URL is valid
            
        Raises:
            ValidationError: If URL format is invalid
        """
        if not url:
            if required:
                raise ValidationError("URL is required", "url", url)
            return True
        
        if not isinstance(url, str):
            raise ValidationError("URL must be a string", "url", url)
        
        allowed_schemes = allowed_schemes or ['http', 'https']
        
        try:
            parsed = urlparse(url)
            
            if not parsed.scheme:
                raise ValidationError("URL must include a scheme (http/https)", "url", url)
            
            if parsed.scheme not in allowed_schemes:
                raise ValidationError(f"URL scheme must be one of: {allowed_schemes}", "url", url)
            
            if not parsed.netloc:
                raise ValidationError("URL must include a domain", "url", url)
            
        except Exception as e:
            raise ValidationError(f"Invalid URL format: {str(e)}", "url", url)
        
        return True
    
    @staticmethod
    def validate_ip_address(ip: str, required: bool = True, version: Optional[int] = None) -> bool:
        """
        Validate IP address format
        
        Args:
            ip: IP address to validate
            required: Whether IP is required
            version: IP version to validate (4, 6, or None for both)
            
        Returns:
            bool: True if IP is valid
            
        Raises:
            ValidationError: If IP format is invalid
        """
        if not ip:
            if required:
                raise ValidationError("IP address is required", "ip", ip)
            return True
        
        if not isinstance(ip, str):
            raise ValidationError("IP address must be a string", "ip", ip)
        
        try:
            ip_obj = ipaddress.ip_address(ip)
            
            if version == 4 and not isinstance(ip_obj, ipaddress.IPv4Address):
                raise ValidationError("Must be a valid IPv4 address", "ip", ip)
            
            if version == 6 and not isinstance(ip_obj, ipaddress.IPv6Address):
                raise ValidationError("Must be a valid IPv6 address", "ip", ip)
            
        except ValueError as e:
            raise ValidationError(f"Invalid IP address: {str(e)}", "ip", ip)
        
        return True
    
    @staticmethod
    def validate_json(data: str, required: bool = True) -> bool:
        """
        Validate JSON format
        
        Args:
            data: JSON string to validate
            required: Whether JSON is required
            
        Returns:
            bool: True if JSON is valid
            
        Raises:
            ValidationError: If JSON format is invalid
        """
        if not data:
            if required:
                raise ValidationError("JSON data is required", "json", data)
            return True
        
        if not isinstance(data, str):
            raise ValidationError("JSON data must be a string", "json", data)
        
        try:
            json.loads(data)
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON format: {str(e)}", "json", data)
        
        return True
    
    @staticmethod
    def validate_datetime(dt: str, required: bool = True, format_str: str = "%Y-%m-%dT%H:%M:%S") -> bool:
        """
        Validate datetime format
        
        Args:
            dt: Datetime string to validate
            required: Whether datetime is required
            format_str: Expected datetime format
            
        Returns:
            bool: True if datetime is valid
            
        Raises:
            ValidationError: If datetime format is invalid
        """
        if not dt:
            if required:
                raise ValidationError("Datetime is required", "datetime", dt)
            return True
        
        if not isinstance(dt, str):
            raise ValidationError("Datetime must be a string", "datetime", dt)
        
        try:
            datetime.strptime(dt, format_str)
        except ValueError as e:
            raise ValidationError(f"Invalid datetime format (expected {format_str}): {str(e)}", "datetime", dt)
        
        return True

def validate_required_fields(data: Dict[str, Any], required_fields: List[str]) -> None:
    """
    Validate that all required fields are present in data
    
    Args:
        data: Data dictionary to validate
        required_fields: List of required field names
        
    Raises:
        ValidationError: If any required fields are missing
    """
    missing_fields = [field for field in required_fields if field not in data or data[field] is None]
    
    if missing_fields:
        raise ValidationError(f"Missing required fields: {', '.join(missing_fields)}")

def validate_field_types(data: Dict[str, Any], field_types: Dict[str, type]) -> None:
    """
    Validate field types in data dictionary
    
    Args:
        data: Data dictionary to validate
        field_types: Dictionary mapping field names to expected types
        
    Raises:
        ValidationError: If any fields have incorrect types
    """
    for field, expected_type in field_types.items():
        if field in data and data[field] is not None:
            if not isinstance(data[field], expected_type):
                raise ValidationError(
                    f"Field '{field}' must be of type {expected_type.__name__}, got {type(data[field]).__name__}",
                    field,
                    data[field]
                )

def validate_field_ranges(data: Dict[str, Any], field_ranges: Dict[str, Dict[str, Union[int, float]]]) -> None:
    """
    Validate numeric field ranges
    
    Args:
        data: Data dictionary to validate
        field_ranges: Dictionary mapping field names to range specifications
                     Format: {'field': {'min': value, 'max': value}}
        
    Raises:
        ValidationError: If any fields are outside specified ranges
    """
    for field, range_spec in field_ranges.items():
        if field in data and data[field] is not None:
            value = data[field]
            
            if 'min' in range_spec and value < range_spec['min']:
                raise ValidationError(
                    f"Field '{field}' must be >= {range_spec['min']}, got {value}",
                    field,
                    value
                )
            
            if 'max' in range_spec and value > range_spec['max']:
                raise ValidationError(
                    f"Field '{field}' must be <= {range_spec['max']}, got {value}",
                    field,
                    value
                )

def sanitize_string(value: str, max_length: Optional[int] = None, strip_html: bool = True) -> str:
    """
    Sanitize string input
    
    Args:
        value: String to sanitize
        max_length: Maximum allowed length
        strip_html: Whether to strip HTML tags
        
    Returns:
        Sanitized string
    """
    if not isinstance(value, str):
        return str(value)
    
    # Strip whitespace
    sanitized = value.strip()
    
    # Strip HTML tags if requested
    if strip_html:
        import html
        sanitized = html.escape(sanitized)
    
    # Truncate if necessary
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized

# Validation decorator
def validate_input(**validation_rules):
    """
    Decorator for automatic input validation
    
    Args:
        **validation_rules: Validation rules for function parameters
        
    Example:
        @validate_input(email=Validator.validate_email, age={'type': int, 'min': 0, 'max': 150})
        def create_user(email: str, age: int):
            pass
    """
    def decorator(func: Callable) -> Callable:
        def wrapper(*args, **kwargs):
            # Get function parameter names
            import inspect
            sig = inspect.signature(func)
            param_names = list(sig.parameters.keys())
            
            # Build parameter dictionary
            params = {}
            for i, arg in enumerate(args):
                if i < len(param_names):
                    params[param_names[i]] = arg
            params.update(kwargs)
            
            # Apply validation rules
            for param_name, rule in validation_rules.items():
                if param_name in params:
                    value = params[param_name]
                    
                    if callable(rule):
                        # Direct validation function
                        rule(value)
                    elif isinstance(rule, dict):
                        # Complex validation rule
                        if 'type' in rule and not isinstance(value, rule['type']):
                            raise ValidationError(f"Parameter '{param_name}' must be of type {rule['type'].__name__}")
                        
                        if 'min' in rule and value < rule['min']:
                            raise ValidationError(f"Parameter '{param_name}' must be >= {rule['min']}")
                        
                        if 'max' in rule and value > rule['max']:
                            raise ValidationError(f"Parameter '{param_name}' must be <= {rule['max']}")
            
            return func(*args, **kwargs)
        return wrapper
    return decorator

# Convenience functions
def validate_email(email: str) -> bool:
    """Convenience function for email validation"""
    return Validator.validate_email(email)

def validate_phone(phone: str) -> bool:
    """Convenience function for phone validation"""
    return Validator.validate_phone(phone)

def validate_url(url: str) -> bool:
    """Convenience function for URL validation"""
    return Validator.validate_url(url)

# Export all validation functions
__all__ = [
    'ValidationError',
    'Validator',
    'validate_required_fields',
    'validate_field_types',
    'validate_field_ranges',
    'sanitize_string',
    'validate_input',
    'validate_email',
    'validate_phone',
    'validate_url'
]
```

## Related Documentation
- [Error Handling Guide](../../../docs/development/debugging.md) - Error handling patterns
- [Configuration Management](../../../docs/deployment/local_development.md) - Configuration utilities
- [Database Utilities](../../../docs/architecture/database_design.md) - Database utility usage
- [AutoGen Integration](../../../docs/api/agents.md#autogen-integration) - AutoGen utility documentation
- [API Validation](../../../docs/api/README.md#request-validation) - Input validation patterns
