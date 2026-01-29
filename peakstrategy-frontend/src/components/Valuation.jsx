import React, { useState, useRef, useEffect } from 'react';
import { TrendingUp, TrendingDown, Minus, DollarSign, BarChart3, Activity, Info, Target, Lightbulb } from 'lucide-react';

// Isolated tooltip component to prevent parent re-renders
const PeerTooltip = ({ tooltipText }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative">
      <Info 
        size={16} 
        className="text-slate-400 cursor-help hover:text-slate-600 transition-colors"
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setShowTooltip(!showTooltip);
        }}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
      />
      {showTooltip && (
        <div className="absolute z-50 right-0 top-full mt-2 w-80 p-3 bg-slate-900 text-white text-sm rounded-lg shadow-xl">
          <div className="relative">
            {tooltipText}
            <div className="absolute -top-2 right-3 w-0 h-0 border-l-4 border-r-4 border-b-4 border-l-transparent border-r-transparent border-b-slate-900"></div>
          </div>
        </div>
      )}
    </div>
  );
};

export const Valuation = ({ valuationData }) => {
  const hasAnimated = useRef(false);

  useEffect(() => {
    // Mark animations as complete after they've run once
    if (!hasAnimated.current) {
      hasAnimated.current = true;
    }
  }, []);

  if (!valuationData) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600">No valuation data available</p>
          </div>
        </div>
      </div>
    );
  } 

  if (valuationData) {
    console.log('Valuation Data:', valuationData);
  }

  const getValueColor = (value, type = 'pe') => {
    if (value === null || value === undefined) return 'text-slate-600';
    
    switch(type) {
      case 'pe':
        if (value < 15) return 'text-emerald-600';
        if (value < 25) return 'text-slate-700';
        return 'text-red-600';
      case 'peg':
        if (value < 1) return 'text-emerald-600';
        if (value < 2) return 'text-slate-700';
        return 'text-red-600';
      case 'percent':
        if (value > 0) return 'text-emerald-600';
        if (value > -10) return 'text-slate-700';
        return 'text-red-600';
      case 'score':
        if (value >= 7) return 'text-emerald-600';
        if (value >= 5) return 'text-slate-700';
        return 'text-red-600';
      default:
        return 'text-slate-700';
    }
  };

  const getVerdictStyle = (verdict) => {
    switch(verdict) {
      case 'Undervalued':
        return 'bg-emerald-100 text-emerald-700 border-emerald-300';
      case 'Fairly Valued':
        return 'bg-slate-100 text-slate-700 border-slate-300';
      case 'Overvalued':
        return 'bg-red-100 text-red-700 border-red-300';
      default:
        return 'bg-slate-100 text-slate-700 border-slate-300';
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

  const peerCount = peerComparison?.peerGroupAvg?.peerCount || 0;
  const peers = peerComparison?.peerGroupAvg?.peers || [];
  const peerTooltipText = peerCount > 0 
    ? `Average of ${peerCount} representative peer${peerCount > 1 ? 's' : ''} in the same sector (${peers.join(', ')}) using Yahoo Finance data`
    : 'Average of 3–5 representative peers in the same sector using Yahoo Finance data';

  const ContentSection = ({ children, delay = 0 }) => (
    <div 
      className={hasAnimated.current ? "" : "opacity-0 animate-fade-in"}
      style={hasAnimated.current ? { opacity: 1 } : { animationDelay: `${delay}s`, animationFillMode: 'forwards' }}
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

        {/* Hero Header */}
        <div 
          className={hasAnimated.current ? "" : "mb-14 relative opacity-0 animate-fade-in"}
          style={hasAnimated.current ? { marginBottom: '3.5rem', position: 'relative', opacity: 1 } : { animationDelay: '0.1s', animationFillMode: 'forwards' }}
        >
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-2">
            Valuation Analysis
          </h1>
          <p className="text-slate-600 text-sm mt-1">Comprehensive valuation metrics and peer comparisons</p>
        </div>

        {/* 1. Valuation Overview */}
        <ContentSection delay={0.2}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <DollarSign className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Valuation Overview</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Current Price</p>
                <p className="text-3xl font-bold text-slate-900">${formatNumber(overview.currentPrice)}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Market Cap</p>
                <p className="text-3xl font-bold text-slate-900">{formatLargeNumber(overview.marketCap)}</p>
              </div>
              <div>
                <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Valuation Verdict</p>
                <div className={`inline-block px-4 py-2 rounded-lg border ${getVerdictStyle(scorecard.verdict)}`}>
                  <p className="text-xl font-bold">{scorecard.verdict}</p>
                </div>
              </div>
            </div>
          </div>
        </ContentSection>

        {/* 2. Relative Valuation Metrics */}
        <ContentSection delay={0.3}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <BarChart3 className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Valuation Metrics</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Metric</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Value</th>
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Interpretation</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">P/E (TTM)</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.trailingPE, 'pe')}`}>
                      {formatNumber(relativeMetrics.trailingPE)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Price per $1 of current earnings</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">P/E (Forward)</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.forwardPE, 'pe')}`}>
                      {formatNumber(relativeMetrics.forwardPE)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Market expectation of future earnings</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">PEG Ratio</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.pegRatio, 'peg')}`}>
                      {formatNumber(relativeMetrics.pegRatio)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Growth-adjusted valuation</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">EV / EBITDA</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg ${getValueColor(relativeMetrics.enterpriseToEbitda, 'pe')}`}>
                      {formatNumber(relativeMetrics.enterpriseToEbitda)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Capital-structure neutral valuation</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">Price / Sales</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg text-slate-700`}>
                      {formatNumber(relativeMetrics.priceToSalesTrailing)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Useful for unprofitable companies</td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">Price / Book</td>
                    <td className={`text-right py-4 px-4 font-bold text-lg text-slate-700`}>
                      {formatNumber(relativeMetrics.priceToBook)}
                    </td>
                    <td className="py-4 px-4 text-slate-600 text-sm">Asset-based valuation</td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </ContentSection>

        {/* 3. Absolute Valuation Context */}
        <ContentSection delay={0.4}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Activity className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Price Positioning</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-4">52-Week Range</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Current Price</span>
                    <span className="text-xl font-bold text-slate-900">${formatNumber(absoluteContext.currentPrice)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">52-Week High</span>
                    <span className="font-semibold text-slate-900">${formatNumber(absoluteContext.fiftyTwoWeekHigh)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">52-Week Low</span>
                    <span className="font-semibold text-slate-900">${formatNumber(absoluteContext.fiftyTwoWeekLow)}</span>
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-slate-200">
                    <span className="text-sm text-slate-600">% from High</span>
                    <span className={`font-bold ${getValueColor(absoluteContext.percentFromHigh, 'percent')}`}>
                      {formatNumber(absoluteContext.percentFromHigh)}%
                    </span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">% from Low</span>
                    <span className={`font-bold ${getValueColor(absoluteContext.percentFromLow, 'percent')}`}>
                      {formatNumber(absoluteContext.percentFromLow)}%
                    </span>
                  </div>
                </div>
              </div>
              <div>
                <h3 className="text-base font-bold text-slate-900 mb-4">Market Cap vs Revenue</h3>
                <div className="space-y-4">
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">Market Cap</span>
                    <span className="font-bold text-slate-900">{formatLargeNumber(businessSize.marketCap)}</span>
                  </div>
                  <div className="flex justify-between items-center">
                    <span className="text-sm text-slate-600">TTM Revenue</span>
                    <span className="font-bold text-slate-900">{formatLargeNumber(businessSize.trailingRevenue)}</span>
                  </div>
                  <div className="flex justify-between items-center pt-2 border-t border-slate-200">
                    <span className="text-sm text-slate-600">Market Cap / Revenue</span>
                    <span className="font-bold text-lg text-slate-900">{formatNumber(businessSize.marketCapToRevenue)}x</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ContentSection>

        {/* 4. Peer Comparison */}
        <ContentSection delay={0.5}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Target className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Peer & Market Comparisons</h2>
            </div>
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-slate-200">
                    <th className="text-left py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">Metric</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">This Stock</th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">
                      <div className="flex items-center justify-end gap-1 relative">
                        <span>Peer Group Avg</span>
                        <PeerTooltip tooltipText={peerTooltipText} />
                      </div>
                    </th>
                    <th className="text-right py-3 px-4 text-xs font-semibold text-slate-500 uppercase tracking-wide">S&P 500</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-200">
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">P/E Ratio</td>
                    <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.pe, 'pe')}`}>
                      {formatNumber(peerComparison.thisStock.pe)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.peerGroupAvg?.pe)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.sp500Avg.pe)}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">Forward P/E</td>
                    <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.forwardPE, 'pe')}`}>
                      {formatNumber(peerComparison.thisStock.forwardPE)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.peerGroupAvg?.forwardPE)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.sp500Avg.forwardPE)}
                    </td>
                  </tr>
                  <tr className="hover:bg-slate-50 transition-colors">
                    <td className="py-4 px-4 text-slate-900 font-medium">PEG Ratio</td>
                    <td className={`text-right py-4 px-4 font-bold ${getValueColor(peerComparison.thisStock.peg, 'peg')}`}>
                      {formatNumber(peerComparison.thisStock.peg)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.peerGroupAvg?.peg)}
                    </td>
                    <td className="text-right py-4 px-4 text-slate-700">
                      {formatNumber(peerComparison.sp500Avg.peg)}
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>
        </ContentSection>

        {/* 5. Growth Metrics */}
        {growthMetrics && (
          <ContentSection delay={0.6}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <TrendingUp className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Growth-Adjusted Valuation</h2>
              </div>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Expected EPS Growth</p>
                  <p className={`text-2xl font-bold ${getValueColor(growthMetrics.expectedEPSGrowth ? growthMetrics.expectedEPSGrowth * 100 : 0, 'percent')}`}>
                    {growthMetrics.expectedEPSGrowth ? `${(growthMetrics.expectedEPSGrowth * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">Expected Revenue Growth</p>
                  <p className={`text-2xl font-bold ${getValueColor(growthMetrics.expectedRevenueGrowth ? growthMetrics.expectedRevenueGrowth * 100 : 0, 'percent')}`}>
                    {growthMetrics.expectedRevenueGrowth ? `${(growthMetrics.expectedRevenueGrowth * 100).toFixed(1)}%` : 'N/A'}
                  </p>
                </div>
                <div>
                  <p className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">PEG Interpretation</p>
                  <p className="text-base font-semibold text-slate-700">{growthMetrics.pegInterpretation}</p>
                </div>
              </div>
            </div>
          </ContentSection>
        )}

        {/* 6. Valuation Insights */}
        {interpretation && interpretation.length > 0 && (
          <ContentSection delay={0.7}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Lightbulb className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Key Insights</h2>
              </div>
              <div className="space-y-3">
                {interpretation.map((insight, idx) => (
                  <div 
                    key={idx} 
                    className={`flex items-start p-4 rounded-lg border ${
                      insight.type === 'positive' ? 'bg-emerald-50 border-emerald-200' :
                      insight.type === 'negative' ? 'bg-red-50 border-red-200' :
                      'bg-slate-50 border-slate-200'
                    }`}
                  >
                    {insight.type === 'positive' ? (
                      <TrendingUp className="text-emerald-600 mr-3 mt-1 flex-shrink-0" size={20} />
                    ) : insight.type === 'negative' ? (
                      <TrendingDown className="text-red-600 mr-3 mt-1 flex-shrink-0" size={20} />
                    ) : (
                      <Minus className="text-slate-600 mr-3 mt-1 flex-shrink-0" size={20} />
                    )}
                    <p className="text-slate-700 leading-relaxed text-sm">{insight.message}</p>
                  </div>
                ))}
              </div>
            </div>
          </ContentSection>
        )}

        {/* 7. Valuation Scorecard */}
        <ContentSection delay={0.8}>
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <BarChart3 className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Valuation Scorecard</h2>
            </div>
            <div className="space-y-5">
              <div className="flex justify-between items-center">
                <span className="text-slate-700 font-medium">Earnings Valuation</span>
                <div className="flex items-center gap-4">
                  <div className="w-48 bg-slate-200 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full transition-all duration-500 ${scorecard.componentScores.earningsValuation >= 7 ? 'bg-emerald-500' : scorecard.componentScores.earningsValuation >= 5 ? 'bg-slate-500' : 'bg-red-500'}`}
                      style={{width: `${scorecard.componentScores.earningsValuation * 10}%`}}
                    ></div>
                  </div>
                  <span className={`font-bold text-lg w-16 text-right ${getValueColor(scorecard.componentScores.earningsValuation, 'score')}`}>
                    {scorecard.componentScores.earningsValuation} / 10
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-700 font-medium">Growth-Adjusted Valuation</span>
                <div className="flex items-center gap-4">
                  <div className="w-48 bg-slate-200 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full transition-all duration-500 ${scorecard.componentScores.growthAdjusted >= 7 ? 'bg-emerald-500' : scorecard.componentScores.growthAdjusted >= 5 ? 'bg-slate-500' : 'bg-red-500'}`}
                      style={{width: `${scorecard.componentScores.growthAdjusted * 10}%`}}
                    ></div>
                  </div>
                  <span className={`font-bold text-lg w-16 text-right ${getValueColor(scorecard.componentScores.growthAdjusted, 'score')}`}>
                    {scorecard.componentScores.growthAdjusted} / 10
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-700 font-medium">Peer Comparison</span>
                <div className="flex items-center gap-4">
                  <div className="w-48 bg-slate-200 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full transition-all duration-500 ${scorecard.componentScores.peerComparison >= 7 ? 'bg-emerald-500' : scorecard.componentScores.peerComparison >= 5 ? 'bg-slate-500' : 'bg-red-500'}`}
                      style={{width: `${scorecard.componentScores.peerComparison * 10}%`}}
                    ></div>
                  </div>
                  <span className={`font-bold text-lg w-16 text-right ${getValueColor(scorecard.componentScores.peerComparison, 'score')}`}>
                    {scorecard.componentScores.peerComparison} / 10
                  </span>
                </div>
              </div>
              <div className="flex justify-between items-center">
                <span className="text-slate-700 font-medium">Historical Context</span>
                <div className="flex items-center gap-4">
                  <div className="w-48 bg-slate-200 rounded-full h-2.5">
                    <div 
                      className={`h-2.5 rounded-full transition-all duration-500 ${scorecard.componentScores.historicalContext >= 7 ? 'bg-emerald-500' : scorecard.componentScores.historicalContext >= 5 ? 'bg-slate-500' : 'bg-red-500'}`}
                      style={{width: `${scorecard.componentScores.historicalContext * 10}%`}}
                    ></div>
                  </div>
                  <span className={`font-bold text-lg w-16 text-right ${getValueColor(scorecard.componentScores.historicalContext, 'score')}`}>
                    {scorecard.componentScores.historicalContext} / 10
                  </span>
                </div>
              </div>
              <div className="border-t border-slate-200 pt-6 mt-6">
                <div className="flex justify-between items-center mb-6">
                  <span className="text-xl font-bold text-slate-900">Overall Valuation Score</span>
                  <div className="flex items-center gap-4">
                    <div className="w-48 bg-slate-200 rounded-full h-3">
                      <div 
                        className={`h-3 rounded-full transition-all duration-500 ${scorecard.overallScore >= 7 ? 'bg-emerald-500' : scorecard.overallScore >= 5 ? 'bg-slate-500' : 'bg-red-500'}`}
                        style={{width: `${scorecard.overallScore * 10}%`}}
                      ></div>
                    </div>
                    <span className={`font-bold text-lg w-16 text-right ${getValueColor(scorecard.overallScore, 'score')}`}>
                      {scorecard.overallScore.toFixed(1)} / 10
                    </span>
                  </div>
                </div>
                <div className="text-center">
                  <div className={`inline-block px-6 py-3 rounded-lg border text-xl font-bold ${getVerdictStyle(scorecard.verdict)}`}>
                    {scorecard.verdict}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </ContentSection>

      </div>
    </div>
  );
};