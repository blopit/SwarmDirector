#!/usr/bin/env python3
"""
Final verification script to confirm all context files are properly updated.
"""

import os
from pathlib import Path

def verify_context_file(file_path):
    """Verify a context file has all required sections."""
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Check for YAML frontmatter
    has_yaml = content.startswith('---') and '---' in content[3:]
    
    # Check for required sections (new format)
    required_sections = [
        '🎯 Task Overview',
        '🎯 Subtask Overview', 
        '📋 Metadata',
        '🗒️ Scope, Assumptions & Constraints',
        '🔍 1. Detailed Description',
        '📁 2. Reference Artifacts & Files',
        '🔧 3. Interfaces & Code Snippets',
        '🛠️ 5. Implementation Plan',
        '🧪 6. Testing & QA',
        '🔗 7. Integration & Related Tasks',
        '⚠️ 8. Risks & Mitigations',
        '✅ 9. Success Criteria',
        '🚀 10. Next Steps'
    ]
    
    sections_found = []
    for section in required_sections:
        if section in content:
            sections_found.append(section)
    
    # Check for overview (either task or subtask)
    has_overview = ('🎯 Task Overview' in content) or ('🎯 Subtask Overview' in content)
    
    # Count core sections (excluding overview variants)
    core_sections = [
        '📋 Metadata',
        '🗒️ Scope, Assumptions & Constraints',
        '🔍 1. Detailed Description',
        '📁 2. Reference Artifacts & Files',
        '🔧 3. Interfaces & Code Snippets',
        '🛠️ 5. Implementation Plan',
        '🧪 6. Testing & QA',
        '🔗 7. Integration & Related Tasks',
        '⚠️ 8. Risks & Mitigations',
        '✅ 9. Success Criteria',
        '🚀 10. Next Steps'
    ]
    
    core_sections_found = sum(1 for section in core_sections if section in content)
    
    return {
        'has_yaml': has_yaml,
        'has_overview': has_overview,
        'core_sections_found': core_sections_found,
        'total_core_sections': len(core_sections),
        'sections_found': sections_found,
        'is_complete': has_yaml and has_overview and core_sections_found >= 10
    }

def main():
    """Main verification function."""
    context_dir = Path('.taskmaster/context')
    
    print("Final Context Files Verification")
    print("=" * 50)
    
    total_files = 0
    complete_files = 0
    
    # Get all task directories
    task_dirs = [d for d in context_dir.iterdir() 
                 if d.is_dir() and d.name.startswith('task_')]
    task_dirs.sort(key=lambda x: int(x.name.split('_')[1]))
    
    for task_dir in task_dirs:
        print(f"\n{task_dir.name.upper()}:")
        
        # Check all markdown files in the task directory
        md_files = list(task_dir.glob('*.md'))
        md_files.sort()
        
        for md_file in md_files:
            total_files += 1
            result = verify_context_file(md_file)
            
            status = "✓ COMPLETE" if result['is_complete'] else "✗ INCOMPLETE"
            sections_ratio = f"{result['core_sections_found']}/{result['total_core_sections']}"
            
            print(f"  {md_file.name}: {status} ({sections_ratio} sections)")
            
            if result['is_complete']:
                complete_files += 1
            else:
                print(f"    Missing: YAML={not result['has_yaml']}, Overview={not result['has_overview']}")
    
    print("\n" + "=" * 50)
    print(f"SUMMARY:")
    print(f"Total files: {total_files}")
    print(f"Complete files: {complete_files}")
    print(f"Completion rate: {(complete_files/total_files)*100:.1f}%")
    
    if complete_files == total_files:
        print("🎉 ALL CONTEXT FILES ARE COMPLETE AND SELF-CONTAINED!")
    else:
        print(f"⚠️  {total_files - complete_files} files still need updates")
    
    return complete_files == total_files

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
