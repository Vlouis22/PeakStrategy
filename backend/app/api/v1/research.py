# app/routes/portfolio.py
from flask import Blueprint, request, jsonify
from app.services.firebase_service import FirebaseService
from app.services.stock_research_service import StockResearchService
from datetime import datetime

research_bp = Blueprint('research', __name__, url_prefix='/research')

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


@research_bp.route('/stock/<ticker>', methods=['GET'])
def get_stock_research(ticker):
    """Get comprehensive stock research data for a given ticker"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        # Validate ticker parameter
        if not ticker or not isinstance(ticker, str):
            return jsonify({'success': False, 'error': 'Valid ticker symbol required'}), 400
        
        ticker = ticker.upper().strip()
        
        # Create StockResearchService instance
        research_service = StockResearchService(ticker)
        
        # Get complete research data
        research_data = research_service.get_stock_info()
        
        # Add metadata
        result = {
            'success': True,
            'ticker': ticker,
            'timestamp': datetime.now().isoformat(),
            'data': research_data
        }
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error getting stock research for {ticker}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500
    