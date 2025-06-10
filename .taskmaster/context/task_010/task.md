---
task_id: task_010
subtask_id: null
title: Implement AutoGen Streaming Interface
status: pending
priority: medium
parent_task: null
dependencies: ['task_004']
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Task Overview
Develop the streaming agent interface for real-time feedback using AutoGen's streaming capabilities.

## 📋 Metadata
- **ID**: task_010
- **Title**: Implement AutoGen Streaming Interface
- **Status**: pending
- **Priority**: medium
- **Parent Task**: null
- **Dependencies**: ['task_004']
- **Subtasks**: 3
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints
- **In Scope**: Complete real-time streaming interface with AutoGen integration, WebSocket support, token buffering, reconnection handling, and performance monitoring for live agent interactions
- **Out of Scope**: Video/audio streaming, file transfer streaming, peer-to-peer connections, mobile app integration, offline caching
- **Assumptions**: Python 3.8+, AutoGen framework available, WebSocket support in client, basic real-time communication knowledge, modern browser compatibility
- **Constraints**: Must handle 100+ concurrent streams, latency <200ms, support reconnection, maintain message ordering, work with existing AutoGen agents

---

## 🔍 1. Detailed Description

The AutoGen Streaming Interface provides real-time communication between clients and AutoGen agents, enabling live feedback during agent processing. It implements WebSocket-based streaming with token-level granularity, automatic reconnection, and comprehensive error handling. The interface supports multiple concurrent streams and integrates seamlessly with existing AutoGen agents.

### Key Features:
- **Real-time Streaming**: Token-by-token streaming of agent responses
- **WebSocket Integration**: Bidirectional communication with clients
- **AutoGen Compatibility**: Works with all AutoGen agent types
- **Reconnection Logic**: Automatic reconnection with state recovery
- **Performance Monitoring**: Real-time metrics and latency tracking
- **Concurrent Support**: Multiple simultaneous streaming sessions
- **Error Recovery**: Graceful handling of network interruptions

### Streaming Flow:
1. **Client Connection**: WebSocket connection establishment
2. **Agent Initialization**: AutoGen agent setup with streaming config
3. **Token Streaming**: Real-time token delivery to client
4. **State Management**: Maintain conversation state across connections
5. **Error Handling**: Automatic recovery and reconnection
6. **Session Cleanup**: Proper resource cleanup on disconnect

## 📁 2. Reference Artifacts & Files

### Project Structure
```
streaming/
├── __init__.py
├── autogen_streamer.py      # Main streaming interface
├── websocket_handler.py     # WebSocket connection management
├── token_buffer.py          # Token buffering and delivery
├── stream_monitor.py        # Performance monitoring
└── reconnection_manager.py  # Reconnection logic

websockets/
├── __init__.py
├── stream_endpoint.py       # WebSocket endpoints
├── connection_manager.py    # Connection lifecycle management
├── message_handler.py       # Message processing
└── auth_middleware.py       # Authentication for streams

client/
├── streaming_client.js      # JavaScript client library
├── reconnection.js          # Client-side reconnection
├── event_handlers.js        # Event handling utilities
└── examples/                # Usage examples
    ├── basic_stream.html
    └── advanced_stream.html

models/
├── stream_session.py        # Stream session data model
├── stream_metrics.py        # Performance metrics model
└── stream_event.py          # Stream event logging

tests/
├── test_autogen_streaming.py # Streaming functionality tests
├── test_websocket_handler.py # WebSocket tests
├── test_performance.py      # Performance and load tests
└── fixtures/                # Test data and mocks
    ├── mock_agents.py
    └── sample_streams.py
```

