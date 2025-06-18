---
title: End-to-End Tests Directory
description: End-to-end testing suite for SwarmDirector web interface and workflows
version: 1.0.0
last_updated: 2025-06-18
maintainer: SwarmDirector Team
tags: [e2e-testing, playwright, automation, web-testing]
---

# End-to-End Tests Directory

## Purpose

The tests/e2e directory contains end-to-end (E2E) tests for SwarmDirector, focusing on testing complete user workflows, web interface functionality, and system integration scenarios. These tests use Playwright to automate browser interactions and validate the entire application stack from the user's perspective.

## Structure

```
tests/e2e/
├── chat-interface.spec.js       # Chat interface E2E tests
├── global-setup.js              # Global test setup configuration
├── global-teardown.js           # Global test cleanup
├── fixtures/                    # Test fixtures and data
│   ├── test-data.json           # Test data for E2E scenarios
│   ├── mock-responses.json      # Mock API responses
│   ├── user-profiles.json       # Test user profiles
│   └── workflow-scenarios.json  # Workflow test scenarios
├── pages/                       # Page Object Model (POM) classes
│   ├── base-page.js             # Base page class with common functionality
│   ├── dashboard-page.js        # Dashboard page object
│   ├── agents-page.js           # Agents management page object
│   ├── tasks-page.js            # Tasks management page object
│   ├── chat-page.js             # Chat interface page object
│   ├── analytics-page.js        # Analytics dashboard page object
│   └── settings-page.js         # Settings page object
├── workflows/                   # Complete workflow tests
│   ├── agent-lifecycle.spec.js  # Agent creation to deletion workflow
│   ├── task-execution.spec.js   # Task creation and execution workflow
│   ├── conversation-flow.spec.js # Complete conversation workflow
│   ├── analytics-workflow.spec.js # Analytics and reporting workflow
│   └── user-management.spec.js  # User management workflow
├── api/                         # API integration tests
│   ├── agent-api.spec.js        # Agent API E2E tests
│   ├── task-api.spec.js         # Task API E2E tests
│   ├── conversation-api.spec.js # Conversation API E2E tests
│   └── analytics-api.spec.js    # Analytics API E2E tests
├── performance/                 # Performance and load tests
│   ├── page-load.spec.js        # Page load performance tests
│   ├── api-performance.spec.js  # API performance tests
│   ├── concurrent-users.spec.js # Concurrent user scenarios
│   └── stress-tests.spec.js     # Stress testing scenarios
├── accessibility/               # Accessibility tests
│   ├── keyboard-navigation.spec.js # Keyboard navigation tests
│   ├── screen-reader.spec.js    # Screen reader compatibility tests
│   ├── color-contrast.spec.js   # Color contrast validation
│   └── aria-compliance.spec.js  # ARIA compliance tests
├── cross-browser/               # Cross-browser compatibility tests
│   ├── chrome.spec.js           # Chrome-specific tests
│   ├── firefox.spec.js          # Firefox-specific tests
│   ├── safari.spec.js           # Safari-specific tests
│   └── edge.spec.js             # Edge-specific tests
├── mobile/                      # Mobile responsiveness tests
│   ├── responsive-design.spec.js # Responsive design tests
│   ├── touch-interactions.spec.js # Touch interaction tests
│   └── mobile-navigation.spec.js # Mobile navigation tests
├── security/                    # Security-focused E2E tests
│   ├── authentication.spec.js   # Authentication flow tests
│   ├── authorization.spec.js    # Authorization and permissions tests
│   ├── xss-protection.spec.js   # XSS protection tests
│   └── csrf-protection.spec.js  # CSRF protection tests
├── utils/                       # Test utilities and helpers
│   ├── test-helpers.js          # Common test helper functions
│   ├── data-generators.js       # Test data generation utilities
│   ├── api-client.js            # API client for E2E tests
│   ├── database-helpers.js      # Database setup and cleanup helpers
│   └── screenshot-helpers.js    # Screenshot and visual testing helpers
└── reports/                     # Test reports and artifacts
    ├── html-report/             # HTML test reports
    ├── screenshots/             # Test failure screenshots
    ├── videos/                  # Test execution videos
    └── traces/                  # Playwright trace files
```

## Guidelines

