"""
Evaluation Manager - Orchestrates comprehensive evaluation of RAG and agent performance
Combines retrieval metrics, answer metrics, and cost tracking
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime
from .retrieval_metrics import RetrievalMetrics
from .answer_metrics import AnswerMetrics
from .cost_tracker import CostTracker

logger = logging.getLogger("marketmind.evaluation.manager")

class EvaluationManager:
    def __init__(self):
        """Initialize evaluation manager with all metric calculators"""
        self.retrieval_metrics = RetrievalMetrics()
        self.answer_metrics = AnswerMetrics()
        self.cost_tracker = CostTracker()
        self.evaluation_history = []
        
    def evaluate_rag_query(self, query: str, retrieved_docs: List[str], 
                          relevant_docs: set, answer: str, context: str,
                          ground_truth: Optional[str] = None,
                          relevance_scores: Optional[Dict[str, float]] = None) -> Dict[str, Any]:
        """
        Comprehensive evaluation of a single RAG query
        
        Args:
            query: Original query
            retrieved_docs: List of retrieved document IDs
            relevant_docs: Set of relevant document IDs
            answer: Generated answer
            context: Retrieved context
            ground_truth: Optional reference answer
            relevance_scores: Optional relevance scores for documents
            
        Returns:
            Comprehensive evaluation results
        """
        evaluation_id = len(self.evaluation_history) + 1
        timestamp = datetime.now()
        
        # Evaluate retrieval
        retrieval_results = self.retrieval_metrics.evaluate_single_query(
            retrieved_docs, relevant_docs, relevance_scores
        )
        
        # Evaluate answer
        answer_results = self.answer_metrics.evaluate_answer(
            answer, query, context, retrieved_docs, ground_truth
        )
        
        # Compile results
        evaluation_result = {
            "evaluation_id": evaluation_id,
            "timestamp": timestamp.isoformat(),
            "query": query,
            "retrieval_metrics": retrieval_results,
            "answer_metrics": answer_results,
            "num_retrieved": len(retrieved_docs),
            "num_relevant": len(relevant_docs)
        }
        
        self.evaluation_history.append(evaluation_result)
        
        logger.info(f"Evaluation completed for query: {query[:50]}...")
        
        return evaluation_result
    
    def evaluate_batch(self, queries_data: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Evaluate a batch of queries
        
        Args:
            queries_data: List of dicts with query, retrieved_docs, relevant_docs, answer, context
            
        Returns:
            Batch evaluation summary
        """
        batch_results = []
        
        for query_data in queries_data:
            result = self.evaluate_rag_query(
                query=query_data.get("query", ""),
                retrieved_docs=query_data.get("retrieved_docs", []),
                relevant_docs=query_data.get("relevant_docs", set()),
                answer=query_data.get("answer", ""),
                context=query_data.get("context", ""),
                ground_truth=query_data.get("ground_truth"),
                relevance_scores=query_data.get("relevance_scores")
            )
            batch_results.append(result)
        
        # Calculate batch averages
        avg_retrieval = self._average_retrieval_metrics(batch_results)
        avg_answer = self._average_answer_metrics(batch_results)
        
        return {
            "num_queries": len(batch_results),
            "avg_retrieval_metrics": avg_retrieval,
            "avg_answer_metrics": avg_answer,
            "individual_results": batch_results
        }
    
    def _average_retrieval_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, float]:
        """Calculate average retrieval metrics across results"""
        if not results:
            return {}
        
        metrics = {}
        metric_keys = results[0]["retrieval_metrics"].keys()
        
        for key in metric_keys:
            values = [r["retrieval_metrics"][key] for r in results if key in r["retrieval_metrics"]]
            if values:
                metrics[key] = float(sum(values) / len(values))
        
        return metrics
    
    def _average_answer_metrics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculate average answer metrics across results"""
        if not results:
            return {}
        
        metrics = {}
        answer_metrics = results[0]["answer_metrics"].keys()
        
        for key in answer_metrics:
            if key == "length_stats":
                continue  # Skip complex nested structure
            values = [r["answer_metrics"][key] for r in results if key in r["answer_metrics"] and r["answer_metrics"][key] is not None]
            if values:
                metrics[key] = float(sum(values) / len(values))
        
        # Calculate hallucination rate
        hallucinated_count = sum(1 for r in results if r["answer_metrics"].get("hallucinated", False))
        metrics["hallucination_rate"] = float(hallucinated_count / len(results))
        
        return metrics
    
    def track_llm_call(self, provider: str, model: str, input_tokens: int, 
                      output_tokens: int, latency_ms: float, cost: Optional[float] = None) -> Dict[str, Any]:
        """Track an LLM API call"""
        return self.cost_tracker.track_api_call(provider, model, input_tokens, output_tokens, latency_ms, cost)
    
    def track_embedding_call(self, provider: str, model: str, num_texts: int,
                           total_tokens: int, latency_ms: float) -> Dict[str, Any]:
        """Track an embedding API call"""
        return self.cost_tracker.track_embedding_call(provider, model, num_texts, total_tokens, latency_ms)
    
    def get_comprehensive_summary(self) -> Dict[str, Any]:
        """Get comprehensive evaluation summary including all metrics"""
        return {
            "retrieval_summary": {
                "queries_evaluated": self.retrieval_metrics.queries_evaluated,
                "avg_retrieved_per_query": self.retrieval_metrics.total_retrieved / max(self.retrieval_metrics.queries_evaluated, 1),
                "avg_relevant_per_query": self.retrieval_metrics.total_relevant / max(self.retrieval_metrics.queries_evaluated, 1)
            },
            "answer_summary": self.answer_metrics.get_average_metrics(),
            "cost_summary": self.cost_tracker.get_summary(),
            "evaluation_count": len(self.evaluation_history),
            "timestamp": datetime.now().isoformat()
        }
    
    def get_evaluation_history(self, limit: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get evaluation history, optionally limited"""
        if limit:
            return self.evaluation_history[-limit:]
        return self.evaluation_history
    
    def reset(self):
        """Reset all evaluation data"""
        self.retrieval_metrics.reset()
        self.answer_metrics.reset()
        self.cost_tracker.reset()
        self.evaluation_history = []
        logger.info("Evaluation manager reset")
