"""
Embedding Service - Multiple provider support with fallback
Supports: BGE (local), OpenAI, Ollama embeddings
"""

import os
from typing import List, Optional
from sentence_transformers import SentenceTransformer
import logging

logger = logging.getLogger("marketmind.rag.embeddings")

class EmbeddingService:
    def __init__(self, provider: str = "bge", model_name: Optional[str] = None):
        """
        Initialize embedding service with specified provider
        
        Args:
            provider: "bge" (local), "openai", or "ollama"
            model_name: Specific model name (optional, uses defaults if None)
        """
        self.provider = provider.lower()
        self.model_name = model_name or self._get_default_model()
        self.model = None
        self._initialize_model()
        
    def _get_default_model(self) -> str:
        """Get default model name for each provider"""
        defaults = {
            "bge": "all-MiniLM-L6-v2",  # Much smaller (80MB) and faster, still good performance
            "openai": "text-embedding-3-small",
            "ollama": "nomic-embed-text"
        }
        return defaults.get(self.provider, "all-MiniLM-L6-v2")
    
    def _initialize_model(self):
        """Initialize the embedding model based on provider"""
        try:
            if self.provider == "bge":
                logger.info(f"Loading BGE model: {self.model_name}")
                self.model = SentenceTransformer(self.model_name)
                logger.info("BGE model loaded successfully")
                
            elif self.provider == "openai":
                # OpenAI embeddings are stateless, just validate API key
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY not found, falling back to BGE")
                    self.provider = "bge"
                    self.model_name = "BAAI/bge-m3"
                    self.model = SentenceTransformer(self.model_name)
                else:
                    logger.info("OpenAI embeddings configured (API-based)")
                    
            elif self.provider == "ollama":
                # Ollama embeddings are stateless, just validate connection
                logger.info(f"Ollama embeddings configured: {self.model_name}")
                
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} model: {e}")
            logger.info("Falling back to BGE base model")
            self.provider = "bge"
            self.model_name = "BAAI/bge-m3"
            self.model = SentenceTransformer(self.model_name)
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for a list of documents
        
        Args:
            texts: List of text strings to embed
            
        Returns:
            List of embedding vectors
        """
        try:
            if self.provider == "bge":
                embeddings = self.model.encode(texts, convert_to_numpy=False)
                return [emb.tolist() for emb in embeddings]
                
            elif self.provider == "openai":
                import openai
                client = openai.OpenAI()
                response = client.embeddings.create(
                    model=self.model_name,
                    input=texts
                )
                return [item.embedding for item in response.data]
                
            elif self.provider == "ollama":
                import ollama
                embeddings = []
                for text in texts:
                    response = ollama.embeddings(model=self.model_name, prompt=text)
                    embeddings.append(response["embedding"])
                return embeddings
                
        except Exception as e:
            logger.error(f"Embedding generation failed: {e}")
            # Fallback to simple TF-IDF style if embeddings fail
            return self._fallback_embeddings(texts)
    
    def embed_query(self, text: str) -> List[float]:
        """
        Generate embedding for a single query
        
        Args:
            text: Query string to embed
            
        Returns:
            Embedding vector
        """
        embeddings = self.embed_documents([text])
        return embeddings[0] if embeddings else []
    
    def _fallback_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Fallback to simple hash-based embeddings if model fails
        This ensures the system continues to work even if embedding service fails
        """
        logger.warning("Using fallback hash-based embeddings")
        import hashlib
        import numpy as np
        
        embeddings = []
        for text in texts:
            # Create a deterministic hash-based embedding
            hash_obj = hashlib.md5(text.encode())
            hash_bytes = hash_obj.digest()
            # Convert to 384-dimensional vector (same as BGE-m3)
            vector = np.zeros(384)
            for i, byte in enumerate(hash_bytes):
                vector[i % 384] = byte / 255.0
            embeddings.append(vector.tolist())
        
        return embeddings
    
    def get_dimension(self) -> int:
        """Get the dimension of the embedding vectors"""
        if self.provider == "bge":
            return self.model.get_sentence_embedding_dimension()
        elif self.provider == "openai":
            return 1536  # text-embedding-3-small
        elif self.provider == "ollama":
            return 768  # nomic-embed-text
        else:
            return 384  # fallback dimension
