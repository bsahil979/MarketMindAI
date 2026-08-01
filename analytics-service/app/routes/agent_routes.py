import math
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import func
from sqlalchemy.orm import Session
from typing import List, Optional

from app.database import get_db, engine, FactAgentEvaluation, FactAgentRetrieval, ModelRegistry
from app.semantic import semantic_similarity

router = APIRouter(prefix="", tags=["agent"])

SEMANTIC_THRESHOLD = float(__import__('os').getenv('SEMANTIC_THRESHOLD', '0.75'))


class AgentQuerySchema(BaseModel):
    query: str
    ticker: Optional[str] = None


class PortfolioQuerySchema(BaseModel):
    capital: float = 100000.0
    risk_profile: str = "Moderate"
    duration_years: int = 5


class CompareQuerySchema(BaseModel):
    tickers: List[str]


@router.post("/api/v1/agent/query")
def run_agent_query(payload: AgentQuerySchema):
    from app.agent.agent_engine import FinancialAgent
    from app.routes.rag_routes import rag_retriever, llm_interface
    
    # Use enhanced agent with RAG if available
    if rag_retriever and llm_interface:
        agent = FinancialAgent(rag_retriever=rag_retriever, llm_interface=llm_interface)
    else:
        agent = FinancialAgent()
    
    return agent.run_agent(payload.query, payload.ticker, use_planner=True)


@router.post("/api/v1/agent/compare")
def run_agent_compare(payload: CompareQuerySchema):
    from app.agent.financial_calculator import get_company_metrics_summary
    results = []
    for t in payload.tickers:
        results.append(get_company_metrics_summary(t))
    return {"comparison": results}


@router.post("/api/v1/agent/portfolio")
def run_agent_portfolio(payload: PortfolioQuerySchema):
    from app.agent.agent_engine import generate_portfolio_recommendation
    return generate_portfolio_recommendation(payload.capital, payload.risk_profile, payload.duration_years)


