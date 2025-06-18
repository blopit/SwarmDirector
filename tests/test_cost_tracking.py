#!/usr/bin/env python3
"""
Test script for cost tracking functionality
"""

import os
import sys
import tempfile
import unittest
from datetime import datetime, timedelta
from decimal import Decimal

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from swarm_director.app import create_app
from swarm_director.models.base import db
from swarm_director.models.cost_tracking import (
    APIUsage, CostBudget, CostAlert, APIProvider, 
    BudgetPeriod, UsageType, AlertSeverity
)
from swarm_director.utils.cost_calculator import cost_calculator
from swarm_director.utils.budget_manager import budget_manager
from swarm_director.utils.cost_analytics import cost_analytics


class TestCostTracking(unittest.TestCase):
    """Test cases for cost tracking functionality"""
    
    def setUp(self):
        """Set up test environment"""
        # Create temporary database
        self.db_fd, self.db_path = tempfile.mkstemp()
        
        # Create test app
        self.app = create_app('testing')
        self.app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{self.db_path}'
        self.app.config['TESTING'] = True
        
        # Create application context
        self.app_context = self.app.app_context()
        self.app_context.push()
        
        # Create all tables
        db.create_all()
        
        # Create test client
        self.client = self.app.test_client()
    
    def tearDown(self):
        """Clean up test environment"""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        os.close(self.db_fd)
        os.unlink(self.db_path)
    
    def test_cost_calculator(self):
        """Test cost calculation functionality"""
        # Test OpenAI GPT-4 cost calculation
        input_cost, output_cost, total_cost, input_price, output_price = cost_calculator.calculate_cost(
            provider=APIProvider.OPENAI,
            model="gpt-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        # Verify calculations
        self.assertGreater(input_cost, 0)
        self.assertGreater(output_cost, 0)
        self.assertEqual(total_cost, input_cost + output_cost)
        self.assertGreater(input_price, 0)
        self.assertGreater(output_price, 0)
        
        print(f"✅ Cost calculation test passed: ${float(total_cost):.6f} for 1500 tokens")
    
    def test_api_usage_creation(self):
        """Test API usage record creation"""
        usage = APIUsage(
            request_id="test-request-001",
            provider=APIProvider.OPENAI,
            model="gpt-4",
            usage_type=UsageType.CHAT_COMPLETION,
            input_tokens=1000,
            output_tokens=500,
            total_tokens=1500,
            input_cost=Decimal("0.030000"),
            output_cost=Decimal("0.030000"),
            total_cost=Decimal("0.060000"),
            response_status="success"
        )
        
        usage.save()
        
        # Verify record was created
        retrieved = APIUsage.query.filter_by(request_id="test-request-001").first()
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.provider, APIProvider.OPENAI)
        self.assertEqual(retrieved.total_tokens, 1500)
        self.assertEqual(float(retrieved.total_cost), 0.060000)
        
        print(f"✅ API usage creation test passed: {retrieved.request_id}")
    
    def test_budget_creation_and_management(self):
        """Test budget creation and management"""
        # Create a test budget
        budget = budget_manager.create_budget(
            name="Test Monthly Budget",
            limit_amount=100.00,
            period=BudgetPeriod.MONTHLY,
            description="Test budget for unit testing",
            warning_threshold=80,
            critical_threshold=95
        )
        
        self.assertIsNotNone(budget)
        self.assertEqual(budget.name, "Test Monthly Budget")
        self.assertEqual(float(budget.limit_amount), 100.00)
        self.assertEqual(budget.period, BudgetPeriod.MONTHLY)
        
        # Test budget status
        status = budget_manager.get_budget_status(budget.id)
        self.assertIn('budget', status)
        self.assertIn('status', status)
        
        print(f"✅ Budget creation test passed: {budget.name}")
    
    def test_budget_threshold_alerts(self):
        """Test budget threshold alerting"""
        # Create a small budget for testing
        budget = budget_manager.create_budget(
            name="Small Test Budget",
            limit_amount=1.00,  # $1 limit
            period=BudgetPeriod.MONTHLY,
            warning_threshold=50,  # 50 cents warning
            critical_threshold=80  # 80 cents critical
        )
        
        # Create usage that triggers warning
        usage = APIUsage(
            request_id="test-warning-001",
            provider=APIProvider.OPENAI,
            model="gpt-4",
            total_cost=Decimal("0.60"),  # 60 cents - should trigger warning
            response_status="success"
        )
        usage.save()
        
        # Update budget usage
        alerts = budget_manager.update_budget_usage(usage)
        
        # Should have created a warning alert
        self.assertGreater(len(alerts), 0)
        warning_alert = alerts[0]
        self.assertEqual(warning_alert.alert_type, 'budget_warning')
        self.assertEqual(warning_alert.severity, AlertSeverity.WARNING)
        
        print(f"✅ Budget alerting test passed: {len(alerts)} alerts created")
    
    def test_cost_analytics(self):
        """Test cost analytics functionality"""
        # Create some test usage data
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=7)
        
        # Create test usage records
        for i in range(5):
            usage = APIUsage(
                request_id=f"test-analytics-{i:03d}",
                provider=APIProvider.OPENAI,
                model="gpt-4" if i % 2 == 0 else "gpt-3.5-turbo",
                input_tokens=1000 + (i * 100),
                output_tokens=500 + (i * 50),
                total_tokens=1500 + (i * 150),
                total_cost=Decimal(f"0.{60 + i:02d}0000"),
                response_status="success",
                created_at=start_date + timedelta(days=i)
            )
            usage.save()
        
        # Test cost summary
        summary = cost_analytics.get_cost_summary(start_date, end_date)
        
        self.assertIn('summary', summary)
        self.assertIn('breakdowns', summary)
        self.assertIn('trends', summary)
        
        # Verify summary data
        self.assertEqual(summary['summary']['total_requests'], 5)
        self.assertGreater(summary['summary']['total_cost'], 0)
        self.assertGreater(summary['summary']['total_tokens'], 0)
        
        print(f"✅ Cost analytics test passed: {summary['summary']['total_requests']} requests analyzed")
    
    def test_api_endpoints(self):
        """Test cost tracking API endpoints"""
        # Create some test data first
        usage = APIUsage(
            request_id="test-api-001",
            provider=APIProvider.ANTHROPIC,
            model="claude-3-sonnet-20240229",
            total_cost=Decimal("0.045000"),
            response_status="success"
        )
        usage.save()
        
        budget = budget_manager.create_budget(
            name="API Test Budget",
            limit_amount=50.00,
            period=BudgetPeriod.MONTHLY
        )
        
        # Test usage endpoint
        response = self.client.get('/api/cost/usage')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        self.assertIn('data', data)
        
        # Test summary endpoint
        response = self.client.get('/api/cost/summary')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        # Test budgets endpoint
        response = self.client.get('/api/cost/budgets')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        # Test dashboard endpoint
        response = self.client.get('/api/cost/dashboard')
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data['status'], 'success')
        
        print("✅ API endpoints test passed: All endpoints responding correctly")
    
    def test_pricing_info(self):
        """Test pricing information retrieval"""
        # Test specific model pricing
        pricing = cost_calculator.get_model_pricing_info(APIProvider.OPENAI, "gpt-4")
        
        self.assertTrue(pricing['pricing_available'])
        self.assertGreater(pricing['input_price_per_1m_tokens'], 0)
        self.assertGreater(pricing['output_price_per_1m_tokens'], 0)
        
        # Test all pricing info
        all_pricing = cost_calculator.get_all_pricing_info()
        
        self.assertIn('pricing', all_pricing)
        self.assertIn('openai', all_pricing['pricing'])
        self.assertIn('anthropic', all_pricing['pricing'])
        
        print("✅ Pricing info test passed: Pricing data available for all providers")


