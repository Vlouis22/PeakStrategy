# app/services/stock_price_service.py
import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
import threading
import time
from typing import Dict, List, Optional
import os
import requests

from app.services.redis_service import RedisService


class StockPriceService:
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(StockPriceService, cls).__new__(cls)
            cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        """Initialize Redis configuration"""
        self.redis_service = RedisService.get_instance()
        self.cache_duration_seconds = 900  # 15 minutes - longer cache to reduce Yahoo Finance API calls
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY', 'demo')  # 'demo' works with limited symbols
        self._yfinance_failed = False  # Track if yfinance is failing (rate limited)
        self._last_alpha_vantage_call = 0  # Track last AV call time for rate limiting
        self._alpha_vantage_min_interval = 12  # 12 seconds between calls (5/min limit)
        print("🚀 Initializing StockPriceService with RedisService...")
    
    def _get_price_cache_key(self, symbol: str) -> str:
        """Generate cache key for stock price"""
        return f"stock_price:{symbol}"
    
    def _get_full_data_cache_key(self, symbol: str) -> str:
        """Generate cache key for full stock data"""
        return f"stock_full_data:{symbol}"
    
    def get_price(self, symbol: str, use_cache: bool = True):
        """
        Get stock price with Redis caching.
        
        Args:
            symbol: Stock ticker symbol (e.g., 'AAPL')
            use_cache: Whether to use cached prices (default: True)
            
        Returns:
            Current price if available, None otherwise
        """
        symbol = symbol.upper().strip()
        
        # Try to get from Redis cache first
        if use_cache:
            cache_key = self._get_price_cache_key(symbol)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                # Check if cache is still valid
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.cache_duration_seconds:
                            price = cached_data.get("price")
                            if price is not None:
                                return price
                    except Exception as e:
                        print(f"Error parsing cache timestamp for {symbol}: {e}")
        
        # Fetch from yfinance
        price = self._fetch_from_yfinance(symbol)
        
        # Update Redis cache
        if price is not None:
            cache_key = self._get_price_cache_key(symbol)
            cache_data = {
                "price": price,
                "timestamp": datetime.now().isoformat(),
                "symbol": symbol
            }
            self.redis_service.set(cache_key, cache_data, self.cache_duration_seconds)
        
        return price
    
    def get_prices(self, symbols, use_cache: bool = True):
        """
        Get multiple stock prices with Redis caching.
        
        Args:
            symbols: List of stock ticker symbols
            use_cache: Whether to use cached prices
            
        Returns:
            Dictionary mapping symbols to prices
        """
        symbols = [s.upper().strip() for s in symbols]
        
        results = {}
        symbols_to_fetch = []
        
        # Try to get from Redis cache first
        for symbol in symbols:
            if use_cache:
                cache_key = self._get_price_cache_key(symbol)
                cached_data = self.redis_service.get(cache_key)
                
                if cached_data:
                    # Check if cache is still valid
                    timestamp_str = cached_data.get("timestamp")
                    if timestamp_str:
                        try:
                            cached_time = datetime.fromisoformat(timestamp_str)
                            age = (datetime.now() - cached_time).total_seconds()
                            if age < self.cache_duration_seconds:
                                price = cached_data.get("price")
                                if price is not None:
                                    results[symbol] = price
                                    continue
                        except Exception as e:
                            print(f"Error parsing cache timestamp for {symbol}: {e}")
            symbols_to_fetch.append(symbol)
        
        # Fetch remaining symbols from yfinance
        if symbols_to_fetch:
            fetched_prices = self._fetch_multiple_from_yfinance(symbols_to_fetch)
            results.update(fetched_prices)
            
            # Update Redis cache with fetched prices
            for symbol, price in fetched_prices.items():
                if price is not None:
                    cache_key = self._get_price_cache_key(symbol)
                    cache_data = {
                        "price": price,
                        "timestamp": datetime.now().isoformat(),
                        "symbol": symbol
                    }
                    self.redis_service.set(cache_key, cache_data, self.cache_duration_seconds)
        
        return results
    
    def _wait_for_alpha_vantage_rate_limit(self):
        """Wait if needed to respect Alpha Vantage rate limit (5 calls/minute)"""
        current_time = time.time()
        time_since_last_call = current_time - self._last_alpha_vantage_call
        if time_since_last_call < self._alpha_vantage_min_interval:
            wait_time = self._alpha_vantage_min_interval - time_since_last_call
            print(f"Alpha Vantage: Waiting {wait_time:.1f}s for rate limit...")
            time.sleep(wait_time)
        self._last_alpha_vantage_call = time.time()

    def _fetch_from_alpha_vantage(self, symbol: str):
        """Fetch stock price from Alpha Vantage as fallback"""
        try:
            # Respect rate limit
            self._wait_for_alpha_vantage_rate_limit()
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data and '05. price' in data['Global Quote']:
                price = float(data['Global Quote']['05. price'])
                print(f"Alpha Vantage: Got price for {symbol}: {price}")
                return price
            
            # Check for rate limit message
            if 'Note' in data or 'Information' in data:
                print(f"Alpha Vantage rate limit or info message for {symbol}")
                return None
            
            return None
        except Exception as e:
            print(f"Alpha Vantage error for {symbol}: {e}")
            return None

    def _fetch_full_data_from_alpha_vantage(self, symbol: str) -> Optional[Dict[str, float]]:
        """Fetch both price and previous close from Alpha Vantage"""
        try:
            # Respect rate limit
            self._wait_for_alpha_vantage_rate_limit()
            
            url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={self.alpha_vantage_key}"
            response = requests.get(url, timeout=10)
            data = response.json()
            
            if 'Global Quote' in data:
                quote = data['Global Quote']
                price = float(quote.get('05. price', 0))
                prev_close = float(quote.get('08. previous close', 0))
                
                if price > 0 and prev_close > 0:
                    print(f"Alpha Vantage: Got full data for {symbol}: price={price}, prev_close={prev_close}")
                    return {"price": price, "previous_close": prev_close}
            
            # Check for rate limit message
            if 'Note' in data or 'Information' in data:
                print(f"Alpha Vantage rate limit for {symbol}")
            
            return None
        except Exception as e:
            print(f"Alpha Vantage full data error for {symbol}: {e}")
            return None

    def _fetch_from_yfinance(self, symbol: str):
        """Fetch single stock price from yfinance"""
        try:
            with threading.Lock():  # yfinance might not be thread-safe
                ticker = yf.Ticker(symbol)
                
                # Try multiple price fields
                info = ticker.info
                price = (
                    info.get('currentPrice') or 
                    info.get('regularMarketPrice') or 
                    info.get('previousClose')
                )
                
                if price is not None:
                    self._yfinance_failed = False
                    return float(price)
                
                # Fallback: try to get the latest price from history
                hist = ticker.history(period='1d', interval='1m')
                if not hist.empty:
                    self._yfinance_failed = False
                    return float(hist['Close'].iloc[-1])
                
                return None
        except Exception as e:
            error_str = str(e)
            if '429' in error_str or 'Too Many Requests' in error_str:
                self._yfinance_failed = True
                print(f"yfinance rate limited for {symbol}, trying Alpha Vantage...")
                return self._fetch_from_alpha_vantage(symbol)
            print(f"Error fetching price for {symbol}: {e}")
            return None
    
    def _fetch_multiple_from_yfinance(self, symbols):
        """
        Fetch multiple stock prices efficiently.
        Note: yfinance supports batch downloads but has limits.
        """
        results = {}
        
        if len(symbols) > 10:  # Reduced batch size to avoid Yahoo Finance issues
            # yfinance has limits, fetch in smaller batches
            for i in range(0, len(symbols), 10):
                batch = symbols[i:i + 10]
                batch_results = self._fetch_yfinance_batch_safe(batch)  # Use safe method
                results.update(batch_results)
        else:
            results = self._fetch_yfinance_batch_safe(symbols)
        
        return results
    
    def _fetch_yfinance_batch_safe(self, symbols):
        """Safer method to fetch batch of symbols, using individual fetches if batch fails"""
        results = {}
        
        try:
            with threading.Lock():
                # Try batch download first
                tickers = yf.download(
                    " ".join(symbols),
                    period="1d",
                    interval="1m",
                    group_by='ticker',
                    progress=False,
                    auto_adjust=True  # Add this to fix the warning
                )
                
                # Check if we got valid data
                if tickers is not None and not tickers.empty:
                    for symbol in symbols:
                        try:
                            if symbol in tickers:
                                # Get the latest available price
                                price = tickers[symbol]['Close'].iloc[-1]
                                if not pd.isna(price):
                                    results[symbol] = float(price)
                                else:
                                    # Fallback to individual fetch
                                    results[symbol] = self._fetch_from_yfinance(symbol)
                            else:
                                # Fallback to individual fetch
                                results[symbol] = self._fetch_from_yfinance(symbol)
                        except Exception as e:
                            print(f"Error processing {symbol} in batch: {e}")
                            results[symbol] = self._fetch_from_yfinance(symbol)
                else:
                    # Batch failed, fallback to individual fetches
                    print("Batch download failed, falling back to individual fetches")
                    for symbol in symbols:
                        results[symbol] = self._fetch_from_yfinance(symbol)
                        
        except Exception as e:
            print(f"Batch fetch failed: {e}")
            # Fallback to individual fetches with rate limiting
            print("Falling back to individual symbol fetches...")
            for i, symbol in enumerate(symbols):
                if i > 0:
                    time.sleep(0.5)  # 500ms delay to avoid rate limiting
                results[symbol] = self._fetch_from_yfinance(symbol)
        
        return results

    def get_intraday_and_previous_close(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """
        Get intraday price and previous close for multiple symbols with Redis caching.
        
        Returns:
        {
            "AAPL": {
                "price": float,
                "previous_close": float
            }
        }
        """
        data = {}
        symbols_to_fetch = []
        
        # Try Redis cache first
        for symbol in symbols:
            symbol_upper = symbol.upper().strip()
            cache_key = self._get_full_data_cache_key(symbol_upper)
            cached_data = self.redis_service.get(cache_key)
            
            if cached_data:
                # Check if cache is still valid
                timestamp_str = cached_data.get("timestamp")
                if timestamp_str:
                    try:
                        cached_time = datetime.fromisoformat(timestamp_str)
                        age = (datetime.now() - cached_time).total_seconds()
                        if age < self.cache_duration_seconds:
                            data[symbol_upper] = {
                                "price": cached_data.get("price"),
                                "previous_close": cached_data.get("previous_close")
                            }
                            continue
                    except Exception as e:
                        print(f"Error parsing cache timestamp for {symbol_upper}: {e}")
            
            symbols_to_fetch.append(symbol_upper)
        
        # Fetch remaining symbols from yfinance
        if symbols_to_fetch:
            fetched_data = self._fetch_intraday_and_previous_close_safe(symbols_to_fetch)
            
            # Cache the results in Redis
            for symbol, symbol_data in fetched_data.items():
                if symbol_data["price"] is not None and symbol_data["previous_close"] is not None:
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
    
    def _fetch_intraday_and_previous_close_safe(self, symbols: List[str]) -> Dict[str, Dict[str, float]]:
        """Safer method to fetch intraday and previous close with Alpha Vantage fallback"""
        data = {}
        
        # Try individual fetches instead of batch to avoid Yahoo Finance issues
        for i, symbol in enumerate(symbols):
            # Add delay between requests to avoid rate limiting
            if i > 0:
                time.sleep(0.5)  # 500ms delay between requests
            
            # If yfinance is known to be failing, skip directly to Alpha Vantage
            if self._yfinance_failed:
                av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                if av_data:
                    data[symbol] = av_data
                continue
            
            try:
                ticker = yf.Ticker(symbol)
                info = ticker.info
                
                # Try to get current price
                price = info.get("regularMarketPrice")
                if price is None:
                    price = info.get('currentPrice') or info.get('previousClose')
                
                # Try to get previous close
                prev_close = info.get("regularMarketPreviousClose")
                
                if price is not None and prev_close is not None:
                    data[symbol] = {
                        "price": float(price),
                        "previous_close": float(prev_close)
                    }
                else:
                    # Fallback: use history for previous close
                    try:
                        hist = ticker.history(period="2d", interval="1d")
                        if not hist.empty:
                            if price is None:
                                price = hist['Close'].iloc[-1]
                            if prev_close is None and len(hist) > 1:
                                prev_close = hist['Close'].iloc[-2]
                            
                            data[symbol] = {
                                "price": float(price) if price is not None else 0.0,
                                "previous_close": float(prev_close) if prev_close is not None else float(price) if price is not None else 0.0
                            }
                    except Exception as hist_error:
                        print(f"Error fetching history for {symbol}: {hist_error}")
                        # Try Alpha Vantage as fallback
                        av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                        if av_data:
                            data[symbol] = av_data
                        continue
                        
            except Exception as e:
                error_str = str(e)
                if '429' in error_str or 'Too Many Requests' in error_str:
                    self._yfinance_failed = True
                    print(f"yfinance rate limited for {symbol}, trying Alpha Vantage...")
                    av_data = self._fetch_full_data_from_alpha_vantage(symbol)
                    if av_data:
                        data[symbol] = av_data
                else:
                    print(f"Error processing {symbol}: {e}")
                continue
        
        return data

# Global instance
stock_price_service = StockPriceService()
print("✅ StockPriceService initialized with RedisService")