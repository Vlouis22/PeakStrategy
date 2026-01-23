# Latest Working Version of get_stock_info() Method
import yfinance as yf
import json
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, asdict
import datetime
import pandas as pd
import finqual as fq
import re
import requests
from .research import stock_valuation
from .research.profitability_and_efficiency import StockProfitabilityAnalyzer
from .research.balance_sheet_data import BalanceSheetData
from .research.analyst_consensus import AnalystConsensus
from .research.shareholder_returns_analyzer import ShareholderReturnsAnalyzer


@dataclass
class StockResearchService:
    """Class to generate stock snapshot data using yfinance"""
    
    def __init__(self, ticker: str):
        """
        Initialize with stock ticker symbol
        
        Args:
            ticker: Stock ticker symbol (e.g., 'AAPL', 'MSFT')
        """
        self.ticker = ticker.upper()
        self.stock = yf.Ticker(self.ticker)
        self.info = self.stock.info
        self.financials_cache = {}
    
    def get_stock_info(self) -> Dict[str, Any]:
        """
        Get comprehensive stock information including all research data
        
        Returns:
            Dictionary containing all stock information
        """
        try:
            # Get all the data components
            snapshot = self._get_snapshot_row()
            scoring_pillars = self._get_scoring_pillars()
            business_understanding = self._get_business_understanding()
            financial_foundation = self._get_financial_foundation()
            analyst_consensus = AnalystConsensus(self.ticker).get_yahoo_analyst_consensus()
            valuation = stock_valuation.get_stock_valuation(self.ticker)
            if valuation.get("success"):
                valuation = valuation.get("valuations", {})
            profitability_and_efficiency = StockProfitabilityAnalyzer(self.ticker).analyze_profitability()
            balance_sheet = BalanceSheetData(self.ticker).fetch_data()
            shareholder_returns = ShareholderReturnsAnalyzer(self.ticker).get_shareholder_returns()
            
            # Combine all data into a single structure
            stock_info = {
                "ticker": self.ticker,
                "company_name": self._get_company_name(),
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
                    "last_updated": datetime.datetime.now().isoformat(),
                    "source": "yfinance",
                    "ticker": self.ticker
                }
            }
            
            return stock_info
            
        except Exception as e:
            print(f"Error getting stock info: {e}")
            return self._get_empty_stock_info()
    
    def get_snapshot_data(self) -> Dict[str, Any]:
        """
        Get complete snapshot data as a dictionary
        
        Returns:
            Dictionary containing all snapshot data
        """
        return {
            "snapshot": self._get_snapshot_row(),
            "scoring_pillars": self._get_scoring_pillars(),
            "business_understanding": self._get_business_understanding(),
            "financial_foundation": self._get_financial_foundation()
        }
    
    def get_json(self) -> str:
        """
        Get complete stock info as JSON string
        
        Returns:
            JSON string containing all stock information
        """
        data = self.get_stock_info()
        return json.dumps(data, indent=2, default=str)
    
    def _get_company_name(self) -> str:
        """Get company name"""
        try:
            name = self.info.get('longName') or self.info.get('shortName')
            if name:
                return str(name)
        except:
            pass
        return self.ticker
    
    def _get_additional_info(self) -> Dict[str, Any]:
        """Get additional stock information"""
        try:
            info = {
                "website": self.info.get('website', ''),
                "employees": self.info.get('fullTimeEmployees'),
                "fiscal_year_end": self.info.get('lastFiscalYearEnd'),
                "most_recent_quarter": self.info.get('mostRecentQuarter'),
                "currency": self.info.get('currency', 'USD'),
                "exchange": self.info.get('exchange', ''),
                "quote_type": self.info.get('quoteType', ''),
                "symbol": self.info.get('symbol', self.ticker)
            }
            
            # Clean up None values
            return {k: v for k, v in info.items() if v is not None}
        except:
            return {}
    
    def _get_empty_stock_info(self) -> Dict[str, Any]:
        """Return empty stock info when data is unavailable"""
        return {
            "ticker": self.ticker,
            "company_name": self.ticker,
            "snapshot": self._get_empty_snapshot(),
            "scoring_pillars": {
                "financial_health": {"score": "", "visual": "", "value": ""},
                "growth": {"score": "", "visual": "", "value": ""},
                "valuation": {"score": "", "visual": "", "value": ""},
                "stability": {"score": "", "visual": "", "value": ""},
                "note": "Data unavailable"
            },
            "business_understanding": {
                "company_description": "",
                "strategic_focus": "",
                "sections": {
                    "what_company_does": {
                        "core_products": [],
                        "revenue_drivers": [],
                        "geographic_exposure": []
                    },
                    "current_strategic_focus": {
                        "major_initiatives": [],
                        "capital_allocation": []
                    }
                }
            },
            "financial_foundation": self._get_empty_financial_foundation(),
            "additional_info": {},
            "metadata": {
                "last_updated": datetime.datetime.now().isoformat(),
                "source": "yfinance",
                "ticker": self.ticker,
                "error": "Failed to fetch complete data"
            }
        }
        
    def _get_financial_foundation(self) -> Dict[str, Any]:
        """
        Get financial foundation data for survivability & quality
        
        Returns:
            Dictionary with financial foundation data
        """
        
        cash_flow__years = []
        cash_flows = []
        total_revenue_values = []
        total_revenue_years = []
        net_income_values = []
        net_income_years = []

        try:
            income_statement = fq.Finqual(self.ticker).income_stmt_period(0, 2025) 
            cash_flow = fq.Finqual(self.ticker).cash_flow_period(0, 2025) 

            income_dict = {
                row[0]: {income_statement.columns[i]: row[i] for i in range(1, len(row))}
                for row in income_statement.to_numpy()
            }

            cash_flow_dict = {
                row[0]: {cash_flow.columns[i]: row[i] for i in range(1, len(row))}
                for row in cash_flow.to_numpy()
            }

            operating_cash_flow_values = list(cash_flow_dict["Operating Cash Flow"].values())
            investing_cash_flow_values = list(cash_flow_dict["Investing Cash Flow"].values())
            cash_flow__years = list(cash_flow_dict["Operating Cash Flow"].keys())

            for operating, investing, year in zip(operating_cash_flow_values, investing_cash_flow_values, cash_flow__years):
                cash_flow__years.append(year)
                cash_flows.append(operating + investing)
                
            total_revenue_values = list(income_dict["Total Revenue"].values())
            total_revenue_years = list(income_dict["Total Revenue"].keys())

            net_income_values = list(income_dict["Net Income"].values())
            net_income_years = list(income_dict["Net Income"].keys())
        except Exception as e:
            print(f"Error fetching financial data from finqual: {e}")

        try:
            # Get 5-year financial data
            income_data = self._get_5_year_income_data()
            cashflow_data = self._get_5_year_cashflow_data()
            
            return {
                "purpose": "Answer: Is this a real business with durable finances?",
                "core_trends": {
                    "revenue": self._format_revenue_data(income_data, total_revenue_values, total_revenue_years),
                    "net_income": self._format_net_income_data(income_data, net_income_values, net_income_years),
                    "free_cash_flow": self._format_free_cashflow_data(cashflow_data, income_data, cash_flows, cash_flow__years), 
                    "margins": self._format_margin_data(income_data)
                },
                "survivability_metrics": self._get_survivability_metrics(),
                "quality_metrics": self._get_quality_metrics(),
                "chart_tabs": ["Revenue", "Net Income", "Free Cash Flow", "Margins"],
                "note": "Clean multi-year line charts without cluttered indicators"
            }
        except Exception as e:
            print(f"Error getting financial foundation: {e}")
            return self._get_empty_financial_foundation()

    def _format_free_cashflow_data(self, cashflow_data: Dict, income_data: Dict, fcf, years) -> Dict[str, Any]:
        """Format free cash flow data with quality metrics"""
        if not cashflow_data or not cashflow_data.get('free_cashflow'):
            return {"data": [], "years": [], "cash_generator": "Unknown"}
        
        if fcf == [] or years == []:
            fcf = cashflow_data['free_cashflow']
            operating_cf = cashflow_data.get('operating_cashflow', [])
            capex = cashflow_data.get('capex', [])
            years = cashflow_data['years'][:len(fcf)]
        else:
            operating_cf = cashflow_data.get('operating_cashflow', [])
            capex = cashflow_data.get('capex', [])
        
        # Get net income from income data
        net_income = income_data.get('net_income', []) if income_data else []
        
        # Get stock-based compensation
        sbc_values = self._get_stock_based_compensation()
        
        # Get revenue for FCF margin calculation
        revenue_values = income_data.get('revenue', []) if income_data else []
        
        # Build enhanced data array
        data_array = []
        for i, year in enumerate(years):
            row = {
                "year": year,
                "value": fcf[i] if i < len(fcf) else None,
                "operating_cf": operating_cf[i] if i < len(operating_cf) else None,
                "net_income": net_income[i] if i < len(net_income) else None,
                "capex": abs(capex[i]) if i < len(capex) and capex[i] else None,
                "sbc": sbc_values[i] if i < len(sbc_values) else None
            }
            data_array.append(row)
        
        # Check cash generation
        positive_cash_years = sum(1 for cash in fcf if cash and cash > 0)
        cash_generator = "Positive FCF" if positive_cash_years == len(fcf) else \
                        "Mostly Positive" if positive_cash_years >= len(fcf) * 0.7 else \
                        "Mixed" if positive_cash_years >= len(fcf) * 0.3 else "Cash Burner"
        
        # Determine trend
        trend = self._determine_trend(fcf)
        
        # Calculate quality metrics
        quality_metrics = self._calculate_fcf_quality_metrics(
            fcf, operating_cf, net_income, capex, sbc_values, revenue_values
        )
        
        # Detect red flags
        red_flags = self._detect_cashflow_red_flags(
            fcf, operating_cf, net_income, revenue_values
        )
        
        return {
            "data": data_array,
            "years": years,
            "values": fcf,
            "unit": "USD",
            "cash_generator": cash_generator,
            "trend": trend,
            "last_value": fcf[0] if fcf else None,
            "quality_metrics": quality_metrics,
            "red_flags": red_flags
        }

    def _get_stock_based_compensation(self) -> List[Optional[float]]:
        """Get stock-based compensation from cash flow statement"""
        try:
            cashflow = self.stock.cashflow
            if cashflow.empty:
                return []
            
            years = sorted(cashflow.columns, reverse=True)[:10]
            sbc_values = []
            
            possible_keys = [
                'Stock Based Compensation',
                'Stock-Based Compensation',
                'Share Based Compensation',
                'Issuance Of Stock'
            ]
            
            for year in years:
                sbc = None
                for key in possible_keys:
                    if key in cashflow.index:
                        value = cashflow.loc[key, year]
                        if pd.notna(value):
                            sbc = abs(float(value))  # Make positive for display
                            break
                sbc_values.append(sbc)
            
            return sbc_values
        except:
            return []

    def _calculate_fcf_quality_metrics(self, fcf, operating_cf, net_income, capex, sbc, revenue) -> Dict[str, Any]:
        """Calculate cash flow quality metrics"""
        metrics = {}
        
        try:
            # Get most recent valid values
            latest_fcf = next((f for f in fcf if f is not None), None)
            latest_ocf = next((o for o in operating_cf if o is not None), None)
            latest_ni = next((n for n in net_income if n is not None), None)
            latest_capex = next((c for c in capex if c is not None), None)
            latest_sbc = next((s for s in sbc if s is not None), None)
            latest_revenue = next((r for r in revenue if r is not None), None)
            
            # 1. Operating Cash Flow vs Net Income Ratio
            if latest_ocf and latest_ni and latest_ni != 0:
                ratio = latest_ocf / latest_ni
                metrics['ocf_to_net_income'] = {
                    "value": f"{ratio:.2f}x",
                    "status": "Excellent" if ratio >= 1.2 else "Good" if ratio >= 1.0 else "Warning" if ratio >= 0.8 else "Concerning"
                }
            
            # 2. FCF Margin
            if latest_fcf and latest_revenue and latest_revenue != 0:
                fcf_margin = (latest_fcf / latest_revenue) * 100
                metrics['fcf_margin'] = {
                    "value": f"{fcf_margin:.1f}%",
                    "status": "Excellent" if fcf_margin >= 15 else "Good" if fcf_margin >= 10 else "Moderate" if fcf_margin >= 5 else "Poor"
                }
            
            # 3. FCF Per Share
            shares_outstanding = self.info.get('sharesOutstanding')
            if latest_fcf and shares_outstanding:
                fcf_per_share = latest_fcf / shares_outstanding
                metrics['fcf_per_share'] = {
                    "value": f"${fcf_per_share:.2f}",
                    "status": "Positive" if fcf_per_share > 0 else "Negative"
                }
            
            # 4. CapEx Trend
            valid_capex = [c for c in capex if c is not None]
            if len(valid_capex) >= 2:
                capex_trend = self._determine_trend(valid_capex)
                avg_capex = sum(valid_capex) / len(valid_capex)
                
                if latest_revenue:
                    capex_intensity = (avg_capex / latest_revenue) * 100
                    metrics['capex_trend'] = {
                        "value": f"{capex_intensity:.1f}% of Revenue",
                        "status": capex_trend,
                        "trend_direction": "Increasing" if capex_trend in ["Upward", "Strong Upward"] else "Decreasing" if capex_trend in ["Downward", "Strong Downward"] else "Stable"
                    }
            
            # 5. Stock-Based Compensation Ratio
            if latest_sbc and latest_ocf and latest_ocf != 0:
                sbc_ratio = (latest_sbc / latest_ocf) * 100
                metrics['sbc_ratio'] = {
                    "value": f"{sbc_ratio:.1f}%",
                    "status": "Good" if sbc_ratio < 10 else "Moderate" if sbc_ratio < 20 else "Concerning"
                }
            
        except Exception as e:
            print(f"Error calculating FCF quality metrics: {e}")
        
        return metrics

    def _detect_cashflow_red_flags(self, fcf, operating_cf, net_income, revenue) -> List[str]:
        """Detect red flags in cash flow"""
        flags = []
        
        try:
            # Get recent values (last 3 years)
            recent_fcf = [f for f in fcf[:3] if f is not None]
            recent_ocf = [o for o in operating_cf[:3] if o is not None]
            recent_ni = [n for n in net_income[:3] if n is not None]
            recent_revenue = [r for r in revenue[:3] if r is not None]
            
            # Flag 1: Rising revenue + negative operating cash flow
            if len(recent_revenue) >= 2 and len(recent_ocf) >= 2:
                revenue_growing = recent_revenue[0] > recent_revenue[-1]
                negative_ocf = any(ocf < 0 for ocf in recent_ocf)
                
                if revenue_growing and negative_ocf:
                    flags.append("Rising revenue but negative operating cash flow - possible earnings quality issue")
            
            # Flag 2: Consistently negative FCF
            if len(recent_fcf) >= 2 and all(f < 0 for f in recent_fcf):
                flags.append("Consistently negative free cash flow - burning cash")
            
            # Flag 3: Operating CF significantly lower than Net Income
            if len(recent_ocf) >= 1 and len(recent_ni) >= 1:
                latest_ocf = recent_ocf[0]
                latest_ni = recent_ni[0]
                
                if latest_ni > 0 and latest_ocf < latest_ni * 0.7:
                    flags.append("Operating cash flow significantly below net income - potential earnings quality concern")
            
            # Flag 4: Deteriorating FCF trend
            if len(recent_fcf) >= 3:
                if all(recent_fcf[i] < recent_fcf[i+1] for i in range(len(recent_fcf)-1)):
                    flags.append("Free cash flow declining for multiple consecutive years")
            
        except Exception as e:
            print(f"Error detecting cash flow red flags: {e}")
        
        return flags
    
    def _get_10_year_income_data(self) -> Dict[str, Any]:
        try:
            if 'income_data' in self.financials_cache:
                return self.financials_cache['income_data']

            income_statement = self.stock.financials
            quarterly_income = self.stock.quarterly_financials

            if income_statement.empty and quarterly_income.empty:
                return {}

            if not income_statement.empty and len(income_statement.columns) >= 10:
                financials = income_statement
            else:
                financials = quarterly_income.T
                financials['year'] = financials.index.year
                financials = financials.groupby('year').sum().T

            years = sorted(financials.columns, reverse=True)[:10]

            data = {
                'years': [str(y) for y in years],
                'revenue': [],
                'net_income': [],
                'gross_profit': [],
                'operating_income': []
            }

            for year in years:
                data['revenue'].append(
                    self._extract_financial_value(financials, year, 'Total Revenue', 'Revenue')
                )
                data['net_income'].append(
                    self._extract_financial_value(financials, year, 'Net Income')
                )
                data['gross_profit'].append(
                    self._extract_financial_value(financials, year, 'Gross Profit')
                )
                data['operating_income'].append(
                    self._extract_financial_value(financials, year, 'Operating Income')
                )

            self.financials_cache['income_data'] = data
            return data

        except Exception as e:
            print(f"Error getting income data: {e}")
            return {}



    def _get_5_year_income_data(self) -> Dict[str, Any]:
        """Get 5 years of income statement data"""
        try:
            if 'income_data' in self.financials_cache:
                return self.financials_cache['income_data']
            
            # Get financials for the last 5 years
            income_statement = self.stock.financials
            quarterly_income = self.stock.quarterly_financials
            
            if income_statement.empty and quarterly_income.empty:
                return {}
            
            # Prefer annual data, fall back to quarterly
            financials = income_statement if not income_statement.empty else quarterly_income
            
            # Get last 5 years of data
            years = sorted(financials.columns, reverse=True)[:10]
            
            data = {
                'years': [str(year.year) for year in years],
                'revenue': [],
                'net_income': [],
                'gross_profit': [],
                'operating_income': []
            }
            
            for year in years:
                # Revenue
                revenue = self._extract_financial_value(financials, year, 'Total Revenue', 'Revenue')
                data['revenue'].append(revenue)
                
                # Net Income
                net_income = self._extract_financial_value(financials, year, 'Net Income', 'Net Income')
                data['net_income'].append(net_income)
                
                # Gross Profit
                gross_profit = self._extract_financial_value(financials, year, 'Gross Profit')
                data['gross_profit'].append(gross_profit)
                
                # Operating Income
                operating_income = self._extract_financial_value(financials, year, 'Operating Income')
                data['operating_income'].append(operating_income)
            
            self.financials_cache['income_data'] = data
            return data
            
        except Exception as e:
            print(f"Error getting income data: {e}")
            return {}
    
    def _get_5_year_cashflow_data(self) -> Dict[str, Any]:
        """Get 5 years of cash flow data"""
        try:
            if 'cashflow_data' in self.financials_cache:
                return self.financials_cache['cashflow_data']
            
            cashflow = self.stock.cashflow
            quarterly_cashflow = self.stock.quarterly_cashflow
            
            if cashflow.empty and quarterly_cashflow.empty:
                return {}
            
            financials = cashflow if not cashflow.empty else quarterly_cashflow
            years = sorted(financials.columns, reverse=True)[:10]
            
            data = {
                'years': [str(year.year) for year in years],
                'operating_cashflow': [],
                'free_cashflow': [],
                'capex': []
            }
            
            for year in years:
                # Operating Cash Flow
                op_cashflow = self._extract_financial_value(financials, year, 'Operating Cash Flow', 'Total Cash From Operating Activities')
                data['operating_cashflow'].append(op_cashflow)
                
                # Capital Expenditure
                capex = self._extract_financial_value(financials, year, 'Capital Expenditure')
                data['capex'].append(capex if capex else 0)
                
                # Free Cash Flow (Operating Cash Flow - Capex)
                free_cashflow = op_cashflow - (capex if capex else 0) if op_cashflow else None
                data['free_cashflow'].append(free_cashflow)
            
            self.financials_cache['cashflow_data'] = data
            return data
            
        except Exception as e:
            print(f"Error getting cashflow data: {e}")
            return {}
    
    def _extract_financial_value(self, financials, year, *possible_keys):
        """Extract financial value trying multiple possible keys"""
        for key in possible_keys:
            try:
                if key in financials.index:
                    value = financials.loc[key, year]
                    if pd.notna(value):
                        return float(value)
            except:
                continue
        return None
    
    def _format_revenue_data(self, income_data: Dict, revenues, years) -> Dict[str, Any]:
        """Format revenue data for display"""
        if not income_data or not income_data.get('revenue'):
            return {"data": [], "years": [], "growth_rate": None, "trend": "Unknown"}
        
        if revenues == [] or years == []:
            revenues = income_data['revenue']
            years = income_data['years'][:len(revenues)]
        
        # Calculate CAGR if we have at least 2 years of data
        growth_rate = None
        if len(revenues) >= 2 and revenues[0] and revenues[-1]:
            start_value = revenues[-1]
            end_value = revenues[0]
            if start_value and end_value and start_value > 0:
                n_years = len(years) - 1
                growth_rate = ((end_value / start_value) ** (1/n_years) - 1) * 100
        
        # Determine trend
        trend = self._determine_trend(revenues)
        
        return {
            "data": [{"year": year, "value": value} for year, value in zip(years, revenues)],
            "years": years,
            "values": revenues,
            "unit": "USD",
            "growth_rate": round(growth_rate, 2) if growth_rate else None,
            "trend": trend,
            "last_value": revenues[0] if revenues else None
        }
    
    def _format_net_income_data(self, income_data: Dict, net_incomes, years) -> Dict[str, Any]:
        """Format net income data for display"""
        if not income_data or not income_data.get('net_income'):
            return {"data": [], "years": [], "profitability": "Unknown"}
        
        if net_incomes == [] or years == []:
            net_incomes = income_data['net_income']
            years = income_data['years'][:len(net_incomes)]
        
        # Check profitability
        profitable_years = sum(1 for ni in net_incomes if ni and ni > 0)
        profitability = "Profitable" if profitable_years == len(net_incomes) else \
                       "Mostly Profitable" if profitable_years >= len(net_incomes) * 0.7 else \
                       "Mixed" if profitable_years >= len(net_incomes) * 0.3 else "Unprofitable"
        
        # Determine trend
        trend = self._determine_trend(net_incomes)
        
        return {
            "data": [{"year": year, "value": value} for year, value in zip(years, net_incomes)],
            "years": years,
            "values": net_incomes,
            "unit": "USD",
            "profitability": profitability,
            "trend": trend,
            "last_value": net_incomes[0] if net_incomes else None
        }
    
    def _format_margin_data(self, income_data: Dict) -> Dict[str, Any]:
        """Format margin data for display"""
        if not income_data or not income_data.get('revenue') or not income_data.get('net_income'):
            return {"data": [], "years": [], "margins": []}
        
        revenues = income_data['revenue']
        net_incomes = income_data['net_income']
        gross_profits = income_data.get('gross_profit', [])
        operating_incomes = income_data.get('operating_income', [])
        years = income_data['years'][:len(revenues)]
        
        margins = []
        for i in range(min(len(years), len(revenues))):
            year_data = {"year": years[i]}
            
            # Gross Margin
            if i < len(gross_profits) and revenues[i] and revenues[i] != 0:
                year_data["gross_margin"] = round((gross_profits[i] / revenues[i]) * 100, 1) if gross_profits[i] else None
            
            # Operating Margin
            if i < len(operating_incomes) and revenues[i] and revenues[i] != 0:
                year_data["operating_margin"] = round((operating_incomes[i] / revenues[i]) * 100, 1) if operating_incomes[i] else None
            
            # Net Margin
            if net_incomes[i] and revenues[i] and revenues[i] != 0:
                year_data["net_margin"] = round((net_incomes[i] / revenues[i]) * 100, 1)
            
            margins.append(year_data)
        
        # Calculate average margins
        avg_margins = {}
        margin_types = ["gross_margin", "operating_margin", "net_margin"]
        for margin_type in margin_types:
            values = [m[margin_type] for m in margins if margin_type in m and m[margin_type] is not None]
            if values:
                avg_margins[margin_type] = round(sum(values) / len(values), 1)
        
        # Determine margin trend
        net_margins = [m.get("net_margin") for m in margins if m.get("net_margin")]
        margin_trend = self._determine_trend(net_margins) if net_margins else "Unknown"
        
        return {
            "data": margins,
            "years": years,
            "margins": ["Gross Margin", "Operating Margin", "Net Margin"],
            "average_margins": avg_margins,
            "trend": margin_trend
        }
    
    def _determine_trend(self, values: List[Optional[float]]) -> str:
        """Determine trend direction from values"""
        if not values or len(values) < 2:
            return "Unknown"
        
        # Filter out None values and get valid indices
        valid_values = [(i, v) for i, v in enumerate(values) if v is not None]
        if len(valid_values) < 2:
            return "Insufficient Data"
        
        # Calculate slope using linear regression on valid points
        indices = [i for i, v in valid_values]
        vals = [v for i, v in valid_values]
        
        # Simple trend detection
        first = vals[-1]  # Oldest valid value
        last = vals[0]    # Most recent valid value
        
        if last is None or first is None:
            return "Unknown"
        
        change_percent = ((last - first) / abs(first)) * 100 if first != 0 else 0
        
        if change_percent > 10:
            return "Strong Upward"
        elif change_percent > 2:
            return "Upward"
        elif change_percent < -10:
            return "Strong Downward"
        elif change_percent < -2:
            return "Downward"
        else:
            return "Stable"
    
    def _get_survivability_metrics(self) -> Dict[str, Any]:
        """Get key survivability metrics"""
        try:
            metrics = {}
            
            # Current Ratio
            if 'currentRatio' in self.info and self.info['currentRatio']:
                current_ratio = float(self.info['currentRatio'])
                metrics['current_ratio'] = {
                    "value": round(current_ratio, 2),
                    "status": "Good" if current_ratio >= 1.5 else "Adequate" if current_ratio >= 1.0 else "Concerning"
                }
            
            # Debt to Equity
            if 'debtToEquity' in self.info and self.info['debtToEquity']:
                debt_to_equity = float(self.info['debtToEquity'])
                metrics['debt_to_equity'] = {
                    "value": round(debt_to_equity, 2),
                    "status": "Low" if debt_to_equity < 0.5 else "Moderate" if debt_to_equity < 1.0 else "High"
                }
            
            # Interest Coverage
            if 'interestCoverage' in self.info and self.info['interestCoverage']:
                interest_coverage = float(self.info['interestCoverage'])
                metrics['interest_coverage'] = {
                    "value": round(interest_coverage, 2),
                    "status": "Strong" if interest_coverage > 5 else "Adequate" if interest_coverage > 2 else "Weak"
                }
            
            # Quick Ratio
            if 'quickRatio' in self.info and self.info['quickRatio']:
                quick_ratio = float(self.info['quickRatio'])
                metrics['quick_ratio'] = {
                    "value": round(quick_ratio, 2),
                    "status": "Good" if quick_ratio >= 1.0 else "Concerning"
                }
            
            return metrics
            
        except Exception as e:
            print(f"Error getting survivability metrics: {e}")
            return {}
    
    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get key quality metrics"""
        try:
            metrics = {}
            
            # Return on Equity
            if 'returnOnEquity' in self.info and self.info['returnOnEquity']:
                roe = float(self.info['returnOnEquity']) * 100
                metrics['return_on_equity'] = {
                    "value": round(roe, 1),
                    "unit": "%",
                    "status": "Excellent" if roe > 20 else "Good" if roe > 15 else "Average" if roe > 10 else "Poor"
                }
            
            # Return on Assets
            if 'returnOnAssets' in self.info and self.info['returnOnAssets']:
                roa = float(self.info['returnOnAssets']) * 100
                metrics['return_on_assets'] = {
                    "value": round(roa, 1),
                    "unit": "%",
                    "status": "Excellent" if roa > 10 else "Good" if roa > 5 else "Average" if roa > 2 else "Poor"
                }
            
            # Operating Margin
            if 'operatingMargins' in self.info and self.info['operatingMargins']:
                op_margin = float(self.info['operatingMargins']) * 100
                metrics['operating_margin'] = {
                    "value": round(op_margin, 1),
                    "unit": "%",
                    "status": "Excellent" if op_margin > 20 else "Good" if op_margin > 15 else "Average" if op_margin > 10 else "Poor"
                }
            
            # Net Margin
            if 'profitMargins' in self.info and self.info['profitMargins']:
                net_margin = float(self.info['profitMargins']) * 100
                metrics['net_margin'] = {
                    "value": round(net_margin, 1),
                    "unit": "%",
                    "status": "Excellent" if net_margin > 15 else "Good" if net_margin > 10 else "Average" if net_margin > 5 else "Poor"
                }
            
            return metrics
            
        except Exception as e:
            print(f"Error getting quality metrics: {e}")
            return {}
    
    def _get_empty_financial_foundation(self) -> Dict[str, Any]:
        """Return empty financial foundation when data is unavailable"""
        return {
            "purpose": "Answer: Is this a real business with durable finances?",
            "core_trends": {
                "revenue": {"data": [], "years": [], "growth_rate": None, "trend": "Unknown"},
                "net_income": {"data": [], "years": [], "profitability": "Unknown"},
                "free_cash_flow": {"data": [], "years": [], "cash_generator": "Unknown"},
                "margins": {"data": [], "years": [], "margins": [], "average_margins": {}, "trend": "Unknown"}
            },
            "survivability_metrics": {},
            "quality_metrics": {},
            "chart_tabs": ["Revenue", "Net Income", "Free Cash Flow", "Margins"],
            "note": "Clean multi-year line charts without cluttered indicators"
        }
    
    def _get_snapshot_row(self) -> Dict[str, Any]:
        """
        Get the main snapshot row data
        
        Returns:
            Dictionary with snapshot metrics
        """
        try:
            # Get current price and day change
            current_price = self._get_current_price()
            day_change = self._get_day_change()
            day_change_percent = self._get_day_change_percent()
            
            # Get market cap
            market_cap = self._get_market_cap()
            
            # Get 52-week range and visual bar
            week_range_low, week_range_high = self._get_52w_range_values()
            range_bar = self._create_range_bar(current_price, week_range_low, week_range_high)
            week_range_str = self._format_52w_range(week_range_low, week_range_high)
            
            # Get sector and industry
            sector = self._get_sector()
            industry = self._get_industry()
            
            # Color code for day change
            day_change_color = self._get_day_change_color(day_change_percent)
            
            return {
                "ticker": self.ticker,
                "metrics": {
                    "price": f"${current_price:.2f}" if current_price is not None else "",
                    "day": f"{day_change_percent:+.2f}%" if day_change_percent is not None else "",
                    "day_change": f"{day_change:+.2f}" if day_change is not None else "",
                    "day_color": day_change_color,
                    "market_cap": market_cap if market_cap else "",
                    "week_52_range": week_range_str,
                    "week_52_range_bar": range_bar,
                    "sector": sector if sector else "",
                    "industry": industry if industry else ""
                },
                "timestamp": datetime.datetime.now().isoformat()
            }
        except Exception as e:
            print(f"Error getting snapshot row: {e}")
            return self._get_empty_snapshot()
    
    def _get_scoring_pillars(self) -> Dict[str, Any]:
        """
        Get scoring pillars data (placeholders for now)
        
        Returns:
            Dictionary with scoring pillars
        """
        return {
            "financial_health": {
                "score": "",
                "visual": "████████░░",
                "value": "8.5"
            },
            "growth": {
                "score": "",
                "visual": "██████░░░░",
                "value": "6.5"
            },
            "valuation": {
                "score": "",
                "visual": "█████░░░░░",
                "value": "5.8"
            },
            "stability": {
                "score": "",
                "visual": "████████░░",
                "value": "8.2"
            },
            "note": ""
        }
    
    def _get_business_understanding(self) -> Dict[str, Any]:
        """
        Get business understanding data
        
        Returns:
            Dictionary with business information
        """
        return {
            "company_description": self._get_company_description(),
            "strategic_focus": self._get_strategic_focus(),
            "sections": {
                "what_company_does": {
                    "core_products": self._get_core_products(),
                    "revenue_drivers": self._get_revenue_drivers(),
                    "geographic_exposure": self._get_geographic_exposure()
                },
                "current_strategic_focus": {
                    "major_initiatives": self._get_major_initiatives(),
                    "capital_allocation": self._get_capital_allocation()
                }
            }
        }
    
    def _get_current_price(self) -> Optional[float]:
        """Get current stock price"""
        try:
            # Try multiple possible price fields
            price_fields = [
                'regularMarketPrice',
                'currentPrice',
                'ask',
                'bid',
                'previousClose'
            ]
            
            for field in price_fields:
                if field in self.info and self.info[field] is not None:
                    price = self.info[field]
                    if isinstance(price, (int, float)):
                        return float(price)
            
            # Try to get from history
            hist = self.stock.history(period='1d', interval='1m')
            if not hist.empty:
                return float(hist['Close'].iloc[-1])
                
        except:
            pass
        return None
    
    def _get_day_change(self) -> Optional[float]:
        """Get day change amount"""
        try:
            current_price = self._get_current_price()
            if current_price is not None and 'previousClose' in self.info:
                previous_close = self.info['previousClose']
                if previous_close is not None and previous_close > 0:
                    return round(current_price - previous_close, 2)
        except:
            pass
        return None
    
    def _get_day_change_percent(self) -> Optional[float]:
        """Get day change percentage"""
        try:
            # Try direct field first
            if 'regularMarketChangePercent' in self.info and self.info['regularMarketChangePercent'] is not None:
                return round(self.info['regularMarketChangePercent'], 2)
            
            # Calculate from price and previous close
            current_price = self._get_current_price()
            if current_price is not None and 'previousClose' in self.info:
                previous_close = self.info['previousClose']
                if previous_close is not None and previous_close > 0:
                    return round(((current_price - previous_close) / previous_close), 2)
        except:
            pass
        return None
    
    def _get_market_cap(self) -> str:
        """Format market cap"""
        try:
            if 'marketCap' in self.info and self.info['marketCap'] is not None:
                market_cap = self.info['marketCap']
                
                # Format market cap
                if market_cap >= 1e12:
                    return f"${market_cap/1e12:.1f}T"
                elif market_cap >= 1e9:
                    return f"${market_cap/1e9:.1f}B"
                elif market_cap >= 1e6:
                    return f"${market_cap/1e6:.1f}M"
                else:
                    return f"${market_cap:,.0f}"
        except:
            pass
        return ""
    
    def _get_52w_range_values(self) -> tuple:
        """Get 52-week range values"""
        try:
            low = self.info.get('fiftyTwoWeekLow')
            high = self.info.get('fiftyTwoWeekHigh')
            
            if low is not None and high is not None:
                return float(low), float(high)
        except:
            pass
        return None, None
    
    def _format_52w_range(self, low: Optional[float], high: Optional[float]) -> str:
        """Format 52-week range string"""
        if low is not None and high is not None:
            return f"${low:.2f} - ${high:.2f}"
        return ""
    
    def _create_range_bar(self, current_price: Optional[float], low: Optional[float], high: Optional[float]) -> str:
        """Create visual bar for 52-week range"""
        if current_price is not None and low is not None and high is not None and high > low:
            # Calculate position in range (0 to 1)
            position = (current_price - low) / (high - low)
            
            # Create a 10-character bar
            filled = int(position * 10)
            filled = max(0, min(10, filled))  # Clamp between 0 and 10
            bar = "▓" * filled + "░" * (10 - filled)
            return bar
        return ""
    
    def _get_sector(self) -> str:
        """Get company sector"""
        try:
            sector = self.info.get('sector')
            if sector:
                return str(sector)
        except:
            pass
        return ""
    
    def _get_industry(self) -> str:
        """Get company industry"""
        try:
            industry = self.info.get('industry')
            if industry:
                return str(industry)
        except:
            pass
        return ""
    
    def _get_day_change_color(self, day_change_percent: Optional[float]) -> str:
        """Determine color for day change"""
        if day_change_percent is None:
            return "neutral"
        return "green" if day_change_percent >= 0 else "red"
    
    def _get_company_description(self) -> str:
        """Get company description"""
        try:
            description = self.info.get('longBusinessSummary')
            if description:
                return str(description)
        except:
            pass
        return ""
    
    def _get_strategic_focus(self) -> str:
        """Get strategic focus"""
        # Not available in yfinance
        return ""
    
    def _get_core_products(self) -> List[str]:
        """Get core products/services"""
        # yfinance doesn't have structured product data
        return []
    
    def _get_revenue_drivers(self) -> List[str]:
        """Get primary revenue drivers"""
        # yfinance doesn't have structured revenue driver data
        return []
    
    def _get_geographic_exposure(self) -> List[str]:
        """Get geographic exposure"""
        try:
            country = self.info.get('country')
            if country:
                return [str(country)]
        except:
            pass
        return []
    
    def _get_major_initiatives(self) -> List[str]:
        """Get major initiatives"""
        # Not available in yfinance
        return []
    
    def _get_capital_allocation(self) -> List[str]:
        """Get capital allocation focus"""
        try:
            allocation = []
            
            # Check for dividends
            dividend_yield = self.info.get('dividendYield')
            if dividend_yield is not None:
                allocation.append(f"Dividend Yield: {dividend_yield*100:.2f}%")
            
            # Check for payout ratio
            payout_ratio = self.info.get('payoutRatio')
            if payout_ratio is not None:
                allocation.append(f"Payout Ratio: {payout_ratio*100:.1f}%")
            
            return allocation
        except:
            pass
        return []
    
    def _get_empty_snapshot(self) -> Dict[str, Any]:
        """Return empty snapshot when data is unavailable"""
        return {
            "ticker": self.ticker,
            "metrics": {
                "price": "",
                "day": "",
                "day_change": "",
                "day_color": "neutral",
                "market_cap": "",
                "week_52_range": "",
                "week_52_range_bar": "",
                "sector": "",
                "industry": ""
            },
            "timestamp": datetime.datetime.now().isoformat()
        }

    def get_earnings_report(self) -> Dict[str, Any]:
        result = {
            "eps_history": [],
            "latest_earnings_transcript": ""
        }

        def get_eps_info() -> List[Dict[str, Any]]:
            earnings_calendar = self.stock.earnings_dates

            if earnings_calendar is None or earnings_calendar.empty:
                return []

            eps_history: List[Dict[str, Any]] = []
            
            # Iterate through all earnings dates
            for date, row in earnings_calendar.iterrows():
                # Skip if this is an upcoming earnings (no reported EPS yet)
                if pd.isna(row["Reported EPS"]):
                    continue
                    
                eps_history.append({
                    "date": date.strftime("%Y-%m-%d"),
                    "eps_estimate": float(row["EPS Estimate"]) if not pd.isna(row["EPS Estimate"]) else None,
                    "reported_eps": float(row["Reported EPS"]),
                    "surprise_percent": float(row["Surprise(%)"]) if not pd.isna(row["Surprise(%)"]) else None
                })

            # Return the latest 5 past earnings (most recent last)
            return eps_history[-5:] if len(eps_history) > 5 else eps_history

        def get_latest_earnings_transcript() -> str:

            earnings_calendar = self.stock.earnings_dates

            print()
            print(earnings_calendar)
            print()

            if earnings_calendar is None or earnings_calendar.empty:
                return "No earnings info available"

            # Find the most recent earnings with a reported EPS
            latest_earnings = None
            for date, row in earnings_calendar.iterrows():
                if not pd.isna(row["Reported EPS"]):
                    latest_earnings = (date, row)
            
            if latest_earnings is None:
                return "No past earnings available"

            date, _ = latest_earnings
            year = date.year
            quarter = (date.month - 1) // 3 + 1

            try:
                pass
            except Exception as e:
                return f"Transcript not available: {str(e)}"

        # Populate results
        result["eps_history"] = get_eps_info()
        result["latest_earnings_transcript"] = get_latest_earnings_transcript()

        return result
        
        

# test analyst consensus function
if __name__ == "__main__":
    ticker = "MSFT"
    stockResearchService = StockResearchService(ticker)
    earnings_report = stockResearchService.get_earnings_report()
    print(earnings_report)
