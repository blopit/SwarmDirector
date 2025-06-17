#!/usr/bin/env python3
"""
Development Environment Setup Script

This script sets up a complete development environment for SwarmDirector,
including database initialization, sample data, and configuration.
"""

import os
import sys
import subprocess
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent.parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Task management integration
try:
    from swarm_director.utils.automation import AutomationIntegrator, AutomationEventType, WorkflowStatus
    TASK_INTEGRATION_AVAILABLE = True
except ImportError:
    TASK_INTEGRATION_AVAILABLE = False
    print("⚠️  Task management integration not available")

def run_command(command, description):
    """Run a shell command and handle errors."""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        if e.stdout:
            print(f"stdout: {e.stdout}")
        if e.stderr:
            print(f"stderr: {e.stderr}")
        return False

def trigger_task_event(event_type, task_id=None, status=None, metadata=None):
    """Trigger task management events if integration is available."""
    if not TASK_INTEGRATION_AVAILABLE:
        return
    
    try:
        from swarm_director.utils.automation import trigger_task_automation
        trigger_task_automation(event_type, task_id or "dev_setup", metadata or {})
    except Exception as e:
        print(f"⚠️  Task event trigger failed: {e}")

def check_python_version():
    """Check if Python version is compatible."""
    print("🐍 Checking Python version...")
    if sys.version_info < (3, 8):
        print("❌ Python 3.8 or higher is required")
        return False
    print(f"✅ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro} is compatible")
    return True

def check_virtual_environment():
    """Check if we're in a virtual environment."""
    print("🏠 Checking virtual environment...")
    if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("✅ Virtual environment detected")
        return True
    else:
        print("⚠️  No virtual environment detected. It's recommended to use a virtual environment.")
        response = input("Continue anyway? (y/N): ")
        return response.lower() in ['y', 'yes']

def install_dependencies():
    """Install Python dependencies."""
    requirements_file = project_root / "requirements.txt"
    if not requirements_file.exists():
        print("❌ requirements.txt not found")
        trigger_task_event(AutomationEventType.TASK_FAILED, metadata={"reason": "requirements.txt not found"})
        return False
    
    trigger_task_event(AutomationEventType.TASK_CREATED, metadata={"action": "installing_dependencies"})
    success = run_command(
        f"pip install -r {requirements_file}",
        "Installing Python dependencies"
    )
    
    if success:
        trigger_task_event(AutomationEventType.TASK_COMPLETED, metadata={"action": "dependencies_installed"})
    else:
        trigger_task_event(AutomationEventType.TASK_FAILED, metadata={"action": "dependency_installation_failed"})
    
    return success

def create_env_file():
    """Create .env file with default development settings."""
    env_file = project_root / ".env"
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    print("📝 Creating .env file with development settings...")
    env_content = """# SwarmDirector Development Configuration
SECRET_KEY=dev-secret-key-change-in-production
FLASK_ENV=development
FLASK_DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///database/data/swarm_director_dev.db
SQLALCHEMY_ECHO=False

# Email Configuration (optional)
# MAIL_SERVER=smtp.gmail.com
# MAIL_PORT=587
# MAIL_USE_TLS=True
# MAIL_USERNAME=your-email@gmail.com
# MAIL_PASSWORD=your-app-password

# Logging Configuration
LOG_LEVEL=DEBUG
LOG_TO_STDOUT=True

# Agent Configuration
DEFAULT_AGENT_TIMEOUT=30
MAX_CONCURRENT_TASKS=10
"""
    
    try:
        with open(env_file, 'w') as f:
            f.write(env_content)
        print("✅ .env file created successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to create .env file: {e}")
        return False

def setup_database():
    """Initialize the database."""
    print("🗄️ Setting up database...")
    trigger_task_event(AutomationEventType.DEPLOYMENT_STARTED, metadata={"action": "database_setup"})
    
    # Ensure database directory exists
    db_dir = project_root / "database" / "data"
    db_dir.mkdir(parents=True, exist_ok=True)
    
    # Import and initialize database
    try:
        from swarm_director.app import create_app
        from swarm_director.models.base import db
        
        app = create_app()
        with app.app_context():
            db.create_all()
            print("✅ Database tables created successfully")
            trigger_task_event(AutomationEventType.DEPLOYMENT_COMPLETED, metadata={"action": "database_initialized"})
            return True
    except Exception as e:
        print(f"❌ Database setup failed: {e}")
        trigger_task_event(AutomationEventType.DEPLOYMENT_FAILED, metadata={"action": "database_setup", "error": str(e)})
        return False

