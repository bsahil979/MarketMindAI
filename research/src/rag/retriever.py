import re
from typing import List, Dict, Any, Optional
from src.rag.vectordb import VectorStoreManager

class HybridRetriever:
    """
    Hybrid retriever combining Dense Vector Similarity Search with BM25 Keyword Search.
    Uses Reciprocal Rank Fusion (RRF) for reranking.
    """

    def __init__(self, vector_store: VectorStoreManager):
        self.vector_store = vector_store
        self.all_chunks: List[Dict[str, Any]] = []

    def load_chunks_for_keyword_search(self, chunks: List[Dict[str, Any]]):
        """
        Loads document chunks for BM25 keyword matching.
        """
        self.all_chunks = chunks

    def retrieve(
        self,
        query: str,
        top_k: int = 4,
        ticker_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Hybrid retrieval combining vector similarity search and keyword matching.
        """
        # 1. Vector Search
        vector_results = self.vector_store.similarity_search(
            query=query,
            top_k=top_k * 2,
            ticker_filter=ticker_filter
        )

        # 2. Keyword Search Fallback/Ranker
        keyword_results = self._keyword_search(query, top_k=top_k * 2, ticker_filter=ticker_filter)

        # 3. Reciprocal Rank Fusion (RRF)
        rrf_scores: Dict[str, float] = {}
        item_map: Dict[str, Dict[str, Any]] = {}

        for rank, item in enumerate(vector_results):
            c_id = item["chunk_id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (60 + rank + 1))
            item_map[c_id] = item

        for rank, item in enumerate(keyword_results):
            c_id = item["chunk_id"]
            rrf_scores[c_id] = rrf_scores.get(c_id, 0.0) + (1.0 / (60 + rank + 1))
            item_map[c_id] = item

        sorted_ids = sorted(rrf_scores.keys(), key=lambda k: rrf_scores[k], reverse=True)
        final_results = [item_map[c_id] for c_id in sorted_ids[:top_k]]

        return final_results

    def _keyword_search(
        self,
        query: str,
        top_k: int = 4,
        ticker_filter: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        query_terms = set(re.findall(r"\w+", query.lower()))
        scored_chunks = []

        for chunk in self.all_chunks:
            if ticker_filter and chunk.get("ticker") != ticker_filter.upper():
                continue
            text_terms = set(re.findall(r"\w+", chunk["text"].lower()))
            overlap = len(query_terms.intersection(text_terms))
            if overlap > 0:
                scored_chunks.append((overlap, chunk))

        scored_chunks.sort(key=lambda x: x[0], reverse=True)
        return [
            {
                "chunk_id": item[1]["chunk_id"],
                "text": item[1]["text"],
                "metadata": {
                    "document_id": item[1].get("document_id"),
                    "ticker": item[1].get("ticker"),
                    "company": item[1].get("company"),
                    "document_type": item[1].get("document_type")
                }
            }
            for item in scored_chunks[:top_k]
        ]

if __name__ == "__main__":
    vsm = VectorStoreManager()
    hr = HybridRetriever(vsm)
    print("HybridRetriever ready.")
