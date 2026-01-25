import yfinance as yf
from typing import Dict, Any, Optional
from .baze_analyzer import BaseAnalyzer


class BalanceSheetAnalyzer(BaseAnalyzer):
    """Fetches and computes balance sheet and debt/liquidity metrics"""
    
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
    
    def fetch_balance_sheet_data(self) -> Dict[str, Any]:
        """Fetch balance sheet data and compute all metrics"""
        try:
            balance_sheet = self.stock.balance_sheet
            financials = self.stock.financials
            
            if balance_sheet is None or balance_sheet.empty:
                return self._empty_result()
            
            latest_bs = balance_sheet.iloc[:, 0]
            latest_fin = financials.iloc[:, 0] if financials is not None and not financials.empty else None
            
            metrics = {
                'ticker': self.ticker,
                'date': str(balance_sheet.columns[0].date()) if len(balance_sheet.columns) > 0 else None,
                'explanations': self.METRIC_EXPLANATIONS,
            }
            
            metrics.update(self._get_debt_metrics(latest_bs, latest_fin))
            metrics.update(self._get_liquidity_metrics(latest_bs))
            
            return metrics
        except:
            return self._empty_result()
    
    def _get_debt_metrics(self, bs, fin) -> Dict[str, Optional[float]]:
        """Calculate debt and leverage metrics"""
        metrics = {}
        
        long_term_debt = self._safe_get(bs, 'Long Term Debt', 0) or self._safe_get(bs, 'Long Term Debt And Capital Lease Obligation', 0)
        short_term_debt = self._safe_get(bs, 'Current Debt', 0) or self._safe_get(bs, 'Current Debt And Capital Lease Obligation', 0)
        
        total_debt = long_term_debt + short_term_debt
        metrics['total_debt'] = total_debt if total_debt > 0 else None
        
        cash = self._safe_get(bs, 'Cash And Cash Equivalents', 0)
        short_term_inv = self._safe_get(bs, 'Other Short Term Investments', 0)
        cash_and_short_term = cash + short_term_inv
        metrics['cash_and_short_term'] = cash_and_short_term if cash_and_short_term > 0 else None
        
        metrics['net_debt'] = total_debt - cash_and_short_term if total_debt and cash_and_short_term else None
        
        total_equity = self._safe_get(bs, 'Stockholders Equity') or self._safe_get(bs, 'Total Equity Gross Minority Interest')
        
        if total_debt and total_equity and total_equity != 0:
            metrics['debt_to_equity'] = total_debt / total_equity
        else:
            metrics['debt_to_equity'] = None
        
        ebitda = self._calculate_ebitda(fin)
        if total_debt and ebitda and ebitda != 0:
            metrics['debt_to_ebitda'] = total_debt / ebitda
        else:
            metrics['debt_to_ebitda'] = None
        
        ebit = self._safe_get(fin, 'EBIT') if fin is not None else None
        interest_expense = self._safe_get(fin, 'Interest Expense') or self._safe_get(fin, 'Interest Expense Non Operating') if fin is not None else None
        
        if ebit and interest_expense and interest_expense != 0:
            metrics['interest_coverage'] = ebit / abs(interest_expense)
        else:
            metrics['interest_coverage'] = None
        
        return metrics
    
    def _get_liquidity_metrics(self, bs) -> Dict[str, Optional[float]]:
        """Calculate liquidity metrics"""
        metrics = {}
        
        current_assets = self._safe_get(bs, 'Current Assets')
        current_liabilities = self._safe_get(bs, 'Current Liabilities')
        
        if current_assets and current_liabilities and current_liabilities != 0:
            metrics['current_ratio'] = current_assets / current_liabilities
        else:
            metrics['current_ratio'] = None
        
        inventory = self._safe_get(bs, 'Inventory', 0)
        
        if current_assets and current_liabilities and current_liabilities != 0:
            quick_assets = current_assets - inventory
            metrics['quick_ratio'] = quick_assets / current_liabilities
        else:
            metrics['quick_ratio'] = None
        
        return metrics
    
    def _calculate_ebitda(self, fin) -> Optional[float]:
        """Calculate EBITDA from financial statements"""
        if fin is None:
            return None
        
        ebitda = self._safe_get(fin, 'EBITDA')
        if ebitda:
            return ebitda
        
        ebit = self._safe_get(fin, 'EBIT')
        if ebit:
            depreciation = self._safe_get(fin, 'Depreciation', 0)
            amortization = self._safe_get(fin, 'Amortization', 0)
            dep_amort = self._safe_get(fin, 'Depreciation And Amortization', 0)
            
            if dep_amort > 0:
                return ebit + dep_amort
            elif depreciation > 0 or amortization > 0:
                return ebit + depreciation + amortization
        
        operating_income = self._safe_get(fin, 'Operating Income')
        if operating_income:
            dep_amort = self._safe_get(fin, 'Depreciation And Amortization', 0)
            if dep_amort > 0:
                return operating_income + dep_amort
        
        return None
    
    def _empty_result(self) -> Dict[str, Any]:
        """Return empty result structure"""
        return {
            'ticker': self.ticker,
            'error': 'No data available',
            'total_debt': None, 'net_debt': None, 'debt_to_equity': None,
            'debt_to_ebitda': None, 'interest_coverage': None,
            'current_ratio': None, 'quick_ratio': None,
            'cash_and_short_term': None,
            'explanations': self.METRIC_EXPLANATIONS,
        }
