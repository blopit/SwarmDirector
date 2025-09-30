# Memory State Change Tracking

## Subtask Metadata
```yaml
subtask_id: "subtask_002"
parent_task: "task_019"
title: "Memory State Change Tracking"
type: "backend_development"
priority: "high"
estimated_effort: "2-3 days"
complexity: "medium"
dependencies:
  - subtask_001
  - existing_agent_system
  - workflow_context_system
assignee: "backend_developer"
status: "blocked"
```

## Objective

Implement automatic tracking of agent memory state changes with event-driven monitoring, change detection, and historical analysis capabilities for debugging and optimization purposes.

## Technical Specifications

### Memory Change Detection System

#### Change Types to Track
```python
class MemoryChangeType(enum.Enum):
    CONVERSATION_MESSAGE = "conversation_message"
    CONVERSATION_START = "conversation_start"
    CONVERSATION_END = "conversation_end"
    WORKFLOW_CONTEXT_UPDATE = "workflow_context_update"
    AGENT_CONFIG_CHANGE = "agent_config_change"
    MEMORY_RESET = "memory_reset"
    MEMORY_CLEANUP = "memory_cleanup"
    SYSTEM_MESSAGE_UPDATE = "system_message_update"
```

#### Memory Change Event Model
```python
class MemoryChangeEvent(BaseModel):
    """Model for tracking memory state changes"""
    __tablename__ = 'memory_change_events'
    
    agent_id = db.Column(db.Integer, db.ForeignKey('agents.id'), nullable=False)
    change_type = db.Column(Enum(MemoryChangeType), nullable=False)
    
    # Change details
    before_state_hash = db.Column(db.String(64))  # SHA256 hash of previous state
    after_state_hash = db.Column(db.String(64))   # SHA256 hash of new state
    change_delta = db.Column(db.JSON)             # Specific changes made
    
    # Memory metrics
    memory_size_before_mb = db.Column(db.Float)
    memory_size_after_mb = db.Column(db.Float)
    memory_delta_mb = db.Column(db.Float)
    
    # Context information
    trigger_source = db.Column(db.String(100))    # What triggered the change
    conversation_id = db.Column(db.Integer, db.ForeignKey('conversations.id'))
    task_id = db.Column(db.Integer, db.ForeignKey('tasks.id'))
    workflow_id = db.Column(db.String(100))
    
    # Performance metrics
    processing_time_ms = db.Column(db.Float)
    
    # Metadata
    metadata = db.Column(db.JSON)
```

### Core Implementation Classes

#### Memory State Monitor
```python
class MemoryStateMonitor:
    """Monitors and tracks agent memory state changes"""
    
    def __init__(self):
        self._active_monitors: Dict[int, AgentMemoryState] = {}
        self._change_handlers: List[Callable] = []
        self._lock = threading.RLock()
    
    def start_monitoring(self, agent_id: int) -> None:
        """Start monitoring memory changes for an agent"""
        
    def stop_monitoring(self, agent_id: int) -> None:
        """Stop monitoring memory changes for an agent"""
        
    def capture_memory_state(self, agent_id: int) -> AgentMemoryState:
        """Capture current memory state for an agent"""
        
    def detect_changes(self, agent_id: int, 
                      old_state: AgentMemoryState,
                      new_state: AgentMemoryState) -> List[MemoryChange]:
        """Detect specific changes between memory states"""
        
    def record_change_event(self, agent_id: int, 
                           change: MemoryChange) -> MemoryChangeEvent:
        """Record a memory change event to database"""

class AgentMemoryState:
    """Represents a snapshot of agent memory state"""
    
    def __init__(self, agent_id: int):
        self.agent_id = agent_id
        self.timestamp = datetime.utcnow()
        self.conversation_memory: Dict[str, Any] = {}
        self.workflow_context: Dict[str, Any] = {}
        self.agent_config: Dict[str, Any] = {}
        self.system_message: str = ""
        
    def calculate_hash(self) -> str:
        """Calculate SHA256 hash of memory state"""
        
    def calculate_size_mb(self) -> float:
        """Calculate memory size in MB"""
        
    def compare_with(self, other: 'AgentMemoryState') -> List[MemoryChange]:
        """Compare with another memory state and return changes"""

class MemoryChange:
    """Represents a specific memory change"""
    
    def __init__(self, change_type: MemoryChangeType,
                 path: str, old_value: Any, new_value: Any):
        self.change_type = change_type
        self.path = path  # JSON path to changed field
        self.old_value = old_value
        self.new_value = new_value
        self.size_delta_bytes = self._calculate_size_delta()
```

