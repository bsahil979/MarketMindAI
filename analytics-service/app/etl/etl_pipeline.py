import os
import json
import shutil
import logging
from datetime import datetime
from pathlib import Path
from sqlalchemy.orm import Session
from app.database import (
    init_db, SessionLocal,
    DimSector, DimExchange, DimCompany, DimDate, DimSource,
    FactMarketPrice, FactNewsSentiment, FactPipelineRun,
    FactPrediction, FactRiskMetrics
)

logger = logging.getLogger("marketmind.etl")
logging.basicConfig(level=logging.INFO)

RAW_STORAGE_PATH = Path("../raw_storage").resolve()
PROCESSED_STORAGE_PATH = Path("../raw_storage/processed").resolve()

def seed_dimensions(db: Session):
    logger.info("Checking and seeding dimension tables...")

    # 1. Seed Sectors
    sectors = ["Technology", "Consumer Discretionary"]
    for name in sectors:
        if not db.query(DimSector).filter_by(name=name).first():
            db.add(DimSector(name=name))
    db.commit()

    # 2. Seed Exchanges
    exchanges = [
        {"code": "NASDAQ", "name": "NASDAQ Stock Market"},
        {"code": "NYSE", "name": "New York Stock Exchange"}
    ]
    for ex in exchanges:
        if not db.query(DimExchange).filter_by(code=ex["code"]).first():
            db.add(DimExchange(code=ex["code"], name=ex["name"]))
    db.commit()

    # 3. Seed Companies
    tech_sector = db.query(DimSector).filter_by(name="Technology").first()
    consumer_sector = db.query(DimSector).filter_by(name="Consumer Discretionary").first()
    nasdaq_ex = db.query(DimExchange).filter_by(code="NASDAQ").first()

    companies = [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": consumer_sector, "exchange": nasdaq_ex},
        {"ticker": "TSLA", "name": "Tesla Inc.", "sector": consumer_sector, "exchange": nasdaq_ex}
    ]

    for company in companies:
        if not db.query(DimCompany).filter_by(ticker=company["ticker"]).first():
            db.add(DimCompany(
                ticker=company["ticker"],
                name=company["name"],
                sector_id=company["sector"].sector_id if company["sector"] else None,
                exchange_id=company["exchange"].exchange_id if company["exchange"] else None
            ))
    seed_forecasts_and_risk(db)
    db.commit()
    logger.info("Dimension tables seed check completed.")

def seed_forecasts_and_risk(db: Session):
    logger.info("Initializing dynamic AI model training and risk calculation on database startup...")
    from app.ai.ai_engine import update_ai_metrics
    update_ai_metrics(db)

def get_or_create_date_id(db: Session, dt: datetime) -> int:
    date_id = int(dt.strftime("%Y%m%d"))
    existing_date = db.query(DimDate).filter_by(date_id=date_id).first()
    if not existing_date:
        # quarter is (month - 1) // 3 + 1
        quarter = (dt.month - 1) // 3 + 1
        new_date = DimDate(
            date_id=date_id,
            date=dt.date(),
            day=dt.day,
            month=dt.month,
            year=dt.year,
            quarter=quarter,
            day_of_week=dt.isoweekday() # 1 = Monday, 7 = Sunday
        )
        db.add(new_date)
        db.commit()
    return date_id

def get_or_create_source_id(db: Session, source_name: str) -> int:
    existing_source = db.query(DimSource).filter_by(name=source_name).first()
    if not existing_source:
        new_source = DimSource(name=source_name)
        db.add(new_source)
        db.commit()
        return new_source.source_id
    return existing_source.source_id

def parse_iso_timestamp(timestamp_val) -> datetime:
    # Jackson serialized localdatetime could be array or ISO string
    if isinstance(timestamp_val, list):
        # format [YYYY, MM, DD, HH, MM, SS, NS]
        # pad array if needed
        parts = timestamp_val + [0] * (7 - len(timestamp_val))
        # convert nano to micro
        parts[6] = parts[6] // 1000
        return datetime(parts[0], parts[1], parts[2], parts[3], parts[4], parts[5], parts[6])
    elif isinstance(timestamp_val, str):
        # Try to parse standard ISO-8601 e.g. 2026-07-17T18:14:05.5462625
        # python's datetime.fromisoformat can handle standard formats, but we strip trailing nanoseconds if they exceed 6 decimal digits
        iso_str = timestamp_val
        if "." in iso_str:
            base, fraction = iso_str.split(".", 1)
            fraction = fraction[:6] # keep max 6 microsecond digits
            iso_str = f"{base}.{fraction}"
        return datetime.fromisoformat(iso_str)
    else:
        return datetime.now()

