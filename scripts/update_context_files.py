#!/usr/bin/env python3
"""
Script to systematically update task context files to be completely self-contained.
This script identifies areas that need improvement and provides a structured approach.
"""

import os
import re
import yaml
from pathlib import Path

class ContextFileUpdater:
    def __init__(self, context_dir=".taskmaster/context"):
        self.context_dir = Path(context_dir)
        self.issues_found = []
        
    def analyze_context_file(self, file_path):
        """Analyze a context file for completeness issues."""
        issues = []
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check YAML frontmatter
        if not content.startswith('---'):
            issues.append("Missing YAML frontmatter")
        else:
            try:
                yaml_end = content.find('---', 3)
                if yaml_end == -1:
                    issues.append("Malformed YAML frontmatter")
                else:
                    yaml_content = content[3:yaml_end]
                    metadata = yaml.safe_load(yaml_content)
                    
                    required_fields = ['task_id', 'title', 'status', 'priority', 'dependencies', 'created', 'updated']
                    for field in required_fields:
                        if field not in metadata:
                            issues.append(f"Missing YAML field: {field}")
            except yaml.YAMLError:
                issues.append("Invalid YAML frontmatter")
        
        # Check for required sections (both old and new formats)
        required_sections = [
            ('🎯 Overview', '🎯 Task Overview', '🎯 Subtask Overview'),
            ('📋 Metadata', '📋 Metadata'),
            ('🗒️ Scope, Assumptions & Constraints', '🗒️ Scope, Assumptions & Constraints'),
            ('🔍 Detailed Description', '🔍 1. Detailed Description'),
            ('📁 Reference Artifacts & Files', '📁 2. Reference Artifacts & Files'),
            ('🔧 Interfaces & Code Snippets', '🔧 3. Interfaces & Code Snippets'),
            ('🛠️ Implementation Plan', '🛠️ 5. Implementation Plan'),
            ('🧪 Testing & QA', '🧪 6. Testing & QA'),
            ('🔗 Integration & Related Tasks', '🔗 7. Integration & Related Tasks'),
            ('⚠️ Risks & Mitigations', '⚠️ 8. Risks & Mitigations'),
            ('✅ Success Criteria', '✅ 9. Success Criteria'),
            ('🚀 Next Steps', '🚀 10. Next Steps')
        ]

        for section_variants in required_sections:
            section_found = False
            for variant in section_variants:
                if variant in content:
                    section_found = True
                    break
            if not section_found:
                issues.append(f"Missing section: {section_variants[0]}")
        
        # Check for specific version numbers in dependencies
        if '📦' in content and 'Dependencies' in content:
            # Look for vague version specifications
            if re.search(r'\^[\d.]+|\~[\d.]+|>=[\d.]+', content):
                issues.append("Vague version specifications found (use exact versions)")
        
        # Check for external references
        external_refs = re.findall(r'https?://[^\s\)]+', content)
        if external_refs:
            issues.append(f"External references found: {len(external_refs)} links")
        
        # Check for incomplete code examples
        code_blocks = re.findall(r'```[\s\S]*?```', content)
        for i, block in enumerate(code_blocks):
            if '...' in block or 'TODO' in block or 'PLACEHOLDER' in block:
                issues.append(f"Incomplete code block #{i+1}")
        
        # Check success criteria specificity
        if '✅' in content:
            success_section = re.search(r'✅.*?(?=##|$)', content, re.DOTALL)
            if success_section:
                criteria_text = success_section.group(0)
                if 'functionality implemented' in criteria_text.lower():
                    issues.append("Vague success criteria (avoid generic terms)")
        
        return issues
    
    def scan_all_context_files(self):
        """Scan all context files and identify issues."""
        results = {}
        
        for task_dir in self.context_dir.iterdir():
            if task_dir.is_dir() and task_dir.name.startswith('task_'):
                task_id = task_dir.name
                results[task_id] = {}
                
                # Check main task file
                main_task_file = task_dir / 'task.md'
                if main_task_file.exists():
                    issues = self.analyze_context_file(main_task_file)
                    results[task_id]['main'] = issues
                
                # Check subtask files
                for subtask_file in task_dir.glob('subtask_*.md'):
                    subtask_id = subtask_file.stem
                    issues = self.analyze_context_file(subtask_file)
                    results[task_id][subtask_id] = issues
        
        return results
    
    def generate_improvement_report(self, results):
        """Generate a report of improvements needed."""
        report = []
        report.append("# Context Files Improvement Report")
        report.append("=" * 50)
        report.append("")
        
        total_issues = 0
        for task_id, task_results in results.items():
            task_issues = sum(len(issues) for issues in task_results.values())
            total_issues += task_issues
            
            if task_issues > 0:
                report.append(f"## {task_id.upper()} ({task_issues} issues)")
                
                for file_type, issues in task_results.items():
                    if issues:
                        report.append(f"### {file_type}")
                        for issue in issues:
                            report.append(f"- {issue}")
                        report.append("")
        
        report.append(f"## Summary")
        report.append(f"Total issues found: {total_issues}")
        report.append(f"Files analyzed: {sum(len(task_results) for task_results in results.values())}")
        
        return "\n".join(report)
    
    def get_priority_updates(self, results):
        """Identify highest priority updates needed."""
        priorities = []
        
        for task_id, task_results in results.items():
            for file_type, issues in task_results.items():
                # High priority issues
                high_priority = [
                    issue for issue in issues 
                    if any(keyword in issue.lower() for keyword in [
                        'missing yaml', 'missing section', 'vague version', 
                        'incomplete code', 'external references'
                    ])
                ]
                
                if high_priority:
                    priorities.append({
                        'task': task_id,
                        'file': file_type,
                        'issues': high_priority,
                        'priority': 'HIGH'
                    })
        
        return sorted(priorities, key=lambda x: len(x['issues']), reverse=True)

def main():
    """Main execution function."""
    updater = ContextFileUpdater()
    
    print("Scanning context files for completeness issues...")
    results = updater.scan_all_context_files()
    
    print("Generating improvement report...")
    report = updater.generate_improvement_report(results)
    
    # Save report to file
    with open('context_improvement_report.md', 'w') as f:
        f.write(report)
    
    print("Report saved to: context_improvement_report.md")
    
    # Show priority updates
    priorities = updater.get_priority_updates(results)
    print(f"\nTop 5 Priority Updates:")
    for i, item in enumerate(priorities[:5], 1):
        print(f"{i}. {item['task']}/{item['file']}: {len(item['issues'])} issues")

if __name__ == "__main__":
    main()
