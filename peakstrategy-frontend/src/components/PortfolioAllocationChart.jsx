// src/components/PortfolioAllocationChart.jsx
import React, { useState, useMemo, useEffect } from 'react';
import {
  PieChart,
  Pie,
  Cell,
  ResponsiveContainer,
  Tooltip,
  Legend
} from 'recharts';

const PortfolioAllocationChart = ({ 
  portfolios, 
  individualPrices, 
  performanceError,
  performanceLoading 
}) => {
  const [selectedPortfolio, setSelectedPortfolio] = useState('all');
  const [viewMode, setViewMode] = useState('current'); // 'current' or 'cost'
  const [activeIndex, setActiveIndex] = useState(null);
  const [hoveredSector, setHoveredSector] = useState(null);
  const [isMobile, setIsMobile] = useState(false);

  // Check for mobile screen size
  useEffect(() => {
    const checkMobile = () => {
      setIsMobile(window.innerWidth <= 768); // Standard mobile breakpoint
    };
    
    // Initial check
    checkMobile();
    
    // Add event listener
    window.addEventListener('resize', checkMobile);
    
    // Cleanup
    return () => window.removeEventListener('resize', checkMobile);
  }, []);

  // Slightly darker professional color palette (15 distinct colors)
  const COLORS = [
    '#0066CC', '#00A88A', '#E0A526', '#E0662E', '#6D67CC',
    '#5CA67D', '#E04A4A', '#3DB8AC', '#E0B542', '#00B58A',
    '#0D6B8B', '#D63A5A', '#052B38', '#5F0A9C', '#C41C6D',
    '#004C99', '#008C72', '#C48C1F', '#CC5C29', '#5A57A8',
    '#4A8C6D', '#CC3A3A', '#33A69C', '#CC9C3A', '#00A07A'
  ];

  // Generate consistent colors based on symbol
  const getColorForSymbol = (symbol, index) => {
    return COLORS[index % COLORS.length];
  };

  // Calculate aggregated data based on selected portfolio
  const { aggregatedHoldings, chartData, totalPortfolioValue, selectedPortfolioName } = useMemo(() => {
    if (!portfolios || portfolios.length === 0) {
      return { 
        aggregatedHoldings: {}, 
        chartData: [], 
        totalPortfolioValue: 0,
        selectedPortfolioName: 'No Portfolios' 
      };
    }

    // Get the portfolios to aggregate
    let portfoliosToAggregate = [];
    let portfolioName = '';
    
    if (selectedPortfolio === 'all') {
      portfoliosToAggregate = portfolios;
      portfolioName = 'All Portfolios';
    } else {
      const portfolio = portfolios.find(p => p.id === selectedPortfolio);
      if (portfolio) {
        portfoliosToAggregate = [portfolio];
        portfolioName = portfolio.name;
      } else {
        portfoliosToAggregate = [];
        portfolioName = 'Portfolio Not Found';
      }
    }

    if (portfoliosToAggregate.length === 0) {
      return { 
        aggregatedHoldings: {}, 
        chartData: [], 
        totalPortfolioValue: 0,
        selectedPortfolioName 
      };
    }

    // Aggregate holdings by symbol
    const holdingsMap = {};
    let totalValue = 0;

    portfoliosToAggregate.forEach(portfolio => {
      portfolio.holdings?.forEach(holding => {
        const symbol = holding.symbol;
        const shares = holding.shares || 0;
        const averagePrice = holding.averageCost || 0;

        // Calculate current value using individual prices or fallback to average price
        const currentPrice = individualPrices?.[symbol] || averagePrice;
        const currentValue = shares * currentPrice;
        const costBasis = shares * averagePrice;
        
        if (!holdingsMap[symbol]) {
          holdingsMap[symbol] = {
            symbol,
            name: holding.name || symbol,
            shares: 0,
            currentValue: 0,
            costBasis: 0,
            currentPrice: 0,
            averagePrice: 0,
            portfolios: [] // Track which portfolios this stock appears in
          };
        }
        
        holdingsMap[symbol].shares += shares;
        holdingsMap[symbol].currentValue += currentValue;
        holdingsMap[symbol].costBasis += costBasis;
        holdingsMap[symbol].currentPrice = currentPrice; // Use latest price
        holdingsMap[symbol].averagePrice = (holdingsMap[symbol].costBasis / holdingsMap[symbol].shares) || averagePrice;
        
        // Track portfolio
        if (!holdingsMap[symbol].portfolios.includes(portfolio.name)) {
          holdingsMap[symbol].portfolios.push(portfolio.name);
        }
        
        // Add to total value based on view mode
        const valueToAdd = viewMode === 'current' ? currentValue : costBasis;
        totalValue += valueToAdd;
      });
    });

    // Convert to array and calculate percentages
    const holdingsArray = Object.values(holdingsMap);
    
    const chartDataArray = holdingsArray.map(holding => {
      const value = viewMode === 'current' ? holding.currentValue : holding.costBasis;
      const percentage = totalValue > 0 ? (value / totalValue) * 100 : 0;
      const change = holding.currentValue - holding.costBasis;
      const changePercent = holding.costBasis > 0 ? 
        ((holding.currentValue - holding.costBasis) / holding.costBasis) * 100 : 0;
      
      return {
        ...holding,
        value,
        percentage,
        formattedValue: value.toLocaleString('en-US', {
          style: 'currency',
          currency: 'USD',
          minimumFractionDigits: 2,
          maximumFractionDigits: 2
        }),
        formattedPercentage: `${percentage.toFixed(2)}%`,
        change,
        changePercent,
        portfolioCount: holding.portfolios.length,
        portfolioList: holding.portfolios.join(', '),
        // For display in tooltip
        displayPrice: viewMode === 'current' ? holding.currentPrice : holding.averagePrice
      };
    }).sort((a, b) => b.value - a.value); // Already sorted from highest to lowest

    return {
      aggregatedHoldings: holdingsMap,
      chartData: chartDataArray,
      totalPortfolioValue: totalValue,
      selectedPortfolioName: portfolioName
    };
  }, [portfolios, individualPrices, selectedPortfolio, viewMode]);

  // Custom tooltip component
  const CustomTooltip = ({ active, payload }) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;

      return (
        <div className="bg-white p-4 border border-gray-200 rounded-lg shadow-lg min-w-[250px]">
          <div className="flex items-center gap-2 mb-2">
            <div 
              className="w-3 h-3 rounded-full" 
              style={{ backgroundColor: payload[0].color }}
            />
            <div>
              <p className="font-bold text-black">{data.name}</p>
              <p className="text-sm text-gray-600">{data.symbol}</p>
            </div>
          </div>
          <div className="space-y-1">
            <p className="text-sm">
              <span className="text-gray-600">Allocation:</span>{' '}
              <span className="font-semibold text-black">{data.formattedPercentage}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-600">Value:</span>{' '}
              <span className="font-semibold text-black">{data.formattedValue}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-600">Shares:</span>{' '}
              <span className="font-semibold text-black">{data.shares.toLocaleString()}</span>
            </p>
            <p className="text-sm">
              <span className="text-gray-600">
                {viewMode === 'current' ? 'Current Price:' : 'Avg. Cost:'}
              </span>{' '}
              <span className="font-semibold text-black">${data.displayPrice.toFixed(2)}</span>
            </p>
            {selectedPortfolio === 'all' && (
              <p className="text-sm">
                <span className="text-gray-600">In Portfolios:</span>{' '}
                <span className="font-semibold text-black">{data.portfolioCount}</span>
              </p>
            )}
          </div>
          <div className="mt-3 pt-3 border-t border-gray-100">
            <p className={`text-sm font-medium ${data.change >= 0 ? 'text-green-600' : 'text-red-600'}`}>
              Unrealized {data.change >= 0 ? 'Gain' : 'Loss'}: ${Math.abs(data.change).toFixed(2)} ({data.changePercent.toFixed(2)}%)
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  const CustomLegend = ({ payload }) => {
    if (!payload || payload.length === 0) return null;
    
    // Use chartData which is already sorted from highest to lowest value
    const topHoldings = chartData.slice(0, 10);
    
    return (
      <div className="space-y-2">
        <div className="flex items-center justify-between mb-2 gap-2">
          <p className="text-sm font-medium text-gray-700">Top Holdings</p>
          <p className="text-xs text-gray-500">
            {viewMode === 'current' ? 'Current Value' : 'Cost Basis'}
          </p>
        </div>
        {topHoldings.map((item, index) => {
          const color = getColorForSymbol(item.symbol, index);
          return (
            <div
              key={`legend-${index}`}
              className="flex items-center justify-between p-2 hover:bg-gray-50 rounded cursor-pointer transition-colors"
              onMouseEnter={() => setHoveredSector(item.symbol)}
              onMouseLeave={() => setHoveredSector(null)}
              style={{
                backgroundColor: hoveredSector === item.symbol ? '#f9fafb' : 'transparent'
              }}
            >
              <div className="flex items-center gap-2">
                <div 
                  className="w-3 h-3 rounded-full" 
                  style={{ backgroundColor: color }}
                />
                <span className="text-sm text-gray-700 truncate max-w-[120px]">
                  {item.symbol}
                </span>
              </div>
              <span className="text-sm font-medium text-black">
                {item.formattedPercentage}
              </span>
            </div>
          );
        })}
        {chartData.length > 10 && (
          <p className="text-xs text-gray-500 text-center mt-2">
            +{chartData.length - 10} more holdings
          </p>
        )}
      </div>
    );
  };

  // Handle pie slice hover
  const onPieEnter = (_, index) => {
    setActiveIndex(index);
  };

  const onPieLeave = () => {
    setActiveIndex(null);
  };

  // Format data for the pie chart
  const formattedChartData = useMemo(() => {
    return chartData.map((item, index) => ({
      ...item,
      fill: getColorForSymbol(item.symbol, index),
      name: item.symbol
    }));
  }, [chartData]);

  // Prepare portfolio options for dropdown
  const portfolioOptions = useMemo(() => {
    if (!portfolios || !Array.isArray(portfolios)) {
      return [{ value: 'all', label: 'All Portfolios' }];
    }
    
    return [
      { value: 'all', label: 'All Portfolios' },
      ...portfolios.map(portfolio => ({
        value: portfolio.id,
        label: portfolio.name
      }))
    ];
  }, [portfolios]);

  if (!portfolios || portfolios.length === 0) {
    return null;
  }

  if (chartData.length === 0) {
    return (
      <div className="bg-white border border-gray-200 rounded-xl p-6">
        <h2 className="text-xl font-bold text-black mb-6">Portfolio Allocation</h2>
        <div className="flex flex-col items-center justify-center py-12">
          <div className="w-32 h-32 mb-4 bg-gray-100 rounded-full flex items-center justify-center">
            <svg className="w-16 h-16 text-gray-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M11 3.055A9.001 9.001 0 1020.945 13H11V3.055z" />
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M20.488 9H15V3.512A9.025 9.025 0 0120.488 9z" />
            </svg>
          </div>
          <p className="text-gray-600">
            {selectedPortfolio === 'all' 
              ? 'No holdings found across all portfolios' 
              : `No holdings found in ${selectedPortfolioName}`}
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6">
      {/* Chart Header with Controls */}
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4 mb-6">
        <div>
          <h2 className="text-xl font-bold text-black">Portfolio Allocation</h2>
          <p className="text-sm text-gray-600 mt-1">
            {selectedPortfolioName} • {chartData.length} holdings
          </p>
        </div>
        
        <div className="flex flex-col sm:flex-row sm:items-center gap-4">
          {/* Portfolio Selection */}
          <div>
            <label htmlFor="portfolio-select" className="block text-sm font-medium text-gray-700 mb-1">
              Select Portfolio
            </label>
            <select
              id="portfolio-select"
              value={selectedPortfolio}
              onChange={(e) => setSelectedPortfolio(e.target.value)}
              className="block w-full sm:w-48 px-3 py-2 text-sm border border-gray-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-black focus:border-transparent"
            >
              {portfolioOptions.map(option => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>
          
          {/* View Mode Toggle */}
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              View by
            </label>
            <div className="flex bg-gray-100 rounded-lg p-1">
              <button
                type="button"
                onClick={() => setViewMode('current')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'current'
                    ? 'bg-white text-black shadow-sm'
                    : 'text-gray-600 hover:text-black'
                }`}
                disabled={performanceError}
              >
                Current Value
              </button>
              <button
                type="button"
                onClick={() => setViewMode('cost')}
                className={`px-3 py-1.5 text-sm font-medium rounded-md transition-colors ${
                  viewMode === 'cost'
                    ? 'bg-white text-black shadow-sm'
                    : 'text-gray-600 hover:text-black'
                }`}
              >
                Cost Basis
              </button>
            </div>
          </div>
        </div>
      </div>

      {/* Performance Loading/Error State */}
      {performanceLoading && (
        <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <div className="flex items-center">
            <svg className="animate-spin h-4 w-4 text-blue-500 mr-2" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
            <span className="text-blue-700 text-sm">Updating current market prices...</span>
          </div>
        </div>
      )}

      {performanceError && viewMode === 'current' && (
        <div className="mb-4 p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
          <div className="flex items-start">
            <svg className="w-4 h-4 text-yellow-500 mr-2 mt-0.5 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-2.5L13.732 4c-.77-.833-1.998-.833-2.732 0L4.732 16.5c-.77.833.192 2.5 1.732 2.5" />
            </svg>
            <div className="flex-1">
              <p className="text-yellow-700 text-sm font-medium">Live prices unavailable</p>
              <p className="text-yellow-600 text-xs mt-1">
                Using cost basis values. Switch to "Cost Basis" view for accurate allocation percentages.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Main Chart Area */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Pie Chart */}
        <div className="lg:col-span-2">
          <div className="h-[400px]">
            <ResponsiveContainer width="100%" height="100%">
              <PieChart>
                <Pie
                  data={formattedChartData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={(entry) => {
                    // Only show labels for slices > 5%
                    if (entry.percentage > 3) {
                      return `${entry.symbol}`;
                    }
                    return '';
                  }}
                  outerRadius={isMobile ? 140 : 180} // Half size on mobile
                  innerRadius={isMobile ? 70 : 90} // Half size on mobile
                  paddingAngle={2}
                  dataKey="value"
                  nameKey="symbol"
                  onMouseEnter={onPieEnter}
                  onMouseLeave={onPieLeave}
                  animationDuration={800}
                  animationBegin={0}
                  isAnimationActive={true}
                >
                  {formattedChartData.map((entry, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={entry.fill}
                      stroke="#ffffff"
                      strokeWidth={2}
                      opacity={activeIndex === null || activeIndex === index ? 1 : 0.6}
                      className="transition-opacity duration-200 cursor-pointer"
                    />
                  ))}
                </Pie>
                <Tooltip content={<CustomTooltip />} />
              {!isMobile && (
                <Legend
                  content={<CustomLegend />}
                  verticalAlign="middle"
                  align="right"
                  layout="vertical"
                  wrapperStyle={{ paddingLeft: '20px' }}
                />
              )}
            </PieChart>
          </ResponsiveContainer>
          </div>
        </div>

        {/* Top Holdings List - Already uses chartData which is sorted from highest to lowest */}
        <div className="lg:col-span-1">
          <div className="bg-gray-50 rounded-lg p-4 h-full">
            <h4 className="font-medium text-black mb-4">Top 5 Holdings</h4>
            <div className="space-y-3">
              {chartData.slice(0, 5).map((item, index) => (
                <div
                  key={item.symbol}
                  className="flex items-center justify-between p-3 bg-white rounded-lg border border-gray-200 hover:border-gray-300 transition-colors"
                  onMouseEnter={() => setHoveredSector(item.symbol)}
                  onMouseLeave={() => setHoveredSector(null)}
                >
                  <div className="flex items-center gap-3">
                    <div 
                      className="w-4 h-4 rounded-full" 
                      style={{ backgroundColor: getColorForSymbol(item.symbol, index) }}
                    />
                    <div>
                      <p className="font-medium text-black">{item.symbol}</p>
                      <p className="text-xs text-gray-500 truncate max-w-[100px]">
                        {item.name}
                      </p>
                    </div>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold text-black">{item.formattedPercentage}</p>
                    <p className="text-xs text-gray-500">{item.formattedValue}</p>
                  </div>
                </div>
              ))}
            </div>
            
            {/* Additional Stats */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h5 className="text-sm font-medium text-gray-700 mb-3">Distribution Stats</h5>
              <div className="space-y-2">
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Top 3 Holdings</span>
                  <span className="text-sm font-medium text-black">
                    {chartData.slice(0, 3).reduce((sum, item) => sum + item.percentage, 0).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Top 5 Holdings</span>
                  <span className="text-sm font-medium text-black">
                    {chartData.slice(0, 5).reduce((sum, item) => sum + item.percentage, 0).toFixed(1)}%
                  </span>
                </div>
                <div className="flex justify-between">
                  <span className="text-sm text-gray-600">Remaining Holdings</span>
                  <span className="text-sm font-medium text-black">
                    {chartData.slice(5).reduce((sum, item) => sum + item.percentage, 0).toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default PortfolioAllocationChart;