"""
Custom exceptions for PeakStrategy application.
"""

class AppError(Exception):
    """Base exception for all application errors."""
    def __init__(self, message, status_code=400, details=None):
        super().__init__(message)
        self.message = message
        self.status_code = status_code
        self.details = details

    def to_dict(self):
        """Convert exception to dictionary for JSON response."""
        error_dict = {
            'success': False,
            'error': self.message,
            'code': self.status_code
        }
        if self.details:
            error_dict['details'] = self.details
        return error_dict

class AuthError(AppError):
    """Authentication and authorization related errors."""
    def __init__(self, message="Authentication failed", details=None):
        super().__init__(message, status_code=401, details=details)

class ValidationError(AppError):
    """Input validation errors."""
    def __init__(self, errors, message="Validation failed"):
        super().__init__(message, status_code=400, details=errors)

class ResourceNotFoundError(AppError):
    """Resource not found errors."""
    def __init__(self, resource_type, resource_id):
        message = f"{resource_type} with id '{resource_id}' not found"
        super().__init__(message, status_code=404)

class DatabaseError(AppError):
    """Database operation errors."""
    def __init__(self, message="Database operation failed", details=None):
        super().__init__(message, status_code=500, details=details)

class RateLimitError(AppError):
    """Rate limiting errors."""
    def __init__(self, message="Rate limit exceeded"):
        super().__init__(message, status_code=429)

class ExternalServiceError(AppError):
    """External service (like Firebase) errors."""
    def __init__(self, service_name, message=None, details=None):
        if not message:
            message = f"Error communicating with {service_name}"
        super().__init__(message, status_code=502, details=details)

class PermissionDeniedError(AppError):
    """Permission/access denied errors."""
    def __init__(self, message="Permission denied"):
        super().__init__(message, status_code=403)