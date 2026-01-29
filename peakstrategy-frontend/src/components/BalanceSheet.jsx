import React, { useState, useRef, useEffect } from 'react';
import { Shield, Activity, DollarSign, Info } from 'lucide-react';

// Isolated InfoIcon component to prevent parent re-renders
const InfoIcon = ({ metricKey, explanation }) => {
  const [isActive, setIsActive] = useState(false);
  const tooltipRef = useRef(null);

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (tooltipRef.current && !tooltipRef.current.contains(event.target)) {
        setIsActive(false);
      }
    };

    if (isActive) {
      document.addEventListener('mousedown', handleClickOutside);
      return () => {
        document.removeEventListener('mousedown', handleClickOutside);
      };
    }
  }, [isActive]);

  if (!explanation) return null;

  return (
    <div className="relative inline-block ml-2" ref={tooltipRef}>
      <div
        onClick={(e) => {
          e.preventDefault();
          e.stopPropagation();
          setIsActive(!isActive);
        }}
        className={`w-4 h-4 rounded-full border flex items-center justify-center cursor-pointer text-xs font-semibold transition-all select-none ${
          isActive
            ? 'bg-slate-200 border-slate-800 text-slate-800'
            : 'bg-transparent border-slate-400 text-slate-400 hover:bg-slate-200 hover:border-slate-800 hover:text-slate-800'
        }`}
      >
        <Info className="w-3 h-3" />
      </div>

      {isActive && (
        <div className="absolute top-[25px] left-1/2 -translate-x-1/2 bg-slate-900 text-white p-3 rounded-lg text-xs leading-relaxed w-[280px] z-50 shadow-xl text-left">
          {explanation}
          <div className="absolute -top-1.5 left-1/2 -translate-x-1/2 w-0 h-0 border-l-[6px] border-l-transparent border-r-[6px] border-r-transparent border-b-[6px] border-b-slate-900" />
        </div>
      )}
    </div>
  );
};

export const BalanceSheet = ({ balanceSheet }) => {
  const hasAnimated = useRef(false);

  useEffect(() => {
    // Mark animations as complete after they've run once
    if (!hasAnimated.current) {
      hasAnimated.current = true;
    }
  }, []);

  // Helper function to format currency
  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    const absValue = Math.abs(value);
    if (absValue >= 1e12) return `$${(value / 1e12).toFixed(2)}T`;
    if (absValue >= 1e9) return `$${(value / 1e9).toFixed(2)}B`;
    if (absValue >= 1e6) return `$${(value / 1e6).toFixed(2)}M`;
    if (absValue >= 1e3) return `$${(value / 1e3).toFixed(2)}K`;
    return `$${value.toFixed(0)}`;
  };

  // Helper function to format ratio
  const formatRatio = (value, suffix = '') => {
    if (value === null || value === undefined) return 'N/A';
    return `${value.toFixed(2)}${suffix}`;
  };

  // Metric row component
  const MetricRow = ({ label, value, metricKey, isRatio = false, suffix = '' }) => (
    <div className="flex justify-between items-center py-3 border-b border-slate-200 hover:bg-slate-50 transition-colors">
      <span className="font-medium text-slate-700 flex items-center text-sm">
        {label}
        <InfoIcon metricKey={metricKey} explanation={balanceSheet?.explanations?.[metricKey]} />
      </span>
      <span className="font-bold font-mono text-sm text-slate-900">
        {isRatio ? formatRatio(value, suffix) : formatCurrency(value)}
      </span>
    </div>
  );

  const ContentSection = ({ children, delay = 0 }) => (
    <div 
      className={hasAnimated.current ? "" : "opacity-0 animate-fade-in"}
      style={hasAnimated.current ? { opacity: 1 } : { animationDelay: `${delay}s`, animationFillMode: 'forwards' }}
    >
      {children}
    </div>
  );

  // Error state
  if (balanceSheet?.error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <h2 className="text-xl font-bold text-red-600 mb-2">Error Loading Data</h2>
            <p className="text-slate-600">{balanceSheet.error}</p>
          </div>
        </div>
      </div>
    );
  }

  // No data state
  if (!balanceSheet) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600 text-center">No balance sheet data available</p>
          </div>
        </div>
      </div>
    );
  }

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
            Balance Sheet Analysis
          </h1>
          {balanceSheet.date && (
            <p className="text-slate-600 text-sm mt-1">As of: {balanceSheet.date}</p>
          )}
        </div>

        {/* Debt & Leverage */}
        <ContentSection delay={0.2}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Shield className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Debt & Leverage</h2>
            </div>
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
          </div>
        </ContentSection>

        {/* Liquidity */}
        <ContentSection delay={0.3}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Activity className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Liquidity</h2>
            </div>
            <div>
              <MetricRow label="Current Ratio" value={balanceSheet.current_ratio} metricKey="current_ratio" isRatio />
              <MetricRow label="Quick Ratio" value={balanceSheet.quick_ratio} metricKey="quick_ratio" isRatio />
              <MetricRow label="Cash & Short-term Investments" value={balanceSheet.cash_and_short_term} metricKey="cash_and_short_term" />
            </div>
          </div>
        </ContentSection>
      </div>
    </div>
  );
};