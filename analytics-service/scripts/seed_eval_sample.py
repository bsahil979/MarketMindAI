from app.database import SessionLocal, init_db, FactAgentEvaluation
from datetime import datetime


def seed_sample():
    init_db()
    db = SessionLocal()
    samples = [
        {"question_id": "bench_0001", "predicted_answer": "$34798 Million", "ground_truth": "$34798 Million", "correct_at_5": 1, "correct_at_1": 1, "faithfulness_score": 0.99, "hallucinated": 0, "latency_ms": 1200},
        {"question_id": "bench_0002", "predicted_answer": "$22798 Million", "ground_truth": "$22798 Million", "correct_at_5": 1, "correct_at_1": 1, "faithfulness_score": 0.97, "hallucinated": 0, "latency_ms": 1100},
        {"question_id": "bench_0003", "predicted_answer": "2023: $34298M, 2024: $34798M", "ground_truth": "2023: $34298M, 2024: $34798M", "correct_at_5": 2, "correct_at_1": 0, "faithfulness_score": 0.95, "hallucinated": 0, "latency_ms": 1500},
        {"question_id": "bench_0004", "predicted_answer": "YoY Growth Rate: Increased by $500.0M (+1.46%)", "ground_truth": "YoY Growth Rate: Increased by $500.0M (+1.46%)", "correct_at_5": 1, "correct_at_1": 1, "faithfulness_score": 0.96, "hallucinated": 0, "latency_ms": 1400},
        {"question_id": "bench_0005", "predicted_answer": "$22798 Million (approx)", "ground_truth": "$22798 Million", "correct_at_5": 0, "correct_at_1": 0, "faithfulness_score": 0.6, "hallucinated": 1, "latency_ms": 900},
    ]

    for s in samples:
        ev = FactAgentEvaluation(
            question_id=s["question_id"],
            predicted_answer=s["predicted_answer"],
            ground_truth=s.get("ground_truth"),
            correct_at_5=s.get("correct_at_5", 0),
            correct_at_1=s.get("correct_at_1", 0),
            faithfulness_score=s.get("faithfulness_score", 0.0),
            hallucinated=s.get("hallucinated", 0),
            latency_ms=s.get("latency_ms", 0),
            created_at=datetime.now()
        )
        db.add(ev)
    db.commit()
    db.close()
    print("Seeded sample evaluation records.")


if __name__ == '__main__':
    seed_sample()
