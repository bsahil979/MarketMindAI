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
    with synthetic multi-company generator for offline evaluation.
    """

    DEFAULT_USER_AGENT = "MarketMindAI Research research@marketmind.ai"
    TARGET_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "JPM", "BRK-B", "NFLX"]

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
        tickers: List[str] = TARGET_TICKERS,
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
            return self.generate_sample_corpus()

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
            print("[SEC Downloader] No live files fetched. Generating 10-company synthetic filing corpus...")
            return self.generate_sample_corpus()

        print(f"[SEC Downloader] Total downloaded files found: {len(downloaded_files)}")
        return downloaded_files

    def generate_sample_corpus(self) -> List[Path]:
        """
        Generates 10-K filing documents for all 10 target companies with structured financial statement tables.
        """
        companies_data = {
            "AAPL": {
                "name": "Apple Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Total net sales increased 6% year-over-year driven by record Services revenue and Mac performance.",
                "rows": [
                    ("iPhone", "201183", "200583"),
                    ("Services", "96169", "85200"),
                    ("Wearables & Home", "37005", "39845"),
                    ("Mac", "29984", "29357"),
                    ("Total Net Sales", "391035", "383285")
                ],
                "risks": "Global economic conditions, supply chain disruptions, and intense competition could impact future revenues."
            },
            "MSFT": {
                "name": "Microsoft Corporation",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Revenue grew 16% driven by Microsoft Cloud expansion and Azure AI demand.",
                "rows": [
                    ("Intelligent Cloud (Azure)", "105362", "87907"),
                    ("Productivity & Business (Office)", "69274", "69274"),
                    ("More Personal Computing", "56700", "54734"),
                    ("Total Revenue", "245121", "211915")
                ],
                "risks": "Cybersecurity threats, fierce AI infrastructure competition, and regulatory scrutiny regarding acquisitions."
            },
            "NVDA": {
                "name": "NVIDIA Corporation",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Data Center revenue surged 217% driven by generative AI enterprise adoption and Hopper GPU demand.",
                "rows": [
                    ("Data Center", "47525", "15005"),
                    ("Gaming", "10447", "9067"),
                    ("Professional Visualization", "1553", "1544"),
                    ("Automotive", "1091", "903"),
                    ("Total Revenue", "60922", "26974")
                ],
                "risks": "Geopolitical trade restrictions, semiconductor fabrication concentration, and rapid technological shifts."
            },
            "TSLA": {
                "name": "Tesla, Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Total revenues increased 19% driven by Model Y volume expansion and Energy Storage deployments.",
                "rows": [
                    ("Automotive Sales", "82419", "71462"),
                    ("Energy Generation & Storage", "6035", "3909"),
                    ("Services & Other", "8319", "6091"),
                    ("Total Revenues", "96773", "81462")
                ],
                "risks": "Battery cell supply constraints, autonomous driving regulatory delays, and global EV price sensitivity."
            },
            "AMZN": {
                "name": "Amazon.com, Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Net sales increased 12% to $574.8 Billion driven by AWS growth and advertising momentum.",
                "rows": [
                    ("North America Retail", "352828", "315880"),
                    ("International Retail", "131200", "118016"),
                    ("AWS Cloud", "90757", "80096"),
                    ("Total Net Sales", "574785", "513992")
                ],
                "risks": "Fulfillment logistics costs, international currency fluctuations, and AWS infrastructure energy demands."
            },
            "GOOGL": {
                "name": "Alphabet Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Consolidated revenues increased 9% reflecting strength in Google Search and Google Cloud profitability.",
                "rows": [
                    ("Google Search & Advertising", "175023", "162450"),
                    ("YouTube Ads", "31510", "29200"),
                    ("Google Cloud", "33088", "26280"),
                    ("Total Revenues", "307394", "282836")
                ],
                "risks": "Antitrust litigation, search advertising market evolution, and generative AI query latency costs."
            },
            "META": {
                "name": "Meta Platforms, Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Ad impressions increased 28% year-over-year across Family of Apps.",
                "rows": [
                    ("Family of Apps (Ad Revenue)", "131948", "113642"),
                    ("Reality Labs", "1896", "2159"),
                    ("Total Revenue", "134902", "116601")
                ],
                "risks": "Youth safety regulatory mandates, advertising privacy restrictions, and Reality Labs capital expenditure."
            },
            "JPM": {
                "name": "JPMorgan Chase & Co.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Net interest income rose significantly supported by interest rate environments and First Republic integration.",
                "rows": [
                    ("Consumer & Community Banking", "70123", "55120"),
                    ("Corporate & Investment Bank", "48700", "46100"),
                    ("Asset & Wealth Management", "19800", "17700"),
                    ("Total Net Revenue", "158104", "128694")
                ],
                "risks": "Credit default rate spikes, commercial real estate exposure, and macroeconomic interest rate shifts."
            },
            "BRK-B": {
                "name": "Berkshire Hathaway Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Insurance float increased to $169 Billion with strong underwriting income across Geico and reinsurance.",
                "rows": [
                    ("Insurance Underwriting & Investment", "95200", "82400"),
                    ("BNSF Railroad", "23400", "24100"),
                    ("Berkshire Hathaway Energy", "26100", "26300"),
                    ("Manufacturing & Service", "164200", "156800"),
                    ("Total Revenue", "364482", "302089")
                ],
                "risks": "Catastrophic climate events, equity market volatility, and succession leadership transitions."
            },
            "NFLX": {
                "name": "Netflix, Inc.",
                "type": "Form 10-K Annual Report",
                "fy": "2024",
                "mda": "Paid memberships grew 12.8% to 260 Million global subscribers driven by paid sharing and ad-supported tiers.",
                "rows": [
                    ("UCAN (US & Canada)", "14860", "14080"),
                    ("EMEA", "10560", "9750"),
                    ("LATAM", "4450", "4070"),
                    ("APAC", "3850", "3570"),
                    ("Total Revenue", "33720", "31615")
                ],
                "risks": "Subscriber churn, content production cost inflation, and international gaming investments."
            }
        }

        generated_paths = []
        for ticker, info in companies_data.items():
            content = f"""{info['name']} - {info['type']}
Ticker: {ticker} | Fiscal Year: {info['fy']}
Item 7. Management's Discussion and Analysis
{info['mda']}

| Segment | 2024 Revenue ($M) | 2023 Revenue ($M) |
| --- | --- | --- |
"""
            for row in info['rows']:
                content += f"| {row[0]} | {row[1]} | {row[2]} |\n"

            content += f"\nRisk Factors\n{info['risks']}\n"

            file_path = self.output_dir / f"sample_{ticker.lower()}_10k.md"
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(content)

            generated_paths.append(file_path)

        print(f"[SEC Downloader] Generated 10-company synthetic filing corpus ({len(generated_paths)} files).")
        return generated_paths

if __name__ == "__main__":
    downloader = SECDownloader()
    downloader.generate_sample_corpus()
