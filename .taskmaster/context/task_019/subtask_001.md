# Memory Inspection API Endpoints

## Subtask Metadata
```yaml
subtask_id: "subtask_001"
parent_task: "task_019"
title: "Memory Inspection API Endpoints"
type: "backend_development"
priority: "high"
estimated_effort: "3-4 days"
complexity: "medium"
dependencies:
  - existing_agent_models
  - conversation_models
  - workflow_context_system
assignee: "backend_developer"
status: "ready"
```

## Objective

Implement comprehensive REST API endpoints for inspecting and managing agent memory states, including conversation history, workflow context, and agent configuration memory.

## Technical Specifications

### New API Endpoints

#### 1. Agent Memory Inspection
```python
# GET /api/agents/{agent_id}/memory
# Response: Complete agent memory state
{
    "agent_id": 123,
    "memory_state": {
        "conversation_memory": {...},
        "workflow_context": {...},
        "configuration": {...},
        "activity_history": [...]
    },
    "memory_usage": {
        "total_size_mb": 15.2,
        "conversation_size_mb": 8.1,
        "context_size_mb": 4.3,
        "config_size_mb": 2.8
    },
    "last_updated": "2025-06-19T10:30:00Z"
}
```

#### 2. Memory History Tracking
```python
# GET /api/agents/{agent_id}/memory/history
# Query params: start_time, end_time, limit
{
    "agent_id": 123,
    "history": [
        {
            "timestamp": "2025-06-19T10:30:00Z",
            "change_type": "conversation_update",
            "memory_delta": {...},
            "size_change_mb": 0.5,
            "trigger": "message_received"
        }
    ],
    "total_changes": 45,
    "time_range": {...}
}
```

#### 3. Memory Management Operations
```python
# POST /api/agents/{agent_id}/memory/reset
# DELETE /api/agents/{agent_id}/memory/conversations/{conv_id}
# PUT /api/agents/{agent_id}/memory/config
```

### Implementation Details

#### Database Schema Enhancements
```sql
-- New table for memory state tracking
CREATE TABLE agent_memory_snapshots (
    id SERIAL PRIMARY KEY,
    agent_id INTEGER REFERENCES agents(id),
    snapshot_type VARCHAR(50) NOT NULL,
    memory_data JSONB NOT NULL,
    memory_size_bytes INTEGER,
    created_at TIMESTAMP DEFAULT NOW(),
    metadata JSONB
);

-- Index for efficient querying
CREATE INDEX idx_memory_snapshots_agent_time 
ON agent_memory_snapshots(agent_id, created_at);
```

#### Core Implementation Classes
```python
class AgentMemoryInspector:
    """Service class for agent memory inspection operations"""
    
    def get_agent_memory_state(self, agent_id: int) -> Dict[str, Any]:
        """Get complete memory state for an agent"""
        
    def get_memory_history(self, agent_id: int, 
                          start_time: datetime = None,
                          end_time: datetime = None,
                          limit: int = 100) -> List[Dict[str, Any]]:
        """Get memory change history for an agent"""
        
    def calculate_memory_usage(self, agent_id: int) -> Dict[str, float]:
        """Calculate memory usage statistics"""
        
    def reset_agent_memory(self, agent_id: int, 
                          memory_types: List[str] = None) -> bool:
        """Reset specific types of agent memory"""

class MemoryStateTracker:
    """Tracks and logs memory state changes"""
    
    def track_memory_change(self, agent_id: int, 
                           change_type: str,
                           old_state: Dict[str, Any],
                           new_state: Dict[str, Any]) -> None:
        """Track a memory state change"""
        
    def create_memory_snapshot(self, agent_id: int) -> str:
        """Create a snapshot of current memory state"""
```

### API Route Implementations

#### File: `src/swarm_director/api/memory_routes.py`
```python
from flask import Blueprint, request, jsonify
from ..services.memory_inspector import AgentMemoryInspector
from ..utils.auth import require_auth
from ..utils.validation import validate_agent_access

memory_bp = Blueprint('memory', __name__, url_prefix='/api/memory')

@memory_bp.route('/agents/<int:agent_id>/memory', methods=['GET'])
@require_auth
@validate_agent_access
def get_agent_memory(agent_id: int):
    """Get complete agent memory state"""
    inspector = AgentMemoryInspector()
    memory_state = inspector.get_agent_memory_state(agent_id)
    return jsonify({
        'success': True,
        'data': memory_state
    })

@memory_bp.route('/agents/<int:agent_id>/memory/history', methods=['GET'])
@require_auth
@validate_agent_access
def get_memory_history(agent_id: int):
    """Get agent memory change history"""
    # Implementation details...
```

