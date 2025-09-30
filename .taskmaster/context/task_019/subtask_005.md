# Memory Timeline Visualization

## Subtask Metadata
```yaml
subtask_id: "subtask_005"
parent_task: "task_019"
title: "Memory Timeline Visualization"
type: "frontend_development"
priority: "medium"
estimated_effort: "3-4 days"
complexity: "high"
dependencies:
  - subtask_001
  - subtask_002
  - subtask_004
assignee: "frontend_developer"
status: "blocked"
```

## Objective

Create an interactive timeline visualization component that displays agent memory changes over time, enabling developers to track memory evolution, identify patterns, and debug memory-related issues through visual analysis.

## Technical Specifications

### Timeline Component Architecture

#### Main Timeline Component
```jsx
// src/swarm_director/web/static/js/components/MemoryTimeline.jsx
import React, { useState, useEffect, useRef } from 'react';
import * as d3 from 'd3';
import { TimelineControls } from './TimelineControls';
import { MemoryChangeTooltip } from './MemoryChangeTooltip';
import { TimelineFilters } from './TimelineFilters';

const MemoryTimeline = ({ agentId, height = 400 }) => {
    const svgRef = useRef();
    const [timelineData, setTimelineData] = useState([]);
    const [selectedTimeRange, setSelectedTimeRange] = useState('24h');
    const [selectedChangeTypes, setSelectedChangeTypes] = useState(['all']);
    const [hoveredEvent, setHoveredEvent] = useState(null);
    const [isLoading, setIsLoading] = useState(true);
    
    // Timeline dimensions and scales
    const margin = { top: 20, right: 30, bottom: 40, left: 60 };
    const width = 800 - margin.left - margin.right;
    const innerHeight = height - margin.top - margin.bottom;
    
    useEffect(() => {
        loadTimelineData();
    }, [agentId, selectedTimeRange, selectedChangeTypes]);
    
    useEffect(() => {
        if (timelineData.length > 0) {
            renderTimeline();
        }
    }, [timelineData]);
    
    return (
        <div className="memory-timeline">
            <div className="timeline-header">
                <h4><i className="fas fa-chart-line"></i> Memory Timeline</h4>
                <TimelineControls
                    selectedTimeRange={selectedTimeRange}
                    onTimeRangeChange={setSelectedTimeRange}
                    onRefresh={loadTimelineData}
                />
            </div>
            
            <TimelineFilters
                selectedChangeTypes={selectedChangeTypes}
                onChangeTypesChange={setSelectedChangeTypes}
            />
            
            <div className="timeline-container">
                <svg
                    ref={svgRef}
                    width={width + margin.left + margin.right}
                    height={height}
                    className="timeline-svg"
                />
                
                {hoveredEvent && (
                    <MemoryChangeTooltip
                        event={hoveredEvent}
                        position={hoveredEvent.position}
                    />
                )}
            </div>
            
            {isLoading && (
                <div className="timeline-loading">
                    <div className="spinner-border" role="status">
                        <span className="sr-only">Loading timeline...</span>
                    </div>
                </div>
            )}
        </div>
    );
};
```

#### Timeline Rendering Logic
```jsx
const renderTimeline = () => {
    const svg = d3.select(svgRef.current);
    svg.selectAll("*").remove(); // Clear previous render
    
    // Create scales
    const xScale = d3.scaleTime()
        .domain(d3.extent(timelineData, d => new Date(d.timestamp)))
        .range([0, width]);
    
    const yScale = d3.scaleLinear()
        .domain([0, d3.max(timelineData, d => d.memory_size_mb)])
        .range([innerHeight, 0]);
    
    const colorScale = d3.scaleOrdinal()
        .domain(['conversation_message', 'workflow_context_update', 'agent_config_change', 'memory_reset'])
        .range(['#007bff', '#28a745', '#ffc107', '#dc3545']);
    
    // Create main group
    const g = svg.append("g")
        .attr("transform", `translate(${margin.left},${margin.top})`);
    
    // Add axes
    g.append("g")
        .attr("transform", `translate(0,${innerHeight})`)
        .call(d3.axisBottom(xScale).tickFormat(d3.timeFormat("%H:%M")));
    
    g.append("g")
        .call(d3.axisLeft(yScale));
    
    // Add axis labels
    g.append("text")
        .attr("transform", "rotate(-90)")
        .attr("y", 0 - margin.left)
        .attr("x", 0 - (innerHeight / 2))
        .attr("dy", "1em")
        .style("text-anchor", "middle")
        .text("Memory Size (MB)");
    
    g.append("text")
        .attr("transform", `translate(${width / 2}, ${innerHeight + margin.bottom})`)
        .style("text-anchor", "middle")
        .text("Time");
    
    // Add memory size line
    const line = d3.line()
        .x(d => xScale(new Date(d.timestamp)))
        .y(d => yScale(d.memory_size_mb))
        .curve(d3.curveMonotoneX);
    
    g.append("path")
        .datum(timelineData)
        .attr("fill", "none")
        .attr("stroke", "#6c757d")
        .attr("stroke-width", 2)
        .attr("d", line);
    
    // Add change events
    g.selectAll(".change-event")
        .data(timelineData.filter(d => d.change_type !== 'baseline'))
        .enter().append("circle")
        .attr("class", "change-event")
        .attr("cx", d => xScale(new Date(d.timestamp)))
        .attr("cy", d => yScale(d.memory_size_mb))
        .attr("r", 6)
        .attr("fill", d => colorScale(d.change_type))
        .attr("stroke", "#fff")
        .attr("stroke-width", 2)
        .style("cursor", "pointer")
        .on("mouseover", handleEventHover)
        .on("mouseout", handleEventLeave)
        .on("click", handleEventClick);
    
    // Add zoom behavior
    const zoom = d3.zoom()
        .scaleExtent([1, 10])
        .on("zoom", handleZoom);
    
    svg.call(zoom);
};
```

