"""
Cost tracking and budget management API routes
"""

from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
import logging
from sqlalchemy import desc, func
from sqlalchemy.exc import IntegrityError

from ..models.base import db
from ..models.cost_tracking import APIUsage, CostBudget, CostAlert, APIProvider, BudgetPeriod, AlertSeverity
from ..utils.response_formatter import ResponseFormatter
from ..utils.validation import validate_json_data
from ..utils.rate_limiter import api_rate_limit, user_rate_limit
from ..utils.cost_calculator import cost_calculator
from ..utils.cost_analytics import cost_analytics
from ..utils.budget_manager import budget_manager

logger = logging.getLogger(__name__)

# Create blueprint for cost tracking routes
cost_bp = Blueprint('cost', __name__, url_prefix='/api/cost')


@cost_bp.route('/usage', methods=['GET'])
@api_rate_limit
def get_api_usage():
    """Get API usage records with filtering and pagination"""
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        
        # Filters
        provider = request.args.get('provider')
        model = request.args.get('model')
        agent_id = request.args.get('agent_id', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Build query
        query = db.session.query(APIUsage)
        
        # Apply filters
        if provider:
            try:
                provider_enum = APIProvider(provider.lower())
                query = query.filter(APIUsage.provider == provider_enum)
            except ValueError:
                return ResponseFormatter.error(f"Invalid provider: {provider}", status_code=400)
        
        if model:
            query = query.filter(APIUsage.model == model)
        
        if agent_id:
            query = query.filter(APIUsage.agent_id == agent_id)
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                query = query.filter(APIUsage.created_at >= start_dt)
            except ValueError:
                return ResponseFormatter.error("Invalid start_date format. Use ISO format.", status_code=400)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
                query = query.filter(APIUsage.created_at <= end_dt)
            except ValueError:
                return ResponseFormatter.error("Invalid end_date format. Use ISO format.", status_code=400)
        
        # Order by creation date (newest first)
        query = query.order_by(desc(APIUsage.created_at))
        
        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )
        
        # Convert to dictionaries
        usage_records = [record.to_dict() for record in pagination.items]
        
        return ResponseFormatter.paginated(
            items=usage_records,
            page=page,
            per_page=per_page,
            total=pagination.total
        )
        
    except Exception as e:
        logger.error(f"Error getting API usage: {e}")
        return ResponseFormatter.error("Failed to retrieve API usage records", status_code=500)


@cost_bp.route('/usage/<int:usage_id>', methods=['GET'])
@api_rate_limit
def get_usage_record(usage_id):
    """Get specific API usage record"""
    try:
        usage_record = db.session.query(APIUsage).get(usage_id)
        if not usage_record:
            return ResponseFormatter.error("Usage record not found", status_code=404)
        
        return ResponseFormatter.success(data=usage_record.to_dict())
        
    except Exception as e:
        logger.error(f"Error getting usage record {usage_id}: {e}")
        return ResponseFormatter.error("Failed to retrieve usage record", status_code=500)


@cost_bp.route('/summary', methods=['GET'])
@api_rate_limit
def get_cost_summary():
    """Get cost summary and analytics"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        provider = request.args.get('provider')
        agent_id = request.args.get('agent_id', type=int)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid start_date format", status_code=400)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid end_date format", status_code=400)
        
        # Parse provider
        provider_enum = None
        if provider:
            try:
                provider_enum = APIProvider(provider.lower())
            except ValueError:
                return ResponseFormatter.error(f"Invalid provider: {provider}", status_code=400)
        
        # Get cost summary
        summary = cost_analytics.get_cost_summary(
            start_date=start_dt,
            end_date=end_dt,
            provider=provider_enum,
            agent_id=agent_id
        )
        
        return ResponseFormatter.success(data=summary)
        
    except Exception as e:
        logger.error(f"Error getting cost summary: {e}")
        return ResponseFormatter.error("Failed to generate cost summary", status_code=500)


@cost_bp.route('/top-drivers', methods=['GET'])
@api_rate_limit
def get_top_cost_drivers():
    """Get top cost drivers (models, agents, etc.)"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        limit = request.args.get('limit', 10, type=int)
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid start_date format", status_code=400)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid end_date format", status_code=400)
        
        # Get top cost drivers
        drivers = cost_analytics.get_top_cost_drivers(
            start_date=start_dt,
            end_date=end_dt,
            limit=min(limit, 50)  # Cap at 50
        )
        
        return ResponseFormatter.success(data=drivers)
        
    except Exception as e:
        logger.error(f"Error getting top cost drivers: {e}")
        return ResponseFormatter.error("Failed to get top cost drivers", status_code=500)


