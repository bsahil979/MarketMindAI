import hashlib
from typing import List, Optional

try:
    from sentence_transformers import SentenceTransformer
    HAS_SENTENCE_TRANSFORMERS = True
except ImportError:
    HAS_SENTENCE_TRANSFORMERS = False

class FinancialEmbeddings:
    """
    Embedding manager for Financial RAG.
    Supports HuggingFace Sentence Transformers (e.g. BAAI/bge-small-en-v1.5) with a lightweight fallback encoder.
    """

    def __init__(self, model_name: str = "BAAI/bge-small-en-v1.5"):
        self.model_name = model_name
        self.model = None
        self.dimension = 384

        if HAS_SENTENCE_TRANSFORMERS:
            try:
                print(f"[Embeddings] Loading SentenceTransformer model: {model_name}...")
                self.model = SentenceTransformer(model_name)
                self.dimension = self.model.get_sentence_embedding_dimension()
            except Exception as e:
                print(f"[Embeddings Warning] Failed to load {model_name}: {e}. Falling back to hash encoder.")

    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        """
        Embeds a list of text strings into vector representations.
        """
        if self.model:
            embeddings = self.model.encode(texts, show_progress_bar=False)
            return embeddings.tolist()
        return [self._fallback_embed(text) for text in texts]

    def embed_query(self, text: str) -> List[float]:
        """
        Embeds a single query string into a vector representation.
        """
        if self.model:
            return self.model.encode(text, show_progress_bar=False).tolist()
        return self._fallback_embed(text)

    def _fallback_embed(self, text: str) -> List[float]:
        """
        Deterministic hash-based fallback embedding (384-dim) for testing without PyTorch dependencies.
        """
        vec = []
        for i in range(self.dimension):
            h = hashlib.sha256(f"{text}_{i}".encode("utf-8")).hexdigest()
            # Convert hex to float normalized between -1.0 and 1.0
            val = (int(h[:8], 16) / 0xFFFFFFFF) * 2.0 - 1.0
            vec.append(val)
        return vec

if __name__ == "__main__":
    embedder = FinancialEmbeddings()
    v = embedder.embed_query("Apple 2024 Revenue")
    print("Embedding dimension:", len(v))
