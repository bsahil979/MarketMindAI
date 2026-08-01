from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict, Any

from app.database import (
    get_db, DimCompany, DimSector, DimExchange, FactMarketPrice, FactNewsSentiment,
    FactPrediction, FactRiskMetrics, DimDate, DimSource
)
from app.cache import get_cached, set_cached
from app.services.data_quality import normalize_price_payload, normalize_prediction_payload

router = APIRouter(prefix="", tags=["financial"])


@router.get("/stocks", response_model=List[Dict[str, Any]])
def get_stocks(db: Session = Depends(get_db)):
    cache_key = "stocks_list"
    cached = get_cached(cache_key)
    if cached:
        return cached

    companies = db.query(DimCompany).all()
    result = []
    for c in companies:
        sector = db.query(DimSector).filter_by(sector_id=c.sector_id).first()
        exchange = db.query(DimExchange).filter_by(exchange_id=c.exchange_id).first()
        result.append({
            "ticker": c.ticker,
            "name": c.name,
            "sector": sector.name if sector else "Unknown",
            "exchange": exchange.code if exchange else "Unknown"
        })
    set_cached(cache_key, result, expire_seconds=60)
    return result


@router.get("/prices/{ticker}")
def get_prices(ticker: str, db: Session = Depends(get_db)):
    ticker_upper = ticker.upper()
    cache_key = f"prices_{ticker_upper}"
    cached = get_cached(cache_key)
    if cached:
        return cached
    company = db.query(DimCompany).filter_by(ticker=ticker_upper).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not found")

    prices = db.query(FactMarketPrice).filter_by(company_id=company.company_id).order_by(FactMarketPrice.created_at.asc()).all()

    if not prices:
        raise HTTPException(status_code=404, detail=f"No price history found for {ticker_upper}")

    normalized_prices = normalize_price_payload([
        {
            "date": p.created_at.date().isoformat() if p.created_at else None,
            "open": p.open,
            "high": p.high,
            "low": p.low,
            "close": p.close,
            "volume": p.volume
        }
        for p in prices
    ])
    if not normalized_prices:
        raise HTTPException(status_code=404, detail=f"No valid price history found for {ticker_upper}")

    response_data = {
        "ticker": ticker_upper,
        "source": "DATABASE",
        "prices": normalized_prices
    }
    set_cached(cache_key, response_data, expire_seconds=30)
    return response_data


@router.get("/sentiment/{ticker}")
def get_sentiment(ticker: str, db: Session = Depends(get_db)):
    ticker_upper = ticker.upper()
    company = db.query(DimCompany).filter_by(ticker=ticker_upper).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not found")

    sentiment_items = db.query(FactNewsSentiment).filter_by(company_id=company.company_id).order_by(FactNewsSentiment.created_at.desc()).all()

    if not sentiment_items:
        raise HTTPException(status_code=404, detail=f"No news sentiment data available for {ticker_upper}")

    scores = [item.sentiment_score for item in sentiment_items]
    confidences = [item.confidence_score for item in sentiment_items]
    avg_sentiment = sum(scores) / len(scores) if scores else 0.0
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    news_list = []
    for item in sentiment_items:
        actual_src = db.query(DimSource).filter_by(source_id=item.source_id).first()
        src_name = actual_src.name if actual_src else "Market"

        news_list.append({
            "title": item.title,
            "url": item.url,
            "sentiment_score": item.sentiment_score,
            "confidence_score": item.confidence_score,
            "source": src_name
        })

    return {
        "ticker": ticker_upper,
        "overall_sentiment": round(avg_sentiment, 4),
        "confidence": round(avg_confidence, 4),
        "source": "DATABASE",
        "news_items": news_list
    }


@router.get("/forecast/{ticker}")
def get_forecast(ticker: str, db: Session = Depends(get_db)):
    ticker_upper = ticker.upper()
    company = db.query(DimCompany).filter_by(ticker=ticker_upper).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not found")

    predictions = db.query(FactPrediction).filter_by(company_id=company.company_id).order_by(FactPrediction.created_at.desc()).all()

    if not predictions:
        raise HTTPException(status_code=404, detail=f"No forecast data available for {ticker_upper}")

    preds_list = []
    for p in predictions:
        date_record = db.query(DimDate).filter_by(date_id=p.date_id).first()
        preds_list.append({
            "date": date_record.date.isoformat() if date_record else p.created_at.date().isoformat(),
            "predicted_close": p.predicted_close,
            "confidence": p.confidence
        })

    return {
        "ticker": ticker_upper,
        "model_version": predictions[0].model_version if predictions else "baseline_linear_v1",
        "source": "DATABASE",
        "predictions": preds_list
    }


@router.get("/risk/{ticker}")
def get_risk(ticker: str, db: Session = Depends(get_db)):
    ticker_upper = ticker.upper()
    company = db.query(DimCompany).filter_by(ticker=ticker_upper).first()
    if not company:
        raise HTTPException(status_code=404, detail=f"Ticker {ticker_upper} not found")

    risk = db.query(FactRiskMetrics).filter_by(company_id=company.company_id).order_by(FactRiskMetrics.created_at.desc()).first()

    if not risk:
        raise HTTPException(status_code=404, detail=f"No risk metrics available for {ticker_upper}")

    return {
        "ticker": ticker_upper,
        "beta": risk.beta,
        "sharpe_ratio": risk.sharpe_ratio,
        "value_at_risk": risk.value_at_risk,
        "source": "DATABASE"
    }
