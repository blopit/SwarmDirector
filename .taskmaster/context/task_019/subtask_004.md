# Memory Inspector Dashboard Component

## Subtask Metadata
```yaml
subtask_id: "subtask_004"
parent_task: "task_019"
title: "Memory Inspector Dashboard Component"
type: "frontend_development"
priority: "high"
estimated_effort: "4-5 days"
complexity: "high"
dependencies:
  - subtask_001
  - existing_dashboard_infrastructure
assignee: "frontend_developer"
status: "blocked"
```

## Objective

Develop a comprehensive React-based dashboard component for real-time agent memory inspection, providing intuitive visualization of memory states, interactive debugging tools, and seamless integration with the existing SwarmDirector dashboard.

## Technical Specifications

### Component Architecture

#### Main Memory Inspector Component
```jsx
// src/swarm_director/web/static/js/components/MemoryInspector.jsx
import React, { useState, useEffect, useCallback } from 'react';
import { MemoryStateViewer } from './MemoryStateViewer';
import { MemoryHistoryPanel } from './MemoryHistoryPanel';
import { MemoryControlPanel } from './MemoryControlPanel';
import { MemoryMetricsPanel } from './MemoryMetricsPanel';

const MemoryInspector = ({ agentId, isRealTime = false }) => {
    const [memoryState, setMemoryState] = useState(null);
    const [memoryHistory, setMemoryHistory] = useState([]);
    const [selectedTimeRange, setSelectedTimeRange] = useState('1h');
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState(null);
    
    // Real-time memory monitoring
    const [wsConnection, setWsConnection] = useState(null);
    const [isConnected, setIsConnected] = useState(false);
    
    return (
        <div className="memory-inspector">
            <div className="memory-inspector-header">
                <h3>Agent Memory Inspector - Agent {agentId}</h3>
                <MemoryControlPanel 
                    agentId={agentId}
                    onRefresh={handleRefresh}
                    onExport={handleExport}
                    onReset={handleReset}
                    isRealTime={isRealTime}
                    onToggleRealTime={handleToggleRealTime}
                />
            </div>
            
            <div className="memory-inspector-content">
                <div className="memory-main-panel">
                    <MemoryStateViewer 
                        memoryState={memoryState}
                        isLoading={isLoading}
                        error={error}
                    />
                </div>
                
                <div className="memory-side-panel">
                    <MemoryMetricsPanel 
                        agentId={agentId}
                        memoryState={memoryState}
                    />
                    
                    <MemoryHistoryPanel 
                        agentId={agentId}
                        memoryHistory={memoryHistory}
                        selectedTimeRange={selectedTimeRange}
                        onTimeRangeChange={setSelectedTimeRange}
                    />
                </div>
            </div>
        </div>
    );
};
```

#### Memory State Viewer Component
```jsx
// MemoryStateViewer.jsx
const MemoryStateViewer = ({ memoryState, isLoading, error }) => {
    const [selectedSection, setSelectedSection] = useState('conversation_memory');
    const [expandedNodes, setExpandedNodes] = useState(new Set());
    const [searchQuery, setSearchQuery] = useState('');
    
    const memorySections = [
        { key: 'conversation_memory', label: 'Conversations', icon: 'fas fa-comments' },
        { key: 'workflow_context', label: 'Workflow Context', icon: 'fas fa-project-diagram' },
        { key: 'agent_config', label: 'Configuration', icon: 'fas fa-cog' },
        { key: 'activity_history', label: 'Activity History', icon: 'fas fa-history' }
    ];
    
    return (
        <div className="memory-state-viewer">
            <div className="memory-section-tabs">
                {memorySections.map(section => (
                    <button
                        key={section.key}
                        className={`memory-tab ${selectedSection === section.key ? 'active' : ''}`}
                        onClick={() => setSelectedSection(section.key)}
                    >
                        <i className={section.icon}></i>
                        {section.label}
                    </button>
                ))}
            </div>
            
            <div className="memory-search-bar">
                <input
                    type="text"
                    placeholder="Search memory content..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="form-control"
                />
            </div>
            
            <div className="memory-content">
                {isLoading ? (
                    <div className="memory-loading">
                        <div className="spinner-border" role="status">
                            <span className="sr-only">Loading memory state...</span>
                        </div>
                    </div>
                ) : error ? (
                    <div className="memory-error alert alert-danger">
                        <i className="fas fa-exclamation-triangle"></i>
                        Error loading memory: {error.message}
                    </div>
                ) : (
                    <MemoryContentTree
                        data={memoryState?.[selectedSection]}
                        expandedNodes={expandedNodes}
                        onToggleNode={handleToggleNode}
                        searchQuery={searchQuery}
                    />
                )}
            </div>
        </div>
    );
};
```

