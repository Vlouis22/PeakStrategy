"""
Portfolio Projection Service
Handles Monte Carlo simulations and financial calculations for portfolio projections
"""
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional
import logging
from app.services.stock_price_service import stock_price_service
from app.services.redis_service import RedisService  # UPDATED
import yfinance as yf 
import json

logger = logging.getLogger(__name__)

class PortfolioProjectionService:
    """Service for portfolio projection calculations"""
    
    def __init__(self):
        """Initialize projection service with Redis cache"""
        self.redis_service = RedisService.get_instance()  # UPDATED
        self.trading_days_per_year = 252  # Average trading days in a year
    
    def _get_cache_key(self, symbol: str, data_type: str) -> str:
        """Generate Redis cache key for market data"""
        return f"market_data:{symbol}:{data_type}"
    
    def _get_historical_prices(self, symbols: List[str], days: int = 1260) -> Dict[str, List[float]]:
        """
        Get historical prices for symbols with Redis caching
        1260 days = ~5 years of trading data
        """
        cached_prices = {}
        symbols_to_fetch = []
        
        # Check Redis cache first
        for symbol in symbols:
            cache_key = self._get_cache_key(symbol, "prices")
            cached = self.redis_service.get(cache_key)  # UPDATED
            if cached:
                cached_prices[symbol] = cached
            else:
                symbols_to_fetch.append(symbol)
        
        # Fetch remaining symbols from external API
        if symbols_to_fetch:
            try:
                fetched_prices = self._fetch_historical_prices(symbols_to_fetch, days)
                
                # Cache the fetched prices for 1 hour
                for symbol, prices in fetched_prices.items():
                    cache_key = self._get_cache_key(symbol, "prices")
                    self.redis_service.set(  # UPDATED
                        cache_key,
                        prices,
                        ttl=3600  # 1 hour TTL
                    )
                    cached_prices[symbol] = prices
                    
            except Exception as e:
                logger.error(f"Error fetching historical prices: {e}")
                # Use fallback data or propagate error
        
        return cached_prices
    
    def _fetch_historical_prices(self, symbols: List[str], days: int) -> Dict[str, List[float]]:
        """
        Fetch historical prices from external API
        This is a placeholder - integrate with your actual historical data source
        """
        prices = {}
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        for symbol in symbols:
            try:
                # Fetch historical data using yfinance
                ticker = yf.Ticker(symbol)
                hist = ticker.history(start=start_date, end=end_date, interval="1d")
                
                if not hist.empty:
                    # Get closing prices as list
                    closing_prices = hist['Close'].tolist()
                    prices[symbol] = closing_prices
                else:
                    logger.warning(f"No historical data found for {symbol}")
                    prices[symbol] = []
                    
            except Exception as e:
                logger.error(f"Error fetching historical data for {symbol}: {e}")
                prices[symbol] = []
        
        return prices
    
    def calculate_statistics(self, historical_prices: Dict[str, List[float]]) -> Dict:
        """
        Calculate expected return (μ), volatility (σ), and covariance matrix
        """
        # Convert to DataFrame for easier calculations
        price_df = pd.DataFrame(historical_prices)
        
        # Calculate daily returns
        returns_df = price_df.pct_change().dropna()
        
        # Calculate statistics
        mu_daily = returns_df.mean()  # Daily expected returns
        sigma_daily = returns_df.std()  # Daily volatility
        cov_matrix_daily = returns_df.cov()  # Daily covariance matrix
        
        # Annualize (assuming 252 trading days)
        mu_annual = mu_daily * self.trading_days_per_year
        sigma_annual = sigma_daily * np.sqrt(self.trading_days_per_year)
        cov_matrix_annual = cov_matrix_daily * self.trading_days_per_year
        
        # Cache statistics for 4 hours
        for symbol in historical_prices.keys():
            stats_cache_key = self._get_cache_key(symbol, "statistics")
            stats_data = {
                'mu_annual': mu_annual.get(symbol, 0),
                'sigma_annual': sigma_annual.get(symbol, 0),
                'last_updated': datetime.now().isoformat()
            }
            self.redis_service.set(  # UPDATED
                stats_cache_key,
                stats_data,
                ttl=14400  # 4 hours
            )
        
        return {
            'mu_daily': mu_daily.to_dict(),
            'mu_annual': mu_annual.to_dict(),
            'sigma_daily': sigma_daily.to_dict(),
            'sigma_annual': sigma_annual.to_dict(),
            'cov_matrix_daily': cov_matrix_daily.to_dict(),
            'cov_matrix_annual': cov_matrix_annual.to_dict()
        }
    
    def get_portfolio_statistics(self, holdings: List[Dict], statistics: Dict) -> Tuple[float, float]:
        """
        Calculate portfolio-level expected return and volatility
        """
        if not holdings:
            return 0.0, 0.0
        
        # Get current prices
        symbols = [h['symbol'].upper() for h in holdings]
        current_prices = stock_price_service.get_prices(symbols)
        
        # Compute holding values
        holding_values = {}
        total_value = 0
        for h in holdings:
            symbol = h['symbol'].upper()
            shares = float(h['shares'])
            price = current_prices.get(symbol, 0)
            value = shares * price
            holding_values[symbol] = value
            total_value += value
        
        if total_value == 0:
            return 0.0, 0.0
        
        # Compute weights
        weights = {symbol: value / total_value for symbol, value in holding_values.items()}
        
        # Compute weighted expected return
        mu = sum(weights[symbol] * statistics['mu_annual'].get(symbol, 0) for symbol in symbols)
        
        # Compute portfolio variance
        cov_matrix = statistics['cov_matrix_annual']
        portfolio_variance = 0
        for i, sym_i in enumerate(symbols):
            for j, sym_j in enumerate(symbols):
                cov_ij = cov_matrix.get(sym_i, {}).get(sym_j, 0)
                portfolio_variance += weights[sym_i] * weights[sym_j] * cov_ij
        
        sigma = np.sqrt(portfolio_variance)
        return mu, sigma
    
    def calculate_deterministic_projection(
        self,
        initial_value: float,
        mu: float,
        sigma: float,
        years: int
    ) -> Dict:
        """Deterministic portfolio projection based on expected return and risk"""
        years_list = list(range(1, years + 1))
        projected = []
        lower = []
        upper = []
        
        for t in years_list:
            projected_value = initial_value * (1 + mu) ** t
            lower_value = initial_value * (1 + mu - sigma) ** t
            upper_value = initial_value * (1 + mu + sigma) ** t
            
            projected.append(projected_value)
            lower.append(lower_value)
            upper.append(upper_value)
        
        return {
            'years': years_list,
            'projected': projected,
            'lower_bound': lower,
            'upper_bound': upper,
            'initial_value': initial_value
        }
    
    def get_portfolio_projection(
        self,
        holdings: List[Dict],
        years: int = 10,
        simulations: int = 10000
    ) -> Dict:
        """
        Main method to get portfolio projection
        """
        try:
            # Generate a cache key for the entire projection
            projection_input = {
                'holdings': holdings,
                'years': years,
                'simulations': simulations
            }
            cache_hash = self.redis_service.generate_hash(projection_input)
            cache_key = f"portfolio:projection:{cache_hash}"
            
            # Check cache first
            cached_result = self.redis_service.get(cache_key)
            if cached_result:
                cached_result['meta'] = {'cached': True, 'timestamp': datetime.now().isoformat()}
                return cached_result
            
            # Get unique symbols
            symbols = list(set([h['symbol'].upper() for h in holdings]))
            
            if not symbols:
                return {
                    'success': False,
                    'error': 'No holdings found in portfolio'
                }
            
            # Get historical prices
            historical_prices = self._get_historical_prices(symbols)
            
            if not historical_prices:
                return {
                    'success': False,
                    'error': 'Could not fetch historical prices'
                }
            
            # Calculate statistics
            statistics = self.calculate_statistics(historical_prices)
            
            # Get current portfolio value
            current_prices = stock_price_service.get_prices(symbols)
            initial_value = sum(
                float(h['shares']) * current_prices.get(h['symbol'].upper(), 0)
                for h in holdings
            )
            
            # Calculate portfolio statistics
            mu, sigma = self.get_portfolio_statistics(holdings, statistics)
            
            # Calculate deterministic projection
            projection = self.calculate_deterministic_projection(
                initial_value=initial_value,
                mu=mu,
                sigma=sigma,
                years=years
            )
            
            result = {
                'success': True,
                'projection': projection,
                'statistics': {
                    'expected_return_annual': mu,
                    'volatility_annual': sigma,
                    'sharpe_ratio': mu / sigma if sigma > 0 else 0
                },
                'timestamp': datetime.now().isoformat(),
                'meta': {'cached': False, 'timestamp': datetime.now().isoformat()}
            }
            
            # Cache the result for 5 minutes
            self.redis_service.set(cache_key, result, ttl=300)
            
            return result
            
        except Exception as e:
            logger.error(f"Error in portfolio projection: {e}")
            return {
                'success': False,
                'error': str(e)
            }

# Singleton instance
portfolio_projection_service = PortfolioProjectionService()