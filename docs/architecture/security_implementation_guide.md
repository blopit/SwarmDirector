# Security Implementation Guide

<!-- Version: 1.0 • Last updated: 2025-06-18 • Author: SwarmDirector Team -->

This guide provides comprehensive security implementation patterns and strategies for SwarmDirector, including JWT authentication, authorization, input validation, and threat mitigation.

## 📋 Table of Contents

1. [Security Architecture Overview](#security-architecture-overview)
2. [JWT Authentication Implementation](#jwt-authentication-implementation)
3. [Authorization and Access Control](#authorization-and-access-control)
4. [Input Validation and Sanitization](#input-validation-and-sanitization)
5. [Security Headers and HTTPS](#security-headers-and-https)
6. [Rate Limiting and DDoS Protection](#rate-limiting-and-ddos-protection)
7. [Security Monitoring and Logging](#security-monitoring-and-logging)

## 🔒 Security Architecture Overview

### Security Layers

```
┌─────────────────────────────────────────────────────────┐
│                    WAF / DDoS Protection                │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│                 Load Balancer (HTTPS)                  │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│             Rate Limiting & Security Headers           │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│           JWT Authentication & Authorization            │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│           Input Validation & Sanitization              │
└─────────────────────┬───────────────────────────────────┘
                      ▼
┌─────────────────────────────────────────────────────────┐
│              Application Logic (Secure)                │
└─────────────────────────────────────────────────────────┘
```

### Security Principles

1. **Defense in Depth**: Multiple security layers
2. **Least Privilege**: Minimal required permissions
3. **Zero Trust**: Verify every request
4. **Secure by Default**: Secure configuration defaults
5. **Fail Securely**: Graceful security failure handling

## 🎫 JWT Authentication Implementation

### JWT Service Implementation

```python
# src/swarm_director/auth/jwt_service.py
import jwt
import secrets
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from flask import current_app
import logging

class JWTService:
    """JWT token management service"""
    
    def __init__(self, app=None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize JWT service with Flask app"""
        app.config.setdefault('JWT_SECRET_KEY', secrets.token_hex(32))
        app.config.setdefault('JWT_ACCESS_TOKEN_EXPIRES', timedelta(hours=1))
        app.config.setdefault('JWT_REFRESH_TOKEN_EXPIRES', timedelta(days=30))
        app.config.setdefault('JWT_ALGORITHM', 'HS256')
        
        self.secret_key = app.config['JWT_SECRET_KEY']
        self.access_token_expires = app.config['JWT_ACCESS_TOKEN_EXPIRES']
        self.refresh_token_expires = app.config['JWT_REFRESH_TOKEN_EXPIRES']
        self.algorithm = app.config['JWT_ALGORITHM']
    
    def generate_access_token(self, user_id: str, roles: list = None) -> str:
        """Generate JWT access token"""
        if roles is None:
            roles = []
        
        payload = {
            'user_id': user_id,
            'roles': roles,
            'token_type': 'access',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.access_token_expires,
            'jti': secrets.token_hex(16)  # JWT ID for token revocation
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def generate_refresh_token(self, user_id: str) -> str:
        """Generate JWT refresh token"""
        payload = {
            'user_id': user_id,
            'token_type': 'refresh',
            'iat': datetime.utcnow(),
            'exp': datetime.utcnow() + self.refresh_token_expires,
            'jti': secrets.token_hex(16)
        }
        
        return jwt.encode(payload, self.secret_key, algorithm=self.algorithm)
    
    def verify_token(self, token: str) -> Optional[Dict[str, Any]]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token, 
                self.secret_key, 
                algorithms=[self.algorithm],
                options={'verify_exp': True}
            )
            
            # Additional validation
            if 'user_id' not in payload:
                return None
            
            # Check if token is blacklisted (implement token blacklist)
            if self._is_token_blacklisted(payload.get('jti')):
                return None
            
            return payload
            
        except jwt.ExpiredSignatureError:
            logging.warning("JWT token expired")
            return None
        except jwt.InvalidTokenError as e:
            logging.warning(f"Invalid JWT token: {e}")
            return None
    
    def refresh_access_token(self, refresh_token: str) -> Optional[str]:
        """Generate new access token from refresh token"""
        payload = self.verify_token(refresh_token)
        
        if not payload or payload.get('token_type') != 'refresh':
            return None
        
        # Generate new access token
        user_id = payload['user_id']
        # Get user roles from database
        roles = self._get_user_roles(user_id)
        
        return self.generate_access_token(user_id, roles)
    
    def revoke_token(self, token: str) -> bool:
        """Revoke a JWT token by adding to blacklist"""
        payload = self.verify_token(token)
        if payload:
            jti = payload.get('jti')
            exp = payload.get('exp')
            
            # Add to blacklist with expiration
            self._blacklist_token(jti, exp)
            return True
        
        return False
    
    def _is_token_blacklisted(self, jti: str) -> bool:
        """Check if token is blacklisted"""
        # Implement Redis-based token blacklist
        from flask import current_app
        redis_client = current_app.extensions.get('redis')
        
        if redis_client:
            return redis_client.exists(f"blacklist:{jti}")
        
        return False
    
    def _blacklist_token(self, jti: str, exp: int):
        """Add token to blacklist"""
        from flask import current_app
        redis_client = current_app.extensions.get('redis')
        
        if redis_client:
            # Set expiry to match token expiry
            ttl = exp - datetime.utcnow().timestamp()
            if ttl > 0:
                redis_client.setex(f"blacklist:{jti}", int(ttl), "1")
    
    def _get_user_roles(self, user_id: str) -> list:
        """Get user roles from database"""
        # Implement user role lookup
        # This would typically query the database
        return ['user']  # Default role
```

### Authentication Decorators

```python
# src/swarm_director/auth/decorators.py
from functools import wraps
from flask import request, jsonify, current_app, g
from .jwt_service import JWTService

def jwt_required(optional: bool = False):
    """Decorator to require JWT authentication"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            token = None
            auth_header = request.headers.get('Authorization')
            
            if auth_header:
                try:
                    # Extract token from "Bearer <token>"
                    token = auth_header.split(' ')[1]
                except IndexError:
                    if not optional:
                        return jsonify({'error': 'Invalid token format'}), 401
            
            if not token and not optional:
                return jsonify({'error': 'Token is missing'}), 401
            
            if token:
                jwt_service = current_app.extensions['jwt']
                payload = jwt_service.verify_token(token)
                
                if not payload:
                    if not optional:
                        return jsonify({'error': 'Token is invalid or expired'}), 401
                else:
                    # Store user info in Flask g object
                    g.current_user = {
                        'user_id': payload['user_id'],
                        'roles': payload.get('roles', []),
                        'token_type': payload.get('token_type')
                    }
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def role_required(required_roles: list):
    """Decorator to require specific roles"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            user_roles = g.current_user.get('roles', [])
            
            if not any(role in user_roles for role in required_roles):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def admin_required(f):
    """Decorator to require admin role"""
    return role_required(['admin'])(f)
```

## 🛡️ Authorization and Access Control

### Role-Based Access Control (RBAC)

```python
# src/swarm_director/auth/rbac.py
from enum import Enum
from typing import Set, Dict, Any
from dataclasses import dataclass

class Permission(Enum):
    """System permissions"""
    # Agent permissions
    AGENT_CREATE = "agent:create"
    AGENT_READ = "agent:read"
    AGENT_UPDATE = "agent:update"
    AGENT_DELETE = "agent:delete"
    AGENT_EXECUTE = "agent:execute"
    
    # Task permissions
    TASK_CREATE = "task:create"
    TASK_READ = "task:read"
    TASK_UPDATE = "task:update"
    TASK_DELETE = "task:delete"
    
    # Admin permissions
    USER_MANAGE = "user:manage"
    SYSTEM_CONFIG = "system:config"
    LOGS_READ = "logs:read"

@dataclass
class Role:
    """Role definition with permissions"""
    name: str
    permissions: Set[Permission]
    description: str = ""

class RBACManager:
    """Role-Based Access Control manager"""
    
    def __init__(self):
        self.roles = self._define_default_roles()
    
    def _define_default_roles(self) -> Dict[str, Role]:
        """Define default system roles"""
        return {
            'admin': Role(
                name='admin',
                permissions={
                    Permission.AGENT_CREATE, Permission.AGENT_READ, 
                    Permission.AGENT_UPDATE, Permission.AGENT_DELETE, 
                    Permission.AGENT_EXECUTE,
                    Permission.TASK_CREATE, Permission.TASK_READ, 
                    Permission.TASK_UPDATE, Permission.TASK_DELETE,
                    Permission.USER_MANAGE, Permission.SYSTEM_CONFIG, 
                    Permission.LOGS_READ
                },
                description="Full system access"
            ),
            'agent_manager': Role(
                name='agent_manager',
                permissions={
                    Permission.AGENT_CREATE, Permission.AGENT_READ, 
                    Permission.AGENT_UPDATE, Permission.AGENT_EXECUTE,
                    Permission.TASK_CREATE, Permission.TASK_READ, 
                    Permission.TASK_UPDATE
                },
                description="Manage agents and tasks"
            ),
            'operator': Role(
                name='operator',
                permissions={
                    Permission.AGENT_READ, Permission.AGENT_EXECUTE,
                    Permission.TASK_READ, Permission.TASK_UPDATE
                },
                description="Execute agents and view tasks"
            ),
            'viewer': Role(
                name='viewer',
                permissions={
                    Permission.AGENT_READ, Permission.TASK_READ
                },
                description="Read-only access"
            )
        }
    
    def has_permission(self, user_roles: list, permission: Permission) -> bool:
        """Check if user has specific permission"""
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role and permission in role.permissions:
                return True
        return False
    
    def get_user_permissions(self, user_roles: list) -> Set[Permission]:
        """Get all permissions for user roles"""
        permissions = set()
        for role_name in user_roles:
            role = self.roles.get(role_name)
            if role:
                permissions.update(role.permissions)
        return permissions

def permission_required(permission: Permission):
    """Decorator to require specific permission"""
    def decorator(f):
        @wraps(f)
        @jwt_required()
        def decorated_function(*args, **kwargs):
            rbac = current_app.extensions['rbac']
            user_roles = g.current_user.get('roles', [])
            
            if not rbac.has_permission(user_roles, permission):
                return jsonify({'error': 'Insufficient permissions'}), 403
            
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator
```

## 🔍 Input Validation and Sanitization

### Comprehensive Input Validation

```python
# src/swarm_director/security/validation.py
import re
import html
import bleach
from typing import Any, Dict, List, Optional
from marshmallow import Schema, fields, validate, ValidationError

class SecurityValidator:
    """Security-focused input validator"""
    
    # Dangerous patterns to detect
    DANGEROUS_PATTERNS = [
        r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>',  # Script tags
        r'javascript:',  # JavaScript URLs
        r'on\w+\s*=',   # Event handlers
        r'<iframe\b[^<]*(?:(?!<\/iframe>)<[^<]*)*<\/iframe>',  # Iframe tags
        r'<object\b[^<]*(?:(?!<\/object>)<[^<]*)*<\/object>',  # Object tags
        r'eval\s*\(',   # eval() calls
        r'\.\./',       # Path traversal
        r'\/etc\/passwd',  # System file access
        r'DROP\s+TABLE',   # SQL injection
        r'UNION\s+SELECT'  # SQL injection
    ]
    
    @staticmethod
    def sanitize_html(value: str) -> str:
        """Sanitize HTML content"""
        if not isinstance(value, str):
            return value
        
        # Allow limited HTML tags
        allowed_tags = ['p', 'br', 'strong', 'em', 'u', 'ol', 'ul', 'li']
        allowed_attributes = {}
        
        return bleach.clean(
            value, 
            tags=allowed_tags, 
            attributes=allowed_attributes,
            strip=True
        )
    
    @staticmethod
    def sanitize_input(value: Any) -> Any:
        """General input sanitization"""
        if isinstance(value, str):
            # Check for dangerous patterns
            for pattern in SecurityValidator.DANGEROUS_PATTERNS:
                if re.search(pattern, value, re.IGNORECASE):
                    raise ValidationError(f"Potentially dangerous content detected")
            
            # HTML escape
            value = html.escape(value)
            
            # Limit length
            if len(value) > 10000:  # 10KB limit
                raise ValidationError("Input too long")
        
        elif isinstance(value, dict):
            return {k: SecurityValidator.sanitize_input(v) for k, v in value.items()}
        
        elif isinstance(value, list):
            return [SecurityValidator.sanitize_input(v) for v in value]
        
        return value
    
    @staticmethod
    def validate_email(email: str) -> bool:
        """Validate email format"""
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
    
    @staticmethod
    def validate_uuid(uuid_string: str) -> bool:
        """Validate UUID format"""
        pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
        return bool(re.match(pattern, uuid_string, re.IGNORECASE))

# Marshmallow schemas for API validation
class AgentCreateSchema(Schema):
    """Schema for agent creation"""
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=1, max=100),
            validate.Regexp(r'^[a-zA-Z0-9\s_-]+$', error="Invalid characters")
        ]
    )
    agent_type = fields.Str(
        required=True,
        validate=validate.OneOf(['email', 'quality', 'review'])
    )
    description = fields.Str(
        validate=validate.Length(max=500),
        missing=""
    )
    config = fields.Dict(missing={})
    
    def validate_config(self, value):
        """Validate configuration dictionary"""
        return SecurityValidator.sanitize_input(value)

class TaskCreateSchema(Schema):
    """Schema for task creation"""
    title = fields.Str(
        required=True,
        validate=validate.Length(min=1, max=200)
    )
    description = fields.Str(
        validate=validate.Length(max=1000),
        missing=""
    )
    agent_id = fields.Str(
        required=True,
        validate=SecurityValidator.validate_uuid
    )
    priority = fields.Str(
        validate=validate.OneOf(['low', 'medium', 'high', 'critical']),
        missing='medium'
    )
```

## 🔒 Security Headers and HTTPS

### Security Headers Implementation

```python
# src/swarm_director/security/headers.py
from flask import Flask

class SecurityHeaders:
    """Security headers manager"""
    
    def __init__(self, app: Flask = None):
        self.app = app
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize security headers"""
        app.after_request(self.add_security_headers)
    
    @staticmethod
    def add_security_headers(response):
        """Add security headers to all responses"""
        
        # Content Security Policy
        csp_policy = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
            "font-src 'self' https://fonts.gstatic.com; "
            "img-src 'self' data: https:; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )
        response.headers['Content-Security-Policy'] = csp_policy
        
        # Security headers
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'DENY'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = (
            "camera=(), microphone=(), geolocation=(), "
            "payment=(), usb=(), magnetometer=(), gyroscope=()"
        )
        
        # HTTPS enforcement
        if not response.headers.get('Strict-Transport-Security'):
            response.headers['Strict-Transport-Security'] = (
                'max-age=31536000; includeSubDomains; preload'
            )
        
        # Remove server information
        response.headers.pop('Server', None)
        
        return response
```

## 🚫 Rate Limiting and DDoS Protection

### Advanced Rate Limiting

```python
# src/swarm_director/security/rate_limiting.py
import time
import redis
from typing import Tuple, Optional
from flask import request, jsonify
from functools import wraps

class AdvancedRateLimiter:
    """Advanced rate limiting with multiple algorithms"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def sliding_window_rate_limit(self, 
                                key: str, 
                                limit: int, 
                                window: int) -> Tuple[bool, dict]:
        """Sliding window rate limiting"""
        now = time.time()
        pipeline = self.redis.pipeline()
        
        # Remove old entries
        pipeline.zremrangebyscore(key, 0, now - window)
        
        # Count current requests
        pipeline.zcard(key)
        
        # Add current request
        pipeline.zadd(key, {str(now): now})
        
        # Set expiry
        pipeline.expire(key, window)
        
        results = pipeline.execute()
        current_count = results[1]
        
        remaining = max(0, limit - current_count)
        reset_time = int(now + window)
        
        return current_count < limit, {
            'limit': limit,
            'remaining': remaining,
            'reset': reset_time,
            'current': current_count
        }
    
    def token_bucket_rate_limit(self, 
                              key: str, 
                              capacity: int, 
                              refill_rate: float) -> Tuple[bool, dict]:
        """Token bucket rate limiting"""
        now = time.time()
        bucket_key = f"bucket:{key}"
        
        # Get current bucket state
        bucket_data = self.redis.hmget(bucket_key, ['tokens', 'last_refill'])
        tokens = float(bucket_data[0] or capacity)
        last_refill = float(bucket_data[1] or now)
        
        # Calculate tokens to add
        time_passed = now - last_refill
        tokens_to_add = time_passed * refill_rate
        tokens = min(capacity, tokens + tokens_to_add)
        
        # Check if request can be processed
        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False
        
        # Update bucket state
        self.redis.hmset(bucket_key, {
            'tokens': tokens,
            'last_refill': now
        })
        self.redis.expire(bucket_key, 3600)  # 1 hour expiry
        
        return allowed, {
            'limit': capacity,
            'remaining': int(tokens),
            'refill_rate': refill_rate
        }

def rate_limit(limit: int = 100, 
              window: int = 3600, 
              per: str = 'ip',
              algorithm: str = 'sliding_window'):
    """Rate limiting decorator"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Determine key
            if per == 'ip':
                key = f"rate_limit:ip:{request.remote_addr}"
            elif per == 'user' and hasattr(g, 'current_user'):
                key = f"rate_limit:user:{g.current_user['user_id']}"
            else:
                key = f"rate_limit:global"
            
            # Apply rate limiting
            redis_client = current_app.extensions['redis']
            limiter = AdvancedRateLimiter(redis_client)
            
            if algorithm == 'sliding_window':
                allowed, info = limiter.sliding_window_rate_limit(key, limit, window)
            elif algorithm == 'token_bucket':
                allowed, info = limiter.token_bucket_rate_limit(key, limit, 1.0)
            else:
                allowed, info = True, {}
            
            if not allowed:
                response = jsonify({
                    'error': 'Rate limit exceeded',
                    'retry_after': info.get('reset', window)
                })
                response.status_code = 429
                
                # Add rate limit headers
                for header, value in info.items():
                    response.headers[f'X-RateLimit-{header.title()}'] = str(value)
                
                return response
            
            # Add rate limit info to response headers
            response = f(*args, **kwargs)
            if hasattr(response, 'headers'):
                for header, value in info.items():
                    response.headers[f'X-RateLimit-{header.title()}'] = str(value)
            
            return response
        
        return decorated_function
    return decorator
```

## 📊 Security Monitoring and Logging

### Security Event Logging

```python
# src/swarm_director/security/monitoring.py
import logging
import json
from datetime import datetime
from typing import Dict, Any
from flask import request, g

class SecurityLogger:
    """Security event logging and monitoring"""
    
    def __init__(self):
        self.logger = logging.getLogger('security')
        self.logger.setLevel(logging.INFO)
        
        # Create file handler for security logs
        handler = logging.FileHandler('logs/security.log')
        formatter = logging.Formatter(
            '%(asctime)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
    
    def log_authentication_attempt(self, 
                                 user_id: str, 
                                 success: bool, 
                                 ip_address: str,
                                 user_agent: str):
        """Log authentication attempts"""
        event = {
            'event_type': 'authentication_attempt',
            'user_id': user_id,
            'success': success,
            'ip_address': ip_address,
            'user_agent': user_agent,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        level = logging.INFO if success else logging.WARNING
        self.logger.log(level, json.dumps(event))
    
    def log_authorization_failure(self, 
                                user_id: str, 
                                endpoint: str, 
                                required_permission: str):
        """Log authorization failures"""
        event = {
            'event_type': 'authorization_failure',
            'user_id': user_id,
            'endpoint': endpoint,
            'required_permission': required_permission,
            'ip_address': request.remote_addr,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.warning(json.dumps(event))
    
    def log_suspicious_activity(self, 
                              activity_type: str, 
                              details: Dict[str, Any]):
        """Log suspicious activities"""
        event = {
            'event_type': 'suspicious_activity',
            'activity_type': activity_type,
            'details': details,
            'ip_address': request.remote_addr,
            'user_agent': request.headers.get('User-Agent'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        if hasattr(g, 'current_user'):
            event['user_id'] = g.current_user.get('user_id')
        
        self.logger.error(json.dumps(event))
    
    def log_rate_limit_exceeded(self, 
                              limit_type: str, 
                              identifier: str):
        """Log rate limit violations"""
        event = {
            'event_type': 'rate_limit_exceeded',
            'limit_type': limit_type,
            'identifier': identifier,
            'ip_address': request.remote_addr,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        self.logger.warning(json.dumps(event))

# Security monitoring decorator
def monitor_security_event(event_type: str):
    """Decorator to monitor security events"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            security_logger = current_app.extensions['security_logger']
            
            try:
                result = f(*args, **kwargs)
                
                # Log successful operation
                details = {
                    'function': f.__name__,
                    'duration': time.time() - start_time,
                    'status': 'success'
                }
                
                return result
                
            except Exception as e:
                # Log security-related exceptions
                details = {
                    'function': f.__name__,
                    'duration': time.time() - start_time,
                    'status': 'error',
                    'error': str(e)
                }
                
                security_logger.log_suspicious_activity(event_type, details)
                raise
                
        return decorated_function
    return decorator
```

---

*This guide provides comprehensive security implementation patterns for SwarmDirector.* 