/**
 * SwarmDirector Streaming Client
 * Handles real-time WebSocket streaming for AutoGen responses
 */

class StreamingClient {
    constructor(options = {}) {
        this.options = {
            url: options.url || window.location.origin,
            autoConnect: options.autoConnect !== false,
            reconnectAttempts: options.reconnectAttempts || 5,
            reconnectDelay: options.reconnectDelay || 1000,
            heartbeatInterval: options.heartbeatInterval || 30000,
            bufferSize: options.bufferSize || 1000,
            rateLimit: options.rateLimit || 50,
            backpressureThreshold: options.backpressureThreshold || 0.8,
            debug: options.debug || false,
            ...options
        };
        
        this.socket = null;
        this.isConnected = false;
        this.isStreaming = false;
        this.currentSessionId = null;
        this.reconnectCount = 0;
        this.heartbeatTimer = null;
        this.metrics = this.initializeMetrics();
        this.eventHandlers = new Map();
        this.streamBuffer = [];
        this.lastTokenTime = null;
        
        // Bind methods to preserve context
        this.connect = this.connect.bind(this);
        this.disconnect = this.disconnect.bind(this);
        this.startStream = this.startStream.bind(this);
        this.stopStream = this.stopStream.bind(this);
        this.pauseStream = this.pauseStream.bind(this);
        this.resumeStream = this.resumeStream.bind(this);
        
        if (this.options.autoConnect) {
            this.connect();
        }
    }
    
    initializeMetrics() {
        return {
            tokensReceived: 0,
            totalLatency: 0,
            averageLatency: 0,
            minLatency: Infinity,
            maxLatency: 0,
            connectionTime: null,
            streamStartTime: null,
            streamEndTime: null,
            reconnectCount: 0,
            errorsCount: 0,
            bytesReceived: 0,
            messagesReceived: 0
        };
    }
    
    log(level, message, data = null) {
        if (!this.options.debug && level === 'debug') return;
        
        const timestamp = new Date().toISOString();
        const logMessage = `[${timestamp}] [StreamingClient] [${level.toUpperCase()}] ${message}`;
        
        console[level](logMessage, data || '');
        
        // Emit log event for external handling
        this.emit('log', { level, message, data, timestamp });
    }
    
    connect() {
        if (this.isConnected || this.socket) {
            this.log('warn', 'Already connected or connection in progress');
            return Promise.resolve();
        }
        
        return new Promise((resolve, reject) => {
            try {
                this.log('info', 'Connecting to WebSocket server', { url: this.options.url });
                
                // Initialize Socket.IO connection
                this.socket = io(this.options.url, {
                    transports: ['websocket', 'polling'],
                    timeout: 10000,
                    forceNew: true
                });
                
                // Connection event handlers
                this.socket.on('connect', () => {
                    this.isConnected = true;
                    this.reconnectCount = 0;
                    this.metrics.connectionTime = Date.now();
                    this.log('info', 'Connected to WebSocket server', { socketId: this.socket.id });
                    this.startHeartbeat();
                    this.emit('connected', { socketId: this.socket.id });
                    resolve();
                });
                
                this.socket.on('disconnect', (reason) => {
                    this.isConnected = false;
                    this.isStreaming = false;
                    this.currentSessionId = null;
                    this.stopHeartbeat();
                    this.log('info', 'Disconnected from WebSocket server', { reason });
                    this.emit('disconnected', { reason });
                    
                    // Attempt reconnection if not manually disconnected
                    if (reason !== 'io client disconnect' && this.reconnectCount < this.options.reconnectAttempts) {
                        this.scheduleReconnect();
                    }
                });
                
                this.socket.on('connect_error', (error) => {
                    this.metrics.errorsCount++;
                    this.log('error', 'Connection error', error);
                    this.emit('error', { type: 'connection', error });
                    reject(error);
                });
                
                // Stream event handlers
                this.setupStreamEventHandlers();
                
            } catch (error) {
                this.log('error', 'Failed to initialize connection', error);
                reject(error);
            }
        });
    }
    
    setupStreamEventHandlers() {
        // Connection status
        this.socket.on('connection_status', (data) => {
            this.log('debug', 'Connection status received', data);
            this.emit('connectionStatus', data);
        });
        
        // Stream lifecycle events
        this.socket.on('stream_started', (data) => {
            this.isStreaming = true;
            this.currentSessionId = data.session_id;
            this.metrics.streamStartTime = Date.now();
            this.streamBuffer = [];
            this.log('info', 'Stream started', data);
            this.emit('streamStarted', data);
        });
        
        this.socket.on('stream_stopped', (data) => {
            this.isStreaming = false;
            this.currentSessionId = null;
            this.metrics.streamEndTime = Date.now();
            this.log('info', 'Stream stopped', data);
            this.emit('streamStopped', data);
        });
        
        this.socket.on('stream_paused', (data) => {
            this.log('info', 'Stream paused', data);
            this.emit('streamPaused', data);
        });
        
        this.socket.on('stream_resumed', (data) => {
            this.log('info', 'Stream resumed', data);
            this.emit('streamResumed', data);
        });
        
        // Token streaming
        this.socket.on('stream_token', (data) => {
            this.handleStreamToken(data);
        });
        
        // Status and metrics
        this.socket.on('stream_status', (data) => {
            this.log('debug', 'Stream status received', data);
            this.emit('streamStatus', data);
        });
        
        this.socket.on('stream_metrics', (data) => {
            this.log('debug', 'Stream metrics received', data);
            this.emit('streamMetrics', data);
        });
        
        // System messages
        this.socket.on('system_message', (data) => {
            this.log('info', `System message [${data.type}]: ${data.message}`);
            this.emit('systemMessage', data);
        });
        
        // Error handling
        this.socket.on('error', (data) => {
            this.metrics.errorsCount++;
            this.log('error', 'Stream error received', data);
            this.emit('streamError', data);
        });
    }
    
