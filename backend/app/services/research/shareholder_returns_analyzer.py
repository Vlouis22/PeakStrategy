import yfinance as yf
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, Optional

class ShareholderReturnsAnalyzer:
    """
    Analyzes shareholder returns including dividends and buybacks.
    Uses Yahoo Finance data with computed metrics where necessary.
    """
    
    def __init__(self, ticker: str):
        self.ticker = ticker
        self.stock = yf.Ticker(ticker)
        
    def get_shareholder_returns(self) -> Dict:
        """
        Returns a comprehensive dictionary of shareholder returns data.
        """
        try:
            # Fetch core data
            info = self.stock.info
            dividends = self.stock.dividends
            shares = self.stock.get_shares_full(start="2020-01-01")
            financials = self.stock.financials
            cash_flow = self.stock.cashflow
            
            # Get current stock price
            current_price = info.get('currentPrice') or info.get('regularMarketPrice', 0)
            
            # Calculate dividend metrics
            dividend_data = self._calculate_dividend_metrics(
                dividends, info, current_price, financials
            )
            
            # Calculate buyback metrics
            buyback_data = self._calculate_buyback_metrics(
                shares, cash_flow, current_price, info
            )
            
            return {
                'ticker': self.ticker,
                'current_price': current_price,
                'dividends': dividend_data,
                'buybacks': buyback_data,
                'timestamp': datetime.now().isoformat()
            }
            
        except Exception as e:
            return {
                'ticker': self.ticker,
                'error': str(e),
                'dividends': self._empty_dividend_data(),
                'buybacks': self._empty_buyback_data()
            }
    
    def _calculate_dividend_metrics(
        self, 
        dividends: pd.Series, 
        info: Dict, 
        current_price: float,
        financials: pd.DataFrame
    ) -> Dict:
        """Calculate all dividend-related metrics."""
        
        if dividends.empty or current_price == 0:
            return self._empty_dividend_data()
        
        # Get trailing twelve months dividends
        # Make datetime timezone-aware if dividends index is timezone-aware
        if hasattr(dividends.index, 'tz') and dividends.index.tz is not None:
            one_year_ago = pd.Timestamp.now(tz=dividends.index.tz) - pd.Timedelta(days=365)
        else:
            one_year_ago = pd.Timestamp.now() - pd.Timedelta(days=365)
        
        recent_divs = dividends[dividends.index >= one_year_ago]
        ttm_dividends = recent_divs.sum() if not recent_divs.empty else 0
        
        # Dividend Yield
        dividend_yield = (ttm_dividends / current_price * 100) if current_price > 0 else 0
        
        # Payout Ratio - from info or calculate from financials
        payout_ratio = info.get('payoutRatio')
        if payout_ratio is None and not financials.empty:
            try:
                # Get net income (most recent year)
                net_income = financials.loc['Net Income'].iloc[0] if 'Net Income' in financials.index else None
                shares_outstanding = info.get('sharesOutstanding', 0)
                
                if net_income and shares_outstanding and net_income > 0:
                    eps = net_income / shares_outstanding
                    annual_dividend = ttm_dividends
                    payout_ratio = (annual_dividend / eps) if eps > 0 else None
            except:
                payout_ratio = None
        
        # Convert payout ratio to percentage
        if payout_ratio is not None:
            payout_ratio = payout_ratio * 100 if payout_ratio <= 1 else payout_ratio
        
        # Dividend Growth - calculate 1-year and 3-year CAGR
        dividend_growth = self._calculate_dividend_growth(dividends)
        
        # Last dividend amount and date
        last_dividend = dividends.iloc[-1] if not dividends.empty else 0
        last_dividend_date = dividends.index[-1].strftime('%Y-%m-%d') if not dividends.empty else None
        
        return {
            'dividend_yield': round(dividend_yield, 2),
            'ttm_dividends': round(float(ttm_dividends), 4),
            'payout_ratio': round(payout_ratio, 2) if payout_ratio else None,
            'dividend_growth_1y': dividend_growth.get('1y'),
            'dividend_growth_3y': dividend_growth.get('3y'),
            'dividend_growth_5y': dividend_growth.get('5y'),
            'last_dividend': round(float(last_dividend), 4),
            'last_dividend_date': last_dividend_date,
            'has_dividend': bool(ttm_dividends > 0)
        }
    
    def _calculate_dividend_growth(self, dividends: pd.Series) -> Dict:
        """Calculate dividend growth rates over different periods."""
        
        if dividends.empty:
            return {'1y': None, '3y': None, '5y': None}
        
        growth_rates = {}
        
        for years, key in [(1, '1y'), (3, '3y'), (5, '5y')]:
            try:
                # Make datetime timezone-aware if dividends index is timezone-aware
                if hasattr(dividends.index, 'tz') and dividends.index.tz is not None:
                    cutoff_date = pd.Timestamp.now(tz=dividends.index.tz) - pd.Timedelta(days=years*365)
                else:
                    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=years*365)
                
                period_divs = dividends[dividends.index >= cutoff_date]
                
                if len(period_divs) < 2:
                    growth_rates[key] = None
                    continue
                
                # Calculate annual dividend for first and last year in period
                first_year = period_divs.index[0].year
                last_year = period_divs.index[-1].year
                
                first_year_total = period_divs[period_divs.index.year == first_year].sum()
                last_year_total = period_divs[period_divs.index.year == last_year].sum()
                
                if first_year_total > 0 and last_year_total > 0:
                    actual_years = last_year - first_year
                    if actual_years > 0:
                        cagr = ((last_year_total / first_year_total) ** (1/actual_years) - 1) * 100
                        growth_rates[key] = round(cagr, 2)
                    else:
                        growth_rates[key] = None
                else:
                    growth_rates[key] = None
                    
            except:
                growth_rates[key] = None
        
        return growth_rates
    
    def _calculate_buyback_metrics(
        self, 
        shares: pd.Series, 
        cash_flow: pd.DataFrame,
        current_price: float,
        info: Dict
    ) -> Dict:
        """Calculate all buyback-related metrics."""
        
        if shares.empty:
            return self._empty_buyback_data()
        
        # Shares outstanding trend
        current_shares = shares.iloc[-1]
        
        # Calculate 1-year, 3-year, 5-year change
        share_changes = self._calculate_share_changes(shares)
        
        # Buyback value from cash flow statement (TTM)
        buyback_value_ttm = None
        if not cash_flow.empty:
            try:
                # Look for "Repurchase Of Capital Stock" or similar
                buyback_row_names = [
                    'Repurchase Of Capital Stock',
                    'Stock Repurchase',
                    'Purchase Of Stock',
                    'Common Stock Repurchased'
                ]
                
                for row_name in buyback_row_names:
                    if row_name in cash_flow.index:
                        # Most recent value (TTM)
                        buyback_value_ttm = abs(cash_flow.loc[row_name].iloc[0])
                        break
            except:
                pass
        
        # Calculate buyback yield
        market_cap = info.get('marketCap', 0)
        buyback_yield = None
        if buyback_value_ttm and market_cap > 0:
            buyback_yield = (buyback_value_ttm / market_cap) * 100
        
        return {
            'current_shares_outstanding': int(current_shares) if current_shares else None,
            'shares_change_1y': share_changes.get('1y'),
            'shares_change_3y': share_changes.get('3y'),
            'shares_change_5y': share_changes.get('5y'),
            'buyback_value_ttm': int(buyback_value_ttm) if buyback_value_ttm else None,
            'buyback_yield': round(buyback_yield, 2) if buyback_yield else None,
            'is_buying_back': bool(share_changes.get('1y', 0) < 0)
        }
    
    def _calculate_share_changes(self, shares: pd.Series) -> Dict:
        """Calculate percentage change in shares outstanding over different periods."""
        
        if shares.empty:
            return {'1y': None, '3y': None, '5y': None}
        
        changes = {}
        current_shares = shares.iloc[-1]
        
        for years, key in [(1, '1y'), (3, '3y'), (5, '5y')]:
            try:
                # Make datetime timezone-aware if shares index is timezone-aware
                if hasattr(shares.index, 'tz') and shares.index.tz is not None:
                    cutoff_date = pd.Timestamp.now(tz=shares.index.tz) - pd.Timedelta(days=years*365)
                else:
                    cutoff_date = pd.Timestamp.now() - pd.Timedelta(days=years*365)
                
                historical_shares = shares[shares.index <= cutoff_date]
                
                if historical_shares.empty:
                    changes[key] = None
                    continue
                
                past_shares = historical_shares.iloc[-1]
                
                if past_shares > 0:
                    pct_change = ((current_shares - past_shares) / past_shares) * 100
                    changes[key] = round(pct_change, 2)
                else:
                    changes[key] = None
                    
            except:
                changes[key] = None
        
        return changes
    
    def _empty_dividend_data(self) -> Dict:
        """Return empty dividend data structure."""
        return {
            'dividend_yield': None,
            'ttm_dividends': None,
            'payout_ratio': None,
            'dividend_growth_1y': None,
            'dividend_growth_3y': None,
            'dividend_growth_5y': None,
            'last_dividend': None,
            'last_dividend_date': None,
            'has_dividend': False
        }
    
    def _empty_buyback_data(self) -> Dict:
        """Return empty buyback data structure."""
        return {
            'current_shares_outstanding': None,
            'shares_change_1y': None,
            'shares_change_3y': None,
            'shares_change_5y': None,
            'buyback_value_ttm': None,
            'buyback_yield': None,
            'is_buying_back': False
        }


# Example usage
if __name__ == "__main__":
    analyzer = ShareholderReturnsAnalyzer("AAPL")
    data = analyzer.get_shareholder_returns()
    
    import json
    print(json.dumps(data, indent=2))