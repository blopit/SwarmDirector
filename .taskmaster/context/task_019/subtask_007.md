# Real-time Memory Monitoring

## Subtask Metadata
```yaml
subtask_id: "subtask_007"
parent_task: "task_019"
title: "Real-time Memory Monitoring"
type: "full_stack_development"
priority: "high"
estimated_effort: "4-5 days"
complexity: "high"
dependencies:
  - subtask_001
  - subtask_002
  - subtask_004
  - websocket_infrastructure
assignee: "full_stack_developer"
status: "blocked"
```

## Objective

Implement real-time memory monitoring capabilities using WebSocket connections to provide live updates of agent memory states, enabling developers to observe memory changes as they happen during agent execution and task processing.

## Technical Specifications

### Backend WebSocket Implementation

#### Memory Monitoring WebSocket Handler
```python
# src/swarm_director/websocket/memory_monitor.py
import asyncio
import json
import logging
from typing import Dict, Set, Optional, Any
from datetime import datetime
from flask_socketio import SocketIO, emit, join_room, leave_room
from ..services.memory_inspector import AgentMemoryInspector
from ..services.memory_monitor import MemoryStateMonitor
from ..utils.auth import verify_websocket_auth

logger = logging.getLogger(__name__)

class MemoryMonitoringWebSocket:
    """WebSocket handler for real-time memory monitoring"""
    
    def __init__(self, socketio: SocketIO):
        self.socketio = socketio
        self.memory_inspector = AgentMemoryInspector()
        self.memory_monitor = MemoryStateMonitor()
        
        # Track active monitoring sessions
        self.active_sessions: Dict[str, Dict[str, Any]] = {}
        self.agent_subscribers: Dict[int, Set[str]] = {}
        
        # Register WebSocket event handlers
        self.register_handlers()
        
        # Start background monitoring task
        self.monitoring_task = None
        
    def register_handlers(self):
        """Register WebSocket event handlers"""
        
        @self.socketio.on('connect', namespace='/memory-monitor')
        def handle_connect(auth):
            """Handle client connection"""
            try:
                # Verify authentication
                user_id = verify_websocket_auth(auth)
                if not user_id:
                    return False
                
                session_id = request.sid
                self.active_sessions[session_id] = {
                    'user_id': user_id,
                    'connected_at': datetime.utcnow(),
                    'monitored_agents': set(),
                    'last_heartbeat': datetime.utcnow()
                }
                
                logger.info(f"Memory monitoring client connected: {session_id}")
                emit('connection_established', {'session_id': session_id})
                
            except Exception as e:
                logger.error(f"Error handling memory monitor connection: {e}")
                return False
        
        @self.socketio.on('disconnect', namespace='/memory-monitor')
        def handle_disconnect():
            """Handle client disconnection"""
            session_id = request.sid
            
            if session_id in self.active_sessions:
                # Remove from agent subscriptions
                monitored_agents = self.active_sessions[session_id]['monitored_agents']
                for agent_id in monitored_agents:
                    self.unsubscribe_from_agent(session_id, agent_id)
                
                del self.active_sessions[session_id]
                logger.info(f"Memory monitoring client disconnected: {session_id}")
        
        @self.socketio.on('start_monitoring', namespace='/memory-monitor')
        def handle_start_monitoring(data):
            """Start monitoring an agent's memory"""
            try:
                session_id = request.sid
                agent_id = data.get('agent_id')
                monitoring_options = data.get('options', {})
                
                if not self.validate_agent_access(session_id, agent_id):
                    emit('error', {'message': 'Access denied for agent'})
                    return
                
                self.subscribe_to_agent(session_id, agent_id, monitoring_options)
                
                # Send initial memory state
                initial_state = self.memory_inspector.get_agent_memory_state(agent_id)
                emit('memory_state_update', {
                    'agent_id': agent_id,
                    'timestamp': datetime.utcnow().isoformat(),
                    'memory_state': initial_state,
                    'change_type': 'initial_load'
                })
                
                logger.info(f"Started monitoring agent {agent_id} for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error starting memory monitoring: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('stop_monitoring', namespace='/memory-monitor')
        def handle_stop_monitoring(data):
            """Stop monitoring an agent's memory"""
            try:
                session_id = request.sid
                agent_id = data.get('agent_id')
                
                self.unsubscribe_from_agent(session_id, agent_id)
                
                emit('monitoring_stopped', {'agent_id': agent_id})
                logger.info(f"Stopped monitoring agent {agent_id} for session {session_id}")
                
            except Exception as e:
                logger.error(f"Error stopping memory monitoring: {e}")
                emit('error', {'message': str(e)})
        
        @self.socketio.on('heartbeat', namespace='/memory-monitor')
        def handle_heartbeat():
            """Handle client heartbeat"""
            session_id = request.sid
            if session_id in self.active_sessions:
                self.active_sessions[session_id]['last_heartbeat'] = datetime.utcnow()
                emit('heartbeat_ack')
    
    def subscribe_to_agent(self, session_id: str, agent_id: int, options: Dict[str, Any]):
        """Subscribe session to agent memory updates"""
        if agent_id not in self.agent_subscribers:
            self.agent_subscribers[agent_id] = set()
        
        self.agent_subscribers[agent_id].add(session_id)
        self.active_sessions[session_id]['monitored_agents'].add(agent_id)
        
        # Start monitoring if this is the first subscriber
        if len(self.agent_subscribers[agent_id]) == 1:
            self.memory_monitor.start_monitoring(agent_id)
    
    def unsubscribe_from_agent(self, session_id: str, agent_id: int):
        """Unsubscribe session from agent memory updates"""
        if agent_id in self.agent_subscribers:
            self.agent_subscribers[agent_id].discard(session_id)
            
            # Stop monitoring if no more subscribers
            if len(self.agent_subscribers[agent_id]) == 0:
                self.memory_monitor.stop_monitoring(agent_id)
                del self.agent_subscribers[agent_id]
        
        if session_id in self.active_sessions:
            self.active_sessions[session_id]['monitored_agents'].discard(agent_id)
    
    def broadcast_memory_change(self, agent_id: int, change_event: Dict[str, Any]):
        """Broadcast memory change to all subscribers"""
        if agent_id in self.agent_subscribers:
            room_name = f"agent_{agent_id}"
            
            self.socketio.emit('memory_change_event', {
                'agent_id': agent_id,
                'timestamp': datetime.utcnow().isoformat(),
                'change_event': change_event
            }, room=room_name, namespace='/memory-monitor')
    
    def validate_agent_access(self, session_id: str, agent_id: int) -> bool:
        """Validate if session has access to monitor agent"""
        # Implement access control logic
        return True  # Simplified for now
    
    async def start_background_monitoring(self):
        """Start background task for memory monitoring"""
        self.monitoring_task = asyncio.create_task(self._monitoring_loop())
    
    async def stop_background_monitoring(self):
        """Stop background monitoring task"""
        if self.monitoring_task:
            self.monitoring_task.cancel()
            try:
                await self.monitoring_task
            except asyncio.CancelledError:
                pass
    
    async def _monitoring_loop(self):
        """Background loop for memory monitoring"""
        while True:
            try:
                # Check for memory changes in monitored agents
                for agent_id in list(self.agent_subscribers.keys()):
                    changes = self.memory_monitor.get_recent_changes(agent_id)
                    for change in changes:
                        self.broadcast_memory_change(agent_id, change)
                
                # Clean up inactive sessions
                await self._cleanup_inactive_sessions()
                
                await asyncio.sleep(1)  # Check every second
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Error in memory monitoring loop: {e}")
                await asyncio.sleep(5)  # Wait before retrying
    
    async def _cleanup_inactive_sessions(self):
        """Clean up inactive WebSocket sessions"""
        current_time = datetime.utcnow()
        inactive_sessions = []
        
        for session_id, session_data in self.active_sessions.items():
            last_heartbeat = session_data['last_heartbeat']
            if (current_time - last_heartbeat).total_seconds() > 60:  # 60 seconds timeout
                inactive_sessions.append(session_id)
        
        for session_id in inactive_sessions:
            logger.info(f"Cleaning up inactive session: {session_id}")
            # Remove from agent subscriptions
            monitored_agents = self.active_sessions[session_id]['monitored_agents']
            for agent_id in monitored_agents:
                self.unsubscribe_from_agent(session_id, agent_id)
            
            del self.active_sessions[session_id]
```

