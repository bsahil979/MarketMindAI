import json
import time
from pathlib import Path
from typing import List, Dict, Any
from src.rag.embeddings import FinancialEmbeddings
from src.rag.vectordb import VectorStoreManager

class EmbeddingEvaluator:
    """
    Evaluator for embedding models on Financial RAG benchmark.
    Measures Recall@K, Precision@K, MRR, and Retrieval Latency.
    """

    def __init__(
        self,
        benchmark_file: str = "research/benchmark/benchmark.json",
        chunks_dir: str = "research/dataset/chunks",
        output_dir: str = "research/eval/embedding_results"
    ):
        self.benchmark_file = Path(benchmark_file)
        self.chunks_dir = Path(chunks_dir)
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def evaluate_model(self, model_name: str = "BAAI/bge-small-en-v1.5") -> Dict[str, Any]:
        """
        Runs retrieval evaluation for a specific embedding model on benchmark questions.
        """
        if not self.benchmark_file.exists():
            print(f"[Embedding Eval Error] Benchmark file {self.benchmark_file} not found.")
            return {}

        benchmark_data = json.loads(self.benchmark_file.read_text(encoding="utf-8"))
        entries = benchmark_data.get("entries", [])

        embedder = FinancialEmbeddings(model_name=model_name)
        vsm = VectorStoreManager(
            persist_dir=f"research/eval/embedding_results/vdb_{model_name.replace('/', '_')}",
            collection_name="eval_collection",
            embedder=embedder
        )

        # Index dataset chunks
        chunks = []
        for file_path in self.chunks_dir.glob("*_chunks.json"):
            chunks.extend(json.loads(file_path.read_text(encoding="utf-8")))

        vsm.index_chunks(chunks)

        recall_at_1 = 0
        recall_at_3 = 0
        recall_at_5 = 0
        reciprocal_ranks = []
        latencies_ms = []

        for entry in entries:
            q = entry["question"]
            target_file = entry.get("source_file", "")
            target_doc_id = entry.get("document_id", "")

            t0 = time.time()
            results = vsm.similarity_search(query=q, top_k=5, ticker_filter=entry.get("ticker"))
            t1 = time.time()

            latencies_ms.append((t1 - t0) * 1000.0)

            retrieved_doc_ids = [r.get("metadata", {}).get("document_id", "") for r in results]

            # Check hits
            if target_doc_id in retrieved_doc_ids[:1]:
                recall_at_1 += 1
            if target_doc_id in retrieved_doc_ids[:3]:
                recall_at_3 += 1
            if target_doc_id in retrieved_doc_ids[:5]:
                recall_at_5 += 1

            # MRR
            if target_doc_id in retrieved_doc_ids:
                rank = retrieved_doc_ids.index(target_doc_id) + 1
                reciprocal_ranks.append(1.0 / rank)
            else:
                reciprocal_ranks.append(0.0)

        total = max(len(entries), 1)

        metrics = {
            "model_name": model_name,
            "total_benchmark_questions": total,
            "recall_at_1": round(recall_at_1 / total, 4),
            "recall_at_3": round(recall_at_3 / total, 4),
            "recall_at_5": round(recall_at_5 / total, 4),
            "mrr": round(sum(reciprocal_ranks) / total, 4),
            "mean_latency_ms": round(sum(latencies_ms) / total, 2)
        }

        # Save metrics JSON
        out_file = self.output_dir / f"metrics_{model_name.replace('/', '_')}.json"
        out_file.write_text(json.dumps(metrics, indent=2), encoding="utf-8")

        return metrics

if __name__ == "__main__":
    ee = EmbeddingEvaluator()
    print("EmbeddingEvaluator ready.")
