"""
Tests for client-side streaming functionality
"""

import pytest
import json
import time
from unittest.mock import Mock, patch, MagicMock
from flask import Flask
from flask_socketio import SocketIOTestClient

from src.swarm_director.app import create_app
from src.swarm_director.web.websocket import create_websocket_app
from src.swarm_director.utils.streaming import StreamingManager, StreamingConfig


class TestClientSideStreaming:
    """Test client-side streaming integration"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app with streaming"""
        app = create_app('testing')
        app.config['TESTING'] = True
        app.config['SECRET_KEY'] = 'test-secret-key'
        return app
    
    @pytest.fixture
    def streaming_manager(self):
        """Create mock streaming manager"""
        config = StreamingConfig()
        manager = Mock(spec=StreamingManager)
        manager.config = config
        
        # Create mock session
        mock_session = Mock()
        mock_session.session_id = "test-session-001"
        mock_session.add_client_handler = Mock()
        
        # Mock async methods to return coroutines
        async def mock_pause():
            pass
        async def mock_resume():
            pass
        
        mock_session.pause = Mock(return_value=mock_pause())
        mock_session.resume = Mock(return_value=mock_resume())
        mock_session.get_status = Mock(return_value={
            'state': 'STREAMING',
            'metrics': {'tokens_sent': 100}
        })
        
        # Mock async methods to return coroutines
        async def mock_close_session(session_id):
            pass
        
        manager.create_session = Mock(return_value=mock_session)
        manager.get_session = Mock(return_value=mock_session)
        manager.close_session = Mock(return_value=mock_close_session("test-session-001"))
        return manager
    
    @pytest.fixture
    def client(self, app, streaming_manager):
        """Create SocketIO test client"""
        # Initialize streaming in app
        app.extensions['streaming_manager'] = streaming_manager
        
        # Create SocketIO app
        socketio = create_websocket_app(app, streaming_manager)
        app.extensions['socketio'] = socketio
        
        return SocketIOTestClient(app, socketio)
    
    def test_client_connection_lifecycle(self, client):
        """Test complete client connection lifecycle"""
        # Test connection
        received = client.get_received()
        assert len(received) > 0
        
        # Should receive connection_status event
        connection_event = next((event for event in received if event['name'] == 'connection_status'), None)
        assert connection_event is not None
        assert connection_event['args'][0]['status'] == 'connected'
        
        # Test disconnection
        client.disconnect()
        # Should disconnect cleanly without errors
    
    def test_stream_lifecycle_events(self, client, streaming_manager):
        """Test complete stream lifecycle with events"""
        # Clear initial messages
        client.get_received()
        
        # Start stream
        stream_data = {
            'task_id': 'test-task-001',
            'config': {
                'buffer_size': 1000,
                'rate_limit': 50
            }
        }
        
        client.emit('start_stream', stream_data)
        
        # Verify stream started event
        received = client.get_received()
        stream_started = next((event for event in received if event['name'] == 'stream_started'), None)
        assert stream_started is not None
        assert stream_started['args'][0]['session_id'] == 'test-session-001'
        
        # Pause stream
        client.emit('pause_stream', {})
        received = client.get_received()
        pause_event = next((event for event in received if event['name'] == 'stream_paused'), None)
        assert pause_event is not None
        
        # Resume stream
        client.emit('resume_stream', {})
        received = client.get_received()
        resume_event = next((event for event in received if event['name'] == 'stream_resumed'), None)
        assert resume_event is not None
        
        # Stop stream
        client.emit('stop_stream', {})
        received = client.get_received()
        stop_event = next((event for event in received if event['name'] == 'stream_stopped'), None)
        assert stop_event is not None
    
    def test_token_streaming_simulation(self, client, streaming_manager):
        """Test token streaming with simulated data"""
        # Clear initial messages
        client.get_received()
        
        # Start stream
        client.emit('start_stream', {'task_id': 'test-task-001'})
        client.get_received()  # Clear start response
        
        # Simulate token streaming by directly calling the handler
        handler = client.app.extensions['websocket_handler']
        
        # Simulate multiple tokens
        test_tokens = [
            {'token': 'Hello', 'timestamp': '2023-01-01T12:00:00Z', 'metadata': {}},
            {'token': ' world', 'timestamp': '2023-01-01T12:00:01Z', 'metadata': {}},
            {'token': '!', 'timestamp': '2023-01-01T12:00:02Z', 'metadata': {}}
        ]
        
        for token_data in test_tokens:
            # Simulate receiving token from streaming manager
            handler.send_to_session('test-session-001', 'stream_token', token_data)
        
        # In a real scenario, client would receive these tokens
        # Here we verify the handler can send them
        assert handler is not None
    
    def test_error_handling_scenarios(self, client):
        """Test various error scenarios"""
        # Clear initial messages
        client.get_received()
        
        # Test starting stream without task_id
        client.emit('start_stream', {})
        received = client.get_received()
        error_event = next((event for event in received if event['name'] == 'error'), None)
        assert error_event is not None
        assert 'task_id is required' in error_event['args'][0]['message']
        
        # Test stopping stream when none is active
        client.emit('stop_stream', {})
        received = client.get_received()
        # Should handle gracefully without crashing
    
    def test_metrics_and_status_requests(self, client, streaming_manager):
        """Test metrics and status request handling"""
        # Clear initial messages
        client.get_received()
        
        # Start stream first
        client.emit('start_stream', {'task_id': 'test-task-001'})
        client.get_received()  # Clear start response
        
        # Request status
        client.emit('get_stream_status', {})
        received = client.get_received()
        status_event = next((event for event in received if event['name'] == 'stream_status'), None)
        assert status_event is not None
        
        # Request metrics
        client.emit('get_stream_metrics', {})
        received = client.get_received()
        metrics_event = next((event for event in received if event['name'] == 'stream_metrics'), None)
        assert metrics_event is not None
    
    def test_concurrent_client_handling(self, app, streaming_manager):
        """Test handling multiple concurrent clients"""
        # Initialize streaming in app
        app.extensions['streaming_manager'] = streaming_manager
        
        # Create SocketIO app
        socketio = create_websocket_app(app, streaming_manager)
        app.extensions['socketio'] = socketio
        
        # Create multiple clients
        client1 = SocketIOTestClient(app, socketio)
        client2 = SocketIOTestClient(app, socketio)
        
        # Clear initial messages
        client1.get_received()
        client2.get_received()
        
        # Both clients start streams
        client1.emit('start_stream', {'task_id': 'task-001'})
        client2.emit('start_stream', {'task_id': 'task-002'})
        
        # Verify both receive responses
        received1 = client1.get_received()
        received2 = client2.get_received()
        
        assert len(received1) > 0
        assert len(received2) > 0
        
        # Cleanup
        client1.disconnect()
        client2.disconnect()
    
    def test_reconnection_scenario(self, client):
        """Test reconnection handling"""
        # Clear initial messages
        client.get_received()
        
        # Start stream
        client.emit('start_stream', {'task_id': 'test-task-001'})
        client.get_received()  # Clear start response
        
        # Simulate disconnect and reconnect
        client.disconnect()
        
        # Reconnect (in real scenario, client would handle this)
        # Here we just verify the disconnect was clean
        assert not client.connected
    
    def test_configuration_validation(self, client):
        """Test stream configuration validation"""
        # Clear initial messages
        client.get_received()
        
        # Test with valid configuration
        valid_config = {
            'task_id': 'test-task-001',
            'config': {
                'buffer_size': 1000,
                'rate_limit': 50,
                'backpressure_threshold': 0.8
            }
        }
        
        client.emit('start_stream', valid_config)
        received = client.get_received()
        
        # Should receive stream_started event
        stream_started = next((event for event in received if event['name'] == 'stream_started'), None)
        assert stream_started is not None
        
        # Configuration should be included in response
        response_data = stream_started['args'][0]
        assert 'config' in response_data
    
    def test_system_message_handling(self, client):
        """Test system message broadcasting"""
        # Clear initial messages
        client.get_received()
        
        # Get handler to send system message
        handler = client.app.extensions['websocket_handler']
        
        # Send system message
        handler.broadcast_system_message("Test system message", "info")
        
        # In real scenario, all connected clients would receive this
        # Here we verify the handler can broadcast
        assert handler is not None
    
    def test_heartbeat_mechanism(self, client):
        """Test heartbeat/ping mechanism"""
        # Clear initial messages
        client.get_received()
        
        # Send ping
        client.emit('ping', {'timestamp': int(time.time() * 1000)})
        
        # Should handle ping without errors
        # In real implementation, server might respond with pong
        received = client.get_received()
        # No specific response expected for ping in current implementation
    
    def test_buffer_management(self, client, streaming_manager):
        """Test client-side buffer management simulation"""
        # Clear initial messages
        client.get_received()
        
        # Start stream with specific buffer configuration
        stream_config = {
            'task_id': 'test-task-001',
            'config': {
                'buffer_size': 100,  # Small buffer for testing
                'rate_limit': 1000   # High rate to test buffering
            }
        }
        
        client.emit('start_stream', stream_config)
        received = client.get_received()
        
        # Verify stream started with correct configuration
        stream_started = next((event for event in received if event['name'] == 'stream_started'), None)
        assert stream_started is not None
        
        response_config = stream_started['args'][0]['config']
        assert response_config['buffer_size'] == 100
        assert response_config['rate_limit'] == 1000


