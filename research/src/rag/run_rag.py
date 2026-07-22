import sys
import json
from pathlib import Path

# Ensure python can import from current package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.rag.rag_chain import FinancialRAGChain

def run_phase3_rag(
    chunks_dir: str = "research/dataset/chunks",
    benchmark_file: str = "research/benchmark/benchmark.json"
):
    """
    Executes Phase 3: Vector Store & RAG Pipeline:
    1. Indexes dataset chunks into persistent ChromaDB Vector Store.
    2. Runs test financial queries through Hybrid Semantic Retriever & Prompt Engine.
    """
    print("==========================================================")
    print("  Portfolio Advisor AI - Phase 3 Vector Store & RAG       ")
    print("==========================================================")

    rag_chain = FinancialRAGChain(chunks_dir=chunks_dir)
    indexed_count = rag_chain.initialize_and_index()
    print(f"[Phase 3] Total chunks indexed into ChromaDB Vector Store: {indexed_count}")

    # Load sample questions from benchmark.json if available
    bench_path = Path(benchmark_file)
    test_questions = []

    if bench_path.exists():
        try:
            data = json.loads(bench_path.read_text(encoding="utf-8"))
            entries = data.get("entries", [])
            for e in entries[:3]:
                test_questions.append((e["question"], e.get("ticker")))
        except Exception:
            pass

    if not test_questions:
        test_questions = [
            ("What was AAPL's Services revenue in 2024?", "AAPL"),
            ("What primary risk factors are highlighted for AAPL?", "AAPL")
        ]

    print("\n--- Running Sample Financial RAG Queries ---")
    for idx, (question, ticker) in enumerate(test_questions, start=1):
        print(f"\n[Query #{idx}] Question: {question} (Ticker: {ticker})")
        res = rag_chain.query(question=question, top_k=2, ticker_filter=ticker)
        print(f"  Retrieved Chunks Count : {len(res['retrieved_chunks'])}")
        if res["retrieved_chunks"]:
            top_meta = res["retrieved_chunks"][0].get("metadata", {})
            print(f"  Top Match Chunk ID     : {res['retrieved_chunks'][0].get('chunk_id')}")
            print(f"  Top Match Ticker       : {top_meta.get('ticker')}")
        print(f"\n  Answer Summary:\n  {res['answer']}")
        print("-" * 60)

    print("\n==========================================================")
    print("  Phase 3 Vector Store & RAG Pipeline Completed!         ")
    print("==========================================================")

if __name__ == "__main__":
    run_phase3_rag()
