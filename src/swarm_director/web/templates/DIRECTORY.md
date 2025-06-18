---
title: Web Templates Directory
description: HTML templates for SwarmDirector web interface
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [templates, html, jinja2, web-interface]
---

# Web Templates Directory

## Purpose

The templates directory contains HTML templates for the SwarmDirector web interface. These templates use the Jinja2 templating engine to provide dynamic, server-rendered web pages with consistent layout, styling, and functionality across the application.

## Structure

```
src/swarm_director/web/templates/
├── base.html                    # Base template with common layout
├── index.html                   # Application home page
├── dashboard.html               # Main dashboard interface
├── agents/                      # Agent management templates
│   ├── list.html                # Agent list view
│   ├── detail.html              # Agent detail view
│   ├── create.html              # Agent creation form
│   └── edit.html                # Agent editing form
├── tasks/                       # Task management templates
│   ├── list.html                # Task list view
│   ├── detail.html              # Task detail view
│   ├── create.html              # Task creation form
│   └── edit.html                # Task editing form
├── conversations/               # Conversation templates
│   ├── list.html                # Conversation list view
│   ├── detail.html              # Conversation detail view
│   └── chat.html                # Live chat interface
├── analytics/                   # Analytics and reporting templates
│   ├── dashboard.html           # Analytics dashboard
│   ├── reports.html             # Report generation interface
│   └── metrics.html             # Metrics visualization
├── admin/                       # Administrative templates
│   ├── settings.html            # System settings
│   ├── users.html               # User management
│   └── logs.html                # System logs viewer
├── demo/                        # Demo interface templates
│   ├── index.html               # Demo landing page
│   ├── chat.html                # Interactive chat interface
│   └── workflow.html            # Workflow demonstration
├── api/                         # API documentation templates
│   ├── index.html               # API documentation home
│   └── endpoints.html           # Endpoint documentation
├── errors/                      # Error page templates
│   ├── 404.html                 # Not found page
│   ├── 500.html                 # Server error page
│   └── maintenance.html         # Maintenance mode page
├── components/                  # Reusable template components
│   ├── navigation.html          # Navigation component
│   ├── sidebar.html             # Sidebar component
│   ├── footer.html              # Footer component
│   ├── pagination.html          # Pagination component
│   └── modals.html              # Modal dialog components
└── emails/                      # Email templates
    ├── notification.html        # Notification email template
    ├── report.html              # Report email template
    └── alert.html               # Alert email template
```

## Guidelines

### 1. Organization
- **Feature-Based**: Organize templates by application feature or domain
- **Component Reuse**: Create reusable components for common UI elements
- **Template Inheritance**: Use template inheritance for consistent layout
- **Responsive Design**: Ensure all templates are mobile-responsive

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for template files
- **Consistent Naming**: Follow consistent naming conventions across templates
- **Action-Based**: Use action-based names for forms (create.html, edit.html)
- **Semantic Structure**: Use semantic HTML structure and class names

### 3. Implementation
- **Jinja2 Templating**: Use Jinja2 templating features effectively
- **Template Inheritance**: Implement proper template inheritance hierarchy
- **Context Variables**: Use meaningful context variable names
- **Security**: Implement proper escaping and CSRF protection
- **Accessibility**: Follow accessibility best practices

### 4. Documentation
- **Template Documentation**: Document template purpose and context variables
- **Component Documentation**: Document reusable components and their usage
- **Style Guide**: Maintain consistent styling and layout patterns
- **Integration Guide**: Document template integration with backend views

## Best Practices

### Template Inheritance
```html
<!-- base.html - Base template -->
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}SwarmDirector{% endblock %}</title>
    
    <!-- CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">
    {% block extra_css %}{% endblock %}
    
    <!-- Favicon -->
    <link rel="icon" type="image/x-icon" href="{{ url_for('static', filename='images/favicon.ico') }}">
</head>
<body>
    <!-- Navigation -->
    {% include 'components/navigation.html' %}
    
    <!-- Main Content -->
    <main class="main-content" role="main">
        {% block content %}{% endblock %}
    </main>
    
    <!-- Footer -->
    {% include 'components/footer.html' %}
    
    <!-- JavaScript -->
    <script src="{{ url_for('static', filename='js/main.js') }}"></script>
    {% block extra_js %}{% endblock %}
</body>
</html>
```

