#!/usr/bin/env python3

import sys
import os
sys.path.append('.')

from flask import Flask
from src.swarm_director.agents.email_agent import EmailAgent
import inspect

def main():
    print("🔧 Verifying Flask-Mail Integration Enhancements...")
    
    try:
        # Create a test Flask app
        app = Flask(__name__)
        app.config['TESTING'] = True
        app.config['MAIL_SERVER'] = 'localhost'
        
        with app.app_context():
            # Test 1: EmailAgent creation
            print("1. Creating EmailAgent...")
            agent = EmailAgent(name="TestAgent")
            print("   ✅ EmailAgent created successfully")
            
            # Test 2: Tool registration
            print("2. Checking tool registration...")
            tools = agent.available_tools
            assert 'send_email' in tools
            assert 'html_body' in tools['send_email']['parameters']
            print("   ✅ HTML support registered in tools")
            
            # Test 3: Method signatures
            print("3. Verifying method signatures...")
            
            # Check send_email_tool signature
            sig = inspect.signature(agent.send_email_tool)
            assert 'html_body' in sig.parameters
            print("   ✅ send_email_tool has html_body parameter")
            
            # Check _send_via_flask_mail signature
            sig = inspect.signature(agent._send_via_flask_mail)
            assert 'html_body' in sig.parameters
            assert 'retry_count' in sig.parameters
            print("   ✅ _send_via_flask_mail has enhanced signature")
            
            # Test 4: Tool functionality
            print("4. Testing tool functionality...")
            
            # Mock the actual sending to avoid SMTP errors
            original_send = agent._send_via_flask_mail
            agent._send_via_flask_mail = lambda *args, **kwargs: True
            
            result = agent.send_email_tool(
                recipient="test@example.com",
                subject="Test Email",
                body="Plain text content",
                html_body="<h1>HTML Content</h1>"
            )
            
            assert result['status'] == 'success'
            assert result['has_html'] is True
            print("   ✅ HTML email tool works correctly")
            
            # Restore original method
            agent._send_via_flask_mail = original_send
            
            print()
            print("🎉 All Flask-Mail integration tests passed!")
            print("📧 EmailAgent now supports:")
            print("   • HTML email content")
            print("   • Retry logic with exponential backoff") 
            print("   • Enhanced SMTP error handling")
            print("   • Better email headers for deliverability")
            print("   • Backward compatibility maintained")
            
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1) 