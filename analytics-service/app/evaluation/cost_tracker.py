"""
Cost Tracker - Track API costs and resource usage
Monitors LLM API calls, embedding costs, and model usage
"""

import logging
import time
from typing import Dict, Any, Optional
from datetime import datetime
from collections import defaultdict

logger = logging.getLogger("marketmind.evaluation.cost")

class CostTracker:
    def __init__(self):
        """Initialize cost tracker"""
        self.api_costs = defaultdict(float)
        self.api_calls = defaultdict(int)
        self.token_usage = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0})
        self.latency_tracking = defaultdict(list)
        self.model_usage = defaultdict(int)
        
        # Pricing (approximate USD per 1K tokens)
        self.pricing = {
            "openai": {
                "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
                "gpt-4o": {"input": 0.005, "output": 0.015},
                "text-embedding-3-small": {"input": 0.00002, "output": 0.0}
            },
            "anthropic": {
                "claude-3-haiku-20240307": {"input": 0.00025, "output": 0.00125},
                "claude-3-sonnet-20240229": {"input": 0.003, "output": 0.015}
            },
            "ollama": {
                "default": {"input": 0.0, "output": 0.0}  # Local, no cost
            },
            "bge": {
                "default": {"input": 0.0, "output": 0.0}  # Local, no cost
            }
        }
    
    def track_api_call(self, provider: str, model: str, input_tokens: int, output_tokens: int, 
                      latency_ms: float, cost: Optional[float] = None) -> Dict[str, Any]:
        """
        Track an API call with token usage and cost
        
        Args:
            provider: API provider (openai, anthropic, ollama, etc.)
            model: Model name
            input_tokens: Number of input tokens
            output_tokens: Number of output tokens
            latency_ms: Request latency in milliseconds
            cost: Optional manual cost override
            
        Returns:
            Tracking result with calculated cost
        """
        # Calculate cost if not provided
        if cost is None:
            cost = self._calculate_cost(provider, model, input_tokens, output_tokens)
        
        # Update tracking
        key = f"{provider}_{model}"
        self.api_costs[key] += cost
        self.api_calls[key] += 1
        self.token_usage[key]["input_tokens"] += input_tokens
        self.token_usage[key]["output_tokens"] += output_tokens
        self.model_usage[model] += 1
        self.latency_tracking[key].append(latency_ms)
        
        logger.info(f"API call tracked: {provider}/{model} - Cost: ${cost:.6f}, Tokens: {input_tokens}+{output_tokens}, Latency: {latency_ms:.2f}ms")
        
        return {
            "provider": provider,
            "model": model,
            "cost": float(cost),
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": input_tokens + output_tokens,
            "latency_ms": float(latency_ms)
        }
    
    def track_embedding_call(self, provider: str, model: str, num_texts: int, 
                            total_tokens: int, latency_ms: float) -> Dict[str, Any]:
        """
        Track an embedding API call
        
        Args:
            provider: Embedding provider (bge, openai, ollama)
            model: Model name
            num_texts: Number of texts embedded
            total_tokens: Total tokens processed
            latency_ms: Processing latency in milliseconds
            
        Returns:
            Tracking result
        """
        # Calculate cost (embeddings usually only have input cost)
        cost = self._calculate_cost(provider, model, total_tokens, 0)
        
        key = f"{provider}_{model}"
        self.api_costs[key] += cost
        self.api_calls[key] += 1
        self.token_usage[key]["input_tokens"] += total_tokens
        self.model_usage[model] += 1
        self.latency_tracking[key].append(latency_ms)
        
        logger.info(f"Embedding call tracked: {provider}/{model} - Cost: ${cost:.6f}, Texts: {num_texts}, Tokens: {total_tokens}")
        
        return {
            "provider": provider,
            "model": model,
            "cost": float(cost),
            "num_texts": num_texts,
            "total_tokens": total_tokens,
            "latency_ms": float(latency_ms)
        }
    
    def _calculate_cost(self, provider: str, model: str, input_tokens: int, output_tokens: int) -> float:
        """Calculate cost based on provider pricing"""
        provider_pricing = self.pricing.get(provider.lower(), {})
        model_pricing = provider_pricing.get(model, provider_pricing.get("default", {"input": 0.0, "output": 0.0}))
        
        input_cost = (input_tokens / 1000) * model_pricing.get("input", 0.0)
        output_cost = (output_tokens / 1000) * model_pricing.get("output", 0.0)
        
        return input_cost + output_cost
    
    def get_total_cost(self) -> float:
        """Get total cost across all providers and models"""
        return float(sum(self.api_costs.values()))
    
    def get_cost_by_provider(self) -> Dict[str, float]:
        """Get cost breakdown by provider"""
        provider_costs = defaultdict(float)
        for key, cost in self.api_costs.items():
            provider = key.split("_")[0]
            provider_costs[provider] += cost
        return dict(provider_costs)
    
    def get_cost_by_model(self) -> Dict[str, float]:
        """Get cost breakdown by model"""
        model_costs = defaultdict(float)
        for key, cost in self.api_costs.items():
            model = "_".join(key.split("_")[1:])  # Get everything after provider
            model_costs[model] += cost
        return dict(model_costs)
    
    def get_token_usage(self) -> Dict[str, Dict[str, int]]:
        """Get token usage by provider/model"""
        return dict(self.token_usage)
    
    def get_latency_stats(self) -> Dict[str, Dict[str, float]]:
        """Get latency statistics by provider/model"""
        stats = {}
        for key, latencies in self.latency_tracking.items():
            if latencies:
                stats[key] = {
                    "avg_latency_ms": float(sum(latencies) / len(latencies)),
                    "min_latency_ms": float(min(latencies)),
                    "max_latency_ms": float(max(latencies)),
                    "total_calls": len(latencies)
                }
        return stats
    
    def get_model_usage(self) -> Dict[str, int]:
        """Get usage count by model"""
        return dict(self.model_usage)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get comprehensive cost summary"""
        return {
            "total_cost": self.get_total_cost(),
            "cost_by_provider": self.get_cost_by_provider(),
            "cost_by_model": self.get_cost_by_model(),
            "token_usage": self.get_token_usage(),
            "latency_stats": self.get_latency_stats(),
            "model_usage": self.get_model_usage(),
            "total_api_calls": sum(self.api_calls.values())
        }
    
    def reset(self):
        """Reset all tracking data"""
        self.api_costs = defaultdict(float)
        self.api_calls = defaultdict(int)
        self.token_usage = defaultdict(lambda: {"input_tokens": 0, "output_tokens": 0})
        self.latency_tracking = defaultdict(list)
        self.model_usage = defaultdict(int)
