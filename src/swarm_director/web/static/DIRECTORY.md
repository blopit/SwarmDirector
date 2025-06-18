---
title: Static Web Assets Directory
description: Static web assets for SwarmDirector web interface
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [static-assets, css, javascript, images, fonts]
---

# Static Web Assets Directory

## Purpose

The static directory contains all static web assets for the SwarmDirector web interface, including CSS stylesheets, JavaScript files, images, fonts, and other client-side resources. This directory serves as the foundation for the user interface and provides a consistent, responsive web experience.

## Structure

```
src/swarm_director/web/static/
├── css/                         # Stylesheets and CSS files
│   ├── main.css                 # Main application stylesheet
│   ├── dashboard.css            # Dashboard-specific styles
│   ├── chat.css                 # Chat interface styles
│   ├── components.css           # Reusable component styles
│   ├── themes/                  # Theme variations
│   │   ├── light.css            # Light theme
│   │   ├── dark.css             # Dark theme
│   │   └── high-contrast.css    # High contrast theme
│   └── vendor/                  # Third-party CSS libraries
│       ├── bootstrap.min.css    # Bootstrap framework
│       └── fontawesome.min.css  # Font Awesome icons
├── js/                          # JavaScript files
│   ├── main.js                  # Main application JavaScript
│   ├── dashboard.js             # Dashboard functionality
│   ├── chat.js                  # Chat interface logic
│   ├── websocket.js             # WebSocket communication
│   ├── api.js                   # API interaction utilities
│   ├── components/              # Reusable JavaScript components
│   │   ├── modal.js             # Modal dialog component
│   │   ├── notification.js      # Notification system
│   │   ├── data-table.js        # Data table component
│   │   └── chart.js             # Chart visualization component
│   └── vendor/                  # Third-party JavaScript libraries
│       ├── jquery.min.js        # jQuery library
│       ├── bootstrap.min.js     # Bootstrap JavaScript
│       └── chart.min.js         # Chart.js library
├── images/                      # Image assets
│   ├── logo.png                 # Application logo
│   ├── favicon.ico              # Browser favicon
│   ├── icons/                   # Icon assets
│   │   ├── agent.svg            # Agent icon
│   │   ├── task.svg             # Task icon
│   │   ├── workflow.svg         # Workflow icon
│   │   └── analytics.svg        # Analytics icon
│   └── backgrounds/             # Background images
│       ├── hero-bg.jpg          # Hero section background
│       └── pattern-bg.png       # Pattern background
├── fonts/                       # Font files
│   ├── roboto/                  # Roboto font family
│   │   ├── roboto-regular.woff2 # Regular weight
│   │   ├── roboto-bold.woff2    # Bold weight
│   │   └── roboto-light.woff2   # Light weight
│   └── icons/                   # Icon fonts
│       └── swarm-icons.woff2    # Custom icon font
└── manifest/                    # Web app manifest files
    ├── manifest.json            # Web app manifest
    ├── service-worker.js        # Service worker for PWA
    └── offline.html             # Offline fallback page
```

## Guidelines

### 1. Organization
- **Asset Type Separation**: Organize assets by type (CSS, JS, images, fonts)
- **Component-Based**: Group related assets by component or feature
- **Vendor Separation**: Keep third-party assets separate from custom code
- **Theme Support**: Support multiple themes and accessibility options

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for all assets
- **Kebab Case**: Use kebab-case for file names (e.g., `main-dashboard.css`)
- **Version Suffixes**: Include version suffixes for cache busting when needed
- **Semantic Naming**: Use semantic names that describe purpose, not appearance

### 3. Implementation
- **Minification**: Minify CSS and JavaScript files for production
- **Compression**: Use appropriate compression for images and fonts
- **Caching**: Implement proper caching strategies for static assets
- **CDN Ready**: Structure assets for CDN deployment
- **Progressive Enhancement**: Design for progressive enhancement

### 4. Documentation
- **Asset Documentation**: Document the purpose and usage of major assets
- **Style Guide**: Maintain a style guide for consistent UI components
- **Build Process**: Document the build and optimization process
- **Accessibility**: Document accessibility features and requirements

## Best Practices

### CSS Organization
```css
/* main.css - Main application stylesheet */

/* 1. CSS Reset and Base Styles */
* {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
}

/* 2. CSS Custom Properties (Variables) */
:root {
    --primary-color: #007bff;
    --secondary-color: #6c757d;
    --success-color: #28a745;
    --danger-color: #dc3545;
    --warning-color: #ffc107;
    --info-color: #17a2b8;
    
    --font-family-primary: 'Roboto', sans-serif;
    --font-size-base: 16px;
    --line-height-base: 1.5;
    
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 3rem;
}

/* 3. Typography */
body {
    font-family: var(--font-family-primary);
    font-size: var(--font-size-base);
    line-height: var(--line-height-base);
    color: var(--text-color);
}

/* 4. Layout Components */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 var(--spacing-md);
}

/* 5. UI Components */
.btn {
    display: inline-block;
    padding: var(--spacing-sm) var(--spacing-md);
    border: none;
    border-radius: 4px;
    cursor: pointer;
    transition: all 0.2s ease;
}

.btn-primary {
    background-color: var(--primary-color);
    color: white;
}

.btn-primary:hover {
    background-color: color-mix(in srgb, var(--primary-color) 85%, black);
}
```