def create_sample_data():
    """Create sample data for development."""
    print("📊 Creating sample data...")
    
    try:
        from swarm_director.app import create_app
        from swarm_director.models.agent import Agent, AgentType, AgentStatus
        from swarm_director.models.task import Task, TaskStatus, TaskPriority
        from swarm_director.models.base import db
        
        app = create_app()
        with app.app_context():
            # Check if data already exists
            if Agent.query.first():
                print("✅ Sample data already exists")
                return True
            
            # Create sample agents
            director = Agent(
                name="DirectorAgent",
                description="Main director agent for task routing",
                agent_type=AgentType.SUPERVISOR,
                status=AgentStatus.ACTIVE,
                capabilities=["routing", "intent_classification", "task_delegation"]
            )
            
            email_agent = Agent(
                name="EmailAgent",
                description="Specialized agent for email operations",
                agent_type=AgentType.SPECIALIST,
                status=AgentStatus.IDLE,
                capabilities=["email_sending", "template_processing"]
            )
            
            worker_agent = Agent(
                name="WorkerAgent",
                description="General purpose worker agent",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                capabilities=["general_tasks", "data_processing"]
            )
            
            # Save agents
            for agent in [director, email_agent, worker_agent]:
                agent.save()
            
            # Create sample tasks
            sample_task = Task(
                title="Welcome Email Campaign",
                description="Send welcome emails to new users",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                assigned_agent_id=email_agent.id,
                input_data={
                    "template": "welcome",
                    "recipients": ["user1@example.com", "user2@example.com"]
                }
            )
            sample_task.save()
            
            print("✅ Sample data created successfully")
            return True
            
    except Exception as e:
        print(f"❌ Sample data creation failed: {e}")
        return False

def verify_installation():
    """Verify that the installation is working."""
    print("🔍 Verifying installation...")
    
    try:
        from swarm_director.app import create_app
        app = create_app()
        
        with app.test_client() as client:
            # Test health endpoint
            response = client.get('/health')
            if response.status_code == 200:
                print("✅ Health endpoint working")
            else:
                print(f"❌ Health endpoint failed: {response.status_code}")
                return False
            
            # Test API endpoints
            response = client.get('/api/agents')
            if response.status_code == 200:
                print("✅ API endpoints working")
            else:
                print(f"❌ API endpoints failed: {response.status_code}")
                return False
        
        print("✅ Installation verification completed successfully")
        return True
        
    except Exception as e:
        print(f"❌ Installation verification failed: {e}")
        return False

def main():
    """Main setup function."""
    print("🚀 SwarmDirector Development Environment Setup")
    print("=" * 50)
    
    # Initialize task tracking for development setup
    trigger_task_event(AutomationEventType.TASK_CREATED, task_id="dev_setup", 
                      metadata={"workflow": "development_environment_setup"})
    
    # Check prerequisites
    if not check_python_version():
        trigger_task_event(AutomationEventType.TASK_FAILED, task_id="dev_setup",
                          metadata={"reason": "python_version_incompatible"})
        sys.exit(1)
    
    if not check_virtual_environment():
        trigger_task_event(AutomationEventType.TASK_FAILED, task_id="dev_setup",
                          metadata={"reason": "virtual_environment_check_failed"})
        sys.exit(1)
    
    # Setup steps
    steps = [
        ("Install dependencies", install_dependencies),
        ("Create .env file", create_env_file),
        ("Setup database", setup_database),
        ("Create sample data", create_sample_data),
        ("Verify installation", verify_installation),
    ]
    
    failed_steps = []
    for step_name, step_function in steps:
        if not step_function():
            failed_steps.append(step_name)
    
    print("=" * 50)
    if failed_steps:
        print("❌ Setup completed with errors:")
        for step in failed_steps:
            print(f"  • {step}")
        print("\nPlease review the errors above and try again.")
        trigger_task_event(AutomationEventType.TASK_FAILED, task_id="dev_setup",
                          metadata={"failed_steps": failed_steps})
        sys.exit(1)
    else:
        print("🎉 Development environment setup completed successfully!")
        print("\nNext steps:")
        print("1. Run the application: python run.py")
        print("2. Open your browser to: http://localhost:5000")
        print("3. Check the dashboard: http://localhost:5000/dashboard")
        print("4. Try the demo: http://localhost:5000/demo")
        print("\nFor more information, see docs/development/getting_started.md")
        trigger_task_event(AutomationEventType.TASK_COMPLETED, task_id="dev_setup",
                          metadata={"setup_successful": True})

if __name__ == "__main__":
    main()
