"""
AutoGen Streaming Interface for SwarmDirector
Provides real-time token streaming with buffering and backpressure handling
"""

import asyncio
import json
import logging
import time
from typing import Dict, List, Optional, AsyncGenerator, Callable, Any, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import deque
from abc import ABC, abstractmethod

logger = logging.getLogger(__name__)


class StreamingState(Enum):
    """States for streaming connections"""
    IDLE = "idle"
    STREAMING = "streaming"
    PAUSED = "paused"
    ERROR = "error"
    CLOSED = "closed"


@dataclass
class StreamingConfig:
    """Configuration for streaming behavior"""
    buffer_size: int = 1000
    max_tokens_per_second: int = 50
    backpressure_threshold: float = 0.8  # Pause when buffer is 80% full
    resume_threshold: float = 0.3  # Resume when buffer is 30% full
    chunk_size: int = 1  # Tokens per chunk
    timeout_seconds: int = 30
    enable_compression: bool = False
    heartbeat_interval: int = 10  # seconds


@dataclass
class StreamingMetrics:
    """Metrics for streaming performance"""
    tokens_sent: int = 0
    chunks_sent: int = 0
    bytes_sent: int = 0
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    errors: int = 0
    pauses: int = 0
    average_latency: float = 0.0
    peak_buffer_size: int = 0
    
    def get_duration(self) -> float:
        """Get streaming duration in seconds"""
        if self.start_time and self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return 0.0
    
    def get_tokens_per_second(self) -> float:
        """Calculate tokens per second rate"""
        duration = self.get_duration()
        return self.tokens_sent / duration if duration > 0 else 0.0


class TokenBuffer:
    """Thread-safe token buffer with backpressure control"""
    
    def __init__(self, config: StreamingConfig):
        self.config = config
        self.buffer = deque(maxlen=config.buffer_size)
        self.lock = asyncio.Lock()
        self.not_empty = asyncio.Condition(self.lock)
        self.not_full = asyncio.Condition(self.lock)
        self._closed = False
        self.metrics = StreamingMetrics()
    
    async def put(self, token: str) -> bool:
        """Add token to buffer, returns False if buffer is full"""
        async with self.not_full:
            if self._closed:
                return False
            
            if len(self.buffer) >= self.config.buffer_size:
                return False  # Buffer full, apply backpressure
            
            self.buffer.append(token)
            self.metrics.peak_buffer_size = max(self.metrics.peak_buffer_size, len(self.buffer))
            self.not_empty.notify()
            return True
    
    async def get(self) -> Optional[str]:
        """Get token from buffer, returns None if buffer is empty"""
        async with self.not_empty:
            if self._closed and not self.buffer:
                return None
            
            while not self.buffer and not self._closed:
                await self.not_empty.wait()
            
            if self.buffer:
                token = self.buffer.popleft()
                self.not_full.notify()
                return token
            
            return None
    
    async def get_chunk(self, size: int = None) -> List[str]:
        """Get multiple tokens as a chunk"""
        size = size or self.config.chunk_size
        chunk = []
        
        for _ in range(size):
            token = await self.get()
            if token is None:
                break
            chunk.append(token)
        
        return chunk
    
    def size(self) -> int:
        """Get current buffer size"""
        return len(self.buffer)
    
    def is_full(self) -> bool:
        """Check if buffer is at backpressure threshold"""
        return len(self.buffer) >= (self.config.buffer_size * self.config.backpressure_threshold)
    
    def should_resume(self) -> bool:
        """Check if streaming should resume"""
        return len(self.buffer) <= (self.config.buffer_size * self.config.resume_threshold)
    
    async def close(self):
        """Close the buffer"""
        async with self.lock:
            self._closed = True
            self.not_empty.notify_all()
            self.not_full.notify_all()


