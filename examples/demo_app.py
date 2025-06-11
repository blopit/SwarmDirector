#!/usr/bin/env python3
"""
Interactive Demo Application for SwarmDirector
Showcases key features with realistic data and visual storytelling elements
"""

import json
import time
from datetime import datetime, timedelta
from flask import Flask, render_template, request, jsonify, redirect, url_for
from app import create_app
from models.task import Task, TaskStatus, TaskPriority
from models.agent import Agent, AgentType, AgentStatus
from models.conversation import Conversation, Message, MessageType
from agents.director import DirectorAgent

# Create demo app that extends main app
demo_app = create_app()

# Demo data for realistic scenarios
DEMO_SCENARIOS = {
    'customer_support': {
        'title': 'Customer Support Automation',
        'description': 'Handle customer inquiries with intelligent routing and automated responses',
        'tasks': [
            {
                'type': 'email',
                'title': 'Welcome new customer',
                'description': 'Send personalized welcome email to Sarah Johnson who just signed up for our premium plan',
                'priority': 'high',
                'args': {
                    'customer_name': 'Sarah Johnson',
                    'plan': 'premium',
                    'template': 'welcome_premium'
                }
            },
            {
                'type': 'analysis',
                'title': 'Analyze support ticket trends',
                'description': 'Review last month\'s support tickets to identify common issues and improvement opportunities',
                'priority': 'medium',
                'args': {
                    'period': 'last_30_days',
                    'categories': ['billing', 'technical', 'feature_requests']
                }
            }
        ]
    },
    'marketing_campaign': {
        'title': 'Marketing Campaign Management',
        'description': 'Coordinate multi-channel marketing campaigns with automated workflow',
        'tasks': [
            {
                'type': 'coordinate',
                'title': 'Launch Q4 product campaign',
                'description': 'Coordinate the launch of our new product feature across all marketing channels',
                'priority': 'high',
                'args': {
                    'campaign_name': 'Q4_Product_Launch',
                    'channels': ['email', 'social_media', 'blog', 'ads'],
                    'budget': '$50000'
                }
            },
            {
                'type': 'email',
                'title': 'Send campaign announcement',
                'description': 'Send announcement email to 15,000 subscribers about the new product features',
                'priority': 'high',
                'args': {
                    'audience': 'all_subscribers',
                    'template': 'product_announcement',
                    'send_time': 'optimal'
                }
            }
        ]
    },
    'data_insights': {
        'title': 'Business Intelligence & Analytics',
        'description': 'Generate automated insights and reports from business data',
        'tasks': [
            {
                'type': 'analysis',
                'title': 'Generate monthly revenue report',
                'description': 'Analyze revenue trends, top customers, and growth metrics for November 2024',
                'priority': 'medium',
                'args': {
                    'report_type': 'revenue_analysis',
                    'period': 'november_2024',
                    'include_forecasts': True
                }
            },
            {
                'type': 'automation',
                'title': 'Automate dashboard updates',
                'description': 'Set up automated updates for executive dashboard with real-time KPIs',
                'priority': 'medium',
                'args': {
                    'dashboard': 'executive_kpis',
                    'refresh_rate': '15_minutes',
                    'metrics': ['revenue', 'customer_acquisition', 'churn_rate']
                }
            }
        ]
    }
}

@demo_app.route('/demo')
def demo_home():
    """Demo application home page"""
    return render_template('demo/index.html', scenarios=DEMO_SCENARIOS)

@demo_app.route('/demo/scenario/<scenario_id>')
def demo_scenario(scenario_id):
    """Display specific demo scenario"""
    scenario = DEMO_SCENARIOS.get(scenario_id)
    if not scenario:
        return redirect(url_for('demo_home'))
    
    return render_template('demo/scenario.html', 
                         scenario=scenario, 
                         scenario_id=scenario_id)