@cost_bp.route('/efficiency', methods=['GET'])
@api_rate_limit
def get_cost_efficiency():
    """Get cost efficiency metrics and recommendations"""
    try:
        # Parse query parameters
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        # Parse dates
        start_dt = None
        end_dt = None
        
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid start_date format", status_code=400)
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                return ResponseFormatter.error("Invalid end_date format", status_code=400)
        
        # Get efficiency metrics
        efficiency = cost_analytics.get_cost_efficiency_metrics(
            start_date=start_dt,
            end_date=end_dt
        )
        
        return ResponseFormatter.success(data=efficiency)
        
    except Exception as e:
        logger.error(f"Error getting cost efficiency: {e}")
        return ResponseFormatter.error("Failed to get cost efficiency metrics", status_code=500)


@cost_bp.route('/pricing', methods=['GET'])
@api_rate_limit
def get_pricing_info():
    """Get current API pricing information"""
    try:
        provider = request.args.get('provider')
        model = request.args.get('model')
        
        if provider and model:
            # Get specific model pricing
            try:
                provider_enum = APIProvider(provider.lower())
                pricing = cost_calculator.get_model_pricing_info(provider_enum, model)
                return ResponseFormatter.success(data=pricing)
            except ValueError:
                return ResponseFormatter.error(f"Invalid provider: {provider}", status_code=400)
        else:
            # Get all pricing information
            all_pricing = cost_calculator.get_all_pricing_info()
            return ResponseFormatter.success(data=all_pricing)
        
    except Exception as e:
        logger.error(f"Error getting pricing info: {e}")
        return ResponseFormatter.error("Failed to get pricing information", status_code=500)


@cost_bp.route('/estimate', methods=['POST'])
@api_rate_limit
def estimate_cost():
    """Estimate cost for planned API usage"""
    try:
        # Validate request data
        required_fields = ['provider', 'model', 'estimated_input_tokens']
        data = validate_json_data(request, required_fields)
        
        # Parse provider
        try:
            provider_enum = APIProvider(data['provider'].lower())
        except ValueError:
            return ResponseFormatter.error(f"Invalid provider: {data['provider']}", status_code=400)
        
        # Get estimate
        estimate = cost_calculator.estimate_cost(
            provider=provider_enum,
            model=data['model'],
            estimated_input_tokens=data['estimated_input_tokens'],
            estimated_output_tokens=data.get('estimated_output_tokens')
        )
        
        return ResponseFormatter.success(data=estimate)

    except Exception as e:
        logger.error(f"Error estimating cost: {e}")
        return ResponseFormatter.error("Failed to estimate cost", status_code=500)


# Budget Management Routes

@cost_bp.route('/budgets', methods=['GET'])
@api_rate_limit
def get_budgets():
    """Get all cost budgets"""
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        is_active = request.args.get('is_active', type=bool)

        # Build query
        query = db.session.query(CostBudget)

        if is_active is not None:
            query = query.filter(CostBudget.is_active == is_active)

        # Order by creation date (newest first)
        query = query.order_by(desc(CostBudget.created_at))

        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Convert to dictionaries with status
        budgets = []
        for budget in pagination.items:
            budget_dict = budget.to_dict()
            # Add current status
            try:
                status = budget_manager.get_budget_status(budget.id)
                budget_dict['status'] = status['status']
            except Exception as e:
                logger.warning(f"Failed to get status for budget {budget.id}: {e}")
                budget_dict['status'] = {'error': 'Failed to calculate status'}
            budgets.append(budget_dict)

        return ResponseFormatter.paginated(
            items=budgets,
            page=page,
            per_page=per_page,
            total=pagination.total
        )

    except Exception as e:
        logger.error(f"Error getting budgets: {e}")
        return ResponseFormatter.error("Failed to retrieve budgets", status_code=500)


