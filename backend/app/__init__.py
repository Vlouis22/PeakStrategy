from flask import Flask, jsonify
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os

def create_app(config_name: str = None) -> Flask:
    """Application factory."""
    app = Flask(__name__)
    
    # Load configuration
    from .config import get_config
    config = get_config(config_name)
    app.config.from_object(config)
    
    # ✅ Configure CORS FIRST, before any other imports
    CORS(app, 
         origins=["*"], 
         supports_credentials=True, 
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
         expose_headers=['Content-Type', 'Authorization'])
    
    # Configure logging
    _setup_logging(app)
    
    # Initialize extensions
    from .extensions import firebase_service
    firebase_service.init_app(app)
    
    # Register blueprints and routes (import here to avoid circular imports)
    from .api.v1.routes import register_v1_blueprints
    register_v1_blueprints(app)
    
    # Register error handlers
    from .api.errors import register_error_handlers
    register_error_handlers(app)
    
    # Add custom middleware
    from .middlewares.auth_middleware import AuthMiddleware
    app.wsgi_app = AuthMiddleware(app.wsgi_app)
    
    # Health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'PeakStrategy API',
            'environment': config_name or app.config['ENV']
        })
    
    return app

def _setup_logging(app: Flask) -> None:
    """Configure application logging."""
    if not app.debug:
        # Create logs directory if it doesn't exist
        if not os.path.exists('logs'):
            os.makedirs('logs')
        
        # Production logging
        file_handler = RotatingFileHandler(
            'logs/peakstrategy.log',
            maxBytes=10485760,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        app.logger.addHandler(file_handler)
        app.logger.setLevel(app.config.get('LOG_LEVEL', 'INFO'))