class StreamingSession:
    """Manages a single streaming session"""
    
    def __init__(self, session_id: str, config: StreamingConfig = None):
        self.session_id = session_id
        self.config = config or StreamingConfig()
        self.buffer = TokenBuffer(self.config)
        self.state = StreamingState.IDLE
        self.created_at = datetime.now()
        self.last_activity = self.created_at
        self.error_message: Optional[str] = None
        self.client_handlers: List[Callable] = []
        self._streaming_task: Optional[asyncio.Task] = None
        
    def add_client_handler(self, handler: Callable[[str], None]):
        """Add a client handler for receiving tokens"""
        self.client_handlers.append(handler)
    
    def remove_client_handler(self, handler: Callable):
        """Remove a client handler"""
        if handler in self.client_handlers:
            self.client_handlers.remove(handler)
    
    async def start_streaming(self, token_generator: AsyncGenerator[str, None]):
        """Start streaming tokens from generator"""
        if self.state != StreamingState.IDLE:
            raise ValueError(f"Cannot start streaming in state: {self.state}")
        
        self.state = StreamingState.STREAMING
        self.buffer.metrics.start_time = datetime.now()
        
        try:
            # Start producer task
            producer_task = asyncio.create_task(self._produce_tokens(token_generator))
            
            # Start consumer task
            consumer_task = asyncio.create_task(self._consume_tokens())
            
            # Wait for both tasks
            await asyncio.gather(producer_task, consumer_task)
            
        except Exception as e:
            self.state = StreamingState.ERROR
            self.error_message = str(e)
            logger.error(f"Streaming error in session {self.session_id}: {e}")
            raise
        finally:
            self.buffer.metrics.end_time = datetime.now()
            await self.buffer.close()
    
    async def _produce_tokens(self, token_generator: AsyncGenerator[str, None]):
        """Producer coroutine that feeds tokens into buffer"""
        try:
            async for token in token_generator:
                if self.state == StreamingState.CLOSED:
                    break
                
                # Apply backpressure
                while self.buffer.is_full() and self.state == StreamingState.STREAMING:
                    self.state = StreamingState.PAUSED
                    self.buffer.metrics.pauses += 1
                    await asyncio.sleep(0.1)  # Brief pause
                
                if self.state == StreamingState.PAUSED and self.buffer.should_resume():
                    self.state = StreamingState.STREAMING
                
                success = await self.buffer.put(token)
                if not success:
                    logger.warning(f"Failed to buffer token in session {self.session_id}")
                
                self.last_activity = datetime.now()
                
        except Exception as e:
            logger.error(f"Producer error in session {self.session_id}: {e}")
            self.state = StreamingState.ERROR
            self.error_message = str(e)
    
    async def _consume_tokens(self):
        """Consumer coroutine that sends tokens to clients"""
        try:
            while self.state in [StreamingState.STREAMING, StreamingState.PAUSED]:
                chunk = await self.buffer.get_chunk()
                if not chunk:
                    break
                
                # Send chunk to all client handlers
                for handler in self.client_handlers:
                    try:
                        await self._send_to_handler(handler, chunk)
                    except Exception as e:
                        logger.error(f"Handler error in session {self.session_id}: {e}")
                        self.buffer.metrics.errors += 1
                
                # Update metrics
                self.buffer.metrics.tokens_sent += len(chunk)
                self.buffer.metrics.chunks_sent += 1
                
                # Rate limiting
                await self._apply_rate_limit()
                
        except Exception as e:
            logger.error(f"Consumer error in session {self.session_id}: {e}")
            self.state = StreamingState.ERROR
            self.error_message = str(e)
    
    async def _send_to_handler(self, handler: Callable, chunk: List[str]):
        """Send chunk to a specific handler"""
        start_time = time.time()
        
        if asyncio.iscoroutinefunction(handler):
            await handler(chunk)
        else:
            handler(chunk)
        
        # Update latency metrics
        latency = time.time() - start_time
        self.buffer.metrics.average_latency = (
            (self.buffer.metrics.average_latency * self.buffer.metrics.chunks_sent + latency) /
            (self.buffer.metrics.chunks_sent + 1)
        )
    
    async def _apply_rate_limit(self):
        """Apply rate limiting based on configuration"""
        if self.config.max_tokens_per_second > 0:
            delay = 1.0 / self.config.max_tokens_per_second
            await asyncio.sleep(delay)
    
    async def pause(self):
        """Pause the streaming session"""
        if self.state == StreamingState.STREAMING:
            self.state = StreamingState.PAUSED
    
    async def resume(self):
        """Resume the streaming session"""
        if self.state == StreamingState.PAUSED:
            self.state = StreamingState.STREAMING
    
    async def close(self):
        """Close the streaming session"""
        self.state = StreamingState.CLOSED
        await self.buffer.close()
        
        if self._streaming_task and not self._streaming_task.done():
            self._streaming_task.cancel()
    
    def get_status(self) -> Dict[str, Any]:
        """Get current session status"""
        return {
            "session_id": self.session_id,
            "state": self.state.value,
            "buffer_size": self.buffer.size(),
            "buffer_capacity": self.config.buffer_size,
            "created_at": self.created_at.isoformat(),
            "last_activity": self.last_activity.isoformat(),
            "error_message": self.error_message,
            "client_count": len(self.client_handlers),
            "metrics": {
                "tokens_sent": self.buffer.metrics.tokens_sent,
                "chunks_sent": self.buffer.metrics.chunks_sent,
                "errors": self.buffer.metrics.errors,
                "pauses": self.buffer.metrics.pauses,
                "average_latency": self.buffer.metrics.average_latency,
                "tokens_per_second": self.buffer.metrics.get_tokens_per_second()
            }
        }


