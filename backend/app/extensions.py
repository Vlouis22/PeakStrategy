"""Centralized extension instances."""
from flask_pyjwt import AuthManager
from .services.firebase_service import FirebaseService

# Initialize extension instances
db = None  # For future database
jwt = AuthManager()  # For JWT token management
firebase_service = FirebaseService()