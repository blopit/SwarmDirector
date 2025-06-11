"""
CRUD Routes for SwarmDirector
Comprehensive REST API endpoints for all models
"""

from flask import jsonify, request
from models import Agent, Task, Conversation
from models.conversation import Message
from models.agent import AgentType, AgentStatus
from models.task import TaskStatus, TaskPriority
from models.conversation import ConversationStatus, MessageType
from datetime import datetime
import uuid

def register_crud_routes(app):
    """Register all CRUD routes with the Flask app"""
    
    # ============================================================================
    # AGENTS CRUD ENDPOINTS
    # ============================================================================
    
    @app.route('/api/agents', methods=['GET'])
    def get_agents():
        """Get all agents with optional filtering"""
        try:
            # Get query parameters
            agent_type = request.args.get('type')
            status = request.args.get('status')
            parent_id = request.args.get('parent_id')
            
            # Build query
            query = Agent.query
            
            if agent_type:
                query = query.filter(Agent.agent_type == getattr(AgentType, agent_type.upper(), None))
            
            if status:
                query = query.filter(Agent.status == getattr(AgentStatus, status.upper(), None))
                
            if parent_id:
                query = query.filter(Agent.parent_id == parent_id)
            
            agents = query.all()
            
            return jsonify({
                'status': 'success',
                'agents': [agent.to_dict() for agent in agents],
                'count': len(agents)
            })
            
        except Exception as e:
            app.logger.error(f'Error fetching agents: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/agents/<int:agent_id>', methods=['GET'])
    def get_agent(agent_id):
        """Get a specific agent by ID"""
        try:
            agent = Agent.query.get_or_404(agent_id)
            return jsonify({
                'status': 'success',
                'agent': agent.to_dict()
            })
        except Exception as e:
            app.logger.error(f'Error fetching agent {agent_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/agents', methods=['POST'])
    def create_agent():
        """Create a new agent"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('name'):
                return jsonify({'status': 'error', 'error': 'Agent name is required'}), 400
            
            if not data.get('agent_type'):
                return jsonify({'status': 'error', 'error': 'Agent type is required'}), 400
            
            # Create new agent
            agent = Agent(
                name=data['name'],
                description=data.get('description', ''),
                agent_type=getattr(AgentType, data['agent_type'].upper()),
                status=getattr(AgentStatus, data.get('status', 'IDLE').upper()),
                parent_id=data.get('parent_id'),
                capabilities=data.get('capabilities', {}),
                config=data.get('config', {}),
                autogen_config=data.get('autogen_config', {}),
                system_message=data.get('system_message', '')
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
    
    @app.route('/api/agents/<int:agent_id>', methods=['PUT'])
    def update_agent(agent_id):
        """Update an existing agent"""
        try:
            agent = Agent.query.get_or_404(agent_id)
            data = request.get_json()
            
            # Update fields
            if 'name' in data:
                agent.name = data['name']
            if 'description' in data:
                agent.description = data['description']
            if 'agent_type' in data:
                agent.agent_type = getattr(AgentType, data['agent_type'].upper())
            if 'status' in data:
                agent.status = getattr(AgentStatus, data['status'].upper())
            if 'parent_id' in data:
                agent.parent_id = data['parent_id']
            if 'capabilities' in data:
                agent.capabilities = data['capabilities']
            if 'config' in data:
                agent.config = data['config']
            if 'autogen_config' in data:
                agent.autogen_config = data['autogen_config']
            if 'system_message' in data:
                agent.system_message = data['system_message']
            
            agent.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Agent updated successfully',
                'agent': agent.to_dict()
            })
            
        except Exception as e:
            app.logger.error(f'Error updating agent {agent_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/agents/<int:agent_id>', methods=['DELETE'])
    def delete_agent(agent_id):
        """Delete an agent"""
        try:
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
    # TASKS CRUD ENDPOINTS
    # ============================================================================
    
    @app.route('/api/tasks', methods=['GET'])
    def get_tasks():
        """Get all tasks with optional filtering"""
        try:
            # Get query parameters
            status = request.args.get('status')
            priority = request.args.get('priority')
            assigned_agent_id = request.args.get('assigned_agent_id')
            parent_task_id = request.args.get('parent_task_id')
            
            # Build query
            query = Task.query
            
            if status:
                query = query.filter(Task.status == getattr(TaskStatus, status.upper(), None))
            
            if priority:
                query = query.filter(Task.priority == getattr(TaskPriority, priority.upper(), None))
                
            if assigned_agent_id:
                query = query.filter(Task.assigned_agent_id == assigned_agent_id)
                
            if parent_task_id:
                query = query.filter(Task.parent_task_id == parent_task_id)
            
            tasks = query.all()
            
            return jsonify({
                'status': 'success',
                'tasks': [task.to_dict() for task in tasks],
                'count': len(tasks)
            })
            
        except Exception as e:
            app.logger.error(f'Error fetching tasks: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/tasks/<int:task_id>', methods=['GET'])
    def get_task(task_id):
        """Get a specific task by ID"""
        try:
            task = Task.query.get_or_404(task_id)
            return jsonify({
                'status': 'success',
                'task': task.to_dict()
            })
        except Exception as e:
            app.logger.error(f'Error fetching task {task_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/tasks', methods=['POST'])
    def create_task():
        """Create a new task"""
        try:
            data = request.get_json()
            
            # Validate required fields
            if not data.get('title'):
                return jsonify({'status': 'error', 'error': 'Task title is required'}), 400
            
            # Create new task
            task = Task(
                title=data['title'],
                description=data.get('description', ''),
                status=getattr(TaskStatus, data.get('status', 'PENDING').upper()),
                priority=getattr(TaskPriority, data.get('priority', 'MEDIUM').upper()),
                assigned_agent_id=data.get('assigned_agent_id'),
                parent_task_id=data.get('parent_task_id'),
                estimated_duration=data.get('estimated_duration'),
                deadline=datetime.fromisoformat(data['deadline']) if data.get('deadline') else None,
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
    
    @app.route('/api/tasks/<int:task_id>', methods=['PUT'])
    def update_task(task_id):
        """Update an existing task"""
        try:
            task = Task.query.get_or_404(task_id)
            data = request.get_json()
            
            # Update fields
            if 'title' in data:
                task.title = data['title']
            if 'description' in data:
                task.description = data['description']
            if 'status' in data:
                task.status = getattr(TaskStatus, data['status'].upper())
            if 'priority' in data:
                task.priority = getattr(TaskPriority, data['priority'].upper())
            if 'assigned_agent_id' in data:
                task.assigned_agent_id = data['assigned_agent_id']
            if 'parent_task_id' in data:
                task.parent_task_id = data['parent_task_id']
            if 'estimated_duration' in data:
                task.estimated_duration = data['estimated_duration']
            if 'actual_duration' in data:
                task.actual_duration = data['actual_duration']
            if 'deadline' in data:
                task.deadline = datetime.fromisoformat(data['deadline']) if data['deadline'] else None
            if 'input_data' in data:
                task.input_data = data['input_data']
            if 'output_data' in data:
                task.output_data = data['output_data']
            if 'error_details' in data:
                task.error_details = data['error_details']
            if 'progress_percentage' in data:
                task.progress_percentage = data['progress_percentage']
            
            task.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Task updated successfully',
                'task': task.to_dict()
            })
            
        except Exception as e:
            app.logger.error(f'Error updating task {task_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/tasks/<int:task_id>', methods=['DELETE'])
    def delete_task(task_id):
        """Delete a task"""
        try:
            task = Task.query.get_or_404(task_id)
            task.delete()
            
            return jsonify({
                'status': 'success',
                'message': 'Task deleted successfully'
            })
            
        except Exception as e:
            app.logger.error(f'Error deleting task {task_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # CONVERSATIONS CRUD ENDPOINTS
    # ============================================================================
    
    @app.route('/api/conversations', methods=['GET'])
    def get_conversations():
        """Get all conversations with optional filtering"""
        try:
            # Get query parameters
            status = request.args.get('status')
            initiator_agent_id = request.args.get('initiator_agent_id')
            conversation_type = request.args.get('type')
            
            # Build query
            query = Conversation.query
            
            if status:
                query = query.filter(Conversation.status == getattr(ConversationStatus, status.upper(), None))
            
            if initiator_agent_id:
                query = query.filter(Conversation.initiator_agent_id == initiator_agent_id)
                
            if conversation_type:
                query = query.filter(Conversation.conversation_type == conversation_type)
            
            conversations = query.all()
            
            return jsonify({
                'status': 'success',
                'conversations': [conv.to_dict() for conv in conversations],
                'count': len(conversations)
            })
            
        except Exception as e:
            app.logger.error(f'Error fetching conversations: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/conversations/<int:conversation_id>', methods=['GET'])
    def get_conversation(conversation_id):
        """Get a specific conversation by ID"""
        try:
            conversation = Conversation.query.get_or_404(conversation_id)
            return jsonify({
                'status': 'success',
                'conversation': conversation.to_dict()
            })
        except Exception as e:
            app.logger.error(f'Error fetching conversation {conversation_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}'), 500
    
    @app.route('/api/conversations', methods=['POST'])
    def create_conversation():
        """Create a new conversation"""
        try:
            data = request.get_json()
            
            # Create new conversation
            conversation = Conversation(
                title=data.get('title', ''),
                description=data.get('description', ''),
                status=getattr(ConversationStatus, data.get('status', 'ACTIVE').upper()),
                initiator_agent_id=data.get('initiator_agent_id'),
                session_id=data.get('session_id', str(uuid.uuid4())),
                user_id=data.get('user_id'),
                conversation_type=data.get('conversation_type', 'general'),
                autogen_chat_history=data.get('autogen_chat_history', []),
                group_chat_config=data.get('group_chat_config', {})
            )
            
            conversation.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Conversation created successfully',
                'conversation': conversation.to_dict()
            }), 201
            
        except Exception as e:
            app.logger.error(f'Error creating conversation: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/conversations/<int:conversation_id>', methods=['PUT'])
    def update_conversation(conversation_id):
        """Update an existing conversation"""
        try:
            conversation = Conversation.query.get_or_404(conversation_id)
            data = request.get_json()
            
            # Update fields
            if 'title' in data:
                conversation.title = data['title']
            if 'description' in data:
                conversation.description = data['description']
            if 'status' in data:
                conversation.status = getattr(ConversationStatus, data['status'].upper())
            if 'conversation_type' in data:
                conversation.conversation_type = data['conversation_type']
            if 'autogen_chat_history' in data:
                conversation.autogen_chat_history = data['autogen_chat_history']
            if 'group_chat_config' in data:
                conversation.group_chat_config = data['group_chat_config']
            
            conversation.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Conversation updated successfully',
                'conversation': conversation.to_dict()
            })
            
        except Exception as e:
            app.logger.error(f'Error updating conversation {conversation_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/conversations/<int:conversation_id>', methods=['DELETE'])
    def delete_conversation(conversation_id):
        """Delete a conversation"""
        try:
            conversation = Conversation.query.get_or_404(conversation_id)
            conversation.delete()
            
            return jsonify({
                'status': 'success',
                'message': 'Conversation deleted successfully'
            })
            
        except Exception as e:
            app.logger.error(f'Error deleting conversation {conversation_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # MESSAGES CRUD ENDPOINTS
    # ============================================================================
    
    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['GET'])
    def get_messages(conversation_id):
        """Get all messages for a conversation"""
        try:
            # Verify conversation exists
            conversation = Conversation.query.get_or_404(conversation_id)
            
            # Get query parameters
            message_type = request.args.get('type')
            sender_agent_id = request.args.get('sender_agent_id')
            limit = request.args.get('limit', type=int)
            
            # Build query
            query = Message.query.filter_by(conversation_id=conversation_id)
            
            if message_type:
                query = query.filter(Message.message_type == getattr(MessageType, message_type.upper(), None))
            
            if sender_agent_id:
                query = query.filter(Message.sender_agent_id == sender_agent_id)
            
            # Order by creation time
            query = query.order_by(Message.created_at.desc())
            
            if limit:
                query = query.limit(limit)
            
            messages = query.all()
            
            return jsonify({
                'status': 'success',
                'messages': [msg.to_dict() for msg in messages],
                'count': len(messages)
            })
            
        except Exception as e:
            app.logger.error(f'Error fetching messages for conversation {conversation_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/messages/<int:message_id>', methods=['GET'])
    def get_message(message_id):
        """Get a specific message by ID"""
        try:
            message = Message.query.get_or_404(message_id)
            return jsonify({
                'status': 'success',
                'message': message.to_dict()
            })
        except Exception as e:
            app.logger.error(f'Error fetching message {message_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/conversations/<int:conversation_id>/messages', methods=['POST'])
    def create_message(conversation_id):
        """Create a new message in a conversation"""
        try:
            # Verify conversation exists
            conversation = Conversation.query.get_or_404(conversation_id)
            
            data = request.get_json()
            
            # Validate required fields
            if not data.get('content'):
                return jsonify({'status': 'error', 'error': 'Message content is required'}), 400
            
            if not data.get('message_type'):
                return jsonify({'status': 'error', 'error': 'Message type is required'}), 400
            
            # Create new message
            message = Message(
                content=data['content'],
                message_type=getattr(MessageType, data['message_type'].upper()),
                conversation_id=conversation_id,
                sender_agent_id=data.get('sender_agent_id'),
                message_metadata=data.get('message_metadata', {}),
                tokens_used=data.get('tokens_used'),
                response_time=data.get('response_time')
            )
            
            message.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Message created successfully',
                'data': message.to_dict()
            }), 201
            
        except Exception as e:
            app.logger.error(f'Error creating message in conversation {conversation_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/messages/<int:message_id>', methods=['PUT'])
    def update_message(message_id):
        """Update an existing message"""
        try:
            message = Message.query.get_or_404(message_id)
            data = request.get_json()
            
            # Update fields
            if 'content' in data:
                message.content = data['content']
            if 'message_type' in data:
                message.message_type = getattr(MessageType, data['message_type'].upper())
            if 'message_metadata' in data:
                message.message_metadata = data['message_metadata']
            if 'tokens_used' in data:
                message.tokens_used = data['tokens_used']
            if 'response_time' in data:
                message.response_time = data['response_time']
            
            message.save()
            
            return jsonify({
                'status': 'success',
                'message': 'Message updated successfully',
                'data': message.to_dict()
            })
            
        except Exception as e:
            app.logger.error(f'Error updating message {message_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500
    
    @app.route('/api/messages/<int:message_id>', methods=['DELETE'])
    def delete_message(message_id):
        """Delete a message"""
        try:
            message = Message.query.get_or_404(message_id)
            message.delete()
            
            return jsonify({
                'status': 'success',
                'message': 'Message deleted successfully'
            })
            
        except Exception as e:
            app.logger.error(f'Error deleting message {message_id}: {str(e)}')
            return jsonify({'status': 'error', 'error': str(e)}), 500

    # ============================================================================
    # WEB UI ROUTES (HTML TEMPLATES)
    # ============================================================================
    
    @app.route('/dashboard')
    def dashboard():
        """Main dashboard page"""
        return '''
        <!DOCTYPE html>
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
                        <a class="nav-link" href="/dashboard/conversations">Conversations</a>
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
                    <div class="col-md-3">
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
                    
                    <div class="col-md-3">
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
                    
                    <div class="col-md-3">
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
                            <div class="card-footer">
                                <a href="/dashboard/conversations" class="text-white">View all conversations</a>
                            </div>
                        </div>
                    </div>
                    
                    <div class="col-md-3">
                        <div class="card text-white bg-warning">
                            <div class="card-body">
                                <div class="d-flex justify-content-between">
                                    <div>
                                        <h4 class="card-title">System</h4>
                                        <p class="card-text" id="system-status">Healthy</p>
                                    </div>
                                    <div class="align-self-center">
                                        <i class="fas fa-heart fa-2x"></i>
                                    </div>
                                </div>
                            </div>
                            <div class="card-footer">
                                <a href="/health" class="text-white">System health</a>
                            </div>
                        </div>
                    </div>
                </div>
                
                <div class="row mt-4">
                    <div class="col-12">
                        <div class="card">
                            <div class="card-header">
                                <h5><i class="fas fa-chart-line"></i> Recent Activity</h5>
                            </div>
                            <div class="card-body">
                                <div id="recent-activity">
                                    <p class="text-muted">Loading recent activity...</p>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
                // Load dashboard data
                async function loadDashboardData() {
                    try {
                        // Load agent count
                        const agentResponse = await fetch('/api/agents');
                        const agentData = await agentResponse.json();
                        document.getElementById('agent-count').textContent = agentData.count || 0;
                        
                        // Load task count
                        const taskResponse = await fetch('/api/tasks');
                        const taskData = await taskResponse.json();
                        document.getElementById('task-count').textContent = taskData.count || 0;
                        
                        // Load conversation count
                        const convResponse = await fetch('/api/conversations');
                        const convData = await convResponse.json();
                        document.getElementById('conversation-count').textContent = convData.count || 0;
                        
                        // Update recent activity
                        document.getElementById('recent-activity').innerHTML = 
                            '<p><i class="fas fa-check text-success"></i> Dashboard loaded successfully</p>' +
                            '<p><i class="fas fa-database text-info"></i> Database connections healthy</p>' +
                            '<p><i class="fas fa-cogs text-primary"></i> All systems operational</p>';
                        
                    } catch (error) {
                        console.error('Error loading dashboard data:', error);
                        document.getElementById('recent-activity').innerHTML = 
                            '<p class="text-danger"><i class="fas fa-exclamation-triangle"></i> Error loading data</p>';
                    }
                }
                
                // Load data when page loads
                document.addEventListener('DOMContentLoaded', loadDashboardData);
            </script>
        </body>
        </html>
        '''
    
    @app.route('/dashboard/agents')
    def agents_page():
        """Agents management page"""
        return '''
        <!DOCTYPE html>
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
                        <a class="nav-link" href="/dashboard/conversations">Conversations</a>
                    </div>
                </div>
            </nav>
            
            <div class="container mt-4">
                <div class="row">
                    <div class="col-12">
                        <div class="d-flex justify-content-between align-items-center">
                            <h1><i class="fas fa-robot"></i> Agent Management</h1>
                            <button class="btn btn-primary" data-bs-toggle="modal" data-bs-target="#addAgentModal">
                                <i class="fas fa-plus"></i> Add Agent
                            </button>
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
                                    <table class="table table-striped" id="agentsTable">
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
            
            <!-- Add Agent Modal -->
            <div class="modal fade" id="addAgentModal" tabindex="-1">
                <div class="modal-dialog">
                    <div class="modal-content">
                        <div class="modal-header">
                            <h5 class="modal-title">Add New Agent</h5>
                            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
                        </div>
                        <div class="modal-body">
                            <form id="addAgentForm">
                                <div class="mb-3">
                                    <label for="agentName" class="form-label">Name *</label>
                                    <input type="text" class="form-control" id="agentName" required>
                                </div>
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
                                <div class="mb-3">
                                    <label for="agentStatus" class="form-label">Status</label>
                                    <select class="form-select" id="agentStatus">
                                        <option value="idle">Idle</option>
                                        <option value="active">Active</option>
                                        <option value="busy">Busy</option>
                                        <option value="offline">Offline</option>
                                    </select>
                                </div>
                                <div class="mb-3">
                                    <label for="agentDescription" class="form-label">Description</label>
                                    <textarea class="form-control" id="agentDescription" rows="3"></textarea>
                                </div>
                            </form>
                        </div>
                        <div class="modal-footer">
                            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancel</button>
                            <button type="button" class="btn btn-primary" onclick="createAgent()">Create Agent</button>
                        </div>
                    </div>
                </div>
            </div>
            
            <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
            <script>
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
                                    <td><span class="badge bg-${getStatusColor(agent.status)}">${agent.status}</span></td>
                                    <td>${agent.description || 'No description'}</td>
                                    <td>
                                        <button class="btn btn-sm btn-outline-primary" onclick="viewAgent(${agent.id})">
                                            <i class="fas fa-eye"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-warning" onclick="editAgent(${agent.id})">
                                            <i class="fas fa-edit"></i>
                                        </button>
                                        <button class="btn btn-sm btn-outline-danger" onclick="deleteAgent(${agent.id})">
                                            <i class="fas fa-trash"></i>
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
                
                function getStatusColor(status) {
                    switch(status) {
                        case 'active': return 'success';
                        case 'busy': return 'warning';
                        case 'offline': return 'secondary';
                        case 'error': return 'danger';
                        default: return 'light';
                    }
                }
                
                async function createAgent() {
                    const name = document.getElementById('agentName').value;
                    const type = document.getElementById('agentType').value;
                    const status = document.getElementById('agentStatus').value;
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
                                status: status,
                                description: description
                            })
                        });
                        
                        const data = await response.json();
                        
                        if (data.status === 'success') {
                            // Close modal and refresh table
                            const modal = bootstrap.Modal.getInstance(document.getElementById('addAgentModal'));
                            modal.hide();
                            document.getElementById('addAgentForm').reset();
                            loadAgents();
                        } else {
                            alert('Error creating agent: ' + data.error);
                        }
                    } catch (error) {
                        console.error('Error creating agent:', error);
                        alert('Error creating agent');
                    }
                }
                
                function viewAgent(id) {
                    window.open(`/api/agents/${id}`, '_blank');
                }
                
                function editAgent(id) {
                    alert('Edit functionality not implemented yet');
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
                
                // Load agents when page loads
                document.addEventListener('DOMContentLoaded', loadAgents);
            </script>
        </body>
        </html>
        ''' 