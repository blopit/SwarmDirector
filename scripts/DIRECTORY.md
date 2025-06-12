# Scripts Directory

## Purpose
Contains utility and maintenance scripts for the SwarmDirector application, providing automation for development, deployment, testing, and operational tasks. These scripts support the development workflow, system maintenance, and administrative operations for the hierarchical AI agent management system.

## Structure
```
scripts/
├── cleanup_test_artifacts.py   # Clean up test artifacts and temporary files
├── comprehensive_context_updater.py # Update context files across the project
├── final_verification.py       # Final system verification and health checks
├── run_tests.py                # Test runner with comprehensive options
├── run_tests.sh                # Shell script for test execution
├── setup_development.py        # Development environment setup
├── update_context_files.py     # Context file maintenance and updates
├── update_task_contexts_for_reorganization.py # Task context reorganization
├── validate_context_files.py   # Context file validation and verification
└── verify_reorganization.py    # Verify project reorganization integrity
```

## Guidelines

### 1. Organization
- **Single Purpose**: Each script should have a clear, single purpose
- **Modular Design**: Break complex operations into reusable functions
- **Configuration**: Support configuration through command-line arguments and environment variables
- **Logging**: Implement comprehensive logging for all operations
- **Error Handling**: Provide robust error handling and recovery mechanisms

### 2. Naming
- **Descriptive Names**: Use clear, descriptive names indicating script purpose
- **Action-Oriented**: Start with action verbs (e.g., `setup_`, `update_`, `verify_`)
- **Consistent Format**: Use snake_case for Python scripts, kebab-case for shell scripts
- **File Extensions**: Use appropriate extensions (.py for Python, .sh for shell)
- **Version Indicators**: Include version information in script headers

### 3. Implementation
- **Argument Parsing**: Use argparse for command-line argument handling
- **Exit Codes**: Use appropriate exit codes for success/failure indication
- **Progress Indicators**: Show progress for long-running operations
- **Dry Run Mode**: Support dry-run mode for testing script behavior
- **Idempotency**: Ensure scripts can be run multiple times safely

### 4. Documentation
- **Script Headers**: Include purpose, usage, and examples in script headers
- **Inline Comments**: Document complex logic and important decisions
- **Usage Examples**: Provide clear usage examples and common scenarios
- **Error Messages**: Use clear, actionable error messages

## Best Practices

### 1. Error Handling
- **Graceful Failures**: Handle errors gracefully with informative messages
- **Rollback Mechanisms**: Implement rollback for destructive operations
- **Validation**: Validate inputs and preconditions before execution
- **Recovery Options**: Provide options for recovering from failures
- **Error Logging**: Log all errors with sufficient context for debugging

### 2. Security
- **Input Validation**: Validate all inputs and file paths
- **Permission Checks**: Verify appropriate permissions before operations
- **Secure Defaults**: Use secure default configurations
- **Credential Handling**: Handle credentials securely, never log sensitive data
- **Path Traversal**: Prevent path traversal attacks in file operations

### 3. Performance
- **Efficient Operations**: Use efficient algorithms and avoid unnecessary work
- **Parallel Processing**: Use parallel processing for independent operations
- **Resource Management**: Monitor and limit resource usage
- **Caching**: Cache expensive operations when appropriate
- **Progress Reporting**: Report progress for long-running operations

### 4. Testing
- **Script Testing**: Test scripts with various inputs and scenarios
- **Mock External Dependencies**: Mock external services and file systems
- **Edge Case Testing**: Test error conditions and edge cases
- **Integration Testing**: Test scripts in realistic environments
- **Automated Testing**: Include scripts in automated test suites

### 5. Documentation
- **Usage Documentation**: Provide comprehensive usage documentation
- **Example Scenarios**: Include examples for common use cases
- **Troubleshooting**: Document common issues and solutions
- **Change Documentation**: Document script changes and version history

## Example

### Comprehensive Development Setup Script

