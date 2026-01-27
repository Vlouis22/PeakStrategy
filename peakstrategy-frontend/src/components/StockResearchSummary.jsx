import React, { useState, useEffect } from 'react';
import { 
  TrendingUp, Shield, DollarSign, BarChart3, Sparkles, AlertCircle, 
  CheckCircle2, Newspaper, Users, MapPin, Calendar, Briefcase, Target,
  ArrowRight, Lightbulb, TrendingDown
} from 'lucide-react';

export const StockResearchSummary = ({ 
  company_name,
  company_logo_url, 
  scoring_pillars, 
  shareholder_returns, 
  ceo, 
  year_founded, 
  employees, 
  location, 
  price_targets, 
  summary_data,
  onMetricClick
}) => {
  const [logoLoaded, setLogoLoaded] = useState(false);
  const [logoError, setLogoError] = useState(false);

  // Helper function to safely format numbers
  const formatNumber = (num) => {
    if (!num || typeof num !== 'number') return null;
    if (num >= 1000000) return `${(num / 1000000).toFixed(1)}M`;
    if (num >= 1000) return `${(num / 1000).toFixed(1)}k`;
    return num.toString();
  };

  const formatCurrency = (num) => {
    if (!num || typeof num !== 'number') return null;
    return `$${num.toFixed(2)}`;
  };

  const scoringPillars = scoring_pillars || {};
  const companyName = company_name || 'Unknown Company';
  const ticker = summary_data?.ticker || price_targets?.ticker || '';
  const sector = summary_data?.snapshot?.metrics?.sector || '';
  const price = summary_data?.snapshot?.metrics?.price || price_targets?.price_targets?.current_price || '';
  const dayChange = summary_data?.snapshot?.metrics?.day || '';

  const companySummary = summary_data?.company_summary || {};
  const description = companySummary.description || {};
  const bullCase = companySummary.bull_case || [];
  const bearCase = companySummary.bear_case || [];
  const macroSensitivity = companySummary.macro_sensitivity || {};
  const latestHeadline = companySummary.latest_high_impact_headline || {};
  const investorTakeaway = companySummary.investor_takeaway || '';

  // Company Logo with improved fallback using company_logo_url prop
  const CompanyLogo = () => {
    const logoUrl = company_logo_url || `https://logo.clearbit.com/${ticker?.toLowerCase()}.com?size=200`;
    
    return (
      <div className="flex items-center gap-6 mb-6 opacity-0 animate-fade-in" style={{ animationDelay: '0.1s', animationFillMode: 'forwards' }}>
        <div className="relative group">
          {!logoError ? (
            <div className="w-24 h-24 rounded-2xl bg-white border-2 border-slate-200 overflow-hidden shadow-md hover:shadow-lg transition-shadow duration-300 flex items-center justify-center flex-shrink-0">
              <img
                src={logoUrl}
                alt={companyName}
                className="w-full h-full object-contain p-3"
                onLoad={() => setLogoLoaded(true)}
                onError={() => {
                  setLogoError(true);
                  setLogoLoaded(false);
                }}
              />
              {!logoLoaded && !logoError && (
                <div className="absolute inset-0 bg-gradient-to-br from-slate-100 to-slate-200 animate-pulse"></div>
              )}
            </div>
          ) : (
            <div className="w-24 h-24 rounded-2xl bg-gradient-to-br from-slate-700 to-slate-900 flex items-center justify-center text-white text-3xl font-bold shadow-md flex-shrink-0">
              {ticker?.charAt(0) || 'C'}
            </div>
          )}
        </div>

        <div className="flex-1">
          <div className="flex items-baseline gap-3 mb-2">
            <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight">
              {companyName}
            </h1>
            {ticker && (
              <span className="font-mono font-semibold text-slate-600 bg-slate-100 px-3 py-1 rounded-lg text-lg">
                {ticker.toUpperCase()}
              </span>
            )}
          </div>
          
          {sector && (
            <div className="inline-flex mb-3">
              <span className="px-3 py-1 rounded-full text-xs font-semibold bg-slate-100 text-slate-700 uppercase tracking-wide">
                {sector}
              </span>
            </div>
          )}

          <div className="flex items-center gap-4">
            {price && (
              <span className="text-2xl font-bold text-slate-900">
                {formatCurrency(typeof price === 'number' ? price : parseFloat(price))}
              </span>
            )}
            {dayChange && (
              <span className={`font-semibold text-base ${dayChange?.toString?.().startsWith('+') ? 'text-emerald-600' : dayChange?.toString?.().startsWith('-') ? 'text-red-600' : 'text-slate-600'}`}>
                {dayChange}
              </span>
            )}
          </div>
        </div>
      </div>
    );
  };

  // Company Info Section
  const CompanyInfo = () => {
    const infoItems = [];
    
    if (year_founded) {
      const yearStr = typeof year_founded === 'number' ? year_founded.toString() : year_founded;
      infoItems.push({ icon: Calendar, label: 'Founded', value: yearStr });
    }
    
    if (ceo) {
      const ceoName = typeof ceo === 'string' ? ceo : ceo?.name || ceo?.title || 'CEO';
      infoItems.push({ icon: Briefcase, label: 'CEO', value: ceoName });
    }
    
    if (employees) {
      const formattedEmployees = formatNumber(employees);
      if (formattedEmployees) {
        infoItems.push({ icon: Users, label: 'Employees', value: formattedEmployees });
      }
    }

    if (location) {
      const locationString = typeof location === 'string' 
        ? location 
        : location?.headquarters || location?.country || null;
      if (locationString) {
        infoItems.push({ icon: MapPin, label: 'Headquarters', value: locationString });
      }
    }

    if (infoItems.length === 0) return null;

    return (
      <div className="mt-8 opacity-0 animate-fade-in" style={{ animationDelay: '0.25s', animationFillMode: 'forwards' }}>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {infoItems.map((item, idx) => {
            const Icon = item.icon;
            return (
              <div 
                key={idx}
                className="bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-all duration-300 group"
              >
                <div className="flex items-center gap-2 mb-2">
                  <Icon className="w-4 h-4 text-slate-400 group-hover:text-slate-500 transition-colors" />
                  <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">{item.label}</span>
                </div>
                <p className="text-sm font-semibold text-slate-900">{item.value}</p>
              </div>
            );
          })}
        </div>
      </div>
    );
  };

  const pillarConfig = [
    { 
      title: 'Valuation', 
      key: 'Valuation',
      icon: DollarSign,
      color: 'from-emerald-500 to-teal-600',
      bgLight: 'bg-emerald-50',
      textColor: 'text-emerald-600',
      borderColor: 'border-emerald-200',
      accentColor: 'text-emerald-600'
    },
    { 
      title: 'Profitability', 
      key: 'Profitability',
      icon: TrendingUp,
      color: 'from-blue-500 to-indigo-600',
      bgLight: 'bg-blue-50',
      textColor: 'text-blue-600',
      borderColor: 'border-blue-200',
      accentColor: 'text-blue-600'
    },
    { 
      title: 'Financial Health', 
      key: 'Financial Health',
      icon: Shield,
      color: 'from-purple-500 to-violet-600',
      bgLight: 'bg-purple-50',
      textColor: 'text-purple-600',
      borderColor: 'border-purple-200',
      accentColor: 'text-purple-600'
    },
    { 
      title: 'Shareholder Returns', 
      key: 'Shareholder Returns',
      icon: Sparkles,
      color: 'from-amber-500 to-orange-600',
      bgLight: 'bg-amber-50',
      textColor: 'text-amber-600',
      borderColor: 'border-amber-200',
      accentColor: 'text-amber-600'
    },
    { 
      title: 'Growth Outlook', 
      key: 'Growth Outlook',
      icon: BarChart3,
      color: 'from-rose-500 to-red-600',
      bgLight: 'bg-rose-50',
      textColor: 'text-rose-600',
      borderColor: 'border-rose-200',
      accentColor: 'text-rose-600'
    },
  ];

  const ScorePillarCard = ({ pillar, rating, index }) => {
    const Icon = pillar.icon;
    const validRating = rating === null || rating === undefined || rating < 1 || rating > 5 ? null : rating;
    
    return (
      <div 
        className="opacity-0 animate-fade-in"
        style={{ animationDelay: `${0.35 + index * 0.06}s`, animationFillMode: 'forwards' }}
      >
        <button
          onClick={() => onMetricClick && onMetricClick(pillar.title)}
          className="h-full w-full bg-white rounded-lg p-5 border border-slate-200 hover:border-slate-400 hover:shadow-md transition-all duration-300 flex flex-col cursor-pointer group text-left"
        >
          <div className="flex items-start justify-between mb-4">
            <div className={`${pillar.bgLight} p-2.5 rounded-lg group-hover:scale-110 transition-transform duration-300`}>
              <Icon className={`${pillar.textColor} w-5 h-5`} />
            </div>
            {validRating !== null && (
              <div className="flex flex-col items-end">
                <span className={`text-xl font-bold ${pillar.accentColor}`}>{validRating.toFixed(1)}</span>
                <span className="text-xs text-slate-400">of 5</span>
              </div>
            )}
          </div>
          
          <h3 className="text-sm font-semibold text-slate-900 mb-3 flex-grow">{pillar.title}</h3>
          
          {validRating === null ? (
            <span className="text-xs text-slate-400">No data available</span>
          ) : (
            <div className="w-full bg-slate-200 h-1.5 rounded-full overflow-hidden">
              <div 
                className={`h-full rounded-full transition-all duration-500 bg-gradient-to-r ${pillar.color}`}
                style={{ width: `${(validRating / 5) * 100}%` }}
              />
            </div>
          )}

          <div className="mt-4 flex items-center gap-2 text-slate-400 group-hover:text-slate-600 transition-colors opacity-0 group-hover:opacity-100">
            <span className="text-xs font-semibold">View Details</span>
            <ArrowRight className="w-3 h-3" />
          </div>
        </button>
      </div>
    );
  };

  const getAnalystSentiment = () => {
    const consensusData = price_targets?.consensus_history?.[0];
    if (!consensusData) return null;
    
    const breakdown = consensusData.breakdown_pct || {};
    const strong_buy = Number(breakdown.strong_buy) || 0;
    const buy = Number(breakdown.buy) || 0;
    const hold = Number(breakdown.hold) || 0;
    const sell = Number(breakdown.sell) || 0;
    const strong_sell = Number(breakdown.strong_sell) || 0;
    
    const bullishPct = strong_buy + buy;
    const neutralPct = hold;
    const bearishPct = sell + strong_sell;

    const currentPrice = price_targets?.price_targets?.current_price || 0;
    const avgTarget = price_targets?.price_targets?.average || 0;
    const upsideDownside = currentPrice > 0 ? ((avgTarget - currentPrice) / currentPrice) * 100 : 0;

    return {
      bullishPct,
      neutralPct,
      bearishPct,
      totalAnalysts: consensusData.total_analysts || 0,
      currentPrice,
      avgTarget,
      upsideDownside
    };
  };

  const analystSentiment = getAnalystSentiment();

  const getShareholderReturnsSummary = () => {
    const dividends = shareholder_returns?.dividends || {};
    const buybacks = shareholder_returns?.buybacks || {};
    
    return { 
      hasDividend: dividends.has_dividend === true, 
      dividendYield: dividends.dividend_yield,
      hasPayoutRatio: dividends.payout_ratio !== null && dividends.payout_ratio !== undefined, 
      payoutRatio: dividends.payout_ratio,
      isBuyingBack: buybacks.is_buying_back === true,
      buybackYield: buybacks.buyback_yield,
      currentPrice: shareholder_returns?.current_price
    };
  };

  const shareholderReturnsSummary = getShareholderReturnsSummary();

  const getMacroSummary = () => {
    const impacts = [];

    if (macroSensitivity.interest_rates?.impact) {
      impacts.push({ 
        category: 'Interest Rates', 
        impact: macroSensitivity.interest_rates.impact,
        explanation: macroSensitivity.interest_rates.explanation
      });
    }
    if (macroSensitivity.economic_cycles?.impact) {
      impacts.push({ 
        category: 'Economic Cycles', 
        impact: macroSensitivity.economic_cycles.impact,
        explanation: macroSensitivity.economic_cycles.explanation
      });
    }
    if (macroSensitivity.regulation_policy?.impact) {
      impacts.push({ 
        category: 'Regulation & Policy', 
        impact: macroSensitivity.regulation_policy.impact,
        explanation: macroSensitivity.regulation_policy.explanation
      });
    }
    if (macroSensitivity.currency_exposure?.impact) {
      impacts.push({ 
        category: 'Currency Exposure', 
        impact: macroSensitivity.currency_exposure.impact,
        explanation: macroSensitivity.currency_exposure.explanation
      });
    }

    return {
      impacts,
      hasHighImpact: impacts.some(i => i.impact === 'High'),
      hasMediumImpact: impacts.some(i => i.impact === 'Medium')
    };
  };

  const macroSummary = getMacroSummary();

  const getImpactColor = (impact) => {
    if (impact === 'High') return 'bg-red-50 border-red-200 text-red-700';
    if (impact === 'Medium') return 'bg-amber-50 border-amber-200 text-amber-700';
    return 'bg-green-50 border-green-200 text-green-700';
  };

  const getImpactDot = (impact) => {
    if (impact === 'High') return 'bg-red-500';
    if (impact === 'Medium') return 'bg-amber-500';
    return 'bg-green-500';
  };

  const getImpactBgColor = (impact) => {
    if (impact === 'High') return 'bg-red-100';
    if (impact === 'Medium') return 'bg-amber-100';
    return 'bg-green-100';
  };

  const getImpactTextColor = (impact) => {
    if (impact === 'High') return 'text-red-700';
    if (impact === 'Medium') return 'text-amber-700';
    return 'text-green-700';
  };

  // Content Section with Animation
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
        
        @keyframes slide-in-right {
          from {
            opacity: 0;
            transform: translateX(-10px);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }
        
        .animate-slide-in-right {
          animation: slide-in-right 0.5s cubic-bezier(0.4, 0, 0.2, 1) forwards;
        }
      `}</style>

      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        
        {/* Hero Header */}
        <div className="mb-14 relative">
          <CompanyLogo />
          <CompanyInfo />
        </div>

        {/* Key Metrics Section */}
        <div className="mb-16">
          <ContentSection delay={0.3}>
            <div className="mb-8">
              <h2 className="text-2xl font-bold text-slate-900 tracking-tight">Key Metrics</h2>
              <p className="text-slate-600 text-sm mt-1">Click any metric to view detailed analysis</p>
            </div>
          </ContentSection>
          
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {pillarConfig.map((pillar, idx) => (
              <ScorePillarCard
                key={pillar.key}
                pillar={pillar}
                rating={scoringPillars[pillar.key]?.rating}
                index={idx}
              />
            ))}
          </div>
        </div>

        {/* Company Overview Section */}
        {(description.line_1 || description.line_2 || description.line_3) && (
          <ContentSection delay={0.45}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Lightbulb className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Company Overview</h2>
              </div>
              <p className="text-slate-700 leading-relaxed">
                {[description.line_1, description.line_2, description.line_3].filter(Boolean).join(' ')}
              </p>
            </div>
          </ContentSection>
        )}

        {/* Bull & Bear Cases Section */}
        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8 mb-16">
          {/* Bull Case */}
          {bullCase.length > 0 && (
            <ContentSection delay={0.5}>
              <div className="h-full">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-emerald-100 flex items-center justify-center">
                    <CheckCircle2 className="text-emerald-600" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Bull Case</h2>
                    <p className="text-xs text-slate-500 mt-0.5">Key investment strengths</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {bullCase.slice(0, 5).map((point, idx) => (
                    <div 
                      key={idx}
                      className="bg-white border border-emerald-100 rounded-lg p-4 hover:border-emerald-300 hover:shadow-sm transition-all duration-300 group"
                    >
                      <h3 className="font-semibold text-emerald-700 text-sm mb-2 group-hover:text-emerald-800 transition-colors">
                        {point.title}
                      </h3>
                      <p className="text-slate-700 text-sm leading-relaxed">{point.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </ContentSection>
          )}

          {/* Bear Case */}
          {bearCase.length > 0 && (
            <ContentSection delay={0.55}>
              <div className="h-full">
                <div className="flex items-center gap-3 mb-6">
                  <div className="w-10 h-10 rounded-lg bg-red-100 flex items-center justify-center">
                    <AlertCircle className="text-red-600" size={24} />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-slate-900">Bear Case</h2>
                    <p className="text-xs text-slate-500 mt-0.5">Key investment risks</p>
                  </div>
                </div>
                <div className="space-y-3">
                  {bearCase.slice(0, 5).map((point, idx) => (
                    <div 
                      key={idx}
                      className="bg-white border border-red-100 rounded-lg p-4 hover:border-red-300 hover:shadow-sm transition-all duration-300 group"
                    >
                      <h3 className="font-semibold text-red-700 text-sm mb-2 group-hover:text-red-800 transition-colors">
                        {point.title}
                      </h3>
                      <p className="text-slate-700 text-sm leading-relaxed">{point.explanation}</p>
                    </div>
                  ))}
                </div>
              </div>
            </ContentSection>
          )}
        </div>

        {/* Analyst Sentiment & Price Target Section */}
        {analystSentiment && (
          <ContentSection delay={0.6}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-blue-100 flex items-center justify-center">
                  <Target className="text-blue-600" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">Analyst Sentiment & Price Target</h2>
                  <p className="text-xs text-slate-500 mt-0.5">{analystSentiment.totalAnalysts} analysts covering</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                  <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-2">Current Price</p>
                  <p className="text-3xl font-bold text-slate-900">{formatCurrency(analystSentiment.currentPrice)}</p>
                </div>
                <div className="bg-blue-50 rounded-lg p-4 border border-blue-200">
                  <p className="text-xs text-blue-600 font-semibold uppercase tracking-wide mb-2">Avg. Target</p>
                  <p className="text-3xl font-bold text-blue-600">{formatCurrency(analystSentiment.avgTarget)}</p>
                </div>
                <div className={`rounded-lg p-4 border-2 ${analystSentiment.upsideDownside > 0 ? 'bg-emerald-50 border-emerald-300' : analystSentiment.upsideDownside < 0 ? 'bg-red-50 border-red-300' : 'bg-slate-50 border-slate-200'}`}>
                  <p className={`text-xs font-semibold uppercase tracking-wide mb-2 ${analystSentiment.upsideDownside > 0 ? 'text-emerald-600' : analystSentiment.upsideDownside < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                    Upside/Downside
                  </p>
                  <p className={`text-3xl font-bold ${analystSentiment.upsideDownside > 0 ? 'text-emerald-600' : analystSentiment.upsideDownside < 0 ? 'text-red-600' : 'text-slate-600'}`}>
                    {analystSentiment.upsideDownside > 0 ? '+' : ''}{analystSentiment.upsideDownside.toFixed(1)}%
                  </p>
                </div>
              </div>

              <div>
                <p className="text-xs text-slate-500 font-semibold uppercase tracking-wide mb-16">Rating Distribution</p>
                <div className="flex items-end gap-2 h-20">
                  <div className="flex-1 flex flex-col items-center justify-end">
                    <div className="flex items-center justify-center mb-2 h-6">
                      <span className="text-xs font-bold text-emerald-700 bg-emerald-100 px-2 py-1 rounded">{analystSentiment.bullishPct}%</span>
                    </div>
                    <div className="w-full bg-emerald-500 rounded-t-lg transition-all duration-300" style={{ height: `${Math.max(analystSentiment.bullishPct * 0.8, 8)}px` }}></div>
                    <p className="text-xs text-slate-600 font-semibold mt-2">Buy</p>
                  </div>
                  <div className="flex-1 flex flex-col items-center justify-end">
                    <div className="flex items-center justify-center mb-2 h-6">
                      <span className="text-xs font-bold text-slate-700 bg-slate-200 px-2 py-1 rounded">{analystSentiment.neutralPct}%</span>
                    </div>
                    <div className="w-full bg-slate-400 rounded-t-lg transition-all duration-300" style={{ height: `${Math.max(analystSentiment.neutralPct * 0.8, 8)}px` }}></div>
                    <p className="text-xs text-slate-600 font-semibold mt-2">Hold</p>
                  </div>
                  <div className="flex-1 flex flex-col items-center justify-end">
                    <div className="flex items-center justify-center mb-2 h-6">
                      <span className="text-xs font-bold text-red-700 bg-red-100 px-2 py-1 rounded">{analystSentiment.bearishPct}%</span>
                    </div>
                    <div className="w-full bg-red-500 rounded-t-lg transition-all duration-300" style={{ height: `${Math.max(analystSentiment.bearishPct * 0.8, 8)}px` }}></div>
                    <p className="text-xs text-slate-600 font-semibold mt-2">Sell</p>
                  </div>
                </div>
              </div>
            </div>
          </ContentSection>
        )}

        {/* Shareholder Returns Section - SIMPLIFIED */}
        {shareholderReturnsSummary && (
          <ContentSection delay={0.65}>
            <div className="mb-16 bg-gradient-to-br from-amber-50 to-orange-50 rounded-lg border border-amber-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-amber-100 flex items-center justify-center">
                  <Sparkles className="text-amber-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Shareholder Returns</h2>
              </div>
              
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-6">
                {/* Current Price */}
                {shareholderReturnsSummary.currentPrice && (
                  <div className="bg-white rounded-lg p-4 border border-amber-100">
                    <p className="text-xs text-slate-600 font-semibold uppercase tracking-wide mb-2">Current Price</p>
                    <p className="text-2xl font-bold text-slate-900">{formatCurrency(shareholderReturnsSummary.currentPrice)}</p>
                  </div>
                )}

                {/* Dividend Yield */}
                {shareholderReturnsSummary.hasDividend && shareholderReturnsSummary.dividendYield !== null && (
                  <div className="bg-white rounded-lg p-4 border border-amber-100">
                    <p className="text-xs text-slate-600 font-semibold uppercase tracking-wide mb-2">Dividend Yield</p>
                    <p className="text-2xl font-bold text-amber-600">{shareholderReturnsSummary.dividendYield?.toFixed(2)}%</p>
                  </div>
                )}

                {/* Payout Ratio */}
                {shareholderReturnsSummary.hasPayoutRatio && shareholderReturnsSummary.payoutRatio !== null && (
                  <div className="bg-white rounded-lg p-4 border border-amber-100">
                    <p className="text-xs text-slate-600 font-semibold uppercase tracking-wide mb-2">Payout Ratio</p>
                    <p className="text-2xl font-bold text-slate-900">{shareholderReturnsSummary.payoutRatio?.toFixed(1)}%</p>
                  </div>
                )}

                {/* Buyback Yield */}
                {shareholderReturnsSummary.isBuyingBack && shareholderReturnsSummary.buybackYield !== null && (
                  <div className="bg-white rounded-lg p-4 border border-amber-100">
                    <p className="text-xs text-slate-600 font-semibold uppercase tracking-wide mb-2">Buyback Yield</p>
                    <p className="text-2xl font-bold text-amber-600">{shareholderReturnsSummary.buybackYield?.toFixed(2)}%</p>
                  </div>
                )}
              </div>

              <p className="text-slate-700 leading-relaxed text-sm">
                {shareholderReturnsSummary.hasDividend ? (
                  <>The company maintains an active dividend program with a sustainable payout ratio, demonstrating a commitment to returning capital to shareholders. </>
                ) : (
                  <>The company does not currently pay a dividend. </>
                )}
                {shareholderReturnsSummary.isBuyingBack ? (
                  <>Share repurchases complement the total shareholder return strategy, reducing share count and supporting per-share metrics.</>
                ) : (
                  <>The company is not currently executing share repurchases.</>
                )}
              </p>
            </div>
          </ContentSection>
        )}

        {/* Macro Sensitivity Section - EXPANDED */}
        {macroSummary.impacts.length > 0 && (
          <ContentSection delay={0.7}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-purple-100 flex items-center justify-center">
                  <BarChart3 className="text-purple-600" size={24} />
                </div>
                <div>
                  <h2 className="text-xl font-bold text-slate-900">Macro Sensitivity</h2>
                  <p className="text-xs text-slate-500 mt-0.5">Exposure to key economic drivers</p>
                </div>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {macroSummary.impacts.map((item, idx) => (
                  <div 
                    key={idx} 
                    className={`rounded-lg border p-5 transition-all duration-300 hover:shadow-sm ${getImpactColor(item.impact)}`}
                  >
                    <div className="flex items-start gap-3 mb-3">
                      <div className={`w-3 h-3 rounded-full mt-1 flex-shrink-0 ${getImpactDot(item.impact)}`}></div>
                      <div className="flex-1">
                        <p className="font-semibold text-sm">{item.category}</p>
                        <p className={`text-xs font-semibold mt-1 ${getImpactTextColor(item.impact)}`}>{item.impact} Impact</p>
                      </div>
                    </div>
                    {item.explanation && (
                      <p className="text-sm leading-relaxed opacity-90">{item.explanation}</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          </ContentSection>
        )}

        {/* Latest High-Impact Headline Section */}
        {latestHeadline.headline && (
          <ContentSection delay={0.75}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-cyan-100 flex items-center justify-center">
                  <Newspaper className="text-cyan-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Latest High-Impact Headline</h2>
              </div>
              <h3 className="font-semibold text-slate-900 mb-3 text-base leading-relaxed">{latestHeadline.headline}</h3>
              {latestHeadline.why_it_matters && (
                <p className="text-slate-700 leading-relaxed text-sm">{latestHeadline.why_it_matters}</p>
              )}
            </div>
          </ContentSection>
        )}

        {/* Investor Takeaway Section */}
        {investorTakeaway && (
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
                  <h2 className="text-xl font-bold mb-3">Investor Takeaway</h2>
                  <p className="text-base leading-relaxed opacity-95">{investorTakeaway}</p>
                </div>
              </div>
            </div>
          </ContentSection>
        )}

      </div>
    </div>
  );
};