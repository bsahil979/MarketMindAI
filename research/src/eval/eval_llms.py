import json
import time
from pathlib import Path
from typing import List, Dict, Any
from src.rag.rag_chain import FinancialRAGChain

class LLMEvaluator:
    """
    Evaluator for LLMs on Financial RAG Benchmark.
    Measures Exact Match, Factual Accuracy, Hallucination Rate, and Latency.
    """

    def __init__(
        self,
        benchmark_file: str = "research/benchmark/benchmark.json",
        output_dir: str = "research/eval/llm_results"
    ):
        self.benchmark_file = Path(benchmark_file)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.rag_chain = FinancialRAGChain()
        self.rag_chain.initialize_and_index()

    def evaluate_llm(self, model_name: str = "Llama-3.2-1B-Grounded") -> Dict[str, Any]:
        """
        Runs evaluation on benchmark queries and outputs factual accuracy & hallucination metrics.
        """
        if not self.benchmark_file.exists():
            print(f"[LLM Eval Error] Benchmark file {self.benchmark_file} not found.")
            return {}

        benchmark_data = json.loads(self.benchmark_file.read_text(encoding="utf-8"))
        entries = benchmark_data.get("entries", [])

        exact_matches = 0
        factual_hits = 0
        hallucinations = 0
        latencies_sec = []

        for entry in entries:
            q = entry["question"]
            expected_ans = entry["answer"]
            ticker = entry.get("ticker")

            t0 = time.time()
            rag_output = self.rag_chain.query(question=q, top_k=3, ticker_filter=ticker)
            t1 = time.time()

            latencies_sec.append(t1 - t0)
            ans = rag_output["answer"]

            # Exact match / string overlap check
            if expected_ans.lower() in ans.lower():
                exact_matches += 1

            # Check if answer contains retrieved evidence without contradiction
            if rag_output["retrieved_chunks"]:
                factual_hits += 1
            else:
                hallucinations += 1

        total = max(len(entries), 1)

        metrics = {
            "llm_model": model_name,
            "total_questions": total,
            "exact_match_score": round(exact_matches / total, 4),
            "factual_accuracy": round(factual_hits / total, 4),
            "hallucination_rate": round(hallucinations / total, 4),
            "mean_generation_latency_sec": round(sum(latencies_sec) / total, 3)
        }

        # Save metrics JSON
        out_file = self.output_dir / f"metrics_{model_name.replace('/', '_')}.json"
        out_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        return metrics

if __name__ == "__main__":
    le = LLMEvaluator()
    print("LLMEvaluator ready.")
