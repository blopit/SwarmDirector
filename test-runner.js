#!/usr/bin/env node

const { spawn } = require('child_process');
const { exec } = require('child_process');
const path = require('path');

let flaskProcess = null;

async function startFlaskServer() {
  return new Promise((resolve, reject) => {
    console.log('🚀 Starting Flask server...');
    
    flaskProcess = spawn('python', ['run.py'], {
      cwd: process.cwd(),
      stdio: ['pipe', 'pipe', 'pipe'],
      env: { ...process.env, FLASK_PORT: '5001' }
    });

    let serverReady = false;
    
    flaskProcess.stdout.on('data', (data) => {
      const output = data.toString();
      console.log(output);
      
      if ((output.includes('Running on http://127.0.0.1:5001') || output.includes('Debugger is active!')) && !serverReady) {
        serverReady = true;
        console.log('✅ Flask server is ready!');
        setTimeout(resolve, 2000); // Give it 2 seconds to fully initialize
      }
    });

    flaskProcess.stderr.on('data', (data) => {
      const output = data.toString();
      console.error(`Flask stderr: ${output}`);
      
      if ((output.includes('Running on http://127.0.0.1:5001') || output.includes('Debugger is active!')) && !serverReady) {
        serverReady = true;
        console.log('✅ Flask server is ready!');
        setTimeout(resolve, 2000); // Give it 2 seconds to fully initialize
      }
    });

    flaskProcess.on('error', (error) => {
      console.error(`Failed to start Flask server: ${error}`);
      reject(error);
    });

    // Timeout after 30 seconds
    setTimeout(() => {
      if (!serverReady) {
        reject(new Error('Flask server failed to start within 30 seconds'));
      }
    }, 30000);
  });
}

async function runPlaywrightTests() {
  return new Promise((resolve, reject) => {
    console.log('🧪 Running Playwright tests...');
    
    const testProcess = spawn('npx', ['playwright', 'test'], {
      cwd: process.cwd(),
      stdio: 'inherit'
    });

    testProcess.on('close', (code) => {
      if (code === 0) {
        console.log('✅ All tests passed!');
        resolve();
      } else {
        console.log(`❌ Tests failed with exit code ${code}`);
        reject(new Error(`Tests failed with exit code ${code}`));
      }
    });

    testProcess.on('error', (error) => {
      console.error(`Failed to run tests: ${error}`);
      reject(error);
    });
  });
}

function cleanup() {
  if (flaskProcess) {
    console.log('🧹 Stopping Flask server...');
    flaskProcess.kill('SIGTERM');
    
    // Force kill if it doesn't stop gracefully
    setTimeout(() => {
      if (flaskProcess && !flaskProcess.killed) {
        flaskProcess.kill('SIGKILL');
      }
    }, 5000);
  }
}

async function main() {
  try {
    // Handle cleanup on exit
    process.on('SIGINT', cleanup);
    process.on('SIGTERM', cleanup);
    process.on('exit', cleanup);

    // Start Flask server
    await startFlaskServer();
    
    // Run tests
    await runPlaywrightTests();
    
    console.log('🎉 Test run completed successfully!');
    
  } catch (error) {
    console.error('❌ Test run failed:', error.message);
    process.exit(1);
  } finally {
    cleanup();
    process.exit(0);
  }
}

main(); 