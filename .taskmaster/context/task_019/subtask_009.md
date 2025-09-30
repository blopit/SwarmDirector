# Memory Debugging Tools Integration

## Subtask Metadata
```yaml
subtask_id: "subtask_009"
parent_task: "task_019"
title: "Memory Debugging Tools Integration"
type: "full_stack_development"
priority: "medium"
estimated_effort: "3-4 days"
complexity: "medium"
dependencies:
  - subtask_001
  - subtask_004
  - subtask_007
  - subtask_008
assignee: "full_stack_developer"
status: "blocked"
```

## Objective

Integrate all memory debugging components into a cohesive debugging toolkit with advanced features like memory breakpoints, state comparison, debugging sessions, and automated debugging workflows to provide developers with comprehensive memory debugging capabilities.

## Technical Specifications

### Integrated Debugging Dashboard

#### Main Debugging Interface
```jsx
// src/swarm_director/web/static/js/components/MemoryDebuggingDashboard.jsx
import React, { useState, useEffect } from 'react';
import { MemoryInspector } from './MemoryInspector';
import { MemoryTimeline } from './MemoryTimeline';
import { ContextRelationshipMap } from './ContextRelationshipMap';
import { MemoryBreakpoints } from './MemoryBreakpoints';
import { MemoryComparison } from './MemoryComparison';
import { DebuggingSession } from './DebuggingSession';
import { OptimizationPanel } from './OptimizationPanel';

const MemoryDebuggingDashboard = ({ agentId }) => {
    const [activeTab, setActiveTab] = useState('inspector');
    const [debuggingSession, setDebuggingSession] = useState(null);
    const [breakpoints, setBreakpoints] = useState([]);
    const [comparisonStates, setComparisonStates] = useState([]);
    
    const debuggingTabs = [
        { id: 'inspector', label: 'Memory Inspector', icon: 'fas fa-search' },
        { id: 'timeline', label: 'Timeline', icon: 'fas fa-chart-line' },
        { id: 'relationships', label: 'Relationships', icon: 'fas fa-project-diagram' },
        { id: 'breakpoints', label: 'Breakpoints', icon: 'fas fa-pause-circle' },
        { id: 'comparison', label: 'Comparison', icon: 'fas fa-balance-scale' },
        { id: 'optimization', label: 'Optimization', icon: 'fas fa-tachometer-alt' }
    ];
    
    const startDebuggingSession = () => {
        const session = {
            id: Date.now(),
            agentId: agentId,
            startTime: new Date(),
            name: `Debug Session ${agentId}`,
            snapshots: [],
            breakpoints: [],
            notes: []
        };
        setDebuggingSession(session);
    };
    
    const stopDebuggingSession = () => {
        if (debuggingSession) {
            // Save session data
            saveDebuggingSession(debuggingSession);
            setDebuggingSession(null);
        }
    };
    
    return (
        <div className="memory-debugging-dashboard">
            <div className="dashboard-header">
                <div className="header-left">
                    <h2><i className="fas fa-bug"></i> Memory Debugging - Agent {agentId}</h2>
                    <div className="session-controls">
                        {!debuggingSession ? (
                            <button 
                                className="btn btn-success"
                                onClick={startDebuggingSession}
                            >
                                <i className="fas fa-play"></i> Start Debug Session
                            </button>
                        ) : (
                            <div className="active-session">
                                <span className="session-indicator">
                                    <i className="fas fa-circle text-success"></i>
                                    Debug Session Active
                                </span>
                                <button 
                                    className="btn btn-danger btn-sm"
                                    onClick={stopDebuggingSession}
                                >
                                    <i className="fas fa-stop"></i> Stop
                                </button>
                            </div>
                        )}
                    </div>
                </div>
                
                <div className="header-right">
                    <DebugToolbar 
                        agentId={agentId}
                        debuggingSession={debuggingSession}
                        onCreateSnapshot={handleCreateSnapshot}
                        onExportSession={handleExportSession}
                    />
                </div>
            </div>
            
            <div className="dashboard-tabs">
                <nav className="nav nav-tabs">
                    {debuggingTabs.map(tab => (
                        <button
                            key={tab.id}
                            className={`nav-link ${activeTab === tab.id ? 'active' : ''}`}
                            onClick={() => setActiveTab(tab.id)}
                        >
                            <i className={tab.icon}></i>
                            {tab.label}
                        </button>
                    ))}
                </nav>
            </div>
            
            <div className="dashboard-content">
                {activeTab === 'inspector' && (
                    <MemoryInspector 
                        agentId={agentId}
                        debuggingSession={debuggingSession}
                        onBreakpointHit={handleBreakpointHit}
                    />
                )}
                
                {activeTab === 'timeline' && (
                    <MemoryTimeline 
                        agentId={agentId}
                        debuggingSession={debuggingSession}
                        breakpoints={breakpoints}
                    />
                )}
                
                {activeTab === 'relationships' && (
                    <ContextRelationshipMap 
                        agentId={agentId}
                        debuggingSession={debuggingSession}
                    />
                )}
                
                {activeTab === 'breakpoints' && (
                    <MemoryBreakpoints 
                        agentId={agentId}
                        breakpoints={breakpoints}
                        onBreakpointsChange={setBreakpoints}
                        debuggingSession={debuggingSession}
                    />
                )}
                
                {activeTab === 'comparison' && (
                    <MemoryComparison 
                        agentId={agentId}
                        comparisonStates={comparisonStates}
                        onStatesChange={setComparisonStates}
                        debuggingSession={debuggingSession}
                    />
                )}
                
                {activeTab === 'optimization' && (
                    <OptimizationPanel 
                        agentId={agentId}
                        debuggingSession={debuggingSession}
                    />
                )}
            </div>
        </div>
    );
};
```

