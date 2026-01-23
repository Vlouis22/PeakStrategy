import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer, LineChart, Line } from 'recharts';
import { TrendingUp, TrendingDown, Users, Target, DollarSign, Activity, Zap } from 'lucide-react';

export const AnalystConsensus = ({ consensusData }) => {
  if (!consensusData || !consensusData.data_available) {
    return (
      <div className="w-full max-w-6xl mx-auto p-6 bg-white border border-gray-200">
        <p className="text-gray-500">No analyst consensus data available.</p>
      </div>
    );
  }

  const { ticker, price_targets, consensus_history, earnings_outlook, growth_profile } = consensusData;

  // Calculate price target difference
  const targetDiff = price_targets.average - price_targets.current_price;
  const targetDiffPct = ((targetDiff / price_targets.current_price) * 100).toFixed(2);
  const isUpside = targetDiff > 0;

  // Get current consensus
  const currentConsensus = consensus_history[0];

  // Prepare chart data - transform for grouped bar chart
  const chartData = [...consensus_history].reverse().map(item => ({
    period: item.period === '0m' ? 'Current' : item.period,
    strongBuy: item.breakdown_pct.strong_buy,
    buy: item.breakdown_pct.buy,
    hold: item.breakdown_pct.hold,
    sell: item.breakdown_pct.sell,
    strongSell: item.breakdown_pct.strong_sell
  }));

  // Calculate overall sentiment
  const bullishPct = currentConsensus.breakdown_pct.strong_buy + currentConsensus.breakdown_pct.buy;
  const bearishPct = currentConsensus.breakdown_pct.sell + currentConsensus.breakdown_pct.strong_sell;

  // Helper function to format currency
  const formatCurrency = (value, decimals = 2) => {
    if (value === null || value === undefined) return "N/A";

    const sign = value < 0 ? "-" : "";
    const absValue = Math.abs(value);

    if (absValue >= 1e12) return `${sign}$${(absValue / 1e12).toFixed(decimals)}T`;
    if (absValue >= 1e9) return `${sign}$${(absValue / 1e9).toFixed(decimals)}B`;
    if (absValue >= 1e6) return `${sign}$${(absValue / 1e6).toFixed(decimals)}M`;

    return `${sign}$${absValue.toFixed(decimals)}`;
  };

  // Helper function to format percentage
  const formatPercent = (value, decimals = 2) => {
    if (value === null || value === undefined) return 'N/A';
    const pct = (value * 100).toFixed(decimals);
    return `${value >= 0 ? '+' : ''}${pct}%`;
  };

  // Prepare growth chart data
  const prepareGrowthChartData = () => {
    const data = [];
    
    if (growth_profile?.revenue_growth?.yoy_current !== null) {
      data.push({
        metric: 'Revenue YoY',
        current: growth_profile.revenue_growth.yoy_current * 100,
        projected: growth_profile.revenue_growth.yoy_projected_next_year ? growth_profile.revenue_growth.yoy_projected_next_year * 100 : null
      });
    }
    
    if (growth_profile?.earnings_growth?.yoy_current !== null) {
      data.push({
        metric: 'Earnings YoY',
        current: growth_profile.earnings_growth.yoy_current * 100,
        projected: growth_profile.earnings_growth.yoy_projected_next_year ? growth_profile.earnings_growth.yoy_projected_next_year * 100 : null
      });
    }
    
    if (growth_profile?.free_cash_flow_growth?.yoy_current !== null) {
      data.push({
        metric: 'FCF YoY',
        current: growth_profile.free_cash_flow_growth.yoy_current * 100,
        projected: null
      });
    }
    
    return data;
  };

  const growthChartData = prepareGrowthChartData();

  // Custom tooltip for the chart
  const CustomTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-300 p-3 shadow-lg rounded">
          <p className="font-semibold text-black mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  const GrowthTooltip = ({ active, payload, label }) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-white border border-gray-300 p-3 shadow-lg rounded">
          <p className="font-semibold text-black mb-2">{label}</p>
          {payload.map((entry, index) => (
            <p key={index} className="text-xs" style={{ color: entry.color }}>
              {entry.name}: {entry.value.toFixed(2)}%
            </p>
          ))}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full max-w-6xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-black mb-2">Analyst Ratings</h1>
        <p className="text-gray-600 flex items-center gap-2">
          <span className="font-semibold text-black">{ticker}</span>
          <span>•</span>
          <span>{currentConsensus.total_analysts} Analysts</span>
        </p>
      </div>

      {/* Price Targets Section */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <div className="border border-gray-300 p-5 bg-gray-50">
          <div className="flex items-center gap-2 mb-2">
            <Target className="w-4 h-4 text-gray-600" />
            <p className="text-sm text-gray-600 font-medium">Current Price</p>
          </div>
          <p className="text-2xl font-bold text-black">${price_targets.current_price.toFixed(2)}</p>
        </div>

        <div className={`border-2 p-5 ${isUpside ? 'border-green-600 bg-green-50' : 'border-red-600 bg-red-50'}`}>
          <div className="flex items-center gap-2 mb-2">
            <Target className={`w-4 h-4 ${isUpside ? 'text-green-700' : 'text-red-700'}`} />
            <p className={`text-sm font-medium ${isUpside ? 'text-green-700' : 'text-red-700'}`}>Average Target</p>
          </div>
          <p className={`text-2xl font-bold ${isUpside ? 'text-green-700' : 'text-red-700'}`}>
            ${price_targets.average.toFixed(2)}
          </p>
          <div className="flex items-center gap-1 mt-1">
            {isUpside ? (
              <TrendingUp className="w-4 h-4 text-green-600" />
            ) : (
              <TrendingDown className="w-4 h-4 text-red-600" />
            )}
            <span className={`text-sm font-medium ${isUpside ? 'text-green-600' : 'text-red-600'}`}>
              {isUpside ? '+' : ''}{targetDiffPct}% {isUpside ? 'upside' : 'downside'}
            </span>
          </div>
        </div>

        <div className="border border-gray-300 p-5 bg-gray-50">
          <p className="text-sm text-gray-600 font-medium mb-2">Low Target</p>
          <p className="text-2xl font-bold text-black">${price_targets.low.toFixed(2)}</p>
        </div>

        <div className="border border-gray-300 p-5 bg-gray-50">
          <p className="text-sm text-gray-600 font-medium mb-2">High Target</p>
          <p className="text-2xl font-bold text-black">${price_targets.high.toFixed(2)}</p>
        </div>
      </div>

      {/* Current Consensus Breakdown */}
      <div>
        <h2 className="text-xl font-bold text-black mb-4 flex items-center gap-2">
          <Users className="w-5 h-5" />
          Current Consensus Breakdown
        </h2>
       
        <div className="border border-gray-300 p-6 bg-white">
          <div className="flex h-12 w-full mb-6 border border-gray-300 overflow-hidden rounded">
            {currentConsensus.breakdown_pct.strong_buy > 0 && (
              <div
                style={{ width: `${currentConsensus.breakdown_pct.strong_buy}%` }}
                className="bg-green-600 flex items-center justify-center text-white text-xs font-semibold"
              >
                {currentConsensus.breakdown_pct.strong_buy}%
              </div>
            )}
            {currentConsensus.breakdown_pct.buy > 0 && (
              <div
                style={{ width: `${currentConsensus.breakdown_pct.buy}%` }}
                className="bg-green-400 flex items-center justify-center text-white text-xs font-semibold"
              >
                {currentConsensus.breakdown_pct.buy}%
              </div>
            )}
            {currentConsensus.breakdown_pct.hold > 0 && (
              <div
                style={{ width: `${currentConsensus.breakdown_pct.hold}%` }}
                className="bg-gray-400 flex items-center justify-center text-white text-xs font-semibold"
              >
                {currentConsensus.breakdown_pct.hold}%
              </div>
            )}
            {currentConsensus.breakdown_pct.sell > 0 && (
              <div
                style={{ width: `${currentConsensus.breakdown_pct.sell}%` }}
                className="bg-red-400 flex items-center justify-center text-white text-xs font-semibold"
              >
                {currentConsensus.breakdown_pct.sell}%
              </div>
            )}
            {currentConsensus.breakdown_pct.strong_sell > 0 && (
              <div
                style={{ width: `${currentConsensus.breakdown_pct.strong_sell}%` }}
                className="bg-red-600 flex items-center justify-center text-white text-xs font-semibold"
              >
                {currentConsensus.breakdown_pct.strong_sell}%
              </div>
            )}
          </div>

          <div className="grid grid-cols-2 md:grid-cols-5 gap-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-600 border border-gray-300 rounded"></div>
              <div>
                <p className="text-xs text-gray-600">Strong Buy</p>
                <p className="text-sm font-bold text-green-700">{currentConsensus.breakdown_pct.strong_buy}%</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-green-400 border border-gray-300 rounded"></div>
              <div>
                <p className="text-xs text-gray-600">Buy</p>
                <p className="text-sm font-bold text-green-600">{currentConsensus.breakdown_pct.buy}%</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-gray-400 border border-gray-300 rounded"></div>
              <div>
                <p className="text-xs text-gray-600">Hold</p>
                <p className="text-sm font-bold text-gray-700">{currentConsensus.breakdown_pct.hold}%</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-400 border border-gray-300 rounded"></div>
              <div>
                <p className="text-xs text-gray-600">Sell</p>
                <p className="text-sm font-bold text-red-600">{currentConsensus.breakdown_pct.sell}%</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 bg-red-600 border border-gray-300 rounded"></div>
              <div>
                <p className="text-xs text-gray-600">Strong Sell</p>
                <p className="text-sm font-bold text-red-700">{currentConsensus.breakdown_pct.strong_sell}%</p>
              </div>
            </div>
          </div>

          <div className="mt-6 pt-6 border-t border-gray-200">
            <div className="grid grid-cols-3 gap-6">
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Bullish Sentiment</p>
                <p className="text-2xl font-bold text-green-600">{bullishPct}%</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Neutral</p>
                <p className="text-2xl font-bold text-gray-700">{currentConsensus.breakdown_pct.hold}%</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-gray-600 mb-1">Bearish Sentiment</p>
                <p className="text-2xl font-bold text-red-600">{bearishPct}%</p>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* GROWTH PROFILE SECTION */}
      {growth_profile && (
        <div>
          <h2 className="text-2xl font-bold text-black mb-6 flex items-center gap-2">
            <Activity className="w-6 h-6" />
            Growth Profile (Forward-Looking Fundamentals)
          </h2>

          {/* Growth Metrics Overview */}
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
            {/* Revenue Growth */}
            {growth_profile.revenue_growth && (
              <div className="border border-gray-300 bg-white p-5">
                <div className="flex items-center gap-2 mb-3">
                  <DollarSign className="w-5 h-5 text-blue-600" />
                  <h3 className="font-semibold text-black">Revenue Growth</h3>
                </div>
                <div className="space-y-2">
                  {growth_profile.revenue_growth.yoy_current !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">YoY Current:</span>
                      <span className={`font-bold ${growth_profile.revenue_growth.yoy_current >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(growth_profile.revenue_growth.yoy_current)}
                      </span>
                    </div>
                  )}
                  {growth_profile.revenue_growth.yoy_projected_next_year !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">YoY Projected:</span>
                      <span className={`font-bold ${growth_profile.revenue_growth.yoy_projected_next_year >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(growth_profile.revenue_growth.yoy_projected_next_year)}
                      </span>
                    </div>
                  )}
                  {growth_profile.revenue_growth.cagr_3_5_year !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">3-5Y CAGR:</span>
                      <span className={`font-bold ${growth_profile.revenue_growth.cagr_3_5_year >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(growth_profile.revenue_growth.cagr_3_5_year)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Earnings Growth */}
            {growth_profile.earnings_growth && (
              <div className="border border-gray-300 bg-white p-5">
                <div className="flex items-center gap-2 mb-3">
                  <TrendingUp className="w-5 h-5 text-green-600" />
                  <h3 className="font-semibold text-black">Earnings Growth</h3>
                </div>
                <div className="space-y-2">
                  {growth_profile.earnings_growth.yoy_current !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">YoY Current:</span>
                      <span className={`font-bold ${growth_profile.earnings_growth.yoy_current >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(growth_profile.earnings_growth.yoy_current)}
                      </span>
                    </div>
                  )}
                  {growth_profile.earnings_growth.yoy_projected_next_year !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">YoY Projected:</span>
                      <span className={`font-bold ${growth_profile.earnings_growth.yoy_projected_next_year >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                        {formatPercent(growth_profile.earnings_growth.yoy_projected_next_year)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Free Cash Flow Growth */}
            {growth_profile.free_cash_flow_growth && growth_profile.free_cash_flow_growth.yoy_current !== null && (
              <div className="border border-gray-300 bg-white p-5">
                <div className="flex items-center gap-2 mb-3">
                  <Zap className="w-5 h-5 text-purple-600" />
                  <h3 className="font-semibold text-black">Free Cash Flow</h3>
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-gray-600">YoY Growth:</span>
                    <span className={`font-bold ${growth_profile.free_cash_flow_growth.yoy_current >= 0 ? 'text-green-600' : 'text-red-600'}`}>
                      {formatPercent(growth_profile.free_cash_flow_growth.yoy_current)}
                    </span>
                  </div>
                  {growth_profile.free_cash_flow_growth.fcf_current !== null && (
                    <div className="flex justify-between items-center">
                      <span className="text-sm text-gray-600">Current FCF:</span>
                      <span className="font-bold text-black">
                        {formatCurrency(growth_profile.free_cash_flow_growth.fcf_current)}
                      </span>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Growth Comparison Chart */}
          {growthChartData.length > 0 && (
            <div className="border border-gray-300 p-6 bg-white mb-6">
              <h3 className="font-semibold text-black mb-4">Growth Rate Comparison</h3>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={growthChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
                  <XAxis dataKey="metric" stroke="#374151" style={{ fontSize: '13px', fontWeight: 500 }} tickLine={false} />
                  <YAxis stroke="#374151" style={{ fontSize: '13px', fontWeight: 500 }} tickLine={false} label={{ value: 'Growth (%)', angle: -90, position: 'insideLeft', style: { fill: '#374151', fontWeight: 500 } }} />
                  <Tooltip content={<GrowthTooltip />} />
                  <Legend wrapperStyle={{ fontSize: '13px', fontWeight: 500, paddingTop: '20px' }} iconType="circle" />
                  <Bar dataKey="current" name="Current YoY" fill="#3b82f6" radius={[4, 4, 0, 0]} />
                  <Bar dataKey="projected" name="Projected YoY" fill="#10b981" radius={[4, 4, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* Analyst Estimates */}
          {growth_profile.analyst_estimates && (
            <div>
              <h3 className="font-semibold text-black mb-4 text-lg">Analyst Estimates</h3>
              
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {/* Revenue Estimates */}
                <div className="border border-gray-300 bg-white p-5">
                  <h4 className="font-semibold text-black mb-4 flex items-center gap-2">
                    <DollarSign className="w-4 h-4 text-blue-600" />
                    Revenue Estimates
                  </h4>
                  <div className="space-y-3">
                    {growth_profile.analyst_estimates.revenue_next_quarter !== null && (
                      <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                        <span className="text-sm text-gray-600">Next Quarter</span>
                        <span className="font-bold text-black">{formatCurrency(growth_profile.analyst_estimates.revenue_next_quarter)}</span>
                      </div>
                    )}
                    {growth_profile.analyst_estimates.revenue_current_year !== null && (
                      <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                        <span className="text-sm text-gray-600">Current Year</span>
                        <span className="font-bold text-black">{formatCurrency(growth_profile.analyst_estimates.revenue_current_year)}</span>
                      </div>
                    )}
                    {growth_profile.analyst_estimates.revenue_next_year !== null && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Next Year</span>
                        <span className="font-bold text-black">{formatCurrency(growth_profile.analyst_estimates.revenue_next_year)}</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* EPS Estimates */}
                <div className="border border-gray-300 bg-white p-5">
                  <h4 className="font-semibold text-black mb-4 flex items-center gap-2">
                    <TrendingUp className="w-4 h-4 text-green-600" />
                    EPS Estimates
                  </h4>
                  <div className="space-y-3">
                    {growth_profile.analyst_estimates.eps_next_quarter !== null && (
                      <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                        <span className="text-sm text-gray-600">Next Quarter</span>
                        <span className="font-bold text-black">${growth_profile.analyst_estimates.eps_next_quarter.toFixed(2)}</span>
                      </div>
                    )}
                    {growth_profile.analyst_estimates.eps_current_year !== null && (
                      <div className="flex justify-between items-center pb-2 border-b border-gray-200">
                        <span className="text-sm text-gray-600">Current Year</span>
                        <span className="font-bold text-black">${growth_profile.analyst_estimates.eps_current_year.toFixed(2)}</span>
                      </div>
                    )}
                    {growth_profile.analyst_estimates.eps_next_year !== null && (
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-gray-600">Next Year</span>
                        <span className="font-bold text-black">${growth_profile.analyst_estimates.eps_next_year.toFixed(2)}</span>
                      </div>
                    )}
                  </div>
                </div>
              </div>

              {/* Long-term Growth & PEG */}
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mt-4">
                {growth_profile.analyst_estimates.growth_next_5_years !== null && (
                  <div className="border-2 border-blue-600 bg-blue-50 p-5">
                    <p className="text-sm text-blue-700 font-medium mb-2">5-Year Growth Rate (Analyst Est.)</p>
                    <p className="text-3xl font-bold text-blue-700">{formatPercent(growth_profile.analyst_estimates.growth_next_5_years)}</p>
                  </div>
                )}
                {growth_profile.analyst_estimates.peg_ratio !== null && (
                  <div className="border border-gray-300 bg-gray-50 p-5">
                    <p className="text-sm text-gray-600 font-medium mb-2">PEG Ratio</p>
                    <p className="text-3xl font-bold text-black">{growth_profile.analyst_estimates.peg_ratio.toFixed(2)}</p>
                    <p className="text-xs text-gray-500 mt-1">Price/Earnings to Growth</p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      )}

      {/* Earnings Outlook */}
      {earnings_outlook && earnings_outlook.next_quarter_eps_avg && (
        <div>
          <h2 className="text-xl font-bold text-black mb-4">Earnings Outlook</h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="border border-gray-300 p-5 bg-gray-50">
              <p className="text-sm text-gray-600 font-medium mb-2">Next Quarter EPS (Avg)</p>
              <p className="text-2xl font-bold text-black">${earnings_outlook.next_quarter_eps_avg.toFixed(2)}</p>
            </div>
           
            {earnings_outlook.next_quarter_revenue_avg && (
              <div className="border border-gray-300 p-5 bg-gray-50">
                <p className="text-sm text-gray-600 font-medium mb-2">Next Quarter Revenue (Avg)</p>
                <p className="text-2xl font-bold text-black">
                  {formatCurrency(earnings_outlook.next_quarter_revenue_avg)}
                </p>
              </div>
            )}
           
            {earnings_outlook.next_quarter_growth_avg !== null && earnings_outlook.next_quarter_growth_avg !== undefined && (
              <div className={`border-2 p-5 ${earnings_outlook.next_quarter_growth_avg >= 0 ? 'border-green-600 bg-green-50' : 'border-red-600 bg-red-50'}`}>
                <p className={`text-sm font-medium mb-2 ${earnings_outlook.next_quarter_growth_avg >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                  Expected Growth
                </p>
                <div className="flex items-center gap-2">
                  <p className={`text-2xl font-bold ${earnings_outlook.next_quarter_growth_avg >= 0 ? 'text-green-700' : 'text-red-700'}`}>
                    {formatPercent(earnings_outlook.next_quarter_growth_avg, 2)}
                  </p>
                  {earnings_outlook.next_quarter_growth_avg >= 0 ? (
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  ) : (
                    <TrendingDown className="w-5 h-5 text-red-600" />
                  )}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* Historical Ratings Chart */}
      <div>
        <h2 className="text-xl font-bold text-black mb-4">Rating History (Past 3 Months)</h2>
        <div className="border border-gray-300 p-6 bg-white">
          <ResponsiveContainer width="100%" height={400}>
            <BarChart
              data={chartData}
              margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
            >
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" vertical={false} />
              <XAxis
                dataKey="period"
                stroke="#374151"
                style={{ fontSize: '13px', fontWeight: 500 }}
                tickLine={false}
              />
              <YAxis
                stroke="#374151"
                style={{ fontSize: '13px', fontWeight: 500 }}
                label={{
                  value: 'Percentage (%)',
                  angle: -90,
                  position: 'insideLeft',
                  style: { fill: '#374151', fontWeight: 500 }
                }}
                tickLine={false}
              />
              <Tooltip content={<CustomTooltip />} />
              <Legend
                wrapperStyle={{ fontSize: '13px', fontWeight: 500, paddingTop: '20px' }}
                iconType="circle"
              />
              <Bar
                dataKey="strongBuy"
                name="Strong Buy"
                fill="#16a34a"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="buy"
                name="Buy"
                fill="#4ade80"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="hold"
                name="Hold"
                fill="#9ca3af"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="sell"
                name="Sell"
                fill="#f87171"
                radius={[4, 4, 0, 0]}
              />
              <Bar
                dataKey="strongSell"
                name="Strong Sell"
                fill="#dc2626"
                radius={[4, 4, 0, 0]}
              />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
};