"""
Workflow Context Management
Provides shared context and data exchange between agents in a workflow
"""

import threading
from typing import Dict, Any, Optional, List
from datetime import datetime
from dataclasses import dataclass, field
from enum import Enum

class ContextScope(Enum):
    """Scope levels for context data"""
    GLOBAL = "global"          # Available to all workflows
    WORKFLOW = "workflow"      # Available to all agents in workflow
    AGENT = "agent"           # Available only to specific agent
    TASK = "task"             # Available only for specific task

@dataclass
class ContextEntry:
    """Individual context entry with metadata"""
    key: str
    value: Any
    scope: ContextScope
    owner_agent: Optional[str] = None
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.utcnow)
    expires_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def is_expired(self) -> bool:
        """Check if this context entry has expired"""
        if self.expires_at is None:
            return False
        return datetime.utcnow() > self.expires_at
    
    def can_access(self, agent_name: str, workflow_id: str, task_id: str = None) -> bool:
        """Check if an agent can access this context entry"""
        if self.is_expired():
            return False
            
        if self.scope == ContextScope.GLOBAL:
            return True
        elif self.scope == ContextScope.WORKFLOW:
            return self.workflow_id == workflow_id
        elif self.scope == ContextScope.AGENT:
            return self.owner_agent == agent_name
        elif self.scope == ContextScope.TASK:
            return self.task_id == task_id
        
        return False

class WorkflowContext:
    """
    Manages shared context and data exchange between agents in workflows
    Thread-safe implementation for concurrent access
    """
    
    def __init__(self, workflow_id: str):
        self.workflow_id = workflow_id
        self._context: Dict[str, ContextEntry] = {}
        self._lock = threading.RLock()
        self._global_context: Dict[str, ContextEntry] = {}
        
    def set(self, key: str, value: Any, scope: ContextScope = ContextScope.WORKFLOW, 
            agent_name: str = None, task_id: str = None, 
            expires_at: datetime = None, metadata: Dict[str, Any] = None) -> bool:
        """Set a context value with specified scope and metadata"""
        with self._lock:
            entry = ContextEntry(
                key=key,
                value=value,
                scope=scope,
                owner_agent=agent_name,
                workflow_id=self.workflow_id,
                task_id=task_id,
                expires_at=expires_at,
                metadata=metadata or {}
            )
            
            if scope == ContextScope.GLOBAL:
                self._global_context[key] = entry
            else:
                self._context[key] = entry
            
            return True
    
    def get(self, key: str, agent_name: str, task_id: str = None, 
            default: Any = None) -> Any:
        """Get a context value if the agent has access"""
        with self._lock:
            # Check workflow/agent/task context first
            if key in self._context:
                entry = self._context[key]
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    return entry.value
            
            # Check global context
            if key in self._global_context:
                entry = self._global_context[key]
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    return entry.value
            
            return default
    
    def get_all_for_agent(self, agent_name: str, task_id: str = None) -> Dict[str, Any]:
        """Get all context entries accessible to an agent"""
        result = {}
        
        with self._lock:
            # Check workflow/agent/task context
            for key, entry in self._context.items():
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    result[key] = entry.value
            
            # Check global context
            for key, entry in self._global_context.items():
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    result[key] = entry.value
        
        return result
    
    def update(self, key: str, value: Any, agent_name: str, task_id: str = None) -> bool:
        """Update an existing context value if agent has permission"""
        with self._lock:
            # Check workflow context
            if key in self._context:
                entry = self._context[key]
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    entry.value = value
                    return True
            
            # Check global context
            if key in self._global_context:
                entry = self._global_context[key]
                if entry.can_access(agent_name, self.workflow_id, task_id):
                    entry.value = value
                    return True
            
            return False
    
    def delete(self, key: str, agent_name: str, task_id: str = None) -> bool:
        """Delete a context entry if agent has permission"""
        with self._lock:
            # Check workflow context
            if key in self._context:
                entry = self._context[key]
                if (entry.scope == ContextScope.AGENT and entry.owner_agent == agent_name) or \
                   (entry.scope == ContextScope.TASK and entry.task_id == task_id):
                    del self._context[key]
                    return True
            
            return False
    
    def cleanup_expired(self) -> int:
        """Remove expired context entries and return count of removed entries"""
        removed_count = 0
        
        with self._lock:
            # Clean workflow context
            expired_keys = [key for key, entry in self._context.items() if entry.is_expired()]
            for key in expired_keys:
                del self._context[key]
                removed_count += 1
            
            # Clean global context
            expired_global_keys = [key for key, entry in self._global_context.items() if entry.is_expired()]
            for key in expired_global_keys:
                del self._global_context[key]
                removed_count += 1
        
        return removed_count
    
    def get_context_info(self) -> Dict[str, Any]:
        """Get information about the current context state"""
        with self._lock:
            return {
                'workflow_id': self.workflow_id,
                'total_entries': len(self._context) + len(self._global_context),
                'workflow_entries': len(self._context),
                'global_entries': len(self._global_context),
                'scopes': {
                    scope.value: len([e for e in self._context.values() if e.scope == scope])
                    for scope in ContextScope
                }
            }
    
    def export_context(self, agent_name: str, task_id: str = None) -> Dict[str, Any]:
        """Export all accessible context for debugging/logging"""
        context_data = self.get_all_for_agent(agent_name, task_id)
        return {
            'workflow_id': self.workflow_id,
            'agent_name': agent_name,
            'task_id': task_id,
            'context': context_data,
            'exported_at': datetime.utcnow().isoformat()
        } 