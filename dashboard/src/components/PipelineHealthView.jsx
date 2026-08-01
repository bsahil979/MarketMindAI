import React from 'react';

export default function PipelineHealthView({ etlRunning, etlHistory, handleRunEtl }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))', gap: '24px' }}>
        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--color-success)', boxShadow: '0 0 10px var(--color-success)' }}></div>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '600' }}>Ingestion Server (Spring Boot)</h4>
            <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>Operational on port 8080</p>
          </div>
        </div>

        <div className="glass-panel" style={{ padding: '24px', display: 'flex', alignItems: 'center', gap: '16px' }}>
          <div style={{ width: '10px', height: '10px', borderRadius: '50%', backgroundColor: 'var(--color-success)', boxShadow: '0 0 10px var(--color-success)' }}></div>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '600' }}>Analytics Database</h4>
            <p style={{ fontSize: '11px', color: 'var(--color-text-muted)', marginTop: '2px' }}>Active connections populated</p>
          </div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '6px' }}>Database ETL Sync Loader</h3>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
            Execute full database synchronization to parse raw JSON folder entries and load compiled star schemas indices.
          </p>
        </div>
        <button onClick={handleRunEtl} disabled={etlRunning} className="btn btn-primary" style={{ padding: '12px 24px' }}>
          {etlRunning ? <div className="spinner"></div> : 'Run ETL Sync Pipeline'}
        </button>
      </div>

      <div className="glass-panel" style={{ padding: '24px' }}>
        <h3 style={{ fontSize: '16px', fontWeight: '600', marginBottom: '20px' }}>Pipeline Run History</h3>
        <div style={{ overflowX: 'auto' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13.5px' }}>
            <thead>
              <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
                <th style={{ padding: '12px' }}>Run ID</th>
                <th style={{ padding: '12px' }}>Timestamp</th>
                <th style={{ padding: '12px' }}>Processed Records</th>
                <th style={{ padding: '12px' }}>Status</th>
              </tr>
            </thead>
            <tbody>
              {etlHistory.map(run => (
                <tr key={run.run_id} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                  <td style={{ padding: '12px', fontWeight: '600' }}>#{run.run_id}</td>
                  <td style={{ padding: '12px', color: 'var(--color-text-secondary)' }}>{run.run_date}</td>
                  <td style={{ padding: '12px' }}>{run.records_processed} files</td>
                  <td style={{ padding: '12px' }}>
                    <span style={{ padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: '600', backgroundColor: run.status === 'SUCCESS' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)', color: run.status === 'SUCCESS' ? 'var(--color-success)' : 'var(--color-danger)' }}>{run.status}</span>
                  </td>
                </tr>
              ))}
              {etlHistory.length === 0 && (
                <tr>
                  <td colSpan="4" style={{ padding: '20px', textAlign: 'center', opacity: 0.5 }}>No logs saved. Trigger a sync run to populate.</td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
