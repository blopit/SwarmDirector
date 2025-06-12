# Web Directory

## Purpose
Contains the web interface components for the SwarmDirector application, including static assets, HTML templates, and web-specific utilities. This directory provides the user interface for monitoring, managing, and interacting with the hierarchical AI agent management system through a modern web dashboard.

## Structure
```
web/
├── __init__.py                  # Web package initialization
├── static/                      # Static assets (CSS, JS, images)
│   ├── css/                     # Stylesheets
│   │   ├── main.css             # Main application styles
│   │   ├── dashboard.css        # Dashboard-specific styles
│   │   └── components.css       # Reusable component styles
│   ├── js/                      # JavaScript files
│   │   ├── main.js              # Main application JavaScript
│   │   ├── dashboard.js         # Dashboard functionality
│   │   ├── api-client.js        # API client utilities
│   │   └── components/          # Reusable JavaScript components
│   ├── images/                  # Image assets
│   │   ├── logo.png             # Application logo
│   │   ├── icons/               # Icon files
│   │   └── backgrounds/         # Background images
│   └── vendor/                  # Third-party libraries
│       ├── bootstrap/           # Bootstrap CSS/JS
│       ├── jquery/              # jQuery library
│       └── chart.js/            # Chart.js for visualizations
└── templates/                   # Jinja2 HTML templates
    ├── base.html                # Base template with common layout
    ├── dashboard/               # Dashboard templates
    │   ├── index.html           # Main dashboard view
    │   ├── agents.html          # Agent management interface
    │   ├── tasks.html           # Task monitoring interface
    │   └── analytics.html       # Analytics and reporting
    ├── demo/                    # Demo interface templates
    │   ├── index.html           # Demo landing page
    │   ├── chat.html            # Interactive chat interface
    │   └── workflow.html        # Workflow demonstration
    ├── api/                     # API documentation templates
    │   ├── index.html           # API documentation home
    │   └── endpoints.html       # Endpoint documentation
    └── errors/                  # Error page templates
        ├── 404.html             # Not found page
        ├── 500.html             # Server error page
        └── maintenance.html     # Maintenance mode page
```

## Guidelines

### 1. Organization
- **Asset Separation**: Keep CSS, JavaScript, and images in separate subdirectories
- **Template Hierarchy**: Use template inheritance with a base template for common layout
- **Component Reusability**: Create reusable components for common UI elements
- **Responsive Design**: Ensure all interfaces work on desktop, tablet, and mobile devices
- **Progressive Enhancement**: Build interfaces that work without JavaScript and enhance with it

### 2. Naming
- **Files**: Use lowercase with hyphens for web assets (e.g., `main.css`, `dashboard.js`)
- **Templates**: Use descriptive names matching their purpose (e.g., `agent-detail.html`)
- **CSS Classes**: Use BEM methodology (Block__Element--Modifier)
- **JavaScript Functions**: Use camelCase for function names (e.g., `updateDashboard`)
- **API Endpoints**: Use RESTful naming conventions for API routes

### 3. Implementation
- **Template Engine**: Use Jinja2 for server-side templating with proper escaping
- **CSS Framework**: Use Bootstrap 5 for responsive design and component library
- **JavaScript**: Use modern ES6+ features with appropriate polyfills
- **API Integration**: Implement proper error handling and loading states
- **Accessibility**: Follow WCAG 2.1 guidelines for web accessibility

### 4. Documentation
- **Template Documentation**: Document template variables and usage patterns
- **Component Documentation**: Document reusable components and their APIs
- **Style Guide**: Maintain a style guide for consistent UI design
- **API Documentation**: Provide interactive API documentation

## Best Practices

### 1. Error Handling
- **User-Friendly Errors**: Display clear, actionable error messages to users
- **Graceful Degradation**: Handle API failures gracefully with fallback content
- **Loading States**: Show appropriate loading indicators during async operations
- **Form Validation**: Implement client-side validation with server-side backup
- **Error Logging**: Log client-side errors for debugging and monitoring

### 2. Security
- **XSS Prevention**: Use proper template escaping and Content Security Policy
- **CSRF Protection**: Implement CSRF tokens for all forms
- **Input Sanitization**: Sanitize all user inputs on both client and server
- **Secure Headers**: Set appropriate security headers (HSTS, X-Frame-Options, etc.)
- **Authentication**: Implement proper session management and authentication

### 3. Performance
- **Asset Optimization**: Minify and compress CSS, JavaScript, and images
- **Caching**: Implement appropriate caching strategies for static assets
- **Lazy Loading**: Load images and content on demand to improve initial load time
- **Bundle Optimization**: Use webpack or similar tools for asset bundling
- **CDN Usage**: Serve static assets from CDN when possible

