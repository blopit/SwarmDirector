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

# Import metrics system
from .utils.metrics import get_current_metrics_summary, metrics_collector, track_performance_metrics
from .utils.logging import setup_metrics_integration

# Initialize streaming manager (will be configured in create_app)
streaming_manager = None
socketio = None

def create_app(config_name='default'):
    """Application factory pattern for Flask app creation"""
    import os
    
    # Get the directory of this file (app.py)
    basedir = os.path.abspath(os.path.dirname(__file__))
    template_dir = os.path.join(basedir, 'web', 'templates')
    static_dir = os.path.join(basedir, 'web', 'static')
    
    app = Flask(__name__, 
                template_folder=template_dir,
                static_folder=static_dir,
                static_url_path='/static')
    
    # Load configuration
    from .config import config
    app.config.from_object(config[config_name])
    
    # Initialize extensions with app
    db.init_app(app)
    migrate.init_app(app, db)
    mail.init_app(app)
    
    # Initialize streaming and WebSocket functionality
    initialize_streaming(app)
    
    # Configure logging
    setup_logging(app)
    
    # Setup metrics integration
    setup_metrics_integration()
    
    # Setup alerting system
    setup_alerting_system(app)
    
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
    
    # Register WebSocket routes
    register_websocket_routes(app)
    
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
    """Register enhanced error handling middleware"""
    from .utils.error_handler import ErrorHandler
    
    # Initialize enhanced error handler
    error_handler = ErrorHandler()
    error_handler.init_app(app)
    
    # Store reference in app extensions
    app.extensions['error_handler'] = error_handler

