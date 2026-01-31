from unittest import result
from flask import Blueprint, request, jsonify
from datetime import datetime
from app.services.firebase_service import FirebaseService
from app.services.portfolio_builder import get_all_hedge_funds, get_company_holdings

portfoliobuilder_bp = Blueprint('portfoliobuilder', __name__, url_prefix='/portfolio-builder')


def verify_token():
    """Verify Firebase ID token from Authorization header"""
    auth_header = request.headers.get('Authorization')
    if not auth_header or not auth_header.startswith('Bearer '):
        return None
    try:
        token = auth_header.split('Bearer ')[1]
        auth = FirebaseService.get_auth()
        decoded_token = auth.verify_id_token(token)
        return decoded_token['uid']
    except Exception as e:
        print(f"Token verification error: {e}")
        return None


@portfoliobuilder_bp.route('/hedge-funds', methods=['GET'])
def get_hedge_funds():
    """Return all hedge funds in the registry"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        hedge_funds = get_all_hedge_funds()
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': hedge_funds
        }
        return jsonify(result), 200
    except Exception as e:
        print(f"Error getting hedge funds: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    
@portfoliobuilder_bp.route('/analyze', methods=['POST'])
def build_portfolio():
    """Return all hedge funds in the registry"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    data = request.get_json()

    try:
        data = get_company_holdings(data.get("companies", ""))
        result = {
            'success': True,
            'timestamp': datetime.now().isoformat(),
            'data': data
        }
        return jsonify(result), 200
    except Exception as e:
        print(f"Error creating new portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500