@cost_bp.route('/budgets', methods=['POST'])
@api_rate_limit
def create_budget():
    """Create a new cost budget"""
    try:
        # Validate request data
        required_fields = ['name', 'limit_amount', 'period']
        data = validate_json_data(request, required_fields)

        # Parse period
        try:
            period_enum = BudgetPeriod(data['period'].lower())
        except ValueError:
            return ResponseFormatter.error(f"Invalid period: {data['period']}", status_code=400)

        # Parse provider if provided
        provider_enum = None
        if data.get('provider'):
            try:
                provider_enum = APIProvider(data['provider'].lower())
            except ValueError:
                return ResponseFormatter.error(f"Invalid provider: {data['provider']}", status_code=400)

        # Create budget
        budget = budget_manager.create_budget(
            name=data['name'],
            limit_amount=float(data['limit_amount']),
            period=period_enum,
            description=data.get('description'),
            provider=provider_enum,
            model=data.get('model'),
            agent_id=data.get('agent_id'),
            warning_threshold=data.get('warning_threshold', 80),
            critical_threshold=data.get('critical_threshold', 95)
        )

        return ResponseFormatter.success(
            data=budget.to_dict(),
            message="Budget created successfully",
            status_code=201
        )

    except Exception as e:
        logger.error(f"Error creating budget: {e}")
        return ResponseFormatter.error("Failed to create budget", status_code=500)


@cost_bp.route('/budgets/<int:budget_id>', methods=['GET'])
@api_rate_limit
def get_budget(budget_id):
    """Get specific budget with detailed status"""
    try:
        budget = db.session.query(CostBudget).get(budget_id)
        if not budget:
            return ResponseFormatter.error("Budget not found", status_code=404)

        # Get detailed status
        status = budget_manager.get_budget_status(budget_id)

        return ResponseFormatter.success(data=status)

    except Exception as e:
        logger.error(f"Error getting budget {budget_id}: {e}")
        return ResponseFormatter.error("Failed to retrieve budget", status_code=500)


@cost_bp.route('/budgets/<int:budget_id>', methods=['PUT'])
@api_rate_limit
def update_budget(budget_id):
    """Update an existing budget"""
    try:
        budget = db.session.query(CostBudget).get(budget_id)
        if not budget:
            return ResponseFormatter.error("Budget not found", status_code=404)

        # Validate request data
        data = validate_json_data(request, [])

        # Update fields
        if 'name' in data:
            budget.name = data['name']
        if 'description' in data:
            budget.description = data['description']
        if 'limit_amount' in data:
            budget.limit_amount = float(data['limit_amount'])
        if 'warning_threshold' in data:
            budget.warning_threshold = int(data['warning_threshold'])
        if 'critical_threshold' in data:
            budget.critical_threshold = int(data['critical_threshold'])
        if 'is_active' in data:
            budget.is_active = bool(data['is_active'])

        # Parse period if provided
        if 'period' in data:
            try:
                budget.period = BudgetPeriod(data['period'].lower())
                # Reset period when period type changes
                budget.reset_period()
            except ValueError:
                return ResponseFormatter.error(f"Invalid period: {data['period']}", status_code=400)

        # Parse provider if provided
        if 'provider' in data:
            if data['provider']:
                try:
                    budget.provider = APIProvider(data['provider'].lower())
                except ValueError:
                    return ResponseFormatter.error(f"Invalid provider: {data['provider']}", status_code=400)
            else:
                budget.provider = None

        if 'model' in data:
            budget.model = data['model'] if data['model'] else None

        if 'agent_id' in data:
            budget.agent_id = data['agent_id'] if data['agent_id'] else None

        budget.save()

        return ResponseFormatter.success(
            data=budget.to_dict(),
            message="Budget updated successfully"
        )

    except Exception as e:
        logger.error(f"Error updating budget {budget_id}: {e}")
        return ResponseFormatter.error("Failed to update budget", status_code=500)


@cost_bp.route('/budgets/<int:budget_id>', methods=['DELETE'])
@api_rate_limit
def delete_budget(budget_id):
    """Delete a budget"""
    try:
        budget = db.session.query(CostBudget).get(budget_id)
        if not budget:
            return ResponseFormatter.error("Budget not found", status_code=404)

        budget.delete()

        return ResponseFormatter.success(message="Budget deleted successfully")

    except Exception as e:
        logger.error(f"Error deleting budget {budget_id}: {e}")
        return ResponseFormatter.error("Failed to delete budget", status_code=500)


# Alert Management Routes

@cost_bp.route('/alerts', methods=['GET'])
@api_rate_limit
def get_cost_alerts():
    """Get cost-related alerts"""
    try:
        # Parse query parameters
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 100)
        is_acknowledged = request.args.get('is_acknowledged', type=bool)
        severity = request.args.get('severity')
        alert_type = request.args.get('alert_type')

        # Build query
        query = db.session.query(CostAlert)

        if is_acknowledged is not None:
            query = query.filter(CostAlert.is_acknowledged == is_acknowledged)

        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
                query = query.filter(CostAlert.severity == severity_enum)
            except ValueError:
                return ResponseFormatter.error(f"Invalid severity: {severity}", status_code=400)

        if alert_type:
            query = query.filter(CostAlert.alert_type == alert_type)

        # Order by creation date (newest first)
        query = query.order_by(desc(CostAlert.created_at))

        # Paginate
        pagination = query.paginate(
            page=page, per_page=per_page, error_out=False
        )

        # Convert to dictionaries
        alerts = [alert.to_dict() for alert in pagination.items]

        return ResponseFormatter.paginated(
            items=alerts,
            page=page,
            per_page=per_page,
            total=pagination.total
        )

    except Exception as e:
        logger.error(f"Error getting cost alerts: {e}")
        return ResponseFormatter.error("Failed to retrieve cost alerts", status_code=500)


@cost_bp.route('/alerts/<int:alert_id>', methods=['GET'])
@api_rate_limit
def get_cost_alert(alert_id):
    """Get specific cost alert"""
    try:
        alert = db.session.query(CostAlert).get(alert_id)
        if not alert:
            return ResponseFormatter.error("Alert not found", status_code=404)

        return ResponseFormatter.success(data=alert.to_dict())

    except Exception as e:
        logger.error(f"Error getting cost alert {alert_id}: {e}")
        return ResponseFormatter.error("Failed to retrieve cost alert", status_code=500)


@cost_bp.route('/alerts/<int:alert_id>/acknowledge', methods=['POST'])
@api_rate_limit
def acknowledge_alert(alert_id):
    """Acknowledge a cost alert"""
    try:
        alert = db.session.query(CostAlert).get(alert_id)
        if not alert:
            return ResponseFormatter.error("Alert not found", status_code=404)

        if alert.is_acknowledged:
            return ResponseFormatter.error("Alert already acknowledged", status_code=400)

        # Get acknowledged_by from request data or use default
        data = request.get_json() or {}
        acknowledged_by = data.get('acknowledged_by', 'system')

        alert.acknowledge(acknowledged_by)

        return ResponseFormatter.success(
            data=alert.to_dict(),
            message="Alert acknowledged successfully"
        )

    except Exception as e:
        logger.error(f"Error acknowledging alert {alert_id}: {e}")
        return ResponseFormatter.error("Failed to acknowledge alert", status_code=500)


