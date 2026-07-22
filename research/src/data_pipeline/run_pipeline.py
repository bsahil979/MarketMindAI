import argparse
import sys
from pathlib import Path
from typing import List

# Ensure python can import from current package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.data_pipeline.sec_downloader import SECDownloader
from src.data_pipeline.document_parser import DocumentParser
from src.data_pipeline.metadata_generator import MetadataGenerator
from src.data_pipeline.chunker import DocumentChunker

def run_phase1_pipeline(
    tickers: List[str],
    limit: int = 1,
    download_sec: bool = False,
    base_dir: str = "research/dataset"
):
    """
    Executes Phase 1 Data Pipeline:
    1. Downloads SEC Filings (if download_sec=True) or reads existing/raw files.
    2. Parses HTML/TXT to clean Markdown text (preserving tables).
    3. Generates structured metadata JSON records.
    4. Token-chunks text into 512-token segments (64 overlap).
    """
    base_path = Path(base_dir)
    raw_dir = base_path / "raw"
    processed_dir = base_path / "processed"
    metadata_dir = base_path / "metadata"
    chunks_dir = base_path / "chunks"

    for d in [raw_dir, processed_dir, metadata_dir, chunks_dir]:
        d.mkdir(parents=True, exist_ok=True)

    print("==========================================================")
    print("  Portfolio Advisor AI - Phase 1 Data Pipeline Runner    ")
    print("==========================================================")

    # 1. Download raw filings if requested
    if download_sec:
        print(f"[Phase 1] Downloading SEC filings for tickers: {tickers} (limit={limit})...")
        downloader = SECDownloader(output_dir=str(raw_dir))
        raw_files = downloader.download_filings(tickers=tickers, limit=limit)
    else:
        # Search for existing raw files
        raw_files = []
        for ext in ["*.html", "*.htm", "*.txt", "*.md"]:
            raw_files.extend(list(raw_dir.rglob(ext)))

    # If raw directory is empty, generate sample financial document for verification
    if not raw_files:
        print("[Phase 1] No raw files found. Creating sample financial filing for pipeline verification...")
        sample_path = raw_dir / "sample_aapl_10k.html"
        sample_html = """
        <html>
          <body>
            <h1>Apple Inc. - Form 10-K Annual Report</h1>
            <p>Ticker: AAPL | Fiscal Year: 2024</p>
            <h2>Item 7. Management's Discussion and Analysis</h2>
            <p>Total net sales increased 6% year-over-year driven by record Services revenue and Mac performance.</p>
            <table>
              <tr><th>Segment</th><th>2024 Revenue ($M)</th><th>2023 Revenue ($M)</th></tr>
              <tr><td>iPhone</td><td>201183</td><td>200583</td></tr>
              <tr><td>Services</td><td>96169</td><td>85200</td></tr>
              <tr><td>Total Net Sales</td><td>391035</td><td>383285</td></tr>
            </table>
            <h2>Risk Factors</h2>
            <p>Global economic conditions, supply chain disruptions, and intense competition could impact future revenues.</p>
          </body>
        </html>
        """
        sample_path.write_text(sample_html.strip(), encoding="utf-8")
        raw_files = [sample_path]

    print(f"[Phase 1] Processing {len(raw_files)} raw filing document(s)...")

    parser = DocumentParser(processed_dir=str(processed_dir))
    meta_gen = MetadataGenerator(metadata_dir=str(metadata_dir))
    chunker = DocumentChunker(chunk_size=512, chunk_overlap=64, chunks_dir=str(chunks_dir))

    total_chunks = 0
    total_tokens = 0

    for idx, raw_file in enumerate(raw_files, start=1):
        doc_id, clean_text = parser.parse_file(raw_file)

        # Detect ticker from path or filename
        ticker = "AAPL"
        for t in tickers:
            if t.lower() in str(raw_file).lower():
                ticker = t.upper()
                break

        metadata = meta_gen.generate(
            document_id=doc_id,
            clean_text=clean_text,
            file_path=raw_file,
            ticker=ticker,
            company=f"{ticker} Inc.",
            document_type="10-K",
            publication_date="2024-10-30"
        )

        chunks = chunker.chunk_document(
            document_id=doc_id,
            text=clean_text,
            metadata=metadata.model_dump()
        )

        total_chunks += len(chunks)
        total_tokens += metadata.token_count

        print(f"  [{idx}/{len(raw_files)}] {doc_id} -> Tokens: {metadata.token_count} | Chunks: {len(chunks)}")

    print("\n==========================================================")
    print("  Phase 1 Data Pipeline Completed Successfully!           ")
    print("==========================================================")
    print(f"  - Total Documents Processed : {len(raw_files)}")
    print(f"  - Total Tokens Counted      : {total_tokens}")
    print(f"  - Total Chunks Generated     : {total_chunks}")
    print(f"  - Processed Text Output     : {processed_dir.resolve()}")
    print(f"  - Metadata JSON Output      : {metadata_dir.resolve()}")
    print(f"  - Chunks Output             : {chunks_dir.resolve()}")

def main():
    parser = argparse.ArgumentParser(description="Portfolio Advisor AI - Data Pipeline CLI")
    parser.add_argument("--tickers", type=str, default="AAPL,NVDA,MSFT", help="Comma-separated list of stock tickers")
    parser.add_argument("--limit", type=int, default=1, help="Max filings per ticker")
    parser.add_argument("--download", action="store_true", help="Download raw filings from SEC EDGAR API")
    args = parser.parse_args()

    ticker_list = [t.strip().upper() for t in args.tickers.split(",") if t.strip()]
    run_phase1_pipeline(tickers=ticker_list, limit=args.limit, download_sec=args.download)

if __name__ == "__main__":
    main()
