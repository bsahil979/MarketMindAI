import os
import logging
from sqlalchemy import create_engine, MetaData, Table, Column, Integer, String, Float, DateTime, Date, BigInteger, ForeignKey
from sqlalchemy.orm import declarative_base, sessionmaker

logger = logging.getLogger("marketmind.database")
logging.basicConfig(level=logging.INFO)

DATABASE_URL_POSTGRES = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/marketmind")
DATABASE_URL_SQLITE = "sqlite:///../marketmind.db" # relative to app folder

# Connection trial
engine = None
try:
    logger.info(f"Attempting to connect to PostgreSQL at {DATABASE_URL_POSTGRES}...")
    # set short timeout for postgres connection test so it doesn't hang long
    test_engine = create_engine(DATABASE_URL_POSTGRES, connect_args={"connect_timeout": 3})
    conn = test_engine.connect()
    conn.close()
    engine = test_engine
    logger.info("Successfully connected to PostgreSQL database!")
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite database at {DATABASE_URL_SQLITE}...")
    engine = create_engine(DATABASE_URL_SQLITE, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL_SQLITE else {})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

# SQLAlchemy ORM Models
class DimSector(Base):
    __tablename__ = "dim_sector"
    sector_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class DimExchange(Base):
    __tablename__ = "dim_exchange"
    exchange_id = Column(Integer, primary_key=True, index=True)
    code = Column(String(10), unique=True, nullable=False)
    name = Column(String(100), nullable=False)

class DimCompany(Base):
    __tablename__ = "dim_company"
    company_id = Column(Integer, primary_key=True, index=True)
    ticker = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(100), nullable=False)
    sector_id = Column(Integer, ForeignKey("dim_sector.sector_id", ondelete="SET NULL"))
    exchange_id = Column(Integer, ForeignKey("dim_exchange.exchange_id", ondelete="SET NULL"))

class DimDate(Base):
    __tablename__ = "dim_date"
    date_id = Column(Integer, primary_key=True) # YYYYMMDD
    date = Column(Date, unique=True, nullable=False)
    day = Column(Integer, nullable=False)
    month = Column(Integer, nullable=False)
    year = Column(Integer, nullable=False)
    quarter = Column(Integer, nullable=False)
    day_of_week = Column(Integer, nullable=False)

class DimSource(Base):
    __tablename__ = "dim_source"
    source_id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)

class FactMarketPrice(Base):
    __tablename__ = "fact_market_price"
    price_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dim_company.company_id", ondelete="CASCADE"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_date.date_id"), nullable=False)
    open = Column(Float, nullable=False)
    high = Column(Float, nullable=False)
    low = Column(Float, nullable=False)
    close = Column(Float, nullable=False)
    volume = Column(BigInteger, nullable=False)
    created_at = Column(DateTime, server_default=None)

class FactNewsSentiment(Base):
    __tablename__ = "fact_news_sentiment"
    sentiment_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dim_company.company_id", ondelete="CASCADE"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_date.date_id"), nullable=False)
    source_id = Column(Integer, ForeignKey("dim_source.source_id"), nullable=False)
    title = Column(String(255), nullable=False)
    url = Column(String, nullable=True)
    sentiment_score = Column(Float, nullable=False)
    confidence_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=None)

class FactPrediction(Base):
    __tablename__ = "fact_prediction"
    prediction_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dim_company.company_id", ondelete="CASCADE"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_date.date_id"), nullable=False)
    predicted_close = Column(Float, nullable=False)
    confidence = Column(Float, nullable=False)
    model_version = Column(String(50), nullable=False)
    created_at = Column(DateTime, server_default=None)

class FactRiskMetrics(Base):
    __tablename__ = "fact_risk_metrics"
    risk_id = Column(Integer, primary_key=True, index=True)
    company_id = Column(Integer, ForeignKey("dim_company.company_id", ondelete="CASCADE"), nullable=False)
    date_id = Column(Integer, ForeignKey("dim_date.date_id"), nullable=False)
    beta = Column(Float, nullable=True)
    sharpe_ratio = Column(Float, nullable=True)
    value_at_risk = Column(Float, nullable=True)
    created_at = Column(DateTime, server_default=None)

class FactPipelineRun(Base):
    __tablename__ = "fact_pipeline_run"
    run_id = Column(Integer, primary_key=True, index=True)
    run_date = Column(DateTime, server_default=None)
    status = Column(String(20), nullable=False)
    records_processed = Column(Integer, nullable=False, default=0)
    error_message = Column(String, nullable=True)

class User(Base):
    __tablename__ = "users"
    user_id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    email = Column(String(100), nullable=True)

class ModelRegistry(Base):
    __tablename__ = "model_registry"
    model_id = Column(Integer, primary_key=True, index=True)
    model_name = Column(String(50), nullable=False)
    version = Column(String(20), nullable=False)
    rmse = Column(Float, nullable=False)
    mape = Column(Float, nullable=False)
    r2_score = Column(Float, nullable=False)
    created_at = Column(DateTime, server_default=None)
    status = Column(String(20), nullable=False)

def init_db():
    logger.info("Initializing database schemas...")
    Base.metadata.create_all(bind=engine)
    logger.info("Database schemas initialized successfully!")

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
