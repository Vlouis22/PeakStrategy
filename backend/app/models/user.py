from app.services.firebase_service import FirebaseService

class User:
    def __init__(self, uid, email, display_name):
        self.uid = uid
        self.email = email
        self.display_name = display_name
    
    @staticmethod
    def create(uid, email, display_name):
        # Create user in Firestore (optional)
        firestore = FirebaseService.get_firestore()
        user_data = {
            'email': email,
            'displayName': display_name,
            'createdAt': firestore.SERVER_TIMESTAMP
        }
        firestore.collection('users').document(uid).set(user_data)
        return User(uid, email, display_name)
    
    @staticmethod
    def get(uid):
        firestore = FirebaseService.get_firestore()
        doc = firestore.collection('users').document(uid).get()
        if doc.exists:
            data = doc.to_dict()
            return User(uid, data.get('email'), data.get('displayName'))
        return None
    
    def to_dict(self):
        return {
            'uid': self.uid,
            'email': self.email,
            'displayName': self.display_name
        }