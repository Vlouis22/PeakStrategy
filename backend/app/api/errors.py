from flask import jsonify
from werkzeug.exceptions import HTTPException
from ..utils.exceptions import AppError

def register_error_handlers(app):
    """
    Registers custom error handlers for the Flask application.
    """
    
    # Handle our custom AppError exceptions
    @app.errorhandler(AppError)
    def handle_app_error(error):
        return jsonify(error.to_dict()), error.status_code
    
    # Handle HTTP exceptions
    @app.errorhandler(HTTPException)
    def handle_http_exception(error):
        return jsonify({
            'success': False,
            'error': error.name,
            'message': error.description,
            'code': error.code
        }), error.code

    # Handle 404 specifically (not always caught by HTTPException)
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            'success': False,
            'error': 'Not Found',
            'message': 'The requested resource was not found.',
            'code': 404
        }), 404

    # Handle 405 specifically
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 'Method Not Allowed',
            'message': 'This method is not allowed for the requested endpoint.',
            'code': 405
        }), 405

    # Catch-all for unexpected errors
    @app.errorhandler(Exception)
    def handle_general_exception(error):
        # Log the actual error for debugging
        app.logger.error(f"Unhandled exception: {str(error)}", exc_info=True)
        
        # In production, don't expose internal error details
        if app.config.get('DEBUG', False):
            message = str(error)
        else:
            message = 'An internal server error occurred.'
            
        return jsonify({
            'success': False,
            'error': 'Internal Server Error',
            'message': message,
            'code': 500
        }), 500