import yfinance as yf
from typing import Dict, Any, Optional, Tuple
from datetime import datetime
from .baze_analyzer import BaseAnalyzer

class SnapshotAnalyzer(BaseAnalyzer):
    """Handles snapshot data and scoring pillars"""
    
    def get_snapshot_row(self) -> Dict[str, Any]:
        """Get main snapshot row data"""
        try:
            current_price = self._get_current_price()
            day_change = self._get_day_change()
            day_change_percent = self._get_day_change_percent()
            week_range_low, week_range_high = self._get_52w_range_values()
            
            return {
                "ticker": self.ticker,
                "metrics": {
                    "price": f"${current_price:.2f}" if current_price is not None else "",
                    "day": f"{day_change_percent:+.2f}%" if day_change_percent is not None else "",
                    "day_change": f"{day_change:+.2f}" if day_change is not None else "",
                    "day_color": "green" if day_change_percent and day_change_percent >= 0 else "red",
                    "market_cap": self._format_market_cap(),
                    "week_52_range": self._format_52w_range(week_range_low, week_range_high),
                    "week_52_range_bar": self._create_range_bar(current_price, week_range_low, week_range_high),
                    "sector": self.info.get('sector', ''),
                    "industry": self.info.get('industry', '')
                },
                "timestamp": datetime.now().isoformat()
            }
        except:
            return {
                "ticker": self.ticker,
                "metrics": {
                    "price": "", "day": "", "day_change": "", "day_color": "neutral",
                    "market_cap": "", "week_52_range": "", "week_52_range_bar": "",
                    "sector": "", "industry": ""
                },
                "timestamp": datetime.now().isoformat()
            }
    
    def get_scoring_pillars(self) -> Dict[str, Any]:
        """Get scoring pillars data"""
        return {
            "Valuation": {"rating": ""},
            "Profitability": {"rating": ""},
            "Financial Health": {"rating": ""},
            "Shareholder Returns": {"rating": ""},
            "Growth Outlook": {"rating": ""}
        }
    
    def _get_current_price(self) -> Optional[float]:
        """Get current stock price"""
        for field in ['regularMarketPrice', 'currentPrice', 'ask', 'bid', 'previousClose']:
            if field in self.info and self.info[field] is not None:
                return float(self.info[field])
        
        try:
            hist = self.stock.history(period='1d', interval='1m')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
        except:
            pass
        return None
    
    def _get_day_change(self) -> Optional[float]:
        """Get day change amount"""
        current_price = self._get_current_price()
        previous_close = self.info.get('previousClose')
        if current_price and previous_close and previous_close > 0:
            return round(current_price - previous_close, 2)
        return None
    
    def _get_day_change_percent(self) -> Optional[float]:
        """Get day change percentage"""
        if 'regularMarketChangePercent' in self.info and self.info['regularMarketChangePercent']:
            return round(self.info['regularMarketChangePercent'], 2)
        
        day_change = self._get_day_change()
        previous_close = self.info.get('previousClose')
        if day_change and previous_close and previous_close > 0:
            return round((day_change / previous_close), 2)
        return None
    
    def _format_market_cap(self) -> str:
        """Format market cap"""
        market_cap = self.info.get('marketCap')
        if not market_cap:
            return ""
        
        if market_cap >= 1e12:
            return f"${market_cap/1e12:.1f}T"
        elif market_cap >= 1e9:
            return f"${market_cap/1e9:.1f}B"
        elif market_cap >= 1e6:
            return f"${market_cap/1e6:.1f}M"
        return f"${market_cap:,.0f}"
    
    def _get_52w_range_values(self) -> Tuple[Optional[float], Optional[float]]:
        """Get 52-week range values"""
        low = self.info.get('fiftyTwoWeekLow')
        high = self.info.get('fiftyTwoWeekHigh')
        return (float(low), float(high)) if low and high else (None, None)
    
    def _format_52w_range(self, low: Optional[float], high: Optional[float]) -> str:
        """Format 52-week range string"""
        return f"${low:.2f} - ${high:.2f}" if low and high else ""
    
    def _create_range_bar(self, current: Optional[float], low: Optional[float], high: Optional[float]) -> str:
        """Create visual bar for 52-week range"""
        if current and low and high and high > low:
            position = (current - low) / (high - low)
            filled = max(0, min(10, int(position * 10)))
            return "▓" * filled + "░" * (10 - filled)
        return ""
