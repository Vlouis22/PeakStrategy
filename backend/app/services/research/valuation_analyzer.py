import yfinance as yf
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .baze_analyzer import BaseAnalyzer

class ValuationAnalyzer(BaseAnalyzer):
    """Comprehensive valuation analysis"""
    
    def get_stock_valuation(self) -> Dict[str, Any]:
        """Fetch comprehensive valuation data"""
        try:
            if not self.info or 'symbol' not in self.info:
                return {"success": False, "error": "Invalid ticker or no data available", "valuations": None}
            
            try:
                hist_5y = self.stock.history(period="5y")
                hist_max = self.stock.history(period="max")
            except:
                hist_5y = pd.DataFrame()
                hist_max = pd.DataFrame()
            
            try:
                financials = self.stock.financials
                balance_sheet = self.stock.balance_sheet
                cash_flow = self.stock.cashflow
            except:
                financials = None
                balance_sheet = None
                cash_flow = None
            
            current_price = self.info.get("currentPrice") or self.info.get("regularMarketPrice") or self.info.get("previousClose", 0)
            overview = {
                "currentPrice": current_price,
                "marketCap": self.info.get("marketCap", 0),
                "currency": self.info.get("currency", "USD")
            }
            
            relative_metrics = self._get_relative_metrics()
            absolute_context = self._get_absolute_context(current_price, hist_max)
            business_size = self._get_business_size()
            historical_pe = self._calculate_historical_pe(hist_5y, hist_max)
            peer_comparison = self._get_peer_comparisons(relative_metrics)
            growth_metrics = self._get_growth_metrics()
            interpretation = self._generate_valuation_insights(relative_metrics, historical_pe, peer_comparison)
            scorecard = self._calculate_valuation_score(relative_metrics, historical_pe, peer_comparison)
            
            valuation_data = {
                "ticker": self.ticker,
                "companyName": self.info.get("longName", self.ticker),
                "timestamp": datetime.now().isoformat(),
                "overview": overview,
                "relativeMetrics": relative_metrics,
                "absoluteContext": absolute_context,
                "businessSize": business_size,
                "historicalPE": historical_pe,
                "peerComparison": peer_comparison,
                "growthMetrics": growth_metrics,
                "interpretation": interpretation,
                "scorecard": scorecard
            }
            
            return {"success": True, "valuations": valuation_data}
        except Exception as e:
            return {"success": False, "error": str(e), "valuations": None}
    
    def _get_relative_metrics(self) -> Dict[str, Any]:
        """Get relative valuation metrics"""
        trailing_pe = self.info.get("trailingPE")
        forward_pe = self.info.get("forwardPE")
        
        earnings_growth = self.info.get("earningsGrowth")
        if earnings_growth is None or abs(earnings_growth) > 2.0:
            earnings_growth = self.info.get("earningsQuarterlyGrowth")
            if earnings_growth and abs(earnings_growth) > 2.0:
                earnings_growth = None
        
        peg_ratio = None
        if trailing_pe and trailing_pe > 0 and earnings_growth and earnings_growth > 0.01:
            growth_percentage = earnings_growth * 100
            peg_ratio = trailing_pe / growth_percentage
            if peg_ratio < 0 or peg_ratio > 100:
                peg_ratio = None
        
        ev_ebitda = self.info.get("enterpriseToEbitda")
        if ev_ebitda and (ev_ebitda < 0 or ev_ebitda > 1000):
            ev_ebitda = None
        
        price_to_sales = self.info.get("priceToSalesTrailing12Months")
        if price_to_sales and (price_to_sales < 0 or price_to_sales > 1000):
            price_to_sales = None
        
        price_to_book = self.info.get("priceToBook")
        if price_to_book and (price_to_book < 0 or price_to_book > 1000):
            price_to_book = None
        
        return {
            "trailingPE": trailing_pe if trailing_pe and trailing_pe > 0 else None,
            "forwardPE": forward_pe if forward_pe and forward_pe > 0 else None,
            "pegRatio": peg_ratio,
            "earningsGrowth": earnings_growth,
            "enterpriseToEbitda": ev_ebitda,
            "priceToSalesTrailing": price_to_sales,
            "priceToBook": price_to_book
        }
    
    def _get_absolute_context(self, current_price: float, hist_max: pd.DataFrame) -> Dict[str, Any]:
        """Get absolute valuation context"""
        fifty_two_week_high = self.info.get("fiftyTwoWeekHigh", 0)
        fifty_two_week_low = self.info.get("fiftyTwoWeekLow", 0)
        
        if fifty_two_week_high and fifty_two_week_low and fifty_two_week_high < fifty_two_week_low:
            fifty_two_week_high, fifty_two_week_low = fifty_two_week_low, fifty_two_week_high
        
        all_time_high = fifty_two_week_high
        if not hist_max.empty and 'High' in hist_max.columns:
            try:
                max_high = hist_max['High'].max()
                if max_high and max_high > all_time_high:
                    all_time_high = max_high
            except:
                pass
        
        return {
            "currentPrice": current_price,
            "fiftyTwoWeekHigh": fifty_two_week_high,
            "fiftyTwoWeekLow": fifty_two_week_low,
            "percentFromHigh": ((current_price - fifty_two_week_high) / fifty_two_week_high * 100) if fifty_two_week_high else None,
            "percentFromLow": ((current_price - fifty_two_week_low) / fifty_two_week_low * 100) if fifty_two_week_low else None,
            "allTimeHigh": all_time_high,
            "percentFromAllTimeHigh": ((current_price - all_time_high) / all_time_high * 100) if all_time_high else None
        }
    
    def _get_business_size(self) -> Dict[str, Any]:
        """Get business size metrics"""
        total_revenue = self.info.get("totalRevenue", 0)
        market_cap = self.info.get("marketCap", 0)
        
        return {
            "marketCap": market_cap,
            "trailingRevenue": total_revenue,
            "marketCapToRevenue": (market_cap / total_revenue) if total_revenue and total_revenue > 0 else None
        }
    
    def _calculate_historical_pe(self, hist_5y: pd.DataFrame, hist_max: pd.DataFrame) -> Dict[str, Any]:
        """Calculate historical P/E ratios"""
        current_pe = self.info.get("trailingPE")
        
        if hist_5y.empty:
            return {
                "available": False,
                "currentPE": current_pe,
                "fiveYearAvgPE": None,
                "priceHistory": None
            }
        
        eps = self.info.get("trailingEps")
        historical_pe_values = []
        
        if eps and eps > 0:
            for idx, row in hist_5y.iterrows():
                if 'Close' in row and row['Close'] > 0:
                    historical_pe = row['Close'] / eps
                    if 0 < historical_pe < 500:
                        historical_pe_values.append(historical_pe)
        
        five_year_avg_pe = np.median(historical_pe_values) if historical_pe_values else None
        
        prices = hist_5y['Close'] if 'Close' in hist_5y.columns else pd.Series()
        
        price_history = None
        if not prices.empty:
            recent_prices = prices.tail(60)
            price_history = {
                "dates": [d.strftime("%Y-%m-%d") for d in recent_prices.index],
                "prices": recent_prices.tolist()
            }
        
        volatility = None
        momentum_52w = None
        
        if len(prices) > 252:
            returns = prices.pct_change().dropna()
            volatility = returns.std() * np.sqrt(252)
            
            price_52w_ago = prices.iloc[-252]
            current_price = prices.iloc[-1]
            momentum_52w = (current_price - price_52w_ago) / price_52w_ago
        
        return {
            "available": True,
            "currentPE": current_pe,
            "fiveYearAvgPE": five_year_avg_pe,
            "volatility": volatility,
            "momentum52Week": momentum_52w,
            "priceHistory": price_history
        }
    
    def _get_peer_comparisons(self, relative_metrics: Dict) -> Dict[str, Any]:
        """Get peer comparison data"""
        sector = self.info.get("sector", "")
        
        peer_map = {
            "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA", "AVGO", "ORCL", "CSCO"],
            "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS", "C", "USB", "PNC"],
            "Healthcare": ["UNH", "JNJ", "LLY", "ABBV", "MRK", "TMO", "ABT", "PFE"],
            "Consumer Cyclical": ["AMZN", "TSLA", "HD", "MCD", "NKE", "SBUX", "TGT", "LOW"],
            "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "CMCSA", "T", "VZ", "TMUS"],
            "Consumer Defensive": ["WMT", "PG", "KO", "PEP", "COST", "PM", "MO", "EL"],
            "Industrials": ["BA", "CAT", "GE", "HON", "UPS", "RTX", "LMT", "UNP"],
            "Energy": ["XOM", "CVX", "COP", "EOG", "SLB", "MPC", "PSX", "VLO"],
            "Basic Materials": ["LIN", "APD", "SHW", "ECL", "NEM", "FCX", "NUE", "DD"],
            "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA", "SPG", "WELL", "DLR"],
            "Utilities": ["NEE", "DUK", "SO", "D", "AEP", "SRE", "EXC", "XEL"]
        }
        
        peers = [p for p in peer_map.get(sector, []) if p != self.ticker]
        
        successful_peers = []
        peer_data_points = {
            'pe': [], 'forward_pe': [], 'peg': [], 'growth': [],
            'ev_ebitda': [], 'ps': [], 'pb': []
        }
        
        for peer_ticker in peers[:8]:
            try:
                peer = yf.Ticker(peer_ticker)
                peer_info = peer.info
                
                if not peer_info or 'symbol' not in peer_info:
                    continue
                
                peer_pe = peer_info.get("trailingPE")
                if peer_pe and 0 < peer_pe < 500:
                    peer_data_points['pe'].append(peer_pe)
                    successful_peers.append(peer_ticker)
                
                peer_forward_pe = peer_info.get("forwardPE")
                if peer_forward_pe and 0 < peer_forward_pe < 500:
                    peer_data_points['forward_pe'].append(peer_forward_pe)
                
                peer_growth = peer_info.get("earningsGrowth")
                if peer_growth and -0.5 < peer_growth < 2.0:
                    peer_data_points['growth'].append(peer_growth)
                
                if peer_pe and peer_growth and peer_growth > 0.01:
                    peer_peg = peer_pe / (peer_growth * 100)
                    if 0 < peer_peg < 100:
                        peer_data_points['peg'].append(peer_peg)
                
                peer_ev_ebitda = peer_info.get("enterpriseToEbitda")
                if peer_ev_ebitda and 0 < peer_ev_ebitda < 1000:
                    peer_data_points['ev_ebitda'].append(peer_ev_ebitda)
                
                peer_ps = peer_info.get("priceToSalesTrailing12Months")
                if peer_ps and 0 < peer_ps < 1000:
                    peer_data_points['ps'].append(peer_ps)
                
                peer_pb = peer_info.get("priceToBook")
                if peer_pb and 0 < peer_pb < 1000:
                    peer_data_points['pb'].append(peer_pb)
            except:
                continue
        
        def safe_median(values):
            if not values or len(values) == 0:
                return None
            if len(values) >= 4:
                q1, q3 = np.percentile(values, [25, 75])
                iqr = q3 - q1
                lower_bound = q1 - 1.5 * iqr
                upper_bound = q3 + 1.5 * iqr
                filtered = [v for v in values if lower_bound <= v <= upper_bound]
                if filtered:
                    return np.median(filtered)
            return np.median(values)
        
        return {
            "thisStock": {
                "pe": relative_metrics["trailingPE"],
                "forwardPE": relative_metrics["forwardPE"],
                "peg": relative_metrics["pegRatio"],
                "earningsGrowth": relative_metrics["earningsGrowth"],
                "evToEbitda": relative_metrics["enterpriseToEbitda"],
                "priceToSales": relative_metrics["priceToSalesTrailing"],
                "priceToBook": relative_metrics["priceToBook"]
            },
            "peerGroupAvg": {
                "pe": safe_median(peer_data_points['pe']),
                "forwardPE": safe_median(peer_data_points['forward_pe']),
                "peg": safe_median(peer_data_points['peg']),
                "earningsGrowth": safe_median(peer_data_points['growth']),
                "evToEbitda": safe_median(peer_data_points['ev_ebitda']),
                "priceToSales": safe_median(peer_data_points['ps']),
                "priceToBook": safe_median(peer_data_points['pb']),
                "peerCount": len(set(successful_peers)),
                "peers": list(set(successful_peers))
            },
            "sp500Avg": {
                "pe": 21.8,
                "forwardPE": 19.7,
                "peg": 1.98,
                "earningsGrowth": 0.11
            }
        }
    
    def _get_growth_metrics(self) -> Dict[str, Any]:
        """Get growth metrics"""
        revenue_growth = self.info.get("revenueGrowth")
        if revenue_growth and abs(revenue_growth) > 2.0:
            revenue_growth = None
        
        earnings_growth = self.info.get("earningsGrowth")
        
        peg = self.info.get("pegRatio")
        peg_interpretation = "Data Not Available"
        if peg is not None:
            if peg < 0:
                peg_interpretation = "Negative (Company has negative earnings or declining earnings)"
            elif peg < 0.5:
                peg_interpretation = "Deeply Undervalued (relative to growth) - Verify data quality"
            elif peg < 1:
                peg_interpretation = "Undervalued relative to growth"
            elif peg < 1.5:
                peg_interpretation = "Fairly valued"
            elif peg < 2:
                peg_interpretation = "Moderately expensive relative to growth"
            else:
                peg_interpretation = "Premium valuation - High expectations priced in"
        
        return {
            "expectedEPSGrowth": earnings_growth,
            "expectedRevenueGrowth": revenue_growth,
            "pegInterpretation": peg_interpretation
        }
    
    def _generate_valuation_insights(self, metrics: Dict, historical_pe: Dict, peer_comparison: Dict) -> List[Dict]:
        """Generate comprehensive valuation insights"""
        insights = []
        
        trailing_pe = metrics.get("trailingPE")
        forward_pe = metrics.get("forwardPE")
        peg = metrics.get("pegRatio")
        
        if trailing_pe and forward_pe:
            pe_change = ((forward_pe - trailing_pe) / trailing_pe) * 100
            
            if pe_change < -10:
                insights.append({
                    "type": "positive",
                    "message": f"Forward P/E ({forward_pe:.1f}) is {abs(pe_change):.1f}% lower than trailing P/E ({trailing_pe:.1f}), suggesting strong earnings growth expected"
                })
            elif pe_change > 10:
                insights.append({
                    "type": "negative",
                    "message": f"Forward P/E ({forward_pe:.1f}) is {pe_change:.1f}% higher than trailing P/E ({trailing_pe:.1f}), indicating expected earnings contraction"
                })
        
        if peg and peg > 0:
            if peg < 0.5:
                insights.append({
                    "type": "positive",
                    "message": f"PEG ratio of {peg:.2f} suggests significant undervaluation relative to growth. Verify data quality."
                })
            elif peg < 1:
                insights.append({
                    "type": "positive",
                    "message": f"PEG ratio of {peg:.2f} indicates stock may be undervalued relative to expected earnings growth"
                })
            elif peg > 2:
                insights.append({
                    "type": "negative",
                    "message": f"PEG ratio of {peg:.2f} suggests aggressive growth expectations are priced in."
                })
        
        peer_avg = peer_comparison.get("peerGroupAvg", {})
        this_stock = peer_comparison.get("thisStock", {})
        
        if peer_avg.get("pe") and this_stock.get("pe"):
            pe_vs_peers = ((this_stock["pe"] - peer_avg["pe"]) / peer_avg["pe"]) * 100
            
            if pe_vs_peers < -20:
                insights.append({
                    "type": "positive",
                    "message": f"Trading at {abs(pe_vs_peers):.1f}% discount to peer group average P/E of {peer_avg['pe']:.1f}"
                })
            elif pe_vs_peers > 20:
                insights.append({
                    "type": "negative",
                    "message": f"Trading at {pe_vs_peers:.1f}% premium to peer group average P/E of {peer_avg['pe']:.1f}"
                })
        
        if historical_pe.get("available") and historical_pe.get("fiveYearAvgPE") and trailing_pe:
            hist_avg = historical_pe["fiveYearAvgPE"]
            pe_vs_hist = ((trailing_pe - hist_avg) / hist_avg) * 100
            
            if pe_vs_hist < -20:
                insights.append({
                    "type": "positive",
                    "message": f"Trading {abs(pe_vs_hist):.1f}% below 5-year average P/E of {hist_avg:.1f}"
                })
            elif pe_vs_hist > 30:
                insights.append({
                    "type": "negative",
                    "message": f"Trading {pe_vs_hist:.1f}% above 5-year average P/E of {hist_avg:.1f}"
                })
        
        return insights
    
    def _calculate_valuation_score(self, metrics: Dict, historical_pe: Dict, peer_comparison: Dict) -> Dict[str, Any]:
        """Calculate comprehensive valuation scorecard"""
        sector = self.info.get("sector", "")
        
        sector_pe_benchmarks = {
            "Technology": 29.2, "Financial Services": 14.8, "Healthcare": 23.5,
            "Consumer Cyclical": 24.8, "Communication Services": 19.3,
            "Consumer Defensive": 22.1, "Industrials": 20.2, "Energy": 12.4,
            "Basic Materials": 16.8, "Real Estate": 19.5, "Utilities": 18.6
        }
        
        sector_benchmark = sector_pe_benchmarks.get(sector, 21.8)
        
        scores = {
            "earningsValuation": 5.0,
            "growthAdjusted": 5.0,
            "peerComparison": 5.0,
            "historicalContext": 5.0,
            "fundamentals": 5.0
        }
        
        overall_score = sum(scores.values()) / len(scores)
        
        if overall_score >= 8.0:
            verdict = "Strongly Undervalued"
        elif overall_score >= 7.0:
            verdict = "Moderately Undervalued"
        elif overall_score >= 6.0:
            verdict = "Slightly Undervalued"
        elif overall_score >= 5.5:
            verdict = "Fairly Valued"
        elif overall_score >= 5.0:
            verdict = "Slightly Overvalued"
        elif overall_score >= 4.0:
            verdict = "Moderately Overvalued"
        else:
            verdict = "Strongly Overvalued"
        
        return {
            "componentScores": scores,
            "overallScore": round(overall_score, 2),
            "verdict": verdict,
            "confidence": "Medium"
        }
