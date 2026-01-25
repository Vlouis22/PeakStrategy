import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import math

class BaseAnalyzer:
    """Base class for all stock analyzers with common utilities"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)
        self._info_cache = None
    
    @property
    def info(self) -> Dict[str, Any]:
        """Cached info property to avoid repeated API calls"""
        if self._info_cache is None:
            try:
                self._info_cache = self.stock.info
            except:
                self._info_cache = {}
        return self._info_cache
    
    def _safe_get(self, df: pd.DataFrame, key: str, default=None):
        """Safely extract value from dataframe"""
        try:
            if key in df.index:
                val = df[key]
                return float(val) if val is not None and str(val) != 'nan' else default
            return default
        except:
            return default
    
    def _safe_division(self, numerator: float, denominator: float) -> Optional[float]:
        """Safely divide two numbers"""
        if denominator is None or numerator is None or denominator == 0:
            return None
        try:
            result = numerator / denominator
            return None if math.isnan(result) or math.isinf(result) else result
        except:
            return None
    
    def _sanitize_value(self, value):
        """Convert NaN, infinity to None for JSON serialization"""
        if value is None:
            return None
        if isinstance(value, (int, float)) and (math.isnan(value) or math.isinf(value)):
            return None
        return value