#### Memory Content Tree Component
```jsx
// MemoryContentTree.jsx
const MemoryContentTree = ({ data, expandedNodes, onToggleNode, searchQuery }) => {
    const renderMemoryNode = (key, value, path = '') => {
        const fullPath = path ? `${path}.${key}` : key;
        const isExpanded = expandedNodes.has(fullPath);
        const isObject = typeof value === 'object' && value !== null;
        const isArray = Array.isArray(value);
        
        // Search filtering
        if (searchQuery && !matchesSearch(key, value, searchQuery)) {
            return null;
        }
        
        return (
            <div key={fullPath} className="memory-node">
                <div className="memory-node-header" onClick={() => onToggleNode(fullPath)}>
                    {isObject && (
                        <i className={`fas fa-chevron-${isExpanded ? 'down' : 'right'} memory-expand-icon`}></i>
                    )}
                    <span className="memory-key">{key}</span>
                    <span className="memory-type-badge">
                        {isArray ? `Array[${value.length}]` : typeof value}
                    </span>
                    {!isObject && (
                        <span className="memory-value">
                            {formatMemoryValue(value)}
                        </span>
                    )}
                </div>
                
                {isObject && isExpanded && (
                    <div className="memory-node-children">
                        {Object.entries(value).map(([childKey, childValue]) =>
                            renderMemoryNode(childKey, childValue, fullPath)
                        )}
                    </div>
                )}
            </div>
        );
    };
    
    return (
        <div className="memory-content-tree">
            {data ? Object.entries(data).map(([key, value]) =>
                renderMemoryNode(key, value)
            ) : (
                <div className="memory-empty">No memory data available</div>
            )}
        </div>
    );
};
```

### Memory Control Panel
```jsx
// MemoryControlPanel.jsx
const MemoryControlPanel = ({ 
    agentId, 
    onRefresh, 
    onExport, 
    onReset, 
    isRealTime, 
    onToggleRealTime 
}) => {
    const [isExporting, setIsExporting] = useState(false);
    const [showResetConfirm, setShowResetConfirm] = useState(false);
    
    return (
        <div className="memory-control-panel">
            <div className="control-group">
                <button 
                    className="btn btn-primary btn-sm"
                    onClick={onRefresh}
                    title="Refresh memory state"
                >
                    <i className="fas fa-sync-alt"></i> Refresh
                </button>
                
                <button 
                    className={`btn btn-sm ${isRealTime ? 'btn-success' : 'btn-outline-secondary'}`}
                    onClick={onToggleRealTime}
                    title="Toggle real-time monitoring"
                >
                    <i className="fas fa-broadcast-tower"></i>
                    {isRealTime ? 'Live' : 'Static'}
                </button>
            </div>
            
            <div className="control-group">
                <button 
                    className="btn btn-info btn-sm"
                    onClick={onExport}
                    disabled={isExporting}
                    title="Export memory state"
                >
                    <i className="fas fa-download"></i>
                    {isExporting ? 'Exporting...' : 'Export'}
                </button>
                
                <button 
                    className="btn btn-warning btn-sm"
                    onClick={() => setShowResetConfirm(true)}
                    title="Reset agent memory"
                >
                    <i className="fas fa-trash-restore"></i> Reset
                </button>
            </div>
            
            {showResetConfirm && (
                <MemoryResetModal
                    agentId={agentId}
                    onConfirm={onReset}
                    onCancel={() => setShowResetConfirm(false)}
                />
            )}
        </div>
    );
};
```