### Frontend Real-time Integration

#### Real-time Memory Hook
```jsx
// src/swarm_director/web/static/js/hooks/useRealTimeMemory.js
import { useState, useEffect, useCallback, useRef } from 'react';
import io from 'socket.io-client';

export const useRealTimeMemory = (agentId, options = {}) => {
    const [memoryState, setMemoryState] = useState(null);
    const [connectionStatus, setConnectionStatus] = useState('disconnected');
    const [lastUpdate, setLastUpdate] = useState(null);
    const [error, setError] = useState(null);
    
    const socketRef = useRef(null);
    const heartbeatIntervalRef = useRef(null);
    
    const {
        autoConnect = true,
        reconnectAttempts = 5,
        heartbeatInterval = 30000, // 30 seconds
        onMemoryChange = null,
        onConnectionChange = null
    } = options;
    
    const connect = useCallback(() => {
        if (socketRef.current?.connected) {
            return;
        }
        
        setConnectionStatus('connecting');
        setError(null);
        
        socketRef.current = io('/memory-monitor', {
            auth: {
                token: localStorage.getItem('auth_token')
            },
            reconnection: true,
            reconnectionAttempts: reconnectAttempts,
            reconnectionDelay: 1000
        });
        
        // Connection event handlers
        socketRef.current.on('connect', () => {
            setConnectionStatus('connected');
            setError(null);
            
            // Start monitoring the agent
            if (agentId) {
                socketRef.current.emit('start_monitoring', {
                    agent_id: agentId,
                    options: options
                });
            }
            
            // Start heartbeat
            startHeartbeat();
            
            if (onConnectionChange) {
                onConnectionChange('connected');
            }
        });
        
        socketRef.current.on('disconnect', () => {
            setConnectionStatus('disconnected');
            stopHeartbeat();
            
            if (onConnectionChange) {
                onConnectionChange('disconnected');
            }
        });
        
        socketRef.current.on('connect_error', (error) => {
            setConnectionStatus('error');
            setError(error.message);
            
            if (onConnectionChange) {
                onConnectionChange('error', error);
            }
        });
        
        // Memory monitoring event handlers
        socketRef.current.on('memory_state_update', (data) => {
            if (data.agent_id === agentId) {
                setMemoryState(data.memory_state);
                setLastUpdate(new Date(data.timestamp));
                
                if (onMemoryChange) {
                    onMemoryChange(data);
                }
            }
        });
        
        socketRef.current.on('memory_change_event', (data) => {
            if (data.agent_id === agentId) {
                // Update memory state with the change
                setMemoryState(prevState => {
                    const newState = applyMemoryChange(prevState, data.change_event);
                    return newState;
                });
                
                setLastUpdate(new Date(data.timestamp));
                
                if (onMemoryChange) {
                    onMemoryChange(data);
                }
            }
        });
        
        socketRef.current.on('error', (error) => {
            setError(error.message);
        });
        
        socketRef.current.on('heartbeat_ack', () => {
            // Heartbeat acknowledged
        });
        
    }, [agentId, reconnectAttempts, onMemoryChange, onConnectionChange]);
    
    const disconnect = useCallback(() => {
        if (socketRef.current) {
            if (agentId) {
                socketRef.current.emit('stop_monitoring', { agent_id: agentId });
            }
            
            socketRef.current.disconnect();
            socketRef.current = null;
        }
        
        stopHeartbeat();
        setConnectionStatus('disconnected');
    }, [agentId]);
    
    const startHeartbeat = useCallback(() => {
        if (heartbeatIntervalRef.current) {
            clearInterval(heartbeatIntervalRef.current);
        }
        
        heartbeatIntervalRef.current = setInterval(() => {
            if (socketRef.current?.connected) {
                socketRef.current.emit('heartbeat');
            }
        }, heartbeatInterval);
    }, [heartbeatInterval]);
    
    const stopHeartbeat = useCallback(() => {
        if (heartbeatIntervalRef.current) {
            clearInterval(heartbeatIntervalRef.current);
            heartbeatIntervalRef.current = null;
        }
    }, []);
    
    const applyMemoryChange = (currentState, changeEvent) => {
        // Apply memory change to current state
        // This would implement the logic to update the memory state
        // based on the change event received
        return { ...currentState, ...changeEvent.new_state };
    };
    
    // Auto-connect on mount
    useEffect(() => {
        if (autoConnect && agentId) {
            connect();
        }
        
        return () => {
            disconnect();
        };
    }, [agentId, autoConnect, connect, disconnect]);
    
    // Cleanup on unmount
    useEffect(() => {
        return () => {
            stopHeartbeat();
            if (socketRef.current) {
                socketRef.current.disconnect();
            }
        };
    }, [stopHeartbeat]);
    
    return {
        memoryState,
        connectionStatus,
        lastUpdate,
        error,
        connect,
        disconnect,
        isConnected: connectionStatus === 'connected',
        isConnecting: connectionStatus === 'connecting'
    };
};
```

