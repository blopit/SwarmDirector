---
task_id: task_001
subtask_id: subtask_001
title: Environment Setup and Project Structure
status: pending
priority: high
parent_task: task_001
dependencies: []
created: 2025-06-10
updated: 2025-06-10
---

# 🎯 Subtask Overview
Create the project directory structure and set up the Python virtual environment with required dependencies

## 📋 Metadata
- **ID**: task_001 / subtask_001
- **Title**: Environment Setup and Project Structure
- **Status**: pending
- **Priority**: high
- **Parent Task**: task_001
- **Dependencies**: []
- **Created / Updated**: 2025-06-10

## 🗒️ Scope, Assumptions & Constraints
- **In Scope**: Create the project directory structure and set up the Python virtual environment with required dependencies
- **Out of Scope**: Features handled by other subtasks
- **Assumptions**: Dependencies completed, required tools available
- **Constraints**: Must integrate with parent task architecture

---

## 🔍 1. Detailed Description

This subtask establishes the foundational project structure and development environment for the SwarmDirector application. It involves creating a clean project directory, setting up Python virtual environment isolation, installing all required dependencies with specific versions, and organizing the complete directory structure that will support the hierarchical AI agent system.

### Key Components:
1. **Project Directory Creation**: Establish the root SwarmDirector directory
2. **Virtual Environment Setup**: Create isolated Python environment with proper activation
3. **Dependency Installation**: Install Flask, SQLAlchemy, AutoGen, and all supporting packages
4. **Directory Structure**: Create organized folder hierarchy for agents, models, utils, templates
5. **Configuration Files**: Set up requirements.txt, .env template, and .gitignore
6. **Verification**: Ensure all components are properly installed and accessible

## 📁 2. Reference Artifacts & Files