### Event-Driven Integration

#### Memory Change Hooks
```python
class MemoryChangeHooks:
    """Hooks into existing systems to detect memory changes"""
    
    @staticmethod
    def hook_conversation_system():
        """Add hooks to conversation message handling"""
        # Patch Conversation.add_message()
        # Patch Message.save()
        
    @staticmethod
    def hook_workflow_context():
        """Add hooks to workflow context updates"""
        # Patch WorkflowContext.set()
        # Patch WorkflowContext.update()
        
    @staticmethod
    def hook_agent_config():
        """Add hooks to agent configuration changes"""
        # Patch Agent.save()
        # Patch Agent.update_config()

# Decorator for automatic memory tracking
def track_memory_changes(agent_id_param: str = 'agent_id'):
    """Decorator to automatically track memory changes"""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Extract agent_id from parameters
            agent_id = kwargs.get(agent_id_param) or args[0]
            
            # Capture before state
            monitor = get_memory_monitor()
            before_state = monitor.capture_memory_state(agent_id)
            
            try:
                # Execute function
                result = func(*args, **kwargs)
                
                # Capture after state and detect changes
                after_state = monitor.capture_memory_state(agent_id)
                changes = monitor.detect_changes(agent_id, before_state, after_state)
                
                # Record changes
                for change in changes:
                    monitor.record_change_event(agent_id, change)
                
                return result
                
            except Exception as e:
                # Record error in memory tracking
                logger.error(f"Memory tracking error for agent {agent_id}: {e}")
                raise
                
        return wrapper
    return decorator
```

## Implementation Steps

### Step 1: Database Schema and Models (Day 1)
1. Create `MemoryChangeEvent` model and migration
2. Add indexes for efficient querying
3. Create database constraints and relationships
4. Test model operations

### Step 2: Core Monitoring Classes (Day 2)
1. Implement `MemoryStateMonitor` class
2. Implement `AgentMemoryState` class
3. Implement `MemoryChange` detection logic
4. Add memory state hashing and comparison

### Step 3: Event-Driven Integration (Day 3)
1. Create memory change hooks for existing systems
2. Implement `@track_memory_changes` decorator
3. Integrate with conversation system
4. Integrate with workflow context system
5. Add configuration change tracking

## Integration Points

### Conversation System Integration
```python
# In src/swarm_director/models/conversation.py
class Message(BaseModel):
    @track_memory_changes(agent_id_param='sender_agent_id')
    def save(self):
        """Enhanced save with memory tracking"""
        super().save()
        
class Conversation(BaseModel):
    @track_memory_changes(agent_id_param='initiator_agent_id')
    def add_message(self, content, message_type, sender_agent_id=None, message_metadata=None):
        """Enhanced add_message with memory tracking"""
        # Existing implementation with memory tracking
```

### Workflow Context Integration
```python
# In src/swarm_director/workflows/workflow_context.py
class WorkflowContext:
    @track_memory_changes(agent_id_param='agent_name')
    def set(self, key: str, value: Any, scope: ContextScope = ContextScope.WORKFLOW, 
            agent_name: str = None, **kwargs) -> bool:
        """Enhanced set with memory tracking"""
        # Existing implementation with memory tracking
```

### Agent Configuration Integration
```python
# In src/swarm_director/models/agent.py
class Agent(BaseModel):
    @track_memory_changes(agent_id_param='id')
    def save(self):
        """Enhanced save with memory tracking"""
        super().save()
```

## Configuration and Settings