### Required Files
- **streaming/autogen_streamer.py**: Main streaming interface
- **websockets/stream_endpoint.py**: WebSocket endpoints
- **streaming/token_buffer.py**: Token buffering system
- **client/streaming_client.js**: Client-side library
- **tests/test_autogen_streaming.py**: Comprehensive test suite

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 AutoGen Streaming Interface (streaming/autogen_streamer.py)
```python
import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Callable, AsyncGenerator
from dataclasses import dataclass, field
import autogen
from streaming.token_buffer import TokenBuffer
from streaming.stream_monitor import StreamMonitor
from models.stream_session import StreamSession

@dataclass
class StreamConfig:
    """Configuration for streaming sessions."""
    session_id: str
    agent_config: Dict
    buffer_size: int = 1000
    flush_interval: float = 0.1  # seconds
    max_tokens_per_second: int = 50
    enable_monitoring: bool = True
    reconnection_timeout: int = 30  # seconds

class AutoGenStreamer:
    """
    Streaming interface for AutoGen agents with real-time token delivery.
    Provides WebSocket-based streaming with buffering and reconnection support.
    """

    def __init__(self, config: StreamConfig):
        """Initialize the AutoGen streamer."""
        self.config = config
        self.session_id = config.session_id
        self.logger = self._setup_logging()

        # Initialize components
        self.token_buffer = TokenBuffer(
            buffer_size=config.buffer_size,
            flush_interval=config.flush_interval
        )
        self.monitor = StreamMonitor() if config.enable_monitoring else None

        # Stream state
        self.is_streaming = False
        self.current_agent = None
        self.stream_callbacks = []
        self.error_callbacks = []

        # Performance tracking
        self.tokens_sent = 0
        self.start_time = None
        self.last_token_time = None

    def _setup_logging(self) -> logging.Logger:
        """Set up logging for streaming operations."""
        logger = logging.getLogger(f"AutoGenStreamer.{self.session_id}")
        logger.setLevel(logging.INFO)

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

        return logger

    async def initialize_agent(self, agent_type: str, agent_config: Dict) -> bool:
        """
        Initialize AutoGen agent for streaming.

        Args:
            agent_type: Type of agent to create
            agent_config: Configuration for the agent

        Returns:
            bool: True if initialization successful
        """
        try:
            # Create AutoGen agent with streaming configuration
            streaming_config = {
                **agent_config,
                "stream": True,
                "stream_callback": self._handle_token_stream,
                "temperature": agent_config.get("temperature", 0.7),
                "max_tokens": agent_config.get("max_tokens", 1000)
            }

            if agent_type == "assistant":
                self.current_agent = autogen.AssistantAgent(
                    name=f"StreamingAssistant_{self.session_id}",
                    llm_config=streaming_config
                )
            elif agent_type == "user_proxy":
                self.current_agent = autogen.UserProxyAgent(
                    name=f"StreamingUserProxy_{self.session_id}",
                    human_input_mode="NEVER",
                    code_execution_config=False
                )
            else:
                raise ValueError(f"Unsupported agent type: {agent_type}")

            self.logger.info(f"Agent initialized: {agent_type}")
            return True

        except Exception as e:
            self.logger.error(f"Agent initialization failed: {str(e)}")
            return False

    async def start_streaming(self, initial_message: str) -> AsyncGenerator[Dict, None]:
        """
        Start streaming conversation with the agent.

        Args:
            initial_message: Initial message to send to agent

        Yields:
            Dict: Stream events with tokens and metadata
        """
        if not self.current_agent:
            raise ValueError("Agent not initialized")

        self.is_streaming = True
        self.start_time = datetime.utcnow()
        self.tokens_sent = 0

        try:
            # Start monitoring if enabled
            if self.monitor:
                self.monitor.start_session(self.session_id)

            # Initialize token buffer
            await self.token_buffer.start()

            # Start agent conversation
            conversation_task = asyncio.create_task(
                self._run_agent_conversation(initial_message)
            )

            # Stream tokens as they become available
            async for token_event in self._stream_tokens():
                yield token_event

                # Check if conversation completed
                if conversation_task.done():
                    break

            # Wait for conversation completion
            await conversation_task

            # Send final completion event
            yield {
                "type": "completion",
                "session_id": self.session_id,
                "total_tokens": self.tokens_sent,
                "duration": (datetime.utcnow() - self.start_time).total_seconds(),
                "timestamp": datetime.utcnow().isoformat()
            }

        except Exception as e:
            self.logger.error(f"Streaming error: {str(e)}")
            yield {
                "type": "error",
                "session_id": self.session_id,
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }
        finally:
            await self._cleanup_stream()

    async def _run_agent_conversation(self, initial_message: str):
        """Run the agent conversation in background."""
        try:
            # Create user proxy for interaction
            user_proxy = autogen.UserProxyAgent(
                name="StreamingUser",
                human_input_mode="NEVER",
                code_execution_config=False
            )

            # Start conversation
            await user_proxy.a_initiate_chat(
                self.current_agent,
                message=initial_message
            )

        except Exception as e:
            self.logger.error(f"Agent conversation error: {str(e)}")
            await self.token_buffer.add_error(str(e))

    async def _stream_tokens(self) -> AsyncGenerator[Dict, None]:
        """Stream tokens from the buffer to clients."""
        while self.is_streaming:
            try:
                # Get tokens from buffer
                tokens = await self.token_buffer.get_tokens(timeout=1.0)

                if tokens:
                    for token_data in tokens:
                        # Create stream event
                        event = {
                            "type": "token",
                            "session_id": self.session_id,
                            "token": token_data["token"],
                            "position": token_data["position"],
                            "timestamp": token_data["timestamp"],
                            "metadata": token_data.get("metadata", {})
                        }

                        # Update metrics
                        self.tokens_sent += 1
                        self.last_token_time = datetime.utcnow()

                        # Monitor performance
                        if self.monitor:
                            self.monitor.record_token(self.session_id, token_data)

                        yield event

                # Check for completion
                if await self.token_buffer.is_complete():
                    break

            except asyncio.TimeoutError:
                # Send heartbeat to keep connection alive
                yield {
                    "type": "heartbeat",
                    "session_id": self.session_id,
                    "timestamp": datetime.utcnow().isoformat()
                }
            except Exception as e:
                self.logger.error(f"Token streaming error: {str(e)}")
                break

    def _handle_token_stream(self, token: str, **kwargs):
        """Handle token stream from AutoGen agent."""
        try:
            token_data = {
                "token": token,
                "position": self.tokens_sent,
                "timestamp": datetime.utcnow().isoformat(),
                "metadata": kwargs
            }

            # Add to buffer asynchronously
            asyncio.create_task(self.token_buffer.add_token(token_data))

        except Exception as e:
            self.logger.error(f"Token handling error: {str(e)}")

    async def stop_streaming(self):
        """Stop the streaming session."""
        self.is_streaming = False

        if self.token_buffer:
            await self.token_buffer.stop()

        if self.monitor:
            self.monitor.stop_session(self.session_id)

        self.logger.info(f"Streaming stopped for session {self.session_id}")

    async def _cleanup_stream(self):
        """Clean up streaming resources."""
        try:
            await self.stop_streaming()

            # Clean up agent resources
            if self.current_agent and hasattr(self.current_agent, 'cleanup'):
                await self.current_agent.cleanup()

            self.current_agent = None

        except Exception as e:
            self.logger.error(f"Cleanup error: {str(e)}")

    def add_stream_callback(self, callback: Callable):
        """Add callback for stream events."""
        self.stream_callbacks.append(callback)

    def add_error_callback(self, callback: Callable):
        """Add callback for error events."""
        self.error_callbacks.append(callback)

    async def get_session_metrics(self) -> Dict:
        """Get performance metrics for the session."""
        if not self.monitor:
            return {}

        return await self.monitor.get_session_metrics(self.session_id)
```

