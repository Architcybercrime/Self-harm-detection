"""
WSGI entry point for Gunicorn deployment on Render/Vercel.
Handles production server setup with proper configuration.
"""

import os
from app import app, socketio

if __name__ == "__main__":
    # Get port from environment (Render/Vercel sets this)
    port = int(os.getenv('PORT', 5000))
    
    # Only use debug in development
    debug = os.getenv('ENVIRONMENT', 'production') == 'development'
    
    # Run with SocketIO support
    socketio.run(
        app,
        host='0.0.0.0',
        port=port,
        debug=debug,
        use_reloader=False,  # Disable for production
        log_output=True
    )
