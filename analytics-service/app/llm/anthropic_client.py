"""
Anthropic Client - Claude API integration
"""

import logging
from typing import List, Dict, Any, Optional
import anthropic

logger = logging.getLogger("marketmind.llm.anthropic")

class AnthropicClient:
    def __init__(self, model: str = "claude-3-haiku-20240307", api_key: Optional[str] = None):
        """
        Initialize Anthropic client
        
        Args:
            model: Model name (e.g., "claude-3-haiku-20240307", "claude-3-sonnet-20240229")
            api_key: Anthropic API key (optional, reads from env if None)
        """
        self.model = model
        self.api_key = api_key
        
        try:
            self.client = anthropic.Anthropic(api_key=self.api_key)
            logger.info(f"Anthropic client initialized with model: {model}")
        except Exception as e:
            logger.error(f"Failed to initialize Anthropic client: {e}")
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
            # Convert messages to Anthropic format
            system_prompt = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    user_messages.append(msg)
            
            response = self.client.messages.create(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=user_messages,
                **kwargs
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"Anthropic chat failed: {e}")
            return f"Error: Anthropic chat failed - {str(e)}"
    
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
            # Convert messages to Anthropic format
            system_prompt = ""
            user_messages = []
            
            for msg in messages:
                if msg["role"] == "system":
                    system_prompt = msg["content"]
                else:
                    user_messages.append(msg)
            
            with self.client.messages.stream(
                model=self.model,
                max_tokens=max_tokens,
                temperature=temperature,
                system=system_prompt,
                messages=user_messages,
                **kwargs
            ) as stream:
                for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming failed: {e}")
            yield f"Error: Anthropic streaming failed - {str(e)}"
    
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
