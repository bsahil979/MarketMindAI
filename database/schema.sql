-- Schema design for MarketMind AI Star Schema

-- Dimension: Sectors
CREATE TABLE IF NOT EXISTS dim_sector (
    sector_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Dimension: Exchanges
CREATE TABLE IF NOT EXISTS dim_exchange (
    exchange_id SERIAL PRIMARY KEY,
    code VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL
);

-- Dimension: Companies / Stocks
CREATE TABLE IF NOT EXISTS dim_company (
    company_id SERIAL PRIMARY KEY,
    ticker VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(100) NOT NULL,
    sector_id INT REFERENCES dim_sector(sector_id) ON DELETE SET NULL,
    exchange_id INT REFERENCES dim_exchange(exchange_id) ON DELETE SET NULL
);

-- Dimension: Date (For analytical time-intelligence queries)
CREATE TABLE IF NOT EXISTS dim_date (
    date_id INT PRIMARY KEY, -- Format YYYYMMDD
    date DATE UNIQUE NOT NULL,
    day INT NOT NULL,
    month INT NOT NULL,
    year INT NOT NULL,
    quarter INT NOT NULL,
    day_of_week INT NOT NULL
);

-- Dimension: Sources (For news, sentiment, telemetry)
CREATE TABLE IF NOT EXISTS dim_source (
    source_id SERIAL PRIMARY KEY,
    name VARCHAR(100) UNIQUE NOT NULL
);

-- Fact: Market Prices
CREATE TABLE IF NOT EXISTS fact_market_price (
    price_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES dim_company(company_id) ON DELETE CASCADE,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    open DECIMAL(15, 4) NOT NULL,
    high DECIMAL(15, 4) NOT NULL,
    low DECIMAL(15, 4) NOT NULL,
    close DECIMAL(15, 4) NOT NULL,
    volume BIGINT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: News Sentiment
CREATE TABLE IF NOT EXISTS fact_news_sentiment (
    sentiment_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES dim_company(company_id) ON DELETE CASCADE,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    source_id INT NOT NULL REFERENCES dim_source(source_id),
    title VARCHAR(255) NOT NULL,
    url TEXT,
    sentiment_score DECIMAL(5, 4) NOT NULL, -- -1.0000 to +1.0000
    confidence_score DECIMAL(5, 4) NOT NULL, -- 0.0000 to +1.0000
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: AI Predictions
CREATE TABLE IF NOT EXISTS fact_prediction (
    prediction_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES dim_company(company_id) ON DELETE CASCADE,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    predicted_close DECIMAL(15, 4) NOT NULL,
    confidence DECIMAL(5, 4) NOT NULL, -- 0.0000 to +1.0000
    model_version VARCHAR(50) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: Risk Metrics
CREATE TABLE IF NOT EXISTS fact_risk_metrics (
    risk_id SERIAL PRIMARY KEY,
    company_id INT NOT NULL REFERENCES dim_company(company_id) ON DELETE CASCADE,
    date_id INT NOT NULL REFERENCES dim_date(date_id),
    beta DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),
    value_at_risk DECIMAL(10, 4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Fact: ETL Pipeline Telemetry Runs
CREATE TABLE IF NOT EXISTS fact_pipeline_run (
    run_id SERIAL PRIMARY KEY,
    run_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL, -- SUCCESS, FAILED, RUNNING
    records_processed INT NOT NULL DEFAULT 0,
    error_message TEXT
);
