#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test Runner Script for SwarmDirector
Runs all tests with comprehensive reporting and proper setup
"""

import os
import sys
import subprocess
import argparse
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Add src directory to Python path for proper imports
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Task management integration
try:
    from swarm_director.utils.automation import AutomationIntegrator, AutomationEventType, WorkflowStatus
    TASK_INTEGRATION_AVAILABLE = True
except ImportError:
    TASK_INTEGRATION_AVAILABLE = False
    print("⚠️  Task management integration not available")

def trigger_task_event(event_type, task_id=None, status=None, metadata=None):
    """Trigger task management events if integration is available."""
    if not TASK_INTEGRATION_AVAILABLE:
        return
    
    try:
        from swarm_director.utils.automation import trigger_task_automation
        trigger_task_automation(event_type, task_id or "test_run", metadata or {})
    except Exception as e:
        print(f"⚠️  Task event trigger failed: {e}")

def check_pytest_installation():
    """Check if pytest is installed, install if missing"""
    try:
        import pytest
        return True
    except ImportError:
        print("⚠️  pytest not found. Installing pytest...")
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", "pytest", "pytest-cov"])
            print("✅ pytest installed successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"❌ Failed to install pytest: {e}")
            return False


def run_pytest_tests(verbose=False, coverage=False, specific_test=None):
    """Run tests using pytest"""
    print("🧪 Running tests with pytest...")
    print("=" * 60)
    
    # Report test start
    trigger_task_event(AutomationEventType.TASK_STARTED, task_id="pytest_run", 
                      metadata={"test_type": "pytest", "coverage": coverage, "specific_test": specific_test})
    
    # Build pytest command
    cmd = [sys.executable, "-m", "pytest"]
    
    if verbose:
        cmd.append("-v")
    else:
        cmd.append("-q")
    
    if coverage:
        cmd.extend(["--cov=src/swarm_director", "--cov-report=term-missing", "--cov-report=html:reports/coverage"])
    
    # Add test directory
    test_dir = project_root / "tests"
    if specific_test:
        cmd.append(str(test_dir / specific_test))
    else:
        cmd.append(str(test_dir))
    
    # Add output formatting
    cmd.extend(["--tb=short", "--color=yes"])
    
    # Set environment variables for proper imports
    env = os.environ.copy()
    env['PYTHONPATH'] = f"{src_path}:{project_root}:{env.get('PYTHONPATH', '')}"
    
    try:
        result = subprocess.run(cmd, cwd=project_root, capture_output=False, env=env)
        success = result.returncode == 0
        
        if success:
            trigger_task_event(AutomationEventType.TASK_COMPLETED, task_id="pytest_run",
                              metadata={"test_passed": True, "exit_code": result.returncode})
        else:
            trigger_task_event(AutomationEventType.TASK_FAILED, task_id="pytest_run",
                              metadata={"test_passed": False, "exit_code": result.returncode})
        
        return success
    except subprocess.CalledProcessError as e:
        print(f"❌ pytest execution failed: {e}")
        trigger_task_event(AutomationEventType.TASK_FAILED, task_id="pytest_run",
                          metadata={"error": str(e), "execution_failed": True})
        return False


def run_standalone_tests():
    """Run tests that have their own run functions for backwards compatibility"""
    print("🔧 Running standalone test functions...")
    print("=" * 60)
    
    success = True
    test_files = [
        "test_app.py",
        "test_database_utils.py",
        "test_director_agent.py"
    ]
    
    # Set up environment for proper imports
    old_path = sys.path[:]
    sys.path.insert(0, str(src_path))
    
    try:
        for test_file in test_files:
            test_path = project_root / "tests" / test_file
            if test_path.exists():
                print(f"\n📋 Running {test_file}...")
                try:
                    # Import and run the test if it has a run function
                    module_name = test_file.replace('.py', '')
                    spec = __import__(f"tests.{module_name}", fromlist=[module_name])
                    if hasattr(spec, 'run_tests'):
                        result = spec.run_tests()
                        if not result:
                            success = False
                            print(f"❌ {test_file} failed")
                        else:
                            print(f"✅ {test_file} passed")
                    else:
                        print(f"⚠️  {test_file} has no run_tests function, skipping standalone run")
                except Exception as e:
                    print(f"❌ Error running {test_file}: {e}")
                    success = False
    finally:
        sys.path[:] = old_path
    
    return success


def create_reports_directory():
    """Ensure reports directory exists"""
    reports_dir = project_root / "reports"
    reports_dir.mkdir(exist_ok=True)
    return reports_dir


def main():
    """Main test runner function"""
    parser = argparse.ArgumentParser(description="Run SwarmDirector tests")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")
    parser.add_argument("-c", "--coverage", action="store_true", help="Run with coverage reporting")
    parser.add_argument("-s", "--standalone", action="store_true", help="Run standalone test functions only")
    parser.add_argument("-p", "--pytest-only", action="store_true", help="Run pytest tests only")
    parser.add_argument("-t", "--test", help="Run specific test file")
    parser.add_argument("--install-deps", action="store_true", help="Install missing test dependencies")
    
    args = parser.parse_args()
    
    print("🚀 SwarmDirector Test Runner")
    print("=" * 60)
    print(f"📁 Project root: {project_root}")
    print(f"🐍 Python version: {sys.version}")
    print(f"📂 Source path: {src_path}")
    
    # Initialize task tracking for test run
    trigger_task_event(AutomationEventType.TASK_STARTED, task_id="test_suite", 
                      metadata={"test_runner": "main", "args": vars(args)})
    
    # Create reports directory
    reports_dir = create_reports_directory()
    print(f"📊 Reports directory: {reports_dir}")
    
    # Check and install pytest if needed
    if args.install_deps or not args.standalone:
        if not check_pytest_installation():
            print("❌ Cannot proceed without pytest")
            trigger_task_event(AutomationEventType.TASK_FAILED, task_id="test_suite",
                              metadata={"reason": "pytest_installation_failed"})
            return False
    
    success = True
    
    # Run tests based on arguments
    if args.standalone:
        success = run_standalone_tests()
    elif args.pytest_only:
        success = run_pytest_tests(args.verbose, args.coverage, args.test)
    else:
        # Run both pytest and standalone tests
        print("\n🎯 Running comprehensive test suite...")
        pytest_success = run_pytest_tests(args.verbose, args.coverage, args.test)
        standalone_success = run_standalone_tests()
        success = pytest_success and standalone_success
    
    # Final results
    print("\n" + "=" * 60)
    if success:
        print("🎉 All tests passed!")
        if args.coverage:
            print(f"📊 Coverage report available at: {reports_dir}/coverage/index.html")
        trigger_task_event(AutomationEventType.TASK_COMPLETED, task_id="test_suite",
                          metadata={"all_tests_passed": True, "coverage_enabled": args.coverage})
    else:
        print("❌ Some tests failed. Check output above for details.")
        trigger_task_event(AutomationEventType.TASK_FAILED, task_id="test_suite",
                          metadata={"tests_failed": True})
    
    print("=" * 60)
    return success


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1) 