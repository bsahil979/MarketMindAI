import React, { useState, useEffect } from 'react';
import { api, getToken, clearToken, getUsername } from './services/api';

export default function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [currentTab, setCurrentTab] = useState('dashboard'); // dashboard, details, news, portfolio, copilot, health, settings
  const [username, setUsername] = useState('Guest');
  
  // Auth Form State
  const [isLoginView, setIsLoginView] = useState(true);
  const [authUsername, setAuthUsername] = useState('');
  const [authPassword, setAuthPassword] = useState('');
  const [authEmail, setAuthEmail] = useState('');
  const [authError, setAuthError] = useState('');
  const [authLoading, setAuthLoading] = useState(false);

  // Financial Data State
  const [stocks, setStocks] = useState([]);
  const [selectedTicker, setSelectedTicker] = useState('AAPL');
  const [selectedStockData, setSelectedStockData] = useState(null);
  const [priceHistory, setPriceHistory] = useState([]);
  const [forecastData, setForecastData] = useState([]);
  const [riskMetrics, setRiskMetrics] = useState(null);
  const [newsSentiment, setNewsSentiment] = useState(null);
  const [stocksLoading, setStocksLoading] = useState(false);
  const [modelRegistry, setModelRegistry] = useState([]);

  // Portfolio Watchlist
  const [watchlist, setWatchlist] = useState(['AAPL', 'MSFT']);

  // AI Copilot State
  const [chatMessages, setChatMessages] = useState([
    { sender: 'ai', text: "Hello! I am your MarketMind AI Copilot. Ask me about stock forecasts, risk metrics, or market sentiment indicators!" }
  ]);
  const [userInput, setUserInput] = useState('');

  // ETL / Telemetry State
  const [etlHistory, setEtlHistory] = useState([]);
  const [etlRunning, setEtlRunning] = useState(false);
  const [etlMessage, setEtlMessage] = useState('');
  const [schedulerEnabled, setSchedulerEnabled] = useState(true);
  const [ingestionCount, setIngestionCount] = useState({ prices: 0, news: 0 });

  // Check auth status on load
  useEffect(() => {
    const token = getToken();
    if (token) {
      setIsAuthenticated(true);
      setUsername(getUsername());
    }
    loadStocks();
    loadTelemetry();
    loadModelRegistry();
  }, []);

  // WebSockets live prices listener hook
  useEffect(() => {
    if (!isAuthenticated) return;
    
    // Connect to FastAPI live price streams socket
    const ws = new WebSocket("ws://localhost:8000/ws/prices");
    
    ws.onmessage = (event) => {
      try {
        const livePrices = JSON.parse(event.data);
        setStocks(prevStocks => {
          return prevStocks.map(stock => {
            const match = livePrices.find(lp => lp.ticker === stock.ticker);
            if (match) {
              return {
                ...stock,
                close: match.price,
                change: match.change
              };
            }
            return stock;
          });
        });
      } catch (e) {
        console.error("Websocket parsing error: ", e);
      }
    };

    ws.onerror = (e) => {
      console.warn("WebSocket error, falling back to database REST calls: ", e);
    };

    return () => {
      ws.close();
    };
  }, [isAuthenticated]);

  // Reload ticker details when selection changes
  useEffect(() => {
    if (selectedTicker) {
      loadTickerData(selectedTicker);
    }
  }, [selectedTicker]);

  const loadModelRegistry = async () => {
    try {
      const data = await api.getModelRegistry();
      setModelRegistry(data);
    } catch (e) {
      console.error("Failed to load model registry: ", e);
    }
  };

  const loadStocks = async () => {
    setStocksLoading(true);
    try {
      const data = await api.getStocks();
      setStocks(data);
      if (data.length > 0 && !selectedTicker) {
        setSelectedTicker(data[0].ticker);
      }
    } catch (e) {
      console.error(e);
    } finally {
      setStocksLoading(false);
    }
  };

  const loadTelemetry = async () => {
    try {
      const history = await api.getEtlHistory();
      setEtlHistory(history);
      
      const status = await api.getSchedulerStatus();
      setSchedulerEnabled(status.schedulerEnabled);
      setIngestionCount({
        prices: status.processedPricesCount || 0,
        news: status.processedNewsCount || 0
      });
    } catch (e) {
      console.error(e);
    }
  };

  const loadTickerData = async (ticker) => {
    try {
      const [pricesRes, forecastRes, riskRes, sentimentRes] = await Promise.all([
        api.getPrices(ticker),
        api.getForecast(ticker),
        api.getRisk(ticker),
        api.getSentiment(ticker)
      ]);

      setPriceHistory(pricesRes.prices || []);
      setForecastData(forecastRes.predictions || []);
      setRiskMetrics(riskRes);
      setNewsSentiment(sentimentRes);
      
      // Find stock display info
      const matched = stocks.find(s => s.ticker === ticker);
      setSelectedStockData(matched || { ticker, name: ticker + " Corp", sector: "Financial", exchange: "NASDAQ" });
    } catch (e) {
      console.error(e);
    }
  };

  // Auth Operations
  const handleAuth = async (e) => {
    e.preventDefault();
    setAuthError('');
    setAuthLoading(true);
    try {
      if (isLoginView) {
        await api.login(authUsername, authPassword);
        setIsAuthenticated(true);
        setUsername(getUsername());
        loadTelemetry(); // refresh telemetry with auth rights
      } else {
        const res = await api.register(authUsername, authPassword, authEmail);
        if (res.status === "SUCCESS") {
          setIsLoginView(true);
          setAuthError('Account created successfully! Please log in.');
        }
      }
    } catch (err) {
      setAuthError(err.message || 'Authentication operation failed');
    } finally {
      setAuthLoading(false);
    }
  };

  const handleLogout = () => {
    clearToken();
    setIsAuthenticated(false);
    setUsername('Guest');
  };

  // Watchlist Toggle
  const toggleWatchlist = (ticker) => {
    if (watchlist.includes(ticker)) {
      setWatchlist(watchlist.filter(t => t !== ticker));
    } else {
      setWatchlist([...watchlist, ticker]);
    }
  };

  // ETL Manual Trigger
  const handleRunEtl = async () => {
    setEtlRunning(true);
    setEtlMessage('');
    try {
      const res = await api.runEtl();
      if (res.status === "SUCCESS") {
        setEtlMessage(`ETL run completed successfully! Loaded ${res.records_processed} records.`);
        loadTelemetry();
        if (selectedTicker) loadTickerData(selectedTicker);
      } else {
        setEtlMessage(`ETL Run Failed: ${res.error_message}`);
      }
    } catch (e) {
      setEtlMessage(`ETL Execution Error: ${e.message}`);
    } finally {
      setEtlRunning(false);
    }
  };

  // Scheduler Status Toggle
  const handleToggleScheduler = async (checked) => {
    try {
      const res = await api.toggleScheduler(checked);
      setSchedulerEnabled(res.schedulerEnabled);
      loadTelemetry();
    } catch (e) {
      console.error(e);
    }
  };

  // Chat Submission
  const handleSendMessage = async (e) => {
    e.preventDefault();
    if (!userInput.trim()) return;

    const queryText = userInput;
    const userMsg = { sender: 'user', text: queryText };
    setChatMessages(prev => [...prev, userMsg]);
    setUserInput('');

    // Detect ticker in message or fallback to selectedTicker
    const cleanInput = queryText.toUpperCase();
    let detectedTicker = selectedTicker;
    const tickersList = ["AAPL", "MSFT", "GOOGL", "AMZN", "TSLA"];
    for (const t of tickersList) {
      if (cleanInput.includes(t)) {
        detectedTicker = t;
        break;
      }
    }

    try {
      const res = await api.copilotExplain(detectedTicker);
      setChatMessages(prev => [...prev, { sender: 'ai', text: res.explanation }]);
    } catch (err) {
      setChatMessages(prev => [...prev, { sender: 'ai', text: "Error connecting to AI Copilot database indexes: " + err.message }]);
    }
  };

  // Sparkline generator helper
  const renderSparkline = (pricesArray) => {
    if (!pricesArray || pricesArray.length < 2) return null;
    const closes = pricesArray.map(p => p.close);
    const min = Math.min(...closes);
    const max = Math.max(...closes);
    const range = max - min || 1;
    const width = 100;
    const height = 30;
    
    const points = closes.map((c, i) => {
      const x = (i / (closes.length - 1)) * width;
      const y = height - ((c - min) / range) * (height - 4) - 2;
      return `${x},${y}`;
    }).join(' ');

    const color = closes[closes.length - 1] >= closes[0] ? 'var(--color-success)' : 'var(--color-danger)';

    return (
      <svg width={width} height={height} style={{ overflow: 'visible' }}>
        <polyline fill="none" stroke={color} strokeWidth="1.8" points={points} />
      </svg>
    );
  };

  // High-fidelity Price/Forecast custom chart
  const renderInteractiveChart = () => {
    if (priceHistory.length === 0) return <div style={{ padding: '40px', textAlign: 'center', opacity: 0.5 }}>No price data available</div>;

    const priceCloses = priceHistory.map(p => p.close);
    const forecastCloses = forecastData.map(f => f.predicted_close);
    const allCloses = [...priceCloses, ...forecastCloses];
    
    const min = Math.min(...allCloses) * 0.98;
    const max = Math.max(...allCloses) * 1.02;
    const range = max - min;

    const width = 600;
    const height = 280;
    const paddingLeft = 40;
    const paddingRight = 20;
    const paddingTop = 20;
    const paddingBottom = 40;

    const chartWidth = width - paddingLeft - paddingRight;
    const chartHeight = height - paddingTop - paddingBottom;

    // Convert data to points
    const getCoordinates = (val, idx, total) => {
      const x = paddingLeft + (idx / (total - 1)) * chartWidth;
      const y = paddingTop + chartHeight - ((val - min) / range) * chartHeight;
      return { x, y };
    };

    const totalPointsCount = priceHistory.length + forecastData.length;
    const pricePoints = priceHistory.map((p, i) => getCoordinates(p.close, i, totalPointsCount));
    
    // Connect first forecast point to last historical point
    const forecastPoints = [];
    if (pricePoints.length > 0) {
      forecastPoints.push(pricePoints[pricePoints.length - 1]);
    }
    forecastData.forEach((f, i) => {
      forecastPoints.push(getCoordinates(f.predicted_close, priceHistory.length + i, totalPointsCount));
    });

    const pricePath = pricePoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
    const forecastPath = forecastPoints.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');

    // Fill gradients area paths
    const priceAreaPath = pricePoints.length > 0 
      ? `${pricePath} L ${pricePoints[pricePoints.length - 1].x} ${paddingTop + chartHeight} L ${pricePoints[0].x} ${paddingTop + chartHeight} Z`
      : '';
    const forecastAreaPath = forecastPoints.length > 0 
      ? `${forecastPath} L ${forecastPoints[forecastPoints.length - 1].x} ${paddingTop + chartHeight} L ${forecastPoints[0].x} ${paddingTop + chartHeight} Z`
      : '';

    return (
      <div style={{ position: 'relative', width: '100%', overflowX: 'auto' }}>
        <svg width="100%" height={height} viewBox={`0 0 ${width} ${height}`} preserveAspectRatio="none">
          <defs>
            <linearGradient id="priceAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-blue)" stopOpacity="0.25" />
              <stop offset="100%" stopColor="var(--accent-blue)" stopOpacity="0.0" />
            </linearGradient>
            <linearGradient id="forecastAreaGrad" x1="0" y1="0" x2="0" y2="1">
              <stop offset="0%" stopColor="var(--accent-purple)" stopOpacity="0.2" />
              <stop offset="100%" stopColor="var(--accent-purple)" stopOpacity="0.0" />
            </linearGradient>
          </defs>

          {/* Grid lines */}
          {[0, 0.25, 0.5, 0.75, 1].map((r, idx) => {
            const y = paddingTop + r * chartHeight;
            const priceVal = min + (1 - r) * range;
            return (
              <g key={idx}>
                <line x1={paddingLeft} y1={y} x2={width - paddingRight} y2={y} stroke="rgba(255,255,255,0.05)" strokeWidth="1" />
                <text x={paddingLeft - 8} y={y + 4} fill="var(--color-text-secondary)" fontSize="10" textAnchor="end">
                  ${Math.round(priceVal)}
                </text>
              </g>
            );
          })}

          {/* Area Gradients */}
          {priceAreaPath && <path d={priceAreaPath} fill="url(#priceAreaGrad)" />}
          {forecastAreaPath && <path d={forecastAreaPath} fill="url(#forecastAreaGrad)" />}

          {/* Axis Labels */}
          <line x1={paddingLeft} y1={paddingTop + chartHeight} x2={width - paddingRight} y2={paddingTop + chartHeight} stroke="rgba(255,255,255,0.15)" strokeWidth="1.2" />

          {/* Lines */}
          {pricePath && <path d={pricePath} fill="none" stroke="var(--accent-blue)" strokeWidth="2.5" className="animate-chart-line" />}
          {forecastPath && <path d={forecastPath} fill="none" stroke="var(--accent-purple)" strokeWidth="2.5" strokeDasharray="4 4" />}

          {/* Date labels */}
          {pricePoints.length > 0 && (
            <text x={pricePoints[0].x} y={paddingTop + chartHeight + 18} fill="var(--color-text-secondary)" fontSize="9" textAnchor="middle">
              {priceHistory[0].date}
            </text>
          )}
          {pricePoints.length > 1 && (
            <text x={pricePoints[pricePoints.length - 1].x} y={paddingTop + chartHeight + 18} fill="var(--color-text-secondary)" fontSize="9" textAnchor="middle">
              {priceHistory[priceHistory.length - 1].date}
            </text>
          )}
          {forecastPoints.length > 1 && (
            <text x={forecastPoints[forecastPoints.length - 1].x} y={paddingTop + chartHeight + 18} fill="var(--accent-purple)" fontSize="9" textAnchor="middle">
              {forecastData[forecastData.length - 1].date} (FC)
            </text>
          )}

          {/* Legend */}
          <g transform={`translate(${paddingLeft + 15}, 15)`}>
            <line x1="0" y1="5" x2="20" y2="5" stroke="var(--accent-blue)" strokeWidth="2.5" />
            <text x="25" y="9" fill="var(--color-text-primary)" fontSize="11">Historical</text>
            <line x1="100" y1="5" x2="120" y2="5" stroke="var(--accent-purple)" strokeWidth="2.5" strokeDasharray="4 4" />
            <text x="125" y="9" fill="var(--color-text-primary)" fontSize="11">AI Forecast</text>
          </g>
        </svg>
      </div>
    );
  };

  // Render Login/Register view if not logged in
  if (!isAuthenticated) {
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
              {isLoginView ? "Don't have an account? " : "Already have an account? "}
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

  // Main Authorized Application
  return (
    <div style={{ display: 'grid', gridTemplateColumns: '260px 1fr', minHeight: '100vh' }}>
      
      {/* Sidebar Navigation */}
      <aside className="glass-panel" style={{ borderRadius: '0', borderLeft: 'none', borderTop: 'none', borderBottom: 'none', display: 'flex', flexDirection: 'column', height: '100vh', position: 'sticky', top: '0', zIndex: 10 }}>
        
        {/* Brand */}
        <div style={{ padding: '30px 24px', borderBottom: '1px solid var(--glass-border)' }}>
          <h2 className="text-gradient-purple-blue" style={{ fontSize: '22px', fontWeight: '800', letterSpacing: '-0.5px' }}>MarketMind AI</h2>
          <div style={{ display: 'flex', alignItems: 'center', gap: '6px', marginTop: '4px' }}>
            <span style={{ width: '6px', height: '6px', borderRadius: '50%', backgroundColor: 'var(--color-success)' }}></span>
            <span style={{ fontSize: '11px', color: 'var(--color-text-muted)', fontWeight: '500' }}>Live Engine Connected</span>
          </div>
        </div>

        {/* Navigation list */}
        <nav style={{ flex: 1, padding: '24px 16px', display: 'flex', flexDirection: 'column', gap: '8px' }}>
          {[
            { id: 'dashboard', label: 'Dashboard', icon: 'M4 5a2 2 0 012-2h8a2 2 0 012 2v3a2 2 0 01-2 2H6a2 2 0 01-2-2V5z M4 15a2 2 0 012-2h8a2 2 0 012 2v3a2 2 0 01-2 2H6a2 2 0 01-2-2v-3z' },
            { id: 'details', label: 'Stock Details', icon: 'M13 6a3 3 0 11-6 0 3 3 0 016 0zM18 8a2 2 0 11-4 0 2 2 0 014 0zM14 15a4 4 0 00-8 0v3h8v-3zM6 8a2 2 0 11-4 0 2 2 0 014 0zM16 18v-3a.997.997 0 00-.751-.967A4.996 4.996 0 0011 12H9c-.73 0-1.4.158-2.002.441A1.996 1.996 0 018 14H8a2 2 0 012 2v3h6z' },
            { id: 'news', label: 'News Sentiment', icon: 'M2 5a2 2 0 012-2h7a2 2 0 012 2v4a2 2 0 01-2 2H9l-3 3v-3H4a2 2 0 01-2-2V5z M15 7h2a2 2 0 012 2v4a2 2 0 01-2 2h-3v3l-3-3H9a2 2 0 01-2-2v-1' },
            { id: 'portfolio', label: 'Portfolio & Watch', icon: 'M4 4a2 2 0 00-2 2v1h16V6a2 2 0 00-2-2H4z M18 9H2v5a2 2 0 002 2h12a2 2 0 002-2V9z M4 13a1 1 0 011-1h1a1 1 0 110 2H5a1 1 0 01-1-1z' },
            { id: 'copilot', label: 'AI Copilot', icon: 'M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-2 0c0-2.21-1.79-4-4-4s-4 1.79-4 4 1.79 4 4 4 4-1.79 4-4z' },
            { id: 'health', label: 'Pipeline Health', icon: 'M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z' },
            { id: 'settings', label: 'Settings', icon: 'M11.49 3.17c-.38-1.56-2.6-1.56-2.98 0a1.532 1.532 0 01-2.286.948c-1.372-.836-2.942.734-2.106 2.106.54.886.061 2.042-.947 2.287-1.561.379-1.561 2.6 0 2.978a1.532 1.532 0 01.947 2.287c-.836 1.372.734 2.942 2.106 2.106a1.532 1.532 0 012.287.947c.379 1.561 2.6 1.561 2.978 0a1.533 1.533 0 012.287-.947c1.372.836 2.942-.734 2.106-2.106a1.533 1.533 0 01.947-2.287c1.561-.379 1.561-2.6 0-2.978a1.532 1.532 0 01-.947-2.287c.836-1.372-.734-2.942-2.106-2.106a1.532 1.532 0 01-2.287-.947zM10 13a3 3 0 100-6 3 3 0 000 6z' },
          ].map(tab => (
            <button
              key={tab.id}
              onClick={() => setCurrentTab(tab.id)}
              className="btn"
              style={{
                width: '100%',
                justifyContent: 'flex-start',
                background: currentTab === tab.id ? 'rgba(255,255,255,0.08)' : 'transparent',
                border: 'none',
                color: currentTab === tab.id ? 'var(--color-text-primary)' : 'var(--color-text-secondary)',
                padding: '12px 16px',
                gap: '12px'
              }}
            >
              <svg width="18" height="18" viewBox="0 0 20 20" fill="currentColor" style={{ opacity: currentTab === tab.id ? 1 : 0.6 }}>
                <path fillRule="evenodd" d={tab.icon} clipRule="evenodd" />
              </svg>
              <span style={{ fontWeight: currentTab === tab.id ? '600' : '400' }}>{tab.label}</span>
            </button>
          ))}
        </nav>

        {/* User Card */}
        <div style={{ padding: '20px 16px', borderTop: '1px solid var(--glass-border)', display: 'flex', flexDirection: 'column', gap: '12px' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '36px', height: '36px', borderRadius: '50%', background: 'linear-gradient(135deg, var(--accent-purple) 0%, var(--accent-blue) 100%)', display: 'flex', alignItems: 'center', justifySelf: 'center', justifyContent: 'center', fontSize: '14px', fontWeight: '700' }}>
              {username[0].toUpperCase()}
            </div>
            <div style={{ flex: 1, minWidth: '0' }}>
              <p style={{ fontSize: '13px', fontWeight: '600', color: 'var(--color-text-primary)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{username}</p>
              <p style={{ fontSize: '11px', color: 'var(--color-text-muted)' }}>Professional Account</p>
            </div>
          </div>
          <button onClick={handleLogout} className="btn btn-secondary" style={{ width: '100%', padding: '8px', fontSize: '12px' }}>
            Sign Out
          </button>
        </div>
      </aside>

      {/* Main View Area */}
      <main style={{ padding: '40px', overflowY: 'auto', maxHeight: '100vh' }}>
        
        {/* Header Summary */}
        <header style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '40px', gap: '20px' }}>
          <div>
            <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '6px' }}>
              {currentTab === 'dashboard' && 'Market Overview'}
              {currentTab === 'details' && `Stock Analytics: ${selectedTicker}`}
              {currentTab === 'news' && 'Sentiment Signals'}
              {currentTab === 'portfolio' && 'Watchlists & Holdings'}
              {currentTab === 'copilot' && 'AI Market Copilot'}
              {currentTab === 'health' && 'Pipeline Control Telemetry'}
              {currentTab === 'settings' && 'Platform Settings'}
            </h1>
            <p style={{ color: 'var(--color-text-secondary)', fontSize: '14px' }}>
              {currentTab === 'dashboard' && 'Explore real-time listings, volumes, and historic stock index sparklines.'}
              {currentTab === 'details' && `In-depth statistics, risk metrics, and linear regression models for ${selectedTicker}.`}
              {currentTab === 'news' && 'Calculated financial news sentiment indices from major media channels.'}
              {currentTab === 'portfolio' && 'Monitor your saved stock tickers and mock assets allocation splits.'}
              {currentTab === 'copilot' && 'Prompt-based conversational agent backed by facts model calculations.'}
              {currentTab === 'health' && 'Trigger manual ETL loads, archive raw data files, and inspect telemetry history.'}
              {currentTab === 'settings' && 'Manage local ingestion properties and scheduler settings.'}
            </p>
          </div>

          <div style={{ display: 'flex', gap: '12px' }}>
            <button 
              onClick={handleRunEtl} 
              disabled={etlRunning} 
              className="btn btn-primary"
              style={{ gap: '8px' }}
            >
              {etlRunning ? <div className="spinner"></div> : (
                <>
                  <svg width="16" height="16" viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M4 2a1 1 0 011 1v2.101a7.002 7.002 0 0111.601 2.566 1 1 0 11-1.885.666A5.002 5.002 0 005.999 7H9a1 1 0 110 2H4a1 1 0 01-1-1V3a1 1 0 011-1zm.008 9.057a1 1 0 011.254-.676A5.002 5.002 0 0014.001 13H11a1 1 0 110-2h5a1 1 0 011 1v5a1 1 0 11-2 0v-2.101a7.002 7.002 0 01-11.601-2.566 1 1 0 01.61-1.276z" clipRule="evenodd" />
                  </svg>
                  <span>Sync ETL</span>
                </>
              )}
            </button>
          </div>
        </header>

        {etlMessage && (
          <div className="glass-panel" style={{ padding: '16px 20px', background: 'rgba(59,130,246,0.06)', borderColor: 'rgba(59,130,246,0.2)', color: 'var(--accent-blue)', marginBottom: '30px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderRadius: '12px', fontSize: '14px' }}>
            <span>{etlMessage}</span>
            <button onClick={() => setEtlMessage('')} style={{ background: 'none', border: 'none', color: 'inherit', cursor: 'pointer', fontSize: '16px', fontWeight: 'bold' }}>&times;</button>
          </div>
        )}

        {/* --- VIEW: DASHBOARD --- */}
        {currentTab === 'dashboard' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            
            {/* Index Grid */}
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '24px' }}>
              {[
                { name: "S&P 500 Index", val: "5,432.12", chg: "+0.32%", up: true },
                { name: "NASDAQ Composite", val: "17,845.60", chg: "+0.85%", up: true },
                { name: "Dow Jones Industrial", val: "39,120.45", chg: "-0.14%", up: false },
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

            {/* Main Stock List table */}
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
                            <td style={{ padding: '16px' }}>
                              {/* deterministic sparklines for lists */}
                              {renderSparkline([
                                { close: 100 }, { close: 102 }, { close: 98 }, { close: 105 }, 
                                { close: stock.ticker === 'TSLA' ? 95 : 108 }
                              ])}
                            </td>
                            <td style={{ padding: '16px', textAlign: 'right' }}>
                              <div style={{ display: 'inline-flex', gap: '8px' }}>
                                <button 
                                  onClick={() => { setSelectedTicker(stock.ticker); setCurrentTab('details'); }} 
                                  className="btn btn-secondary" 
                                  style={{ padding: '6px 12px', fontSize: '12px' }}
                                >
                                  Analyze
                                </button>
                                <button 
                                  onClick={() => toggleWatchlist(stock.ticker)} 
                                  className="btn btn-secondary" 
                                  style={{ padding: '6px 10px', fontSize: '12px' }}
                                >
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
        )}

        {/* --- VIEW: STOCK DETAILS --- */}
        {currentTab === 'details' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            
            {/* Ticker selector tab bar */}
            <div style={{ display: 'flex', gap: '10px', borderBottom: '1px solid var(--glass-border)', paddingBottom: '16px' }}>
              {stocks.map(s => (
                <button
                  key={s.ticker}
                  onClick={() => setSelectedTicker(s.ticker)}
                  className="btn"
                  style={{
                    background: selectedTicker === s.ticker ? 'var(--accent-blue)' : 'rgba(255,255,255,0.03)',
                    color: '#ffffff',
                    padding: '8px 16px',
                    fontSize: '13px'
                  }}
                >
                  {s.ticker}
                </button>
              ))}
            </div>

            {selectedStockData && (
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

                {/* Primary SVG Chart */}
                <div className="glass-panel" style={{ padding: '20px', background: 'rgba(0,0,0,0.15)', marginBottom: '30px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '16px' }}>Price History & AI Predictions (3-Day Horizon)</h4>
                  {renderInteractiveChart()}
                </div>

                {/* Grid details */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '30px' }}>
                  
                  {/* Stats Grid */}
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

                  {/* Risk Analytics Grid */}
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

                {/* Model Registry Comparison Table */}
                <div className="glass-panel" style={{ padding: '20px', marginTop: '30px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '16px', color: 'var(--color-text-secondary)' }}>
                    MLOps Model Registry Performance Comparison
                  </h4>
                  <div style={{ overflowX: 'auto' }}>
                    <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left', fontSize: '13px' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid var(--glass-border)', color: 'var(--color-text-secondary)' }}>
                          <th style={{ padding: '10px' }}>Model Name</th>
                          <th style={{ padding: '10px' }}>Version</th>
                          <th style={{ padding: '10px' }}>RMSE</th>
                          <th style={{ padding: '10px' }}>MAPE</th>
                          <th style={{ padding: '10px' }}>R² Score</th>
                          <th style={{ padding: '10px' }}>Status</th>
                        </tr>
                      </thead>
                      <tbody>
                        {modelRegistry.map((model, idx) => (
                          <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.03)' }}>
                            <td style={{ padding: '10px', fontWeight: '600' }}>{model.model_name}</td>
                            <td style={{ padding: '10px', color: 'var(--color-text-secondary)' }}>{model.version}</td>
                            <td style={{ padding: '10px' }}>{model.rmse.toFixed(3)}</td>
                            <td style={{ padding: '10px' }}>{(model.mape * 100).toFixed(2)}%</td>
                            <td style={{ padding: '10px', color: 'var(--color-success)', fontWeight: '600' }}>{model.r2_score.toFixed(3)}</td>
                            <td style={{ padding: '10px' }}>
                              <span style={{
                                padding: '2px 6px',
                                borderRadius: '4px',
                                fontSize: '10px',
                                fontWeight: '600',
                                backgroundColor: model.status === 'DEPLOYED' ? 'rgba(16,185,129,0.1)' : 'rgba(255,255,255,0.05)',
                                color: model.status === 'DEPLOYED' ? 'var(--color-success)' : 'var(--color-text-secondary)'
                              }}>{model.status}</span>
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
            )}
          </div>
        )}

        {/* --- VIEW: NEWS SENTIMENT --- */}
        {currentTab === 'news' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            {/* Selector */}
            <div style={{ display: 'flex', gap: '10px' }}>
              {stocks.map(s => (
                <button
                  key={s.ticker}
                  onClick={() => setSelectedTicker(s.ticker)}
                  className="btn"
                  style={{
                    background: selectedTicker === s.ticker ? 'var(--accent-purple)' : 'rgba(255,255,255,0.03)',
                    color: '#ffffff',
                    padding: '8px 16px',
                    fontSize: '13px'
                  }}
                >
                  {s.ticker}
                </button>
              ))}
            </div>

            {newsSentiment ? (
              <div style={{ display: 'grid', gridTemplateColumns: '320px 1fr', gap: '30px', alignItems: 'flex-start' }}>
                
                {/* Score Summary Panel */}
                <div className="glass-panel" style={{ padding: '24px', display: 'flex', flexDirection: 'column', alignItems: 'center', textAlign: 'center' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '24px' }}>Sentiment Rating Index</h4>
                  
                  {/* Circle gauge representation */}
                  <div style={{ width: '120px', height: '120px', borderRadius: '50%', border: '8px solid rgba(255,255,255,0.04)', display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', position: 'relative', marginBottom: '20px' }}>
                    <div style={{ position: 'absolute', inset: '-8px', borderRadius: '50%', border: '8px solid transparent', borderTopColor: newsSentiment.overall_sentiment >= 0 ? 'var(--color-success)' : 'var(--color-danger)', transform: `rotate(${(newsSentiment.overall_sentiment + 1) * 90}deg)` }}></div>
                    <span style={{ fontSize: '28px', fontWeight: '800', color: newsSentiment.overall_sentiment >= 0 ? 'var(--color-success)' : 'var(--color-danger)' }}>
                      {newsSentiment.overall_sentiment >= 0 ? '+' : ''}{newsSentiment.overall_sentiment.toFixed(2)}
                    </span>
                    <span style={{ fontSize: '10px', color: 'var(--color-text-muted)', marginTop: '2px' }}>Confidence: {newsSentiment.confidence}</span>
                  </div>

                  <h3 style={{ fontSize: '18px', fontWeight: '700', marginBottom: '8px' }}>
                    {newsSentiment.overall_sentiment > 0.15 ? 'Bullish Sentiment' : newsSentiment.overall_sentiment < -0.15 ? 'Bearish Sentiment' : 'Neutral Sentiment'}
                  </h3>
                  <p style={{ fontSize: '13px', color: 'var(--color-text-secondary)' }}>Based on parsed article contents loaded in DB fact index.</p>
                </div>

                {/* News timeline list */}
                <div className="glass-panel" style={{ padding: '24px' }}>
                  <h4 style={{ fontSize: '14px', fontWeight: '600', color: 'var(--color-text-secondary)', marginBottom: '20px' }}>Headlines Timeline</h4>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                    {newsSentiment.news_items && newsSentiment.news_items.length > 0 ? (
                      newsSentiment.news_items.map((item, idx) => (
                        <div key={idx} style={{ paddingBottom: '16px', borderBottom: '1px solid rgba(255,255,255,0.04)', display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', gap: '16px' }}>
                          <div>
                            <h5 style={{ fontSize: '14px', fontWeight: '600', marginBottom: '6px', lineHeight: '1.4' }}>{item.title}</h5>
                            <div style={{ display: 'flex', gap: '12px', fontSize: '11px', color: 'var(--color-text-muted)' }}>
                              <span>Source: {item.source}</span>
                              <span>•</span>
                              <a href={item.url} target="_blank" rel="noopener noreferrer" style={{ color: 'var(--accent-blue)', textDecoration: 'none' }}>Original URL</a>
                            </div>
                          </div>
                          <span style={{
                            padding: '3px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: '600',
                            backgroundColor: item.sentiment_score > 0 ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                            color: item.sentiment_score > 0 ? 'var(--color-success)' : 'var(--color-danger)',
                            border: `1px solid ${item.sentiment_score > 0 ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)'}`
                          }}>
                            {item.sentiment_score > 0 ? '+' : ''}{item.sentiment_score.toFixed(1)}
                          </span>
                        </div>
                      ))
                    ) : <p style={{ opacity: 0.5 }}>Run Ingestion & ETL to load news articles sentiment.</p>}
                  </div>
                </div>

              </div>
            ) : <div style={{ display: 'flex', justifyContent: 'center', padding: '40px' }}><div className="spinner"></div></div>}
          </div>
        )}

        {/* --- VIEW: PORTFOLIO --- */}
        {currentTab === 'portfolio' && (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 340px', gap: '30px' }}>
            
            {/* Watchlist */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Active Watchlist</h3>
              {watchlist.length > 0 ? (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {watchlist.map(ticker => {
                    const matched = stocks.find(s => s.ticker === ticker);
                    return (
                      <div key={ticker} className="glass-panel" style={{ padding: '16px 20px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <h4 style={{ fontSize: '16px', fontWeight: '700' }}>{ticker}</h4>
                          <p style={{ fontSize: '11px', color: 'var(--color-text-secondary)', marginTop: '2px' }}>{matched ? matched.name : 'Stock Ticker'}</p>
                        </div>
                        <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                          <button 
                            onClick={() => { setSelectedTicker(ticker); setCurrentTab('details'); }} 
                            className="btn btn-secondary" 
                            style={{ padding: '6px 12px', fontSize: '12px' }}
                          >
                            Analyze
                          </button>
                          <button 
                            onClick={() => toggleWatchlist(ticker)} 
                            className="btn" 
                            style={{ padding: '6px', background: 'none', border: 'none', color: 'var(--color-danger)', cursor: 'pointer', fontSize: '16px' }}
                          >
                            &times;
                          </button>
                        </div>
                      </div>
                    );
                  })}
                </div>
              ) : <p style={{ opacity: 0.5 }}>Your watchlist is currently empty. Star stocks from the dashboard to add them.</p>}
            </div>

            {/* Asset Allocation Panel */}
            <div className="glass-panel" style={{ padding: '24px' }}>
              <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '20px' }}>Asset Allocation</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '20px' }}>
                {[
                  { asset: "Technology Stocks", pct: 60, val: "$12,400.00", color: "var(--accent-blue)" },
                  { asset: "Consumer Discretionary", pct: 25, val: "$5,100.00", color: "var(--accent-purple)" },
                  { asset: "Liquid Reserves", pct: 15, val: "$3,000.00", color: "var(--color-success)" }
                ].map((item, idx) => (
                  <div key={idx}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '13px', marginBottom: '6px' }}>
                      <span style={{ fontWeight: '500' }}>{item.asset}</span>
                      <span style={{ color: 'var(--color-text-secondary)' }}>{item.val} ({item.pct}%)</span>
                    </div>
                    <div style={{ width: '100%', height: '6px', backgroundColor: 'rgba(255,255,255,0.05)', borderRadius: '3px', overflow: 'hidden' }}>
                      <div style={{ width: `${item.pct}%`, height: '100%', backgroundColor: item.color }}></div>
                    </div>
                  </div>
                ))}
              </div>
            </div>

          </div>
        )}

        {/* --- VIEW: AI COPILOT --- */}
        {currentTab === 'copilot' && (
          <div className="glass-panel" style={{ display: 'flex', flexDirection: 'column', height: '560px', overflow: 'hidden' }}>
            
            {/* Conversation Log */}
            <div style={{ flex: 1, padding: '24px', overflowY: 'auto', display: 'flex', flexDirection: 'column', gap: '16px' }}>
              {chatMessages.map((msg, i) => (
                <div 
                  key={i} 
                  style={{
                    display: 'flex', 
                    justifyContent: msg.sender === 'ai' ? 'flex-start' : 'flex-end',
                  }}
                >
                  <div 
                    className="glass-panel" 
                    style={{
                      maxWidth: '75%', 
                      padding: '12px 18px', 
                      background: msg.sender === 'ai' ? 'var(--glass-bg)' : 'linear-gradient(135deg, rgba(168,85,247,0.1) 0%, rgba(59,130,246,0.1) 100%)',
                      borderColor: msg.sender === 'ai' ? 'var(--glass-border)' : 'rgba(59,130,246,0.2)',
                      borderRadius: msg.sender === 'ai' ? '16px 16px 16px 4px' : '16px 16px 4px 16px',
                      fontSize: '13.5px',
                      lineHeight: '1.5'
                    }}
                  >
                    <p>{msg.text}</p>
                  </div>
                </div>
              ))}
            </div>

            {/* Prompt input Form */}
            <form onSubmit={handleSendMessage} style={{ padding: '16px 24px', borderTop: '1px solid var(--glass-border)', display: 'flex', gap: '12px' }}>
              <input 
                type="text" 
                className="input-field" 
                placeholder="Ask about forecast prices, beta risk, or database sentiments..." 
                value={userInput}
                onChange={(e) => setUserInput(e.target.value)}
              />
              <button type="submit" className="btn btn-primary">
                Send
              </button>
            </form>

          </div>
        )}

        {/* --- VIEW: PIPELINE HEALTH --- */}
        {currentTab === 'health' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            
            {/* Connection Status cards */}
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

            {/* ETL Trigger control */}
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

            {/* Pipeline Runs history */}
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
                          <span style={{
                            padding: '2px 8px',
                            borderRadius: '4px',
                            fontSize: '11px',
                            fontWeight: '600',
                            backgroundColor: run.status === 'SUCCESS' ? 'rgba(16,185,129,0.1)' : 'rgba(239,68,68,0.1)',
                            color: run.status === 'SUCCESS' ? 'var(--color-success)' : 'var(--color-danger)'
                          }}>{run.status}</span>
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
        )}

        {/* --- VIEW: SETTINGS --- */}
        {currentTab === 'settings' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '30px' }}>
            
            {/* Scheduler toggles */}
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
                  <input 
                    type="checkbox" 
                    id="schedulerToggle" 
                    checked={schedulerEnabled}
                    onChange={(e) => handleToggleScheduler(e.target.checked)}
                    style={{ opacity: 0, width: 0, height: 0 }}
                  />
                  <label 
                    htmlFor="schedulerToggle" 
                    style={{
                      position: 'absolute', cursor: 'pointer', inset: 0, 
                      backgroundColor: schedulerEnabled ? 'var(--accent-blue)' : 'rgba(255,255,255,0.1)',
                      borderRadius: '34px', transition: '0.3s',
                      display: 'flex', alignItems: 'center',
                      justifyContent: schedulerEnabled ? 'flex-end' : 'flex-start',
                      padding: '4px'
                    }}
                  >
                    <span style={{ width: '18px', height: '18px', borderRadius: '50%', backgroundColor: '#ffffff', display: 'block', transition: '0.3s' }}></span>
                  </label>
                </div>
              </div>

              {/* Status details */}
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

            {/* Profile specifications */}
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
        )}

      </main>

    </div>
  );
}
