"""
AI Service Client - Communicates with the separate AI microservice
Provides fallback to local simulated models if AI service unavailable
"""

import httpx
import logging
from typing import Dict, Any, Optional
import os

logger = logging.getLogger("marketmind.ai_client")

class AIServiceClient:
    """Client for communicating with the AI microservice"""
    
    def __init__(self):
        self.base_url = os.getenv("AI_SERVICE_URL", "http://localhost:8001")
        self.enabled = os.getenv("ENABLE_AI_SERVICE", "false").lower() == "true"
        self.timeout = 30.0
        
    def is_available(self) -> bool:
        """Check if AI service is available"""
        if not self.enabled:
            return False
            
        try:
            response = httpx.get(f"{self.base_url}/health", timeout=5.0)
            return response.status_code == 200
        except Exception as e:
            logger.warning(f"AI service health check failed: {e}")
            return False
    
    def generate_forecast(self, company_id: int, ticker: str) -> Dict[str, Any]:
        """Generate ML-based forecast via AI service"""
        if not self.is_available():
            logger.info("AI service unavailable, using local forecasting")
            return {"status": "fallback", "message": "Using local simulated models"}
        
        try:
            response = httpx.post(
                f"{self.base_url}/forecast",
                json={"company_id": company_id, "ticker": ticker},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AI service forecast request failed: {e}")
            return {"status": "error", "message": str(e)}
    
    def rag_query(self, query: str, ticker: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
        """Process RAG query via AI service"""
        if not self.is_available():
            logger.info("AI service unavailable, RAG not available")
            return {
                "query": query,
                "answer": "AI service unavailable. RAG features require the AI microservice to be running.",
                "sources": []
            }
        
        try:
            response = httpx.post(
                f"{self.base_url}/rag/query",
                json={"query": query, "ticker": ticker, "top_k": top_k},
                timeout=self.timeout
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"AI service RAG request failed: {e}")
            return {
                "query": query,
                "answer": f"RAG query failed: {str(e)}",
                "sources": []
            }

# Global AI service client instance
ai_client = AIServiceClient()
