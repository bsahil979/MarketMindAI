import json
from pathlib import Path
from typing import Dict, Any, Optional
import tiktoken
from pydantic import BaseModel, Field

class DocumentMetadata(BaseModel):
    document_id: str
    company: str
    ticker: str
    document_type: str  # 10-K, 10-Q, Annual Report, etc.
    source: str         # SEC EDGAR, IR, etc.
    publication_date: str
    token_count: int

class MetadataGenerator:
    """
    Metadata generator for financial documents in Portfolio Advisor AI.
    Calculates exact token counts and saves JSON metadata records.
    """

    def __init__(
        self,
        metadata_dir: str = "research/dataset/metadata",
        encoding_name: str = "cl100k_base"
    ):
        self.metadata_dir = Path(metadata_dir)
        self.metadata_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.tokenizer = None

    def count_tokens(self, text: str) -> int:
        if self.tokenizer:
            return len(self.tokenizer.encode(text, disallowed_special=()))
        return len(text.split())  # Fallback word count approximation

    def generate(
        self,
        document_id: str,
        clean_text: str,
        file_path: Path,
        ticker: str = "UNKNOWN",
        company: str = "UNKNOWN",
        document_type: str = "Financial Report",
        publication_date: str = "2024-01-01"
    ) -> DocumentMetadata:
        """
        Generates and saves JSON metadata for a document.
        """
        # Infer metadata from SEC folder structure if available
        parts = [p.upper() for p in file_path.parts]
        for part in ["10-K", "10-Q", "8-K"]:
            if part in parts:
                document_type = part
                break

        # Attempt ticker extraction from path
        path_str = str(file_path)
        if "sec-edgar-filings" in path_str or "sec_edgar_filings" in path_str:
            for parent in file_path.parents:
                if parent.name.isupper() and len(parent.name) <= 5:
                    ticker = parent.name
                    company = f"{ticker} Inc."
                    break

        token_count = self.count_tokens(clean_text)

        meta = DocumentMetadata(
            document_id=document_id,
            company=company,
            ticker=ticker.upper(),
            document_type=document_type,
            source="SEC EDGAR",
            publication_date=publication_date,
            token_count=token_count
        )

        out_path = self.metadata_dir / f"{document_id}.json"
        out_path.write_text(meta.model_dump_json(indent=2), encoding="utf-8")

        return meta

if __name__ == "__main__":
    mg = MetadataGenerator()
    print("MetadataGenerator ready.")
