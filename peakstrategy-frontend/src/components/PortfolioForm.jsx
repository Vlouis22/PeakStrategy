// src/components/PortfolioForm.jsx
import React, { useState } from 'react';
import { useAuth } from '../contexts/AuthContext';
import { portfolioApi } from '../services/portfolioApi';

const PortfolioForm = ({ portfolio = null, isEditing = false, onSuccess, onCancel }) => {
  const { currentUser } = useAuth();
  const [portfolioName, setPortfolioName] = useState(portfolio?.name || 'My Portfolio');
  const [holdings, setHoldings] = useState(portfolio?.holdings || []);
  const [isLoading, setIsLoading] = useState(false);
  const [errors, setErrors] = useState({});

  const [newHolding, setNewHolding] = useState({
    symbol: '',
    name: '',
    shares: '',
    averageCost: ''
  });

  const COMMON_STOCKS = [
    'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'NVDA', 'JPM', 'V', 'JNJ',
    'WMT', 'PG', 'UNH', 'HD', 'BAC', 'MA', 'DIS', 'ADBE', 'NFLX', 'CRM'
  ];

  const validateTicker = (symbol) => {
    const pattern = /^[A-Z]{1,5}$/;
    return pattern.test(symbol.toUpperCase());
  };

  const validateHolding = (holding) => {
    const errors = {};

    if (!holding.symbol.trim()) {
      errors.symbol = 'Ticker symbol is required';
    } else if (!validateTicker(holding.symbol)) {
      errors.symbol = 'Invalid ticker symbol (1-5 uppercase letters)';
    }

    if (!holding.shares) {
      errors.shares = 'Shares is required';
    } else if (parseFloat(holding.shares) <= 0) {
      errors.shares = 'Shares must be greater than 0';
    }

    if (!holding.averageCost) {
      errors.averageCost = 'Average cost is required';
    } else if (parseFloat(holding.averageCost) <= 0) {
      errors.averageCost = 'Average cost must be greater than 0';
    }

    return errors;
  };

  const addHolding = () => {
    const holdingErrors = validateHolding(newHolding);
    
    if (Object.keys(holdingErrors).length > 0) {
      setErrors(holdingErrors);
      return;
    }

    const holdingToAdd = {
      symbol: newHolding.symbol.toUpperCase(),
      name: newHolding.name || newHolding.symbol.toUpperCase(),
      shares: parseFloat(newHolding.shares),
      averageCost: parseFloat(newHolding.averageCost)
    };

    setHoldings([...holdings, holdingToAdd]);
    
    setNewHolding({
      symbol: '',
      name: '',
      shares: '',
      averageCost: ''
    });
    setErrors({});
  };

  const removeHolding = (index) => {
    const updatedHoldings = [...holdings];
    updatedHoldings.splice(index, 1);
    setHoldings(updatedHoldings);
  };

  const calculateTotalCostBasis = () => {
    return holdings.reduce((total, holding) => {
      return total + (holding.shares * holding.averageCost);
    }, 0).toFixed(2);
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    
    if (!currentUser) {
      alert('Please sign in to create a portfolio');
      return;
    }

    if (holdings.length === 0) {
      alert('Please add at least one holding to the portfolio');
      return;
    }

    setIsLoading(true);
    setErrors({});

    try {
      const portfolioData = {
        name: portfolioName,
        holdings: holdings.map(h => ({
          symbol: h.symbol,
          name: h.name,
          shares: h.shares,
          averageCost: h.averageCost
        }))
      };

      let response;
      
      if (isEditing && portfolio) {
        response = await portfolioApi.updatePortfolioHoldings(portfolio.id, portfolioData);
      } else {
        response = await portfolioApi.createPortfolio(portfolioData);
      }
      
      if (!isEditing) {
        setPortfolioName('My Portfolio');
        setHoldings([]);
      }
      
      if (onSuccess) {
        onSuccess(response);
      }
      
    } catch (error) {
      console.error('Error submitting portfolio:', error);
      alert(`Failed to save portfolio: ${error.message}`);
    } finally {
      setIsLoading(false);
    }
  };

  const clearForm = () => {
    setNewHolding({
      symbol: '',
      name: '',
      shares: '',
      averageCost: ''
    });
    setErrors({});
  };

  if (!currentUser) {
    return (
      <div className="min-h-screen flex items-center justify-center p-4">
        <div className="w-full max-w-md text-center">
          <div className="mb-6">
            <div className="w-16 h-16 mx-auto bg-black rounded-full flex items-center justify-center mb-4">
              <svg className="w-8 h-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
            </div>
            <h1 className="text-2xl font-bold text-black mb-2">Authentication Required</h1>
            <p className="text-gray-600">Please sign in to create or edit portfolios.</p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-white p-4 sm:p-6">
      {/* Main Container */}
      <div className="w-full mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-4">
            <div>
              <h1 className="text-3xl sm:text-4xl font-bold text-black tracking-tight">
                {isEditing ? 'Edit Portfolio' : 'Create New Portfolio'}
              </h1>
              <p className="text-gray-600 text-sm mt-1">
                Signed in as: {currentUser.email || currentUser.uid}
              </p>
            </div>
            <button
              onClick={onCancel}
              className="px-5 py-2.5 border-2 border-black text-black font-medium rounded-lg hover:bg-black hover:text-white transition-all duration-200 self-start sm:self-center whitespace-nowrap"
            >
              Cancel & Return
            </button>
          </div>
          <div className="h-px bg-gray-200"></div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Left Column - Portfolio Info & Holdings List */}
          <div className="lg:col-span-2 space-y-8">
            {/* Portfolio Name Card */}
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-black">Portfolio Details</h2>
                  <p className="text-gray-600 text-sm">Give your portfolio a name</p>
                </div>
              </div>
              
              <div>
                <label className="block text-sm font-medium text-gray-900 mb-2">
                  Portfolio Name
                </label>
                <input
                  type="text"
                  value={portfolioName}
                  onChange={(e) => setPortfolioName(e.target.value)}
                  className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                  placeholder="e.g., Tech Growth Portfolio"
                />
              </div>
            </div>

            {/* Holdings List Card */}
            <div className="bg-white border border-gray-200 rounded-xl shadow-sm overflow-hidden">
              <div className="px-6 py-5 border-b border-gray-200">
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3">
                    <div className="w-9 h-9 bg-black rounded-lg flex items-center justify-center">
                      <svg className="w-4 h-4 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
                      </svg>
                    </div>
                    <div>
                      <h2 className="text-xl font-semibold text-black">Portfolio Holdings</h2>
                      <p className="text-gray-600 text-sm">{holdings.length} holding{holdings.length !== 1 ? 's' : ''} • Total: ${calculateTotalCostBasis()}</p>
                    </div>
                  </div>
                  {holdings.length > 0 && (
                    <div className="text-sm text-gray-600">
                      {holdings.reduce((acc, h) => acc + h.shares, 0).toFixed(2)} total shares
                    </div>
                  )}
                </div>
              </div>

              {holdings.length > 0 ? (
                <div className="overflow-x-auto">
                  <table className="w-full">
                    <thead>
                      <tr className="border-b border-gray-200">
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider">Symbol</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider">Name</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider">Shares</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider">Avg Cost</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider">Cost Basis</th>
                        <th className="text-left py-4 px-6 text-sm font-semibold text-gray-900 uppercase tracking-wider"></th>
                      </tr>
                    </thead>
                    <tbody>
                      {holdings.map((holding, index) => (
                        <tr key={index} className="border-b border-gray-100 hover:bg-gray-50 transition-colors">
                          <td className="py-4 px-6">
                            <div className="flex items-center gap-2">
                              <div className="w-8 h-8 bg-black rounded flex items-center justify-center">
                                <span className="text-white text-xs font-bold">{holding.symbol.charAt(0)}</span>
                              </div>
                              <span className="font-bold text-black">{holding.symbol}</span>
                            </div>
                          </td>
                          <td className="py-4 px-6 text-gray-700 max-w-[200px] truncate">
                            {holding.name}
                          </td>
                            <td className="py-4 px-6">
                            {isEditing ? (
                                <input
                                type="number"
                                step="0.000001"
                                min="0.000001"
                                value={holding.shares}
                                onChange={(e) => {
                                    const updatedHoldings = [...holdings];
                                    updatedHoldings[index].shares = parseFloat(e.target.value) || 0;
                                    setHoldings(updatedHoldings);
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                                />
                            ) : (
                                <span className="font-medium text-black">{holding.shares.toFixed(6)}</span>
                            )}
                            </td>
                            <td className="py-4 px-6">
                            {isEditing ? (
                                <input
                                type="number"
                                step="0.01"
                                min="0.01"
                                value={holding.averageCost}
                                onChange={(e) => {
                                    const updatedHoldings = [...holdings];
                                    updatedHoldings[index].averageCost = parseFloat(e.target.value) || 0;
                                    setHoldings(updatedHoldings);
                                }}
                                className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
                                />
                            ) : (
                                <span className="text-gray-700">${holding.averageCost.toFixed(2)}</span>
                            )}
                            </td>
                          <td className="py-4 px-6">
                            <span className="font-semibold text-black">${(holding.shares * holding.averageCost).toFixed(2)}</span>
                          </td>
                          <td className="py-4 px-6">
                            <button
                              type="button"
                              onClick={() => removeHolding(index)}
                              className="text-sm font-medium text-gray-500 hover:text-black transition-colors"
                            >
                              Remove
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <div className="py-16 text-center">
                  <div className="w-20 h-20 mx-auto mb-4 bg-gray-100 rounded-full flex items-center justify-center">
                    <svg className="w-10 h-10 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
                    </svg>
                  </div>
                  <h3 className="text-lg font-medium text-gray-900 mb-2">No holdings added yet</h3>
                  <p className="text-gray-600 max-w-sm mx-auto">Add your first holding using the form to the right</p>
                </div>
              )}

              {holdings.length > 0 && (
                <div className="px-6 py-4 bg-gray-50 border-t border-gray-200">
                  <div className="flex justify-between items-center">
                    <div className="text-sm text-gray-600">
                      {holdings.length} holding{holdings.length !== 1 ? 's' : ''}
                    </div>
                    <div className="text-right">
                      <div className="text-sm text-gray-600 mb-1">Total Cost Basis</div>
                      <div className="text-2xl font-bold text-black">${calculateTotalCostBasis()}</div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>

          {/* Right Column - Add Holding Form */}
          <div className="lg:col-span-1">
            <div className="bg-white border border-gray-200 rounded-xl p-6 shadow-sm sticky top-6">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 bg-black rounded-lg flex items-center justify-center">
                  <svg className="w-5 h-5 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                  </svg>
                </div>
                <div>
                  <h2 className="text-xl font-semibold text-black">Add Holding</h2>
                  <p className="text-gray-600 text-sm">Enter stock details</p>
                </div>
              </div>

              <form onSubmit={(e) => { e.preventDefault(); addHolding(); }} className="space-y-6">
                {/* Ticker Symbol */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Ticker Symbol *
                  </label>
                  <div className="space-y-2">
                    <div className="relative">
                      <input
                        type="text"
                        value={newHolding.symbol}
                        onChange={(e) => {
                          setNewHolding({...newHolding, symbol: e.target.value.toUpperCase()});
                          if (errors.symbol) setErrors({...errors, symbol: ''});
                        }}
                        className={`w-full px-4 py-3 text-base border rounded-lg focus:outline-none focus:ring-2 focus:ring-black transition-all ${
                          errors.symbol ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="e.g., AAPL"
                      />
                      {errors.symbol && (
                        <p className="mt-1 text-sm text-red-600">{errors.symbol}</p>
                      )}
                    </div>
                    
                    <div>
                      <label className="block text-xs text-gray-600 mb-2">Quick Select</label>
                      <div className="flex flex-wrap gap-2">
                        {COMMON_STOCKS.slice(0, 8).map(symbol => (
                          <button
                            key={symbol}
                            type="button"
                            onClick={() => setNewHolding({...newHolding, symbol})}
                            className="px-3 py-1.5 text-sm border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors"
                          >
                            {symbol}
                          </button>
                        ))}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Stock Name */}
                <div>
                  <label className="block text-sm font-medium text-gray-900 mb-2">
                    Stock Name (Optional)
                  </label>
                  <input
                    type="text"
                    value={newHolding.name}
                    onChange={(e) => setNewHolding({...newHolding, name: e.target.value})}
                    className="w-full px-4 py-3 text-base border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent transition-all"
                    placeholder="e.g., Apple Inc."
                  />
                </div>

                {/* Shares & Average Cost - Side by side on desktop, stacked on mobile */}
                <div className="grid grid-cols-1 sm:grid-cols-2 gap-6">
                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Number of Shares *
                    </label>
                    <div className="relative">
                      <input
                        type="number"
                        step="0.000001"
                        min="0.000001"
                        value={newHolding.shares}
                        onChange={(e) => {
                          setNewHolding({...newHolding, shares: e.target.value});
                          if (errors.shares) setErrors({...errors, shares: ''});
                        }}
                        className={`w-full px-4 py-3 text-base border rounded-lg focus:outline-none focus:ring-2 focus:ring-black transition-all ${
                          errors.shares ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="0.000000"
                      />
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <span className="text-gray-500 text-sm">shares</span>
                      </div>
                    </div>
                    {errors.shares && (
                      <p className="mt-1 text-sm text-red-600">{errors.shares}</p>
                    )}
                  </div>

                  <div>
                    <label className="block text-sm font-medium text-gray-900 mb-2">
                      Average Cost *
                    </label>
                    <div className="relative">
                      <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <span className="text-gray-700">$</span>
                      </div>
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        value={newHolding.averageCost}
                        onChange={(e) => {
                          setNewHolding({...newHolding, averageCost: e.target.value});
                          if (errors.averageCost) setErrors({...errors, averageCost: ''});
                        }}
                        className={`w-full pl-8 pr-4 py-3 text-base border rounded-lg focus:outline-none focus:ring-2 focus:ring-black transition-all ${
                          errors.averageCost ? 'border-red-500' : 'border-gray-300'
                        }`}
                        placeholder="0.00"
                      />
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center pointer-events-none">
                        <span className="text-gray-500 text-sm">per share</span>
                      </div>
                    </div>
                    {errors.averageCost && (
                      <p className="mt-1 text-sm text-red-600">{errors.averageCost}</p>
                    )}
                  </div>
                </div>

                {/* Add Button */}
                <div className="pt-4">
                  <button
                    type="submit"
                    className="w-full py-3.5 bg-black text-white font-medium rounded-lg hover:bg-gray-800 transition-all duration-200 flex items-center justify-center gap-2"
                  >
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
                    </svg>
                    Add to Portfolio
                  </button>
                </div>

                {/* Clear Form */}
                {newHolding.symbol || newHolding.name || newHolding.shares || newHolding.averageCost ? (
                  <div className="text-center">
                    <button
                      type="button"
                      onClick={clearForm}
                      className="text-sm text-gray-500 hover:text-black transition-colors"
                    >
                      Clear form
                    </button>
                  </div>
                ) : null}
              </form>

              {/* Stats Summary */}
              {holdings.length > 0 && (
                <div className="mt-8 pt-6 border-t border-gray-200">
                  <h3 className="text-sm font-medium text-gray-900 mb-4">Portfolio Summary</h3>
                  <div className="space-y-3">
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Holdings</span>
                      <span className="text-sm font-medium text-black">{holdings.length}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Shares</span>
                      <span className="text-sm font-medium text-black">
                        {holdings.reduce((acc, h) => acc + h.shares, 0).toFixed(2)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-sm text-gray-600">Total Cost Basis</span>
                      <span className="text-sm font-bold text-black">${calculateTotalCostBasis()}</span>
                    </div>
                  </div>
                </div>
              )}
            </div>
          </div>
        </div>

        {/* Save Portfolio Footer */}
        <div className="mt-8 pt-6 border-t border-gray-200">
          <div className="flex flex-col sm:flex-row items-center justify-between gap-4">
            <div>
              <div className="text-sm text-gray-600">
                {holdings.length} holding{holdings.length !== 1 ? 's' : ''} • ${calculateTotalCostBasis()} total
              </div>
              <div className="text-xs text-gray-500 mt-1">
                {isEditing ? 'Update your portfolio holdings' : 'Ready to create your new portfolio'}
              </div>
            </div>
            
            <div className="flex items-center gap-4 self-stretch sm:self-center">
              <button
                type="button"
                onClick={onCancel}
                className="px-6 py-3 border-2 border-black text-black font-medium rounded-lg hover:bg-gray-50 transition-all duration-200 whitespace-nowrap flex-1 sm:flex-none"
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={handleSubmit}
                disabled={isLoading || holdings.length === 0}
                className={`px-8 py-3 font-medium rounded-lg transition-all duration-200 whitespace-nowrap flex-1 sm:flex-none ${
                  isLoading || holdings.length === 0
                    ? 'bg-gray-300 text-gray-500 cursor-not-allowed'
                    : 'bg-black text-white hover:bg-gray-800'
                }`}
              >
                {isLoading ? (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="animate-spin h-5 w-5 text-white" fill="none" viewBox="0 0 24 24">
                      <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                      <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
                    </svg>
                    Processing...
                  </span>
                ) : (
                  <span className="flex items-center justify-center gap-2">
                    <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
                    </svg>
                    {isEditing ? 'Update Portfolio' : 'Create Portfolio'}
                  </span>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioForm;