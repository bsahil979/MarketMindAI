from enum import Enum
from typing import List, Dict, Optional
from pydantic import BaseModel, Field

class BenchmarkCategory(str, Enum):
    NUMERICAL = "Numerical"
    COMPARISON = "Comparison"
    TREND = "Trend"
    RISK = "Risk"
    MULTI_DOCUMENT = "Multi-document"
    CASH_FLOW = "Cash Flow"
    SEGMENT_REVENUE = "Segment Revenue"
    FINANCIAL_RATIOS = "Financial Ratios"
    CEO_COMMENTARY = "CEO Commentary"

class DifficultyLevel(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"

class BenchmarkEntry(BaseModel):
    id: str = Field(..., description="Unique benchmark QA ID, e.g., bench_0001")
    question: str = Field(..., description="Financial question prompt")
    answer: str = Field(..., description="Ground-truth factual answer")
    ground_truth: str = Field("", description="Explicit ground-truth monetary figure or summary")
    evidence: str = Field("", description="Verbatim evidence snippet from filing")
    page: int = Field(1, description="Filing page number reference")
    category: BenchmarkCategory = Field(..., description="Evaluation category")
    difficulty: DifficultyLevel = Field(..., description="Difficulty level")
    ticker: str = Field(..., description="Stock ticker, e.g., AAPL")
    document_id: str = Field(..., description="Parent filing document ID")
    source_file: str = Field(..., description="Path to processed source document")
    evidence_text: str = Field("", description="Exact supporting snippet or table row")
    chunk_id: Optional[str] = Field(None, description="Matching document chunk ID if available")

class BenchmarkDataset(BaseModel):
    version: str = "3.0.0"
    total_entries: int
    category_counts: Dict[str, int]
    entries: List[BenchmarkEntry]
