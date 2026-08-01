"""
Tool Executor - Execute financial analysis tools with proper error handling
Integrates with existing financial calculator, RAG, and database systems
"""

import logging
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session

from app.agent.financial_calculator import calculate_ratio, get_company_metrics_summary
from app.agent.financial_planner import ToolType, PlanningStep
from app.database import SessionLocal, DimCompany, FactMarketPrice, FactRiskMetrics, FactPrediction

logger = logging.getLogger("marketmind.agent.tool_executor")

class ToolExecutor:
    def __init__(self):
        """Initialize tool executor with access to all systems"""
        self.rag_retriever = None
        self.llm_interface = None
    
    def set_rag_system(self, rag_retriever, llm_interface):
        """Set RAG system for retrieval and LLM operations"""
        self.rag_retriever = rag_retriever
        self.llm_interface = llm_interface
    
    def execute_step(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a single planning step
        
        Args:
            step: Planning step to execute
            context: Context from previous steps
            
        Returns:
            Execution result
        """
        try:
            logger.info(f"Executing step {step.step_id}: {step.description}")
            
            if step.tool == ToolType.RAG_RETRIEVAL:
                result = self._execute_rag_retrieval(step, context)
            elif step.tool == ToolType.FINANCIAL_CALCULATOR:
                result = self._execute_financial_calculator(step, context)
            elif step.tool == ToolType.MARKET_DATA:
                result = self._execute_market_data(step, context)
            elif step.tool == ToolType.COMPARISON_MATRIX:
                result = self._execute_comparison_matrix(step, context)
            elif step.tool == ToolType.RISK_ANALYSIS:
                result = self._execute_risk_analysis(step, context)
            elif step.tool == ToolType.PORTFOLIO_OPTIMIZATION:
                result = self._execute_portfolio_optimization(step, context)
            else:
                result = {"error": f"Unknown tool: {step.tool}"}
            
            step.result = result
            step.status = "completed"
            
            return result
            
        except Exception as e:
            logger.error(f"Step {step.step_id} failed: {e}")
            step.result = {"error": str(e)}
            step.status = "failed"
            return {"error": str(e)}
    
    def _execute_rag_retrieval(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute RAG retrieval"""
        if not self.rag_retriever:
            return {"error": "RAG system not initialized"}
        
        query = step.parameters.get("query", "")
        tickers = step.parameters.get("tickers", [])
        top_k = step.parameters.get("top_k", 5)
        synthesis_mode = step.parameters.get("synthesis_mode", False)
        
        # Prepare metadata filter
        filter_metadata = {}
        if tickers:
            filter_metadata["ticker"] = tickers[0] if len(tickers) == 1 else {"$in": tickers}
        
        if synthesis_mode:
            # Final synthesis mode - use LLM with all context
            retrieval_result = self.rag_retriever.retrieve_with_context(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            # Combine with previous context
            context_summary = self._summarize_context(context)
            
            if self.llm_interface and retrieval_result["context"]:
                answer = self.llm_interface.generate_with_context(
                    query=query,
                    context=f"Previous Analysis:\n{context_summary}\n\nSEC Document Context:\n{retrieval_result['context']}",
                    temperature=0.7
                )
                return {
                    "answer": answer,
                    "sources": retrieval_result["sources"],
                    "context_used": True
                }
            else:
                return {
                    "answer": "Unable to generate synthesis - LLM or context unavailable",
                    "sources": retrieval_result.get("sources", [])
                }
        else:
            # Regular retrieval
            retrieval_result = self.rag_retriever.retrieve_with_context(
                query=query,
                top_k=top_k,
                filter_metadata=filter_metadata if filter_metadata else None
            )
            
            return {
                "context": retrieval_result["context"],
                "sources": retrieval_result["sources"],
                "source_count": retrieval_result["source_count"]
            }
    
    def _execute_financial_calculator(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute financial calculator"""
        tickers = step.parameters.get("tickers", ["AAPL"])
        ratios = step.parameters.get("ratios", ["current_ratio", "debt_to_equity", "roe"])
        
        results = {}
        for ticker in tickers:
            ticker_results = {}
            for ratio in ratios:
                try:
                    ratio_result = calculate_ratio(ticker, ratio)
                    ticker_results[ratio] = ratio_result
                except Exception as e:
                    ticker_results[ratio] = {"error": str(e)}
            results[ticker] = ticker_results
        
        return results
    
    def _execute_market_data(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute market data retrieval"""
        tickers = step.parameters.get("tickers", ["AAPL"])
        timeframe = step.parameters.get("timeframe", "annual")
        
        db = SessionLocal()
        try:
            market_data = {}
            for ticker in tickers:
                company = db.query(DimCompany).filter_by(ticker=ticker.upper()).first()
                if not company:
                    market_data[ticker] = {"error": "Company not found"}
                    continue
                
                # Get latest price
                latest_price = db.query(FactMarketPrice).filter_by(
                    company_id=company.company_id
                ).order_by(FactMarketPrice.created_at.desc()).first()
                
                # Get predictions
                predictions = db.query(FactPrediction).filter_by(
                    company_id=company.company_id
                ).order_by(FactPrediction.created_at.desc()).limit(3).all()
                
                market_data[ticker] = {
                    "company_name": company.name,
                    "latest_price": float(latest_price.close) if latest_price else None,
                    "latest_price_date": latest_price.created_at.isoformat() if latest_price else None,
                    "predictions": [
                        {
                            "date": pred.date_id,
                            "predicted_close": float(pred.predicted_close),
                            "confidence": float(pred.confidence),
                            "model_version": pred.model_version
                        }
                        for pred in predictions
                    ]
                }
            
            return market_data
            
        finally:
            db.close()
    
    def _execute_comparison_matrix(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute comparison matrix generation"""
        tickers = step.parameters.get("tickers", ["AAPL", "MSFT"])
        metrics = step.parameters.get("metrics", ["revenue", "debt", "cash", "roe"])
        
        comparison = {}
        for ticker in tickers:
            try:
                summary = get_company_metrics_summary(ticker)
                comparison[ticker] = summary
            except Exception as e:
                comparison[ticker] = {"error": str(e)}
        
        return comparison
    
    def _execute_risk_analysis(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute risk analysis"""
        tickers = step.parameters.get("tickers", ["AAPL"])
        
        db = SessionLocal()
        try:
            risk_data = {}
            for ticker in tickers:
                company = db.query(DimCompany).filter_by(ticker=ticker.upper()).first()
                if not company:
                    risk_data[ticker] = {"error": "Company not found"}
                    continue
                
                # Get latest risk metrics
                latest_risk = db.query(FactRiskMetrics).filter_by(
                    company_id=company.company_id
                ).order_by(FactRiskMetrics.created_at.desc()).first()
                
                if latest_risk:
                    risk_data[ticker] = {
                        "beta": float(latest_risk.beta),
                        "sharpe_ratio": float(latest_risk.sharpe_ratio),
                        "value_at_risk": float(latest_risk.value_at_risk),
                        "analysis_date": latest_risk.created_at.isoformat()
                    }
                else:
                    risk_data[ticker] = {"error": "No risk data available"}
            
            return risk_data
            
        finally:
            db.close()
    
    def _execute_portfolio_optimization(self, step: PlanningStep, context: Dict[str, Any]) -> Dict[str, Any]:
        """Execute portfolio optimization"""
        from app.agent.agent_engine import generate_portfolio_recommendation
        
        tickers = step.parameters.get("tickers", [])
        risk_profile = step.parameters.get("risk_profile", "moderate")
        
        # Generate portfolio recommendation
        portfolio = generate_portfolio_recommendation(
            capital=100000,  # Default $100k
            risk_profile=risk_profile,
            duration_years=5
        )
        
        return portfolio
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """Summarize context from previous steps"""
        summary_parts = []
        
        for step_id, step_data in context.items():
            if isinstance(step_data, dict) and "error" not in step_data:
                summary_parts.append(f"Step {step_id}: {str(step_data)[:200]}...")
        
        return "\n".join(summary_parts) if summary_parts else "No previous context available"
    
    def execute_plan(self, steps: List[PlanningStep]) -> Dict[str, Any]:
        """
        Execute all steps in a plan
        
        Args:
            steps: List of planning steps
            
        Returns:
            Complete execution results
        """
        context = {}
        results = []
        
        for step in steps:
            # Check if dependencies are satisfied
            dependencies_met = all(
                dep_id in context and "error" not in context[dep_id]
                for dep_id in step.dependencies
            )
            
            if not dependencies_met and step.dependencies:
                logger.warning(f"Step {step.step_id} dependencies not met, skipping")
                step.status = "skipped"
                continue
            
            # Execute step
            result = self.execute_step(step, context)
            context[step.step_id] = result
            results.append(step.to_dict())
        
        return {
            "steps_executed": len([s for s in steps if s.status == "completed"]),
            "steps_failed": len([s for s in steps if s.status == "failed"]),
            "steps_skipped": len([s for s in steps if s.status == "skipped"]),
            "results": results,
            "final_context": context
        }
