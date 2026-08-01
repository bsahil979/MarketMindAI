"""
Vector Store - ChromaDB integration for document storage and retrieval
"""

import os
import logging
from typing import List, Dict, Any, Optional
import chromadb
from chromadb.config import Settings
from chromadb.utils import embedding_functions

logger = logging.getLogger("marketmind.rag.vector_store")

class VectorStore:
    def __init__(self, collection_name: str = "sec_documents", persist_directory: Optional[str] = None):
        """
        Initialize ChromaDB vector store
        
        Args:
            collection_name: Name of the collection
            persist_directory: Directory to persist data (optional)
        """
        self.collection_name = collection_name
        self.persist_directory = persist_directory or os.path.join(os.getcwd(), "chroma_db")
        
        # Ensure persist directory exists
        os.makedirs(self.persist_directory, exist_ok=True)
        
        # Initialize ChromaDB client
        self.client = chromadb.PersistentClient(
            path=self.persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True
            )
        )
        
        # Get or create collection
        self.collection = self._get_or_create_collection()
        logger.info(f"Vector store initialized with collection: {collection_name}")
    
    def _get_or_create_collection(self):
        """Get existing collection or create new one"""
        try:
            # Try to get existing collection
            collection = self.client.get_collection(name=self.collection_name)
            logger.info(f"Loaded existing collection: {self.collection_name}")
            return collection
        except:
            # Create new collection
            collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "SEC 10-K and financial documents"}
            )
            logger.info(f"Created new collection: {self.collection_name}")
            return collection
    
    def add_documents(
        self,
        documents: List[str],
        embeddings: List[List[float]],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ):
        """
        Add documents to the vector store
        
        Args:
            documents: List of document text chunks
            embeddings: List of embedding vectors
            metadatas: List of metadata dictionaries
            ids: List of unique document IDs
        """
        try:
            self.collection.add(
                documents=documents,
                embeddings=embeddings,
                metadatas=metadatas,
                ids=ids
            )
            logger.info(f"Added {len(documents)} documents to vector store")
        except Exception as e:
            logger.error(f"Failed to add documents: {e}")
            raise
    
    def query(
        self,
        query_embeddings: Optional[List[float]] = None,
        query_texts: Optional[List[str]] = None,
        n_results: int = 5,
        where: Optional[Dict[str, Any]] = None,
        where_document: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Query the vector store
        
        Args:
            query_embeddings: Query embedding vector
            query_texts: Query text (alternative to embeddings)
            n_results: Number of results to return
            where: Metadata filter
            where_document: Document content filter
            
        Returns:
            Dictionary with query results
        """
        try:
            results = self.collection.query(
                query_embeddings=query_embeddings,
                query_texts=query_texts,
                n_results=n_results,
                where=where,
                where_document=where_document
            )
            return results
        except Exception as e:
            logger.error(f"Query failed: {e}")
            return {"documents": [], "metadatas": [], "distances": [], "ids": []}
    
    def get_document_by_id(self, doc_id: str) -> Optional[Dict[str, Any]]:
        """Get a specific document by ID"""
        try:
            results = self.collection.get(ids=[doc_id])
            if results["ids"]:
                return {
                    "id": results["ids"][0],
                    "document": results["documents"][0],
                    "metadata": results["metadatas"][0]
                }
            return None
        except Exception as e:
            logger.error(f"Failed to get document {doc_id}: {e}")
            return None
    
    def delete_documents(self, ids: List[str]):
        """Delete documents by IDs"""
        try:
            self.collection.delete(ids=ids)
            logger.info(f"Deleted {len(ids)} documents")
        except Exception as e:
            logger.error(f"Failed to delete documents: {e}")
    
    def get_collection_stats(self) -> Dict[str, Any]:
        """Get statistics about the collection"""
        try:
            count = self.collection.count()
            return {
                "collection_name": self.collection_name,
                "document_count": count,
                "persist_directory": self.persist_directory
            }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def reset_collection(self):
        """Delete and recreate the collection (use with caution)"""
        try:
            self.client.delete_collection(name=self.collection_name)
            self.collection = self.client.create_collection(
                name=self.collection_name,
                metadata={"description": "SEC 10-K and financial documents"}
            )
            logger.info(f"Reset collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to reset collection: {e}")
            raise
    
    def update_document(
        self,
        doc_id: str,
        document: Optional[str] = None,
        embedding: Optional[List[float]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Update an existing document"""
        try:
            self.collection.update(
                ids=[doc_id],
                documents=[document] if document else None,
                embeddings=[embedding] if embedding else None,
                metadatas=[metadata] if metadata else None
            )
            logger.info(f"Updated document: {doc_id}")
        except Exception as e:
            logger.error(f"Failed to update document {doc_id}: {e}")
