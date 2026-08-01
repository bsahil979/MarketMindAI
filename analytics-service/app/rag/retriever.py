"""
RAG Retriever - Main retrieval orchestration
Combines vector store, hybrid search, and LLM for complete RAG pipeline
"""

import logging
from typing import List, Dict, Any, Optional
from .vector_store import VectorStore
from .embeddings import EmbeddingService
from .document_processor import DocumentProcessor
from .hybrid_search import HybridSearchEngine

logger = logging.getLogger("marketmind.rag.retriever")

class RAGRetriever:
    def __init__(
        self,
        embedding_provider: str = "bge",
        collection_name: str = "sec_documents",
        chunk_size: int = 1000,
        chunk_overlap: int = 200
    ):
        """
        Initialize RAG retriever with all components
        
        Args:
            embedding_provider: Provider for embeddings ("bge", "openai", "ollama")
            collection_name: ChromaDB collection name
            chunk_size: Document chunk size
            chunk_overlap: Document chunk overlap
        """
        # Initialize components
        self.embedding_service = EmbeddingService(provider=embedding_provider)
        self.vector_store = VectorStore(collection_name=collection_name)
        self.document_processor = DocumentProcessor(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap
        )
        self.hybrid_search = HybridSearchEngine()
        
        # Track if index is built
        self.index_built = False
        
        logger.info("RAG Retriever initialized successfully")
    
    def index_documents(
        self,
        documents: List[Dict[str, Any]],
        rebuild_index: bool = False
    ) -> Dict[str, Any]:
        """
        Index documents into the vector store
        
        Args:
            documents: List of documents with "text" and "metadata" keys
            rebuild_index: Whether to rebuild the entire index
            
        Returns:
            Indexing statistics
        """
        try:
            if rebuild_index:
                logger.info("Rebuilding vector store collection")
                self.vector_store.reset_collection()
            
            # Process documents into chunks
            all_chunks = []
            all_embeddings = []
            all_metadatas = []
            all_ids = []
            
            doc_count = 0
            for doc in documents:
                doc_count += 1
                text = doc.get("text", "")
                metadata = doc.get("metadata", {})
                
                # Chunk the document
                chunks = self.document_processor.chunk_document(text, metadata)
                
                for chunk in chunks:
                    chunk_text = chunk["text"]
                    chunk_metadata = chunk["metadata"]
                    
                    # Generate unique ID
                    chunk_id = f"{metadata.get('ticker', 'unknown')}_{metadata.get('form_type', 'doc')}_{len(all_chunks)}"
                    
                    all_chunks.append(chunk_text)
                    all_metadatas.append(chunk_metadata)
                    all_ids.append(chunk_id)
            
            # Generate embeddings for all chunks
            logger.info(f"Generating embeddings for {len(all_chunks)} chunks...")
            all_embeddings = self.embedding_service.embed_documents(all_chunks)
            
            # Add to vector store
            self.vector_store.add_documents(
                documents=all_chunks,
                embeddings=all_embeddings,
                metadatas=all_metadatas,
                ids=all_ids
            )
            
            # Build BM25 index for hybrid search
            self.hybrid_search.build_bm25_index(all_chunks)
            self.index_built = True
            
            stats = {
                "documents_processed": doc_count,
                "chunks_created": len(all_chunks),
                "embedding_dimension": len(all_embeddings[0]) if all_embeddings else 0,
                "index_built": True
            }
            
            logger.info(f"Document indexing completed: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Document indexing failed: {e}")
            return {"error": str(e), "index_built": False}
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None,
        use_hybrid: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve relevant documents for a query
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"ticker": "AAPL"})
            use_hybrid: Whether to use hybrid search (BM25 + vector)
            
        Returns:
            List of retrieved documents with relevance scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_service.embed_query(query)
            
            if use_hybrid and self.index_built:
                # Hybrid search
                vector_results = self.vector_store.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k * 2,  # Get more candidates for hybrid
                    where=filter_metadata
                )
                
                # Convert vector results to format expected by hybrid search
                formatted_vector_results = []
                for i, (doc, metadata, distance) in enumerate(zip(
                    vector_results.get("documents", [[]])[0],
                    vector_results.get("metadatas", [[]])[0],
                    vector_results.get("distances", [[]])[0]
                )):
                    formatted_vector_results.append({
                        "index": i,
                        "text": doc,
                        "metadata": metadata,
                        "distance": distance
                    })
                
                # Perform hybrid search
                hybrid_results = self.hybrid_search.search(
                    query=query,
                    query_embedding=query_embedding,
                    vector_results=formatted_vector_results,
                    rerank=True
                )
                
                # Format results
                results = []
                for result in hybrid_results[:top_k]:
                    results.append({
                        "text": result["text"],
                        "metadata": formatted_vector_results[result["index"]].get("metadata", {}),
                        "relevance_score": result.get("rerank_score", result["combined_score"]),
                        "bm25_score": result["bm25_score"],
                        "vector_score": result["vector_score"],
                        "overlap_ratio": result.get("overlap_ratio", 0.0)
                    })
                
                return results
                
            else:
                # Vector-only search
                vector_results = self.vector_store.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=filter_metadata
                )
                
                results = []
                for doc, metadata, distance in zip(
                    vector_results.get("documents", [[]])[0],
                    vector_results.get("metadatas", [[]])[0],
                    vector_results.get("distances", [[]])[0]
                ):
                    results.append({
                        "text": doc,
                        "metadata": metadata,
                        "relevance_score": 1.0 / (1.0 + distance),  # Convert distance to similarity
                        "distance": distance
                    })
                
                return results
                
        except Exception as e:
            logger.error(f"Retrieval failed: {e}")
            return []
    
    def retrieve_with_context(
        self,
        query: str,
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve documents and format them for LLM context
        
        Args:
            query: Search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            Dictionary with retrieved context and metadata
        """
        results = self.retrieve(query, top_k=top_k, filter_metadata=filter_metadata)
        
        # Format context for LLM
        context_parts = []
        for i, result in enumerate(results, 1):
            metadata = result.get("metadata", {})
            source = metadata.get("ticker", "Unknown")
            section = metadata.get("section", "Unknown")
            form_type = metadata.get("form_type", "Document")
            
            context_part = f"[Source {i}: {source} - {form_type} - {section}]\n{result['text']}"
            context_parts.append(context_part)
        
        context = "\n\n".join(context_parts)
        
        return {
            "query": query,
            "context": context,
            "sources": results,
            "source_count": len(results),
            "metadata": {
                "embedding_provider": self.embedding_service.provider,
                "index_built": self.index_built,
                "retrieval_method": "hybrid" if self.index_built else "vector_only"
            }
        }
    
    def add_documents(self, documents: List[Dict[str, Any]]):
        """
        Add new documents to the index without rebuilding
        
        Args:
            documents: List of documents to add
        """
        # Process new documents
        new_chunks = []
        new_embeddings = []
        new_metadatas = []
        new_ids = []
        
        for doc in documents:
            text = doc.get("text", "")
            metadata = doc.get("metadata", {})
            
            chunks = self.document_processor.chunk_document(text, metadata)
            
            for chunk in chunks:
                chunk_text = chunk["text"]
                chunk_metadata = chunk["metadata"]
                chunk_id = f"{metadata.get('ticker', 'unknown')}_{metadata.get('form_type', 'doc')}_{hash(chunk_text) % 1000000}"
                
                new_chunks.append(chunk_text)
                new_metadatas.append(chunk_metadata)
                new_ids.append(chunk_id)
        
        # Generate embeddings
        new_embeddings = self.embedding_service.embed_documents(new_chunks)
        
        # Add to vector store
        self.vector_store.add_documents(
            documents=new_chunks,
            embeddings=new_embeddings,
            metadatas=new_metadatas,
            ids=new_ids
        )
        
        # Update hybrid search index
        self.hybrid_search.update_index(new_chunks)
        
        logger.info(f"Added {len(documents)} documents to index")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get RAG system statistics"""
        vector_stats = self.vector_store.get_collection_stats()
        hybrid_stats = self.hybrid_search.get_stats()
        
        return {
            "vector_store": vector_stats,
            "hybrid_search": hybrid_stats,
            "embedding_service": {
                "provider": self.embedding_service.provider,
                "model": self.embedding_service.model_name,
                "dimension": self.embedding_service.get_dimension()
            },
            "document_processor": {
                "chunk_size": self.document_processor.chunk_size,
                "chunk_overlap": self.document_processor.chunk_overlap
            },
            "index_built": self.index_built
        }
    
    def initialize_with_sample_data(self):
        """Initialize the RAG system with sample SEC documents"""
        logger.info("Initializing RAG system with sample SEC documents...")
        
        # Get sample documents
        sample_docs = self.document_processor.create_sample_sec_documents()
        
        # Index them
        stats = self.index_documents(sample_docs, rebuild_index=True)
        
        logger.info(f"RAG system initialized with sample data: {stats}")
        return stats
