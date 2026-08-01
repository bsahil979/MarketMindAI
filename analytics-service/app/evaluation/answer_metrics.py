"""
Answer Metrics - Measure quality of generated answers
Includes faithfulness, relevance, hallucination detection, and semantic similarity
"""

import logging
import re
from typing import List, Dict, Any, Optional, Set
from collections import Counter

logger = logging.getLogger("marketmind.evaluation.answer")

class AnswerMetrics:
    def __init__(self):
        """Initialize answer metrics calculator"""
        self.queries_evaluated = 0
        self.total_faithfulness = 0.0
        self.total_relevance = 0.0
        self.hallucination_count = 0
        
    def calculate_faithfulness(self, answer: str, context: str, retrieved_docs: List[str]) -> float:
        """
        Calculate faithfulness score - how well answer is grounded in retrieved context
        
        Args:
            answer: Generated answer
            context: Retrieved context/documents
            retrieved_docs: List of retrieved document IDs
            
        Returns:
            Faithfulness score (0-1)
        """
        if not answer or not context:
            return 0.0
        
        # Extract key entities and numbers from answer
        answer_entities = self._extract_entities(answer)
        context_entities = self._extract_entities(context)
        
        if not answer_entities:
            return 0.5  # Neutral score if no entities found
        
        # Calculate overlap
        matched_entities = answer_entities.intersection(context_entities)
        faithfulness = len(matched_entities) / len(answer_entities) if answer_entities else 0.0
        
        return float(faithfulness)
    
    def calculate_relevance(self, answer: str, query: str) -> float:
        """
        Calculate relevance score - how well answer addresses the query
        
        Args:
            answer: Generated answer
            query: Original query
            
        Returns:
            Relevance score (0-1)
        """
        if not answer or not query:
            return 0.0
        
        # Extract keywords from query
        query_keywords = set(self._extract_keywords(query.lower()))
        answer_lower = answer.lower()
        
        if not query_keywords:
            return 0.5  # Neutral score if no keywords
        
        # Check if query keywords appear in answer
        matched_keywords = sum(1 for keyword in query_keywords if keyword in answer_lower)
        relevance = matched_keywords / len(query_keywords)
        
        return float(relevance)
    
    def detect_hallucinations(self, answer: str, context: str, retrieved_docs: List[str]) -> Dict[str, Any]:
        """
        Detect potential hallucinations in the answer
        
        Args:
            answer: Generated answer
            context: Retrieved context/documents
            retrieved_docs: List of retrieved document IDs
            
        Returns:
            Dictionary with hallucination detection results
        """
        if not answer or not context:
            return {"hallucinated": False, "confidence": 0.0, "suspicious_phrases": []}
        
        # Extract numbers and facts from answer
        answer_facts = self._extract_facts(answer)
        context_facts = self._extract_facts(context)
        
        # Check for facts in answer not in context
        hallucinated_facts = []
        for fact in answer_facts:
            if fact not in context_facts:
                hallucinated_facts.append(fact)
        
        # Calculate hallucination probability
        hallucination_prob = len(hallucinated_facts) / len(answer_facts) if answer_facts else 0.0
        
        # Check for suspicious phrases
        suspicious_phrases = self._detect_suspicious_phrases(answer)
        
        return {
            "hallucinated": hallucination_prob > 0.3,
            "confidence": float(hallucination_prob),
            "hallucinated_facts": hallucinated_facts[:5],  # Limit to top 5
            "suspicious_phrases": suspicious_phrases
        }
    
    def calculate_answer_length(self, answer: str) -> Dict[str, int]:
        """
        Calculate answer length statistics
        
        Args:
            answer: Generated answer
            
        Returns:
            Dictionary with length statistics
        """
        if not answer:
            return {"characters": 0, "words": 0, "sentences": 0}
        
        words = answer.split()
        sentences = re.split(r'[.!?]+', answer)
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return {
            "characters": len(answer),
            "words": len(words),
            "sentences": len(sentences)
        }
    
    def calculate_semantic_similarity(self, answer: str, ground_truth: str) -> float:
        """
        Calculate semantic similarity between answer and ground truth
        Simple implementation using word overlap (can be enhanced with embeddings)
        
        Args:
            answer: Generated answer
            ground_truth: Reference answer
            
        Returns:
            Semantic similarity score (0-1)
        """
        if not answer or not ground_truth:
            return 0.0
        
        answer_words = set(self._extract_keywords(answer.lower()))
        ground_truth_words = set(self._extract_keywords(ground_truth.lower()))
        
        if not answer_words or not ground_truth_words:
            return 0.0
        
        # Jaccard similarity
        intersection = answer_words.intersection(ground_truth_words)
        union = answer_words.union(ground_truth_words)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        return float(similarity)
    
    def _extract_entities(self, text: str) -> Set[str]:
        """Extract named entities (simplified)"""
        # Extract capitalized words and numbers
        entities = set()
        
        # Extract numbers
        numbers = re.findall(r'\d+\.?\d*', text)
        entities.update(numbers)
        
        # Extract capitalized words (potential entities)
        capitalized = re.findall(r'\b[A-Z][a-zA-Z]+\b', text)
        entities.update(capitalized)
        
        return entities
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extract meaningful keywords from text"""
        # Remove common stop words
        stop_words = {'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been', 'being',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'must', 'shall', 'can', 'to', 'of', 'in',
                     'for', 'on', 'at', 'by', 'with', 'from', 'as', 'into', 'through',
                     'during', 'before', 'after', 'above', 'below', 'between', 'under',
                     'again', 'further', 'then', 'once', 'here', 'there', 'when', 'where',
                     'why', 'how', 'all', 'each', 'few', 'more', 'most', 'other', 'some',
                     'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so', 'than', 'too',
                     'very', 'just', 'and', 'but', 'if', 'or', 'because', 'until', 'while',
                     'it', 'its', 'this', 'that', 'these', 'those', 'i', 'you', 'he', 'she',
                     'we', 'they', 'what', 'which', 'who', 'whom', 'about', 'against', 'between'}
        
        words = re.findall(r'\b\w+\b', text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]
        
        return keywords
    
    def _extract_facts(self, text: str) -> Set[str]:
        """Extract factual statements (simplified)"""
        facts = set()
        
        # Extract patterns like "X is Y", "X equals Y", "X was Y"
        patterns = [
            r'\w+\s+is\s+\d+\.?\d*',
            r'\w+\s+equals\s+\d+\.?\d*',
            r'\w+\s+was\s+\d+\.?\d*',
            r'\$\d+\.?\d*',
            r'\d+\.?\d*\s*(percent|%|billion|million|thousand)',
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text, re.IGNORECASE)
            facts.update(matches)
        
        return facts
    
    def _detect_suspicious_phrases(self, text: str) -> List[str]:
        """Detect phrases that might indicate hallucination"""
        suspicious_patterns = [
            r'I believe that',
            r'It seems likely that',
            r'Probably',
            r'Maybe',
            r'Possibly',
            r'I think',
            r'Unclear',
            r'Not sure',
            r'Appears to be',
        ]
        
        suspicious = []
        text_lower = text.lower()
        
        for pattern in suspicious_patterns:
            if pattern.lower() in text_lower:
                suspicious.append(pattern)
        
        return suspicious
    
    def evaluate_answer(self, answer: str, query: str, context: str, 
                       retrieved_docs: List[str], ground_truth: Optional[str] = None) -> Dict[str, Any]:
        """
        Comprehensive answer evaluation
        
        Args:
            answer: Generated answer
            query: Original query
            context: Retrieved context/documents
            retrieved_docs: List of retrieved document IDs
            ground_truth: Optional reference answer
            
        Returns:
            Dictionary of all answer metrics
        """
        self.queries_evaluated += 1
        
        # Calculate individual metrics
        faithfulness = self.calculate_faithfulness(answer, context, retrieved_docs)
        relevance = self.calculate_relevance(answer, query)
        hallucination_result = self.detect_hallucinations(answer, context, retrieved_docs)
        length_stats = self.calculate_answer_length(answer)
        
        # Update running totals
        self.total_faithfulness += faithfulness
        self.total_relevance += relevance
        if hallucination_result["hallucinated"]:
            self.hallucination_count += 1
        
        # Semantic similarity if ground truth provided
        semantic_similarity = 0.0
        if ground_truth:
            semantic_similarity = self.calculate_semantic_similarity(answer, ground_truth)
        
        return {
            "faithfulness": float(faithfulness),
            "relevance": float(relevance),
            "hallucinated": hallucination_result["hallucinated"],
            "hallucination_confidence": hallucination_result["confidence"],
            "length_stats": length_stats,
            "semantic_similarity": float(semantic_similarity) if ground_truth else None,
            "suspicious_phrases": hallucination_result["suspicious_phrases"]
        }
    
    def get_average_metrics(self) -> Dict[str, float]:
        """Get average metrics across all evaluated answers"""
        if self.queries_evaluated == 0:
            return {
                "avg_faithfulness": 0.0,
                "avg_relevance": 0.0,
                "hallucination_rate": 0.0,
                "queries_evaluated": 0
            }
        
        return {
            "avg_faithfulness": float(self.total_faithfulness / self.queries_evaluated),
            "avg_relevance": float(self.total_relevance / self.queries_evaluated),
            "hallucination_rate": float(self.hallucination_count / self.queries_evaluated),
            "queries_evaluated": self.queries_evaluated
        }
    
    def reset(self):
        """Reset metrics counters"""
        self.queries_evaluated = 0
        self.total_faithfulness = 0.0
        self.total_relevance = 0.0
        self.hallucination_count = 0