def run_etl() -> dict:
    logger.info("Initializing ETL Pipeline Run...")
    
    # 1. Initialize DB and seed static dimensions
    init_db()
    db = SessionLocal()
    seed_dimensions(db)

    # Prepare archive paths
    os.makedirs(PROCESSED_STORAGE_PATH / "prices", exist_ok=True)
    os.makedirs(PROCESSED_STORAGE_PATH / "news", exist_ok=True)

    records_processed = 0
    error_message = None
    status = "SUCCESS"

    prices_dir = RAW_STORAGE_PATH / "prices"
    news_dir = RAW_STORAGE_PATH / "news"

    try:
        # 2. Process Stock Prices
        if prices_dir.exists():
            for file_path in prices_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)
                    
                    ticker = data.get("ticker")
                    timestamp = parse_iso_timestamp(data.get("timestamp"))
                    
                    company = db.query(DimCompany).filter_by(ticker=ticker).first()
                    if not company:
                        logger.warning(f"Ticker {ticker} from file {file_path.name} not found in dim_company. Skipping.")
                        continue
                        
                    date_id = get_or_create_date_id(db, timestamp)

                    # Insert fact
                    price_fact = FactMarketPrice(
                        company_id=company.company_id,
                        date_id=date_id,
                        open=data.get("open"),
                        high=data.get("high"),
                        low=data.get("low"),
                        close=data.get("close"),
                        volume=data.get("volume"),
                        created_at=timestamp
                    )
                    db.add(price_fact)
                    db.commit()

                    # Move file to processed archive
                    shutil.move(str(file_path), str(PROCESSED_STORAGE_PATH / "prices" / file_path.name))
                    records_processed += 1
                except Exception as e:
                    logger.error(f"Error processing price file {file_path.name}: {e}")
                    error_message = f"Error processing price file {file_path.name}: {str(e)}"
                    status = "FAILED"

        # 3. Process News Sentiment
        if news_dir.exists():
            for file_path in news_dir.glob("*.json"):
                try:
                    with open(file_path, "r") as f:
                        data = json.load(f)

                    ticker = data.get("ticker")
                    timestamp = parse_iso_timestamp(data.get("timestamp"))
                    source_name = data.get("source", "Unknown")

                    company = db.query(DimCompany).filter_by(ticker=ticker).first()
                    if not company:
                        logger.warning(f"Ticker {ticker} from file {file_path.name} not found in dim_company. Skipping.")
                        continue

                    date_id = get_or_create_date_id(db, timestamp)
                    source_id = get_or_create_source_id(db, source_name)

                    # Insert fact
                    news_fact = FactNewsSentiment(
                        company_id=company.company_id,
                        date_id=date_id,
                        source_id=source_id,
                        title=data.get("title"),
                        url=data.get("url"),
                        sentiment_score=data.get("sentimentScore", 0.0),
                        confidence_score=data.get("confidenceScore", 0.0),
                        created_at=timestamp
                    )
                    db.add(news_fact)
                    db.commit()

                    # Move file to processed archive
                    shutil.move(str(file_path), str(PROCESSED_STORAGE_PATH / "news" / file_path.name))
                    records_processed += 1
                except Exception as e:
                    logger.error(f"Error processing news file {file_path.name}: {e}")
                    error_message = f"Error processing news file {file_path.name}: {str(e)}"
                    status = "FAILED"

        # Trigger dynamic AI models updates after loading new price/sentiment data
        from app.ai.ai_engine import update_ai_metrics
        update_ai_metrics(db)

    except Exception as e:
        logger.error(f"ETL pipeline fatal exception: {e}")
        status = "FAILED"
        error_message = f"Fatal ETL failure: {str(e)}"
    finally:
        # Register pipeline run
        run_record = FactPipelineRun(
            run_date=datetime.now(),
            status=status,
            records_processed=records_processed,
            error_message=error_message
        )
        db.add(run_record)
        db.commit()
        db.close()

    logger.info(f"ETL Run complete. Status: {status}. Processed records: {records_processed}.")
    return {
        "status": status,
        "records_processed": records_processed,
        "error_message": error_message
    }