### 3.2 Token Buffer System (streaming/token_buffer.py)
```python
import asyncio
import time
from datetime import datetime
from typing import List, Dict, Optional
from collections import deque
import logging

class TokenBuffer:
    """
    High-performance token buffering system for streaming.
    Manages token queuing, batching, and delivery with configurable flush intervals.
    """

    def __init__(self, buffer_size: int = 1000, flush_interval: float = 0.1):
        """
        Initialize token buffer.

        Args:
            buffer_size: Maximum number of tokens to buffer
            flush_interval: Time interval for automatic flushing (seconds)
        """
        self.buffer_size = buffer_size
        self.flush_interval = flush_interval
        self.logger = logging.getLogger(__name__)

        # Buffer state
        self.token_queue = deque(maxlen=buffer_size)
        self.pending_tokens = []
        self.is_running = False
        self.is_complete = False

        # Synchronization
        self.queue_lock = asyncio.Lock()
        self.flush_event = asyncio.Event()
        self.completion_event = asyncio.Event()

        # Performance tracking
        self.tokens_processed = 0
        self.last_flush_time = time.time()
        self.flush_task = None

    async def start(self):
        """Start the token buffer processing."""
        self.is_running = True
        self.flush_task = asyncio.create_task(self._flush_loop())
        self.logger.info("Token buffer started")

    async def stop(self):
        """Stop the token buffer processing."""
        self.is_running = False

        if self.flush_task:
            self.flush_task.cancel()
            try:
                await self.flush_task
            except asyncio.CancelledError:
                pass

        # Flush remaining tokens
        await self._flush_tokens()
        self.logger.info("Token buffer stopped")

    async def add_token(self, token_data: Dict):
        """
        Add token to buffer.

        Args:
            token_data: Token data including token, position, timestamp, metadata
        """
        async with self.queue_lock:
            self.token_queue.append(token_data)
            self.tokens_processed += 1

            # Trigger flush if buffer is getting full
            if len(self.token_queue) >= self.buffer_size * 0.8:
                self.flush_event.set()

    async def add_error(self, error_message: str):
        """Add error to buffer."""
        error_data = {
            "type": "error",
            "error": error_message,
            "timestamp": datetime.utcnow().isoformat()
        }

        async with self.queue_lock:
            self.token_queue.append(error_data)
            self.flush_event.set()

    async def get_tokens(self, timeout: float = 1.0) -> List[Dict]:
        """
        Get available tokens from buffer.

        Args:
            timeout: Maximum time to wait for tokens

        Returns:
            List of token data
        """
        try:
            # Wait for tokens or timeout
            await asyncio.wait_for(self.flush_event.wait(), timeout=timeout)
            self.flush_event.clear()

            # Get pending tokens
            async with self.queue_lock:
                tokens = self.pending_tokens.copy()
                self.pending_tokens.clear()
                return tokens

        except asyncio.TimeoutError:
            return []

    async def mark_complete(self):
        """Mark token stream as complete."""
        self.is_complete = True
        self.completion_event.set()

        # Final flush
        await self._flush_tokens()

    async def is_complete(self) -> bool:
        """Check if token stream is complete."""
        return self.is_complete and len(self.token_queue) == 0

    async def _flush_loop(self):
        """Background loop for periodic token flushing."""
        while self.is_running:
            try:
                await asyncio.sleep(self.flush_interval)
                await self._flush_tokens()
            except asyncio.CancelledError:
                break
            except Exception as e:
                self.logger.error(f"Flush loop error: {str(e)}")

    async def _flush_tokens(self):
        """Flush tokens from queue to pending list."""
        async with self.queue_lock:
            if self.token_queue:
                # Move tokens to pending list
                while self.token_queue:
                    self.pending_tokens.append(self.token_queue.popleft())

                # Signal that tokens are available
                self.flush_event.set()
                self.last_flush_time = time.time()

    def get_buffer_stats(self) -> Dict:
        """Get buffer performance statistics."""
        return {
            "buffer_size": len(self.token_queue),
            "pending_tokens": len(self.pending_tokens),
            "tokens_processed": self.tokens_processed,
            "last_flush_time": self.last_flush_time,
            "is_running": self.is_running,
            "is_complete": self.is_complete
        }
```

