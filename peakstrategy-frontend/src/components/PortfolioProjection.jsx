import { useState, useEffect, useMemo } from 'react';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';

const PortfolioProjection = ({ portfolios, performanceError }) => {
  // Configuration state
  const [projectionYears, setProjectionYears] = useState(20);
  const [annualReturn, setAnnualReturn] = useState(10);
  const [additionalInvestment, setAdditionalInvestment] = useState(0);
  const [investmentFrequency, setInvestmentFrequency] = useState('monthly');
  const [isCustomReturn, setIsCustomReturn] = useState(false);
  
  // Calculate total current portfolio value for default starting value
  const totalPortfolioValue = useMemo(() => {
    if (performanceError || !portfolios || portfolios.length === 0) return 0;
    return portfolios.reduce((sum, portfolio) => sum + (portfolio.currentValue || 0), 0);
  }, [portfolios, performanceError]);

  // Editable starting value state
  const [startingValue, setStartingValue] = useState(totalPortfolioValue);
  const [isManualStartValue, setIsManualStartValue] = useState(false);
  const [inputValue, setInputValue] = useState('');

  // Format number for display (no decimals, with commas)
  const formatNumber = (num) => {
    return Math.round(num).toLocaleString('en-US');
  };

  // Initialize input value when component mounts or totalPortfolioValue changes
  useEffect(() => {
    if (!isManualStartValue) {
      setStartingValue(totalPortfolioValue);
      setInputValue(formatNumber(totalPortfolioValue));
    }
  }, [totalPortfolioValue, isManualStartValue]);

  // Initialize input value on component mount
  useEffect(() => {
    setInputValue(formatNumber(totalPortfolioValue));
  }, []);

  // Reset to actual portfolio value
  const resetToPortfolioValue = () => {
    setStartingValue(totalPortfolioValue);
    setInputValue(formatNumber(totalPortfolioValue));
    setIsManualStartValue(false);
  };

  // Handle starting value input change - allow only numbers and commas
  const handleInputChange = (e) => {
    let value = e.target.value;
    
    // Remove all non-digit characters except commas
    value = value.replace(/[^0-9,]/g, '');
    
    // Remove extra commas
    value = value.replace(/,+/g, ',');
    
    // Don't allow comma at the beginning
    if (value.startsWith(',')) {
      value = value.substring(1);
    }
    
    setInputValue(value);
    setIsManualStartValue(true);
    
    // Convert to number for calculations (remove commas and parse)
    const numValue = parseInt(value.replace(/,/g, '') || '0', 10);
    setStartingValue(numValue);
  };

  // Format input value with commas on blur
  const handleInputBlur = () => {
    if (inputValue) {
      const numValue = parseInt(inputValue.replace(/,/g, '') || '0', 10);
      setInputValue(formatNumber(numValue));
      setStartingValue(numValue);
    }
  };

  // Handle increment/decrement with keyboard
  const handleKeyDown = (e) => {
    if (e.key === 'ArrowUp') {
      e.preventDefault();
      const currentValue = parseInt(inputValue.replace(/,/g, '') || '0', 10);
      const newValue = currentValue + 1;
      setInputValue(formatNumber(newValue));
      setStartingValue(newValue);
      setIsManualStartValue(true);
    } else if (e.key === 'ArrowDown') {
      e.preventDefault();
      const currentValue = parseInt(inputValue.replace(/,/g, '') || '0', 10);
      const newValue = Math.max(0, currentValue - 1000);
      setInputValue(formatNumber(newValue));
      setStartingValue(newValue);
      setIsManualStartValue(true);
    }
  };

  // Generate projection data
  const projectionData = useMemo(() => {
    if (!portfolios || portfolios.length === 0) return [];
    
    const data = [];
    let currentValue = startingValue;
    
    // Calculate contributions per period
    const getContributionsPerPeriod = () => {
      switch (investmentFrequency) {
        case 'weekly': return additionalInvestment * 52;
        case 'biweekly': return additionalInvestment * 26;
        case 'monthly': return additionalInvestment * 12;
        case 'yearly': return additionalInvestment;
        default: return additionalInvestment * 12;
      }
    };
    
    const annualContribution = getContributionsPerPeriod();
    const monthlyReturn = annualReturn / 100 / 12;
    const periods = projectionYears * 12;
    
    for (let i = 0; i <= periods; i++) {
      const year = Math.floor(i / 12);
      const month = i % 12;
      
      if (i > 0) {
        // Apply monthly return
        currentValue = currentValue * (1 + monthlyReturn);
        
        // Add contributions based on frequency
        if (additionalInvestment > 0) {
          switch (investmentFrequency) {
            case 'weekly':
              if (i % (12/52) === 0) currentValue += additionalInvestment;
              break;
            case 'biweekly':
              if (i % (12/26) === 0) currentValue += additionalInvestment;
              break;
            case 'monthly':
              currentValue += additionalInvestment;
              break;
            case 'yearly':
              if (month === 0) currentValue += additionalInvestment;
              break;
          }
        }
      }
      
      // Only add yearly points to the chart for cleaner display
      if (month === 0 || i === 0) {
        data.push({
          year: year,
          label: `Year ${year}`,
          value: parseFloat(currentValue.toFixed(2)),
          contributions: parseFloat((annualContribution * year).toFixed(2)),
          growth: parseFloat((currentValue - startingValue - (annualContribution * year)).toFixed(2))
        });
      }
    }
    
    return data;
  }, [startingValue, projectionYears, annualReturn, additionalInvestment, investmentFrequency, portfolios]);

  // Format currency with commas, no decimals
  const formatCurrency = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 0,
      maximumFractionDigits: 0,
    }).format(value);
  };

  // Format currency with 2 decimal places for tooltips
  const formatCurrencyWithDecimals = (value) => {
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }).format(value);
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white p-4 border border-gray-300 rounded-lg shadow-lg">
          <p className="font-semibold text-black mb-2">{label}</p>
          <p className="text-black">
            <span className="font-medium">Portfolio Value: </span>
            {formatCurrencyWithDecimals(payload[0].value)}
          </p>
          <p className="text-gray-600">
            <span className="font-medium">Total Contributions: </span>
            {formatCurrencyWithDecimals(payload[0].payload.contributions)}
          </p>
          <p className="text-gray-600">
            <span className="font-medium">Investment Growth: </span>
            {formatCurrencyWithDecimals(payload[0].payload.growth)}
          </p>
        </div>
      );
    }
    return null;
  };

  // Reset to S&P 500 average
  const resetToSP500 = () => {
    setAnnualReturn(7.5);
    setIsCustomReturn(false);
  };

  // Calculate final value
  const finalValue = useMemo(() => {
    return projectionData[projectionData.length - 1]?.value || 0;
  }, [projectionData]);

  // Calculate total growth
  const totalGrowth = useMemo(() => {
    return finalValue - startingValue;
  }, [finalValue, startingValue]);

  if (!portfolios || portfolios.length === 0) {
    return null;
  }

  return (
    <div className="bg-white border border-gray-200 rounded-xl p-6 mb-8">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between mb-6">
        <div>
          <h2 className="text-2xl font-bold text-black mb-2">Portfolio Projection</h2>
          <p className="text-gray-600">
            Project your investment growth over time based on historical market returns
          </p>
        </div>
        <div className="mt-4 lg:mt-0">
          <div className="flex items-center gap-2">
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
        {/* Controls Panel */}
        <div className="lg:col-span-1 space-y-6">
          <div className="border border-gray-200 rounded-lg p-5">
            <h3 className="font-semibold text-black mb-4">Projection Settings</h3>
            
            {/* Starting Value - Much Improved Input */}
            <div className="mb-5">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Starting Value
                </label>
                <button
                  onClick={resetToPortfolioValue}
                  className="text-xs text-gray-500 hover:text-black transition-colors"
                  disabled={!isManualStartValue}
                >
                  Reset to Current Portfolio
                </button>
              </div>
              <div className="relative">
                <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500 text-lg font-medium">$</span>
                <input
                  type="text"
                  value={inputValue}
                  onChange={handleInputChange}
                  onBlur={handleInputBlur}
                  onKeyDown={handleKeyDown}
                  className="w-full pl-10 pr-12 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:border-transparent text-lg font-medium"
                  placeholder="Enter amount"
                />
                <div className="absolute right-3 top-1/2 transform -translate-y-1/2 flex flex-col">
                  <button
                    type="button"
                    onClick={() => {
                      const currentValue = parseInt(inputValue.replace(/,/g, '') || '0', 10);
                      const newValue = currentValue + 1;
                      setInputValue(formatNumber(newValue));
                      setStartingValue(newValue);
                      setIsManualStartValue(true);
                    }}
                    className="text-gray-500 hover:text-black mb-1"
                  >
                    ▲
                  </button>
                  <button
                    type="button"
                    onClick={() => {
                      const currentValue = parseInt(inputValue.replace(/,/g, '') || '0', 10);
                      const newValue = Math.max(0, currentValue - 1000);
                      setInputValue(formatNumber(newValue));
                      setStartingValue(newValue);
                      setIsManualStartValue(true);
                    }}
                    className="text-gray-500 hover:text-black"
                  >
                    ▼
                  </button>
                </div>
              </div>
              <div className="flex justify-between mt-2">
              </div>
              <p className="text-xs text-gray-500 mt-2">
                {isManualStartValue ? 'Using custom starting value' : `Based on current portfolio value: ${formatCurrency(totalPortfolioValue)}`}
              </p>
            </div>

            {/* Time Horizon */}
            <div className="mb-5">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Time Horizon: {projectionYears} years
              </label>
              <input
                type="range"
                min="1"
                max="40"
                value={projectionYears}
                onChange={(e) => setProjectionYears(parseInt(e.target.value))}
                className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
              />
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>1 year</span>
                <span>40 years</span>
              </div>
            </div>

            {/* Annual Return Rate */}
            <div className="mb-5">
              <div className="flex justify-between items-center mb-2">
                <label className="block text-sm font-medium text-gray-700">
                  Annual Return Rate
                </label>
                <button
                  onClick={resetToSP500}
                  className="text-xs text-gray-500 hover:text-black transition-colors"
                >
                  Reset to S&P 500 Average
                </button>
              </div>
              <div className="flex items-center space-x-3">
                <input
                  type="range"
                  min="0"
                  max="25"
                  step="0.5"
                  value={annualReturn}
                  onChange={(e) => {
                    setAnnualReturn(parseFloat(e.target.value));
                    setIsCustomReturn(true);
                  }}
                  className="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer"
                />
                <div className="w-20 text-center">
                  <span className="font-semibold text-black">{annualReturn}%</span>
                </div>
              </div>
              <div className="flex justify-between text-xs text-gray-500 mt-1">
                <span>0%</span>
                <span>25%</span>
              </div>
            </div>

            {/* Additional Investments */}
            <div className="mb-5">
              <label className="block text-sm font-medium text-gray-700 mb-2">
                Additional Investments
              </label>
              <div className="flex items-center space-x-3">
                <div className="flex-1">
                  <div className="relative">
                    <span className="absolute left-3 top-1/2 transform -translate-y-1/2 text-gray-500">$</span>
                    <input
                      type="number"
                      min="0"
                      step="100"
                      value={additionalInvestment}
                      onChange={(e) => setAdditionalInvestment(parseFloat(e.target.value) || 0)}
                      className="w-full pl-8 pr-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:border-transparent"
                      placeholder="0"
                    />
                  </div>
                </div>
                <select
                  value={investmentFrequency}
                  onChange={(e) => setInvestmentFrequency(e.target.value)}
                  className="py-2 px-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-black focus:border-transparent"
                >
                  <option value="weekly">Weekly</option>
                  <option value="biweekly">Bi-weekly</option>
                  <option value="monthly">Monthly</option>
                  <option value="yearly">Yearly</option>
                </select>
              </div>
              <p className="text-xs text-gray-500 mt-2">
                Total annual contribution: ${(additionalInvestment * 
                  (investmentFrequency === 'weekly' ? 52 :
                   investmentFrequency === 'biweekly' ? 26 :
                   investmentFrequency === 'monthly' ? 12 : 1)).toLocaleString()}
              </p>
            </div>
          </div>
        </div>

        {/* Chart Panel */}
        <div className="lg:col-span-2">
          <div className="border border-gray-200 rounded-lg p-5 h-full">
            <div className="h-96">
              <ResponsiveContainer width="100%" height="100%">
                <LineChart
                  data={projectionData}
                  margin={{ top: 20, right: 30, left: 20, bottom: 20 }}
                >
                  <CartesianGrid 
                    strokeDasharray="3 3" 
                    stroke="#e5e7eb"
                    horizontal={true}
                    vertical={false}
                  />
                  <XAxis 
                    dataKey="label"
                    stroke="#6b7280"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                  />
                  <YAxis 
                    stroke="#6b7280"
                    fontSize={12}
                    tickLine={false}
                    axisLine={{ stroke: '#e5e7eb' }}
                    tickFormatter={(value) => `$${(value / 1000).toFixed(0)}k`}
                  />
                  <Tooltip content={<CustomTooltip />} />
                  <Legend />
                  <Line
                    type="monotone"
                    dataKey="value"
                    name="Portfolio Value"
                    stroke="#000000"
                    strokeWidth={3}
                    dot={false}
                    activeDot={{ r: 6, fill: '#000000' }}
                  />
                </LineChart>
              </ResponsiveContainer>
            </div>
            
            {/* Key Metrics */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mt-6 pt-6 border-t border-gray-100">
              <div className="text-center p-4 border border-gray-100 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Projected Value</p>
                <p className="text-2xl font-bold text-black">
                  {formatCurrency(finalValue)}
                </p>
                <p className="text-xs text-gray-500">in {projectionYears} years</p>
              </div>
              <div className="text-center p-4 border border-gray-100 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Annual Return</p>
                <p className="text-2xl font-bold text-black">{annualReturn}%</p>
              </div>
              <div className="text-center p-4 border border-gray-100 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Total Growth</p>
                <p className={`text-2xl font-bold ${totalGrowth >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                  {formatCurrency(totalGrowth)}
                </p>
              </div>
              <div className="text-center p-4 border border-gray-100 rounded-lg">
                <p className="text-sm text-gray-600 mb-1">Total Contributions</p>
                <p className="text-2xl font-bold text-black">
                  {formatCurrency(projectionData[projectionData.length - 1]?.contributions || 0)}
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>

      <div className="text-sm text-gray-500 border-t border-gray-100 pt-4">
        <p className="mb-1">
          <span className="font-medium">Note:</span> Projections are estimates based on the specified annual return rate. 
          Actual investment returns will vary and are not guaranteed. Past performance (including S&P 500 historical averages) 
          does not guarantee future results.
        </p>
      </div>
    </div>
  );
};

export default PortfolioProjection;