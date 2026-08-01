import json
import os
import urllib.parse
import urllib.request
from typing import Any, Dict, List

from app.config import settings


class ExternalDataError(RuntimeError):
    pass


def normalize_market_quote(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ExternalDataError("Market provider returned an invalid payload")
    return {
        "ticker": str(payload.get("ticker", "")).upper(),
        "price": float(payload.get("price", 0.0)),
        "change": float(payload.get("change", 0.0)),
        "source": payload.get("source") or "external",
    }


def normalize_news_item(payload: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(payload, dict):
        raise ExternalDataError("News provider returned an invalid payload")
    return {
        "title": payload.get("title") or "Untitled article",
        "url": payload.get("url") or "",
        "summary": payload.get("summary") or "",
        "published_at": payload.get("published_at") or None,
        "source": payload.get("source") or "external",
    }


def fetch_market_quote(ticker: str) -> Dict[str, Any]:
    provider = settings.MARKET_PROVIDER or os.getenv("MARKET_PROVIDER", "yfinance")
    ticker_upper = ticker.upper()

    if provider == "yfinance":
        try:
            url = f"https://query1.finance.yahoo.com/v8/finance/chart/{ticker_upper}"
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=4) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                meta = body.get("chart", {}).get("result", [{}])[0].get("meta", {})
                price = meta.get("regularMarketPrice")
                change = meta.get("chartPreviousClose")
                if price is None:
                    raise ExternalDataError("No price returned by Yahoo Finance")
                return normalize_market_quote({
                    "ticker": ticker_upper,
                    "price": float(price),
                    "change": float(change or 0.0),
                    "source": provider,
                })
        except Exception as exc:
            raise ExternalDataError(f"Market provider failed: {exc}") from exc

    raise ExternalDataError(f"Unsupported market provider: {provider}")


def fetch_news_items(query: str, limit: int = 5) -> List[Dict[str, Any]]:
    provider = settings.NEWS_PROVIDER or os.getenv("NEWS_PROVIDER", "newsapi")
    api_key = settings.NEWS_API_KEY or os.getenv("NEWS_API_KEY")

    if provider == "newsapi":
        if not api_key:
            raise ExternalDataError("NEWS_API_KEY is not configured")
        try:
            url = (
                "https://newsapi.org/v2/everything?"
                f"q={urllib.parse.quote(query)}&language=en&pageSize={limit}&apiKey={api_key}"
            )
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=6) as resp:
                body = json.loads(resp.read().decode("utf-8"))
                articles = body.get("articles", [])
                return [normalize_news_item(article) for article in articles[:limit]]
        except Exception as exc:
            raise ExternalDataError(f"News provider failed: {exc}") from exc

    raise ExternalDataError(f"Unsupported news provider: {provider}")
