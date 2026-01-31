from flask import Blueprint, request, jsonify, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from ...services.user_service import UserService
from ...utils.exceptions import AuthError, ResourceNotFoundError, PermissionDeniedError
from ...middlewares.auth_middleware import auth_required
from django.core.exceptions import ValidationError

# Create blueprint
users_bp = Blueprint('users', __name__, url_prefix='/users')

# Rate limiting
limiter = Limiter(key_func=get_remote_address)

# Middleware to require authentication for all user endpoints
@users_bp.before_request
@auth_required
def require_auth():
    """Require authentication for all user endpoints."""
    pass

@users_bp.route('/profile', methods=['GET'])
def get_profile():
    """Get the current user's profile."""
    try:
        # Get user info from the request (set by auth middleware)
        user_id = request.user_id
        user_email = getattr(request, 'user_email', '')
        
        # Return profile from the already-verified token data
        # This avoids additional Firestore calls
        profile = {
            'uid': user_id,
            'email': user_email,
            'display_name': user_email.split('@')[0] if user_email else '',
            'status': 'active'
        }
        
        return jsonify({
            'success': True,
            'data': profile
        }), 200
        
    except Exception as e:
        current_app.logger.error(f"Error getting user profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to retrieve profile'
        }), 500

@users_bp.route('/profile', methods=['POST'])
@limiter.limit("10 per minute")
def create_profile():
    """Create a new user profile."""
    print("\n\nCreate profile endpoint hit\n\n")
    try:
        user_id = request.user_id
        data = request.get_json()
        
        user_service = UserService()
        created_profile = user_service.create_user_profile(user_id, data)
        
        current_app.logger.info(f"User profile created: {user_id}")
        
        return jsonify({
            'success': True,
            'data': created_profile,
            'message': 'Profile created successfully'
        }), 201
        
    except Exception as e:
        current_app.logger.error(f"Error creating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to create profile'
        }), 500
    

@users_bp.route('/profile', methods=['PUT'])
@limiter.limit("10 per minute")
def update_profile():
    try:
        user_id = request.user_id
        data = request.get_json(force=True) or {}

        if not data:
            return jsonify({
                'success': True,
                'message': 'No profile changes'
            }), 200

        user_service = UserService()
        print("\n\nStep 1: Updating user profile with data:", data, "\n\n")
        updated_profile = user_service.update_user_profile(user_id, data)

        current_app.logger.info(f"User profile updated: {user_id}")

        return jsonify({
            'success': True,
            'data': updated_profile,
            'message': 'Profile updated successfully'
        }), 200

    except ValidationError as e:
        return jsonify({
            'success': False,
            'error': 'Validation failed',
            'details': e.details
        }), 400

    except Exception as e:
        current_app.logger.error(f"Error updating profile: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Failed to update profile'
        }), 500

@users_bp.route('/search', methods=['GET'])
@limiter.limit("30 per minute")
def search_users():
    """Search for users (admin or specific use cases)."""
    try:
        # Extract query parameters
        email = request.args.get('email', '').strip()
        display_name = request.args.get('name', '').strip()
        limit = min(int(request.args.get('limit', 10)), 50)  # Max 50 results
        offset = int(request.args.get('offset', 0))
        
        if not email and not display_name:
            return jsonify({
                'success': False,
                'error': 'Please provide search criteria (email or name)'
            }), 400
        
        user_service = UserService()
        results = user_service.search_users(
            email=email,
            display_name=display_name,
            limit=limit,
            offset=offset
        )
        
        return jsonify({
            'success': True,
            'data': results,
            'pagination': {
                'limit': limit,
                'offset': offset,
                'total': len(results)
            }
        }), 200
        
    except PermissionDeniedError as e:
        raise e
        
    except Exception as e:
        current_app.logger.error(f"Error searching users: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Search failed'
        }), 500

@users_bp.route('/<user_id>', methods=['GET'])
def get_user_by_id(user_id):
    """Get a specific user's public profile (if allowed)."""
    try:
        user_service = UserService()
        profile = user_service.get_public_profile(user_id)
        
        return jsonify({
            'success': True,
            'data': profile
        }), 200
        
    except ResourceNotFoundError as e:
        raise e
        
    except Exception as e:
        current_app.logger.error(f"Error getting user by ID: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'User not found'
        }), 404

# Admin-only endpoints (commented out for now, enable when you add admin roles)
# @users_bp.route('/admin/users', methods=['GET'])
# @admin_required
# def list_all_users():
#     """List all users (admin only)."""
#     pass

# @users_bp.route('/admin/users/<user_id>/status', methods=['PUT'])
# @admin_required
# def update_user_status(user_id):
#     """Update user status (admin only)."""
#     pass