# app/services/cache_warming_service.py
import threading
import time
import logging
from datetime import datetime
from typing import Set, List
from collections import defaultdict

logger = logging.getLogger(__name__)


class CacheWarmingService:
    """
    Service to warm cache with frequently accessed stock symbols.
    Reduces cold-start latency and API calls for popular symbols.
    """
    _instance = None
    _lock = threading.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._init_service()
        return cls._instance
    
    def _init_service(self):
        self._lock = threading.Lock()  # Thread-safe access to shared data
        self._popular_symbols: Set[str] = set()
        self._symbol_access_counts: defaultdict = defaultdict(int)
        self._last_warm_time: float = 0
        self._warm_interval: int = 600  # 10 minutes
        self._min_access_count: int = 3  # Min accesses to be considered "popular"
        self._is_warming: bool = False
        self._warming_thread: threading.Thread = None
        logger.info("CacheWarmingService initialized")
    
    def record_symbol_access(self, symbols: List[str]):
        """Record that symbols were accessed (thread-safe)."""
        with self._lock:
            for symbol in symbols:
                symbol = symbol.upper().strip()
                self._symbol_access_counts[symbol] += 1
                
                if self._symbol_access_counts[symbol] >= self._min_access_count:
                    self._popular_symbols.add(symbol)
    
    def get_popular_symbols(self) -> List[str]:
        """Get list of frequently accessed symbols (thread-safe)."""
        with self._lock:
            return list(self._popular_symbols)
    
    def should_warm_cache(self) -> bool:
        """Check if cache should be warmed based on time interval."""
        return (time.time() - self._last_warm_time) > self._warm_interval
    
    def start_background_warming(self):
        """Start background cache warming if needed (thread-safe)."""
        with self._lock:
            if self._is_warming or not self.should_warm_cache():
                return
            
            if not self._popular_symbols:
                return
            
            self._is_warming = True
        
        self._warming_thread = threading.Thread(
            target=self._warm_cache_background,
            daemon=True
        )
        self._warming_thread.start()
    
    def _warm_cache_background(self):
        """Background task to warm cache with popular symbols."""
        try:
            from app.services.stock_price_service import stock_price_service
            
            with self._lock:
                symbols = list(self._popular_symbols)[:20]  # Limit to top 20
            
            if symbols:
                logger.info(f"Warming cache for {len(symbols)} symbols: {symbols}")
                stock_price_service.get_prices(symbols, use_cache=False)
                with self._lock:
                    self._last_warm_time = time.time()
                logger.info("Cache warming completed")
                
        except Exception as e:
            logger.error(f"Cache warming failed: {e}")
        finally:
            with self._lock:
                self._is_warming = False
    
    def get_stats(self) -> dict:
        """Get cache warming statistics (thread-safe)."""
        with self._lock:
            return {
                "popular_symbols_count": len(self._popular_symbols),
                "popular_symbols": list(self._popular_symbols)[:10],
                "total_tracked_symbols": len(self._symbol_access_counts),
                "last_warm_time": datetime.fromtimestamp(self._last_warm_time).isoformat() if self._last_warm_time else None,
                "is_warming": self._is_warming
            }


cache_warming_service = CacheWarmingService()