### 4. Testing
- **Unit Tests**: Test JavaScript functions and components
- **Integration Tests**: Test complete user workflows
- **Cross-Browser Testing**: Ensure compatibility across major browsers
- **Accessibility Testing**: Test with screen readers and accessibility tools
- **Performance Testing**: Monitor and optimize page load times

### 5. Documentation
- **Component Library**: Maintain a living style guide with component examples
- **User Documentation**: Provide help documentation and user guides
- **Developer Documentation**: Document build processes and development setup
- **API Documentation**: Keep API documentation up-to-date with interactive examples

## Example

### Complete Dashboard Implementation

```html
<!-- templates/dashboard/index.html -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SwarmDirector Dashboard</title>
    
    <!-- CSS -->
    <link href="{{ url_for('static', filename='vendor/bootstrap/css/bootstrap.min.css') }}" rel="stylesheet">
    <link href="{{ url_for('static', filename='css/dashboard.css') }}" rel="stylesheet">
    
    <!-- Security Headers -->
    <meta http-equiv="Content-Security-Policy" content="default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';">
</head>
<body>
    <!-- Navigation -->
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container-fluid">
            <a class="navbar-brand" href="{{ url_for('dashboard.index') }}">
                <img src="{{ url_for('static', filename='images/logo.png') }}" alt="SwarmDirector" height="30">
                SwarmDirector
            </a>
            
            <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav">
                <span class="navbar-toggler-icon"></span>
            </button>
            
            <div class="collapse navbar-collapse" id="navbarNav">
                <ul class="navbar-nav me-auto">
                    <li class="nav-item">
                        <a class="nav-link active" href="{{ url_for('dashboard.index') }}">Dashboard</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('dashboard.agents') }}">Agents</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('dashboard.tasks') }}">Tasks</a>
                    </li>
                    <li class="nav-item">
                        <a class="nav-link" href="{{ url_for('dashboard.analytics') }}">Analytics</a>
                    </li>
                </ul>
                
                <ul class="navbar-nav">
                    <li class="nav-item dropdown">
                        <a class="nav-link dropdown-toggle" href="#" id="userDropdown" role="button" data-bs-toggle="dropdown">
                            <i class="fas fa-user"></i> Admin
                        </a>
                        <ul class="dropdown-menu">
                            <li><a class="dropdown-item" href="{{ url_for('api.docs') }}">API Docs</a></li>
                            <li><a class="dropdown-item" href="{{ url_for('dashboard.settings') }}">Settings</a></li>
                            <li><hr class="dropdown-divider"></li>
                            <li><a class="dropdown-item" href="{{ url_for('auth.logout') }}">Logout</a></li>
                        </ul>
                    </li>
                </ul>
            </div>
        </div>
    </nav>

    <!-- Main Content -->
    <div class="container-fluid mt-4">
        <!-- System Status Cards -->
        <div class="row mb-4">
            <div class="col-md-3">
                <div class="card bg-primary text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Active Agents</h5>
                                <h2 class="mb-0" id="active-agents-count">{{ system_stats.active_agents }}</h2>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-robot fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Completed Tasks</h5>
                                <h2 class="mb-0" id="completed-tasks-count">{{ system_stats.completed_tasks }}</h2>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-check-circle fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">Pending Tasks</h5>
                                <h2 class="mb-0" id="pending-tasks-count">{{ system_stats.pending_tasks }}</h2>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-clock fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h5 class="card-title">System Health</h5>
                                <h2 class="mb-0" id="system-health">{{ system_stats.health_status }}</h2>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-heartbeat fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <!-- Charts and Analytics -->
        <div class="row mb-4">
            <div class="col-md-8">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Task Completion Trends</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="task-trends-chart" height="100"></canvas>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Agent Status Distribution</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="agent-status-chart"></canvas>
                    </div>
                </div>
            </div>
        </div>

        <!-- Recent Activity -->
        <div class="row">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Recent Tasks</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Task</th>
                                        <th>Agent</th>
                                        <th>Status</th>
                                        <th>Time</th>
                                    </tr>
                                </thead>
                                <tbody id="recent-tasks-table">
                                    {% for task in recent_tasks %}
                                    <tr>
                                        <td>
                                            <a href="{{ url_for('dashboard.task_detail', task_id=task.id) }}">
                                                {{ task.title[:30] }}{% if task.title|length > 30 %}...{% endif %}
                                            </a>
                                        </td>
                                        <td>{{ task.assigned_agent.name if task.assigned_agent else 'Unassigned' }}</td>
                                        <td>
                                            <span class="badge bg-{{ 'success' if task.status.value == 'completed' else 'warning' if task.status.value == 'pending' else 'primary' }}">
                                                {{ task.status.value.title() }}
                                            </span>
                                        </td>
                                        <td>{{ task.created_at.strftime('%H:%M') }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
            
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5 class="card-title mb-0">Agent Activity</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-sm">
                                <thead>
                                    <tr>
                                        <th>Agent</th>
                                        <th>Status</th>
                                        <th>Current Task</th>
                                        <th>Last Active</th>
                                    </tr>
                                </thead>
                                <tbody id="agent-activity-table">
                                    {% for agent in active_agents %}
                                    <tr>
                                        <td>
                                            <a href="{{ url_for('dashboard.agent_detail', agent_id=agent.id) }}">
                                                {{ agent.name }}
                                            </a>
                                        </td>
                                        <td>
                                            <span class="badge bg-{{ 'success' if agent.status.value == 'active' else 'secondary' }}">
                                                {{ agent.status.value.title() }}
                                            </span>
                                        </td>
                                        <td>
                                            {% if agent.current_task %}
                                                {{ agent.current_task.title[:20] }}{% if agent.current_task.title|length > 20 %}...{% endif %}
                                            {% else %}
                                                -
                                            {% endif %}
                                        </td>
                                        <td>{{ agent.updated_at.strftime('%H:%M') }}</td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='vendor/jquery/jquery.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/bootstrap/js/bootstrap.bundle.min.js') }}"></script>
    <script src="{{ url_for('static', filename='vendor/chart.js/chart.min.js') }}"></script>
    <script src="{{ url_for('static', filename='js/api-client.js') }}"></script>
    <script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
    
    <!-- Initialize Dashboard -->
    <script>
        document.addEventListener('DOMContentLoaded', function() {
            // Initialize dashboard with real-time updates
            Dashboard.init({
                updateInterval: 30000, // 30 seconds
                apiEndpoint: '{{ url_for("api.dashboard_data") }}',
                csrfToken: '{{ csrf_token() }}'
            });
        });
    </script>
</body>
</html>
```

