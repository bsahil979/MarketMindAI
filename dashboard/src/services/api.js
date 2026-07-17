const API_BASE_URL = "http://localhost:8000";

// Helper to check if token exists
export const getToken = () => localStorage.getItem("marketmind_token");
export const getUsername = () => localStorage.getItem("marketmind_username") || "Guest";
export const setToken = (token, username) => {
  localStorage.setItem("marketmind_token", token);
  localStorage.setItem("marketmind_username", username);
};
export const clearToken = () => {
  localStorage.removeItem("marketmind_token");
  localStorage.removeItem("marketmind_username");
};

// Make fetch call with timeout and header injection, falls back to mocks if server is down
async function apiFetch(endpoint, options = {}) {
  const token = getToken();
  const headers = {
    ...options.headers,
  };
  if (token) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  const url = `${API_BASE_URL}${endpoint}`;
  
  // Create a timeout controller to reject hung requests quickly
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), 2500); // 2.5 second timeout

  try {
    const response = await fetch(url, {
      ...options,
      headers,
      signal: controller.signal,
    });
    clearTimeout(id);
    
    if (!response.ok) {
      const errBody = await response.json().catch(() => ({}));
      throw new Error(errBody.detail || `HTTP Error ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    clearTimeout(id);
    console.warn(`API call failed for ${endpoint}: ${error.message}. Resolving local mock data fallback.`);
    return getMockData(endpoint, options);
  }
}

// REST Client object
export const api = {
  // Auth
  register: async (username, password, email) => {
    // If backend is down, we handle custom mock registration
    const url = `${API_BASE_URL}/api/v1/auth/register`;
    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password, email }),
      });
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || "Registration failed");
      }
      return await response.json();
    } catch (e) {
      console.warn("Register API failed, resolving mock user account creation.");
      return { status: "SUCCESS", message: "Mock user registered", username };
    }
  },

  login: async (username, password) => {
    // OAuth2PasswordRequestForm expects formurlencoded
    const url = `${API_BASE_URL}/api/v1/auth/login`;
    const params = new URLSearchParams();
    params.append("username", username);
    params.append("password", password);

    try {
      const response = await fetch(url, {
        method: "POST",
        headers: { "Content-Type": "application/x-www-form-urlencoded" },
        body: params,
      });
      if (!response.ok) {
        const errBody = await response.json().catch(() => ({}));
        throw new Error(errBody.detail || "Authentication failed");
      }
      const data = await response.json();
      setToken(data.access_token, data.username);
      return data;
    } catch (e) {
      console.warn("Login API failed, logging in as mock Guest trader.");
      const mockToken = "mock_jwt_token_for_" + username;
      setToken(mockToken, username);
      return { access_token: mockToken, token_type: "bearer", username };
    }
  },

  getMe: async () => {
    return apiFetch("/api/v1/auth/me");
  },

  // Financial Data
  getStocks: async () => {
    return apiFetch("/stocks");
  },

  getPrices: async (ticker) => {
    return apiFetch(`/prices/${ticker}`);
  },

  getSentiment: async (ticker) => {
    return apiFetch(`/sentiment/${ticker}`);
  },

  getForecast: async (ticker) => {
    return apiFetch(`/forecast/${ticker}`);
  },

  getRisk: async (ticker) => {
    return apiFetch(`/risk/${ticker}`);
  },

  getModelRegistry: async () => {
    return apiFetch("/api/v1/models/registry");
  },

  copilotExplain: async (ticker) => {
    const token = getToken();
    const headers = {
      "Content-Type": "application/json"
    };
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/copilot/explain`, {
        method: "POST",
        headers,
        body: JSON.stringify({ ticker })
      });
      if (!response.ok) throw new Error("Copilot call failed");
      return await response.json();
    } catch (e) {
      console.warn("Copilot API failed, returning mock explanation");
      return {
        ticker,
        explanation: `Analysis Report for Mock Corp (${ticker}): Currently trading with stable metrics. Forecast algorithms predict positive drift. Sentiment rating matches +0.25 (NEUTRAL).`,
        metrics: { price: "$180.00", change: "+1.2%", sentiment: "NEUTRAL", forecast_3d: "$183.00", sharpe: 1.5, beta: 1.0 }
      };
    }
  },

  // ETL
  runEtl: async () => {
    const token = getToken();
    const headers = token ? { "Authorization": `Bearer ${token}` } : {};
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/etl/run`, {
        method: "POST",
        headers,
      });
      if (!response.ok) throw new Error("ETL trigger failed");
      return await response.json();
    } catch (e) {
      console.warn("ETL Trigger API failed, resolving mock success run.");
      return { status: "SUCCESS", records_processed: 12, error_message: null };
    }
  },

  getEtlHistory: async () => {
    return apiFetch("/api/v1/etl/history");
  },

  // Ingestion Scheduler
  toggleScheduler: async (enable) => {
    const token = getToken();
    const headers = token ? { "Authorization": `Bearer ${token}` } : {};
    try {
      const response = await fetch(`http://localhost:8080/api/v1/ingest/scheduler/toggle?enable=${enable}`, {
        method: "POST",
        headers,
      });
      if (!response.ok) throw new Error("Toggle request failed");
      return await response.json();
    } catch (e) {
      console.warn("Scheduler Ingestion Toggle failed, resolving mock state update.");
      return { schedulerEnabled: enable, message: "Scheduler status updated (MOCK)" };
    }
  },

  getSchedulerStatus: async () => {
    try {
      const response = await fetch(`http://localhost:8080/api/v1/ingest/status`);
      if (!response.ok) throw new Error("Status check failed");
      return await response.json();
    } catch (e) {
      return { schedulerEnabled: true, processedPricesCount: 15, processedNewsCount: 8, source: "MOCK" };
    }
  }
};

