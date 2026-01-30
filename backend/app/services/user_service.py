from typing import Dict, Any, List, Optional
from ..utils.exceptions import (
    AuthError, 
    ValidationError, 
    ResourceNotFoundError, 
    PermissionDeniedError,
    ExternalServiceError
)
from .firebase_service import FirebaseService
from google.cloud.firestore import SERVER_TIMESTAMP


class UserService:
    """User management service."""
    
    def __init__(self):
        try:
            self.firebase = FirebaseService
            self.db = self.firebase.get_firestore()
            self.auth = self.firebase.get_auth()
        except Exception as e:
            raise RuntimeError(f"Failed to initialize UserService: {str(e)}")
    
    def get_user_profile(self, user_id: str) -> Dict[str, Any]:
        """Get full user profile (private, for the user themselves)."""
        try:
            # Get Firebase user record
            user_record = self.auth.get_user(user_id)
            
            # Get Firestore user document
            user_doc = self.db.collection('users').document(user_id).get()
            
            if not user_doc.exists:
                # Create basic profile if it doesn't exist
                profile_data = {
                    'email': user_record.email,
                    'display_name': user_record.display_name or '',
                    'created_at': SERVER_TIMESTAMP,
                    'updated_at': SERVER_TIMESTAMP,
                    'status': 'active'
                }
                self.db.collection('users').document(user_id).set(profile_data)
                user_data = profile_data
            else:
                user_data = user_doc.to_dict()
            
            # Combine Firebase and Firestore data
            profile = {
                'uid': user_id,
                'email': user_record.email,
                'email_verified': user_record.email_verified,
                'display_name': user_record.display_name or user_data.get('display_name', ''),
                'created_at': user_data.get('created_at'),
                'last_login_at': user_data.get('last_login_at'),
                'status': user_data.get('status', 'active'),
                'preferences': user_data.get('preferences', {})
            }
            
            return profile
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise ResourceNotFoundError("User", user_id)
            raise ExternalServiceError("Firebase", str(e))
            
    def create_user_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """Create initial user profile."""
        try:
            # Get Firebase user record
            user_record = self.auth.get_user(user_id)
            
            # Default profile data
            profile_data = {
                'email': user_record.email,
                'display_name': data.get('display_name') or user_record.display_name or user_record.email.split('@')[0],
                'created_at': SERVER_TIMESTAMP,
                'updated_at': SERVER_TIMESTAMP,
                'status': 'active',
                'preferences': data.get('preferences', {})
            }
            
            # Create the document
            self.db.collection('users').document(user_id).set(profile_data)
            
            # Return the created profile
            profile_data['uid'] = user_id
            return profile_data
            
        except Exception as e:
            raise ExternalServiceError("Firebase", str(e))
    
    def update_user_profile(self, user_id: str, data: Dict[str, Any]) -> Dict[str, Any]:
        updates = {}

        if 'displayName' in data:
            if not isinstance(data['displayName'], str) or not data['displayName'].strip():
                raise ValidationError(
                    {'displayName': 'Must be a non-empty string'},
                    'Invalid display name'
                )
            updates['display_name'] = data['displayName'].strip()

        if 'preferences' in data:
            updates['preferences'] = data['preferences']

        if not updates:
            raise ValidationError({}, "No valid fields provided for update")

        try:
            # Update Firebase Auth
            if 'display_name' in updates:
                self.auth.update_user(
                    user_id,
                    display_name=updates['display_name']
                )

            # Update Firestore
            updates['updated_at'] = SERVER_TIMESTAMP
            self.db.collection('users').document(user_id).update(updates)

            return self.get_user_profile(user_id)

        except Exception as e:
            raise ExternalServiceError("Firebase", str(e))
    
    def search_users(self, email: str = '', display_name: str = '', 
                    limit: int = 10, offset: int = 0) -> List[Dict[str, Any]]:
        """Search for users by email or display name."""
        try:
            query = self.db.collection('users')
            
            if email:
                # Note: Firestore doesn't support partial email search well
                # In production, consider using Algolia or ElasticSearch
                query = query.where('email', '>=', email).where('email', '<=', email + '\uf8ff')
            elif display_name:
                query = query.where('display_name', '>=', display_name).where('display_name', '<=', display_name + '\uf8ff')
            else:
                return []
            
            # Execute query
            results = query.limit(limit).offset(offset).get()
            
            users = []
            for doc in results:
                user_data = doc.to_dict()
                user_data['uid'] = doc.id
                # Remove sensitive data
                user_data.pop('email', None)  # Don't expose emails in search results
                users.append(user_data)
            
            return users
            
        except Exception as e:
            raise ExternalServiceError("Firebase Firestore", str(e))
    
    def get_public_profile(self, user_id: str) -> Dict[str, Any]:
        """Get public user profile (safe to share)."""
        try:
            # Get basic profile
            profile = self.get_user_profile(user_id)
            
            # Filter to only public fields
            public_profile = {
                'uid': profile['uid'],
                'display_name': profile['display_name'],
                'created_at': profile.get('created_at')
            }
            
            return public_profile
            
        except ResourceNotFoundError:
            raise
        except Exception as e:
            raise ExternalServiceError("Firebase", str(e))
    
    def update_last_login(self, user_id: str) -> None:
        """Update user's last login timestamp."""
        try:
            self.db.collection('users').document(user_id).update({
                'last_login_at': SERVER_TIMESTAMP
            })
        except Exception:
            # Non-critical, just log it
            import logging
            logging.warning(f"Failed to update last login for user: {user_id}")