### 1. Organization
- **Feature-Based Structure**: Organize tests by application features and workflows
- **Page Object Model**: Use POM pattern for maintainable test code
- **Reusable Components**: Create reusable test components and utilities
- **Test Data Management**: Centralize test data and fixtures

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names for test files and functions
- **Spec Suffix**: Use `.spec.js` suffix for test files
- **Feature Prefixes**: Use feature prefixes for related test groups
- **Consistent Format**: Follow consistent naming conventions

### 3. Implementation
- **Playwright Framework**: Use Playwright for cross-browser testing
- **Async/Await**: Use async/await patterns for all test operations
- **Error Handling**: Implement robust error handling and recovery
- **Test Isolation**: Ensure tests are independent and can run in any order
- **Data Cleanup**: Clean up test data after each test run

### 4. Documentation
- **Test Documentation**: Document test scenarios and expected outcomes
- **Setup Instructions**: Provide clear setup and execution instructions
- **Troubleshooting**: Include troubleshooting guides for common issues
- **Best Practices**: Document E2E testing best practices
- **Maintenance**: Document test maintenance procedures

## Best Practices

### Page Object Model Implementation
```javascript
// pages/base-page.js - Base page class with common functionality
class BasePage {
    constructor(page) {
        this.page = page;
        this.baseUrl = process.env.BASE_URL || 'http://localhost:8000';
    }

    async navigate(path = '') {
        const url = `${this.baseUrl}${path}`;
        await this.page.goto(url, { waitUntil: 'networkidle' });
    }

    async waitForElement(selector, options = {}) {
        return await this.page.waitForSelector(selector, {
            timeout: 10000,
            ...options
        });
    }

    async clickElement(selector) {
        await this.waitForElement(selector);
        await this.page.click(selector);
    }

    async fillInput(selector, value) {
        await this.waitForElement(selector);
        await this.page.fill(selector, value);
    }

    async getText(selector) {
        await this.waitForElement(selector);
        return await this.page.textContent(selector);
    }

    async isVisible(selector) {
        try {
            await this.waitForElement(selector, { timeout: 5000 });
            return await this.page.isVisible(selector);
        } catch {
            return false;
        }
    }

    async takeScreenshot(name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${name}-${timestamp}.png`;
        await this.page.screenshot({
            path: `tests/e2e/reports/screenshots/${filename}`,
            fullPage: true
        });
        return filename;
    }

    async waitForApiResponse(urlPattern, method = 'GET') {
        return await this.page.waitForResponse(response => 
            response.url().includes(urlPattern) && 
            response.request().method() === method
        );
    }

    async mockApiResponse(urlPattern, responseData, status = 200) {
        await this.page.route(urlPattern, route => {
            route.fulfill({
                status,
                contentType: 'application/json',
                body: JSON.stringify(responseData)
            });
        });
    }
}

module.exports = BasePage;
```

### Security
- **Test Data Security**: Use non-sensitive test data
- **Authentication Testing**: Test authentication and authorization flows
- **Input Validation**: Test input validation and sanitization
- **Session Management**: Test session handling and security
- **HTTPS Testing**: Test HTTPS enforcement and security headers

### Performance
- **Test Execution Speed**: Optimize test execution time
- **Parallel Execution**: Run tests in parallel where possible
- **Resource Management**: Manage browser resources efficiently
- **Network Optimization**: Optimize network requests during tests
- **Test Data Size**: Use minimal test data sets

### Testing
```javascript
// workflows/agent-lifecycle.spec.js - Complete agent lifecycle test
const { test, expect } = require('@playwright/test');
const DashboardPage = require('../pages/dashboard-page');
const AgentsPage = require('../pages/agents-page');
const { generateTestAgent } = require('../utils/data-generators');

