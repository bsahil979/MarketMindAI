import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.rag.embeddings import FinancialEmbeddings

try:
    import chromadb
    from chromadb.config import Settings
    HAS_CHROMADB = True
except ImportError:
    HAS_CHROMADB = False

class VectorStoreManager:
    """
    Vector Store Manager using ChromaDB for persistent document vector indexing.
    Includes a fallback JSON index if chromadb is not installed.
    """

    def __init__(
        self,
        persist_dir: str = "research/rag/vectordb",
        collection_name: str = "financial_filings",
        embedder: Optional[FinancialEmbeddings] = None
    ):
        self.persist_dir = Path(persist_dir)
        self.persist_dir.mkdir(parents=True, exist_ok=True)
        self.collection_name = collection_name
        self.embedder = embedder or FinancialEmbeddings()
        self.client = None
        self.collection = None
        self._fallback_index: List[Dict[str, Any]] = []

        if HAS_CHROMADB:
            try:
                self.client = chromadb.PersistentClient(path=str(self.persist_dir))
                self.collection = self.client.get_or_create_collection(name=collection_name)
            except Exception as e:
                print(f"[VectorStore Warning] ChromaDB initialization failed: {e}. Using local JSON index fallback.")

    def index_chunks(self, chunks: List[Dict[str, Any]]) -> int:
        """
        Indexes a list of chunk dictionaries into ChromaDB / Fallback index.
        """
        if not chunks:
            return 0

        ids = [c["chunk_id"] for c in chunks]
        texts = [c["text"] for c in chunks]
        metadatas = [
            {
                "document_id": c.get("document_id", ""),
                "ticker": c.get("ticker", ""),
                "company": c.get("company", ""),
                "document_type": c.get("document_type", ""),
                "chunk_index": c.get("chunk_index", 0)
            }
            for c in chunks
        ]

        embeddings = self.embedder.embed_documents(texts)

        if self.collection:
            self.collection.add(
                ids=ids,
                documents=texts,
                embeddings=embeddings,
                metadatas=metadatas
            )
        else:
            # Fallback in-memory index
            for idx, c_id in enumerate(ids):
                self._fallback_index.append({
                    "id": c_id,
                    "text": texts[idx],
                    "metadata": metadatas[idx],
                    "embedding": embeddings[idx]
                })
            # Save fallback index to disk
            fallback_file = self.persist_dir / "fallback_index.json"
            fallback_file.write_text(json.dumps(self._fallback_index, indent=2), encoding="utf-8")

        return len(chunks)

    def similarity_search(
        self,
        query: str,
        top_k: int = 4,
        ticker_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Performs semantic similarity search for a query with optional ticker metadata filter.
        """
        query_vec = self.embedder.embed_query(query)
        results = []

        if self.collection:
            where_clause = {"ticker": ticker_filter.upper()} if ticker_filter else None
            query_results = self.collection.query(
                query_embeddings=[query_vec],
                n_results=top_k,
                where=where_clause
            )

            if query_results and "documents" in query_results and query_results["documents"]:
                docs = query_results["documents"][0]
                metas = query_results["metadatas"][0] if "metadatas" in query_results else [{}] * len(docs)
                ids = query_results["ids"][0] if "ids" in query_results else [""] * len(docs)

                for i in range(len(docs)):
                    results.append({
                        "chunk_id": ids[i],
                        "text": docs[i],
                        "metadata": metas[i]
                    })
        else:
            # Fallback search
            for item in self._fallback_index:
                if ticker_filter and item["metadata"].get("ticker") != ticker_filter.upper():
                    continue
                results.append({
                    "chunk_id": item["id"],
                    "text": item["text"],
                    "metadata": item["metadata"]
                })
            results = results[:top_k]

        return results

if __name__ == "__main__":
    vsm = VectorStoreManager()
    print("VectorStoreManager ready.")
