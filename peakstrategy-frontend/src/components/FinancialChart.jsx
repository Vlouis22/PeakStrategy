import { useState, useMemo, useRef } from "react";
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  CartesianGrid,
  Legend,
} from "recharts";
import { AlertCircle, TrendingUp, TrendingDown, Info, BarChart3, DollarSign } from "lucide-react";
import ReactDOM from "react-dom";

const TABS = [
  { key: "revenue", label: "Revenue" },
  { key: "net_income", label: "Net Income" },
  { key: "free_cash_flow", label: "Free Cash Flow" },
  { key: "cash_flow_quality", label: "Cash Flow Quality" },
  { key: "margins", label: "Margins" },
];

const toNumber = (val) => {
  if (val === null || val === undefined) return null;
  if (typeof val === "number") return val;

  if (typeof val === "string") {
    const num = Number(val.replace(/[^0-9.-]+/g, ""));
    return isNaN(num) ? null : num;
  }

  return null;
};

const formatAbbreviated = (value, decimals = 2) => {
  if (value === null || value === undefined) return "N/A";

  const abs = Math.abs(value);
  const sign = value < 0 ? "-" : "";

  if (abs >= 1e12) return `${sign}$${(abs / 1e12).toFixed(decimals)}T`;
  if (abs >= 1e9) return `${sign}$${(abs / 1e9).toFixed(decimals)}B`;
  if (abs >= 1e6) return `${sign}$${(abs / 1e6).toFixed(decimals)}M`;
  if (abs >= 1e3) return `${sign}$${(abs / 1e3).toFixed(decimals)}K`;

  return `${sign}$${abs.toFixed(0)}`;
};

const InfoTooltip = ({ text }) => {
  const [showTooltip, setShowTooltip] = useState(false);
  const [position, setPosition] = useState({ top: 0, left: 0 });
  const iconRef = useRef(null);

  const handleMouseEnter = () => {
    if (iconRef.current) {
      const rect = iconRef.current.getBoundingClientRect();
      setPosition({
        top: rect.top - 8,
        left: rect.left + rect.width / 2,
      });
    }
    setShowTooltip(true);
  };

  return (
    <div className="relative inline-block ml-1">
      <Info
        ref={iconRef}
        className="w-3.5 h-3.5 text-slate-400 hover:text-slate-600 cursor-help inline transition-colors"
        onMouseEnter={handleMouseEnter}
        onMouseLeave={() => setShowTooltip(false)}
        onClick={() => setShowTooltip(!showTooltip)}
      />
      {showTooltip &&
        ReactDOM.createPortal(
          <div
            className="fixed z-50 w-56 p-3 text-xs text-white bg-slate-900 rounded-lg shadow-xl"
            style={{
              whiteSpace: "normal",
              top: position.top + "px",
              left: position.left + "px",
              transform: "translateX(-50%) translateY(-100%)",
            }}
          >
            {text}
            <div className="absolute w-2 h-2 bg-slate-900 transform rotate-45 top-full left-1/2 -translate-x-1/2 -mt-1"></div>
          </div>,
          document.body
        )}
    </div>
  );
};

const QualityMetricCard = ({ title, value, status, icon: Icon, description }) => {
  const getStatusColor = (status) => {
    if (status === "Good" || status === "Excellent" || status === "Positive") {
      return "border-emerald-200 bg-emerald-50";
    }
    if (status === "Warning" || status === "Moderate") {
      return "border-amber-200 bg-amber-50";
    }
    if (status === "Concerning" || status === "Poor" || status === "Negative") {
      return "border-red-200 bg-red-50";
    }
    return "border-slate-200 bg-slate-50";
  };

  const getTextColor = (status) => {
    if (status === "Good" || status === "Excellent" || status === "Positive") {
      return "text-emerald-700";
    }
    if (status === "Warning" || status === "Moderate") {
      return "text-amber-700";
    }
    if (status === "Concerning" || status === "Poor" || status === "Negative") {
      return "text-red-700";
    }
    return "text-slate-700";
  };

  return (
    <div className={`border rounded-lg p-5 ${getStatusColor(status)} transition-all duration-300 hover:shadow-sm`}>
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1">
          <div className="text-xs font-semibold text-slate-500 uppercase tracking-wide mb-2">
            {title}
          </div>
          <div className={`text-2xl font-bold ${getTextColor(status)}`}>
            {value}
          </div>
        </div>
        {Icon && <Icon className={`w-5 h-5 ${getTextColor(status)}`} />}
      </div>
      {description && (
        <div className="text-xs text-slate-600 leading-relaxed mt-2">{description}</div>
      )}
      <div className={`text-xs font-semibold mt-3 ${getTextColor(status)}`}>
        {status}
      </div>
    </div>
  );
};

