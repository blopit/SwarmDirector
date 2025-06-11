#!/usr/bin/env python3
"""
Test Artifact Cleanup Script for SwarmDirector

This script removes all test-related backup and migration directories,
database files, and other artifacts that may persist after test runs.
"""

import os
import shutil
import glob
from pathlib import Path

def cleanup_test_artifacts():
    """Remove all test artifacts from the project directory"""
    project_root = Path(__file__).parent.parent
    print(f"🧹 Cleaning test artifacts from: {project_root}")
    
    removed_count = 0
    
    # Remove timestamped test directories in project root
    patterns = [
        'test_backups_*',
        'test_migrations_*', 
        'pytest_backups_*',
        'pytest_migrations_*'
    ]
    
    for pattern in patterns:
        for path in glob.glob(str(project_root / pattern)):
            try:
                if os.path.isdir(path):
                    shutil.rmtree(path)
                    print(f"✅ Removed directory: {Path(path).name}")
                    removed_count += 1
            except (OSError, PermissionError) as e:
                print(f"❌ Could not remove {path}: {e}")
    
    # Remove test database files from instance directory
    instance_dir = project_root / "instance"
    if instance_dir.exists():
        db_patterns = ['*_test_*.db*', '*_pytest_*.db*']
        for pattern in db_patterns:
            for db_file in instance_dir.glob(pattern):
                try:
                    db_file.unlink()
                    print(f"✅ Removed database: {db_file.name}")
                    removed_count += 1
                except (OSError, PermissionError) as e:
                    print(f"❌ Could not remove {db_file}: {e}")
    
    # Remove temporary test files in project root
    temp_patterns = ['*_pytest_*.db*', 'test_*.db*']
    for pattern in temp_patterns:
        for temp_file in project_root.glob(pattern):
            try:
                temp_file.unlink()
                print(f"✅ Removed temp file: {temp_file.name}")
                removed_count += 1
            except (OSError, PermissionError) as e:
                print(f"❌ Could not remove {temp_file}: {e}")
    
    # Remove legacy test directories
    legacy_dirs = ['test_backups', 'test_migrations']
    for dir_name in legacy_dirs:
        dir_path = project_root / dir_name
        if dir_path.exists():
            try:
                shutil.rmtree(dir_path)
                print(f"✅ Removed legacy directory: {dir_name}")
                removed_count += 1
            except (OSError, PermissionError) as e:
                print(f"❌ Could not remove {dir_path}: {e}")
    
    if removed_count == 0:
        print("✨ No test artifacts found - project is clean!")
    else:
        print(f"🎉 Cleanup complete! Removed {removed_count} test artifacts.")
    
    return removed_count

def main():
    """Main function"""
    print("🚀 SwarmDirector Test Artifact Cleanup")
    print("=" * 50)
    
    try:
        cleanup_test_artifacts()
        print("=" * 50)
        print("✅ Test artifact cleanup completed successfully!")
        return True
    except Exception as e:
        print(f"❌ Cleanup failed: {e}")
        return False

if __name__ == "__main__":
    import sys
    success = main()
    sys.exit(0 if success else 1)
