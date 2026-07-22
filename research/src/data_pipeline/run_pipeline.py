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

DEFAULT_10_TICKERS = ["AAPL", "MSFT", "NVDA", "TSLA", "AMZN", "GOOGL", "META", "JPM", "BRK-B", "NFLX"]

def run_phase1_pipeline(
    tickers: List[str] = DEFAULT_10_TICKERS,
    limit: int = 1,
    download_sec: bool = False,
    base_dir: str = "research/dataset"
):
    """
    Executes Phase 1 Data Pipeline across 10 corporate tickers:
    1. Ingests SEC filings or generates 10-company structured corpus.
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

    downloader = SECDownloader(output_dir=str(raw_dir))

    # 1. Download raw filings if requested, else generate 10-company corpus
    if download_sec:
        print(f"[Phase 1] Downloading live SEC filings for tickers: {tickers} (limit={limit})...")
        raw_files = downloader.download_filings(tickers=tickers, limit=limit)
    else:
        raw_files = []
        for ext in ["*.html", "*.htm", "*.txt", "*.md"]:
            raw_files.extend(list(raw_dir.rglob(ext)))

    if len(raw_files) < 5:
        print("[Phase 1] Ingesting 10-company corporate filing corpus...")
        raw_files = downloader.generate_sample_corpus()

    print(f"[Phase 1] Processing {len(raw_files)} raw filing document(s)...")

    parser = DocumentParser(processed_dir=str(processed_dir))
    meta_gen = MetadataGenerator(metadata_dir=str(metadata_dir))
    chunker = DocumentChunker(chunk_size=512, chunk_overlap=64, chunks_dir=str(chunks_dir))

    total_chunks = 0
    total_tokens = 0

    for idx, raw_file in enumerate(raw_files, start=1):
        doc_id, clean_text = parser.parse_file(raw_file)

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
            company=f"{ticker} Corporation",
            document_type="10-K"
        )

        chunks = chunker.chunk_document(document_id=doc_id, text=clean_text, metadata=metadata.model_dump())

        total_tokens += metadata.token_count
        total_chunks += len(chunks)

        print(f"  [{idx}/{len(raw_files)}] {doc_id} -> Tokens: {metadata.token_count} | Chunks: {len(chunks)}")

    print("\n==========================================================")
    print("  Phase 1 Data Pipeline Completed Successfully!           ")
    print("==========================================================")
    print(f"  - Total Documents Processed : {len(raw_files)}")
    print(f"  - Total Tokens Counted      : {total_tokens}")
    print(f"  - Total Chunks Generated     : {total_chunks}")
    print(f"  - Processed Text Output     : {processed_dir.resolve()}")
    print(f"  - Metadata JSON Output      : {metadata_dir.resolve()}")
    print(f"  - Chunks Output             : {chunks_dir.resolve()}\n")

    return total_chunks

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Phase 1 Financial Dataset Pipeline")
    parser.add_argument("--tickers", type=str, default="AAPL,MSFT,NVDA,TSLA,AMZN,GOOGL,META,JPM,BRK-B,NFLX", help="Comma-separated list of tickers")
    parser.add_argument("--limit", type=int, default=1, help="Max filings per ticker")
    parser.add_argument("--download", action="store_true", help="Download live SEC filings via sec-edgar-downloader")
    args = parser.parse_args()

    ticker_list = [t.strip() for t in args.tickers.split(",") if t.strip()]
    run_phase1_pipeline(tickers=ticker_list, limit=args.limit, download_sec=args.download)