## Implementation Steps

### Step 1: Database Schema Updates (Day 1)
1. Create migration for `agent_memory_snapshots` table
2. Add indexes for efficient querying
3. Update existing models to support memory tracking
4. Test migration on development database

### Step 2: Core Service Classes (Day 2)
1. Implement `AgentMemoryInspector` class
2. Implement `MemoryStateTracker` class
3. Add memory calculation utilities
4. Create unit tests for service classes

### Step 3: API Route Implementation (Day 3)
1. Create `memory_routes.py` blueprint
2. Implement all memory inspection endpoints
3. Add request validation and error handling
4. Integrate with existing authentication system

### Step 4: Testing and Documentation (Day 4)
1. Write comprehensive unit tests
2. Create integration tests for API endpoints
3. Add API documentation with examples
4. Performance testing for memory operations

## Testing Requirements

### Unit Tests
```python
class TestAgentMemoryInspector:
    def test_get_agent_memory_state(self):
        """Test memory state retrieval"""
        
    def test_memory_history_filtering(self):
        """Test memory history with time filters"""
        
    def test_memory_usage_calculation(self):
        """Test memory usage statistics"""
        
    def test_memory_reset_operations(self):
        """Test memory reset functionality"""
```

### Integration Tests
- Test API endpoints with real agent data
- Verify memory tracking accuracy
- Test concurrent memory operations
- Validate memory size calculations

### Performance Tests
- Memory inspection response time < 500ms
- History queries with large datasets
- Concurrent memory operations
- Memory usage of tracking system itself

## Security Considerations

### Access Control
- Require authentication for all memory endpoints
- Validate agent access permissions
- Log all memory inspection activities
- Rate limiting for memory operations

### Data Privacy
- Sanitize sensitive data in memory exports
- Implement data retention policies
- Secure memory snapshot storage
- Audit trail for memory modifications

## Error Handling

### Common Error Scenarios
- Agent not found (404)
- Insufficient permissions (403)
- Memory operation failures (500)
- Invalid time range parameters (400)
- Memory size limits exceeded (413)

### Error Response Format
```python
{
    "success": false,
    "error": {
        "code": "AGENT_NOT_FOUND",
        "message": "Agent with ID 123 not found",
        "details": {...}
    }
}
```

## Configuration

### Environment Variables
```bash
# Memory debugging configuration
MEMORY_DEBUG_ENABLED=true
MEMORY_SNAPSHOT_RETENTION_DAYS=30
MEMORY_HISTORY_MAX_ENTRIES=1000
MEMORY_EXPORT_MAX_SIZE_MB=100
MEMORY_TRACKING_INTERVAL_SECONDS=60
```

### Feature Flags
- `enable_memory_debugging`: Master switch for memory debugging
- `enable_memory_tracking`: Enable automatic memory state tracking
- `enable_memory_snapshots`: Enable memory snapshot creation
- `enable_memory_reset`: Allow memory reset operations

## Success Criteria

### Functional Requirements
- [ ] All memory inspection endpoints implemented and tested
- [ ] Memory history tracking with configurable retention
- [ ] Memory reset operations with proper validation
- [ ] Memory usage calculations and statistics
- [ ] Comprehensive error handling and logging

### Performance Requirements
- [ ] Memory inspection API response time < 500ms
- [ ] Support for agents with 100+ conversations
- [ ] Efficient memory history queries
- [ ] Minimal performance impact on existing operations

### Quality Requirements
- [ ] 95%+ unit test coverage
- [ ] Integration tests for all endpoints
- [ ] Comprehensive API documentation
- [ ] Security validation and access control

## Related Files
- `src/swarm_director/models/agent.py` - Agent model enhancements
- `src/swarm_director/models/conversation.py` - Conversation memory tracking
- `src/swarm_director/workflows/workflow_context.py` - Context memory access
- `src/swarm_director/services/memory_inspector.py` - New service class
- `database/migrations/` - Database schema updates
