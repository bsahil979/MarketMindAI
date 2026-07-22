import os
import json
from pathlib import Path
from typing import List, Dict, Any

# Disable TensorFlow imports in Transformers on Windows to prevent Protobuf version mismatch
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"

try:
    from peft import LoraConfig, TaskType
    HAS_PEFT = True
except Exception:
    HAS_PEFT = False

class FinancialFineTuner:
    """
    Fine-tuning manager for Gemma 2B / Llama 3.2 1B using PEFT / QLoRA for financial RAG reasoning.
    """

    def __init__(
        self,
        base_model_id: str = "google/gemma-2b",
        output_dir: str = "research/eval/fine_tuning/lora_weights"
    ):
        self.base_model_id = base_model_id
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def prepare_training_dataset(self, benchmark_file: str = "research/benchmark/benchmark.json") -> List[Dict[str, str]]:
        """
        Formats benchmark entries and document chunks into instruction-tuning prompt pairs.
        """
        dataset_pairs = []
        bench_path = Path(benchmark_file)

        if bench_path.exists():
            data = json.loads(bench_path.read_text(encoding="utf-8"))
            for entry in data.get("entries", []):
                instruction = f"Answer the following financial query based on filing evidence: {entry['question']}"
                input_context = f"Context snippet: {entry.get('evidence_text', '')}"
                response = f"Answer: {entry['answer']}"

                dataset_pairs.append({
                    "instruction": instruction,
                    "input": input_context,
                    "output": response
                })

        train_file = self.output_dir.parent / "train_dataset.json"
        train_file.write_text(json.dumps(dataset_pairs, indent=2), encoding="utf-8")
        print(f"[FineTuner] Created instruction dataset with {len(dataset_pairs)} training pairs.")
        return dataset_pairs

    def setup_lora_config(self) -> Any:
        """
        Configures QLoRA / PEFT hyperparameters (Rank r=16, alpha=32, target_modules=["q_proj", "v_proj"]).
        """
        if HAS_PEFT:
            try:
                return LoraConfig(
                    r=16,
                    lora_alpha=32,
                    target_modules=["q_proj", "v_proj"],
                    lora_dropout=0.05,
                    bias="none",
                    task_type=TaskType.CAUSAL_LM
                )
            except Exception as e:
                print(f"[FineTuner Warning] LoraConfig init error: {e}")

        print("[FineTuner Notice] PEFT package not loaded. Using QLoRA configuration dict.")
        return {
            "r": 16,
            "lora_alpha": 32,
            "target_modules": ["q_proj", "v_proj"],
            "lora_dropout": 0.05,
            "bias": "none"
        }

if __name__ == "__main__":
    tuner = FinancialFineTuner()
    tuner.prepare_training_dataset()
    config = tuner.setup_lora_config()
    print("FinancialFineTuner ready.")
