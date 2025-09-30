# Context Relationship Mapping

## Subtask Metadata
```yaml
subtask_id: "subtask_006"
parent_task: "task_019"
title: "Context Relationship Mapping"
type: "frontend_development"
priority: "medium"
estimated_effort: "3-4 days"
complexity: "high"
dependencies:
  - subtask_001
  - subtask_004
  - workflow_context_system
assignee: "frontend_developer"
status: "blocked"
```

## Objective

Develop an interactive visual mapping system that displays relationships between agent memory contexts, workflow sharing, and cross-agent dependencies to help developers understand memory interconnections and debug complex multi-agent scenarios.

## Technical Specifications

### Context Relationship Visualization

#### Main Context Map Component
```jsx
// src/swarm_director/web/static/js/components/ContextRelationshipMap.jsx
import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { ContextMapControls } from './ContextMapControls';
import { RelationshipDetails } from './RelationshipDetails';
import { ContextFilters } from './ContextFilters';

const ContextRelationshipMap = ({ agentId, workflowId = null }) => {
    const svgRef = useRef();
    const [contextData, setContextData] = useState({ nodes: [], links: [] });
    const [selectedNode, setSelectedNode] = useState(null);
    const [selectedRelationship, setSelectedRelationship] = useState(null);
    const [mapLayout, setMapLayout] = useState('force'); // force, hierarchical, circular
    const [filterOptions, setFilterOptions] = useState({
        showWorkflowContext: true,
        showAgentMemory: true,
        showConversations: true,
        relationshipTypes: ['all']
    });
    
    const width = 800;
    const height = 600;
    
    useEffect(() => {
        loadContextRelationships();
    }, [agentId, workflowId, filterOptions]);
    
    useEffect(() => {
        if (contextData.nodes.length > 0) {
            renderContextMap();
        }
    }, [contextData, mapLayout]);
    
    return (
        <div className="context-relationship-map">
            <div className="map-header">
                <h4><i className="fas fa-project-diagram"></i> Context Relationships</h4>
                <ContextMapControls
                    mapLayout={mapLayout}
                    onLayoutChange={setMapLayout}
                    onRefresh={loadContextRelationships}
                    onExport={handleExportMap}
                />
            </div>
            
            <ContextFilters
                filterOptions={filterOptions}
                onFilterChange={setFilterOptions}
            />
            
            <div className="map-container">
                <svg
                    ref={svgRef}
                    width={width}
                    height={height}
                    className="context-map-svg"
                />
                
                <div className="map-legend">
                    <ContextMapLegend />
                </div>
            </div>
            
            {selectedNode && (
                <RelationshipDetails
                    node={selectedNode}
                    onClose={() => setSelectedNode(null)}
                />
            )}
        </div>
    );
};
```

