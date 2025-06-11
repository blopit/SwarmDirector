#!/usr/bin/env python3
"""
Script to validate context files for consistency and correctness.
"""

import json
import os
import yaml
from pathlib import Path

def load_tasks():
    """Load tasks from the JSON file."""
    with open('.taskmaster/tasks/tasks.json', 'r') as f:
        return json.load(f)

def validate_yaml_frontmatter(file_path):
    """Validate YAML frontmatter in a markdown file."""
    issues = []
    
    try:
        with open(file_path, 'r') as f:
            content = f.read()
        
        # Check if file starts with ---
        if not content.startswith('---\n'):
            issues.append("Missing YAML frontmatter start marker")
            return issues
        
        # Find the end of frontmatter
        end_marker = content.find('\n---\n', 4)
        if end_marker == -1:
            issues.append("Missing YAML frontmatter end marker")
            return issues
        
        # Extract and parse YAML
        yaml_content = content[4:end_marker]
        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            issues.append(f"Invalid YAML syntax: {e}")
            return issues
        
        # Check required fields
        required_fields = ['task_id', 'title', 'status', 'priority', 'dependencies', 'created', 'updated']
        for field in required_fields:
            if field not in frontmatter:
                issues.append(f"Missing required field: {field}")
        
        # Validate field values
        if 'status' in frontmatter and frontmatter['status'] not in ['pending', 'in progress', 'blocked', 'done']:
            issues.append(f"Invalid status: {frontmatter['status']}")
        
        if 'priority' in frontmatter and frontmatter['priority'] not in ['low', 'medium', 'high', 'critical']:
            issues.append(f"Invalid priority: {frontmatter['priority']}")
        
        return issues, frontmatter
        
    except Exception as e:
        return [f"Error reading file: {e}"], None

def validate_task_references(tasks_data):
    """Validate that task references are consistent."""
    issues = []
    
    # Build reference maps
    task_ids = {f"task_{task['id']:03d}" for task in tasks_data['tasks']}
    subtask_refs = {}
    
    for task in tasks_data['tasks']:
        task_id = f"task_{task['id']:03d}"
        for subtask in task.get('subtasks', []):
            subtask_id = f"subtask_{subtask['id']:03d}"
            subtask_refs[f"{task_id}/{subtask_id}"] = True
    
    # Check all context files
    context_dir = Path('.taskmaster/context')
    for task_dir in context_dir.iterdir():
        if not task_dir.is_dir():
            continue
            
        for file_path in task_dir.glob('*.md'):
            if file_path.name == 'README.md':
                continue
                
            file_issues, frontmatter = validate_yaml_frontmatter(file_path)
            if file_issues:
                issues.extend([f"{file_path}: {issue}" for issue in file_issues])
                continue
            
            if not frontmatter:
                continue
            
            # Validate task_id format
            task_id = frontmatter.get('task_id')
            if task_id and task_id not in task_ids:
                issues.append(f"{file_path}: Invalid task_id reference: {task_id}")
            
            # Validate dependencies
            deps = frontmatter.get('dependencies', [])
            if isinstance(deps, list):
                for dep in deps:
                    if isinstance(dep, str):
                        if dep.startswith('task_') and '/' not in dep:
                            if dep not in task_ids:
                                issues.append(f"{file_path}: Invalid task dependency: {dep}")
                        elif '/' in dep:
                            if dep not in subtask_refs:
                                issues.append(f"{file_path}: Invalid subtask dependency: {dep}")
    
    return issues

def validate_file_structure():
    """Validate that all expected files exist."""
    issues = []
    tasks_data = load_tasks()
    
    for task in tasks_data['tasks']:
        task_id = f"task_{task['id']:03d}"
        task_dir = Path(f".taskmaster/context/{task_id}")
        
        # Check task directory exists
        if not task_dir.exists():
            issues.append(f"Missing task directory: {task_dir}")
            continue
        
        # Check main task file
        task_file = task_dir / "task.md"
        if not task_file.exists():
            issues.append(f"Missing main task file: {task_file}")
        
        # Check subtask files
        for subtask in task.get('subtasks', []):
            subtask_file = task_dir / f"subtask_{subtask['id']:03d}.md"
            if not subtask_file.exists():
                issues.append(f"Missing subtask file: {subtask_file}")
    
    return issues

def validate_content_consistency():
    """Validate content consistency between JSON and markdown files."""
    issues = []
    tasks_data = load_tasks()
    
    for task in tasks_data['tasks']:
        task_id = f"task_{task['id']:03d}"
        task_file = Path(f".taskmaster/context/{task_id}/task.md")
        
        if task_file.exists():
            file_issues, frontmatter = validate_yaml_frontmatter(task_file)
            if not file_issues and frontmatter:
                # Check title consistency
                if frontmatter.get('title') != task['title']:
                    issues.append(f"{task_file}: Title mismatch - JSON: '{task['title']}', File: '{frontmatter.get('title')}'")
                
                # Check status consistency
                if frontmatter.get('status') != task['status']:
                    issues.append(f"{task_file}: Status mismatch - JSON: '{task['status']}', File: '{frontmatter.get('status')}'")
                
                # Check priority consistency
                if frontmatter.get('priority') != task['priority']:
                    issues.append(f"{task_file}: Priority mismatch - JSON: '{task['priority']}', File: '{frontmatter.get('priority')}'")
        
        # Check subtasks
        for subtask in task.get('subtasks', []):
            subtask_file = Path(f".taskmaster/context/{task_id}/subtask_{subtask['id']:03d}.md")
            
            if subtask_file.exists():
                file_issues, frontmatter = validate_yaml_frontmatter(subtask_file)
                if not file_issues and frontmatter:
                    # Check title consistency
                    if frontmatter.get('title') != subtask['title']:
                        issues.append(f"{subtask_file}: Title mismatch - JSON: '{subtask['title']}', File: '{frontmatter.get('title')}'")
                    
                    # Check status consistency
                    if frontmatter.get('status') != subtask['status']:
                        issues.append(f"{subtask_file}: Status mismatch - JSON: '{subtask['status']}', File: '{frontmatter.get('status')}'")
    
    return issues

def main():
    """Main validation function."""
    print("🔍 Validating context files...")
    
    all_issues = []
    
    # Validate file structure
    print("📁 Checking file structure...")
    structure_issues = validate_file_structure()
    all_issues.extend(structure_issues)
    
    # Validate task references
    print("🔗 Checking task references...")
    tasks_data = load_tasks()
    reference_issues = validate_task_references(tasks_data)
    all_issues.extend(reference_issues)
    
    # Validate content consistency
    print("📝 Checking content consistency...")
    content_issues = validate_content_consistency()
    all_issues.extend(content_issues)
    
    # Report results
    if all_issues:
        print(f"\n❌ Found {len(all_issues)} issues:")
        for issue in all_issues:
            print(f"  - {issue}")
    else:
        print("\n✅ All context files are valid!")
    
    return len(all_issues) == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
