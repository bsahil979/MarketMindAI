"""
LLM Module - Unified interface for multiple LLM providers
Supports: Ollama, OpenAI, Anthropic, Groq, Gemini
"""

from .llm_interface import LLMInterface, LLMProvider
from .ollama_client import OllamaClient

# Optional imports - only import if available
try:
    from .openai_client import OpenAIClient
except ImportError:
    OpenAIClient = None

try:
    from .anthropic_client import AnthropicClient
except ImportError:
    AnthropicClient = None

__all__ = [
    "LLMInterface",
    "LLMProvider",
    "OllamaClient",
    "OpenAIClient",
    "AnthropicClient"
]
