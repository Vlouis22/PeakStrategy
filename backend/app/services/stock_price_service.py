# app/services/stock_price_service.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import logging
import random
import os
from typing import Dict, List, Optional, Tuple
from supabase import create_client, Client

from app.services.redis_service import RedisService
from app.services.api_metrics_service import api_metrics_service

logger = logging.getLogger(__name__)


class StockPriceService:
    _instance = None
    _lock = threading.Lock()
    
    # TTL Configuration (in seconds)
    REDIS_TTL = 90  # 1 minute - fastest, most frequent updates
    SUPABASE_TTL_MARKET_OPEN = 300  # 5 minutes during market hours
    SUPABASE_TTL_MARKET_CLOSED = 3600  # 1 hour when market is closed
    SUPABASE_TTL_EXTENDED = 14400  # 4 hours for extended hours/weekends
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StockPriceService, cls).__new__(cls)
                    cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        """Initialize service configuration with Supabase"""
        self.redis_service = RedisService.get_instance()
        self.cache_duration_seconds = 900  # 15 minutes (legacy compatibility)
        self._fetch_lock = threading.Lock()
        self._pending_fetches: Dict[str, tuple] = {}
        self._max_retries = 3
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            logger.warning("SUPABASE_URL and SUPABASE_KEY not set - Supabase caching disabled")
            self.supabase: Optional[Client] = None
        else:
            try:
                self.supabase: Client = create_client(supabase_url, supabase_key)
                logger.info("StockPriceService initialized with Redis + Supabase + Yahoo Finance")
            except Exception as e:
                logger.error(f"Failed to initialize Supabase: {e}")
                self.supabase = None
        
        # Background refresh queue
        self._background_refresh_queue = set()
        self._background_refresh_lock = threading.Lock()
        self._start_background_refresh_worker()
    
    def _start_background_refresh_worker(self):
        """Start background worker for async cache updates"""
        def worker():
            while True:
                try:
                    time.sleep(5)  # Check every 5 seconds
                    
                    with self._background_refresh_lock:
                        if not self._background_refresh_queue:
                            continue
                        symbols_to_refresh = list(self._background_refresh_queue)
                        self._background_refresh_queue.clear()
                    
                    if symbols_to_refresh:
                        logger.debug(f"Background refreshing {len(symbols_to_refresh)} symbols")
                        self._batch_fetch_and_store(symbols_to_refresh)
                        
                except Exception as e:
                    logger.error(f"Background refresh worker error: {e}")
        
        thread = threading.Thread(target=worker, daemon=True)
        thread.start()
    
    def _get_market_status(self) -> str:
        """Determine current market status for TTL selection"""
        now = datetime.utcnow()
        weekday = now.weekday()
        hour = now.hour
        
        # Weekend
        if weekday >= 5:
            return "CLOSED"
        
        # Regular market hours (9:30 AM - 4:00 PM ET = 14:30-21:00 UTC)
        if 14 <= hour < 21:
            return "OPEN"
        
        # Extended hours (4:00 AM - 9:30 AM and 4:00 PM - 8:00 PM ET)
        if (9 <= hour < 14) or (21 <= hour < 24) or (0 <= hour < 1):
            return "EXTENDED"
        
        return "CLOSED"
    
    def _get_appropriate_supabase_ttl(self) -> int:
        """Get appropriate TTL based on market status"""
        status = self._get_market_status()
        
        if status == "OPEN":
            return self.SUPABASE_TTL_MARKET_OPEN
        elif status == "EXTENDED":
            return self.SUPABASE_TTL_EXTENDED
        else:  # CLOSED
            return self.SUPABASE_TTL_MARKET_CLOSED
    
    def _is_supabase_data_fresh(self, last_updated: str) -> bool:
        """Check if Supabase data is fresh based on market status"""
        try:
            last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
            age_seconds = (datetime.utcnow() - last_updated_dt.replace(tzinfo=None)).total_seconds()
            ttl = self._get_appropriate_supabase_ttl()
            return age_seconds < ttl
        except Exception as e:
            logger.warning(f"Error checking Supabase data freshness: {e}")
            return False
    
    def _get_from_supabase(self, symbol: str) -> Optional[Dict[str, any]]:
        """Get stock data from Supabase (tier 2 cache)"""
        if not self.supabase:
            return None
        
        try:
            response = self.supabase.table('stock').select('*').eq('symbol', symbol).execute()
            
            if response.data and len(response.data) > 0:
                record = response.data[0]
                
                # Check if data is fresh
                if self._is_supabase_data_fresh(record['last_updated']):
                    return {
                        'price': float(record['price']),
                        'previous_close': float(record['previous_close']) if record.get('previous_close') else None,
                        'last_updated': record['last_updated'],
                        'from_supabase': True
                    }
                else:
                    # Data is stale - schedule background refresh
                    with self._background_refresh_lock:
                        self._background_refresh_queue.add(symbol)
                    
                    # Return stale data for now (stale-while-revalidate pattern)
                    return {
                        'price': float(record['price']),
                        'previous_close': float(record['previous_close']) if record.get('previous_close') else None,
                        'last_updated': record['last_updated'],
                        'from_supabase': True,
                        'stale': True
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"Error fetching from Supabase for {symbol}: {e}")
            return None
    
    def _get_many_from_supabase(self, symbols: List[str]) -> Dict[str, Dict[str, any]]:
        """Batch get stock data from Supabase"""
        if not self.supabase:
            return {}
        
        try:
            response = self.supabase.table('stock').select('*').in_('symbol', symbols).execute()
            
            results = {}
            stale_symbols = []
            
            for record in response.data:
                symbol = record['symbol']
                is_fresh = self._is_supabase_data_fresh(record['last_updated'])
                
                results[symbol] = {
                    'price': float(record['price']),
                    'previous_close': float(record['previous_close']) if record.get('previous_close') else None,
                    'last_updated': record['last_updated'],
                    'from_supabase': True,
                    'stale': not is_fresh
                }
                
                if not is_fresh:
                    stale_symbols.append(symbol)
            
            # Schedule stale symbols for background refresh
            if stale_symbols:
                with self._background_refresh_lock:
                    self._background_refresh_queue.update(stale_symbols)
            
            return results
            
        except Exception as e:
            logger.error(f"Error batch fetching from Supabase: {e}")
            return {}
    
    def _save_to_supabase(self, symbol: str, price: float, previous_close: Optional[float] = None):
        """Save stock data to Supabase"""
        if not self.supabase:
            return
        
        try:
            data = {
                'symbol': symbol,
                'price': price,
                'previous_close': previous_close,
                'last_updated': datetime.utcnow().isoformat()
            }
            
            # Upsert (insert or update)
            self.supabase.table('stock').upsert(data).execute()
            
        except Exception as e:
            logger.error(f"Error saving to Supabase for {symbol}: {e}")
    
    def _save_many_to_supabase(self, data_dict: Dict[str, Dict[str, float]]):
        """Batch save stock data to Supabase"""
        if not self.supabase or not data_dict:
            return
        
        try:
            now = datetime.utcnow().isoformat()
            records = []
            
            for symbol, data in data_dict.items():
                records.append({
                    'symbol': symbol,
                    'price': data.get('price'),
                    'previous_close': data.get('previous_close'),
                    'last_updated': now
                })
            
            # Batch upsert
            self.supabase.table('stock').upsert(records).execute()
            logger.debug(f"Saved {len(records)} records to Supabase")
            
        except Exception as e:
            logger.error(f"Error batch saving to Supabase: {e}")
    
    def _get_price_cache_key(self, symbol: str) -> str:
        return f"stock_price:{symbol}"
    
    def _get_full_data_cache_key(self, symbol: str) -> str:
        return f"stock_full_data:{symbol}"
    
    def _deduplicated_fetch(self, symbol: str, fetch_func) -> Optional[float]:
        """
        Fetch with request deduplication - prevents multiple concurrent requests
        for the same symbol from hitting external APIs.
        """
        request_key = f"fetch:{symbol}"
        
        with self._fetch_lock:
            if request_key in self._pending_fetches:
                event, _ = self._pending_fetches[request_key]
                is_waiter = True
            else:
                event = threading.Event()
                self._pending_fetches[request_key] = (event, None)
                is_waiter = False
        
        if is_waiter:
            logger.debug(f"Waiting for pending fetch: {symbol}")
            event.wait(timeout=30)
            with self._fetch_lock:
                entry = self._pending_fetches.get(request_key)
                if entry:
                    return entry[1]
                return None
        
        try:
            start_time = time.time()
            result = fetch_func()
            elapsed_ms = (time.time() - start_time) * 1000
            
            api_metrics_service.record_api_call(
                service_name="stock_price",
                success=result is not None,
                response_time_ms=elapsed_ms,
                cached=False
            )
            
            with self._fetch_lock:
                self._pending_fetches[request_key] = (event, result)
            
            return result
        finally:
            event.set()
            def cleanup():
                time.sleep(1)
                with self._fetch_lock:
                    if request_key in self._pending_fetches:
                        del self._pending_fetches[request_key]
            threading.Thread(target=cleanup, daemon=True).start()
    
    def get_price(self, symbol: str, use_cache: bool = True) -> Optional[float]:
        """
        Get stock price with three-tier caching: Redis → Supabase → API
        
        Caching strategy:
        1. Check Redis (60s TTL) - fastest
        2. Check Supabase (5min-1hr TTL based on market status) - fast
        3. Fetch from Yahoo Finance API - slow
        """
        symbol = symbol.upper().strip()
        start_time = time.time()
        
        # TIER 1: Redis Cache (fastest)
        if use_cache:
            cache_key = self._get_price_cache_key(symbol)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.REDIS_TTL:
                            price = cached_data.get("price")
                            if price is not None:
                                elapsed_ms = (time.time() - start_time) * 1000
                                api_metrics_service.record_api_call(
                                    service_name="stock_price",
                                    success=True,
                                    response_time_ms=elapsed_ms,
                                    cached=True
                                )
                                logger.debug(f"[REDIS HIT] {symbol}: ${price}")
                                return price
                    except Exception as e:
                        logger.warning(f"Error parsing Redis cache timestamp for {symbol}: {e}")
        
        # TIER 2: Supabase Database (fast)
        if use_cache:
            supabase_data = self._get_from_supabase(symbol)
            if supabase_data:
                price = supabase_data['price']
                
                # Cache in Redis for faster subsequent access
                cache_key = self._get_price_cache_key(symbol)
                cache_data = {
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol
                }
                self.redis_service.set(cache_key, cache_data, self.REDIS_TTL)
                
                elapsed_ms = (time.time() - start_time) * 1000
                api_metrics_service.record_api_call(
                    service_name="stock_price",
                    success=True,
                    response_time_ms=elapsed_ms,
                    cached=True
                )
                
                stale_indicator = " (stale)" if supabase_data.get('stale') else ""
                logger.debug(f"[SUPABASE HIT{stale_indicator}] {symbol}: ${price}")
                return price
        
        # TIER 3: Yahoo Finance API (slow)
        logger.debug(f"[API FETCH] {symbol}")
        price = self._fetch_price(symbol)
        
        if price is not None and price > 0:
            # Store in both caches
            cache_key = self._get_price_cache_key(symbol)
            cache_data = {
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol
            }
            self.redis_service.set(cache_key, cache_data, self.REDIS_TTL)
            
            # Save to Supabase (async to not block response)
            threading.Thread(
                target=self._save_to_supabase,
                args=(symbol, price),
                daemon=True
            ).start()
        
        return price
    
    def get_prices(self, symbols: List[str], use_cache: bool = True) -> Dict[str, Optional[float]]:
        """
        Get multiple stock prices with three-tier caching and intelligent batch fetching
        
        Strategy:
        1. Check Redis for all symbols
        2. Check Supabase for remaining symbols
        3. Batch fetch remaining from Yahoo Finance
        4. Store results in both caches
        """
        symbols = list(set(s.upper().strip() for s in symbols))
        
        results = {}
        symbols_to_check_supabase = []
        symbols_to_fetch_api = []
        
        # TIER 1: Redis Cache
        if use_cache:
            cache_keys = [self._get_price_cache_key(s) for s in symbols]
            cached_data = self.redis_service.get_multi(cache_keys)
            
            for symbol in symbols:
                cache_key = self._get_price_cache_key(symbol)
                data = cached_data.get(cache_key)
                
                if data:
                    timestamp_str = data.get("timestamp")
                    price = data.get("price")
                    
                    if timestamp_str and price is not None:
                        try:
                            cached_time = datetime.fromisoformat(timestamp_str)
                            age = (datetime.now() - cached_time).total_seconds()
                            
                            if age < self.REDIS_TTL:
                                results[symbol] = price
                                api_metrics_service.record_api_call(
                                    service_name="stock_price",
                                    success=True,
                                    response_time_ms=0.1,
                                    cached=True
                                )
                                continue
                        except Exception as e:
                            logger.warning(f"Error parsing Redis cache timestamp for {symbol}: {e}")
                
                symbols_to_check_supabase.append(symbol)
        else:
            symbols_to_check_supabase = symbols
        
        # TIER 2: Supabase Database
        if symbols_to_check_supabase and use_cache:
            logger.debug(f"Checking Supabase for {len(symbols_to_check_supabase)} symbols")
            supabase_data = self._get_many_from_supabase(symbols_to_check_supabase)
            
            # Cache Supabase results in Redis
            redis_cache_items = {}
            
            for symbol in symbols_to_check_supabase:
                if symbol in supabase_data:
                    price = supabase_data[symbol]['price']
                    results[symbol] = price
                    
                    # Cache in Redis
                    cache_key = self._get_price_cache_key(symbol)
                    redis_cache_items[cache_key] = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    
                    api_metrics_service.record_api_call(
                        service_name="stock_price",
                        success=True,
                        response_time_ms=0.5,
                        cached=True
                    )
                else:
                    symbols_to_fetch_api.append(symbol)
            
            if redis_cache_items:
                self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
        else:
            symbols_to_fetch_api = symbols_to_check_supabase
        
        # TIER 3: Yahoo Finance API
        if symbols_to_fetch_api:
            logger.info(f"Fetching {len(symbols_to_fetch_api)} symbols from API: {symbols_to_fetch_api}")
            fetched_prices = self._batch_fetch_prices(symbols_to_fetch_api)
            
            # Store in both caches
            redis_cache_items = {}
            supabase_data = {}
            
            for symbol, price in fetched_prices.items():
                if price is not None and price > 0:
                    results[symbol] = price
                    
                    # Prepare Redis cache
                    cache_key = self._get_price_cache_key(symbol)
                    redis_cache_items[cache_key] = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    
                    # Prepare Supabase data
                    supabase_data[symbol] = {"price": price}
            
            # Store in Redis immediately
            if redis_cache_items:
                self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
            
            # Store in Supabase (async)
            if supabase_data:
                threading.Thread(
                    target=self._save_many_to_supabase,
                    args=(supabase_data,),
                    daemon=True
                ).start()
        
        logger.debug(f"Price fetch summary: {len(results)}/{len(symbols)} successful")
        return results
    
    def _refresh_stale_symbols_background(self, symbols: List[str]):
        """Refresh stale cache entries in background thread."""
        def do_refresh():
            try:
                fetched_prices = self._batch_fetch_prices(symbols)
                redis_cache_items = {}
                supabase_data = {}
                
                for symbol, price in fetched_prices.items():
                    if price is not None and price > 0:
                        cache_key = self._get_price_cache_key(symbol)
                        redis_cache_items[cache_key] = {
                            "price": price,
                            "timestamp": datetime.now().isoformat(),
                            "symbol": symbol
                        }
                        supabase_data[symbol] = {"price": price}
                
                if redis_cache_items:
                    self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
                    
                if supabase_data:
                    self._save_many_to_supabase(supabase_data)
                    
                logger.debug(f"Background refresh completed for {len(redis_cache_items)} symbols")
            except Exception as e:
                logger.error(f"Background refresh failed: {e}")
        
        thread = threading.Thread(target=do_refresh, daemon=True)
        thread.start()
    
    def _batch_fetch_and_store(self, symbols: List[str]):
        """Batch fetch and store in both caches"""
        fetched_prices = self._batch_fetch_prices(symbols)
        
        redis_cache_items = {}
        supabase_data = {}
        
        for symbol, price in fetched_prices.items():
            if price is not None and price > 0:
                cache_key = self._get_price_cache_key(symbol)
                redis_cache_items[cache_key] = {
                    "price": price,
                    "timestamp": datetime.now().isoformat(),
                    "symbol": symbol
                }
                supabase_data[symbol] = {"price": price}
        
        if redis_cache_items:
            self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
            
        if supabase_data:
            self._save_many_to_supabase(supabase_data)
    
    def _batch_fetch_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Batch fetch prices using Yahoo Finance."""
        results = {}
        start_time = time.time()
        
        try:
            yf_results = self._try_yfinance_batch(symbols)
            results.update(yf_results)
        except Exception as e:
            logger.error(f"Batch fetch failed: {e}")
        
        elapsed_ms = (time.time() - start_time) * 1000
        success_count = sum(1 for v in results.values() if v is not None)
        
        api_metrics_service.record_api_call(
            service_name="stock_price_batch",
            success=success_count > 0,
            response_time_ms=elapsed_ms,
            cached=False
        )
        
        return results
    
    def _try_yfinance_batch(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Try to fetch prices using yfinance batch download with retry."""
        results = {}
        
        for attempt in range(self._max_retries):
            try:
                with self._fetch_lock:
                    tickers = yf.download(
                        " ".join(symbols),
                        period="1d",
                        interval="1m",
                        group_by='ticker',
                        progress=False,
                        auto_adjust=True
                    )
                    
                    if tickers is not None and not tickers.empty:
                        for symbol in symbols:
                            try:
                                if len(symbols) == 1:
                                    price = tickers['Close'].iloc[-1]
                                elif symbol in tickers:
                                    price = tickers[symbol]['Close'].iloc[-1]
                                else:
                                    continue
                                    
                                if not pd.isna(price):
                                    results[symbol] = float(price)
                            except Exception as e:
                                logger.debug(f"Error extracting {symbol} from batch: {e}")
                        
                        if results:
                            return results
                    else:
                        logger.warning(f"yfinance batch download returned empty data (attempt {attempt + 1}/{self._max_retries})")
                        
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Too Many Requests' in error_str or 'rate' in error_str.lower():
                    api_metrics_service.record_api_call(
                        service_name="yfinance",
                        success=False,
                        response_time_ms=0,
                        rate_limited=True
                    )
                    logger.warning(f"yfinance rate limited (attempt {attempt + 1}/{self._max_retries}), will retry")
                else:
                    logger.error(f"yfinance batch error: {e}")
            
            if attempt < self._max_retries - 1:
                backoff = (2 ** attempt) + (random.random() * 0.5)
                logger.debug(f"Retrying yfinance in {backoff:.1f}s (attempt {attempt + 2}/{self._max_retries})")
                time.sleep(backoff)
        
        if not results:
            logger.warning("yfinance failed after all retries")
        
        return results
    
    def _fetch_price(self, symbol: str) -> Optional[float]:
        """Fetch price from Yahoo Finance with retry logic."""
        def do_fetch():
            for attempt in range(self._max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    price = (
                        info.get('currentPrice') or 
                        info.get('regularMarketPrice') or 
                        info.get('previousClose')
                    )
                    
                    if price is not None:
                        return float(price)
                        
                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'Too Many Requests' in error_str or 'rate' in error_str.lower():
                        logger.warning(f"yfinance rate limited for {symbol} (attempt {attempt + 1}/{self._max_retries})")
                        if attempt < self._max_retries - 1:
                            backoff = (2 ** attempt) + (random.random() * 0.5)
                            time.sleep(backoff)
                            continue
                    else:
                        logger.error(f"yfinance error for {symbol}: {e}")
                        break
            
            return None
        
        return self._deduplicated_fetch(symbol, do_fetch)

    def get_intraday_and_previous_close(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get intraday price and previous close with three-tier caching.
        
        This method uses the full_data cache which includes both current price and previous close.
        """
        symbols = list(set(s.upper().strip() for s in symbols))
        data = {}
        symbols_to_check_supabase = []
        symbols_to_fetch = []
        
        # TIER 1: Redis Cache
        for symbol in symbols:
            cache_key = self._get_full_data_cache_key(symbol)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.REDIS_TTL:
                            data[symbol] = {
                                "price": cached_data.get("price"),
                                "previous_close": cached_data.get("previous_close")
                            }
                            api_metrics_service.record_api_call(
                                service_name="intraday_data",
                                success=True,
                                response_time_ms=0.1,
                                cached=True
                            )
                            continue
                    except Exception as e:
                        logger.warning(f"Error parsing Redis cache for {symbol}: {e}")
            
            symbols_to_check_supabase.append(symbol)
        
        # TIER 2: Supabase Database
        if symbols_to_check_supabase:
            logger.debug(f"Checking Supabase for intraday data: {len(symbols_to_check_supabase)} symbols")
            supabase_data = self._get_many_from_supabase(symbols_to_check_supabase)
            
            redis_cache_items = {}
            
            for symbol in symbols_to_check_supabase:
                if symbol in supabase_data:
                    db_record = supabase_data[symbol]
                    
                    if db_record.get('price') and db_record.get('previous_close'):
                        data[symbol] = {
                            "price": db_record['price'],
                            "previous_close": db_record['previous_close']
                        }
                        
                        # Cache in Redis
                        cache_key = self._get_full_data_cache_key(symbol)
                        redis_cache_items[cache_key] = {
                            "price": db_record['price'],
                            "previous_close": db_record['previous_close'],
                            "timestamp": datetime.now().isoformat(),
                            "symbol": symbol
                        }
                        
                        api_metrics_service.record_api_call(
                            service_name="intraday_data",
                            success=True,
                            response_time_ms=0.5,
                            cached=True
                        )
                    else:
                        symbols_to_fetch.append(symbol)
                else:
                    symbols_to_fetch.append(symbol)
            
            if redis_cache_items:
                self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
        
        # TIER 3: Yahoo Finance API
        if symbols_to_fetch:
            logger.info(f"Fetching intraday data from API for {len(symbols_to_fetch)} symbols")
            fetched_data = self._fetch_intraday_batch(symbols_to_fetch)
            
            # Store in both caches
            redis_cache_items = {}
            supabase_data_dict = {}
            
            for symbol, symbol_data in fetched_data.items():
                if symbol_data.get("price") and symbol_data.get("previous_close"):
                    data[symbol] = symbol_data
                    
                    # Prepare Redis cache
                    cache_key = self._get_full_data_cache_key(symbol)
                    redis_cache_items[cache_key] = {
                        "price": symbol_data["price"],
                        "previous_close": symbol_data["previous_close"],
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    
                    # Prepare Supabase data
                    supabase_data_dict[symbol] = {
                        "price": symbol_data["price"],
                        "previous_close": symbol_data["previous_close"]
                    }
            
            # Store in Redis immediately
            if redis_cache_items:
                self.redis_service.set_multi(redis_cache_items, self.REDIS_TTL)
            
            # Store in Supabase (async)
            if supabase_data_dict:
                threading.Thread(
                    target=self._save_many_to_supabase,
                    args=(supabase_data_dict,),
                    daemon=True
                ).start()
        
        return data
    
    def _fetch_intraday_batch(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Fetch intraday data using Yahoo Finance."""
        data = {}
        start_time = time.time()
        
        for symbol in symbols:
            fetched = False
            for attempt in range(self._max_retries):
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    
                    price = info.get("regularMarketPrice") or info.get('currentPrice')
                    prev_close = info.get("regularMarketPreviousClose")
                    
                    if price and prev_close:
                        data[symbol] = {
                            "price": float(price),
                            "previous_close": float(prev_close)
                        }
                        fetched = True
                        break
                    else:
                        break
                            
                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'Too Many Requests' in error_str or 'rate' in error_str.lower():
                        logger.warning(f"yfinance rate limited for {symbol} (attempt {attempt + 1}/{self._max_retries})")
                        if attempt < self._max_retries - 1:
                            backoff = (2 ** attempt) + (random.random() * 0.5)
                            time.sleep(backoff)
                            continue
                    else:
                        break
            
            if not fetched:
                logger.debug(f"Could not fetch intraday data for {symbol}")
        
        elapsed_ms = (time.time() - start_time) * 1000
        api_metrics_service.record_api_call(
            service_name="intraday_data",
            success=len(data) > 0,
            response_time_ms=elapsed_ms,
            cached=False
        )
        
        return data
    
    def invalidate_cache(self, symbol: str):
        """Invalidate all caches for a specific symbol"""
        symbol = symbol.upper().strip()
        
        # Invalidate Redis
        price_key = self._get_price_cache_key(symbol)
        full_data_key = self._get_full_data_cache_key(symbol)
        self.redis_service.delete(price_key)
        self.redis_service.delete(full_data_key)
        
        logger.info(f"Cache invalidated for {symbol}")
    
    def warm_cache(self, symbols: List[str]):
        """
        Proactively warm the cache for frequently accessed symbols.
        Useful for pre-loading data before market open or for popular stocks.
        """
        logger.info(f"Warming cache for {len(symbols)} symbols")
        self.get_prices(symbols, use_cache=False)
        logger.info(f"Cache warming complete")


stock_price_service = StockPriceService()