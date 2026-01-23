// src/components/PriceChangesTable.jsx
import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import { portfolioApi } from '../services/portfolioApi';
import {
  TrendingUp,
  TrendingDown,
  RefreshCw,
  AlertCircle,
  Loader2,
  ChevronUp,
  ChevronDown,
  Filter,
  ArrowUpDown,
} from 'lucide-react';

export default function PriceChangesTable() {
  const [priceData, setPriceData] = useState(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  const [sortConfig, setSortConfig] = useState({
    key: 'value',
    direction: 'desc',
  });
  const [showSortDropdown, setShowSortDropdown] = useState(false);

  const intervalRef = useRef(null);
  const dropdownRef = useRef(null);

  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  const formatPercentage = (value) => {
    const numValue = parseFloat(value);
    return `${numValue >= 0 ? '+' : ''}${numValue.toFixed(2)}%`;
  };

  const fetchPriceChanges = useCallback(async () => {
    try {
      const result = await portfolioApi.getPriceChanges();
      setPriceData(result);
      setError(null);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to fetch price changes:', err);
      setError('Unable to load market data. Please try again.');
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    let isActive = true;

    const initializeData = async () => {
      if (isActive) {
        await fetchPriceChanges();
      }
    };

    initializeData();

    // Set up polling every 60 seconds
    intervalRef.current = setInterval(fetchPriceChanges, 60000);

    return () => {
      isActive = false;
      clearInterval(intervalRef.current);
    };
  }, [fetchPriceChanges]);

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setShowSortDropdown(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const handleSort = (key, direction = null) => {
    if (direction) {
      setSortConfig({ key, direction });
    } else {
      let newDirection = 'asc';
      if (sortConfig.key === key && sortConfig.direction === 'asc') {
        newDirection = 'desc';
      }
      setSortConfig({ key, direction: newDirection });
    }
    setShowSortDropdown(false);
  };

  const getSortIndicator = (key) => {
    if (sortConfig.key !== key) return null;
    
    return (
      <div className="ml-2 flex items-center">
        {sortConfig.direction === 'asc' ? (
          <ChevronUp className="w-3 h-3 text-blue-600" />
        ) : (
          <ChevronDown className="w-3 h-3 text-blue-600" />
        )}
        <span className="ml-1 text-xs font-normal text-blue-600">
          {sortConfig.direction === 'asc' ? 'A → Z' : 'Z → A'}
        </span>
      </div>
    );
  };

  const getSortLabel = (key) => {
    switch (key) {
      case 'symbol':
        return 'Symbol';
      case 'value':
        return 'Position Value';
      case 'dailyChange':
        return 'Daily Change %';
      case 'allocation':
        return 'Allocation';
      default:
        return '';
    }
  };

  const sortedHoldings = useMemo(() => {
    if (!priceData?.holdings) return [];

    const holdings = [...priceData.holdings];
    
    holdings.sort((a, b) => {
      let aValue, bValue;
      
      switch (sortConfig.key) {
        case 'symbol':
          aValue = a.symbol;
          bValue = b.symbol;
          break;
        case 'value':
          aValue = a.value;
          bValue = b.value;
          break;
        case 'dailyChange':
          // Sort by percentage instead of absolute value
          aValue = parseFloat(a.dailyChange.percent);
          bValue = parseFloat(b.dailyChange.percent);
          break;
        case 'allocation':
          aValue = a.weight;
          bValue = b.weight;
          break;
        default:
          return 0;
      }
      
      if (sortConfig.key === 'symbol') {
        return sortConfig.direction === 'asc' 
          ? aValue.localeCompare(bValue)
          : bValue.localeCompare(aValue);
      }
      
      if (sortConfig.direction === 'asc') {
        return aValue - bValue;
      } else {
        return bValue - aValue;
      }
    });
    
    return holdings;
  }, [priceData?.holdings, sortConfig]);

  const renderMarketStatus = (status) => {
    const isOpen = status === 'OPEN';
    return (
      <div className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-medium ${
        isOpen 
          ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
          : 'bg-gray-100 text-gray-600 border border-gray-200'
      }`}>
        <div className={`w-2 h-2 rounded-full mr-2 ${isOpen ? 'bg-emerald-500' : 'bg-gray-500'}`} />
        Market {isOpen ? 'Open' : 'Closed'}
      </div>
    );
  };

  const renderLoadingState = () => (
    <div className="flex flex-col items-center justify-center p-8 space-y-3">
      <Loader2 className="w-8 h-8 text-blue-500 animate-spin" />
      <p className="text-gray-600">Loading market data...</p>
      <p className="text-sm text-gray-500">Fetching real-time price updates</p>
    </div>
  );

  const renderErrorState = () => (
    <div className="p-6 border border-red-200 rounded-lg bg-red-50">
      <div className="flex items-start">
        <AlertCircle className="w-5 h-5 text-red-500 mt-0.5 mr-3 flex-shrink-0" />
        <div>
          <h4 className="text-red-800 font-medium">Data Unavailable</h4>
          <p className="text-red-600 text-sm mt-1">{error}</p>
          <button
            onClick={fetchPriceChanges}
            className="mt-3 px-4 py-2 bg-white border border-red-300 text-red-700 rounded-md text-sm font-medium hover:bg-red-50 transition-colors"
          >
            <RefreshCw className="w-4 h-4 inline mr-2" />
            Retry
          </button>
        </div>
      </div>
    </div>
  );

  const renderEmptyState = () => (
    <div className="text-center p-8 border-2 border-dashed border-gray-200 rounded-lg">
      <div className="text-gray-400 mb-3">
        <TrendingUp className="w-12 h-12 mx-auto" />
      </div>
      <h4 className="text-gray-700 font-medium mb-1">No Holdings Found</h4>
      <p className="text-gray-500 text-sm">Add investments to track price changes</p>
    </div>
  );

  if (isLoading) return renderLoadingState();
  if (error) return renderErrorState();
  if (!priceData?.holdings?.length) return renderEmptyState();

  const { portfolio, market } = priceData;

  return (
    <div className="bg-white rounded-xl border border-gray-200 shadow-sm overflow-hidden">
      {/* Header */}
      <div className="px-6 py-4 border-b border-gray-100 bg-gradient-to-r from-gray-50 to-white">
        <div className="flex items-center justify-between">
          <div>
            <h2 className="text-xl font-semibold text-gray-900">Daily Performance</h2>
            <p className="text-sm text-gray-600 mt-1">Real-time price changes and portfolio metrics</p>
          </div>
          {renderMarketStatus(market.status)}
        </div>
      </div>

      {/* Portfolio Summary */}
      <div className="px-6 py-4 bg-gradient-to-r from-blue-50 to-indigo-50 border-b border-blue-100">
        <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between">
          <div>
            <p className="text-sm text-gray-600 mb-1">Total Portfolio Value</p>
            <p className="text-2xl font-bold text-gray-900">
              {formatCurrency(portfolio.totalValue)}
            </p>
          </div>
          
          <div className={`mt-3 sm:mt-0 flex items-center ${
            portfolio.dailyChange.absolute >= 0 ? 'text-emerald-700' : 'text-rose-700'
          }`}>
            {portfolio.dailyChange.absolute >= 0 ? (
              <TrendingUp className="w-5 h-5 mr-2" />
            ) : (
              <TrendingDown className="w-5 h-5 mr-2" />
            )}
            <div>
              <p className="text-lg font-semibold">
                {portfolio.dailyChange.absolute >= 0 ? '+' : ''}
                {formatCurrency(portfolio.dailyChange.absolute)}
              </p>
              <p className="text-sm">
                {formatPercentage(portfolio.dailyChange.percent)}
              </p>
            </div>
          </div>
        </div>
      </div>

      {/* Sorting Controls */}
      <div className="px-6 py-3 bg-gray-50 border-b border-gray-200">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-4">
            <div className="relative" ref={dropdownRef}>
              <button
                onClick={() => setShowSortDropdown(!showSortDropdown)}
                className="flex items-center px-3 py-1.5 bg-white border border-gray-300 rounded-lg text-sm font-medium text-gray-700 hover:bg-gray-50 transition-colors"
              >
                <Filter className="w-4 h-4 mr-2 text-gray-500" />
                Sort by
                <ChevronDown className="w-4 h-4 ml-1" />
              </button>
              
              {showSortDropdown && (
                <div className="absolute top-full left-0 mt-1 w-56 bg-white border border-gray-200 rounded-lg shadow-lg z-10">
                  <div className="p-2">
                    <div className="px-3 py-2 text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Sort by column
                    </div>
                    {['symbol', 'value', 'dailyChange', 'allocation'].map((key) => (
                      <div key={key} className="flex items-center justify-between px-3 py-2 hover:bg-gray-50 rounded cursor-pointer">
                        <div 
                          className="flex-1"
                          onClick={() => handleSort(key)}
                        >
                          {getSortLabel(key)}
                        </div>
                        <div className="flex space-x-1">
                          <button
                            onClick={() => handleSort(key, 'asc')}
                            className={`p-1 rounded ${sortConfig.key === key && sortConfig.direction === 'asc' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-gray-100'}`}
                            title="Sort ascending"
                          >
                            <ChevronUp className="w-4 h-4" />
                          </button>
                          <button
                            onClick={() => handleSort(key, 'desc')}
                            className={`p-1 rounded ${sortConfig.key === key && sortConfig.direction === 'desc' ? 'bg-blue-100 text-blue-600' : 'text-gray-400 hover:bg-gray-100'}`}
                            title="Sort descending"
                          >
                            <ChevronDown className="w-4 h-4" />
                          </button>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              )}
            </div>
            
            <div className="flex items-center text-sm text-gray-600">
              <span className="mr-2">Currently sorted by:</span>
              <span className="font-medium text-blue-600">
                {getSortLabel(sortConfig.key)} {sortConfig.direction === 'asc' ? '(low to high)' : '(high to low)'}
              </span>
            </div>
          </div>
          
          <div className="text-xs text-gray-500">
            Click headers or use dropdown to sort
          </div>
        </div>
      </div>

      {/* Table */}
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50">
            <tr>
              <th 
                scope="col" 
                className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 group"
                onClick={() => handleSort('symbol')}
              >
                <div className={`flex items-center ${sortConfig.key === 'symbol' ? 'text-blue-600' : ''}`}>
                  Symbol
                  {getSortIndicator('symbol')}
                  <div className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ArrowUpDown className="w-3 h-3 text-gray-400" />
                  </div>
                </div>
              </th>
              <th scope="col" className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                Current Price
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 group"
                onClick={() => handleSort('value')}
              >
                <div className={`flex items-center justify-end ${sortConfig.key === 'value' ? 'text-blue-600' : ''}`}>
                  Position Value
                  {getSortIndicator('value')}
                  <div className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ArrowUpDown className="w-3 h-3 text-gray-400" />
                  </div>
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 group"
                onClick={() => handleSort('dailyChange')}
              >
                <div className={`flex items-center justify-end ${sortConfig.key === 'dailyChange' ? 'text-blue-600' : ''}`}>
                  Daily Change
                  {getSortIndicator('dailyChange')}
                  <div className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ArrowUpDown className="w-3 h-3 text-gray-400" />
                  </div>
                </div>
              </th>
              <th 
                scope="col" 
                className="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider cursor-pointer hover:bg-gray-100 group"
                onClick={() => handleSort('allocation')}
              >
                <div className={`flex items-center justify-end ${sortConfig.key === 'allocation' ? 'text-blue-600' : ''}`}>
                  Allocation
                  {getSortIndicator('allocation')}
                  <div className="ml-1 opacity-0 group-hover:opacity-100 transition-opacity">
                    <ArrowUpDown className="w-3 h-3 text-gray-400" />
                  </div>
                </div>
              </th>
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {sortedHoldings.map((holding) => {
              const isPositive = parseFloat(holding.dailyChange.percent) >= 0;
              return (
                <tr key={holding.symbol} className="hover:bg-gray-50 transition-colors">
                  <td className="px-6 py-4 whitespace-nowrap">
                    <div className="flex items-center">
                      <div className="ml-0">
                        <div className="text-sm font-semibold text-gray-900">
                          {holding.symbol}
                        </div>
                      </div>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    {formatCurrency(holding.price)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right text-sm text-gray-900 font-medium">
                    {formatCurrency(holding.value)}
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className={`inline-flex items-center px-2.5 py-1 rounded-full text-sm font-medium ${
                      isPositive
                        ? 'bg-emerald-50 text-emerald-700'
                        : 'bg-rose-50 text-rose-700'
                    }`}>
                      {isPositive ? (
                        <TrendingUp className="w-3.5 h-3.5 mr-1.5" />
                      ) : (
                        <TrendingDown className="w-3.5 h-3.5 mr-1.5" />
                      )}
                      <span>
                        {formatPercentage(holding.dailyChange.percent)}
                        <span className="ml-1">({formatCurrency(holding.dailyChange.absolute)})</span>
                      </span>
                    </div>
                  </td>
                  
                  <td className="px-6 py-4 whitespace-nowrap text-right">
                    <div className="text-sm text-gray-900 font-medium">
                      {(holding.weight * 100).toFixed(1)}%
                    </div>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>

      {/* Footer */}
      <div className="px-6 py-3 bg-gray-50 border-t border-gray-200">
        <div className="flex items-center justify-between text-sm text-gray-500">
          <div className="flex items-center">
            <RefreshCw className="w-3.5 h-3.5 mr-1.5 text-gray-400" />
            <span>Auto-refreshes every 60 seconds</span>
          </div>
          <div>
            {lastUpdated && (
              <span>
                Updated {lastUpdated.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
              </span>
            )}
          </div>
        </div>
      </div>
    </div>
  );
}