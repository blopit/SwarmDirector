"""
Budget management service for AI API cost control
Handles budget creation, monitoring, and alerting
"""

import logging
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy import and_, func
from decimal import Decimal

from ..models.base import db
from ..models.cost_tracking import (
    CostBudget, CostAlert, APIUsage, APIProvider, 
    BudgetPeriod, AlertSeverity
)
from .alerting import AlertingEngine

logger = logging.getLogger(__name__)


class BudgetManager:
    """Main budget management service"""
    
    def __init__(self, alerting_engine: Optional[AlertingEngine] = None):
        self.logger = logging.getLogger(f"{__name__}.BudgetManager")
        self.alerting_engine = alerting_engine
    
    def create_budget(
        self,
        name: str,
        limit_amount: float,
        period: BudgetPeriod = BudgetPeriod.MONTHLY,
        description: Optional[str] = None,
        provider: Optional[APIProvider] = None,
        model: Optional[str] = None,
        agent_id: Optional[int] = None,
        warning_threshold: int = 80,
        critical_threshold: int = 95
    ) -> CostBudget:
        """Create a new cost budget"""
        try:
            budget = CostBudget(
                name=name,
                description=description,
                provider=provider,
                model=model,
                agent_id=agent_id,
                period=period,
                limit_amount=Decimal(str(limit_amount)),
                warning_threshold=warning_threshold,
                critical_threshold=critical_threshold,
                is_active=True
            )
            
            # Set initial period
            budget.reset_period()
            
            self.logger.info(f"Created budget '{name}' with limit ${limit_amount} per {period.value}")
            return budget
            
        except Exception as e:
            self.logger.error(f"Failed to create budget '{name}': {e}")
            raise
    
    def update_budget_usage(self, usage_record: APIUsage) -> List[CostAlert]:
        """Update budget usage and check for threshold violations"""
        alerts = []
        
        try:
            # Find applicable budgets
            applicable_budgets = self._find_applicable_budgets(usage_record)
            
            for budget in applicable_budgets:
                # Check if budget period needs reset
                if datetime.utcnow() > budget.current_period_end:
                    budget.reset_period()
                
                # Update budget usage
                old_spent = budget.current_period_spent
                budget.current_period_spent += usage_record.total_cost
                budget.save()
                
                self.logger.debug(
                    f"Updated budget '{budget.name}': "
                    f"${float(old_spent):.6f} -> ${float(budget.current_period_spent):.6f}"
                )
                
                # Check for threshold violations
                alerts.extend(self._check_budget_thresholds(budget, usage_record))
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to update budget usage: {e}")
            return []
    
    def _find_applicable_budgets(self, usage_record: APIUsage) -> List[CostBudget]:
        """Find budgets that apply to the given usage record"""
        query = db.session.query(CostBudget).filter(
            CostBudget.is_active == True,
            CostBudget.current_period_start <= datetime.utcnow(),
            CostBudget.current_period_end > datetime.utcnow()
        )
        
        applicable_budgets = []
        
        for budget in query.all():
            # Check if budget applies to this usage
            if self._budget_applies_to_usage(budget, usage_record):
                applicable_budgets.append(budget)
        
        return applicable_budgets
    
    def _budget_applies_to_usage(self, budget: CostBudget, usage: APIUsage) -> bool:
        """Check if a budget applies to a specific usage record"""
        # Check provider filter
        if budget.provider and budget.provider != usage.provider:
            return False
        
        # Check model filter
        if budget.model and budget.model != usage.model:
            return False
        
        # Check agent filter
        if budget.agent_id and budget.agent_id != usage.agent_id:
            return False
        
        return True
    
    def _check_budget_thresholds(self, budget: CostBudget, usage_record: APIUsage) -> List[CostAlert]:
        """Check budget thresholds and create alerts if necessary"""
        alerts = []
        usage_percentage = budget.get_usage_percentage()
        
        try:
            # Check critical threshold
            if usage_percentage >= budget.critical_threshold:
                if not self._alert_exists(budget, 'budget_critical'):
                    alert = self._create_budget_alert(
                        budget=budget,
                        alert_type='budget_critical',
                        severity=AlertSeverity.CRITICAL,
                        usage_record=usage_record,
                        usage_percentage=usage_percentage
                    )
                    alerts.append(alert)
            
            # Check warning threshold
            elif usage_percentage >= budget.warning_threshold:
                if not self._alert_exists(budget, 'budget_warning'):
                    alert = self._create_budget_alert(
                        budget=budget,
                        alert_type='budget_warning',
                        severity=AlertSeverity.WARNING,
                        usage_record=usage_record,
                        usage_percentage=usage_percentage
                    )
                    alerts.append(alert)
            
            # Check if budget is exceeded
            if budget.current_period_spent > budget.limit_amount:
                if not self._alert_exists(budget, 'budget_exceeded'):
                    alert = self._create_budget_alert(
                        budget=budget,
                        alert_type='budget_exceeded',
                        severity=AlertSeverity.CRITICAL,
                        usage_record=usage_record,
                        usage_percentage=usage_percentage
                    )
                    alerts.append(alert)
            
            return alerts
            
        except Exception as e:
            self.logger.error(f"Failed to check budget thresholds for '{budget.name}': {e}")
            return []
    
    def _alert_exists(self, budget: CostBudget, alert_type: str) -> bool:
        """Check if an alert of the given type already exists for this budget period"""
        return db.session.query(CostAlert).filter(
            CostAlert.budget_id == budget.id,
            CostAlert.alert_type == alert_type,
            CostAlert.created_at >= budget.current_period_start,
            CostAlert.is_acknowledged == False
        ).first() is not None
    
    def _create_budget_alert(
        self,
        budget: CostBudget,
        alert_type: str,
        severity: AlertSeverity,
        usage_record: APIUsage,
        usage_percentage: float
    ) -> CostAlert:
        """Create a budget-related alert"""
        # Generate alert title and message
        if alert_type == 'budget_warning':
            title = f"Budget Warning: {budget.name}"
            message = (
                f"Budget '{budget.name}' has reached {usage_percentage:.1f}% of its "
                f"${float(budget.limit_amount):.2f} {budget.period.value} limit. "
                f"Current spending: ${float(budget.current_period_spent):.2f}"
            )
        elif alert_type == 'budget_critical':
            title = f"Budget Critical: {budget.name}"
            message = (
                f"Budget '{budget.name}' has reached {usage_percentage:.1f}% of its "
                f"${float(budget.limit_amount):.2f} {budget.period.value} limit. "
                f"Current spending: ${float(budget.current_period_spent):.2f}. "
                f"Immediate attention required!"
            )
        elif alert_type == 'budget_exceeded':
            title = f"Budget Exceeded: {budget.name}"
            message = (
                f"Budget '{budget.name}' has been exceeded! "
                f"Limit: ${float(budget.limit_amount):.2f}, "
                f"Current spending: ${float(budget.current_period_spent):.2f} "
                f"({usage_percentage:.1f}% of limit)"
            )
        else:
            title = f"Budget Alert: {budget.name}"
            message = f"Budget alert for '{budget.name}'"
        
        # Create alert
        alert = CostAlert(
            alert_type=alert_type,
            severity=severity,
            title=title,
            message=message,
            budget_id=budget.id,
            usage_id=usage_record.id,
            agent_id=usage_record.agent_id,
            metadata={
                'usage_percentage': usage_percentage,
                'budget_limit': float(budget.limit_amount),
                'current_spent': float(budget.current_period_spent),
                'period': budget.period.value,
                'provider': usage_record.provider.value,
                'model': usage_record.model
            }
        )
        
        alert.save()
        
        self.logger.warning(f"Created {alert_type} alert for budget '{budget.name}': {usage_percentage:.1f}%")
        
        # Send notification if alerting engine is available
        if self.alerting_engine:
            try:
                self.alerting_engine.send_alert(alert)
                alert.notification_sent = True
                alert.save()
            except Exception as e:
                self.logger.error(f"Failed to send alert notification: {e}")
        
        return alert
    
    def get_budget_status(self, budget_id: int) -> Dict[str, Any]:
        """Get current status of a budget"""
        budget = db.session.query(CostBudget).get(budget_id)
        if not budget:
            raise ValueError(f"Budget {budget_id} not found")
        
        # Check if period needs reset
        if datetime.utcnow() > budget.current_period_end:
            budget.reset_period()
        
        return {
            'budget': budget.to_dict(),
            'status': {
                'is_over_warning': budget.is_over_threshold('warning'),
                'is_over_critical': budget.is_over_threshold('critical'),
                'is_exceeded': budget.current_period_spent > budget.limit_amount,
                'days_remaining': (budget.current_period_end - datetime.utcnow()).days,
                'usage_trend': self._calculate_usage_trend(budget)
            }
        }
    
    def _calculate_usage_trend(self, budget: CostBudget) -> Dict[str, Any]:
        """Calculate usage trend for a budget"""
        try:
            # Get daily usage for current period
            daily_usage = db.session.query(
                func.date(APIUsage.created_at).label('date'),
                func.sum(APIUsage.total_cost).label('daily_cost')
            ).filter(
                APIUsage.created_at >= budget.current_period_start,
                APIUsage.created_at < budget.current_period_end
            )
            
            # Apply budget filters
            if budget.provider:
                daily_usage = daily_usage.filter(APIUsage.provider == budget.provider)
            if budget.model:
                daily_usage = daily_usage.filter(APIUsage.model == budget.model)
            if budget.agent_id:
                daily_usage = daily_usage.filter(APIUsage.agent_id == budget.agent_id)
            
            daily_usage = daily_usage.group_by(func.date(APIUsage.created_at)).all()
            
            if len(daily_usage) < 2:
                return {'trend': 'insufficient_data', 'daily_average': 0.0}
            
            # Calculate trend
            recent_avg = sum(float(day.daily_cost) for day in daily_usage[-3:]) / min(3, len(daily_usage))
            overall_avg = sum(float(day.daily_cost) for day in daily_usage) / len(daily_usage)
            
            if recent_avg > overall_avg * 1.2:
                trend = 'increasing'
            elif recent_avg < overall_avg * 0.8:
                trend = 'decreasing'
            else:
                trend = 'stable'
            
            return {
                'trend': trend,
                'daily_average': overall_avg,
                'recent_average': recent_avg,
                'data_points': len(daily_usage)
            }
            
        except Exception as e:
            self.logger.error(f"Failed to calculate usage trend: {e}")
            return {'trend': 'error', 'daily_average': 0.0}
    
    def get_all_budgets_status(self) -> List[Dict[str, Any]]:
        """Get status of all active budgets"""
        budgets = db.session.query(CostBudget).filter(CostBudget.is_active == True).all()
        return [self.get_budget_status(budget.id) for budget in budgets]


# Global budget manager instance
budget_manager = BudgetManager()
