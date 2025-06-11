#!/usr/bin/env python3
"""
Task Context Updater for Repository Reorganization

This script updates all task context files to reflect the new repository structure
after the comprehensive reorganization of SwarmDirector.
"""

import os
import re
import json
from pathlib import Path
from datetime import datetime

class TaskContextUpdater:
    def __init__(self):
        self.project_root = Path(__file__).parent.parent
        self.context_dir = self.project_root / ".taskmaster" / "context"
        self.tasks_file = self.project_root / ".taskmaster" / "tasks" / "tasks.json"
        
        # New repository structure mappings
        self.structure_updates = {
            # Old paths -> New paths
            "app.py": "src/swarm_director/app.py",
            "config.py": "src/swarm_director/config.py",
            "agents/": "src/swarm_director/agents/",
            "models/": "src/swarm_director/models/",
            "utils/": "src/swarm_director/utils/",
            "static/": "src/swarm_director/web/static/",
            "templates/": "src/swarm_director/web/templates/",
            "test_*.py": "tests/",
            "migrations/": "database/migrations/",
            "*.sql": "database/schemas/",
            "*.db": "database/data/",
            "demo_app.py": "examples/demo_app.py",
            "comprehensive_context_updater.py": "scripts/comprehensive_context_updater.py",
            "update_context_files.py": "scripts/update_context_files.py",
            "validate_context_files.py": "scripts/validate_context_files.py",
            "final_verification.py": "scripts/final_verification.py"
        }
        
        # New documentation structure
        self.new_docs = {
            "PROJECT_STRUCTURE.md": "docs/PROJECT_STRUCTURE.md",
            "CONTRIBUTING.md": "docs/CONTRIBUTING.md", 
            "CHANGELOG.md": "docs/CHANGELOG.md",
            "API_REFERENCE.md": "docs/api/README.md",
            "ARCHITECTURE.md": "docs/architecture/overview.md",
            "DEVELOPMENT_GUIDE.md": "docs/development/getting_started.md",
            "DEPLOYMENT_GUIDE.md": "docs/deployment/local_development.md"
        }

    def load_tasks_data(self):
        """Load tasks data from tasks.json."""
        try:
            with open(self.tasks_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading tasks data: {e}")
            return {"tasks": []}

    def update_file_references(self, content):
        """Update file references in content to reflect new structure."""
        updated_content = content
        
        # Update specific file paths
        for old_path, new_path in self.structure_updates.items():
            # Handle different reference patterns
            patterns = [
                f"`{old_path}`",
                f"**{old_path}**",
                f"- {old_path}",
                f"/{old_path}",
                f"./{old_path}",
                f"{old_path}:",
                f"in {old_path}",
                f"from {old_path}",
                f"import {old_path}"
            ]
            
            for pattern in patterns:
                if old_path in pattern:
                    new_pattern = pattern.replace(old_path, new_path)
                    updated_content = updated_content.replace(pattern, new_pattern)
        
        return updated_content

    def update_project_structure_section(self, content):
        """Update the project structure section with new organization."""
        new_structure = """
### Primary Implementation Files:
```
SwarmDirector/
├── src/                          # Source code
│   └── swarm_director/          # Main application package
│       ├── __init__.py          # Package initialization
│       ├── app.py               # Flask application
│       ├── config.py            # Configuration
│       ├── agents/              # AI agent implementations
│       ├── models/              # Database models
│       ├── utils/               # Utility functions
│       └── web/                 # Web interface
│           ├── static/          # Static assets
│           └── templates/       # Jinja2 templates
├── tests/                       # Test suite
├── scripts/                     # Utility scripts
├── examples/                    # Demo applications
├── docs/                        # Documentation
│   ├── api/                     # API documentation
│   ├── architecture/            # System architecture
│   ├── deployment/              # Deployment guides
│   └── development/             # Development guides
├── database/                    # Database files and schemas
│   ├── schemas/                 # Schema definitions
│   ├── migrations/              # Alembic migrations
│   └── data/                    # Database files
├── reports/                     # Generated reports
└── logs/                        # Application logs
```

### Configuration Files:
- **src/swarm_director/config.py**: Application configuration classes
- **.env**: Environment variables (create from template)
- **requirements.txt**: Python dependencies
- **run.py**: Application launcher script

### Key Documentation:
- **README.md**: Project overview and quick start
- **docs/PROJECT_STRUCTURE.md**: Detailed project organization
- **docs/api/README.md**: API documentation
- **docs/architecture/overview.md**: System architecture
- **docs/development/getting_started.md**: Developer guide
- **QUICKSTART.md**: 1-minute setup guide
"""
        
        # Replace the existing structure section
        pattern = r"### Primary Implementation Files:.*?(?=###|\n---|\n##|$)"
        if re.search(pattern, content, re.DOTALL):
            updated_content = re.sub(pattern, new_structure.strip(), content, flags=re.DOTALL)
        else:
            # If pattern not found, append to the file references section
            file_ref_pattern = r"(## 📁 2\. Reference Artifacts & Files.*?)(\n---|\n##)"
            if re.search(file_ref_pattern, content, re.DOTALL):
                updated_content = re.sub(
                    file_ref_pattern, 
                    r"\1" + new_structure + r"\2", 
                    content, 
                    flags=re.DOTALL
                )
            else:
                updated_content = content + new_structure
        
        return updated_content

    def update_interfaces_section(self, content):
        """Update interfaces and code snippets section."""
        new_interfaces = """
### Import Structure (New Package Organization):
```python
# Main application
from src.swarm_director.app import create_app

# Models
from src.swarm_director.models.agent import Agent, AgentType
from src.swarm_director.models.task import Task, TaskStatus
from src.swarm_director.models.conversation import Conversation

# Agents
from src.swarm_director.agents.director import DirectorAgent
from src.swarm_director.agents.base_agent import BaseAgent

# Utilities
from src.swarm_director.utils.database import get_database_info
from src.swarm_director.utils.logging import log_agent_action
```

### Application Startup:
```python
# Using the new launcher
python run.py

# Or directly
from src.swarm_director.app import create_app
app = create_app()
app.run(debug=True)
```

### Development Commands:
```bash
# Set up development environment
python scripts/setup_development.py

# Run tests
pytest tests/

# Verify installation
python scripts/verify_reorganization.py

# Update context files
python scripts/update_task_contexts_for_reorganization.py
```
"""
        
        # Find and update the interfaces section
        pattern = r"(## 🔧 3\. Interfaces & Code Snippets.*?)(?=\n---|\n##|$)"
        if re.search(pattern, content, re.DOTALL):
            updated_content = re.sub(
                pattern, 
                r"## 🔧 3. Interfaces & Code Snippets" + new_interfaces, 
                content, 
                flags=re.DOTALL
            )
        else:
            updated_content = content + "\n## 🔧 3. Interfaces & Code Snippets" + new_interfaces
        
        return updated_content

    def add_reorganization_context(self, content, task_id):
        """Add context about the repository reorganization."""
        reorganization_note = f"""
## 🏗️ Repository Reorganization Context

**Note**: This task context has been updated to reflect the comprehensive repository reorganization completed on {datetime.now().strftime('%Y-%m-%d')}.

### Key Changes:
- **Source code** moved to `src/swarm_director/` package structure
- **Tests** organized in dedicated `tests/` directory
- **Documentation** structured in `docs/` with comprehensive guides
- **Database files** organized in `database/` directory
- **Utility scripts** moved to `scripts/` directory
- **Examples** placed in `examples/` directory

### New Project Benefits:
- ✅ Professional Python package structure
- ✅ Comprehensive documentation (15+ guides)
- ✅ Improved developer experience with setup tools
- ✅ Clear separation of concerns
- ✅ Industry-standard organization

### Updated References:
All file paths and import statements in this context have been updated to reflect the new structure. See `docs/PROJECT_STRUCTURE.md` for complete details.

---
"""
        
        # Insert after the metadata section
        metadata_pattern = r"(## 📋 Metadata.*?)(\n---|\n##)"
        if re.search(metadata_pattern, content, re.DOTALL):
            updated_content = re.sub(
                metadata_pattern,
                r"\1" + reorganization_note + r"\2",
                content,
                flags=re.DOTALL
            )
        else:
            # Insert after overview if metadata not found
            overview_pattern = r"(## 🎯 Overview.*?)(\n---|\n##)"
            if re.search(overview_pattern, content, re.DOTALL):
                updated_content = re.sub(
                    overview_pattern,
                    r"\1" + reorganization_note + r"\2",
                    content,
                    flags=re.DOTALL
                )
            else:
                updated_content = reorganization_note + content
        
        return updated_content

    def update_task_file(self, task_file_path):
        """Update a single task context file."""
        print(f"Updating {task_file_path}")
        
        try:
            with open(task_file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract task ID from path
            task_id = task_file_path.parent.name
            
            # Apply updates
            updated_content = self.update_file_references(content)
            updated_content = self.update_project_structure_section(updated_content)
            updated_content = self.update_interfaces_section(updated_content)
            updated_content = self.add_reorganization_context(updated_content, task_id)
            
            # Write updated content
            with open(task_file_path, 'w', encoding='utf-8') as f:
                f.write(updated_content)
            
            print(f"✅ Updated {task_file_path}")
            return True
            
        except Exception as e:
            print(f"❌ Error updating {task_file_path}: {e}")
            return False

    def update_all_context_files(self):
        """Update all task context files."""
        print("🔄 Updating all task context files for repository reorganization...")
        print("=" * 70)
        
        updated_count = 0
        error_count = 0
        
        # Get all task directories
        task_dirs = [d for d in self.context_dir.iterdir() 
                     if d.is_dir() and d.name.startswith('task_')]
        
        task_dirs.sort(key=lambda x: int(x.name.split('_')[1]))
        
        for task_dir in task_dirs:
            print(f"\n📁 Processing {task_dir.name}...")
            
            # Update main task file
            main_task_file = task_dir / 'task.md'
            if main_task_file.exists():
                if self.update_task_file(main_task_file):
                    updated_count += 1
                else:
                    error_count += 1
            
            # Update subtask files
            subtask_files = list(task_dir.glob('subtask_*.md'))
            subtask_files.sort()
            
            for subtask_file in subtask_files:
                if self.update_task_file(subtask_file):
                    updated_count += 1
                else:
                    error_count += 1
        
        print("\n" + "=" * 70)
        print(f"📊 Update Summary:")
        print(f"✅ Successfully updated: {updated_count} files")
        print(f"❌ Errors: {error_count} files")
        print(f"📁 Task directories processed: {len(task_dirs)}")
        
        return updated_count, error_count

def main():
    """Main execution function."""
    print("🚀 SwarmDirector Task Context Updater for Repository Reorganization")
    print("=" * 70)
    print("This script updates all task context files to reflect the new repository structure.")
    print()
    
    updater = TaskContextUpdater()
    
    # Check if context directory exists
    if not updater.context_dir.exists():
        print(f"❌ Context directory not found: {updater.context_dir}")
        return False
    
    # Perform updates
    updated_count, error_count = updater.update_all_context_files()
    
    if error_count == 0:
        print("\n🎉 All task context files updated successfully!")
        print("\nNext steps:")
        print("1. Review updated context files in .taskmaster/context/")
        print("2. Verify changes with: python scripts/validate_context_files.py")
        print("3. Check the new project structure: docs/PROJECT_STRUCTURE.md")
        return True
    else:
        print(f"\n⚠️  Updates completed with {error_count} errors.")
        print("Please review the errors above and retry if needed.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
