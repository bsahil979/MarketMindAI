# Portfolio Advisor AI Research Documentation & Codebase

> **Status**: *Research prototype with reproducible evaluation framework.*

This repository contains the documentation, source code, datasets, benchmarks, vector database, and evaluation suite for **Portfolio Advisor AI** built on top of MarketMind AI.

## Key Research Artifacts & Documentation
- [00_Research_Design_Specification.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/00_Research_Design_Specification.md) - Research Roadmap & Design Specification
- [01_Financial_Dataset_Documentation.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/01_Financial_Dataset_Documentation.md) - Corporate Corpus Specification (10 Companies)
- [08_Research_Paper.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/08_Research_Paper.md) - Academic Paper Draft (12 Sections)
- [09_Complete_Implementation_Guide.md](file:///c:/Users/Sahil%20Belchada/Desktop/maybe%20the%20final%20year%20project/research/09_Complete_Implementation_Guide.md) - End-to-End Developer Implementation Guide

## Executable Pipeline Modules (`src/`)
- `src/data_pipeline/`: Phase 1 - Ingestion, HTML table-aware parser, metadata, 512-token chunking.
- `src/benchmark/`: Phase 2 - 5-category QA generator (228 questions across 10 companies), schema validator, evidence exporter.
- `src/rag/`: Phase 3 - ChromaDB vector store, Hybrid Semantic Retriever (Dense + BM25 RRF), grounded prompt engine.
- `src/eval/`: Phase 4 - Embedding evaluator (`Recall@K`, `MRR`), LLM evaluator (`Factual Accuracy`), ablation experiment runner (`run_ablation_study.py`), and QLoRA fine-tuning dataset builder.

## Running RAG Ablation Experiments
```bash
python research/src/eval/run_ablation_study.py
```
