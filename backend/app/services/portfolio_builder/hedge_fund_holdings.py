"""
Hedge Fund Holdings Fetcher
Simple class to get stocks and shares held by hedge funds.
Uses Finnhub API (free tier: 60 calls/minute)
"""

import requests
import os


class HedgeFundHoldings:
    """
    Get stocks and shares held by hedge funds.
    
    Setup:
    1. Get free API key from https://finnhub.io/
    2. Set environment variable: export FINNHUB_API_KEY='your_key'
    3. Use the class
    
    Usage:
        holdings = HedgeFundHoldings()
        result = holdings.get("Berkshire Hathaway")
        print(result)
    """
    
    # Common hedge funds with their CIK numbers
    FUNDS = {
        "berkshire hathaway": "0001067983",
        "warren buffett": "0001067983",
        "bridgewater": "0001350694",
        "bridgewater associates": "0001350694",
        "ray dalio": "0001350694",
        "renaissance technologies": "0001037389",
        "jim simons": "0001037389",
        "two sigma": "0001568285",
        "citadel": "0001423053",
        "ken griffin": "0001423053",
        "d.e. shaw": "0001393818",
        "de shaw": "0001393818",
        "millennium": "0001549917",
        "millennium management": "0001549917",
        "point72": "0001603466",
        "steve cohen": "0001603466",
        "elliott": "0001342919",
        "elliott management": "0001342919",
        "paul singer": "0001342919",
        "pershing square": "0001336528",
        "bill ackman": "0001336528",
        "viking global": "0001103804",
        "tiger global": "0001167483",
        "coatue": "0001567892",
        "coatue management": "0001567892",
        "appaloosa": "0001082552",
        "baupost": "0001061768",
        "baupost group": "0001061768",
        "seth klarman": "0001061768",
        "soros": "0001029160",
        "soros fund management": "0001029160",
        "george soros": "0001029160",
        "ark": "0001659180",
        "ark invest": "0001659180",
        "cathie wood": "0001659180",
    }
    
    def __init__(self, api_key=None):
        """
        Initialize with Finnhub API key.
        
        Args:
            api_key: Finnhub API key (or set FINNHUB_API_KEY env variable)
        """
        self.api_key = api_key or os.getenv('FINNHUB_API_KEY')
        print(f"Using FINNHUB_API_KEY: {self.api_key}")
        if not self.api_key:
            raise ValueError(
                "API key required. Get free key at https://finnhub.io/ then:\n"
                "1. Set env variable: export FINNHUB_API_KEY='your_key'\n"
                "2. Or pass directly: HedgeFundHoldings(api_key='your_key')"
            )
        self.base_url = "https://finnhub.io/api/v1"
    
    def get(self, fund_name):
        """
        Get all stocks and shares held by a hedge fund.
        
        Args:
            fund_name: Name of hedge fund or manager (e.g., "Berkshire Hathaway", "Warren Buffett")
        
        Returns:
            Dictionary with fund info and holdings:
            {
                'fund_name': 'Berkshire Hathaway Inc',
                'cik': '0001067983',
                'filing_date': '2024-12-31',
                'total_value': 350000000000.0,
                'stocks': {
                    'AAPL': {
                        'company_name': 'Apple Inc',
                        'shares': 915560382,
                        'value': 174520000000.0
                    },
                    'BAC': {...},
                    ...
                }
            }
        """
        # Get CIK from fund name
        cik = self._get_cik(fund_name)
        if not cik:
            return {
                'error': f"Fund '{fund_name}' not found. Available funds: {', '.join(set(self.FUNDS.values()))}"
            }
        
        # Fetch holdings from Finnhub
        url = f"{self.base_url}/stock/institutional-portfolio"
        params = {
            'cik': cik,
            'token': self.api_key
        }
        
        response = requests.get(url, params=params)
        
        if response.status_code != 200:
            return {'error': f"API error: {response.status_code}"}
        
        data = response.json()
        
        if not data or 'data' not in data:
            return {'error': 'No holdings data available for this fund'}
        
        # Format the response
        stocks = {}
        total_value = 0
        
        for holding in data.get('data', []):
            ticker = holding.get('symbol', '')
            if not ticker:
                continue
                
            shares = int(holding.get('share', 0))
            value = float(holding.get('value', 0))
            
            stocks[ticker] = {
                'company_name': holding.get('name', ''),
                'shares': shares,
                'value': value
            }
            total_value += value
        
        return {
            'fund_name': data.get('name', 'Unknown'),
            'cik': cik,
            'filing_date': data.get('reportDate', ''),
            'total_value': total_value,
            'stocks': stocks
        }
    
    def _get_cik(self, fund_name):
        """Get CIK number from fund name"""
        name_lower = fund_name.lower().strip()
        
        # Direct match
        if name_lower in self.FUNDS:
            return self.FUNDS[name_lower]
        
        # Partial match
        for key, cik in self.FUNDS.items():
            if name_lower in key or key in name_lower:
                return cik
        
        # If it looks like a CIK (numbers), use it directly
        if fund_name.strip().replace('0', '').isdigit():
            return fund_name.strip().zfill(10)
        
        return None


if __name__ == "__main__":
    # Example usage
    holdings = HedgeFundHoldings("d5s1li9r01qoo9r23p80d5s1li9r01qoo9r23p8g")
    
    # Get Berkshire Hathaway holdings
    result = holdings.get("Berkshire Hathaway")
    
    if 'error' in result:
        print(f"Error: {result['error']}")
    else:
        print(f"\n{result['fund_name']}")
        print(f"Filing Date: {result['filing_date']}")
        print(f"Total Portfolio Value: ${result['total_value']:,.0f}")
        print(f"\nStocks held: {len(result['stocks'])}")
        print("\nTop 10 holdings:")
        
        # Sort by value and show top 10
        sorted_stocks = sorted(
            result['stocks'].items(),
            key=lambda x: x[1]['value'],
            reverse=True
        )[:10]
        
        for ticker, info in sorted_stocks:
            print(f"{ticker}: {info['shares']:,} shares (${info['value']:,.0f})")