def run_integration_test():
    """Run a simple integration test"""
    print("🧪 Running Cost Tracking Integration Test")
    print("=" * 50)
    
    # Create test app
    app = create_app('testing')
    
    with app.app_context():
        # Test cost calculation
        input_cost, output_cost, total_cost, _, _ = cost_calculator.calculate_cost(
            provider=APIProvider.OPENAI,
            model="gpt-4",
            input_tokens=1000,
            output_tokens=500
        )
        
        print(f"💰 Cost Calculation Test:")
        print(f"   Input tokens: 1000 → ${float(input_cost):.6f}")
        print(f"   Output tokens: 500 → ${float(output_cost):.6f}")
        print(f"   Total cost: ${float(total_cost):.6f}")
        print()
        
        # Test pricing info
        pricing = cost_calculator.get_model_pricing_info(APIProvider.ANTHROPIC, "claude-3-sonnet-20240229")
        print(f"📊 Pricing Info Test:")
        print(f"   Model: {pricing['model']}")
        print(f"   Input: ${pricing['input_price_per_1m_tokens']}/1M tokens")
        print(f"   Output: ${pricing['output_price_per_1m_tokens']}/1M tokens")
        print()
        
        print("✅ Integration test completed successfully!")


if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'integration':
        # Run integration test
        run_integration_test()
    else:
        # Run unit tests
        unittest.main(verbosity=2)
