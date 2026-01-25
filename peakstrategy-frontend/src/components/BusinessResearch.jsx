import React, { useState, useEffect } from 'react';
import { Building2, Users, Target, Briefcase, Globe, TrendingUp, Shield, MapPin, Phone, ExternalLink } from 'lucide-react';

export const BusinessResearch = ({ data }) => {
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (data) {
      setLoading(false);
    }
  }, [data]);

  if (loading) {
    return (
      <div className="min-h-screen bg-slate-50 p-8">
        <div className="max-w-7xl mx-auto">
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

  return (
    <div className="min-h-screen bg-slate-50">
      <div className="max-w-7xl mx-auto p-8">

        {/* Key Metrics Bar */}
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <Users className="w-5 h-5 text-blue-600" />
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Employees</div>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {formatNumber(operations?.employees)}
            </div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <MapPin className="w-5 h-5 text-blue-600" />
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Headquarters</div>
            </div>
            <div className="text-lg font-bold text-slate-900">
              {overview?.headquarters?.city}
            </div>
            <div className="text-sm text-slate-600">{overview?.headquarters?.country}</div>
          </div>

          <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-5">
            <div className="flex items-center gap-2 mb-2">
              <TrendingUp className="w-5 h-5 text-blue-600" />
              <div className="text-xs font-semibold text-slate-600 uppercase tracking-wide">Founded</div>
            </div>
            <div className="text-2xl font-bold text-slate-900">
              {overview?.founded}
            </div>
          </div>
        </div>

        {/* Company Overview Section */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Target className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Company Overview</h2>
          </div>
          <p className="text-slate-700 text-lg leading-relaxed">
            {overview?.oneLineSummary}
          </p>
        </div>

        {/* Leadership & Governance */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-5">
            <Users className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Leadership & Governance</h2>
          </div>

          {/* CEO Section */}
          {ceo && ceo.name !== 'N/A' && (
            <div className="bg-gradient-to-r from-blue-50 to-indigo-50 rounded-lg p-6 mb-6 border-2 border-blue-200">
              <div className="text-sm font-semibold text-blue-800 uppercase tracking-wide mb-1">
                Chief Executive Officer
              </div>
              <div className="text-2xl font-bold text-slate-900 mb-1">
                {ceo.name}
              </div>
              <div className="text-slate-700">{ceo.title}</div>
              {ceo.age && ceo.age !== 'N/A' && (
                <div className="text-sm text-slate-600 mt-2">Age: {ceo.age}</div>
              )}
            </div>
          )}

          {/* C-Suite Executives */}
          {data.leadershipGovernance?.cSuite && data.leadershipGovernance.cSuite.length > 0 && (
            <div className="mb-6">
              <h3 className="text-lg font-bold text-slate-900 mb-3">Executive Leadership</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {data.leadershipGovernance.cSuite.map((exec, idx) => (
                  <div key={idx} className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                    <div className="font-bold text-slate-900">{exec.name}</div>
                    <div className="text-sm text-slate-600 mt-1">{exec.title}</div>
                    {exec.age && exec.age !== 'N/A' && (
                      <div className="text-xs text-slate-500 mt-2">Age: {exec.age}</div>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Governance Risks */}
          {data.leadershipGovernance?.governance && (
            <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
              <h3 className="text-sm font-bold text-slate-900 mb-3 uppercase tracking-wide">Governance Risk Assessment</h3>
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-xs text-slate-600 mb-1">Overall Risk</div>
                  <div className="text-lg font-bold text-slate-900">
                    {data.leadershipGovernance.governance.overallRisk}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Board Risk</div>
                  <div className="text-lg font-bold text-slate-900">
                    {data.leadershipGovernance.governance.boardRisk}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Audit Risk</div>
                  <div className="text-lg font-bold text-slate-900">
                    {data.leadershipGovernance.governance.auditRisk}
                  </div>
                </div>
                <div>
                  <div className="text-xs text-slate-600 mb-1">Compensation Risk</div>
                  <div className="text-lg font-bold text-slate-900">
                    {data.leadershipGovernance.governance.compensationRisk}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>

        {/* Business Model */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Briefcase className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Business Model & Revenue Strategy</h2>
          </div>
          
          <div className="prose max-w-none">
            <p className="text-slate-700 text-base leading-relaxed mb-6">
              {businessModel?.description}
            </p>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Revenue Model</h3>
                <p className="text-slate-700 text-sm">{businessModel?.revenueModel}</p>
              </div>
              
              <div className="bg-slate-50 rounded-lg p-5 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Customer Segments</h3>
                <p className="text-slate-700 text-sm">{businessModel?.customerSegments}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Products & Services */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <Shield className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Products & Services</h2>
          </div>
          
          <div className="bg-gradient-to-br from-slate-50 to-blue-50 rounded-lg p-5 border border-slate-200 mb-4">
            <p className="text-slate-700 text-base leading-relaxed">
              {products?.coreFocus}
            </p>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
              <div>
                <div className="text-sm font-semibold text-slate-900">Primary Focus</div>
                <div className="text-sm text-slate-600 mt-1">{products?.primaryOfferings}</div>
              </div>
            </div>
            <div className="flex items-start gap-3">
              <div className="w-2 h-2 bg-blue-600 rounded-full mt-2"></div>
              <div>
                <div className="text-sm font-semibold text-slate-900">Industry Classification</div>
                <div className="text-sm text-slate-600 mt-1">{products?.industry}</div>
              </div>
            </div>
          </div>
        </div>

        {/* Strategic Position & Competitive Landscape */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <TrendingUp className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Strategic Position & Competitive Landscape</h2>
          </div>

          <div className="space-y-5">
            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Market Position</h3>
              <p className="text-slate-700">{position?.marketPosition}</p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-5">
              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Geographic Presence</h3>
                <div className="text-sm text-slate-700">
                  <div>HQ: {position?.geographicPresence?.headquarters}</div>
                  <div className="mt-1">Scope: {position?.geographicPresence?.scope}</div>
                </div>
              </div>

              <div className="bg-slate-50 rounded-lg p-4 border border-slate-200">
                <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Competitive Advantage</h3>
                <p className="text-sm text-slate-700">{position?.competitiveAdvantage}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Contact & Operations */}
        <div className="bg-white rounded-lg shadow-sm border border-slate-200 p-6 mb-6">
          <div className="flex items-center gap-2 mb-4">
            <MapPin className="w-6 h-6 text-blue-600" />
            <h2 className="text-xl font-bold text-slate-900">Corporate Information</h2>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Address</h3>
              <div className="text-sm text-slate-700">
                <div>{operations?.locations?.headquarters}</div>
                <div>{operations?.locations?.country}</div>
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Contact</h3>
              <div className="text-sm text-slate-700">
                <div className="flex items-center gap-2 mb-2">
                  <Phone className="w-4 h-4" />
                  <span>{operations?.phone}</span>
                </div>
                {operations?.website && operations.website !== 'N/A' && (
                  <a 
                    href={operations.website} 
                    target="_blank" 
                    rel="noopener noreferrer"
                    className="flex items-center gap-2 text-blue-600 hover:underline"
                  >
                    <ExternalLink className="w-4 h-4" />
                    <span>Corporate Website</span>
                  </a>
                )}
              </div>
            </div>

            <div>
              <h3 className="text-sm font-bold text-slate-900 mb-2 uppercase tracking-wide">Exchange Listing</h3>
              <div className="text-sm text-slate-700">
                <div>{operations?.exchange?.listing}</div>
                <div className="text-blue-600 font-semibold mt-1">{operations?.exchange?.symbol}</div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}