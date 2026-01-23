from flask import Blueprint, request, jsonify, current_app
from ...services.auth_service import AuthService
from ...utils.exceptions import AuthError, ValidationError

# Create blueprint
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    """User registration endpoint."""
    try:
        auth_service = AuthService()
        result = auth_service.signup(request.get_json())
        
        current_app.logger.info(f"New user created: {result['user']['email']}")
        
        return jsonify({
            'success': True,
            'data': result
        }), 201
        
    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.errors
        }), 400
        
    except AuthError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 400
        
    except Exception as e:
        current_app.logger.error(f"Signup error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """User login endpoint."""
    try:
        auth_service = AuthService()
        result = auth_service.login(request.get_json())
        
        return jsonify({
            'success': True,
            'data': result
        }), 200
        
    except AuthError as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 401
        
    except Exception as e:
        current_app.logger.error(f"Login error: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Internal server error'
        }), 500