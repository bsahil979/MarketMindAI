"""
Ollama Client - Local LLM integration
"""

import logging
from typing import List, Dict, Any, Optional
import ollama

logger = logging.getLogger("marketmind.llm.ollama")

class OllamaClient:
    def __init__(self, model: str = "llama3.1", host: Optional[str] = None):
        """
        Initialize Ollama client
        
        Args:
            model: Model name (e.g., "llama3.1", "mistral", "gemma2")
            host: Ollama host URL (optional, uses default if None)
        """
        self.model = model
        self.host = host or "http://localhost:11434"
        
        # Validate Ollama is available
        try:
            models = ollama.list()
            available_models = [m["model"] for m in models.get("models", [])]
            if model not in available_models:
                logger.warning(f"Model {model} not found. Available: {available_models}")
                logger.info(f"Attempting to pull model {model}...")
                try:
                    ollama.pull(model)
                    logger.info(f"Successfully pulled model {model}")
                except Exception as e:
                    logger.error(f"Failed to pull model {model}: {e}")
                    # Use first available model as fallback
                    if available_models:
                        self.model = available_models[0]
                        logger.info(f"Using fallback model: {self.model}")
        except Exception as e:
            logger.error(f"Failed to connect to Ollama at {self.host}: {e}")
            logger.warning("Ollama may not be running. Start with: ollama serve")
        
        logger.info(f"Ollama client initialized with model: {self.model}")
    
    def chat(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """
        Chat completion
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated response text
        """
        try:
            response = ollama.chat(
                model=self.model,
                messages=messages,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **kwargs
                }
            )
            return response["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama chat failed: {e}")
            return f"Error: Ollama chat failed - {str(e)}"
    
    def stream(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ):
        """
        Stream chat completion
        
        Args:
            messages: List of message dictionaries
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Yields:
            Text chunks as they are generated
        """
        try:
            for chunk in ollama.chat(
                model=self.model,
                messages=messages,
                stream=True,
                options={
                    "temperature": temperature,
                    "num_predict": max_tokens,
                    **kwargs
                }
            ):
                if "message" in chunk and "content" in chunk["message"]:
                    yield chunk["message"]["content"]
        except Exception as e:
            logger.error(f"Ollama streaming failed: {e}")
            yield f"Error: Ollama streaming failed - {str(e)}"
    
    def generate(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 1024,
        **kwargs
    ) -> str:
        """
        Simple text generation
        
        Args:
            prompt: Input prompt
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            **kwargs: Additional parameters
            
        Returns:
            Generated text
        """
        messages = [{"role": "user", "content": prompt}]
        return self.chat(messages, temperature, max_tokens, **kwargs)
    
    def list_models(self) -> List[str]:
        """List available models"""
        try:
            response = ollama.list()
            return [m["model"] for m in response.get("models", [])]
        except Exception as e:
            logger.error(f"Failed to list models: {e}")
            return []
    
    def pull_model(self, model_name: str) -> bool:
        """
        Pull a new model from Ollama registry
        
        Args:
            model_name: Name of model to pull
            
        Returns:
            True if successful
        """
        try:
            ollama.pull(model_name)
            logger.info(f"Successfully pulled model: {model_name}")
            return True
        except Exception as e:
            logger.error(f"Failed to pull model {model_name}: {e}")
            return False
