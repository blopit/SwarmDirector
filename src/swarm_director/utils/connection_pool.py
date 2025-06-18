"""
Connection Pool Manager for SwarmDirector
Provides centralized connection pool management, monitoring, and health checks
"""

import logging
import threading
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from contextlib import contextmanager
from sqlalchemy import create_engine, text, event
from sqlalchemy.pool import QueuePool, StaticPool, NullPool
from sqlalchemy.engine import Engine
from sqlalchemy.exc import SQLAlchemyError, DisconnectionError, TimeoutError as SQLTimeoutError
from flask import current_app

from .metrics import metrics_collector

logger = logging.getLogger(__name__)

@dataclass
class ConnectionPoolMetrics:
    """Metrics for connection pool performance"""
    pool_size: int = 0
    checked_out: int = 0
    overflow: int = 0
    invalid: int = 0
    total_connections: int = 0
    peak_checked_out: int = 0
    peak_overflow: int = 0
    connection_errors: int = 0
    timeout_errors: int = 0
    total_checkouts: int = 0
    total_checkins: int = 0
    avg_checkout_time: float = 0.0
    last_reset: datetime = field(default_factory=datetime.now)

@dataclass
class ConnectionPoolHealth:
    """Health status of connection pool"""
    is_healthy: bool = True
    pool_utilization: float = 0.0
    error_rate: float = 0.0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    last_check: datetime = field(default_factory=datetime.now)
    recommendations: List[str] = field(default_factory=list)

