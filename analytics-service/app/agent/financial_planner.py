"""
Financial Planner - Multi-step reasoning for complex financial queries
Breaks down complex questions into executable steps with tool selection
"""

import logging
from typing import List, Dict, Any, Optional
from enum import Enum

logger = logging.getLogger("marketmind.agent.planner")

class ToolType(Enum):
    """Available tools for financial analysis"""
    RAG_RETRIEVAL = "rag_retrieval"
    FINANCIAL_CALCULATOR = "financial_calculator"
    MARKET_DATA = "market_data"
    COMPARISON_MATRIX = "comparison_matrix"
    RISK_ANALYSIS = "risk_analysis"
    PORTFOLIO_OPTIMIZATION = "portfolio_optimization"

class PlanningStep:
    """Represents a single step in the financial analysis plan"""
    def __init__(
        self,
        step_id: int,
        tool: ToolType,
        description: str,
        parameters: Dict[str, Any],
        dependencies: Optional[List[int]] = None
    ):
        self.step_id = step_id
        self.tool = tool
        self.description = description
        self.parameters = parameters
        self.dependencies = dependencies or []
        self.result = None
        self.status = "pending"
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_id": self.step_id,
            "tool": self.tool.value,
            "description": self.description,
            "parameters": self.parameters,
            "dependencies": self.dependencies,
            "status": self.status,
            "result": self.result
        }