#### Context Map Rendering Logic
```jsx
const renderContextMap = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove();
    
    // Create simulation based on layout type
    let simulation;
    
    switch (mapLayout) {
        case 'force':
            simulation = createForceLayout();
            break;
        case 'hierarchical':
            simulation = createHierarchicalLayout();
            break;
        case 'circular':
            simulation = createCircularLayout();
            break;
        default:
            simulation = createForceLayout();
    }
    
    // Create main group
    const g = svg.append("g");
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([0.1, 4])
        .on("zoom", (event) => {
            g.attr("transform", event.transform);
        });
    
    svg.call(zoom);
    
    // Render links (relationships)
    const links = g.selectAll(".relationship-link")
        .data(contextData.links)
        .enter().append("line")
        .attr("class", "relationship-link")
        .attr("stroke", d => getRelationshipColor(d.type))
        .attr("stroke-width", d => getRelationshipWidth(d.strength))
        .attr("stroke-dasharray", d => getRelationshipDash(d.type))
        .style("opacity", 0.7);
    
    // Render nodes (context entities)
    const nodes = g.selectAll(".context-node")
        .data(contextData.nodes)
        .enter().append("g")
        .attr("class", "context-node")
        .style("cursor", "pointer")
        .call(d3.drag()
            .on("start", dragStarted)
            .on("drag", dragged)
            .on("end", dragEnded))
        .on("click", handleNodeClick)
        .on("mouseover", handleNodeHover)
        .on("mouseout", handleNodeLeave);
    
    // Add node circles
    nodes.append("circle")
        .attr("r", d => getNodeRadius(d.type, d.size))
        .attr("fill", d => getNodeColor(d.type))
        .attr("stroke", "#fff")
        .attr("stroke-width", 2);
    
    // Add node icons
    nodes.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", "0.35em")
        .attr("font-family", "FontAwesome")
        .attr("font-size", d => getNodeRadius(d.type, d.size) * 0.6)
        .attr("fill", "#fff")
        .text(d => getNodeIcon(d.type));
    
    // Add node labels
    nodes.append("text")
        .attr("text-anchor", "middle")
        .attr("dy", d => getNodeRadius(d.type, d.size) + 15)
        .attr("font-size", "12px")
        .attr("fill", "#333")
        .text(d => d.label);
    
    // Update positions on simulation tick
    simulation.on("tick", () => {
        links
            .attr("x1", d => d.source.x)
            .attr("y1", d => d.source.y)
            .attr("x2", d => d.target.x)
            .attr("y2", d => d.target.y);
        
        nodes.attr("transform", d => `translate(${d.x},${d.y})`);
    });
    
    simulation.nodes(contextData.nodes);
    simulation.force("link").links(contextData.links);
};

const createForceLayout = () => {
    return d3.forceSimulation()
        .force("link", d3.forceLink().id(d => d.id).distance(100))
        .force("charge", d3.forceManyBody().strength(-300))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(d => getNodeRadius(d.type, d.size) + 5));
};
```

#### Node and Relationship Styling
```jsx
const getNodeColor = (nodeType) => {
    const colors = {
        'agent': '#007bff',
        'conversation': '#28a745',
        'workflow': '#ffc107',
        'context_shared': '#17a2b8',
        'memory_store': '#6f42c1'
    };
    return colors[nodeType] || '#6c757d';
};

const getNodeRadius = (nodeType, size) => {
    const baseRadius = {
        'agent': 25,
        'conversation': 20,
        'workflow': 22,
        'context_shared': 18,
        'memory_store': 15
    };
    
    const sizeMultiplier = Math.sqrt(size || 1) * 0.5 + 0.5;
    return (baseRadius[nodeType] || 20) * sizeMultiplier;
};

const getNodeIcon = (nodeType) => {
    const icons = {
        'agent': '\uf544', // fa-robot
        'conversation': '\uf086', // fa-comments
        'workflow': '\uf542', // fa-project-diagram
        'context_shared': '\uf1e0', // fa-share-alt
        'memory_store': '\uf1c0'  // fa-database
    };
    return icons[nodeType] || '\uf059'; // fa-question-circle
};

const getRelationshipColor = (relationshipType) => {
    const colors = {
        'shares_context': '#28a745',
        'memory_reference': '#007bff',
        'workflow_dependency': '#ffc107',
        'conversation_participant': '#17a2b8',
        'config_inheritance': '#6f42c1'
    };
    return colors[relationshipType] || '#6c757d';
};

const getRelationshipWidth = (strength) => {
    return Math.max(1, Math.min(5, strength * 3));
};

const getRelationshipDash = (relationshipType) => {
    const patterns = {
        'shares_context': '0',
        'memory_reference': '5,5',
        'workflow_dependency': '10,5',
        'conversation_participant': '2,3',
        'config_inheritance': '8,2,2,2'
    };
    return patterns[relationshipType] || '0';
};
```

