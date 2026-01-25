import yfinance as yf
import pandas as pd
import finqual as fq
from typing import Dict, Any, Optional, List
from .baze_analyzer import BaseAnalyzer

class FinancialFoundationAnalyzer(BaseAnalyzer):
    """Handles financial foundation data including trends and metrics"""
    
    def __init__(self, ticker: str):
        super().__init__(ticker)
        self.financials_cache = {}
    
    def get_financial_foundation(self) -> Dict[str, Any]:
        """Get complete financial foundation data"""
        try:
            finqual_data = self._get_finqual_data()
            income_data = self._get_income_data()
            cashflow_data = self._get_cashflow_data()
            
            return {
                "purpose": "Answer: Is this a real business with durable finances?",
                "core_trends": {
                    "revenue": self._format_revenue_data(income_data, finqual_data),
                    "net_income": self._format_net_income_data(income_data, finqual_data),
                    "free_cash_flow": self._format_fcf_data(cashflow_data, income_data, finqual_data),
                    "margins": self._format_margin_data(income_data)
                },
                "survivability_metrics": self._get_survivability_metrics(),
                "quality_metrics": self._get_quality_metrics(),
                "chart_tabs": ["Revenue", "Net Income", "Free Cash Flow", "Margins"],
                "note": "Clean multi-year line charts without cluttered indicators"
            }
        except:
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
    
    def _get_finqual_data(self) -> Dict[str, Any]:
        """Get data from finqual API"""
        data = {"cash_flows": [], "cash_flow_years": [], "revenues": [], "revenue_years": [], 
                "net_incomes": [], "net_income_years": []}
        try:
            income_stmt = fq.Finqual(self.ticker).income_stmt_period(0, 2025)
            cash_flow = fq.Finqual(self.ticker).cash_flow_period(0, 2025)
            
            income_dict = {row[0]: {income_stmt.columns[i]: row[i] for i in range(1, len(row))}
                          for row in income_stmt.to_numpy()}
            cash_flow_dict = {row[0]: {cash_flow.columns[i]: row[i] for i in range(1, len(row))}
                             for row in cash_flow.to_numpy()}
            
            operating_cf = list(cash_flow_dict["Operating Cash Flow"].values())
            investing_cf = list(cash_flow_dict["Investing Cash Flow"].values())
            years = list(cash_flow_dict["Operating Cash Flow"].keys())
            
            data["cash_flows"] = [op + inv for op, inv in zip(operating_cf, investing_cf)]
            data["cash_flow_years"] = years
            data["revenues"] = list(income_dict["Total Revenue"].values())
            data["revenue_years"] = list(income_dict["Total Revenue"].keys())
            data["net_incomes"] = list(income_dict["Net Income"].values())
            data["net_income_years"] = list(income_dict["Net Income"].keys())
        except:
            pass
        return data

    def _get_income_data(self) -> Dict[str, Any]:
        """Get income statement data"""
        if 'income_data' in self.financials_cache:
            return self.financials_cache['income_data']
        
        try:
            income_stmt = self.stock.financials
            if income_stmt.empty:
                return {}
            
            years = sorted(income_stmt.columns, reverse=True)[:10]
            data = {
                'years': [str(year.year) for year in years],
                'revenue': [], 'net_income': [], 'gross_profit': [], 'operating_income': []
            }
            
            for year in years:
                data['revenue'].append(self._extract_financial_value(income_stmt, year, 'Total Revenue', 'Revenue'))
                data['net_income'].append(self._extract_financial_value(income_stmt, year, 'Net Income'))
                data['gross_profit'].append(self._extract_financial_value(income_stmt, year, 'Gross Profit'))
                data['operating_income'].append(self._extract_financial_value(income_stmt, year, 'Operating Income'))
            
            self.financials_cache['income_data'] = data
            return data
        except:
            return {}
    
    def _get_cashflow_data(self) -> Dict[str, Any]:
        """Get cash flow data"""
        if 'cashflow_data' in self.financials_cache:
            return self.financials_cache['cashflow_data']
        
        try:
            cashflow = self.stock.cashflow
            if cashflow.empty:
                return {}
            
            years = sorted(cashflow.columns, reverse=True)[:10]
            data = {
                'years': [str(year.year) for year in years],
                'operating_cashflow': [], 'free_cashflow': [], 'capex': []
            }
            
            for year in years:
                op_cf = self._extract_financial_value(cashflow, year, 'Operating Cash Flow', 'Total Cash From Operating Activities')
                capex = self._extract_financial_value(cashflow, year, 'Capital Expenditure') or 0
                
                data['operating_cashflow'].append(op_cf)
                data['capex'].append(capex)
                data['free_cashflow'].append(op_cf - capex if op_cf else None)
            
            self.financials_cache['cashflow_data'] = data
            return data
        except:
            return {}
    
    def _extract_financial_value(self, financials: pd.DataFrame, year, *possible_keys):
        """Extract financial value trying multiple keys"""
        for key in possible_keys:
            try:
                if key in financials.index:
                    value = financials.loc[key, year]
                    if pd.notna(value):
                        return float(value)
            except:
                continue
        return None
    
    def _format_revenue_data(self, income_data: Dict, finqual_data: Dict) -> Dict[str, Any]:
        """Format revenue data"""
        revenues = finqual_data.get("revenues") or income_data.get('revenue', [])
        years = finqual_data.get("revenue_years") or income_data.get('years', [])[:len(revenues)]
        
        if not revenues:
            return {"data": [], "years": [], "growth_rate": None, "trend": "Unknown"}
        
        growth_rate = None
        if len(revenues) >= 2 and revenues[0] and revenues[-1] and revenues[-1] > 0:
            n_years = len(years) - 1
            growth_rate = ((revenues[0] / revenues[-1]) ** (1/n_years) - 1) * 100
        
        return {
            "data": [{"year": y, "value": v} for y, v in zip(years, revenues)],
            "years": years, "values": revenues, "unit": "USD",
            "growth_rate": round(growth_rate, 2) if growth_rate else None,
            "trend": self._determine_trend(revenues),
            "last_value": revenues[0] if revenues else None
        }
    
    def _format_net_income_data(self, income_data: Dict, finqual_data: Dict) -> Dict[str, Any]:
        """Format net income data"""
        net_incomes = finqual_data.get("net_incomes") or income_data.get('net_income', [])
        years = finqual_data.get("net_income_years") or income_data.get('years', [])[:len(net_incomes)]
        
        if not net_incomes:
            return {"data": [], "years": [], "profitability": "Unknown"}
        
        profitable_years = sum(1 for ni in net_incomes if ni and ni > 0)
        profitability = ("Profitable" if profitable_years == len(net_incomes) else
                        "Mostly Profitable" if profitable_years >= len(net_incomes) * 0.7 else
                        "Mixed" if profitable_years >= len(net_incomes) * 0.3 else "Unprofitable")
        
        return {
            "data": [{"year": y, "value": v} for y, v in zip(years, net_incomes)],
            "years": years, "values": net_incomes, "unit": "USD",
            "profitability": profitability,
            "trend": self._determine_trend(net_incomes),
            "last_value": net_incomes[0] if net_incomes else None
        }
    
    def _format_fcf_data(self, cashflow_data: Dict, income_data: Dict, finqual_data: Dict) -> Dict[str, Any]:
        """Format free cash flow data"""
        fcf = finqual_data.get("cash_flows") or cashflow_data.get('free_cashflow', [])
        years = finqual_data.get("cash_flow_years") or cashflow_data.get('years', [])[:len(fcf)]
        
        if not fcf:
            return {"data": [], "years": [], "cash_generator": "Unknown"}
        
        operating_cf = cashflow_data.get('operating_cashflow', [])
        capex = cashflow_data.get('capex', [])
        net_income = income_data.get('net_income', [])
        sbc_values = self._get_stock_based_compensation()
        revenue_values = income_data.get('revenue', [])
        
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
        
        positive_cash_years = sum(1 for cash in fcf if cash and cash > 0)
        cash_generator = ("Positive FCF" if positive_cash_years == len(fcf) else
                         "Mostly Positive" if positive_cash_years >= len(fcf) * 0.7 else
                         "Mixed" if positive_cash_years >= len(fcf) * 0.3 else "Cash Burner")
        
        quality_metrics = self._calculate_fcf_quality_metrics(fcf, operating_cf, net_income, capex, sbc_values, revenue_values)
        red_flags = self._detect_cashflow_red_flags(fcf, operating_cf, net_income, revenue_values)
        
        return {
            "data": data_array, "years": years, "values": fcf, "unit": "USD",
            "cash_generator": cash_generator, "trend": self._determine_trend(fcf),
            "last_value": fcf[0] if fcf else None,
            "quality_metrics": quality_metrics, "red_flags": red_flags
        }
    
    def _get_stock_based_compensation(self) -> List[Optional[float]]:
        """Get stock-based compensation"""
        try:
            cashflow = self.stock.cashflow
            if cashflow.empty:
                return []
            
            years = sorted(cashflow.columns, reverse=True)[:10]
            sbc_values = []
            possible_keys = ['Stock Based Compensation', 'Stock-Based Compensation', 
                           'Share Based Compensation', 'Issuance Of Stock']
            
            for year in years:
                sbc = None
                for key in possible_keys:
                    if key in cashflow.index:
                        value = cashflow.loc[key, year]
                        if pd.notna(value):
                            sbc = abs(float(value))
                            break
                sbc_values.append(sbc)
            return sbc_values
        except:
            return []
    
    def _calculate_fcf_quality_metrics(self, fcf, operating_cf, net_income, capex, sbc, revenue) -> Dict[str, Any]:
        """Calculate FCF quality metrics"""
        metrics = {}
        try:
            latest_fcf = next((f for f in fcf if f is not None), None)
            latest_ocf = next((o for o in operating_cf if o is not None), None)
            latest_ni = next((n for n in net_income if n is not None), None)
            latest_capex = next((c for c in capex if c is not None), None)
            latest_sbc = next((s for s in sbc if s is not None), None)
            latest_revenue = next((r for r in revenue if r is not None), None)
            
            if latest_ocf and latest_ni and latest_ni != 0:
                ratio = latest_ocf / latest_ni
                metrics['ocf_to_net_income'] = {
                    "value": f"{ratio:.2f}x",
                    "status": "Excellent" if ratio >= 1.2 else "Good" if ratio >= 1.0 else "Warning" if ratio >= 0.8 else "Concerning"
                }
            
            if latest_fcf and latest_revenue and latest_revenue != 0:
                fcf_margin = (latest_fcf / latest_revenue) * 100
                metrics['fcf_margin'] = {
                    "value": f"{fcf_margin:.1f}%",
                    "status": "Excellent" if fcf_margin >= 15 else "Good" if fcf_margin >= 10 else "Moderate" if fcf_margin >= 5 else "Poor"
                }
            
            shares_outstanding = self.info.get('sharesOutstanding')
            if latest_fcf and shares_outstanding:
                fcf_per_share = latest_fcf / shares_outstanding
                metrics['fcf_per_share'] = {
                    "value": f"${fcf_per_share:.2f}",
                    "status": "Positive" if fcf_per_share > 0 else "Negative"
                }
            
            valid_capex = [c for c in capex if c is not None]
            if len(valid_capex) >= 2 and latest_revenue:
                avg_capex = sum(valid_capex) / len(valid_capex)
                capex_intensity = (avg_capex / latest_revenue) * 100
                capex_trend = self._determine_trend(valid_capex)
                metrics['capex_trend'] = {
                    "value": f"{capex_intensity:.1f}% of Revenue",
                    "status": capex_trend,
                    "trend_direction": "Increasing" if capex_trend in ["Upward", "Strong Upward"] else "Decreasing" if capex_trend in ["Downward", "Strong Downward"] else "Stable"
                }
            
            if latest_sbc and latest_ocf and latest_ocf != 0:
                sbc_ratio = (latest_sbc / latest_ocf) * 100
                metrics['sbc_ratio'] = {
                    "value": f"{sbc_ratio:.1f}%",
                    "status": "Good" if sbc_ratio < 10 else "Moderate" if sbc_ratio < 20 else "Concerning"
                }
        except:
            pass
        return metrics
    
    def _detect_cashflow_red_flags(self, fcf, operating_cf, net_income, revenue) -> List[str]:
        """Detect red flags in cash flow"""
        flags = []
        try:
            recent_fcf = [f for f in fcf[:3] if f is not None]
            recent_ocf = [o for o in operating_cf[:3] if o is not None]
            recent_ni = [n for n in net_income[:3] if n is not None]
            recent_revenue = [r for r in revenue[:3] if r is not None]
            
            if len(recent_revenue) >= 2 and len(recent_ocf) >= 2:
                revenue_growing = recent_revenue[0] > recent_revenue[-1]
                negative_ocf = any(ocf < 0 for ocf in recent_ocf)
                if revenue_growing and negative_ocf:
                    flags.append("Rising revenue but negative operating cash flow - possible earnings quality issue")
            
            if len(recent_fcf) >= 2 and all(f < 0 for f in recent_fcf):
                flags.append("Consistently negative free cash flow - burning cash")
            
            if len(recent_ocf) >= 1 and len(recent_ni) >= 1:
                if recent_ni[0] > 0 and recent_ocf[0] < recent_ni[0] * 0.7:
                    flags.append("Operating cash flow significantly below net income - potential earnings quality concern")
            
            if len(recent_fcf) >= 3 and all(recent_fcf[i] < recent_fcf[i+1] for i in range(len(recent_fcf)-1)):
                flags.append("Free cash flow declining for multiple consecutive years")
        except:
            pass
        return flags

    def _format_margin_data(self, income_data: Dict) -> Dict[str, Any]:
        """Format margin data"""
        if not income_data or not income_data.get('revenue'):
            return {"data": [], "years": [], "margins": []}
        
        revenues = income_data['revenue']
        net_incomes = income_data.get('net_income', [])
        gross_profits = income_data.get('gross_profit', [])
        operating_incomes = income_data.get('operating_income', [])
        years = income_data['years'][:len(revenues)]
        
        margins = []
        for i in range(min(len(years), len(revenues))):
            year_data = {"year": years[i]}
            
            if i < len(gross_profits) and revenues[i] and revenues[i] != 0 and gross_profits[i]:
                year_data["gross_margin"] = round((gross_profits[i] / revenues[i]) * 100, 1)
            
            if i < len(operating_incomes) and revenues[i] and revenues[i] != 0 and operating_incomes[i]:
                year_data["operating_margin"] = round((operating_incomes[i] / revenues[i]) * 100, 1)
            
            if net_incomes[i] and revenues[i] and revenues[i] != 0:
                year_data["net_margin"] = round((net_incomes[i] / revenues[i]) * 100, 1)
            
            margins.append(year_data)
        
        avg_margins = {}
        for margin_type in ["gross_margin", "operating_margin", "net_margin"]:
            values = [m[margin_type] for m in margins if margin_type in m and m[margin_type] is not None]
            if values:
                avg_margins[margin_type] = round(sum(values) / len(values), 1)
        
        net_margins = [m.get("net_margin") for m in margins if m.get("net_margin")]
        margin_trend = self._determine_trend(net_margins) if net_margins else "Unknown"
        
        return {
            "data": margins, "years": years,
            "margins": ["Gross Margin", "Operating Margin", "Net Margin"],
            "average_margins": avg_margins, "trend": margin_trend
        }
    
    def _determine_trend(self, values: List[Optional[float]]) -> str:
        """Determine trend direction from values"""
        if not values or len(values) < 2:
            return "Unknown"
        
        valid_values = [(i, v) for i, v in enumerate(values) if v is not None]
        if len(valid_values) < 2:
            return "Insufficient Data"
        
        first = valid_values[-1][1]
        last = valid_values[0][1]
        
        if last is None or first is None or first == 0:
            return "Unknown"
        
        change_percent = ((last - first) / abs(first)) * 100
        
        if change_percent > 10:
            return "Strong Upward"
        elif change_percent > 2:
            return "Upward"
        elif change_percent < -10:
            return "Strong Downward"
        elif change_percent < -2:
            return "Downward"
        return "Stable"
    
    def _get_survivability_metrics(self) -> Dict[str, Any]:
        """Get survivability metrics"""
        metrics = {}
        try:
            if 'currentRatio' in self.info and self.info['currentRatio']:
                current_ratio = float(self.info['currentRatio'])
                metrics['current_ratio'] = {
                    "value": round(current_ratio, 2),
                    "status": "Good" if current_ratio >= 1.5 else "Adequate" if current_ratio >= 1.0 else "Concerning"
                }
            
            if 'debtToEquity' in self.info and self.info['debtToEquity']:
                debt_to_equity = float(self.info['debtToEquity'])
                metrics['debt_to_equity'] = {
                    "value": round(debt_to_equity, 2),
                    "status": "Low" if debt_to_equity < 0.5 else "Moderate" if debt_to_equity < 1.0 else "High"
                }
            
            if 'interestCoverage' in self.info and self.info['interestCoverage']:
                interest_coverage = float(self.info['interestCoverage'])
                metrics['interest_coverage'] = {
                    "value": round(interest_coverage, 2),
                    "status": "Strong" if interest_coverage > 5 else "Adequate" if interest_coverage > 2 else "Weak"
                }
            
            if 'quickRatio' in self.info and self.info['quickRatio']:
                quick_ratio = float(self.info['quickRatio'])
                metrics['quick_ratio'] = {
                    "value": round(quick_ratio, 2),
                    "status": "Good" if quick_ratio >= 1.0 else "Concerning"
                }
        except:
            pass
        return metrics
    
    def _get_quality_metrics(self) -> Dict[str, Any]:
        """Get quality metrics"""
        metrics = {}
        try:
            if 'returnOnEquity' in self.info and self.info['returnOnEquity']:
                roe = float(self.info['returnOnEquity']) * 100
                metrics['return_on_equity'] = {
                    "value": round(roe, 1), "unit": "%",
                    "status": "Excellent" if roe > 20 else "Good" if roe > 15 else "Average" if roe > 10 else "Poor"
                }
            
            if 'returnOnAssets' in self.info and self.info['returnOnAssets']:
                roa = float(self.info['returnOnAssets']) * 100
                metrics['return_on_assets'] = {
                    "value": round(roa, 1), "unit": "%",
                    "status": "Excellent" if roa > 10 else "Good" if roa > 5 else "Average" if roa > 2 else "Poor"
                }
            
            if 'operatingMargins' in self.info and self.info['operatingMargins']:
                op_margin = float(self.info['operatingMargins']) * 100
                metrics['operating_margin'] = {
                    "value": round(op_margin, 1), "unit": "%",
                    "status": "Excellent" if op_margin > 20 else "Good" if op_margin > 15 else "Average" if op_margin > 10 else "Poor"
                }
            
            if 'profitMargins' in self.info and self.info['profitMargins']:
                net_margin = float(self.info['profitMargins']) * 100
                metrics['net_margin'] = {
                    "value": round(net_margin, 1), "unit": "%",
                    "status": "Excellent" if net_margin > 15 else "Good" if net_margin > 10 else "Average" if net_margin > 5 else "Poor"
                }
        except:
            pass
        return metrics
