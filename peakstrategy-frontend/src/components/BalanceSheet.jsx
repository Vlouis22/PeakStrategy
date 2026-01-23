import React, { useState } from 'react'

export const BalanceSheet = ({ balanceSheet }) => {
  const [activeTooltip, setActiveTooltip] = useState(null)

  // Helper function to format currency
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A'
    const absValue = Math.abs(value)
    if (absValue >= 1e12) return `$${(value / 1e12).toFixed(2)}T`
    if (absValue >= 1e9) return `$${(value / 1e9).toFixed(2)}B`
    if (absValue >= 1e6) return `$${(value / 1e6).toFixed(2)}M`
    if (absValue >= 1e3) return `$${(value / 1e3).toFixed(2)}K`
    return `$${value.toFixed(0)}`
  }

  // Helper function to format ratio
  const formatRatio = (value, suffix = '') => {
    if (value === null || value === undefined) return 'N/A'
    return `${value.toFixed(2)}${suffix}`
  }

  // Info icon component
  const InfoIcon = ({ metricKey }) => {
    const explanation = balanceSheet?.explanations?.[metricKey]
    if (!explanation) return null

    const isActive = activeTooltip === metricKey

    return (
      <div className="relative inline-block ml-2">
        <div
          onClick={() => setActiveTooltip(isActive ? null : metricKey)}
          className={`w-4.5 h-4.5 rounded-full border-[1.5px] flex items-center justify-center cursor-pointer text-xs font-semibold transition-all select-none ${
            isActive
              ? 'bg-gray-200 border-gray-800 text-gray-800'
              : 'bg-transparent border-gray-400 text-gray-400'
          }`}
          onMouseEnter={(e) => {
            e.currentTarget.classList.add('bg-gray-200', 'border-gray-800', 'text-gray-800')
          }}
          onMouseLeave={(e) => {
            if (!isActive) {
              e.currentTarget.classList.remove('bg-gray-200', 'border-gray-800', 'text-gray-800')
              e.currentTarget.classList.add('bg-transparent', 'border-gray-400', 'text-gray-400')
            }
          }}
        >
          i
        </div>

        {isActive && (
          <div className="absolute top-[25px] left-1/2 -translate-x-1/2 bg-gray-800 text-white p-2.5 rounded-md text-[13px] leading-6 w-[280px] z-50 shadow-lg text-left">
            {explanation}
            <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[6px] border-b-gray-800" />
          </div>
        )}
      </div>
    )
  }

  // Metric row component
  const MetricRow = ({ label, value, metricKey, isRatio = false, suffix = '' }) => (
    <div className="flex justify-between items-center py-3 border-b border-gray-200">
      <span className="font-medium text-gray-800 flex items-center">
        {label}
        <InfoIcon metricKey={metricKey} />
      </span>
      <span className="font-semibold font-mono text-sm text-black">
        {isRatio ? formatRatio(value, suffix) : formatCurrency(value)}
      </span>
    </div>
  )

  // Section header component
  const SectionHeader = ({ title }) => (
    <h3 className="text-lg font-bold mt-6 mb-3 text-black border-b-2 border-black pb-2">{title}</h3>
  )

  // Error state
  if (balanceSheet?.error) {
    return (
      <div className="bg-white text-black p-6 w-full">
        <h2 className="text-2xl mb-4 text-red-700">Error Loading Data</h2>
        <p className="text-gray-500">{balanceSheet.error}</p>
      </div>
    )
  }

  // No data state
  if (!balanceSheet) {
    return (
      <div className="bg-white text-black p-6 w-full">
        <p className="text-gray-500 text-center">No balance sheet data available</p>
      </div>
    )
  }

  return (
    <div
      className="bg-white text-black p-8 w-full font-sans"
      onClick={(e) => {
        if (!e.target.closest('[class*="cursor-pointer"]')) setActiveTooltip(null)
      }}
    >
      {/* Header */}
      <div className="mb-6">
        <p className="text-lg text-gray-500 mb-1">Balance Sheet Analysis</p>
        {balanceSheet.date && <p className="text-xs text-gray-400">As of: {balanceSheet.date}</p>}
      </div>

      {/* Debt & Leverage */}
      <SectionHeader title="Debt & Leverage" />
      <div>
        <MetricRow label="Total Debt" value={balanceSheet.total_debt} metricKey="total_debt" />
        <MetricRow label="Net Debt" value={balanceSheet.net_debt} metricKey="net_debt" />
        <MetricRow label="Debt / Equity" value={balanceSheet.debt_to_equity} metricKey="debt_to_equity" isRatio />
        <MetricRow label="Debt / EBITDA" value={balanceSheet.debt_to_ebitda} metricKey="debt_to_ebitda" isRatio />
        <MetricRow
          label="Interest Coverage Ratio"
          value={balanceSheet.interest_coverage}
          metricKey="interest_coverage"
          isRatio
          suffix="x"
        />
      </div>

      {/* Liquidity */}
      <SectionHeader title="Liquidity" />
      <div>
        <MetricRow label="Current Ratio" value={balanceSheet.current_ratio} metricKey="current_ratio" isRatio />
        <MetricRow label="Quick Ratio" value={balanceSheet.quick_ratio} metricKey="quick_ratio" isRatio />
        <MetricRow label="Cash & Short-term Investments" value={balanceSheet.cash_and_short_term} metricKey="cash_and_short_term" />
      </div>

      {/* Footer Note */}
      <div className="mt-8 p-4 bg-gray-100 text-gray-500 text-xs">
        <strong>Note:</strong> Data sourced from Yahoo Finance. Metrics marked as "N/A" indicate unavailable or insufficient data for calculation. All financial values are in USD. Click the info icons to learn what each metric means.
      </div>
    </div>
  )
}