### JavaScript Dashboard Controller

```javascript
// static/js/dashboard.js
/**
 * SwarmDirector Dashboard Controller
 * Handles real-time dashboard updates and user interactions
 */

class Dashboard {
    constructor(config) {
        this.config = config;
        this.charts = {};
        this.updateTimer = null;
        this.isUpdating = false;
        
        this.initializeCharts();
        this.startRealTimeUpdates();
        this.bindEventHandlers();
    }
    
    static init(config) {
        return new Dashboard(config);
    }
    
    initializeCharts() {
        // Task trends chart
        const taskTrendsCtx = document.getElementById('task-trends-chart');
        if (taskTrendsCtx) {
            this.charts.taskTrends = new Chart(taskTrendsCtx, {
                type: 'line',
                data: {
                    labels: [],
                    datasets: [{
                        label: 'Completed Tasks',
                        data: [],
                        borderColor: 'rgb(75, 192, 192)',
                        backgroundColor: 'rgba(75, 192, 192, 0.2)',
                        tension: 0.1
                    }, {
                        label: 'Failed Tasks',
                        data: [],
                        borderColor: 'rgb(255, 99, 132)',
                        backgroundColor: 'rgba(255, 99, 132, 0.2)',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true
                        }
                    }
                }
            });
        }
        
        // Agent status chart
        const agentStatusCtx = document.getElementById('agent-status-chart');
        if (agentStatusCtx) {
            this.charts.agentStatus = new Chart(agentStatusCtx, {
                type: 'doughnut',
                data: {
                    labels: ['Active', 'Idle', 'Busy', 'Error'],
                    datasets: [{
                        data: [0, 0, 0, 0],
                        backgroundColor: [
                            'rgb(40, 167, 69)',
                            'rgb(108, 117, 125)',
                            'rgb(255, 193, 7)',
                            'rgb(220, 53, 69)'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: true
                }
            });
        }
    }
    
    startRealTimeUpdates() {
        this.updateDashboard();
        this.updateTimer = setInterval(() => {
            this.updateDashboard();
        }, this.config.updateInterval);
    }
    
    async updateDashboard() {
        if (this.isUpdating) return;
        
        this.isUpdating = true;
        
        try {
            const response = await ApiClient.get('/api/v1/dashboard/data');
            
            if (response.success) {
                this.updateStatCards(response.data.stats);
                this.updateCharts(response.data.charts);
                this.updateTables(response.data.tables);
            }
        } catch (error) {
            console.error('Failed to update dashboard:', error);
            this.showError('Failed to update dashboard data');
        } finally {
            this.isUpdating = false;
        }
    }
    
    updateStatCards(stats) {
        // Update stat cards with animation
        this.animateCounter('active-agents-count', stats.active_agents);
        this.animateCounter('completed-tasks-count', stats.completed_tasks);
        this.animateCounter('pending-tasks-count', stats.pending_tasks);
        
        const healthElement = document.getElementById('system-health');
        if (healthElement) {
            healthElement.textContent = stats.health_status;
            healthElement.className = `mb-0 ${stats.health_status === 'Healthy' ? 'text-success' : 'text-warning'}`;
        }
    }
    
    updateCharts(chartData) {
        // Update task trends chart
        if (this.charts.taskTrends && chartData.task_trends) {
            this.charts.taskTrends.data.labels = chartData.task_trends.labels;
            this.charts.taskTrends.data.datasets[0].data = chartData.task_trends.completed;
            this.charts.taskTrends.data.datasets[1].data = chartData.task_trends.failed;
            this.charts.taskTrends.update('none');
        }
        
        // Update agent status chart
        if (this.charts.agentStatus && chartData.agent_status) {
            this.charts.agentStatus.data.datasets[0].data = [
                chartData.agent_status.active,
                chartData.agent_status.idle,
                chartData.agent_status.busy,
                chartData.agent_status.error
            ];
            this.charts.agentStatus.update('none');
        }
    }
    
    updateTables(tableData) {
        // Update recent tasks table
        if (tableData.recent_tasks) {
            const tbody = document.getElementById('recent-tasks-table');
            if (tbody) {
                tbody.innerHTML = tableData.recent_tasks.map(task => `
                    <tr>
                        <td><a href="/dashboard/tasks/${task.id}">${this.truncate(task.title, 30)}</a></td>
                        <td>${task.agent_name || 'Unassigned'}</td>
                        <td><span class="badge bg-${this.getStatusColor(task.status)}">${task.status}</span></td>
                        <td>${this.formatTime(task.created_at)}</td>
                    </tr>
                `).join('');
            }
        }
        
        // Update agent activity table
        if (tableData.agent_activity) {
            const tbody = document.getElementById('agent-activity-table');
            if (tbody) {
                tbody.innerHTML = tableData.agent_activity.map(agent => `
                    <tr>
                        <td><a href="/dashboard/agents/${agent.id}">${agent.name}</a></td>
                        <td><span class="badge bg-${this.getStatusColor(agent.status)}">${agent.status}</span></td>
                        <td>${agent.current_task ? this.truncate(agent.current_task, 20) : '-'}</td>
                        <td>${this.formatTime(agent.last_active)}</td>
                    </tr>
                `).join('');
            }
        }
    }
    
    animateCounter(elementId, targetValue) {
        const element = document.getElementById(elementId);
        if (!element) return;
        
        const currentValue = parseInt(element.textContent) || 0;
        const increment = (targetValue - currentValue) / 20;
        let current = currentValue;
        
        const timer = setInterval(() => {
            current += increment;
            if ((increment > 0 && current >= targetValue) || (increment < 0 && current <= targetValue)) {
                current = targetValue;
                clearInterval(timer);
            }
            element.textContent = Math.round(current);
        }, 50);
    }
    
    bindEventHandlers() {
        // Handle page visibility changes
        document.addEventListener('visibilitychange', () => {
            if (document.hidden) {
                this.pauseUpdates();
            } else {
                this.resumeUpdates();
            }
        });
        
        // Handle window focus/blur
        window.addEventListener('focus', () => this.resumeUpdates());
        window.addEventListener('blur', () => this.pauseUpdates());
    }
    
    pauseUpdates() {
        if (this.updateTimer) {
            clearInterval(this.updateTimer);
            this.updateTimer = null;
        }
    }
    
    resumeUpdates() {
        if (!this.updateTimer) {
            this.startRealTimeUpdates();
        }
    }
    
    // Utility methods
    truncate(text, length) {
        return text.length > length ? text.substring(0, length) + '...' : text;
    }
    
    getStatusColor(status) {
        const colors = {
            'completed': 'success',
            'active': 'success',
            'pending': 'warning',
            'idle': 'secondary',
            'busy': 'primary',
            'failed': 'danger',
            'error': 'danger'
        };
        return colors[status.toLowerCase()] || 'secondary';
    }
    
    formatTime(timestamp) {
        return new Date(timestamp).toLocaleTimeString('en-US', {
            hour: '2-digit',
            minute: '2-digit'
        });
    }
    
    showError(message) {
        // Show error notification (implement based on your notification system)
        console.error(message);
    }
    
    destroy() {
        this.pauseUpdates();
        
        // Destroy charts
        Object.values(this.charts).forEach(chart => {
            if (chart && typeof chart.destroy === 'function') {
                chart.destroy();
            }
        });
    }
}

// Export for use in other modules
window.Dashboard = Dashboard;
```

## Related Documentation
- [Flask Templates](../../../docs/api/README.md#templates) - Template development guide
- [API Integration](../../../docs/api/README.md) - API client implementation
- [UI Components](../../../docs/development/coding_standards.md#ui-components) - Component development standards
- [Accessibility Guide](../../../docs/development/testing.md#accessibility) - Web accessibility requirements
- [Deployment Guide](../../../docs/deployment/local_development.md#web-assets) - Asset deployment procedures
