import React from 'react';

export default function AuthPanel({
  isLoginView,
  authUsername,
  authPassword,
  authEmail,
  authError,
  authLoading,
  setAuthUsername,
  setAuthPassword,
  setAuthEmail,
  setIsLoginView,
  setAuthError,
  handleAuth,
}) {
  return (
    <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', minHeight: '100vh', padding: '20px' }}>
      <div className="glass-panel" style={{ width: '100%', maxWidth: '420px', padding: '40px', boxShadow: '0 20px 40px rgba(0,0,0,0.6)' }}>
        <div style={{ textAlign: 'center', marginBottom: '30px' }}>
          <h1 className="text-gradient-purple-blue" style={{ fontSize: '32px', fontWeight: '800', marginBottom: '8px' }}>MarketMind AI</h1>
          <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>Real-Time Financial Intelligence Engine</p>
        </div>

        <form onSubmit={handleAuth} style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
          {authError && (
            <div className="glass-panel" style={{ padding: '12px 16px', background: 'rgba(239, 68, 68, 0.08)', borderColor: 'rgba(239, 68, 68, 0.2)', color: 'var(--color-danger)', fontSize: '13px' }}>
              {authError}
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>Username</label>
            <input
              type="text"
              required
              className="input-field"
              placeholder="Enter username"
              value={authUsername}
              onChange={(e) => setAuthUsername(e.target.value)}
            />
          </div>

          {!isLoginView && (
            <div>
              <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>Email</label>
              <input
                type="email"
                className="input-field"
                placeholder="Enter email (optional)"
                value={authEmail}
                onChange={(e) => setAuthEmail(e.target.value)}
              />
            </div>
          )}

          <div>
            <label style={{ display: 'block', marginBottom: '8px', fontSize: '13px', color: 'var(--color-text-secondary)' }}>Password</label>
            <input
              type="password"
              required
              className="input-field"
              placeholder="Enter password"
              value={authPassword}
              onChange={(e) => setAuthPassword(e.target.value)}
            />
          </div>

          <button type="submit" className="btn btn-primary" style={{ width: '100%', height: '45px', marginTop: '10px' }} disabled={authLoading}>
            {authLoading ? <div className="spinner"></div> : (isLoginView ? 'Sign In' : 'Register Account')}
          </button>
        </form>

        <div style={{ textAlign: 'center', marginTop: '24px', fontSize: '13px' }}>
          <span style={{ color: 'var(--color-text-secondary)' }}>
            {isLoginView ? "Don't have an account? " : 'Already have an account? '}
          </span>
          <button
            onClick={() => { setIsLoginView(!isLoginView); setAuthError(''); }}
            style={{ background: 'none', border: 'none', color: 'var(--accent-blue)', fontWeight: '600', cursor: 'pointer' }}
          >
            {isLoginView ? 'Register Now' : 'Sign In'}
          </button>
        </div>
      </div>
    </div>
  );
}
