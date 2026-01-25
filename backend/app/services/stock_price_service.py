# app/services/stock_price_service.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import logging
import random
from typing import Dict, List, Optional

from app.services.redis_service import RedisService
from app.services.api_metrics_service import api_metrics_service

logger = logging.getLogger(__name__)


class StockPriceService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super(StockPriceService, cls).__new__(cls)
                    cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        """Initialize service configuration"""
        self.redis_service = RedisService.get_instance()
        self.cache_duration_seconds = 900  # 15 minutes
        self._fetch_lock = threading.Lock()
        self._pending_fetches: Dict[str, tuple] = {}  # Maps symbol -> (event, result)
        self._max_retries = 3  # Max retries with exponential backoff
        logger.info("StockPriceService initialized with RedisService (Yahoo Finance only)")
    
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
        """Get stock price with Redis caching and request deduplication."""
        symbol = symbol.upper().strip()
        start_time = time.time()
        
        if use_cache:
            cache_key = self._get_price_cache_key(symbol)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.cache_duration_seconds:
                            price = cached_data.get("price")
                            if price is not None:
                                elapsed_ms = (time.time() - start_time) * 1000
                                api_metrics_service.record_api_call(
                                    service_name="stock_price",
                                    success=True,
                                    response_time_ms=elapsed_ms,
                                    cached=True
                                )
                                return price
                    except Exception as e:
                        logger.warning(f"Error parsing cache timestamp for {symbol}: {e}")
        
        price = self._fetch_price(symbol)
        
        if price is not None and price > 0:
            cache_key = self._get_price_cache_key(symbol)
            cache_data = {
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol
            }
            self.redis_service.set(cache_key, cache_data, self.cache_duration_seconds)
        
        return price
    
    def get_prices(self, symbols: List[str], use_cache: bool = True) -> Dict[str, Optional[float]]:
        """Get multiple stock prices with two-tier caching and stale-while-revalidate."""
        symbols = list(set(s.upper().strip() for s in symbols))
        
        results = {}
        symbols_to_fetch = []
        stale_symbols = []
        
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
                            
                            if age < self.cache_duration_seconds:
                                results[symbol] = price
                                api_metrics_service.record_api_call(
                                    service_name="stock_price",
                                    success=True,
                                    response_time_ms=0.1,
                                    cached=True
                                )
                                continue
                            elif age < self.cache_duration_seconds * 2:
                                results[symbol] = price
                                stale_symbols.append(symbol)
                                api_metrics_service.record_api_call(
                                    service_name="stock_price",
                                    success=True,
                                    response_time_ms=0.1,
                                    cached=True
                                )
                                continue
                        except Exception as e:
                            logger.warning(f"Error parsing cache timestamp for {symbol}: {e}")
                
                symbols_to_fetch.append(symbol)
        else:
            symbols_to_fetch = symbols
        
        if symbols_to_fetch:
            logger.info(f"Fetching {len(symbols_to_fetch)} symbols: {symbols_to_fetch}")
            fetched_prices = self._batch_fetch_prices(symbols_to_fetch)
            
            cache_items = {}
            for symbol, price in fetched_prices.items():
                if price is not None and price > 0:
                    cache_key = self._get_price_cache_key(symbol)
                    cache_items[cache_key] = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
            
            if cache_items:
                self.redis_service.set_multi(cache_items, self.cache_duration_seconds)
            
            results.update(fetched_prices)
        
        if stale_symbols:
            self._refresh_stale_symbols_background(stale_symbols)
        
        return results
    
    def _refresh_stale_symbols_background(self, symbols: List[str]):
        """Refresh stale cache entries in background thread."""
        def do_refresh():
            try:
                fetched_prices = self._batch_fetch_prices(symbols)
                cache_items = {}
                for symbol, price in fetched_prices.items():
                    if price is not None and price > 0:
                        cache_key = self._get_price_cache_key(symbol)
                        cache_items[cache_key] = {
                            "price": price,
                            "timestamp": datetime.now().isoformat(),
                            "symbol": symbol
                        }
                if cache_items:
                    self.redis_service.set_multi(cache_items, self.cache_duration_seconds)
                    logger.debug(f"Background refresh completed for {len(cache_items)} symbols")
            except Exception as e:
                logger.error(f"Background refresh failed: {e}")
        
        thread = threading.Thread(target=do_refresh, daemon=True)
        thread.start()
    
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
                # Let yfinance handle its own session (uses curl_cffi internally)
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
                    # Let yfinance handle its own session
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
        """Get intraday price and previous close with caching."""
        symbols = list(set(s.upper().strip() for s in symbols))
        data = {}
        symbols_to_fetch = []
        
        for symbol in symbols:
            cache_key = self._get_full_data_cache_key(symbol)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.cache_duration_seconds:
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
                        logger.warning(f"Error parsing cache for {symbol}: {e}")
            
            symbols_to_fetch.append(symbol)
        
        if symbols_to_fetch:
            fetched_data = self._fetch_intraday_batch(symbols_to_fetch)
            
            for symbol, symbol_data in fetched_data.items():
                if symbol_data.get("price") and symbol_data.get("previous_close"):
                    cache_data = {
                        "price": symbol_data["price"],
                        "previous_close": symbol_data["previous_close"],
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    cache_key = self._get_full_data_cache_key(symbol)
                    self.redis_service.set(cache_key, cache_data, self.cache_duration_seconds)
            
            data.update(fetched_data)
        
        return data
    
    def _fetch_intraday_batch(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Fetch intraday data using Yahoo Finance."""
        data = {}
        start_time = time.time()
        
        for symbol in symbols:
            fetched = False
            for attempt in range(self._max_retries):
                try:
                    # Let yfinance handle its own session
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


stock_price_service = StockPriceService()