---

## 🔌 4. API Endpoints

### 4.1 WebSocket Streaming Endpoints
```python
from flask import Flask
from flask_socketio import SocketIO, emit, join_room, leave_room
from streaming.autogen_streamer import AutoGenStreamer, StreamConfig
import asyncio
import json

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Active streaming sessions
active_sessions = {}

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    print(f"Client connected: {request.sid}")
    emit('connected', {'status': 'connected', 'session_id': request.sid})

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    session_id = request.sid
    print(f"Client disconnected: {session_id}")

    # Clean up streaming session
    if session_id in active_sessions:
        streamer = active_sessions[session_id]
        asyncio.create_task(streamer.stop_streaming())
        del active_sessions[session_id]

@socketio.on('start_stream')
def handle_start_stream(data):
    """Start a new streaming session."""
    try:
        session_id = request.sid

        # Validate request data
        required_fields = ['agent_type', 'message']
        for field in required_fields:
            if field not in data:
                emit('error', {'error': f'Missing required field: {field}'})
                return

        # Create stream configuration
        config = StreamConfig(
            session_id=session_id,
            agent_config=data.get('agent_config', {}),
            buffer_size=data.get('buffer_size', 1000),
            flush_interval=data.get('flush_interval', 0.1)
        )

        # Create and initialize streamer
        streamer = AutoGenStreamer(config)
        active_sessions[session_id] = streamer

        # Join session room
        join_room(session_id)

        # Start streaming in background
        asyncio.create_task(
            _run_streaming_session(streamer, data['agent_type'], data['message'], session_id)
        )

        emit('stream_started', {
            'session_id': session_id,
            'agent_type': data['agent_type'],
            'status': 'streaming'
        })

    except Exception as e:
        emit('error', {'error': str(e)})

@socketio.on('stop_stream')
def handle_stop_stream():
    """Stop the current streaming session."""
    session_id = request.sid

    if session_id in active_sessions:
        streamer = active_sessions[session_id]
        asyncio.create_task(streamer.stop_streaming())
        del active_sessions[session_id]

        emit('stream_stopped', {'session_id': session_id})
    else:
        emit('error', {'error': 'No active streaming session'})

@socketio.on('get_metrics')
def handle_get_metrics():
    """Get streaming session metrics."""
    session_id = request.sid

    if session_id in active_sessions:
        streamer = active_sessions[session_id]
        metrics = asyncio.create_task(streamer.get_session_metrics())
        emit('metrics', metrics.result())
    else:
        emit('error', {'error': 'No active streaming session'})

async def _run_streaming_session(streamer: AutoGenStreamer, agent_type: str, message: str, session_id: str):
    """Run streaming session in background."""
    try:
        # Initialize agent
        agent_initialized = await streamer.initialize_agent(agent_type, {})
        if not agent_initialized:
            socketio.emit('error', {'error': 'Agent initialization failed'}, room=session_id)
            return

        # Start streaming
        async for event in streamer.start_streaming(message):
            # Emit event to client
            socketio.emit('stream_event', event, room=session_id)

            # Handle different event types
            if event['type'] == 'completion':
                socketio.emit('stream_completed', event, room=session_id)
                break
            elif event['type'] == 'error':
                socketio.emit('stream_error', event, room=session_id)
                break

    except Exception as e:
        socketio.emit('error', {'error': str(e)}, room=session_id)
    finally:
        # Clean up session
        if session_id in active_sessions:
            del active_sessions[session_id]

# REST API endpoints for session management
@app.route('/api/v1/stream/sessions', methods=['GET'])
def list_active_sessions():
    """List all active streaming sessions."""
    sessions = []
    for session_id, streamer in active_sessions.items():
        sessions.append({
            'session_id': session_id,
            'tokens_sent': streamer.tokens_sent,
            'start_time': streamer.start_time.isoformat() if streamer.start_time else None,
            'is_streaming': streamer.is_streaming
        })

    return {'active_sessions': sessions, 'total_count': len(sessions)}

@app.route('/api/v1/stream/health', methods=['GET'])
def stream_health_check():
    """Health check for streaming service."""
    return {
        'status': 'healthy',
        'active_sessions': len(active_sessions),
        'timestamp': datetime.utcnow().isoformat()
    }
```