### Context Map Controls
```jsx
// ContextMapControls.jsx
const ContextMapControls = ({ mapLayout, onLayoutChange, onRefresh, onExport }) => {
    const layouts = [
        { value: 'force', label: 'Force Layout', icon: 'fas fa-atom' },
        { value: 'hierarchical', label: 'Hierarchical', icon: 'fas fa-sitemap' },
        { value: 'circular', label: 'Circular', icon: 'fas fa-circle-notch' }
    ];
    
    return (
        <div className="context-map-controls">
            <div className="layout-selector">
                <label>Layout:</label>
                <div className="btn-group" role="group">
                    {layouts.map(layout => (
                        <button
                            key={layout.value}
                            type="button"
                            className={`btn btn-sm ${mapLayout === layout.value ? 'btn-primary' : 'btn-outline-primary'}`}
                            onClick={() => onLayoutChange(layout.value)}
                            title={layout.label}
                        >
                            <i className={layout.icon}></i>
                        </button>
                    ))}
                </div>
            </div>
            
            <div className="map-actions">
                <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={onRefresh}
                    title="Refresh map"
                >
                    <i className="fas fa-sync-alt"></i>
                </button>
                
                <button 
                    className="btn btn-sm btn-outline-info"
                    onClick={onExport}
                    title="Export map"
                >
                    <i className="fas fa-download"></i>
                </button>
            </div>
        </div>
    );
};
```

### Context Filters Component
```jsx
// ContextFilters.jsx
const ContextFilters = ({ filterOptions, onFilterChange }) => {
    const handleFilterToggle = (filterKey) => {
        onFilterChange({
            ...filterOptions,
            [filterKey]: !filterOptions[filterKey]
        });
    };
    
    const handleRelationshipTypeChange = (relationshipType) => {
        const currentTypes = filterOptions.relationshipTypes;
        let newTypes;
        
        if (relationshipType === 'all') {
            newTypes = ['all'];
        } else {
            newTypes = currentTypes.includes('all')
                ? [relationshipType]
                : currentTypes.includes(relationshipType)
                    ? currentTypes.filter(t => t !== relationshipType)
                    : [...currentTypes, relationshipType];
        }
        
        onFilterChange({
            ...filterOptions,
            relationshipTypes: newTypes.length === 0 ? ['all'] : newTypes
        });
    };
    
    return (
        <div className="context-filters">
            <div className="filter-section">
                <label>Show Context Types:</label>
                <div className="filter-checkboxes">
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={filterOptions.showWorkflowContext}
                            onChange={() => handleFilterToggle('showWorkflowContext')}
                        />
                        <span className="context-type-indicator workflow"></span>
                        Workflow Context
                    </label>
                    
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={filterOptions.showAgentMemory}
                            onChange={() => handleFilterToggle('showAgentMemory')}
                        />
                        <span className="context-type-indicator agent"></span>
                        Agent Memory
                    </label>
                    
                    <label className="checkbox-label">
                        <input
                            type="checkbox"
                            checked={filterOptions.showConversations}
                            onChange={() => handleFilterToggle('showConversations')}
                        />
                        <span className="context-type-indicator conversation"></span>
                        Conversations
                    </label>
                </div>
            </div>
            
            <div className="filter-section">
                <label>Relationship Types:</label>
                <div className="relationship-filters">
                    {['all', 'shares_context', 'memory_reference', 'workflow_dependency', 'conversation_participant'].map(type => (
                        <button
                            key={type}
                            className={`btn btn-xs relationship-filter ${
                                filterOptions.relationshipTypes.includes(type) ? 'active' : ''
                            }`}
                            onClick={() => handleRelationshipTypeChange(type)}
                        >
                            {type.replace('_', ' ')}
                        </button>
                    ))}
                </div>
            </div>
        </div>
    );
};
```

