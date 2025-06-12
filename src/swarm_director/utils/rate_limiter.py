"""
Rate limiting utilities for SwarmDirector API
Provides memory-based rate limiting with IP and user-based limits
"""

import time
import threading
from typing import Dict, Optional, Tuple
from collections import defaultdict, deque
from functools import wraps
from flask import request, jsonify, current_app
import logging

logger = logging.getLogger(__name__)

class RateLimiter:
    """Thread-safe in-memory rate limiter"""
    
    def __init__(self):
        self._requests = defaultdict(deque)  # key -> deque of timestamps
        self._lock = threading.RLock()
        self._cleanup_interval = 3600  # Cleanup old entries every hour
        self._last_cleanup = time.time()
    
    def _cleanup_old_entries(self, current_time: float, window: int):
        """Remove expired entries to prevent memory leaks"""
        if current_time - self._last_cleanup > self._cleanup_interval:
            with self._lock:
                cutoff_time = current_time - window
                for key in list(self._requests.keys()):
                    # Remove old timestamps
                    while self._requests[key] and self._requests[key][0] < cutoff_time:
                        self._requests[key].popleft()
                    
                    # Remove empty deques
                    if not self._requests[key]:
                        del self._requests[key]
                
                self._last_cleanup = current_time
    
    def is_allowed(self, key: str, limit: int, window: int) -> Tuple[bool, Dict[str, int]]:
        """
        Check if request is allowed under rate limit
        
        Args:
            key: Unique identifier (IP, user_id, etc.)
            limit: Maximum number of requests allowed
            window: Time window in seconds
            
        Returns:
            Tuple of (is_allowed, rate_limit_info)
        """
        current_time = time.time()
        
        with self._lock:
            # Cleanup old entries periodically
            self._cleanup_old_entries(current_time, window)
            
            # Get request history for this key
            requests = self._requests[key]
            
            # Remove requests outside the current window
            cutoff_time = current_time - window
            while requests and requests[0] < cutoff_time:
                requests.popleft()
            
            # Check if under limit
            current_count = len(requests)
            is_allowed = current_count < limit
            
            if is_allowed:
                requests.append(current_time)
            
            # Calculate reset time (when oldest request will expire)
            reset_time = int(cutoff_time + window) if requests else int(current_time + window)
            
            rate_limit_info = {
                'limit': limit,
                'remaining': max(0, limit - current_count - (1 if is_allowed else 0)),
                'reset': reset_time,
                'retry_after': int(window - (current_time - requests[0])) if requests else 0
            }
            
            return is_allowed, rate_limit_info

# Global rate limiter instance
rate_limiter = RateLimiter()

class RateLimitConfig:
    """Rate limiting configuration"""
    
    # Default limits (requests per time window)
    DEFAULT_LIMITS = {
        'ip': (100, 3600),      # 100 requests per hour per IP
        'user': (1000, 3600),   # 1000 requests per hour per user
        'global': (10000, 3600), # 10000 requests per hour globally
        'burst': (10, 60)       # 10 requests per minute for burst protection
    }
    
    @classmethod
    def get_limit(cls, limit_type: str) -> Tuple[int, int]:
        """Get rate limit configuration for given type"""
        return cls.DEFAULT_LIMITS.get(limit_type, (100, 3600))

def get_client_identifier() -> str:
    """Get unique identifier for the client (IP address)"""
    # Check for forwarded headers (when behind proxy)
    forwarded_for = request.headers.get('X-Forwarded-For')
    if forwarded_for:
        # Take the first IP in the chain
        return forwarded_for.split(',')[0].strip()
    
    return request.remote_addr or 'unknown'

def get_user_identifier() -> Optional[str]:
    """Get user identifier from request context"""
    # Try to get user info from request context (set by auth decorator)
    user_info = getattr(request, 'user_info', None)
    if user_info and 'user_id' in user_info:
        return user_info['user_id']
    
    # Fallback to API key or token
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return f"token_{auth_header[7:15]}"  # Use first 8 chars of token
    
    api_key = request.headers.get('X-API-Key', '')
    if api_key:
        return f"apikey_{api_key[:8]}"
    
    return None

