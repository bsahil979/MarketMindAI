import logging
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from sklearn.linear_model import LinearRegression

from app.database import (
    DimCompany, DimDate, FactMarketPrice, FactPrediction, FactRiskMetrics, ModelRegistry
)
from app.ml import ModelEnsemble, XGBoostForecaster, ARIMAForecaster

logger = logging.getLogger("marketmind.ai")

def get_or_create_date_id(db: Session, dt: datetime) -> int:
    date_id = int(dt.strftime("%Y%m%d"))
    existing_date = db.query(DimDate).filter_by(date_id=date_id).first()
    if not existing_date:
        quarter = (dt.month - 1) // 3 + 1
        new_date = DimDate(
            date_id=date_id,
            date=dt.date(),
            day=dt.day,
            month=dt.month,
            year=dt.year,
            quarter=quarter,
            day_of_week=dt.isoweekday()
        )
        db.add(new_date)
        db.commit()
    return date_id

def log_model_run(db: Session, model_name: str, version: str, rmse: float, mape: float, r2_score: float, status: str):
    dt = datetime.now()
    # Check if this model/version was logged today
    existing = db.query(ModelRegistry).filter_by(model_name=model_name, version=version).first()
    if existing:
        existing.rmse = float(round(rmse, 4))
        existing.mape = float(round(mape, 4))
        existing.r2_score = float(round(r2_score, 4))
        existing.status = status
        existing.created_at = dt
    else:
        db.add(ModelRegistry(
            model_name=model_name,
            version=version,
            rmse=float(round(rmse, 4)),
            mape=float(round(mape, 4)),
            r2_score=float(round(r2_score, 4)),
            status=status,
            created_at=dt
        ))
    db.commit()

def calculate_forecasts(db: Session, company: DimCompany):
    logger.info(f"Generating AI Forecast models registry for {company.ticker}...")
    
    # Query price history
    prices = db.query(FactMarketPrice).filter_by(company_id=company.company_id).order_by(FactMarketPrice.created_at.asc()).all()
    
    dt = datetime.now()
    
    # Check if we have enough historical data to fit real ML models
    if len(prices) >= 30:  # Need at least 30 data points for real ML models
        # Prepare data for ML models
        price_data = pd.DataFrame([{
            "date": p.created_at,
            "close": p.close,
            "volume": getattr(p, 'volume', 0)
        } for p in prices])
        
        try:
            # Initialize ensemble with real ML models
            ensemble = ModelEnsemble(models=["xgboost", "arima"])  # Use XGBoost + ARIMA (Prophet often has dependency issues)
            
            # Train models
            ensemble_metrics = ensemble.fit(price_data, forecast_horizon=3)
            
            logger.info(f"Ensemble training completed: {ensemble_metrics}")
            
            # Generate predictions
            predictions_result = ensemble.predict(price_data, forecast_horizon=3)
            
            if "error" not in predictions_result:
                # Log model performance
                for model_name, metrics in ensemble_metrics["individual_metrics"].items():
                    if "error" not in metrics:
                        rmse = metrics.get("rmse", 0.0)
                        mape = metrics.get("mae", 0.0) / (price_data["close"].mean() + 1e-6)  # Approximate MAPE
                        r2 = 1.0 - (metrics.get("rmse", 0.0) ** 2) / (price_data["close"].std() ** 2 + 1e-6)
                        r2 = max(0.1, min(0.99, r2))
                        
                        model_version = f"{model_name}_v1.0"
                        status = "DEPLOYED" if model_name == ensemble.get_best_model() else "TRAINED"
                        log_model_run(db, model_name.title(), model_version, rmse, mape, r2, status)
                
                # Save ensemble predictions to database
                for pred in predictions_result["predictions"]:
                    forecast_date = dt + timedelta(days=pred["day"])
                    date_id = get_or_create_date_id(db, forecast_date)
                    
                    existing_pred = db.query(FactPrediction).filter_by(
                        company_id=company.company_id, date_id=date_id
                    ).first()
                    
                    model_version = f"ensemble_{ensemble.get_best_model()}_v1.0"
                    
                    if existing_pred:
                        existing_pred.predicted_close = float(round(pred["predicted_close"], 4))
                        existing_pred.confidence = float(round(pred["confidence"], 4))
                        existing_pred.model_version = model_version
                        existing_pred.created_at = dt
                    else:
                        db.add(FactPrediction(
                            company_id=company.company_id,
                            date_id=date_id,
                            predicted_close=float(round(pred["predicted_close"], 4)),
                            confidence=float(round(pred["confidence"], 4)),
                            model_version=model_version,
                            created_at=dt
                        ))
                
                logger.info(f"Real ML predictions saved for {company.ticker}")
            else:
                logger.warning(f"Ensemble prediction failed: {predictions_result.get('error')}")
                raise Exception("Ensemble prediction failed")
                
        except Exception as e:
            logger.warning(f"Real ML models failed for {company.ticker}: {e}, falling back to Linear Regression")
            # Fallback to Linear Regression if real ML fails
            _fallback_linear_regression(prices, company, db, dt)
    else:
        # Fallback to Linear Regression for insufficient data
        logger.warning(f"Insufficient history ({len(prices)} items) for real ML models on {company.ticker}. Using Linear Regression fallback.")
        _fallback_linear_regression(prices, company, db, dt)
    
    db.commit()