### Memory Breakpoints System

#### Breakpoints Component
```jsx
// src/swarm_director/web/static/js/components/MemoryBreakpoints.jsx
const MemoryBreakpoints = ({ agentId, breakpoints, onBreakpointsChange, debuggingSession }) => {
    const [newBreakpoint, setNewBreakpoint] = useState({
        type: 'memory_size',
        condition: 'greater_than',
        value: '',
        enabled: true
    });
    
    const breakpointTypes = [
        { value: 'memory_size', label: 'Memory Size', unit: 'MB' },
        { value: 'conversation_count', label: 'Conversation Count', unit: 'count' },
        { value: 'message_count', label: 'Message Count', unit: 'count' },
        { value: 'memory_change', label: 'Memory Change', unit: 'MB' },
        { value: 'context_update', label: 'Context Update', unit: 'event' }
    ];
    
    const conditions = [
        { value: 'greater_than', label: 'Greater Than' },
        { value: 'less_than', label: 'Less Than' },
        { value: 'equals', label: 'Equals' },
        { value: 'change_by', label: 'Changes By' }
    ];
    
    const addBreakpoint = () => {
        if (!newBreakpoint.value) return;
        
        const breakpoint = {
            id: Date.now(),
            agentId: agentId,
            ...newBreakpoint,
            createdAt: new Date(),
            hitCount: 0,
            lastHit: null
        };
        
        onBreakpointsChange([...breakpoints, breakpoint]);
        
        // Register breakpoint with backend
        registerBreakpoint(breakpoint);
        
        // Reset form
        setNewBreakpoint({
            type: 'memory_size',
            condition: 'greater_than',
            value: '',
            enabled: true
        });
    };
    
    const toggleBreakpoint = (breakpointId) => {
        const updatedBreakpoints = breakpoints.map(bp =>
            bp.id === breakpointId ? { ...bp, enabled: !bp.enabled } : bp
        );
        onBreakpointsChange(updatedBreakpoints);
        
        // Update backend
        const breakpoint = updatedBreakpoints.find(bp => bp.id === breakpointId);
        updateBreakpoint(breakpoint);
    };
    
    const removeBreakpoint = (breakpointId) => {
        const updatedBreakpoints = breakpoints.filter(bp => bp.id !== breakpointId);
        onBreakpointsChange(updatedBreakpoints);
        
        // Remove from backend
        unregisterBreakpoint(breakpointId);
    };
    
    return (
        <div className="memory-breakpoints">
            <div className="breakpoints-header">
                <h4><i className="fas fa-pause-circle"></i> Memory Breakpoints</h4>
                <div className="breakpoint-stats">
                    <span className="stat">
                        <strong>{breakpoints.length}</strong> Total
                    </span>
                    <span className="stat">
                        <strong>{breakpoints.filter(bp => bp.enabled).length}</strong> Active
                    </span>
                    <span className="stat">
                        <strong>{breakpoints.reduce((sum, bp) => sum + bp.hitCount, 0)}</strong> Hits
                    </span>
                </div>
            </div>
            
            <div className="add-breakpoint-form">
                <h5>Add New Breakpoint</h5>
                <div className="form-row">
                    <div className="form-group">
                        <label>Type</label>
                        <select 
                            value={newBreakpoint.type}
                            onChange={(e) => setNewBreakpoint({...newBreakpoint, type: e.target.value})}
                            className="form-select"
                        >
                            {breakpointTypes.map(type => (
                                <option key={type.value} value={type.value}>
                                    {type.label}
                                </option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="form-group">
                        <label>Condition</label>
                        <select 
                            value={newBreakpoint.condition}
                            onChange={(e) => setNewBreakpoint({...newBreakpoint, condition: e.target.value})}
                            className="form-select"
                        >
                            {conditions.map(condition => (
                                <option key={condition.value} value={condition.value}>
                                    {condition.label}
                                </option>
                            ))}
                        </select>
                    </div>
                    
                    <div className="form-group">
                        <label>Value</label>
                        <input
                            type="number"
                            value={newBreakpoint.value}
                            onChange={(e) => setNewBreakpoint({...newBreakpoint, value: e.target.value})}
                            className="form-control"
                            placeholder="Enter value"
                        />
                    </div>
                    
                    <div className="form-group">
                        <button 
                            className="btn btn-primary"
                            onClick={addBreakpoint}
                            disabled={!newBreakpoint.value}
                        >
                            <i className="fas fa-plus"></i> Add
                        </button>
                    </div>
                </div>
            </div>
            
            <div className="breakpoints-list">
                <h5>Active Breakpoints</h5>
                {breakpoints.length === 0 ? (
                    <div className="no-breakpoints">
                        <i className="fas fa-info-circle"></i>
                        No breakpoints configured. Add a breakpoint to pause execution when conditions are met.
                    </div>
                ) : (
                    <div className="breakpoints-table">
                        <table className="table">
                            <thead>
                                <tr>
                                    <th>Status</th>
                                    <th>Type</th>
                                    <th>Condition</th>
                                    <th>Value</th>
                                    <th>Hits</th>
                                    <th>Last Hit</th>
                                    <th>Actions</th>
                                </tr>
                            </thead>
                            <tbody>
                                {breakpoints.map(breakpoint => (
                                    <tr key={breakpoint.id} className={breakpoint.enabled ? '' : 'disabled'}>
                                        <td>
                                            <button
                                                className={`btn btn-sm ${breakpoint.enabled ? 'btn-success' : 'btn-secondary'}`}
                                                onClick={() => toggleBreakpoint(breakpoint.id)}
                                                title={breakpoint.enabled ? 'Disable' : 'Enable'}
                                            >
                                                <i className={`fas ${breakpoint.enabled ? 'fa-pause' : 'fa-play'}`}></i>
                                            </button>
                                        </td>
                                        <td>{breakpointTypes.find(t => t.value === breakpoint.type)?.label}</td>
                                        <td>{conditions.find(c => c.value === breakpoint.condition)?.label}</td>
                                        <td>{breakpoint.value}</td>
                                        <td>
                                            <span className="badge badge-info">{breakpoint.hitCount}</span>
                                        </td>
                                        <td>
                                            {breakpoint.lastHit ? new Date(breakpoint.lastHit).toLocaleString() : 'Never'}
                                        </td>
                                        <td>
                                            <button
                                                className="btn btn-sm btn-danger"
                                                onClick={() => removeBreakpoint(breakpoint.id)}
                                                title="Remove breakpoint"
                                            >
                                                <i className="fas fa-trash"></i>
                                            </button>
                                        </td>
                                    </tr>
                                ))}
                            </tbody>
                        </table>
                    </div>
                )}
            </div>
        </div>
    );
};
```

