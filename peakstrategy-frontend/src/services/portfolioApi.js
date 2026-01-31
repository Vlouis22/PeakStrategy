// src/services/portfolioApi.js
import { auth } from '../firebase.js';

const BACKEND_URL = import.meta.env.VITE_REACT_APP_BACKEND_URL || '';

// Helper to get authorization headers
const getAuthHeaders = async () => {
  const currentUser = auth.currentUser;
  
  if (!currentUser) {
    throw new Error('No user is currently signed in');
  }

  // Get the Firebase ID token
  const token = await currentUser.getIdToken();
  
  return {
    'Content-Type': 'application/json',
    'Authorization': `Bearer ${token}`,
  };
};

export const portfolioApi = {
  // Create new portfolio
  createPortfolio: async (portfolioData) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/`, {
        method: 'POST',
        headers,
        body: JSON.stringify(portfolioData),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to create portfolio');
      }

      return await response.json();
    } catch (error) {
      console.error('Create portfolio error:', error);
      throw error;
    }
  },

  // Get all portfolios for current user
  getPortfolios: async () => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to fetch portfolios');
      }

      return await response.json();
    } catch (error) {
      console.error('Get portfolios error: ', error);
      throw error;
    }
  },

  // Get single portfolio with holdings
  getPortfolio: async (portfolioId) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to fetch portfolio');
      }

      return await response.json();
    } catch (error) {
      console.error('Get portfolio error:', error);
      throw error;
    }
  },

  // Update portfolio holdings
  updatePortfolioHoldings: async (portfolioId, portfolioData) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}/holdings`, {
        method: 'PUT',
        headers,
        body: JSON.stringify({ portfolioData }),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to update portfolio');
      }

      return await response.json();
    } catch (error) {
      console.error('Update portfolio error:', error);
      throw error;
    }
  },

  // Add single holding to portfolio
  addHolding: async (portfolioId, holding) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}/holdings`, {
        method: 'POST',
        headers,
        body: JSON.stringify(holding),
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to add holding');
      }

      return await response.json();
    } catch (error) {
      console.error('Add holding error:', error);
      throw error;
    }
  },

  // Delete portfolio
  deletePortfolio: async (portfolioId) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}`, {
        method: 'DELETE',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to delete portfolio');
      }

      return await response.json();
    } catch (error) {
      console.error('Delete portfolio error:', error);
      throw error;
    }
  },
  
  // Get performance for a single portfolio
  getPortfolioPerformance: async (portfolioId) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/${portfolioId}/performance`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to fetch portfolio performance');
      }

      return await response.json();
    } catch (error) {
      console.error('Get portfolio performance error:', error);
      throw error;
    }
  },
  
  // Get performance for all portfolios
  getPortfoliosPerformance: async () => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/performance`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to fetch portfolios performance');
      }

      return await response.json();
    } catch (error) {
      console.error('Get portfolios performance error:', error);
      throw error;
    }
  },

  getPortfolioProjection: async(portfolioSelection, years) => {
    const headers = await getAuthHeaders();
    const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/projection`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
        portfolio_selection: portfolioSelection,
        years: years
        })
    });

    if (!response.ok) {
        throw new Error('Failed to fetch portfolio projection');
    }

    return response.json();
    },

  getPriceChanges: async (symbols) => {
    const headers = await getAuthHeaders();
    console.log(symbols);
    const response = await fetch(`${BACKEND_URL}/api/v1/portfolios/daily_change`, {
      method: 'GET',
      headers,
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.error || error.message || 'Failed to fetch price changes');
    }

    return response.json();
  },
  
  getStockResearch: async (ticker) => {
    try {
      const headers = await getAuthHeaders();
      
      const response = await fetch(`${BACKEND_URL}/api/v1/research/stock/${ticker}`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || `Failed to fetch research for ${ticker}`);
      }

      return await response.json();
    } catch (error) {
      console.error(`Get stock research error for ${ticker}:`, error);
      throw error;
    }
  },
  
  // Note: Removed getStockPrice and getStockPrices since they're not in the backend portfolio.py
  // If you need stock price endpoints, you'll need to create separate routes for them
};

export const portfolioBuilderApi = {
  // Get all hedge funds
  getHedgeFunds: async () => {
    try {
      const headers = await getAuthHeaders();

      const response = await fetch(`${BACKEND_URL}/api/v1/portfolio-builder/hedge-funds`, {
        method: 'GET',
        headers,
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || error.message || 'Failed to fetch hedge funds');
      }

      return await response.json();
    } catch (error) {
      console.error('Get hedge funds error:', error);
      throw error;
    }
  },

  analyzePortfolios: async (companyNames) => {
    console.log("API companies:", companyNames);
    try {
      const headers = {
        'Content-Type': 'application/json',
        ...await getAuthHeaders()
      };

      const response = await fetch(`${BACKEND_URL}/api/v1/portfolio-builder/analyze`, {
        method: 'POST',
        headers,
        body: JSON.stringify({ companies: companyNames })
      });

      if (!response.ok) {
        const error = await response.json();
        throw new Error(error.error || 'Failed to analyze portfolios');
      }

      return await response.json();
    } catch (error) {
      console.error('Analyze portfolios error:', error);
      throw error;
    }
  }

  // You can add more portfolio-builder-specific endpoints here later
};

// Ticker validation helper
export const validateTicker = (symbol) => {
  const pattern = /^[A-Z]{1,5}$/;
  return pattern.test(symbol.toUpperCase());
};
