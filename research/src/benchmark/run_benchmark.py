import sys
from pathlib import Path

# Ensure python can import from current package
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent))

from src.benchmark.generator import BenchmarkGenerator

def run_phase2_benchmark(
    dataset_dir: str = "research/dataset",
    output_dir: str = "research/benchmark"
):
    """
    Executes Phase 2: Benchmark Dataset Construction:
    1. Scans processed documents & chunks from Phase 1.
    2. Synthesizes ground-truth financial QA benchmark entries.
    3. Saves benchmark.json, evidence snippets, and annotation summaries.
    """
    print("==========================================================")
    print("  Portfolio Advisor AI - Phase 2 Benchmark Construction   ")
    print("==========================================================")

    generator = BenchmarkGenerator(dataset_dir=dataset_dir, output_dir=output_dir)
    dataset = generator.generate_benchmark()

    print("\n==========================================================")
    print("  Phase 2 Benchmark Construction Completed Successfully!  ")
    print("==========================================================")
    print(f"  - Total Benchmark Questions : {dataset.total_entries}")
    print(f"  - Version                   : {dataset.version}")
    print("  - Category Distribution:")
    for cat, count in dataset.category_counts.items():
        print(f"      * {cat:<15}: {count} questions")
    print(f"  - Main Benchmark File       : {Path(output_dir).resolve() / 'benchmark.json'}")
    print(f"  - Evidence Directory        : {Path(output_dir).resolve() / 'evidence'}")
    print(f"  - Annotations Directory     : {Path(output_dir).resolve() / 'annotations'}")

if __name__ == "__main__":
    run_phase2_benchmark()