### Timeline Controls Component
```jsx
// TimelineControls.jsx
const TimelineControls = ({ selectedTimeRange, onTimeRangeChange, onRefresh }) => {
    const timeRanges = [
        { value: '1h', label: '1 Hour' },
        { value: '6h', label: '6 Hours' },
        { value: '24h', label: '24 Hours' },
        { value: '7d', label: '7 Days' },
        { value: '30d', label: '30 Days' }
    ];
    
    return (
        <div className="timeline-controls">
            <div className="time-range-selector">
                <label>Time Range:</label>
                <select 
                    value={selectedTimeRange}
                    onChange={(e) => onTimeRangeChange(e.target.value)}
                    className="form-select form-select-sm"
                >
                    {timeRanges.map(range => (
                        <option key={range.value} value={range.value}>
                            {range.label}
                        </option>
                    ))}
                </select>
            </div>
            
            <button 
                className="btn btn-sm btn-outline-primary"
                onClick={onRefresh}
                title="Refresh timeline"
            >
                <i className="fas fa-sync-alt"></i>
            </button>
        </div>
    );
};
```

### Timeline Filters Component
```jsx
// TimelineFilters.jsx
const TimelineFilters = ({ selectedChangeTypes, onChangeTypesChange }) => {
    const changeTypes = [
        { value: 'all', label: 'All Changes', color: '#6c757d' },
        { value: 'conversation_message', label: 'Messages', color: '#007bff' },
        { value: 'workflow_context_update', label: 'Workflow', color: '#28a745' },
        { value: 'agent_config_change', label: 'Config', color: '#ffc107' },
        { value: 'memory_reset', label: 'Reset', color: '#dc3545' }
    ];
    
    const handleFilterChange = (changeType) => {
        if (changeType === 'all') {
            onChangeTypesChange(['all']);
        } else {
            const newTypes = selectedChangeTypes.includes('all') 
                ? [changeType]
                : selectedChangeTypes.includes(changeType)
                    ? selectedChangeTypes.filter(t => t !== changeType)
                    : [...selectedChangeTypes.filter(t => t !== 'all'), changeType];
            
            onChangeTypesChange(newTypes.length === 0 ? ['all'] : newTypes);
        }
    };
    
    return (
        <div className="timeline-filters">
            <label>Show Changes:</label>
            <div className="filter-buttons">
                {changeTypes.map(type => (
                    <button
                        key={type.value}
                        className={`btn btn-sm filter-btn ${
                            selectedChangeTypes.includes(type.value) ? 'active' : ''
                        }`}
                        style={{ 
                            borderColor: type.color,
                            backgroundColor: selectedChangeTypes.includes(type.value) ? type.color : 'transparent',
                            color: selectedChangeTypes.includes(type.value) ? '#fff' : type.color
                        }}
                        onClick={() => handleFilterChange(type.value)}
                    >
                        <span 
                            className="filter-color-dot"
                            style={{ backgroundColor: type.color }}
                        ></span>
                        {type.label}
                    </button>
                ))}
            </div>
        </div>
    );
};
```

