from flask import Blueprint, request, jsonify
from app.services.firebase_service import FirebaseService
from app.models.user import User
from app.utils.validators import validate_email, validate_password
import requests

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')

@auth_bp.route('/signup', methods=['POST'])
def signup():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')
    display_name = data.get('displayName', '').strip()

    # Input validation
    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400
    
    if not validate_email(email):
        return jsonify({'success': False, 'error': 'Invalid email format'}), 400
    
    is_valid, msg = validate_password(password)
    if not is_valid:
        return jsonify({'success': False, 'error': msg}), 400

    try:
        # Create user in Firebase Authentication
        auth = FirebaseService.get_auth()
        user_record = auth.create_user(
            email=email,
            password=password,
            display_name=display_name
        )

        # Create user in Firestore (optional)
        User.create(user_record.uid, email, display_name)

        # Generate custom token for client
        custom_token = auth.create_custom_token(user_record.uid)

        return jsonify({
            'success': True,
            'user': {
                'uid': user_record.uid,
                'email': user_record.email,
                'displayName': display_name
            },
            'token': custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token
        }), 201

    except auth.EmailAlreadyExistsError:
        return jsonify({'success': False, 'error': 'Email already exists'}), 400
    except auth.WeakPasswordError:
        return jsonify({'success': False, 'error': 'Password is too weak'}), 400
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email', '').strip()
    password = data.get('password', '')

    if not email or not password:
        return jsonify({'success': False, 'error': 'Email and password are required'}), 400

    # We'll use the Firebase REST API for password authentication
    # Note: This requires the Firebase Web API key (not the admin key)
    # We'll store it in environment variables as FIREBASE_WEB_API_KEY
    import os
    FIREBASE_WEB_API_KEY = os.getenv('FIREBASE_WEB_API_KEY')
    
    if not FIREBASE_WEB_API_KEY:
        return jsonify({'success': False, 'error': 'Server configuration error'}), 500

    try:
        response = requests.post(
            f'https://identitytoolkit.googleapis.com/v1/accounts:signInWithPassword?key={FIREBASE_WEB_API_KEY}',
            json={
                'email': email,
                'password': password,
                'returnSecureToken': True
            }
        )
        result = response.json()

        if 'error' in result:
            error_msg = result['error']['message'].replace('_', ' ').capitalize()
            return jsonify({'success': False, 'error': error_msg}), 401

        # Get user uid from the result
        uid = result['localId']
        
        # Generate a custom token for the client
        auth = FirebaseService.get_auth()
        custom_token = auth.create_custom_token(uid)

        # Get user from Firestore (optional)
        user = User.get(uid)
        user_data = user.to_dict() if user else {'uid': uid, 'email': email}

        return jsonify({
            'success': True,
            'user': user_data,
            'token': custom_token.decode('utf-8') if isinstance(custom_token, bytes) else custom_token,
            'idToken': result.get('idToken')
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@auth_bp.route('/user/<uid>', methods=['GET'])
def get_user(uid):
    try:
        auth = FirebaseService.get_auth()
        user_record = auth.get_user(uid)
        
        user = User.get(uid)
        user_data = user.to_dict() if user else {
            'uid': user_record.uid,
            'email': user_record.email,
            'displayName': user_record.display_name
        }

        return jsonify({'success': True, 'user': user_data}), 200
    except auth.UserNotFoundError:
        return jsonify({'success': False, 'error': 'User not found'}), 404
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500