class ConnectionPoolManager:
    """Manages database connection pooling with monitoring and health checks"""
    
    def __init__(self, app=None):
        self.app = app
        self.engine: Optional[Engine] = None
        self.metrics = ConnectionPoolMetrics()
        self.health = ConnectionPoolHealth()
        self._lock = threading.RLock()
        self._checkout_times: Dict[int, float] = {}
        self._monitoring_enabled = True
        
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Initialize connection pool manager with Flask app"""
        self.app = app
        self._monitoring_enabled = app.config.get('CONNECTION_POOL_MONITORING', True)
        
        # Set up event listeners for pool monitoring
        if self._monitoring_enabled:
            self._setup_pool_listeners()
        
        # Store reference in app extensions
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['connection_pool_manager'] = self
        
        logger.info("Connection pool manager initialized")
    
    def _setup_pool_listeners(self):
        """Set up SQLAlchemy event listeners for pool monitoring"""
        
        @event.listens_for(Engine, "connect")
        def on_connect(dbapi_connection, connection_record):
            """Track new connections"""
            with self._lock:
                self.metrics.total_connections += 1
                logger.debug("New database connection created")
        
        @event.listens_for(Engine, "checkout")
        def on_checkout(dbapi_connection, connection_record, connection_proxy):
            """Track connection checkouts"""
            with self._lock:
                self.metrics.total_checkouts += 1
                connection_id = id(connection_proxy)
                self._checkout_times[connection_id] = time.time()
                
                # Update pool metrics
                if hasattr(self.engine, 'pool'):
                    pool = self.engine.pool
                    self.metrics.checked_out = pool.checkedout()
                    self.metrics.overflow = pool.overflow()
                    self.metrics.invalid = pool.invalidated()
                    self.metrics.peak_checked_out = max(
                        self.metrics.peak_checked_out, 
                        self.metrics.checked_out
                    )
                    self.metrics.peak_overflow = max(
                        self.metrics.peak_overflow, 
                        self.metrics.overflow
                    )
        
        @event.listens_for(Engine, "checkin")
        def on_checkin(dbapi_connection, connection_record):
            """Track connection checkins"""
            with self._lock:
                self.metrics.total_checkins += 1
                
                # Calculate checkout time if we tracked it
                for conn_id, checkout_time in list(self._checkout_times.items()):
                    checkout_duration = time.time() - checkout_time
                    # Update average checkout time
                    if self.metrics.total_checkins > 0:
                        self.metrics.avg_checkout_time = (
                            (self.metrics.avg_checkout_time * (self.metrics.total_checkins - 1) + 
                             checkout_duration) / self.metrics.total_checkins
                        )
                    del self._checkout_times[conn_id]
                    break  # Only process one entry per checkin
        
        @event.listens_for(Engine, "invalidate")
        def on_invalidate(dbapi_connection, connection_record, exception):
            """Track connection invalidations"""
            with self._lock:
                self.metrics.connection_errors += 1
                if exception:
                    self.health.last_error = str(exception)
                logger.warning(f"Database connection invalidated: {exception}")
    
    def get_engine(self) -> Optional[Engine]:
        """Get the current database engine"""
        return self.engine
    
    def set_engine(self, engine: Engine):
        """Set the database engine for monitoring"""
        self.engine = engine
        if hasattr(engine, 'pool'):
            pool = engine.pool
            self.metrics.pool_size = getattr(pool, 'size', lambda: 0)()
        logger.info("Database engine set for connection pool monitoring")
    
    @contextmanager
    def get_connection(self):
        """Context manager for getting database connections"""
        if not self.engine:
            raise RuntimeError("Database engine not initialized")
        
        connection = None
        start_time = time.time()
        
        try:
            connection = self.engine.connect()
            yield connection
        except SQLTimeoutError as e:
            with self._lock:
                self.metrics.timeout_errors += 1
            self.health.last_error = f"Connection timeout: {str(e)}"
            logger.error(f"Database connection timeout: {e}")
            raise
        except SQLAlchemyError as e:
            with self._lock:
                self.metrics.connection_errors += 1
            self.health.last_error = f"Database error: {str(e)}"
            logger.error(f"Database connection error: {e}")
            raise
        finally:
            if connection:
                try:
                    connection.close()
                except Exception as e:
                    logger.warning(f"Error closing connection: {e}")
            
            # Update response time metrics
            response_time = time.time() - start_time
            self.health.avg_response_time = (
                (self.health.avg_response_time * 0.9) + (response_time * 0.1)
            )
    
    def get_pool_status(self) -> Dict[str, Any]:
        """Get current connection pool status"""
        if not self.engine or not hasattr(self.engine, 'pool'):
            return {'error': 'Database engine or pool not available'}
        
        pool = self.engine.pool
        
        try:
            with self._lock:
                status = {
                    'pool_size': getattr(pool, 'size', lambda: 0)(),
                    'checked_out': pool.checkedout(),
                    'overflow': pool.overflow(),
                    'invalid': pool.invalidated(),
                    'total_connections': self.metrics.total_connections,
                    'peak_checked_out': self.metrics.peak_checked_out,
                    'peak_overflow': self.metrics.peak_overflow,
                    'total_checkouts': self.metrics.total_checkouts,
                    'total_checkins': self.metrics.total_checkins,
                    'connection_errors': self.metrics.connection_errors,
                    'timeout_errors': self.metrics.timeout_errors,
                    'avg_checkout_time': self.metrics.avg_checkout_time,
                    'last_updated': datetime.now().isoformat()
                }
                
                # Calculate utilization
                if status['pool_size'] > 0:
                    utilization = (status['checked_out'] + status['overflow']) / (
                        status['pool_size'] + status['overflow']
                    )
                    status['utilization_percent'] = round(utilization * 100, 2)
                else:
                    status['utilization_percent'] = 0.0
                
                return status
        except Exception as e:
            logger.error(f"Error getting pool status: {e}")
            return {'error': str(e)}
    
    def get_health_status(self) -> ConnectionPoolHealth:
        """Get connection pool health assessment"""
        try:
            status = self.get_pool_status()
            
            if 'error' in status:
                self.health.is_healthy = False
                self.health.last_error = status['error']
                return self.health
            
            # Calculate health metrics
            self.health.pool_utilization = status.get('utilization_percent', 0.0) / 100.0
            
            # Calculate error rate (errors per 100 operations)
            total_operations = max(status.get('total_checkouts', 0), 1)
            total_errors = status.get('connection_errors', 0) + status.get('timeout_errors', 0)
            self.health.error_rate = (total_errors / total_operations) * 100
            
            # Determine overall health
            self.health.is_healthy = (
                self.health.pool_utilization < 0.9 and  # Less than 90% utilization
                self.health.error_rate < 5.0 and        # Less than 5% error rate
                self.health.avg_response_time < 1.0     # Less than 1 second avg response
            )
            
            # Generate recommendations
            self.health.recommendations = []
            
            if self.health.pool_utilization > 0.8:
                self.health.recommendations.append(
                    "High pool utilization detected. Consider increasing pool_size or max_overflow."
                )
            
            if self.health.error_rate > 2.0:
                self.health.recommendations.append(
                    "High error rate detected. Check database connectivity and pool configuration."
                )
            
            if self.health.avg_response_time > 0.5:
                self.health.recommendations.append(
                    "Slow database responses detected. Consider optimizing queries or database performance."
                )
            
            if status.get('timeout_errors', 0) > 0:
                self.health.recommendations.append(
                    "Connection timeouts detected. Consider increasing pool_timeout setting."
                )
            
            self.health.last_check = datetime.now()
            
        except Exception as e:
            logger.error(f"Error assessing pool health: {e}")
            self.health.is_healthy = False
            self.health.last_error = str(e)
        
        return self.health
    
    def test_connection(self) -> bool:
        """Test database connectivity"""
        try:
            with self.get_connection() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                return result == 1
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False
    
    def reset_metrics(self):
        """Reset connection pool metrics"""
        with self._lock:
            self.metrics = ConnectionPoolMetrics()
            self._checkout_times.clear()
            logger.info("Connection pool metrics reset")
    
    def collect_metrics_for_monitoring(self):
        """Collect metrics for external monitoring systems"""
        if not self._monitoring_enabled:
            return
        
        try:
            status = self.get_pool_status()
            health = self.get_health_status()
            
            if 'error' not in status:
                # Send metrics to metrics collector
                metrics_collector.track_gauge(
                    'connection_pool_size', 
                    status.get('pool_size', 0)
                )
                metrics_collector.track_gauge(
                    'connection_pool_checked_out', 
                    status.get('checked_out', 0)
                )
                metrics_collector.track_gauge(
                    'connection_pool_overflow', 
                    status.get('overflow', 0)
                )
                metrics_collector.track_gauge(
                    'connection_pool_utilization', 
                    status.get('utilization_percent', 0.0)
                )
                metrics_collector.track_gauge(
                    'connection_pool_error_rate', 
                    health.error_rate
                )
                metrics_collector.track_gauge(
                    'connection_pool_avg_response_time', 
                    health.avg_response_time * 1000  # Convert to milliseconds
                )
                
                # Track health as binary metric
                metrics_collector.track_gauge(
                    'connection_pool_healthy', 
                    1.0 if health.is_healthy else 0.0
                )
        
        except Exception as e:
            logger.error(f"Error collecting pool metrics: {e}")

# Global connection pool manager instance
connection_pool_manager = ConnectionPoolManager()

def get_connection_pool_manager() -> ConnectionPoolManager:
    """Get the global connection pool manager instance"""
    return connection_pool_manager

def initialize_connection_pool_manager(app) -> ConnectionPoolManager:
    """Initialize the global connection pool manager"""
    connection_pool_manager.init_app(app)
    return connection_pool_manager
