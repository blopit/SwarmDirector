"""
Unit tests for response formatting utilities
Tests all standardized response formats and edge cases
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.utils.response_formatter import ResponseFormatter, APIResponse
from swarm_director.app import create_app


@pytest.fixture
def app():
    """Create Flask app for testing"""
    app = create_app('testing')
    return app


@pytest.fixture
def app_context(app):
    """Create Flask application context for testing"""
    with app.app_context():
        yield app


class TestResponseFormatter:
    """Test cases for ResponseFormatter class"""
    
    def test_success_response_basic(self, app_context):
        """Test basic success response"""
        response, status_code = ResponseFormatter.success(
            data={'message': 'test'},
            status_code=200
        )
        
        # Parse JSON response
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 200
        assert response_data['status'] == 'success'
        assert response_data['data']['message'] == 'test'
        assert 'timestamp' in response_data
        
    def test_success_response_with_message(self, app_context):
        """Test success response with message"""
        response, status_code = ResponseFormatter.success(
            data={'result': 42},
            message='Operation completed',
            status_code=201
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 201
        assert response_data['data']['result'] == 42
        assert response_data['data']['message'] == 'Operation completed'
        
    def test_success_response_with_metadata(self, app_context):
        """Test success response with metadata"""
        metadata = {'version': '1.0', 'build': '123'}
        response, status_code = ResponseFormatter.success(
            data={'test': True},
            metadata=metadata
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['metadata'] == metadata
        
    def test_error_response_basic(self, app_context):
        """Test basic error response"""
        response, status_code = ResponseFormatter.error(
            message='Test error',
            error_code='TEST_ERROR',
            status_code=400
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 400
        assert response_data['status'] == 'error'
        assert response_data['error']['message'] == 'Test error'
        assert response_data['error']['code'] == 'TEST_ERROR'
        assert 'timestamp' in response_data
        
    def test_error_response_with_field(self, app_context):
        """Test error response with field information"""
        response, status_code = ResponseFormatter.error(
            message='Validation failed',
            error_code='VALIDATION_ERROR',
            field='email',
            status_code=400
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['error']['field'] == 'email'
        
    def test_error_response_with_details(self, app_context):
        """Test error response with additional details"""
        details = {'invalid_fields': ['email', 'phone']}
        response, status_code = ResponseFormatter.error(
            message='Multiple validation errors',
            details=details
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['error']['details'] == details
        
    def test_paginated_response(self, app_context):
        """Test paginated response"""
        items = [{'id': 1}, {'id': 2}]
        response, status_code = ResponseFormatter.paginated(
            items=items,
            page=1,
            per_page=10,
            total=25
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 200
        assert response_data['status'] == 'success'
        assert response_data['data']['items'] == items
        assert response_data['data']['count'] == 2
        assert response_data['metadata']['pagination']['page'] == 1
        assert response_data['metadata']['pagination']['total'] == 25
        assert response_data['metadata']['pagination']['total_pages'] == 3
        assert response_data['metadata']['pagination']['has_next'] is True
        assert response_data['metadata']['pagination']['has_prev'] is False
        
    def test_paginated_response_last_page(self, app_context):
        """Test paginated response on last page"""
        items = [{'id': 1}]
        response, status_code = ResponseFormatter.paginated(
            items=items,
            page=3,
            per_page=10,
            total=25
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['metadata']['pagination']['has_next'] is False
        assert response_data['metadata']['pagination']['has_prev'] is True
        assert response_data['metadata']['pagination']['next_page'] is None
        assert response_data['metadata']['pagination']['prev_page'] == 2
        
    def test_task_created_response(self, app_context):
        """Test task created response"""
        response, status_code = ResponseFormatter.task_created(
            task_id='task_123',
            message='Task created successfully'
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 201
        assert response_data['data']['task_id'] == 'task_123'
        assert response_data['data']['message'] == 'Task created successfully'
        
    def test_validation_error_response(self, app_context):
        """Test validation error response"""
        response, status_code = ResponseFormatter.validation_error(
            message='Invalid email format',
            field='email'
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 400
        assert response_data['error']['code'] == 'VALIDATION_ERROR'
        assert response_data['error']['field'] == 'email'
        
    def test_not_found_response(self, app_context):
        """Test not found response"""
        response, status_code = ResponseFormatter.not_found('User')
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 404
        assert response_data['error']['code'] == 'NOT_FOUND'
        assert 'User not found' in response_data['error']['message']
        
    def test_unauthorized_response(self, app_context):
        """Test unauthorized response"""
        response, status_code = ResponseFormatter.unauthorized()
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 401
        assert response_data['error']['code'] == 'UNAUTHORIZED'
        
    def test_forbidden_response(self, app_context):
        """Test forbidden response"""
        response, status_code = ResponseFormatter.forbidden()
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 403
        assert response_data['error']['code'] == 'FORBIDDEN'
        
    def test_rate_limited_response(self, app_context):
        """Test rate limited response"""
        response, status_code = ResponseFormatter.rate_limited(retry_after=60)
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 429
        assert response_data['error']['code'] == 'RATE_LIMIT_EXCEEDED'
        assert response_data['error']['details']['retry_after'] == 60
        assert response.headers['Retry-After'] == '60'
        
    def test_internal_error_response(self, app_context):
        """Test internal error response"""
        response, status_code = ResponseFormatter.internal_error()
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 500
        assert response_data['error']['code'] == 'INTERNAL_SERVER_ERROR'
        
    def test_timestamp_format(self, app_context):
        """Test timestamp format is ISO 8601"""
        response, status_code = ResponseFormatter.success(data={'test': True})
        response_data = json.loads(response.get_data(as_text=True))
        
        timestamp = response_data['timestamp']
        # Should be ISO format ending with 'Z'
        assert timestamp.endswith('Z')
        # Should be parseable as datetime
        datetime.fromisoformat(timestamp.replace('Z', '+00:00'))


class TestAPIResponse:
    """Test cases for APIResponse convenience class"""
    
    def test_json_success(self, app_context):
        """Test json_success convenience method"""
        response, status_code = APIResponse.json_success(
            data={'test': True},
            status_code=201
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert status_code == 201
        assert response_data['status'] == 'success'
        assert response_data['data']['test'] is True
        
    def test_json_error(self, app_context):
        """Test json_error convenience method"""
        response, status_code = APIResponse.json_error(
            message='Test error',
            error_code='TEST_ERROR'
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['error']['code'] == 'TEST_ERROR'
        
    def test_json_paginated(self, app_context):
        """Test json_paginated convenience method"""
        items = [{'id': 1}]
        response, status_code = APIResponse.json_paginated(
            items=items,
            page=1,
            per_page=10,
            total=1
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['data']['items'] == items
        assert 'pagination' in response_data['metadata']


class TestEdgeCases:
    """Test edge cases and error conditions"""
    
    def test_empty_data_success(self, app_context):
        """Test success response with empty data"""
        response, status_code = ResponseFormatter.success(data=None)
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['data'] is None
        assert response_data['status'] == 'success'
        
    def test_zero_pagination(self, app_context):
        """Test pagination with zero items"""
        response, status_code = ResponseFormatter.paginated(
            items=[],
            page=1,
            per_page=10,
            total=0
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['data']['count'] == 0
        assert response_data['metadata']['pagination']['total_pages'] == 0
        assert response_data['metadata']['pagination']['has_next'] is False
        
    def test_zero_per_page_pagination(self, app_context):
        """Test pagination with zero per_page"""
        response, status_code = ResponseFormatter.paginated(
            items=[],
            page=1,
            per_page=0,
            total=10
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['metadata']['pagination']['total_pages'] == 0
        
    def test_message_with_non_dict_data(self, app_context):
        """Test adding message to non-dict data"""
        response, status_code = ResponseFormatter.success(
            data="simple string",
            message="Test message"
        )
        
        response_data = json.loads(response.get_data(as_text=True))
        
        assert response_data['data']['result'] == "simple string"
        assert response_data['data']['message'] == "Test message"


if __name__ == '__main__':
    pytest.main([__file__]) 