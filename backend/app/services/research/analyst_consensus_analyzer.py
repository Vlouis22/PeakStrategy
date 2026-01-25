import yfinance as yf
import numpy as np
from typing import Dict, Any
from .baze_analyzer import BaseAnalyzer

class AnalystConsensusAnalyzer(BaseAnalyzer):
    """Fetch analyst consensus data"""
    
    def get_analyst_consensus(self) -> Dict[str, Any]:
        """Return analyst consensus, price targets, earnings outlook, and growth profile"""
        result = {
            "ticker": self.ticker,
            "price_targets": {"average": None, "low": None, "high": None, "current_price": None},
            "consensus_history": [],
            "earnings_outlook": {"next_quarter_eps_avg": None, "next_quarter_revenue_avg": None, "next_quarter_growth_avg": None},
            "growth_profile": {
                "revenue_growth": {"yoy_current": None, "yoy_current_period": None, "yoy_projected_next_year": None, "cagr_3_5_year": None},
                "earnings_growth": {"yoy_current": None, "yoy_current_period": None, "yoy_projected_next_year": None, "eps_next_quarter_estimate": None, "eps_next_year_estimate": None, "eps_current_year_estimate": None},
                "free_cash_flow_growth": {"yoy_current": None, "fcf_current": None, "fcf_previous": None},
                "analyst_estimates": {"revenue_next_quarter": None, "revenue_next_year": None, "revenue_current_year": None, "eps_next_quarter": None, "eps_next_year": None, "eps_current_year": None, "growth_next_5_years": None, "peg_ratio": None}
            },
            "data_available": False
        }
        
        try:
            result["price_targets"] = {
                "average": self.info.get("targetMeanPrice"),
                "low": self.info.get("targetLowPrice"),
                "high": self.info.get("targetHighPrice"),
                "current_price": self.info.get("currentPrice")
            }
            
            trend_df = self.stock.recommendations_summary
            if trend_df is not None and not trend_df.empty:
                for _, row in trend_df.head(4).iterrows():
                    ratings = {
                        "strong_buy": row.get('strongBuy', 0),
                        "buy": row.get('buy', 0),
                        "hold": row.get('hold', 0),
                        "sell": row.get('sell', 0),
                        "strong_sell": row.get('strongSell', 0)
                    }
                    total = sum(ratings.values())
                    if total > 0:
                        result["consensus_history"].append({
                            "period": row.get('period'),
                            "total_analysts": int(total),
                            "breakdown_pct": {k: round((v / total) * 100) for k, v in ratings.items()}
                        })
            
            earnings_est = self.stock.earnings_estimate
            if earnings_est is not None and not earnings_est.empty:
                mask = earnings_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                if mask.any():
                    val = earnings_est[mask].iloc[0, 0]
                    result["earnings_outlook"]["next_quarter_eps_avg"] = float(val) if val is not None else None
            
            revenue_est = self.stock.revenue_estimate
            if revenue_est is not None and not revenue_est.empty:
                mask = revenue_est.index.str.contains('Current Qtr|0Q|Qtr', case=False, na=False)
                if mask.any():
                    val = revenue_est[mask].iloc[0, 0]
                else:
                    val = revenue_est.iloc[0, 0]
                result["earnings_outlook"]["next_quarter_revenue_avg"] = float(val) if val is not None else None
            
            growth_df = self.stock.growth_estimates
            q_growth_val = None
            if growth_df is not None and not growth_df.empty:
                mask = growth_df.index.str.contains('Current Qtr|0Q|Qtr|0q', case=False, na=False)
                if mask.any():
                    val = growth_df[mask]['stockTrend'].iloc[0]
                    if val is not None and not (isinstance(val, float) and np.isnan(val)):
                        q_growth_val = float(val)
            
            if q_growth_val is None:
                q_growth_val = self.info.get("earningsQuarterlyGrowth")
            
            result["earnings_outlook"]["next_quarter_growth_avg"] = q_growth_val
            
            revenue_growth_rate = self.info.get("revenueGrowth")
            if revenue_growth_rate is not None:
                result["growth_profile"]["revenue_growth"]["yoy_current"] = revenue_growth_rate
                result["growth_profile"]["revenue_growth"]["yoy_current_period"] = "quarterly"
            
            if revenue_est is not None and not revenue_est.empty:
                try:
                    current_year_mask = revenue_est.index.str.contains('Current Year|0Y', case=False, na=False)
                    if current_year_mask.any():
                        current_year_rev = revenue_est[current_year_mask].iloc[0, 0]
                        result["growth_profile"]["analyst_estimates"]["revenue_current_year"] = float(current_year_rev) if current_year_rev is not None else None
                    
                    next_year_mask = revenue_est.index.str.contains('Next Year|\\+1Y', case=False, na=False)
                    if next_year_mask.any():
                        next_year_rev = revenue_est[next_year_mask].iloc[0, 0]
                        result["growth_profile"]["analyst_estimates"]["revenue_next_year"] = float(next_year_rev) if next_year_rev is not None else None
                        
                        if current_year_rev and next_year_rev and current_year_rev > 0:
                            yoy_proj = (next_year_rev - current_year_rev) / current_year_rev
                            result["growth_profile"]["revenue_growth"]["yoy_projected_next_year"] = yoy_proj
                    
                    next_qtr_mask = revenue_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                    if next_qtr_mask.any():
                        next_qtr_rev = revenue_est[next_qtr_mask].iloc[0, 0]
                        result["growth_profile"]["analyst_estimates"]["revenue_next_quarter"] = float(next_qtr_rev) if next_qtr_rev is not None else None
                except:
                    pass
            
            earnings_growth_rate = self.info.get("earningsGrowth")
            if earnings_growth_rate is not None:
                result["growth_profile"]["earnings_growth"]["yoy_current"] = earnings_growth_rate
                result["growth_profile"]["earnings_growth"]["yoy_current_period"] = "quarterly"
            
            if earnings_est is not None and not earnings_est.empty:
                try:
                    current_year_mask = earnings_est.index.str.contains('Current Year|0Y', case=False, na=False)
                    if current_year_mask.any():
                        current_year_eps = earnings_est[current_year_mask].iloc[0, 0]
                        result["growth_profile"]["earnings_growth"]["eps_current_year_estimate"] = float(current_year_eps) if current_year_eps is not None else None
                        result["growth_profile"]["analyst_estimates"]["eps_current_year"] = float(current_year_eps) if current_year_eps is not None else None
                    
                    next_year_mask = earnings_est.index.str.contains('Next Year|\\+1Y', case=False, na=False)
                    if next_year_mask.any():
                        next_year_eps = earnings_est[next_year_mask].iloc[0, 0]
                        result["growth_profile"]["earnings_growth"]["eps_next_year_estimate"] = float(next_year_eps) if next_year_eps is not None else None
                        result["growth_profile"]["analyst_estimates"]["eps_next_year"] = float(next_year_eps) if next_year_eps is not None else None
                        
                        if current_year_eps and next_year_eps and current_year_eps > 0:
                            yoy_proj_earnings = (next_year_eps - current_year_eps) / current_year_eps
                            result["growth_profile"]["earnings_growth"]["yoy_projected_next_year"] = yoy_proj_earnings
                    
                    next_qtr_mask = earnings_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                    if next_qtr_mask.any():
                        next_qtr_eps = earnings_est[next_qtr_mask].iloc[0, 0]
                        result["growth_profile"]["earnings_growth"]["eps_next_quarter_estimate"] = float(next_qtr_eps) if next_qtr_eps is not None else None
                        result["growth_profile"]["analyst_estimates"]["eps_next_quarter"] = float(next_qtr_eps) if next_qtr_eps is not None else None
                except:
                    pass
            
            try:
                cashflow_df = self.stock.cashflow
                if cashflow_df is not None and not cashflow_df.empty:
                    if 'Free Cash Flow' in cashflow_df.index:
                        fcf_values = cashflow_df.loc['Free Cash Flow'].dropna()
                        if len(fcf_values) >= 2:
                            fcf_current = fcf_values.iloc[0]
                            fcf_previous = fcf_values.iloc[1]
                            result["growth_profile"]["free_cash_flow_growth"]["fcf_current"] = float(fcf_current)
                            result["growth_profile"]["free_cash_flow_growth"]["fcf_previous"] = float(fcf_previous)
                            
                            if fcf_previous != 0:
                                fcf_growth = (fcf_current - fcf_previous) / abs(fcf_previous)
                                result["growth_profile"]["free_cash_flow_growth"]["yoy_current"] = fcf_growth
                    elif 'Total Cash From Operating Activities' in cashflow_df.index and 'Capital Expenditures' in cashflow_df.index:
                        ocf = cashflow_df.loc['Total Cash From Operating Activities'].dropna()
                        capex = cashflow_df.loc['Capital Expenditures'].dropna()
                        if len(ocf) >= 2 and len(capex) >= 2:
                            fcf_current = ocf.iloc[0] + capex.iloc[0]
                            fcf_previous = ocf.iloc[1] + capex.iloc[1]
                            result["growth_profile"]["free_cash_flow_growth"]["fcf_current"] = float(fcf_current)
                            result["growth_profile"]["free_cash_flow_growth"]["fcf_previous"] = float(fcf_previous)
                            
                            if fcf_previous != 0:
                                fcf_growth = (fcf_current - fcf_previous) / abs(fcf_previous)
                                result["growth_profile"]["free_cash_flow_growth"]["yoy_current"] = fcf_growth
            except:
                pass
            
            if growth_df is not None and not growth_df.empty:
                try:
                    five_year_mask = growth_df.index.str.contains('Next 5 Years|5Y', case=False, na=False)
                    if five_year_mask.any():
                        five_year_growth = growth_df[five_year_mask]['stockTrend'].iloc[0]
                        if five_year_growth is not None and not (isinstance(five_year_growth, float) and np.isnan(five_year_growth)):
                            result["growth_profile"]["analyst_estimates"]["growth_next_5_years"] = float(five_year_growth)
                            result["growth_profile"]["revenue_growth"]["cagr_3_5_year"] = float(five_year_growth)
                except:
                    pass
            
            peg_ratio = self.info.get("pegRatio")
            if peg_ratio is not None:
                result["growth_profile"]["analyst_estimates"]["peg_ratio"] = peg_ratio
            
            if self.info.get("targetMeanPrice") or result["consensus_history"]:
                result["data_available"] = True
        except:
            pass
        
        return result