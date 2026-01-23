# app/routes/portfolio.py
from flask import Blueprint, request, jsonify
from app.services.firebase_service import FirebaseService
from app.services.redis_service import RedisService
from firebase_admin import firestore
from datetime import datetime
import uuid
import logging
from app.services.stock_price_service import stock_price_service
from app.services.portfolio_projection_service import portfolio_projection_service
from app.services.portfolio_daily_change_service import PortfolioDailyChangeService
from app.services.cache_warming_service import cache_warming_service
from google.cloud.firestore_v1.base_query import FieldFilter

logger = logging.getLogger(__name__)

portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/v1/portfolios')
portfolio_bp.url_map = False

# Initialize Redis service
redis_service = RedisService.get_instance()

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
        logger.warning(f"Token verification error: {e}")
        return None

# ... keep your OPTIONS handlers as they are ...

@portfolio_bp.route('/', methods=['POST'])
def create_portfolio():
    """Create a new portfolio"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        # Validate required fields
        if 'name' not in data:
            return jsonify({'success': False, 'error': 'Portfolio name is required'}), 400
        
        portfolio_name = data['name'].strip()
        if not portfolio_name:
            return jsonify({'success': False, 'error': 'Portfolio name cannot be empty'}), 400
        
        holdings = data.get('holdings', [])
        if not isinstance(holdings, list):
            return jsonify({'success': False, 'error': 'Holdings must be an array'}), 400
        
        # Validate each holding
        for holding in holdings:
            if not all(k in holding for k in ['symbol', 'shares', 'averageCost']):
                return jsonify({'success': False, 'error': 'Each holding must have symbol, shares, and averageCost'}), 400
            
            try:
                shares = float(holding['shares'])
                avg_cost = float(holding['averageCost'])
                if shares <= 0 or avg_cost <= 0:
                    return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid number format in holdings'}), 400
        
        db = FirebaseService.get_firestore()
        
        # Generate portfolio ID
        portfolio_id = str(uuid.uuid4())
        current_time = datetime.utcnow()
        
        # Calculate total cost basis
        total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in holdings)
        
        portfolio_data = {
            'id': portfolio_id,
            'uid': uid,
            'name': portfolio_name,
            'holdings': holdings,
            'createdAt': current_time,
            'updatedAt': current_time,
            'totalCostBasis': total_cost_basis
        }
        
        # Store in Firestore
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_ref.set(portfolio_data)
        
        # Invalidate cache for this user's portfolio list and performance
        redis_service.invalidate_user_cache(uid)
        
        return jsonify({
            'success': True,
            'portfolio': portfolio_data,
            'message': 'Portfolio created successfully'
        }), 201
        
    except Exception as e:
        print(f"Error creating portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/', methods=['GET'])
def get_portfolios():
    """Get all portfolios for the authenticated user - WITH CACHING"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Generate cache key
    cache_key = redis_service.get_user_cache_key(uid, 'portfolios_list')
    
    # Try to get from cache
    cached_data = redis_service.get(cache_key)
    if cached_data:
        cached_data['meta'] = {'cached': True, 'timestamp': datetime.utcnow().isoformat()}
        print( "*" * 100, "THIS PORTFOLIO WAS RETRIEVED FROM CACHE ", "*" * 100)
        return jsonify(cached_data), 200
    
    try:
        db = FirebaseService.get_firestore()
        
        portfolios_ref = db.collection('portfolios')\
            .where(filter=FieldFilter("uid", "==", uid))\
            .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
        docs = portfolios_ref.stream()
        
        portfolios = []
        for doc in docs:
            portfolio_data = doc.to_dict()
            # Convert Firestore timestamps to ISO format
            for time_field in ['createdAt', 'updatedAt']:
                if time_field in portfolio_data:
                    portfolio_data[time_field] = portfolio_data[time_field].isoformat()
            portfolios.append(portfolio_data)
        
        result = {
            'success': True,
            'portfolios': portfolios,
            'count': len(portfolios),
            'meta': {'cached': False, 'timestamp': datetime.utcnow().isoformat()}
        }
        
        # Cache for 5 minutes (300 seconds)
        redis_service.set(cache_key, result, ttl=300)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error fetching portfolios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/<portfolio_id>', methods=['GET'])
