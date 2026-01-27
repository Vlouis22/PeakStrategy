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
    
    def get_scoring_pillars(self, 
                       valuation_data: Dict[str, Any],
                       profitability_data: Dict[str, Any],
                       balance_sheet_data: Dict[str, Any],
                       shareholder_data: Dict[str, Any],
                       analyst_data: Dict[str, Any]) -> Dict[str, Any]:
    
        def calculate_valuation_rating() -> int:
            """Calculate valuation rating matching the valuation scorecard logic"""
            scorecard = valuation_data.get('scorecard', {})
            
            # Use the overall valuation score from the valuation analyzer
            overall_score = scorecard.get('overallScore')
            
            if overall_score is None:
                return None
            
            # Convert 10-point scale to 5-point scale
            # 10-point: 1-10, 5-point: 1-5
            # Simple mapping: divide by 2 and round
            five_point_score = round(overall_score / 2)
            
            # Ensure it's within 1-5 range
            return max(1, min(5, five_point_score))
    
        def calculate_profitability_rating() -> int:
            """Calculate profitability rating based on margins and returns"""
            score = 0
            count = 0
            
            metrics = profitability_data.get('metrics', {})
            
            # ROE - most important profitability metric
            roe = metrics.get('roe')
            if roe is not None:
                if roe > 25:
                    score += 5
                elif roe > 18:
                    score += 4
                elif roe > 12:
                    score += 3
                elif roe > 6:
                    score += 2
                elif roe > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # Operating Margin
            op_margin = metrics.get('operating_margin')
            if op_margin is not None:
                if op_margin > 25:
                    score += 5
                elif op_margin > 18:
                    score += 4
                elif op_margin > 12:
                    score += 3
                elif op_margin > 6:
                    score += 2
                elif op_margin > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # Net Margin
            net_margin = metrics.get('net_margin')
            if net_margin is not None:
                if net_margin > 20:
                    score += 5
                elif net_margin > 15:
                    score += 4
                elif net_margin > 10:
                    score += 3
                elif net_margin > 5:
                    score += 2
                elif net_margin > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # ROA
            roa = metrics.get('roa')
            if roa is not None:
                if roa > 12:
                    score += 5
                elif roa > 8:
                    score += 4
                elif roa > 5:
                    score += 3
                elif roa > 2:
                    score += 2
                elif roa > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # ROIC if available
            roic = metrics.get('roic')
            if roic is not None:
                if roic > 20:
                    score += 5
                elif roic > 15:
                    score += 4
                elif roic > 10:
                    score += 3
                elif roic > 5:
                    score += 2
                elif roic > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            if count == 0:
                return None
            
            avg_score = score / count
            return max(1, round(avg_score))
    
        def calculate_financial_health_rating() -> int:
            """Calculate financial health rating"""
            score = 0
            count = 0
            
            # Current Ratio
            current_ratio = balance_sheet_data.get('current_ratio')
            if current_ratio is not None:
                if current_ratio > 2.5:
                    score += 5
                elif current_ratio > 1.8:
                    score += 4
                elif current_ratio > 1.2:
                    score += 3
                elif current_ratio > 0.8:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Quick Ratio
            quick_ratio = balance_sheet_data.get('quick_ratio')
            if quick_ratio is not None:
                if quick_ratio > 1.5:
                    score += 5
                elif quick_ratio > 1.0:
                    score += 4
                elif quick_ratio > 0.75:
                    score += 3
                elif quick_ratio > 0.5:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Debt to Equity - lower is better
            debt_to_equity = balance_sheet_data.get('debt_to_equity')
            if debt_to_equity is not None:
                if debt_to_equity < 0.3:
                    score += 5
                elif debt_to_equity < 0.6:
                    score += 4
                elif debt_to_equity < 1.0:
                    score += 3
                elif debt_to_equity < 1.5:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Interest Coverage - higher is better
            interest_coverage = balance_sheet_data.get('interest_coverage')
            if interest_coverage is not None:
                if interest_coverage > 10:
                    score += 5
                elif interest_coverage > 6:
                    score += 4
                elif interest_coverage > 3:
                    score += 3
                elif interest_coverage > 1.5:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Debt to EBITDA - lower is better
            debt_to_ebitda = balance_sheet_data.get('debt_to_ebitda')
            if debt_to_ebitda is not None:
                if debt_to_ebitda < 1.5:
                    score += 5
                elif debt_to_ebitda < 2.5:
                    score += 4
                elif debt_to_ebitda < 4.0:
                    score += 3
                elif debt_to_ebitda < 6.0:
                    score += 2
                else:
                    score += 1
                count += 1
            
            if count == 0:
                return None
            
            avg_score = score / count
            return max(1, round(avg_score))
        
        def calculate_shareholder_returns_rating() -> int:
            """Calculate shareholder returns rating"""
            score = 0
            count = 0
            
            dividends = shareholder_data.get('dividends', {})
            buybacks = shareholder_data.get('buybacks', {})
            
            has_dividend = dividends.get('has_dividend', False)
            is_buying_back = buybacks.get('is_buying_back', False)
            
            # If no dividend and no buyback, return low score
            if not has_dividend and not is_buying_back:
                return 1
            
            # Dividend Yield
            div_yield = dividends.get('dividend_yield')
            if div_yield is not None and div_yield > 0:
                if div_yield > 4.0:
                    score += 5
                elif div_yield > 3.0:
                    score += 4
                elif div_yield > 2.0:
                    score += 3
                elif div_yield > 1.0:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Payout Ratio - sustainable range is best
            payout = dividends.get('payout_ratio')
            if payout is not None:
                if 30 <= payout <= 60:
                    score += 5
                elif 20 <= payout < 30 or 60 < payout <= 75:
                    score += 4
                elif 10 <= payout < 20 or 75 < payout <= 85:
                    score += 3
                elif payout < 10 or 85 < payout < 100:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Dividend Growth
            div_growth_5y = dividends.get('dividend_growth_5y')
            if div_growth_5y is not None:
                if div_growth_5y > 10:
                    score += 5
                elif div_growth_5y > 7:
                    score += 4
                elif div_growth_5y > 4:
                    score += 3
                elif div_growth_5y > 0:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Share Buybacks - negative is good (share count decreasing)
            shares_change_1y = buybacks.get('shares_change_1y')
            if shares_change_1y is not None:
                if shares_change_1y < -5:
                    score += 5
                elif shares_change_1y < -2:
                    score += 4
                elif shares_change_1y < 0:
                    score += 3
                elif shares_change_1y < 3:
                    score += 2
                else:
                    score += 1
                count += 1
            
            # Buyback Yield
            buyback_yield = buybacks.get('buyback_yield')
            if buyback_yield is not None and buyback_yield > 0:
                if buyback_yield > 5:
                    score += 5
                elif buyback_yield > 3:
                    score += 4
                elif buyback_yield > 1:
                    score += 3
                elif buyback_yield > 0:
                    score += 2
                else:
                    score += 1
                count += 1
            
            if count == 0:
                return None
            
            avg_score = score / count
            return max(1, round(avg_score))
        
        def calculate_growth_outlook_rating() -> int:
            """Calculate growth outlook rating"""
            score = 0
            count = 0
            
            growth_profile = analyst_data.get('growth_profile', {})
            revenue_growth = growth_profile.get('revenue_growth', {})
            earnings_growth = growth_profile.get('earnings_growth', {})
            analyst_estimates = growth_profile.get('analyst_estimates', {})
            
            # Revenue Growth YoY (most recent)
            rev_yoy = revenue_growth.get('yoy_current')
            if rev_yoy is not None:
                rev_pct = rev_yoy * 100
                if rev_pct > 25:
                    score += 5
                elif rev_pct > 15:
                    score += 4
                elif rev_pct > 8:
                    score += 3
                elif rev_pct > 3:
                    score += 2
                elif rev_pct > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # Earnings Growth YoY
            earn_yoy = earnings_growth.get('yoy_current')
            if earn_yoy is not None:
                earn_pct = earn_yoy * 100
                if earn_pct > 30:
                    score += 5
                elif earn_pct > 20:
                    score += 4
                elif earn_pct > 12:
                    score += 3
                elif earn_pct > 5:
                    score += 2
                elif earn_pct > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # Projected Revenue Growth Next Year
            rev_proj = revenue_growth.get('yoy_projected_next_year')
            if rev_proj is not None:
                rev_proj_pct = rev_proj * 100
                if rev_proj_pct > 20:
                    score += 5
                elif rev_proj_pct > 15:
                    score += 4
                elif rev_proj_pct > 10:
                    score += 3
                elif rev_proj_pct > 5:
                    score += 2
                elif rev_proj_pct > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # Projected Earnings Growth Next Year
            earn_proj = earnings_growth.get('yoy_projected_next_year')
            if earn_proj is not None:
                earn_proj_pct = earn_proj * 100
                if earn_proj_pct > 25:
                    score += 5
                elif earn_proj_pct > 18:
                    score += 4
                elif earn_proj_pct > 12:
                    score += 3
                elif earn_proj_pct > 6:
                    score += 2
                elif earn_proj_pct > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            # 5-Year Growth Estimate (CAGR)
            growth_5y = analyst_estimates.get('growth_next_5_years')
            if growth_5y is not None:
                growth_5y_pct = growth_5y * 100
                if growth_5y_pct > 20:
                    score += 5
                elif growth_5y_pct > 15:
                    score += 4
                elif growth_5y_pct > 10:
                    score += 3
                elif growth_5y_pct > 5:
                    score += 2
                elif growth_5y_pct > 0:
                    score += 1
                else:
                    score += 0
                count += 1
            
            if count == 0:
                return None
            
            avg_score = score / count
            return max(1, round(avg_score))
        
        return {
            "Valuation": {"rating": calculate_valuation_rating()},
            "Profitability": {"rating": calculate_profitability_rating()},
            "Financial Health": {"rating": calculate_financial_health_rating()},
            "Shareholder Returns": {"rating": calculate_shareholder_returns_rating()},
            "Growth Outlook": {"rating": calculate_growth_outlook_rating()}
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
