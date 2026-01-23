from typing import Dict, Any
import firebase_admin.firestore as firestore
from ..utils.exceptions import ValidationError, ExternalServiceError
from .firebase_service import FirebaseService
import os
import requests


class AuthService:
    """Authentication service containing business logic."""
    
    def __init__(self):
        # Access the class directly, not an instance
        self.firebase = FirebaseService
        self.firebase_web_api_key = os.getenv('VITE_FIREBASE_API_KEY') or os.getenv('FIREBASE_WEB_API_KEY')

    
    def signup(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user signup."""
        try:
            email = request_data['email']
            password = request_data['password']
            display_name = request_data.get('display_name', '').strip()
            
            # Validate display name
            if not display_name:
                raise ValidationError(
                    {"display_name": ["Display name is required"]},
                    "Display name must be provided"
                )
            
            if len(display_name) < 2:
                raise ValidationError(
                    {"display_name": ["Display name must be at least 2 characters"]},
                    "Display name too short"
                )
            
            # Create user in Firebase
            # Use the class method directly
            user_data = self.firebase.create_user(
                email=email,
                password=password,
                display_name=display_name
            )
            
            # Create user profile in Firestore
            self._create_user_profile(user_data['uid'], email, display_name)
            
            # Generate custom token
            custom_token = self.firebase.create_custom_token(user_data['uid'])
            
            # Ensure token is string, not bytes
            token_str = custom_token
            if isinstance(custom_token, bytes):
                token_str = custom_token.decode('utf-8')
            
            return {
                'user': user_data,
                'token': token_str
            }
            
        except Exception as e:
            # Convert Firebase errors
            error_str = str(e).lower()
            if "email already exists" in error_str:
                raise ValidationError(
                    {"email": ["This email is already registered"]},
                    "Email already in use"
                )
            elif "weak password" in error_str:
                raise ValidationError(
                    {"password": ["Password must be at least 8 characters with uppercase, lowercase, and numbers"]},
                    "Password too weak"
                )
            else:
                raise ExternalServiceError("Firebase", str(e))
    
    def login(self, request_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle user login."""
        try:
            email = request_data['email']
            password = request_data['password']
            
            if not self.firebase_web_api_key:
                raise ExternalServiceError("Firebase", "Server configuration error: Missing Firebase Web API key")
            
            # Use Firebase REST API for password authentication
            response = requests.post(
                f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={self.firebase_web_api_key}',
                json={
                    'email': email,
                    'password': password,
                    'returnSecureToken': True
                },
                timeout=10
            )
            result = response.json()
            
            if 'error' in result:
                error_msg = result['error']['message'].replace('_', ' ').capitalize()
                if result['error']['message'] == 'EMAIL_NOT_FOUND':
                    raise ValidationError(
                        {"email": ["No account found with this email"]},
                        "Email not found"
                    )
                elif result['error']['message'] == 'INVALID_PASSWORD':
                    raise ValidationError(
                        {"password": ["Incorrect password"]},
                        "Invalid password"
                    )
                elif result['error']['message'] == 'USER_DISABLED':
                    raise ValidationError(
                        {"email": ["This account has been disabled"]},
                        "Account disabled"
                    )
                else:
                    raise ValidationError(
                        {"general": [error_msg]},
                        error_msg
                    )
            
            # Get user uid from the result
            uid = result['localId']
            
            # Generate a custom token for the client
            custom_token = self.firebase.create_custom_token(uid)
            
            # Get user from Firestore
            user_profile = self._get_user_profile(uid)
            
            user_data = user_profile or {
                'uid': uid,
                'email': email,
                'display_name': result.get('displayName', '')
            }
            
            return {
                'user': user_data,
                'token': custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token,
                'idToken': result.get('idToken'),
                'refreshToken': result.get('refreshToken')
            }
        
        except ValidationError:
            # Re-raise validation errors
            raise
        except Exception as e:
            raise ExternalServiceError("Firebase", str(e))

    def _get_user_profile(self, uid: str) -> Dict[str, Any]:
        """Get user profile from Firestore."""
        try:
            db = self.firebase.get_firestore()
            doc_ref = db.collection('users').document(uid)
            doc = doc_ref.get()
            
            if doc.exists:
                profile_data = doc.to_dict()
                profile_data['uid'] = uid
                return profile_data
            return None
        except Exception as e:
            import logging
            logging.error(f"Failed to get user profile for {uid}: {str(e)}")
            return None
        
    def _create_user_profile(self, uid: str, email: str, display_name: str) -> None:
        """Create user profile in Firestore."""
        try:
            db = self.firebase.get_firestore()
            profile_data = {
                'email': email,
                'display_name': display_name,
                'created_at': firestore.SERVER_TIMESTAMP,
                'updated_at': firestore.SERVER_TIMESTAMP,
                'status': 'active'
            }
            
            db.collection('users').document(uid).set(profile_data)
        except Exception as e:
            # Log but don't fail signup
            import logging
            logging.error(f"Failed to create user profile for {uid}: {str(e)}")