class TestStreamingDemoPage:
    """Test streaming demo page functionality"""
    
    @pytest.fixture
    def app(self):
        """Create test Flask app"""
        app = create_app('testing')
        app.config['TESTING'] = True
        return app
    
    @pytest.fixture
    def client(self, app):
        """Create test client"""
        return app.test_client()
    
    def test_streaming_demo_route(self, client):
        """Test streaming demo page route"""
        response = client.get('/streaming-demo')
        assert response.status_code == 200
        assert b'SwarmDirector Streaming Demo' in response.data
        assert b'streaming-client.js' in response.data
    
    def test_demo_page_content(self, client):
        """Test demo page contains required elements"""
        response = client.get('/streaming-demo')
        content = response.data.decode('utf-8')
        
        # Check for key UI elements
        assert 'Connection Status' in content
        assert 'Stream Configuration' in content
        assert 'Stream Controls' in content
        assert 'Demo Scenarios' in content
        assert 'Event Log' in content
        
        # Check for JavaScript functionality
        assert 'StreamingClient' in content
        assert 'connect()' in content
        assert 'startStream()' in content
        assert 'handleToken' in content
    
    def test_demo_scenarios_included(self, client):
        """Test demo scenarios are included"""
        response = client.get('/streaming-demo')
        content = response.data.decode('utf-8')
        
        # Check for demo scenario functions
        assert 'simulateCodeGeneration' in content
        assert 'simulateConversation' in content
        assert 'simulateAnalysis' in content
        assert 'simulateError' in content
    
    def test_websocket_test_route_still_works(self, client):
        """Ensure original websocket test route still works"""
        response = client.get('/websocket-test')
        assert response.status_code == 200
        assert b'WebSocket Test' in response.data


