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
    API_TITLE: str = os.getenv("API_TITLE", "MarketMind AI Analytics Service")
    API_DESCRIPTION: str = os.getenv(
        "API_DESCRIPTION",
        "FastAPI service for market data analysis, forecasts, news sentiment, and risk metrics.",
    )
    API_VERSION: str = os.getenv("API_VERSION", "1.0.0")
    DATABASE_URL: str = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/marketmind")
    SQLITE_PATH: str = os.getenv("SQLITE_PATH", str(BASE_DIR / "marketmind.db"))
    ALLOWED_ORIGINS: List[str] = _get_env_list("ALLOWED_ORIGINS", "*")
    AUTO_SYNC_INTERVAL_SECONDS: int = int(os.getenv("AUTO_SYNC_INTERVAL_SECONDS", "300"))
    WEBSOCKET_POLL_INTERVAL_SECONDS: int = int(os.getenv("WEBSOCKET_POLL_INTERVAL_SECONDS", "3"))
    API_HOST: str = os.getenv("HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("PORT", "8000"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")


settings = Settings()
