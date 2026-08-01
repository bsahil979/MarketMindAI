import React from 'react';

export default function PortfolioAllocatorView({
  portfolioCapital,
  setPortfolioCapital,
  portfolioRisk,
  setPortfolioRisk,
  portfolioDuration,
  setPortfolioDuration,
  portfolioResult,
  handleRunPortfolioAllocation,
}) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div className="glass-panel" style={{ padding: '30px' }}>
        <h3 style={{ fontSize: '20px', fontWeight: '700', color: '#f8fafc', marginBottom: '6px' }}>
          Risk-Adjusted Portfolio Allocation Calculator
        </h3>
        <p style={{ fontSize: '13px', color: '#94a3b8', marginBottom: '24px' }}>
          Configure your target investment capital, risk appetite, and horizon to generate optimized allocation recommendations.
        </p>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '20px', marginBottom: '24px' }}>
          <div>
            <label style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600', display: 'block', marginBottom: '8px' }}>Total Capital ($ or ₹)</label>
            <input
              type="number"
              className="input-field"
              value={portfolioCapital}
              onChange={(e) => setPortfolioCapital(Number(e.target.value))}
            />
          </div>
          <div>
            <label style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600', display: 'block', marginBottom: '8px' }}>Risk Appetite</label>
            <select
              className="input-field"
              value={portfolioRisk}
              onChange={(e) => setPortfolioRisk(e.target.value)}
            >
              <option value="Conservative">Conservative (Low Risk)</option>
              <option value="Moderate">Moderate (Balanced)</option>
              <option value="Aggressive">Aggressive (High Growth)</option>
            </select>
          </div>
          <div>
            <label style={{ fontSize: '12px', color: '#94a3b8', fontWeight: '600', display: 'block', marginBottom: '8px' }}>Time Horizon (Years)</label>
            <select
              className="input-field"
              value={portfolioDuration}
              onChange={(e) => setPortfolioDuration(Number(e.target.value))}
            >
              <option value={1}>1 Year (Short Term)</option>
              <option value={5}>5 Years (Medium Term)</option>
              <option value={10}>10 Years (Long Term)</option>
            </select>
          </div>
        </div>

        <button onClick={handleRunPortfolioAllocation} className="btn btn-primary" style={{ padding: '12px 28px', fontSize: '14px', fontWeight: '700' }}>
          Generate Recommendation
        </button>
      </div>

      {portfolioResult && (
        <div className="glass-panel" style={{ padding: '30px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '700', color: '#f8fafc', marginBottom: '16px' }}>
            Recommended Asset Allocation
          </h3>
          <p style={{ fontSize: '13.5px', color: '#cbd5e1', marginBottom: '24px' }}>{portfolioResult.summary}</p>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(260px, 1fr))', gap: '20px' }}>
            {portfolioResult.allocations.map((alloc, idx) => (
              <div key={idx} style={{ background: '#090d16', padding: '20px', borderRadius: '12px', border: `1px solid ${alloc.color}40` }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '10px' }}>
                  <span style={{ fontSize: '15px', fontWeight: '700', color: '#f8fafc' }}>{alloc.asset}</span>
                  <span style={{ fontSize: '16px', fontWeight: '800', color: alloc.color }}>{alloc.percentage}%</span>
                </div>
                <div className="visual-bar-track" style={{ marginBottom: '12px' }}>
                  <div className="visual-bar-fill" style={{ width: `${alloc.percentage}%`, background: alloc.color }}></div>
                </div>
                <div style={{ fontSize: '12px', color: '#94a3b8' }}>
                  Allocated Capital: <strong style={{ color: '#f8fafc' }}>${((portfolioCapital * alloc.percentage) / 100).toLocaleString()}</strong>
                </div>
                <div style={{ fontSize: '11.5px', color: '#cbd5e1', marginTop: '6px', fontStyle: 'italic' }}>
                  Rationale: {alloc.reason}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