def get_portfolio(portfolio_id):
    """Get a specific portfolio - WITH CACHING"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Generate cache key
    cache_key = redis_service.get_user_cache_key(uid, 'portfolio', portfolio_id)
    
    # Try to get from cache
    cached_data = redis_service.get(cache_key)
    if cached_data:
        cached_data['meta'] = {'cached': True, 'timestamp': datetime.utcnow().isoformat()}
        print( "*" * 100, "THIS SINGLE PORTFOLIO WAS RETRIEVED FROM CACHE ", "*" * 100)
        return jsonify(cached_data), 200
    
    try:
        db = FirebaseService.get_firestore()
        
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        portfolio_data = portfolio_doc.to_dict()
        
        # Check ownership
        if portfolio_data['uid'] != uid:
            return jsonify({'success': False, 'error': 'Unauthorized to access this portfolio'}), 403
        
        # Convert timestamps
        for time_field in ['createdAt', 'updatedAt']:
            if time_field in portfolio_data:
                portfolio_data[time_field] = portfolio_data[time_field].isoformat()
        
        result = {
            'success': True,
            'portfolio': portfolio_data,
            'meta': {'cached': False, 'timestamp': datetime.utcnow().isoformat()}
        }
        
        # Cache for 5 minutes
        redis_service.set(cache_key, result, ttl=300)
        
        return jsonify(result), 200
        
    except Exception as e:
        print(f"Error fetching portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/<portfolio_id>/holdings', methods=['PUT'])
def update_portfolio_holdings(portfolio_id):
    """Update all holdings in a portfolio"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Holdings data is required'}), 400
        
        holdings = data['portfolioData']['holdings']

        if not isinstance(holdings, list):
            return jsonify({'success': False, 'error': 'Holdings must be an array'}), 400
                
        # Validate holdings
        for holding in holdings:
            if not all(k in holding for k in ['symbol', 'shares', 'averageCost']):
                return jsonify({'success': False, 'error': 'Each holding must have symbol, shares, and averageCost'}), 400
            
            try:
                shares = float(holding['shares'])
                avg_cost = float(holding['averageCost'])
                if shares <= 0 or avg_cost <= 0:
                    return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
            except (ValueError, TypeError):
                return jsonify({'success': False, 'error': 'Invalid number format in holdings'}), 400
        
        db = FirebaseService.get_firestore()
        
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        portfolio_data = portfolio_doc.to_dict()
        
        # Check ownership
        if portfolio_data['uid'] != uid:
            return jsonify({'success': False, 'error': 'Unauthorized to update this portfolio'}), 403
        
        # Calculate total cost basis
        total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in holdings)
        
        # Update portfolio
        update_data = {
            'holdings': holdings,
            'updatedAt': datetime.utcnow(),
            'totalCostBasis': total_cost_basis, 
        }

        if 'name' in data['portfolioData']:
            new_name = data['portfolioData']['name'].strip()
            if new_name:
                update_data['name'] = new_name
        
        portfolio_ref.update(update_data)
        
        # Invalidate cache for this portfolio and user's portfolio list
        redis_service.invalidate_user_cache(uid)
        
        # Also invalidate specific portfolio cache
        portfolio_cache_key = redis_service.get_user_cache_key(uid, 'portfolio', portfolio_id)
        redis_service.delete(portfolio_cache_key)
        
        # Get updated portfolio
        updated_portfolio = portfolio_ref.get().to_dict()
        for time_field in ['createdAt', 'updatedAt']:
            if time_field in updated_portfolio:
                updated_portfolio[time_field] = updated_portfolio[time_field].isoformat()
        
        return jsonify({
            'success': True,
            'portfolio': updated_portfolio,
            'message': 'Portfolio holdings updated successfully'
        }), 200
        
    except Exception as e:
        print(f"Error updating portfolio holdings: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/<portfolio_id>/holdings', methods=['POST'])
def add_holding(portfolio_id):
    """Add a single holding to a portfolio"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'Holding data is required'}), 400
        
        # Validate holding
        if not all(k in data for k in ['symbol', 'shares', 'averageCost']):
            return jsonify({'success': False, 'error': 'Holding must have symbol, shares, and averageCost'}), 400
        
        try:
            shares = float(data['shares'])
            avg_cost = float(data['averageCost'])
            if shares <= 0 or avg_cost <= 0:
                return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
        except (ValueError, TypeError):
            return jsonify({'success': False, 'error': 'Invalid number format'}), 400
        
        db = FirebaseService.get_firestore()
        
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        portfolio_data = portfolio_doc.to_dict()
        
        # Check ownership
        if portfolio_data['uid'] != uid:
            return jsonify({'success': False, 'error': 'Unauthorized to modify this portfolio'}), 403
        
        # Create new holding object
        new_holding = {
            'symbol': data['symbol'].upper(),
            'name': data.get('name', data['symbol'].upper()),
            'shares': data['shares'],
            'averageCost': data['averageCost']
        }
        
        # Get current holdings and add new one
        current_holdings = portfolio_data.get('holdings', [])
        updated_holdings = current_holdings + [new_holding]
        
        # Calculate new total cost basis
        total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in updated_holdings)
        
        # Update portfolio
        update_data = {
            'holdings': updated_holdings,
            'updatedAt': datetime.utcnow(),
            'totalCostBasis': total_cost_basis
        }
        
        portfolio_ref.update(update_data)
        
        # Invalidate cache
        redis_service.invalidate_user_cache(uid)
        portfolio_cache_key = redis_service.get_user_cache_key(uid, 'portfolio', portfolio_id)
        redis_service.delete(portfolio_cache_key)
        
        # Get updated portfolio
        updated_portfolio = portfolio_ref.get().to_dict()
        for time_field in ['createdAt', 'updatedAt']:
            if time_field in updated_portfolio:
                updated_portfolio[time_field] = updated_portfolio[time_field].isoformat()
        
        return jsonify({
            'success': True,
            'portfolio': updated_portfolio,
            'holding': new_holding,
            'message': 'Holding added successfully'
        }), 201
        
    except Exception as e:
        print(f"Error adding holding: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/<portfolio_id>', methods=['DELETE'])
def delete_portfolio(portfolio_id):
    """Delete a portfolio"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        db = FirebaseService.get_firestore()
        
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        portfolio_data = portfolio_doc.to_dict()
        
        # Check ownership
        if portfolio_data['uid'] != uid:
            return jsonify({'success': False, 'error': 'Unauthorized to delete this portfolio'}), 403
        
        # Delete the portfolio
        portfolio_ref.delete()
        
        # Invalidate all cache for this user
        redis_service.invalidate_user_cache(uid)
        
        return jsonify({
            'success': True,
            'message': 'Portfolio deleted successfully'
        }), 200
        
    except Exception as e:
        print(f"Error deleting portfolio: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@portfolio_bp.route('/performance', methods=['GET'])
def get_all_portfolios_performance():
    """Get performance for all user portfolios - WITH CACHING"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Generate cache key
    cache_key = redis_service.get_user_cache_key(uid, 'all_performance')
    
    # Try to get from cache
    cached_data = redis_service.get(cache_key)
    if cached_data:
        cached_data['meta'] = {'cached': True, 'timestamp': datetime.utcnow().isoformat()}
        print( "*" * 100, "Portfolio PERFORMANCE WAS RETRIEVED FROM CACHE ", "*" * 100)
        return jsonify(cached_data), 200
    
    try:
        db = FirebaseService.get_firestore()
        
        # Get all portfolios for user
        portfolios_ref = db.collection('portfolios')\
            .where(filter=FieldFilter("uid", "==", uid))\
            .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
        portfolios_docs = portfolios_ref.stream()
        
        portfolios = []
        all_symbols = set()
        
        # First pass: collect all portfolios and symbols
        for doc in portfolios_docs:
            portfolio = doc.to_dict()
            portfolio['id'] = doc.id
            
            # Convert Firestore timestamps
            for field in ['createdAt', 'updatedAt']:
                if field in portfolio:
                    portfolio[field] = portfolio[field].isoformat()
            
            # Collect symbols from holdings
            holdings = portfolio.get('holdings', [])
            for holding in holdings:
                all_symbols.add(holding['symbol'].upper())
            
            portfolios.append(portfolio)
        
        # Get all prices at once - WITH PRICE CACHING (15 min TTL)
        symbols_list = list(all_symbols)
        price_cache_ttl = 900  # 15 minutes
        
        # Record symbols for cache warming (popular symbols tracking)
        if symbols_list:
            cache_warming_service.record_symbol_access(symbols_list)
            cache_warming_service.start_background_warming()
        
        # Try to get cached prices first
        cached_prices = {}
        for symbol in symbols_list:
            price_key = f"price:{symbol}"
            price_data = redis_service.get(price_key)
            if price_data and price_data.get('price') is not None:
                cached_prices[symbol] = price_data.get('price')
        
        # Determine which symbols need fresh prices
        symbols_to_fetch = [s for s in symbols_list if s not in cached_prices]
        
        if symbols_to_fetch:
            # Fetch only missing prices
            fresh_prices = stock_price_service.get_prices(symbols_to_fetch)
            
            # Cache ONLY valid prices with 15-minute TTL
            for symbol, price in fresh_prices.items():
                if price is not None and price > 0:
                    price_key = f"price:{symbol}"
                    redis_service.set(price_key, {'price': price, 'timestamp': datetime.utcnow().isoformat()}, ttl=price_cache_ttl)
            
            # Merge cached and fresh prices (only include valid fresh prices)
            valid_fresh_prices = {k: v for k, v in fresh_prices.items() if v is not None and v > 0}
            prices = {**cached_prices, **valid_fresh_prices}
        else:
            prices = cached_prices
        
        # Calculate performance for each portfolio
        portfolio_performances = []
        individual_prices = {}
        total_portfolio_cost = 0
        total_portfolio_value = 0
        
        for portfolio in portfolios:
            holdings = portfolio.get('holdings', [])
            portfolio_cost = 0
            portfolio_value = 0
            
            for holding in holdings:
                symbol = holding['symbol'].upper()
                shares = float(holding['shares'])
                avg_cost = float(holding['averageCost'])
                
                cost_basis = shares * avg_cost
                portfolio_cost += cost_basis
                
                current_price = prices.get(symbol)
                # Fallback to average cost if no price available (prevents $0 display)
                if current_price and current_price > 0:
                    portfolio_value += shares * current_price
                else:
                    # Use average cost as fallback - better than showing $0
                    portfolio_value += cost_basis

                if symbol not in individual_prices:
                    individual_prices[symbol] = current_price if current_price and current_price > 0 else avg_cost
            
            portfolio_change = portfolio_value - portfolio_cost
            portfolio_change_percent = (portfolio_change / portfolio_cost * 100) if portfolio_cost > 0 else 0
            
            total_portfolio_cost += portfolio_cost
            total_portfolio_value += portfolio_value
            
            portfolio_performances.append({
                'id': portfolio['id'],
                'name': portfolio.get('name', 'Unnamed Portfolio'),
                'holdings_count': len(holdings),
                'total_cost_basis': portfolio_cost,
                'current_value': portfolio_value,
                'total_change': portfolio_change,
                'total_change_percent': portfolio_change_percent,
                'created_at': portfolio.get('createdAt'),
                'updated_at': portfolio.get('updatedAt'),
            })

        # Calculate overall metrics
        overall_change = total_portfolio_value - total_portfolio_cost
        overall_change_percent = (overall_change / total_portfolio_cost * 100) if total_portfolio_cost > 0 else 0
        
        result = {
            'success': True,
            'portfolios': portfolio_performances,
            'overall': {
                'total_cost_basis': total_portfolio_cost,
                'current_value': total_portfolio_value,
                'total_change': overall_change,
                'total_change_percent': overall_change_percent
            },
            'individual_prices': individual_prices,
            'timestamp': datetime.now().isoformat(),
            'meta': {'cached': False, 'timestamp': datetime.utcnow().isoformat()}
        }
        
        # Cache performance result for 60 seconds
        redis_service.set(cache_key, result, ttl=60)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error fetching portfolio performances: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/<portfolio_id>/performance', methods=['GET'])
def get_portfolio_performance(portfolio_id):
    """Get performance metrics for a portfolio - WITH CACHING"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    # Generate cache key
    cache_key = redis_service.get_user_cache_key(uid, 'portfolio_performance', portfolio_id)
    
    # Try to get from cache
    cached_data = redis_service.get(cache_key)
    if cached_data:
        cached_data['meta'] = {'cached': True, 'timestamp': datetime.utcnow().isoformat()}
        return jsonify(cached_data), 200
    
    try:
        db = FirebaseService.get_firestore()
        
        # Get portfolio from Firestore
        portfolio_ref = db.collection('portfolios').document(portfolio_id)
        portfolio_doc = portfolio_ref.get()
        
        if not portfolio_doc.exists:
            return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
        portfolio = portfolio_doc.to_dict()
        
        # Check ownership
        if portfolio['uid'] != uid:
            return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
        holdings = portfolio.get('holdings', [])
        
        if not holdings:
            result = {
                'success': True,
                'portfolio_id': portfolio_id,
                'total_cost_basis': 0,
                'current_value': 0,
                'total_change': 0,
                'total_change_percent': 0,
                'holdings': [],
                'timestamp': datetime.now().isoformat(),
                'meta': {'cached': False}
            }
            return jsonify(result)
        
        # Extract unique symbols
        symbols = list(set([h['symbol'].upper() for h in holdings]))
        
        # Try to get cached prices first
        cached_prices = {}
        for symbol in symbols:
            price_key = f"price:{symbol}"
            price_data = redis_service.get(price_key)
            if price_data:
                cached_prices[symbol] = price_data.get('price')
        
        # Determine which symbols need fresh prices
        symbols_to_fetch = [s for s in symbols if s not in cached_prices]
        
        if symbols_to_fetch:
            # Fetch only missing prices
            fresh_prices = stock_price_service.get_prices(symbols_to_fetch)
            
            # Cache the new prices
            for symbol, price in fresh_prices.items():
                price_key = f"price:{symbol}"
                redis_service.set(price_key, {'price': price, 'timestamp': datetime.utcnow().isoformat()}, ttl=60)
            
            # Merge cached and fresh prices
            prices = {**cached_prices, **fresh_prices}
        else:
            prices = cached_prices
        
        # Calculate portfolio metrics
        total_cost_basis = 0
        current_value = 0
        holding_details = []
        
        for holding in holdings:
            symbol = holding['symbol'].upper()
            shares = float(holding['shares'])
            avg_cost = float(holding['averageCost'])
            
            cost_basis = shares * avg_cost
            total_cost_basis += cost_basis
            
            current_price = prices.get(symbol)
            if current_price:
                holding_value = shares * current_price
                holding_change = holding_value - cost_basis
                holding_change_percent = (holding_change / cost_basis * 100) if cost_basis > 0 else 0
            else:
                holding_value = 0
                holding_change = -cost_basis
                holding_change_percent = -100
            
            current_value += holding_value
            
            holding_details.append({
                'symbol': symbol,
                'name': holding.get('name', symbol),
                'shares': shares,
                'average_cost': avg_cost,
                'cost_basis': cost_basis,
                'current_price': current_price,
                'current_value': holding_value,
                'change': holding_change,
                'change_percent': holding_change_percent
            })
        
        # Calculate total portfolio metrics
        total_change = current_value - total_cost_basis
        total_change_percent = (total_change / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
        result = {
            'success': True,
            'portfolio_id': portfolio_id,
            'portfolio_name': portfolio.get('name', 'Unnamed Portfolio'),
            'total_cost_basis': total_cost_basis,
            'current_value': current_value,
            'total_change': total_change,
            'total_change_percent': total_change_percent,
            'holdings': holding_details,
            'timestamp': datetime.now().isoformat(),
            'meta': {'cached': False, 'timestamp': datetime.utcnow().isoformat()}
        }
        
        # Cache for 60 seconds
        redis_service.set(cache_key, result, ttl=60)
        
        return jsonify(result)
        
    except Exception as e:
        print(f"Error calculating portfolio performance: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/projection', methods=['POST'])
def get_portfolio_projection():
    """Get portfolio projection using Monte Carlo simulation - WITH CACHING"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    try:
        data = request.get_json()
        portfolio_selection = data.get('portfolio_selection', 'All')
        years = int(data.get('years', 10))
        
        # Generate cache key based on input parameters
        cache_input = {
            'uid': uid,
            'portfolio_selection': portfolio_selection,
            'years': years
        }
        cache_hash = redis_service.generate_hash(cache_input)
        cache_key = redis_service.get_user_cache_key(uid, 'projection', cache_hash)
        
        # Try to get from cache
        cached_data = redis_service.get(cache_key)
        if cached_data:
            cached_data['meta'] = {'cached': True, 'timestamp': datetime.utcnow().isoformat()}
            return jsonify(cached_data), 200
        
        db = FirebaseService.get_firestore()
        
        # Get user's portfolios
        portfolios_ref = db.collection('portfolios')\
            .where(filter=FieldFilter("uid", "==", uid))\
            .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
        portfolios_docs = portfolios_ref.stream()
        portfolios = []
        
        for doc in portfolios_docs:
            portfolio = doc.to_dict()
            portfolio['id'] = doc.id
            portfolios.append(portfolio)
        
        # Filter portfolios based on selection
        if portfolio_selection != 'All':
            portfolios = [p for p in portfolios if p.get('name') == portfolio_selection]
        
        if not portfolios:
            return jsonify({
                'success': False,
                'error': 'No portfolios found'
            }), 404
        
        # Combine holdings from selected portfolios
        combined_holdings = []
        for portfolio in portfolios:
            holdings = portfolio.get('holdings', [])
            # Merge holdings with same symbol
            for holding in holdings:
                symbol = holding['symbol'].upper()
                existing = next(
                    (h for h in combined_holdings if h['symbol'].upper() == symbol),
                    None
                )
                
                if existing:
                    # Merge shares
                    existing['shares'] = str(float(existing['shares']) + float(holding['shares']))
                else:
                    combined_holdings.append(holding.copy())
        
        # Get projection from service
        projection_result = portfolio_projection_service.get_portfolio_projection(
            holdings=combined_holdings,
            years=years,
            simulations=10000
        )
        
        if not projection_result['success']:
            return jsonify(projection_result), 400
        
        # Add metadata
        projection_result['meta'] = {'cached': False, 'timestamp': datetime.utcnow().isoformat()}
        
        # Cache for 5 minutes (projection is computationally expensive)
        redis_service.set(cache_key, projection_result, ttl=300)
        
        return jsonify(projection_result), 200
        
    except Exception as e:
        print(f"Error in portfolio projection: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@portfolio_bp.route('/projection', methods=['OPTIONS'])
def handle_options_projection():
    """Handle OPTIONS preflight request for projection route."""
    return '', 200

@portfolio_bp.route('/daily_change', methods=['GET'])
def get_portfolios_daily_change():
    """Get intraday daily change for ALL user portfolios combined"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401

    try:
        service = PortfolioDailyChangeService()
        result = service.get_all_portfolios_daily_change(uid)
        return jsonify(result), 200

    except Exception as e:
        print(f"Error fetching daily change: {e}")
        return jsonify({'success': False, 'error': 'Failed to compute daily change'}), 500

@portfolio_bp.route('/daily_change', methods=['OPTIONS'])
def handle_options_daily_change():
    return '', 200

# NEW: Add cache clearing endpoint (for development/testing)
@portfolio_bp.route('/clear_cache', methods=['POST'])
def clear_cache():
    """Clear all cache for the current user (development only)"""
    uid = verify_token()
    if not uid:
        return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
    redis_service.invalidate_user_cache(uid)
    return jsonify({'success': True, 'message': 'Cache cleared for user'}), 200

@portfolio_bp.route('/clear_cache', methods=['OPTIONS'])
def handle_options_clear_cache():
    return '', 200


# # app/routes/portfolio.py
# from flask import Blueprint, request, jsonify
# from app.services.firebase_service import FirebaseService
# from firebase_admin import firestore
# from datetime import datetime
# import uuid
# from app.services.stock_price_service import stock_price_service
# from app.services.portfolio_projection_service import portfolio_projection_service
# from app.services.portfolio_daily_change_service import PortfolioDailyChangeService

# portfolio_bp = Blueprint('portfolio', __name__, url_prefix='/api/v1/portfolios')
# portfolio_bp.url_map = False

# def verify_token():
#     """Verify Firebase ID token from Authorization header"""
#     auth_header = request.headers.get('Authorization')
#     if not auth_header or not auth_header.startswith('Bearer '):
#         return None
    
#     try:
#         token = auth_header.split('Bearer ')[1]
#         auth = FirebaseService.get_auth()
#         decoded_token = auth.verify_id_token(token)
#         return decoded_token['uid']
#     except Exception as e:
#         print(f"Token verification error: {e}")
#         return None

# # Add OPTIONS handlers for CORS preflight
# @portfolio_bp.route('/', methods=['OPTIONS'])
# def handle_options():
#     """Handle OPTIONS preflight request."""
#     return '', 200

# @portfolio_bp.route('/<portfolio_id>', methods=['OPTIONS'])
# def handle_options_with_id(portfolio_id):
#     """Handle OPTIONS preflight request for portfolio ID routes."""
#     return '', 200

# @portfolio_bp.route('/<portfolio_id>/holdings', methods=['OPTIONS'])
# def handle_options_holdings(portfolio_id):
#     """Handle OPTIONS preflight request for holdings routes."""
#     return '', 200

# @portfolio_bp.route('/performance', methods=['OPTIONS'])
# def handle_options_performance():
#     """Handle OPTIONS preflight request for performance routes."""
#     return '', 200

# @portfolio_bp.route('/<portfolio_id>/performance', methods=['OPTIONS'])
# def handle_options_portfolio_performance(portfolio_id):
#     """Handle OPTIONS preflight request for portfolio performance routes."""
#     return '', 200

# @portfolio_bp.route('/', methods=['POST'])
# def create_portfolio():
#     """Create a new portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'success': False, 'error': 'No data provided'}), 400
        
#         # Validate required fields
#         if 'name' not in data:
#             return jsonify({'success': False, 'error': 'Portfolio name is required'}), 400
        
#         portfolio_name = data['name'].strip()
#         if not portfolio_name:
#             return jsonify({'success': False, 'error': 'Portfolio name cannot be empty'}), 400
        
#         holdings = data.get('holdings', [])
#         if not isinstance(holdings, list):
#             return jsonify({'success': False, 'error': 'Holdings must be an array'}), 400
        
#         # Validate each holding
#         for holding in holdings:
#             if not all(k in holding for k in ['symbol', 'shares', 'averageCost']):
#                 return jsonify({'success': False, 'error': 'Each holding must have symbol, shares, and averageCost'}), 400
            
#             try:
#                 shares = float(holding['shares'])
#                 avg_cost = float(holding['averageCost'])
#                 if shares <= 0 or avg_cost <= 0:
#                     return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
#             except (ValueError, TypeError):
#                 return jsonify({'success': False, 'error': 'Invalid number format in holdings'}), 400
        
#         db = FirebaseService.get_firestore()
        
#         # Generate portfolio ID
#         portfolio_id = str(uuid.uuid4())
#         current_time = datetime.utcnow()
        
#         # Calculate total cost basis
#         total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in holdings)
        
#         portfolio_data = {
#             'id': portfolio_id,
#             'uid': uid,
#             'name': portfolio_name,
#             'holdings': holdings,
#             'createdAt': current_time,
#             'updatedAt': current_time,
#             'totalCostBasis': total_cost_basis
#         }
        
#         # Store in Firestore
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_ref.set(portfolio_data)
        
#         return jsonify({
#             'success': True,
#             'portfolio': portfolio_data,
#             'message': 'Portfolio created successfully'
#         }), 201
        
#     except Exception as e:
#         print(f"Error creating portfolio: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/', methods=['GET'])
# def get_portfolios():
#     """Get all portfolios for the authenticated user"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         db = FirebaseService.get_firestore()
        
#         # Query portfolios for this user, ordered by creation date
#         portfolios_ref = db.collection('portfolios')\
#             .where('uid', '==', uid)\
#             .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
#         docs = portfolios_ref.stream()
        
#         portfolios = []
#         for doc in docs:
#             portfolio_data = doc.to_dict()
#             # Convert Firestore timestamps to ISO format
#             for time_field in ['createdAt', 'updatedAt']:
#                 if time_field in portfolio_data:
#                     portfolio_data[time_field] = portfolio_data[time_field].isoformat()
#             portfolios.append(portfolio_data)
        
#         return jsonify({
#             'success': True,
#             'portfolios': portfolios,
#             'count': len(portfolios)
#         }), 200
        
#     except Exception as e:
#         print(f"Error fetching portfolios: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/<portfolio_id>', methods=['GET'])
# def get_portfolio(portfolio_id):
#     """Get a specific portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         db = FirebaseService.get_firestore()
        
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_doc = portfolio_ref.get()
        
#         if not portfolio_doc.exists:
#             return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
#         portfolio_data = portfolio_doc.to_dict()
        
#         # Check ownership
#         if portfolio_data['uid'] != uid:
#             return jsonify({'success': False, 'error': 'Unauthorized to access this portfolio'}), 403
        
#         # Convert timestamps
#         for time_field in ['createdAt', 'updatedAt']:
#             if time_field in portfolio_data:
#                 portfolio_data[time_field] = portfolio_data[time_field].isoformat()
        
#         return jsonify({
#             'success': True,
#             'portfolio': portfolio_data
#         }), 200
        
#     except Exception as e:
#         print(f"Error fetching portfolio: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/<portfolio_id>/holdings', methods=['PUT'])
# def update_portfolio_holdings(portfolio_id):
#     """Update all holdings in a portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'success': False, 'error': 'Holdings data is required'}), 400
        
#         holdings = data['portfolioData']['holdings']

#         if not isinstance(holdings, list):
#             return jsonify({'success': False, 'error': 'Holdings must be an array'}), 400
                
#         # Validate holdings
#         for holding in holdings:
#             if not all(k in holding for k in ['symbol', 'shares', 'averageCost']):
#                 return jsonify({'success': False, 'error': 'Each holding must have symbol, shares, and averageCost'}), 400
            
#             try:
#                 shares = float(holding['shares'])
#                 avg_cost = float(holding['averageCost'])
#                 if shares <= 0 or avg_cost <= 0:
#                     return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
#             except (ValueError, TypeError):
#                 return jsonify({'success': False, 'error': 'Invalid number format in holdings'}), 400
        
#         db = FirebaseService.get_firestore()
        
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_doc = portfolio_ref.get()
        
#         if not portfolio_doc.exists:
#             return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
#         portfolio_data = portfolio_doc.to_dict()
        
#         # Check ownership
#         if portfolio_data['uid'] != uid:
#             return jsonify({'success': False, 'error': 'Unauthorized to update this portfolio'}), 403
        
        
#         # Calculate total cost basis
#         total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in holdings)
        
#         # Update portfolio
#         update_data = {
#             'holdings': holdings,
#             'updatedAt': datetime.utcnow(),
#             'totalCostBasis': total_cost_basis, 
#         }

#         if 'name' in data['portfolioData']:
#             new_name = data['portfolioData']['name'].strip()
#             if new_name:
#                 update_data['name'] = new_name
        
#         portfolio_ref.update(update_data)

        
#         # Get updated portfolio
#         updated_portfolio = portfolio_ref.get().to_dict()
#         for time_field in ['createdAt', 'updatedAt']:
#             if time_field in updated_portfolio:
#                 updated_portfolio[time_field] = updated_portfolio[time_field].isoformat()
        
#         return jsonify({
#             'success': True,
#             'portfolio': updated_portfolio,
#             'message': 'Portfolio holdings updated successfully'
#         }), 200
        
#     except Exception as e:
#         print(f"Error updating portfolio holdings: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/<portfolio_id>/holdings', methods=['POST'])
# def add_holding(portfolio_id):
#     """Add a single holding to a portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         data = request.get_json()
#         if not data:
#             return jsonify({'success': False, 'error': 'Holding data is required'}), 400
        
#         # Validate holding
#         if not all(k in data for k in ['symbol', 'shares', 'averageCost']):
#             return jsonify({'success': False, 'error': 'Holding must have symbol, shares, and averageCost'}), 400
        
#         try:
#             shares = float(data['shares'])
#             avg_cost = float(data['averageCost'])
#             if shares <= 0 or avg_cost <= 0:
#                 return jsonify({'success': False, 'error': 'Shares and average cost must be positive'}), 400
#         except (ValueError, TypeError):
#             return jsonify({'success': False, 'error': 'Invalid number format'}), 400
        
#         db = FirebaseService.get_firestore()
        
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_doc = portfolio_ref.get()
        
#         if not portfolio_doc.exists:
#             return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
#         portfolio_data = portfolio_doc.to_dict()
        
#         # Check ownership
#         if portfolio_data['uid'] != uid:
#             return jsonify({'success': False, 'error': 'Unauthorized to modify this portfolio'}), 403
        
#         # Create new holding object
#         new_holding = {
#             'symbol': data['symbol'].upper(),
#             'name': data.get('name', data['symbol'].upper()),
#             'shares': data['shares'],
#             'averageCost': data['averageCost']
#         }
        
#         # Get current holdings and add new one
#         current_holdings = portfolio_data.get('holdings', [])
#         updated_holdings = current_holdings + [new_holding]
        
#         # Calculate new total cost basis
#         total_cost_basis = sum(float(h['shares']) * float(h['averageCost']) for h in updated_holdings)
        
#         # Update portfolio
#         update_data = {
#             'holdings': updated_holdings,
#             'updatedAt': datetime.utcnow(),
#             'totalCostBasis': total_cost_basis
#         }
        
#         portfolio_ref.update(update_data)
        
#         # Get updated portfolio
#         updated_portfolio = portfolio_ref.get().to_dict()
#         for time_field in ['createdAt', 'updatedAt']:
#             if time_field in updated_portfolio:
#                 updated_portfolio[time_field] = updated_portfolio[time_field].isoformat()
        
#         return jsonify({
#             'success': True,
#             'portfolio': updated_portfolio,
#             'holding': new_holding,
#             'message': 'Holding added successfully'
#         }), 201
        
#     except Exception as e:
#         print(f"Error adding holding: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/<portfolio_id>', methods=['DELETE'])
# def delete_portfolio(portfolio_id):
#     """Delete a portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         db = FirebaseService.get_firestore()
        
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_doc = portfolio_ref.get()
        
#         if not portfolio_doc.exists:
#             return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
#         portfolio_data = portfolio_doc.to_dict()
        
#         # Check ownership
#         if portfolio_data['uid'] != uid:
#             return jsonify({'success': False, 'error': 'Unauthorized to delete this portfolio'}), 403
        
#         # Delete the portfolio
#         portfolio_ref.delete()
        
#         return jsonify({
#             'success': True,
#             'message': 'Portfolio deleted successfully'
#         }), 200
        
#     except Exception as e:
#         print(f"Error deleting portfolio: {e}")
#         return jsonify({'success': False, 'error': str(e)}), 500

# @portfolio_bp.route('/performance', methods=['GET'])
# def get_all_portfolios_performance():
#     """Get performance for all user portfolios"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         db = FirebaseService.get_firestore()
        
#         # Get all portfolios for user
#         portfolios_ref = db.collection('portfolios')\
#             .where('uid', '==', uid)\
#             .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
#         portfolios_docs = portfolios_ref.stream()
        
#         portfolios = []
#         all_symbols = set()
        
#         # First pass: collect all portfolios and symbols
#         for doc in portfolios_docs:
#             portfolio = doc.to_dict()
#             portfolio['id'] = doc.id
            
#             # Convert Firestore timestamps
#             for field in ['createdAt', 'updatedAt']:
#                 if field in portfolio:
#                     portfolio[field] = portfolio[field].isoformat()
            
#             # Collect symbols from holdings
#             holdings = portfolio.get('holdings', [])
#             for holding in holdings:
#                 all_symbols.add(holding['symbol'].upper())
            
#             portfolios.append(portfolio)
        
#         # Get all prices at once
#         prices = stock_price_service.get_prices(list(all_symbols))
        
#         # Calculate performance for each portfolio
#         portfolio_performances = []
#         individual_prices = {}
#         total_portfolio_cost = 0
#         total_portfolio_value = 0
        
#         for portfolio in portfolios:
#             holdings = portfolio.get('holdings', [])
#             portfolio_cost = 0
#             portfolio_value = 0
            
#             for holding in holdings:
#                 symbol = holding['symbol'].upper()
#                 shares = float(holding['shares'])
#                 avg_cost = float(holding['averageCost'])
                
#                 cost_basis = shares * avg_cost
#                 portfolio_cost += cost_basis
                
#                 current_price = prices.get(symbol)
#                 if current_price:
#                     portfolio_value += shares * current_price

#                 if symbol not in individual_prices:
#                     individual_prices[symbol] = current_price
            
#             portfolio_change = portfolio_value - portfolio_cost
#             portfolio_change_percent = (portfolio_change / portfolio_cost * 100) if portfolio_cost > 0 else 0
            
#             total_portfolio_cost += portfolio_cost
#             total_portfolio_value += portfolio_value
            
#             portfolio_performances.append({
#                 'id': portfolio['id'],
#                 'name': portfolio.get('name', 'Unnamed Portfolio'),
#                 'holdings_count': len(holdings),
#                 'total_cost_basis': portfolio_cost,
#                 'current_value': portfolio_value,
#                 'total_change': portfolio_change,
#                 'total_change_percent': portfolio_change_percent,
#                 'created_at': portfolio.get('createdAt'),
#                 'updated_at': portfolio.get('updatedAt'),
#             })


#         # Calculate overall metrics
#         overall_change = total_portfolio_value - total_portfolio_cost
#         overall_change_percent = (overall_change / total_portfolio_cost * 100) if total_portfolio_cost > 0 else 0
        
#         return jsonify({
#             'success': True,
#             'portfolios': portfolio_performances,
#             'overall': {
#                 'total_cost_basis': total_portfolio_cost,
#                 'current_value': total_portfolio_value,
#                 'total_change': overall_change,
#                 'total_change_percent': overall_change_percent
#             },
#             'individual_prices': individual_prices,
#             'timestamp': datetime.now().isoformat()
#         })
        
#     except Exception as e:
#         print(f"Error fetching portfolio performances: {e}")
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500

# @portfolio_bp.route('/<portfolio_id>/performance', methods=['GET'])
# def get_portfolio_performance(portfolio_id):
#     """Get performance metrics for a portfolio"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         db = FirebaseService.get_firestore()
        
#         # Get portfolio from Firestore
#         portfolio_ref = db.collection('portfolios').document(portfolio_id)
#         portfolio_doc = portfolio_ref.get()
        
#         if not portfolio_doc.exists:
#             return jsonify({'success': False, 'error': 'Portfolio not found'}), 404
        
#         portfolio = portfolio_doc.to_dict()
        
#         # Check ownership
#         if portfolio['uid'] != uid:
#             return jsonify({'success': False, 'error': 'Unauthorized'}), 403
        
#         holdings = portfolio.get('holdings', [])
        
#         if not holdings:
#             return jsonify({
#                 'success': True,
#                 'portfolio_id': portfolio_id,
#                 'total_cost_basis': 0,
#                 'current_value': 0,
#                 'total_change': 0,
#                 'total_change_percent': 0,
#                 'holdings': [],
#                 'timestamp': datetime.now().isoformat()
#             })
        
#         # Extract unique symbols
#         symbols = list(set([h['symbol'].upper() for h in holdings]))
        
#         # Get current prices
#         prices = stock_price_service.get_prices(symbols)
        
#         # Calculate portfolio metrics
#         total_cost_basis = 0
#         current_value = 0
#         holding_details = []
        
#         for holding in holdings:
#             symbol = holding['symbol'].upper()
#             shares = float(holding['shares'])
#             avg_cost = float(holding['averageCost'])
            
#             cost_basis = shares * avg_cost
#             total_cost_basis += cost_basis
            
#             current_price = prices.get(symbol)
#             if current_price:
#                 holding_value = shares * current_price
#                 holding_change = holding_value - cost_basis
#                 holding_change_percent = (holding_change / cost_basis * 100) if cost_basis > 0 else 0
#             else:
#                 holding_value = 0
#                 holding_change = -cost_basis
#                 holding_change_percent = -100
            
#             current_value += holding_value
            
#             holding_details.append({
#                 'symbol': symbol,
#                 'name': holding.get('name', symbol),
#                 'shares': shares,
#                 'average_cost': avg_cost,
#                 'cost_basis': cost_basis,
#                 'current_price': current_price,
#                 'current_value': holding_value,
#                 'change': holding_change,
#                 'change_percent': holding_change_percent
#             })
        
#         # Calculate total portfolio metrics
#         total_change = current_value - total_cost_basis
#         total_change_percent = (total_change / total_cost_basis * 100) if total_cost_basis > 0 else 0
        
#         return jsonify({
#             'success': True,
#             'portfolio_id': portfolio_id,
#             'portfolio_name': portfolio.get('name', 'Unnamed Portfolio'),
#             'total_cost_basis': total_cost_basis,
#             'current_value': current_value,
#             'total_change': total_change,
#             'total_change_percent': total_change_percent,
#             'holdings': holding_details,
#             'timestamp': datetime.now().isoformat()
#         })
        
#     except Exception as e:
#         print(f"Error calculating portfolio performance: {e}")
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500
    

# @portfolio_bp.route('/projection', methods=['POST'])
# def get_portfolio_projection():
#     """Get portfolio projection using Monte Carlo simulation"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401
    
#     try:
#         data = request.get_json()
#         portfolio_selection = data.get('portfolio_selection', 'All')  # 'All' or portfolio name
#         years = int(data.get('years', 10))
        
#         db = FirebaseService.get_firestore()
        
#         # Get user's portfolios
#         portfolios_ref = db.collection('portfolios')\
#             .where('uid', '==', uid)\
#             .order_by('createdAt', direction=firestore.Query.DESCENDING)
        
#         portfolios_docs = portfolios_ref.stream()
#         portfolios = []
        
#         for doc in portfolios_docs:
#             portfolio = doc.to_dict()
#             portfolio['id'] = doc.id
#             portfolios.append(portfolio)
        
#         # Filter portfolios based on selection
#         if portfolio_selection != 'All':
#             portfolios = [p for p in portfolios if p.get('name') == portfolio_selection]
        
#         if not portfolios:
#             return jsonify({
#                 'success': False,
#                 'error': 'No portfolios found'
#             }), 404
        
#         # Combine holdings from selected portfolios
#         combined_holdings = []
#         for portfolio in portfolios:
#             holdings = portfolio.get('holdings', [])
#             # Merge holdings with same symbol
#             for holding in holdings:
#                 symbol = holding['symbol'].upper()
#                 existing = next(
#                     (h for h in combined_holdings if h['symbol'].upper() == symbol),
#                     None
#                 )
                
#                 if existing:
#                     # Merge shares
#                     existing['shares'] = str(float(existing['shares']) + float(holding['shares']))
#                     # Weighted average cost (optional for projection)
#                 else:
#                     combined_holdings.append(holding.copy())
        
#         # Get projection from service
#         projection_result = portfolio_projection_service.get_portfolio_projection(
#             holdings=combined_holdings,
#             years=years,
#             simulations=10000
#         )
        
#         if not projection_result['success']:
#             return jsonify(projection_result), 400
        
#         return jsonify(projection_result), 200
        
#     except Exception as e:
#         print(f"Error in portfolio projection: {e}")
#         return jsonify({
#             'success': False,
#             'error': str(e)
#         }), 500

# @portfolio_bp.route('/projection', methods=['OPTIONS'])
# def handle_options_projection():
#     """Handle OPTIONS preflight request for projection route."""
#     return '', 200


# @portfolio_bp.route('/daily_change', methods=['GET'])
# def get_portfolios_daily_change():
#     """Get intraday daily change for ALL user portfolios combined"""
#     uid = verify_token()
#     if not uid:
#         return jsonify({'success': False, 'error': 'Unauthorized'}), 401

#     try:
#         service = PortfolioDailyChangeService()
#         result = service.get_all_portfolios_daily_change(uid)
#         return jsonify(result), 200

#     except Exception as e:
#         print(f"Error fetching daily change: {e}")
#         return jsonify({'success': False, 'error': 'Failed to compute daily change'}), 500

# @portfolio_bp.route('/daily_change', methods=['OPTIONS'])
# def handle_options_daily_change():
#     return '', 200