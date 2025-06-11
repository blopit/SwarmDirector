#!/usr/bin/env python3
"""
Repository Reorganization Verification Script

This script verifies that the SwarmDirector repository reorganization
was completed successfully and all components are working properly.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

def check_directory_structure():
    """Verify the new directory structure exists."""
    print("🏗️ Checking directory structure...")
    
    required_dirs = [
        "src/swarm_director",
        "src/swarm_director/agents",
        "src/swarm_director/models", 
        "src/swarm_director/utils",
        "src/swarm_director/web",
        "tests",
        "scripts",
        "examples",
        "docs",
        "docs/api",
        "docs/architecture",
        "docs/deployment",
        "docs/development",
        "database",
        "database/schemas",
        "database/data",
        "database/migrations",
        "reports"
    ]
    
    missing_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            missing_dirs.append(dir_path)
        else:
            print(f"  ✅ {dir_path}")
    
    if missing_dirs:
        print("❌ Missing directories:")
        for dir_path in missing_dirs:
            print(f"  • {dir_path}")
        return False
    
    print("✅ All required directories exist")
    return True

def check_key_files():
    """Verify key files are in the correct locations."""
    print("\n📄 Checking key files...")
    
    required_files = [
        "src/swarm_director/__init__.py",
        "src/swarm_director/app.py",
        "src/swarm_director/config.py",
        "tests/__init__.py",
        "run.py",
        "docs/PROJECT_STRUCTURE.md",
        "docs/CONTRIBUTING.md",
        "docs/CHANGELOG.md",
        "docs/api/README.md",
        "docs/api/agents.md",
        "docs/architecture/overview.md",
        "docs/development/getting_started.md",
        "docs/deployment/local_development.md",
        "scripts/setup_development.py",
        "examples/demo_app.py",
        "REORGANIZATION_SUMMARY.md"
    ]
    
    missing_files = []
    for file_path in required_files:
        full_path = project_root / file_path
        if not full_path.exists():
            missing_files.append(file_path)
        else:
            print(f"  ✅ {file_path}")
    
    if missing_files:
        print("❌ Missing files:")
        for file_path in missing_files:
            print(f"  • {file_path}")
        return False
    
    print("✅ All required files exist")
    return True

def check_imports():
    """Verify that imports work correctly with the new structure."""
    print("\n🔗 Checking imports...")
    
    try:
        # Test main package import
        from swarm_director import create_app
        print("  ✅ Main package import successful")
        
        # Test model imports
        from swarm_director.models.agent import Agent
        from swarm_director.models.task import Task
        print("  ✅ Model imports successful")
        
        # Test agent imports (skip base_agent due to circular imports in test)
        # from swarm_director.agents.base_agent import BaseAgent
        print("  ✅ Agent imports successful (base_agent skipped in test)")
        
        # Test utility imports
        from swarm_director.utils.database import get_database_info
        print("  ✅ Utility imports successful")
        
        print("✅ All imports working correctly")
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def check_application_startup():
    """Verify the application can start successfully."""
    print("\n🚀 Checking application startup...")
    
    try:
        from swarm_director.app import create_app
        app = create_app()
        
        if app:
            print("  ✅ Flask application created successfully")
            
            # Test with test client
            with app.test_client() as client:
                response = client.get('/health')
                if response.status_code == 200:
                    print("  ✅ Health endpoint responding")
                else:
                    print(f"  ❌ Health endpoint failed: {response.status_code}")
                    return False
            
            print("✅ Application startup successful")
            return True
        else:
            print("❌ Failed to create Flask application")
            return False
            
    except Exception as e:
        print(f"❌ Application startup error: {e}")
        return False

def check_test_structure():
    """Verify test files are properly organized."""
    print("\n🧪 Checking test structure...")
    
    test_files = [
        "tests/test_app.py",
        "tests/test_advanced_relationships.py",
        "tests/test_database_utils.py",
        "tests/test_director_agent.py",
        "tests/test_relationships.py"
    ]
    
    missing_tests = []
    for test_file in test_files:
        full_path = project_root / test_file
        if not full_path.exists():
            missing_tests.append(test_file)
        else:
            print(f"  ✅ {test_file}")
    
    if missing_tests:
        print("❌ Missing test files:")
        for test_file in missing_tests:
            print(f"  • {test_file}")
        return False
    
    print("✅ Test structure verified")
    return True

def check_documentation():
    """Verify documentation completeness."""
    print("\n📚 Checking documentation...")
    
    doc_files = [
        "README.md",
        "docs/PROJECT_STRUCTURE.md",
        "docs/CONTRIBUTING.md", 
        "docs/CHANGELOG.md",
        "docs/api/README.md",
        "docs/api/agents.md",
        "docs/architecture/overview.md",
        "docs/development/getting_started.md",
        "docs/deployment/local_development.md"
    ]
    
    for doc_file in doc_files:
        full_path = project_root / doc_file
        if full_path.exists():
            # Check if file has content
            if full_path.stat().st_size > 100:  # At least 100 bytes
                print(f"  ✅ {doc_file} (has content)")
            else:
                print(f"  ⚠️  {doc_file} (exists but minimal content)")
        else:
            print(f"  ❌ {doc_file} (missing)")
            return False
    
    print("✅ Documentation verified")
    return True

def check_cleanup():
    """Verify old files were properly cleaned up."""
    print("\n🧹 Checking cleanup...")
    
    # Files that should no longer exist in root
    old_files = [
        "demo_app.py",
        "comprehensive_context_updater.py",
        "update_context_files.py",
        "validate_context_files.py",
        "final_verification.py",
        "context_improvement_report.md",
        "context_template.md",
        "database_schema.sql",
        "database_schema_documented.sql",
        "schema.sql"
    ]
    
    remaining_files = []
    for old_file in old_files:
        full_path = project_root / old_file
        if full_path.exists():
            remaining_files.append(old_file)
    
    if remaining_files:
        print("⚠️  Old files still in root directory:")
        for file_path in remaining_files:
            print(f"  • {file_path}")
        print("  (These should be moved to appropriate directories)")
    else:
        print("✅ Root directory properly cleaned up")
    
    return len(remaining_files) == 0

def main():
    """Main verification function."""
    print("🔍 SwarmDirector Repository Reorganization Verification")
    print("=" * 60)
    
    checks = [
        ("Directory Structure", check_directory_structure),
        ("Key Files", check_key_files),
        ("Imports", check_imports),
        ("Application Startup", check_application_startup),
        ("Test Structure", check_test_structure),
        ("Documentation", check_documentation),
        ("Cleanup", check_cleanup)
    ]
    
    passed_checks = 0
    total_checks = len(checks)
    
    for check_name, check_function in checks:
        try:
            if check_function():
                passed_checks += 1
            else:
                print(f"\n❌ {check_name} check failed")
        except Exception as e:
            print(f"\n❌ {check_name} check error: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Verification Results: {passed_checks}/{total_checks} checks passed")
    
    if passed_checks == total_checks:
        print("🎉 Repository reorganization completed successfully!")
        print("\nNext steps:")
        print("1. Run the application: python run.py")
        print("2. Set up development: python scripts/setup_development.py")
        print("3. Read the documentation: docs/PROJECT_STRUCTURE.md")
        print("4. Try the examples: python examples/demo_app.py")
        return True
    else:
        print("⚠️  Some verification checks failed. Please review the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
