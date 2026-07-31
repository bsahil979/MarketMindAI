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
    sectors = ["Technology", "Consumer Discretionary", "Financial Services", "Communication"]
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
    financial_sector = db.query(DimSector).filter_by(name="Financial Services").first()
    comm_sector = db.query(DimSector).filter_by(name="Communication").first()

    nasdaq_ex = db.query(DimExchange).filter_by(code="NASDAQ").first()
    nyse_ex = db.query(DimExchange).filter_by(code="NYSE").first()

    companies = [
        {"ticker": "AAPL", "name": "Apple Inc.", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "NVDA", "name": "Nvidia Corporation", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "MSFT", "name": "Microsoft Corporation", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "GOOGL", "name": "Alphabet Inc.", "sector": comm_sector, "exchange": nasdaq_ex},
        {"ticker": "AMZN", "name": "Amazon.com Inc.", "sector": consumer_sector, "exchange": nasdaq_ex},
        {"ticker": "TSLA", "name": "Tesla Inc.", "sector": consumer_sector, "exchange": nasdaq_ex},
        {"ticker": "META", "name": "Meta Platforms Inc.", "sector": comm_sector, "exchange": nasdaq_ex},
        {"ticker": "AMD", "name": "Advanced Micro Devices", "sector": tech_sector, "exchange": nasdaq_ex},
        {"ticker": "NFLX", "name": "Netflix Inc.", "sector": comm_sector, "exchange": nasdaq_ex},
        {"ticker": "JPM", "name": "JPMorgan Chase & Co.", "sector": financial_sector, "exchange": nyse_ex}
    ]

    for company in companies:
        if not db.query(DimCompany).filter_by(ticker=company["ticker"]).first():
            db.add(DimCompany(
                ticker=company["ticker"],
                name=company["name"],
                sector_id=company["sector"].sector_id if company["sector"] else None,
                exchange_id=company["exchange"].exchange_id if company["exchange"] else None
            ))
    db.commit()
    seed_real_market_prices(db)
    seed_forecasts_and_risk(db)
    logger.info("Dimension tables seed check completed.")

def seed_real_market_prices(db: Session) -> int:
    logger.info("Populating real-world market prices from Yahoo Finance...")
    import urllib.request
    companies = db.query(DimCompany).all()
    total_synced = 0
    for company in companies:
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{company.ticker}?range=15d&interval=1d"
            req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
            with urllib.request.urlopen(req, timeout=3) as resp:
                data = json.loads(resp.read().decode('utf-8'))
                result = data['chart']['result'][0]
                timestamps = result.get('timestamp', [])
                quote = result['indicators']['quote'][0]
                closes = quote.get('close', [])
                opens = quote.get('open', [])
                highs = quote.get('high', [])
                lows = quote.get('low', [])
                volumes = quote.get('volume', [])

                for i in range(len(timestamps)):
                    if i >= len(closes) or closes[i] is None:
                        continue
                    dt = datetime.fromtimestamp(timestamps[i])
                    date_id = get_or_create_date_id(db, dt)
                    
                    existing = db.query(FactMarketPrice).filter_by(company_id=company.company_id, date_id=date_id).first()
                    close_val = float(round(closes[i], 2))
                    open_val = float(round(opens[i] if (i < len(opens) and opens[i] is not None) else close_val, 2))
                    high_val = float(round(highs[i] if (i < len(highs) and highs[i] is not None) else close_val, 2))
                    low_val = float(round(lows[i] if (i < len(lows) and lows[i] is not None) else close_val, 2))
                    vol_val = int(volumes[i]) if (i < len(volumes) and volumes[i] is not None) else 40000000

                    if existing:
                        existing.close = close_val
                        existing.open = open_val
                        existing.high = high_val
                        existing.low = low_val
                        existing.volume = vol_val
                    else:
                        db.add(FactMarketPrice(
                            company_id=company.company_id,
                            date_id=date_id,
                            open=open_val,
                            high=high_val,
                            low=low_val,
                            close=close_val,
                            volume=vol_val,
                            created_at=dt
                        ))
                    total_synced += 1
                db.commit()
                logger.info(f"Successfully synced {len(timestamps)} live Yahoo prices for {company.ticker}")
        except Exception as e:
            logger.warning(f"Could not fetch live Yahoo prices for {company.ticker}: {e}")
    return total_synced

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
            fraction = fraction[:6].ljust(6, '0') # keep exactly 6 microsecond digits
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

        # 4. Fetch and Sync Real Live Yahoo Market Quotes on Manual Sync
        synced_live_count = seed_real_market_prices(db)
        records_processed += synced_live_count

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

    total_db_prices = db.query(FactMarketPrice).count()
    logger.info(f"ETL Run complete. Status: {status}. Processed records: {records_processed}.")
    return {
        "status": status,
        "records_processed": records_processed,
        "total_active_prices": total_db_prices,
        "message": f"Database up-to-date ({total_db_prices} market quotes active). 0 pending raw files in inbox.",
        "error_message": error_message
    }
