import React from 'react';

export const ProfitabilityAndEfficiency = ({ financialData }) => {
  if (!financialData) {
    return (
      <div style={{ padding: '24px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        <div style={{ color: '#666', fontSize: '14px' }}>No financial data available</div>
      </div>
    );
  }

  if (financialData.error) {
    return (
      <div style={{ padding: '24px', fontFamily: 'system-ui, -apple-system, sans-serif' }}>
        <div style={{ color: '#d32f2f', fontSize: '14px' }}>{financialData.error}</div>
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
    if (!roic) return { label: 'Insufficient Data', color: '#666' };
    if (roic >= 15) return { label: 'Excellent', color: '#2e7d32' };
    if (roic >= 10) return { label: 'Good', color: '#558b2f' };
    if (roic >= 5) return { label: 'Fair', color: '#f57c00' };
    return { label: 'Poor', color: '#c62828' };
  };

  const qualityRating = getQualityRating(metrics.roic);

  return (
    <div style={{
      padding: '32px',
      fontFamily: 'system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif',
      maxWidth: '1200px',
      background: 'white',
      color: 'black'
    }}>
      {/* Header */}
      <div style={{ marginBottom: '32px', borderBottom: '2px solid black', paddingBottom: '16px' }}>
        <h2 style={{ margin: '0 0 8px 0', fontSize: '24px', fontWeight: '600' }}>
          Profitability & Efficiency
        </h2>
        <p style={{ margin: 0, fontSize: '14px', color: '#555' }}>
          Quality of Business Analysis • {ticker}
        </p>
      </div>

      {/* Key Quality Indicator - ROIC Highlighted */}
      <div style={{
        background: '#f8f9fa',
        border: '2px solid black',
        padding: '24px',
        marginBottom: '32px',
        borderRadius: '4px'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <div style={{ fontSize: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', marginBottom: '8px', fontWeight: '600' }}>
              Return on Invested Capital (ROIC) ⭐
            </div>
            <div style={{ fontSize: '36px', fontWeight: '700', marginBottom: '4px' }}>
              {formatPercent(metrics.roic)}
            </div>
            <div style={{ fontSize: '13px', color: '#666' }}>
              Capital Efficiency & Competitive Advantage
            </div>
          </div>
          <div style={{
            padding: '12px 24px',
            background: qualityRating.color,
            color: 'white',
            borderRadius: '4px',
            fontWeight: '600',
            fontSize: '16px'
          }}>
            {qualityRating.label}
          </div>
        </div>
      </div>

      {/* Core Return Metrics */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Return Metrics
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <MetricCard title="ROE" value={formatPercent(metrics.roe)} subtitle="Return on Equity" />
          <MetricCard title="ROA" value={formatPercent(metrics.roa)} subtitle="Return on Assets" />
          <MetricCard title="ROIC" value={formatPercent(metrics.roic)} subtitle="Return on Invested Capital" highlight />
        </div>
      </div>

      {/* Margin Analysis */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
          Margin Profile
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
          <MetricCard title="Gross Margin" value={formatPercent(metrics.gross_margin)} subtitle="Pricing Power" />
          <MetricCard title="Operating Margin" value={formatPercent(metrics.operating_margin)} subtitle="Operational Efficiency" />
          <MetricCard title="Net Margin" value={formatPercent(metrics.net_margin)} subtitle="Bottom Line Profitability" />
        </div>
      </div>

      {/* Trend Analysis */}
      {trends && (
        <>
          {/* Margin Trends */}
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Margin Trends (5-Year)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
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

          {/* Return Trends */}
          <div style={{ marginBottom: '32px' }}>
            <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '16px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Return Trends (5-Year)
            </h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
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
        </>
      )}

      {/* Operating Leverage */}
      {operating_leverage && operating_leverage.data && operating_leverage.data.length > 0 && (
        <div style={{ marginBottom: '32px' }}>
          <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '8px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
            Operating Leverage Analysis
          </h3>
          <p style={{ fontSize: '13px', color: '#666', marginBottom: '16px' }}>
            {operating_leverage.interpretation}
          </p>
          <div style={{ border: '1px solid #ddd' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f5f5f5', borderBottom: '2px solid black' }}>
                  <th style={tableHeaderStyle}>Year</th>
                  <th style={tableHeaderStyle}>Revenue Growth</th>
                  <th style={tableHeaderStyle}>Operating Income Growth</th>
                  <th style={tableHeaderStyle}>Leverage Ratio</th>
                </tr>
              </thead>
              <tbody>
                {operating_leverage.data.map((item, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid #e0e0e0' }}>
                    <td style={tableCellStyle}>{item.year}</td>
                    <td style={tableCellStyle}>{formatPercent(item.revenue_growth)}</td>
                    <td style={tableCellStyle}>{formatPercent(item.operating_income_growth)}</td>
                    <td style={{
                      ...tableCellStyle,
                      fontWeight: '600',
                      color: item.leverage_ratio > 1 ? '#2e7d32' : item.leverage_ratio < 1 ? '#c62828' : 'black'
                    }}>
                      {item.leverage_ratio ? item.leverage_ratio.toFixed(2) + 'x' : 'N/A'}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Interpretation Guide */}
      <div style={{
        background: '#f8f9fa',
        padding: '20px',
        borderLeft: '4px solid black',
        fontSize: '13px',
        lineHeight: '1.6'
      }}>
        <div style={{ fontWeight: '600', marginBottom: '8px' }}>Quality Business Indicators:</div>
        <ul style={{ margin: 0, paddingLeft: '20px' }}>
          <li><strong>ROIC &gt; 15%:</strong> Indicates strong competitive advantage and efficient capital allocation</li>
          <li><strong>ROE &gt; 15%:</strong> Management effectively generating returns for shareholders</li>
          <li><strong>Stable/Expanding Margins:</strong> Pricing power and operational discipline</li>
          <li><strong>Operating Leverage &gt; 1:</strong> Scalable business model with operating efficiency</li>
        </ul>
      </div>
    </div>
  );
};

// Supporting Components
const MetricCard = ({ title, value, subtitle, highlight }) => (
  <div style={{
    border: highlight ? '2px solid black' : '1px solid #ddd',
    padding: '16px',
    borderRadius: '4px',
    background: highlight ? '#fffde7' : 'white'
  }}>
    <div style={{ fontSize: '12px', color: '#666', marginBottom: '4px', fontWeight: '500' }}>
      {title}
    </div>
    <div style={{ fontSize: '24px', fontWeight: '700', marginBottom: '4px' }}>
      {value}
    </div>
    <div style={{ fontSize: '11px', color: '#888' }}>
      {subtitle}
    </div>
  </div>
);

const TrendTable = ({ title, data, formatter, highlight }) => (
  <div>
    <div style={{
      fontSize: '13px',
      fontWeight: '600',
      marginBottom: '8px',
      color: highlight ? 'black' : '#333'
    }}>
      {title}
    </div>
    <div style={{ border: highlight ? '2px solid black' : '1px solid #ddd' }}>
      <table style={{ width: '100%', borderCollapse: 'collapse' }}>
        <thead>
          <tr style={{ background: highlight ? '#fffde7' : '#f5f5f5', borderBottom: '1px solid #ddd' }}>
            <th style={{ ...tableHeaderStyle, fontSize: '12px' }}>Year</th>
            <th style={{ ...tableHeaderStyle, fontSize: '12px' }}>Value</th>
          </tr>
        </thead>
        <tbody>
          {data.map((item, idx) => (
            <tr key={idx} style={{ borderBottom: '1px solid #e0e0e0' }}>
              <td style={{ ...tableCellStyle, fontSize: '12px' }}>{item.year}</td>
              <td style={{ ...tableCellStyle, fontSize: '12px', fontWeight: '600' }}>
                {formatter(item.value)}
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  </div>
);

const tableHeaderStyle = {
  padding: '12px',
  textAlign: 'left',
  fontSize: '11px',
  fontWeight: '600',
  textTransform: 'uppercase',
  letterSpacing: '0.5px'
};

const tableCellStyle = {
  padding: '12px',
  fontSize: '13px'
};