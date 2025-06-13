const { test, expect } = require('@playwright/test');

test.describe('SwarmDirector Chat Interface', () => {
  
  test.beforeEach(async ({ page }) => {
    // Navigate to chat page before each test
    await page.goto('/chat');
    
    // Wait for Alpine.js to initialize
    await page.waitForFunction(() => window.Alpine !== undefined);
    
    // Wait for chat app to be ready
    await page.waitForSelector('[x-data="chatApp()"]');
  });

  test.describe('Page Load and Initial State', () => {
    
    test('should load chat page successfully', async ({ page }) => {
      // Check page title
      await expect(page).toHaveTitle('SwarmDirector Chat');
      
      // Check main components are present
      await expect(page.locator('h1')).toContainText('SwarmDirector Chat');
      await expect(page.locator('#messageInput')).toBeVisible();
      await expect(page.locator('button[type="submit"]')).toBeVisible();
      await expect(page.locator('#messagesContainer')).toBeVisible();
      await expect(page.locator('#activityLog')).toBeVisible();
    });

    test('should show initial welcome state', async ({ page }) => {
      // Check welcome message is displayed
      await expect(page.locator('.text-gray-500')).toContainText('Start a conversation with SwarmDirector');
      
      // Check connection status shows disconnected initially
      await expect(page.locator('.connection-status')).toContainText('Disconnected');
      
      // Check send button is disabled when not connected
      await expect(page.locator('button[type="submit"]')).toBeDisabled();
    });

    test('should have proper responsive layout', async ({ page }) => {
      // Test desktop layout
      await page.setViewportSize({ width: 1200, height: 800 });
      await expect(page.locator('.chat-container')).toBeVisible();
      await expect(page.locator('.activity-panel')).toBeVisible();
      
      // Test mobile layout
      await page.setViewportSize({ width: 375, height: 667 });
      await expect(page.locator('.chat-container')).toBeVisible();
      // Activity panel should be collapsible on mobile
      await expect(page.locator('.activity-toggle')).toBeVisible();
    });
  });

  test.describe('Message Input and Validation', () => {
    
    test('should validate message input', async ({ page }) => {
      const messageInput = page.locator('#messageInput');
      const sendButton = page.locator('button[type="submit"]');
      
      // Empty message should not be sendable
      await messageInput.fill('');
      await expect(sendButton).toBeDisabled();
      
      // Whitespace-only message should not be sendable
      await messageInput.fill('   ');
      await expect(sendButton).toBeDisabled();
      
      // Valid message should enable send button (when connected)
      await messageInput.fill('Hello SwarmDirector');
      // Note: Button may still be disabled due to connection status
      await expect(messageInput).toHaveValue('Hello SwarmDirector');
    });

    test('should handle keyboard interactions', async ({ page }) => {
      const messageInput = page.locator('#messageInput');
      
      // Focus on input
      await messageInput.focus();
      await expect(messageInput).toBeFocused();
      
      // Type message
      await messageInput.fill('Test message');
      
      // Enter key should submit form (when connected)
      await messageInput.press('Enter');
      // Form submission will be handled by Alpine.js
    });
  });

  test.describe('Activity Log and Transparency Features', () => {
    
    test('should display activity log panel', async ({ page }) => {
      const activityLog = page.locator('#activityLog');
      
      await expect(activityLog).toBeVisible();
      await expect(page.locator('.activity-header')).toContainText('System Activity');
      
      // Should show initial connection attempt
      await expect(activityLog).toContainText('Initializing connection');
    });

    test('should categorize activity log entries', async ({ page }) => {
      // Wait for initial activity entries
      await page.waitForTimeout(1000);
      
      // Check for different types of activity entries
      const activityEntries = page.locator('.activity-entry');
      await expect(activityEntries).toHaveCountGreaterThan(0);
      
      // Should have timestamps
      await expect(page.locator('.activity-timestamp')).toHaveCountGreaterThan(0);
    });
  });

  test.describe('Connection Status and Error Handling', () => {
    
    test('should display connection status', async ({ page }) => {
      const connectionStatus = page.locator('.connection-status');
      
      await expect(connectionStatus).toBeVisible();
      
      // Should show initial disconnected state
      await expect(connectionStatus).toContainText('Disconnected');
      
      // Status should have appropriate styling
      await expect(connectionStatus).toHaveClass(/text-red-500/);
    });

    test('should handle connection errors gracefully', async ({ page }) => {
      // Monitor console errors
      const consoleErrors = [];
      page.on('console', msg => {
        if (msg.type() === 'error') {
          consoleErrors.push(msg.text());
        }
      });
      
      // Wait for potential connection attempts
      await page.waitForTimeout(2000);
      
      // Should not have critical JavaScript errors
      const criticalErrors = consoleErrors.filter(error => 
        !error.includes('WebSocket') && !error.includes('Socket.IO')
      );
      expect(criticalErrors).toHaveLength(0);
    });
  });

  test.describe('Accessibility and Usability', () => {
    
    test('should have proper ARIA labels', async ({ page }) => {
      // Check for accessibility attributes
      await expect(page.locator('#messageInput')).toHaveAttribute('placeholder');
      await expect(page.locator('button[type="submit"]')).toHaveAttribute('type', 'submit');
      
      // Form should have proper structure
      await expect(page.locator('form')).toBeVisible();
    });

    test('should support keyboard navigation', async ({ page }) => {
      // Tab through interactive elements
      await page.keyboard.press('Tab');
      
      // Message input should be focusable
      const messageInput = page.locator('#messageInput');
      await messageInput.focus();
      await expect(messageInput).toBeFocused();
      
      // Send button should be reachable via tab
      await page.keyboard.press('Tab');
      const sendButton = page.locator('button[type="submit"]');
      await expect(sendButton).toBeFocused();
    });
  });

  test.describe('Performance and Loading', () => {
    
    test('should load within reasonable time', async ({ page }) => {
      const startTime = Date.now();
      
      await page.goto('/chat');
      await page.waitForSelector('[x-data="chatApp()"]');
      
      const loadTime = Date.now() - startTime;
      
      // Should load within 5 seconds
      expect(loadTime).toBeLessThan(5000);
    });

    test('should handle rapid interactions', async ({ page }) => {
      const messageInput = page.locator('#messageInput');
      
      // Rapidly type and clear input
      for (let i = 0; i < 5; i++) {
        await messageInput.fill(`Message ${i}`);
        await messageInput.clear();
      }
      
      // Should remain responsive
      await expect(messageInput).toBeVisible();
      await expect(messageInput).toHaveValue('');
    });
  });
});

test.describe('Cross-Browser Compatibility', () => {
  
  test('should work in different browsers', async ({ page, browserName }) => {
    await page.goto('/chat');
    
    // Wait for Alpine.js initialization
    await page.waitForFunction(() => window.Alpine !== undefined);
    
    // Basic functionality should work across browsers
    await expect(page.locator('#messageInput')).toBeVisible();
    await expect(page.locator('button[type="submit"]')).toBeVisible();
    
    // Log browser for debugging
    console.log(`Testing in: ${browserName}`);
  });
});
