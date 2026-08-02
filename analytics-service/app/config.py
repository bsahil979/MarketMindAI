import os
from pathlib import Path
from typing import List

BASE_DIR = Path(__file__).resolve().parent.parent


def _get_env_list(name: str, default: str = "*") -> List[str]:
    value = os.getenv(name, default)
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


class Settings:
    def __init__(self) -> None:
        self.API_TITLE: str = os.getenv("API_TITLE", "MarketMind AI Analytics Service")
        self.API_DESCRIPTION: str = os.getenv(
            "API_DESCRIPTION",
            "FastAPI service for market data analysis, forecasts, news sentiment, and risk metrics.",
        )
        self.API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
        self.DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/marketmind")
        self.SQLITE_PATH: str = os.getenv("SQLITE_PATH", str(BASE_DIR / "marketmind.db"))
        
        # Explicitly allow common origins for development and production
        default_origins = [
            "http://localhost:5173",
            "http://localhost:3000",
            "http://127.0.0.1:5173",
            "http://127.0.0.1:3000",
            "https://market-mind-ai-q1kl.vercel.app",
            "https://marketmindai.vercel.app",
            "*"
        ]
        self.ALLOWED_ORIGINS: List[str] = _get_env_list("ALLOWED_ORIGINS", ",".join(default_origins))
        
        self.AUTO_SYNC_INTERVAL_SECONDS: int = int(os.getenv("AUTO_SYNC_INTERVAL_SECONDS", "300"))
        self.WEBSOCKET_POLL_INTERVAL_SECONDS: int = int(os.getenv("WEBSOCKET_POLL_INTERVAL_SECONDS", "3"))
        self.API_HOST: str = os.getenv("HOST", "0.0.0.0")
        self.API_PORT: int = int(os.getenv("PORT", "8000"))
        self.LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
        self.MARKET_PROVIDER: str = os.getenv("MARKET_PROVIDER", "yfinance")
        self.NEWS_PROVIDER: str = os.getenv("NEWS_PROVIDER", "newsapi")
        self.NEWS_API_KEY: str = os.getenv("NEWS_API_KEY", "")


settings = Settings()
