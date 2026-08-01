"""
AI Service API - Separate microservice for heavy AI operations
Handles ML forecasting, RAG, and evaluation independently
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import logging
import os
from sqlalchemy.orm import Session

from app.database import SessionLocal, DimCompany
from app.ai.ai_engine import calculate_forecasts, calculate_risk_metrics
from app.rag import RAGRetriever
from app.llm import LLMInterface
from app.evaluation import EvaluationManager

logger = logging.getLogger("marketmind.ai_service")

app = FastAPI(title="MarketMind AI Service", version="1.0.0")

# Global AI components
rag_retriever = None
llm_interface = None
evaluation_manager = EvaluationManager()

class ForecastRequest(BaseModel):
    company_id: int
    ticker: str

class RAGQueryRequest(BaseModel):
    query: str
    ticker: Optional[str] = None
    top_k: int = 5
    llm_provider: str = "ollama"

@app.get("/health")
def health_check():
    """AI service health check"""
    return {
        "status": "UP",
        "service": "ai-service",
        "rag_initialized": rag_retriever is not None,
        "llm_initialized": llm_interface is not None
    }

@app.post("/forecast")
def generate_forecast(request: ForecastRequest):
    """Generate ML-based price forecast"""
    try:
        db = SessionLocal()
        company = db.query(DimCompany).filter_by(company_id=request.company_id).first()
        if not company:
            raise HTTPException(status_code=404, detail="Company not found")
        
        calculate_forecasts(db, company)
        db.close()
        
        return {"status": "success", "message": f"Forecast generated for {request.ticker}"}
    except Exception as e:
        logger.error(f"Forecast generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/rag/query")
def rag_query(request: RAGQueryRequest):
    """RAG-powered query processing"""
    global rag_retriever, llm_interface
    
    if not rag_retriever:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        # Initialize LLM if needed
        if not llm_interface or llm_interface.provider != request.llm_provider:
            llm_interface = LLMInterface(provider=request.llm_provider)
        
        # Retrieve relevant documents
        filter_metadata = {"ticker": request.ticker} if request.ticker else None
        retrieval_result = rag_retriever.retrieve_with_context(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=filter_metadata
        )
        
        if not retrieval_result["context"]:
            return {
                "query": request.query,
                "answer": "No relevant information found",
                "sources": []
            }
        
        # Generate answer
        answer = llm_interface.generate_with_context(
            query=request.query,
            context=retrieval_result["context"]
        )
        
        return {
            "query": request.query,
            "answer": answer,
            "sources": retrieval_result["sources"]
        }
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.on_event("startup")
async def startup():
    """Initialize AI components"""
    global rag_retriever, llm_interface

    # Skip RAG initialization if environment variable is set
    if os.getenv("SKIP_RAG_INIT", "false").lower() == "true":
        logger.info("Skipping RAG system initialization (SKIP_RAG_INIT=true)")
    else:
        try:
            logger.info("Initializing RAG system...")
            rag_retriever = RAGRetriever(embedding_provider="bge")
            rag_retriever.initialize_with_sample_data()
            logger.info("RAG system initialized")
        except Exception as e:
            logger.warning(f"RAG initialization failed: {e}")

    try:
        logger.info("Initializing LLM interface...")
        llm_interface = LLMInterface(provider="ollama")
        logger.info("LLM interface initialized")
    except Exception as e:
        logger.warning(f"LLM initialization failed: {e}")