@cost_bp.route('/alerts/acknowledge-all', methods=['POST'])
@api_rate_limit
def acknowledge_all_alerts():
    """Acknowledge all unacknowledged alerts"""
    try:
        # Get request data
        data = request.get_json() or {}
        acknowledged_by = data.get('acknowledged_by', 'system')
        severity = data.get('severity')  # Optional: only acknowledge alerts of specific severity

        # Build query for unacknowledged alerts
        query = db.session.query(CostAlert).filter(CostAlert.is_acknowledged == False)

        if severity:
            try:
                severity_enum = AlertSeverity(severity.lower())
                query = query.filter(CostAlert.severity == severity_enum)
            except ValueError:
                return ResponseFormatter.error(f"Invalid severity: {severity}", status_code=400)

        # Get all unacknowledged alerts
        alerts = query.all()

        # Acknowledge all alerts
        acknowledged_count = 0
        for alert in alerts:
            alert.acknowledge(acknowledged_by)
            acknowledged_count += 1

        return ResponseFormatter.success(
            data={'acknowledged_count': acknowledged_count},
            message=f"Acknowledged {acknowledged_count} alerts"
        )

    except Exception as e:
        logger.error(f"Error acknowledging all alerts: {e}")
        return ResponseFormatter.error("Failed to acknowledge alerts", status_code=500)


# Dashboard and Status Routes

@cost_bp.route('/dashboard', methods=['GET'])
@api_rate_limit
def get_cost_dashboard():
    """Get comprehensive cost dashboard data"""
    try:
        # Get current date range (last 30 days)
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=30)

        # Get cost summary
        cost_summary = cost_analytics.get_cost_summary(start_date, end_date)

        # Get budget status
        budget_status = budget_manager.get_all_budgets_status()

        # Get recent alerts (last 10 unacknowledged)
        recent_alerts = db.session.query(CostAlert).filter(
            CostAlert.is_acknowledged == False
        ).order_by(desc(CostAlert.created_at)).limit(10).all()

        # Get top cost drivers
        top_drivers = cost_analytics.get_top_cost_drivers(start_date, end_date, limit=5)

        # Get efficiency metrics
        efficiency = cost_analytics.get_cost_efficiency_metrics(start_date, end_date)

        dashboard_data = {
            'cost_summary': cost_summary,
            'budget_status': budget_status,
            'recent_alerts': [alert.to_dict() for alert in recent_alerts],
            'top_drivers': top_drivers,
            'efficiency_metrics': efficiency,
            'generated_at': datetime.utcnow().isoformat()
        }

        return ResponseFormatter.success(data=dashboard_data)

    except Exception as e:
        logger.error(f"Error generating cost dashboard: {e}")
        return ResponseFormatter.error("Failed to generate cost dashboard", status_code=500)


@cost_bp.route('/status', methods=['GET'])
@api_rate_limit
def get_cost_status():
    """Get current cost tracking system status"""
    try:
        # Get basic statistics
        total_usage_records = db.session.query(func.count(APIUsage.id)).scalar()
        total_budgets = db.session.query(func.count(CostBudget.id)).scalar()
        active_budgets = db.session.query(func.count(CostBudget.id)).filter(
            CostBudget.is_active == True
        ).scalar()
        unacknowledged_alerts = db.session.query(func.count(CostAlert.id)).filter(
            CostAlert.is_acknowledged == False
        ).scalar()

        # Get recent usage (last 24 hours)
        yesterday = datetime.utcnow() - timedelta(days=1)
        recent_usage = db.session.query(func.count(APIUsage.id)).filter(
            APIUsage.created_at >= yesterday
        ).scalar()

        # Get total cost (last 30 days)
        thirty_days_ago = datetime.utcnow() - timedelta(days=30)
        total_cost_30d = db.session.query(func.sum(APIUsage.total_cost)).filter(
            APIUsage.created_at >= thirty_days_ago
        ).scalar() or 0

        status_data = {
            'system_status': 'operational',
            'statistics': {
                'total_usage_records': total_usage_records,
                'total_budgets': total_budgets,
                'active_budgets': active_budgets,
                'unacknowledged_alerts': unacknowledged_alerts,
                'recent_usage_24h': recent_usage,
                'total_cost_30d': float(total_cost_30d)
            },
            'last_updated': datetime.utcnow().isoformat()
        }

        return ResponseFormatter.success(data=status_data)

    except Exception as e:
        logger.error(f"Error getting cost status: {e}")
        return ResponseFormatter.error("Failed to get cost status", status_code=500)
