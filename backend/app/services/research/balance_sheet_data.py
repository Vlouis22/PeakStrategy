import yfinance as yf
from typing import Dict, Optional, Union

class BalanceSheetData:
    """
    Fetches and computes balance sheet and debt/liquidity metrics for stock analysis.
    Designed for professional investors with accurate financial calculations.
    """
    
    # Metric explanations for investor education
    METRIC_EXPLANATIONS = {
        'total_debt': 'The total amount of short-term and long-term debt obligations the company owes.',
        'net_debt': 'Total debt minus cash and liquid assets, showing the actual debt burden after accounting for available cash.',
        'debt_to_equity': 'Measures financial leverage by comparing total debt to shareholder equity; higher ratios indicate more debt financing.',
        'debt_to_ebitda': 'Shows how many years it would take to pay off all debt using earnings before interest, taxes, depreciation, and amortization.',
        'interest_coverage': 'Measures how easily a company can pay interest on outstanding debt using its earnings; higher is better.',
        'current_ratio': 'Measures ability to pay short-term obligations with current assets; a ratio above 1.0 indicates good short-term financial health.',
        'quick_ratio': 'Similar to current ratio but excludes inventory, providing a more conservative measure of liquidity.',
        'cash_and_short_term': 'Total cash and easily convertible short-term investments available for immediate use.',
    }
    
    def __init__(self, ticker: str):
        """
        Initialize with a stock ticker symbol.
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        """
        self.ticker = ticker.upper()
        self.stock = None
        self.balance_sheet = None
        self.financials = None
        self.info = None
        
    def fetch_data(self) -> Dict[str, Union[float, str, None, Dict]]:
        """
        Fetch balance sheet data and compute all metrics.
        
        Returns:
            Dictionary containing all debt and liquidity metrics with explanations
        """
        try:
            self.stock = yf.Ticker(self.ticker)
            self.balance_sheet = self.stock.balance_sheet
            self.financials = self.stock.financials
            self.info = self.stock.info
            
            if self.balance_sheet is None or self.balance_sheet.empty:
                raise ValueError(f"No balance sheet data available for {self.ticker}")
            
            # Get most recent column (latest data)
            latest_bs = self.balance_sheet.iloc[:, 0]
            latest_fin = self.financials.iloc[:, 0] if self.financials is not None and not self.financials.empty else None
            
            metrics = {
                'ticker': self.ticker,
                'date': str(self.balance_sheet.columns[0].date()) if len(self.balance_sheet.columns) > 0 else None,
                'explanations': self.METRIC_EXPLANATIONS,
            }
            
            # Fetch/compute debt metrics
            metrics.update(self._get_debt_metrics(latest_bs, latest_fin))
            
            # Fetch/compute liquidity metrics
            metrics.update(self._get_liquidity_metrics(latest_bs))
            
            return metrics
            
        except Exception as e:
            return {
                'ticker': self.ticker,
                'error': str(e),
                'total_debt': None,
                'net_debt': None,
                'debt_to_equity': None,
                'debt_to_ebitda': None,
                'interest_coverage': None,
                'current_ratio': None,
                'quick_ratio': None,
                'cash_and_short_term': None,
                'explanations': self.METRIC_EXPLANATIONS,
            }
    
    def _safe_get(self, df, key: str, default=None):
        """Safely get value from dataframe."""
        try:
            if key in df.index:
                val = df[key]
                return float(val) if val is not None and str(val) != 'nan' else default
            return default
        except:
            return default
    
    def _get_debt_metrics(self, bs, fin) -> Dict[str, Optional[float]]:
        """Calculate debt and leverage metrics."""
        metrics = {}
        
        # Total Debt = Long-term debt + Short-term debt
        long_term_debt = self._safe_get(bs, 'Long Term Debt', 0)
        short_term_debt = self._safe_get(bs, 'Current Debt', 0)
        
        # Alternative field names
        if long_term_debt == 0:
            long_term_debt = self._safe_get(bs, 'Long Term Debt And Capital Lease Obligation', 0)
        if short_term_debt == 0:
            short_term_debt = self._safe_get(bs, 'Current Debt And Capital Lease Obligation', 0)
        
        total_debt = long_term_debt + short_term_debt
        metrics['total_debt'] = total_debt if total_debt > 0 else None
        
        # Cash & Short-term Investments
        cash = self._safe_get(bs, 'Cash And Cash Equivalents', 0)
        short_term_inv = self._safe_get(bs, 'Other Short Term Investments', 0)
        cash_and_short_term = cash + short_term_inv
        metrics['cash_and_short_term'] = cash_and_short_term if cash_and_short_term > 0 else None
        
        # Net Debt = Total Debt - Cash & Short-term Investments
        if total_debt is not None and cash_and_short_term is not None:
            metrics['net_debt'] = total_debt - cash_and_short_term
        else:
            metrics['net_debt'] = None
        
        # Debt to Equity
        total_equity = self._safe_get(bs, 'Stockholders Equity')
        if total_equity is None:
            total_equity = self._safe_get(bs, 'Total Equity Gross Minority Interest')
        
        if total_debt and total_equity and total_equity != 0:
            metrics['debt_to_equity'] = total_debt / total_equity
        else:
            metrics['debt_to_equity'] = None
        
        # EBITDA calculation for Debt/EBITDA
        ebitda = self._calculate_ebitda(fin)
        if total_debt and ebitda and ebitda != 0:
            metrics['debt_to_ebitda'] = total_debt / ebitda
        else:
            metrics['debt_to_ebitda'] = None
        
        # Interest Coverage Ratio = EBIT / Interest Expense
        ebit = self._safe_get(fin, 'EBIT') if fin is not None else None
        interest_expense = self._safe_get(fin, 'Interest Expense') if fin is not None else None
        
        if interest_expense is None and fin is not None:
            interest_expense = self._safe_get(fin, 'Interest Expense Non Operating')
        
        if ebit and interest_expense and interest_expense != 0:
            # Interest expense is typically negative, so we use absolute value
            metrics['interest_coverage'] = ebit / abs(interest_expense)
        else:
            metrics['interest_coverage'] = None
        
        return metrics
    
    def _get_liquidity_metrics(self, bs) -> Dict[str, Optional[float]]:
        """Calculate liquidity metrics."""
        metrics = {}
        
        # Current Ratio = Current Assets / Current Liabilities
        current_assets = self._safe_get(bs, 'Current Assets')
        current_liabilities = self._safe_get(bs, 'Current Liabilities')
        
        if current_assets and current_liabilities and current_liabilities != 0:
            metrics['current_ratio'] = current_assets / current_liabilities
        else:
            metrics['current_ratio'] = None
        
        # Quick Ratio = (Current Assets - Inventory) / Current Liabilities
        inventory = self._safe_get(bs, 'Inventory', 0)
        
        if current_assets and current_liabilities and current_liabilities != 0:
            quick_assets = current_assets - inventory
            metrics['quick_ratio'] = quick_assets / current_liabilities
        else:
            metrics['quick_ratio'] = None
        
        return metrics
    
    def _calculate_ebitda(self, fin) -> Optional[float]:
        """
        Calculate EBITDA from financial statements.
        EBITDA = EBIT + Depreciation + Amortization
        or EBITDA = Net Income + Interest + Taxes + Depreciation + Amortization
        """
        if fin is None:
            return None
        
        # Try to get EBITDA directly
        ebitda = self._safe_get(fin, 'EBITDA')
        if ebitda:
            return ebitda
        
        # Calculate from EBIT
        ebit = self._safe_get(fin, 'EBIT')
        if ebit:
            depreciation = self._safe_get(fin, 'Depreciation', 0)
            amortization = self._safe_get(fin, 'Amortization', 0)
            dep_amort = self._safe_get(fin, 'Depreciation And Amortization', 0)
            
            if dep_amort > 0:
                return ebit + dep_amort
            elif depreciation > 0 or amortization > 0:
                return ebit + depreciation + amortization
        
        # Calculate from Operating Income
        operating_income = self._safe_get(fin, 'Operating Income')
        if operating_income:
            dep_amort = self._safe_get(fin, 'Depreciation And Amortization', 0)
            if dep_amort > 0:
                return operating_income + dep_amort
        
        return None


