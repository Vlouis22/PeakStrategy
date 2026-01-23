# app/services/stock_price_service.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
import logging
from typing import Dict, List, Optional
import os
import requests

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
        """Initialize Redis configuration"""
        self.redis_service = RedisService.get_instance()
        self.cache_duration_seconds = 900  # 15 minutes
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')
        self._yfinance_failed = False
        self._last_alpha_vantage_call = 0
        self._alpha_vantage_min_interval = 12  # 12 seconds between calls (5/min limit)
        self._fetch_lock = threading.Lock()
        self._pending_fetches: Dict[str, tuple] = {}  # Maps symbol -> (event, result)
        self._alpha_vantage_lock = threading.Lock()  # Global lock for Alpha Vantage rate limiting
        self._max_alpha_vantage_per_batch = 3  # Limit AV calls per request to avoid long waits
        logger.info("StockPriceService initialized with RedisService")
    
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
                # Another request is already fetching this symbol - wait for it
                event, _ = self._pending_fetches[request_key]
                is_waiter = True
            else:
                # First request for this symbol - create the fetch entry
                event = threading.Event()
                self._pending_fetches[request_key] = (event, None)
                is_waiter = False
        
        if is_waiter:
            # Wait for the first request to complete
            logger.debug(f"Waiting for pending fetch: {symbol}")
            event.wait(timeout=30)
            with self._fetch_lock:
                entry = self._pending_fetches.get(request_key)
                if entry:
                    return entry[1]  # Return the result
                return None
        
        # This is the first request - do the actual fetch
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
            
            # Store result for waiters
            with self._fetch_lock:
                self._pending_fetches[request_key] = (event, result)
            
            return result
        finally:
            # Signal waiters and schedule cleanup
            event.set()
            # Keep result available briefly for waiters, then clean up
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
        
        price = self._fetch_price_with_fallback(symbol)
        
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
        """Get multiple stock prices with caching - optimized to minimize API calls."""
        symbols = list(set(s.upper().strip() for s in symbols))
        
        results = {}
        symbols_to_fetch = []
        
        for symbol in symbols:
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
                                    results[symbol] = price
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
        
        if symbols_to_fetch:
            logger.info(f"Fetching {len(symbols_to_fetch)} symbols: {symbols_to_fetch}")
            fetched_prices = self._batch_fetch_prices(symbols_to_fetch)
            
            for symbol, price in fetched_prices.items():
                if price is not None and price > 0:
                    cache_key = self._get_price_cache_key(symbol)
                    cache_data = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    self.redis_service.set(cache_key, cache_data, self.cache_duration_seconds)
            
            results.update(fetched_prices)
        
        return results
    
    def _batch_fetch_prices(self, symbols: List[str]) -> Dict[str, Optional[float]]:
        """Batch fetch with deduplication - single entry point for external API calls."""
        results = {}
        start_time = time.time()
        
        try:
            if not self._yfinance_failed:
                yf_results = self._try_yfinance_batch(symbols)
                results.update(yf_results)
            
            failed_symbols = [s for s in symbols if results.get(s) is None]
            
            if failed_symbols:
                # Limit Alpha Vantage calls to avoid long waits
                symbols_to_try = failed_symbols[:self._max_alpha_vantage_per_batch]
                if len(failed_symbols) > self._max_alpha_vantage_per_batch:
                    logger.info(f"Limiting Alpha Vantage to {self._max_alpha_vantage_per_batch} of {len(failed_symbols)} symbols")
                
                for symbol in symbols_to_try:
                    av_price = self._fetch_from_alpha_vantage(symbol)
                    if av_price is not None:
                        results[symbol] = av_price
                    
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
        """Try to fetch prices using yfinance batch download."""
        results = {}
        
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
                                self._yfinance_failed = False
                        except Exception as e:
                            logger.debug(f"Error extracting {symbol} from batch: {e}")
                else:
                    logger.warning("yfinance batch download returned empty data")
                    self._yfinance_failed = True
                    
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'Too Many Requests' in error_str:
                self._yfinance_failed = True
                api_metrics_service.record_api_call(
                    service_name="yfinance",
                    success=False,
                    response_time_ms=0,
                    rate_limited=True
                )
                logger.warning("yfinance rate limited, switching to Alpha Vantage")
            else:
                logger.error(f"yfinance batch error: {e}")
        
        return results
    
    def _wait_for_alpha_vantage_rate_limit(self) -> bool:
        """
        Wait if needed to respect Alpha Vantage rate limit (5 calls/minute).
        Uses a global lock to prevent multiple concurrent calls from bypassing the limit.
        Returns True if wait was successful, False if we should skip this call.
        """
        with self._alpha_vantage_lock:
            current_time = time.time()
            time_since_last_call = current_time - self._last_alpha_vantage_call
            if time_since_last_call < self._alpha_vantage_min_interval:
                wait_time = self._alpha_vantage_min_interval - time_since_last_call
                # Only wait a short time to not block the entire request
                if wait_time > 5:
                    logger.debug(f"Alpha Vantage: Skipping {wait_time:.1f}s wait to avoid blocking")
                    return False
                logger.debug(f"Alpha Vantage: Waiting {wait_time:.1f}s for rate limit")
                time.sleep(wait_time)
            self._last_alpha_vantage_call = time.time()
            return True

    def _fetch_from_alpha_vantage(self, symbol: str) -> Optional[float]:
        """Fetch stock price from Alpha Vantage as fallback."""
        start_time = time.time()
        try:
            if not self._wait_for_alpha_vantage_rate_limit():
                logger.debug(f"Alpha Vantage: Skipping {symbol} due to rate limit")
                return None
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                logger.info(f"Alpha Vantage: Got price for {symbol}: {price}")
                
                api_metrics_service.record_api_call(
                    service_name="alpha_vantage",
                    success=True,
                    response_time_ms=elapsed_ms,
                    cached=False
                )
                return price
            
            if 'Note' in data or 'Information' in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}")
                api_metrics_service.record_api_call(
                    service_name="alpha_vantage",
                    success=False,
                    response_time_ms=elapsed_ms,
                    rate_limited=True
                )
                return None
            
            api_metrics_service.record_api_call(
                service_name="alpha_vantage",
                success=False,
                response_time_ms=elapsed_ms,
                cached=False
            )
            return None
            
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Alpha Vantage error for {symbol}: {e}")
            api_metrics_service.record_api_call(
                service_name="alpha_vantage",
                success=False,
                response_time_ms=elapsed_ms,
                cached=False
            )
            return None

    def _fetch_full_data_from_alpha_vantage(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch both price and previous close from Alpha Vantage."""
        start_time = time.time()
        try:
            if not self._wait_for_alpha_vantage_rate_limit():
                logger.debug(f"Alpha Vantage: Skipping full data for {symbol} due to rate limit")
                return None
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            elapsed_ms = (time.time() - start_time) * 1000
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = float(quote.get('05. price', 0))
                prev_close = float(quote.get('08. previous close', 0))
                
                if price > 0 and prev_close > 0:
                    logger.info(f"Alpha Vantage: Got full data for {symbol}")
                    api_metrics_service.record_api_call(
                        service_name="alpha_vantage_full",
                        success=True,
                        response_time_ms=elapsed_ms,
                        cached=False
                    )
                    return {"price": price, "previous_close": prev_close}
            
            if 'Note' in data or 'Information' in data:
                logger.warning(f"Alpha Vantage rate limit for {symbol}")
                api_metrics_service.record_api_call(
                    service_name="alpha_vantage_full",
                    success=False,
                    response_time_ms=elapsed_ms,
                    rate_limited=True
                )
            
            return None
        except Exception as e:
            elapsed_ms = (time.time() - start_time) * 1000
            logger.error(f"Alpha Vantage full data error for {symbol}: {e}")
            api_metrics_service.record_api_call(
                service_name="alpha_vantage_full",
                success=False,
                response_time_ms=elapsed_ms,
                cached=False
            )
            return None

    def _fetch_price_with_fallback(self, symbol: str) -> Optional[float]:
        """Fetch price with yfinance -> Alpha Vantage fallback, using deduplication."""
        def do_fetch():
            if not self._yfinance_failed:
                try:
                    ticker = yf.Ticker(symbol)
                    info = ticker.info
                    price = (
                        info.get('currentPrice') or 
                        info.get('regularMarketPrice') or 
                        info.get('previousClose')
                    )
                    
                    if price is not None:
                        self._yfinance_failed = False
                        return float(price)
                        
                except Exception as e:
                    error_str = str(e)
                    if '429' in error_str or 'Too Many Requests' in error_str:
                        self._yfinance_failed = True
                        logger.warning(f"yfinance rate limited for {symbol}")
                    else:
                        logger.error(f"yfinance error for {symbol}: {e}")
            
            return self._fetch_from_alpha_vantage(symbol)
        
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
        """Fetch intraday data with Alpha Vantage fallback."""
        data = {}
        start_time = time.time()
        
        for i, symbol in enumerate(symbols):
            if i > 0:
                time.sleep(0.3)  # Small delay between requests
            
            if self._yfinance_failed:
                av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                if av_data:
                    data[symbol] = av_data
                continue
            
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
                    self._yfinance_failed = False
                else:
                    av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                    if av_data:
                        data[symbol] = av_data
                        
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    self._yfinance_failed = True
                    logger.warning(f"yfinance rate limited, using Alpha Vantage")
                    
                av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                if av_data:
                    data[symbol] = av_data
        
        elapsed_ms = (time.time() - start_time) * 1000
        api_metrics_service.record_api_call(
            service_name="intraday_data",
            success=len(data) > 0,
            response_time_ms=elapsed_ms,
            cached=False
        )
        
        return data


stock_price_service = StockPriceService()