### Component Templates
```html
<!-- components/navigation.html - Navigation component -->
<nav class="navbar" role="navigation" aria-label="Main navigation">
    <div class="navbar-container">
        <!-- Brand -->
        <div class="navbar-brand">
            <a href="{{ url_for('main.index') }}" class="brand-link">
                <img src="{{ url_for('static', filename='images/logo.png') }}" 
                     alt="SwarmDirector Logo" class="brand-logo">
                <span class="brand-text">SwarmDirector</span>
            </a>
        </div>
        
        <!-- Navigation Links -->
        <ul class="navbar-nav" role="menubar">
            <li class="nav-item" role="none">
                <a href="{{ url_for('main.dashboard') }}" 
                   class="nav-link {% if request.endpoint == 'main.dashboard' %}active{% endif %}"
                   role="menuitem">Dashboard</a>
            </li>
            <li class="nav-item" role="none">
                <a href="{{ url_for('agents.list') }}" 
                   class="nav-link {% if request.endpoint.startswith('agents.') %}active{% endif %}"
                   role="menuitem">Agents</a>
            </li>
            <li class="nav-item" role="none">
                <a href="{{ url_for('tasks.list') }}" 
                   class="nav-link {% if request.endpoint.startswith('tasks.') %}active{% endif %}"
                   role="menuitem">Tasks</a>
            </li>
            <li class="nav-item" role="none">
                <a href="{{ url_for('analytics.dashboard') }}" 
                   class="nav-link {% if request.endpoint.startswith('analytics.') %}active{% endif %}"
                   role="menuitem">Analytics</a>
            </li>
        </ul>
        
        <!-- User Menu -->
        <div class="navbar-user">
            <div class="dropdown">
                <button class="dropdown-toggle" aria-haspopup="true" aria-expanded="false">
                    <span class="user-name">{{ current_user.name if current_user else 'Guest' }}</span>
                </button>
                <ul class="dropdown-menu" role="menu">
                    <li role="none">
                        <a href="{{ url_for('auth.profile') }}" class="dropdown-item" role="menuitem">Profile</a>
                    </li>
                    <li role="none">
                        <a href="{{ url_for('auth.settings') }}" class="dropdown-item" role="menuitem">Settings</a>
                    </li>
                    <li role="separator" class="dropdown-divider"></li>
                    <li role="none">
                        <a href="{{ url_for('auth.logout') }}" class="dropdown-item" role="menuitem">Logout</a>
                    </li>
                </ul>
            </div>
        </div>
    </div>
</nav>
```

### Security
- **CSRF Protection**: Include CSRF tokens in all forms
- **Content Escaping**: Properly escape all user-generated content
- **Input Validation**: Validate all form inputs on both client and server
- **XSS Prevention**: Use Jinja2's auto-escaping features

### Performance
- **Template Caching**: Enable template caching in production
- **Asset Optimization**: Optimize CSS and JavaScript loading
- **Lazy Loading**: Implement lazy loading for images and heavy content
- **Minification**: Minify HTML output in production

### Testing
```python
# test_templates.py - Template testing
import pytest
from flask import url_for
from src.swarm_director.app import create_app

@pytest.fixture
def app():
    app = create_app(testing=True)
    return app

@pytest.fixture
def client(app):
    return app.test_client()

def test_dashboard_template_renders(client):
    """Test that dashboard template renders correctly."""
    response = client.get('/dashboard')
    assert response.status_code == 200
    assert b'Dashboard' in response.data
    assert b'navbar' in response.data

def test_agent_list_template(client):
    """Test agent list template rendering."""
    response = client.get('/agents')
    assert response.status_code == 200
    assert b'Agents' in response.data
    assert b'agent-list' in response.data

def test_error_template_404(client):
    """Test 404 error template."""
    response = client.get('/nonexistent-page')
    assert response.status_code == 404
    assert b'Page Not Found' in response.data
```

### Accessibility
- **Semantic HTML**: Use semantic HTML elements appropriately
- **ARIA Labels**: Include ARIA labels for screen readers
- **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
- **Color Contrast**: Maintain sufficient color contrast ratios

## Examples