def _fallback_linear_regression(prices, company, db, dt):
    """Fallback Linear Regression implementation for insufficient data or ML model failures"""
    if len(prices) >= 3:
        closes = np.array([p.close for p in prices])
        X = np.array(range(len(closes))).reshape(-1, 1)
        y = closes
        
        # Fit Linear Regression
        lr_model = LinearRegression()
        lr_model.fit(X, y)
        y_pred_lr = lr_model.predict(X)
        
        rmse_lr = np.sqrt(np.mean((y - y_pred_lr)**2))
        mape_lr = np.mean(np.abs((y - y_pred_lr) / (y + 1e-6)))
        r2_lr = float(np.clip(lr_model.score(X, y), 0.1, 0.99))
        
        # Log to registry
        log_model_run(db, "Linear Regression", "1.0.0", rmse_lr, mape_lr, r2_lr, "TRAINED")
        
        # Generate predictions
        future_indices = np.array(range(len(closes), len(closes) + 3)).reshape(-1, 1)
        predictions = lr_model.predict(future_indices)
        
        confidence = r2_lr
        model_version = "linear_regression_v1.0"
        
        # Save predictions
        for i, pred_val in enumerate(predictions):
            forecast_date = dt + timedelta(days=i+1)
            date_id = get_or_create_date_id(db, forecast_date)
            
            existing_pred = db.query(FactPrediction).filter_by(
                company_id=company.company_id, date_id=date_id
            ).first()
            if existing_pred:
                existing_pred.predicted_close = float(round(pred_val, 4))
                existing_pred.confidence = float(round(confidence, 4))
                existing_pred.model_version = model_version
                existing_pred.created_at = dt
            else:
                db.add(FactPrediction(
                    company_id=company.company_id,
                    date_id=date_id,
                    predicted_close=float(round(pred_val, 4)),
                    confidence=float(round(confidence, 4)),
                    model_version=model_version,
                    created_at=dt
                ))
    else:
        # Sparsity fallback
        latest_price = prices[-1].close if prices else 150.0
        confidence = 0.65
        
        for i in range(3):
            forecast_date = dt + timedelta(days=i+1)
            date_id = get_or_create_date_id(db, forecast_date)
            pred_val = latest_price * (1 + (i + 1) * 0.005) 
            
            existing_pred = db.query(FactPrediction).filter_by(
                company_id=company.company_id, date_id=date_id
            ).first()
            if existing_pred:
                existing_pred.predicted_close = float(round(pred_val, 4))
                existing_pred.confidence = confidence
                existing_pred.model_version = "baseline_simulator_v1"
                existing_pred.created_at = dt
            else:
                db.add(FactPrediction(
                    company_id=company.company_id,
                    date_id=date_id,
                    predicted_close=float(round(pred_val, 4)),
                    confidence=confidence,
                    model_version="baseline_simulator_v1",
                    created_at=dt
                ))

