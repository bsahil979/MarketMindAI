import json
import re
from pathlib import Path
from typing import List, Dict, Any
from src.benchmark.schema import (
    BenchmarkEntry,
    BenchmarkCategory,
    DifficultyLevel,
    BenchmarkDataset
)

class BenchmarkGenerator:
    """
    Generator for financial RAG benchmark entries from processed filings & chunks.
    Constructs ground-truth QA pairs across Numerical, Comparison, Trend, Risk, and Multi-document categories.
    """

    def __init__(
        self,
        dataset_dir: str = "research/dataset",
        output_dir: str = "research/benchmark"
    ):
        self.dataset_dir = Path(dataset_dir)
        self.processed_dir = self.dataset_dir / "processed"
        self.chunks_dir = self.dataset_dir / "chunks"
        self.output_dir = Path(output_dir)
        self.evidence_dir = self.output_dir / "evidence"
        self.annotations_dir = self.output_dir / "annotations"

        for d in [self.output_dir, self.evidence_dir, self.annotations_dir]:
            d.mkdir(parents=True, exist_ok=True)

    def generate_benchmark(self) -> BenchmarkDataset:
        """
        Scans dataset folder, parses financial tables & risk sections, and synthesizes QA entries.
        """
        entries: List[BenchmarkEntry] = []
        entry_counter = 1

        processed_files = list(self.processed_dir.glob("*.md"))

        for file_path in processed_files:
            doc_id = file_path.stem
            content = file_path.read_text(encoding="utf-8")
            ticker = doc_id.split("_")[1].upper() if "_" in doc_id else "AAPL"

            # Parse Markdown tables for Numerical & Comparison questions
            table_entries = self._extract_table_qa(content, doc_id, ticker, file_path, entry_counter)
            entries.extend(table_entries)
            entry_counter += len(table_entries)

            # Extract Risk questions
            risk_entries = self._extract_risk_qa(content, doc_id, ticker, file_path, entry_counter)
            entries.extend(risk_entries)
            entry_counter += len(risk_entries)

            # Extract Trend questions
            trend_entries = self._extract_trend_qa(content, doc_id, ticker, file_path, entry_counter)
            entries.extend(trend_entries)
            entry_counter += len(trend_entries)

        # Multi-document comparative questions
        multi_doc_entries = self._extract_multi_doc_qa(entries, entry_counter)
        entries.extend(multi_doc_entries)

        # Calculate category counts
        category_counts: Dict[str, int] = {}
        for entry in entries:
            cat = entry.category.value
            category_counts[cat] = category_counts.get(cat, 0) + 1

        dataset = BenchmarkDataset(
            version="1.0.0",
            total_entries=len(entries),
            category_counts=category_counts,
            entries=entries
        )

        # Save main benchmark JSON
        benchmark_file = self.output_dir / "benchmark.json"
        benchmark_file.write_text(dataset.model_dump_json(indent=2), encoding="utf-8")

        # Save evidence files & annotation stats
        self._save_evidence_and_annotations(dataset)

        return dataset

    def _extract_table_qa(
        self,
        content: str,
        doc_id: str,
        ticker: str,
        file_path: Path,
        counter_start: int
    ) -> List[BenchmarkEntry]:
        entries = []
        lines = content.splitlines()

        table_rows = [line for line in lines if line.startswith("|") and "---" not in line]
        if len(table_rows) >= 2:
            header = [c.strip() for c in table_rows[0].split("|")[1:-1]]
            for idx, row_str in enumerate(table_rows[1:], start=1):
                cols = [c.strip() for c in row_str.split("|")[1:-1]]
                if len(cols) >= 2 and cols[0] and cols[1]:
                    segment = cols[0]
                    val_2024 = cols[1]

                    # 1. Numerical Question
                    entries.append(
                        BenchmarkEntry(
                            id=f"bench_{counter_start + len(entries):04d}",
                            question=f"What was {ticker}'s {segment} revenue in 2024 according to the filing?",
                            answer=f"${val_2024} Million",
                            category=BenchmarkCategory.NUMERICAL,
                            difficulty=DifficultyLevel.EASY,
                            ticker=ticker,
                            document_id=doc_id,
                            source_file=str(file_path),
                            evidence_text=row_str
                        )
                    )

                    # 2. Comparison / Growth Question
                    if len(cols) >= 3 and cols[2]:
                        val_2023 = cols[2]
                        entries.append(
                            BenchmarkEntry(
                                id=f"bench_{counter_start + len(entries):04d}",
                                question=f"How did {ticker}'s {segment} revenue change from 2023 to 2024?",
                                answer=f"2023: ${val_2023} Million, 2024: ${val_2024} Million",
                                category=BenchmarkCategory.COMPARISON,
                                difficulty=DifficultyLevel.MEDIUM,
                                ticker=ticker,
                                document_id=doc_id,
                                source_file=str(file_path),
                                evidence_text=row_str
                            )
                        )

        return entries

    def _extract_risk_qa(
        self,
        content: str,
        doc_id: str,
        ticker: str,
        file_path: Path,
        counter_start: int
    ) -> List[BenchmarkEntry]:
        entries = []
        if "Risk Factors" in content:
            risk_section = content.split("Risk Factors")[-1].strip()
            snippet = risk_section[:300].strip()
            entries.append(
                BenchmarkEntry(
                    id=f"bench_{counter_start:04d}",
                    question=f"What primary risk factors are highlighted for {ticker}?",
                    answer=snippet,
                    category=BenchmarkCategory.RISK,
                    difficulty=DifficultyLevel.MEDIUM,
                    ticker=ticker,
                    document_id=doc_id,
                    source_file=str(file_path),
                    evidence_text=snippet
                )
            )
        return entries

    def _extract_trend_qa(
        self,
        content: str,
        doc_id: str,
        ticker: str,
        file_path: Path,
        counter_start: int
    ) -> List[BenchmarkEntry]:
        entries = []
        if "Management's Discussion" in content or "MD&A" in content or "sales" in content.lower():
            for line in content.splitlines():
                if "increased" in line.lower() or "decreased" in line.lower() or "growth" in line.lower():
                    entries.append(
                        BenchmarkEntry(
                            id=f"bench_{counter_start:04d}",
                            question=f"What management trend is reported regarding {ticker}'s financial performance?",
                            answer=line.strip(),
                            category=BenchmarkCategory.TREND,
                            difficulty=DifficultyLevel.MEDIUM,
                            ticker=ticker,
                            document_id=doc_id,
                            source_file=str(file_path),
                            evidence_text=line.strip()
                        )
                    )
                    break
        return entries

    def _extract_multi_doc_qa(
        self,
        existing_entries: List[BenchmarkEntry],
        counter_start: int
    ) -> List[BenchmarkEntry]:
        entries = []
        numerical_entries = [e for e in existing_entries if e.category == BenchmarkCategory.NUMERICAL]
        if numerical_entries:
            first_entry = numerical_entries[0]
            entries.append(
                BenchmarkEntry(
                    id=f"bench_{counter_start:04d}",
                    question=f"Summarize {first_entry.ticker}'s key segment financial highlights and primary risk factors.",
                    answer=f"Revenue: {first_entry.answer}. Key evidence: {first_entry.evidence_text}",
                    category=BenchmarkCategory.MULTI_DOCUMENT,
                    difficulty=DifficultyLevel.HARD,
                    ticker=first_entry.ticker,
                    document_id=first_entry.document_id,
                    source_file=first_entry.source_file,
                    evidence_text=first_entry.evidence_text
                )
            )
        return entries

    def _save_evidence_and_annotations(self, dataset: BenchmarkDataset):
        for entry in dataset.entries:
            ev_file = self.evidence_dir / f"{entry.id}_evidence.txt"
            ev_file.write_text(f"QA ID: {entry.id}\nQuestion: {entry.question}\nEvidence:\n{entry.evidence_text}", encoding="utf-8")

        annotation_summary = {
            "version": dataset.version,
            "total_benchmark_questions": dataset.total_entries,
            "category_distribution": dataset.category_counts,
            "difficulty_distribution": {
                "Easy": len([e for e in dataset.entries if e.difficulty == DifficultyLevel.EASY]),
                "Medium": len([e for e in dataset.entries if e.difficulty == DifficultyLevel.MEDIUM]),
                "Hard": len([e for e in dataset.entries if e.difficulty == DifficultyLevel.HARD])
            }
        }
        annot_file = self.annotations_dir / "annotations_summary.json"
        annot_file.write_text(json.dumps(annotation_summary, indent=2), encoding="utf-8")

if __name__ == "__main__":
    bg = BenchmarkGenerator()
    print("BenchmarkGenerator ready.")
