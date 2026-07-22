import sys
from pathlib import Path

# Ensure python can import from current package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.eval.eval_embeddings import EmbeddingEvaluator
from src.eval.eval_llms import LLMEvaluator
from src.fine_tuning.train_lora import FinancialFineTuner

def run_phase4_evaluation():
    """
    Executes Phase 4 Evaluation & Fine-Tuning Suite:
    1. Evaluates Embedding Models on Recall@K, MRR, and Retrieval Latency.
    2. Evaluates LLM Grounded Answers on Exact Match, Factual Accuracy, and Hallucination Rate.
    3. Prepares QLoRA instruction fine-tuning dataset and configuration.
    """
    print("==========================================================")
    print("  Portfolio Advisor AI - Phase 4 Evaluation & Fine-Tuning ")
    print("==========================================================")

    # 1. Embedding Evaluation
    print("\n--- Phase 4.1: Embedding Model Benchmarking ---")
    embed_eval = EmbeddingEvaluator()
    embed_metrics = embed_eval.evaluate_model(model_name="BAAI/bge-small-en-v1.5")
    
    print(f"  Model Name          : {embed_metrics.get('model_name')}")
    print(f"  Recall@1            : {embed_metrics.get('recall_at_1')}")
    print(f"  Recall@3            : {embed_metrics.get('recall_at_3')}")
    print(f"  Recall@5            : {embed_metrics.get('recall_at_5')}")
    print(f"  MRR                 : {embed_metrics.get('mrr')}")
    print(f"  Mean Latency        : {embed_metrics.get('mean_latency_ms')} ms")

    # 2. LLM Evaluation
    print("\n--- Phase 4.2: LLM Grounded Answer Benchmarking ---")
    llm_eval = LLMEvaluator()
    llm_metrics = llm_eval.evaluate_llm(model_name="Llama-3.2-1B-Grounded")

    print(f"  LLM Model           : {llm_metrics.get('llm_model')}")
    print(f"  Exact Match Score   : {llm_metrics.get('exact_match_score')}")
    print(f"  Factual Accuracy    : {llm_metrics.get('factual_accuracy')}")
    print(f"  Hallucination Rate  : {llm_metrics.get('hallucination_rate') * 100}%")
    print(f"  Generation Latency  : {llm_metrics.get('mean_generation_latency_sec')} s")

    # 3. Fine-Tuning Setup
    print("\n--- Phase 4.3: QLoRA Fine-Tuning Setup ---")
    tuner = FinancialFineTuner()
    pairs = tuner.prepare_training_dataset()
    config = tuner.setup_lora_config()
    print(f"  Instruction Pairs   : {len(pairs)}")
    print(f"  LoRA Target Modules : {config.target_modules if hasattr(config, 'target_modules') else config.get('target_modules')}")

    print("\n==========================================================")
    print("  Phase 4 Evaluation & Fine-Tuning Completed!            ")
    print("==========================================================")

if __name__ == "__main__":
    run_phase4_evaluation()