@router.get("/api/v1/agent/metrics")
def get_agent_metrics(db: Session = Depends(get_db)):
    total = db.query(func.count(FactAgentEvaluation.eval_id)).scalar() or 0

    if total == 0:
        return {
            "accuracy": 0.0,
            "semantic_accuracy": 0.0,
            "faithfulness_score": 0.0,
            "hallucination_rate": 0.0,
            "avg_latency_ms": 0.0,
            "precision_at_5": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "ndcg_at_5": 0.0,
            "eval_sample_count": 0,
            "benchmark_dataset": "SEC 10-K & 10-Q FinancialQA Benchmark"
        }

    try:
        import logging
        logging.getLogger('marketmind.main').info(f"DB engine url: {str(engine.url)}")
        print(f"[DEBUG] DB engine url: {str(engine.url)}")
    except Exception:
        pass

    avg_latency_ms = db.query(func.coalesce(func.avg(FactAgentEvaluation.latency_ms), 0)).scalar() or 0
    faithfulness_score = db.query(func.coalesce(func.avg(FactAgentEvaluation.faithfulness_score), 0)).scalar() or 0
    hallucinated_count = db.query(func.coalesce(func.sum(FactAgentEvaluation.hallucinated), 0)).scalar() or 0
    hallucination_rate = float(hallucinated_count) / float(total) if total > 0 else 0.0

    eval_rows = db.query(FactAgentEvaluation).all()
    semantic_correct = 0
    correct_top1_sum = 0
    semantic_sims = []
    for rec in eval_rows:
        try:
            sim = semantic_similarity((rec.predicted_answer or ''), (rec.ground_truth or ''))
        except Exception:
            sim = 0.0
        semantic_sims.append(sim)
        if sim >= SEMANTIC_THRESHOLD:
            semantic_correct += 1
        correct_top1_sum += int(rec.correct_at_1 or 0)

    accuracy = float(correct_top1_sum) / float(total) if total > 0 else 0.0
    semantic_accuracy = float(semantic_correct) / float(total) if total > 0 else 0.0

    eval_ids = [r[0] for r in db.query(FactAgentRetrieval.eval_id).distinct().all()]
    if not eval_ids:
        return {
            "faithfulness_score": round(float(faithfulness_score), 4) if faithfulness_score else 0.0,
            "hallucination_rate": round(hallucination_rate, 4),
            "avg_latency_ms": round(float(avg_latency_ms), 3),
            "precision_at_5": 0.0,
            "recall_at_5": 0.0,
            "mrr": 0.0,
            "ndcg_at_5": 0.0,
            "eval_sample_count": int(total),
            "benchmark_dataset": "SEC 10-K & 10-Q FinancialQA Benchmark"
        }

    precisions = []
    recalls = []
    rr_list = []
    ndcg_list = []

    for eid in eval_ids:
        rows = db.query(FactAgentRetrieval).filter_by(eval_id=eid).order_by(FactAgentRetrieval.rank.asc()).limit(5).all()
        if not rows:
            precisions.append(0.0)
            recalls.append(0.0)
            rr_list.append(0.0)
            ndcg_list.append(0.0)
            continue

        rels = [1 if (r.is_relevant and int(r.is_relevant) == 1) else 0 for r in rows]
        relevant_count = sum(rels)
        precisions.append(float(relevant_count) / 5.0)
        recalls.append(1.0 if relevant_count > 0 else 0.0)

        first_rank = 0
        for i, rrel in enumerate(rels, start=1):
            if rrel:
                first_rank = i
                break
        rr_list.append((1.0 / first_rank) if first_rank > 0 else 0.0)

        dcg = 0.0
        for i, rrel in enumerate(rels, start=1):
            if rrel:
                dcg += (2 ** rrel - 1) / math.log2(i + 1)
        ideal_rels = min(sum(rels), 5)
        idcg = 0.0
        for i in range(1, ideal_rels + 1):
            idcg += (2 ** 1 - 1) / math.log2(i + 1)
        ndcg = (dcg / idcg) if idcg > 0 else 0.0
        ndcg_list.append(ndcg)

    count_evals = len(eval_ids)
    precision_at_5 = float(sum(precisions) / count_evals) if count_evals else 0.0
    recall_at_5 = float(sum(recalls) / count_evals) if count_evals else 0.0
    mrr = float(sum(rr_list) / count_evals) if count_evals else 0.0
    ndcg_at_5 = float(sum(ndcg_list) / count_evals) if count_evals else 0.0

    return {
        "accuracy": round(accuracy, 4),
        "semantic_accuracy": round(semantic_accuracy, 4),
        "faithfulness_score": round(float(faithfulness_score), 4) if faithfulness_score else 0.0,
        "hallucination_rate": round(hallucination_rate, 4),
        "avg_latency_ms": round(float(avg_latency_ms), 3),
        "precision_at_5": round(precision_at_5, 4),
        "recall_at_5": round(recall_at_5, 4),
        "mrr": round(mrr, 4),
        "ndcg_at_5": round(ndcg_at_5, 4),
        "eval_sample_count": int(total),
        "benchmark_dataset": "SEC 10-K & 10-Q FinancialQA Benchmark"
    }


@router.get("/api/v1/agent/evaluations/{eval_id}")
def get_evaluation_detail(eval_id: int, db: Session = Depends(get_db)):
    rec = db.query(FactAgentEvaluation).filter_by(eval_id=eval_id).first()
    if not rec:
        raise HTTPException(status_code=404, detail=f"Evaluation id {eval_id} not found")
    try:
        sim = semantic_similarity((rec.predicted_answer or ''), (rec.ground_truth or ''))
    except Exception:
        sim = 0.0
    return {
        "eval_id": rec.eval_id,
        "question_id": rec.question_id,
        "predicted_answer": rec.predicted_answer,
        "ground_truth": rec.ground_truth,
        "correct_at_1": int(rec.correct_at_1 or 0),
        "correct_at_5": int(rec.correct_at_5 or 0),
        "faithfulness_score": float(rec.faithfulness_score or 0.0),
        "hallucinated": int(rec.hallucinated or 0),
        "latency_ms": int(rec.latency_ms or 0),
        "semantic_similarity": float(sim)
    }


@router.get("/api/v1/agent/retrievals/{eval_id}")
def get_retrievals_for_eval(eval_id: int, db: Session = Depends(get_db)):
    rows = db.query(FactAgentRetrieval).filter_by(eval_id=eval_id).order_by(FactAgentRetrieval.rank.asc()).all()
    if not rows:
        raise HTTPException(status_code=404, detail=f"No retrievals found for eval_id {eval_id}")
    return [
        {
            "retrieval_id": r.retrieval_id,
            "eval_id": r.eval_id,
            "rank": r.rank,
            "doc_id": r.doc_id,
            "snippet": r.snippet,
            "is_relevant": int(r.is_relevant) if r.is_relevant is not None else None,
            "similarity_score": float(r.similarity_score) if r.similarity_score is not None else None
        }
        for r in rows
    ]
