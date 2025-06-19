"""
Validation API Routes

REST API endpoints for the hierarchical validation system and plugin management.
"""

from flask import Blueprint, request, jsonify, current_app
from flask_cors import cross_origin
import asyncio
from typing import Dict, Any

from ..services.validation_service import ValidationService
from ..models.task import Task
from ..models.agent import Agent
from ..models.validation import ValidationRecord
from ..models.plugin import PluginRecord
from ..utils.auth import require_auth
from ..utils.validation import validate_json

validation_bp = Blueprint('validation', __name__, url_prefix='/api/validation')


def get_validation_service() -> ValidationService:
    """Get validation service instance"""
    if not hasattr(current_app, 'validation_service'):
        current_app.validation_service = ValidationService()
    return current_app.validation_service


@validation_bp.route('/validate/task/<int:task_id>', methods=['POST'])
@cross_origin()
@require_auth
@validate_json({
    'type': 'object',
    'properties': {
        'tool_agent_id': {'type': 'integer'},
        'dept_agent_id': {'type': 'integer'},
        'director_agent_id': {'type': 'integer'}
    },
    'required': ['tool_agent_id']
})
async def validate_task(task_id: int):
    """
    Validate a task through the hierarchical validation system
    
    POST /api/validation/validate/task/<task_id>
    {
        "tool_agent_id": 123,
        "dept_agent_id": 456,  // optional
        "director_agent_id": 789  // optional
    }
    """
    try:
        data = request.get_json()
        service = get_validation_service()
        
        result = await service.validate_task_hierarchically(
            task_id=task_id,
            tool_agent_id=data['tool_agent_id'],
            dept_agent_id=data.get('dept_agent_id'),
            director_agent_id=data.get('director_agent_id')
        )
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/history', methods=['GET'])
@cross_origin()
@require_auth
def get_validation_history():
    """
    Get validation history
    
    GET /api/validation/history?task_id=123&agent_id=456&limit=100
    """
    try:
        task_id = request.args.get('task_id', type=int)
        agent_id = request.args.get('agent_id', type=int)
        limit = request.args.get('limit', 100, type=int)
        
        service = get_validation_service()
        history = service.get_validation_history(task_id, agent_id, limit)
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/statistics', methods=['GET'])
@cross_origin()
@require_auth
def get_validation_statistics():
    """
    Get validation system statistics
    
    GET /api/validation/statistics
    """
    try:
        service = get_validation_service()
        stats = service.integrator.get_system_health()
        
        return jsonify({
            'success': True,
            'statistics': stats
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/plugins', methods=['GET'])
@cross_origin()
@require_auth
def list_plugins():
    """
    List available plugins
    
    GET /api/validation/plugins?status=installed&type=agent
    """
    try:
        status = request.args.get('status')
        plugin_type = request.args.get('type')
        
        query = PluginRecord.query
        
        if status:
            query = query.filter_by(status=status)
        if plugin_type:
            query = query.filter_by(plugin_type=plugin_type)
        
        plugins = query.all()
        
        return jsonify({
            'success': True,
            'plugins': [plugin.to_dict() for plugin in plugins],
            'count': len(plugins)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/plugins/<plugin_name>/install', methods=['POST'])
@cross_origin()
@require_auth
@validate_json({
    'type': 'object',
    'properties': {
        'force_reinstall': {'type': 'boolean'}
    }
})
async def install_plugin(plugin_name: str):
    """
    Install a plugin
    
    POST /api/validation/plugins/<plugin_name>/install
    {
        "force_reinstall": false
    }
    """
    try:
        data = request.get_json() or {}
        force_reinstall = data.get('force_reinstall', False)
        
        service = get_validation_service()
        result = await service.install_plugin(plugin_name, force_reinstall)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/plugins/status', methods=['GET'])
@cross_origin()
@require_auth
def get_plugin_status():
    """
    Get plugin system status
    
    GET /api/validation/plugins/status
    """
    try:
        service = get_validation_service()
        status = service.get_plugin_status()
        
        return jsonify({
            'success': True,
            'status': status
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/capabilities/gaps/<int:task_id>', methods=['GET'])
@cross_origin()
@require_auth
async def analyze_capability_gaps(task_id: int):
    """
    Analyze capability gaps for a task
    
    GET /api/validation/capabilities/gaps/<task_id>
    """
    try:
        service = get_validation_service()
        result = await service.analyze_capability_gaps(task_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/capabilities/gaps/<int:task_id>/resolve', methods=['POST'])
@cross_origin()
@require_auth
async def auto_resolve_gaps(task_id: int):
    """
    Automatically resolve capability gaps for a task
    
    POST /api/validation/capabilities/gaps/<task_id>/resolve
    """
    try:
        service = get_validation_service()
        result = await service.auto_resolve_gaps(task_id)
        
        return jsonify(result), 200 if result['success'] else 400
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/capabilities/gaps/summary', methods=['GET'])
@cross_origin()
@require_auth
def get_capability_gaps_summary():
    """
    Get summary of capability gaps across all tasks
    
    GET /api/validation/capabilities/gaps/summary
    """
    try:
        service = get_validation_service()
        result = service.get_capability_gaps_summary()
        
        return jsonify(result), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/quality-gates', methods=['GET'])
@cross_origin()
@require_auth
def list_quality_gates():
    """
    List all available quality gates
    
    GET /api/validation/quality-gates
    """
    try:
        service = get_validation_service()
        gates = service.integrator.quality_gate_manager.get_all_gates()
        
        return jsonify({
            'success': True,
            'quality_gates': gates,
            'count': len(gates)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/quality-gates', methods=['POST'])
@cross_origin()
@require_auth
@validate_json({
    'type': 'object',
    'properties': {
        'name': {'type': 'string'},
        'tier': {'type': 'string', 'enum': ['tool', 'department', 'director']},
        'description': {'type': 'string'},
        'config_data': {'type': 'object'}
    },
    'required': ['name', 'tier', 'config_data']
})
def create_quality_gate():
    """
    Create a new quality gate
    
    POST /api/validation/quality-gates
    {
        "name": "code_coverage_check",
        "tier": "department",
        "description": "Ensures minimum code coverage",
        "config_data": {"threshold": 80.0}
    }
    """
    try:
        data = request.get_json()
        service = get_validation_service()
        
        gate = service.integrator.quality_gate_manager.create_gate(
            name=data['name'],
            tier=data['tier'],
            description=data.get('description', ''),
            config_data=data['config_data']
        )
        
        return jsonify({
            'success': True,
            'message': 'Quality gate created successfully',
            'gate': gate
        }), 201
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/rollbacks', methods=['GET'])
@cross_origin()
@require_auth
def get_rollback_history():
    """
    Get rollback history
    
    GET /api/validation/rollbacks
    """
    try:
        service = get_validation_service()
        history = service.integrator.rollback_manager.get_history()
        
        return jsonify({
            'success': True,
            'history': history,
            'count': len(history)
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@validation_bp.route('/health', methods=['GET'])
@cross_origin()
def health_check():
    """
    Health check for the validation service
    
    GET /api/validation/health
    """
    return jsonify({
        'status': 'ok',
        'service': 'validation'
    })
