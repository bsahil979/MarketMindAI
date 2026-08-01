"""
AI Integration Routes - Routes that use the AI microservice
Provides AI features in the main application with fallback to local models
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
import logging

from app.services.ai_service_client import ai_client

logger = logging.getLogger("marketmind.api.ai_integration")

router = APIRouter(prefix="/api/v1/ai", tags=["AI Integration"])

class RAGQueryRequest(BaseModel):
    query: str = Field(..., description="User query about financial data")
    ticker: Optional[str] = Field(None, description="Filter by ticker symbol")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")

class ForecastRequest(BaseModel):
    company_id: int = Field(..., description="Company ID")
    ticker: str = Field(..., description="Company ticker symbol")

@router.get("/status")
def ai_status():
    """Check AI service status"""
    return {
        "ai_service_enabled": ai_client.enabled,
        "ai_service_available": ai_client.is_available(),
        "ai_service_url": ai_client.base_url
    }

@router.post("/rag-query")
def rag_query(request: RAGQueryRequest):
    """
    Process RAG query using AI service
    
    This endpoint:
    1. Checks if AI service is available
    2. Sends query to AI service for RAG processing
    3. Returns answer with source citations
    4. Falls back to error message if AI service unavailable
    """
    try:
        result = ai_client.rag_query(
            query=request.query,
            ticker=request.ticker,
            top_k=request.top_k
        )
        return result
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.post("/forecast")
def generate_forecast(request: ForecastRequest):
    """
    Generate ML-based forecast using AI service
    
    This endpoint:
    1. Checks if AI service is available
    2. Sends forecast request to AI service
    3. Returns forecast generation status
    4. Falls back to local models if AI service unavailable
    """
    try:
        result = ai_client.generate_forecast(
            company_id=request.company_id,
            ticker=request.ticker
        )
        return result
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(status_code=500, detail=f"Forecast failed: {str(e)}")
