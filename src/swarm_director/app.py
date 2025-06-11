import os
import logging
from flask import Flask, jsonify, request
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_mail import Mail
from dotenv import load_dotenv
from sqlalchemy import text

# Load environment variables
load_dotenv()

# Initialize extensions
from .models.base import db
migrate = Migrate()
mail = Mail()

def create_app(config_name='default'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Load configuration
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Configure logging
    setup_logging(app)
    
    # Register error handlers
    register_error_handlers(app)
    
    # Register blueprints/routes
    register_routes(app)
    
    # Import models to ensure they're registered with SQLAlchemy
    try:
        from .models.base import db as models_db
        # Import all models to register them
        from .models.agent import Agent
        from .models.task import Task
        from .models.conversation import Conversation, Message
    except ImportError as e:
        # Models import failed, log the error but continue
        print(f"Warning: Could not import models - {e}")
        pass
    
    # Register CLI commands
    register_database_commands(app)
    
    return app

def setup_logging(app):
    """Configure application logging"""
    if not app.debug and not app.testing:
        # Production logging
        file_handler = logging.FileHandler('logs/swarm_director.log')
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info('SwarmDirector startup')
    
    # Console logging for development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    console_handler.setFormatter(formatter)
    app.logger.addHandler(console_handler)

def register_error_handlers(app):
    """Register error handling middleware"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({'error': 'Resource not found'}), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        app.logger.error(f'Server Error: {error}')
        return jsonify({'error': 'Internal server error'}), 500
    
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({'error': 'Bad request'}), 400

def register_routes(app):
    """Register application routes"""
    
    @app.route('/')
    def index():
        """Health check endpoint"""
        return jsonify({
            'message': 'SwarmDirector API is running',
            'status': 'healthy'
        })
    
    @app.route('/health')
    def health_check():
        """Detailed health check endpoint"""
        try:
            # Test database connection using proper SQLAlchemy syntax
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return jsonify({
            'status': 'healthy',
            'database': db_status,
            'version': '1.0.0'
        })
    
    @app.route('/task', methods=['POST'])
    def submit_task():
        """Task submission endpoint for DirectorAgent routing"""
        try:
            # Validate request content type
            if not request.is_json:
                return jsonify({
                    'status': 'error',
                    'error': 'Content-Type must be application/json'
                }), 400
            
            try:
                data = request.get_json(force=True)
            except Exception:
                return jsonify({
                    'status': 'error',
                    'error': 'Invalid JSON in request body'
                }), 400
            
            # Validate required fields
            if not data:
                return jsonify({
                    'status': 'error',
                    'error': 'Request body is required'
                }), 400
            
            if 'type' not in data:
                return jsonify({
                    'status': 'error',
                    'error': 'Field "type" is required'
                }), 400
            
            # Extract task details
            task_type = data.get('type')
            task_args = data.get('args', {})
            task_title = data.get('title', f'Task: {task_type}')
            task_description = data.get('description', '')
            task_priority = data.get('priority', 'medium')
            
            # Import here to avoid circular imports
            from .models.task import Task, TaskStatus, TaskPriority
            from .models.agent import Agent, AgentType
            from .agents.director import DirectorAgent
            
            # Create task in database
            from datetime import datetime
            task = Task(
                title=task_title,
                description=task_description,
                status=TaskStatus.PENDING,
                priority=getattr(TaskPriority, task_priority.upper(), TaskPriority.MEDIUM),
                input_data={
                    'type': task_type,
                    'args': task_args,
                    'submitted_at': datetime.utcnow().isoformat()
                }
            )
            task.save()
            
            # Generate unique task_id for response
            task_id = f"task_{task.id}_{task.created_at.strftime('%Y%m%d_%H%M%S')}"
            
            # Get or create DirectorAgent
            director_db = Agent.query.filter_by(
                agent_type=AgentType.SUPERVISOR,
                name='DirectorAgent'
            ).first()
            
            if not director_db:
                # Create DirectorAgent if it doesn't exist
                director_db = Agent(
                    name='DirectorAgent',
                    agent_type=AgentType.SUPERVISOR,
                    capabilities=['routing', 'intent_classification', 'task_delegation']
                )
                director_db.save()
            
            director = DirectorAgent(director_db)
            
            # Process task through DirectorAgent
            result = director.execute_task(task)
            
            # Log the task submission
            app.logger.info(f'Task submitted: {task_id}, type: {task_type}')
            
            # Return standardized response
            return jsonify({
                'status': 'success',
                'task_id': task_id,
                'message': 'Task submitted successfully',
                'routing_result': result,
                'task_details': {
                    'id': task.id,
                    'title': task.title,
                    'type': task_type,
                    'status': task.status.value,
                    'created_at': task.created_at.isoformat()
                }
            }), 201
            
        except Exception as e:
            # Log the error
            app.logger.error(f'Error processing task submission: {str(e)}')
            
            return jsonify({
                'status': 'error',
                'error': 'Internal server error',
                'message': 'Failed to process task submission'
            }), 500

    # ============================================================================
    # AGENTS CRUD API ENDPOINTS
    # ============================================================================
    
    @app.route('/api/agents', methods=['GET'])
    def get_agents():
        """Get all agents"""
        try:
            from .models import Agent
            agents = Agent.query.all()
            return jsonify({
                'status': 'success',
                'agents': [agent.to_dict() for agent in agents],
                'count': len(agents)
            })
        except Exception as e:
            app.logger.error(f'Error fetching agents: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/agents', methods=['POST'])
    def create_agent():
        """Create a new agent"""
        try:
            data = request.get_json()
            if not data.get('name'):
                return jsonify({'status': 'error', 'error': 'Agent name is required'}), 400
            if not data.get('agent_type'):
                return jsonify({'status': 'error', 'error': 'Agent type is required'}), 400
            
            from .models import Agent
            from .models.agent import AgentType, AgentStatus
            agent = Agent(
                name=data['name'],
                description=data.get('description', ''),
                agent_type=getattr(AgentType, data['agent_type'].upper()),
                status=getattr(AgentStatus, data.get('status', 'IDLE').upper()),
                capabilities=data.get('capabilities', {}),
                config=data.get('config', {})
            )
            agent.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Agent created successfully',
                'agent': agent.to_dict()
            }), 201
            
        except Exception as e:
            app.logger.error(f'Error creating agent: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/agents/<int:agent_id>', methods=['DELETE'])
    def delete_agent(agent_id):
        """Delete an agent"""
        try:
            from .models import Agent
            agent = Agent.query.get_or_404(agent_id)
            agent.delete()
            return jsonify({
                'status': 'success',
                'message': 'Agent deleted successfully'
            })
        except Exception as e:
            app.logger.error(f'Error deleting agent {agent_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # TASKS CRUD API ENDPOINTS
    # ============================================================================
    
    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        """Get all tasks"""
        try:
            from .models.task import Task
            tasks = Task.query.all()
            return jsonify({
                'status': 'success',
                'tasks': [task.to_dict() for task in tasks],
                'count': len(tasks)
            })
        except Exception as e:
            app.logger.error(f'Error fetching tasks: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/tasks', methods=['POST'])
    def create_task_api():
        """Create a new task (different from existing submit_task)"""
        try:
            data = request.get_json()
            if not data.get('title'):
                return jsonify({'status': 'error', 'error': 'Task title is required'}), 400
            
            from models.task import TaskStatus, TaskPriority
            task = Task(
                title=data['title'],
                description=data.get('description', ''),
                status=getattr(TaskStatus, data.get('status', 'PENDING').upper()),
                priority=getattr(TaskPriority, data.get('priority', 'MEDIUM').upper()),
                assigned_agent_id=data.get('assigned_agent_id'),
                input_data=data.get('input_data', {}),
                progress_percentage=data.get('progress_percentage', 0)
            )
            task.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Task created successfully',
                'task': task.to_dict()
            }), 201
            
        except Exception as e:
            app.logger.error(f'Error creating task: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # CONVERSATIONS CRUD API ENDPOINTS
    # ============================================================================
    
    @app.route('/api/conversations', methods=['GET'])
    def get_conversations():
        """Get all conversations"""
        try:
            from .models.conversation import Conversation
            conversations = Conversation.query.all()
            return jsonify({
                'status': 'success',
                'conversations': [conv.to_dict() for conv in conversations],
                'count': len(conversations)
            })
        except Exception as e:
            app.logger.error(f'Error fetching conversations: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # WEB UI DASHBOARD ROUTES
    # ============================================================================
    
    @app.route('/dashboard')
    def dashboard():
        """Main dashboard page"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SwarmDirector Dashboard</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/dashboard">
                <i class="fas fa-sitemap"></i> SwarmDirector
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/dashboard/agents">Agents</a>
                <a class="nav-link" href="/dashboard/tasks">Tasks</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1><i class="fas fa-tachometer-alt"></i> SwarmDirector Dashboard</h1>
                <p class="lead">Hierarchical AI Agent Management System</p>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-md-4">
                <div class="card text-white bg-primary">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">Agents</h4>
                                <p class="card-text" id="agent-count">Loading...</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-robot fa-2x"></i>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <a href="/dashboard/agents" class="text-white">View all agents</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card text-white bg-success">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">Tasks</h4>
                                <p class="card-text" id="task-count">Loading...</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-tasks fa-2x"></i>
                            </div>
                        </div>
                    </div>
                    <div class="card-footer">
                        <a href="/dashboard/tasks" class="text-white">View all tasks</a>
                    </div>
                </div>
            </div>
            
            <div class="col-md-4">
                <div class="card text-white bg-info">
                    <div class="card-body">
                        <div class="d-flex justify-content-between">
                            <div>
                                <h4 class="card-title">Conversations</h4>
                                <p class="card-text" id="conversation-count">Loading...</p>
                            </div>
                            <div class="align-self-center">
                                <i class="fas fa-comments fa-2x"></i>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        async function loadDashboardData() {
            try {
                const [agentResponse, taskResponse, convResponse] = await Promise.all([
                    fetch('/api/agents'),
                    fetch('/api/tasks'),
                    fetch('/api/conversations')
                ]);
                
                const [agentData, taskData, convData] = await Promise.all([
                    agentResponse.json(),
                    taskResponse.json(),
                    convResponse.json()
                ]);
                
                document.getElementById('agent-count').textContent = agentData.count || 0;
                document.getElementById('task-count').textContent = taskData.count || 0;
                document.getElementById('conversation-count').textContent = convData.count || 0;
                
            } catch (error) {
                console.error('Error loading dashboard data:', error);
            }
        }
        
        document.addEventListener('DOMContentLoaded', loadDashboardData);
    </script>
</body>
</html>'''
    
    @app.route('/dashboard/agents')
    def agents_page():
        """Agents management page"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agents - SwarmDirector</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/dashboard">
                <i class="fas fa-sitemap"></i> SwarmDirector
            </a>
            <div class="navbar-nav">
                <a class="nav-link active" href="/dashboard/agents">Agents</a>
                <a class="nav-link" href="/dashboard/tasks">Tasks</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <div class="d-flex justify-content-between align-items-center">
                    <h1><i class="fas fa-robot"></i> Agent Management</h1>
                    <button class="btn btn-primary" onclick="toggleAddForm()">
                        <i class="fas fa-plus"></i> Add Agent
                    </button>
                </div>
            </div>
        </div>
        
        <div id="addForm" style="display: none;" class="row mt-3">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5>Add New Agent</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="agentName" class="form-label">Name *</label>
                                    <input type="text" class="form-control" id="agentName" required>
                                </div>
                            </div>
                            <div class="col-md-6">
                                <div class="mb-3">
                                    <label for="agentType" class="form-label">Type *</label>
                                    <select class="form-select" id="agentType" required>
                                        <option value="">Select type...</option>
                                        <option value="supervisor">Supervisor</option>
                                        <option value="coordinator">Coordinator</option>
                                        <option value="worker">Worker</option>
                                        <option value="specialist">Specialist</option>
                                    </select>
                                </div>
                            </div>
                        </div>
                        <div class="mb-3">
                            <label for="agentDescription" class="form-label">Description</label>
                            <textarea class="form-control" id="agentDescription" rows="3"></textarea>
                        </div>
                        <div class="d-flex gap-2">
                            <button type="button" class="btn btn-success" onclick="createAgent()">Create Agent</button>
                            <button type="button" class="btn btn-secondary" onclick="toggleAddForm()">Cancel</button>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-list"></i> All Agents</h5>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Status</th>
                                        <th>Description</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="agentsTableBody">
                                    <tr>
                                        <td colspan="6" class="text-center">Loading agents...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <script>
        function toggleAddForm() {
            const form = document.getElementById('addForm');
            form.style.display = form.style.display === 'none' ? 'block' : 'none';
        }
        
        async function loadAgents() {
            try {
                const response = await fetch('/api/agents');
                const data = await response.json();
                
                const tbody = document.getElementById('agentsTableBody');
                
                if (data.agents && data.agents.length > 0) {
                    tbody.innerHTML = data.agents.map(agent => `
                        <tr>
                            <td>${agent.id}</td>
                            <td>${agent.name}</td>
                            <td><span class="badge bg-info">${agent.agent_type}</span></td>
                            <td><span class="badge bg-success">${agent.status}</span></td>
                            <td>${agent.description || 'No description'}</td>
                            <td>
                                <button class="btn btn-sm btn-outline-danger" onclick="deleteAgent(${agent.id})">
                                    <i class="fas fa-trash"></i> Delete
                                </button>
                            </td>
                        </tr>
                    `).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="6" class="text-center">No agents found</td></tr>';
                }
            } catch (error) {
                console.error('Error loading agents:', error);
                document.getElementById('agentsTableBody').innerHTML = 
                    '<tr><td colspan="6" class="text-center text-danger">Error loading agents</td></tr>';
            }
        }
        
        async function createAgent() {
            const name = document.getElementById('agentName').value;
            const type = document.getElementById('agentType').value;
            const description = document.getElementById('agentDescription').value;
            
            if (!name || !type) {
                alert('Name and type are required');
                return;
            }
            
            try {
                const response = await fetch('/api/agents', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        name: name,
                        agent_type: type,
                        description: description
                    })
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    // Reset form and hide it
                    document.getElementById('agentName').value = '';
                    document.getElementById('agentType').value = '';
                    document.getElementById('agentDescription').value = '';
                    toggleAddForm();
                    loadAgents();
                } else {
                    alert('Error creating agent: ' + data.error);
                }
            } catch (error) {
                console.error('Error creating agent:', error);
                alert('Error creating agent');
            }
        }
        
        async function deleteAgent(id) {
            if (!confirm('Are you sure you want to delete this agent?')) {
                return;
            }
            
            try {
                const response = await fetch(`/api/agents/${id}`, {
                    method: 'DELETE'
                });
                
                const data = await response.json();
                
                if (data.status === 'success') {
                    loadAgents();
                } else {
                    alert('Error deleting agent: ' + data.error);
                }
            } catch (error) {
                console.error('Error deleting agent:', error);
                alert('Error deleting agent');
            }
        }
        
        document.addEventListener('DOMContentLoaded', loadAgents);
    </script>
</body>
</html>'''

def register_database_commands(app):
    """Register database management CLI commands"""
    
    @app.cli.command()
    def init_db():
        """Initialize the database with tables"""
        from models.base import db
        db.create_all()
        print("✅ Database tables created successfully!")
        
    @app.cli.command()
    def reset_db():
        """Reset the database (WARNING: This will delete all data!)"""
        from models.base import db
        import click
        
        if click.confirm('⚠️  This will delete ALL data. Are you sure?'):
            db.drop_all()
            db.create_all()
            print("✅ Database reset completed!")
        else:
            print("❌ Database reset cancelled.")
            
    @app.cli.command()
    def seed_db():
        """Seed the database with sample data"""
        from .models.agent import Agent, AgentType, AgentStatus
        from .models.task import Task, TaskStatus, TaskPriority
        from .models.conversation import Conversation, ConversationStatus
        from .models.base import db
        
        try:
            # Create sample agents
            supervisor = Agent(
                name="Supervisor Agent",
                description="Main supervisor for coordinating work",
                agent_type=AgentType.SUPERVISOR,
                status=AgentStatus.ACTIVE,
                capabilities={"coordination": True, "task_assignment": True},
                config={"max_concurrent_tasks": 10}
            )
            supervisor.save()
            
            worker = Agent(
                name="Worker Agent 1",
                description="Worker agent for general tasks",
                agent_type=AgentType.WORKER,
                status=AgentStatus.IDLE,
                parent_id=supervisor.id,
                capabilities={"data_processing": True, "analysis": True},
                config={"max_task_duration": 60}
            )
            worker.save()
            
            # Create sample task
            task = Task(
                title="Sample Task",
                description="A sample task for testing",
                status=TaskStatus.PENDING,
                priority=TaskPriority.MEDIUM,
                assigned_agent_id=worker.id,
                input_data={"test": "data"}
            )
            task.save()
            
            # Create sample conversation
            conversation = Conversation(
                title="Test Conversation",
                description="Sample conversation for testing",
                status=ConversationStatus.ACTIVE,
                initiator_agent_id=supervisor.id,
                session_id="test-session-001",
                conversation_type="task_assignment"
            )
            conversation.save()
            
            print("✅ Database seeded with sample data!")
            print(f"   - Agents: {Agent.query.count()}")
            print(f"   - Tasks: {Task.query.count()}")
            print(f"   - Conversations: {Conversation.query.count()}")
            
        except Exception as e:
            print(f"❌ Error seeding database: {e}")
            db.session.rollback()
            
    @app.cli.command()
    def db_status():
        """Show database status and record counts"""
        from .models.agent import Agent
        from .models.task import Task
        from .models.conversation import Conversation, Message
        from .models.base import db
        from sqlalchemy import text
        
        try:
            # Get table list
            result = db.session.execute(text('SELECT name FROM sqlite_master WHERE type="table" AND name != "alembic_version"')).fetchall()
            tables = [row[0] for row in result]
            
            print("📊 Database Status:")
            print(f"   Database file: swarm_director_dev.db")
            print(f"   Tables: {', '.join(tables)}")
            print()
            print("📈 Record Counts:")
            print(f"   - Agents: {Agent.query.count()}")
            print(f"   - Tasks: {Task.query.count()}")
            print(f"   - Conversations: {Conversation.query.count()}")
            print(f"   - Messages: {Message.query.count()}")
            
        except Exception as e:
            print(f"❌ Error checking database status: {e}")
            
    @app.cli.command()
    def validate_schema():
        """Validate database schema matches models"""
        from .models.base import db
        from sqlalchemy import inspect
        
        try:
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            print("🔍 Schema Validation:")
            
            expected_tables = ['agents', 'tasks', 'conversations', 'messages']
            missing_tables = [table for table in expected_tables if table not in tables]
            
            if missing_tables:
                print(f"❌ Missing tables: {missing_tables}")
            else:
                print("✅ All expected tables present")
                
            for table_name in expected_tables:
                if table_name in tables:
                    columns = inspector.get_columns(table_name)
                    print(f"   - {table_name}: {len(columns)} columns")
                    
        except Exception as e:
            print(f"❌ Error validating schema: {e}")

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create and run the app
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 