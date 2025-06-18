"""
Comprehensive tests for SwarmDirector error handling system
Tests cover custom exceptions, global error handlers, and core error handling functionality.
"""

import pytest
import json
import time
import threading
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
from flask import Flask

from src.swarm_director.utils.error_handler import (
    SwarmDirectorError, ValidationError, AuthenticationError, 
    ResourceNotFoundError, RateLimitError, DatabaseError,
    ErrorHandler, require_error_handling
)


class TestSwarmDirectorExceptions:
    """Test custom exception classes"""
    
    def test_swarm_director_error_basic(self):
        """Test basic SwarmDirectorError functionality"""
        error = SwarmDirectorError("Test error")
        
        assert str(error) == "Test error"
        assert error.message == "Test error"
        assert error.error_code == "SwarmDirectorError"
        assert error.status_code == 500
        assert error.details == {}
        assert error.correlation_id is not None
        assert error.timestamp is not None
    
    def test_swarm_director_error_with_details(self):
        """Test SwarmDirectorError with custom details"""
        details = {"field": "username", "value": "invalid"}
        error = SwarmDirectorError(
            message="Custom error",
            error_code="CUSTOM_ERROR",
            status_code=422,
            details=details,
            correlation_id="test-123"
        )
        
        assert error.message == "Custom error"
        assert error.error_code == "CUSTOM_ERROR"
        assert error.status_code == 422
        assert error.details == details
        assert error.correlation_id == "test-123"
    
    def test_validation_error(self):
        """Test ValidationError specific functionality"""
        error = ValidationError("Invalid field", field="username", value="test@")
        
        assert error.message == "Invalid field"
        assert error.error_code == "VALIDATION_ERROR"
        assert error.status_code == 400
        assert error.details["field"] == "username"
        assert error.details["rejected_value"] == "test@"
    
    def test_authentication_error(self):
        """Test AuthenticationError functionality"""
        error = AuthenticationError()
        
        assert error.message == "Authentication required"
        assert error.error_code == "AUTHENTICATION_ERROR"
        assert error.status_code == 401
    
    def test_resource_not_found_error(self):
        """Test ResourceNotFoundError functionality"""
        error = ResourceNotFoundError(
            message="User not found",
            resource_type="User",
            resource_id="123"
        )
        
        assert error.message == "User not found"
        assert error.error_code == "RESOURCE_NOT_FOUND"
        assert error.status_code == 404
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "123"
    
    def test_rate_limit_error(self):
        """Test RateLimitError functionality"""
        error = RateLimitError(retry_after=60)
        
        assert error.message == "Rate limit exceeded"
        assert error.error_code == "RATE_LIMIT_EXCEEDED"
        assert error.status_code == 429
        assert error.details["retry_after"] == 60
    
    def test_database_error(self):
        """Test DatabaseError functionality"""
        error = DatabaseError("Connection failed")
        
        assert error.message == "Connection failed"
        assert error.error_code == "DATABASE_ERROR"
        assert error.status_code == 500