class FinancialPlanner:
    def __init__(self):
        """Initialize financial planner with reasoning capabilities"""
        self.query_patterns = {
            # Revenue and growth analysis
            "revenue": [ToolType.RAG_RETRIEVAL, ToolType.FINANCIAL_CALCULATOR],
            "growth": [ToolType.RAG_RETRIEVAL, ToolType.MARKET_DATA],
            "sales": [ToolType.RAG_RETRIEVAL, ToolType.FINANCIAL_CALCULATOR],
            
            # Financial health and ratios
            "ratio": [ToolType.FINANCIAL_CALCULATOR, ToolType.RAG_RETRIEVAL],
            "debt": [ToolType.FINANCIAL_CALCULATOR, ToolType.RAG_RETRIEVAL, ToolType.RISK_ANALYSIS],
            "liquidity": [ToolType.FINANCIAL_CALCULATOR, ToolType.RAG_RETRIEVAL],
            "cash flow": [ToolType.FINANCIAL_CALCULATOR, ToolType.RAG_RETRIEVAL],
            
            # Risk and performance
            "risk": [ToolType.RISK_ANALYSIS, ToolType.RAG_RETRIEVAL],
            "performance": [ToolType.MARKET_DATA, ToolType.RAG_RETRIEVAL],
            "volatility": [ToolType.RISK_ANALYSIS, ToolType.MARKET_DATA],
            
            # Comparative analysis
            "compare": [ToolType.COMPARISON_MATRIX, ToolType.RAG_RETRIEVAL, ToolType.FINANCIAL_CALCULATOR],
            "vs": [ToolType.COMPARISON_MATRIX, ToolType.RAG_RETRIEVAL],
            "better": [ToolType.COMPARISON_MATRIX, ToolType.FINANCIAL_CALCULATOR],
            
            # Portfolio and investment
            "portfolio": [ToolType.PORTFOLIO_OPTIMIZATION, ToolType.RISK_ANALYSIS],
            "investment": [ToolType.PORTFOLIO_OPTIMIZATION, ToolType.RAG_RETRIEVAL],
            "allocation": [ToolType.PORTFOLIO_OPTIMIZATION, ToolType.RISK_ANALYSIS],
            
            # SEC and regulatory
            "sec": [ToolType.RAG_RETRIEVAL],
            "filing": [ToolType.RAG_RETRIEVAL],
            "10-k": [ToolType.RAG_RETRIEVAL],
            "10-q": [ToolType.RAG_RETRIEVAL],
            "regulatory": [ToolType.RAG_RETRIEVAL]
        }
    
    def analyze_query(self, query: str) -> Dict[str, Any]:
        """
        Analyze the query to determine intent and required tools
        
        Args:
            query: User's financial query
            
        Returns:
            Analysis result with detected intent and suggested tools
        """
        query_lower = query.lower()
        
        # Detect query type
        detected_intents = []
        for pattern, tools in self.query_patterns.items():
            if pattern in query_lower:
                detected_intents.extend(tools)
        
        # Remove duplicates while preserving order
        detected_intents = list(dict.fromkeys(detected_intents))
        
        # Detect tickers
        tickers = self._extract_tickers(query)
        
        # Detect timeframes
        timeframe = self._extract_timeframe(query)
        
        # Detect comparison intent
        is_comparison = any(word in query_lower for word in ["compare", "vs", "versus", "against", "better"])
        
        return {
            "query": query,
            "detected_intents": [intent.value for intent in detected_intents],
            "tickers": tickers,
            "timeframe": timeframe,
            "is_comparison": is_comparison,
            "complexity": self._assess_complexity(query, detected_intents, is_comparison)
        }
    
    def create_plan(self, query: str) -> List[PlanningStep]:
        """
        Create a step-by-step plan for answering the query
        
        Args:
            query: User's financial query
            
        Returns:
            List of planning steps
        """
        analysis = self.analyze_query(query)
        steps = []
        step_id = 0
        
        # Step 1: Always start with information retrieval
        if ToolType.RAG_RETRIEVAL in [ToolType(intent) for intent in analysis["detected_intents"]]:
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.RAG_RETRIEVAL,
                description="Retrieve relevant SEC filings and financial documents",
                parameters={
                    "query": query,
                    "tickers": analysis["tickers"],
                    "top_k": 5
                }
            ))
        
        # Step 2: Market data retrieval if needed
        if any(t in analysis["detected_intents"] for t in ["market_data", "performance", "volatility"]):
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.MARKET_DATA,
                description="Fetch current market prices and historical data",
                parameters={
                    "tickers": analysis["tickers"],
                    "timeframe": analysis["timeframe"]
                },
                dependencies=[] if step_id == 1 else [step_id - 1]
            ))
        
        # Step 3: Financial calculations
        if any(t in analysis["detected_intents"] for t in ["financial_calculator", "ratio", "debt", "liquidity"]):
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.FINANCIAL_CALCULATOR,
                description="Calculate financial ratios and metrics",
                parameters={
                    "tickers": analysis["tickers"],
                    "ratios": self._detect_ratios(query)
                },
                dependencies=[1] if step_id > 1 else []
            ))
        
        # Step 4: Comparison matrix for comparative queries
        if analysis["is_comparison"] and len(analysis["tickers"]) >= 2:
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.COMPARISON_MATRIX,
                description="Generate multi-company comparison matrix",
                parameters={
                    "tickers": analysis["tickers"],
                    "metrics": ["revenue", "debt", "cash", "roe", "risk"]
                },
                dependencies=[1] if step_id > 1 else []
            ))
        
        # Step 5: Risk analysis
        if any(t in analysis["detected_intents"] for t in ["risk_analysis", "risk", "volatility"]):
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.RISK_ANALYSIS,
                description="Calculate risk metrics and assess portfolio risk",
                parameters={
                    "tickers": analysis["tickers"]
                },
                dependencies=[2] if step_id > 2 else []
            ))
        
        # Step 6: Portfolio optimization for investment queries
        if any(t in analysis["detected_intents"] for t in ["portfolio_optimization", "portfolio", "investment"]):
            step_id += 1
            steps.append(PlanningStep(
                step_id=step_id,
                tool=ToolType.PORTFOLIO_OPTIMIZATION,
                description="Generate portfolio allocation recommendations",
                parameters={
                    "tickers": analysis["tickers"],
                    "risk_profile": self._detect_risk_profile(query)
                },
                dependencies=[4] if step_id > 4 else []
            ))
        
        # Step 7: Final synthesis with LLM
        step_id += 1
        steps.append(PlanningStep(
            step_id=step_id,
            tool=ToolType.RAG_RETRIEVAL,  # Using RAG for final LLM synthesis
            description="Synthesize all information into comprehensive answer",
            parameters={
                "query": query,
                "synthesis_mode": "final"
            },
            dependencies=list(range(1, step_id))  # Depends on all previous steps
        ))
        
        logger.info(f"Created plan with {len(steps)} steps for query: {query}")
        return steps
    
    def _extract_tickers(self, query: str) -> List[str]:
        """Extract stock tickers from query"""
        query_upper = query.upper()
        known_tickers = ["AAPL", "MSFT", "NVDA", "AMZN", "GOOGL", "TSLA", "META", "AMD", "NFLX", "JPM"]
        
        detected = []
        for ticker in known_tickers:
            if ticker in query_upper:
                detected.append(ticker)
        
        # Also check for company names
        company_map = {
            "APPLE": "AAPL",
            "MICROSOFT": "MSFT", 
            "NVIDIA": "NVDA",
            "AMAZON": "AMZN",
            "GOOGLE": "GOOGL",
            "ALPHABET": "GOOGL",
            "TESLA": "TSLA",
            "META": "META",
            "FACEBOOK": "META",
            "AMD": "AMD",
            "NETFLIX": "NFLX",
            "JPMORGAN": "JPM",
            "J P MORGAN": "JPM"
        }
        
        for company, ticker in company_map.items():
            if company in query_upper:
                if ticker not in detected:
                    detected.append(ticker)
        
        return detected if detected else ["AAPL"]  # Default to Apple if no ticker detected
    
    def _extract_timeframe(self, query: str) -> str:
        """Extract timeframe from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["year", "annual", "fy", "fiscal"]):
            return "annual"
        elif any(word in query_lower for word in ["quarter", "q1", "q2", "q3", "q4"]):
            return "quarterly"
        elif any(word in query_lower for word in ["month", "monthly"]):
            return "monthly"
        else:
            return "annual"  # Default
    
    def _assess_complexity(self, query: str, intents: List, is_comparison: bool) -> str:
        """Assess query complexity"""
        complexity_score = len(intents)
        if is_comparison:
            complexity_score += 2
        
        if complexity_score <= 2:
            return "simple"
        elif complexity_score <= 4:
            return "moderate"
        else:
            return "complex"
    
    def _detect_ratios(self, query: str) -> List[str]:
        """Detect which financial ratios to calculate"""
        query_lower = query.lower()
        ratios = []
        
        if "debt" in query_lower or "leverage" in query_lower:
            ratios.append("debt_to_equity")
        if "current" in query_lower and "ratio" in query_lower:
            ratios.append("current_ratio")
        if "roe" in query_lower or "return on equity" in query_lower:
            ratios.append("roe")
        if "cash flow" in query_lower or "fcf" in query_lower:
            ratios.append("free_cash_flow")
        if "p/e" in query_lower or "pe ratio" in query_lower:
            ratios.append("pe_ratio")
        
        return ratios if ratios else ["current_ratio", "debt_to_equity", "roe"]
    
    def _detect_risk_profile(self, query: str) -> str:
        """Detect risk profile from query"""
        query_lower = query.lower()
        
        if any(word in query_lower for word in ["conservative", "low risk", "safe"]):
            return "conservative"
        elif any(word in query_lower for word in ["aggressive", "high risk", "growth"]):
            return "aggressive"
        else:
            return "moderate"
