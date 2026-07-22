import json
from pathlib import Path
from typing import List, Dict, Any
import tiktoken
from pydantic import BaseModel

class Chunk(BaseModel):
    chunk_id: str
    document_id: str
    ticker: str
    company: str
    document_type: str
    chunk_index: int
    text: str
    token_count: int

class DocumentChunker:
    """
    Sliding window chunker for financial text.
    Configured for 512 token chunk size and 64 token overlap.
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 64,
        chunks_dir: str = "research/dataset/chunks",
        encoding_name: str = "cl100k_base"
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks_dir = Path(chunks_dir)
        self.chunks_dir.mkdir(parents=True, exist_ok=True)
        try:
            self.tokenizer = tiktoken.get_encoding(encoding_name)
        except Exception:
            self.tokenizer = None

    def chunk_document(
        self,
        document_id: str,
        text: str,
        metadata: Dict[str, Any]
    ) -> List[Chunk]:
        """
        Splits text into chunks of specified token size with overlap.
        Saves chunks to research/dataset/chunks/{document_id}_chunks.json.
        """
        if self.tokenizer:
            tokens = self.tokenizer.encode(text, disallowed_special=())
        else:
            # Fallback word-level chunking
            words = text.split()
            tokens = list(range(len(words)))

        chunks: List[Chunk] = []
        step = self.chunk_size - self.chunk_overlap
        if step <= 0:
            step = self.chunk_size

        chunk_idx = 0
        for i in range(0, len(tokens), step):
            token_slice = tokens[i : i + self.chunk_size]
            if not token_slice:
                break

            if self.tokenizer:
                chunk_text = self.tokenizer.decode(token_slice)
            else:
                chunk_text = " ".join(words[i : i + self.chunk_size])

            chunk_id = f"{document_id}_chunk_{chunk_idx:04d}"

            chunk_obj = Chunk(
                chunk_id=chunk_id,
                document_id=document_id,
                ticker=metadata.get("ticker", "UNKNOWN"),
                company=metadata.get("company", "UNKNOWN"),
                document_type=metadata.get("document_type", "UNKNOWN"),
                chunk_index=chunk_idx,
                text=chunk_text.strip(),
                token_count=len(token_slice)
            )

            chunks.append(chunk_obj)
            chunk_idx += 1

        # Save document chunks output JSON
        output_file = self.chunks_dir / f"{document_id}_chunks.json"
        chunk_dicts = [c.model_dump() for c in chunks]
        output_file.write_text(json.dumps(chunk_dicts, indent=2), encoding="utf-8")

        return chunks

if __name__ == "__main__":
    chunker = DocumentChunker()
    print("DocumentChunker ready.")
