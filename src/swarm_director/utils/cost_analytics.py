"""
Cost analytics service for AI API usage analysis and reporting
Provides comprehensive cost analysis, trends, and insights
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import func, and_, desc
from decimal import Decimal

from ..models.base import db
from ..models.cost_tracking import APIUsage, CostBudget, APIProvider, UsageType
from ..models.agent import Agent
from ..models.task import Task

logger = logging.getLogger(__name__)


class CostAnalytics:
    """Main cost analytics service"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.CostAnalytics")
    
    def get_cost_summary(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        provider: Optional[APIProvider] = None,
        agent_id: Optional[int] = None
    ) -> Dict[str, Any]:
        """Get comprehensive cost summary for specified period"""
        try:
            # Default to last 30 days if no dates provided
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Build base query
            query = db.session.query(APIUsage).filter(
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            )
            
            # Apply filters
            if provider:
                query = query.filter(APIUsage.provider == provider)
            if agent_id:
                query = query.filter(APIUsage.agent_id == agent_id)
            
            # Get all usage records
            usage_records = query.all()
            
            if not usage_records:
                return self._empty_summary(start_date, end_date)
            
            # Calculate summary statistics
            total_cost = sum(float(record.total_cost) for record in usage_records)
            total_tokens = sum(record.total_tokens for record in usage_records)
            total_requests = len(usage_records)
            
            # Calculate averages
            avg_cost_per_request = total_cost / total_requests if total_requests > 0 else 0
            avg_tokens_per_request = total_tokens / total_requests if total_requests > 0 else 0
            avg_cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            
            # Get breakdown by provider
            provider_breakdown = self._get_provider_breakdown(usage_records)
            
            # Get breakdown by model
            model_breakdown = self._get_model_breakdown(usage_records)
            
            # Get breakdown by agent
            agent_breakdown = self._get_agent_breakdown(usage_records)
            
            # Get daily trend
            daily_trend = self._get_daily_trend(start_date, end_date, provider, agent_id)
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat(),
                    'days': (end_date - start_date).days
                },
                'summary': {
                    'total_cost': round(total_cost, 6),
                    'total_tokens': total_tokens,
                    'total_requests': total_requests,
                    'avg_cost_per_request': round(avg_cost_per_request, 6),
                    'avg_tokens_per_request': round(avg_tokens_per_request, 2),
                    'avg_cost_per_token': round(avg_cost_per_token, 8)
                },
                'breakdowns': {
                    'by_provider': provider_breakdown,
                    'by_model': model_breakdown,
                    'by_agent': agent_breakdown
                },
                'trends': {
                    'daily': daily_trend
                },
                'filters_applied': {
                    'provider': provider.value if provider else None,
                    'agent_id': agent_id
                }
            }
            
        except Exception as e:
            self.logger.error(f"Failed to generate cost summary: {e}")
            return self._empty_summary(start_date, end_date)
    
    def _empty_summary(self, start_date: datetime, end_date: datetime) -> Dict[str, Any]:
        """Return empty summary structure"""
        return {
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': (end_date - start_date).days
            },
            'summary': {
                'total_cost': 0.0,
                'total_tokens': 0,
                'total_requests': 0,
                'avg_cost_per_request': 0.0,
                'avg_tokens_per_request': 0.0,
                'avg_cost_per_token': 0.0
            },
            'breakdowns': {
                'by_provider': [],
                'by_model': [],
                'by_agent': []
            },
            'trends': {
                'daily': []
            },
            'filters_applied': {}
        }
    
    def _get_provider_breakdown(self, usage_records: List[APIUsage]) -> List[Dict[str, Any]]:
        """Get cost breakdown by provider"""
        provider_stats = {}
        
        for record in usage_records:
            provider = record.provider.value
            if provider not in provider_stats:
                provider_stats[provider] = {
                    'cost': 0.0,
                    'tokens': 0,
                    'requests': 0
                }
            
            provider_stats[provider]['cost'] += float(record.total_cost)
            provider_stats[provider]['tokens'] += record.total_tokens
            provider_stats[provider]['requests'] += 1
        
        # Convert to list and sort by cost
        breakdown = []
        for provider, stats in provider_stats.items():
            breakdown.append({
                'provider': provider,
                'total_cost': round(stats['cost'], 6),
                'total_tokens': stats['tokens'],
                'total_requests': stats['requests'],
                'avg_cost_per_request': round(stats['cost'] / stats['requests'], 6) if stats['requests'] > 0 else 0,
                'avg_cost_per_token': round(stats['cost'] / stats['tokens'], 8) if stats['tokens'] > 0 else 0
            })
        
        return sorted(breakdown, key=lambda x: x['total_cost'], reverse=True)
    
    def _get_model_breakdown(self, usage_records: List[APIUsage]) -> List[Dict[str, Any]]:
        """Get cost breakdown by model"""
        model_stats = {}
        
        for record in usage_records:
            key = f"{record.provider.value}/{record.model}"
            if key not in model_stats:
                model_stats[key] = {
                    'provider': record.provider.value,
                    'model': record.model,
                    'cost': 0.0,
                    'tokens': 0,
                    'requests': 0
                }
            
            model_stats[key]['cost'] += float(record.total_cost)
            model_stats[key]['tokens'] += record.total_tokens
            model_stats[key]['requests'] += 1
        
        # Convert to list and sort by cost
        breakdown = []
        for stats in model_stats.values():
            breakdown.append({
                'provider': stats['provider'],
                'model': stats['model'],
                'total_cost': round(stats['cost'], 6),
                'total_tokens': stats['tokens'],
                'total_requests': stats['requests'],
                'avg_cost_per_request': round(stats['cost'] / stats['requests'], 6) if stats['requests'] > 0 else 0,
                'avg_cost_per_token': round(stats['cost'] / stats['tokens'], 8) if stats['tokens'] > 0 else 0
            })
        
        return sorted(breakdown, key=lambda x: x['total_cost'], reverse=True)
    
    def _get_agent_breakdown(self, usage_records: List[APIUsage]) -> List[Dict[str, Any]]:
        """Get cost breakdown by agent"""
        agent_stats = {}
        
        for record in usage_records:
            agent_id = record.agent_id or 'unknown'
            if agent_id not in agent_stats:
                agent_stats[agent_id] = {
                    'agent_id': agent_id,
                    'agent_name': None,
                    'cost': 0.0,
                    'tokens': 0,
                    'requests': 0
                }
            
            agent_stats[agent_id]['cost'] += float(record.total_cost)
            agent_stats[agent_id]['tokens'] += record.total_tokens
            agent_stats[agent_id]['requests'] += 1
        
        # Get agent names
        agent_ids = [aid for aid in agent_stats.keys() if aid != 'unknown' and aid is not None]
        if agent_ids:
            agents = db.session.query(Agent).filter(Agent.id.in_(agent_ids)).all()
            agent_names = {agent.id: agent.name for agent in agents}
            
            for agent_id, stats in agent_stats.items():
                if agent_id in agent_names:
                    stats['agent_name'] = agent_names[agent_id]
        
        # Convert to list and sort by cost
        breakdown = []
        for stats in agent_stats.values():
            breakdown.append({
                'agent_id': stats['agent_id'],
                'agent_name': stats['agent_name'] or 'Unknown',
                'total_cost': round(stats['cost'], 6),
                'total_tokens': stats['tokens'],
                'total_requests': stats['requests'],
                'avg_cost_per_request': round(stats['cost'] / stats['requests'], 6) if stats['requests'] > 0 else 0,
                'avg_cost_per_token': round(stats['cost'] / stats['tokens'], 8) if stats['tokens'] > 0 else 0
            })
        
        return sorted(breakdown, key=lambda x: x['total_cost'], reverse=True)
    
    def _get_daily_trend(
        self,
        start_date: datetime,
        end_date: datetime,
        provider: Optional[APIProvider] = None,
        agent_id: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get daily cost trend"""
        try:
            # Build query for daily aggregation
            query = db.session.query(
                func.date(APIUsage.created_at).label('date'),
                func.sum(APIUsage.total_cost).label('daily_cost'),
                func.sum(APIUsage.total_tokens).label('daily_tokens'),
                func.count(APIUsage.id).label('daily_requests')
            ).filter(
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            )
            
            # Apply filters
            if provider:
                query = query.filter(APIUsage.provider == provider)
            if agent_id:
                query = query.filter(APIUsage.agent_id == agent_id)
            
            # Group by date and order
            daily_data = query.group_by(func.date(APIUsage.created_at)).order_by('date').all()
            
            # Convert to list of dictionaries
            trend = []
            for day in daily_data:
                trend.append({
                    'date': day.date.isoformat(),
                    'cost': round(float(day.daily_cost), 6),
                    'tokens': int(day.daily_tokens),
                    'requests': int(day.daily_requests),
                    'avg_cost_per_request': round(float(day.daily_cost) / int(day.daily_requests), 6) if day.daily_requests > 0 else 0
                })
            
            return trend
            
        except Exception as e:
            self.logger.error(f"Failed to get daily trend: {e}")
            return []
    
    def get_top_cost_drivers(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """Get top cost drivers (models, agents, tasks)"""
        try:
            # Default to last 30 days
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Top models by cost
            top_models = db.session.query(
                APIUsage.provider,
                APIUsage.model,
                func.sum(APIUsage.total_cost).label('total_cost'),
                func.count(APIUsage.id).label('request_count')
            ).filter(
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            ).group_by(
                APIUsage.provider, APIUsage.model
            ).order_by(
                desc('total_cost')
            ).limit(limit).all()
            
            # Top agents by cost
            top_agents = db.session.query(
                APIUsage.agent_id,
                func.sum(APIUsage.total_cost).label('total_cost'),
                func.count(APIUsage.id).label('request_count')
            ).filter(
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date,
                APIUsage.agent_id.isnot(None)
            ).group_by(
                APIUsage.agent_id
            ).order_by(
                desc('total_cost')
            ).limit(limit).all()
            
            # Get agent names
            agent_ids = [agent.agent_id for agent in top_agents]
            agent_names = {}
            if agent_ids:
                agents = db.session.query(Agent).filter(Agent.id.in_(agent_ids)).all()
                agent_names = {agent.id: agent.name for agent in agents}
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'top_models': [
                    {
                        'provider': model.provider.value,
                        'model': model.model,
                        'total_cost': round(float(model.total_cost), 6),
                        'request_count': model.request_count
                    }
                    for model in top_models
                ],
                'top_agents': [
                    {
                        'agent_id': agent.agent_id,
                        'agent_name': agent_names.get(agent.agent_id, 'Unknown'),
                        'total_cost': round(float(agent.total_cost), 6),
                        'request_count': agent.request_count
                    }
                    for agent in top_agents
                ]
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get top cost drivers: {e}")
            return {'top_models': [], 'top_agents': []}
    
    def get_cost_efficiency_metrics(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> Dict[str, Any]:
        """Get cost efficiency metrics and insights"""
        try:
            # Default to last 30 days
            if not end_date:
                end_date = datetime.utcnow()
            if not start_date:
                start_date = end_date - timedelta(days=30)
            
            # Get usage data
            usage_records = db.session.query(APIUsage).filter(
                APIUsage.created_at >= start_date,
                APIUsage.created_at <= end_date
            ).all()
            
            if not usage_records:
                return {'message': 'No usage data available for the specified period'}
            
            # Calculate efficiency metrics
            total_cost = sum(float(record.total_cost) for record in usage_records)
            successful_requests = len([r for r in usage_records if r.response_status == 'success'])
            failed_requests = len([r for r in usage_records if r.response_status == 'error'])
            
            success_rate = (successful_requests / len(usage_records)) * 100 if usage_records else 0
            
            # Cost per successful request
            cost_per_success = total_cost / successful_requests if successful_requests > 0 else 0
            
            # Average response time
            response_times = [r.request_duration_ms for r in usage_records if r.request_duration_ms]
            avg_response_time = sum(response_times) / len(response_times) if response_times else 0
            
            # Token efficiency (cost per token)
            total_tokens = sum(record.total_tokens for record in usage_records)
            cost_per_token = total_cost / total_tokens if total_tokens > 0 else 0
            
            return {
                'period': {
                    'start_date': start_date.isoformat(),
                    'end_date': end_date.isoformat()
                },
                'efficiency_metrics': {
                    'success_rate_percent': round(success_rate, 2),
                    'cost_per_successful_request': round(cost_per_success, 6),
                    'cost_per_token': round(cost_per_token, 8),
                    'avg_response_time_ms': round(avg_response_time, 2),
                    'total_requests': len(usage_records),
                    'successful_requests': successful_requests,
                    'failed_requests': failed_requests
                },
                'recommendations': self._generate_efficiency_recommendations(usage_records)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to get efficiency metrics: {e}")
            return {'error': str(e)}
    
    def _generate_efficiency_recommendations(self, usage_records: List[APIUsage]) -> List[str]:
        """Generate cost efficiency recommendations"""
        recommendations = []
        
        try:
            # Analyze model usage patterns
            model_costs = {}
            for record in usage_records:
                key = f"{record.provider.value}/{record.model}"
                if key not in model_costs:
                    model_costs[key] = {'cost': 0.0, 'requests': 0}
                model_costs[key]['cost'] += float(record.total_cost)
                model_costs[key]['requests'] += 1
            
            # Find expensive models with low usage
            for model, stats in model_costs.items():
                avg_cost = stats['cost'] / stats['requests']
                if avg_cost > 0.01 and stats['requests'] < 10:  # Expensive but rarely used
                    recommendations.append(
                        f"Consider using a more cost-effective alternative to {model} "
                        f"(avg cost: ${avg_cost:.4f} per request, only {stats['requests']} requests)"
                    )
            
            # Check error rates
            error_rate = len([r for r in usage_records if r.response_status == 'error']) / len(usage_records) * 100
            if error_rate > 5:
                recommendations.append(
                    f"High error rate ({error_rate:.1f}%) detected. "
                    "Review API call patterns and error handling to reduce wasted costs."
                )
            
            # Check for potential batch optimization
            total_requests = len(usage_records)
            if total_requests > 100:
                recommendations.append(
                    "Consider batching API requests where possible to reduce per-request overhead costs."
                )
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Failed to generate recommendations: {e}")
            return ["Unable to generate recommendations due to analysis error."]


# Global cost analytics instance
cost_analytics = CostAnalytics()
