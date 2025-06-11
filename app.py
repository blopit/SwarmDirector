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
from models.base import db
migrate = Migrate()
mail = Mail()

def create_app(config_name='default'):
    """Application factory pattern for Flask app creation"""
    app = Flask(__name__)
    
    # Load configuration
    from config import config
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
        from models.base import db as models_db
        # Import all models to register them
        from models.agent import Agent
        from models.task import Task  
        from models.conversation import Conversation, Message
    except ImportError as e:
        # Models import failed, log the error but continue
        print(f"Warning: Could not import models - {e}")
        pass
    
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
            from models.task import Task, TaskStatus, TaskPriority
            from models.agent import Agent, AgentType
            from agents.director import DirectorAgent
            
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

if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create and run the app
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 