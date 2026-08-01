from app.config import Settings
from app.services.external_integrations import normalize_market_quote, normalize_news_item


def test_settings_reads_provider_configuration(monkeypatch):
    monkeypatch.setenv("MARKET_PROVIDER", "yfinance")
    monkeypatch.setenv("NEWS_PROVIDER", "newsapi")
    monkeypatch.setenv("NEWS_API_KEY", "demo-key")

    settings = Settings()

    assert settings.MARKET_PROVIDER == "yfinance"
    assert settings.NEWS_PROVIDER == "newsapi"
    assert settings.NEWS_API_KEY == "demo-key"


def test_normalize_market_quote_handles_api_payload():
    payload = {
        "ticker": "AAPL",
        "price": 191.45,
        "change": 1.12,
        "source": "yfinance"
    }
    normalized = normalize_market_quote(payload)
    assert normalized["ticker"] == "AAPL"
    assert normalized["price"] == 191.45
    assert normalized["change"] == 1.12
    assert normalized["source"] == "yfinance"


def test_normalize_news_item_handles_api_payload():
    payload = {
        "title": "Stocks rise on earnings",
        "url": "https://example.com/news",
        "summary": "Markets advanced after strong earnings.",
        "published_at": "2026-08-01T10:00:00Z",
        "source": "newsapi"
    }
    normalized = normalize_news_item(payload)
    assert normalized["title"] == "Stocks rise on earnings"
    assert normalized["url"] == "https://example.com/news"
    assert normalized["summary"] == "Markets advanced after strong earnings."
    assert normalized["source"] == "newsapi"
