"""
Unified LLM Interface - Support multiple providers through single interface
"""

import os
import logging
from typing import List, Dict, Any, Optional, Union
from enum import Enum
from .ollama_client import OllamaClient

# Optional imports - only import if available
try:
    from .openai_client import OpenAIClient
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    from .anthropic_client import AnthropicClient
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

logger = logging.getLogger("marketmind.llm.interface")

class LLMProvider(Enum):
    """Supported LLM providers"""
    OLLAMA = "ollama"
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    GROQ = "groq"
    GEMINI = "gemini"

class LLMInterface:
    def __init__(self, provider: str = "ollama", model: Optional[str] = None):
        """
        Initialize unified LLM interface
        
        Args:
            provider: LLM provider ("ollama", "openai", "anthropic", "groq", "gemini")
            model: Specific model name (optional, uses defaults if None)
        """
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = self._initialize_client()
        
        logger.info(f"LLM Interface initialized: {self.provider} with model {self.model}")
    
    def _get_default_model(self) -> str:
        """Get default model for each provider"""
        defaults = {
            "ollama": "llama3:latest",  # Good general purpose model
            "openai": "gpt-4o-mini",  # Cost-effective
            "anthropic": "claude-3-haiku-20240307",  # Fast and cost-effective
            "groq": "llama3-70b-8192",  # Fast inference
            "gemini": "gemini-1.5-flash"  # Fast and cost-effective
        }
        return defaults.get(self.provider, "llama3:latest")
    
    def _initialize_client(self):
        """Initialize the appropriate client based on provider"""
        try:
            if self.provider == "ollama":
                return OllamaClient(model=self.model)
            elif self.provider == "openai":
                if not OPENAI_AVAILABLE:
                    logger.warning("OpenAI client not available, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                api_key = os.getenv("OPENAI_API_KEY")
                if not api_key:
                    logger.warning("OPENAI_API_KEY not found, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                return OpenAIClient(model=self.model, api_key=api_key)
            elif self.provider == "anthropic":
                if not ANTHROPIC_AVAILABLE:
                    logger.warning("Anthropic client not available, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.warning("ANTHROPIC_API_KEY not found, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                return AnthropicClient(model=self.model, api_key=api_key)
            elif self.provider == "groq":
                # Groq uses OpenAI-compatible API
                if not OPENAI_AVAILABLE:
                    logger.warning("Groq requires OpenAI client, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                api_key = os.getenv("GROQ_API_KEY")
                if not api_key:
                    logger.warning("GROQ_API_KEY not found, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                return OpenAIClient(model=self.model, api_key=api_key, base_url="https://api.groq.com/openai/v1")
            elif self.provider == "gemini":
                # Gemini uses OpenAI-compatible API
                if not OPENAI_AVAILABLE:
                    logger.warning("Gemini requires OpenAI client, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                api_key = os.getenv("GEMINI_API_KEY")
                if not api_key:
                    logger.warning("GEMINI_API_KEY not found, falling back to Ollama")
                    self.provider = "ollama"
                    self.model = "llama3.1"
                    return OllamaClient(model=self.model)
                return OpenAIClient(model=self.model, api_key=api_key, base_url="https://generativelanguage.googleapis.com/v1beta")
            else:
                logger.warning(f"Unknown provider {self.provider}, falling back to Ollama")
                self.provider = "ollama"
                self.model = "llama3.1"
                return OllamaClient(model=self.model)
        except Exception as e:
            logger.error(f"Failed to initialize {self.provider} client: {e}")
            logger.info("Falling back to Ollama")
            self.provider = "ollama"
            self.model = "llama3.1"
            return OllamaClient(model=self.model)
    
    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated text
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = self.client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Generation failed: {e}")
            return f"Error generating response: {str(e)}"
    
    def generate_with_context(
        self,
        query: str,
        context: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1536
    ) -> str:
        """
        Generate response with RAG context
        
        Args:
            query: User query
            context: Retrieved context from documents
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Returns:
            Generated response with context
        """
        # Default financial analyst system prompt
        if system_prompt is None:
            system_prompt = """You are a financial analyst AI assistant. Your role is to:
1. Answer questions about financial data, SEC filings, and market analysis
2. Use the provided context from SEC filings and financial documents
3. Provide accurate, well-reasoned answers with citations
4. If the context doesn't contain the answer, acknowledge this limitation
5. Be precise with financial data and calculations
6. Explain complex concepts clearly when needed"""
        
        # Combine query with context
        full_prompt = f"""Context from SEC filings and financial documents:
{context}

Question: {query}

Please provide a detailed answer based on the context above. Include specific citations where possible."""
        
        return self.generate(
            prompt=full_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
            max_tokens=max_tokens
        )
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """
        Chat completion with message history
        
        Args:
            messages: List of message dictionaries with "role" and "content"
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Returns:
            Generated response
        """
        try:
            response = self.client.chat(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response
        except Exception as e:
            logger.error(f"Chat completion failed: {e}")
            return f"Error in chat completion: {str(e)}"
    
    def stream(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ):
        """
        Stream text completion (generator)
        
        Args:
            prompt: User prompt
            system_prompt: System prompt (optional)
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional provider-specific parameters
            
        Yields:
            Text chunks as they are generated
        """
        try:
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            for chunk in self.client.stream(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            ):
                yield chunk
                
        except Exception as e:
            logger.error(f"Streaming failed: {e}")
            yield f"Error in streaming: {str(e)}"
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about current model"""
        return {
            "provider": self.provider,
            "model": self.model,
            "client_type": type(self.client).__name__
        }
    
    def switch_provider(self, provider: str, model: Optional[str] = None):
        """
        Switch to a different provider
        
        Args:
            provider: New provider name
            model: New model name (optional)
        """
        logger.info(f"Switching from {self.provider} to {provider}")
        self.provider = provider.lower()
        self.model = model or self._get_default_model()
        self.client = self._initialize_client()
        logger.info(f"Switched to {self.provider} with model {self.model}")
