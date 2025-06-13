// Global teardown for Playwright tests
async function globalTeardown(config) {
  console.log('🧹 Starting global teardown for SwarmDirector chat tests...');
  
  try {
    // Clean up any test artifacts if needed
    const fs = require('fs');
    const path = require('path');
    
    // Log test completion
    console.log('📊 Test execution completed');
    
    // Optional: Clean up temporary files (uncomment if needed)
    // const tempDir = path.join(process.cwd(), 'temp-test-files');
    // if (fs.existsSync(tempDir)) {
    //   fs.rmSync(tempDir, { recursive: true, force: true });
    //   console.log('🗑️  Cleaned up temporary test files');
    // }
    
    console.log('✅ Global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ Global teardown failed:', error.message);
    // Don't throw error in teardown to avoid masking test failures
  }
}

module.exports = globalTeardown; 