import os
import logging
import math

logger = logging.getLogger("marketmind.semantic")

# Try to use configured embedding provider: 'openai', 'sentence_transformers', or 'auto'
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
EMBEDDING_PROVIDER = os.getenv("EMBEDDING_PROVIDER", "auto").lower()


def _cosine(a, b):
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    mag_a = math.sqrt(sum(x * x for x in a))
    mag_b = math.sqrt(sum(y * y for y in b))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


# Lazy-loaded model or client
_openai_client = None
_st_model = None


def _ensure_openai():
    global _openai_client
    try:
        import openai
    except Exception:
        return False
    if OPENAI_API_KEY:
        openai.api_key = OPENAI_API_KEY
        _openai_client = openai
        return True
    return False


def _ensure_st():
    global _st_model
    if _st_model is not None:
        return True
    try:
        from sentence_transformers import SentenceTransformer
    except Exception:
        return False
    try:
        _st_model = SentenceTransformer('all-MiniLM-L6-v2')
        return True
    except Exception as e:
        logger.warning(f"Failed to load sentence-transformers model: {e}")
        return False


def embed_text(text: str):
    """Return embedding vector for text or None if not available."""
    if not text:
        return None
    # provider preference
    if EMBEDDING_PROVIDER == 'openai' and _ensure_openai():
        try:
            resp = _openai_client.Embedding.create(model="text-embedding-3-small", input=text)
            vec = resp['data'][0]['embedding']
            return vec
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")
    if EMBEDDING_PROVIDER == 'sentence_transformers' and _ensure_st():
        try:
            vec = _st_model.encode(text).tolist()
            return vec
        except Exception as e:
            logger.warning(f"SentenceTransformer encode failed: {e}")
    # auto: prefer OpenAI if available, else sentence-transformers
    if EMBEDDING_PROVIDER == 'auto':
        if _ensure_openai():
            try:
                resp = _openai_client.Embedding.create(model="text-embedding-3-small", input=text)
                vec = resp['data'][0]['embedding']
                return vec
            except Exception as e:
                logger.warning(f"OpenAI embedding failed: {e}")
        if _ensure_st():
            try:
                vec = _st_model.encode(text).tolist()
                return vec
            except Exception as e:
                logger.warning(f"SentenceTransformer encode failed: {e}")
    # fallback to any available provider
    if _ensure_openai():
        try:
            resp = _openai_client.Embedding.create(model="text-embedding-3-small", input=text)
            vec = resp['data'][0]['embedding']
            return vec
        except Exception as e:
            logger.warning(f"OpenAI embedding failed: {e}")
    if _ensure_st():
        try:
            vec = _st_model.encode(text).tolist()
            return vec
        except Exception as e:
            logger.warning(f"SentenceTransformer encode failed: {e}")
    return None


def semantic_similarity(a: str, b: str) -> float:
    """Return semantic similarity in [0,1]. Falls back to fuzzy ratio if embeddings unavailable."""
    if not a or not b:
        return 0.0
    emb_a = embed_text(a)
    emb_b = embed_text(b)
    if emb_a and emb_b:
        try:
            return float(_cosine(emb_a, emb_b))
        except Exception as e:
            logger.warning(f"Cosine computation failed: {e}")
    # fallback to SequenceMatcher ratio
    try:
        from difflib import SequenceMatcher
        ratio = SequenceMatcher(None, a.lower(), b.lower()).ratio()
        return float(ratio)
    except Exception:
        return 0.0
 