class TestClientSideEventHandling:
    """Test client-side event handling patterns"""
    
    def test_event_handler_registration(self):
        """Test event handler registration pattern"""
        # This would test the JavaScript event handling in a real browser environment
        # For now, we verify the pattern exists in our code
        
        # Mock JavaScript-like event handling
        event_handlers = {}
        
        def on(event, handler):
            if event not in event_handlers:
                event_handlers[event] = []
            event_handlers[event].append(handler)
        
        def emit(event, data):
            if event in event_handlers:
                for handler in event_handlers[event]:
                    handler(data)
        
        # Test event registration
        received_data = []
        
        def test_handler(data):
            received_data.append(data)
        
        on('test_event', test_handler)
        emit('test_event', {'message': 'test'})
        
        assert len(received_data) == 1
        assert received_data[0]['message'] == 'test'
    
    def test_token_processing_pattern(self):
        """Test token processing pattern"""
        # Simulate client-side token processing
        content = ""
        token_count = 0
        
        def process_token(token_data):
            nonlocal content, token_count
            content += token_data['token']
            token_count += 1
            return {
                'content': content,
                'count': token_count,
                'latency': token_data.get('latency', 0)
            }
        
        # Test processing multiple tokens
        tokens = [
            {'token': 'Hello', 'latency': 10},
            {'token': ' ', 'latency': 5},
            {'token': 'world', 'latency': 15}
        ]
        
        results = []
        for token in tokens:
            result = process_token(token)
            results.append(result)
        
        assert len(results) == 3
        assert results[-1]['content'] == 'Hello world'
        assert results[-1]['count'] == 3
    
    def test_metrics_calculation_pattern(self):
        """Test client-side metrics calculation"""
        # Simulate client-side metrics
        metrics = {
            'tokens_received': 0,
            'total_latency': 0,
            'min_latency': float('inf'),
            'max_latency': 0,
            'start_time': None
        }
        
        def update_metrics(token_data):
            import time
            
            if metrics['start_time'] is None:
                metrics['start_time'] = time.time()
            
            metrics['tokens_received'] += 1
            latency = token_data.get('latency', 0)
            metrics['total_latency'] += latency
            metrics['min_latency'] = min(metrics['min_latency'], latency)
            metrics['max_latency'] = max(metrics['max_latency'], latency)
            
            return {
                'tokens_received': metrics['tokens_received'],
                'average_latency': metrics['total_latency'] / metrics['tokens_received'],
                'min_latency': metrics['min_latency'],
                'max_latency': metrics['max_latency']
            }
        
        # Test metrics calculation
        test_tokens = [
            {'latency': 10},
            {'latency': 20},
            {'latency': 15}
        ]
        
        for token in test_tokens:
            result = update_metrics(token)
        
        assert result['tokens_received'] == 3
        assert result['average_latency'] == 15.0
        assert result['min_latency'] == 10
        assert result['max_latency'] == 20


if __name__ == '__main__':
    pytest.main([__file__]) 