    handleStreamToken(data) {
        const receiveTime = Date.now();
        const sendTime = new Date(data.timestamp).getTime();
        const latency = receiveTime - sendTime;
        
        // Update metrics
        this.metrics.tokensReceived++;
        this.metrics.messagesReceived++;
        this.metrics.bytesReceived += JSON.stringify(data).length;
        this.metrics.totalLatency += latency;
        this.metrics.averageLatency = this.metrics.totalLatency / this.metrics.tokensReceived;
        this.metrics.minLatency = Math.min(this.metrics.minLatency, latency);
        this.metrics.maxLatency = Math.max(this.metrics.maxLatency, latency);
        
        // Add to buffer
        this.streamBuffer.push({
            ...data,
            receiveTime,
            latency
        });
        
        // Keep buffer size manageable
        if (this.streamBuffer.length > this.options.bufferSize) {
            this.streamBuffer.shift();
        }
        
        this.lastTokenTime = receiveTime;
        
        this.log('debug', `Token received: "${data.token}" (latency: ${latency}ms)`);
        this.emit('token', { ...data, latency, receiveTime });
    }
    
    startHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
        }
        
        this.heartbeatTimer = setInterval(() => {
            if (this.isConnected && this.socket) {
                this.socket.emit('ping', { timestamp: Date.now() });
            }
        }, this.options.heartbeatInterval);
    }
    
    stopHeartbeat() {
        if (this.heartbeatTimer) {
            clearInterval(this.heartbeatTimer);
            this.heartbeatTimer = null;
        }
    }
    
    scheduleReconnect() {
        this.reconnectCount++;
        this.metrics.reconnectCount++;
        const delay = this.options.reconnectDelay * Math.pow(2, this.reconnectCount - 1); // Exponential backoff
        
        this.log('info', `Scheduling reconnection attempt ${this.reconnectCount}/${this.options.reconnectAttempts} in ${delay}ms`);
        
        setTimeout(() => {
            if (!this.isConnected) {
                this.connect().catch(error => {
                    this.log('error', 'Reconnection failed', error);
                    if (this.reconnectCount >= this.options.reconnectAttempts) {
                        this.emit('reconnectFailed', { attempts: this.reconnectCount });
                    }
                });
            }
        }, delay);
    }
    
    disconnect() {
        this.log('info', 'Manually disconnecting');
        this.stopHeartbeat();
        
        if (this.socket) {
            this.socket.disconnect();
            this.socket = null;
        }
        
        this.isConnected = false;
        this.isStreaming = false;
        this.currentSessionId = null;
        this.reconnectCount = this.options.reconnectAttempts; // Prevent auto-reconnect
    }
    
    startStream(taskId, config = {}) {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        if (this.isStreaming) {
            throw new Error('Stream already active');
        }
        
        const streamConfig = {
            buffer_size: config.bufferSize || this.options.bufferSize,
            rate_limit: config.rateLimit || this.options.rateLimit,
            backpressure_threshold: config.backpressureThreshold || this.options.backpressureThreshold,
            backpressure_resume_threshold: config.backpressureResumeThreshold || 0.3,
            ...config
        };
        
        const data = {
            task_id: taskId,
            config: streamConfig
        };
        
        this.log('info', 'Starting stream', data);
        this.socket.emit('start_stream', data);
    }
    
    stopStream() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        this.log('info', 'Stopping stream');
        this.socket.emit('stop_stream', {});
    }
    
    pauseStream() {
        if (!this.isConnected || !this.isStreaming) {
            throw new Error('No active stream to pause');
        }
        
        this.log('info', 'Pausing stream');
        this.socket.emit('pause_stream', {});
    }
    
    resumeStream() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        this.log('info', 'Resuming stream');
        this.socket.emit('resume_stream', {});
    }
    
    getStreamStatus() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        this.socket.emit('get_stream_status', {});
    }
    
    getStreamMetrics() {
        if (!this.isConnected) {
            throw new Error('Not connected to WebSocket server');
        }
        
        this.socket.emit('get_stream_metrics', {});
    }
    
    // Event system
    on(event, handler) {
        if (!this.eventHandlers.has(event)) {
            this.eventHandlers.set(event, []);
        }
        this.eventHandlers.get(event).push(handler);
    }
    
    off(event, handler) {
        if (this.eventHandlers.has(event)) {
            const handlers = this.eventHandlers.get(event);
            const index = handlers.indexOf(handler);
            if (index > -1) {
                handlers.splice(index, 1);
            }
        }
    }
    
    emit(event, data) {
        if (this.eventHandlers.has(event)) {
            this.eventHandlers.get(event).forEach(handler => {
                try {
                    handler(data);
                } catch (error) {
                    this.log('error', `Error in event handler for ${event}`, error);
                }
            });
        }
    }
    
    // Utility methods
    getMetrics() {
        return { ...this.metrics };
    }
    
    getConnectionInfo() {
        return {
            isConnected: this.isConnected,
            isStreaming: this.isStreaming,
            currentSessionId: this.currentSessionId,
            socketId: this.socket?.id,
            reconnectCount: this.reconnectCount,
            bufferSize: this.streamBuffer.length
        };
    }
    
    getStreamBuffer() {
        return [...this.streamBuffer];
    }
    
    clearBuffer() {
        this.streamBuffer = [];
        this.log('info', 'Stream buffer cleared');
    }
    
    resetMetrics() {
        this.metrics = this.initializeMetrics();
        this.log('info', 'Metrics reset');
    }
}

// Export for use in other modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { StreamingClient };
} else if (typeof window !== 'undefined') {
    window.StreamingClient = StreamingClient;
} 