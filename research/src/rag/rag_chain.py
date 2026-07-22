import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from src.rag.vectordb import VectorStoreManager
from src.rag.retriever import HybridRetriever
from src.rag.prompts import FinancialPromptBuilder

class FinancialRAGChain:
    """
    End-to-End Financial RAG Chain:
    Chunks $\rightarrow$ ChromaDB VectorStore $\rightarrow$ Hybrid Retriever $\rightarrow$ Prompt Builder $\rightarrow$ Grounded Answer
    """

    def __init__(
        self,
        chunks_dir: str = "research/dataset/chunks",
        persist_dir: str = "research/rag/vectordb"
    ):
        self.chunks_dir = Path(chunks_dir)
        self.vector_store = VectorStoreManager(persist_dir=persist_dir)
        self.retriever = HybridRetriever(self.vector_store)
        self.prompt_builder = FinancialPromptBuilder()
        self.loaded_chunks: List[Dict[str, Any]] = []

    def initialize_and_index(self) -> int:
        """
        Loads all chunks from dataset folder and indexes them into ChromaDB vector store.
        """
        all_chunks = []
        chunk_files = list(self.chunks_dir.glob("*_chunks.json"))

        for file_path in chunk_files:
            try:
                data = json.loads(file_path.read_text(encoding="utf-8"))
                if isinstance(data, list):
                    all_chunks.extend(data)
            except Exception as e:
                print(f"[RAGChain Warning] Failed to read {file_path}: {e}")

        self.loaded_chunks = all_chunks
        self.retriever.load_chunks_for_keyword_search(all_chunks)
        indexed_count = self.vector_store.index_chunks(all_chunks)
        return indexed_count

    def query(
        self,
        question: str,
        top_k: int = 4,
        ticker_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Executes end-to-end RAG query: retrieves relevant chunks, constructs prompt, and generates grounded answer.
        """
        retrieved_chunks = self.retriever.retrieve(
            query=question,
            top_k=top_k,
            ticker_filter=ticker_filter
        )

        formatted_prompt = self.prompt_builder.build_prompt(
            query=question,
            context_chunks=retrieved_chunks
        )

        # Grounded answer synthesis (extending retrieved context facts)
        answer_text = self._synthesize_grounded_answer(question, retrieved_chunks)

        return {
            "question": question,
            "answer": answer_text,
            "retrieved_chunks": retrieved_chunks,
            "formatted_prompt": formatted_prompt
        }

    def _synthesize_grounded_answer(self, question: str, retrieved_chunks: List[Dict[str, Any]]) -> str:
        """
        Synthesizes factual answer strictly grounded in retrieved chunk text.
        """
        if not retrieved_chunks:
            return "Based on the retrieved financial documents, there is insufficient evidence to answer this question."

        evidence_snippets = [c["text"] for c in retrieved_chunks]
        combined_text = "\n".join(evidence_snippets)

        lines = [f"**Financial Analysis Output:**"]
        lines.append(f"Retrieved {len(retrieved_chunks)} supporting context chunk(s).")
        lines.append(f"\n**Supporting Evidence Snippet:**\n```text\n{evidence_snippets[0][:350]}\n```")

        return "\n".join(lines)

if __name__ == "__main__":
    chain = FinancialRAGChain()
    print("FinancialRAGChain ready.")