### Memory State Comparison

#### Comparison Component
```jsx
// src/swarm_director/web/static/js/components/MemoryComparison.jsx
const MemoryComparison = ({ agentId, comparisonStates, onStatesChange, debuggingSession }) => {
    const [selectedStates, setSelectedStates] = useState([]);
    const [comparisonResult, setComparisonResult] = useState(null);
    const [isLoading, setIsLoading] = useState(false);
    
    const captureCurrentState = async () => {
        try {
            const response = await fetch(`/api/memory/agents/${agentId}/memory`);
            const data = await response.json();
            
            const snapshot = {
                id: Date.now(),
                name: `Snapshot ${new Date().toLocaleTimeString()}`,
                timestamp: new Date(),
                memoryState: data.data,
                metadata: {
                    capturedDuring: debuggingSession?.id || null,
                    agentId: agentId
                }
            };
            
            onStatesChange([...comparisonStates, snapshot]);
        } catch (error) {
            console.error('Error capturing memory state:', error);
        }
    };
    
    const compareStates = async () => {
        if (selectedStates.length < 2) return;
        
        setIsLoading(true);
        try {
            const response = await fetch('/api/memory/compare', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    agent_id: agentId,
                    state_ids: selectedStates
                })
            });
            
            const data = await response.json();
            setComparisonResult(data.comparison);
        } catch (error) {
            console.error('Error comparing states:', error);
        } finally {
            setIsLoading(false);
        }
    };
    
    return (
        <div className="memory-comparison">
            <div className="comparison-header">
                <h4><i className="fas fa-balance-scale"></i> Memory State Comparison</h4>
                <div className="comparison-controls">
                    <button 
                        className="btn btn-primary"
                        onClick={captureCurrentState}
                    >
                        <i className="fas fa-camera"></i> Capture Current State
                    </button>
                    
                    <button 
                        className="btn btn-success"
                        onClick={compareStates}
                        disabled={selectedStates.length < 2 || isLoading}
                    >
                        <i className="fas fa-balance-scale"></i>
                        {isLoading ? 'Comparing...' : 'Compare Selected'}
                    </button>
                </div>
            </div>
            
            <div className="comparison-content">
                <div className="states-selection">
                    <h5>Available States ({comparisonStates.length})</h5>
                    <div className="states-grid">
                        {comparisonStates.map(state => (
                            <div 
                                key={state.id}
                                className={`state-card ${selectedStates.includes(state.id) ? 'selected' : ''}`}
                                onClick={() => toggleStateSelection(state.id)}
                            >
                                <div className="state-header">
                                    <h6>{state.name}</h6>
                                    <span className="state-time">
                                        {state.timestamp.toLocaleString()}
                                    </span>
                                </div>
                                
                                <div className="state-metrics">
                                    <div className="metric">
                                        <span className="label">Memory:</span>
                                        <span className="value">
                                            {state.memoryState.memory_usage?.total_size_mb?.toFixed(1) || 0}MB
                                        </span>
                                    </div>
                                    <div className="metric">
                                        <span className="label">Conversations:</span>
                                        <span className="value">
                                            {state.memoryState.memory_state?.conversation_memory?.conversations?.length || 0}
                                        </span>
                                    </div>
                                </div>
                                
                                {selectedStates.includes(state.id) && (
                                    <div className="selection-indicator">
                                        <i className="fas fa-check-circle"></i>
                                    </div>
                                )}
                            </div>
                        ))}
                    </div>
                </div>
                
                {comparisonResult && (
                    <div className="comparison-results">
                        <h5>Comparison Results</h5>
                        <MemoryComparisonResults result={comparisonResult} />
                    </div>
                )}
            </div>
        </div>
    );
};
```

