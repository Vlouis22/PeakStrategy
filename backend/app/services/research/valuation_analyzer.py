
import yfinance as yf
import numpy as np
import pandas as pd
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime, timedelta
from .baze_analyzer import BaseAnalyzer

class ValuationAnalyzer(BaseAnalyzer):
    """Comprehensive valuation analysis with robust error handling and fallbacks"""
    
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
            scorecard = self._calculate_valuation_score(relative_metrics, historical_pe, peer_comparison, hist_5y)
            
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
        """Get relative valuation metrics with enhanced validation"""
        trailing_pe = self._validate_pe(self.info.get("trailingPE"))
        forward_pe = self._validate_pe(self.info.get("forwardPE"))
        
        # Get earnings growth with multiple fallbacks
        earnings_growth = self._get_earnings_growth()
        
        # Calculate PEG ratio with strict validation
        peg_ratio = self._calculate_peg_ratio(trailing_pe, earnings_growth)
        
        # Get other valuation metrics with validation
        ev_ebitda = self._validate_metric(self.info.get("enterpriseToEbitda"), min_val=0, max_val=1000)
        price_to_sales = self._validate_metric(self.info.get("priceToSalesTrailing12Months"), min_val=0, max_val=1000)
        price_to_book = self._validate_metric(self.info.get("priceToBook"), min_val=0, max_val=1000)
        
        return {
            "trailingPE": trailing_pe,
            "forwardPE": forward_pe,
            "pegRatio": peg_ratio,
            "earningsGrowth": earnings_growth,
            "enterpriseToEbitda": ev_ebitda,
            "priceToSalesTrailing": price_to_sales,
            "priceToBook": price_to_book
        }
    
    def _validate_pe(self, pe: Optional[float]) -> Optional[float]:
        """Validate P/E ratio with reasonable bounds"""
        if pe is None or pe <= 0:
            return None
        if pe > 500:
            return None
        return pe
    
    def _validate_metric(self, value: Optional[float], min_val: float = 0, max_val: float = 1000) -> Optional[float]:
        """Validate a metric within bounds"""
        if value is None or value < min_val or value > max_val:
            return None
        return value
    
    def _get_earnings_growth(self) -> Optional[float]:
        """Get earnings growth with multiple fallback strategies"""
        # Primary source
        earnings_growth = self.info.get("earningsGrowth")
        if earnings_growth is not None and abs(earnings_growth) <= 2.0 and earnings_growth != 0:
            return earnings_growth
        
        # Fallback 1: Quarterly earnings growth
        earnings_growth_quarterly = self.info.get("earningsQuarterlyGrowth")
        if earnings_growth_quarterly is not None and abs(earnings_growth_quarterly) <= 2.0 and earnings_growth_quarterly != 0:
            return earnings_growth_quarterly
        
        # Fallback 2: Calculate from financial statements if available
        try:
            financials = self.stock.financials
            if financials is not None and not financials.empty and len(financials.columns) >= 2:
                for col in financials.index:
                    if 'Net Income' in str(col) or 'net income' in str(col).lower():
                        values = financials.loc[col].dropna()
                        if len(values) >= 2:
                            most_recent = values.iloc[0]
                            previous = values.iloc[1]
                            if previous != 0:
                                calc_growth = (most_recent - previous) / abs(previous)
                                if abs(calc_growth) <= 2.0 and calc_growth != 0:
                                    return calc_growth
                        break
        except:
            pass
        
        # Fallback 3: Revenue growth as proxy
        revenue_growth = self.info.get("revenueGrowth")
        if revenue_growth is not None and abs(revenue_growth) <= 2.0 and revenue_growth > 0:
            return revenue_growth * 0.8  # Conservative estimate
        
        return None
    
    def _calculate_peg_ratio(self, trailing_pe: Optional[float], earnings_growth: Optional[float]) -> Optional[float]:
        """Calculate PEG ratio with robust validation"""
        if not trailing_pe or not earnings_growth:
            return None
        
        if trailing_pe <= 0 or earnings_growth <= 0.001:
            return None
        
        try:
            growth_percentage = earnings_growth * 100
            peg_ratio = trailing_pe / growth_percentage
            
            if peg_ratio < 0 or peg_ratio > 100:
                return None
            
            return peg_ratio
        except:
            return None
    
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
                
                peer_pe = self._validate_pe(peer_info.get("trailingPE"))
                if peer_pe:
                    peer_data_points['pe'].append(peer_pe)
                    successful_peers.append(peer_ticker)
                
                peer_forward_pe = self._validate_pe(peer_info.get("forwardPE"))
                if peer_forward_pe:
                    peer_data_points['forward_pe'].append(peer_forward_pe)
                
                peer_growth = peer_info.get("earningsGrowth")
                if peer_growth and -0.5 < peer_growth < 2.0:
                    peer_data_points['growth'].append(peer_growth)
                
                if peer_pe and peer_growth and peer_growth > 0.01:
                    peer_peg = peer_pe / (peer_growth * 100)
                    if 0 < peer_peg < 100:
                        peer_data_points['peg'].append(peer_peg)
                
                peer_ev_ebitda = self._validate_metric(peer_info.get("enterpriseToEbitda"), 0, 1000)
                if peer_ev_ebitda:
                    peer_data_points['ev_ebitda'].append(peer_ev_ebitda)
                
                peer_ps = self._validate_metric(peer_info.get("priceToSalesTrailing12Months"), 0, 1000)
                if peer_ps:
                    peer_data_points['ps'].append(peer_ps)
                
                peer_pb = self._validate_metric(peer_info.get("priceToBook"), 0, 1000)
                if peer_pb:
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
        
        earnings_growth = self._get_earnings_growth()
        peg = self.info.get("pegRatio")
        peg_interpretation = self._interpret_peg(peg)
        
        return {
            "expectedEPSGrowth": earnings_growth,
            "expectedRevenueGrowth": revenue_growth,
            "pegInterpretation": peg_interpretation
        }
    
    def _interpret_peg(self, peg: Optional[float]) -> str:
        """Interpret PEG ratio"""
        if peg is None:
            return "Data Not Available"
        if peg < 0:
            return "Negative (Company has negative earnings or declining earnings)"
        elif peg < 0.5:
            return "Deeply Undervalued (relative to growth) - Verify data quality"
        elif peg < 1:
            return "Undervalued relative to growth"
        elif peg < 1.5:
            return "Fairly valued"
        elif peg < 2:
            return "Moderately expensive relative to growth"
        else:
            return "Premium valuation - High expectations priced in"
    
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
    
    def _calculate_valuation_score(self, metrics: Dict, historical_pe: Dict, peer_comparison: Dict, hist_5y: pd.DataFrame) -> Dict[str, Any]:
        """Calculate comprehensive valuation scorecard with robust fallbacks"""
        
        scores = {
            "earningsValuation": None,
            "growthAdjusted": None,
            "peerComparison": None,
            "historicalContext": None,
            "fundamentals": None
        }
        
        # 1. EARNINGS VALUATION (P/E based)
        trailing_pe = metrics.get("trailingPE")
        forward_pe = metrics.get("forwardPE")
        
        if trailing_pe and trailing_pe > 0:
            scores["earningsValuation"] = self._score_pe(trailing_pe)
            
            if forward_pe and forward_pe > 0:
                pe_improvement = ((trailing_pe - forward_pe) / trailing_pe) * 100
                if pe_improvement > 20:
                    scores["earningsValuation"] = min(10.0, scores["earningsValuation"] + 1.0)
                elif pe_improvement < -20:
                    scores["earningsValuation"] = max(1.0, scores["earningsValuation"] - 1.0)
        
        # 2. GROWTH-ADJUSTED VALUATION with fallbacks
        peg = metrics.get("pegRatio")
        
        if peg and peg > 0:
            scores["growthAdjusted"] = self._score_peg(peg)
        else:
            scores["growthAdjusted"] = self._calculate_growth_adjusted_fallback(metrics, peer_comparison, hist_5y)
        
        # 3. PEER COMPARISON
        this_stock = peer_comparison.get("thisStock", {})
        peer_avg = peer_comparison.get("peerGroupAvg", {})
        
        this_pe = this_stock.get("pe")
        peer_pe = peer_avg.get("pe")
        
        if this_pe and peer_pe and peer_pe > 0:
            pe_vs_peers = ((this_pe - peer_pe) / peer_pe) * 100
            scores["peerComparison"] = self._score_peer_comparison(pe_vs_peers)
        
        # 4. HISTORICAL CONTEXT
        current_pe = trailing_pe
        historical_avg_pe = historical_pe.get("fiveYearAvgPE")
        
        if current_pe and historical_avg_pe and historical_avg_pe > 0:
            pe_vs_history = ((current_pe - historical_avg_pe) / historical_avg_pe) * 100
            scores["historicalContext"] = self._score_historical_context(pe_vs_history)
        
        # 5. FUNDAMENTALS (P/B, P/S, EV/EBITDA)
        pb = metrics.get("priceToBook")
        ps = metrics.get("priceToSalesTrailing")
        ev_ebitda = metrics.get("enterpriseToEbitda")
        
        fundamental_scores = []
        
        if pb and pb > 0:
            fundamental_scores.append(self._score_pb(pb))
        if ps and ps > 0:
            fundamental_scores.append(self._score_ps(ps))
        if ev_ebitda and ev_ebitda > 0:
            fundamental_scores.append(self._score_ev_ebitda(ev_ebitda))
        
        if fundamental_scores:
            scores["fundamentals"] = sum(fundamental_scores) / len(fundamental_scores)
        
        # CALCULATE OVERALL SCORE
        valid_scores = [s for s in scores.values() if s is not None]
        
        if not valid_scores:
            overall_score = 5.0
            verdict = "Insufficient Data"
        else:
            overall_score = sum(valid_scores) / len(valid_scores)
            verdict = self._determine_verdict(overall_score)
        
        data_points = sum(1 for s in scores.values() if s is not None)
        confidence = self._determine_confidence(data_points)
        
        return {
            "componentScores": scores,
            "overallScore": round(overall_score, 2),
            "verdict": verdict,
            "confidence": confidence
        }
    
    def _score_pe(self, pe: float) -> float:
        """Score P/E ratio"""
        if pe < 10:
            return 9.0
        elif pe < 15:
            return 8.0
        elif pe < 20:
            return 7.0
        elif pe < 25:
            return 6.0
        elif pe < 30:
            return 5.0
        elif pe < 40:
            return 4.0
        elif pe < 60:
            return 3.0
        elif pe < 100:
            return 2.0
        else:
            return 1.0
    
    def _score_peg(self, peg: float) -> float:
        """Score PEG ratio"""
        if peg < 0.5:
            return 10.0
        elif peg < 0.75:
            return 9.0
        elif peg < 1.0:
            return 8.0
        elif peg < 1.25:
            return 7.0
        elif peg < 1.5:
            return 6.0
        elif peg < 2.0:
            return 5.0
        elif peg < 2.5:
            return 4.0
        elif peg < 3.0:
            return 3.0
        elif peg < 4.0:
            return 2.0
        else:
            return 1.0
    
    def _calculate_growth_adjusted_fallback(self, metrics: Dict, peer_comparison: Dict, hist_5y: pd.DataFrame) -> Optional[float]:
        """Fallback for growth-adjusted scoring when PEG unavailable"""
        trailing_pe = metrics.get("trailingPE")
        earnings_growth = metrics.get("earningsGrowth")
        peer_avg = peer_comparison.get("peerGroupAvg", {})
        peer_pe = peer_avg.get("pe")
        peer_growth = peer_avg.get("earningsGrowth")
        
        # Method 1: Estimate PEG from available growth
        if trailing_pe and earnings_growth and earnings_growth > 0.001:
            estimated_peg = trailing_pe / (earnings_growth * 100)
            if 0 < estimated_peg < 100:
                return self._score_peg(estimated_peg)
        
        # Method 2: Compare P/E to S&P 500 with growth adjustment
        sp500_pe = 21.8
        if trailing_pe:
            # Assume stock is fair if trading near market multiple
            if trailing_pe < sp500_pe * 0.7:
                return 8.0  # Good discount
            elif trailing_pe < sp500_pe:
                return 6.5  # Slight discount
            elif trailing_pe < sp500_pe * 1.3:
                return 5.5  # Near market
            elif trailing_pe < sp500_pe * 1.7:
                return 4.5  # Premium
            else:
                return 3.0  # High premium
        
        # Method 3: Price momentum as growth proxy
        if not hist_5y.empty and 'Close' in hist_5y.columns:
            prices = hist_5y['Close']
            if len(prices) > 252:
                momentum_1y = (prices.iloc[-1] - prices.iloc[-252]) / prices.iloc[-252]
                if momentum_1y > 0.30:
                    return 6.0  # Strong upward momentum
                elif momentum_1y > 0.10:
                    return 5.5
                elif momentum_1y > -0.10:
                    return 5.0
                else:
                    return 4.0
        
        # Method 4: Default neutral score (insufficient data)
        return 5.0
    
    def _score_peer_comparison(self, pe_vs_peers: float) -> float:
        """Score peer comparison"""
        if pe_vs_peers < -50:
            return 10.0
        elif pe_vs_peers < -30:
            return 9.0
        elif pe_vs_peers < -20:
            return 8.0
        elif pe_vs_peers < -10:
            return 7.0
        elif pe_vs_peers < 10:
            return 6.0
        elif pe_vs_peers < 20:
            return 5.0
        elif pe_vs_peers < 50:
            return 4.0
        elif pe_vs_peers < 100:
            return 3.0
        elif pe_vs_peers < 200:
            return 2.0
        else:
            return 1.0
    
    def _score_historical_context(self, pe_vs_history: float) -> float:
        """Score historical context"""
        if pe_vs_history < -40:
            return 10.0
        elif pe_vs_history < -30:
            return 9.0
        elif pe_vs_history < -20:
            return 8.0
        elif pe_vs_history < -10:
            return 7.0
        elif pe_vs_history < 10:
            return 6.0
        elif pe_vs_history < 30:
            return 5.0
        elif pe_vs_history < 50:
            return 4.0
        elif pe_vs_history < 100:
            return 3.0
        elif pe_vs_history < 200:
            return 2.0
        else:
            return 1.0
    
    def _score_pb(self, pb: float) -> float:
        """Score price-to-book ratio"""
        if pb < 1.0:
            return 9.0
        elif pb < 2.0:
            return 8.0
        elif pb < 3.0:
            return 7.0
        elif pb < 5.0:
            return 6.0
        elif pb < 10.0:
            return 5.0
        elif pb < 20.0:
            return 4.0
        elif pb < 40.0:
            return 3.0
        elif pb < 60.0:
            return 2.0
        else:
            return 1.0
    
    def _score_ps(self, ps: float) -> float:
        """Score price-to-sales ratio"""
        if ps < 1.0:
            return 9.0
        elif ps < 2.0:
            return 8.0
        elif ps < 4.0:
            return 7.0
        elif ps < 6.0:
            return 6.0
        elif ps < 10.0:
            return 5.0
        elif ps < 20.0:
            return 4.0
        elif ps < 40.0:
            return 3.0
        elif ps < 80.0:
            return 2.0
        else:
            return 1.0
    
    def _score_ev_ebitda(self, ev_ebitda: float) -> float:
        """Score EV/EBITDA ratio"""
        if ev_ebitda < 8:
            return 9.0
        elif ev_ebitda < 12:
            return 8.0
        elif ev_ebitda < 15:
            return 7.0
        elif ev_ebitda < 20:
            return 6.0
        elif ev_ebitda < 25:
            return 5.0
        elif ev_ebitda < 40:
            return 4.0
        elif ev_ebitda < 80:
            return 3.0
        elif ev_ebitda < 200:
            return 2.0
        else:
            return 1.0
    
    def _determine_verdict(self, score: float) -> str:
        """Determine verdict from score"""
        if score >= 8.5:
            return "Strongly Undervalued"
        elif score >= 7.5:
            return "Moderately Undervalued"
        elif score >= 6.5:
            return "Slightly Undervalued"
        elif score >= 5.5:
            return "Fairly Valued"
        elif score >= 4.5:
            return "Slightly Overvalued"
        elif score >= 3.5:
            return "Moderately Overvalued"
        elif score >= 2.5:
            return "Significantly Overvalued"
        else:
            return "Extremely Overvalued"
    
    def _determine_confidence(self, data_points: int) -> str:
        """Determine confidence from data availability"""
        if data_points >= 4:
            return "High"
        elif data_points >= 2:
            return "Medium"
        else:
            return "Low"