#### Real-time Memory Inspector Component
```jsx
// Enhanced MemoryInspector with real-time capabilities
import { useRealTimeMemory } from '../hooks/useRealTimeMemory';

const RealTimeMemoryInspector = ({ agentId }) => {
    const [isRealTimeEnabled, setIsRealTimeEnabled] = useState(false);
    const [memoryChanges, setMemoryChanges] = useState([]);
    const [staticMemoryState, setStaticMemoryState] = useState(null);
    
    const {
        memoryState: realTimeMemoryState,
        connectionStatus,
        lastUpdate,
        error: realTimeError,
        connect,
        disconnect,
        isConnected
    } = useRealTimeMemory(agentId, {
        autoConnect: false,
        onMemoryChange: handleMemoryChange,
        onConnectionChange: handleConnectionChange
    });
    
    const handleMemoryChange = useCallback((data) => {
        // Add to memory changes log
        setMemoryChanges(prev => [
            {
                id: Date.now(),
                timestamp: data.timestamp,
                changeType: data.change_event?.change_type || 'update',
                details: data.change_event
            },
            ...prev.slice(0, 99) // Keep last 100 changes
        ]);
    }, []);
    
    const handleConnectionChange = useCallback((status, error) => {
        if (status === 'connected') {
            console.log('Real-time memory monitoring connected');
        } else if (status === 'error') {
            console.error('Real-time connection error:', error);
        }
    }, []);
    
    const toggleRealTime = useCallback(() => {
        if (isRealTimeEnabled) {
            disconnect();
            setIsRealTimeEnabled(false);
        } else {
            connect();
            setIsRealTimeEnabled(true);
        }
    }, [isRealTimeEnabled, connect, disconnect]);
    
    // Use real-time state when available, fallback to static
    const currentMemoryState = isRealTimeEnabled && realTimeMemoryState 
        ? realTimeMemoryState 
        : staticMemoryState;
    
    return (
        <div className="realtime-memory-inspector">
            <div className="inspector-header">
                <h3>Agent Memory Inspector - Agent {agentId}</h3>
                
                <div className="realtime-controls">
                    <div className="connection-status">
                        <span className={`status-indicator ${connectionStatus}`}>
                            <i className={`fas ${getConnectionIcon(connectionStatus)}`}></i>
                        </span>
                        <span className="status-text">{connectionStatus}</span>
                    </div>
                    
                    <button
                        className={`btn btn-sm ${isRealTimeEnabled ? 'btn-success' : 'btn-outline-secondary'}`}
                        onClick={toggleRealTime}
                        disabled={connectionStatus === 'connecting'}
                    >
                        <i className="fas fa-broadcast-tower"></i>
                        {isRealTimeEnabled ? 'Live' : 'Static'}
                    </button>
                    
                    {lastUpdate && (
                        <span className="last-update">
                            Last update: {lastUpdate.toLocaleTimeString()}
                        </span>
                    )}
                </div>
            </div>
            
            {realTimeError && (
                <div className="alert alert-warning">
                    <i className="fas fa-exclamation-triangle"></i>
                    Real-time connection error: {realTimeError}
                </div>
            )}
            
            <div className="inspector-content">
                <div className="memory-main-panel">
                    <MemoryStateViewer 
                        memoryState={currentMemoryState}
                        isRealTime={isRealTimeEnabled && isConnected}
                    />
                </div>
                
                <div className="memory-side-panel">
                    {isRealTimeEnabled && (
                        <RealTimeChangesPanel 
                            changes={memoryChanges}
                            connectionStatus={connectionStatus}
                        />
                    )}
                    
                    <MemoryMetricsPanel 
                        agentId={agentId}
                        memoryState={currentMemoryState}
                        isRealTime={isRealTimeEnabled}
                    />
                </div>
            </div>
        </div>
    );
};

const getConnectionIcon = (status) => {
    switch (status) {
        case 'connected': return 'fa-wifi';
        case 'connecting': return 'fa-spinner fa-spin';
        case 'disconnected': return 'fa-wifi-slash';
        case 'error': return 'fa-exclamation-triangle';
        default: return 'fa-question-circle';
    }
};
```