### JavaScript Organization
```javascript
// main.js - Main application JavaScript

// 1. Application Configuration
const SwarmDirector = {
    config: {
        apiBaseUrl: '/api/v1',
        websocketUrl: 'ws://localhost:8000/ws',
        refreshInterval: 30000
    },
    
    // 2. Utility Functions
    utils: {
        formatDate: (date) => {
            return new Intl.DateTimeFormat('en-US', {
                year: 'numeric',
                month: 'short',
                day: 'numeric',
                hour: '2-digit',
                minute: '2-digit'
            }).format(new Date(date));
        },
        
        debounce: (func, wait) => {
            let timeout;
            return function executedFunction(...args) {
                const later = () => {
                    clearTimeout(timeout);
                    func(...args);
                };
                clearTimeout(timeout);
                timeout = setTimeout(later, wait);
            };
        }
    },
    
    // 3. API Interface
    api: {
        async get(endpoint) {
            const response = await fetch(`${this.config.apiBaseUrl}${endpoint}`);
            if (!response.ok) {
                throw new Error(`API request failed: ${response.statusText}`);
            }
            return response.json();
        },
        
        async post(endpoint, data) {
            const response = await fetch(`${this.config.apiBaseUrl}${endpoint}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(data)
            });
            if (!response.ok) {
                throw new Error(`API request failed: ${response.statusText}`);
            }
            return response.json();
        }
    },
    
    // 4. Application Initialization
    init: () => {
        console.log('SwarmDirector application initialized');
        // Initialize components
        SwarmDirector.components.init();
        // Setup event listeners
        SwarmDirector.events.init();
    }
};

// 5. Initialize on DOM ready
document.addEventListener('DOMContentLoaded', SwarmDirector.init);
```

### Security
- **Content Security Policy**: Implement CSP headers for XSS protection
- **Asset Integrity**: Use Subresource Integrity (SRI) for external assets
- **HTTPS Only**: Serve all assets over HTTPS in production
- **Input Sanitization**: Sanitize any user-generated content in JavaScript

### Performance
- **Asset Optimization**: Optimize images, minify CSS/JS, use appropriate formats
- **Lazy Loading**: Implement lazy loading for images and non-critical assets
- **Caching**: Use appropriate cache headers and versioning strategies
- **Bundle Splitting**: Split JavaScript bundles for better loading performance

### Testing
```javascript
// test-utils.js - Testing utilities for frontend components

const TestUtils = {
    // Mock API responses
    mockApiResponse: (data, delay = 100) => {
        return new Promise(resolve => {
            setTimeout(() => resolve(data), delay);
        });
    },
    
    // DOM testing helpers
    createTestElement: (tag, attributes = {}) => {
        const element = document.createElement(tag);
        Object.entries(attributes).forEach(([key, value]) => {
            element.setAttribute(key, value);
        });
        return element;
    },
    
    // Event simulation
    simulateClick: (element) => {
        const event = new MouseEvent('click', {
            view: window,
            bubbles: true,
            cancelable: true
        });
        element.dispatchEvent(event);
    }
};
```

### Accessibility
- **ARIA Labels**: Include appropriate ARIA labels for screen readers
- **Keyboard Navigation**: Ensure all interactive elements are keyboard accessible
- **Color Contrast**: Maintain sufficient color contrast ratios
- **Focus Management**: Implement proper focus management for dynamic content

## Examples

### Responsive CSS Component
```css
/* components.css - Reusable component styles */

.card {
    background: white;
    border-radius: 8px;
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
    padding: var(--spacing-lg);
    margin-bottom: var(--spacing-md);
}

.card-header {
    border-bottom: 1px solid #e9ecef;
    padding-bottom: var(--spacing-md);
    margin-bottom: var(--spacing-md);
}

.card-title {
    font-size: 1.25rem;
    font-weight: 600;
    margin: 0;
}

/* Responsive design */
@media (max-width: 768px) {
    .card {
        padding: var(--spacing-md);
        margin-bottom: var(--spacing-sm);
    }
}
```

### Interactive JavaScript Component
```javascript
// components/notification.js - Notification system

class NotificationSystem {
    constructor() {
        this.container = this.createContainer();
        this.notifications = new Map();
    }
    
    createContainer() {
        const container = document.createElement('div');
        container.className = 'notification-container';
        container.setAttribute('aria-live', 'polite');
        document.body.appendChild(container);
        return container;
    }
    
    show(message, type = 'info', duration = 5000) {
        const id = Date.now().toString();
        const notification = this.createNotification(id, message, type);
        
        this.container.appendChild(notification);
        this.notifications.set(id, notification);
        
        // Auto-remove after duration
        setTimeout(() => this.remove(id), duration);
        
        return id;
    }
    
    createNotification(id, message, type) {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.setAttribute('role', 'alert');
        notification.innerHTML = `
            <span class="notification-message">${message}</span>
            <button class="notification-close" aria-label="Close notification">×</button>
        `;
        
        // Add close event listener
        notification.querySelector('.notification-close').addEventListener('click', () => {
            this.remove(id);
        });
        
        return notification;
    }
    
    remove(id) {
        const notification = this.notifications.get(id);
        if (notification) {
            notification.remove();
            this.notifications.delete(id);
        }
    }
}

// Initialize global notification system
window.notifications = new NotificationSystem();
```

## Related Documentation

- [Web Interface Documentation](../README.md) - Web interface overview
- [API Documentation](../../../docs/api/web.md) - Web API reference
- [UI Style Guide](../../../docs/development/ui_style_guide.md) - UI design guidelines
- [Accessibility Guide](../../../docs/development/accessibility.md) - Accessibility requirements
- [Performance Guide](../../../docs/development/frontend_performance.md) - Frontend performance optimization
- [Build Process](../../../docs/development/build_process.md) - Asset build and deployment process