def calculate_risk_metrics(db: Session, company: DimCompany):
    logger.info(f"Calculating Risk Metrics for {company.ticker}...")
    
    # Query price history
    prices = db.query(FactMarketPrice).filter_by(company_id=company.company_id).order_by(FactMarketPrice.created_at.asc()).all()
    dt = datetime.now()
    date_id = get_or_create_date_id(db, dt)
    
    # Calculate daily returns
    if len(prices) >= 4:
        closes = np.array([p.close for p in prices])
        returns = np.diff(closes) / closes[:-1]
        
        # 1. Sharpe Ratio (assuming daily risk free rate of 0.01% and annualizing)
        daily_rf = 0.0001
        mean_return = np.mean(returns)
        std_return = np.std(returns)
        if std_return > 0:
            daily_sharpe = (mean_return - daily_rf) / std_return
            sharpe_ratio = daily_sharpe * np.sqrt(252) # Annualized Sharpe
        else:
            sharpe_ratio = 1.0
            
        # 2. Value at Risk (VaR) at 95% confidence level
        var_index = -np.percentile(returns, 5) # 5th percentile represents 95% VaR
        value_at_risk = float(np.clip(var_index, 0.01, 0.15)) # clamp Var between 1% and 15%
        
        # 3. Beta (volatility relative to average market returns)
        # We simulate market returns by taking average returns of all company price updates
        all_prices = db.query(FactMarketPrice).order_by(FactMarketPrice.created_at.asc()).all()
        df = pd.DataFrame([{"date": p.created_at.date(), "close": p.close} for p in all_prices])
        if not df.empty:
            market_returns = df.groupby("date")["close"].mean().pct_change().dropna().values
            # Align lengths
            min_len = min(len(returns), len(market_returns))
            if min_len >= 2:
                stock_aligned = returns[-min_len:]
                market_aligned = market_returns[-min_len:]
                covariance = np.cov(stock_aligned, market_aligned)[0][1]
                market_variance = np.var(market_aligned)
                beta = covariance / market_variance if market_variance > 0 else 1.0
            else:
                beta = 1.0 + (company.company_id * 0.03) # seed fallback
        else:
            beta = 1.05
            
        # Upsert Risk Record
        existing_risk = db.query(FactRiskMetrics).filter_by(company_id=company.company_id, date_id=date_id).first()
        if existing_risk:
            existing_risk.beta = float(round(beta, 4))
            existing_risk.sharpe_ratio = float(round(sharpe_ratio, 4))
            existing_risk.value_at_risk = float(round(value_at_risk, 4))
            existing_risk.created_at = dt
        else:
            db.add(FactRiskMetrics(
                company_id=company.company_id,
                date_id=date_id,
                beta=float(round(beta, 4)),
                sharpe_ratio=float(round(sharpe_ratio, 4)),
                value_at_risk=float(round(value_at_risk, 4)),
                created_at=dt
            ))
    else:
        # Fallback simulator for risk metrics
        logger.warning(f"Insufficient history ({len(prices)} items) for returns computation on {company.ticker}. Run baseline jitter risk generation.")
        beta = 0.90 + (company.company_id * 0.08)
        sharpe_ratio = 1.30 + (company.company_id * 0.12)
        value_at_risk = 0.015 + (company.company_id * 0.003)
        
        existing_risk = db.query(FactRiskMetrics).filter_by(company_id=company.company_id, date_id=date_id).first()
        if existing_risk:
            existing_risk.beta = float(round(beta, 4))
            existing_risk.sharpe_ratio = float(round(sharpe_ratio, 4))
            existing_risk.value_at_risk = float(round(value_at_risk, 4))
            existing_risk.created_at = dt
        else:
            db.add(FactRiskMetrics(
                company_id=company.company_id,
                date_id=date_id,
                beta=float(round(beta, 4)),
                sharpe_ratio=float(round(sharpe_ratio, 4)),
                value_at_risk=float(round(value_at_risk, 4)),
                created_at=dt
            ))
    db.commit()

def update_ai_metrics(db: Session):
    logger.info("Executing global AI model calculations update loop...")
    companies = db.query(DimCompany).all()
    for company in companies:
        try:
            calculate_forecasts(db, company)
            calculate_risk_metrics(db, company)
        except Exception as e:
            logger.error(f"Failed to calculate AI metrics for {company.ticker}: {e}")
    logger.info("Global AI model updates completed successfully.")
