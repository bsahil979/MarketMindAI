
# MarketMind AI - Architecture & Design Specifications

This specification details the engineering systems design, ER schemas, and data pipelines structure of the MarketMind AI platform.

---

## 1. System Components Architecture

The architecture relies on loosely coupled services communicating via REST APIs, WebSockets, and a Kafka message broker.

```mermaid
graph TD
    subgraph Client Layer
        A[React Vite Dashboard]
    end

    subgraph Streaming Queue
        B[Yahoo Finance chart REST] -->|Ingest Job| C[Spring Scheduler]
        C -->|Publish| D[Kafka Broker: marketmind-prices]
        C -->|Publish| E[Kafka Broker: marketmind-news]
        D -->|Event Listeners| F[Spring Consumer]
        E -->|Event Listeners| F
        F -->|JSON Writer| G[(raw_storage/)]
    end

    subgraph Batch ETL & ML Engine
        G -->|Extract / Validate / Clean| H[Python ETL Sync]
        H -->|Load Facts schema| I[(RDS PostgreSQL / SQLite)]
        I -->|Linear, Prophet, LSTM| J[AI Model Registries]
        J -->|Write accuracy log| I
    end

    subgraph Service Layer
        A -->|REST Queries / Auth| K[FastAPI Analytics Engine]
        A -->|Live WebSockets| K
        K -->|Read cache| L[(Redis Cache)]
        K -->|Fallback Query| I
    end
```

---

## 2. Database Entity-Relationship (ER) Schema

The database model follows a high-performance Dimensional Star Schema optimized for financial time-series querying:

```mermaid
erDiagram
    dim_company ||--o{ fact_market_price : "has historic close"
    dim_company ||--o{ fact_news_sentiment : "has article sentiment"
    dim_company ||--o{ fact_prediction : "has model forecast"
    dim_company ||--o{ fact_risk_metrics : "has volatility metric"
    
    dim_date ||--o{ fact_market_price : "occurs on"
    dim_date ||--o{ fact_news_sentiment : "occurs on"
    dim_date ||--o{ fact_prediction : "occurs on"
    dim_date ||--o{ fact_risk_metrics : "occurs on"

    dim_company {
        int company_id PK
        varchar ticker UK
        varchar name
        int sector_id FK
        int exchange_id Fk 
    }

    dim_date {
        int date_id PK
        date date
        int day
        int month
        int year
        int quarter
        int day_of_week
    }

    fact_market_price {
        int price_id PK
        int company_id FK
        int date_id FK
        float open
        float high
        float low
        float close
        bigint volume
        timestamp created_at
    }

    fact_news_sentiment {
        int news_id PK
        int company_id FK
        int date_id FK
        varchar title
        varchar url
        float sentiment_score
        float confidence_score
        timestamp created_at
    }

    fact_prediction {
        int prediction_id PK
        int company_id FK
        int date_id FK
        float predicted_close
        float confidence
        varchar model_version
        timestamp created_at
    }

    fact_risk_metrics {
        int risk_id PK
        int company_id FK
        int date_id FK
        float beta
        float sharpe_ratio
        float value_at_risk
        timestamp created_at
    }

    model_registry {
        int model_id PK
        varchar model_name
        varchar version
        float rmse
        float mape
        float r2_score
        varchar status
        timestamp created_at
    }
```

---

## 3. Data Streaming & Batch ETL Sequences

### Real-time Event Ingestion Flow
```mermaid
sequenceDiagram
    participant YahooFinance as Yahoo Finance API
    participant Scheduler as Spring Ingestion Scheduler
    participant Kafka as Kafka Topic (marketmind-prices)
    participant Consumer as Spring Consumer Listener
    participant RawStorage as raw_storage/prices/

    loop Every 30 Seconds
        Scheduler->>YahooFinance: GET /chart/AAPL
        YahooFinance-->>Scheduler: Return JSON Close Data
        Scheduler->>Kafka: Publish AAPL Price Update
        Kafka-->>Consumer: Trigger onMessage Event
        Consumer->>RawStorage: Save AAPL_TIMESTAMP.json
    end
```

### Batch ETL & MLOps Training Pipeline (Airflow DAG)
```mermaid
sequenceDiagram
    participant Trigger as Airflow Scheduler
    participant Extract as task_extract
    participant Validate as task_validate
    participant Clean as task_clean
    participant Load as task_load
    participant Train as task_train (scikit-learn)
    participant Registry as Model Registry Table

    Trigger->>Extract: Run Extract Job
    Extract-->>Validate: Completed (Files list parsed)
    Validate-->>Clean: Completed (Metadata validated)
    Clean-->>Load: Completed (Duplicates dropped)
    Load-->>Train: Completed (Loaded to Postgres)
    Train->>Registry: Log RMSE, MAPE, R2 for LR, Prophet, LSTM
    Registry-->>Train: Registered Successfully
```

### Live WebSocket Broadcast Flow
```mermaid
sequenceDiagram
    participant Client as React Dashboard (App.jsx)
    participant Server as FastAPI WebSocket (/ws/prices)
    participant Cache as Redis Cache
    participant DB as SQLite / PostgreSQL

    Client->>Server: Establish Connection (WS)
    Server-->>Client: Connection Accepted
    loop Every 3 Seconds
        Server->>Cache: GET stocks_live_prices
        alt Cache HIT
            Cache-->>Server: Return cached prices
        else Cache MISS
            Server->>DB: Query latest FactMarketPrice
            DB-->>Server: Return prices list
            Server->>Cache: SET stocks_live_prices (TTL: 3s)
        end
        Server->>Client: Send JSON message (Ticker price ticks)
    end
```
