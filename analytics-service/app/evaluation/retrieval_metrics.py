"""
Retrieval Metrics - Measure quality of document retrieval
Includes precision, recall, MRR, NDCG, and other IR metrics
"""

import logging
import numpy as np
from typing import List, Dict, Any, Set, Optional
from collections import defaultdict

logger = logging.getLogger("marketmind.evaluation.retrieval")

class RetrievalMetrics:
    def __init__(self):
        """Initialize retrieval metrics calculator"""
        self.queries_evaluated = 0
        self.total_retrieved = 0
        self.total_relevant = 0
        
    def calculate_precision_at_k(self, retrieved_docs: List[str], relevant_docs: Set[str], k: int) -> float:
        """
        Calculate Precision@K
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            k: Number of documents to consider
            
        Returns:
            Precision@K score
        """
        if not retrieved_docs or k <= 0:
            return 0.0
        
        retrieved_at_k = retrieved_docs[:k]
        relevant_retrieved = len([doc for doc in retrieved_at_k if doc in relevant_docs])
        
        return relevant_retrieved / min(k, len(retrieved_at_k))
    
    def calculate_recall_at_k(self, retrieved_docs: List[str], relevant_docs: Set[str], k: int) -> float:
        """
        Calculate Recall@K
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            k: Number of documents to consider
            
        Returns:
            Recall@K score
        """
        if not relevant_docs or k <= 0:
            return 0.0
        
        retrieved_at_k = retrieved_docs[:k]
        relevant_retrieved = len([doc for doc in retrieved_at_k if doc in relevant_docs])
        
        return relevant_retrieved / len(relevant_docs)
    
    def calculate_mrr(self, retrieved_docs: List[str], relevant_docs: Set[str]) -> float:
        """
        Calculate Mean Reciprocal Rank
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            
        Returns:
            MRR score
        """
        if not retrieved_docs or not relevant_docs:
            return 0.0
        
        for i, doc in enumerate(retrieved_docs, start=1):
            if doc in relevant_docs:
                return 1.0 / i
        
        return 0.0
    
    def calculate_ndcg_at_k(self, retrieved_docs: List[str], relevant_docs: Set[str], relevance_scores: Dict[str, float], k: int) -> float:
        """
        Calculate Normalized Discounted Cumulative Gain@K
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            relevance_scores: Dict mapping doc IDs to relevance scores (0-1)
            k: Number of documents to consider
            
        Returns:
            NDCG@K score
        """
        if not retrieved_docs or k <= 0:
            return 0.0
        
        retrieved_at_k = retrieved_docs[:k]
        
        # Calculate DCG
        dcg = 0.0
        for i, doc in enumerate(retrieved_at_k, start=1):
            relevance = relevance_scores.get(doc, 0.0)
            if doc in relevant_docs:
                dcg += relevance / np.log2(i + 1)
        
        # Calculate IDCG (ideal DCG)
        ideal_relevances = sorted([relevance_scores.get(doc, 0.0) for doc in relevant_docs], reverse=True)[:k]
        idcg = 0.0
        for i, relevance in enumerate(ideal_relevances, start=1):
            idcg += relevance / np.log2(i + 1)
        
        return dcg / idcg if idcg > 0 else 0.0
    
    def calculate_average_precision(self, retrieved_docs: List[str], relevant_docs: Set[str]) -> float:
        """
        Calculate Average Precision
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            
        Returns:
            Average Precision score
        """
        if not retrieved_docs or not relevant_docs:
            return 0.0
        
        precisions = []
        relevant_count = 0
        
        for i, doc in enumerate(retrieved_docs, start=1):
            if doc in relevant_docs:
                relevant_count += 1
                precision = relevant_count / i
                precisions.append(precision)
        
        return np.mean(precisions) if precisions else 0.0
    
    def evaluate_retrieval(self, query_results: List[Dict[str, Any]], ground_truth: Dict[str, Set[str]], 
                          relevance_scores: Optional[Dict[str, Dict[str, float]]] = None) -> Dict[str, Any]:
        """
        Evaluate retrieval performance across multiple queries
        
        Args:
            query_results: List of dicts with 'query_id', 'retrieved_docs'
            ground_truth: Dict mapping query_id to set of relevant doc IDs
            relevance_scores: Optional dict mapping query_id to doc relevance scores
            
        Returns:
            Dictionary of evaluation metrics
        """
        if relevance_scores is None:
            relevance_scores = {}
        
        k_values = [1, 3, 5, 10]
        metrics = defaultdict(list)
        
        for query_result in query_results:
            query_id = query_result['query_id']
            retrieved_docs = query_result['retrieved_docs']
            relevant_docs = ground_truth.get(query_id, set())
            
            self.queries_evaluated += 1
            self.total_retrieved += len(retrieved_docs)
            self.total_relevant += len(relevant_docs)
            
            # Calculate metrics for different k values
            for k in k_values:
                precision = self.calculate_precision_at_k(retrieved_docs, relevant_docs, k)
                recall = self.calculate_recall_at_k(retrieved_docs, relevant_docs, k)
                metrics[f'precision_at_{k}'].append(precision)
                metrics[f'recall_at_{k}'].append(recall)
            
            # MRR
            mrr = self.calculate_mrr(retrieved_docs, relevant_docs)
            metrics['mrr'].append(mrr)
            
            # NDCG
            query_relevance = relevance_scores.get(query_id, {})
            for k in k_values:
                ndcg = self.calculate_ndcg_at_k(retrieved_docs, relevant_docs, query_relevance, k)
                metrics[f'ndcg_at_{k}'].append(ndcg)
            
            # Average Precision
            ap = self.calculate_average_precision(retrieved_docs, relevant_docs)
            metrics['average_precision'].append(ap)
        
        # Calculate average metrics
        avg_metrics = {}
        for metric_name, values in metrics.items():
            avg_metrics[metric_name] = float(np.mean(values)) if values else 0.0
        
        return {
            'num_queries': self.queries_evaluated,
            'avg_retrieved_per_query': self.total_retrieved / max(self.queries_evaluated, 1),
            'avg_relevant_per_query': self.total_relevant / max(self.queries_evaluated, 1),
            'metrics': avg_metrics
        }
    
    def evaluate_single_query(self, retrieved_docs: List[str], relevant_docs: Set[str], 
                             relevance_scores: Optional[Dict[str, float]] = None) -> Dict[str, float]:
        """
        Evaluate retrieval for a single query
        
        Args:
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            relevance_scores: Optional dict mapping doc IDs to relevance scores
            
        Returns:
            Dictionary of metrics for this query
        """
        if relevance_scores is None:
            relevance_scores = {doc: 1.0 for doc in relevant_docs}
        
        k_values = [1, 3, 5, 10]
        metrics = {}
        
        for k in k_values:
            metrics[f'precision_at_{k}'] = self.calculate_precision_at_k(retrieved_docs, relevant_docs, k)
            metrics[f'recall_at_{k}'] = self.calculate_recall_at_k(retrieved_docs, relevant_docs, k)
            metrics[f'ndcg_at_{k}'] = self.calculate_ndcg_at_k(retrieved_docs, relevant_docs, relevance_scores, k)
        
        metrics['mrr'] = self.calculate_mrr(retrieved_docs, relevant_docs)
        metrics['average_precision'] = self.calculate_average_precision(retrieved_docs, relevant_docs)
        
        return metrics
    
    def reset(self):
        """Reset metrics counters"""
        self.queries_evaluated = 0
        self.total_retrieved = 0
        self.total_relevant = 0
