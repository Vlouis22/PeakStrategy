from datetime import datetime, timezone
from typing import Dict, Any
from collections import defaultdict
import json
import hashlib

from app.services.stock_price_service import stock_price_service
from app.services.firebase_service import FirebaseService
from app.services.redis_service import RedisService
from google.cloud.firestore_v1.base_query import FieldFilter  # ADD THIS IMPORT


class PortfolioDailyChangeService:
    """
    Computes intraday / daily change for ALL user portfolios combined.
    Prices fetched via Yahoo Finance.
    """

    CACHE_TTL_SECONDS = 60
    PRICE_INTERVAL = "1m"

    def __init__(self):
        """Initialize Redis service"""
        self.redis_service = RedisService.get_instance()

    @staticmethod
    def get_market_status() -> str:
        now = datetime.now(timezone.utc)
        weekday = now.weekday()
        hour = now.hour

        if weekday >= 5:
            return "CLOSED"

        # US market hours approx 14:30–21:00 UTC
        if 14 <= hour < 21:
            return "OPEN"

        return "CLOSED"

    def _get_cache_key(self, uid: str) -> str:
        """Generate Redis cache key for user's portfolio data"""
        return self.redis_service.get_user_cache_key(uid, "daily_change")

    def _get_holdings_hash_key(self, uid: str) -> str:
        """Generate Redis key for storing holdings hash"""
        return self.redis_service.get_user_cache_key(uid, "holdings_hash")

    def _compute_holdings_hash(self, aggregated_holdings: Dict[str, float]) -> str:
        """Compute a hash of the current holdings to detect changes"""
        holdings_str = json.dumps(sorted(aggregated_holdings.items()))
        return hashlib.md5(holdings_str.encode()).hexdigest()

    def _get_cached_result(self, uid: str) -> Dict[str, Any] or None:
        """Retrieve cached result from Redis if available and valid"""
        cache_key = self._get_cache_key(uid)
        cached_data = self.redis_service.get(cache_key)
        
        if not cached_data:
            return None
        
        # Check if cache is still fresh by timestamp
        cache_timestamp = datetime.fromisoformat(cached_data.get('timestamp', '').replace('Z', '+00:00'))
        current_time = datetime.now(timezone.utc)
        age_seconds = (current_time - cache_timestamp).total_seconds()
        
        if age_seconds < self.CACHE_TTL_SECONDS:
            # Verify holdings haven't changed
            holdings_hash_key = self._get_holdings_hash_key(uid)
            cached_hash = self.redis_service.get(holdings_hash_key)
            
            if cached_hash:
                # Get current holdings to compute hash
                db = FirebaseService.get_firestore()
                portfolio_docs = (
                    db.collection("portfolios")
                    .where(filter=FieldFilter("uid", "==", uid))  # FIXED HERE
                    .stream()
                )
                
                current_holdings = defaultdict(float)
                for doc in portfolio_docs:
                    portfolio = doc.to_dict()
                    for h in portfolio.get("holdings", []):
                        symbol = h["symbol"].upper()
                        current_holdings[symbol] += float(h["shares"])
                
                current_hash = self._compute_holdings_hash(current_holdings)
                
                if current_hash == cached_hash:
                    # Cache is valid
                    return cached_data
        
        return None

    def _cache_result(self, uid: str, result: Dict[str, Any], holdings_hash: str):
        """Cache result in Redis"""
        cache_key = self._get_cache_key(uid)
        holdings_hash_key = self._get_holdings_hash_key(uid)
        
        # Store both the result and the holdings hash
        self.redis_service.set(cache_key, result, self.CACHE_TTL_SECONDS)
        self.redis_service.set(holdings_hash_key, holdings_hash, self.CACHE_TTL_SECONDS)

    def get_all_portfolios_daily_change(self, uid: str) -> Dict[str, Any]:
        # Try to get from cache first
        cached_result = self._get_cached_result(uid)
        if cached_result:
            # Update timestamp to current time but keep cached data
            cached_result['timestamp'] = datetime.utcnow().replace(tzinfo=timezone.utc).isoformat()
            cached_result['market']['lastUpdated'] = cached_result['timestamp']
            cached_result['meta']['cached'] = True
            return cached_result

        # Not in cache or cache invalid, compute fresh result
        db = FirebaseService.get_firestore()

        # Fetch ALL portfolios for this user - CORRECTED HERE
        portfolio_docs = (
            db.collection("portfolios")
            .where(filter=FieldFilter("uid", "==", uid))  # FIXED HERE
            .stream()
        )

        aggregated_holdings = defaultdict(float)

        for doc in portfolio_docs:
            portfolio = doc.to_dict()
            for h in portfolio.get("holdings", []):
                symbol = h["symbol"].upper()
                aggregated_holdings[symbol] += float(h["shares"])

        if not aggregated_holdings:
            return self._empty_response()

        symbols = list(aggregated_holdings.keys())

        # Fetch intraday + previous close prices
        price_data = stock_price_service.get_intraday_and_previous_close(symbols)

        holdings_response = []
        total_value = 0.0
        previous_close_value = 0.0

        for symbol, quantity in aggregated_holdings.items():
            prices = price_data.get(symbol)
            if not prices:
                continue

            current_price = prices.get("price")
            previous_close = prices.get("previous_close")
            
            if current_price is None or previous_close is None:
                continue

            value = quantity * current_price
            prev_value = quantity * previous_close

            daily_abs = value - prev_value
            daily_pct = (daily_abs / prev_value * 100) if prev_value > 0 else 0.0

            total_value += value
            previous_close_value += prev_value

            holdings_response.append({
                "symbol": symbol,
                "quantity": round(quantity, 4),
                "price": round(current_price, 2),
                "previousClose": round(previous_close, 2),
                "value": round(value, 2),
                "dailyChange": {
                    "absolute": round(daily_abs, 2),
                    "percent": round(daily_pct, 2)
                }
            })

        portfolio_abs = total_value - previous_close_value
        portfolio_pct = (
            portfolio_abs / previous_close_value * 100
            if previous_close_value > 0 else 0.0
        )

        # Add weights
        for h in holdings_response:
            h["weight"] = (
                round(h["value"] / total_value, 4)
                if total_value > 0 else 0.0
            )

        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        result = {
            "portfolioId": "ALL",
            "timestamp": now.isoformat(),
            "market": {
                "status": self.get_market_status(),
                "lastUpdated": now.isoformat(),
                "interval": self.PRICE_INTERVAL
            },
            "portfolio": {
                "totalValue": round(total_value, 2),
                "previousCloseValue": round(previous_close_value, 2),
                "dailyChange": {
                    "absolute": round(portfolio_abs, 2),
                    "percent": round(portfolio_pct, 2)
                }
            },
            "holdings": holdings_response,
            "meta": {
                "currency": "USD",
                "source": "yahoo_finance",
                "cached": False,  # This is fresh data
                "cacheTtlSeconds": self.CACHE_TTL_SECONDS
            }
        }

        # Cache the result
        holdings_hash = self._compute_holdings_hash(aggregated_holdings)
        self._cache_result(uid, result, holdings_hash)

        return result

    def _empty_response(self) -> Dict[str, Any]:
        now = datetime.utcnow().replace(tzinfo=timezone.utc)

        return {
            "portfolioId": "ALL",
            "timestamp": now.isoformat(),
            "market": {
                "status": self.get_market_status(),
                "lastUpdated": now.isoformat(),
                "interval": self.PRICE_INTERVAL
            },
            "portfolio": {
                "totalValue": 0,
                "previousCloseValue": 0,
                "dailyChange": {
                    "absolute": 0,
                    "percent": 0
                }
            },
            "holdings": [],
            "meta": {
                "currency": "USD",
                "source": "yahoo_finance",
                "cached": False,
                "cacheTtlSeconds": self.CACHE_TTL_SECONDS
            }
        }

    def invalidate_user_cache(self, uid: str):
        """Invalidate cache for a specific user"""
        self.redis_service.invalidate_user_cache(uid)