### Relationship Details Panel
```jsx
// RelationshipDetails.jsx
const RelationshipDetails = ({ node, onClose }) => {
    const [nodeDetails, setNodeDetails] = useState(null);
    const [relatedNodes, setRelatedNodes] = useState([]);
    
    useEffect(() => {
        loadNodeDetails(node.id);
    }, [node]);
    
    const loadNodeDetails = async (nodeId) => {
        try {
            const response = await fetch(`/api/memory/context/nodes/${nodeId}/details`);
            const data = await response.json();
            setNodeDetails(data.details);
            setRelatedNodes(data.related_nodes);
        } catch (error) {
            console.error('Error loading node details:', error);
        }
    };
    
    return (
        <div className="relationship-details-panel">
            <div className="panel-header">
                <h5>
                    <i className={`fas ${getNodeIcon(node.type)}`}></i>
                    {node.label}
                </h5>
                <button 
                    className="btn btn-sm btn-outline-secondary"
                    onClick={onClose}
                >
                    <i className="fas fa-times"></i>
                </button>
            </div>
            
            <div className="panel-content">
                <div className="node-info">
                    <div className="info-row">
                        <strong>Type:</strong> {node.type}
                    </div>
                    <div className="info-row">
                        <strong>Size:</strong> {formatSize(node.size)}
                    </div>
                    <div className="info-row">
                        <strong>Last Updated:</strong> {formatTimestamp(node.lastUpdated)}
                    </div>
                </div>
                
                {nodeDetails && (
                    <div className="node-details">
                        <h6>Details</h6>
                        <pre className="details-content">
                            {JSON.stringify(nodeDetails, null, 2)}
                        </pre>
                    </div>
                )}
                
                <div className="related-nodes">
                    <h6>Related Nodes ({relatedNodes.length})</h6>
                    <div className="related-nodes-list">
                        {relatedNodes.map(relatedNode => (
                            <div key={relatedNode.id} className="related-node-item">
                                <i className={`fas ${getNodeIcon(relatedNode.type)}`}></i>
                                <span>{relatedNode.label}</span>
                                <span className="relationship-type">
                                    {relatedNode.relationshipType}
                                </span>
                            </div>
                        ))}
                    </div>
                </div>
            </div>
        </div>
    );
};
```

## Data Processing and API Integration

### Context Relationship Data Service
```javascript
// contextRelationshipService.js
class ContextRelationshipService {
    async getContextRelationships(agentId, workflowId = null, filters = {}) {
        const params = new URLSearchParams({
            agent_id: agentId,
            ...(workflowId && { workflow_id: workflowId }),
            ...filters
        });
        
        const response = await fetch(`/api/memory/context/relationships?${params}`);
        const data = await response.json();
        
        return {
            nodes: this.processNodes(data.nodes),
            links: this.processLinks(data.links)
        };
    }
    
    processNodes(rawNodes) {
        return rawNodes.map(node => ({
            id: node.id,
            label: node.name || node.id,
            type: node.type,
            size: node.memory_size_mb || 1,
            lastUpdated: new Date(node.last_updated),
            metadata: node.metadata || {}
        }));
    }
    
    processLinks(rawLinks) {
        return rawLinks.map(link => ({
            source: link.source_id,
            target: link.target_id,
            type: link.relationship_type,
            strength: link.strength || 1,
            metadata: link.metadata || {}
        }));
    }
    
    async getNodeDetails(nodeId) {
        const response = await fetch(`/api/memory/context/nodes/${nodeId}/details`);
        return await response.json();
    }
    
    async exportContextMap(agentId, format = 'json') {
        const response = await fetch(`/api/memory/context/export`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                agent_id: agentId,
                format: format
            })
        });
        return await response.json();
    }
}

export const contextRelationshipService = new ContextRelationshipService();
```

## Implementation Steps

### Step 1: Core Visualization (Day 1-2)
1. Create main `ContextRelationshipMap` component
2. Implement D3.js force-directed layout
3. Add basic node and link rendering
4. Create node interaction handlers

### Step 2: Layout Options (Day 2-3)
1. Implement hierarchical layout algorithm
2. Add circular layout option
3. Create layout switching controls
4. Optimize layout performance

### Step 3: Interactive Features (Day 3)
1. Add context filtering capabilities
2. Implement node details panel
3. Create relationship type filtering
4. Add map export functionality

### Step 4: Advanced Features (Day 4)
1. Add context search and highlighting
2. Implement relationship strength visualization
3. Create context comparison mode
4. Add accessibility features

## Styling and CSS

