import json
import time
import re
from pathlib import Path
from datetime import datetime
from difflib import SequenceMatcher
import json
import os

from app.agent.agent_engine import FinancialAgent
from app.agent.advanced_retriever import hybrid_retrieve
from app.database import init_db, SessionLocal, FactAgentEvaluation, FactAgentRetrieval
from app.semantic import semantic_similarity

# Configurable semantic threshold via environment variable
SEMANTIC_THRESHOLD = float(os.getenv("SEMANTIC_THRESHOLD", "0.75"))

BENCH_PATH = Path(__file__).resolve().parents[2] / 'research' / 'benchmark' / 'benchmark.json'


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9$.%]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def fuzzy_match(a: str, b: str, threshold: float = 0.85) -> bool:
    if not a or not b:
        return False
    a_n = normalize_text(a)
    b_n = normalize_text(b)
    if b_n in a_n or a_n in b_n:
        return True
    digits_a = re.sub(r"[^0-9.\-]", "", a_n)
    digits_b = re.sub(r"[^0-9.\-]", "", b_n)
    if digits_b and digits_b in digits_a:
        return True
    ratio = SequenceMatcher(None, a_n, b_n).ratio()
    return ratio >= threshold


def evaluate_answer(pred: str, ground: str) -> (int, int):
    if not ground:
        return 0, 0
    correct1 = 1 if fuzzy_match(pred or "", ground or "") else 0
    return correct1, correct1


def run_benchmark(limit: int = None, top_k: int = 5, run_agent_answers: bool = True):
    if not BENCH_PATH.exists():
        print(f"Benchmark file not found at {BENCH_PATH}")
        return

    with open(BENCH_PATH, 'r', encoding='utf-8') as f:
        bench = json.load(f)

    entries = bench.get('entries', [])
    if limit:
        entries = entries[:limit]

    init_db()
    db = SessionLocal()
    agent = FinancialAgent()

    for idx, e in enumerate(entries, start=1):
        qid = e.get('id')
        question = e.get('question')
        ground = e.get('ground_truth') or e.get('answer')
        ticker = e.get('ticker')

        try:
            retrieved = hybrid_retrieve(question, ticker=ticker, top_k=top_k)
        except Exception as ex:
            print(f"Retrieval failed for {qid}: {ex}")
            retrieved = []

        relevant_count = 0
        # persist retrieval candidates per-question
        retrieval_rows = []
        for rank, r in enumerate(retrieved[:top_k], start=1):
            text_candidates = []
            doc_id = None
            if isinstance(r, dict):
                doc_id = r.get('id') or r.get('doc_id') or r.get('source')
                text_candidates.extend([r.get('evidence_text', ''), r.get('text', ''), r.get('snippet', '')])
            else:
                text_candidates.append(str(r))
            candidate_text = " \n ".join([tc for tc in text_candidates if tc])
            sim = semantic_similarity(candidate_text, ground or "")
            matched = 1 if sim >= SEMANTIC_THRESHOLD else 0
            if matched:
                relevant_count += 1
            retrieval_rows.append({
                'rank': rank,
                'doc_id': doc_id,
                'snippet': candidate_text,
                'is_relevant': int(matched),
                'similarity_score': float(sim)
            })

        start = time.time()
        pred = ''
        eval_metrics = {}
        if run_agent_answers:
            try:
                res = agent.run_agent(question, ticker=ticker)
                pred = res.get('response_professional') or res.get('response_eli10') or ''
                eval_metrics = res.get('evaluation_metrics', {}) or {}
            except Exception as ex:
                print(f"Agent failed for {qid}: {ex}")
        elapsed = time.time() - start

        correct_at_1 = 1 if fuzzy_match(pred or '', ground or '') else 0
        correct_at_5 = relevant_count

        faith = float(eval_metrics.get('faithfulness_score') or 0.0)
        hallucinated = 1 if faith < 0.8 else 0
        latency_ms = int(round((eval_metrics.get('latency_seconds') or elapsed) * 1000))

        record = FactAgentEvaluation(
            question_id=qid,
            predicted_answer=(pred or '')[:2000],
            ground_truth=ground or '',
            correct_at_5=int(correct_at_5),
            correct_at_1=int(correct_at_1),
            faithfulness_score=round(faith, 4),
            hallucinated=int(hallucinated),
            latency_ms=latency_ms,
            created_at=datetime.now()
        )

        db.add(record)
        db.commit()

        # persist retrieval candidates linked to this evaluation
        try:
            for rr in retrieval_rows:
                rr_obj = FactAgentRetrieval(
                    eval_id=record.eval_id,
                    rank=rr['rank'],
                    doc_id=rr['doc_id'],
                    snippet=(rr['snippet'] or '')[:4000],
                    is_relevant=rr['is_relevant'],
                    similarity_score=rr['similarity_score'],
                    created_at=datetime.now()
                )
                db.add(rr_obj)
            db.commit()
        except Exception as e:
            print(f"Failed to persist retrieval rows for {qid}: {e}")

        print(f"[{idx}/{len(entries)}] Recorded {qid}: correct@1={correct_at_1}, correct@5={correct_at_5}/{top_k}, faith={faith}, latency_ms={latency_ms}")

    db.close()
    print("Benchmark run complete.")


if __name__ == '__main__':
    run_benchmark(limit=None, top_k=5, run_agent_answers=True)
