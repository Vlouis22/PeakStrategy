import yfinance as yf
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import json

def get_stock_valuation(ticker_symbol):
    """
    Fetch comprehensive valuation data for a given stock ticker.
    Returns a dictionary with all valuation metrics and analysis.
    """
    try:
        ticker = yf.Ticker(ticker_symbol)
        info = ticker.info
        
        # Get historical data
        hist_5y = ticker.history(period="5y")
        hist_max = ticker.history(period="max")
        
        # Get financial statements
        financials = ticker.financials
        earnings = ticker.earnings_dates if hasattr(ticker, 'earnings_dates') else None
        
        # 1. Valuation Overview
        overview = {
            "currentPrice": info.get("currentPrice", info.get("regularMarketPrice", 0)),
            "marketCap": info.get("marketCap", 0),
            "currency": info.get("currency", "USD")
        }
        
        # 2. Relative Valuation Metrics - Calculate PEG manually
        trailing_pe = info.get("trailingPE")
        forward_pe = info.get("forwardPE")
        
        # Get earnings growth rate (expressed as percentage, e.g., 0.15 = 15%)
        earnings_growth = info.get("earningsGrowth") or info.get("earningsQuarterlyGrowth")
        
        # Calculate PEG Ratio manually: PEG = (P/E Ratio) / (Expected Annual Earnings Growth Rate in %)
        peg_ratio = None
        if trailing_pe and earnings_growth and earnings_growth > 0:
            # Convert growth rate to percentage (e.g., 0.15 -> 15)
            growth_percentage = earnings_growth * 100
            peg_ratio = trailing_pe / growth_percentage
        
        relative_metrics = {
            "trailingPE": trailing_pe,
            "forwardPE": forward_pe,
            "pegRatio": peg_ratio,
            "earningsGrowth": earnings_growth,  # Store for use in peer comparison
            "enterpriseToEbitda": info.get("enterpriseToEbitda"),
            "priceToSalesTrailing": info.get("priceToSalesTrailing12Months"),
            "priceToBook": info.get("priceToBook")
        }
        
        # 3. Absolute Valuation Context
        current_price = overview["currentPrice"]
        fifty_two_week_high = info.get("fiftyTwoWeekHigh", 0)
        fifty_two_week_low = info.get("fiftyTwoWeekLow", 0)
        
        # Calculate all-time high
        all_time_high = hist_max['High'].max() if not hist_max.empty else fifty_two_week_high
        
        absolute_context = {
            "currentPrice": current_price,
            "fiftyTwoWeekHigh": fifty_two_week_high,
            "fiftyTwoWeekLow": fifty_two_week_low,
            "percentFromHigh": ((current_price - fifty_two_week_high) / fifty_two_week_high * 100) if fifty_two_week_high else 0,
            "percentFromLow": ((current_price - fifty_two_week_low) / fifty_two_week_low * 100) if fifty_two_week_low else 0,
            "allTimeHigh": all_time_high,
            "percentFromAllTimeHigh": ((current_price - all_time_high) / all_time_high * 100) if all_time_high else 0
        }
        
        # Market Cap vs Business Size
        total_revenue = info.get("totalRevenue", 0)
        business_size = {
            "marketCap": info.get("marketCap", 0),
            "trailingRevenue": total_revenue,
            "marketCapToRevenue": (info.get("marketCap", 0) / total_revenue) if total_revenue else 0
        }
        
        # 4. Historical Valuation Trend
        historical_pe = calculate_historical_pe(hist_5y, ticker_symbol)
        
        # 5. Peer Comparisons - Calculate PEG for peers and averages
        peer_comparison = get_peer_comparisons(ticker_symbol, info, relative_metrics)
        
        # 6. Growth-Adjusted Valuation
        revenue_growth = info.get("revenueGrowth") or info.get("revenueQuarterlyGrowth")
        
        growth_metrics = {
            "expectedEPSGrowth": earnings_growth,
            "expectedRevenueGrowth": revenue_growth,
            "pegInterpretation": interpret_peg(peg_ratio)
        }
        
        # 7. Valuation Interpretation
        interpretation = generate_valuation_insights(
            relative_metrics,
            info,
            historical_pe
        )
        
        # 8. Valuation Scorecard
        scorecard = calculate_valuation_score(
            relative_metrics,
            historical_pe,
            peer_comparison,
            info
        )
        
        # Compile final result
        valuation_data = {
            "ticker": ticker_symbol,
            "companyName": info.get("longName", ticker_symbol),
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


def calculate_peg_ratio(pe_ratio, earnings_growth):
    """
    Calculate PEG Ratio manually
    Formula: PEG = (P/E Ratio) / (Expected Annual Earnings Growth Rate in %)
    
    Args:
        pe_ratio: P/E ratio value
        earnings_growth: Growth rate as decimal (e.g., 0.15 for 15%)
    
    Returns:
        PEG ratio or None if calculation not possible
    """
    if pe_ratio and earnings_growth and earnings_growth > 0:
        growth_percentage = earnings_growth * 100
        return pe_ratio / growth_percentage
    return None


def get_peer_comparisons(ticker_symbol, info, relative_metrics):
    """Get peer comparison data including calculated PEG ratios"""
    
    # Get sector and industry
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    
    # Define peer groups by sector
    peer_map = {
        "Technology": ["AAPL", "MSFT", "GOOGL", "META", "NVDA"],
        "Financial Services": ["JPM", "BAC", "WFC", "GS", "MS"],
        "Healthcare": ["UNH", "JNJ", "PFE", "ABBV", "MRK"],
        "Consumer Cyclical": ["AMZN", "TSLA", "HD", "NKE", "SBUX"],
        "Communication Services": ["GOOGL", "META", "DIS", "NFLX", "T"],
        "Consumer Defensive": ["WMT", "PG", "KO", "PEP", "COST"],
        "Industrials": ["BA", "CAT", "GE", "HON", "UPS"],
        "Energy": ["XOM", "CVX", "COP", "SLB", "EOG"],
        "Basic Materials": ["LIN", "APD", "SHW", "ECL", "NEM"],
        "Real Estate": ["AMT", "PLD", "CCI", "EQIX", "PSA"],
        "Utilities": ["NEE", "DUK", "SO", "D", "AEP"]
    }
    
    # Get peers for this stock's sector
    peers = peer_map.get(sector, [])
    
    # Remove the current ticker from peers if present
    peers = [p for p in peers if p != ticker_symbol]
    
    # Track which peers were successfully fetched
    successful_peers = []
    
    # Calculate peer group averages
    peer_pe_values = []
    peer_forward_pe_values = []
    peer_peg_values = []
    peer_growth_values = []
    
    for peer_ticker in peers[:5]:  # Limit to 5 peers to avoid rate limiting
        try:
            peer = yf.Ticker(peer_ticker)
            peer_info = peer.info
            
            peer_pe = peer_info.get("trailingPE")
            peer_forward_pe = peer_info.get("forwardPE")
            peer_growth = peer_info.get("earningsGrowth") or peer_info.get("earningsQuarterlyGrowth")
            
            # Only count peer if we got at least some data
            if peer_pe or peer_forward_pe:
                successful_peers.append(peer_ticker)
            
            if peer_pe:
                peer_pe_values.append(peer_pe)
            if peer_forward_pe:
                peer_forward_pe_values.append(peer_forward_pe)
            if peer_growth:
                peer_growth_values.append(peer_growth)
            
            # Calculate PEG for peer using manual formula
            peer_peg = calculate_peg_ratio(peer_pe, peer_growth)
            if peer_peg:
                peer_peg_values.append(peer_peg)
                
        except:
            continue
    
    # Calculate peer group averages
    peer_avg_pe = np.mean(peer_pe_values) if peer_pe_values else None
    peer_avg_forward_pe = np.mean(peer_forward_pe_values) if peer_forward_pe_values else None
    peer_avg_growth = np.mean(peer_growth_values) if peer_growth_values else None
    
    # Calculate peer PEG from averages
    peer_avg_peg = None
    if peer_peg_values:
        peer_avg_peg = np.mean(peer_peg_values)
    elif peer_avg_pe and peer_avg_growth:
        # Fallback: calculate from average P/E and average growth
        peer_avg_peg = calculate_peg_ratio(peer_avg_pe, peer_avg_growth)
    
    # S&P 500 averages (approximate current values)
    sp500_avg_pe = 21.5
    sp500_avg_forward_pe = 19.5
    sp500_avg_growth = 0.10  # Approximate 10% earnings growth
    
    # Calculate S&P 500 PEG using the formula
    sp500_avg_peg = calculate_peg_ratio(sp500_avg_pe, sp500_avg_growth)
    
    return {
        "thisStock": {
            "pe": relative_metrics["trailingPE"],
            "forwardPE": relative_metrics["forwardPE"],
            "peg": relative_metrics["pegRatio"],
            "earningsGrowth": relative_metrics["earningsGrowth"],
            "evToEbitda": relative_metrics["enterpriseToEbitda"]
        },
        "peerGroupAvg": {
            "pe": peer_avg_pe,
            "forwardPE": peer_avg_forward_pe,
            "peg": peer_avg_peg,
            "earningsGrowth": peer_avg_growth,
            "peerCount": len(successful_peers),
            "peers": successful_peers
        },
        "sp500Avg": {
            "pe": sp500_avg_pe,
            "forwardPE": sp500_avg_forward_pe,
            "peg": sp500_avg_peg,
            "earningsGrowth": sp500_avg_growth
        }
    }


def calculate_historical_pe(hist_data, ticker_symbol):
    """Calculate historical P/E ratios"""
    if hist_data.empty:
        return {"available": False}
    
    ticker = yf.Ticker(ticker_symbol)
    info = ticker.info
    current_pe = info.get("trailingPE")
    
    # Calculate 5-year average if we have price history
    prices = hist_data['Close']
    
    return {
        "available": True,
        "currentPE": current_pe,
        "fiveYearAvgPE": None,  # Would need historical EPS data
        "priceHistory": {
            "dates": [d.strftime("%Y-%m-%d") for d in prices.index[-60:]],  # Last 60 days
            "prices": prices.tail(60).tolist()
        }
    }


def interpret_peg(peg_ratio):
    """Interpret PEG ratio"""
    if peg_ratio is None:
        return "Data Not Available"
    if peg_ratio < 0:
        return "Negative (Company losing money)"
    if peg_ratio < 1:
        return "Undervalued relative to growth"
    elif peg_ratio <= 2:
        return "Fairly valued"
    else:
        return "Premium valuation"


def generate_valuation_insights(metrics, info, historical_pe):
    """Generate human-readable valuation insights"""
    insights = []
    
    # P/E Analysis
    trailing_pe = metrics.get("trailingPE")
    forward_pe = metrics.get("forwardPE")
    
    if trailing_pe and forward_pe:
        if forward_pe < trailing_pe:
            insights.append({
                "type": "positive",
                "message": f"Forward P/E ({forward_pe:.1f}) is lower than trailing P/E ({trailing_pe:.1f}) → earnings expected to grow"
            })
        elif forward_pe > trailing_pe:
            insights.append({
                "type": "negative",
                "message": f"Forward P/E ({forward_pe:.1f}) is higher than trailing P/E ({trailing_pe:.1f}) → earnings expected to decline"
            })
    
    # PEG Analysis
    peg = metrics.get("pegRatio")
    if peg and peg > 0:
        if peg < 1:
            insights.append({
                "type": "positive",
                "message": f"PEG ratio of {peg:.2f} suggests stock may be undervalued relative to growth"
            })
        elif peg > 2:
            insights.append({
                "type": "negative",
                "message": f"PEG ratio of {peg:.2f} indicates aggressive growth pricing"
            })
        else:
            insights.append({
                "type": "neutral",
                "message": f"PEG ratio of {peg:.2f} indicates fairly valued relative to growth"
            })
    
    # Price to Book with ROE
    pb = metrics.get("priceToBook")
    roe = info.get("returnOnEquity")
    if pb and roe:
        if pb < 2 and roe and roe > 0.15:
            insights.append({
                "type": "positive",
                "message": f"Low P/B ({pb:.2f}) with strong ROE ({roe*100:.1f}%) → possible undervaluation"
            })
    
    # Price to Sales
    ps = metrics.get("priceToSalesTrailing")
    profit_margin = info.get("profitMargins")
    if ps and profit_margin:
        if ps > 5 and profit_margin and profit_margin > 0.15:
            insights.append({
                "type": "neutral",
                "message": f"High P/S ({ps:.2f}) but strong margins ({profit_margin*100:.1f}%) → growth valuation"
            })
    
    return insights


def calculate_valuation_score(metrics, historical_pe, peer_comparison, info):
    """Calculate comprehensive valuation scorecard based on real market data"""
    
    def score_pe(trailing_pe, forward_pe, sector, industry):
        """Score P/E metrics with sector-adjusted benchmarks"""
        if not trailing_pe:
            return 5
        
        # Real sector-specific P/E benchmarks (average from S&P 500 sectors)
        sector_pe_benchmarks = {
            "Technology": 28.5,
            "Financial Services": 14.2,
            "Healthcare": 22.8,
            "Consumer Cyclical": 24.1,
            "Communication Services": 18.7,
            "Consumer Defensive": 21.3,
            "Industrials": 19.4,
            "Energy": 11.6,
            "Basic Materials": 15.9,
            "Real Estate": 18.2,
            "Utilities": 17.8
        }
        
        # Get sector benchmark, default to market average (21.5)
        sector_benchmark = sector_pe_benchmarks.get(sector, 21.5)
        
        # Calculate P/E relative to sector
        pe_ratio = trailing_pe / sector_benchmark
        
        # Forward P/E premium/discount
        forward_premium = 0
        if forward_pe and trailing_pe:
            forward_premium = (forward_pe / trailing_pe - 1) * 100  # Percentage difference
        
        # Score based on deviation from sector average
        if pe_ratio < 0.7:
            if forward_premium < -5:  # Forward P/E significantly lower
                return 9.5
            elif forward_premium < 0:
                return 9.0
            else:
                return 8.5
        elif pe_ratio < 0.9:
            if forward_premium < -5:
                return 8.0
            elif forward_premium < 0:
                return 7.5
            else:
                return 7.0
        elif pe_ratio < 1.1:
            if forward_premium < -5:
                return 7.0
            elif forward_premium < 0:
                return 6.5
            elif forward_premium > 5:
                return 5.0
            else:
                return 6.0
        elif pe_ratio < 1.3:
            if forward_premium > 5:
                return 4.0
            elif forward_premium > 0:
                return 4.5
            else:
                return 5.0
        else:  # pe_ratio >= 1.3
            if forward_premium > 5:
                return 2.0
            elif forward_premium > 0:
                return 2.5
            else:
                return 3.0
    
    def score_peg(peg_ratio, growth_rate, industry):
        """Score PEG ratio with growth-adjusted benchmarks"""
        if not peg_ratio or peg_ratio < 0:
            return 5
        
        # Industry-specific PEG benchmarks (based on historical data)
        industry_peg_benchmarks = {
            "Software": 2.0,
            "Semiconductors": 1.8,
            "Pharmaceuticals": 1.6,
            "Banks": 1.2,
            "Consumer Electronics": 1.5,
            "Retail": 1.4,
            "Biotechnology": 2.2,
            "Automotive": 1.3,
            "Aerospace": 1.4,
            "Oil & Gas": 1.1
        }
        
        # Get industry benchmark, default to 1.5
        industry_benchmark = 1.5
        for key, value in industry_peg_benchmarks.items():
            if key in industry:
                industry_benchmark = value
                break
        
        # Adjust benchmark based on growth rate (higher growth = higher acceptable PEG)
        if growth_rate:
            growth_adjustment = min(max(growth_rate * 100 / 15, 0.7), 1.3)  # Scale between 0.7-1.3
            adjusted_benchmark = industry_benchmark * growth_adjustment
        else:
            adjusted_benchmark = industry_benchmark
        
        peg_relative = peg_ratio / adjusted_benchmark
        
        # Score based on relative PEG
        if peg_relative < 0.7:
            return 9.5
        elif peg_relative < 0.9:
            return 8.5
        elif peg_relative < 1.1:
            return 7.0
        elif peg_relative < 1.3:
            return 6.0
        elif peg_relative < 1.5:
            return 5.0
        elif peg_relative < 2.0:
            return 4.0
        else:
            return 2.5
    
    def score_peer_comparison(this_metrics, peer_avg, market_avg, sector):
        """Score based on multiple peer comparison metrics"""
        if not peer_avg.get('pe') or not this_metrics.get('trailingPE'):
            return 5
        
        scores = []
        
        # 1. P/E relative to peers
        pe_ratio = this_metrics.get('trailingPE', 0) / peer_avg.get('pe', 1)
        if pe_ratio < 0.7:
            scores.append(9.0)
        elif pe_ratio < 0.9:
            scores.append(8.0)
        elif pe_ratio < 1.1:
            scores.append(6.5)
        elif pe_ratio < 1.3:
            scores.append(5.0)
        else:
            scores.append(3.0)
        
        # 2. PEG relative to peers
        if this_metrics.get('pegRatio') and peer_avg.get('peg'):
            peg_ratio = this_metrics['pegRatio'] / peer_avg['peg']
            if peg_ratio < 0.7:
                scores.append(9.0)
            elif peg_ratio < 0.9:
                scores.append(8.0)
            elif peg_ratio < 1.1:
                scores.append(6.5)
            elif peg_ratio < 1.3:
                scores.append(5.0)
            else:
                scores.append(3.0)
        
        # 3. EV/EBITDA relative to peers
        if this_metrics.get('enterpriseToEbitda') and peer_avg.get('evToEbitda'):
            ev_ratio = this_metrics['enterpriseToEbitda'] / peer_avg.get('evToEbitda', 1)
            if ev_ratio < 0.7:
                scores.append(8.5)
            elif ev_ratio < 0.9:
                scores.append(7.5)
            elif ev_ratio < 1.1:
                scores.append(6.0)
            elif ev_ratio < 1.3:
                scores.append(5.0)
            else:
                scores.append(3.5)
        
        # 4. Growth rate relative to peers
        if this_metrics.get('earningsGrowth') and peer_avg.get('earningsGrowth'):
            growth_ratio = this_metrics['earningsGrowth'] / peer_avg['earningsGrowth']
            if growth_ratio > 1.5:
                scores.append(9.5)  # Higher growth than peers
            elif growth_ratio > 1.2:
                scores.append(8.5)
            elif growth_ratio > 0.8:
                scores.append(6.0)
            else:
                scores.append(4.0)
        
        # Return average of available scores
        return round(sum(scores) / len(scores), 1) if scores else 5.0
    
    def score_historical_context(current_pe, historical_pe, info):
        """Score based on historical valuation context"""
        if not current_pe or not historical_pe.get('available', False):
            return 5
        
        # Get historical P/E data if available
        historical_avg = historical_pe.get('fiveYearAvgPE')
        
        # Use 52-week high/low context
        current_price = info.get("currentPrice", 0)
        week_52_high = info.get("fiftyTwoWeekHigh", current_price * 1.2)
        week_52_low = info.get("fiftyTwoWeekLow", current_price * 0.8)
        
        # Calculate price position in 52-week range (0-100%)
        if week_52_high != week_52_low:
            price_position = (current_price - week_52_low) / (week_52_high - week_52_low) * 100
        else:
            price_position = 50
        
        scores = []
        
        # 1. Score based on 52-week position
        if price_position < 30:
            scores.append(8.5)  # Near 52-week low
        elif price_position < 40:
            scores.append(7.5)
        elif price_position < 60:
            scores.append(6.0)
        elif price_position < 70:
            scores.append(5.0)
        elif price_position < 80:
            scores.append(4.0)
        else:
            scores.append(3.0)  # Near 52-week high
        
        # 2. Score based on historical P/E (if available)
        if historical_avg and current_pe:
            pe_relative = current_pe / historical_avg
            if pe_relative < 0.7:
                scores.append(9.0)
            elif pe_relative < 0.9:
                scores.append(8.0)
            elif pe_relative < 1.1:
                scores.append(6.5)
            elif pe_relative < 1.3:
                scores.append(5.0)
            else:
                scores.append(3.5)
        
        # 3. Score based on momentum
        rsi = info.get("rsi", 50)
        if rsi < 30:
            scores.append(8.0)  # Oversold
        elif rsi < 40:
            scores.append(7.0)
        elif rsi < 60:
            scores.append(6.0)
        elif rsi < 70:
            scores.append(5.0)
        else:
            scores.append(4.0)  # Overbought
        
        return round(sum(scores) / len(scores), 1)
    
    def score_fundamentals(info):
        """Score based on fundamental financial health"""
        scores = []
        
        # 1. Profitability
        profit_margins = info.get("profitMargins", 0)
        if profit_margins > 0.20:  # 20%+
            scores.append(9.0)
        elif profit_margins > 0.15:
            scores.append(8.0)
        elif profit_margins > 0.10:
            scores.append(7.0)
        elif profit_margins > 0.05:
            scores.append(6.0)
        elif profit_margins > 0:
            scores.append(5.0)
        else:
            scores.append(3.0)
        
        # 2. Return on Equity
        roe = info.get("returnOnEquity", 0)
        if roe > 0.20:  # 20%+
            scores.append(9.0)
        elif roe > 0.15:
            scores.append(8.0)
        elif roe > 0.10:
            scores.append(7.0)
        elif roe > 0.05:
            scores.append(6.0)
        else:
            scores.append(4.0)
        
        # 3. Debt to Equity
        debt_to_equity = info.get("debtToEquity", 0)
        if debt_to_equity < 0.5:
            scores.append(8.5)
        elif debt_to_equity < 1.0:
            scores.append(7.5)
        elif debt_to_equity < 1.5:
            scores.append(6.0)
        elif debt_to_equity < 2.0:
            scores.append(5.0)
        else:
            scores.append(3.5)
        
        # 4. Current Ratio (liquidity)
        current_ratio = info.get("currentRatio", 1)
        if current_ratio > 2.0:
            scores.append(8.0)
        elif current_ratio > 1.5:
            scores.append(7.0)
        elif current_ratio > 1.0:
            scores.append(6.0)
        else:
            scores.append(4.0)
        
        return round(sum(scores) / len(scores), 1)
    
    # Calculate individual component scores
    sector = info.get("sector", "")
    industry = info.get("industry", "")
    
    earnings_score = score_pe(
        metrics.get("trailingPE"), 
        metrics.get("forwardPE"),
        sector,
        industry
    )
    
    growth_score = score_peg(
        metrics.get("pegRatio"),
        metrics.get("earningsGrowth"),
        industry
    )
    
    peer_score = score_peer_comparison(
        metrics,
        peer_comparison.get("peerGroupAvg", {}),
        peer_comparison.get("sp500Avg", {}),
        sector
    )
    
    historical_score = score_historical_context(
        metrics.get("trailingPE"),
        historical_pe,
        info
    )
    
    fundamentals_score = score_fundamentals(info)
    
    # Weighted overall score (adjust weights as needed)
    weights = {
        'earnings': 0.25,      # P/E analysis
        'growth': 0.20,        # PEG analysis
        'peer': 0.20,          # Peer comparison
        'historical': 0.15,     # Historical context
        'fundamentals': 0.20    # Financial health
    }
    
    overall_score = (
        earnings_score * weights['earnings'] +
        growth_score * weights['growth'] +
        peer_score * weights['peer'] +
        historical_score * weights['historical'] +
        fundamentals_score * weights['fundamentals']
    )
    
    # Determine verdict with confidence levels
    if overall_score >= 8.0:
        verdict = "Strongly Undervalued"
        confidence = "High"
    elif overall_score >= 7.0:
        verdict = "Moderately Undervalued"
        confidence = "Medium-High"
    elif overall_score >= 6.0:
        verdict = "Slightly Undervalued"
        confidence = "Medium"
    elif overall_score >= 5.5:
        verdict = "Fairly Valued"
        confidence = "Medium"
    elif overall_score >= 5.0:
        verdict = "Slightly Overvalued"
        confidence = "Medium"
    elif overall_score >= 4.0:
        verdict = "Moderately Overvalued"
        confidence = "Medium-High"
    else:
        verdict = "Strongly Overvalued"
        confidence = "High"
    
    return {
        "componentScores": {
            "earningsValuation": round(earnings_score, 1),
            "growthAdjusted": round(growth_score, 1),
            "peerComparison": round(peer_score, 1),
            "historicalContext": round(historical_score, 1),
            "fundamentals": round(fundamentals_score, 1)
        },
        "overallScore": round(overall_score, 2),
        "verdict": verdict,
        "confidence": confidence,
        "weighting": weights
    }
    
    earnings_score = score_pe(metrics.get("trailingPE"), metrics.get("forwardPE"))
    growth_score = score_peg(metrics.get("pegRatio"))
    
    peer_pe = peer_comparison.get("peerGroupAvg", {}).get("pe")
    peer_score = score_peer_comparison(metrics.get("trailingPE"), peer_pe)
    
    historical_score = 7  # Default since we have limited historical data
    
    overall_score = np.mean([earnings_score, growth_score, peer_score, historical_score])
    
    # Determine verdict
    if overall_score >= 7:
        verdict = "Undervalued"
    elif overall_score >= 5:
        verdict = "Fairly Valued"
    else:
        verdict = "Overvalued"
    
    return {
        "earningsValuation": earnings_score,
        "growthAdjusted": growth_score,
        "peerComparison": peer_score,
        "historicalContext": historical_score,
        "overallScore": round(overall_score, 1),
        "verdict": verdict
    }


# Example usage
if __name__ == "__main__":
    result = get_stock_valuation("AAPL")
    print(json.dumps(result, indent=2))