### Context Map Styles
```css
/* context-relationship-map.css */
.context-relationship-map {
    background: #fff;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.map-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #dee2e6;
}

.context-map-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.layout-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.context-filters {
    display: flex;
    gap: 2rem;
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 4px;
}

.filter-section {
    display: flex;
    flex-direction: column;
    gap: 0.5rem;
}

.filter-checkboxes {
    display: flex;
    gap: 1rem;
}

.checkbox-label {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    cursor: pointer;
}

.context-type-indicator {
    width: 12px;
    height: 12px;
    border-radius: 50%;
    display: inline-block;
}

.context-type-indicator.workflow { background: #ffc107; }
.context-type-indicator.agent { background: #007bff; }
.context-type-indicator.conversation { background: #28a745; }

.map-container {
    position: relative;
    border: 1px solid #dee2e6;
    border-radius: 4px;
    overflow: hidden;
}

.context-map-svg {
    background: #fafafa;
}

.context-node {
    transition: all 0.2s;
}

.context-node:hover {
    filter: brightness(1.1);
}

.relationship-link {
    transition: opacity 0.2s;
}

.relationship-link:hover {
    opacity: 1 !important;
    stroke-width: 3px;
}

.map-legend {
    position: absolute;
    top: 10px;
    right: 10px;
    background: rgba(255, 255, 255, 0.9);
    padding: 0.75rem;
    border-radius: 4px;
    font-size: 0.875rem;
}

.relationship-details-panel {
    position: absolute;
    top: 0;
    right: 0;
    width: 300px;
    height: 100%;
    background: #fff;
    border-left: 1px solid #dee2e6;
    display: flex;
    flex-direction: column;
}

.panel-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 1rem;
    border-bottom: 1px solid #dee2e6;
    background: #f8f9fa;
}

.panel-content {
    flex: 1;
    padding: 1rem;
    overflow-y: auto;
}

.node-info {
    margin-bottom: 1rem;
}

.info-row {
    margin-bottom: 0.5rem;
}

.details-content {
    background: #f8f9fa;
    padding: 0.5rem;
    border-radius: 4px;
    font-size: 0.75rem;
    max-height: 200px;
    overflow-y: auto;
}

.related-nodes-list {
    max-height: 200px;
    overflow-y: auto;
}

.related-node-item {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.5rem;
    border-bottom: 1px solid #f0f0f0;
}

.relationship-type {
    margin-left: auto;
    font-size: 0.75rem;
    color: #6c757d;
    font-style: italic;
}
```

## Testing Requirements

### Component Tests
```javascript
// __tests__/ContextRelationshipMap.test.js
describe('ContextRelationshipMap', () => {
    test('renders context map with nodes and links', () => {
        // Test basic rendering
    });
    
    test('switches between layout types', () => {
        // Test layout switching
    });
    
    test('filters nodes by context type', () => {
        // Test filtering functionality
    });
    
    test('shows node details on click', () => {
        // Test node interaction
    });
});
```

## Success Criteria

### Functional Requirements
- [ ] Visual representation of context relationships
- [ ] Multiple layout algorithms (force, hierarchical, circular)
- [ ] Interactive node and relationship exploration
- [ ] Context type and relationship filtering
- [ ] Detailed node information panels

### Performance Requirements
- [ ] Map renders within 2 seconds for 100+ nodes
- [ ] Smooth layout transitions and interactions
- [ ] Efficient filtering and search operations
- [ ] Responsive design for various screen sizes

### User Experience Requirements
- [ ] Intuitive visual design and navigation
- [ ] Clear relationship type indicators
- [ ] Informative tooltips and details
- [ ] Accessible keyboard navigation

## Related Files
- `src/swarm_director/web/static/js/components/ContextRelationshipMap.jsx` - Main component
- `src/swarm_director/web/static/css/context-relationship-map.css` - Map styles
- `src/swarm_director/web/static/js/services/contextRelationshipService.js` - Data service
- `src/swarm_director/api/context_relationship_routes.py` - API endpoints
