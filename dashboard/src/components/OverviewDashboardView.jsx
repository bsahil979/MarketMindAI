import React from 'react';

export default function OverviewDashboardView({
  stocks,
  stocksLoading,
  watchlist,
  setSelectedTicker,
  setCurrentTab,
  toggleWatchlist,
  renderSparkline,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px' }}>
        {[
          { name: 'S&P 500 Index', val: '5,432.12', chg: '+0.32%', up: true },
          { name: 'NASDAQ Composite', val: '17,845.60', chg: '+0.85%', up: true },
          { name: 'Dow Jones Industrial', val: '39,120.45', chg: '-0.14%', up: false },
        ].map((idx, i) => (
          <div key={i} className="glass-panel glass-panel-hover" style={{ padding: '24px' }}>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginBottom: '8px' }}>{idx.name}</p>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline' }}>
              <h3 style={{ fontSize: '24px', fontWeight: '700' }}>{idx.val}</h3>
              <span style={{ color: idx.up ? 'var(--color-success)' : 'var(--color-danger)', fontWeight: '600', fontSize: '13px' }}>{idx.chg}</span>
            </div>
          </div>
        ))}
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Monitored Asset Feeds</h3>

        {stocksLoading ? (
          <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><div className="spinner"></div></div>
        ) : (
          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)', fontSize: '13px' }}>
                  <th style={{ padding: '16px' }}>Company</th>
                  <th style={{ padding: '16px' }}>Sector</th>
                  <th style={{ padding: '16px' }}>Exchange</th>
                  <th style={{ padding: '16px' }}>Trend (7D)</th>
                  <th style={{ padding: '16px', textAlign: 'right' }}>Actions</th>
                </tr>
              </thead>
              <tbody>
                {stocks.map((stock) => {
                  const isStarred = watchlist.includes(stock.ticker);
                  return (
                    <tr key={stock.ticker} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)', fontSize: '14px', transition: 'var(--transition-smooth)' }} className="table-row-hover">
                      <td style={{ padding: '16px', fontWeight: '600' }}>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <span style={{ color: 'var(--color-text-primary)' }}>{stock.ticker}</span>
                          <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: 'normal' }}>{stock.name}</span>
                        </div>
                      </td>
                      <td style={{ padding: '16px', color: 'var(--color-text-secondary)' }}>{stock.sector}</td>
                      <td style={{ padding: '16px', color: 'var(--color-text-muted)' }}>
                        <span style={{ background: 'rgba(255,255,255,0.04)', padding: '2px 8px', borderRadius: '4px', fontSize: '11px' }}>{stock.exchange}</span>
                      </td>
                      <td style={{ padding: '16px' }}>{renderSparkline([{ close: 100 }, { close: 102 }, { close: 98 }, { close: 105 }, { close: stock.ticker === 'TSLA' ? 95 : 108 }])}</td>
                      <td style={{ padding: '16px', textAlign: 'right' }}>
                        <div style={{ display: 'inline-flex', gap: '8px' }}>
                          <button onClick={() => { setSelectedTicker(stock.ticker); setCurrentTab('details'); }} className="btn btn-secondary" style={{ padding: '6px 12px', fontSize: '12px' }}>
                            Analyze
                          </button>
                          <button onClick={() => toggleWatchlist(stock.ticker)} className="btn btn-secondary" style={{ padding: '6px 10px', fontSize: '12px' }}>
                            {isStarred ? '★' : '☆'}
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