def register_routes(app):
    """Register application routes"""
    
    @app.route('/')
    def index():
        """Health check endpoint"""
        from .utils.response_formatter import ResponseFormatter
        return ResponseFormatter.success(
            data={
                'message': 'SwarmDirector API is running',
                'status': 'healthy'
            }
        )
    
    @app.route('/health')
    def health_check():
        """Detailed health check endpoint"""
        from .utils.response_formatter import ResponseFormatter
        try:
            # Test database connection using proper SQLAlchemy syntax
            db.session.execute(text('SELECT 1'))
            db_status = 'connected'
        except Exception as e:
            db_status = f'error: {str(e)}'
        
        return ResponseFormatter.success(
            data={
                'status': 'healthy',
                'database': db_status,
                'version': '1.0.0'
            }
        )
    
    # Performance Metrics API Endpoints
    @app.route('/api/metrics/summary')
    @track_performance_metrics(endpoint='/api/metrics/summary')
    def get_metrics_summary():
        """Get comprehensive metrics summary"""
        try:
            summary = get_current_metrics_summary()
            return jsonify({
                'success': True,
                'data': summary
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/metrics/system')
    @track_performance_metrics(endpoint='/api/metrics/system')
    def get_system_metrics():
        """Get current system metrics"""
        try:
            correlation_id = request.headers.get('X-Correlation-ID')
            system_metrics = metrics_collector.collect_system_metrics(correlation_id)
            
            metrics_data = {
                name: {
                    'value': metric.value,
                    'unit': metric.unit,
                    'timestamp': metric.timestamp.isoformat(),
                    'tags': metric.tags
                } for name, metric in system_metrics.items()
            }
            
            return jsonify({
                'success': True,
                'data': metrics_data
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/metrics/endpoints')
    @track_performance_metrics(endpoint='/api/metrics/endpoints')
    def get_endpoint_metrics():
        """Get endpoint performance statistics"""
        try:
            endpoint_stats = metrics_collector.get_all_endpoint_stats()
            return jsonify({
                'success': True,
                'data': endpoint_stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/metrics/endpoint/<path:endpoint_name>')
    @track_performance_metrics(endpoint='/api/metrics/endpoint/*')
    def get_endpoint_metric(endpoint_name):
        """Get metrics for a specific endpoint"""
        try:
            stats = metrics_collector.get_endpoint_stats(endpoint_name)
            return jsonify({
                'success': True,
                'data': stats
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    # ============================================================================
    # MONITORING AND ALERTING API ENDPOINTS
    # ============================================================================

    @app.route('/monitoring')
    def monitoring_dashboard():
        """Monitoring dashboard page with real-time metrics visualization"""
        from flask import render_template
        return render_template('monitoring_dashboard.html')

    @app.route('/api/alerts/active')
    def get_active_alerts():
        """Get all active alerts"""
        try:
            from .utils.alerting import get_alerting_engine
            alerting_engine = get_alerting_engine()
            active_alerts = alerting_engine.get_active_alerts()
            
            return jsonify({
                'success': True,
                'data': active_alerts,
                'count': len(active_alerts)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/alerts/history')
    def get_alert_history():
        """Get alert history"""
        try:
            from .utils.alerting import get_alerting_engine
            alerting_engine = get_alerting_engine()
            limit = request.args.get('limit', 100, type=int)
            alert_history = alerting_engine.get_alert_history(limit)
            
            return jsonify({
                'success': True,
                'data': alert_history,
                'count': len(alert_history)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/alerts/acknowledge/<alert_id>', methods=['POST'])
    def acknowledge_alert(alert_id):
        """Acknowledge an active alert"""
        try:
            from .utils.alerting import get_alerting_engine
            alerting_engine = get_alerting_engine()
            
            data = request.get_json() or {}
            acknowledged_by = data.get('acknowledged_by', 'Unknown')
            
            success = alerting_engine.acknowledge_alert(alert_id, acknowledged_by)
            
            if success:
                return jsonify({
                    'success': True,
                    'message': 'Alert acknowledged successfully'
                })
            else:
                return jsonify({
                    'success': False,
                    'error': 'Alert not found or already acknowledged'
                }), 404
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/alerts/thresholds', methods=['GET', 'POST'])
    def manage_alert_thresholds():
        """Get or update alert thresholds"""
        try:
            from .utils.alerting import get_alerting_engine
            alerting_engine = get_alerting_engine()
            
            if request.method == 'GET':
                # Return current thresholds
                thresholds = {}
                for name, threshold in alerting_engine.thresholds.items():
                    thresholds[name] = {
                        'metric_name': threshold.metric_name,
                        'threshold_value': threshold.threshold_value,
                        'comparison': threshold.comparison,
                        'level': threshold.level.value,
                        'cooldown_minutes': threshold.cooldown_minutes,
                        'description': threshold.description
                    }
                
                return jsonify({
                    'success': True,
                    'data': thresholds
                })
            
            elif request.method == 'POST':
                # Update thresholds
                data = request.get_json() or {}
                updated_count = 0
                
                for metric_name, new_value in data.items():
                    if alerting_engine.update_threshold_value(metric_name, float(new_value)):
                        updated_count += 1
                
                return jsonify({
                    'success': True,
                    'message': f'Updated {updated_count} thresholds'
                })
                
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500

    @app.route('/api/logs/recent')
    def get_recent_logs():
        """Get recent log entries for dashboard display"""
        try:
            # This would typically read from your log files or database
            # For now, return mock data that matches the expected format
            mock_logs = [
                {
                    'timestamp': '2025-06-13T05:30:00Z',
                    'level': 'INFO',
                    'message': 'System health check completed successfully',
                    'correlation_id': 'health-check-001'
                },
                {
                    'timestamp': '2025-06-13T05:29:45Z',
                    'level': 'DEBUG',
                    'message': 'Metrics collection cycle completed',
                    'correlation_id': 'metrics-001'
                },
                {
                    'timestamp': '2025-06-13T05:29:30Z',
                    'level': 'INFO',
                    'message': 'Performance monitoring active',
                    'correlation_id': 'perf-monitor-001'
                }
            ]
            
            return jsonify({
                'success': True,
                'data': mock_logs,
                'count': len(mock_logs)
            })
        except Exception as e:
            return jsonify({
                'success': False,
                'error': str(e)
            }), 500
    
    @app.route('/task', methods=['POST'])
    @track_performance_metrics(endpoint='/task')
    def submit_task():
        """Enhanced task submission endpoint with comprehensive validation"""
        try:
            # Import validation utilities and response formatter
            from .utils.validation import validate_request, RequestValidator
            from .utils.rate_limiter import api_rate_limit
            from .schemas.task_schemas import get_schema_for_task_type
            from .utils.response_formatter import ResponseFormatter
            from .utils.error_handler import ValidationError, RateLimitError, DatabaseError, SwarmDirectorError
            from .utils.rate_limiter import rate_limiter, get_client_identifier
            from jsonschema import validate, ValidationError as JsonSchemaValidationError
            
            # Apply comprehensive validation
            try:
                # 1. Content-type validation
                RequestValidator.validate_content_type()
                
                # 2. JSON body validation and sanitization
                data = RequestValidator.validate_json_body()
                
                # 3. Basic structure validation
                if not data or 'type' not in data:
                    raise ValidationError('Field "type" is required', field='type')
                
                # 4. Get task-specific schema and validate
                task_type = data.get('type')
                schema = get_schema_for_task_type(task_type)
                
                # Apply schema validation
                try:
                    validate(instance=data, schema=schema)
                except JsonSchemaValidationError as e:
                    field_path = ".".join(str(p) for p in e.absolute_path) if e.absolute_path else "root"
                    raise ValidationError(
                        f"Schema validation failed: {e.message}",
                        field=field_path
                    )
                
                # 5. Sanitize all input data
                data = RequestValidator.sanitize_input(data)
                
                # 6. Rate limiting check (simulated - would normally use decorator)
                client_id = get_client_identifier()
                is_allowed, rate_info = rate_limiter.is_allowed(f"ip:{client_id}", 100, 3600)
                
                if not is_allowed:
                    raise RateLimitError(
                        'Rate limit exceeded',
                        retry_after=rate_info.get('retry_after')
                    )
                
            except (ValidationError, RateLimitError):
                # Re-raise custom errors to be handled by error handlers
                raise
            except Exception as validation_error:
                raise ValidationError(str(validation_error))
            
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
            try:
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
            except Exception as db_error:
                raise DatabaseError(
                    f"Failed to create task: {str(db_error)}",
                    details={'operation': 'task_creation'}
                )
            
            # Generate unique task_id for response
            task_id = f"task_{task.id}_{task.created_at.strftime('%Y%m%d_%H%M%S')}"
            
            # Get or create DirectorAgent
            try:
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
            except Exception as db_error:
                raise DatabaseError(
                    f"Failed to access or create DirectorAgent: {str(db_error)}",
                    details={'operation': 'agent_access'}
                )
            
            director = DirectorAgent(director_db)
            
            # Process task through DirectorAgent
            try:
                result = director.execute_task(task)
            except Exception as execution_error:
                raise SwarmDirectorError(
                    f"Task execution failed: {str(execution_error)}",
                    error_code='TASK_EXECUTION_ERROR',
                    status_code=500,
                    details={'task_id': task_id, 'task_type': task_type}
                )
            
            # Log the task submission
            app.logger.info(f'Task submitted: {task_id}, type: {task_type}')
            
            # Return standardized response
            return ResponseFormatter.success(
                data={
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
                },
                status_code=201
            )
        
        except (ValidationError, RateLimitError, DatabaseError, SwarmDirectorError):
            # Re-raise SwarmDirector errors to be handled by the error handlers
            raise
        except Exception as e:
            # Log the error
            app.logger.error(f'Error processing task submission: {str(e)}')
            
            return ResponseFormatter.internal_error(
                message='Failed to process task submission'
            )

    # ============================================================================
    # AGENTS CRUD API ENDPOINTS
    # ============================================================================
    
    @app.route('/api/agents', methods=['GET'])
    def get_agents():
        """Get all agents"""
        from .utils.response_formatter import ResponseFormatter
        try:
            from .models import Agent
            agents = Agent.query.all()
            return ResponseFormatter.success(
                data={
                    'agents': [agent.to_dict() for agent in agents],
                    'count': len(agents)
                }
            )
        except Exception as e:
            app.logger.error(f'Error fetching agents: {str(e)}')
            return ResponseFormatter.internal_error(
                message='Failed to fetch agents'
            )
    
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
            app.logger.error(f'Error fetching conversations: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    # ===== ANALYTICS ROUTES =====
    
    @app.route('/api/analytics/conversations', methods=['GET'])
    def get_conversation_analytics():
        """Get analytics for all conversations"""
        try:
            from .models.conversation import Conversation, ConversationAnalytics
            from .utils.conversation_analytics import create_analytics_engine
            
            # Get query parameters
            status_filter = request.args.get('status')
            pattern_filter = request.args.get('pattern')
            limit = request.args.get('limit', 50, type=int)
            
            # Build query
            query = Conversation.query
            if status_filter:
                query = query.filter_by(status=status_filter)
            if pattern_filter:
                query = query.filter_by(orchestration_pattern=pattern_filter)
            
            conversations = query.order_by(Conversation.created_at.desc()).limit(limit).all()
            
            # Get analytics for each conversation
            analytics_engine = create_analytics_engine()
            results = []
            
            for conv in conversations:
                analytics = ConversationAnalytics.query.filter_by(conversation_id=conv.id).first()
                if not analytics:
                    # Generate analytics if not exists
                    analytics = analytics_engine.analyze_conversation(conv.id)
                
                conv_data = conv.to_dict()
                conv_data['analytics'] = analytics.to_dict() if analytics else None
                results.append(conv_data)
            
            return jsonify({
                'status': 'success',
                'conversations': results,
                'total': len(results)
            })
        except Exception as e:
            app.logger.error(f'Error fetching conversation analytics: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/conversations/<int:conversation_id>', methods=['GET'])
    def get_conversation_analytics_detail(conversation_id):
        """Get detailed analytics for a specific conversation"""
        try:
            from .models.conversation import Conversation
            from .utils.conversation_analytics import create_analytics_engine
            
            conversation = Conversation.query.get_or_404(conversation_id)
            analytics_engine = create_analytics_engine()
            
            # Get comprehensive insights
            insights = analytics_engine.get_conversation_insights(conversation_id)
            
            return jsonify({
                'status': 'success',
                'conversation': conversation.to_dict(),
                'insights': insights
            })
        except Exception as e:
            app.logger.error(f'Error fetching conversation analytics detail: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/conversations/<int:conversation_id>/regenerate', methods=['POST'])
    def regenerate_conversation_analytics(conversation_id):
        """Regenerate analytics for a specific conversation"""
        try:
            from .models.conversation import Conversation
            from .utils.conversation_analytics import create_analytics_engine
            
            conversation = Conversation.query.get_or_404(conversation_id)
            analytics_engine = create_analytics_engine()
            
            # Force regeneration of analytics
            analytics = analytics_engine.analyze_conversation(conversation_id)
            
            return jsonify({
                'status': 'success',
                'message': 'Analytics regenerated successfully',
                'analytics': analytics.to_dict() if analytics else None
            })
        except Exception as e:
            app.logger.error(f'Error regenerating analytics: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/summary', methods=['GET'])
    def get_analytics_summary():
        """Get overall analytics summary across all conversations"""
        try:
            from .models.conversation import Conversation, ConversationAnalytics, OrchestrationPattern
            from sqlalchemy import func
            
            # Basic conversation stats
            total_conversations = Conversation.query.count()
            active_conversations = Conversation.query.filter_by(status='active').count()
            completed_conversations = Conversation.query.filter_by(status='completed').count()
            
            # Analytics aggregations
            analytics_stats = db.session.query(
                func.avg(ConversationAnalytics.total_duration).label('avg_duration'),
                func.avg(ConversationAnalytics.goal_achievement).label('avg_goal_achievement'),
                func.avg(ConversationAnalytics.agent_collaboration_score).label('avg_collaboration'),
                func.avg(ConversationAnalytics.overall_sentiment).label('avg_sentiment'),
                func.sum(ConversationAnalytics.total_participants).label('total_participants'),
                func.sum(ConversationAnalytics.error_count).label('total_errors')
            ).first()
            
            # Pattern distribution
            pattern_distribution = db.session.query(
                Conversation.orchestration_pattern,
                func.count(Conversation.id).label('count')
            ).group_by(Conversation.orchestration_pattern).all()
            
            # Recent activity (last 7 days)
            from datetime import datetime, timedelta
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_conversations = Conversation.query.filter(
                Conversation.created_at >= week_ago
            ).count()
            
            return jsonify({
                'status': 'success',
                'summary': {
                    'total_conversations': total_conversations,
                    'active_conversations': active_conversations,
                    'completed_conversations': completed_conversations,
                    'recent_conversations': recent_conversations,
                    'avg_duration_seconds': float(analytics_stats.avg_duration or 0),
                    'avg_goal_achievement': float(analytics_stats.avg_goal_achievement or 0),
                    'avg_collaboration_score': float(analytics_stats.avg_collaboration or 0),
                    'avg_sentiment': float(analytics_stats.avg_sentiment or 0),
                    'total_participants': int(analytics_stats.total_participants or 0),
                    'total_errors': int(analytics_stats.total_errors or 0),
                    'pattern_distribution': {
                        pattern[0].value if pattern[0] else None: pattern[1] for pattern in pattern_distribution if pattern[0]
                    }
                }
            })
        except Exception as e:
            app.logger.error(f'Error fetching analytics summary: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

    # ===== TASK ANALYTICS ROUTES =====
    
    @app.route('/api/analytics/tasks/metrics', methods=['GET'])
    def get_task_analytics_metrics():
        """Get comprehensive task analytics metrics"""
        try:
            from .analytics.engine import create_analytics_engine
            from datetime import datetime, timedelta
            
            # Get query parameters
            days = request.args.get('days', 30, type=int)
            start_date = request.args.get('start_date')
            end_date = request.args.get('end_date')
            
            # Calculate time range
            if start_date and end_date:
                start_time = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            else:
                end_time = datetime.utcnow()
                start_time = end_time - timedelta(days=days)
            
            time_range = (start_time, end_time)
            
            # Create analytics engine and collect metrics
            analytics_engine = create_analytics_engine()
            metrics = analytics_engine.collect_task_metrics(time_range)
            
            return jsonify({
                'status': 'success',
                'metrics': metrics,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                }
            })
        except Exception as e:
            app.logger.error(f'Error fetching task analytics metrics: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/tasks/insights', methods=['GET'])
    def get_task_analytics_insights():
        """Get task analytics insights and recommendations"""
        try:
            from .analytics.engine import create_analytics_engine
            from datetime import datetime, timedelta
            
            # Get query parameters
            days = request.args.get('days', 30, type=int)
            priority_filter = request.args.get('priority')
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            time_range = (start_time, end_time)
            
            # Create analytics engine
            analytics_engine = create_analytics_engine()
            
            # Collect metrics and generate insights
            metrics = analytics_engine.collect_task_metrics(time_range)
            insights = analytics_engine.generate_insights(metrics)
            
            # Filter insights by priority if requested
            if priority_filter:
                insights = [insight for insight in insights if insight.get('priority') == priority_filter]
            
            return jsonify({
                'status': 'success',
                'insights': insights,
                'metrics_summary': {
                    'completion_rate': metrics['completion_rates']['completion_rate'],
                    'failure_rate': metrics['completion_rates']['failure_rate'],
                    'total_tasks': metrics['completion_rates']['total_tasks']
                },
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                }
            })
        except Exception as e:
            app.logger.error(f'Error fetching task analytics insights: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/tasks/real-time', methods=['GET'])
    def get_task_real_time_metrics():
        """Get real-time task metrics"""
        try:
            from .analytics.engine import create_analytics_engine
            from datetime import datetime
            
            # Create analytics engine and get real-time metrics
            analytics_engine = create_analytics_engine()
            real_time_metrics = analytics_engine.get_real_time_metrics()
            
            return jsonify({
                'status': 'success',
                'real_time_metrics': real_time_metrics,
                'timestamp': datetime.utcnow().isoformat()
            })
        except Exception as e:
            app.logger.error(f'Error fetching real-time task metrics: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/tasks/performance-snapshot', methods=['POST'])
    def create_task_performance_snapshot():
        """Create a performance snapshot for current task state"""
        try:
            from .analytics.engine import create_analytics_engine
            
            # Create analytics engine and performance snapshot
            analytics_engine = create_analytics_engine()
            snapshot = analytics_engine.create_performance_snapshot()
            
            if snapshot:
                db.session.add(snapshot)
                db.session.commit()
                
                return jsonify({
                    'status': 'success',
                    'message': 'Performance snapshot created successfully',
                    'snapshot': snapshot.to_dict()
                })
            else:
                return jsonify({
                    'status': 'error',
                    'message': 'Failed to create performance snapshot'
                }), 500
        except Exception as e:
            app.logger.error(f'Error creating performance snapshot: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/tasks/trends', methods=['GET'])
    def get_task_performance_trends():
        """Get task performance trends over time"""
        try:
            from .analytics.engine import create_analytics_engine
            from datetime import datetime, timedelta
            
            # Get query parameters
            days = request.args.get('days', 30, type=int)
            metric_type = request.args.get('metric', 'completion_rate')
            
            # Calculate time range
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(days=days)
            time_range = (start_time, end_time)
            
            # Create analytics engine
            analytics_engine = create_analytics_engine()
            metrics = analytics_engine.collect_task_metrics(time_range)
            
            # Extract trend data based on metric type
            trend_data = metrics.get('performance_trends', {})
            
            return jsonify({
                'status': 'success',
                'trends': trend_data,
                'metric_type': metric_type,
                'time_range': {
                    'start': start_time.isoformat(),
                    'end': end_time.isoformat(),
                    'days': days
                }
            })
        except Exception as e:
            app.logger.error(f'Error fetching task performance trends: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500
    
    @app.route('/api/analytics/tasks/summary', methods=['GET'])
    def get_task_analytics_summary():
        """Get overall task analytics summary"""
        try:
            from .models.task import Task, TaskStatus
            from .analytics.engine import create_analytics_engine
            from sqlalchemy import func
            from datetime import datetime, timedelta
            
            # Basic task statistics
            total_tasks = Task.query.count()
            completed_tasks = Task.query.filter_by(status=TaskStatus.COMPLETED).count()
            failed_tasks = Task.query.filter_by(status=TaskStatus.FAILED).count()
            pending_tasks = Task.query.filter_by(status=TaskStatus.PENDING).count()
            in_progress_tasks = Task.query.filter_by(status=TaskStatus.IN_PROGRESS).count()
            
            # Recent activity (last 7 days)
            week_ago = datetime.utcnow() - timedelta(days=7)
            recent_tasks = Task.query.filter(Task.created_at >= week_ago).count()
            recent_completed = Task.query.filter(
                Task.created_at >= week_ago,
                Task.status == TaskStatus.COMPLETED
            ).count()
            
            # Average processing times
            avg_processing_time = db.session.query(
                func.avg(Task.processing_time)
            ).filter(Task.processing_time.isnot(None)).scalar()
            
            avg_queue_time = db.session.query(
                func.avg(Task.queue_time)
            ).filter(Task.queue_time.isnot(None)).scalar()
            
            # Task type distribution
            type_distribution = db.session.query(
                Task.type,
                func.count(Task.id).label('count')
            ).group_by(Task.type).all()
            
            # Priority distribution
            priority_distribution = db.session.query(
                Task.priority,
                func.count(Task.id).label('count')
            ).group_by(Task.priority).all()
            
            # Calculate rates
            completion_rate = completed_tasks / total_tasks if total_tasks > 0 else 0
            failure_rate = failed_tasks / total_tasks if total_tasks > 0 else 0
            recent_completion_rate = recent_completed / recent_tasks if recent_tasks > 0 else 0
            
            return jsonify({
                'status': 'success',
                'summary': {
                    'total_tasks': total_tasks,
                    'completed_tasks': completed_tasks,
                    'failed_tasks': failed_tasks,
                    'pending_tasks': pending_tasks,
                    'in_progress_tasks': in_progress_tasks,
                    'recent_tasks': recent_tasks,
                    'recent_completed': recent_completed,
                    'completion_rate': round(completion_rate, 3),
                    'failure_rate': round(failure_rate, 3),
                    'recent_completion_rate': round(recent_completion_rate, 3),
                    'avg_processing_time_minutes': float(avg_processing_time or 0),
                    'avg_queue_time_minutes': float(avg_queue_time or 0),
                    'type_distribution': {
                        task_type[0].value if task_type[0] else 'unknown': task_type[1] 
                        for task_type in type_distribution
                    },
                    'priority_distribution': {
                        priority[0].value if priority[0] else 'unknown': priority[1] 
                        for priority in priority_distribution
                    }
                }
            })
        except Exception as e:
            app.logger.error(f'Error fetching task analytics summary: {e}')
            return jsonify({
                'status': 'error',
                'message': str(e)
            }), 500

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
                <a class="nav-link" href="/dashboard/analytics">Analytics</a>
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
    
    @app.route('/websocket-test')
    def websocket_test():
        """WebSocket test page"""
        from flask import render_template
        return render_template('websocket_test.html')
    
    @app.route('/streaming-demo')
    def streaming_demo():
        """Comprehensive streaming demo page"""
        from flask import render_template
        return render_template('streaming_demo.html')
    
    @app.route('/chat')
    def chat():
        """Main chat interface with transparency features"""
        from flask import render_template
        return render_template('chat.html')
    
    @app.route('/health')
    def health():
        """Health check endpoint for testing"""
        return {'status': 'healthy', 'service': 'SwarmDirector'}
    
    @app.route('/dashboard/analytics')
    def analytics_page():
        """Analytics dashboard page"""
        return '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Analytics - SwarmDirector</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-dark">
        <div class="container">
            <a class="navbar-brand" href="/dashboard">
                <i class="fas fa-sitemap"></i> SwarmDirector
            </a>
            <div class="navbar-nav">
                <a class="nav-link" href="/dashboard/agents">Agents</a>
                <a class="nav-link active" href="/dashboard/analytics">Analytics</a>
                <a class="nav-link" href="/dashboard/tasks">Tasks</a>
            </div>
        </div>
    </nav>
    
    <div class="container mt-4">
        <div class="row">
            <div class="col-12">
                <h1><i class="fas fa-chart-line"></i> SwarmDirector Analytics</h1>
                <ul class="nav nav-tabs" id="analyticsTab" role="tablist">
                    <li class="nav-item" role="presentation">
                        <button class="nav-link active" id="tasks-tab" data-bs-toggle="tab" data-bs-target="#tasks" type="button" role="tab">
                            <i class="fas fa-tasks"></i> Task Analytics
                        </button>
                    </li>
                    <li class="nav-item" role="presentation">
                        <button class="nav-link" id="conversations-tab" data-bs-toggle="tab" data-bs-target="#conversations" type="button" role="tab">
                            <i class="fas fa-comments"></i> Conversation Analytics
                        </button>
                    </li>
                </ul>
            </div>
        </div>
        
        <div class="tab-content" id="analyticsTabContent">
            <!-- Task Analytics Tab -->
            <div class="tab-pane fade show active" id="tasks" role="tabpanel">
                <!-- Task Summary Cards -->
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5><i class="fas fa-tasks"></i> Total Tasks</h5>
                                <h2 id="totalTasks">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-success text-white">
                            <div class="card-body">
                                <h5><i class="fas fa-check-circle"></i> Completed</h5>
                                <h2 id="completedTasks">-</h2>
                                <small id="completionRate">-</small>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-warning text-white">
                            <div class="card-body">
                                <h5><i class="fas fa-spinner"></i> In Progress</h5>
                                <h2 id="inProgressTasks">-</h2>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-3">
                        <div class="card bg-danger text-white">
                            <div class="card-body">
                                <h5><i class="fas fa-exclamation-triangle"></i> Failed</h5>
                                <h2 id="failedTasks">-</h2>
                                <small id="failureRate">-</small>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Task Performance Metrics -->
                <div class="row mt-4">
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-line"></i> Performance Trends</h5>
                            </div>
                            <div class="card-body">
                                <canvas id="taskTrendsChart" width="400" height="200"></canvas>
                            </div>
                        </div>
                    </div>
                    <div class="col-md-6">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-pie"></i> Task Distribution</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-6">
                                        <canvas id="taskTypeChart" width="200" height="200"></canvas>
                                    </div>
                                    <div class="col-6">
                                        <canvas id="taskPriorityChart" width="200" height="200"></canvas>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Task Timing Analytics -->
                <div class="row mt-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-clock"></i> Timing Analytics</h5>
                            </div>
                            <div class="card-body">
                                <div class="row">
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6>Avg Processing Time</h6>
                                            <span id="avgProcessingTime" class="h4 text-primary">-</span>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6>Avg Queue Time</h6>
                                            <span id="avgQueueTime" class="h4 text-warning">-</span>
                                        </div>
                                    </div>
                                    <div class="col-md-4">
                                        <div class="text-center">
                                            <h6>Recent Tasks (7 days)</h6>
                                            <span id="recentTasks" class="h4 text-info">-</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
                
                <!-- Task Insights -->
                <div class="row mt-4">
                    <div class="col-md-12">
                        <div class="card">
                            <div class="card-header d-flex justify-content-between align-items-center">
                                <h5><i class="fas fa-lightbulb"></i> Analytics Insights</h5>
                                <button class="btn btn-sm btn-outline-primary" onclick="refreshInsights()">
                                    <i class="fas fa-refresh"></i> Refresh
                                </button>
                            </div>
                            <div class="card-body">
                                <div id="taskInsights">
                                    <div class="text-center">
                                        <div class="spinner-border" role="status">
                                            <span class="visually-hidden">Loading insights...</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Conversation Analytics Tab -->
            <div class="tab-pane fade" id="conversations" role="tabpanel">
        
                <!-- Summary Cards -->
                <div class="row mt-4">
                    <div class="col-md-3">
                        <div class="card bg-primary text-white">
                            <div class="card-body">
                                <h5><i class="fas fa-comments"></i> Total Conversations</h5>
                                <h2 id="totalConversations">-</h2>
                            </div>
                        </div>
                    </div>
            <div class="col-md-3">
                <div class="card bg-success text-white">
                    <div class="card-body">
                        <h5><i class="fas fa-check-circle"></i> Completed</h5>
                        <h2 id="completedConversations">-</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-warning text-white">
                    <div class="card-body">
                        <h5><i class="fas fa-clock"></i> Active</h5>
                        <h2 id="activeConversations">-</h2>
                    </div>
                </div>
            </div>
            <div class="col-md-3">
                <div class="card bg-info text-white">
                    <div class="card-body">
                        <h5><i class="fas fa-calendar-week"></i> This Week</h5>
                        <h2 id="recentConversations">-</h2>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Metrics Row -->
        <div class="row mt-4">
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-pie"></i> Orchestration Patterns</h5>
                    </div>
                    <div class="card-body">
                        <canvas id="patternsChart" width="400" height="200"></canvas>
                    </div>
                </div>
            </div>
            <div class="col-md-6">
                <div class="card">
                    <div class="card-header">
                        <h5><i class="fas fa-chart-bar"></i> Performance Metrics</h5>
                    </div>
                    <div class="card-body">
                        <div class="row">
                            <div class="col-6">
                                <div class="text-center">
                                    <h6>Avg Duration</h6>
                                    <span id="avgDuration" class="h4 text-primary">-</span>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center">
                                    <h6>Goal Achievement</h6>
                                    <span id="avgGoalAchievement" class="h4 text-success">-</span>
                                </div>
                            </div>
                            <div class="col-6 mt-3">
                                <div class="text-center">
                                    <h6>Collaboration Score</h6>
                                    <span id="avgCollaboration" class="h4 text-info">-</span>
                                </div>
                            </div>
                            <div class="col-6 mt-3">
                                <div class="text-center">
                                    <h6>Sentiment</h6>
                                    <span id="avgSentiment" class="h4 text-warning">-</span>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Conversations List -->
        <div class="row mt-4">
            <div class="col-12">
                <div class="card">
                    <div class="card-header d-flex justify-content-between align-items-center">
                        <h5><i class="fas fa-list"></i> Recent Conversations</h5>
                        <div>
                            <select id="statusFilter" class="form-select form-select-sm" onchange="loadConversations()">
                                <option value="">All Status</option>
                                <option value="active">Active</option>
                                <option value="completed">Completed</option>
                                <option value="paused">Paused</option>
                                <option value="error">Error</option>
                            </select>
                        </div>
                    </div>
                    <div class="card-body">
                        <div class="table-responsive">
                            <table class="table table-striped">
                                <thead>
                                    <tr>
                                        <th>ID</th>
                                        <th>Title</th>
                                        <th>Status</th>
                                        <th>Pattern</th>
                                        <th>Duration</th>
                                        <th>Messages</th>
                                        <th>Goal Achievement</th>
                                        <th>Actions</th>
                                    </tr>
                                </thead>
                                <tbody id="conversationsTableBody">
                                    <tr>
                                        <td colspan="8" class="text-center">Loading conversations...</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        </div> <!-- Close tab-content -->
    </div>
    
    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        let patternsChart = null;
        let taskTrendsChart = null;
        let taskTypeChart = null;
        let taskPriorityChart = null;
        
        // Task Analytics Functions
        async function loadTaskSummary() {
            try {
                const response = await fetch('/api/analytics/tasks/summary');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const summary = data.summary;
                    
                    // Update task summary cards
                    document.getElementById('totalTasks').textContent = summary.total_tasks;
                    document.getElementById('completedTasks').textContent = summary.completed_tasks;
                    document.getElementById('inProgressTasks').textContent = summary.in_progress_tasks;
                    document.getElementById('failedTasks').textContent = summary.failed_tasks;
                    
                    // Update rates
                    document.getElementById('completionRate').textContent = 
                        summary.completion_rate ? (summary.completion_rate * 100).toFixed(1) + '% completion rate' : 'No data';
                    document.getElementById('failureRate').textContent = 
                        summary.failure_rate ? (summary.failure_rate * 100).toFixed(1) + '% failure rate' : 'No data';
                    
                    // Update timing metrics
                    document.getElementById('avgProcessingTime').textContent = 
                        summary.avg_processing_time_minutes ? Math.round(summary.avg_processing_time_minutes) + ' min' : 'N/A';
                    document.getElementById('avgQueueTime').textContent = 
                        summary.avg_queue_time_minutes ? Math.round(summary.avg_queue_time_minutes) + ' min' : 'N/A';
                    document.getElementById('recentTasks').textContent = summary.recent_tasks;
                    
                    // Update charts
                    updateTaskTypeChart(summary.type_distribution);
                    updateTaskPriorityChart(summary.priority_distribution);
                }
            } catch (error) {
                console.error('Error loading task summary:', error);
            }
        }
        
        async function loadTaskTrends() {
            try {
                const response = await fetch('/api/analytics/tasks/trends?days=30');
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateTaskTrendsChart(data.trends);
                }
            } catch (error) {
                console.error('Error loading task trends:', error);
            }
        }
        
        async function loadTaskInsights() {
            try {
                const response = await fetch('/api/analytics/tasks/insights?days=30');
                const data = await response.json();
                
                const insightsContainer = document.getElementById('taskInsights');
                
                if (data.status === 'success' && data.insights.length > 0) {
                    insightsContainer.innerHTML = data.insights.map(insight => `
                        <div class="alert alert-${getPriorityClass(insight.priority)} mb-2">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="mb-1"><i class="fas fa-${getPriorityIcon(insight.priority)}"></i> ${insight.title}</h6>
                                    <p class="mb-1">${insight.description}</p>
                                    ${insight.action_items ? `<small><strong>Actions:</strong> ${insight.action_items.join(', ')}</small>` : ''}
                                </div>
                                <span class="badge bg-${getPriorityClass(insight.priority)}">${insight.priority}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    insightsContainer.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check"></i> All systems running smoothly! No critical insights at this time.
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading task insights:', error);
                document.getElementById('taskInsights').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> Error loading insights: ${error.message}
                    </div>
                `;
            }
        }
        
        function updateTaskTrendsChart(trendsData) {
            const ctx = document.getElementById('taskTrendsChart').getContext('2d');
            
            if (taskTrendsChart) {
                taskTrendsChart.destroy();
            }
            
            const dailyTrends = trendsData.daily_trends || [];
            
            taskTrendsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dailyTrends.map(d => d.date),
                    datasets: [{
                        label: 'Completed Tasks',
                        data: dailyTrends.map(d => d.completed_count),
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Avg Processing Time (min)',
                        data: dailyTrends.map(d => d.avg_processing_time),
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        }
        
        function updateTaskTypeChart(typeData) {
            const ctx = document.getElementById('taskTypeChart').getContext('2d');
            
            if (taskTypeChart) {
                taskTypeChart.destroy();
            }
            
            const labels = Object.keys(typeData);
            const data = Object.values(typeData);
            
            taskTypeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#007bff',
                            '#28a745',
                            '#ffc107',
                            '#dc3545',
                            '#6f42c1',
                            '#20c997'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'By Type'
                        }
                    }
                }
            });
        }
        
        function updateTaskPriorityChart(priorityData) {
            const ctx = document.getElementById('taskPriorityChart').getContext('2d');
            
            if (taskPriorityChart) {
                taskPriorityChart.destroy();
            }
            
            const labels = Object.keys(priorityData);
            const data = Object.values(priorityData);
            
            taskPriorityChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#dc3545',
                            '#ffc107',
                            '#28a745',
                            '#6c757d'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'By Priority'
                        }
                    }
                }
            });
        }
        
        function getPriorityClass(priority) {
            switch(priority) {
                case 'critical': return 'danger';
                case 'high': return 'warning';
                case 'medium': return 'info';
                case 'low': return 'secondary';
                default: return 'primary';
            }
        }
        
        function getPriorityIcon(priority) {
            switch(priority) {
                case 'critical': return 'exclamation-triangle';
                case 'high': return 'exclamation-circle';
                case 'medium': return 'info-circle';
                case 'low': return 'check-circle';
                default: return 'lightbulb';
            }
        }
        
        function refreshInsights() {
            document.getElementById('taskInsights').innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading insights...</span>
                    </div>
                </div>
            `;
            loadTaskInsights();
        }
        let taskTrendsChart = null;
        let taskTypeChart = null;
        let taskPriorityChart = null;
        
        // Task Analytics Functions
        async function loadTaskSummary() {
            try {
                const response = await fetch('/api/analytics/tasks/summary');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const summary = data.summary;
                    
                    // Update task summary cards
                    document.getElementById('totalTasks').textContent = summary.total_tasks;
                    document.getElementById('completedTasks').textContent = summary.completed_tasks;
                    document.getElementById('inProgressTasks').textContent = summary.in_progress_tasks;
                    document.getElementById('failedTasks').textContent = summary.failed_tasks;
                    
                    // Update rates
                    document.getElementById('completionRate').textContent = 
                        summary.completion_rate ? (summary.completion_rate * 100).toFixed(1) + '% completion rate' : 'No data';
                    document.getElementById('failureRate').textContent = 
                        summary.failure_rate ? (summary.failure_rate * 100).toFixed(1) + '% failure rate' : 'No data';
                    
                    // Update timing metrics
                    document.getElementById('avgProcessingTime').textContent = 
                        summary.avg_processing_time_minutes ? Math.round(summary.avg_processing_time_minutes) + ' min' : 'N/A';
                    document.getElementById('avgQueueTime').textContent = 
                        summary.avg_queue_time_minutes ? Math.round(summary.avg_queue_time_minutes) + ' min' : 'N/A';
                    document.getElementById('recentTasks').textContent = summary.recent_tasks;
                    
                    // Update charts
                    updateTaskTypeChart(summary.type_distribution);
                    updateTaskPriorityChart(summary.priority_distribution);
                }
            } catch (error) {
                console.error('Error loading task summary:', error);
            }
        }
        
        async function loadTaskTrends() {
            try {
                const response = await fetch('/api/analytics/tasks/trends?days=30');
                const data = await response.json();
                
                if (data.status === 'success') {
                    updateTaskTrendsChart(data.trends);
                }
            } catch (error) {
                console.error('Error loading task trends:', error);
            }
        }
        
        async function loadTaskInsights() {
            try {
                const response = await fetch('/api/analytics/tasks/insights?days=30');
                const data = await response.json();
                
                const insightsContainer = document.getElementById('taskInsights');
                
                if (data.status === 'success' && data.insights.length > 0) {
                    insightsContainer.innerHTML = data.insights.map(insight => `
                        <div class="alert alert-${getPriorityClass(insight.priority)} mb-2">
                            <div class="d-flex justify-content-between align-items-start">
                                <div>
                                    <h6 class="mb-1"><i class="fas fa-${getPriorityIcon(insight.priority)}"></i> ${insight.title}</h6>
                                    <p class="mb-1">${insight.description}</p>
                                    ${insight.action_items ? `<small><strong>Actions:</strong> ${insight.action_items.join(', ')}</small>` : ''}
                                </div>
                                <span class="badge bg-${getPriorityClass(insight.priority)}">${insight.priority}</span>
                            </div>
                        </div>
                    `).join('');
                } else {
                    insightsContainer.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check"></i> All systems running smoothly! No critical insights at this time.
                        </div>
                    `;
                }
            } catch (error) {
                console.error('Error loading task insights:', error);
                document.getElementById('taskInsights').innerHTML = `
                    <div class="alert alert-danger">
                        <i class="fas fa-exclamation-triangle"></i> Error loading insights: ${error.message}
                    </div>
                `;
            }
        }
        
        function updateTaskTrendsChart(trendsData) {
            const ctx = document.getElementById('taskTrendsChart').getContext('2d');
            
            if (taskTrendsChart) {
                taskTrendsChart.destroy();
            }
            
            const dailyTrends = trendsData.daily_trends || [];
            
            taskTrendsChart = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: dailyTrends.map(d => d.date),
                    datasets: [{
                        label: 'Completed Tasks',
                        data: dailyTrends.map(d => d.completed_count),
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        tension: 0.1
                    }, {
                        label: 'Avg Processing Time (min)',
                        data: dailyTrends.map(d => d.avg_processing_time),
                        borderColor: '#007bff',
                        backgroundColor: 'rgba(0, 123, 255, 0.1)',
                        yAxisID: 'y1',
                        tension: 0.1
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'top',
                        }
                    },
                    scales: {
                        y: {
                            type: 'linear',
                            display: true,
                            position: 'left',
                        },
                        y1: {
                            type: 'linear',
                            display: true,
                            position: 'right',
                            grid: {
                                drawOnChartArea: false,
                            },
                        }
                    }
                }
            });
        }
        
        function updateTaskTypeChart(typeData) {
            const ctx = document.getElementById('taskTypeChart').getContext('2d');
            
            if (taskTypeChart) {
                taskTypeChart.destroy();
            }
            
            const labels = Object.keys(typeData);
            const data = Object.values(typeData);
            
            taskTypeChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#007bff',
                            '#28a745',
                            '#ffc107',
                            '#dc3545',
                            '#6f42c1',
                            '#20c997'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'By Type'
                        }
                    }
                }
            });
        }
        
        function updateTaskPriorityChart(priorityData) {
            const ctx = document.getElementById('taskPriorityChart').getContext('2d');
            
            if (taskPriorityChart) {
                taskPriorityChart.destroy();
            }
            
            const labels = Object.keys(priorityData);
            const data = Object.values(priorityData);
            
            taskPriorityChart = new Chart(ctx, {
                type: 'doughnut',
                data: {
                    labels: labels,
                    datasets: [{
                        data: data,
                        backgroundColor: [
                            '#dc3545',
                            '#ffc107',
                            '#28a745',
                            '#6c757d'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        },
                        title: {
                            display: true,
                            text: 'By Priority'
                        }
                    }
                }
            });
        }
        
        function getPriorityClass(priority) {
            switch(priority) {
                case 'critical': return 'danger';
                case 'high': return 'warning';
                case 'medium': return 'info';
                case 'low': return 'secondary';
                default: return 'primary';
            }
        }
        
        function getPriorityIcon(priority) {
            switch(priority) {
                case 'critical': return 'exclamation-triangle';
                case 'high': return 'exclamation-circle';
                case 'medium': return 'info-circle';
                case 'low': return 'check-circle';
                default: return 'lightbulb';
            }
        }
        
        function refreshInsights() {
            document.getElementById('taskInsights').innerHTML = `
                <div class="text-center">
                    <div class="spinner-border" role="status">
                        <span class="visually-hidden">Loading insights...</span>
                    </div>
                </div>
            `;
            loadTaskInsights();
        }
        
        // Conversation Analytics Functions (existing)        
        // Initialize dashboard on load
        document.addEventListener('DOMContentLoaded', function() {
            // Load task analytics by default
            loadTaskSummary();
            loadTaskTrends();
            loadTaskInsights();
            
            // Handle tab switching
            const tabTriggerList = document.querySelectorAll('#analyticsTab button[data-bs-toggle="tab"]');
            tabTriggerList.forEach(tabTrigger => {
                tabTrigger.addEventListener('shown.bs.tab', function (event) {
                    const target = event.target.getAttribute('data-bs-target');
                    if (target === '#tasks') {
                        // Load task analytics when switching to tasks tab
                        loadTaskSummary();
                        loadTaskTrends();
                        loadTaskInsights();
                    } else if (target === '#conversations') {
                        // Load conversation analytics when switching to conversations tab
                        loadSummary();
                        loadConversations();
                    }
                });
            });
        });
        
        // Conversation Analytics Functions (existing)
        async function loadSummary() {
            try {
                const response = await fetch('/api/analytics/summary');
                const data = await response.json();
                
                if (data.status === 'success') {
                    const summary = data.summary;
                    
                    // Update summary cards
                    document.getElementById('totalConversations').textContent = summary.total_conversations;
                    document.getElementById('completedConversations').textContent = summary.completed_conversations;
                    document.getElementById('activeConversations').textContent = summary.active_conversations;
                    document.getElementById('recentConversations').textContent = summary.recent_conversations;
                    
                    // Update metrics
                    document.getElementById('avgDuration').textContent = 
                        summary.avg_duration_seconds ? Math.round(summary.avg_duration_seconds) + 's' : 'N/A';
                    document.getElementById('avgGoalAchievement').textContent = 
                        summary.avg_goal_achievement ? Math.round(summary.avg_goal_achievement) + '%' : 'N/A';
                    document.getElementById('avgCollaboration').textContent = 
                        summary.avg_collaboration_score ? Math.round(summary.avg_collaboration_score) + '%' : 'N/A';
                    document.getElementById('avgSentiment').textContent = 
                        summary.avg_sentiment ? summary.avg_sentiment.toFixed(2) : 'N/A';
                    
                    // Update patterns chart
                    updatePatternsChart(summary.pattern_distribution);
                }
            } catch (error) {
                console.error('Error loading summary:', error);
            }
        }
        
        function updatePatternsChart(patternData) {
            const ctx = document.getElementById('patternsChart').getContext('2d');
            
            if (patternsChart) {
                patternsChart.destroy();
            }
            
            const labels = Object.keys(patternData);
            const values = Object.values(patternData);
            
            patternsChart = new Chart(ctx, {
                type: 'pie',
                data: {
                    labels: labels.map(label => label.replace('_', ' ').toUpperCase()),
                    datasets: [{
                        data: values,
                        backgroundColor: [
                            '#FF6384', '#36A2EB', '#FFCE56', '#4BC0C0', 
                            '#9966FF', '#FF9F40', '#FF6384', '#C9CBCF'
                        ]
                    }]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    plugins: {
                        legend: {
                            position: 'bottom'
                        }
                    }
                }
            });
        }
        
        async function loadConversations() {
            try {
                const statusFilter = document.getElementById('statusFilter').value;
                const params = new URLSearchParams();
                if (statusFilter) params.append('status', statusFilter);
                
                const response = await fetch(`/api/analytics/conversations?${params}`);
                const data = await response.json();
                
                const tbody = document.getElementById('conversationsTableBody');
                
                if (data.conversations && data.conversations.length > 0) {
                    tbody.innerHTML = data.conversations.map(conv => {
                        const analytics = conv.analytics;
                        return `
                            <tr>
                                <td>${conv.id}</td>
                                <td>${conv.title || 'Untitled'}</td>
                                <td><span class="badge bg-${getStatusColor(conv.status)}">${conv.status}</span></td>
                                <td>${conv.orchestration_pattern || 'N/A'}</td>
                                <td>${analytics && analytics.total_duration ? Math.round(analytics.total_duration) + 's' : 'N/A'}</td>
                                <td>${conv.total_messages || 0}</td>
                                <td>${analytics && analytics.goal_achievement ? Math.round(analytics.goal_achievement) + '%' : 'N/A'}</td>
                                <td>
                                    <button class="btn btn-sm btn-outline-info" onclick="viewDetails(${conv.id})">
                                        <i class="fas fa-eye"></i> View
                                    </button>
                                    <button class="btn btn-sm btn-outline-warning" onclick="regenerateAnalytics(${conv.id})">
                                        <i class="fas fa-refresh"></i> Refresh
                                    </button>
                                </td>
                            </tr>
                        `;
                    }).join('');
                } else {
                    tbody.innerHTML = '<tr><td colspan="8" class="text-center">No conversations found</td></tr>';
                }
            } catch (error) {
                console.error('Error loading conversations:', error);
                document.getElementById('conversationsTableBody').innerHTML = 
                    '<tr><td colspan="8" class="text-center text-danger">Error loading conversations</td></tr>';
            }
        }
        
        function getStatusColor(status) {
            switch(status) {
                case 'active': return 'warning';
                case 'completed': return 'success';
                case 'paused': return 'secondary';
                case 'error': return 'danger';
                default: return 'light';
            }
        }
        
        async function viewDetails(conversationId) {
            try {
                const response = await fetch(`/api/analytics/conversations/${conversationId}`);
                const data = await response.json();
                
                if (data.status === 'success') {
                    const insights = data.insights;
                    let detailsHtml = '<div class="row">';
                    
                    // Display insights
                    if (insights.summary) {
                        detailsHtml += '<div class="col-12"><h6>Summary:</h6>';
                        Object.entries(insights.summary).forEach(([key, value]) => {
                            detailsHtml += `<p><strong>${key.replace('_', ' ')}:</strong> ${value}</p>`;
                        });
                        detailsHtml += '</div>';
                    }
                    
                    if (insights.recommendations && insights.recommendations.length > 0) {
                        detailsHtml += '<div class="col-12 mt-3"><h6>Recommendations:</h6><ul>';
                        insights.recommendations.forEach(rec => {
                            detailsHtml += `<li>${rec}</li>`;
                        });
                        detailsHtml += '</ul></div>';
                    }
                    
                    detailsHtml += '</div>';
                    
                    // Simple modal using alert for now (could be enhanced with Bootstrap modal)
                    alert('Conversation Details:\\n\\n' + JSON.stringify(insights, null, 2));
                }
            } catch (error) {
                console.error('Error loading conversation details:', error);
                alert('Error loading conversation details');
            }
        }
        
        async function regenerateAnalytics(conversationId) {
            if (!confirm('Regenerate analytics for this conversation?')) return;
            
            try {
                const response = await fetch(`/api/analytics/conversations/${conversationId}/regenerate`, {
                    method: 'POST'
                });
                const data = await response.json();
                
                if (data.status === 'success') {
                    alert('Analytics regenerated successfully');
                    loadConversations();
                } else {
                    alert('Error regenerating analytics: ' + data.message);
                }
            } catch (error) {
                console.error('Error regenerating analytics:', error);
                alert('Error regenerating analytics');
            }
        }
        
        // Load data on page load
        document.addEventListener('DOMContentLoaded', function() {
            loadSummary();
            loadConversations();
        });
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

def initialize_streaming(app):
    """Initialize streaming manager and WebSocket functionality"""
    global streaming_manager, socketio
    
    try:
        # Import streaming components
        from .utils.streaming import StreamingManager, StreamingConfig
        from .web.websocket import create_websocket_app
        
        # Create streaming manager with default configuration
        config = StreamingConfig(
            buffer_size=app.config.get('STREAMING_BUFFER_SIZE', 1000),
            max_tokens_per_second=app.config.get('STREAMING_RATE_LIMIT', 50),
            backpressure_threshold=app.config.get('STREAMING_BACKPRESSURE_THRESHOLD', 0.8),
            resume_threshold=app.config.get('STREAMING_BACKPRESSURE_RESUME', 0.3)
        )
        
        streaming_manager = StreamingManager(config)
        
        # Create WebSocket application
        socketio = create_websocket_app(app, streaming_manager)
        
        # Store references in app extensions
        app.extensions['streaming_manager'] = streaming_manager
        app.extensions['socketio'] = socketio
        
        app.logger.info("Streaming and WebSocket functionality initialized")
        
    except Exception as e:
        app.logger.error(f"Failed to initialize streaming functionality: {str(e)}")
        # Continue without streaming if initialization fails
        app.extensions['streaming_manager'] = None
        app.extensions['socketio'] = None


def register_websocket_routes(app):
    """Register WebSocket-related HTTP routes"""
    try:
        from .web.websocket import register_websocket_routes as register_ws_routes
        register_ws_routes(app)
    except Exception as e:
        app.logger.error(f"Failed to register WebSocket routes: {str(e)}")


def setup_alerting_system(app):
    """Setup and initialize the alerting system"""
    try:
        from .utils.alerting import setup_alerting
        
        # Get alerting configuration from app config or use defaults
        alerting_config = app.config.get('ALERTING_CONFIG', {
            'check_interval_seconds': 30,
            'max_history_size': 1000,
            'thresholds': {
                'cpu_usage': {
                    'threshold_value': 80.0,
                    'comparison': 'gt',
                    'level': 'warning',
                    'cooldown_minutes': 5,
                    'description': 'High CPU usage detected'
                },
                'memory_usage': {
                    'threshold_value': 85.0,
                    'comparison': 'gt',
                    'level': 'warning',
                    'cooldown_minutes': 5,
                    'description': 'High memory usage detected'
                },
                'error_rate': {
                    'threshold_value': 5.0,
                    'comparison': 'gt',
                    'level': 'error',
                    'cooldown_minutes': 3,
                    'description': 'High error rate detected'
                }
            },
            'notifications': {
                'console': {'enabled': True},
                'email': {'enabled': False},
                'webhook': {'enabled': False}
            }
        })
        
        # Initialize and start alerting
        alerting_engine = setup_alerting(alerting_config)
        
        # Store reference in app extensions for cleanup
        if not hasattr(app, 'extensions'):
            app.extensions = {}
        app.extensions['alerting_engine'] = alerting_engine
        
        app.logger.info("Alerting system initialized successfully")
        
    except Exception as e:
        app.logger.error(f"Failed to setup alerting system: {str(e)}")
        # Don't fail the entire app if alerting setup fails
        pass


if __name__ == '__main__':
    # Create logs directory if it doesn't exist
    os.makedirs('logs', exist_ok=True)
    
    # Create and run the app
    app = create_app()
    app.run(debug=True, host='0.0.0.0', port=5000) 