## Implementation Steps

### Step 1: Backend WebSocket Infrastructure (Day 1-2)
1. Implement `MemoryMonitoringWebSocket` class
2. Create WebSocket event handlers for memory monitoring
3. Integrate with existing memory monitoring system
4. Add authentication and access control

### Step 2: Real-time Memory Change Broadcasting (Day 2-3)
1. Enhance memory state monitor to support real-time updates
2. Implement change event broadcasting
3. Add session management and cleanup
4. Create background monitoring task

### Step 3: Frontend Real-time Integration (Day 3-4)
1. Create `useRealTimeMemory` hook
2. Implement WebSocket connection management
3. Add real-time state synchronization
4. Create connection status indicators

### Step 4: Enhanced UI Components (Day 4-5)
1. Enhance memory inspector with real-time capabilities
2. Create real-time changes panel
3. Add connection management controls
4. Implement error handling and recovery

## Testing Requirements

### Backend Tests
```python
# tests/test_memory_monitoring_websocket.py
import pytest
from unittest.mock import Mock, patch
from src.swarm_director.websocket.memory_monitor import MemoryMonitoringWebSocket

class TestMemoryMonitoringWebSocket:
    def test_client_connection(self):
        """Test WebSocket client connection"""
        
    def test_start_monitoring_agent(self):
        """Test starting agent memory monitoring"""
        
    def test_memory_change_broadcasting(self):
        """Test memory change event broadcasting"""
        
    def test_session_cleanup(self):
        """Test inactive session cleanup"""
```

