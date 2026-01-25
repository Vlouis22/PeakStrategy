import yfinance as yf
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .baze_analyzer import BaseAnalyzer
from .snapshot_analyzer import SnapshotAnalyzer



class ProfitabilityAnalyzer(BaseAnalyzer):
    """Professional-grade stock profitability and efficiency analyzer"""
    
    def analyze_profitability(self) -> Dict:
        """Gather and compute all profitability and efficiency metrics"""
        try:
            balance_sheet = self.stock.balance_sheet
            income_stmt = self.stock.income_stmt
            
            if balance_sheet.empty or income_stmt.empty:
                return {"error": "Unable to fetch financial data for this ticker"}
            
            latest_bs = balance_sheet.iloc[:, 0]
            latest_is = income_stmt.iloc[:, 0]
            
            total_assets = self._sanitize_value(latest_bs.get('Total Assets', None))
            total_equity = self._sanitize_value(
                latest_bs.get('Stockholders Equity', None) or 
                latest_bs.get('Total Equity Gross Minority Interest', None)
            )
            total_debt = self._sanitize_value(latest_bs.get('Total Debt', 0)) or 0
            
            net_income = self._sanitize_value(latest_is.get('Net Income', None))
            operating_income = self._sanitize_value(latest_is.get('Operating Income', None))
            total_revenue = self._sanitize_value(latest_is.get('Total Revenue', None))
            gross_profit = self._sanitize_value(latest_is.get('Gross Profit', None))
            interest_expense = abs(self._sanitize_value(latest_is.get('Interest Expense', 0)) or 0)
            
            tax_rate = self._get_tax_rate(income_stmt)
            
            roe = self._safe_division(net_income, total_equity)
            roa = self._safe_division(net_income, total_assets)
            roic = self._compute_roic(net_income, interest_expense, tax_rate, total_debt, total_equity)
            
            gross_margin = self._safe_division(gross_profit, total_revenue)
            operating_margin = self._safe_division(operating_income, total_revenue)
            net_margin = self._safe_division(net_income, total_revenue)
            
            trends = self._compute_trends(income_stmt, balance_sheet)
            operating_leverage = self._compute_operating_leverage(income_stmt)
            
            return {
                "ticker": self.ticker,
                "timestamp": datetime.now().isoformat(),
                "metrics": {
                    "roe": roe * 100 if roe is not None else None,
                    "roa": roa * 100 if roa is not None else None,
                    "roic": roic * 100 if roic is not None else None,
                    "gross_margin": gross_margin * 100 if gross_margin is not None else None,
                    "operating_margin": operating_margin * 100 if operating_margin is not None else None,
                    "net_margin": net_margin * 100 if net_margin is not None else None,
                },
                "trends": trends,
                "operating_leverage": operating_leverage,
                "raw_data": {
                    "total_assets": total_assets,
                    "total_equity": total_equity,
                    "total_debt": total_debt,
                    "net_income": net_income,
                    "total_revenue": total_revenue,
                    "operating_income": operating_income,
                    "tax_rate": tax_rate * 100,
                }
            }
        except Exception as e:
            return {"error": f"Analysis failed: {str(e)}"}
    
    def _compute_roic(self, net_income: float, interest_expense: float, 
                      tax_rate: float, total_debt: float, total_equity: float) -> Optional[float]:
        """Compute Return on Invested Capital (ROIC)"""
        try:
            if any(x is None for x in [net_income, interest_expense, tax_rate, total_debt, total_equity]):
                return None
            
            net_income = self._sanitize_value(net_income)
            interest_expense = self._sanitize_value(interest_expense)
            tax_rate = self._sanitize_value(tax_rate)
            total_debt = self._sanitize_value(total_debt)
            total_equity = self._sanitize_value(total_equity)
            
            if any(x is None for x in [net_income, interest_expense, tax_rate, total_debt, total_equity]):
                return None
                
            nopat = net_income + (interest_expense * (1 - tax_rate))
            invested_capital = total_debt + total_equity
            
            return self._safe_division(nopat, invested_capital)
        except:
            return None
    
    def _get_tax_rate(self, income_stmt: pd.DataFrame) -> float:
        """Extract or estimate effective tax rate"""
        try:
            if 'Tax Provision' in income_stmt.index and 'Pretax Income' in income_stmt.index:
                tax_provision = income_stmt.loc['Tax Provision'].iloc[0]
                pretax_income = income_stmt.loc['Pretax Income'].iloc[0]
                
                tax_provision = self._sanitize_value(tax_provision)
                pretax_income = self._sanitize_value(pretax_income)
                
                if pretax_income and pretax_income != 0 and tax_provision is not None:
                    rate = abs(tax_provision / pretax_income)
                    rate = self._sanitize_value(rate)
                    if rate is not None and 0 <= rate <= 1:
                        return rate
            return 0.21
        except:
            return 0.21
    
    def _compute_trends(self, income_stmt: pd.DataFrame, balance_sheet: pd.DataFrame) -> Dict:
        """Compute multi-year trends for margins and returns"""
        trends = {
            "gross_margin_trend": [],
            "operating_margin_trend": [],
            "roe_trend": [],
            "roic_trend": []
        }
        
        num_periods = min(5, income_stmt.shape[1])
        
        for i in range(num_periods):
            try:
                is_col = income_stmt.iloc[:, i]
                bs_col = balance_sheet.iloc[:, i]
                
                revenue = self._sanitize_value(is_col.get('Total Revenue', None))
                gross_profit = self._sanitize_value(is_col.get('Gross Profit', None))
                operating_income = self._sanitize_value(is_col.get('Operating Income', None))
                net_income = self._sanitize_value(is_col.get('Net Income', None))
                
                equity = self._sanitize_value(
                    bs_col.get('Stockholders Equity', None) or 
                    bs_col.get('Total Equity Gross Minority Interest', None)
                )
                debt = self._sanitize_value(bs_col.get('Total Debt', 0)) or 0
                interest_exp = abs(self._sanitize_value(is_col.get('Interest Expense', 0)) or 0)
                
                year = income_stmt.columns[i].year
                
                gm = self._safe_division(gross_profit, revenue)
                om = self._safe_division(operating_income, revenue)
                roe = self._safe_division(net_income, equity)
                
                tax_rate = self._get_tax_rate(income_stmt)
                roic = self._compute_roic(net_income, interest_exp, tax_rate, debt, equity)
                
                trends["gross_margin_trend"].append({
                    "year": year,
                    "value": gm * 100 if gm is not None else None
                })
                trends["operating_margin_trend"].append({
                    "year": year,
                    "value": om * 100 if om is not None else None
                })
                trends["roe_trend"].append({
                    "year": year,
                    "value": roe * 100 if roe is not None else None
                })
                trends["roic_trend"].append({
                    "year": year,
                    "value": roic * 100 if roic is not None else None
                })
            except:
                continue
        
        return trends
    
    def _compute_operating_leverage(self, income_stmt: pd.DataFrame) -> Dict:
        """Analyze operating leverage"""
        leverage_data = []
        
        num_periods = min(5, income_stmt.shape[1] - 1)
        
        for i in range(num_periods):
            try:
                current = income_stmt.iloc[:, i]
                previous = income_stmt.iloc[:, i + 1]
                
                curr_revenue = self._sanitize_value(current.get('Total Revenue', None))
                prev_revenue = self._sanitize_value(previous.get('Total Revenue', None))
                curr_op_income = self._sanitize_value(current.get('Operating Income', None))
                prev_op_income = self._sanitize_value(previous.get('Operating Income', None))
                
                if all(x is not None and x != 0 for x in [curr_revenue, prev_revenue, curr_op_income, prev_op_income]):
                    revenue_growth = ((curr_revenue - prev_revenue) / abs(prev_revenue)) * 100
                    op_income_growth = ((curr_op_income - prev_op_income) / abs(prev_op_income)) * 100
                    
                    revenue_growth = self._sanitize_value(revenue_growth)
                    op_income_growth = self._sanitize_value(op_income_growth)
                    
                    leverage_ratio = None
                    if revenue_growth is not None and revenue_growth != 0:
                        leverage_ratio = self._safe_division(op_income_growth, revenue_growth)
                    
                    if revenue_growth is not None or op_income_growth is not None:
                        leverage_data.append({
                            "year": income_stmt.columns[i].year,
                            "revenue_growth": revenue_growth,
                            "operating_income_growth": op_income_growth,
                            "leverage_ratio": leverage_ratio
                        })
            except:
                continue
        
        return {
            "data": leverage_data,
            "interpretation": "Leverage > 1 indicates operating income growing faster than revenue (positive operating leverage)"
        }