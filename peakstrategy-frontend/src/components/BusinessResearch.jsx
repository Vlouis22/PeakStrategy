import React, { useState, useEffect } from 'react';
import { Building2, Users, Target, Briefcase, Globe, TrendingUp, Shield, MapPin, Phone, ExternalLink, Calendar, Lightbulb } from 'lucide-react';

export const BusinessResearch = ({ data }) => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (data) {
      setLoading(false);
    }
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
        <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
          <div className="animate-pulse space-y-6">
            <div className="h-16 bg-slate-200 rounded w-2/5"></div>
            <div className="grid grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="h-32 bg-slate-200 rounded"></div>
              ))}
            </div>
            <div className="h-64 bg-slate-200 rounded"></div>
          </div>
        </div>
      </div>
    );
  }

  const formatNumber = (value) => {
    if (value === 'N/A' || value === null || value === undefined) return 'N/A';
    if (typeof value === 'number') {
      return value.toLocaleString();
    }
    return value;
  };

  const ceo = data.leadershipGovernance?.ceo;
  const overview = data.companyOverview;
  const businessModel = data.businessModel;
  const products = data.productsServices;
  const position = data.strategicPosition;
  const operations = data.operationalMetrics;

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
            Business Understanding
          </h1>
        </div>
        {/* Company Overview Section */}
        {overview?.oneLineSummary && (
          <ContentSection delay={0.3}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Target className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Company Overview</h2>
              </div>
              <p className="text-slate-700 leading-relaxed">
                {overview.oneLineSummary}
              </p>
            </div>
          </ContentSection>
        )}

        {/* Key Metrics Bar */}
        <ContentSection delay={0.2}>
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-16">
            <div className="bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-all duration-300 group">
              <div className="flex items-center gap-2 mb-2">
                <Users className="w-4 h-4 text-slate-400 group-hover:text-slate-500 transition-colors" />
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Employees</span>
              </div>
              <p className="text-sm font-semibold text-slate-900">
                {formatNumber(operations?.employees)}
              </p>
            </div>

            <div className="bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-all duration-300 group">
              <div className="flex items-center gap-2 mb-2">
                <MapPin className="w-4 h-4 text-slate-400 group-hover:text-slate-500 transition-colors" />
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Headquarters</span>
              </div>
              <p className="text-sm font-semibold text-slate-900">
                {overview?.headquarters?.city}
              </p>
              <p className="text-xs text-slate-600 mt-0.5">{overview?.headquarters?.country}</p>
            </div>

            <div className="bg-white rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-all duration-300 group">
              <div className="flex items-center gap-2 mb-2">
                <Calendar className="w-4 h-4 text-slate-400 group-hover:text-slate-500 transition-colors" />
                <span className="text-xs font-semibold text-slate-500 uppercase tracking-wide">Founded</span>
              </div>
              <p className="text-sm font-semibold text-slate-900">
                {overview?.founded}
              </p>
            </div>
          </div>
        </ContentSection>

        {/* Leadership & Governance */}
        <ContentSection delay={0.4}>
          <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
            <div className="flex items-center gap-3 mb-6">
              <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                <Users className="text-slate-600" size={24} />
              </div>
              <h2 className="text-xl font-bold text-slate-900">Leadership & Governance</h2>
            </div>

            {/* CEO Section */}
            {ceo && ceo.name !== 'N/A' && (
              <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg p-6 mb-6 border border-slate-200">
                <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
                  Chief Executive Officer
                </div>
                <div className="text-2xl font-bold text-slate-900 mb-1">
                  {ceo.name}
                </div>
                <div className="text-slate-700">{ceo.title}</div>
              </div>
            )}

            {/* C-Suite Executives */}
            {data.leadershipGovernance?.cSuite && data.leadershipGovernance.cSuite.length > 0 && (
              <div className="mb-6">
                <h3 className="text-base font-bold text-slate-900 mb-3">Executive Leadership</h3>
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                  {data.leadershipGovernance.cSuite.map((exec, idx) => (
                    <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200 hover:border-slate-300 transition-all duration-300">
                      <div className="font-semibold text-slate-900">{exec.name}</div>
                      <div className="text-sm text-slate-600 mt-1">{exec.title}</div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Governance Risks */}
            {data.leadershipGovernance?.governance && (
              <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900 mb-4 uppercase tracking-wide">Governance Risk Assessment</h3>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div>
                    <div className="text-xs text-slate-600 mb-1">Overall Risk</div>
                    <div className="text-base font-bold text-slate-900">
                      {data.leadershipGovernance.governance.overallRisk}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-600 mb-1">Board Risk</div>
                    <div className="text-base font-bold text-slate-900">
                      {data.leadershipGovernance.governance.boardRisk}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-600 mb-1">Audit Risk</div>
                    <div className="text-base font-bold text-slate-900">
                      {data.leadershipGovernance.governance.auditRisk}
                    </div>
                  </div>
                  <div>
                    <div className="text-xs text-slate-600 mb-1">Compensation Risk</div>
                    <div className="text-base font-bold text-slate-900">
                      {data.leadershipGovernance.governance.compensationRisk}
                    </div>
                  </div>
                </div>
              </div>
            )}
          </div>
        </ContentSection>

        {/* Business Model */}
        {businessModel && (
          <ContentSection delay={0.5}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Briefcase className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Business Model & Revenue Strategy</h2>
              </div>
              
              {businessModel.description && (
                <p className="text-slate-700 leading-relaxed mb-6">
                  {businessModel.description}
                </p>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                {businessModel.revenueModel && (
                  <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                    <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Revenue Model</h3>
                    <p className="text-slate-700 text-sm leading-relaxed">{businessModel.revenueModel}</p>
                  </div>
                )}
                
                {businessModel.customerSegments && (
                  <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                    <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Customer Segments</h3>
                    <p className="text-slate-700 text-sm leading-relaxed">{businessModel.customerSegments}</p>
                  </div>
                )}
              </div>
            </div>
          </ContentSection>
        )}

        {/* Products & Services */}
        {products && (
          <ContentSection delay={0.6}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <Shield className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Products & Services</h2>
              </div>
              
              {products.coreFocus && (
                <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg p-5 border border-slate-200 mb-6">
                  <p className="text-slate-700 leading-relaxed">
                    {products.coreFocus}
                  </p>
                </div>
              )}

              <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                {products.primaryOfferings && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-slate-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-sm font-semibold text-slate-900">Primary Focus</div>
                      <div className="text-sm text-slate-600 mt-1 leading-relaxed">{products.primaryOfferings}</div>
                    </div>
                  </div>
                )}
                {products.industry && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-slate-600 rounded-full mt-2 flex-shrink-0"></div>
                    <div>
                      <div className="text-sm font-semibold text-slate-900">Industry Classification</div>
                      <div className="text-sm text-slate-600 mt-1 leading-relaxed">{products.industry}</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ContentSection>
        )}

        {/* Strategic Position & Competitive Landscape */}
        {position && (
          <ContentSection delay={0.7}>
            <div className="mb-16 bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <TrendingUp className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Strategic Position & Competitive Landscape</h2>
              </div>

              <div className="space-y-6">
                {position.marketPosition && (
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Market Position</h3>
                    <p className="text-slate-700 leading-relaxed">{position.marketPosition}</p>
                  </div>
                )}

                <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
                  {position.geographicPresence && (
                    <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                      <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wide">Geographic Presence</h3>
                      <div className="text-sm text-slate-700 space-y-1">
                        {position.geographicPresence.headquarters && (
                          <div><span className="font-semibold">HQ:</span> {position.geographicPresence.headquarters}</div>
                        )}
                        {position.geographicPresence.scope && (
                          <div><span className="font-semibold">Scope:</span> {position.geographicPresence.scope}</div>
                        )}
                      </div>
                    </div>
                  )}

                  {position.competitiveAdvantage && (
                    <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                      <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wide">Competitive Advantage</h3>
                      <p className="text-sm text-slate-700 leading-relaxed">{position.competitiveAdvantage}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </ContentSection>
        )}

        {/* Contact & Operations */}
        {operations && (
          <ContentSection delay={0.8}>
            <div className="bg-white rounded-lg border border-slate-200 p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
              <div className="flex items-center gap-3 mb-6">
                <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                  <MapPin className="text-slate-600" size={24} />
                </div>
                <h2 className="text-xl font-bold text-slate-900">Corporate Information</h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                {operations.locations && (
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Address</h3>
                    <div className="text-sm text-slate-700 space-y-1">
                      {operations.locations.headquarters && <div>{operations.locations.headquarters}</div>}
                      {operations.locations.country && <div>{operations.locations.country}</div>}
                    </div>
                  </div>
                )}

                <div>
                  <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Contact</h3>
                  <div className="text-sm text-slate-700 space-y-2">
                    {operations.phone && (
                      <div className="flex items-center gap-2">
                        <Phone className="w-4 h-4 text-slate-400" />
                        <span>{operations.phone}</span>
                      </div>
                    )}
                    {operations.website && operations.website !== 'N/A' && (
                      <a 
                        href={operations.website} 
                        target="_blank" 
                        rel="noopener noreferrer"
                        className="flex items-center gap-2 text-slate-600 hover:text-slate-900 transition-colors"
                      >
                        <ExternalLink className="w-4 h-4" />
                        <span>Corporate Website</span>
                      </a>
                    )}
                  </div>
                </div>

                {operations.exchange && (
                  <div>
                    <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Exchange Listing</h3>
                    <div className="text-sm text-slate-700 space-y-1">
                      {operations.exchange.listing && <div>{operations.exchange.listing}</div>}
                      {operations.exchange.symbol && (
                        <div className="font-mono font-semibold text-slate-900 mt-1">{operations.exchange.symbol}</div>
                      )}
                    </div>
                  </div>
                )}
              </div>
            </div>
          </ContentSection>
        )}

      </div>
    </div>
  );
};