### Memory Change Tooltip
```jsx
// MemoryChangeTooltip.jsx
const MemoryChangeTooltip = ({ event, position }) => {
    const formatTimestamp = (timestamp) => {
        return new Date(timestamp).toLocaleString();
    };
    
    const formatMemorySize = (sizeMb) => {
        return `${sizeMb.toFixed(2)} MB`;
    };
    
    const getChangeTypeIcon = (changeType) => {
        const icons = {
            'conversation_message': 'fas fa-comment',
            'workflow_context_update': 'fas fa-project-diagram',
            'agent_config_change': 'fas fa-cog',
            'memory_reset': 'fas fa-trash-restore'
        };
        return icons[changeType] || 'fas fa-info-circle';
    };
    
    return (
        <div 
            className="memory-change-tooltip"
            style={{
                position: 'absolute',
                left: position.x + 10,
                top: position.y - 10,
                zIndex: 1000
            }}
        >
            <div className="tooltip-header">
                <i className={getChangeTypeIcon(event.change_type)}></i>
                <span className="change-type">{event.change_type.replace('_', ' ')}</span>
            </div>
            
            <div className="tooltip-content">
                <div className="tooltip-row">
                    <strong>Time:</strong> {formatTimestamp(event.timestamp)}
                </div>
                <div className="tooltip-row">
                    <strong>Memory Size:</strong> {formatMemorySize(event.memory_size_mb)}
                </div>
                {event.memory_delta_mb && (
                    <div className="tooltip-row">
                        <strong>Change:</strong> 
                        <span className={event.memory_delta_mb > 0 ? 'positive' : 'negative'}>
                            {event.memory_delta_mb > 0 ? '+' : ''}{formatMemorySize(event.memory_delta_mb)}
                        </span>
                    </div>
                )}
                {event.trigger_source && (
                    <div className="tooltip-row">
                        <strong>Trigger:</strong> {event.trigger_source}
                    </div>
                )}
            </div>
            
            <div className="tooltip-actions">
                <button 
                    className="btn btn-xs btn-outline-primary"
                    onClick={() => handleViewDetails(event)}
                >
                    View Details
                </button>
            </div>
        </div>
    );
};
```

## Advanced Timeline Features

### Memory Comparison Mode
```jsx
// MemoryComparisonTimeline.jsx
const MemoryComparisonTimeline = ({ agentIds, height = 400 }) => {
    const [comparisonData, setComparisonData] = useState({});
    const [selectedAgents, setSelectedAgents] = useState(agentIds);
    
    const renderComparisonTimeline = () => {
        // Render multiple agent memory timelines for comparison
        const svg = d3.select(svgRef.current);
        
        // Create separate y-scales for each agent
        const agentScales = {};
        selectedAgents.forEach(agentId => {
            agentScales[agentId] = d3.scaleLinear()
                .domain([0, d3.max(comparisonData[agentId] || [], d => d.memory_size_mb)])
                .range([innerHeight, 0]);
        });
        
        // Render lines for each agent with different colors
        selectedAgents.forEach((agentId, index) => {
            const color = d3.schemeCategory10[index % 10];
            const data = comparisonData[agentId] || [];
            
            const line = d3.line()
                .x(d => xScale(new Date(d.timestamp)))
                .y(d => agentScales[agentId](d.memory_size_mb))
                .curve(d3.curveMonotoneX);
            
            g.append("path")
                .datum(data)
                .attr("fill", "none")
                .attr("stroke", color)
                .attr("stroke-width", 2)
                .attr("class", `agent-line agent-${agentId}`);
        });
    };
    
    return (
        <div className="memory-comparison-timeline">
            {/* Comparison timeline implementation */}
        </div>
    );
};
```

### Timeline Annotations
```jsx
// TimelineAnnotations.jsx
const TimelineAnnotations = ({ annotations, xScale, yScale }) => {
    return (
        <g className="timeline-annotations">
            {annotations.map((annotation, index) => (
                <g key={index} className="annotation">
                    <line
                        x1={xScale(new Date(annotation.timestamp))}
                        y1={0}
                        x2={xScale(new Date(annotation.timestamp))}
                        y2={yScale.range()[0]}
                        stroke="#dc3545"
                        strokeWidth={2}
                        strokeDasharray="5,5"
                    />
                    <text
                        x={xScale(new Date(annotation.timestamp))}
                        y={-5}
                        textAnchor="middle"
                        className="annotation-text"
                    >
                        {annotation.label}
                    </text>
                </g>
            ))}
        </g>
    );
};
```

## Implementation Steps

### Step 1: Basic Timeline Structure (Day 1)
1. Create main `MemoryTimeline` component
2. Implement D3.js timeline rendering
3. Add basic time and memory size axes
4. Create memory size line chart

### Step 2: Interactive Features (Day 2)
1. Add timeline controls for time range selection
2. Implement change type filtering
3. Create hover tooltips for memory events
4. Add zoom and pan functionality

### Step 3: Advanced Visualizations (Day 3)
1. Implement memory change event markers
2. Add timeline annotations for significant events
3. Create memory comparison mode for multiple agents
4. Add timeline export functionality

### Step 4: Performance and Polish (Day 4)
1. Optimize rendering for large datasets
2. Add loading states and error handling
3. Implement responsive design
4. Add accessibility features

## Styling and CSS

