from flask import Blueprint

# Create API v1 blueprint
api_v1_bp = Blueprint('api_v1', __name__, url_prefix='/api/v1')

def register_v1_blueprints(app):
    """Register all v1 blueprints."""
    # Import here to avoid circular imports
    from .auth import auth_bp
    from .users import users_bp
    from .portfolios import portfolio_bp
    from .research import research_bp
    
    # Register nested blueprints
    api_v1_bp.register_blueprint(auth_bp)
    api_v1_bp.register_blueprint(users_bp)
    api_v1_bp.register_blueprint(portfolio_bp)
    api_v1_bp.register_blueprint(research_bp)
    
    # Register the main API blueprint
    app.register_blueprint(api_v1_bp)
    app.register_blueprint(portfolio_bp) 