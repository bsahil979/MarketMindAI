import json
import time
import re
from pathlib import Path
from datetime import datetime
from app.agent.agent_engine import FinancialAgent
from app.database import init_db, SessionLocal, FactAgentEvaluation

BENCH_PATH = Path(__file__).resolve().parents[2] / 'research' / 'benchmark' / 'benchmark.json'


def normalize_text(s: str) -> str:
    if not s:
        return ""
    s = s.lower()
    s = re.sub(r"[^a-z0-9$.%]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


def evaluate_answer(pred: str, ground: str) -> (int, int):
    """Return (correct_at_1, correct_at_5) using simple substring matching."""
    n_pred = normalize_text(pred)
    n_ground = normalize_text(ground)
    if not n_ground:
        return 0, 0
    if n_ground in n_pred:
        return 1, 1
    # attempt numeric fuzzy match: extract digits and compare
    digits_ground = re.sub(r"[^0-9.\-]", "", n_ground)
    digits_pred = re.sub(r"[^0-9.\-]", "", n_pred)
    if digits_ground and digits_ground in digits_pred:
        return 1, 1
    return 0, 0


def run_benchmark(limit: int = None):
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

    for e in entries:
        qid = e.get('id')
        question = e.get('question')
        ground = e.get('ground_truth') or e.get('answer')
        ticker = e.get('ticker')

        start = time.time()
        try:
            res = agent.run_agent(question, ticker=ticker)
        except Exception as ex:
            print(f"Agent failed for {qid}: {ex}")
            continue
        elapsed = time.time() - start

        # Prefer professional response for evaluation
        pred = res.get('response_professional') or res.get('response_eli10') or ''

        correct_at_1, correct_at_5 = evaluate_answer(pred, ground)

        eval_metrics = res.get('evaluation_metrics', {}) or {}
        faith = float(eval_metrics.get('faithfulness_score') or 0.0)
        # mark hallucination if faithfulness is low
        hallucinated = 1 if faith < 0.8 else 0
        latency_ms = int(round((eval_metrics.get('latency_seconds') or elapsed) * 1000))

        record = FactAgentEvaluation(
            question_id=qid,
            predicted_answer=pred[:2000] if pred else '',
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
        print(f"Recorded {qid}: correct@1={correct_at_1}, correct@5={correct_at_5}, faith={faith}, latency_ms={latency_ms}")

    db.close()
    print("Benchmark run complete.")


if __name__ == '__main__':
    run_benchmark(limit=50)  # limit default to 50 for quick runs
