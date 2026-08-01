import React from 'react';

export default function StockDetailView({
  selectedStockData,
  selectedTicker,
  priceHistory,
  forecastData = [],
  riskMetrics,
  modelRegistry,
  stocks = [],
  onSelectTicker,
  renderInteractiveChart,
}) {
  if (!selectedStockData) {
    return (
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', padding: '60px', textAlign: 'center' }}>
        <div style={{ fontSize: '48px', marginBottom: '20px' }}>📊</div>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '12px', color: 'var(--color-text-primary)' }}>
          Loading Stock Data...
        </h3>
        <p style={{ fontSize: '14px', color: 'var(--color-text-secondary)', maxWidth: '400px' }}>
          Fetching real-time analytics for {selectedTicker || 'selected stock'}. If this persists, the backend API may be unavailable.
        </p>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px', flexWrap: 'wrap' }}>
        {stocks.map((stock) => (
          <button
            key={stock.ticker}
            onClick={() => onSelectTicker?.(stock.ticker)}
            className={`ticker-pill ${selectedTicker === stock.ticker ? 'ticker-pill-active' : ''}`}
          >
            {stock.ticker}
          </button>
        ))}
      </div>

      <div className="glass-panel" style={{ padding: '30px' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
          <div>
            <h2 style={{ fontSize: '24px', fontWeight: '700' }}>{selectedStockData.name} ({selectedTicker})</h2>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px', marginTop: '4px' }}>{selectedStockData.sector} • {selectedStockData.exchange}</p>
          </div>
          {priceHistory.length > 0 && (
            <div style={{ textAlign: 'right' }}>
              <h3 style={{ fontSize: '28px', fontWeight: '800', color: 'var(--accent-blue)' }}>
                ${priceHistory[priceHistory.length - 1].close}
              </h3>
              <p style={{ fontSize: '12px', color: 'var(--color-success)', fontWeight: '600' }}>+1.45% past day</p>
            </div>
          )}
        </div>

        <div className="glass-panel" style={{ padding: '20px', background: 'rgba(0,0,0,0.15)', marginBottom: '30px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>Price History & AI Predictions (3-Day Horizon)</h4>
          {renderInteractiveChart()}
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '30px' }}>
          <div className="glass-panel" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: 'var(--color-text-secondary)' }}>Historic Price Points</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {priceHistory.length > 0 ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Open</span>
                    <span style={{ fontWeight: '600' }}>${priceHistory[priceHistory.length - 1].open}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>High</span>
                    <span style={{ fontWeight: '600' }}>${priceHistory[priceHistory.length - 1].high}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Low</span>
                    <span style={{ fontWeight: '600' }}>${priceHistory[priceHistory.length - 1].low}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Volume</span>
                    <span style={{ fontWeight: '600' }}>{priceHistory[priceHistory.length - 1].volume.toLocaleString()}</span>
                  </div>
                </>
              ) : <p style={{ opacity: 0.5 }}>Run ETL to seed database records.</p>}
            </div>
          </div>

          <div className="glass-panel" style={{ padding: '20px' }}>
            <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: 'var(--color-text-secondary)' }}>Risk Indicators</h4>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
              {riskMetrics ? (
                <>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Beta Index</span>
                    <span style={{ fontWeight: '600' }}>{riskMetrics.beta}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Sharpe Ratio</span>
                    <span style={{ fontWeight: '600' }}>{riskMetrics.sharpe_ratio}</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px' }}>
                    <span style={{ color: 'var(--color-text-muted)' }}>Value at Risk (VaR)</span>
                    <span style={{ fontWeight: '600', color: 'var(--color-danger)' }}>{(riskMetrics.value_at_risk * 100).toFixed(1)}%</span>
                  </div>
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: 'var(--color-text-muted)', borderTop: '1px solid var(--glass-border)', paddingTop: '8px', marginTop: '4px' }}>
                    <span>Source: {riskMetrics.source}</span>
                  </div>
                </>
              ) : <p style={{ opacity: 0.5 }}>No risk indicators loaded.</p>}
            </div>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px', marginTop: '30px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px', flexWrap: 'wrap', gap: '12px' }}>
            <div>
              <h4 style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc' }}>
                MLOps Model Registry & Deployment Benchmark
              </h4>
              <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>
                Accuracy metrics logged across historical evaluation runs.
              </p>
            </div>
            <div style={{ display: 'flex', gap: '16px', fontSize: '11px', background: '#090d16', padding: '6px 12px', borderRadius: '8px', border: '1px solid rgba(255,255,255,0.06)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#34d399', boxShadow: '0 0 8px #34d399' }}></span>
                <span style={{ color: '#34d399', fontWeight: '700' }}>DEPLOYED:</span>
                <span style={{ color: '#94a3b8' }}>Active serving model in API</span>
              </div>
              <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                <span style={{ width: '8px', height: '8px', borderRadius: '50%', backgroundColor: '#94a3b8' }}></span>
                <span style={{ color: '#cbd5e1', fontWeight: '700' }}>TRAINED:</span>
                <span style={{ color: '#94a3b8' }}>Evaluated baseline in registry</span>
              </div>
            </div>
          </div>

          <div style={{ overflowX: 'auto' }}>
            <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
              <thead>
                <tr style={{ borderBottom: '1px solid var(--glass-border)', color: '#94a3b8' }}>
                  <th style={{ padding: '12px 10px' }}>Model Name</th>
                  <th style={{ padding: '12px 10px' }}>Version</th>
                  <th style={{ padding: '12px 10px' }}>RMSE</th>
                  <th style={{ padding: '12px 10px' }}>MAPE</th>
                  <th style={{ padding: '12px 10px' }}>R² Score</th>
                  <th style={{ padding: '12px 10px' }}>Status</th>
                </tr>
              </thead>
              <tbody>
                {modelRegistry.map((model, idx) => (
                  <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }} className="table-row-hover">
                    <td style={{ padding: '12px 10px', fontWeight: '600', color: '#f8fafc' }}>{model.model_name}</td>
                    <td style={{ padding: '12px 10px', color: '#cbd5e1', fontFamily: 'var(--font-mono)' }}>{model.version}</td>
                    <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{model.rmse.toFixed(3)}</td>
                    <td style={{ padding: '12px 10px', fontFamily: 'var(--font-mono)' }}>{(model.mape * 100).toFixed(2)}%</td>
                    <td style={{ padding: '12px 10px', color: '#34d399', fontWeight: '700', fontFamily: 'var(--font-mono)' }}>{model.r2_score.toFixed(3)}</td>
                    <td style={{ padding: '12px 10px' }}>
                      <span className={model.status === 'DEPLOYED' ? 'badge-success' : 'btn-secondary'} style={{ fontSize: '10px', padding: '3px 8px', borderRadius: '4px' }}>
                        {model.status === 'DEPLOYED' ? '● DEPLOYED' : 'TRAINED'}
                      </span>
                    </td>
                  </tr>
                ))}
                {modelRegistry.length === 0 && (
                  <tr>
                    <td colSpan="6" style={{ padding: '16px', textAlign: 'center', opacity: 0.5 }}>Run Ingest/ETL to seed the models registry records.</td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>
    </div>
  );
}
