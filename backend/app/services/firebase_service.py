import firebase_admin
from firebase_admin import auth, credentials, firestore, exceptions
from typing import Optional, Dict, Any

class FirebaseService:
    """Firebase service abstraction layer."""
    
    _initialized = False
    _auth = None
    _firestore = None
    
    @classmethod
    def init_app(cls, app):
        """Initialize Firebase with app configuration."""
        if not cls._initialized:
            # Access the config properly - check both possible locations
            firebase_config = app.config.get('FIREBASE_CONFIG') or app.config.get('FIREBASE_SERVICE_ACCOUNT')
            
            if not firebase_config:
                raise ValueError("Firebase configuration not found in app config")
            
            print(f"🔥 Initializing Firebase with config from: {app.config.get('FIREBASE_SERVICE_ACCOUNT_PATH', 'config')}")
            
            cred = credentials.Certificate(firebase_config)
            firebase_admin.initialize_app(cred)
            cls._auth = auth
            cls._firestore = firestore.client()
            cls._initialized = True
            print(f"✅ Firebase initialized successfully")
    
    @classmethod
    def get_auth(cls):
        if not cls._initialized:
            raise RuntimeError("Firebase not initialized. Call init_app first.")
        return cls._auth
    
    @classmethod
    def get_firestore(cls):
        if not cls._initialized:
            raise RuntimeError("Firebase not initialized. Call init_app first.")
        return cls._firestore
    
    @classmethod
    def create_user(cls, email: str, password: str, **kwargs) -> Dict[str, Any]:
        """Create a new user in Firebase Auth."""
        try:
            # Ensure auth is initialized
            if cls._auth is None:
                raise RuntimeError("Firebase Auth not initialized")
                
            user_record = cls._auth.create_user(
                email=email,
                password=password,
                **kwargs
            )
            return {
                'uid': user_record.uid,
                'email': user_record.email,
                'display_name': user_record.display_name or kwargs.get('display_name', '')
            }
        except exceptions.FirebaseError as e:
            from ..utils.exceptions import ValidationError
            raise ValidationError(
                {"firebase": [str(e)]},
                "Failed to create user in Firebase"
            )
    
    @classmethod
    def create_custom_token(cls, uid: str) -> str:
        """Create a custom token for client authentication."""
        if cls._auth is None:
            raise RuntimeError("Firebase Auth not initialized")
            
        custom_token = cls._auth.create_custom_token(uid)
        # Convert bytes to string if necessary
        if isinstance(custom_token, bytes):
            return custom_token.decode('utf-8')
        return custom_token
    
    @classmethod
    def verify_id_token(cls, token: str) -> Optional[Dict[str, Any]]:
        """Verify a Firebase ID token."""
        try:
            if cls._auth is None:
                return None
            return cls._auth.verify_id_token(token)
        except exceptions.FirebaseError:
            return None