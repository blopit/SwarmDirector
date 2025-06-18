# Horizontal Scalability Architecture Guide

<!-- Version: 1.0 • Last updated: 2025-06-18 • Author: SwarmDirector Team -->

This guide provides comprehensive instructions for implementing horizontal scalability patterns and strategies in SwarmDirector, including load balancing, distributed processing, and performance optimization.

## 📋 Table of Contents

1. [Scalability Overview](#scalability-overview)
2. [Load Balancing Strategies](#load-balancing-strategies)
3. [Database Scaling Patterns](#database-scaling-patterns)
4. [Distributed Processing](#distributed-processing)
5. [Caching Strategies](#caching-strategies)
6. [Resource Management](#resource-management)
7. [Performance Monitoring](#performance-monitoring)

## 🔄 Scalability Overview

### Horizontal Scaling Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    Load Balancer (HAProxy/NGINX)           │
└─────────────────────┬───────────────────────────────────────┘
                      │
         ┌────────────┼────────────┐
         ▼            ▼            ▼
   ┌─────────┐  ┌─────────┐  ┌─────────┐
   │ App Pod │  │ App Pod │  │ App Pod │
   │    #1   │  │    #2   │  │    #3   │
   └─────────┘  └─────────┘  └─────────┘
         │            │            │
         └────────────┼────────────┘
                      ▼
         ┌─────────────────────────────┐
         │     Database Cluster        │
         │  ┌─────────┐  ┌─────────┐   │
         │  │ Master  │  │ Replica │   │
         │  │   DB    │  │   DB    │   │
         │  └─────────┘  └─────────┘   │
         └─────────────────────────────┘
```

### Scaling Dimensions

1. **Application Layer**: Horizontal pod autoscaling based on CPU/memory/custom metrics
2. **Database Layer**: Read replicas, connection pooling, query optimization
3. **Caching Layer**: Distributed Redis cluster for session and data caching
4. **Agent Processing**: Parallel agent execution with queue-based task distribution
5. **File Storage**: Distributed object storage for attachments and artifacts

## ⚖️ Load Balancing Strategies

### Application Load Balancing

```yaml
# deploy/load-balancer/nginx-config.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: nginx-config
data:
  nginx.conf: |
    upstream swarmdirector_backend {
        least_conn;
        server swarmdirector-app-1:8000 max_fails=3 fail_timeout=30s;
        server swarmdirector-app-2:8000 max_fails=3 fail_timeout=30s;
        server swarmdirector-app-3:8000 max_fails=3 fail_timeout=30s;
    }
    
    server {
        listen 80;
        server_name swarmdirector.com;
        
        location /health {
            access_log off;
            return 200 "healthy\n";
        }
        
        location / {
            proxy_pass http://swarmdirector_backend;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
            
            # Connection settings
            proxy_connect_timeout 30s;
            proxy_send_timeout 30s;
            proxy_read_timeout 30s;
            
            # Session affinity for agent state
            proxy_cookie_path / "/; HTTPOnly; Secure";
        }
    }
```

### Kubernetes Horizontal Pod Autoscaler

```yaml
# deploy/autoscaling/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: swarmdirector-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: swarmdirector
  minReplicas: 3
  maxReplicas: 20
  metrics:
  - type: Resource
    resource:
      name: cpu
      target:
        type: Utilization
        averageUtilization: 70
  - type: Resource
    resource:
      name: memory
      target:
        type: Utilization
        averageUtilization: 80
  - type: Pods
    pods:
      metric:
        name: http_requests_per_second
      target:
        type: AverageValue
        averageValue: "100"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
      - type: Percent
        value: 100
        periodSeconds: 15
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
      - type: Percent
        value: 10
        periodSeconds: 60
```

## 💾 Database Scaling Patterns

### Read Replica Configuration

```python
# src/swarm_director/database/scaling.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from contextlib import contextmanager
import random

class DatabaseRouter:
    """Route database operations to appropriate instances"""
    
    def __init__(self, config):
        # Master database for writes
        self.master_engine = create_engine(
            config.MASTER_DATABASE_URL,
            pool_size=20,
            max_overflow=40,
            pool_timeout=60,
            pool_recycle=1800,
            pool_pre_ping=True
        )
        
        # Read replicas for read operations
        self.replica_engines = [
            create_engine(
                replica_url,
                pool_size=15,
                max_overflow=30,
                pool_timeout=60,
                pool_recycle=1800,
                pool_pre_ping=True
            )
            for replica_url in config.REPLICA_DATABASE_URLS
        ]
        
        self.MasterSession = sessionmaker(bind=self.master_engine)
        self.ReplicaSessions = [
            sessionmaker(bind=engine) for engine in self.replica_engines
        ]
    
    @contextmanager
    def write_session(self):
        """Session for write operations (master)"""
        session = self.MasterSession()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    
    @contextmanager
    def read_session(self):
        """Session for read operations (replica)"""
        # Round-robin or random selection of read replica
        session_class = random.choice(self.ReplicaSessions)
        session = session_class()
        try:
            yield session
        finally:
            session.close()

# Usage example
router = DatabaseRouter(config)

# Write operations
with router.write_session() as session:
    agent = Agent(name="New Agent", type="worker")
    session.add(agent)

# Read operations
with router.read_session() as session:
    agents = session.query(Agent).filter(Agent.status == "active").all()
```

### Database Connection Pooling Optimization

```python
# src/swarm_director/config/database.py
class DatabaseConfig:
    """Environment-specific database configuration"""
    
    @staticmethod
    def get_engine_options(environment: str) -> dict:
        """Get optimized engine options per environment"""
        
        base_options = {
            'pool_pre_ping': True,
            'pool_recycle': 1800,  # 30 minutes
            'echo': False
        }
        
        if environment == 'development':
            return {
                **base_options,
                'pool_size': 5,
                'max_overflow': 10,
                'pool_timeout': 20,
                'echo': True  # SQL logging in development
            }
        
        elif environment == 'staging':
            return {
                **base_options,
                'pool_size': 10,
                'max_overflow': 20,
                'pool_timeout': 30
            }
        
        elif environment == 'production':
            return {
                **base_options,
                'pool_size': 20,
                'max_overflow': 40,
                'pool_timeout': 60,
                'pool_recycle': 900,  # More frequent recycling in production
            }
        
        return base_options
```

## 🔄 Distributed Processing

### Agent Task Queue Implementation

```python
# src/swarm_director/queue/distributed_queue.py
import redis
import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional

class DistributedTaskQueue:
    """Distributed task queue for agent processing"""
    
    def __init__(self, redis_url: str):
        self.redis_client = redis.from_url(redis_url)
        self.task_queue = "agent_tasks"
        self.processing_queue = "processing_tasks"
        self.completed_queue = "completed_tasks"
        self.failed_queue = "failed_tasks"
    
    def enqueue_task(self, task_data: Dict[str, Any], priority: int = 5) -> str:
        """Add task to distributed queue with priority"""
        task_id = str(uuid.uuid4())
        
        task = {
            'id': task_id,
            'data': task_data,
            'priority': priority,
            'created_at': datetime.utcnow().isoformat(),
            'attempts': 0,
            'max_attempts': 3
        }
        
        # Use sorted set for priority queue
        self.redis_client.zadd(
            self.task_queue, 
            {json.dumps(task): priority}
        )
        
        return task_id
    
    def dequeue_task(self, worker_id: str) -> Optional[Dict[str, Any]]:
        """Get next task for processing"""
        # Get highest priority task
        task_data = self.redis_client.zpopmax(self.task_queue, 1)
        
        if not task_data:
            return None
        
        task_json, priority = task_data[0]
        task = json.loads(task_json)
        
        # Move to processing queue with worker assignment
        task['worker_id'] = worker_id
        task['processing_started'] = datetime.utcnow().isoformat()
        
        self.redis_client.hset(
            self.processing_queue, 
            task['id'], 
            json.dumps(task)
        )
        
        return task
    
    def complete_task(self, task_id: str, result: Dict[str, Any]):
        """Mark task as completed"""
        task_json = self.redis_client.hget(self.processing_queue, task_id)
        
        if task_json:
            task = json.loads(task_json)
            task['result'] = result
            task['completed_at'] = datetime.utcnow().isoformat()
            
            # Move to completed queue
            self.redis_client.hset(
                self.completed_queue, 
                task_id, 
                json.dumps(task)
            )
            
            # Remove from processing
            self.redis_client.hdel(self.processing_queue, task_id)
    
    def fail_task(self, task_id: str, error: str):
        """Handle task failure with retry logic"""
        task_json = self.redis_client.hget(self.processing_queue, task_id)
        
        if task_json:
            task = json.loads(task_json)
            task['attempts'] += 1
            task['last_error'] = error
            task['failed_at'] = datetime.utcnow().isoformat()
            
            if task['attempts'] < task['max_attempts']:
                # Retry with exponential backoff
                delay = 2 ** task['attempts']  # 2, 4, 8 seconds
                retry_time = datetime.utcnow() + timedelta(seconds=delay)
                
                # Re-queue for retry
                self.redis_client.zadd(
                    self.task_queue, 
                    {json.dumps(task): task['priority']}
                )
            else:
                # Move to failed queue
                self.redis_client.hset(
                    self.failed_queue, 
                    task_id, 
                    json.dumps(task)
                )
            
            # Remove from processing
            self.redis_client.hdel(self.processing_queue, task_id)
```

### Parallel Agent Execution

```python
# src/swarm_director/agents/parallel_executor.py
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Any
import logging

class ParallelAgentExecutor:
    """Execute multiple agents in parallel with resource management"""
    
    def __init__(self, max_workers: int = 10):
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.logger = logging.getLogger(__name__)
    
    async def execute_agents_batch(self, 
                                 agent_tasks: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute multiple agent tasks in parallel"""
        
        # Split into batches to prevent resource exhaustion
        batch_size = min(self.max_workers, len(agent_tasks))
        results = []
        
        for i in range(0, len(agent_tasks), batch_size):
            batch = agent_tasks[i:i + batch_size]
            batch_results = await self._execute_batch(batch)
            results.extend(batch_results)
        
        return results
    
    async def _execute_batch(self, batch: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Execute a single batch of tasks"""
        loop = asyncio.get_event_loop()
        
        # Submit tasks to thread pool
        futures = [
            loop.run_in_executor(
                self.executor, 
                self._execute_single_agent, 
                task
            )
            for task in batch
        ]
        
        # Wait for completion with timeout
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*futures, return_exceptions=True), 
                timeout=300  # 5 minutes
            )
            return results
        except asyncio.TimeoutError:
            self.logger.error("Batch execution timed out")
            return [{"error": "timeout"} for _ in batch]
    
    def _execute_single_agent(self, task: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a single agent task"""
        try:
            agent_type = task.get('agent_type')
            agent_data = task.get('data', {})
            
            # Dynamic agent instantiation
            agent_class = self._get_agent_class(agent_type)
            agent = agent_class()
            
            result = agent.process_task(agent_data)
            
            return {
                'task_id': task.get('id'),
                'status': 'success',
                'result': result,
                'agent_type': agent_type
            }
            
        except Exception as e:
            self.logger.error(f"Agent execution failed: {str(e)}")
            return {
                'task_id': task.get('id'),
                'status': 'error',
                'error': str(e),
                'agent_type': task.get('agent_type')
            }
    
    def _get_agent_class(self, agent_type: str):
        """Get agent class by type"""
        from src.swarm_director.agents import (
            EmailAgent, 
            QualityScorer, 
            DraftReviewAgent
        )
        
        agent_map = {
            'email': EmailAgent,
            'quality': QualityScorer,
            'review': DraftReviewAgent
        }
        
        return agent_map.get(agent_type, EmailAgent)
```

## 🗄️ Caching Strategies

### Distributed Redis Caching

```python
# src/swarm_director/cache/distributed_cache.py
import redis
import json
import pickle
from typing import Any, Optional, Union
from datetime import timedelta

class DistributedCache:
    """Distributed caching with Redis"""
    
    def __init__(self, redis_cluster_urls: List[str]):
        self.cluster = redis.RedisCluster(
            startup_nodes=[
                {"host": url.split(':')[0], "port": int(url.split(':')[1])}
                for url in redis_cluster_urls
            ],
            decode_responses=False,
            skip_full_coverage_check=True
        )
    
    def set(self, key: str, value: Any, ttl: Optional[int] = None) -> bool:
        """Set cache value with optional TTL"""
        try:
            serialized_value = pickle.dumps(value)
            
            if ttl:
                return self.cluster.setex(key, ttl, serialized_value)
            else:
                return self.cluster.set(key, serialized_value)
        except Exception as e:
            logging.error(f"Cache set failed: {e}")
            return False
    
    def get(self, key: str) -> Optional[Any]:
        """Get cache value"""
        try:
            value = self.cluster.get(key)
            if value:
                return pickle.loads(value)
            return None
        except Exception as e:
            logging.error(f"Cache get failed: {e}")
            return None
    
    def cache_agent_result(self, agent_id: str, task_hash: str, result: Any, ttl: int = 3600):
        """Cache agent execution result"""
        cache_key = f"agent_result:{agent_id}:{task_hash}"
        return self.set(cache_key, result, ttl)
    
    def get_cached_agent_result(self, agent_id: str, task_hash: str) -> Optional[Any]:
        """Get cached agent result"""
        cache_key = f"agent_result:{agent_id}:{task_hash}"
        return self.get(cache_key)

# Cache decorator for agent methods
def cache_result(ttl: int = 3600):
    """Decorator to cache agent method results"""
    def decorator(func):
        def wrapper(self, *args, **kwargs):
            # Generate cache key from method name and arguments
            import hashlib
            cache_key = f"{self.__class__.__name__}:{func.__name__}:{hashlib.md5(str(args).encode()).hexdigest()}"
            
            # Try to get from cache
            cached_result = self.cache.get(cache_key)
            if cached_result:
                return cached_result
            
            # Execute function and cache result
            result = func(self, *args, **kwargs)
            self.cache.set(cache_key, result, ttl)
            
            return result
        return wrapper
    return decorator
```

## 📊 Resource Management

### Resource Quotas and Limits

```yaml
# deploy/resource-management/resource-quota.yaml
apiVersion: v1
kind: ResourceQuota
metadata:
  name: swarmdirector-quota
  namespace: swarmdirector
spec:
  hard:
    requests.cpu: "20"
    requests.memory: 40Gi
    limits.cpu: "40"
    limits.memory: 80Gi
    persistentvolumeclaims: "10"
    pods: "50"
    services: "10"
---
apiVersion: v1
kind: LimitRange
metadata:
  name: swarmdirector-limits
  namespace: swarmdirector
spec:
  limits:
  - default:
      cpu: "1"
      memory: "2Gi"
    defaultRequest:
      cpu: "500m"
      memory: "1Gi"
    type: Container
  - max:
      cpu: "4"
      memory: "8Gi"
    min:
      cpu: "100m"
      memory: "128Mi"
    type: Container
```

### Dynamic Resource Allocation

```python
# src/swarm_director/scaling/resource_manager.py
import psutil
import logging
from typing import Dict, Any

class ResourceManager:
    """Manage system resources and scaling decisions"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.cpu_threshold = 70  # CPU utilization threshold
        self.memory_threshold = 80  # Memory utilization threshold
    
    def get_system_metrics(self) -> Dict[str, Any]:
        """Get current system resource utilization"""
        return {
            'cpu_percent': psutil.cpu_percent(interval=1),
            'memory_percent': psutil.virtual_memory().percent,
            'disk_percent': psutil.disk_usage('/').percent,
            'load_average': psutil.getloadavg(),
            'active_connections': len(psutil.net_connections()),
            'active_processes': len(psutil.pids())
        }
    
    def should_scale_up(self) -> bool:
        """Determine if system should scale up"""
        metrics = self.get_system_metrics()
        
        return (
            metrics['cpu_percent'] > self.cpu_threshold or
            metrics['memory_percent'] > self.memory_threshold
        )
    
    def should_scale_down(self) -> bool:
        """Determine if system can scale down"""
        metrics = self.get_system_metrics()
        
        return (
            metrics['cpu_percent'] < (self.cpu_threshold * 0.5) and
            metrics['memory_percent'] < (self.memory_threshold * 0.5)
        )
    
    def get_optimal_worker_count(self) -> int:
        """Calculate optimal number of workers"""
        cpu_count = psutil.cpu_count()
        memory_gb = psutil.virtual_memory().total / (1024**3)
        
        # Conservative approach: 1 worker per 2 cores or 4GB RAM
        cpu_workers = max(1, cpu_count // 2)
        memory_workers = max(1, int(memory_gb // 4))
        
        return min(cpu_workers, memory_workers)
```

## 📈 Performance Monitoring

### Metrics Collection

```python
# src/swarm_director/monitoring/metrics.py
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry
import time
from functools import wraps

class MetricsCollector:
    """Collect application metrics for monitoring"""
    
    def __init__(self):
        self.registry = CollectorRegistry()
        
        # Request metrics
        self.request_count = Counter(
            'http_requests_total',
            'Total HTTP requests',
            ['method', 'endpoint', 'status'],
            registry=self.registry
        )
        
        self.request_duration = Histogram(
            'http_request_duration_seconds',
            'HTTP request duration',
            ['method', 'endpoint'],
            registry=self.registry
        )
        
        # Agent metrics
        self.agent_task_count = Counter(
            'agent_tasks_total',
            'Total agent tasks',
            ['agent_type', 'status'],
            registry=self.registry
        )
        
        self.agent_processing_time = Histogram(
            'agent_processing_duration_seconds',
            'Agent task processing duration',
            ['agent_type'],
            registry=self.registry
        )
        
        # System metrics
        self.active_connections = Gauge(
            'active_database_connections',
            'Active database connections',
            registry=self.registry
        )
        
        self.queue_size = Gauge(
            'task_queue_size',
            'Size of task queue',
            ['queue_type'],
            registry=self.registry
        )

def monitor_endpoint(metrics: MetricsCollector):
    """Decorator to monitor HTTP endpoints"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                status = getattr(result, 'status_code', 200)
                metrics.request_count.labels(
                    method='GET', 
                    endpoint=func.__name__, 
                    status=status
                ).inc()
                
                return result
                
            except Exception as e:
                metrics.request_count.labels(
                    method='GET', 
                    endpoint=func.__name__, 
                    status=500
                ).inc()
                raise
                
            finally:
                duration = time.time() - start_time
                metrics.request_duration.labels(
                    method='GET', 
                    endpoint=func.__name__
                ).observe(duration)
        
        return wrapper
    return decorator
```

---

*This guide provides comprehensive horizontal scalability patterns for SwarmDirector.* 