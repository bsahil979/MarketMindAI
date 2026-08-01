"""
Evaluation Routes - API endpoints for system evaluation and metrics
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Set, Dict, Any
from app.evaluation import EvaluationManager

router = APIRouter(prefix="", tags=["evaluation"])

# Global evaluation manager
evaluation_manager = EvaluationManager()

class EvaluationQuerySchema(BaseModel):
    query: str
    retrieved_docs: List[str]
    relevant_docs: Set[str]
    answer: str
    context: str
    ground_truth: Optional[str] = None
    relevance_scores: Optional[Dict[str, float]] = None

class BatchEvaluationSchema(BaseModel):
    queries: List[EvaluationQuerySchema]

class LLMAPIUsageSchema(BaseModel):
    provider: str
    model: str
    input_tokens: int
    output_tokens: int
    latency_ms: float
    cost: Optional[float] = None

class EmbeddingUsageSchema(BaseModel):
    provider: str
    model: str
    num_texts: int
    total_tokens: int
    latency_ms: float

@router.post("/api/v1/evaluation/rag-query")
def evaluate_rag_query(payload: EvaluationQuerySchema):
    """Evaluate a single RAG query with comprehensive metrics"""
    try:
        result = evaluation_manager.evaluate_rag_query(
            query=payload.query,
            retrieved_docs=payload.retrieved_docs,
            relevant_docs=payload.relevant_docs,
            answer=payload.answer,
            context=payload.context,
            ground_truth=payload.ground_truth,
            relevance_scores=payload.relevance_scores
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/evaluation/batch")
def evaluate_batch(payload: BatchEvaluationSchema):
    """Evaluate a batch of RAG queries"""
    try:
        queries_data = [q.dict() for q in payload.queries]
        result = evaluation_manager.evaluate_batch(queries_data)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/evaluation/track-llm")
def track_llm_call(payload: LLMAPIUsageSchema):
    """Track an LLM API call for cost and usage metrics"""
    try:
        result = evaluation_manager.track_llm_call(
            provider=payload.provider,
            model=payload.model,
            input_tokens=payload.input_tokens,
            output_tokens=payload.output_tokens,
            latency_ms=payload.latency_ms,
            cost=payload.cost
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/evaluation/track-embedding")
def track_embedding_call(payload: EmbeddingUsageSchema):
    """Track an embedding API call for cost and usage metrics"""
    try:
        result = evaluation_manager.track_embedding_call(
            provider=payload.provider,
            model=payload.model,
            num_texts=payload.num_texts,
            total_tokens=payload.total_tokens,
            latency_ms=payload.latency_ms
        )
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/evaluation/summary")
def get_evaluation_summary():
    """Get comprehensive evaluation summary"""
    try:
        return evaluation_manager.get_comprehensive_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/evaluation/history")
def get_evaluation_history(limit: Optional[int] = None):
    """Get evaluation history, optionally limited"""
    try:
        return evaluation_manager.get_evaluation_history(limit=limit)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/api/v1/evaluation/reset")
def reset_evaluation():
    """Reset all evaluation data"""
    try:
        evaluation_manager.reset()
        return {"message": "Evaluation data reset successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/evaluation/costs")
def get_cost_breakdown():
    """Get detailed cost breakdown"""
    try:
        return evaluation_manager.cost_tracker.get_summary()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/evaluation/retrieval-metrics")
def get_retrieval_metrics():
    """Get retrieval quality metrics"""
    try:
        return {
            "queries_evaluated": evaluation_manager.retrieval_metrics.queries_evaluated,
            "total_retrieved": evaluation_manager.retrieval_metrics.total_retrieved,
            "total_relevant": evaluation_manager.retrieval_metrics.total_relevant
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/api/v1/evaluation/answer-metrics")
def get_answer_metrics():
    """Get answer quality metrics"""
    try:
        return evaluation_manager.answer_metrics.get_average_metrics()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