### 4.2 API Documentation
| Event Type | Direction | Description | Data Format |
|------------|-----------|-------------|-------------|
| `connect` | Client→Server | Establish connection | None |
| `start_stream` | Client→Server | Start streaming session | `{"agent_type": "...", "message": "..."}` |
| `stream_event` | Server→Client | Stream token/event | `{"type": "token", "token": "...", "position": N}` |
| `stop_stream` | Client→Server | Stop streaming | None |
| `stream_completed` | Server→Client | Stream completion | `{"type": "completion", "total_tokens": N}` |

---

## 📦 5. Dependencies

### 5.1 Required Packages
```txt
# Core streaming framework
flask-socketio==5.3.6
python-socketio==5.9.0

# WebSocket support
websockets==12.0
aiohttp==3.9.1

# AutoGen framework
pyautogen==0.2.0

# Async utilities
asyncio==3.4.3
aiofiles==23.2.1

# Performance monitoring
prometheus-client==0.19.0
psutil==5.9.6

# Client-side libraries (JavaScript)
# socket.io-client==4.7.2 (npm package)
# reconnecting-websocket==4.4.0 (npm package)

# Testing
pytest-asyncio==0.21.1
pytest-websocket==0.1.0
websocket-client==1.6.4
```

### 5.2 Installation Commands
```bash
# Install core streaming dependencies
pip install flask-socketio==5.3.6 python-socketio==5.9.0

# Install WebSocket support
pip install websockets==12.0 aiohttp==3.9.1

# Install AutoGen framework
pip install pyautogen==0.2.0

# Install async utilities
pip install asyncio==3.4.3 aiofiles==23.2.1

# Install monitoring
pip install prometheus-client==0.19.0 psutil==5.9.6

# Install testing dependencies
pip install pytest-asyncio==0.21.1 pytest-websocket==0.1.0 websocket-client==1.6.4

# Install JavaScript client dependencies (if using npm)
npm install socket.io-client@4.7.2 reconnecting-websocket@4.4.0
```