### Dashboard Template
```html
<!-- dashboard.html - Main dashboard -->
{% extends "base.html" %}

{% block title %}Dashboard - SwarmDirector{% endblock %}

{% block extra_css %}
<link rel="stylesheet" href="{{ url_for('static', filename='css/dashboard.css') }}">
{% endblock %}

{% block content %}
<div class="dashboard-container">
    <!-- Dashboard Header -->
    <header class="dashboard-header">
        <h1 class="dashboard-title">Dashboard</h1>
        <div class="dashboard-actions">
            <button class="btn btn-primary" onclick="refreshDashboard()">
                <i class="icon-refresh" aria-hidden="true"></i>
                Refresh
            </button>
        </div>
    </header>
    
    <!-- Dashboard Stats -->
    <section class="dashboard-stats" aria-label="System statistics">
        <div class="stat-card">
            <h3 class="stat-title">Active Agents</h3>
            <div class="stat-value">{{ stats.active_agents }}</div>
        </div>
        <div class="stat-card">
            <h3 class="stat-title">Pending Tasks</h3>
            <div class="stat-value">{{ stats.pending_tasks }}</div>
        </div>
        <div class="stat-card">
            <h3 class="stat-title">Completed Today</h3>
            <div class="stat-value">{{ stats.completed_today }}</div>
        </div>
        <div class="stat-card">
            <h3 class="stat-title">Success Rate</h3>
            <div class="stat-value">{{ "%.1f"|format(stats.success_rate * 100) }}%</div>
        </div>
    </section>
    
    <!-- Dashboard Content -->
    <div class="dashboard-content">
        <!-- Recent Activity -->
        <section class="dashboard-section">
            <h2 class="section-title">Recent Activity</h2>
            <div class="activity-list">
                {% for activity in recent_activities %}
                <div class="activity-item">
                    <div class="activity-icon">
                        <i class="icon-{{ activity.type }}" aria-hidden="true"></i>
                    </div>
                    <div class="activity-content">
                        <div class="activity-title">{{ activity.title }}</div>
                        <div class="activity-time">{{ activity.timestamp|timeago }}</div>
                    </div>
                </div>
                {% else %}
                <div class="empty-state">
                    <p>No recent activity</p>
                </div>
                {% endfor %}
            </div>
        </section>
        
        <!-- Quick Actions -->
        <section class="dashboard-section">
            <h2 class="section-title">Quick Actions</h2>
            <div class="quick-actions">
                <a href="{{ url_for('tasks.create') }}" class="action-card">
                    <i class="icon-plus" aria-hidden="true"></i>
                    <span>Create Task</span>
                </a>
                <a href="{{ url_for('agents.create') }}" class="action-card">
                    <i class="icon-robot" aria-hidden="true"></i>
                    <span>Add Agent</span>
                </a>
                <a href="{{ url_for('analytics.reports') }}" class="action-card">
                    <i class="icon-chart" aria-hidden="true"></i>
                    <span>View Reports</span>
                </a>
            </div>
        </section>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/dashboard.js') }}"></script>
<script>
    // Initialize dashboard
    document.addEventListener('DOMContentLoaded', function() {
        Dashboard.init({
            refreshInterval: 30000,
            apiEndpoint: '{{ url_for("api.dashboard_data") }}'
        });
    });
</script>
{% endblock %}
```

### Form Template
```html
<!-- tasks/create.html - Task creation form -->
{% extends "base.html" %}

{% block title %}Create Task - SwarmDirector{% endblock %}

{% block content %}
<div class="form-container">
    <header class="form-header">
        <h1>Create New Task</h1>
        <a href="{{ url_for('tasks.list') }}" class="btn btn-secondary">
            <i class="icon-arrow-left" aria-hidden="true"></i>
            Back to Tasks
        </a>
    </header>
    
    <form method="POST" class="task-form" novalidate>
        {{ form.hidden_tag() }}
        
        <!-- Task Title -->
        <div class="form-group">
            {{ form.title.label(class="form-label") }}
            {{ form.title(class="form-control" + (" is-invalid" if form.title.errors else "")) }}
            {% if form.title.errors %}
                <div class="invalid-feedback">
                    {% for error in form.title.errors %}
                        <div>{{ error }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
        
        <!-- Task Description -->
        <div class="form-group">
            {{ form.description.label(class="form-label") }}
            {{ form.description(class="form-control", rows="4") }}
            {% if form.description.errors %}
                <div class="invalid-feedback">
                    {% for error in form.description.errors %}
                        <div>{{ error }}</div>
                    {% endfor %}
                </div>
            {% endif %}
        </div>
        
        <!-- Priority and Agent -->
        <div class="form-row">
            <div class="form-group col-md-6">
                {{ form.priority.label(class="form-label") }}
                {{ form.priority(class="form-control") }}
            </div>
            <div class="form-group col-md-6">
                {{ form.assigned_agent.label(class="form-label") }}
                {{ form.assigned_agent(class="form-control") }}
            </div>
        </div>
        
        <!-- Form Actions -->
        <div class="form-actions">
            <button type="submit" class="btn btn-primary">
                <i class="icon-save" aria-hidden="true"></i>
                Create Task
            </button>
            <a href="{{ url_for('tasks.list') }}" class="btn btn-secondary">Cancel</a>
        </div>
    </form>
</div>
{% endblock %}
```

## Related Documentation

- [Web Interface Documentation](../README.md) - Web interface overview
- [Flask Templates Guide](../../../docs/development/flask_templates.md) - Flask templating guide
- [UI Style Guide](../../../docs/development/ui_style_guide.md) - UI design guidelines
- [Accessibility Guide](../../../docs/development/accessibility.md) - Accessibility requirements
- [Form Handling](../../../docs/development/form_handling.md) - Form processing guide
- [Static Assets](static/README.md) - Static assets documentation