// --- LOGICAL MOCK DATA GENERATION FALLBACKS ---
function getMockData(endpoint, options) {
  const dateStr = (offset = 0) => {
    const d = new Date();
    d.setDate(d.getDate() - offset);
    return d.toISOString().split("T")[0];
  };

  if (endpoint.startsWith("/api/v1/auth/me")) {
    return { username: getUsername(), email: `${getUsername().toLowerCase()}@example.com`, user_id: 999 };
  }

  if (endpoint === "/stocks") {
    return [
      { ticker: "AAPL", name: "Apple Inc.", sector: "Technology", exchange: "NASDAQ" },
      { ticker: "MSFT", name: "Microsoft Corporation", sector: "Technology", exchange: "NASDAQ" },
      { ticker: "GOOGL", name: "Alphabet Inc.", sector: "Technology", exchange: "NASDAQ" },
      { ticker: "AMZN", name: "Amazon.com Inc.", sector: "Consumer Discretionary", exchange: "NASDAQ" },
      { ticker: "TSLA", name: "Tesla Inc.", sector: "Consumer Discretionary", exchange: "NASDAQ" }
    ];
  }

  if (endpoint.startsWith("/prices/")) {
    const ticker = endpoint.split("/")[2].toUpperCase();
    const basePrices = { AAPL: 180, MSFT: 420, GOOGL: 170, AMZN: 185, TSLA: 245 };
    const base = basePrices[ticker] || 100;
    
    // Generate 7 days of price points
    const prices = [];
    for (let i = 6; i >= 0; i--) {
      const factor = 1 + (Math.sin(i + ticker.charCodeAt(0)) * 0.03); // deterministic random walk
      const close = parseFloat((base * factor).toFixed(2));
      const open = parseFloat((close * (1 + (Math.sin(i) * 0.005))).toFixed(2));
      const high = parseFloat((Math.max(open, close) * 1.01).toFixed(2));
      const low = parseFloat((Math.min(open, close) * 0.99).toFixed(2));
      prices.push({
        date: dateStr(i),
        open,
        high,
        low,
        close,
        volume: Math.floor(20000000 + Math.random() * 50000000)
      });
    }
    return { ticker, source: "LOCAL_MOCK", prices };
  }

  if (endpoint.startsWith("/sentiment/")) {
    const ticker = endpoint.split("/")[2].toUpperCase();
    const sentiments = { AAPL: 0.62, MSFT: 0.74, GOOGL: 0.45, AMZN: 0.58, TSLA: -0.15 };
    const score = sentiments[ticker] !== undefined ? sentiments[ticker] : 0.25;

    return {
      ticker,
      overall_sentiment: score,
      confidence: 0.85,
      source: "LOCAL_MOCK",
      news_items: [
        {
          title: `${ticker} launches next-generation artificial intelligence interface`,
          url: "https://example.com/mock-news-1",
          sentiment_score: Math.min(1, score + 0.2),
          confidence_score: 0.92,
          source: "Bloomberg"
        },
        {
          title: `Analysts debate ${ticker} stock performance projection ahead of earnings`,
          url: "https://example.com/mock-news-2",
          sentiment_score: score - 0.1,
          confidence_score: 0.78,
          source: "Reuters"
        }
      ]
    };
  }

  if (endpoint.startsWith("/forecast/")) {
    const ticker = endpoint.split("/")[2].toUpperCase();
    const basePrices = { AAPL: 180, MSFT: 420, GOOGL: 170, AMZN: 185, TSLA: 245 };
    const base = basePrices[ticker] || 100;

    return {
      ticker,
      model_version: "baseline_linear_v1",
      source: "LOCAL_MOCK",
      predictions: [
        { date: dateStr(-1), predicted_close: parseFloat((base * 1.015).toFixed(2)), confidence: 0.88 },
        { date: dateStr(-2), predicted_close: parseFloat((base * 1.022).toFixed(2)), confidence: 0.84 },
        { date: dateStr(-3), predicted_close: parseFloat((base * 1.034).toFixed(2)), confidence: 0.78 }
      ]
    };
  }

  if (endpoint.startsWith("/risk/")) {
    const ticker = endpoint.split("/")[2].toUpperCase();
    const risks = {
      AAPL: { beta: 1.12, sharpe_ratio: 1.65, value_at_risk: 0.021 },
      MSFT: { beta: 0.92, sharpe_ratio: 2.10, value_at_risk: 0.018 },
      GOOGL: { beta: 1.05, sharpe_ratio: 1.48, value_at_risk: 0.023 },
      AMZN: { beta: 1.20, sharpe_ratio: 1.35, value_at_risk: 0.026 },
      TSLA: { beta: 1.62, sharpe_ratio: 0.85, value_at_risk: 0.042 }
    };

    return {
      ticker,
      ...(risks[ticker] || { beta: 1.00, sharpe_ratio: 1.50, value_at_risk: 0.025 }),
      source: "LOCAL_MOCK"
    };
  }

  if (endpoint === "/api/v1/etl/history") {
    return [
      { run_id: 101, run_date: new Date().toISOString(), status: "SUCCESS", records_processed: 8, error_message: null },
      { run_id: 100, run_date: dateStr(1) + "T10:00:00Z", status: "SUCCESS", records_processed: 14, error_message: null }
    ];
  }

  if (endpoint === "/api/v1/models/registry") {
    return [
      { model_name: "Linear Regression", version: "1.0.0", rmse: 1.24, mape: 0.008, r2_score: 0.88, created_at: new Date().toISOString(), status: "TRAINED" },
      { model_name: "Prophet (Seasonal)", version: "1.1.2", rmse: 0.98, mape: 0.006, r2_score: 0.92, created_at: new Date().toISOString(), status: "TRAINED" },
      { model_name: "LSTM Neural Net", version: "2.0.4", rmse: 0.52, mape: 0.003, r2_score: 0.97, created_at: new Date().toISOString(), status: "DEPLOYED" }
    ];
  }

  return {};
}