class AutoGenStreamingAdapter:
    """Adapter to convert AutoGen responses into streaming tokens"""
    
    def __init__(self, config: StreamingConfig = None):
        self.config = config or StreamingConfig()
    
    async def stream_from_response(self, response: str) -> AsyncGenerator[str, None]:
        """Convert a complete response into streaming tokens"""
        words = response.split()
        
        for word in words:
            yield word + " "
            # Add small delay to simulate streaming
            await asyncio.sleep(0.01)
    
    async def stream_from_generator(self, generator: AsyncGenerator[str, None]) -> AsyncGenerator[str, None]:
        """Pass through an existing async generator"""
        async for token in generator:
            yield token
    
    async def stream_from_autogen_chat(self, chat_result: Dict) -> AsyncGenerator[str, None]:
        """Extract and stream content from AutoGen chat result"""
        if "chat_history" in chat_result:
            for message in chat_result["chat_history"]:
                if "content" in message:
                    async for token in self.stream_from_response(message["content"]):
                        yield token
        elif "content" in chat_result:
            async for token in self.stream_from_response(chat_result["content"]):
                yield token


class StreamingManager:
    """Manages multiple streaming sessions"""
    
    def __init__(self, config: StreamingConfig = None):
        self.config = config or StreamingConfig()
        self.sessions: Dict[str, StreamingSession] = {}
        self.cleanup_task: Optional[asyncio.Task] = None
        
    def create_session(self, session_id: str = None) -> StreamingSession:
        """Create a new streaming session"""
        if session_id is None:
            session_id = f"stream_{int(time.time() * 1000)}"
        
        if session_id in self.sessions:
            raise ValueError(f"Session {session_id} already exists")
        
        session = StreamingSession(session_id, self.config)
        self.sessions[session_id] = session
        
        # Start cleanup task if not running
        if self.cleanup_task is None or self.cleanup_task.done():
            self.cleanup_task = asyncio.create_task(self._cleanup_sessions())
        
        logger.info(f"Created streaming session: {session_id}")
        return session
    
    def get_session(self, session_id: str) -> Optional[StreamingSession]:
        """Get an existing streaming session"""
        return self.sessions.get(session_id)
    
    async def close_session(self, session_id: str):
        """Close and remove a streaming session"""
        if session_id in self.sessions:
            session = self.sessions[session_id]
            await session.close()
            del self.sessions[session_id]
            logger.info(f"Closed streaming session: {session_id}")
    
    async def close_all_sessions(self):
        """Close all streaming sessions"""
        for session_id in list(self.sessions.keys()):
            await self.close_session(session_id)
    
    async def _cleanup_sessions(self):
        """Periodic cleanup of inactive sessions"""
        while True:
            try:
                current_time = datetime.now()
                expired_sessions = []
                
                for session_id, session in self.sessions.items():
                    # Check for timeout
                    inactive_time = (current_time - session.last_activity).total_seconds()
                    if inactive_time > self.config.timeout_seconds:
                        expired_sessions.append(session_id)
                    
                    # Check for error state
                    elif session.state == StreamingState.ERROR:
                        expired_sessions.append(session_id)
                
                # Clean up expired sessions
                for session_id in expired_sessions:
                    await self.close_session(session_id)
                
                # Sleep before next cleanup
                await asyncio.sleep(self.config.heartbeat_interval)
                
            except Exception as e:
                logger.error(f"Error in session cleanup: {e}")
                await asyncio.sleep(self.config.heartbeat_interval)
    
    def get_all_sessions_status(self) -> Dict[str, Dict]:
        """Get status of all sessions"""
        return {
            session_id: session.get_status()
            for session_id, session in self.sessions.items()
        }


# Global streaming manager instance
_streaming_manager: Optional[StreamingManager] = None


def get_streaming_manager(config: StreamingConfig = None) -> StreamingManager:
    """Get or create the global streaming manager"""
    global _streaming_manager
    if _streaming_manager is None:
        _streaming_manager = StreamingManager(config)
    return _streaming_manager


async def create_streaming_session(session_id: str = None, config: StreamingConfig = None) -> StreamingSession:
    """Convenience function to create a streaming session"""
    manager = get_streaming_manager(config)
    return manager.create_session(session_id)


async def stream_autogen_response(response: Union[str, Dict], session_id: str = None) -> StreamingSession:
    """Stream an AutoGen response through a session"""
    session = await create_streaming_session(session_id)
    adapter = AutoGenStreamingAdapter(session.config)
    
    if isinstance(response, str):
        token_generator = adapter.stream_from_response(response)
    else:
        token_generator = adapter.stream_from_autogen_chat(response)
    
    await session.start_streaming(token_generator)
    return session 