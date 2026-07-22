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
    Downloader for SEC 10-K and 10-Q filings using sec-edgar-downloader,
    with synthetic multi-company generator for offline 50+ corporate corpus evaluation.
    """

    DEFAULT_USER_AGENT = "MarketMindAI Research research@marketmind.ai"
    TARGET_50_TICKERS = [
        "AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "JPM", "BRK-B", "NFLX",
        "BAC", "WMT", "DIS", "AMD", "INTC", "ORCL", "CRM", "CSCO", "PYPL", "UBER",
        "ABNB", "COIN", "PLTR", "SNOW", "NET", "SQ", "SHOP", "SPOT", "PANW", "CRWD",
        "PFE", "JNJ", "UNH", "PG", "HD", "MA", "V", "XOM", "CVX", "PEP",
        "KO", "COST", "AVGO", "TXN", "QCOM", "TMUS", "NKE", "SBUX", "CAT", "GE"
    ]

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
            print("[SEC Downloader Notice] sec-edgar-downloader package not installed. Using dual-mode synthetic corpus generator.")

    def download_filings(
        self,
        tickers: List[str] = TARGET_50_TICKERS,
        form_types: List[str] = ["10-K", "10-Q"],
        limit: int = 2
    ) -> List[Path]:
        """
        Downloads filings for a list of tickers.
        Returns a list of paths to downloaded raw filing files.
        """
        downloaded_files = []

        if not self.dl:
            print("[SEC Downloader] Skipping live SEC download (downloader package missing).")
            return self.generate_sample_corpus(tickers=tickers)

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

        if len(downloaded_files) == 0:
            print("[SEC Downloader] No live files fetched. Generating 50-company corporate filing corpus...")
            return self.generate_sample_corpus(tickers=tickers)

        print(f"[SEC Downloader] Total downloaded files found: {len(downloaded_files)}")
        return downloaded_files

    def generate_sample_corpus(self, tickers: List[str] = TARGET_50_TICKERS) -> List[Path]:
        """
        Generates 10-K, 10-Q, and Earnings Call transcript documents for 50 target companies.
        """
        generated_paths = []
        for ticker in tickers:
            t = ticker.upper()
            
            # 1. Form 10-K Annual Report
            content_10k = f"""{t} Corp. - Form 10-K Annual Report
Ticker: {t} | Fiscal Year: 2024 | Page: 32
Item 7. Management's Discussion and Analysis
Total Net Revenue for FY 2024 reached ${10000 + hash(t) % 90000} Million, an increase of {(hash(t) % 15) + 5}% year-over-year.

| Segment | 2024 Revenue ($M) | 2023 Revenue ($M) | Operating Margin |
| --- | --- | --- | --- |
| Primary Segment A | {5000 + hash(t) % 40000} | {4500 + hash(t) % 35000} | 28.5% |
| Enterprise Segment B | {3000 + hash(t) % 25000} | {2800 + hash(t) % 20000} | 34.2% |
| Consumer & Other | {2000 + hash(t) % 15000} | {1800 + hash(t) % 12000} | 18.9% |
| Total Net Sales | {10000 + hash(t) % 90000} | {9100 + hash(t) % 80000} | 27.1% |

Operating Cash Flow: ${2500 + hash(t) % 15000} Million. Free Cash Flow: ${1800 + hash(t) % 10000} Million.

Item 1A. Risk Factors
Key risks include global macroeconomic volatility, cybersecurity threats, international regulatory compliance, and supply chain concentration.
"""
            p_10k = self.output_dir / f"sample_{t.lower()}_10k.md"
            p_10k.write_text(content_10k, encoding="utf-8")
            generated_paths.append(p_10k)

            # 2. Form 10-Q Quarterly Report
            content_10q = f"""{t} Corp. - Form 10-Q Quarterly Report (Q3 2024)
Ticker: {t} | Quarter: Q3 2024 | Page: 18
Item 2. Management's Discussion and Analysis
Quarterly net revenue for Q3 2024 was ${2500 + hash(t) % 22000} Million, up {(hash(t) % 12) + 3}% compared to Q3 2023.

| Quarter | Q3 2024 ($M) | Q3 2023 ($M) |
| --- | --- | --- |
| Total Quarterly Revenue | {2500 + hash(t) % 22000} | {2200 + hash(t) % 19000} |
| Net Income | {600 + hash(t) % 6000} | {510 + hash(t) % 5000} |

Cash and Cash Equivalents ended the quarter at ${4000 + hash(t) % 30000} Million.
"""
            p_10q = self.output_dir / f"sample_{t.lower()}_10q.md"
            p_10q.write_text(content_10q, encoding="utf-8")
            generated_paths.append(p_10q)

            # 3. Earnings Call Transcript
            content_call = f"""{t} Corp. - Q4 & Full Year 2024 Earnings Call Transcript
Ticker: {t} | Date: Q4 2024 | Page: 4
Executive Commentary:
CEO Statement: "We delivered exceptional financial performance across our core segments in FY 2024. Our strategic investments in AI infrastructure and enterprise cloud solutions continue to accelerate customer adoption."
CFO Guidance: "For FY 2025, we anticipate revenue growth of 10% to 14% year-over-year with expanding operating margins."
"""
            p_call = self.output_dir / f"sample_{t.lower()}_earnings_call.md"
            p_call.write_text(content_call, encoding="utf-8")
            generated_paths.append(p_call)

        print(f"[SEC Downloader] Generated {len(generated_paths)} documents across {len(tickers)} corporate entities.")
        return generated_paths

if __name__ == "__main__":
    downloader = SECDownloader()
    downloader.generate_sample_corpus()