### Memory Metrics Panel
```jsx
// MemoryMetricsPanel.jsx
const MemoryMetricsPanel = ({ agentId, memoryState }) => {
    const [metrics, setMetrics] = useState(null);
    
    useEffect(() => {
        if (memoryState) {
            calculateMemoryMetrics(memoryState).then(setMetrics);
        }
    }, [memoryState]);
    
    return (
        <div className="memory-metrics-panel">
            <h5><i className="fas fa-chart-bar"></i> Memory Metrics</h5>
            
            {metrics && (
                <div className="metrics-grid">
                    <div className="metric-card">
                        <div className="metric-value">{metrics.totalSizeMB}MB</div>
                        <div className="metric-label">Total Size</div>
                    </div>
                    
                    <div className="metric-card">
                        <div className="metric-value">{metrics.conversationCount}</div>
                        <div className="metric-label">Conversations</div>
                    </div>
                    
                    <div className="metric-card">
                        <div className="metric-value">{metrics.messageCount}</div>
                        <div className="metric-label">Messages</div>
                    </div>
                    
                    <div className="metric-card">
                        <div className="metric-value">{metrics.workflowCount}</div>
                        <div className="metric-label">Workflows</div>
                    </div>
                </div>
            )}
            
            <div className="memory-size-breakdown">
                <h6>Size Breakdown</h6>
                <MemorySizeChart data={metrics?.sizeBreakdown} />
            </div>
        </div>
    );
};
```

## Implementation Steps

### Step 1: Core Component Structure (Day 1-2)
1. Create main `MemoryInspector` component
2. Implement `MemoryStateViewer` with tab navigation
3. Create `MemoryContentTree` for hierarchical data display
4. Add basic styling and layout

### Step 2: Interactive Features (Day 2-3)
1. Implement memory content search functionality
2. Add expandable tree navigation
3. Create memory metrics calculation and display
4. Add memory control panel with actions

### Step 3: Real-time Integration (Day 3-4)
1. Implement WebSocket connection for real-time updates
2. Add real-time memory state synchronization
3. Create connection status indicators
4. Handle connection errors and reconnection

### Step 4: Advanced Features (Day 4-5)
1. Add memory export functionality
2. Implement memory reset confirmation modal
3. Create memory comparison tools
4. Add performance optimizations

## Styling and CSS

### Component Styles
```css
/* src/swarm_director/web/static/css/memory-inspector.css */
.memory-inspector {
    display: flex;
    flex-direction: column;
    height: 100%;
    background: #f8f9fa;
    border-radius: 8px;
    overflow: hidden;
}

.memory-inspector-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    background: #fff;
    border-bottom: 1px solid #dee2e6;
}

.memory-inspector-content {
    display: flex;
    flex: 1;
    overflow: hidden;
}

.memory-main-panel {
    flex: 2;
    display: flex;
    flex-direction: column;
    background: #fff;
    margin: 0.5rem;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.memory-side-panel {
    flex: 1;
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
    padding: 0.5rem;
}

.memory-section-tabs {
    display: flex;
    border-bottom: 1px solid #dee2e6;
    background: #f8f9fa;
}

.memory-tab {
    padding: 0.75rem 1rem;
    border: none;
    background: transparent;
    cursor: pointer;
    transition: all 0.2s;
}

.memory-tab.active {
    background: #fff;
    border-bottom: 2px solid #007bff;
    color: #007bff;
}

.memory-content-tree {
    padding: 1rem;
    overflow-y: auto;
    font-family: 'Monaco', 'Menlo', monospace;
    font-size: 0.875rem;
}

.memory-node {
    margin-bottom: 0.25rem;
}

.memory-node-header {
    display: flex;
    align-items: center;
    padding: 0.25rem 0.5rem;
    cursor: pointer;
    border-radius: 4px;
    transition: background-color 0.2s;
}

.memory-node-header:hover {
    background-color: #f8f9fa;
}

.memory-key {
    font-weight: 600;
    color: #495057;
    margin-right: 0.5rem;
}

.memory-type-badge {
    background: #6c757d;
    color: white;
    padding: 0.125rem 0.375rem;
    border-radius: 12px;
    font-size: 0.75rem;
    margin-right: 0.5rem;
}

.memory-value {
    color: #28a745;
    font-style: italic;
}

.memory-metrics-panel {
    background: #fff;
    padding: 1rem;
    border-radius: 6px;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.metrics-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 0.5rem;
    margin-bottom: 1rem;
}

.metric-card {
    text-align: center;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 4px;
}

.metric-value {
    font-size: 1.25rem;
    font-weight: bold;
    color: #007bff;
}

.metric-label {
    font-size: 0.75rem;
    color: #6c757d;
    text-transform: uppercase;
}
```