### Timeline Styles
```css
/* memory-timeline.css */
.memory-timeline {
    background: #fff;
    border-radius: 8px;
    padding: 1rem;
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.timeline-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid #dee2e6;
}

.timeline-controls {
    display: flex;
    align-items: center;
    gap: 1rem;
}

.time-range-selector {
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.timeline-filters {
    margin-bottom: 1rem;
    padding: 0.75rem;
    background: #f8f9fa;
    border-radius: 4px;
}

.filter-buttons {
    display: flex;
    gap: 0.5rem;
    flex-wrap: wrap;
}

.filter-btn {
    display: flex;
    align-items: center;
    gap: 0.25rem;
    transition: all 0.2s;
}

.filter-color-dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    display: inline-block;
}

.timeline-container {
    position: relative;
    overflow: hidden;
}

.timeline-svg {
    border: 1px solid #dee2e6;
    border-radius: 4px;
}

.change-event {
    transition: r 0.2s;
}

.change-event:hover {
    r: 8;
}

.memory-change-tooltip {
    background: rgba(0, 0, 0, 0.9);
    color: white;
    padding: 0.75rem;
    border-radius: 6px;
    font-size: 0.875rem;
    max-width: 250px;
    box-shadow: 0 4px 8px rgba(0,0,0,0.2);
}

.tooltip-header {
    display: flex;
    align-items: center;
    gap: 0.5rem;
    margin-bottom: 0.5rem;
    font-weight: bold;
}

.tooltip-row {
    margin-bottom: 0.25rem;
}

.tooltip-row .positive {
    color: #28a745;
}

.tooltip-row .negative {
    color: #dc3545;
}

.tooltip-actions {
    margin-top: 0.5rem;
    padding-top: 0.5rem;
    border-top: 1px solid rgba(255,255,255,0.2);
}

.timeline-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
}
```

## Data Processing and API Integration

### Timeline Data Service
```javascript
// timelineDataService.js
class TimelineDataService {
    async getMemoryTimeline(agentId, timeRange = '24h', changeTypes = ['all']) {
        const params = new URLSearchParams({
            range: timeRange,
            change_types: changeTypes.join(',')
        });
        
        const response = await fetch(
            `/api/memory/agents/${agentId}/timeline?${params}`
        );
        
        const data = await response.json();
        return this.processTimelineData(data.timeline);
    }
    
    processTimelineData(rawData) {
        return rawData.map(event => ({
            ...event,
            timestamp: new Date(event.timestamp),
            memory_size_mb: parseFloat(event.memory_size_mb),
            memory_delta_mb: parseFloat(event.memory_delta_mb || 0)
        }));
    }
    
    async getTimelineAnnotations(agentId, timeRange) {
        const response = await fetch(
            `/api/memory/agents/${agentId}/annotations?range=${timeRange}`
        );
        return await response.json();
    }
}

export const timelineDataService = new TimelineDataService();
```

## Testing Requirements

### Component Tests
```javascript
// __tests__/MemoryTimeline.test.js
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryTimeline } from '../MemoryTimeline';

describe('MemoryTimeline', () => {
    test('renders timeline with correct dimensions', () => {
        render(<MemoryTimeline agentId={123} height={400} />);
        const svg = screen.getByRole('img');
        expect(svg).toHaveAttribute('height', '400');
    });
    
    test('loads timeline data on mount', async () => {
        // Mock timeline data
        global.fetch = jest.fn(() =>
            Promise.resolve({
                json: () => Promise.resolve({ timeline: mockTimelineData })
            })
        );
        
        render(<MemoryTimeline agentId={123} />);
        
        await waitFor(() => {
            expect(screen.getByText(/Memory Timeline/)).toBeInTheDocument();
        });
    });
    
    test('filters timeline by change type', () => {
        // Test filtering functionality
    });
    
    test('handles timeline zoom and pan', () => {
        // Test zoom/pan interactions
    });
});
```

## Success Criteria

### Functional Requirements
- [ ] Interactive timeline showing memory changes over time
- [ ] Filterable by change type and time range
- [ ] Hover tooltips with detailed change information
- [ ] Zoom and pan functionality for detailed analysis
- [ ] Memory size trend visualization

### Performance Requirements
- [ ] Timeline renders within 1 second for 1000+ events
- [ ] Smooth zoom and pan interactions
- [ ] Efficient data processing for large datasets
- [ ] Responsive updates when filters change

### User Experience Requirements
- [ ] Intuitive timeline navigation
- [ ] Clear visual distinction between change types
- [ ] Informative tooltips and annotations
- [ ] Responsive design for various screen sizes

## Related Files
- `src/swarm_director/web/static/js/components/MemoryTimeline.jsx` - Main component
- `src/swarm_director/web/static/css/memory-timeline.css` - Timeline styles
- `src/swarm_director/web/static/js/services/timelineDataService.js` - Data service
- `src/swarm_director/api/memory_timeline_routes.py` - Timeline API endpoints