### Memory Tracking Configuration
```python
class MemoryTrackingConfig:
    """Configuration for memory tracking system"""
    
    # Tracking settings
    ENABLE_MEMORY_TRACKING = True
    TRACK_CONVERSATION_CHANGES = True
    TRACK_WORKFLOW_CONTEXT = True
    TRACK_AGENT_CONFIG = True
    
    # Performance settings
    MAX_MEMORY_STATES_IN_MEMORY = 1000
    MEMORY_STATE_CLEANUP_INTERVAL = 3600  # seconds
    BATCH_SIZE_FOR_CHANGE_EVENTS = 100
    
    # Storage settings
    MEMORY_CHANGE_RETENTION_DAYS = 30
    COMPRESS_OLD_MEMORY_STATES = True
    MAX_CHANGE_DELTA_SIZE_KB = 100
```

### Environment Variables
```bash
# Memory tracking configuration
MEMORY_TRACKING_ENABLED=true
MEMORY_TRACKING_RETENTION_DAYS=30
MEMORY_TRACKING_BATCH_SIZE=100
MEMORY_STATE_CLEANUP_INTERVAL=3600
MEMORY_TRACKING_COMPRESSION=true
```

## Performance Considerations

### Optimization Strategies
1. **Lazy State Capture**: Only capture full state when changes detected
2. **Batch Processing**: Process change events in batches
3. **Compression**: Compress old memory states
4. **Selective Tracking**: Allow disabling tracking for specific agents
5. **Async Processing**: Process change events asynchronously

### Memory Usage Management
```python
class MemoryTrackingOptimizer:
    """Optimizes memory tracking performance"""
    
    def cleanup_old_states(self, retention_days: int = 30) -> int:
        """Clean up old memory states"""
        
    def compress_memory_states(self, older_than_days: int = 7) -> int:
        """Compress old memory states"""
        
    def optimize_change_detection(self, agent_id: int) -> None:
        """Optimize change detection for specific agent"""
```

## Testing Requirements

### Unit Tests
```python
class TestMemoryStateMonitor:
    def test_memory_state_capture(self):
        """Test memory state capture accuracy"""
        
    def test_change_detection(self):
        """Test change detection between states"""
        
    def test_memory_size_calculation(self):
        """Test memory size calculations"""
        
    def test_state_hashing(self):
        """Test memory state hashing consistency"""

class TestMemoryChangeTracking:
    def test_conversation_change_tracking(self):
        """Test conversation memory change tracking"""
        
    def test_workflow_context_tracking(self):
        """Test workflow context change tracking"""
        
    def test_agent_config_tracking(self):
        """Test agent configuration change tracking"""
```

### Integration Tests
- Test memory tracking with real agent operations
- Verify change detection accuracy
- Test performance with high-frequency changes
- Validate memory tracking overhead

### Performance Tests
- Memory tracking overhead < 5% of operation time
- Change detection for large memory states
- Batch processing performance
- Memory cleanup efficiency

## Monitoring and Alerting

### Key Metrics
- Memory change event frequency
- Memory tracking processing time
- Memory state size growth rates
- Change detection accuracy
- System overhead from tracking

### Alerts
- High memory change frequency (> 1000 events/hour per agent)
- Large memory state sizes (> 100MB per agent)
- Memory tracking processing delays
- Failed change event recordings

## Success Criteria

### Functional Requirements
- [ ] Automatic detection of all memory state changes
- [ ] Accurate change delta calculation
- [ ] Historical memory change analysis
- [ ] Integration with existing agent systems
- [ ] Configurable tracking granularity

### Performance Requirements
- [ ] Memory tracking overhead < 5% of operation time
- [ ] Change detection processing < 100ms
- [ ] Support for 100+ agents with active tracking
- [ ] Efficient storage of change history

### Quality Requirements
- [ ] 95%+ unit test coverage
- [ ] Integration tests for all change types
- [ ] Performance benchmarks established
- [ ] Comprehensive error handling

## Error Handling

### Common Error Scenarios
- Memory state capture failures
- Change detection errors
- Database recording failures
- Hook integration issues
- Performance degradation

### Error Recovery Strategies
- Graceful degradation when tracking fails
- Retry mechanisms for failed recordings
- Fallback to basic logging when hooks fail
- Circuit breaker for performance issues

## Related Files
- `src/swarm_director/models/memory_change_event.py` - New model
- `src/swarm_director/services/memory_monitor.py` - New service
- `src/swarm_director/utils/memory_tracking.py` - Utilities and decorators
- `database/migrations/` - Schema updates