class TestErrorHandler:
    """Test ErrorHandler class functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def error_handler(self, app):
        """Create ErrorHandler instance"""
        handler = ErrorHandler()
        handler.init_app(app)
        return handler
    
    def test_error_handler_initialization(self, app, error_handler):
        """Test ErrorHandler initialization"""
        assert error_handler.app == app
        assert error_handler.logger == app.logger
        assert 'error_handler' in app.extensions
    
    def test_get_error_severity(self, error_handler):
        """Test error severity classification"""
        assert error_handler._get_error_severity(200) == 'info'
        assert error_handler._get_error_severity(404) == 'warning'
        assert error_handler._get_error_severity(500) == 'error'
    
    def test_log_error_with_context(self, app, error_handler):
        """Test error logging with request context"""
        with app.test_request_context('/api/test', method='POST', headers={'User-Agent': 'TestAgent'}):
            error = SwarmDirectorError("Test error")
            
            with patch.object(error_handler.logger, 'error') as mock_log:
                context = error_handler.log_error(error, severity='error')
                
                assert context['error_type'] == 'SwarmDirectorError'
                assert context['method'] == 'POST'
                assert 'url' in context
                assert 'user_agent' in context
                mock_log.assert_called_once()
    
    def test_log_error_with_traceback(self, error_handler):
        """Test error logging with traceback"""
        error = Exception("Test exception")
        
        with patch.object(error_handler.logger, 'error') as mock_log:
            context = error_handler.log_error(error, include_traceback=True)
            
            assert 'traceback' in context
            mock_log.assert_called_once()
    
    def test_require_error_handling_decorator(self, app):
        """Test require_error_handling decorator"""
        with app.app_context():
            @require_error_handling
            def test_function():
                raise ValueError("Test error")
            
            with pytest.raises(SwarmDirectorError) as exc_info:
                test_function()
            
            assert exc_info.value.error_code == "UNEXPECTED_ERROR"
            assert exc_info.value.status_code == 500
            assert "original_error" in exc_info.value.details
    
    def test_require_error_handling_passthrough(self, app):
        """Test decorator passes through SwarmDirectorError"""
        with app.app_context():
            @require_error_handling
            def test_function():
                raise ValidationError("Test validation error")
            
            with pytest.raises(ValidationError):
                test_function()


class TestRetryMechanisms:
    """Test retry mechanisms and patterns"""
    
    def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation"""
        base_delay = 1.0
        max_delay = 60.0
        
        # Test exponential progression
        delays = []
        for attempt in range(5):
            delay = min(base_delay * (2 ** attempt), max_delay)
            delays.append(delay)
        
        assert delays[0] == 1.0
        assert delays[1] == 2.0
        assert delays[2] == 4.0
        assert delays[3] == 8.0
        assert delays[4] == 16.0
    
    def test_retry_with_jitter(self):
        """Test retry with jitter to prevent thundering herd"""
        import random
        
        base_delay = 2.0
        jitter_factor = 0.1
        
        # Generate multiple jittered delays
        delays = []
        for _ in range(10):
            jitter = random.uniform(-jitter_factor, jitter_factor)
            jittered_delay = base_delay * (1 + jitter)
            delays.append(jittered_delay)
        
        # All delays should be within jitter range
        min_expected = base_delay * (1 - jitter_factor)
        max_expected = base_delay * (1 + jitter_factor)
        
        for delay in delays:
            assert min_expected <= delay <= max_expected
    
    def test_retry_error_classification(self):
        """Test error classification for retry decisions"""
        # Transient errors should be retryable
        transient_errors = [
            ConnectionError("Network timeout"),
            TimeoutError("Request timeout"),
            Exception("Temporary service unavailable")
        ]
        
        # Persistent errors should not be retryable
        persistent_errors = [
            ValueError("Invalid input format"),
            KeyError("Missing required field"),
            AuthenticationError("Invalid credentials")
        ]
        
        def is_retryable_error(error):
            """Simple retry classification logic"""
            return isinstance(error, (ConnectionError, TimeoutError)) or \
                   "timeout" in str(error).lower() or \
                   "unavailable" in str(error).lower()
        
        # Test transient errors
        for error in transient_errors:
            assert is_retryable_error(error), f"Error should be retryable: {error}"
        
        # Test persistent errors
        for error in persistent_errors:
            if not isinstance(error, (ConnectionError, TimeoutError)):
                assert not is_retryable_error(error), f"Error should not be retryable: {error}"