test.describe('Agent Lifecycle Workflow', () => {
    let dashboardPage;
    let agentsPage;
    let testAgent;

    test.beforeEach(async ({ page }) => {
        dashboardPage = new DashboardPage(page);
        agentsPage = new AgentsPage(page);
        testAgent = generateTestAgent();

        // Navigate to dashboard
        await dashboardPage.navigate('/dashboard');
        await dashboardPage.waitForPageLoad();
    });

    test('should complete full agent lifecycle', async ({ page }) => {
        // Step 1: Navigate to agents page
        await test.step('Navigate to agents page', async () => {
            await dashboardPage.clickNavigation('Agents');
            await agentsPage.waitForPageLoad();
            
            // Verify we're on the agents page
            expect(await agentsPage.getPageTitle()).toBe('Agents');
        });

        // Step 2: Create new agent
        await test.step('Create new agent', async () => {
            await agentsPage.clickCreateAgent();
            await agentsPage.fillAgentForm(testAgent);
            
            // Wait for API response
            const createResponse = await agentsPage.waitForApiResponse('/api/v1/agents', 'POST');
            expect(createResponse.status()).toBe(201);
            
            await agentsPage.submitAgentForm();
            
            // Verify agent appears in list
            await agentsPage.waitForAgentInList(testAgent.name);
            expect(await agentsPage.isAgentVisible(testAgent.name)).toBe(true);
        });

        // Step 3: View agent details
        await test.step('View agent details', async () => {
            await agentsPage.clickAgent(testAgent.name);
            await agentsPage.waitForAgentDetails();
            
            // Verify agent details
            expect(await agentsPage.getAgentName()).toBe(testAgent.name);
            expect(await agentsPage.getAgentType()).toBe(testAgent.type);
            expect(await agentsPage.getAgentStatus()).toBe('inactive');
        });

        // Step 4: Activate agent
        await test.step('Activate agent', async () => {
            await agentsPage.clickActivateAgent();
            
            // Wait for activation API call
            const activateResponse = await agentsPage.waitForApiResponse('/api/v1/agents/*/activate', 'POST');
            expect(activateResponse.status()).toBe(200);
            
            // Verify agent is activated
            await agentsPage.waitForStatusChange('active');
            expect(await agentsPage.getAgentStatus()).toBe('active');
        });

        // Step 5: Assign task to agent
        await test.step('Assign task to agent', async () => {
            const testTask = {
                title: 'E2E Test Task',
                description: 'Task created during E2E testing',
                priority: 3
            };
            
            await agentsPage.clickAssignTask();
            await agentsPage.fillTaskForm(testTask);
            await agentsPage.submitTaskForm();
            
            // Verify task assignment
            await agentsPage.waitForTaskAssignment();
            expect(await agentsPage.getAssignedTasksCount()).toBeGreaterThan(0);
        });

        // Step 6: Monitor agent performance
        await test.step('Monitor agent performance', async () => {
            await agentsPage.clickPerformanceTab();
            await agentsPage.waitForPerformanceMetrics();
            
            // Verify performance metrics are displayed
            expect(await agentsPage.isPerformanceMetricsVisible()).toBe(true);
            expect(await agentsPage.getTasksCompletedCount()).toBeGreaterThanOrEqual(0);
        });

        // Step 7: Update agent configuration
        await test.step('Update agent configuration', async () => {
            await agentsPage.clickEditAgent();
            
            const updatedConfig = {
                ...testAgent,
                description: 'Updated during E2E testing'
            };
            
            await agentsPage.fillAgentForm(updatedConfig);
            await agentsPage.submitAgentForm();
            
            // Verify update
            expect(await agentsPage.getAgentDescription()).toBe(updatedConfig.description);
        });

        // Step 8: Deactivate agent
        await test.step('Deactivate agent', async () => {
            await agentsPage.clickDeactivateAgent();
            await agentsPage.confirmDeactivation();
            
            // Wait for deactivation
            await agentsPage.waitForStatusChange('inactive');
            expect(await agentsPage.getAgentStatus()).toBe('inactive');
        });

        // Step 9: Delete agent
        await test.step('Delete agent', async () => {
            await agentsPage.clickDeleteAgent();
            await agentsPage.confirmDeletion();
            
            // Wait for deletion API call
            const deleteResponse = await agentsPage.waitForApiResponse('/api/v1/agents/*', 'DELETE');
            expect(deleteResponse.status()).toBe(200);
            
            // Verify agent is removed from list
            await agentsPage.waitForAgentRemoval(testAgent.name);
            expect(await agentsPage.isAgentVisible(testAgent.name)).toBe(false);
        });
    });

    test('should handle agent creation errors gracefully', async ({ page }) => {
        await test.step('Navigate to agents page', async () => {
            await dashboardPage.clickNavigation('Agents');
            await agentsPage.waitForPageLoad();
        });

        await test.step('Attempt to create agent with invalid data', async () => {
            await agentsPage.clickCreateAgent();
            
            // Submit form with missing required fields
            await agentsPage.submitAgentForm();
            
            // Verify validation errors are displayed
            expect(await agentsPage.isValidationErrorVisible()).toBe(true);
            expect(await agentsPage.getValidationErrorMessage()).toContain('Name is required');
        });

        await test.step('Attempt to create duplicate agent', async () => {
            // First, create a valid agent
            await agentsPage.fillAgentForm(testAgent);
            await agentsPage.submitAgentForm();
            await agentsPage.waitForAgentInList(testAgent.name);
            
            // Try to create another agent with the same name
            await agentsPage.clickCreateAgent();
            await agentsPage.fillAgentForm(testAgent);
            await agentsPage.submitAgentForm();
            
            // Verify error handling
            expect(await agentsPage.isErrorMessageVisible()).toBe(true);
            expect(await agentsPage.getErrorMessage()).toContain('Agent name already exists');
        });
    });

    test.afterEach(async ({ page }) => {
        // Cleanup: Remove any test agents that might have been created
        try {
            await agentsPage.cleanupTestAgents(testAgent.name);
        } catch (error) {
            console.log('Cleanup warning:', error.message);
        }
    });
});
```

### Test Data Management
- **Isolated Test Data**: Use isolated test data for each test
- **Data Generation**: Generate test data dynamically
- **Data Cleanup**: Clean up test data after each test
- **Realistic Data**: Use realistic test data that mimics production
- **Data Versioning**: Version test data for consistency

## Examples

### Chat Interface E2E Test
```javascript
// chat-interface.spec.js - Chat interface E2E tests
const { test, expect } = require('@playwright/test');
const ChatPage = require('./pages/chat-page');
const { generateTestMessage } = require('./utils/data-generators');

