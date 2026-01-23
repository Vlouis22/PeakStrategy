import React from 'react';

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
    if (value === null || value === undefined) return 'text-gray-500';
    const isPositive = inverse ? value < 0 : value > 0;
    return isPositive ? 'text-green-600' : 'text-red-600';
  };

  if (!data || data.error) {
    return (
      <div className="bg-white p-6 rounded-lg border border-gray-200">
        <h2 className="text-xl font-semibold mb-4 text-black">Shareholder Returns</h2>
        <p className="text-gray-500">Unable to load shareholder returns data.</p>
        {data?.error && <p className="text-sm text-red-600 mt-2">{data.error}</p>}
      </div>
    );
  }

  const { dividends, buybacks } = data;

  return (
    <div className="bg-white p-6 rounded-lg border border-gray-200">
      <h2 className="text-xl font-semibold mb-6 text-black">Shareholder Returns</h2>
      
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Dividends Section */}
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-black">Dividends</h3>
            {dividends.has_dividend ? (
              <span className="px-3 py-1 bg-blue-100 text-blue-800 text-xs font-medium rounded-full">
                Active
              </span>
            ) : (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                None
              </span>
            )}
          </div>

          {dividends.has_dividend ? (
            <div className="space-y-4">
              {/* Dividend Yield */}
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Dividend Yield</span>
                <span className="text-base font-semibold text-black">
                  {formatPercentage(dividends.dividend_yield, false)}
                </span>
              </div>

              {/* TTM Dividends */}
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Annual Dividend</span>
                <span className="text-base font-medium text-black">
                  ${dividends.ttm_dividends?.toFixed(4) || 'N/A'}
                </span>
              </div>

              {/* Payout Ratio */}
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Payout Ratio</span>
                <span className="text-base font-medium text-black">
                  {dividends.payout_ratio !== null 
                    ? formatPercentage(dividends.payout_ratio, false)
                    : 'N/A'}
                </span>
              </div>

              {/* Dividend Growth */}
              <div className="pt-2">
                <div className="text-sm font-medium text-gray-700 mb-3">Dividend Growth</div>
                <div className="grid grid-cols-3 gap-2">
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-xs text-gray-500 mb-1">1Y</div>
                    <div className={`text-sm font-semibold ${getColorClass(dividends.dividend_growth_1y)}`}>
                      {formatPercentage(dividends.dividend_growth_1y)}
                    </div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-xs text-gray-500 mb-1">3Y</div>
                    <div className={`text-sm font-semibold ${getColorClass(dividends.dividend_growth_3y)}`}>
                      {formatPercentage(dividends.dividend_growth_3y)}
                    </div>
                  </div>
                  <div className="text-center p-2 bg-gray-50 rounded">
                    <div className="text-xs text-gray-500 mb-1">5Y</div>
                    <div className={`text-sm font-semibold ${getColorClass(dividends.dividend_growth_5y)}`}>
                      {formatPercentage(dividends.dividend_growth_5y)}
                    </div>
                  </div>
                </div>
              </div>

              {/* Last Dividend Info */}
              {dividends.last_dividend_date && (
                <div className="pt-2 mt-2 border-t border-gray-200">
                  <div className="text-xs text-gray-500">
                    Last: ${dividends.last_dividend?.toFixed(4)} on {dividends.last_dividend_date}
                  </div>
                </div>
              )}
            </div>
          ) : (
            <div className="text-center py-8 text-gray-400">
              No dividend payments
            </div>
          )}
        </div>

        {/* Buybacks Section */}
        <div className="border border-gray-200 rounded-lg p-5">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-lg font-semibold text-black">Share Buybacks</h3>
            {buybacks.is_buying_back ? (
              <span className="px-3 py-1 bg-green-100 text-green-800 text-xs font-medium rounded-full">
                Active
              </span>
            ) : (
              <span className="px-3 py-1 bg-gray-100 text-gray-600 text-xs font-medium rounded-full">
                Inactive
              </span>
            )}
          </div>

          <div className="space-y-4">
            {/* Shares Outstanding */}
            <div className="flex justify-between items-center py-2 border-b border-gray-100">
              <span className="text-sm text-gray-600">Shares Outstanding</span>
              <span className="text-base font-medium text-black">
                {formatNumber(buybacks.current_shares_outstanding)}
              </span>
            </div>

            {/* Buyback Value TTM */}
            {buybacks.buyback_value_ttm !== null && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Buyback Value (TTM)</span>
                <span className="text-base font-semibold text-black">
                  {formatLargeNumber(buybacks.buyback_value_ttm)}
                </span>
              </div>
            )}

            {/* Buyback Yield */}
            {buybacks.buyback_yield !== null && (
              <div className="flex justify-between items-center py-2 border-b border-gray-100">
                <span className="text-sm text-gray-600">Buyback Yield</span>
                <span className="text-base font-semibold text-black">
                  {formatPercentage(buybacks.buyback_yield, false)}
                </span>
              </div>
            )}

            {/* Share Count Change */}
            <div className="pt-2">
              <div className="text-sm font-medium text-gray-700 mb-3">Share Count Change</div>
              <div className="grid grid-cols-3 gap-2">
                <div className="text-center p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500 mb-1">1Y</div>
                  <div className={`text-sm font-semibold ${getColorClass(buybacks.shares_change_1y, true)}`}>
                    {formatPercentage(buybacks.shares_change_1y)}
                  </div>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500 mb-1">3Y</div>
                  <div className={`text-sm font-semibold ${getColorClass(buybacks.shares_change_3y, true)}`}>
                    {formatPercentage(buybacks.shares_change_3y)}
                  </div>
                </div>
                <div className="text-center p-2 bg-gray-50 rounded">
                  <div className="text-xs text-gray-500 mb-1">5Y</div>
                  <div className={`text-sm font-semibold ${getColorClass(buybacks.shares_change_5y, true)}`}>
                    {formatPercentage(buybacks.shares_change_5y)}
                  </div>
                </div>
              </div>
            </div>

            {/* Info note */}
            <div className="pt-2 mt-2 border-t border-gray-200">
              <div className="text-xs text-gray-500">
                Negative values indicate share reduction (buybacks)
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* Total Shareholder Return Summary */}
      {(dividends.has_dividend || buybacks.is_buying_back) && (
        <div className="mt-6 p-4 bg-blue-50 rounded-lg border border-blue-100">
          <div className="flex items-start gap-3">
            <svg className="w-5 h-5 text-blue-600 mt-0.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div className="flex-1">
              <div className="text-sm font-medium text-blue-900 mb-1">Total Shareholder Yield</div>
              <div className="text-sm text-blue-700">
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
                  <span className="font-semibold ml-1">
                    Combined yield: ~{(dividends.dividend_yield + buybacks.buyback_yield).toFixed(2)}%
                  </span>
                )}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};