### Debugging Session Management

#### Session Component
```jsx
// src/swarm_director/web/static/js/components/DebuggingSession.jsx
const DebuggingSession = ({ session, onSessionUpdate }) => {
    const [sessionNotes, setSessionNotes] = useState(session?.notes || []);
    const [newNote, setNewNote] = useState('');
    
    const addNote = () => {
        if (!newNote.trim()) return;
        
        const note = {
            id: Date.now(),
            content: newNote,
            timestamp: new Date(),
            type: 'user_note'
        };
        
        const updatedNotes = [...sessionNotes, note];
        setSessionNotes(updatedNotes);
        setNewNote('');
        
        onSessionUpdate({
            ...session,
            notes: updatedNotes
        });
    };
    
    const exportSession = () => {
        const sessionData = {
            ...session,
            notes: sessionNotes,
            exportedAt: new Date()
        };
        
        const blob = new Blob([JSON.stringify(sessionData, null, 2)], {
            type: 'application/json'
        });
        
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = `debug-session-${session.id}.json`;
        a.click();
        URL.revokeObjectURL(url);
    };
    
    return (
        <div className="debugging-session">
            <div className="session-info">
                <h5>Session: {session.name}</h5>
                <div className="session-details">
                    <span>Started: {session.startTime.toLocaleString()}</span>
                    <span>Duration: {formatDuration(Date.now() - session.startTime)}</span>
                    <span>Snapshots: {session.snapshots?.length || 0}</span>
                </div>
            </div>
            
            <div className="session-notes">
                <h6>Session Notes</h6>
                <div className="add-note">
                    <textarea
                        value={newNote}
                        onChange={(e) => setNewNote(e.target.value)}
                        placeholder="Add a note about your debugging session..."
                        className="form-control"
                        rows="3"
                    />
                    <button 
                        className="btn btn-sm btn-primary"
                        onClick={addNote}
                        disabled={!newNote.trim()}
                    >
                        Add Note
                    </button>
                </div>
                
                <div className="notes-list">
                    {sessionNotes.map(note => (
                        <div key={note.id} className="note-item">
                            <div className="note-header">
                                <span className="note-time">
                                    {note.timestamp.toLocaleTimeString()}
                                </span>
                                <span className="note-type">{note.type}</span>
                            </div>
                            <div className="note-content">{note.content}</div>
                        </div>
                    ))}
                </div>
            </div>
            
            <div className="session-actions">
                <button 
                    className="btn btn-info"
                    onClick={exportSession}
                >
                    <i className="fas fa-download"></i> Export Session
                </button>
            </div>
        </div>
    );
};
```

