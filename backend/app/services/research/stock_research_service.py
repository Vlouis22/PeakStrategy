import yfinance as yf
import json
import pandas as pd
import os
import requests
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from supabase import create_client, Client
import threading
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
    """Main orchestrator class for comprehensive stock research with Supabase caching"""
    
    # Class-level lock for concurrency control
    _locks = {}
    _locks_lock = threading.Lock()
    
    # TTL definitions in minutes
    TTL_SNAPSHOT = 10  # 10 minutes
    TTL_VALUATION = 60  # 1 hour
    TTL_OTHER = 10080  # 7 days (7 * 24 * 60)
    
    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.gemini_api_key = os.getenv("GEMINI_API_KEY")
        self.deepseek_api_key = os.getenv("DEEPSEEK_API_KEY")
        
        # Initialize Supabase client
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_KEY")
        
        if not supabase_url or not supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY environment variables must be set")
        
        self.supabase: Client = create_client(supabase_url, supabase_key)
        
        # Initialize analyzers
        self.snapshot_analyzer = SnapshotAnalyzer(ticker)
        self.financial_analyzer = FinancialFoundationAnalyzer(ticker)
        self.analyst_analyzer = AnalystConsensusAnalyzer(ticker)
        self.balance_sheet_analyzer = BalanceSheetAnalyzer(ticker)
        self.business_analyzer = BusinessIntelligenceAnalyzer(ticker)
        self.profitability_analyzer = ProfitabilityAnalyzer(ticker)
        self.shareholder_analyzer = ShareholderReturnsAnalyzer(ticker)
        self.valuation_analyzer = ValuationAnalyzer(ticker)
        self.summary_generator = CompanySummaryGenerator(self.gemini_api_key, self.deepseek_api_key)
    
    def _get_lock(self) -> threading.Lock:
        """Get or create a lock for this specific ticker"""
        with self._locks_lock:
            if self.ticker not in self._locks:
                self._locks[self.ticker] = threading.Lock()
            return self._locks[self.ticker]
    
    def _is_stale(self, last_updated: datetime, ttl_minutes: int) -> bool:
        """Check if data is stale based on TTL"""
        if not last_updated:
            return True
        
        now = datetime.now()
        age_minutes = (now - last_updated).total_seconds() / 60
        return age_minutes > ttl_minutes
    
    def _fetch_from_supabase(self) -> Optional[Dict[str, Any]]:
        """Fetch cached stock data from Supabase"""
        try:
            response = self.supabase.table('research').select('*').eq('stock_symbol', self.ticker).execute()
            
            if response.data and len(response.data) > 0:
                record = response.data[0]
                return {
                    'data': record.get('data', {}),
                    'last_updated': datetime.fromisoformat(record['last_updated'].replace('Z', '+00:00')) if record.get('last_updated') else None
                }
            return None
        except Exception as e:
            print(f"Error fetching from Supabase: {e}")
            return None
    
    def _save_to_supabase(self, stock_info: Dict[str, Any]) -> bool:
        """Save or update stock data in Supabase"""
        try:
            data_to_save = {
                'stock_symbol': self.ticker,
                'data': stock_info,
                'last_updated': datetime.now().isoformat()
            }
            
            # Upsert (insert or update)
            self.supabase.table('research').upsert(data_to_save).execute()
            return True
        except Exception as e:
            print(f"Error saving to Supabase: {e}")
            return False
    
    def _determine_refresh_needs(self, cached_data: Dict[str, Any]) -> Dict[str, bool]:
        """Determine which parts of the data need refreshing based on TTL"""
        last_updated = cached_data.get('last_updated')
        
        if not last_updated:
            return {
                'snapshot': True,
                'valuation': True,
                'other': True
            }
        
        # Check individual component timestamps if they exist in metadata
        data = cached_data.get('data', {})
        metadata = data.get('metadata', {})
        component_timestamps = metadata.get('component_timestamps', {})
        
        refresh_needs = {}
        
        # Check snapshot freshness
        snapshot_timestamp = component_timestamps.get('snapshot')
        if snapshot_timestamp:
            snapshot_dt = datetime.fromisoformat(snapshot_timestamp)
            refresh_needs['snapshot'] = self._is_stale(snapshot_dt, self.TTL_SNAPSHOT)
        else:
            refresh_needs['snapshot'] = self._is_stale(last_updated, self.TTL_SNAPSHOT)
        
        # Check valuation freshness
        valuation_timestamp = component_timestamps.get('valuation')
        if valuation_timestamp:
            valuation_dt = datetime.fromisoformat(valuation_timestamp)
            refresh_needs['valuation'] = self._is_stale(valuation_dt, self.TTL_VALUATION)
        else:
            refresh_needs['valuation'] = self._is_stale(last_updated, self.TTL_VALUATION)
        
        # Check other data freshness
        other_timestamp = component_timestamps.get('other')
        if other_timestamp:
            other_dt = datetime.fromisoformat(other_timestamp)
            refresh_needs['other'] = self._is_stale(other_dt, self.TTL_OTHER)
        else:
            refresh_needs['other'] = self._is_stale(last_updated, self.TTL_OTHER)
        
        return refresh_needs
    
    def _fetch_fresh_data(self, refresh_needs: Dict[str, bool], cached_data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Fetch fresh data for components that need refreshing"""
        now_iso = datetime.now().isoformat()
        
        # Start with cached data if available
        if cached_data and cached_data.get('data'):
            stock_info = cached_data['data'].copy()
            component_timestamps = stock_info.get('metadata', {}).get('component_timestamps', {})
        else:
            stock_info = {}
            component_timestamps = {}
        
        # Refresh snapshot if needed
        if refresh_needs.get('snapshot', True):
            print("\n\nRefreshing snapshot data...\n\n")
            stock_info['snapshot'] = self.snapshot_analyzer.get_snapshot_row()
            component_timestamps['snapshot'] = now_iso
        
        # Refresh valuation if needed
        if refresh_needs.get('valuation', True):
            print("\n\nRefreshing Valuation data...\n\n")
            valuation = self.valuation_analyzer.get_stock_valuation()
            if valuation.get("success"):
                stock_info['valuation'] = valuation.get("valuations", {})
            else:
                stock_info['valuation'] = valuation
            component_timestamps['valuation'] = now_iso
        
        # Refresh other data if needed
        if refresh_needs.get('other', True):
            print("\n\nRefreshing other data...\n\n")
            stock_info['business_understanding'] = self.business_analyzer.get_business_intelligence()
            stock_info['financial_foundation'] = self.financial_analyzer.get_financial_foundation()
            stock_info['analyst_consensus'] = self.analyst_analyzer.get_analyst_consensus()
            stock_info['profitability_and_efficiency'] = self.profitability_analyzer.analyze_profitability()
            stock_info['balance_sheet'] = self.balance_sheet_analyzer.fetch_balance_sheet_data()
            stock_info['shareholder_returns'] = self.shareholder_analyzer.get_shareholder_returns()
            stock_info['additional_info'] = self._get_additional_info()
            component_timestamps['other'] = now_iso
        
        # Calculate scoring pillars (always recalculate when snapshot or other data changes)
        if refresh_needs.get('snapshot', True) or refresh_needs.get('valuation', True) or refresh_needs.get('other', True):
            stock_info['scoring_pillars'] = self.snapshot_analyzer.get_scoring_pillars(
                valuation_data=stock_info.get('valuation', {}),
                profitability_data=stock_info.get('profitability_and_efficiency', {}),
                balance_sheet_data=stock_info.get('balance_sheet', {}),
                shareholder_data=stock_info.get('shareholder_returns', {}),
                analyst_data=stock_info.get('analyst_consensus', {})
            )
        
        # Always update basic metadata
        stock_info['ticker'] = self.ticker
        stock_info['company_name'] = self._get_company_name()
        stock_info['company_logo_url'] = self._get_company_logo_url()
        
        # Update metadata with component timestamps
        stock_info['metadata'] = {
            "last_updated": now_iso,
            "source": "yfinance",
            "ticker": self.ticker,
            "component_timestamps": component_timestamps
        }
        
        # Generate summary if any data was refreshed
        if any(refresh_needs.values()):
            summary = self.summary_generator.generate_summary(stock_info)
            stock_info["company_summary"] = summary
        
        return stock_info
    
    def get_stock_info(self) -> Dict[str, Any]:
        """Get comprehensive stock information with intelligent caching"""
        # Use per-ticker lock to prevent concurrent fetches of same symbol
        lock = self._get_lock()
        
        with lock:
            try:
                # 1. Check if data exists in Supabase
                cached_data = self._fetch_from_supabase()
                
                if cached_data:
                    # 2. Determine what needs refreshing based on TTL
                    refresh_needs = self._determine_refresh_needs(cached_data)
                    
                    # 3. If nothing needs refreshing, return cached data
                    if not any(refresh_needs.values()):
                        return cached_data['data']
                    
                    # 4. Refresh only stale components
                    stock_info = self._fetch_fresh_data(refresh_needs, cached_data)
                else:
                    # 5. No cached data - fetch everything
                    refresh_needs = {'snapshot': True, 'valuation': True, 'other': True}
                    stock_info = self._fetch_fresh_data(refresh_needs)
                
                # 6. Save updated data to Supabase
                self._save_to_supabase(stock_info)
                
                return stock_info
            
            except Exception as e:
                # Fallback to cached data if available, otherwise return error
                cached_data = self._fetch_from_supabase()
                if cached_data and cached_data.get('data'):
                    print(f"Error fetching fresh data, returning cached data: {e}")
                    return cached_data['data']
                
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