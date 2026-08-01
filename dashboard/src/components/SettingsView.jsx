import React from 'react';

export default function SettingsView({ schedulerEnabled, handleToggleScheduler, ingestionCount, username, getToken }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
      <div className="glass-panel" style={{ padding: '30px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '24px' }}>Automatic Ingestion Preferences</h3>

        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', paddingBottom: '20px', borderBottom: '1px solid var(--glass-border)' }}>
          <div>
            <h4 style={{ fontSize: '15px', fontWeight: '600', marginBottom: '4px' }}>Real-time Background Scheduler</h4>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '13px' }}>
              Enable or disable the Spring Boot background scheduled thread runner (runs every 30 seconds).
            </p>
          </div>
          <div style={{ position: 'relative', display: 'inline-block', width: '50px', height: '26px' }}>
            <input type="checkbox" id="schedulerToggle" checked={schedulerEnabled} onChange={(e) => handleToggleScheduler(e.target.checked)} style={{ opacity: 0, width: 0, height: 0 }} />
            <label htmlFor="schedulerToggle" style={{ position: 'absolute', cursor: 'pointer', inset: 0, backgroundColor: schedulerEnabled ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)', borderRadius: '34px', transition: '0.3s', display: 'flex', alignItems: 'center', justifyContent: schedulerEnabled ? 'flex-end' : 'flex-start', padding: '4px' }}>
              <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: '#ffffff', display: 'block', transition: '0.3s' }}></span>
            </label>
          </div>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '20px', paddingTop: '20px', fontSize: '13px' }}>
          <div>
            <span style={{ color: 'var(--color-text-muted)' }}>Prices Files Ingested in Session</span>
            <p style={{ fontSize: '20px', fontWeight: '700', marginTop: '6px', color: 'var(--accent-blue)' }}>{ingestionCount.prices}</p>
          </div>
          <div>
            <span style={{ color: 'var(--color-text-muted)' }}>News Files Ingested in Session</span>
            <p style={{ fontSize: '20px', fontWeight: '700', marginTop: '6px', color: 'var(--accent-purple)' }}>{ingestionCount.news}</p>
          </div>
        </div>
      </div>

      <div className="glass-panel" style={{ padding: '30px' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>User Details</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '16px', fontSize: '13.5px' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Registered Username</span>
            <span style={{ fontWeight: '600' }}>{username}</span>
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '12px', borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
            <span style={{ color: 'var(--color-text-secondary)' }}>Security Token Active</span>
            <span style={{ fontFamily: 'monospace', color: 'var(--color-text-muted)' }}>{getToken() ? 'Bearer *********' : 'None (Mock Auth)'}</span>
          </div>
        </div>
      </div>
    </div>
  );
}
