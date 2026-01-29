import React from 'react';
import { DollarSign, TrendingUp, Sparkles, Lightbulb } from 'lucide-react';

export const ShareholderReturns = ({ data }) => {
  // Helper function to format numbers
  const formatNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    return num.toLocaleString('en-US');
  };

  // Helper function to format large numbers (billions/millions)
  const formatLargeNumber = (num) => {
    if (num === null || num === undefined) return 'N/A';
    if (num >= 1e9) return `$${(num / 1e9).toFixed(2)}B`;
    if (num >= 1e6) return `$${(num / 1e6).toFixed(2)}M`;
    return `$${formatNumber(num)}`;
  };

  // Helper function to format percentages with color
  const formatPercentage = (num, showSign = true) => {
    if (num === null || num === undefined) return 'N/A';
    const sign = showSign && num > 0 ? '+' : '';
    return `${sign}${num.toFixed(2)}%`;
  };

  // Helper function to get color class based on value
  const getColorClass = (value, inverse = false) => {
    if (value === null || value === undefined) return 'text-slate-500';
    const isPositive = inverse ? value < 0 : value > 0;
    return isPositive ? 'text-emerald-600' : 'text-red-600';
  };

  const ContentSection = ({ children, delay = 0 }) => (
    <div 
      className="opacity-0 animate-fade-in"
      style={{ animationDelay: `${delay}s`, animationFillMode: 'forwards' }}
    >
      {children}
    </div>
  );

  if (!data || data.error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <h2 className="text-xl font-bold text-slate-900 mb-4">Shareholder Returns</h2>
            <p className="text-slate-600">Unable to load shareholder returns data.</p>
            {data?.error && <p className="text-sm text-red-600 mt-2">{data.error}</p>}
          </div>
        </div>
      </div>
    );
  }

  const { dividends, buybacks } = data;

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
        <div className="mb-14 relative opacity-0 animate-fade-in" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-2">
            Shareholder Returns
          </h1>
          <p className="text-slate-600 text-sm mt-1">Capital allocation and distribution analysis</p>
        </div>
        
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-16">
          {/* Dividends Section */}
          <ContentSection delay={0.2}>
            <div className="h-full bg-white rounded-lg border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-amber-50 flex items-center justify-center">
                    <DollarSign className="text-amber-600" size={20} />
                  </div>
                  <h2 className="text-lg font-bold text-slate-900">Dividends</h2>
                </div>
                {dividends.has_dividend ? (
                  <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-semibold rounded-full uppercase tracking-wide">
                    Active
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-full uppercase tracking-wide">
                    None
                  </span>
                )}
              </div>

              {dividends.has_dividend ? (
                <div className="space-y-4">
                  {/* Dividend Yield */}
                  <div className="flex justify-between items-center py-2 border-b border-slate-200">
                    <span className="text-sm text-slate-600">Dividend Yield</span>
                    <span className="text-base font-bold text-slate-900">
                      {formatPercentage(dividends.dividend_yield, false)}
                    </span>
                  </div>

                  {/* TTM Dividends */}
                  <div className="flex justify-between items-center py-2 border-b border-slate-200">
                    <span className="text-sm text-slate-600">Annual Dividend</span>
                    <span className="text-base font-semibold text-slate-900">
                      ${dividends.ttm_dividends?.toFixed(4) || 'N/A'}
                    </span>
                  </div>

                  {/* Payout Ratio */}
                  <div className="flex justify-between items-center py-2 border-b border-slate-200">
                    <span className="text-sm text-slate-600">Payout Ratio</span>
                    <span className="text-base font-semibold text-slate-900">
                      {dividends.payout_ratio !== null 
                        ? formatPercentage(dividends.payout_ratio, false)
                        : 'N/A'}
                    </span>
                  </div>

                  {/* Dividend Growth */}
                  <div className="pt-2">
                    <div className="text-sm font-semibold text-slate-700 mb-3">Dividend Growth</div>
                    <div className="grid grid-cols-3 gap-2">
                      <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="text-xs text-slate-500 mb-1 font-medium">1Y</div>
                        <div className={`text-sm font-bold ${getColorClass(dividends.dividend_growth_1y)}`}>
                          {formatPercentage(dividends.dividend_growth_1y)}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="text-xs text-slate-500 mb-1 font-medium">3Y</div>
                        <div className={`text-sm font-bold ${getColorClass(dividends.dividend_growth_3y)}`}>
                          {formatPercentage(dividends.dividend_growth_3y)}
                        </div>
                      </div>
                      <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                        <div className="text-xs text-slate-500 mb-1 font-medium">5Y</div>
                        <div className={`text-sm font-bold ${getColorClass(dividends.dividend_growth_5y)}`}>
                          {formatPercentage(dividends.dividend_growth_5y)}
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Last Dividend Info */}
                  {dividends.last_dividend_date && (
                    <div className="pt-3 mt-3 border-t border-slate-200">
                      <div className="text-xs text-slate-500">
                        Last: ${dividends.last_dividend?.toFixed(4)} on {dividends.last_dividend_date}
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-center py-12 text-slate-400">
                  <DollarSign className="w-12 h-12 mx-auto mb-2 opacity-50" />
                  <p className="text-sm">No dividend payments</p>
                </div>
              )}
            </div>
          </ContentSection>

          {/* Buybacks Section */}
          <ContentSection delay={0.3}>
            <div className="h-full bg-white rounded-lg border border-slate-200 p-6 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center justify-between mb-5">
                <div className="flex items-center gap-3">
                  <div className="w-9 h-9 rounded-lg bg-emerald-50 flex items-center justify-center">
                    <TrendingUp className="text-emerald-600" size={20} />
                  </div>
                  <h2 className="text-lg font-bold text-slate-900">Share Buybacks</h2>
                </div>
                {buybacks.is_buying_back ? (
                  <span className="px-3 py-1 bg-emerald-100 text-emerald-800 text-xs font-semibold rounded-full uppercase tracking-wide">
                    Active
                  </span>
                ) : (
                  <span className="px-3 py-1 bg-slate-100 text-slate-600 text-xs font-semibold rounded-full uppercase tracking-wide">
                    Inactive
                  </span>
                )}
              </div>

              <div className="space-y-4">
                {/* Shares Outstanding */}
                <div className="flex justify-between items-center py-2 border-b border-slate-200">
                  <span className="text-sm text-slate-600">Shares Outstanding</span>
                  <span className="text-base font-semibold text-slate-900">
                    {formatNumber(buybacks.current_shares_outstanding)}
                  </span>
                </div>

                {/* Buyback Value TTM */}
                {buybacks.buyback_value_ttm !== null && (
                  <div className="flex justify-between items-center py-2 border-b border-slate-200">
                    <span className="text-sm text-slate-600">Buyback Value (TTM)</span>
                    <span className="text-base font-bold text-slate-900">
                      {formatLargeNumber(buybacks.buyback_value_ttm)}
                    </span>
                  </div>
                )}

                {/* Buyback Yield */}
                {buybacks.buyback_yield !== null && (
                  <div className="flex justify-between items-center py-2 border-b border-slate-200">
                    <span className="text-sm text-slate-600">Buyback Yield</span>
                    <span className="text-base font-bold text-slate-900">
                      {formatPercentage(buybacks.buyback_yield, false)}
                    </span>
                  </div>
                )}

                {/* Share Count Change */}
                <div className="pt-2">
                  <div className="text-sm font-semibold text-slate-700 mb-3">Share Count Change</div>
                  <div className="grid grid-cols-3 gap-2">
                    <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-xs text-slate-500 mb-1 font-medium">1Y</div>
                      <div className={`text-sm font-bold ${getColorClass(buybacks.shares_change_1y, true)}`}>
                        {formatPercentage(buybacks.shares_change_1y)}
                      </div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-xs text-slate-500 mb-1 font-medium">3Y</div>
                      <div className={`text-sm font-bold ${getColorClass(buybacks.shares_change_3y, true)}`}>
                        {formatPercentage(buybacks.shares_change_3y)}
                      </div>
                    </div>
                    <div className="text-center p-3 bg-slate-50 rounded-lg border border-slate-200">
                      <div className="text-xs text-slate-500 mb-1 font-medium">5Y</div>
                      <div className={`text-sm font-bold ${getColorClass(buybacks.shares_change_5y, true)}`}>
                        {formatPercentage(buybacks.shares_change_5y)}
                      </div>
                    </div>
                  </div>
                </div>

                {/* Info note */}
                <div className="pt-3 mt-3 border-t border-slate-200">
                  <div className="text-xs text-slate-500">
                    Negative values indicate share reduction (buybacks)
                  </div>
                </div>
              </div>
            </div>
          </ContentSection>
        </div>

        {/* Total Shareholder Return Summary */}
        {(dividends.has_dividend || buybacks.is_buying_back) && (
          <ContentSection delay={0.4}>
            <div className="relative rounded-lg overflow-hidden p-8 text-white">
              <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900"></div>
              <div className="absolute inset-0 opacity-5" style={{
                backgroundImage: 'linear-gradient(45deg, #ffffff 1px, transparent 1px)',
                backgroundSize: '20px 20px'
              }}></div>
              <div className="relative flex items-start gap-4">
                <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                  <Sparkles className="text-white" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold mb-3">Total Shareholder Yield</h2>
                  <div className="text-base leading-relaxed opacity-95">
                    {dividends.has_dividend && buybacks.is_buying_back && (
                      <>This company returns capital through both dividends and buybacks.</>
                    )}
                    {dividends.has_dividend && !buybacks.is_buying_back && (
                      <>This company primarily returns capital through dividends.</>
                    )}
                    {!dividends.has_dividend && buybacks.is_buying_back && (
                      <>This company primarily returns capital through share buybacks.</>
                    )}
                    {dividends.dividend_yield !== null && buybacks.buyback_yield !== null && (
                      <span className="font-bold ml-1">
                        Combined yield: ~{(dividends.dividend_yield + buybacks.buyback_yield).toFixed(2)}%
                      </span>
                    )}
                  </div>
                </div>
              </div>
            </div>
          </ContentSection>
        )}

      </div>
    </div>
  );
};