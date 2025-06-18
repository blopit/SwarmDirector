"""
Flask Middleware for Request Queuing
Automatically queues requests during high load periods using the RequestQueueManager
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable
from functools import wraps
from flask import Flask, request, g, jsonify, current_app

from .request_queue import (
    RequestQueueManager, RequestType, QueuePriority, 
    get_request_queue_manager, RequestStatus
)
from .response_formatter import ResponseFormatter
from .metrics import metrics_collector

logger = logging.getLogger(__name__)

class QueueMiddleware:
    """Flask middleware for automatic request queuing"""
    
    def __init__(self, app: Optional[Flask] = None, queue_manager: Optional[RequestQueueManager] = None):
        self.app = app
        self.queue_manager = queue_manager
        self.enabled = True
        self.load_threshold = 0.8  # Queue requests when system load exceeds this
        
        if app:
            self.init_app(app)
    
    def init_app(self, app: Flask):
        """Initialize middleware with Flask app"""
        self.app = app
        
        # Get queue manager from app extensions or global
        if not self.queue_manager:
            self.queue_manager = app.extensions.get('request_queue_manager') or get_request_queue_manager()
        
        # Store middleware in app extensions
        if self.queue_manager:
            app.extensions['queue_middleware'] = self
            logger.info("QueueMiddleware initialized successfully")
        else:
            logger.warning("QueueMiddleware initialized without RequestQueueManager")

def get_queue_middleware() -> Optional[QueueMiddleware]:
    """Get the current queue middleware instance"""
    if current_app:
        return current_app.extensions.get('queue_middleware')
    return None

def initialize_queue_middleware(app: Flask, queue_manager: Optional[RequestQueueManager] = None) -> QueueMiddleware:
    """Initialize queue middleware for Flask app"""
    middleware = QueueMiddleware(app, queue_manager)
    return middleware