const RedFlagAlert = ({ flags }) => {
  if (!flags || flags.length === 0) return null;

  return (
    <div className="bg-red-50 border border-red-200 rounded-lg p-5 mb-6">
      <div className="flex items-start gap-3">
        <AlertCircle className="w-5 h-5 text-red-600 mt-0.5 flex-shrink-0" />
        <div className="flex-1">
          <div className="font-semibold text-red-800 mb-3 text-sm">
            🚩 Potential Cash Flow Issues
          </div>
          <ul className="space-y-2">
            {flags.map((flag, idx) => (
              <li key={idx} className="text-sm text-red-700 leading-relaxed">
                • {flag}
              </li>
            ))}
          </ul>
        </div>
      </div>
    </div>
  );
};

const FinancialChart = ({ data }) => {
  const [activeTab, setActiveTab] = useState("revenue");

  const rawData =
    data?.financial_foundation?.core_trends?.[
      activeTab === "cash_flow_quality" ? "free_cash_flow" : activeTab
    ]?.data ?? [];

  const cashFlowQuality =
    data?.financial_foundation?.core_trends?.free_cash_flow?.quality_metrics ?? {};

  const redFlags =
    data?.financial_foundation?.core_trends?.free_cash_flow?.red_flags ?? [];

  const chartData = useMemo(() => {
    return rawData
      .map((row) => {
        let value;

        if (activeTab === "margins") {
          value =
            toNumber(row.gross_margin) ??
            toNumber(row.operating_margin) ??
            toNumber(row.net_margin);
        } else {
          value = toNumber(row.value);
        }

        if (value === null || !row.year) return null;

        return {
          year: Number(row.year),
          value,
          operating_cf: toNumber(row.operating_cf),
          net_income: toNumber(row.net_income),
          capex: toNumber(row.capex),
          sbc: toNumber(row.sbc),
        };
      })
      .filter(Boolean)
      .sort((a, b) => a.year - b.year);
  }, [rawData, activeTab]);

  const fcfQualityData = useMemo(() => {
    return chartData.filter(
      (row) =>
        row.value !== null &&
        row.operating_cf !== null &&
        row.net_income !== null &&
        row.capex !== null
    );
  }, [chartData]);

  const enhancedData = useMemo(() => {
    const dataWithYoY = chartData.map((d, i) => {
      const prev = i > 0 ? chartData[i - 1].value : null;
      const yoy =
        prev !== null && prev !== 0
          ? ((d.value - prev) / Math.abs(prev)) * 100
          : null;

      return { ...d, yoy };
    });

    const last5 = dataWithYoY.slice(-5).filter((d) => d.yoy !== null);
    const last10 = dataWithYoY.slice(-10).filter((d) => d.yoy !== null);
    const allTime = dataWithYoY.filter((d) => d.yoy !== null);

    const avg = (arr) =>
      arr.length > 0 ? arr.reduce((acc, d) => acc + d.yoy, 0) / arr.length : 0;

    return {
      dataWithYoY,
      avg5: avg(last5),
      avg10: avg(last10),
      avgAll: avg(allTime),
    };
  }, [chartData]);

  const yAxisFormatter = (v) =>
    activeTab === "margins" ? `${v}%` : formatAbbreviated(v, 0);

  const tooltipFormatter = (v) =>
    activeTab === "margins" ? `${v}%` : formatAbbreviated(v);

  const getYoYColor = (yoy) => {
    if (yoy === null) return "bg-slate-200 text-slate-500";
    return yoy > 0
      ? "bg-emerald-100 text-emerald-800"
      : "bg-red-100 text-red-800";
  };

  const getAvgColor = (avg) =>
    avg > 0 ? "text-emerald-600" : avg < 0 ? "text-red-600" : "text-slate-500";

  return (
    <div className="min-h-screen bg-gradient-to-b from-slate-50 via-white to-slate-50">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 lg:py-16">
        
        <div className="mb-14">
          <h1 className="text-4xl md:text-5xl font-bold text-slate-900 tracking-tight mb-6">
            Financial Performance
          </h1>
          <div className="flex gap-2 flex-wrap">
            {TABS.map((tab) => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                className={`px-4 py-2 rounded-lg text-sm font-medium transition-all duration-300 ${
                  activeTab === tab.key
                    ? "bg-slate-900 text-white shadow-md"
                    : "border border-slate-300 text-slate-700 hover:bg-slate-50 hover:border-slate-400"
                }`}
              >
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        <div className="bg-white border border-slate-200 rounded-lg p-8 shadow-sm hover:shadow-md transition-shadow duration-300">
          
          {/* Cash Flow Quality Tab */}
          {activeTab === "cash_flow_quality" ? (
            <div>
              {redFlags.length > 0 && <RedFlagAlert flags={redFlags} />}

              <div className="mb-8">
                <div className="flex items-center gap-3 mb-2">
                  <div className="w-10 h-10 rounded-lg bg-slate-100 flex items-center justify-center">
                    <BarChart3 className="text-slate-600" size={24} />
                  </div>
                  <h2 className="text-xl font-bold text-slate-900">
                    Cash Flow Quality Analysis (Last {fcfQualityData.length} Years)
                  </h2>
                </div>
                <p className="text-sm text-slate-600 ml-13">
                  Based on detailed cash flow disclosures
                </p>
              </div>

              {/* Quality Metrics Cards */}
              {Object.keys(cashFlowQuality).length > 0 && (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 mb-8">
                  {cashFlowQuality.ocf_to_net_income && (
                    <QualityMetricCard
                      title="Operating CF vs Net Income"
                      value={cashFlowQuality.ocf_to_net_income.value}
                      status={cashFlowQuality.ocf_to_net_income.status}
                      description="Higher ratio indicates better earnings quality"
                      icon={TrendingUp}
                    />
                  )}
                  {cashFlowQuality.fcf_margin && (
                    <QualityMetricCard
                      title="FCF Margin"
                      value={cashFlowQuality.fcf_margin.value}
                      status={cashFlowQuality.fcf_margin.status}
                      description="Free cash flow as % of revenue"
                    />
                  )}
                  {cashFlowQuality.fcf_per_share && (
                    <QualityMetricCard
                      title="FCF Per Share"
                      value={cashFlowQuality.fcf_per_share.value}
                      status={cashFlowQuality.fcf_per_share.status}
                      description="Free cash flow per outstanding share"
                    />
                  )}
                  {cashFlowQuality.capex_trend && (
                    <QualityMetricCard
                      title="CapEx Trend"
                      value={cashFlowQuality.capex_trend.value}
                      status={cashFlowQuality.capex_trend.status}
                      description="Capital expenditure growth pattern"
                      icon={
                        cashFlowQuality.capex_trend.trend_direction === "Increasing"
                          ? TrendingUp
                          : TrendingDown
                      }
                    />
                  )}
                  {cashFlowQuality.sbc_ratio && (
                    <QualityMetricCard
                      title="Stock-Based Comp"
                      value={cashFlowQuality.sbc_ratio.value}
                      status={cashFlowQuality.sbc_ratio.status}
                      description="SBC as % of operating cash flow"
                      icon={AlertCircle}
                    />
                  )}
                </div>
              )}

              {/* Quality Detail Chart */}
              {fcfQualityData.length > 0 ? (
                <>
                  <div className="h-80 mb-8">
                    <ResponsiveContainer width="100%" height="100%">
                      <LineChart data={fcfQualityData}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                        <XAxis dataKey="year" stroke="#64748b" />
                        <YAxis tickFormatter={(v) => formatAbbreviated(v, 0)} stroke="#64748b" />
                        <Tooltip formatter={(v) => formatAbbreviated(v)} />
                        <Legend />
                        <Line
                          type="monotone"
                          dataKey="value"
                          name="Free Cash Flow"
                          stroke="#2563eb"
                          strokeWidth={3}
                          dot={{ r: 4, fill: "#2563eb" }}
                        />
                        <Line
                          type="monotone"
                          dataKey="operating_cf"
                          name="Operating CF"
                          stroke="#10b981"
                          strokeWidth={2}
                          dot={{ r: 3, fill: "#10b981" }}
                          strokeDasharray="5 5"
                        />
                        <Line
                          type="monotone"
                          dataKey="net_income"
                          name="Net Income"
                          stroke="#f59e0b"
                          strokeWidth={2}
                          dot={{ r: 3, fill: "#f59e0b" }}
                          strokeDasharray="5 5"
                        />
                      </LineChart>
                    </ResponsiveContainer>
                  </div>

                  {/* Quality Breakdown Table */}
                  <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
                    <table className="w-full text-left text-sm">
                      <thead className="bg-slate-50 border-b border-slate-200">
                        <tr>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            Year
                          </th>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            Operating CF
                            <InfoTooltip text="Cash generated from business operations" />
                          </th>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            Net Income
                            <InfoTooltip text="Accounting profit after all expenses and taxes" />
                          </th>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            CapEx
                            <InfoTooltip text="Capital expenditure on assets and infrastructure" />
                          </th>
                          {fcfQualityData.some((d) => d.sbc !== null) && (
                            <th className="px-4 py-3 font-semibold text-slate-700">
                              SBC
                              <InfoTooltip text="Stock-based compensation paid to employees" />
                            </th>
                          )}
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            FCF
                            <InfoTooltip text="Free cash flow: Operating CF minus CapEx" />
                          </th>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            FCF Margin
                            <InfoTooltip text="Free cash flow as percentage of revenue" />
                          </th>
                          <th className="px-4 py-3 font-semibold text-slate-700">
                            OCF/NI Ratio
                            <InfoTooltip text="Operating cash flow divided by net income" />
                          </th>
                        </tr>
                      </thead>
                      <tbody>
                        {fcfQualityData.map((row, idx) => {
                          const revenueData = data?.financial_foundation?.core_trends?.revenue?.data?.find(
                            (r) => r.year === row.year.toString()
                          );
                          const fcfMargin =
                            row.value && revenueData?.value
                              ? (
                                  (row.value / toNumber(revenueData.value)) *
                                  100
                                ).toFixed(1) + "%"
                              : "N/A";

                          const ocfNiRatio =
                            row.operating_cf &&
                            row.net_income &&
                            row.net_income !== 0
                              ? (row.operating_cf / row.net_income).toFixed(2) + "x"
                              : "N/A";

                          return (
                            <tr
                              key={row.year}
                              className={`border-b border-slate-200 hover:bg-slate-50 transition-colors ${
                                idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                              }`}
                            >
                              <td className="px-4 py-3 font-semibold text-slate-900">{row.year}</td>
                              <td className="px-4 py-3 text-slate-700">
                                {formatAbbreviated(row.operating_cf)}
                              </td>
                              <td className="px-4 py-3 text-slate-700">
                                {formatAbbreviated(row.net_income)}
                              </td>
                              <td className="px-4 py-3 text-slate-700">
                                {formatAbbreviated(row.capex)}
                              </td>
                              {fcfQualityData.some((d) => d.sbc !== null) && (
                                <td className="px-4 py-3 text-slate-700">
                                  {formatAbbreviated(row.sbc)}
                                </td>
                              )}
                              <td className="px-4 py-3 font-bold text-slate-900">
                                {formatAbbreviated(row.value)}
                              </td>
                              <td className="px-4 py-3 font-bold text-slate-900">
                                {fcfMargin}
                              </td>
                              <td className="px-4 py-3 font-bold text-slate-900">
                                {ocfNiRatio}
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </table>
                  </div>
                </>
              ) : (
                <div className="text-center py-16 text-slate-500">
                  <p className="text-lg font-semibold">
                    Insufficient data for quality analysis
                  </p>
                  <p className="text-sm mt-2">
                    Complete cash flow data not available for recent years
                  </p>
                </div>
              )}
            </div>
          ) : (
            /* Standard Tabs (Revenue, Net Income, Free Cash Flow, Margins) */
            <>
              {/* Main Chart */}
              <div className="h-96 mb-8">
                <ResponsiveContainer width="100%" height="100%">
                  <LineChart data={enhancedData.dataWithYoY}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#e2e8f0" />
                    <XAxis dataKey="year" stroke="#64748b" />
                    <YAxis tickFormatter={yAxisFormatter} stroke="#64748b" />
                    <Tooltip formatter={tooltipFormatter} />
                    <Legend />
                    <Line
                      type="monotone"
                      dataKey="value"
                      stroke="#2563eb"
                      strokeWidth={3}
                      dot={{ r: 5, fill: "#2563eb" }}
                    />
                  </LineChart>
                </ResponsiveContainer>
              </div>

              <div className="flex justify-center gap-8 mb-8 pb-6 border-b border-slate-200">
                <div
                  className={`text-center text-sm ${getAvgColor(
                    enhancedData.avg5
                  )}`}
                >
                  <div className="font-semibold mb-1">5Y Avg Change</div>
                  <div className="text-xl font-bold">
                    {enhancedData.avg5.toFixed(2)}%
                  </div>
                </div>
                <div
                  className={`text-center text-sm ${getAvgColor(
                    enhancedData.avg10
                  )}`}
                >
                  <div className="font-semibold mb-1">10Y Avg Change</div>
                  <div className="text-xl font-bold">
                    {enhancedData.avg10.toFixed(2)}%
                  </div>
                </div>
                <div
                  className={`text-center text-sm ${getAvgColor(
                    enhancedData.avgAll
                  )}`}
                >
                  <div className="font-semibold mb-1">All-Time Avg Change</div>
                  <div className="text-xl font-bold">
                    {enhancedData.avgAll.toFixed(2)}%
                  </div>
                </div>
              </div>

              {/* Historical Summary Table */}
              <div className="overflow-x-auto border border-slate-200 rounded-lg shadow-sm">
                <table className="w-full text-left text-sm">
                  <thead className="bg-slate-50 border-b border-slate-200">
                    <tr>
                      <th className="px-4 py-3 font-semibold text-slate-700">Year</th>
                      <th className="px-4 py-3 font-semibold text-slate-700">Value</th>
                      <th className="px-4 py-3 font-semibold text-slate-700">YoY %</th>
                    </tr>
                  </thead>
                  <tbody>
                    {enhancedData.dataWithYoY.map((row, idx) => (
                      <tr
                        key={row.year}
                        className={`border-b border-slate-200 hover:bg-slate-50 transition-colors ${
                          idx % 2 === 0 ? "bg-white" : "bg-slate-50/50"
                        }`}
                      >
                        <td className="px-4 py-3 font-semibold text-slate-900">{row.year}</td>
                        <td className="px-4 py-3 text-slate-700">
                          {formatAbbreviated(row.value)}
                        </td>
                        <td className="px-4 py-3">
                          <span
                            className={`font-semibold inline-block rounded-full px-3 py-1 text-xs ${getYoYColor(
                              row.yoy
                            )}`}
                          >
                            {row.yoy !== null ? row.yoy.toFixed(2) + "%" : "-"}
                          </span>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          )}
        </div>
      </div>
    </div>
  );
};

export default FinancialChart;