### Primary Files Created:
- **SwarmDirector/** (project root directory)
- **venv/** (virtual environment)
- **requirements.txt** (dependency specifications)
- **.env.template** (environment variable template)
- **.gitignore** (version control exclusions)
- **README.md** (project documentation)

### Directory Structure Created:
```
SwarmDirector/
├── venv/                     # Virtual environment (not committed)
├── requirements.txt          # Python dependencies
├── .env.template            # Environment variables template
├── .env                     # Environment variables (not committed)
├── .gitignore              # Git ignore rules
├── README.md               # Project documentation
├── instance/               # Instance-specific files
├── migrations/             # Database migrations (created later)
├── models/                 # SQLAlchemy models
│   └── __init__.py
├── agents/                 # AI agent implementations
│   └── __init__.py
├── utils/                  # Utility functions
│   └── __init__.py
├── templates/              # Jinja2 templates
├── static/                 # Static assets
│   ├── css/
│   ├── js/
│   └── images/
├── tests/                  # Test files
│   └── __init__.py
├── routes/                 # Flask route blueprints
│   └── __init__.py
└── logs/                   # Application logs (created at runtime)
```

### Related Task Files:
- **Parent Task**: `.taskmaster/context/task_001/task.md`
- **Task Definition**: `.taskmaster/tasks/task_001.txt`

---

## 🔧 3. Interfaces & Code Snippets

### 3.1 Requirements File (requirements.txt)
```txt
# Core Flask framework
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Migrate==4.0.5
Flask-Mail==0.9.1

# Database
SQLAlchemy==2.0.23
alembic==1.12.1

# Environment management
python-dotenv==1.0.0

# AI/ML frameworks
pyautogen==0.2.0
openai==1.3.0
anthropic==0.7.0

# Utilities
requests==2.31.0
python-dateutil==2.8.2

# Development tools
pytest==7.4.3
pytest-flask==1.3.0
pytest-cov==4.1.0
black==23.9.1
flake8==6.1.0

# Production server
gunicorn==21.2.0

# Additional dependencies
Werkzeug==2.3.7
Jinja2==3.1.2
MarkupSafe==2.1.3
itsdangerous==2.1.2
click==8.1.7
blinker==1.6.3
```

### 3.2 Environment Template (.env.template)
```bash
# Flask configuration
SECRET_KEY=your-secret-key-here-minimum-32-characters-long
FLASK_APP=app.py
FLASK_ENV=development
FLASK_DEBUG=1

# Database configuration
DATABASE_URL=sqlite:///instance/swarm_director.db
SQLALCHEMY_TRACK_MODIFICATIONS=False

# Mail configuration (Gmail example)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=1
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password

# AI API Keys
OPENAI_API_KEY=your-openai-api-key-here
ANTHROPIC_API_KEY=your-anthropic-api-key-here

# Application settings
POSTS_PER_PAGE=25
LOG_LEVEL=INFO
MAX_CONTENT_LENGTH=16777216
```

### 3.3 Git Ignore Configuration (.gitignore)
```gitignore
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
env.bak/
venv.bak/
*.egg-info/
dist/
build/

# Flask
instance/
.env
.flaskenv

# Database
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo
.DS_Store
Thumbs.db

# Logs
logs/
*.log

# Testing
.coverage
htmlcov/
.pytest_cache/
.tox/

# Documentation
docs/_build/
```

---

## 🛠️ 4. Implementation Plan

### Step 1: Project Directory Setup
```bash
# Create project root directory
mkdir SwarmDirector
cd SwarmDirector

# Verify directory creation
pwd  # Should show path ending in /SwarmDirector
ls -la  # Should show empty directory
```

### Step 2: Virtual Environment Creation
```bash
# Create virtual environment
python3 -m venv venv

# Verify virtual environment creation
ls -la venv/  # Should show bin/, lib/, include/ directories

# Activate virtual environment
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Verify activation
which python  # Should point to venv/bin/python
python --version  # Should show Python 3.8+
```

### Step 3: Dependency Installation
```bash
# Upgrade pip to latest version
pip install --upgrade pip

# Create requirements.txt file (use content from section 3.1)
cat > requirements.txt << 'EOF'
[content from section 3.1]
EOF

# Install all dependencies
pip install -r requirements.txt

# Verify installation
pip list | grep Flask  # Should show Flask==2.3.3
pip list | grep SQLAlchemy  # Should show SQLAlchemy==2.0.23
pip list | grep pyautogen  # Should show pyautogen==0.2.0
```

### Step 4: Directory Structure Creation
```bash
# Create main directories
mkdir -p instance migrations models agents utils templates static tests routes logs

# Create static subdirectories
mkdir -p static/css static/js static/images

# Create __init__.py files for Python packages
touch models/__init__.py
touch agents/__init__.py
touch utils/__init__.py
touch tests/__init__.py
touch routes/__init__.py

# Verify directory structure
tree . -I 'venv'  # Should match structure from section 2
```

### Step 5: Configuration Files Creation
```bash
# Create .env.template (use content from section 3.2)
cat > .env.template << 'EOF'
[content from section 3.2]
EOF

# Create .gitignore (use content from section 3.3)
cat > .gitignore << 'EOF'
[content from section 3.3]
EOF

# Create initial README.md
cat > README.md << 'EOF'
# SwarmDirector - Hierarchical AI Agent System

## Setup Instructions

1. Activate virtual environment: `source venv/bin/activate`
2. Install dependencies: `pip install -r requirements.txt`
3. Copy .env.template to .env and configure
4. Run application: `python app.py`

## Project Structure

See directory structure in project documentation.
EOF
```

### Step 6: Environment Configuration
```bash
# Copy template to actual .env file
cp .env.template .env

# Generate a secure secret key
python -c "
import secrets
key = secrets.token_urlsafe(32)
print(f'Generated SECRET_KEY: {key}')
"

# Edit .env file with actual values (manual step)
# Replace placeholder values with real configuration
```

### Step 7: Verification and Testing
```bash
# Test Python environment
python -c "
import sys
print(f'Python version: {sys.version}')
print(f'Python executable: {sys.executable}')
"

# Test package imports
python -c "
import flask
import sqlalchemy
import flask_migrate
import flask_mail
print('All core packages imported successfully')
print(f'Flask version: {flask.__version__}')
print(f'SQLAlchemy version: {sqlalchemy.__version__}')
"

# Test environment loading
python -c "
from dotenv import load_dotenv
import os
load_dotenv()
print('Environment variables loaded')
print(f'SECRET_KEY configured: {bool(os.getenv(\"SECRET_KEY\"))}')
"

# Verify directory permissions
ls -la instance/  # Should be writable
ls -la logs/      # Should be writable (if created)
```

---

---

## 🧪 5. Testing & QA

### 5.1 Automated Verification Script
```python
#!/usr/bin/env python3
"""
Environment setup verification script.
Run this after completing the setup to verify everything is working.
"""

import os
import sys
import subprocess
import importlib.util

def check_python_version():
    """Verify Python version is 3.8+"""
    version = sys.version_info
    if version.major == 3 and version.minor >= 8:
        print(f"✓ Python {version.major}.{version.minor}.{version.micro} is supported")
        return True
    else:
        print(f"✗ Python {version.major}.{version.minor}.{version.micro} is not supported (need 3.8+)")
        return False

def check_virtual_environment():
    """Verify virtual environment is active"""
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✓ Virtual environment is active")
        return True
    else:
        print("✗ Virtual environment is not active")
        return False

def check_required_packages():
    """Verify all required packages are installed"""
    required_packages = [
        ('flask', '2.3.3'),
        ('sqlalchemy', '2.0.23'),
        ('flask_migrate', None),
        ('flask_mail', None),
        ('dotenv', None),
    ]

    all_good = True
    for package, expected_version in required_packages:
        try:
            spec = importlib.util.find_spec(package)
            if spec is not None:
                module = importlib.import_module(package)
                version = getattr(module, '__version__', 'unknown')
                if expected_version and not version.startswith(expected_version):
                    print(f"⚠ {package} version {version} (expected {expected_version})")
                else:
                    print(f"✓ {package} {version}")
            else:
                print(f"✗ {package} not found")
                all_good = False
        except ImportError:
            print(f"✗ {package} import failed")
            all_good = False

    return all_good

def check_directory_structure():
    """Verify directory structure is correct"""
    required_dirs = [
        'instance', 'models', 'agents', 'utils', 'templates',
        'static', 'tests', 'routes', 'static/css', 'static/js', 'static/images'
    ]

    all_good = True
    for directory in required_dirs:
        if os.path.exists(directory) and os.path.isdir(directory):
            print(f"✓ Directory {directory} exists")
        else:
            print(f"✗ Directory {directory} missing")
            all_good = False

    return all_good

def check_required_files():
    """Verify required files exist"""
    required_files = [
        'requirements.txt', '.env.template', '.gitignore', 'README.md',
        'models/__init__.py', 'agents/__init__.py', 'utils/__init__.py',
        'tests/__init__.py', 'routes/__init__.py'
    ]

    all_good = True
    for file_path in required_files:
        if os.path.exists(file_path) and os.path.isfile(file_path):
            print(f"✓ File {file_path} exists")
        else:
            print(f"✗ File {file_path} missing")
            all_good = False

    return all_good

def check_environment_variables():
    """Verify environment variables can be loaded"""
    try:
        from dotenv import load_dotenv
        load_dotenv('.env.template')  # Test with template
        print("✓ Environment variable loading works")
        return True
    except Exception as e:
        print(f"✗ Environment variable loading failed: {e}")
        return False

def main():
    """Run all verification checks"""
    print("SwarmDirector Environment Setup Verification")
    print("=" * 50)

    checks = [
        check_python_version,
        check_virtual_environment,
        check_required_packages,
        check_directory_structure,
        check_required_files,
        check_environment_variables,
    ]

    results = []
    for check in checks:
        print(f"\n{check.__doc__}:")
        results.append(check())

    print("\n" + "=" * 50)
    if all(results):
        print("✓ All checks passed! Environment setup is complete.")
        return 0
    else:
        print("✗ Some checks failed. Please review and fix issues.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
```

### 5.2 Manual Testing Checklist
- [ ] **Environment Setup**
  - [ ] Project directory created successfully
  - [ ] Virtual environment activated
  - [ ] Python version 3.8+ confirmed
  - [ ] All dependencies installed without errors
- [ ] **Directory Structure**
  - [ ] All required directories exist
  - [ ] __init__.py files in Python packages
  - [ ] Static subdirectories created
  - [ ] Proper permissions on instance/ directory
- [ ] **Configuration Files**
  - [ ] requirements.txt contains all dependencies
  - [ ] .env.template has all required variables
  - [ ] .gitignore excludes sensitive files
  - [ ] README.md provides basic instructions
- [ ] **Package Verification**
  - [ ] Flask imports successfully
  - [ ] SQLAlchemy imports successfully
  - [ ] Flask-Migrate imports successfully
  - [ ] Flask-Mail imports successfully
  - [ ] AutoGen imports successfully
- [ ] **Environment Loading**
  - [ ] python-dotenv loads variables
  - [ ] .env file can be created from template
  - [ ] Environment variables accessible in Python

### 5.3 Integration Testing
```bash
# Test complete workflow
cd SwarmDirector
source venv/bin/activate
python -c "
# Test all imports
import flask
import sqlalchemy
import flask_migrate
import flask_mail
from dotenv import load_dotenv
import os

# Test environment loading
load_dotenv('.env.template')

# Test basic functionality
app = flask.Flask(__name__)
print('✓ Flask application created successfully')
print('✓ All imports successful')
print('✓ Environment setup complete')
"
```

---

## 🔗 6. Integration & Related Tasks

### 6.1 Parent Task Integration
- **Parent**: task_001 (Setup Project Skeleton with Flask and SQLite)
- **Relationship**: This subtask provides the foundation for all other subtasks
- **Outputs**: Complete project structure and environment ready for development

### 6.2 Dependent Subtasks
- **Enables**: subtask_002 (Core Flask Application Configuration)
- **Enables**: subtask_003 (Database Schema and Initialization)
- **Enables**: subtask_004 (CRUD Operations Implementation)

### 6.3 External Dependencies
- **System Requirements**: Python 3.8+, pip, git
- **Network Requirements**: Internet access for package downloads
- **Disk Requirements**: ~500MB for virtual environment and packages

---

## ⚠️ 7. Risks & Mitigations

| Risk | Impact | Probability | Mitigation Strategy |
|------|--------|-------------|-------------------|
| Python version incompatibility | High | Low | Verify Python 3.8+ before starting, test with multiple versions |
| Package installation failures | High | Medium | Use specific versions, provide alternative installation methods |
| Virtual environment issues | Medium | Low | Document activation steps clearly, provide troubleshooting guide |
| Directory permission problems | Medium | Low | Set proper permissions, document required access levels |
| Network connectivity issues | Medium | Medium | Provide offline installation options, cache packages |

### 7.1 Common Issues & Solutions

**Issue**: Virtual environment activation fails
**Solution**:
```bash
# On Windows, try:
venv\Scripts\activate.bat

# On macOS/Linux with different shells:
source venv/bin/activate.fish  # Fish shell
source venv/bin/activate.csh   # C shell
```

**Issue**: Package installation fails due to permissions
**Solution**:
```bash
# Use user installation if needed
pip install --user -r requirements.txt

# Or fix permissions
sudo chown -R $USER:$USER venv/
```

**Issue**: Directory creation fails
**Solution**:
```bash
# Check current directory permissions
ls -la .

# Create with explicit permissions
mkdir -m 755 SwarmDirector
```

---

## ✅ 8. Success Criteria

### 8.1 Functional Requirements
- [ ] Project directory "SwarmDirector" created successfully
- [ ] Virtual environment created and can be activated
- [ ] All dependencies from requirements.txt installed without conflicts
- [ ] Complete directory structure matches specification
- [ ] All required __init__.py files created
- [ ] Configuration files (.env.template, .gitignore) created
- [ ] Environment variables can be loaded successfully

### 8.2 Technical Requirements
- [ ] Python 3.8+ confirmed as active interpreter
- [ ] Virtual environment isolation verified (pip list shows only project packages)
- [ ] All core packages (Flask, SQLAlchemy, etc.) import successfully
- [ ] Directory permissions allow read/write access
- [ ] Git repository can be initialized (if desired)

### 8.3 Quality Requirements
- [ ] Verification script runs without errors
- [ ] All manual testing checklist items pass
- [ ] Documentation is complete and accurate
- [ ] Setup can be reproduced on different systems
- [ ] No security vulnerabilities in dependency versions

---

## 🚀 9. Next Steps

### 9.1 Immediate Actions
1. **Run Verification**: Execute the verification script to confirm setup
2. **Test Environment**: Activate virtual environment and test imports
3. **Configure .env**: Copy template to .env and add real values
4. **Initialize Git**: Set up version control if not already done

### 9.2 Preparation for Next Subtasks
1. **Review Flask Basics**: Ensure familiarity with Flask application factory pattern
2. **Study SQLAlchemy**: Review database model creation and migration concepts
3. **Understand AutoGen**: Read AutoGen documentation for agent implementation
4. **Plan Configuration**: Think about environment-specific settings needed

### 9.3 Documentation Updates
1. **Update README**: Add specific setup instructions discovered during implementation
2. **Document Issues**: Record any problems encountered and solutions found
3. **Create Troubleshooting Guide**: Document common issues for future reference
