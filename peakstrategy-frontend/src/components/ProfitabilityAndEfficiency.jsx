import React from 'react';
import { TrendingUp, Shield, BarChart3, Target, Zap, Lightbulb } from 'lucide-react';

export const ProfitabilityAndEfficiency = ({ financialData }) => {
  if (!financialData) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <p className="text-slate-600">No financial data available</p>
          </div>
        </div>
      </div>
    );
  }

  if (financialData.error) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm">
            <p className="text-red-600">{financialData.error}</p>
          </div>
        </div>
      </div>
    );
  }

  const { metrics, trends, operating_leverage, ticker } = financialData;

  if(financialData){
    console.log("ProfitabilityAndEfficiency financialData:", financialData);
  }

  const formatPercent = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return `${value.toFixed(2)}%`;
  };

  const formatCurrency = (value) => {
    if (value === null || value === undefined) return 'N/A';
    return new Intl.NumberFormat('en-US', {
      style: 'currency',
      currency: 'USD',
      notation: 'compact',
      maximumFractionDigits: 2
    }).format(value);
  };

  const getQualityRating = (roic) => {
    if (!roic) return { label: 'Insufficient Data', color: 'bg-slate-100 text-slate-700 border-slate-300' };
    if (roic >= 15) return { label: 'Excellent', color: 'bg-emerald-100 text-emerald-700 border-emerald-300' };
    if (roic >= 10) return { label: 'Good', color: 'bg-emerald-50 text-emerald-600 border-emerald-200' };
    if (roic >= 5) return { label: 'Fair', color: 'bg-amber-100 text-amber-700 border-amber-300' };
    return { label: 'Poor', color: 'bg-red-100 text-red-700 border-red-300' };
  };

  const qualityRating = getQualityRating(metrics.roic);

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
        
        {/* Hero Header */}
        <div className="mb-14 relative opacity-0 animate-fade-in" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-2">
            Profitability & Efficiency
          </h1>
          <p className="text-slate-600 text-sm mt-1">Quality of Business Analysis • {ticker}</p>
        </div>

        {/* Key Quality Indicator - ROIC Highlighted */}
        <ContentSection delay={0.2}>
          <div className={`mb-16 rounded-lg border p-8 shadow-sm hover:shadow-md transition-shadow duration-300 ${qualityRating.color}`}>
            <div className="flex flex-col md:flex-row justify-between items-start md:items-center gap-6">
              <div className="flex-1">
                <div className="flex items-center gap-3 mb-3">
                  <div className="w-10 h-10 rounded-lg bg-white/50 flex items-center justify-center">
                    <Target className="text-slate-700" size={24} />
                  </div>
                  <div className="text-xs font-semibold text-slate-700 uppercase tracking-wide">
                    Return on Invested Capital (ROIC) ⭐
                  </div>
                </div>
                <div className="text-4xl font-bold mb-2 text-slate-900">
                  {formatPercent(metrics.roic)}
                </div>
                <div className="text-sm text-slate-700">
                  Capital Efficiency & Competitive Advantage
                </div>
              </div>
              <div className={`px-6 py-3 rounded-lg border font-semibold text-base ${qualityRating.color}`}>
                {qualityRating.label}
              </div>
            </div>
          </div>
        </ContentSection>

        {/* Core Return Metrics */}
        <ContentSection delay={0.3}>
          <div className="mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <TrendingUp className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Return Metrics</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <MetricCard title="ROE" value={formatPercent(metrics.roe)} subtitle="Return on Equity" />
              <MetricCard title="ROA" value={formatPercent(metrics.roa)} subtitle="Return on Assets" />
              <MetricCard title="ROIC" value={formatPercent(metrics.roic)} subtitle="Return on Invested Capital" highlight />
            </div>
          </div>
        </ContentSection>

        {/* Margin Analysis */}
        <ContentSection delay={0.4}>
          <div className="mb-16">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <BarChart3 className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Margin Profile</h2>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              <MetricCard title="Gross Margin" value={formatPercent(metrics.gross_margin)} subtitle="Pricing Power" />
              <MetricCard title="Operating Margin" value={formatPercent(metrics.operating_margin)} subtitle="Operational Efficiency" />
              <MetricCard title="Net Margin" value={formatPercent(metrics.net_margin)} subtitle="Bottom Line Profitability" />
            </div>
          </div>
        </ContentSection>

        {/* Trend Analysis */}
        {trends && (
          <>
            {/* Margin Trends */}
            <ContentSection delay={0.5}>
              <div className="mb-16">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <Shield className="text-slate-600" size={24} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">Margin Trends (5-Year)</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TrendTable 
                    title="Gross Margin Trend" 
                    data={trends.gross_margin_trend} 
                    formatter={formatPercent}
                  />
                  <TrendTable 
                    title="Operating Margin Trend" 
                    data={trends.operating_margin_trend} 
                    formatter={formatPercent}
                  />
                </div>
              </div>
            </ContentSection>

            {/* Return Trends */}
            <ContentSection delay={0.6}>
              <div className="mb-16">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <Zap className="text-slate-600" size={24} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">Return Trends (5-Year)</h2>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <TrendTable 
                    title="ROE Trend" 
                    data={trends.roe_trend} 
                    formatter={formatPercent}
                  />
                  <TrendTable 
                    title="ROIC Trend" 
                    data={trends.roic_trend} 
                    formatter={formatPercent}
                    highlight
                  />
                </div>
              </div>
            </ContentSection>
          </>
        )}

        {/* Operating Leverage */}
        {operating_leverage && operating_leverage.data && operating_leverage.data.length > 0 && (
          <ContentSection delay={0.7}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-2">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <BarChart3 className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Operating Leverage Analysis</h2>
              </div>
              <p className="text-sm text-slate-600 mb-6 ml-13">
                {operating_leverage.interpretation}
              </p>
              <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
                <table className="w-full">
                  <thead>
                    <tr className="bg-slate-50 border-b border-slate-200">
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Year</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Revenue Growth</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Operating Income Growth</th>
                      <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Leverage Ratio</th>
                    </tr>
                  </thead>
                  <tbody>
                    {operating_leverage.data.map((item, idx) => (
                      <tr key={idx} className={`border-b border-slate-200 hover:bg-slate-50 transition-colors ${
                        idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                      }`}>
                        <td className="px-4 py-3 font-semibold text-slate-900">{item.year}</td>
                        <td className="px-4 py-3 text-slate-700">{formatPercent(item.revenue_growth)}</td>
                        <td className="px-4 py-3 text-slate-700">{formatPercent(item.operating_income_growth)}</td>
                        <td className={`px-4 py-3 font-bold ${
                          item.leverage_ratio > 1 ? 'text-emerald-600' : item.leverage_ratio < 1 ? 'text-red-600' : 'text-slate-900'
                        }`}>
                          {item.leverage_ratio ? item.leverage_ratio.toFixed(2) + 'x' : 'N/A'}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          </ContentSection>
        )}

        {/* Interpretation Guide */}
        <ContentSection delay={0.8}>
          <div className="relative rounded-lg overflow-hidden p-8 text-white">
            <div className="absolute inset-0 bg-gradient-to-br from-slate-800 via-slate-700 to-slate-900"></div>
            <div className="absolute inset-0 opacity-5" style={{
              backgroundImage: 'linear-gradient(45deg, #ffffff 1px, transparent 1px)',
              backgroundSize: '20px 20px'
            }}></div>
            <div className="relative flex items-start gap-4">
              <div className="w-10 h-10 rounded-lg bg-white/20 flex items-center justify-center flex-shrink-0 mt-0.5">
                <Lightbulb className="text-white" size={24} />
              </div>
              <div>
                <h2 className="text-xl font-bold mb-3">Quality Business Indicators</h2>
                <ul className="space-y-2 text-base leading-relaxed opacity-95">
                  <li><strong>ROIC &gt; 15%:</strong> Indicates strong competitive advantage and efficient capital allocation</li>
                  <li><strong>ROE &gt; 15%:</strong> Management effectively generating returns for shareholders</li>
                  <li><strong>Stable/Expanding Margins:</strong> Pricing power and operational discipline</li>
                  <li><strong>Operating Leverage &gt; 1:</strong> Scalable business model with operating efficiency</li>
                </ul>
              </div>
            </div>
          </div>
        </ContentSection>

      </div>
    </div>
  );
};

// Supporting Components
const MetricCard = ({ title, value, subtitle, highlight }) => (
  <div className={`rounded-lg p-5 border transition-all duration-300 hover:shadow-sm ${
    highlight 
      ? 'border-slate-300 bg-gradient-to-br from-slate-50 to-blue-50' 
      : 'border-slate-200 bg-white hover:border-slate-300'
  }`}>
    <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
      {title}
    </div>
    <div className="text-2xl font-bold text-slate-900 mb-2">
      {value}
    </div>
    <div className="text-xs text-slate-600">
      {subtitle}
    </div>
  </div>
);

const TrendTable = ({ title, data, formatter, highlight }) => (
  <div className={`rounded-lg border p-5 bg-white shadow-sm hover:shadow-md transition-shadow duration-300 ${
    highlight ? 'border-slate-300' : 'border-slate-200'
  }`}>
    <div className="text-sm font-bold text-slate-900 mb-4">
      {title}
    </div>
    <div className="overflow-x-auto border border-slate-200 rounded-lg">
      <table className="w-full">
        <thead>
          <tr className={`border-b border-slate-200 ${highlight ? 'bg-slate-50' : 'bg-slate-50'}`}>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Year</th>
            <th className="px-4 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wide">Value</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr key={idx} className={`border-b border-slate-200 hover:bg-slate-50 transition-colors ${
              idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
            }`}>
              <td className="px-4 py-3 text-sm text-slate-700">{item.year}</td>
              <td className="px-4 py-3 text-sm font-bold text-slate-900">
                {formatter(item.value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);