```python
#!/usr/bin/env python3
"""
SwarmDirector Development Environment Setup Script

This script automates the setup of a complete development environment
for the SwarmDirector project, including dependencies, database,
configuration, and verification.

Usage:
    python setup_development.py [options]

Examples:
    # Basic setup
    python setup_development.py

    # Setup with specific Python version
    python setup_development.py --python-version 3.9

    # Setup with custom database
    python setup_development.py --database-url postgresql://localhost/swarm_dev

    # Dry run to see what would be done
    python setup_development.py --dry-run

Author: SwarmDirector Team
Version: 2.0.0
Last Updated: 2023-12-01
"""

import argparse
import logging
import os
import subprocess
import sys
import tempfile
import shutil
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import json
import yaml

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('setup_development.log')
    ]
)
logger = logging.getLogger(__name__)

class DevelopmentSetup:
    """
    Development environment setup manager
    
    Handles all aspects of setting up a SwarmDirector development environment
    including virtual environment, dependencies, database, and configuration.
    """
    
    def __init__(self, config: Dict):
        self.config = config
        self.project_root = Path(__file__).parent.parent
        self.dry_run = config.get('dry_run', False)
        self.errors = []
        self.warnings = []
        
    def setup_environment(self) -> bool:
        """
        Setup complete development environment
        
        Returns:
            bool: True if setup successful, False otherwise
        """
        logger.info("🚀 Starting SwarmDirector development environment setup")
        
        try:
            # Verify system requirements
            if not self._verify_system_requirements():
                return False
            
            # Setup virtual environment
            if not self._setup_virtual_environment():
                return False
            
            # Install dependencies
            if not self._install_dependencies():
                return False
            
            # Setup database
            if not self._setup_database():
                return False
            
            # Create configuration
            if not self._create_configuration():
                return False
            
            # Initialize application
            if not self._initialize_application():
                return False
            
            # Run verification tests
            if not self._run_verification():
                return False
            
            # Generate documentation
            if not self._generate_documentation():
                return False
            
            self._print_success_summary()
            return True
            
        except Exception as e:
            logger.error(f"❌ Setup failed with error: {e}")
            self.errors.append(str(e))
            return False
        
        finally:
            self._print_summary()
    
    def _verify_system_requirements(self) -> bool:
        """Verify system requirements"""
        logger.info("🔍 Verifying system requirements")
        
        requirements = [
            ('python', self.config.get('python_version', '3.8')),
            ('git', '2.0'),
            ('pip', '20.0')
        ]
        
        for tool, min_version in requirements:
            if not self._check_tool_version(tool, min_version):
                self.errors.append(f"Required tool {tool} >= {min_version} not found")
                return False
        
        # Check available disk space
        if not self._check_disk_space():
            return False
        
        # Check network connectivity
        if not self._check_network_connectivity():
            return False
        
        logger.info("✅ System requirements verified")
        return True
    
    def _setup_virtual_environment(self) -> bool:
        """Setup Python virtual environment"""
        logger.info("🐍 Setting up virtual environment")
        
        venv_path = self.project_root / 'venv'
        
        if venv_path.exists():
            if self.config.get('force_recreate', False):
                logger.info("🗑️  Removing existing virtual environment")
                if not self.dry_run:
                    shutil.rmtree(venv_path)
            else:
                logger.info("📁 Virtual environment already exists, skipping creation")
                return True
        
        # Create virtual environment
        python_cmd = self.config.get('python_command', 'python3')
        cmd = [python_cmd, '-m', 'venv', str(venv_path)]
        
        if not self._run_command(cmd, "Creating virtual environment"):
            return False
        
        # Upgrade pip in virtual environment
        pip_cmd = str(venv_path / 'bin' / 'pip')
        if sys.platform == 'win32':
            pip_cmd = str(venv_path / 'Scripts' / 'pip.exe')
        
        upgrade_cmd = [pip_cmd, 'install', '--upgrade', 'pip', 'setuptools', 'wheel']
        if not self._run_command(upgrade_cmd, "Upgrading pip"):
            return False
        
        logger.info("✅ Virtual environment setup complete")
        return True
    
    def _install_dependencies(self) -> bool:
        """Install project dependencies"""
        logger.info("📦 Installing dependencies")
        
        venv_path = self.project_root / 'venv'
        pip_cmd = str(venv_path / 'bin' / 'pip')
        if sys.platform == 'win32':
            pip_cmd = str(venv_path / 'Scripts' / 'pip.exe')
        
        # Install production dependencies
        requirements_file = self.project_root / 'requirements.txt'
        if requirements_file.exists():
            cmd = [pip_cmd, 'install', '-r', str(requirements_file)]
            if not self._run_command(cmd, "Installing production dependencies"):
                return False
        
        # Install development dependencies
        dev_requirements = self.project_root / 'requirements-dev.txt'
        if dev_requirements.exists():
            cmd = [pip_cmd, 'install', '-r', str(dev_requirements)]
            if not self._run_command(cmd, "Installing development dependencies"):
                return False
        
        # Install optional dependencies
        if self.config.get('install_optional', True):
            optional_deps = ['pyautogen', 'redis', 'celery']
            for dep in optional_deps:
                cmd = [pip_cmd, 'install', dep]
                if not self._run_command(cmd, f"Installing optional dependency {dep}", allow_failure=True):
                    self.warnings.append(f"Failed to install optional dependency: {dep}")
        
        logger.info("✅ Dependencies installation complete")
        return True
    
    def _setup_database(self) -> bool:
        """Setup development database"""
        logger.info("🗄️  Setting up database")
        
        database_url = self.config.get('database_url')
        
        if database_url and database_url.startswith('postgresql://'):
            return self._setup_postgresql_database(database_url)
        else:
            return self._setup_sqlite_database()
    
    def _setup_sqlite_database(self) -> bool:
        """Setup SQLite development database"""
        logger.info("📁 Setting up SQLite database")
        
        db_dir = self.project_root / 'database' / 'data'
        db_dir.mkdir(parents=True, exist_ok=True)
        
        db_path = db_dir / 'swarm_director_dev.db'
        
        if db_path.exists() and not self.config.get('force_recreate', False):
            logger.info("📊 Database already exists, skipping creation")
            return True
        
        # Initialize database using Flask app
        init_script = f"""
import sys
sys.path.insert(0, '{self.project_root / 'src'}')
from swarm_director.app import create_app
from swarm_director.models.base import db

app = create_app('development')
with app.app_context():
    db.create_all()
    print('Database initialized successfully')
"""
        
        if not self.dry_run:
            venv_python = self._get_venv_python()
            result = subprocess.run(
                [venv_python, '-c', init_script],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.error(f"Database initialization failed: {result.stderr}")
                return False
        
        logger.info("✅ SQLite database setup complete")
        return True
    
    def _create_configuration(self) -> bool:
        """Create development configuration"""
        logger.info("⚙️  Creating configuration files")
        
        config_dir = self.project_root / 'config'
        config_dir.mkdir(exist_ok=True)
        
        # Create .env file for development
        env_file = self.project_root / '.env'
        if not env_file.exists() or self.config.get('force_recreate', False):
            env_content = self._generate_env_content()
            
            if not self.dry_run:
                with open(env_file, 'w') as f:
                    f.write(env_content)
            
            logger.info("📝 Created .env configuration file")
        
        # Create development config
        dev_config = config_dir / 'development.py'
        if not dev_config.exists():
            config_content = self._generate_dev_config()
            
            if not self.dry_run:
                with open(dev_config, 'w') as f:
                    f.write(config_content)
            
            logger.info("📝 Created development configuration")
        
        logger.info("✅ Configuration setup complete")
        return True
    
    def _initialize_application(self) -> bool:
        """Initialize application with sample data"""
        logger.info("🎯 Initializing application")
        
        if self.config.get('skip_sample_data', False):
            logger.info("⏭️  Skipping sample data creation")
            return True
        
        # Create sample agents and tasks
        init_script = f"""
import sys
sys.path.insert(0, '{self.project_root / 'src'}')
from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.agent import Agent, AgentType, AgentStatus
from swarm_director.models.task import Task, TaskStatus, TaskPriority

app = create_app('development')
with app.app_context():
    # Create director agent
    director = Agent(
        name='MainDirector',
        description='Primary director agent for development',
        agent_type=AgentType.SUPERVISOR,
        status=AgentStatus.IDLE,
        capabilities={{'routing': True, 'department_management': True}}
    )
    director.save()
    
    # Create sample department agents
    email_agent = Agent(
        name='EmailAgent',
        description='Email handling agent',
        agent_type=AgentType.WORKER,
        status=AgentStatus.IDLE,
        capabilities={{'email_handling': True, 'smtp_integration': True}}
    )
    email_agent.save()
    
    print('Sample agents created successfully')
"""
        
        if not self.dry_run:
            venv_python = self._get_venv_python()
            result = subprocess.run(
                [venv_python, '-c', init_script],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.error(f"Application initialization failed: {result.stderr}")
                return False
        
        logger.info("✅ Application initialization complete")
        return True
    
    def _run_verification(self) -> bool:
        """Run verification tests"""
        logger.info("🧪 Running verification tests")
        
        venv_python = self._get_venv_python()
        
        # Run basic import test
        import_test = """
import sys
sys.path.insert(0, 'src')
try:
    from swarm_director.app import create_app
    from swarm_director.models.base import db
    from swarm_director.agents.director import DirectorAgent
    print('✅ All imports successful')
except ImportError as e:
    print(f'❌ Import failed: {e}')
    sys.exit(1)
"""
        
        if not self.dry_run:
            result = subprocess.run(
                [venv_python, '-c', import_test],
                capture_output=True,
                text=True,
                cwd=self.project_root
            )
            
            if result.returncode != 0:
                logger.error(f"Import verification failed: {result.stderr}")
                return False
        
        # Run basic functionality test
        if self.config.get('run_tests', True):
            test_cmd = [venv_python, '-m', 'pytest', 'tests/', '-v', '--tb=short']
            if not self._run_command(test_cmd, "Running verification tests", allow_failure=True):
                self.warnings.append("Some verification tests failed")
        
        logger.info("✅ Verification complete")
        return True
    
    def _generate_documentation(self) -> bool:
        """Generate development documentation"""
        logger.info("📚 Generating documentation")
        
        if self.config.get('skip_docs', False):
            logger.info("⏭️  Skipping documentation generation")
            return True
        
        # Generate API documentation
        docs_cmd = [
            self._get_venv_python(),
            '-c',
            'import sys; sys.path.insert(0, "src"); from swarm_director.app import create_app; print("Docs generated")'
        ]
        
        if not self._run_command(docs_cmd, "Generating documentation", allow_failure=True):
            self.warnings.append("Documentation generation failed")
        
        logger.info("✅ Documentation generation complete")
        return True
    
    def _run_command(self, cmd: List[str], description: str, allow_failure: bool = False) -> bool:
        """Run a command with logging"""
        logger.info(f"🔧 {description}")
        
        if self.dry_run:
            logger.info(f"[DRY RUN] Would run: {' '.join(cmd)}")
            return True
        
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                cwd=self.project_root,
                timeout=300  # 5 minute timeout
            )
            
            if result.returncode == 0:
                logger.debug(f"Command output: {result.stdout}")
                return True
            else:
                error_msg = f"Command failed: {result.stderr}"
                if allow_failure:
                    logger.warning(error_msg)
                    return True
                else:
                    logger.error(error_msg)
                    return False
                    
        except subprocess.TimeoutExpired:
            error_msg = f"Command timed out: {' '.join(cmd)}"
            if allow_failure:
                logger.warning(error_msg)
                return True
            else:
                logger.error(error_msg)
                return False
        except Exception as e:
            error_msg = f"Command execution failed: {e}"
            if allow_failure:
                logger.warning(error_msg)
                return True
            else:
                logger.error(error_msg)
                return False
    
    def _get_venv_python(self) -> str:
        """Get path to virtual environment Python"""
        venv_path = self.project_root / 'venv'
        if sys.platform == 'win32':
            return str(venv_path / 'Scripts' / 'python.exe')
        else:
            return str(venv_path / 'bin' / 'python')
    
    def _check_tool_version(self, tool: str, min_version: str) -> bool:
        """Check if tool meets minimum version requirement"""
        try:
            result = subprocess.run([tool, '--version'], capture_output=True, text=True)
            if result.returncode == 0:
                logger.debug(f"{tool} version: {result.stdout.strip()}")
                return True
            return False
        except FileNotFoundError:
            logger.error(f"Tool {tool} not found")
            return False
    
    def _check_disk_space(self, min_gb: int = 2) -> bool:
        """Check available disk space"""
        try:
            import shutil
            total, used, free = shutil.disk_usage(self.project_root)
            free_gb = free // (1024**3)
            
            if free_gb < min_gb:
                self.errors.append(f"Insufficient disk space: {free_gb}GB available, {min_gb}GB required")
                return False
            
            logger.debug(f"Available disk space: {free_gb}GB")
            return True
        except Exception as e:
            logger.warning(f"Could not check disk space: {e}")
            return True
    
    def _check_network_connectivity(self) -> bool:
        """Check network connectivity for package downloads"""
        try:
            import urllib.request
            urllib.request.urlopen('https://pypi.org', timeout=10)
            logger.debug("Network connectivity verified")
            return True
        except Exception as e:
            logger.warning(f"Network connectivity check failed: {e}")
            return True  # Don't fail setup for network issues
    
    def _generate_env_content(self) -> str:
        """Generate .env file content"""
        return f"""# SwarmDirector Development Environment Configuration
# Generated by setup_development.py

# Flask Configuration
FLASK_ENV=development
FLASK_DEBUG=true
SECRET_KEY=dev-secret-key-change-in-production

# Database Configuration
DATABASE_URL=sqlite:///database/data/swarm_director_dev.db

# SwarmDirector Configuration
SWARM_DIRECTOR_LOG_LEVEL=DEBUG
SWARM_DIRECTOR_MAX_AGENTS=50
SWARM_DIRECTOR_TASK_TIMEOUT=300

# Optional AutoGen Configuration
# AUTOGEN_API_KEY=your-api-key-here
# AUTOGEN_MODEL=gpt-3.5-turbo

# Email Configuration (for testing)
SMTP_SERVER=localhost
SMTP_PORT=1025
SMTP_USERNAME=
SMTP_PASSWORD=
SMTP_USE_TLS=false
"""
    
    def _generate_dev_config(self) -> str:
        """Generate development configuration"""
        return '''"""
Development configuration for SwarmDirector
Generated by setup_development.py
"""

import os
from .base import Config

class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    TESTING = False
    
    # Database
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \\
        'sqlite:///database/data/swarm_director_dev.db'
    SQLALCHEMY_ECHO = True
    
    # Security (development only)
    WTF_CSRF_ENABLED = False
    
    # SwarmDirector specific
    SWARM_DIRECTOR_LOG_LEVEL = 'DEBUG'
    SWARM_DIRECTOR_MAX_AGENTS = 50
'''
    
    def _print_success_summary(self):
        """Print success summary"""
        logger.info("🎉 Development environment setup completed successfully!")
        logger.info("")
        logger.info("Next steps:")
        logger.info("1. Activate virtual environment: source venv/bin/activate")
        logger.info("2. Start the application: python run.py")
        logger.info("3. Access the dashboard: http://localhost:5000/dashboard")
        logger.info("4. Run tests: pytest tests/")
        logger.info("")
    
    def _print_summary(self):
        """Print setup summary"""
        if self.warnings:
            logger.warning("⚠️  Warnings encountered:")
            for warning in self.warnings:
                logger.warning(f"  - {warning}")
        
        if self.errors:
            logger.error("❌ Errors encountered:")
            for error in self.errors:
                logger.error(f"  - {error}")

def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Setup SwarmDirector development environment",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s                          # Basic setup
  %(prog)s --python-version 3.9     # Specific Python version
  %(prog)s --dry-run                # See what would be done
  %(prog)s --force-recreate         # Force recreate existing components
        """
    )
    
    parser.add_argument(
        '--python-version',
        default='3.8',
        help='Minimum Python version required (default: 3.8)'
    )
    
    parser.add_argument(
        '--python-command',
        default='python3',
        help='Python command to use (default: python3)'
    )
    
    parser.add_argument(
        '--database-url',
        help='Database URL (default: SQLite)'
    )
    
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Show what would be done without executing'
    )
    
    parser.add_argument(
        '--force-recreate',
        action='store_true',
        help='Force recreate existing components'
    )
    
    parser.add_argument(
        '--skip-sample-data',
        action='store_true',
        help='Skip creating sample data'
    )
    
    parser.add_argument(
        '--skip-docs',
        action='store_true',
        help='Skip documentation generation'
    )
    
    parser.add_argument(
        '--no-tests',
        action='store_true',
        help='Skip running verification tests'
    )
    
    parser.add_argument(
        '--install-optional',
        action='store_true',
        default=True,
        help='Install optional dependencies'
    )
    
    parser.add_argument(
        '--verbose', '-v',
        action='store_true',
        help='Enable verbose logging'
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Build configuration
    config = {
        'python_version': args.python_version,
        'python_command': args.python_command,
        'database_url': args.database_url,
        'dry_run': args.dry_run,
        'force_recreate': args.force_recreate,
        'skip_sample_data': args.skip_sample_data,
        'skip_docs': args.skip_docs,
        'run_tests': not args.no_tests,
        'install_optional': args.install_optional
    }
    
    # Run setup
    setup = DevelopmentSetup(config)
    success = setup.setup_environment()
    
    sys.exit(0 if success else 1)

if __name__ == '__main__':
    main()
```

## Related Documentation
- [Development Guide](../../docs/development/getting_started.md) - Development environment setup
- [Testing Scripts](../../docs/development/testing.md) - Test automation and scripts
- [Deployment Scripts](../../docs/deployment/local_development.md) - Deployment automation
- [Maintenance Guide](../../docs/development/debugging.md) - System maintenance procedures
- [CI/CD Integration](../../docs/deployment/local_development.md#continuous-integration) - Automated script execution