# Example usage
if __name__ == "__main__":
    # Test with Apple
    bs_data = BalanceSheetData("AAPL")
    result = bs_data.fetch_data()
    
    print(f"\nBalance Sheet Metrics for {result['ticker']}")
    print(f"Date: {result.get('date', 'N/A')}")
    print("\nDebt & Leverage:")
    print(f"  Total Debt: ${result['total_debt']:,.0f}" if result['total_debt'] else "  Total Debt: N/A")
    print(f"  Net Debt: ${result['net_debt']:,.0f}" if result['net_debt'] else "  Net Debt: N/A")
    print(f"  Debt/Equity: {result['debt_to_equity']:.2f}" if result['debt_to_equity'] else "  Debt/Equity: N/A")
    print(f"  Debt/EBITDA: {result['debt_to_ebitda']:.2f}" if result['debt_to_ebitda'] else "  Debt/EBITDA: N/A")
    print(f"  Interest Coverage: {result['interest_coverage']:.2f}x" if result['interest_coverage'] else "  Interest Coverage: N/A")
    print("\nLiquidity:")
    print(f"  Current Ratio: {result['current_ratio']:.2f}" if result['current_ratio'] else "  Current Ratio: N/A")
    print(f"  Quick Ratio: {result['quick_ratio']:.2f}" if result['quick_ratio'] else "  Quick Ratio: N/A")
    print(f"  Cash & Short-term: ${result['cash_and_short_term']:,.0f}" if result['cash_and_short_term'] else "  Cash & Short-term: N/A")