## Backend Integration

### Debugging Session API
```python
# src/swarm_director/api/debugging_routes.py
from flask import Blueprint, request, jsonify
from ..services.debugging_session import DebuggingSessionManager
from ..services.memory_breakpoints import MemoryBreakpointManager
from ..utils.auth import require_auth

debugging_bp = Blueprint('debugging', __name__, url_prefix='/api/debugging')

@debugging_bp.route('/sessions', methods=['POST'])
@require_auth
def create_debugging_session():
    """Create a new debugging session"""
    try:
        data = request.get_json()
        session_manager = DebuggingSessionManager()
        session = session_manager.create_session(
            agent_id=data['agent_id'],
            name=data.get('name'),
            user_id=request.user_id
        )
        
        return jsonify({
            'success': True,
            'session': session.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@debugging_bp.route('/breakpoints', methods=['POST'])
@require_auth
def create_breakpoint():
    """Create a memory breakpoint"""
    try:
        data = request.get_json()
        breakpoint_manager = MemoryBreakpointManager()
        breakpoint = breakpoint_manager.create_breakpoint(
            agent_id=data['agent_id'],
            breakpoint_type=data['type'],
            condition=data['condition'],
            value=data['value']
        )
        
        return jsonify({
            'success': True,
            'breakpoint': breakpoint.to_dict()
        })
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500
```

## Implementation Steps

### Step 1: Integrated Dashboard (Day 1-2)
1. Create main debugging dashboard component
2. Implement tab-based navigation
3. Add debugging session management
4. Create debug toolbar and controls

### Step 2: Breakpoints System (Day 2-3)
1. Implement memory breakpoints component
2. Create breakpoint management backend
3. Add breakpoint condition evaluation
4. Integrate with real-time monitoring

### Step 3: Comparison Tools (Day 3)
1. Create memory state comparison component
2. Implement state capture and storage
3. Add comparison algorithms
4. Create comparison visualization

### Step 4: Session Management (Day 4)
1. Implement debugging session persistence
2. Add session export/import functionality
3. Create session notes and annotations
4. Add session sharing capabilities

## Success Criteria

### Functional Requirements
- [ ] Integrated debugging dashboard with all tools
- [ ] Memory breakpoints with condition evaluation
- [ ] Memory state comparison and analysis
- [ ] Debugging session management and persistence
- [ ] Export/import capabilities for debugging data

### User Experience Requirements
- [ ] Intuitive debugging workflow
- [ ] Seamless tool integration
- [ ] Efficient debugging session management
- [ ] Clear visual feedback and status indicators

### Technical Requirements
- [ ] Real-time breakpoint evaluation
- [ ] Efficient state comparison algorithms
- [ ] Reliable session persistence
- [ ] Cross-browser compatibility

## Related Files
- `src/swarm_director/web/static/js/components/MemoryDebuggingDashboard.jsx` - Main dashboard
- `src/swarm_director/web/static/js/components/MemoryBreakpoints.jsx` - Breakpoints system
- `src/swarm_director/web/static/js/components/MemoryComparison.jsx` - State comparison
- `src/swarm_director/api/debugging_routes.py` - Debugging API endpoints
- `src/swarm_director/services/debugging_session.py` - Session management service
