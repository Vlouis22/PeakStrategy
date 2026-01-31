import React, { useState, useMemo, useEffect, useRef } from 'react';
import { Search, X, Check, ChevronDown, Plus, AlertCircle } from 'lucide-react';
import Fuse from 'fuse.js';
import { portfolioBuilderApi } from '../services/portfolioApi';

const PortfolioBuilder = () => {
  const [hedgeFunds, setHedgeFunds] = useState([]);
  const [selectedInvestors, setSelectedInvestors] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [showCustomInput, setShowCustomInput] = useState(false);
  const [customInvestorName, setCustomInvestorName] = useState('');
  const [customCompanyName, setCustomCompanyName] = useState('');

  const dropdownRef = useRef(null);
  const searchRef = useRef(null);

  useEffect(() => {
    const CACHE_KEY = 'hedgeFundsCache';
    const CACHE_EXPIRY = 1000 * 60 * 60;

    const fetchHedgeFunds = async () => {
      try {
        const cached = localStorage.getItem(CACHE_KEY);
        if (cached) {
          const { data, timestamp } = JSON.parse(cached);
          if (Date.now() - timestamp < CACHE_EXPIRY) {
            setHedgeFunds(data);
            setIsLoading(false);
            return;
          }
        }

        const response = await portfolioBuilderApi.getHedgeFunds();
        const data = response.data || [];
        setHedgeFunds(data);

        localStorage.setItem(
          CACHE_KEY,
          JSON.stringify({ data, timestamp: Date.now() })
        );
      } catch (error) {
        console.error('Error fetching hedge funds:', error);
      } finally {
        setIsLoading(false);
      }
    };

    fetchHedgeFunds();
  }, []);

  // Handle click outside to close dropdown
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (
        dropdownRef.current &&
        !dropdownRef.current.contains(event.target) &&
        searchRef.current &&
        !searchRef.current.contains(event.target)
      ) {
        setIsDropdownOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
    };
  }, []);

  const fuse = useMemo(
    () =>
      new Fuse(hedgeFunds, {
        keys: ['company', 'manager'],
        threshold: 0.3,
      }),
    [hedgeFunds]
  );

  const filteredInvestors = useMemo(() => {
    if (!searchQuery.trim()) return hedgeFunds;
    return fuse.search(searchQuery).map((result) => result.item);
  }, [searchQuery, hedgeFunds, fuse]);

  const toggleInvestor = (investor) => {
    setSelectedInvestors((prev) => {
      const exists = prev.some((i) => i.company === investor.company);
      return exists
        ? prev.filter((i) => i.company !== investor.company)
        : [...prev, investor];
    });
  };

  const removeInvestor = (company) =>
    setSelectedInvestors((prev) => prev.filter((i) => i.company !== company));

  const isSelected = (company) =>
    selectedInvestors.some((i) => i.company === company);

  const handleAddCustomInvestor = () => {
    if (!customInvestorName.trim() || !customCompanyName.trim()) return;

    const customInvestor = {
      manager: customInvestorName.trim(),
      company: customCompanyName.trim(),
      cik: `custom-${Date.now()}`,
      isCustom: true,
    };

    setSelectedInvestors((prev) => [...prev, customInvestor]);
    setCustomInvestorName('');
    setCustomCompanyName('');
    setShowCustomInput(false);
    setSearchQuery('');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (selectedInvestors.length === 0) return;

    const companyNames = selectedInvestors.map((inv) => inv.company);

    try {
      const result = await portfolioBuilderApi.analyzePortfolios(companyNames);
      console.log('Analysis result:', result);
    } catch (err) {
      console.error('Error analyzing portfolios:', err);
    }
  };

  if (isLoading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-6 py-12">
        <h1 className="text-4xl font-bold mb-2">Portfolio Builder</h1>
        <p className="text-gray-600 mb-8">
          Select professional investors to analyze their portfolios and build
          your custom investment strategy.
        </p>

        {selectedInvestors.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Selected Investors ({selectedInvestors.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {selectedInvestors.map((inv) => (
                <div
                  key={inv.cik}
                  className={`flex items-center gap-2 px-4 py-2 rounded-full shadow-sm ${
                    inv.isCustom
                      ? 'bg-red-600 text-white'
                      : 'bg-black text-white'
                  }`}
                >
                  <span className="font-medium">{inv.manager}</span>
                  {inv.isCustom && (
                    <span className="text-xs bg-white/20 px-2 py-0.5 rounded">
                      Custom
                    </span>
                  )}
                  <button
                    onClick={() => removeInvestor(inv.company)}
                    className="hover:text-gray-300 transition-colors"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        <div className="mb-6 relative" ref={searchRef}>
          <Search
            className="absolute left-4 top-1/2 -translate-y-1/2 text-gray-400"
            size={20}
          />
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => {
              setSearchQuery(e.target.value);
              setIsDropdownOpen(true);
              setShowCustomInput(false);
            }}
            onFocus={() => setIsDropdownOpen(true)}
            placeholder="Search by investor or company..."
            className="w-full pl-12 pr-4 py-3 border-2 border-gray-300 rounded-lg shadow-sm focus:outline-none focus:border-black focus:ring-1 focus:ring-black transition"
          />
          {searchQuery && (
            <button
              className="absolute right-4 top-1/2 -translate-y-1/2 text-gray-400 hover:text-black"
              onClick={() => {
                setSearchQuery('');
                setIsDropdownOpen(false);
              }}
            >
              <X size={20} />
            </button>
          )}
        </div>

        {isDropdownOpen && (
          <div ref={dropdownRef} className="rounded-lg shadow-md max-h-96 overflow-y-auto mb-4">
            {filteredInvestors.length > 0 ? (
              filteredInvestors.map((inv, index) => (
                <button
                  key={inv.cik}
                  onClick={() => toggleInvestor(inv)}
                  className={`w-full px-4 py-3 flex justify-between items-center transition-colors ${
                    index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  } hover:bg-gray-100`}
                >
                  <div className="flex flex-col text-left">
                    <span className="font-semibold text-black">
                      {inv.manager}
                    </span>
                    <span className="text-sm text-gray-500">{inv.company}</span>
                  </div>

                  {isSelected(inv.cik) && (
                    <div className="bg-black text-white rounded-full p-1">
                      <Check size={16} />
                    </div>
                  )}
                </button>
              ))
            ) : (
              <div className="p-6 text-center">
                <p className="text-gray-500 mb-3">No investors found</p>
                <button
                  onClick={() => {
                    setShowCustomInput(true);
                    setIsDropdownOpen(false);
                  }}
                  className="text-red-600 hover:text-red-700 font-medium text-sm"
                >
                  Add "{searchQuery}" as custom investor →
                </button>
              </div>
            )}
          </div>
        )}

        {/* Add Custom Investor Button */}
        {!showCustomInput && !isDropdownOpen && (
          <button
            onClick={() => {
              setShowCustomInput(true);
              setIsDropdownOpen(false);
            }}
            className="w-full mt-4 flex items-center justify-center gap-2 px-6 py-3 border-2 border-dashed border-gray-300 rounded-lg hover:border-red-500 hover:bg-red-50 transition text-gray-600 hover:text-red-600"
          >
            <Plus size={20} />
            <span className="font-medium">Add Custom Investor</span>
          </button>
        )}

        {/* Custom Investor Input Form */}
        {showCustomInput && (
          <div className="mt-4 p-6 bg-white border-2 border-red-200 rounded-lg shadow-sm">
            <div className="flex items-start gap-2 mb-4 p-3 bg-red-50 rounded-lg">
              <AlertCircle size={20} className="text-red-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-red-800">
                <p className="font-semibold mb-1">
                  Please double-check your spelling
                </p>
                <p className="text-red-700">
                  Accurate names are essential for analyzing the correct
                  portfolios. Make sure the investor/company name matches
                  official SEC filings.
                </p>
              </div>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Investor Name
                </label>
                <input
                  type="text"
                  value={customInvestorName}
                  onChange={(e) => setCustomInvestorName(e.target.value)}
                  placeholder="e.g., Warren Buffett"
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && customCompanyName.trim()) {
                      handleAddCustomInvestor();
                    }
                  }}
                />
              </div>

              <div>
                <label className="block text-sm font-semibold text-gray-700 mb-2">
                  Company Name
                </label>
                <input
                  type="text"
                  value={customCompanyName}
                  onChange={(e) => setCustomCompanyName(e.target.value)}
                  placeholder="e.g., Berkshire Hathaway Inc."
                  className="w-full px-4 py-3 border-2 border-gray-300 rounded-lg focus:outline-none focus:border-red-500 focus:ring-1 focus:ring-red-500"
                  onKeyPress={(e) => {
                    if (e.key === 'Enter' && customInvestorName.trim()) {
                      handleAddCustomInvestor();
                    }
                  }}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <button
                  onClick={handleAddCustomInvestor}
                  disabled={
                    !customInvestorName.trim() || !customCompanyName.trim()
                  }
                  className="flex-1 bg-red-600 text-white py-3 rounded-lg font-semibold hover:bg-red-700 transition disabled:bg-gray-300 disabled:cursor-not-allowed"
                >
                  Add Investor
                </button>
                <button
                  onClick={() => {
                    setShowCustomInput(false);
                    setCustomInvestorName('');
                    setCustomCompanyName('');
                  }}
                  className="px-6 py-3 border-2 border-gray-300 rounded-lg font-semibold hover:bg-gray-50 transition"
                >
                  Cancel
                </button>
              </div>
            </div>
          </div>
        )}

        {!isDropdownOpen && searchQuery === '' && !showCustomInput && (
          <button
            onClick={() => setIsDropdownOpen(true)}
            className="w-full mt-6 flex justify-between items-center px-6 py-4 border-2 border-gray-300 rounded-lg hover:border-black transition"
          >
            <span className="font-medium text-gray-700">
              Browse All Investors ({hedgeFunds.length})
            </span>
            <ChevronDown size={20} className="text-gray-400" />
          </button>
        )}

        {selectedInvestors.length > 0 && (
          <button
            onClick={handleSubmit}
            className="w-full mt-8 bg-black text-white py-4 rounded-lg font-semibold text-lg hover:bg-gray-900 transition"
          >
            Analyze Selected Portfolios →
          </button>
        )}
      </div>
    </div>
  );
};

export default PortfolioBuilder;