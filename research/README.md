# Portfolio Advisor AI Research Documentation & Codebase

This package contains the complete research documentation, pipeline source code, datasets, benchmarks, vector database, and evaluation suite for **Portfolio Advisor AI** built on top of MarketMind AI.

## Research Documents
- [00_Research_Design_Specification.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/00_Research_Design_Specification.md) - Research Roadmap & Questions
- [01_Financial_Dataset_Documentation.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/01_Financial_Dataset_Documentation.md) - Financial Corpus Specification
- [08_Research_Paper.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/08_Research_Paper.md) - Academic Paper Draft (12 Sections)
- [09_Complete_Implementation_Guide.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/09_Complete_Implementation_Guide.md) - End-to-End Developer Guide

## Executable Pipeline Modules (`src/`)
- `src/data_pipeline/`: Phase 1 - Ingestion, HTML table-aware parsing, metadata, 512-token chunking.
- `src/benchmark/`: Phase 2 - 5-category QA generator, schema validator, evidence exporter.
- `src/rag/`: Phase 3 - ChromaDB vector store, Hybrid Semantic Retriever (Dense + BM25 RRF), prompt engine.
- `src/eval/`: Phase 4 - Embedding evaluator (`Recall@K`, `MRR`), LLM evaluator (`Factual Accuracy`), and runner.
- `src/fine_tuning/`: Phase 4 - QLoRA instruction dataset builder & PEFT training config.
