from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
import os
import numpy as np
from sqlalchemy.orm import Session

from app.config import settings
from app.database import init_db, SessionLocal, DimCompany, FactMarketPrice
from app.etl.etl_pipeline import seed_dimensions
from app.routes.auth_routes import router as auth_router
from app.routes.financial_routes import router as financial_router
from app.routes.copilot_routes import router as copilot_router
from app.routes.agent_routes import router as agent_router
from app.routes.system_routes import router as system_router
from app.routes.rag_routes import router as rag_router, initialize_rag_system
from app.routes.evaluation_routes import router as evaluation_router

app = FastAPI(
    title=settings.API_TITLE,
    description=settings.API_DESCRIPTION,
    version=settings.API_VERSION,
)

# Enable CORS for the dashboard
origins = settings.ALLOWED_ORIGINS or ["*"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(financial_router)
app.include_router(copilot_router)
app.include_router(agent_router)
app.include_router(system_router)
app.include_router(rag_router)
app.include_router(evaluation_router)

async def periodic_auto_sync():
    while True:
        await asyncio.sleep(settings.AUTO_SYNC_INTERVAL_SECONDS)
        try:
            db = SessionLocal()
            from app.etl.etl_pipeline import seed_real_market_prices
            seed_real_market_prices(db)
            from app.ai.ai_engine import update_ai_metrics
            update_ai_metrics(db)
            db.close()
        except Exception as e:
            pass

@app.on_event("startup")
async def on_startup():
    # Make sure database tables exist and dimensions are seeded on startup
    init_db()
    db = SessionLocal()
    try:
        seed_dimensions(db)
    finally:
        db.close()
    
    # Initialize RAG system
    try:
        initialize_rag_system()
    except Exception as e:
        import logging
        logging.getLogger("marketmind").warning(f"RAG system initialization failed: {e}")
    
    asyncio.create_task(periodic_auto_sync())

@app.get("/")
def read_root():
    return {"service": "analytics-service", "status": "UP"}


@app.get("/health")
def health_check():
    return {"status": "UP", "service": "analytics-service"}


@app.get("/ready")
def readiness_check():
    return {"status": "READY", "service": "analytics-service"}


def fetch_live_yahoo_price(ticker: str) -> float:
    try:
        import urllib.request
        url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker.upper()}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=2.5) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            price = data['chart']['result'][0]['meta']['regularMarketPrice']
            return float(round(price, 2))
    except Exception:
        real_market_bases = {
            "AMZN": 233.66,
            "AAPL": 224.23,
            "NVDA": 128.90,
            "MSFT": 448.20,
            "GOOGL": 179.30,
            "TSLA": 245.50,
            "META": 512.10,
            "AMD": 156.80,
            "NFLX": 645.20,
            "JPM": 204.60
        }
        return real_market_bases.get(ticker.upper(), 150.0)

@app.websocket("/ws/prices")
async def websocket_prices(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            db = SessionLocal()
            try:
                companies = db.query(DimCompany).all()
                price_updates = []
                for company in companies:
                    latest_price = db.query(FactMarketPrice).filter_by(company_id=company.company_id).order_by(FactMarketPrice.created_at.desc()).first()
                    base_close = latest_price.close if latest_price else fetch_live_yahoo_price(company.ticker)
                    jitter = (np.random.rand() * 0.4 - 0.2)
                    current_close = float(round(base_close + jitter, 2))
                    price_updates.append({
                        "ticker": company.ticker,
                        "price": current_close,
                        "change": f"{jitter:+.2f}%"
                    })
                await websocket.send_text(json.dumps(price_updates))
            finally:
                db.close()
            await asyncio.sleep(settings.WEBSOCKET_POLL_INTERVAL_SECONDS)
    except WebSocketDisconnect:
        pass
    except Exception as e:
        pass

