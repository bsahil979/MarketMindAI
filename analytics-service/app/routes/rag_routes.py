"""
RAG Routes - API endpoints for RAG-powered financial Q&A
"""

from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import logging

from app.rag import RAGRetriever
from app.llm import LLMInterface
from app.database import get_db
from app.evaluation import EvaluationManager
from sqlalchemy.orm import Session

logger = logging.getLogger("marketmind.api.rag")

router = APIRouter(prefix="/api/v1/rag", tags=["RAG"])

# Global RAG instance (initialized on startup)
rag_retriever: Optional[RAGRetriever] = None
llm_interface: Optional[LLMInterface] = None
evaluation_manager: EvaluationManager = EvaluationManager()

class QueryRequest(BaseModel):
    query: str = Field(..., description="User query about financial data")
    ticker: Optional[str] = Field(None, description="Filter by ticker symbol")
    top_k: int = Field(5, ge=1, le=20, description="Number of documents to retrieve")
    use_hybrid: bool = Field(True, description="Use hybrid search (BM25 + vector)")
    temperature: float = Field(0.7, ge=0.0, le=1.0, description="LLM temperature")
    llm_provider: str = Field("ollama", description="LLM provider to use")

class QueryResponse(BaseModel):
    query: str
    answer: str
    sources: List[Dict[str, Any]]
    retrieval_metadata: Dict[str, Any]
    llm_metadata: Dict[str, Any]
    evaluation_metrics: Optional[Dict[str, Any]] = None

class IndexRequest(BaseModel):
    rebuild: bool = Field(False, description="Rebuild entire index")
    use_sample_data: bool = Field(True, description="Use sample SEC documents")

class IndexResponse(BaseModel):
    status: str
    message: str
    stats: Dict[str, Any]

@router.post("/query", response_model=QueryResponse)
async def query_rag(request: QueryRequest, db: Session = Depends(get_db)):
    """
    Query the RAG system with a financial question
    
    This endpoint:
    1. Retrieves relevant documents using hybrid search
    2. Generates an answer using the LLM with context
    3. Returns the answer with source citations
    4. Tracks evaluation metrics for quality assessment
    """
    global rag_retriever, llm_interface, evaluation_manager
    
    if not rag_retriever:
        raise HTTPException(status_code=503, detail="RAG system not initialized")
    
    try:
        import time
        start_time = time.time()
        
        # Prepare metadata filter
        filter_metadata = {}
        if request.ticker:
            filter_metadata["ticker"] = request.ticker.upper()
        
        # Retrieve relevant documents
        retrieval_result = rag_retriever.retrieve_with_context(
            query=request.query,
            top_k=request.top_k,
            filter_metadata=filter_metadata if filter_metadata else None
        )
        
        if not retrieval_result["context"]:
            return QueryResponse(
                query=request.query,
                answer="I couldn't find relevant information in the SEC filings to answer your question. Please try a different query or check if the documents are indexed.",
                sources=[],
                retrieval_metadata=retrieval_result["metadata"],
                llm_metadata={"provider": llm_interface.provider if llm_interface else "none"},
                evaluation_metrics=None
            )
        
        # Initialize LLM if needed or switch provider
        if not llm_interface or llm_interface.provider != request.llm_provider:
            llm_interface = LLMInterface(provider=request.llm_provider)
        
        # Generate answer with context
        answer = llm_interface.generate_with_context(
            query=request.query,
            context=retrieval_result["context"],
            temperature=request.temperature
        )
        
        # Track evaluation metrics
        evaluation_metrics = None
        try:
            # Extract retrieved document IDs
            retrieved_doc_ids = [source.get("doc_id", f"doc_{i}") for i, source in enumerate(retrieval_result["sources"])]
            
            # For evaluation, we assume all retrieved docs are relevant (in production, use ground truth)
            relevant_docs = set(retrieved_doc_ids)
            
            # Evaluate the query
            eval_result = evaluation_manager.evaluate_rag_query(
                query=request.query,
                retrieved_docs=retrieved_doc_ids,
                relevant_docs=relevant_docs,
                answer=answer,
                context=retrieval_result["context"],
                ground_truth=None  # No ground truth in production
            )
            evaluation_metrics = {
                "retrieval_metrics": eval_result["retrieval_metrics"],
                "answer_metrics": eval_result["answer_metrics"]
            }
        except Exception as eval_error:
            logger.warning(f"Evaluation tracking failed: {eval_error}")
        
        # Track LLM API usage
        try:
            latency_ms = (time.time() - start_time) * 1000
            # Estimate token usage (rough approximation)
            input_tokens = len(request.query) // 4 + len(retrieval_result["context"]) // 4
            output_tokens = len(answer) // 4
            
            evaluation_manager.track_llm_call(
                provider=request.llm_provider,
                model=llm_interface.model if llm_interface else "unknown",
                input_tokens=input_tokens,
                output_tokens=output_tokens,
                latency_ms=latency_ms
            )
        except Exception as cost_error:
            logger.warning(f"Cost tracking failed: {cost_error}")
        
        return QueryResponse(
            query=request.query,
            answer=answer,
            sources=retrieval_result["sources"],
            retrieval_metadata=retrieval_result["metadata"],
            llm_metadata=llm_interface.get_model_info(),
            evaluation_metrics=evaluation_metrics
        )
        
    except Exception as e:
        logger.error(f"RAG query failed: {e}")
        raise HTTPException(status_code=500, detail=f"Query failed: {str(e)}")