@demo_app.route('/demo/api/submit_task', methods=['POST'])
def demo_submit_task():
    """Demo task submission with enhanced response"""
    try:
        data = request.get_json()
        
        # Add demo metadata
        data['demo_mode'] = True
        data['submitted_at'] = datetime.utcnow().isoformat()
        
        # Submit to actual task endpoint
        with demo_app.test_client() as client:
            response = client.post('/task', 
                                 data=json.dumps(data),
                                 content_type='application/json')
            
            if response.status_code == 201:
                result = response.get_json()
                
                # Enhance with demo-specific information
                demo_result = {
                    **result,
                    'demo_info': {
                        'processing_time': f"{len(data.get('title', '')) * 0.1:.2f}s",
                        'confidence_score': 0.92,
                        'department_load': {
                            'communications': '23%',
                            'analysis': '45%',
                            'coordination': '31%',
                            'automation': '18%'
                        }
                    }
                }
                
                return jsonify(demo_result), 201
            else:
                return response.get_json(), response.status_code
                
    except Exception as e:
        return jsonify({
            'status': 'error',
            'error': str(e),
            'demo_mode': True
        }), 500

@demo_app.route('/demo/api/system_status')
def demo_system_status():
    """Get demo system status"""
    with demo_app.app_context():
        # Get real data
        task_count = Task.query.count()
        agent_count = Agent.query.count()
        
        # Enhanced demo status
        status = {
            'system_health': 'optimal',
            'uptime': '99.9%',
            'tasks_processed': task_count + 1847,  # Add demo padding
            'active_agents': agent_count + 3,
            'avg_response_time': '0.23s',
            'success_rate': '98.7%',
            'current_load': {
                'cpu': '23%',
                'memory': '45%',
                'network': '12%'
            },
            'recent_activity': [
                {
                    'time': '2 minutes ago',
                    'event': 'Email campaign sent to 1,200 customers',
                    'status': 'completed'
                },
                {
                    'time': '5 minutes ago',
                    'event': 'Sales data analysis completed',
                    'status': 'completed'
                },
                {
                    'time': '8 minutes ago',
                    'event': 'Customer support ticket routed',
                    'status': 'in_progress'
                }
            ]
        }
        
        return jsonify(status)

@demo_app.route('/demo/api/analytics')
def demo_analytics():
    """Get demo analytics data"""
    # Generate realistic demo analytics
    analytics = {
        'task_distribution': {
            'communications': 35,
            'analysis': 28,
            'coordination': 22,
            'automation': 15
        },
        'performance_metrics': {
            'avg_completion_time': '2.3 minutes',
            'success_rate': 98.7,
            'user_satisfaction': 4.6,
            'cost_savings': '$12,450/month'
        },
        'trend_data': {
            'labels': ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun'],
            'tasks_completed': [45, 52, 48, 61, 55, 42, 38],
            'response_times': [2.1, 1.9, 2.3, 2.0, 1.8, 2.2, 2.4]
        },
        'department_efficiency': {
            'communications': 94.5,
            'analysis': 87.2,
            'coordination': 91.8,
            'automation': 96.1
        }
    }
    
    return jsonify(analytics)

@demo_app.route('/demo/reset')
def demo_reset():
    """Reset demo data"""
    # In a real implementation, this would reset demo-specific data
    # For now, just return success
    return jsonify({
        'status': 'success',
        'message': 'Demo data has been reset',
        'timestamp': datetime.utcnow().isoformat()
    })

# Error handlers for demo
@demo_app.errorhandler(404)
def demo_not_found(error):
    return render_template('demo/404.html'), 404

@demo_app.errorhandler(500)
def demo_server_error(error):
    return render_template('demo/500.html'), 500

if __name__ == '__main__':
    print("🚀 Starting SwarmDirector Interactive Demo")
    print("=" * 50)
    print("📱 Demo will be available at: http://localhost:5000/demo")
    print("🔍 API Status: http://localhost:5000/demo/api/system_status")
    print("📊 Analytics: http://localhost:5000/demo/api/analytics")
    print("=" * 50)
    
    demo_app.run(debug=True, port=5000) 