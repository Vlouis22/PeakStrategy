import React, { useState, useMemo, useEffect } from 'react';
import { Search, X, Check, ChevronDown } from 'lucide-react';
import Fuse from 'fuse.js';
import hedgeFundsData from '../data/hedge_fund_ciks.json';

const PortfolioBuilder = () => {
  const [hedgeFunds, setHedgeFunds] = useState([]);
  const [selectedInvestors, setSelectedInvestors] = useState([]);
  const [searchQuery, setSearchQuery] = useState('');
  const [isDropdownOpen, setIsDropdownOpen] = useState(false);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    setHedgeFunds(hedgeFundsData);
    setIsLoading(false);
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
      const exists = prev.some((i) => i.cik === investor.cik);
      return exists
        ? prev.filter((i) => i.cik !== investor.cik)
        : [...prev, investor];
    });
    console.log(selectedInvestors)
  };

  const removeInvestor = (cik) =>
    setSelectedInvestors((prev) => prev.filter((i) => i.cik !== cik));

  const isSelected = (cik) =>
    selectedInvestors.some((i) => i.cik === cik);

  if (isLoading)
    return (
      <div className="min-h-screen flex items-center justify-center">
        Loading...
      </div>
    );

  return (
    <div className="min-h-screen bg-gray-50">
      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Header */}
        <h1 className="text-4xl font-bold mb-2">Portfolio Builder</h1>
        <p className="text-gray-600 mb-8">
          Select professional investors to analyze their portfolios and build
          your custom investment strategy.
        </p>

        {/* Selected Investors */}
        {selectedInvestors.length > 0 && (
          <div className="mb-8">
            <h2 className="text-sm font-semibold text-gray-700 mb-3 uppercase tracking-wide">
              Selected Investors ({selectedInvestors.length})
            </h2>
            <div className="flex flex-wrap gap-2">
              {selectedInvestors.map((inv) => (
                <div
                  key={inv.cik}
                  className="flex items-center gap-2 bg-black text-white px-4 py-2 rounded-full shadow-sm"
                >
                  <span className="font-medium">{inv.manager}</span>
                  <button
                    onClick={() => removeInvestor(inv.cik)}
                    className="hover:text-gray-300 transition-colors"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Search Input */}
        <div className="mb-6 relative">
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

        {/* Dropdown / Investor List */}
        {isDropdownOpen && (
          <div className="rounded-lg shadow-md max-h-96 overflow-y-auto">
            {filteredInvestors.length > 0 ? (
              filteredInvestors.map((inv, index) => (
                <button
                  key={inv.cik + inv.company}
                  onClick={() => toggleInvestor(inv)}
                  className={`w-full px-4 py-3 flex justify-between items-center transition-colors ${
                    index % 2 === 0 ? 'bg-white' : 'bg-gray-50'
                  } hover:bg-gray-100`}
                >
                  {/* Left: Manager & Company */}
                  <div className="flex flex-col text-left">
                    <span className="font-semibold text-black">{inv.manager}</span>
                    <span className="text-sm text-gray-500">{inv.company}</span>
                  </div>

                  {/* Right: Checkmark */}
                  {isSelected(inv.cik) && (
                    <div className="bg-black text-white rounded-full p-1">
                      <Check size={16} />
                    </div>
                  )}
                </button>
              ))
            ) : (
              <div className="p-6 text-center text-gray-500">No investors found</div>
            )}
          </div>
        )}
        {/* Browse All Button */}
        {!isDropdownOpen && searchQuery === '' && (
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

        {/* Analyze Action */}
        {selectedInvestors.length > 0 && (
          <button
            onClick={() => console.log(selectedInvestors)}
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
