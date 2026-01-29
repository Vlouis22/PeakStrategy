import { useState } from "react";
import { portfolioApi } from "../services/portfolioApi";
import FinancialChart from "../components/FinancialChart";
import { AnalystConsensus } from "../components/AnalystConsensus";
import { Valuation } from "../components/Valuation";
import { ProfitabilityAndEfficiency } from "../components/ProfitabilityAndEfficiency";
import { BalanceSheet } from "../components/BalanceSheet";
import { ShareholderReturns } from "../components/ShareholderReturns";
import { BusinessResearch } from "../components/BusinessResearch";
import { StockResearchSummary } from "../components/StockResearchSummary";
import ResearchLoadingAnimation from "../components/ResearchLoadingAnimation";

const TABS = [
  "Summary",
  "Business",
  "Financials",
  "Valuation",
  "Profitability & Efficiency",
  "Balance Sheet",
  "Shareholder Returns",
  "Outlook",
];

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
      const res = await portfolioApi.getStockResearch(searchQuery.toUpperCase());
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

  const handleMetricClick = (metricName) => {
    const tabMap = {
      Valuation: "Valuation",
      Profitability: "Profitability & Efficiency",
      "Financial Health": "Balance Sheet",
      "Shareholder Returns": "Shareholder Returns",
      "Growth Outlook": "Outlook",
    };

    setActiveTab(tabMap[metricName] || metricName);
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const changeColor = (change) =>
    !change
      ? "text-neutral-500"
      : change.includes("-")
      ? "text-red-600"
      : "text-emerald-600";

  const MetricCard = ({ label, value, valueColor }) => (
    <div className="bg-white border border-neutral-200 rounded-xl px-4 py-3">
      <div className="text-xs uppercase tracking-wide text-neutral-500 mb-1">
        {label}
      </div>
      <div className={`text-lg font-semibold ${valueColor}`}>
        {value ?? "-"}
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-transparent">
      <div className="sticky top-0 z-40 bg-transparent backdrop-blur-sm">
        <form
          onSubmit={handleSearch}
          className="max-w-6xl mx-auto px-6 py-6 relative"
        >
          <input
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value.toUpperCase())}
            placeholder="Enter stock symbol (AAPL, MSFT)"
            className="w-full px-7 py-4 text-xl border border-neutral-300 rounded-xl focus:outline-none focus:border-black bg-white"
            disabled={loading}
          />
          <button
            type="submit"
            disabled={loading}
            className="absolute right-8 top-1/2 -translate-y-1/2 px-7 py-2.5 rounded-lg bg-black text-white text-sm font-medium hover:bg-neutral-800 disabled:bg-neutral-300"
          >
            {loading ? "Loading…" : "Analyze"}
          </button>
        </form>
      </div>

      <div className="max-w-6xl mx-auto px-6 py-0">
        <div className="bg-white border-neutral-200 rounded-2xl mt-6 px-6 py-10">
          {error && (
            <div className="mb-6 text-sm text-red-700 bg-red-50 border border-red-100 rounded-lg px-4 py-3">
              {error}
            </div>
          )}

          {loading && <ResearchLoadingAnimation ticker={searchQuery} />}

          {!stockData && !loading && (
            <div className="text-center py-28 text-neutral-400 text-lg">
              Start by searching a stock symbol
            </div>
          )}

          {stockData && (
            <div className="space-y-10">
              <div className="space-y-6">
                <div className="flex items-start justify-between">
                  <div>
                    <h1 className="text-4xl font-light text-neutral-900">
                      {stockData.company_name}
                    </h1>
                    <div className="mt-2 text-base text-neutral-500">
                      {stockData.ticker} •{" "}
                      {stockData.snapshot.metrics.sector}
                    </div>
                  </div>

                  <div className="text-right">
                    <div className="text-3xl font-light">
                      {stockData.snapshot.metrics.price}
                    </div>
                    <div
                      className={`text-base font-medium ${changeColor(
                        stockData.snapshot.metrics.day_change
                      )}`}
                    >
                      {stockData.snapshot.metrics.day} (
                      {stockData.snapshot.metrics.day_change})
                    </div>
                  </div>
                </div>

                <div className="bg-neutral-50 border border-neutral-200 rounded-2xl p-4">
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <MetricCard
                      label="Market Cap"
                      value={stockData.snapshot.metrics.market_cap}
                      valueColor="text-indigo-600"
                    />
                    <MetricCard
                      label="Industry"
                      value={stockData.snapshot.metrics.industry}
                      valueColor="text-blue-600"
                    />
                    <MetricCard
                      label="52W Range"
                      value={stockData.snapshot.metrics.week_52_range}
                      valueColor="text-emerald-600"
                    />
                    <MetricCard
                      label="Dividend Yield"
                      value={
                        stockData.shareholder_returns.dividends.dividend_yield?.toFixed(2) + "%"
                      }
                      valueColor="text-amber-600"
                    />
                  </div>
                </div>
              </div>

              <div className="flex gap-8 border-b border-neutral-200 overflow-x-auto">
                {TABS.map((tab) => (
                  <button
                    key={tab}
                    onClick={() => setActiveTab(tab)}
                    className={`pb-4 text-base font-medium whitespace-nowrap transition-colors ${
                      activeTab === tab
                        ? "text-black border-b-2 border-black"
                        : "text-neutral-500 hover:text-neutral-800"
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              <div className="pt-6">
                {activeTab === "Summary" && (
                  <StockResearchSummary
                    scoring_pillars={stockData.scoring_pillars}
                    company_name={
                      stockData.business_understanding.companyOverview.companyName
                    }
                    company_logo_url={stockData.company_logo_url}
                    shareholder_returns={stockData.shareholder_returns}
                    ceo={stockData.business_understanding.leadershipGovernance.ceo}
                    year_founded={
                      stockData.business_understanding.companyOverview.founded
                    }
                    employees={
                      stockData.business_understanding.operationalMetrics.employees
                    }
                    location={
                      stockData.business_understanding.operationalMetrics.locations
                    }
                    price_targets={stockData.analyst_consensus}
                    summary_data={stockData.company_summary}
                    onMetricClick={handleMetricClick}
                  />
                )}

                {activeTab === "Business" && (
                  <BusinessResearch data={stockData.business_understanding} />
                )}

                {activeTab === "Financials" && (
                  <FinancialChart data={stockData} />
                )}

                {activeTab === "Valuation" && (
                  <Valuation valuationData={stockData.valuation} />
                )}

                {activeTab === "Profitability & Efficiency" && (
                  <ProfitabilityAndEfficiency
                    financialData={stockData.profitability_and_efficiency}
                  />
                )}

                {activeTab === "Balance Sheet" && (
                  <BalanceSheet balanceSheet={stockData.balance_sheet} />
                )}

                {activeTab === "Shareholder Returns" && (
                  <ShareholderReturns data={stockData.shareholder_returns} />
                )}

                {activeTab === "Outlook" && (
                  <AnalystConsensus
                    consensusData={stockData.analyst_consensus}
                  />
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

const Metric = ({ label, value, color }) => (
  <div>
    <div className="text-sm text-neutral-500 mb-1">{label}</div>
    <div className={`text-xl font-semibold ${color}`}>
      {value ?? "-"}
    </div>
  </div>
);

export default Research;