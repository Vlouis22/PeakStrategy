"""
Authentication middleware for PeakStrategy API.
Includes both WSGI middleware class and route decorator.
"""
import re
import logging
from functools import wraps
from flask import request, g, current_app

from ..utils.exceptions import AuthError
from ..services.firebase_service import FirebaseService

logger = logging.getLogger(__name__)

class AuthMiddleware:
    """
    WSGI middleware that processes ALL incoming requests.
    Checks authentication and adds user info to the WSGI environ.
    """
    
    def __init__(self, app):
        self.wrapped_app = app
        # Define public paths that don't require authentication
        self.public_paths = [
            r'^/$',                           # Root
            r'^/health$',                     # Health check
            r'^/api/v1/auth/login$',          # Login endpoint
            r'^/api/v1/auth/signup$',         # Signup endpoint
            r'^/api/v1/auth/.*$',             # Any other auth endpoints
            r'^/docs',                        # API documentation
            r'^/swagger',                     # Swagger UI
            r'^/favicon.ico$',                # Favicon
        ]
    
    def __call__(self, environ, start_response):
        """Process each incoming request."""
        # Check if this is a public path
        path = environ.get('PATH_INFO', '')
        
        is_public = False
        for pattern in self.public_paths:
            if re.match(pattern, path):
                is_public = True
                break
        
        # If it's not public, check for authentication token
        if not is_public:
            auth_header = environ.get('HTTP_AUTHORIZATION', '')
            
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header[7:]  # Remove "Bearer " prefix
                
                try:
                    # Verify the Firebase token
                    from ..services.firebase_service import FirebaseService
                    decoded_token = FirebaseService.verify_id_token(token)
                    if decoded_token:
                        # Add user info to the WSGI environment
                        environ['USER_ID'] = decoded_token['uid']
                        environ['USER_EMAIL'] = decoded_token.get('email', '')
                        environ['USER_AUTHENTICATED'] = 'true'
                    else:
                        environ['USER_AUTHENTICATED'] = 'false'
                except Exception as e:
                    # Use the logger, not current_app
                    logger.warning(f"Token verification failed: {str(e)}")
                    environ['USER_AUTHENTICATED'] = 'false'
            else:
                environ['USER_AUTHENTICATED'] = 'false'
        else:
            environ['USER_AUTHENTICATED'] = 'false'
        
        # Pass the request to the Flask app
        return self.wrapped_app(environ, start_response)

def auth_required(f):
    """
    Decorator to require authentication for a route.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # ✅ SKIP AUTH for OPTIONS requests (preflight)
        if request.method == 'OPTIONS':
            return f(*args, **kwargs)
        
        # Get token from header
        auth_header = request.headers.get('Authorization', '')
        
        if not auth_header.startswith('Bearer '):
            from ..utils.exceptions import AuthError
            raise AuthError("Authentication required")
        
        token = auth_header[7:]
        
        # Verify token
        from ..services.firebase_service import FirebaseService
        decoded_token = FirebaseService.verify_id_token(token)
        
        if not decoded_token:
            from ..utils.exceptions import AuthError
            raise AuthError("Invalid or expired token")
        
        # Add user info to request
        request.user_id = decoded_token['uid']
        request.user_email = decoded_token.get('email', '')
        
        return f(*args, **kwargs)
    return decorated_function

def get_current_user():
    """Helper function to get current user from request context."""
    if hasattr(request, 'user_id') and request.user_id:
        return {
            'uid': request.user_id,
            'email': request.user_email
        }
    return None