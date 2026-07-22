import os
import time
from pathlib import Path
from typing import List, Optional

try:
    from sec_edgar_downloader import Downloader
    HAS_SEC_DOWNLOADER = True
except ImportError:
    HAS_SEC_DOWNLOADER = False

class SECDownloader:
    """
    Downloader for SEC 10-K and 10-Q filings using sec-edgar-downloader.
    """

    DEFAULT_USER_AGENT = "MarketMindAI Research research@marketmind.ai"

    def __init__(
        self,
        output_dir: str = "research/dataset/raw",
        user_agent: Optional[str] = None
    ):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.user_agent = user_agent or self.DEFAULT_USER_AGENT
        
        parts = self.user_agent.split()
        company_name = parts[0] if parts else "MarketMindAI"
        email = parts[-1] if "@" in parts[-1] else "research@marketmind.ai"

        if HAS_SEC_DOWNLOADER:
            self.dl = Downloader(company_name, email, self.output_dir)
        else:
            self.dl = None
            print("[SEC Downloader Notice] sec-edgar-downloader package not installed. SEC downloading unavailable until `pip install -r research/requirements.txt` is run.")

    def download_filings(
        self,
        tickers: List[str],
        form_types: List[str] = ["10-K", "10-Q"],
        limit: int = 2
    ) -> List[Path]:
        """
        Downloads filings for a list of tickers.
        Returns a list of paths to downloaded raw filing files.
        """
        downloaded_files = []

        if not self.dl:
            print("[SEC Downloader] Skipping SEC download (downloader package missing).")
            return downloaded_files

        for ticker in tickers:
            ticker_upper = ticker.strip().upper()
            for form in form_types:
                try:
                    print(f"[SEC Downloader] Fetching {form} for {ticker_upper} (limit={limit})...")
                    self.dl.get(form, ticker_upper, limit=limit)
                    time.sleep(0.2)
                except Exception as e:
                    print(f"[SEC Downloader Error] Failed to download {form} for {ticker_upper}: {e}")

        for ext in ["*.html", "*.txt", "*.htm"]:
            downloaded_files.extend(list(self.output_dir.rglob(ext)))

        print(f"[SEC Downloader] Total downloaded files found: {len(downloaded_files)}")
        return downloaded_files

if __name__ == "__main__":
    downloader = SECDownloader()
    print("SECDownloader ready.")
