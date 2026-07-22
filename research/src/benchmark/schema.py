from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class BenchmarkCategory(str, Enum):
    NUMERICAL = "Numerical"
    COMPARISON = "Comparison"
    TREND = "Trend"
    RISK = "Risk"
    MULTI_DOCUMENT = "Multi-document"

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class BenchmarkEntry(BaseModel):
    id: str = Field(..., description="Unique benchmark QA ID, e.g., bench_0001")
    question: str = Field(..., description="Financial question prompt")
    answer: str = Field(..., description="Ground-truth factual answer")
    category: BenchmarkCategory = Field(..., description="Evaluation category")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    ticker: str = Field(..., description="Stock ticker, e.g., AAPL")
    document_id: str = Field(..., description="Parent filing document ID")
    source_file: str = Field(..., description="Path to processed source document")
    evidence_text: str = Field(..., description="Exact supporting snippet or table row")
    chunk_id: Optional[str] = Field(None, description="Matching document chunk ID if available")

class BenchmarkDataset(BaseModel):
    version: str = "1.0.0"
    total_entries: int
    category_counts: Dict[str, int]
    entries: List[BenchmarkEntry]