## Integration with Existing Dashboard

### Dashboard Route Integration
```jsx
// Add to existing dashboard routing
import { MemoryInspector } from './components/MemoryInspector';

// In dashboard routes
<Route path="/dashboard/agents/:agentId/memory" 
       component={({ match }) => 
           <MemoryInspector agentId={match.params.agentId} />
       } 
/>
```

### Navigation Integration
```jsx
// Add memory inspector link to agent management page
<a href={`/dashboard/agents/${agent.id}/memory`} 
   className="btn btn-sm btn-outline-info">
    <i className="fas fa-memory"></i> Memory
</a>
```

## API Integration

### Memory API Service
```javascript
// src/swarm_director/web/static/js/services/memoryApi.js
class MemoryApiService {
    constructor() {
        this.baseUrl = '/api/memory';
    }
    
    async getAgentMemory(agentId) {
        const response = await fetch(`${this.baseUrl}/agents/${agentId}/memory`);
        return await response.json();
    }
    
    async getMemoryHistory(agentId, timeRange = '1h') {
        const response = await fetch(
            `${this.baseUrl}/agents/${agentId}/memory/history?range=${timeRange}`
        );
        return await response.json();
    }
    
    async exportMemory(agentId, options = {}) {
        const response = await fetch(`${this.baseUrl}/agents/${agentId}/memory/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(options)
        });
        return await response.json();
    }
    
    async resetMemory(agentId, memoryTypes = []) {
        const response = await fetch(`${this.baseUrl}/agents/${agentId}/memory/reset`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ memory_types: memoryTypes })
        });
        return await response.json();
    }
}

export const memoryApi = new MemoryApiService();
```

## Testing Requirements

### Component Tests
```javascript
// __tests__/MemoryInspector.test.js
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryInspector } from '../MemoryInspector';

describe('MemoryInspector', () => {
    test('renders memory inspector with agent ID', () => {
        render(<MemoryInspector agentId={123} />);
        expect(screen.getByText(/Agent Memory Inspector - Agent 123/)).toBeInTheDocument();
    });
    
    test('loads memory state on mount', async () => {
        // Mock API response
        global.fetch = jest.fn(() =>
            Promise.resolve({
                json: () => Promise.resolve({ success: true, data: mockMemoryState })
            })
        );
        
        render(<MemoryInspector agentId={123} />);
        
        await waitFor(() => {
            expect(screen.getByText(/Conversations/)).toBeInTheDocument();
        });
    });
    
    test('handles memory refresh', async () => {
        // Test refresh functionality
    });
    
    test('toggles real-time monitoring', () => {
        // Test real-time toggle
    });
});
```

## Success Criteria

### Functional Requirements
- [ ] Display complete agent memory state in organized tabs
- [ ] Interactive tree navigation for memory content
- [ ] Real-time memory state updates
- [ ] Memory search and filtering capabilities
- [ ] Memory export and reset functionality

### User Experience Requirements
- [ ] Responsive design for various screen sizes
- [ ] Intuitive navigation and interaction
- [ ] Fast loading and smooth performance
- [ ] Clear visual feedback for all actions
- [ ] Accessible design following WCAG guidelines

### Technical Requirements
- [ ] Component renders within 500ms
- [ ] Real-time updates with <100ms latency
- [ ] Handles large memory states (100MB+) efficiently
- [ ] Cross-browser compatibility
- [ ] Mobile-responsive design

## Related Files
- `src/swarm_director/web/static/js/components/MemoryInspector.jsx` - Main component
- `src/swarm_director/web/static/css/memory-inspector.css` - Component styles
- `src/swarm_director/web/static/js/services/memoryApi.js` - API service
- `src/swarm_director/web/templates/dashboard/memory_inspector.html` - Template
