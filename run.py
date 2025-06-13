#!/usr/bin/env python3
"""
SwarmDirector Application Launcher

This script provides an easy way to run the SwarmDirector application
with proper Python path configuration.
"""

import os
import sys
from pathlib import Path

# Add the src directory to Python path
project_root = Path(__file__).parent
src_path = project_root / "src"
sys.path.insert(0, str(src_path))

# Now import and run the application
from swarm_director.app import create_app

def main():
    """Main entry point for the application."""
    print("🚀 Starting SwarmDirector...")
    print("=" * 50)
    
    # Create the Flask application
    app = create_app()
    
    # Get configuration from environment or use defaults
    host = os.environ.get('FLASK_HOST', '127.0.0.1')
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() in ['true', '1', 'yes']
    
    print(f"📱 Application will be available at: http://{host}:{port}")
    print(f"🔍 Debug mode: {'Enabled' if debug else 'Disabled'}")
    print(f"🗄️ Database: {app.config.get('SQLALCHEMY_DATABASE_URI', 'Not configured')}")
    print("=" * 50)
    print("📊 Available endpoints:")
    print("  • Main Dashboard: http://localhost:5000/dashboard")
    print("  • API Health: http://localhost:5000/health")
    print("  • Demo Interface: http://localhost:5000/demo")
    print("  • API Documentation: See docs/api/")
    print("=" * 50)
    
    try:
        # Check if SocketIO is available and use it, otherwise fall back to regular Flask
        socketio = app.extensions.get('socketio')
        if socketio:
            print("🔌 WebSocket support enabled")
            print("  • WebSocket endpoint: ws://localhost:5000/socket.io/")
            print("  • WebSocket status: http://localhost:5000/api/websocket/status")
            print("=" * 50)
            # Run with SocketIO support
            socketio.run(app, host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
        else:
            print("⚠️  WebSocket support not available, running without streaming")
            print("=" * 50)
            # Run regular Flask application
            app.run(host=host, port=port, debug=debug, allow_unsafe_werkzeug=True)
    except KeyboardInterrupt:
        print("\n👋 SwarmDirector stopped by user")
    except Exception as e:
        print(f"❌ Error starting SwarmDirector: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
