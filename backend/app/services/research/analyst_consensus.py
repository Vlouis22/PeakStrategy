import yfinance as yf
from typing import Dict, Any
import numpy as np
import pandas as pd


class AnalystConsensus:
    """Fetch Yahoo Finance analyst consensus data for a stock"""

    def __init__(self, ticker: str):
        self.ticker = ticker.upper()
        self.ticker_obj = yf.Ticker(self.ticker)

    def get_yahoo_analyst_consensus(self) -> Dict[str, Any]:
        """Return analyst consensus, price targets, earnings outlook, and growth profile"""
        default_response = {
            "ticker": self.ticker,
            "price_targets": {"average": None, "low": None, "high": None, "current_price": None},
            "consensus_history": [],
            "earnings_outlook": {
                "next_quarter_eps_avg": None, 
                "next_quarter_revenue_avg": None, 
                "next_quarter_growth_avg": None
            },
            "growth_profile": {
                "revenue_growth": {
                    "yoy_current": None,
                    "yoy_current_period": None,  # "quarterly" or "annual"
                    "yoy_projected_next_year": None,
                    "cagr_3_5_year": None
                },
                "earnings_growth": {
                    "yoy_current": None,
                    "yoy_current_period": None,  # "quarterly" or "annual"
                    "yoy_projected_next_year": None,
                    "eps_next_quarter_estimate": None,
                    "eps_next_year_estimate": None,
                    "eps_current_year_estimate": None
                },
                "free_cash_flow_growth": {
                    "yoy_current": None,
                    "fcf_current": None,
                    "fcf_previous": None
                },
                "analyst_estimates": {
                    "revenue_next_quarter": None,
                    "revenue_next_year": None,
                    "revenue_current_year": None,
                    "eps_next_quarter": None,
                    "eps_next_year": None,
                    "eps_current_year": None,
                    "growth_next_5_years": None,
                    "peg_ratio": None
                }
            },
            "data_available": False
        }

        try:
            info = self.ticker_obj.info
            if not info:
                return default_response

            # Price targets
            default_response["price_targets"] = {
                "average": info.get("targetMeanPrice"),
                "low": info.get("targetLowPrice"),
                "high": info.get("targetHighPrice"),
                "current_price": info.get("currentPrice")
            }

            # Recommendation history
            trend_df = self.ticker_obj.recommendations_summary
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
                        default_response["consensus_history"].append({
                            "period": row.get('period'),
                            "total_analysts": int(total),
                            "breakdown_pct": {k: round((v / total) * 100) for k, v in ratings.items()}
                        })

            # Earnings outlook
            earnings_est = self.ticker_obj.earnings_estimate
            if earnings_est is not None and not earnings_est.empty:
                mask = earnings_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                if mask.any():
                    val = earnings_est[mask].iloc[0, 0]
                    default_response["earnings_outlook"]["next_quarter_eps_avg"] = float(val) if val is not None else None

            # Revenue outlook
            revenue_est = self.ticker_obj.revenue_estimate
            if revenue_est is not None and not revenue_est.empty:
                mask = revenue_est.index.str.contains('Current Qtr|0Q|Qtr', case=False, na=False)
                if mask.any():
                    val = revenue_est[mask].iloc[0, 0]
                    default_response["earnings_outlook"]["next_quarter_revenue_avg"] = float(val) if val is not None else None
                else:
                    val = revenue_est.iloc[0, 0]
                    default_response["earnings_outlook"]["next_quarter_revenue_avg"] = float(val) if val is not None else None

            # Growth outlook
            growth_df = self.ticker_obj.growth_estimates
            q_growth_val = None
            if growth_df is not None and not growth_df.empty:
                mask = growth_df.index.str.contains('Current Qtr|0Q|Qtr|0q', case=False, na=False)
                if mask.any():
                    val = growth_df[mask]['stockTrend'].iloc[0]
                    if val is not None and not (isinstance(val, float) and np.isnan(val)):
                        q_growth_val = float(val)

            if q_growth_val is None:
                q_growth_val = info.get("earningsQuarterlyGrowth")

            default_response["earnings_outlook"]["next_quarter_growth_avg"] = q_growth_val

            # ===== GROWTH PROFILE DATA =====
            
            # Revenue Growth
            # Yahoo Finance's revenueGrowth is typically quarterly YoY
            revenue_growth_rate = info.get("revenueGrowth")
            if revenue_growth_rate is not None:
                default_response["growth_profile"]["revenue_growth"]["yoy_current"] = revenue_growth_rate
                default_response["growth_profile"]["revenue_growth"]["yoy_current_period"] = "quarterly"

            # Get revenue estimates for projected growth
            if revenue_est is not None and not revenue_est.empty:
                try:
                    # Current year revenue estimate
                    current_year_mask = revenue_est.index.str.contains('Current Year|0Y', case=False, na=False)
                    if current_year_mask.any():
                        current_year_rev = revenue_est[current_year_mask].iloc[0, 0]
                        default_response["growth_profile"]["analyst_estimates"]["revenue_current_year"] = float(current_year_rev) if current_year_rev is not None else None
                    
                    # Next year revenue estimate
                    next_year_mask = revenue_est.index.str.contains('Next Year|\\+1Y', case=False, na=False)
                    if next_year_mask.any():
                        next_year_rev = revenue_est[next_year_mask].iloc[0, 0]
                        default_response["growth_profile"]["analyst_estimates"]["revenue_next_year"] = float(next_year_rev) if next_year_rev is not None else None
                        
                        # Calculate projected YoY revenue growth
                        if current_year_rev and next_year_rev and current_year_rev > 0:
                            yoy_proj = (next_year_rev - current_year_rev) / current_year_rev
                            default_response["growth_profile"]["revenue_growth"]["yoy_projected_next_year"] = yoy_proj
                    
                    # Next quarter revenue
                    next_qtr_mask = revenue_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                    if next_qtr_mask.any():
                        next_qtr_rev = revenue_est[next_qtr_mask].iloc[0, 0]
                        default_response["growth_profile"]["analyst_estimates"]["revenue_next_quarter"] = float(next_qtr_rev) if next_qtr_rev is not None else None
                except Exception as e:
                    print(f"Error parsing revenue estimates: {e}")

            # Earnings Growth
            # Yahoo Finance's earningsGrowth is typically quarterly YoY
            earnings_growth_rate = info.get("earningsGrowth")
            if earnings_growth_rate is not None:
                default_response["growth_profile"]["earnings_growth"]["yoy_current"] = earnings_growth_rate
                default_response["growth_profile"]["earnings_growth"]["yoy_current_period"] = "quarterly"

            # Get earnings estimates
            if earnings_est is not None and not earnings_est.empty:
                try:
                    # Current year EPS
                    current_year_mask = earnings_est.index.str.contains('Current Year|0Y', case=False, na=False)
                    if current_year_mask.any():
                        current_year_eps = earnings_est[current_year_mask].iloc[0, 0]
                        default_response["growth_profile"]["earnings_growth"]["eps_current_year_estimate"] = float(current_year_eps) if current_year_eps is not None else None
                        default_response["growth_profile"]["analyst_estimates"]["eps_current_year"] = float(current_year_eps) if current_year_eps is not None else None
                    
                    # Next year EPS
                    next_year_mask = earnings_est.index.str.contains('Next Year|\\+1Y', case=False, na=False)
                    if next_year_mask.any():
                        next_year_eps = earnings_est[next_year_mask].iloc[0, 0]
                        default_response["growth_profile"]["earnings_growth"]["eps_next_year_estimate"] = float(next_year_eps) if next_year_eps is not None else None
                        default_response["growth_profile"]["analyst_estimates"]["eps_next_year"] = float(next_year_eps) if next_year_eps is not None else None
                        
                        # Calculate projected YoY earnings growth
                        if current_year_eps and next_year_eps and current_year_eps > 0:
                            yoy_proj_earnings = (next_year_eps - current_year_eps) / current_year_eps
                            default_response["growth_profile"]["earnings_growth"]["yoy_projected_next_year"] = yoy_proj_earnings
                    
                    # Next quarter EPS
                    next_qtr_mask = earnings_est.index.str.contains('Current Qtr|0Q', case=False, na=False)
                    if next_qtr_mask.any():
                        next_qtr_eps = earnings_est[next_qtr_mask].iloc[0, 0]
                        default_response["growth_profile"]["earnings_growth"]["eps_next_quarter_estimate"] = float(next_qtr_eps) if next_qtr_eps is not None else None
                        default_response["growth_profile"]["analyst_estimates"]["eps_next_quarter"] = float(next_qtr_eps) if next_qtr_eps is not None else None
                except Exception as e:
                    print(f"Error parsing earnings estimates: {e}")

            # Free Cash Flow Growth
            try:
                cashflow_df = self.ticker_obj.cashflow
                if cashflow_df is not None and not cashflow_df.empty:
                    # Get Free Cash Flow (Operating Cash Flow - Capital Expenditures)
                    if 'Free Cash Flow' in cashflow_df.index:
                        fcf_values = cashflow_df.loc['Free Cash Flow'].dropna()
                        if len(fcf_values) >= 2:
                            fcf_current = fcf_values.iloc[0]
                            fcf_previous = fcf_values.iloc[1]
                            default_response["growth_profile"]["free_cash_flow_growth"]["fcf_current"] = float(fcf_current)
                            default_response["growth_profile"]["free_cash_flow_growth"]["fcf_previous"] = float(fcf_previous)
                            
                            if fcf_previous != 0:
                                fcf_growth = (fcf_current - fcf_previous) / abs(fcf_previous)
                                default_response["growth_profile"]["free_cash_flow_growth"]["yoy_current"] = fcf_growth
                    else:
                        # Calculate FCF manually
                        if 'Total Cash From Operating Activities' in cashflow_df.index and 'Capital Expenditures' in cashflow_df.index:
                            ocf = cashflow_df.loc['Total Cash From Operating Activities'].dropna()
                            capex = cashflow_df.loc['Capital Expenditures'].dropna()
                            if len(ocf) >= 2 and len(capex) >= 2:
                                fcf_current = ocf.iloc[0] + capex.iloc[0]  # CapEx is negative
                                fcf_previous = ocf.iloc[1] + capex.iloc[1]
                                default_response["growth_profile"]["free_cash_flow_growth"]["fcf_current"] = float(fcf_current)
                                default_response["growth_profile"]["free_cash_flow_growth"]["fcf_previous"] = float(fcf_previous)
                                
                                if fcf_previous != 0:
                                    fcf_growth = (fcf_current - fcf_previous) / abs(fcf_previous)
                                    default_response["growth_profile"]["free_cash_flow_growth"]["yoy_current"] = fcf_growth
            except Exception as e:
                print(f"Error calculating FCF growth: {e}")

            # 3-5 Year Growth Rate (CAGR)
            growth_next_5y = info.get("earningsQuarterlyGrowth")  # This is sometimes used for forward estimates
            if growth_df is not None and not growth_df.empty:
                try:
                    # Look for next 5 year growth estimate
                    five_year_mask = growth_df.index.str.contains('Next 5 Years|5Y', case=False, na=False)
                    if five_year_mask.any():
                        five_year_growth = growth_df[five_year_mask]['stockTrend'].iloc[0]
                        if five_year_growth is not None and not (isinstance(five_year_growth, float) and np.isnan(five_year_growth)):
                            default_response["growth_profile"]["analyst_estimates"]["growth_next_5_years"] = float(five_year_growth)
                            default_response["growth_profile"]["revenue_growth"]["cagr_3_5_year"] = float(five_year_growth)
                except Exception as e:
                    print(f"Error parsing 5-year growth: {e}")

            # PEG Ratio
            peg_ratio = info.get("pegRatio")
            if peg_ratio is not None:
                default_response["growth_profile"]["analyst_estimates"]["peg_ratio"] = peg_ratio

            # Flag if data exists
            if info.get("targetMeanPrice") or default_response["consensus_history"]:
                default_response["data_available"] = True

            return default_response

        except Exception as e:
            print(f"Error fetching analyst consensus for {self.ticker}: {e}")
            return default_response
        
if __name__ == "__main__":
    ticker = "AAPL"
    ac = AnalystConsensus(ticker)
    data = ac.get_yahoo_analyst_consensus()
    print(data)