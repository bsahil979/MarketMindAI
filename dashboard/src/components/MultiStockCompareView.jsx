import React from 'react';

export default function MultiStockCompareView({
  compareTickers,
  setCompareTickers,
  compareData,
  compareLoading,
  handleRunComparison,
}) {
  const toggleTicker = (ticker) => {
    if (compareTickers.includes(ticker)) {
      setCompareTickers(compareTickers.filter((item) => item !== ticker));
    } else {
      setCompareTickers([...compareTickers, ticker]);
    }
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div className="glass-panel" style={{ padding: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px', flexWrap: 'wrap', gap: '16px' }}>
          <div>
            <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#f8fafc' }}>Side-by-Side Multi-Company Financial Matrix</h3>
            <p style={{ fontSize: '13px', color: '#94a3b8', marginTop: '4px' }}>Compare revenue, net income, cash flow, and debt liabilities across top market leader tickers.</p>
          </div>
          <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
            {['AAPL', 'MSFT', 'NVDA', 'AMZN', 'TSLA', 'GOOGL', 'META'].map((ticker) => {
              const isSel = compareTickers.includes(ticker);
              return (
                <button
                  key={ticker}
                  onClick={() => toggleTicker(ticker)}
                  className="btn"
                  style={{
                    fontSize: '12px',
                    padding: '6px 12px',
                    background: isSel ? 'var(--accent-blue)' : 'rgba(255,255,255,0.04)',
                    color: '#ffffff'
                  }}
                >
                  {ticker}
                </button>
              );
            })}
          </div>
        </div>

        <button onClick={() => handleRunComparison(compareTickers)} className="btn btn-primary" style={{ padding: '10px 18px', fontSize: '13px', marginBottom: '20px' }}>
          {compareLoading ? 'Comparing…' : 'Run Comparison'}
        </button>

        {compareData.length > 0 && (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
                  <th style={{ padding: '14px' }}>Company</th>
                  <th style={{ padding: '14px' }}>Revenue ($B)</th>
                  <th style={{ padding: '14px' }}>Net Income ($B)</th>
                  <th style={{ padding: '14px' }}>Free Cash Flow ($B)</th>
                  <th style={{ padding: '14px' }}>Total Debt ($B)</th>
                  <th style={{ padding: '14px' }}>Cash Reserves ($B)</th>
                  <th style={{ padding: '14px' }}>Current Ratio</th>
                  <th style={{ padding: '14px' }}>Debt/Equity</th>
                </tr>
              </thead>
              <tbody>
                {compareData.map((item) => (
                  <tr key={item.ticker} style={{ borderBottom: '1px solid rgba(255,255,255,0.04)' }}>
                    <td style={{ padding: '14px', fontWeight: '700', color: '#f8fafc' }}>
                      {item.name} <span style={{ color: '#38bdf8', fontSize: '11px', marginLeft: '6px' }}>({item.ticker})</span>
                    </td>
                    <td style={{ padding: '14px', fontWeight: '600' }}>${item.revenue_b}B</td>
                    <td style={{ padding: '14px', color: '#34d399', fontWeight: '600' }}>${item.net_income_b}B</td>
                    <td style={{ padding: '14px', color: '#38bdf8' }}>${item.fcf_b}B</td>
                    <td style={{ padding: '14px', color: '#f43f5e' }}>${item.debt_b}B</td>
                    <td style={{ padding: '14px', color: '#c084fc', fontWeight: '600' }}>${item.cash_b}B</td>
                    <td style={{ padding: '14px' }}>{item.current_ratio}x</td>
                    <td style={{ padding: '14px' }}>{item.debt_equity}x</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <div className="glass-panel" style={{ padding: '30px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#f8fafc', marginBottom: '20px' }}>
          Visual Cash vs Debt Breakdown
        </h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '24px' }}>
          {compareData.map((comp) => (
            <div key={comp.ticker} style={{ background: '#090d16', padding: '20px', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <h4 style={{ fontSize: '16px', fontWeight: '700', color: '#f8fafc', marginBottom: '14px' }}>
                {comp.ticker} — {comp.name}
              </h4>
              <div className="visual-bar-container">
                <div className="visual-bar-label">
                  <span>Revenue</span>
                  <span style={{ color: '#38bdf8' }}>${comp.revenue_b}B</span>
                </div>
                <div className="visual-bar-track">
                  <div className="visual-bar-fill" style={{ width: `${Math.min((comp.revenue_b / 600) * 100, 100)}%`, background: '#38bdf8' }}></div>
                </div>

                <div className="visual-bar-label" style={{ marginTop: '6px' }}>
                  <span>Cash Reserves</span>
                  <span style={{ color: '#34d399' }}>${comp.cash_b}B</span>
                </div>
                <div className="visual-bar-track">
                  <div className="visual-bar-fill" style={{ width: `${Math.min((comp.cash_b / 120) * 100, 100)}%`, background: '#34d399' }}></div>
                </div>

                <div className="visual-bar-label" style={{ marginTop: '6px' }}>
                  <span>Total Debt</span>
                  <span style={{ color: '#f43f5e' }}>${comp.debt_b}B</span>
                </div>
                <div className="visual-bar-track">
                  <div className="visual-bar-fill" style={{ width: `${Math.min((comp.debt_b / 160) * 100, 100)}%`, background: '#f43f5e' }}></div>
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
