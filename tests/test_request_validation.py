"""
Tests for request validation utilities
"""

import pytest
import json
from unittest.mock import Mock, patch
from flask import Flask, request
from src.swarm_director.utils.validation import (
    ValidationError,
    RequestValidator,
    SchemaValidator,
    validate_request
)
from src.swarm_director.schemas.task_schemas import BASE_TASK_SCHEMA, get_schema_for_task_type

class TestValidationError:
    """Test custom ValidationError class"""
    
    def test_validation_error_creation(self):
        error = ValidationError("Test message", "TEST_CODE", "test_field")
        assert error.message == "Test message"
        assert error.error_code == "TEST_CODE"
        assert error.field == "test_field"
        assert str(error) == "Test message"

class TestRequestValidator:
    """Test RequestValidator class"""
    
    def setup_method(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    def test_sanitize_input_string(self):
        """Test input sanitization for strings"""
        # Test basic string
        result = RequestValidator.sanitize_input("Hello World")
        assert result == "Hello World"
        
        # Test XSS prevention
        malicious = "<script>alert('xss')</script>"
        result = RequestValidator.sanitize_input(malicious)
        assert "<script>" not in result
        assert "alert" not in result
        
        # Test HTML escaping
        html = "<div>Test & Content</div>"
        result = RequestValidator.sanitize_input(html)
        assert "&lt;div&gt;" in result
        assert "&amp;" in result
    
    def test_sanitize_input_dict(self):
        """Test input sanitization for dictionaries"""
        data = {
            "safe": "normal text",
            "dangerous": "<script>alert('xss')</script>",
            "nested": {
                "html": "<div>content</div>"
            }
        }
        result = RequestValidator.sanitize_input(data)
        
        assert result["safe"] == "normal text"
        assert "<script>" not in result["dangerous"]
        assert "&lt;div&gt;" in result["nested"]["html"]
    
    def test_sanitize_input_list(self):
        """Test input sanitization for lists"""
        data = ["normal", "<script>alert('xss')</script>", {"key": "<div>test</div>"}]
        result = RequestValidator.sanitize_input(data)
        
        assert result[0] == "normal"
        assert "<script>" not in result[1]
        assert "&lt;div&gt;" in result[2]["key"]
    
    def test_sanitize_input_too_long(self):
        """Test input length validation"""
        long_string = "x" * 10001  # Exceeds 10KB limit
        
        with pytest.raises(ValidationError) as exc_info:
            RequestValidator.sanitize_input(long_string)
        
        assert exc_info.value.error_code == "INPUT_TOO_LONG"

class TestSchemaValidator:
    """Test SchemaValidator class"""
    
    def test_validate_basic_task(self):
        """Test validation of basic task structure"""
        valid_task = {
            "type": "test_task",
            "title": "Test Task",
            "description": "A test task",
            "priority": "medium"
        }
        
        result = SchemaValidator.validate_schema(valid_task)
        assert result == valid_task
    
    def test_validate_missing_required_field(self):
        """Test validation fails when required field is missing"""
        invalid_task = {
            "title": "Test Task",
            "description": "Missing type field"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SchemaValidator.validate_schema(invalid_task)
        
        assert exc_info.value.error_code == "SCHEMA_VALIDATION_ERROR"
        assert "type" in exc_info.value.message
    
    def test_validate_invalid_priority(self):
        """Test validation fails for invalid priority value"""
        invalid_task = {
            "type": "test_task",
            "priority": "invalid_priority"
        }
        
        with pytest.raises(ValidationError) as exc_info:
            SchemaValidator.validate_schema(invalid_task)
        
        assert exc_info.value.error_code == "SCHEMA_VALIDATION_ERROR"
    
    def test_validate_additional_properties(self):
        """Test validation allows additional properties (updated behavior)"""
        task_with_extra = {
            "type": "test_task",
            "extra_field": "this is now allowed"
        }
        
        # Should not raise an error since we now allow additional properties
        result = SchemaValidator.validate_schema(task_with_extra)
        assert result == task_with_extra

class TestSchemaSelection:
    """Test task type schema selection"""
    
    def test_get_communication_schema(self):
        """Test getting schema for communication tasks"""
        schema = get_schema_for_task_type("communication")
        assert "allOf" in schema  # Communication tasks use allOf structure
    
    def test_get_generic_schema(self):
        """Test fallback to generic schema for unknown types"""
        schema = get_schema_for_task_type("unknown_type")
        assert schema == BASE_TASK_SCHEMA
    
    def test_validate_communication_task(self):
        """Test validation of communication task with specific schema"""
        comm_task = {
            "type": "communication",
            "title": "Send Email",
            "args": {
                "recipient": "test@example.com",
                "content": "Hello World",
                "channel": "email"
            }
        }
        
        schema = get_schema_for_task_type("communication")
        result = SchemaValidator.validate_schema(comm_task, schema)
        assert result == comm_task
    
    def test_validate_communication_task_missing_args(self):
        """Test communication task validation fails without required args"""
        comm_task = {
            "type": "communication",
            "title": "Send Email",
            "args": {
                "content": "Hello World"  # Missing recipient
            }
        }
        
        schema = get_schema_for_task_type("communication")
        with pytest.raises(ValidationError):
            SchemaValidator.validate_schema(comm_task, schema)

class TestValidateRequestDecorator:
    """Test the validate_request decorator"""
    
    def setup_method(self):
        self.app = Flask(__name__)
        self.app.config['TESTING'] = True
    
    def test_valid_request(self):
        """Test decorator with valid request"""
        with self.app.test_request_context(
            '/test',
            method='POST',
            data=json.dumps({"type": "test_task", "title": "Test"}),
            content_type='application/json'
        ):
            @validate_request()
            def test_endpoint():
                return {"status": "success"}, 200
            
            result = test_endpoint()
            assert result[1] == 200
    
    def test_invalid_content_type(self):
        """Test decorator with invalid content type"""
        with self.app.test_request_context(
            '/test',
            method='POST',
            data="not json",
            content_type='text/plain'
        ):
            @validate_request()
            def test_endpoint():
                return {"status": "success"}, 200
            
            result = test_endpoint()
            assert result[1] == 400
            # Check the actual response content, not the string representation
            response_data = result[0].get_data(as_text=True)
            assert "MISSING_CONTENT_TYPE" in response_data or "INVALID_CONTENT_TYPE" in response_data
    
    def test_invalid_json(self):
        """Test decorator with invalid JSON"""
        with self.app.test_request_context(
            '/test',
            method='POST',
            data="invalid json {",
            content_type='application/json'
        ):
            @validate_request()
            def test_endpoint():
                return {"status": "success"}, 200
            
            result = test_endpoint()
            assert result[1] == 400

if __name__ == '__main__':
    pytest.main([__file__]) 