test.describe('SwarmDirector Chat Interface', () => {
    let chatPage;

    test.beforeEach(async ({ page }) => {
        chatPage = new ChatPage(page);
        await chatPage.navigate('/chat');
        await chatPage.waitForPageLoad();
    });

    test('should load chat page successfully', async ({ page }) => {
        // Verify page elements are present
        expect(await chatPage.isChatInterfaceVisible()).toBe(true);
        expect(await chatPage.isMessageInputVisible()).toBe(true);
        expect(await chatPage.isSendButtonVisible()).toBe(true);
        expect(await chatPage.isActivityLogVisible()).toBe(true);
    });

    test('should display initial welcome state', async ({ page }) => {
        // Verify welcome message
        expect(await chatPage.isWelcomeMessageVisible()).toBe(true);
        expect(await chatPage.getWelcomeMessage()).toContain('Welcome to SwarmDirector');
        
        // Verify empty conversation state
        expect(await chatPage.getMessageCount()).toBe(0);
        expect(await chatPage.isEmptyStateVisible()).toBe(true);
    });

    test('should send and receive messages', async ({ page }) => {
        const testMessage = generateTestMessage();
        
        // Send message
        await chatPage.typeMessage(testMessage.content);
        await chatPage.clickSendButton();
        
        // Verify message appears in chat
        await chatPage.waitForMessage(testMessage.content);
        expect(await chatPage.isMessageVisible(testMessage.content)).toBe(true);
        
        // Verify message metadata
        expect(await chatPage.getMessageSender(testMessage.content)).toBe('You');
        expect(await chatPage.getMessageTimestamp(testMessage.content)).toBeTruthy();
        
        // Wait for agent response
        await chatPage.waitForAgentResponse();
        expect(await chatPage.getMessageCount()).toBeGreaterThan(1);
    });

    test('should validate message input', async ({ page }) => {
        // Test empty message
        await chatPage.clickSendButton();
        expect(await chatPage.isValidationErrorVisible()).toBe(true);
        
        // Test message too long
        const longMessage = 'a'.repeat(5001);
        await chatPage.typeMessage(longMessage);
        await chatPage.clickSendButton();
        expect(await chatPage.getValidationError()).toContain('Message too long');
        
        // Test valid message
        await chatPage.clearMessage();
        await chatPage.typeMessage('Valid message');
        await chatPage.clickSendButton();
        expect(await chatPage.isValidationErrorVisible()).toBe(false);
    });

    test('should display connection status', async ({ page }) => {
        // Verify initial connection status
        expect(await chatPage.getConnectionStatus()).toBe('Connected');
        expect(await chatPage.isConnectionIndicatorGreen()).toBe(true);
        
        // Simulate connection loss
        await page.setOffline(true);
        await chatPage.waitForConnectionStatusChange();
        expect(await chatPage.getConnectionStatus()).toBe('Disconnected');
        expect(await chatPage.isConnectionIndicatorRed()).toBe(true);
        
        // Restore connection
        await page.setOffline(false);
        await chatPage.waitForConnectionStatusChange();
        expect(await chatPage.getConnectionStatus()).toBe('Connected');
    });

    test('should display activity log panel', async ({ page }) => {
        // Verify activity log is visible
        expect(await chatPage.isActivityLogVisible()).toBe(true);
        
        // Send a message to generate activity
        await chatPage.typeMessage('Test message for activity log');
        await chatPage.clickSendButton();
        
        // Verify activity appears in log
        await chatPage.waitForActivityLogEntry();
        expect(await chatPage.getActivityLogEntryCount()).toBeGreaterThan(0);
        
        // Verify activity log entry details
        const latestEntry = await chatPage.getLatestActivityLogEntry();
        expect(latestEntry.type).toBe('message_sent');
        expect(latestEntry.timestamp).toBeTruthy();
    });

    test('should categorize activity log entries', async ({ page }) => {
        // Send different types of messages/actions
        await chatPage.typeMessage('Hello agent');
        await chatPage.clickSendButton();
        await chatPage.waitForAgentResponse();
        
        // Check activity log categories
        const entries = await chatPage.getActivityLogEntries();
        const messageTypes = entries.map(entry => entry.type);
        
        expect(messageTypes).toContain('message_sent');
        expect(messageTypes).toContain('message_received');
        expect(messageTypes).toContain('agent_response');
    });

    test('should handle keyboard interactions', async ({ page }) => {
        // Test Enter key to send message
        await chatPage.typeMessage('Test message');
        await chatPage.pressEnterInMessageInput();
        await chatPage.waitForMessage('Test message');
        
        // Test Shift+Enter for new line
        await chatPage.typeMessage('Line 1');
        await chatPage.pressShiftEnterInMessageInput();
        await chatPage.typeMessage('Line 2');
        expect(await chatPage.getMessageInputValue()).toContain('\n');
        
        // Test Escape to clear input
        await chatPage.pressEscapeInMessageInput();
        expect(await chatPage.getMessageInputValue()).toBe('');
    });

    test('should support keyboard navigation', async ({ page }) => {
        // Test tab navigation
        await page.keyboard.press('Tab');
        expect(await chatPage.isMessageInputFocused()).toBe(true);
        
        await page.keyboard.press('Tab');
        expect(await chatPage.isSendButtonFocused()).toBe(true);
        
        // Test arrow key navigation in message history
        await chatPage.typeMessage('Message 1');
        await chatPage.clickSendButton();
        await chatPage.typeMessage('Message 2');
        await chatPage.clickSendButton();
        
        await page.keyboard.press('ArrowUp');
        expect(await chatPage.getSelectedMessageIndex()).toBe(1);
        
        await page.keyboard.press('ArrowUp');
        expect(await chatPage.getSelectedMessageIndex()).toBe(0);
    });

    test('should have proper ARIA labels', async ({ page }) => {
        // Check ARIA labels for accessibility
        expect(await chatPage.getMessageInputAriaLabel()).toBe('Type your message');
        expect(await chatPage.getSendButtonAriaLabel()).toBe('Send message');
        expect(await chatPage.getChatAreaAriaLabel()).toBe('Chat conversation');
        expect(await chatPage.getActivityLogAriaLabel()).toBe('Activity log');
        
        // Check ARIA live regions
        expect(await chatPage.getChatAreaAriaLive()).toBe('polite');
        expect(await chatPage.getStatusAreaAriaLive()).toBe('assertive');
    });

    test('should have proper responsive layout', async ({ page }) => {
        // Test desktop layout
        await page.setViewportSize({ width: 1200, height: 800 });
        expect(await chatPage.isSidebarVisible()).toBe(true);
        expect(await chatPage.getChatAreaWidth()).toBeGreaterThan(600);
        
        // Test tablet layout
        await page.setViewportSize({ width: 768, height: 1024 });
        expect(await chatPage.isSidebarCollapsed()).toBe(true);
        expect(await chatPage.getChatAreaWidth()).toBeLessThan(800);
        
        // Test mobile layout
        await page.setViewportSize({ width: 375, height: 667 });
        expect(await chatPage.isMobileLayoutActive()).toBe(true);
        expect(await chatPage.isActivityLogHidden()).toBe(true);
    });

    test('should handle rapid interactions', async ({ page }) => {
        // Send multiple messages rapidly
        const messages = ['Message 1', 'Message 2', 'Message 3'];
        
        for (const message of messages) {
            await chatPage.typeMessage(message);
            await chatPage.clickSendButton();
        }
        
        // Verify all messages are sent
        for (const message of messages) {
            expect(await chatPage.isMessageVisible(message)).toBe(true);
        }
        
        // Verify message order is preserved
        const messageOrder = await chatPage.getMessageOrder();
        expect(messageOrder).toEqual(messages);
    });

    test('should work in different browsers', async ({ browserName, page }) => {
        // Browser-specific tests
        if (browserName === 'chromium') {
            // Chrome-specific functionality
            expect(await chatPage.isWebSocketSupported()).toBe(true);
        } else if (browserName === 'firefox') {
            // Firefox-specific functionality
            expect(await chatPage.isLocalStorageSupported()).toBe(true);
        } else if (browserName === 'webkit') {
            // Safari-specific functionality
            expect(await chatPage.isTouchEventsSupported()).toBe(true);
        }
        
        // Common functionality should work in all browsers
        await chatPage.typeMessage('Cross-browser test');
        await chatPage.clickSendButton();
        expect(await chatPage.isMessageVisible('Cross-browser test')).toBe(true);
    });
});
```

### Test Utilities
```javascript
// utils/test-helpers.js - Common test helper functions
class TestHelpers {
    static async waitForCondition(conditionFn, timeout = 10000, interval = 100) {
        const startTime = Date.now();
        
        while (Date.now() - startTime < timeout) {
            if (await conditionFn()) {
                return true;
            }
            await this.sleep(interval);
        }
        
        throw new Error(`Condition not met within ${timeout}ms`);
    }
    