@router.post("/index", response_model=IndexResponse)
async def index_documents(request: IndexRequest, db: Session = Depends(get_db)):
    """
    Index documents into the RAG system
    
    This endpoint:
    1. Processes and chunks documents
    2. Generates embeddings
    3. Builds vector and BM25 indexes
    """
    global rag_retriever
    
    try:
        # Initialize RAG retriever if needed
        if not rag_retriever:
            rag_retriever = RAGRetriever(embedding_provider="bge")
        
        if request.use_sample_data:
            # Use sample SEC documents
            stats = rag_retriever.initialize_with_sample_data()
            return IndexResponse(
                status="success",
                message="Indexed sample SEC documents",
                stats=stats
            )
        else:
            # In a real implementation, you would load documents from database or files
            # For now, we'll use sample data
            stats = rag_retriever.initialize_with_sample_data()
            return IndexResponse(
                status="success",
                message="Indexed documents (using sample data)",
                stats=stats
            )
            
    except Exception as e:
        logger.error(f"Document indexing failed: {e}")
        raise HTTPException(status_code=500, detail=f"Indexing failed: {str(e)}")

@router.get("/stats")
async def get_rag_stats():
    """Get RAG system statistics"""
    global rag_retriever
    
    if not rag_retriever:
        return {
            "status": "not_initialized",
            "message": "RAG system not initialized. Call POST /index first."
        }
    
    return rag_retriever.get_stats()

@router.get("/health")
async def rag_health():
    """Check RAG system health"""
    global rag_retriever, llm_interface
    
    return {
        "rag_initialized": rag_retriever is not None,
        "llm_initialized": llm_interface is not None,
        "index_built": rag_retriever.index_built if rag_retriever else False,
        "llm_provider": llm_interface.provider if llm_interface else "none"
    }

def initialize_rag_system():
    """Initialize RAG system on startup"""
    global rag_retriever, llm_interface
    
    try:
        logger.info("Initializing RAG system...")
        rag_retriever = RAGRetriever(embedding_provider="bge")
        llm_interface = LLMInterface(provider="ollama")
        
        # Initialize with sample data
        stats = rag_retriever.initialize_with_sample_data()
        logger.info(f"RAG system initialized: {stats}")
        
    except Exception as e:
        logger.error(f"Failed to initialize RAG system: {e}")
        # Don't fail startup, just log the error
