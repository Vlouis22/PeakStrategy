import React from 'react';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { TrendingUp, TrendingDown, Users, Target, DollarSign, Activity, Zap } from 'lucide-react';

export const AnalystConsensus = ({ consensusData }) => {
  if (!consensusData || !consensusData.data_available) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600">No analyst consensus data available.</p>
          </div>
        </div>
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
        <div className="bg-white border border-slate-200 p-3 shadow-lg rounded-lg">
          <p className="font-semibold text-slate-900 mb-2 text-sm">{label}</p>
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
        <div className="bg-white border border-slate-200 p-3 shadow-lg rounded-lg">
          <p className="font-semibold text-slate-900 mb-2 text-sm">{label}</p>
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

  const ContentSection = ({ children, delay = 0 }) => (
    <div 
      className="opacity-0 animate-fade-in"
      style={{ animationDelay: `${delay}s`, animationFillMode: 'forwards' }}
    >
      {children}
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <style>{`
        @keyframes fade-in {
          from {
            opacity: 0;
            transform: translateY(10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }
        
        .animate-fade-in {
          animation: fade-in 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
      `}</style>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        
        {/* Header */}
        <div className="mb-14 relative opacity-0 animate-fade-in" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-2">
            Analyst Ratings
          </h1>
          <p className="text-slate-600 text-sm mt-1 flex items-center gap-2">
            <span className="font-semibold text-slate-900">{ticker}</span>
            <span>•</span>
            <span>{currentConsensus.total_analysts} Analysts</span>
          </p>
        </div>

        {/* Price Targets Section */}
        <ContentSection delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-16">
            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-2 mb-2">
                <Target className="w-4 h-4 text-slate-400" />
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Current Price</p>
              </div>
              <p className="text-2xl font-bold text-slate-900">${price_targets.current_price.toFixed(2)}</p>
            </div>

            <div className={`border-2 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300 ${
              isUpside ? 'border-emerald-300 bg-emerald-50' : 'border-red-300 bg-red-50'
            }`}>
              <div className="flex items-center gap-2 mb-2">
                <Target className={`w-4 h-4 ${isUpside ? 'text-emerald-600' : 'text-red-600'}`} />
                <p className={`text-xs font-semibold uppercase tracking-wide ${isUpside ? 'text-emerald-700' : 'text-red-700'}`}>Average Target</p>
              </div>
              <p className={`text-2xl font-bold ${isUpside ? 'text-emerald-700' : 'text-red-700'}`}>
                ${price_targets.average.toFixed(2)}
              </p>
              <div className="flex items-center gap-1 mt-2">
                {isUpside ? (
                  <TrendingUp className="w-4 h-4 text-emerald-600" />
                ) : (
                  <TrendingDown className="w-4 h-4 text-red-600" />
                )}
                <span className={`text-sm font-semibold ${isUpside ? 'text-emerald-600' : 'text-red-600'}`}>
                  {isUpside ? '+' : ''}{targetDiffPct}% {isUpside ? 'upside' : 'downside'}
                </span>
              </div>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Low Target</p>
              <p className="text-2xl font-bold text-slate-900">${price_targets.low.toFixed(2)}</p>
            </div>

            <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
              <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">High Target</p>
              <p className="text-2xl font-bold text-slate-900">${price_targets.high.toFixed(2)}</p>
            </div>
          </div>
        </ContentSection>

        {/* Current Consensus Breakdown */}
        <ContentSection delay={0.3}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Users className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Current Consensus Breakdown</h2>
            </div>
           
            <div className="flex h-12 w-full mb-6 border border-slate-200 overflow-hidden rounded-lg shadow-sm">
              {currentConsensus.breakdown_pct.strong_buy > 0 && (
                <div
                  style={{ width: `${currentConsensus.breakdown_pct.strong_buy}%` }}
                  className="bg-emerald-600 flex items-center justify-center text-white text-xs font-bold"
                >
                  {currentConsensus.breakdown_pct.strong_buy}%
                </div>
              )}
              {currentConsensus.breakdown_pct.buy > 0 && (
                <div
                  style={{ width: `${currentConsensus.breakdown_pct.buy}%` }}
                  className="bg-emerald-400 flex items-center justify-center text-white text-xs font-bold"
                >
                  {currentConsensus.breakdown_pct.buy}%
                </div>
              )}
              {currentConsensus.breakdown_pct.hold > 0 && (
                <div
                  style={{ width: `${currentConsensus.breakdown_pct.hold}%` }}
                  className="bg-slate-400 flex items-center justify-center text-white text-xs font-bold"
                >
                  {currentConsensus.breakdown_pct.hold}%
                </div>
              )}
              {currentConsensus.breakdown_pct.sell > 0 && (
                <div
                  style={{ width: `${currentConsensus.breakdown_pct.sell}%` }}
                  className="bg-red-400 flex items-center justify-center text-white text-xs font-bold"
                >
                  {currentConsensus.breakdown_pct.sell}%
                </div>
              )}
              {currentConsensus.breakdown_pct.strong_sell > 0 && (
                <div
                  style={{ width: `${currentConsensus.breakdown_pct.strong_sell}%` }}
                  className="bg-red-600 flex items-center justify-center text-white text-xs font-bold"
                >
                  {currentConsensus.breakdown_pct.strong_sell}%
                </div>
              )}
            </div>

            <div className="grid grid-cols-2 md:grid-cols-5 gap-4 mb-6">
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-emerald-600 border border-slate-200 rounded flex-shrink-0"></div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Strong Buy</p>
                  <p className="text-sm font-bold text-emerald-700">{currentConsensus.breakdown_pct.strong_buy}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-emerald-400 border border-slate-200 rounded flex-shrink-0"></div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Buy</p>
                  <p className="text-sm font-bold text-emerald-600">{currentConsensus.breakdown_pct.buy}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-slate-400 border border-slate-200 rounded flex-shrink-0"></div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Hold</p>
                  <p className="text-sm font-bold text-slate-700">{currentConsensus.breakdown_pct.hold}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-400 border border-slate-200 rounded flex-shrink-0"></div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Sell</p>
                  <p className="text-sm font-bold text-red-600">{currentConsensus.breakdown_pct.sell}%</p>
                </div>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-4 h-4 bg-red-600 border border-slate-200 rounded flex-shrink-0"></div>
                <div>
                  <p className="text-xs text-slate-500 font-medium">Strong Sell</p>
                  <p className="text-sm font-bold text-red-700">{currentConsensus.breakdown_pct.strong_sell}%</p>
                </div>
              </div>
            </div>

            <div className="pt-6 border-t border-slate-200">
              <div className="grid grid-cols-3 gap-6">
                <div className="text-center">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Bullish Sentiment</p>
                  <p className="text-2xl font-bold text-emerald-600">{bullishPct}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Neutral</p>
                  <p className="text-2xl font-bold text-slate-700">{currentConsensus.breakdown_pct.hold}%</p>
                </div>
                <div className="text-center">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-1">Bearish Sentiment</p>
                  <p className="text-2xl font-bold text-red-600">{bearishPct}%</p>
                </div>
              </div>
            </div>
          </div>
        </ContentSection>

        {/* GROWTH PROFILE SECTION */}
        {growth_profile && (
          <ContentSection delay={0.4}>
            <div className="mb-16">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Activity className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Growth Profile</h2>
              </div>

              {/* Growth Metrics Overview */}
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
                {/* Revenue Growth */}
                {growth_profile.revenue_growth && (
                  <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-2 mb-3">
                      <DollarSign className="w-5 h-5 text-blue-600" />
                      <h3 className="font-semibold text-slate-900">Revenue Growth</h3>
                    </div>
                    <div className="space-y-2">
                      {growth_profile.revenue_growth.yoy_current !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">YoY Current:</span>
                          <span className={`font-bold ${growth_profile.revenue_growth.yoy_current >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {formatPercent(growth_profile.revenue_growth.yoy_current)}
                          </span>
                        </div>
                      )}
                      {growth_profile.revenue_growth.yoy_projected_next_year !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">YoY Projected:</span>
                          <span className={`font-bold ${growth_profile.revenue_growth.yoy_projected_next_year >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {formatPercent(growth_profile.revenue_growth.yoy_projected_next_year)}
                          </span>
                        </div>
                      )}
                      {growth_profile.revenue_growth.cagr_3_5_year !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">3-5Y CAGR:</span>
                          <span className={`font-bold ${growth_profile.revenue_growth.cagr_3_5_year >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {formatPercent(growth_profile.revenue_growth.cagr_3_5_year)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Earnings Growth */}
                {growth_profile.earnings_growth && (
                  <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-2 mb-3">
                      <TrendingUp className="w-5 h-5 text-emerald-600" />
                      <h3 className="font-semibold text-slate-900">Earnings Growth</h3>
                    </div>
                    <div className="space-y-2">
                      {growth_profile.earnings_growth.yoy_current !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">YoY Current:</span>
                          <span className={`font-bold ${growth_profile.earnings_growth.yoy_current >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {formatPercent(growth_profile.earnings_growth.yoy_current)}
                          </span>
                        </div>
                      )}
                      {growth_profile.earnings_growth.yoy_projected_next_year !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">YoY Projected:</span>
                          <span className={`font-bold ${growth_profile.earnings_growth.yoy_projected_next_year >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                            {formatPercent(growth_profile.earnings_growth.yoy_projected_next_year)}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {/* Free Cash Flow Growth */}
                {growth_profile.free_cash_flow_growth && growth_profile.free_cash_flow_growth.yoy_current !== null && (
                  <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                    <div className="flex items-center gap-2 mb-3">
                      <Zap className="w-5 h-5 text-purple-600" />
                      <h3 className="font-semibold text-slate-900">Free Cash Flow</h3>
                    </div>
                    <div className="space-y-2">
                      <div className="flex justify-between items-center">
                        <span className="text-sm text-slate-600">YoY Growth:</span>
                        <span className={`font-bold ${growth_profile.free_cash_flow_growth.yoy_current >= 0 ? 'text-emerald-600' : 'text-red-600'}`}>
                          {formatPercent(growth_profile.free_cash_flow_growth.yoy_current)}
                        </span>
                      </div>
                      {growth_profile.free_cash_flow_growth.fcf_current !== null && (
                        <div className="flex justify-between items-center">
                          <span className="text-sm text-slate-600">Current FCF:</span>
                          <span className="font-bold text-slate-900">
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
                <div className="bg-white border border-slate-200 rounded-lg p-6 shadow-sm hover:shadow-md transition-shadow duration-300 mb-6">
                  <h3 className="font-semibold text-slate-900 mb-4">Growth Rate Comparison</h3>
                  <ResponsiveContainer width="100%" height={300}>
                    <BarChart data={growthChartData} margin={{ top: 20, right: 30, left: 20, bottom: 5 }}>
                      <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                      <XAxis dataKey="metric" stroke="#64748b" style={{ fontSize: '13px', fontWeight: 500 }} tickLine={false} />
                      <YAxis stroke="#64748b" style={{ fontSize: '13px', fontWeight: 500 }} tickLine={false} label={{ value: 'Growth (%)', angle: -90, position: 'insideLeft', style: { fill: '#64748b', fontWeight: 500 } }} />
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
                  <h3 className="font-semibold text-slate-900 mb-4 text-base">Analyst Estimates</h3>
                  
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-6">
                    {/* Revenue Estimates */}
                    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                      <h4 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <DollarSign className="w-4 h-4 text-blue-600" />
                        Revenue Estimates
                      </h4>
                      <div className="space-y-3">
                        {growth_profile.analyst_estimates.revenue_next_quarter !== null && (
                          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                            <span className="text-sm text-slate-600">Next Quarter</span>
                            <span className="font-bold text-slate-900">{formatCurrency(growth_profile.analyst_estimates.revenue_next_quarter)}</span>
                          </div>
                        )}
                        {growth_profile.analyst_estimates.revenue_current_year !== null && (
                          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                            <span className="text-sm text-slate-600">Current Year</span>
                            <span className="font-bold text-slate-900">{formatCurrency(growth_profile.analyst_estimates.revenue_current_year)}</span>
                          </div>
                        )}
                        {growth_profile.analyst_estimates.revenue_next_year !== null && (
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Next Year</span>
                            <span className="font-bold text-slate-900">{formatCurrency(growth_profile.analyst_estimates.revenue_next_year)}</span>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* EPS Estimates */}
                    <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                      <h4 className="font-semibold text-slate-900 mb-4 flex items-center gap-2">
                        <TrendingUp className="w-4 h-4 text-emerald-600" />
                        EPS Estimates
                      </h4>
                      <div className="space-y-3">
                        {growth_profile.analyst_estimates.eps_next_quarter !== null && (
                          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                            <span className="text-sm text-slate-600">Next Quarter</span>
                            <span className="font-bold text-slate-900">${growth_profile.analyst_estimates.eps_next_quarter.toFixed(2)}</span>
                          </div>
                        )}
                        {growth_profile.analyst_estimates.eps_current_year !== null && (
                          <div className="flex justify-between items-center pb-2 border-b border-slate-200">
                            <span className="text-sm text-slate-600">Current Year</span>
                            <span className="font-bold text-slate-900">${growth_profile.analyst_estimates.eps_current_year.toFixed(2)}</span>
                          </div>
                        )}
                        {growth_profile.analyst_estimates.eps_next_year !== null && (
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-slate-600">Next Year</span>
                            <span className="font-bold text-slate-900">${growth_profile.analyst_estimates.eps_next_year.toFixed(2)}</span>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>

                  {/* Long-term Growth & PEG */}
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {growth_profile.analyst_estimates.growth_next_5_years !== null && (
                      <div className="border-2 border-blue-300 bg-blue-50 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                        <p className="text-xs text-blue-700 font-semibold uppercase tracking-wide mb-2">5-Year Growth Rate (Analyst Est.)</p>
                        <p className="text-3xl font-bold text-blue-700">{formatPercent(growth_profile.analyst_estimates.growth_next_5_years)}</p>
                      </div>
                    )}
                    {growth_profile.analyst_estimates.peg_ratio !== null && (
                      <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                        <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-2">PEG Ratio</p>
                        <p className="text-3xl font-bold text-slate-900">{growth_profile.analyst_estimates.peg_ratio.toFixed(2)}</p>
                        <p className="text-xs text-slate-500 mt-1">Price/Earnings to Growth</p>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </ContentSection>
        )}

        {/* Earnings Outlook */}
        {earnings_outlook && earnings_outlook.next_quarter_eps_avg && (
          <ContentSection delay={0.5}>
            <div className="mb-16">
              <h2 className="text-xl font-bold text-slate-900 mb-4">Earnings Outlook</h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
                <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Next Quarter EPS (Avg)</p>
                  <p className="text-2xl font-bold text-slate-900">${earnings_outlook.next_quarter_eps_avg.toFixed(2)}</p>
                </div>
               
                {earnings_outlook.next_quarter_revenue_avg && (
                  <div className="bg-white border border-slate-200 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300">
                    <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Next Quarter Revenue (Avg)</p>
                    <p className="text-2xl font-bold text-slate-900">
                      {formatCurrency(earnings_outlook.next_quarter_revenue_avg)}
                    </p>
                  </div>
                )}
               
                {earnings_outlook.next_quarter_growth_avg !== null && earnings_outlook.next_quarter_growth_avg !== undefined && (
                  <div className={`border-2 rounded-lg p-5 shadow-sm hover:shadow-md transition-shadow duration-300 ${
                    earnings_outlook.next_quarter_growth_avg >= 0 ? 'border-emerald-300 bg-emerald-50' : 'border-red-300 bg-red-50'
                  }`}>
                    <p className={`text-xs font-semibold uppercase tracking-wide mb-2 ${
                      earnings_outlook.next_quarter_growth_avg >= 0 ? 'text-emerald-700' : 'text-red-700'
                    }`}>
                      Expected Growth
                    </p>
                    <div className="flex items-center gap-2">
                      <p className={`text-2xl font-bold ${
                        earnings_outlook.next_quarter_growth_avg >= 0 ? 'text-emerald-700' : 'text-red-700'
                      }`}>
                        {formatPercent(earnings_outlook.next_quarter_growth_avg, 2)}
                      </p>
                      {earnings_outlook.next_quarter_growth_avg >= 0 ? (
                        <TrendingUp className="w-5 h-5 text-emerald-600" />
                      ) : (
                        <TrendingDown className="w-5 h-5 text-red-600" />
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ContentSection>
        )}

        {/* Historical Ratings Chart */}
        <ContentSection delay={0.6}>
          <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <h2 className="text-xl font-bold text-slate-900 mb-6">Rating History (Past 3 Months)</h2>
            <ResponsiveContainer width="100%" height={400}>
              <BarChart
                data={chartData}
                margin={{ top: 20, right: 30, left: 20, bottom: 5 }}
              >
                <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" vertical={false} />
                <XAxis
                  dataKey="period"
                  stroke="#64748b"
                  style={{ fontSize: '13px', fontWeight: 500 }}
                  tickLine={false}
                />
                <YAxis
                  stroke="#64748b"
                  style={{ fontSize: '13px', fontWeight: 500 }}
                  label={{
                    value: 'Percentage (%)',
                    angle: -90,
                    position: 'insideLeft',
                    style: { fill: '#64748b', fontWeight: 500 }
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
        </ContentSection>

      </div>
    </div>
  );
};