"""
Hybrid Search Engine - Combines BM25 lexical search with vector similarity
Includes reranking for improved retrieval quality
"""

import logging
from typing import List, Dict, Any, Optional
from rank_bm25 import BM25Okapi
import numpy as np

logger = logging.getLogger("marketmind.rag.hybrid_search")

class HybridSearchEngine:
    def __init__(self, alpha: float = 0.5, top_k: int = 10):
        """
        Initialize hybrid search engine
        
        Args:
            alpha: Weight for vector search (0-1), BM25 weight is (1-alpha)
            top_k: Number of results to return
        """
        self.alpha = alpha
        self.top_k = top_k
        self.bm25_index = None
        self.documents = []
        self.tokenized_docs = []
        
    def build_bm25_index(self, documents: List[str]):
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document texts
        """
        self.documents = documents
        self.tokenized_docs = [self._tokenize(doc) for doc in documents]
        self.bm25_index = BM25Okapi(self.tokenized_docs)
        logger.info(f"Built BM25 index with {len(documents)} documents")
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization for BM25"""
        import re
        # Convert to lowercase and split on non-alphanumeric
        tokens = re.findall(r'\b\w+\b', text.lower())
        return tokens
    
    def search(
        self,
        query: str,
        query_embedding: Optional[List[float]] = None,
        vector_results: Optional[List[Dict]] = None,
        rerank: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search combining BM25 and vector search
        
        Args:
            query: Search query text
            query_embedding: Query embedding vector (optional)
            vector_results: Pre-computed vector search results (optional)
            rerank: Whether to apply reranking
            
        Returns:
            List of ranked documents with scores
        """
        if not self.bm25_index:
            logger.warning("BM25 index not built, returning vector results only")
            return vector_results or []
        
        # BM25 search
        tokenized_query = self._tokenize(query)
        bm25_scores = self.bm25_index.get_scores(tokenized_query)
        
        # Combine with vector results if provided
        if vector_results and query_embedding:
            results = self._combine_scores(
                bm25_scores, 
                vector_results, 
                self.alpha
            )
        else:
            # BM25 only
            results = [
                {
                    "index": i,
                    "text": self.documents[i],
                    "bm25_score": float(bm25_scores[i]),
                    "vector_score": 0.0,
                    "combined_score": float(bm25_scores[i])
                }
                for i in range(len(self.documents))
            ]
        
        # Sort by combined score
        results.sort(key=lambda x: x["combined_score"], reverse=True)
        
        # Apply reranking if requested
        if rerank:
            results = self._rerank(query, results)
        
        return results[:self.top_k]
    
    def _combine_scores(
        self,
        bm25_scores: np.ndarray,
        vector_results: List[Dict],
        alpha: float
    ) -> List[Dict[str, Any]]:
        """
        Combine BM25 and vector scores with weighted average
        
        Args:
            bm25_scores: BM25 scores array
            vector_results: Vector search results with distances
            alpha: Weight for vector search
            
        Returns:
            Combined results
        """
        # Normalize BM25 scores
        if bm25_scores.max() > 0:
            bm25_normalized = bm25_scores / bm25_scores.max()
        else:
            bm25_normalized = bm25_scores
        
        # Create a mapping from vector result indices to their scores
        vector_score_map = {}
        for result in vector_results:
            idx = result.get("index")
            # Convert distance to similarity (lower distance = higher similarity)
            distance = result.get("distance", 1.0)
            vector_score = 1.0 / (1.0 + distance)  # Convert to similarity
            vector_score_map[idx] = vector_score
        
        # Combine scores
        combined_results = []
        for i in range(len(self.documents)):
            bm25_score = bm25_normalized[i]
            vector_score = vector_score_map.get(i, 0.0)
            
            combined_score = alpha * vector_score + (1 - alpha) * bm25_score
            
            combined_results.append({
                "index": i,
                "text": self.documents[i],
                "bm25_score": float(bm25_score),
                "vector_score": float(vector_score),
                "combined_score": float(combined_score)
            })
        
        return combined_results
    
    def _rerank(self, query: str, results: List[Dict]) -> List[Dict]:
        """
        Apply cross-encoder style reranking based on query-document relevance
        
        Args:
            query: Original query
            results: Initial search results
            
        Returns:
            Reranked results
        """
        query_lower = query.lower()
        query_terms = set(self._tokenize(query))
        
        for result in results:
            text = result["text"].lower()
            text_terms = set(self._tokenize(text))
            
            # Calculate term overlap
            overlap = len(query_terms & text_terms)
            overlap_ratio = overlap / max(len(query_terms), 1)
            
            # Boost score based on term overlap
            rerank_boost = 1.0 + (overlap_ratio * 0.5)
            result["rerank_score"] = result["combined_score"] * rerank_boost
            result["overlap_ratio"] = overlap_ratio
        
        # Sort by rerank score
        results.sort(key=lambda x: x["rerank_score"], reverse=True)
        
        return results
    
    def update_index(self, new_documents: List[str]):
        """
        Update BM25 index with new documents
        
        Args:
            new_documents: List of new document texts
        """
        self.documents.extend(new_documents)
        new_tokenized = [self._tokenize(doc) for doc in new_documents]
        self.tokenized_docs.extend(new_tokenized)
        
        # Rebuild index
        self.bm25_index = BM25Okapi(self.tokenized_docs)
        logger.info(f"Updated BM25 index with {len(new_documents)} new documents")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get search engine statistics"""
        return {
            "total_documents": len(self.documents),
            "alpha": self.alpha,
            "top_k": self.top_k,
            "bm25_index_built": self.bm25_index is not None
        }