class TestIntegrationScenarios:
    """Test integrated error handling scenarios"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with error handling"""
        app = Flask(__name__)
        app.config['TESTING'] = True
        
        error_handler = ErrorHandler()
        error_handler.init_app(app)
        
        @app.route('/test-validation-error')
        def test_validation_error():
            raise ValidationError("Invalid input", field="username")
        
        @app.route('/test-auth-error')
        def test_auth_error():
            raise AuthenticationError()
        
        @app.route('/test-generic-error')
        def test_generic_error():
            raise Exception("Unexpected error")
        
        @app.route('/test-success')
        def test_success():
            return {"message": "Success"}
        
        return app
    
    def test_validation_error_response(self, app):
        """Test validation error response format"""
        with app.test_client() as client:
            response = client.get('/test-validation-error')
            
            assert response.status_code == 400
            data = json.loads(response.data)
            
            assert data['status'] == 'error'
            assert data['error']['code'] == 'VALIDATION_ERROR'
            assert 'timestamp' in data
            assert 'field' in data['error']
    
    def test_authentication_error_response(self, app):
        """Test authentication error response format"""
        with app.test_client() as client:
            response = client.get('/test-auth-error')
            
            assert response.status_code == 401
            data = json.loads(response.data)
            
            assert data['status'] == 'error'
            assert data['error']['code'] == 'AUTHENTICATION_ERROR'
    
    def test_generic_error_handling(self, app):
        """Test generic error handling"""
        # In testing mode, Flask re-raises exceptions instead of handling them
        # This is the expected behavior for debugging
        with app.test_client() as client:
            with pytest.raises(Exception, match="Unexpected error"):
                client.get('/test-generic-error')
    
    def test_successful_request(self, app):
        """Test that successful requests work normally"""
        with app.test_client() as client:
            response = client.get('/test-success')
            
            assert response.status_code == 200
            data = json.loads(response.data)
            assert data['message'] == 'Success'


class TestErrorHandlingPatterns:
    """Test common error handling patterns"""
    
    def test_context_preservation_during_errors(self):
        """Test that error context is preserved"""
        original_context = {
            "user_id": "123",
            "operation": "data_processing",
            "request_id": "req-456"
        }
        
        try:
            # Simulate operation that fails with context
            raise ValueError("Processing failed")
        except Exception as e:
            # Create error with preserved context
            error = SwarmDirectorError(
                message=str(e),
                error_code="PROCESSING_ERROR",
                details={"original_context": original_context}
            )
            
            assert error.details["original_context"] == original_context
            assert error.details["original_context"]["user_id"] == "123"
    
    def test_error_correlation_tracking(self):
        """Test error correlation ID tracking"""
        correlation_id = "test-correlation-123"
        
        error1 = SwarmDirectorError("First error", correlation_id=correlation_id)
        error2 = SwarmDirectorError("Related error", correlation_id=correlation_id)
        
        assert error1.correlation_id == correlation_id
        assert error2.correlation_id == correlation_id
        assert error1.correlation_id == error2.correlation_id
    
    def test_error_chaining(self):
        """Test error chaining and root cause tracking"""
        try:
            try:
                raise ValueError("Root cause error")
            except ValueError as root_error:
                raise DatabaseError(
                    "Database operation failed",
                    details={"root_cause": str(root_error)}
                )
        except DatabaseError as db_error:
            final_error = SwarmDirectorError(
                "Workflow failed",
                details={
                    "database_error": str(db_error),
                    "root_cause": db_error.details.get("root_cause")
                }
            )
            
            assert "root_cause" in final_error.details
            assert final_error.details["root_cause"] == "Root cause error"
    
    def test_graceful_degradation_pattern(self):
        """Test graceful degradation when services fail"""
        def primary_service():
            raise ConnectionError("Primary service unavailable")
        
        def fallback_service():
            return {"data": "fallback_data", "source": "fallback"}
        
        def service_with_fallback():
            try:
                return primary_service()
            except ConnectionError:
                # Log the error but continue with fallback
                return fallback_service()
        
        result = service_with_fallback()
        assert result["source"] == "fallback"
        assert result["data"] == "fallback_data"


class TestConcurrentErrorHandling:
    """Test error handling under concurrent conditions"""
    
    def test_concurrent_error_logging(self):
        """Test that error logging is thread-safe"""
        app = Flask(__name__)
        error_handler = ErrorHandler()
        error_handler.init_app(app)
        
        errors_logged = []
        
        def log_error(worker_id):
            with app.app_context():
                error = SwarmDirectorError(f"Error from worker {worker_id}")
                with patch.object(error_handler.logger, 'error') as mock_log:
                    error_handler.log_error(error)
                    errors_logged.append(worker_id)
        
        # Start multiple threads logging errors
        threads = []
        for i in range(5):
            thread = threading.Thread(target=log_error, args=(i,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Verify all errors were logged
        assert len(errors_logged) == 5
        assert set(errors_logged) == {0, 1, 2, 3, 4}


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