### Frontend Tests
```javascript
// __tests__/useRealTimeMemory.test.js
import { renderHook, act } from '@testing-library/react-hooks';
import { useRealTimeMemory } from '../useRealTimeMemory';

describe('useRealTimeMemory', () => {
    test('connects to WebSocket on mount', () => {
        // Test WebSocket connection
    });
    
    test('handles memory state updates', () => {
        // Test memory state updates
    });
    
    test('manages connection status', () => {
        // Test connection status management
    });
});
```

## Success Criteria

### Functional Requirements
- [ ] Real-time WebSocket connection for memory monitoring
- [ ] Live memory state updates without page refresh
- [ ] Connection status management and error handling
- [ ] Session-based monitoring with proper cleanup
- [ ] Authentication and access control for WebSocket connections

### Performance Requirements
- [ ] Memory updates delivered within 100ms of change
- [ ] Support for 50+ concurrent monitoring sessions
- [ ] Efficient memory change detection and broadcasting
- [ ] Minimal impact on agent performance during monitoring

### Reliability Requirements
- [ ] Automatic reconnection on connection loss
- [ ] Graceful handling of WebSocket errors
- [ ] Session timeout and cleanup mechanisms
- [ ] Fallback to static mode when real-time unavailable

## Related Files
- `src/swarm_director/websocket/memory_monitor.py` - WebSocket handler
- `src/swarm_director/web/static/js/hooks/useRealTimeMemory.js` - React hook
- `src/swarm_director/web/static/js/components/RealTimeMemoryInspector.jsx` - Enhanced component
- `src/swarm_director/services/memory_monitor.py` - Enhanced monitoring service
