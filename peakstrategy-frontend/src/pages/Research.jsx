import { useState } from "react";
import { portfolioApi } from "../services/portfolioApi";
import FinancialChart from "../components/FinancialChart";
import { AnalystConsensus } from "../components/AnalystConsensus";
import { Valuation } from "../components/Valuation";
import { ProfitabilityAndEfficiency } from "../components/ProfitabilityAndEfficiency";
import { BalanceSheet } from "../components/BalanceSheet";
import { ShareholderReturns } from "../components/ShareholderReturns";
import { BusinessResearch } from "../components/BusinessResearch";


const Research = () => {
  const [searchQuery, setSearchQuery] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [stockData, setStockData] = useState(null);
  const [activeTab, setActiveTab] = useState("Summary");

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchQuery.trim()) return;

    setLoading(true);
    setError(null);
    setStockData(null);

    try {
      const res = await portfolioApi.getStockResearch(
        searchQuery.toUpperCase()
      );

      if (res.success) {
        setStockData(res.data);
        setActiveTab("Summary");
      } else {
        setError("Failed to fetch stock data");
      }
    } catch (err) {
      setError(err.message || "Error fetching stock data");
    } finally {
      setLoading(false);
    }
  };

  const changeColor = (change) =>
    !change
      ? "text-gray-500"
      : change.includes("-")
      ? "text-red-600"
      : "text-green-600";

  return (
    <div className="min-h-screen bg-white">
      {/* Search */}
      <div className="sticky top-0 bg-white border-b px-6 py-4 z-10">
        <form onSubmit={handleSearch} className="max-w-5xl mx-auto relative">
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
            placeholder="Search stock symbol (AAPL, MSFT...)"
            className="w-full px-6 py-3 text-base border rounded-lg"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-2 top-2 px-4 py-1.5 bg-black text-white rounded-md text-sm"
          >
            {loading ? "Loading..." : "Search"}
          </button>
        </form>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-8">
        {error && (
          <div className="mb-6 p-4 bg-red-50 border rounded text-sm">{error}</div>
        )}

        {!stockData && !loading && (
          <div className="text-center py-20 text-gray-500 text-sm">
            Search for a stock to begin
          </div>
        )}

        {stockData && (
          <div className="space-y-8">
            {/* Header */}
            <div className="border rounded-xl p-4 bg-white shadow-sm">
              <h1 className="text-2xl font-bold mb-2">
                {stockData.company_name} ({stockData.ticker})
              </h1>

              {/* Key Metrics (Compact) */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
                {[
                  { label: "Price", value: stockData.snapshot.metrics.price },
                  {
                    label: "Day Change",
                    value: `${stockData.snapshot.metrics.day} (${stockData.snapshot.metrics.day_change})`,
                    color: changeColor(stockData.snapshot.metrics.day_change),
                  },
                  { label: "Market Cap", value: stockData.snapshot.metrics.market_cap },
                  { label: "Sector", value: stockData.snapshot.metrics.sector },
                  { label: "Industry", value: stockData.snapshot.metrics.industry },
                  { label: "52-Week Range", value: stockData.snapshot.metrics.week_52_range },
                ].map(({ label, value, color }) => (
                  <div
                    key={label}
                    className="flex flex-col justify-center items-start border rounded-lg p-2 bg-gray-50 shadow-sm"
                  >
                    <span className="text-gray-500 text-[10px] font-medium uppercase">{label}</span>
                    <span className={`font-semibold text-sm mt-1 ${color ? color : ""}`}>
                      {value ?? "-"}
                    </span>
                  </div>
                ))}
              </div>
            </div>

            {/* Tabs */}
            <div className="border-b flex gap-8">
              {["Summary", "Business", "Financials", "Valuation", "Profitability & Efficiency", "Balance Sheet", "Shareholder Returns", "Outlook"].map((tab) => (
                <button
                  key={tab}
                  onClick={() => setActiveTab(tab)}
                  className={`py-3 font-medium ${
                    activeTab === tab
                      ? "border-b-2 border-black"
                      : "text-gray-500"
                  }`}
                >
                  {tab}
                </button>
              ))}
            </div>

            {/* Summary */}
            {activeTab === "Summary" && (
              <div className="space-y-6">
                <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                  {stockData.business_understanding.company_description}
                </div>
              </div>
            )}

            {/* Business */}
            {activeTab === "Business" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <BusinessResearch data={stockData.business_understanding} />
              </div>
            )}

            {/* Financials */}
            {activeTab === "Financials" && (
              <FinancialChart data={stockData} />
            )}

            {/* Valuation */}
            {activeTab === "Valuation" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <Valuation valuationData={stockData.valuation} />
              </div>
            )}

            {/* Profitability & Efficiency */}
            {activeTab === "Profitability & Efficiency" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <ProfitabilityAndEfficiency financialData={stockData.profitability_and_efficiency} />
              </div>
            )}

            {/* Balance Sheet */}
            {activeTab === "Balance Sheet" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <BalanceSheet balanceSheet={stockData.balance_sheet} />
              </div>
            )}

            {/* Shareholder Returns */}
            {activeTab === "Shareholder Returns" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <ShareholderReturns data={stockData.shareholder_returns} />
              </div>
            )}


            {/* Outlook */}
            {activeTab === "Outlook" && (
              <div className="border rounded-xl p-4 bg-white shadow-sm text-sm">
                <AnalystConsensus consensusData={stockData.analyst_consensus} />
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
};

export default Research;