### 5.3 Environment Configuration
```bash
# Streaming Configuration
export STREAM_MAX_CONNECTIONS="100"
export STREAM_BUFFER_SIZE="1000"
export STREAM_FLUSH_INTERVAL="0.1"
export STREAM_TIMEOUT="300"

# WebSocket Configuration
export WEBSOCKET_PORT="5001"
export WEBSOCKET_HOST="0.0.0.0"
export CORS_ORIGINS="http://localhost:3000,https://yourdomain.com"

# Performance Settings
export STREAM_MAX_TOKENS_PER_SECOND="50"
export STREAM_HEARTBEAT_INTERVAL="30"
export STREAM_RECONNECTION_TIMEOUT="30"

# Monitoring
export PROMETHEUS_METRICS_PORT="8001"
export STREAM_LOG_LEVEL="INFO"
```

---

## 🛠️ 6. Implementation Plan
1. Create streaming module in utils/streaming.py
2. Implement AutoGen streaming configuration
3. Create WebSocket endpoint for streaming connections
4. Implement streaming agent wrapper
5. Add token buffering mechanism
6. Create client-side event handling
7. Implement reconnection logic
8. Add streaming performance monitoring
9. Create utility functions for stream management
10. Implement error handling for stream interruptions

---

## 🧪 7. Testing & QA
1. Test streaming with mock agents
2. Verify token delivery without loss
3. Test reconnection scenarios
4. Validate performance under various network conditions
5. Benchmark streaming latency
6. Test concurrent streaming connections

---

## 🔗 8. Integration & Related Tasks
- **Dependencies**: ['task_004']
- **Subtasks**: ['subtask_001', 'subtask_002', 'subtask_003']

---

## ⚠️ 9. Risks & Mitigations
| Risk | Mitigation |
|------|------------|
| Implementation complexity | Break down into smaller subtasks |
| Integration challenges | Follow defined interfaces and protocols |
| Performance issues | Implement monitoring and optimization |

---

## ✅ 10. Success Criteria
- [ ] All subtasks completed successfully
- [ ] Integration tests pass
- [ ] Performance requirements met
- [ ] Documentation updated
- [ ] Code review completed

---

## 🚀 11. Next Steps
1. Complete all subtasks in dependency order
2. Perform integration testing
3. Update documentation and examples
