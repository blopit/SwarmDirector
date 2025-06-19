"""
Validation Service

Provides validation system functionality as a service within SwarmDirector.
Integrates with the existing service architecture.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

from ..validation_plugin_integration import ValidationPluginIntegrator
from ..models.validation import ValidationRecord, QualityGateConfig, RollbackRecord
from ..models.plugin import PluginRecord, PluginInstallation, CapabilityGap
from ..models.task import Task
from ..models.agent import Agent
from ..models.base import db

logger = logging.getLogger(__name__)


class ValidationService:
    """
    Service for managing validation operations and plugin functionality
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.integrator = ValidationPluginIntegrator(self.config)
        
    async def validate_task_hierarchically(self, task_id: int, 
                                           tool_agent_id: int,
                                           dept_agent_id: Optional[int] = None,
                                           director_agent_id: Optional[int] = None) -> Dict[str, Any]:
        """
        Validate a task through the hierarchical validation system
        """
        try:
            # Load task and agents from database using Session.get()
            task = db.session.get(Task, task_id)
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}
            
            tool_agent = db.session.get(Agent, tool_agent_id)
            if not tool_agent:
                return {'success': False, 'error': f'Tool agent {tool_agent_id} not found'}
            
            dept_agent = db.session.get(Agent, dept_agent_id) if dept_agent_id else None
            director_agent = db.session.get(Agent, director_agent_id) if director_agent_id else None
            
            # Process through validation chain
            result = await self.integrator.process_task_with_full_validation(
                task=task,
                tool_agent=tool_agent,
                dept_agent=dept_agent,
                director_agent=director_agent
            )
            
            # Store validation records in database
            await self._store_validation_results(result)
            
            # Update task with validation status
            task.validation_status = 'passed' if result['success'] else 'failed'
            task.validation_score = self._calculate_overall_score(result)
            task.validation_tier = self._get_highest_tier(result)
            db.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error in hierarchical validation: {e}", exc_info=True)
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    async def install_plugin(self, plugin_name: str, force_reinstall: bool = False) -> Dict[str, Any]:
        """Install a plugin through the plugin manager"""
        try:
            # Check if plugin exists in database
            plugin_record = PluginRecord.query.filter_by(name=plugin_name).first()
            if not plugin_record:
                return {'success': False, 'error': f'Plugin {plugin_name} not found in registry'}
            
            # Create installation record
            installation = PluginInstallation(
                plugin_record_id=plugin_record.id,
                installation_type='install',
                status='started'
            )
            db.session.add(installation)
            db.session.commit()
            
            try:
                # Install through plugin manager
                success = self.integrator.plugin_manager.install_plugin(plugin_name, force_reinstall)
                
                # Update installation record
                installation.status = 'completed' if success else 'failed'
                installation.completed_at = datetime.utcnow()
                
                if success:
                    # Update plugin record
                    plugin_record.status = 'installed'
                    plugin_record.installed_at = datetime.utcnow()
                
                db.session.commit()
                
                return {
                    'success': success,
                    'plugin_name': plugin_name,
                    'installation_id': installation.id
                }
                
            except Exception as e:
                installation.status = 'failed'
                installation.error_details = str(e)
                installation.completed_at = datetime.utcnow()
                db.session.commit()
                raise
                
        except Exception as e:
            logger.error(f"Error installing plugin {plugin_name}: {e}")
            return {'success': False, 'error': str(e)}
    
    async def analyze_capability_gaps(self, task_id: int) -> Dict[str, Any]:
        """Analyze capability gaps for a task"""
        try:
            task = db.session.get(Task, task_id)
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}
            
            # Get capability assessment
            assessment = self.integrator.capability_discovery.assess_task_capabilities(task)
            
            # Store capability gaps in database
            for gap in assessment.gaps:
                gap_record = CapabilityGap(
                    task_id=task_id,
                    capability_name=gap.name,
                    capability_type=gap.capability_type.value,
                    severity=gap.severity.value,
                    description=gap.description,
                    impact_score=gap.impact_score,
                    effort_to_resolve=gap.effort_to_resolve,
                    suggested_plugins=gap.suggested_plugins
                )
                db.session.add(gap_record)
            
            # Update task with capability gap information
            task.capability_gaps = [gap.to_dict() for gap in assessment.gaps]
            db.session.commit()
            
            return {
                'success': True,
                'assessment': {
                    'task_id': str(task_id),
                    'required_capabilities': assessment.required_capabilities,
                    'available_capabilities': assessment.available_capabilities,
                    'gaps_count': len(assessment.gaps),
                    'completeness_score': assessment.completeness_score,
                    'can_complete_task': assessment.can_complete_task,
                    'gaps': [gap.to_dict() for gap in assessment.gaps]
                }
            }
            
        except Exception as e:
            logger.error(f"Error analyzing capability gaps: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    async def auto_resolve_gaps(self, task_id: int) -> Dict[str, Any]:
        """Automatically resolve capability gaps for a task"""
        try:
            task = db.session.get(Task, task_id)
            if not task:
                return {'success': False, 'error': f'Task {task_id} not found'}
            
            # Auto-resolve through plugin manager
            result = await self.integrator.auto_resolve_capability_gaps(task)
            
            # Update resolved gaps in database
            if result['success'] and result.get('plugins_installed'):
                gaps = CapabilityGap.query.filter_by(task_id=task_id, resolved=False).all()
                for gap in gaps:
                    if any(plugin in gap.suggested_plugins for plugin in result['plugins_installed']):
                        gap.resolved = True
                        gap.resolved_at = datetime.utcnow()
                        gap.resolution_method = 'plugin_install'
                
                db.session.commit()
            
            return result
            
        except Exception as e:
            logger.error(f"Error auto-resolving gaps: {e}")
            db.session.rollback()
            return {'success': False, 'error': str(e)}
    
    def get_validation_history(self, task_id: Optional[int] = None, 
                               agent_id: Optional[int] = None,
                               limit: int = 100) -> List[Dict[str, Any]]:
        """Get validation history from database"""
        try:
            query = ValidationRecord.query
            
            if task_id:
                query = query.filter_by(task_id=task_id)
            if agent_id:
                query = query.filter_by(agent_id=agent_id)
            
            records = query.order_by(ValidationRecord.validation_timestamp.desc()).limit(limit).all()
            
            return [record.to_dict() for record in records]
            
        except Exception as e:
            logger.error(f"Error getting validation history: {e}")
            return []
    
    def get_plugin_status(self) -> Dict[str, Any]:
        """Get plugin system status"""
        try:
            plugins = PluginRecord.query.all()
            installations = PluginInstallation.query.order_by(PluginInstallation.started_at.desc()).limit(10).all()
            
            status = {
                'total_plugins': len(plugins),
                'installed_plugins': len([p for p in plugins if p.status.value == 'installed']),
                'available_plugins': len([p for p in plugins if p.status.value == 'available']),
                'recent_installations': [inst.to_dict() for inst in installations],
                'system_status': self.integrator.get_system_health()
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting plugin status: {e}")
            return {'error': str(e)}
    
    def get_capability_gaps_summary(self) -> Dict[str, Any]:
        """Get summary of capability gaps across all tasks"""
        try:
            gaps = CapabilityGap.query.all()
            
            # Group by capability name
            gap_summary = {}
            for gap in gaps:
                if gap.capability_name not in gap_summary:
                    gap_summary[gap.capability_name] = {
                        'count': 0,
                        'resolved': 0,
                        'severities': {},
                        'suggested_plugins': set()
                    }
                
                gap_summary[gap.capability_name]['count'] += 1
                if gap.resolved:
                    gap_summary[gap.capability_name]['resolved'] += 1
                
                if gap.severity not in gap_summary[gap.capability_name]['severities']:
                    gap_summary[gap.capability_name]['severities'][gap.severity] = 0
                gap_summary[gap.capability_name]['severities'][gap.severity] += 1
                
                if gap.suggested_plugins:
                    gap_summary[gap.capability_name]['suggested_plugins'].update(gap.suggested_plugins)
            
            # Convert sets to lists for JSON serialization
            for cap_name in gap_summary:
                gap_summary[cap_name]['suggested_plugins'] = list(gap_summary[cap_name]['suggested_plugins'])
            
            return {
                'total_gaps': len(gaps),
                'resolved_gaps': len([g for g in gaps if g.resolved]),
                'by_capability': gap_summary,
                'most_common_gaps': sorted(
                    gap_summary.items(), 
                    key=lambda x: x[1]['count'], 
                    reverse=True
                )[:10]
            }
            
        except Exception as e:
            logger.error(f"Error getting capability gaps summary: {e}")
            return {'error': str(e)}
    
    async def _store_validation_results(self, result: Dict[str, Any]):
        """Store validation results in database"""
        try:
            if 'validation_results' in result:
                for validation in result['validation_results']:
                    # Create validation record (simplified - would need more mapping)
                    record = ValidationRecord(
                        task_id=int(result['task_id']),
                        agent_id=1,  # Would need proper agent mapping
                        tier=validation['tier'],
                        status=validation['status'],
                        validator_name=f"{validation['tier']}_validator",
                        metrics={'overall_score': validation['score']},
                        validation_timestamp=datetime.utcnow()
                    )
                    db.session.add(record)
            
            db.session.commit()
            
        except Exception as e:
            logger.error(f"Error storing validation results: {e}")
    
    def _calculate_overall_score(self, result: Dict[str, Any]) -> float:
        """Calculate overall validation score"""
        if 'validation_results' not in result:
            return 0.0
        
        scores = [v['score'] for v in result['validation_results']]
        return sum(scores) / len(scores) if scores else 0.0
    
    def _get_highest_tier(self, result: Dict[str, Any]) -> str:
        """Get the highest validation tier reached"""
        if 'validation_results' not in result:
            return 'none'
        
        tiers = [v['tier'] for v in result['validation_results']]
        if 'director' in tiers:
            return 'director'
        elif 'department' in tiers:
            return 'department'
        elif 'tool' in tiers:
            return 'tool'
        else:
            return 'none'