    static async sleep(ms) {
        return new Promise(resolve => setTimeout(resolve, ms));
    }
    
    static generateUniqueId() {
        return `test_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
    }
    
    static async retryOperation(operation, maxRetries = 3, delay = 1000) {
        for (let attempt = 1; attempt <= maxRetries; attempt++) {
            try {
                return await operation();
            } catch (error) {
                if (attempt === maxRetries) {
                    throw error;
                }
                console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
                await this.sleep(delay);
            }
        }
    }
    
    static async captureNetworkRequests(page, urlPattern) {
        const requests = [];
        
        page.on('request', request => {
            if (request.url().includes(urlPattern)) {
                requests.push({
                    url: request.url(),
                    method: request.method(),
                    headers: request.headers(),
                    postData: request.postData()
                });
            }
        });
        
        return requests;
    }
    
    static async mockApiEndpoint(page, endpoint, responseData, status = 200) {
        await page.route(`**/${endpoint}`, route => {
            route.fulfill({
                status,
                contentType: 'application/json',
                body: JSON.stringify(responseData)
            });
        });
    }
    
    static async clearBrowserData(page) {
        // Clear localStorage
        await page.evaluate(() => localStorage.clear());
        
        // Clear sessionStorage
        await page.evaluate(() => sessionStorage.clear());
        
        // Clear cookies
        const context = page.context();
        await context.clearCookies();
    }
    
    static async takeFullPageScreenshot(page, name) {
        const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
        const filename = `${name}-${timestamp}.png`;
        const path = `tests/e2e/reports/screenshots/${filename}`;
        
        await page.screenshot({
            path,
            fullPage: true
        });
        
        return { filename, path };
    }
    
    static async compareScreenshots(page, baselinePath, threshold = 0.2) {
        const screenshot = await page.screenshot();
        // Implementation would use image comparison library
        // This is a placeholder for the actual comparison logic
        return { match: true, difference: 0 };
    }
}

module.exports = TestHelpers;
```

## Related Documentation

- [Testing Guide](../DIRECTORY.md) - Main testing documentation
- [Playwright Configuration](../../playwright.config.js) - Playwright test configuration
- [API Testing](../api/README.md) - API testing documentation
- [Performance Testing](../performance/README.md) - Performance testing guide
- [Accessibility Testing](../accessibility/README.md) - Accessibility testing guide
- [CI/CD Integration](../../docs/deployment/ci_cd/README.md) - CI/CD pipeline integration