def rate_limit(limit_type: str = 'ip', custom_limit: Tuple[int, int] = None):
    """
    Rate limiting decorator
    
    Args:
        limit_type: Type of limit ('ip', 'user', 'global', 'burst')
        custom_limit: Custom (limit, window) tuple to override defaults
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            try:
                # Get rate limit configuration
                if custom_limit:
                    limit, window = custom_limit
                else:
                    limit, window = RateLimitConfig.get_limit(limit_type)
                
                # Determine the key based on limit type
                if limit_type == 'ip':
                    key = f"ip:{get_client_identifier()}"
                elif limit_type == 'user':
                    user_id = get_user_identifier()
                    if not user_id:
                        # Fall back to IP if no user identifier
                        key = f"ip:{get_client_identifier()}"
                    else:
                        key = f"user:{user_id}"
                elif limit_type == 'global':
                    key = "global"
                elif limit_type == 'burst':
                    key = f"burst:{get_client_identifier()}"
                else:
                    key = f"{limit_type}:{get_client_identifier()}"
                
                # Check rate limit
                is_allowed, rate_info = rate_limiter.is_allowed(key, limit, window)
                
                if not is_allowed:
                    # Rate limit exceeded
                    response = jsonify({
                        'status': 'error',
                        'error': 'Rate limit exceeded',
                        'error_code': 'RATE_LIMIT_EXCEEDED',
                        'rate_limit': rate_info
                    })
                    
                    # Add rate limit headers
                    response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                    response.headers['Retry-After'] = str(rate_info['retry_after'])
                    
                    return response, 429
                
                # Request allowed, execute function
                response = f(*args, **kwargs)
                
                # Add rate limit headers to successful responses
                if hasattr(response, 'headers'):
                    response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                    response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                    response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                
                return response
                
            except Exception as e:
                logger.error(f"Rate limiting error: {str(e)}")
                # Continue without rate limiting if there's an error
                return f(*args, **kwargs)
        
        return decorated_function
    return decorator

def check_multiple_limits(*limit_specs):
    """
    Check multiple rate limits at once
    
    Args:
        *limit_specs: Tuples of (limit_type, custom_limit)
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Check each limit
            for spec in limit_specs:
                if isinstance(spec, str):
                    limit_type = spec
                    custom_limit = None
                else:
                    limit_type, custom_limit = spec
                
                # Apply the specific rate limit check
                try:
                    # Get configuration
                    if custom_limit:
                        limit, window = custom_limit
                    else:
                        limit, window = RateLimitConfig.get_limit(limit_type)
                    
                    # Determine key
                    if limit_type == 'ip':
                        key = f"ip:{get_client_identifier()}"
                    elif limit_type == 'user':
                        user_id = get_user_identifier()
                        key = f"user:{user_id}" if user_id else f"ip:{get_client_identifier()}"
                    elif limit_type == 'global':
                        key = "global"
                    elif limit_type == 'burst':
                        key = f"burst:{get_client_identifier()}"
                    else:
                        key = f"{limit_type}:{get_client_identifier()}"
                    
                    # Check this specific limit
                    is_allowed, rate_info = rate_limiter.is_allowed(key, limit, window)
                    
                    if not is_allowed:
                        response = jsonify({
                            'status': 'error',
                            'error': f'Rate limit exceeded for {limit_type}',
                            'error_code': 'RATE_LIMIT_EXCEEDED',
                            'limit_type': limit_type,
                            'rate_limit': rate_info
                        })
                        
                        response.headers['X-RateLimit-Limit'] = str(rate_info['limit'])
                        response.headers['X-RateLimit-Remaining'] = str(rate_info['remaining'])
                        response.headers['X-RateLimit-Reset'] = str(rate_info['reset'])
                        response.headers['Retry-After'] = str(rate_info['retry_after'])
                        
                        return response, 429
                
                except Exception as e:
                    logger.error(f"Rate limiting error for {limit_type}: {str(e)}")
                    continue
            
            # All limits passed, execute function
            return f(*args, **kwargs)
        
        return decorated_function
    return decorator

# Convenience decorators for common scenarios
def api_rate_limit(f):
    """Standard API rate limiting (IP + burst protection)"""
    return check_multiple_limits('ip', 'burst')(f)

def user_rate_limit(f):
    """User-based rate limiting with burst protection"""
    return check_multiple_limits('user', 'burst')(f)

def strict_rate_limit(f):
    """Strict rate limiting (all limits)"""
    return check_multiple_limits('ip', 'user', 'burst', 'global')(f) 