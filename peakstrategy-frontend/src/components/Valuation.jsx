import React, { useState } from 'react';
import { TrendingUp, TrendingDown, Minus, DollarSign, BarChart3, Activity, Info } from 'lucide-react';

export const Valuation = ({ valuationData }) => {
  const [showPeerTooltip, setShowPeerTooltip] = useState(false);

  if (!valuationData) {
    return (
      <div className="bg-white text-black p-8 rounded-lg border border-gray-300">
        <p className="text-gray-600">No valuation data available</p>
      </div>
    );
  } 

  if (valuationData) {
    console.log('Valuation Data:', valuationData);
  }

  const getValueColor = (value, type = 'pe') => {
    if (value === null || value === undefined) return 'text-gray-600';
    
    switch(type) {
      case 'pe':
        if (value < 15) return 'text-green-600';
        if (value < 25) return 'text-gray-700';
        return 'text-red-600';
      case 'peg':
        if (value < 1) return 'text-green-600';
        if (value < 2) return 'text-gray-700';
        return 'text-red-600';
      case 'percent':
        if (value > 0) return 'text-green-600';
        if (value > -10) return 'text-gray-700';
        return 'text-red-600';
      case 'score':
        if (value >= 7) return 'text-green-600';
        if (value >= 5) return 'text-gray-700';
        return 'text-red-600';
      default:
        return 'text-gray-700';
    }
  };

  const getVerdictStyle = (verdict) => {
    switch(verdict) {
      case 'Undervalued':
        return 'bg-green-100 text-green-700 border-green-300';
      case 'Fairly Valued':
        return 'bg-gray-100 text-gray-700 border-gray-300';
      case 'Overvalued':
        return 'bg-red-100 text-red-700 border-red-300';
      default:
        return 'bg-gray-100 text-gray-700 border-gray-300';
    }
  };

  const formatNumber = (num, decimals = 2) => {
    if (num === null || num === undefined) return 'N/A';
    if (typeof num === 'number') {
      return num.toFixed(decimals);
    }
    return num;
  };

  const formatLargeNumber = (num) => {
    if (!num) return 'N/A';
    if (num >= 1e12) return `$${(num / 1e12).toFixed(2)}T`;
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${num.toFixed(2)}`;
  };

  const { overview, relativeMetrics, absoluteContext, businessSize, peerComparison, growthMetrics, interpretation, scorecard } = valuationData;

  // Get peer information for tooltip
  const peerCount = peerComparison?.peerGroupAvg?.peerCount || 0;
  const peers = peerComparison?.peerGroupAvg?.peers || [];
  const peerTooltipText = peerCount > 0 
    ? `Average of ${peerCount} representative peer${peerCount > 1 ? 's' : ''} in the same sector (${peers.join(', ')}) using Yahoo Finance data`
    : 'Average of 3–5 representative peers in the same sector using Yahoo Finance data';

  return (
    <div className="bg-white text-black p-8">
      <div className="max-w-7xl mx-auto space-y-8">

        {/* 1. Valuation Overview */}
        <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
          <h2 className="text-2xl font-bold mb-6 flex items-center text-black">
            <DollarSign className="mr-2" />
            Valuation Overview
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <p className="text-gray-600 text-sm mb-2">Current Price</p>
              <p className="text-3xl font-bold text-black">${formatNumber(overview.currentPrice)}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm mb-2">Market Cap</p>
              <p className="text-3xl font-bold text-black">{formatLargeNumber(overview.marketCap)}</p>
            </div>
            <div>
              <p className="text-gray-600 text-sm mb-2">Valuation Verdict</p>
              <div className={`inline-block px-4 py-2 rounded-lg border ${getVerdictStyle(scorecard.verdict)}`}>
                <p className="text-xl font-bold">{scorecard.verdict}</p>
              </div>
            </div>
          </div>
        </div>

        {/* 2. Relative Valuation Metrics */}
        <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
          <h2 className="text-2xl font-bold mb-6 flex items-center text-black">
            <BarChart3 className="mr-2" />
            Valuation Metrics
          </h2>
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-gray-300">
                  <th className="text-left py-3 px-4 text-gray-600 font-semibold">Metric</th>
                  <th className="text-right py-3 px-4 text-gray-600 font-semibold">Value</th>
                  <th className="text-left py-3 px-4 text-gray-600 font-semibold">Interpretation</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-gray-200">
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">P/E (TTM)</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.trailingPE, 'pe')}`}>
                    {formatNumber(relativeMetrics.trailingPE)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Price per $1 of current earnings</td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">P/E (Forward)</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.forwardPE, 'pe')}`}>
                    {formatNumber(relativeMetrics.forwardPE)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Market expectation of future earnings</td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">PEG Ratio</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.pegRatio, 'peg')}`}>
                    {formatNumber(relativeMetrics.pegRatio)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Growth-adjusted valuation</td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">EV / EBITDA</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.enterpriseToEbitda, 'pe')}`}>
                    {formatNumber(relativeMetrics.enterpriseToEbitda)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Capital-structure neutral valuation</td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">Price / Sales</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg text-gray-700`}>
                    {formatNumber(relativeMetrics.priceToSalesTrailing)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Useful for unprofitable companies</td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">Price / Book</td>
                  <td className={`text-right py-4 px-4 font-bold text-lg text-gray-700`}>
                    {formatNumber(relativeMetrics.priceToBook)}
                  </td>
                  <td className="py-4 px-4 text-gray-600">Asset-based valuation</td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 3. Absolute Valuation Context */}
        <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
          <h2 className="text-2xl font-bold mb-6 flex items-center text-black">
            <Activity className="mr-2" />
            Price Positioning
          </h2>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-700">52-Week Range</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Current Price</span>
                  <span className="text-xl font-bold text-black">${formatNumber(absoluteContext.currentPrice)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">52-Week High</span>
                  <span className="font-semibold text-black">${formatNumber(absoluteContext.fiftyTwoWeekHigh)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">52-Week Low</span>
                  <span className="font-semibold text-black">${formatNumber(absoluteContext.fiftyTwoWeekLow)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">% from High</span>
                  <span className={`font-bold ${getValueColor(absoluteContext.percentFromHigh, 'percent')}`}>
                    {formatNumber(absoluteContext.percentFromHigh)}%
                  </span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">% from Low</span>
                  <span className={`font-bold ${getValueColor(absoluteContext.percentFromLow, 'percent')}`}>
                    {formatNumber(absoluteContext.percentFromLow)}%
                  </span>
                </div>
              </div>
            </div>
            <div>
              <h3 className="text-lg font-semibold mb-4 text-gray-700">Market Cap vs Revenue</h3>
              <div className="space-y-4">
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Market Cap</span>
                  <span className="font-bold text-black">{formatLargeNumber(businessSize.marketCap)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">TTM Revenue</span>
                  <span className="font-bold text-black">{formatLargeNumber(businessSize.trailingRevenue)}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-gray-600">Market Cap / Revenue</span>
                  <span className="font-bold text-lg text-black">{formatNumber(businessSize.marketCapToRevenue)}x</span>
                </div>
              </div>
            </div>
          </div>
        </div>
        {/* 4. Peer Comparison */}
        <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
        <h2 className="text-2xl font-bold mb-6 text-black">Peer & Market Comparisons</h2>
        <div className="overflow-x-auto">
            <table className="w-full">
            <thead>
                <tr className="border-b border-gray-300">
                <th className="text-left py-3 px-4 text-gray-600 font-semibold">Metric</th>
                <th className="text-right py-3 px-4 text-gray-600 font-semibold">This Stock</th>
                <th className="text-right py-3 px-4 text-gray-600 font-semibold">
                    <div className="flex items-center justify-end gap-1 relative">
                    <span>Peer Group Avg</span>
                    <div className="relative">
                        <Info 
                        size={16} 
                        className="text-gray-500 cursor-help hover:text-gray-700"
                        onClick={() => setShowPeerTooltip(!showPeerTooltip)}
                        onMouseEnter={() => setShowPeerTooltip(true)}
                        onMouseLeave={() => setShowPeerTooltip(false)}
                        />
                        {/* Tooltip that appears below on click/hover */}
                        {showPeerTooltip && (
                        <div className="absolute z-50 right-0 top-full mt-2 w-80 p-3 bg-gray-900 text-white text-sm rounded-lg shadow-xl">
                            <div className="relative">
                            {peerTooltipText}
                            {/* Arrow pointing up to icon */}
                            <div className="absolute -top-2 right-3 w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent border-b-gray-900"></div>
                            </div>
                        </div>
                        )}
                    </div>
                    </div>
                </th>
                <th className="text-right py-3 px-4 text-gray-600 font-semibold">S&P 500</th>
                </tr>
            </thead>
              <tbody className="divide-y divide-gray-200">
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">P/E Ratio</td>
                  <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.pe, 'pe')}`}>
                    {formatNumber(peerComparison.thisStock.pe)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.peerGroupAvg?.pe)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.sp500Avg.pe)}
                  </td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">Forward P/E</td>
                  <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.forwardPE, 'pe')}`}>
                    {formatNumber(peerComparison.thisStock.forwardPE)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.peerGroupAvg?.forwardPE)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.sp500Avg.forwardPE)}
                  </td>
                </tr>
                <tr className="hover:bg-gray-50 transition-colors">
                  <td className="py-4 px-4 text-black">PEG Ratio</td>
                  <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.peg, 'peg')}`}>
                    {formatNumber(peerComparison.thisStock.peg)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.peerGroupAvg?.peg)}
                  </td>
                  <td className="text-right py-4 px-4 text-gray-700">
                    {formatNumber(peerComparison.sp500Avg.peg)}
                  </td>
                </tr>
              </tbody>
            </table>
          </div>
        </div>

        {/* 5. Growth Metrics */}
        {growthMetrics && (
          <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
            <h2 className="text-2xl font-bold mb-6 text-black">Growth-Adjusted Valuation</h2>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-gray-600 text-sm mb-2">Expected EPS Growth</p>
                <p className={`text-2xl font-bold ${getValueColor(growthMetrics.expectedEPSGrowth ? growthMetrics.expectedEPSGrowth * 100 : 0, 'percent')}`}>
                  {growthMetrics.expectedEPSGrowth ? `${(growthMetrics.expectedEPSGrowth * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-gray-600 text-sm mb-2">Expected Revenue Growth</p>
                <p className={`text-2xl font-bold ${getValueColor(growthMetrics.expectedRevenueGrowth ? growthMetrics.expectedRevenueGrowth * 100 : 0, 'percent')}`}>
                  {growthMetrics.expectedRevenueGrowth ? `${(growthMetrics.expectedRevenueGrowth * 100).toFixed(1)}%` : 'N/A'}
                </p>
              </div>
              <div>
                <p className="text-gray-600 text-sm mb-2">PEG Interpretation</p>
                <p className="text-lg font-semibold text-gray-700">{growthMetrics.pegInterpretation}</p>
              </div>
            </div>
          </div>
        )}

        {/* 6. Valuation Insights */}
        {interpretation && interpretation.length > 0 && (
          <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
            <h2 className="text-2xl font-bold mb-6 text-black">Key Insights</h2>
            <div className="space-y-3">
              {interpretation.map((insight, idx) => (
                <div 
                  key={idx} 
                  className={`flex items-start p-4 rounded-lg border ${
                    insight.type === 'positive' ? 'bg-green-50 border-green-300' :
                    insight.type === 'negative' ? 'bg-red-50 border-red-300' :
                    'bg-gray-50 border-gray-300'
                  }`}
                >
                  {insight.type === 'positive' ? (
                    <TrendingUp className="text-green-600 mr-3 mt-1 flex-shrink-0" size={20} />
                  ) : insight.type === 'negative' ? (
                    <TrendingDown className="text-red-600 mr-3 mt-1 flex-shrink-0" size={20} />
                  ) : (
                    <Minus className="text-gray-600 mr-3 mt-1 flex-shrink-0" size={20} />
                  )}
                  <p className="text-gray-700">{insight.message}</p>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* 7. Valuation Scorecard */}
        <div className="bg-white rounded-lg p-6 border border-gray-300 shadow-sm">
          <h2 className="text-2xl font-bold mb-6 text-black">Valuation Scorecard</h2>
          <div className="space-y-4">
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Earnings Valuation</span>
              <div className="flex items-center">
                <div className="w-48 bg-gray-200 rounded-full h-3 mr-4">
                  <div 
                    className={`h-3 rounded-full ${scorecard.componentScores.earningsValuation >= 7 ? 'bg-green-500' : scorecard.componentScores.earningsValuation >= 5 ? 'bg-gray-500' : 'bg-red-500'}`}
                    style={{width: `${scorecard.componentScores.earningsValuation * 10}%`}}
                  ></div>
                </div>
                <span className={`font-bold text-lg ${getValueColor(scorecard.componentScores.earningsValuation, 'score')}`}>
                  {scorecard.componentScores.earningsValuation} / 10
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Growth-Adjusted Valuation</span>
              <div className="flex items-center">
                <div className="w-48 bg-gray-200 rounded-full h-3 mr-4">
                  <div 
                    className={`h-3 rounded-full ${scorecard.componentScores.growthAdjusted >= 7 ? 'bg-green-500' : scorecard.componentScores.growthAdjusted >= 5 ? 'bg-gray-500' : 'bg-red-500'}`}
                    style={{width: `${scorecard.componentScores.growthAdjusted * 10}%`}}
                  ></div>
                </div>
                <span className={`font-bold text-lg ${getValueColor(scorecard.componentScores.growthAdjusted, 'score')}`}>
                  {scorecard.componentScores.growthAdjusted} / 10
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Peer Comparison</span>
              <div className="flex items-center">
                <div className="w-48 bg-gray-200 rounded-full h-3 mr-4">
                  <div 
                    className={`h-3 rounded-full ${scorecard.componentScores.peerComparison >= 7 ? 'bg-green-500' : scorecard.componentScores.peerComparison >= 5 ? 'bg-gray-500' : 'bg-red-500'}`}
                    style={{width: `${scorecard.componentScores.peerComparison * 10}%`}}
                  ></div>
                </div>
                <span className={`font-bold text-lg ${getValueColor(scorecard.componentScores.peerComparison, 'score')}`}>
                  {scorecard.componentScores.peerComparison} / 10
                </span>
              </div>
            </div>
            <div className="flex justify-between items-center">
              <span className="text-gray-700">Historical Context</span>
              <div className="flex items-center">
                <div className="w-48 bg-gray-200 rounded-full h-3 mr-4">
                  <div 
                    className={`h-3 rounded-full ${scorecard.componentScores.historicalContext >= 7 ? 'bg-green-500' : scorecard.componentScores.historicalContext >= 5 ? 'bg-gray-500' : 'bg-red-500'}`}
                    style={{width: `${scorecard.componentScores.historicalContext * 10}%`}}
                  ></div>
                </div>
                <span className={`font-bold text-lg ${getValueColor(scorecard.componentScores.historicalContext, 'score')}`}>
                  {scorecard.componentScores.historicalContext} / 10
                </span>
              </div>
            </div>
            <div className="border-t border-gray-300 pt-4 mt-4">
              <div className="flex justify-between items-center">
                <span className="text-xl font-bold text-black">Overall Valuation Score</span>
                <div className="flex items-center">
                  <div className="w-48 bg-gray-200 rounded-full h-4 mr-4">
                    <div 
                      className={`h-4 rounded-full ${scorecard.overallScore >= 7 ? 'bg-green-500' : scorecard.overallScore >= 5 ? 'bg-gray-500' : 'bg-red-500'}`}
                      style={{width: `${scorecard.overallScore * 10}%`}}
                    ></div>
                  </div>
                  <span className={`font-bold text-2xl ${getValueColor(scorecard.overallScore, 'score')}`}>
                    {scorecard.overallScore} / 10
                  </span>
                </div>
              </div>
              <div className="mt-4 text-center">
                <div className={`inline-block px-6 py-3 rounded-lg border text-xl font-bold ${getVerdictStyle(scorecard.verdict)}`}>
                  {scorecard.verdict}
                </div>
              </div>
            </div>
          </div>
        </div>

      </div>
    </div>
  );
};