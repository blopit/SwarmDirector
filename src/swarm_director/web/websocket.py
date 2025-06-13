"""
WebSocket endpoints for SwarmDirector streaming functionality
Provides real-time streaming of AutoGen responses with backpressure handling
"""

import logging
import asyncio
import json
from typing import Dict, Any, Optional, List
from datetime import datetime
from flask import request, session
from flask_socketio import SocketIO, emit, disconnect, join_room, leave_room
from ..utils.streaming import StreamingManager, StreamingConfig, AutoGenStreamingAdapter
from ..utils.response_formatter import ResponseFormatter
from ..utils.error_handler import SwarmDirectorError, ValidationError

logger = logging.getLogger(__name__)

class WebSocketHandler:
    """
    WebSocket handler for streaming AutoGen responses
    Manages client connections, streaming sessions, and real-time communication
    """
    
    def __init__(self, socketio: SocketIO, streaming_manager: StreamingManager):
        """
        Initialize WebSocket handler
        
        Args:
            socketio: Flask-SocketIO instance
            streaming_manager: Global streaming manager instance
        """
        self.socketio = socketio
        self.streaming_manager = streaming_manager
        self.client_sessions: Dict[str, str] = {}  # client_id -> session_id mapping
        
        # Register event handlers
        self._register_handlers()
        
        logger.info("WebSocket handler initialized")
    
    def _register_handlers(self):
        """Register all WebSocket event handlers"""
        
        @self.socketio.on('connect')
        def handle_connect(auth=None):
            """Handle client connection"""
            try:
                client_id = request.sid
                logger.info(f"Client connected: {client_id}")
                
                # Send connection confirmation
                emit('connection_status', {
                    'status': 'connected',
                    'client_id': client_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'server_info': {
                        'streaming_enabled': True,
                        'max_buffer_size': self.streaming_manager.config.buffer_size,
                        'rate_limit': self.streaming_manager.config.max_tokens_per_second
                    }
                })
                
                return True
                
            except Exception as e:
                logger.error(f"Error handling connection: {str(e)}")
                emit('error', {'message': 'Connection failed', 'error': str(e)})
                return False
        
        @self.socketio.on('disconnect')
        def handle_disconnect():
            """Handle client disconnection"""
            try:
                client_id = request.sid
                logger.info(f"Client disconnected: {client_id}")
                
                # Clean up any active streaming sessions
                if client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                    asyncio.create_task(self.streaming_manager.stop_session(session_id))
                    del self.client_sessions[client_id]
                
            except Exception as e:
                logger.error(f"Error handling disconnection: {str(e)}")
        
        @self.socketio.on('start_stream')
        def handle_start_stream(data):
            """Start a new streaming session"""
            try:
                client_id = request.sid
                
                # Validate request data
                if not data or 'task_id' not in data:
                    emit('error', {'message': 'task_id is required'})
                    return
                
                task_id = data.get('task_id')
                stream_config = data.get('config', {})
                
                # Create streaming configuration
                config = StreamingConfig(
                    buffer_size=stream_config.get('buffer_size', 1000),
                    max_tokens_per_second=stream_config.get('rate_limit', 50),
                    backpressure_threshold=stream_config.get('backpressure_threshold', 0.8),
                    resume_threshold=stream_config.get('backpressure_resume_threshold', 0.3)
                )
                
                # Start streaming session
                session_id = asyncio.run(self._start_streaming_session(
                    client_id, task_id, config
                ))
                
                if session_id:
                    self.client_sessions[client_id] = session_id
                    
                    # Join client to session room for targeted messaging
                    join_room(session_id)
                    
                    # Create response config with both internal and client-friendly names
                    response_config = config.__dict__.copy()
                    response_config['rate_limit'] = config.max_tokens_per_second  # Add client-friendly alias
                    
                    emit('stream_started', {
                        'session_id': session_id,
                        'task_id': task_id,
                        'config': response_config,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('error', {'message': 'Failed to start streaming session'})
                
            except Exception as e:
                logger.error(f"Error starting stream: {str(e)}")
                emit('error', {'message': 'Failed to start stream', 'error': str(e)})
        
        @self.socketio.on('stop_stream')
        def handle_stop_stream(data):
            """Stop an active streaming session"""
            try:
                client_id = request.sid
                session_id = data.get('session_id') if data else None
                
                # Use client's active session if no session_id provided
                if not session_id and client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                
                if session_id:
                    asyncio.run(self.streaming_manager.close_session(session_id))
                    
                    # Clean up client session mapping
                    if client_id in self.client_sessions:
                        del self.client_sessions[client_id]
                    
                    # Leave session room
                    leave_room(session_id)
                    
                    emit('stream_stopped', {
                        'session_id': session_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('error', {'message': 'No active streaming session found'})
                
            except Exception as e:
                logger.error(f"Error stopping stream: {str(e)}")
                emit('error', {'message': 'Failed to stop stream', 'error': str(e)})
        
        @self.socketio.on('pause_stream')
        def handle_pause_stream(data):
            """Pause an active streaming session"""
            try:
                client_id = request.sid
                session_id = data.get('session_id') if data else None
                
                if not session_id and client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                
                if session_id:
                    session = self.streaming_manager.get_session(session_id)
                    if session:
                        asyncio.run(session.pause())
                    
                    emit('stream_paused', {
                        'session_id': session_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('error', {'message': 'No active streaming session found'})
                
            except Exception as e:
                logger.error(f"Error pausing stream: {str(e)}")
                emit('error', {'message': 'Failed to pause stream', 'error': str(e)})
        
        @self.socketio.on('resume_stream')
        def handle_resume_stream(data):
            """Resume a paused streaming session"""
            try:
                client_id = request.sid
                session_id = data.get('session_id') if data else None
                
                if not session_id and client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                
                if session_id:
                    session = self.streaming_manager.get_session(session_id)
                    if session:
                        asyncio.run(session.resume())
                    
                    emit('stream_resumed', {
                        'session_id': session_id,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('error', {'message': 'No active streaming session found'})
                
            except Exception as e:
                logger.error(f"Error resuming stream: {str(e)}")
                emit('error', {'message': 'Failed to resume stream', 'error': str(e)})
        
        @self.socketio.on('get_stream_status')
        def handle_get_stream_status(data):
            """Get status of streaming session"""
            try:
                client_id = request.sid
                session_id = data.get('session_id') if data else None
                
                if not session_id and client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                
                if session_id:
                    session = self.streaming_manager.get_session(session_id)
                    if session:
                        status = session.get_status()
                    
                    emit('stream_status', {
                        'session_id': session_id,
                        'status': status,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('stream_status', {
                        'session_id': None,
                        'status': None,
                        'message': 'No active streaming session'
                    })
                
            except Exception as e:
                logger.error(f"Error getting stream status: {str(e)}")
                emit('error', {'message': 'Failed to get stream status', 'error': str(e)})
        
        @self.socketio.on('get_stream_metrics')
        def handle_get_stream_metrics(data):
            """Get metrics for streaming session"""
            try:
                client_id = request.sid
                session_id = data.get('session_id') if data else None
                
                if not session_id and client_id in self.client_sessions:
                    session_id = self.client_sessions[client_id]
                
                if session_id:
                    session = self.streaming_manager.get_session(session_id)
                    if session:
                        status = session.get_status()
                        metrics = status.get('metrics', {})
                    
                    emit('stream_metrics', {
                        'session_id': session_id,
                        'metrics': metrics,
                        'timestamp': datetime.utcnow().isoformat()
                    })
                else:
                    emit('error', {'message': 'No active streaming session found'})
                
            except Exception as e:
                logger.error(f"Error getting stream metrics: {str(e)}")
                emit('error', {'message': 'Failed to get stream metrics', 'error': str(e)})
    
    async def _start_streaming_session(self, client_id: str, task_id: str, 
                                     config: StreamingConfig) -> Optional[str]:
        """
        Start a new streaming session for a client
        
        Args:
            client_id: WebSocket client identifier
            task_id: Task to stream responses for
            config: Streaming configuration
            
        Returns:
            Session ID if successful, None otherwise
        """
        try:
            # Create streaming session
            session = self.streaming_manager.create_session(
                f"ws_{client_id}_{task_id}"
            )
            session_id = session.session_id
            
            if not session_id:
                logger.error(f"Failed to create streaming session for client {client_id}")
                return None
            
            # Set up client handler for this session
            async def client_handler(token_data: Dict[str, Any]):
                """Handle streaming tokens for WebSocket client"""
                try:
                    # Emit token to specific client
                    self.socketio.emit('stream_token', {
                        'session_id': session_id,
                        'token': token_data.get('token', ''),
                        'metadata': token_data.get('metadata', {}),
                        'timestamp': datetime.utcnow().isoformat()
                    }, room=session_id)
                    
                except Exception as e:
                    logger.error(f"Error sending token to client: {str(e)}")
            
            # Register client handler
            session.add_client_handler(client_handler)
            
            logger.info(f"Started streaming session {session_id} for client {client_id}")
            return session_id
            
        except Exception as e:
            logger.error(f"Error starting streaming session: {str(e)}")
            return None
    
    def broadcast_system_message(self, message: str, message_type: str = 'info'):
        """
        Broadcast system message to all connected clients
        
        Args:
            message: Message content
            message_type: Type of message (info, warning, error)
        """
        try:
            self.socketio.emit('system_message', {
                'message': message,
                'type': message_type,
                'timestamp': datetime.utcnow().isoformat()
            })
            
            logger.info(f"Broadcasted system message: {message}")
            
        except Exception as e:
            logger.error(f"Error broadcasting system message: {str(e)}")
    
    def send_to_session(self, session_id: str, event: str, data: Dict[str, Any]):
        """
        Send message to specific streaming session
        
        Args:
            session_id: Target session ID
            event: Event name
            data: Event data
        """
        try:
            self.socketio.emit(event, data, room=session_id)
            logger.debug(f"Sent {event} to session {session_id}")
            
        except Exception as e:
            logger.error(f"Error sending to session {session_id}: {str(e)}")
    
    def get_active_sessions(self) -> Dict[str, str]:
        """Get mapping of active client sessions"""
        return self.client_sessions.copy()
    
    def cleanup_client_session(self, client_id: str):
        """Clean up client session on disconnect"""
        try:
            if client_id in self.client_sessions:
                session_id = self.client_sessions[client_id]
                asyncio.create_task(self.streaming_manager.close_session(session_id))
                del self.client_sessions[client_id]
                logger.info(f"Cleaned up session for client {client_id}")
                
        except Exception as e:
            logger.error(f"Error cleaning up client session: {str(e)}")


def create_websocket_app(app, streaming_manager: StreamingManager) -> SocketIO:
    """
    Create and configure SocketIO instance with WebSocket handlers
    
    Args:
        app: Flask application instance
        streaming_manager: Global streaming manager
        
    Returns:
        Configured SocketIO instance
    """
    # Configure SocketIO with CORS and async support
    socketio = SocketIO(
        app,
        cors_allowed_origins="*",  # Configure appropriately for production
        async_mode='threading',  # Use threading for better Flask integration
        logger=True,
        engineio_logger=True,
        ping_timeout=60,
        ping_interval=25
    )
    
    # Create WebSocket handler
    ws_handler = WebSocketHandler(socketio, streaming_manager)
    
    # Store handler reference in app extensions
    app.extensions['websocket_handler'] = ws_handler
    
    logger.info("WebSocket application configured")
    return socketio


def register_websocket_routes(app):
    """
    Register HTTP endpoints for WebSocket management
    
    Args:
        app: Flask application instance
    """
    
    @app.route('/api/websocket/status')
    def websocket_status():
        """Get WebSocket server status"""
        try:
            ws_handler = app.extensions.get('websocket_handler')
            streaming_manager = app.extensions.get('streaming_manager')
            
            if not ws_handler or not streaming_manager:
                return ResponseFormatter.error(
                    'WebSocket services not available',
                    status_code=503
                )
            
            active_sessions = ws_handler.get_active_sessions()
            global_status = asyncio.run(streaming_manager.get_global_status())
            
            return ResponseFormatter.success(data={
                'websocket_enabled': True,
                'active_client_sessions': len(active_sessions),
                'active_streaming_sessions': len(global_status.get('sessions', {})),
                'server_metrics': global_status.get('metrics', {}),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error getting WebSocket status: {str(e)}")
            return ResponseFormatter.error(
                'Failed to get WebSocket status',
                details={'error': str(e)},
                status_code=500
            )
    
    @app.route('/api/websocket/sessions')
    def list_websocket_sessions():
        """List active WebSocket sessions"""
        try:
            ws_handler = app.extensions.get('websocket_handler')
            streaming_manager = app.extensions.get('streaming_manager')
            
            if not ws_handler or not streaming_manager:
                return ResponseFormatter.error(
                    'WebSocket services not available',
                    status_code=503
                )
            
            client_sessions = ws_handler.get_active_sessions()
            global_status = asyncio.run(streaming_manager.get_global_status())
            
            sessions_info = []
            for client_id, session_id in client_sessions.items():
                session_status = global_status.get('sessions', {}).get(session_id, {})
                sessions_info.append({
                    'client_id': client_id,
                    'session_id': session_id,
                    'status': session_status.get('state', 'unknown'),
                    'metrics': session_status.get('metrics', {})
                })
            
            return ResponseFormatter.success(data={
                'sessions': sessions_info,
                'total_sessions': len(sessions_info),
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except Exception as e:
            logger.error(f"Error listing WebSocket sessions: {str(e)}")
            return ResponseFormatter.error(
                'Failed to list WebSocket sessions',
                details={'error': str(e)},
                status_code=500
            )
    
    @app.route('/api/websocket/broadcast', methods=['POST'])
    def broadcast_message():
        """Broadcast message to all connected WebSocket clients"""
        try:
            from ..utils.validation import RequestValidator
            
            # Validate request
            RequestValidator.validate_content_type()
            data = RequestValidator.validate_json_body()
            
            if not data or 'message' not in data:
                raise ValidationError('Field "message" is required', field='message')
            
            message = data.get('message')
            message_type = data.get('type', 'info')
            
            # Get WebSocket handler
            ws_handler = app.extensions.get('websocket_handler')
            if not ws_handler:
                return ResponseFormatter.error(
                    'WebSocket services not available',
                    status_code=503
                )
            
            # Broadcast message
            ws_handler.broadcast_system_message(message, message_type)
            
            return ResponseFormatter.success(data={
                'message': 'Message broadcasted successfully',
                'broadcast_message': message,
                'message_type': message_type,
                'timestamp': datetime.utcnow().isoformat()
            })
            
        except ValidationError as e:
            return ResponseFormatter.error(
                'Validation failed',
                details={'field': e.field, 'message': str(e)},
                status_code=400
            )
        except Exception as e:
            logger.error(f"Error broadcasting message: {str(e)}")
            return ResponseFormatter.error(
                'Failed to broadcast message',
                details={'error': str(e)},
                status_code=500
            )
    
    logger.info("WebSocket HTTP routes registered") 