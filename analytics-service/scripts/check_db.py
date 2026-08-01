from app.database import SessionLocal, FactAgentEvaluation, FactAgentRetrieval, init_db
from sqlalchemy import func

if __name__ == '__main__':
    init_db()
    db = SessionLocal()
    try:
        eval_count = db.query(func.count(FactAgentEvaluation.eval_id)).scalar()
        retr_count = db.query(func.count(FactAgentRetrieval.retrieval_id)).scalar()
        print('Evaluations count:', eval_count)
        print('Retrievals count:', retr_count)
        rows = db.query(FactAgentEvaluation).order_by(FactAgentEvaluation.created_at.desc()).limit(5).all()
        for r in rows:
            print('eval', r.eval_id, getattr(r,'ticker',None), r.created_at, r.correct_at_1, r.correct_at_5, r.latency_ms)
        rows2 = db.query(FactAgentRetrieval).order_by(FactAgentRetrieval.created_at.desc()).limit(5).all()
        for r in rows2:
            print('retr', r.retrieval_id, r.eval_id, r.rank, r.doc_id, r.is_relevant, r.similarity_score)
    finally:
        db.close()
