import yfinance as yf
import json
import pandas as pd
import os
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .snapshot_analyzer import SnapshotAnalyzer
from .snapshot_analyzer import SnapshotAnalyzer
from .business_intelligence_analyzer import BusinessIntelligenceAnalyzer
from .financial_foundation_analyzer import FinancialFoundationAnalyzer
from .analyst_consensus_analyzer import AnalystConsensusAnalyzer
from .balance_sheet_analyzer import BalanceSheetAnalyzer
from .profitability_analyzer import ProfitabilityAnalyzer
from .shareholder_returns_analyzer import ShareholderReturnsAnalyzer
from .valuation_analyzer import ValuationAnalyzer
from .company_summary_generator import CompanySummaryGenerator


class StockResearchService:
    """Main orchestrator class for comprehensive stock research"""
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        self.snapshot_analyzer = SnapshotAnalyzer(ticker)
        self.financial_analyzer = FinancialFoundationAnalyzer(ticker)
        self.analyst_analyzer = AnalystConsensusAnalyzer(ticker)
        self.balance_sheet_analyzer = BalanceSheetAnalyzer(ticker)
        self.business_analyzer = BusinessIntelligenceAnalyzer(ticker)
        self.profitability_analyzer = ProfitabilityAnalyzer(ticker)
        self.shareholder_analyzer = ShareholderReturnsAnalyzer(ticker)
        self.valuation_analyzer = ValuationAnalyzer(ticker)
        self.summary_generator = CompanySummaryGenerator(self.gemini_api_key, self.deepseek_api_key)
    
    def get_stock_info(self) -> Dict[str, Any]:
        """Get comprehensive stock information including all research data"""
        try:
            snapshot = self.snapshot_analyzer.get_snapshot_row()
            business_understanding = self.business_analyzer.get_business_intelligence()
            financial_foundation = self.financial_analyzer.get_financial_foundation()
            analyst_consensus = self.analyst_analyzer.get_analyst_consensus()
            valuation = self.valuation_analyzer.get_stock_valuation()
            
            if valuation.get("success"):
                valuation = valuation.get("valuations", {})
            
            profitability_and_efficiency = self.profitability_analyzer.analyze_profitability()
            balance_sheet = self.balance_sheet_analyzer.fetch_balance_sheet_data()
            shareholder_returns = self.shareholder_analyzer.get_shareholder_returns()
            
            # Calculate scoring pillars LAST using all gathered data
            scoring_pillars = self.snapshot_analyzer.get_scoring_pillars(
                valuation_data=valuation,
                profitability_data=profitability_and_efficiency,
                balance_sheet_data=balance_sheet,
                shareholder_data=shareholder_returns,
                analyst_data=analyst_consensus
            )
            
            stock_info = {
                "ticker": self.ticker,
                "company_name": self._get_company_name(),
                "company_logo_url": self._get_company_logo_url(),
                "snapshot": snapshot,
                "scoring_pillars": scoring_pillars,
                "business_understanding": business_understanding,
                "financial_foundation": financial_foundation,
                "analyst_consensus": analyst_consensus,
                "valuation": valuation,
                "profitability_and_efficiency": profitability_and_efficiency,
                "balance_sheet": balance_sheet,
                "shareholder_returns": shareholder_returns,
                "additional_info": self._get_additional_info(),
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "source": "yfinance",
                    "ticker": self.ticker
                }
            }
            
            summary = self.summary_generator.generate_summary(stock_info)
            stock_info["company_summary"] = summary

            return stock_info
        
        except Exception as e:
            return {
                "ticker": self.ticker,
                "error": str(e),
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "source": "yfinance",
                    "ticker": self.ticker,
                    "error": "Failed to fetch complete data"
                }
            }
        
    def get_json(self) -> str:
        """Get complete stock info as JSON string"""
        data = self.get_stock_info()
        return json.dumps(data, indent=2, default=str)
    
    def _get_company_name(self) -> str:
        """Get company name"""
        try:
            info = self.snapshot_analyzer.info
            name = info.get('longName') or info.get('shortName')
            if name:
                return str(name)
        except:
            pass
        return self.ticker
    
    def _get_company_logo_url(self) -> str:
        """Get company logo URL using Finnhub API"""
        try:
            finnhub_api_key = os.getenv("FINNHUB_API_KEY")
            if not finnhub_api_key:
                return ""
            url = f"https://finnhub.io/api/v1/stock/profile2?symbol={self.ticker}&token={finnhub_api_key}"
            response = requests.get(url)
            if response.status_code == 200:
                data = response.json()
                logo_url = data.get("logo", "")
                return logo_url
        except:
            pass
        return ""
    
    def _get_additional_info(self) -> Dict[str, Any]:
        """Get additional stock information"""
        try:
            info = self.snapshot_analyzer.info
            additional = {
                "website": info.get('website', ''),
                "employees": info.get('fullTimeEmployees'),
                "fiscal_year_end": info.get('lastFiscalYearEnd'),
                "most_recent_quarter": info.get('mostRecentQuarter'),
                "currency": info.get('currency', 'USD'),
                "exchange": info.get('exchange', ''),
                "quote_type": info.get('quoteType', ''),
                "symbol": info.get('symbol', self.ticker)
            }
            
            return {k: v for k, v in additional.items() if v is not None}
        except:
            return {}