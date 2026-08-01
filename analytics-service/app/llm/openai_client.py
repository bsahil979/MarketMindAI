"""
OpenAI Client - OpenAI API integration
"""

import logging
from typing import List, Dict, Any, Optional
import openai

logger = logging.getLogger("marketmind.llm.openai")

class OpenAIClient:
    def __init__(self, model: str = "gpt-4o-mini", api_key: Optional[str] = None, base_url: Optional[str] = None):
        """
        Initialize OpenAI client
        
        Args:
            model: Model name (e.g., "gpt-4o-mini", "gpt-4o")
            api_key: OpenAI API key (optional, reads from env if None)
            base_url: Custom base URL (optional, for compatible APIs like Groq)
        """
        self.model = model
        self.api_key = api_key
        self.base_url = base_url or "https://api.openai.com/v1"
        
        try:
            self.client = openai.OpenAI(
                api_key=self.api_key,
                base_url=self.base_url
            )
            logger.info(f"OpenAI client initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize OpenAI client: {e}")
            raise
    
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
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"OpenAI chat failed: {e}")
            return f"Error: OpenAI chat failed - {str(e)}"
    
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
            stream = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                stream=True,
                **kwargs
            )
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"OpenAI streaming failed: {e}")
            yield f"Error: OpenAI streaming failed - {str(e)}"
    
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
    
    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Get embeddings for texts
        
        Args:
            texts: List of text strings
            
        Returns:
            List of embedding vectors
        """
        try:
            response = self.client.embeddings.create(
                model="text-embedding-3-small",
                input=texts
            )
            return [item.embedding for item in response.data]
        except Exception as e:
            logger.error(f"OpenAI embeddings failed: {e}")
            return []
