"""
Model Ensemble - Combines multiple forecasting models for improved accuracy
Uses weighted averaging and model selection based on performance
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from .xgboost_model import XGBoostForecaster
from .prophet_model import ProphetForecaster
from .arima_model import ARIMAForecaster

logger = logging.getLogger("marketmind.ml.ensemble")

class ModelEnsemble:
    def __init__(self, models: Optional[List[str]] = None):
        """
        Initialize model ensemble
        
        Args:
            models: List of model names to include ("xgboost", "prophet", "arima")
        """
        self.models = models or ["xgboost", "arima"]  # Default to XGBoost + ARIMA (Prophet often has dependency issues)
        self.forecasters = {}
        self.model_weights = {}
        self.is_fitted = False
        
        # Initialize forecasters
        if "xgboost" in self.models:
            self.forecasters["xgboost"] = XGBoostForecaster()
        if "prophet" in self.models:
            self.forecasters["prophet"] = ProphetForecaster()
        if "arima" in self.models:
            self.forecasters["arima"] = ARIMAForecaster()
    
    def fit(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Train all models in the ensemble
        
        Args:
            df: DataFrame with columns: date, close, volume (optional)
            forecast_horizon: Number of days to forecast
            
        Returns:
            Training metrics for all models
        """
        all_metrics = {}
        model_errors = {}
        
        for model_name, forecaster in self.forecasters.items():
            try:
                logger.info(f"Training {model_name} model...")
                metrics = forecaster.fit(df, forecast_horizon)
                all_metrics[model_name] = metrics
                
                # Store error for weighting (lower error = higher weight)
                if "error" not in metrics:
                    mae = metrics.get("mae", float('inf'))
                    model_errors[model_name] = mae
                else:
                    logger.warning(f"{model_name} training failed: {metrics.get('error')}")
                    
            except Exception as e:
                logger.error(f"Error training {model_name}: {e}")
                all_metrics[model_name] = {"error": str(e)}
        
        # Calculate weights based on inverse MAE
        if model_errors:
            total_inverse_error = sum(1.0 / (error + 1e-6) for error in model_errors.values())
            for model_name, error in model_errors.items():
                weight = (1.0 / (error + 1e-6)) / total_inverse_error
                self.model_weights[model_name] = weight
                logger.info(f"{model_name} weight: {weight:.3f} (MAE: {error:.4f})")
        else:
            # Equal weights if no successful models
            for model_name in self.forecasters.keys():
                self.model_weights[model_name] = 1.0 / len(self.forecasters)
        
        self.is_fitted = len([m for m in all_metrics.values() if "error" not in m]) > 0
        
        return {
            "individual_metrics": all_metrics,
            "ensemble_weights": self.model_weights,
            "successful_models": len([m for m in all_metrics.values() if "error" not in m]),
            "total_models": len(self.forecasters)
        }
    
    def predict(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Generate ensemble predictions
        
        Args:
            df: DataFrame with recent price data
            forecast_horizon: Number of days to forecast
            
        Returns:
            Ensemble predictions with confidence intervals
        """
        if not self.is_fitted:
            logger.warning("Ensemble not fitted, returning baseline predictions")
            return {"error": "Ensemble not fitted"}
        
        all_predictions = {}
        successful_predictions = {}
        
        # Get predictions from each model
        for model_name, forecaster in self.forecasters.items():
            try:
                if forecaster.is_fitted:
                    prediction = forecaster.predict(df, forecast_horizon)
                    if "error" not in prediction:
                        all_predictions[model_name] = prediction
                        successful_predictions[model_name] = True
                    else:
                        logger.warning(f"{model_name} prediction failed: {prediction.get('error')}")
            except Exception as e:
                logger.error(f"Error predicting with {model_name}: {e}")
        
        if not all_predictions:
            return {"error": "No successful predictions from any model"}
        
        # Ensemble predictions using weighted average
        current_price = df['close'].iloc[-1]
        ensemble_predictions = []
        
        for day in range(1, forecast_horizon + 1):
            day_prices = []
            day_weights = []
            
            for model_name, pred in all_predictions.items():
                if day <= len(pred["predictions"]):
                    day_pred = pred["predictions"][day - 1]
                    day_prices.append(day_pred["predicted_close"])
                    day_weights.append(self.model_weights.get(model_name, 1.0))
            
            if day_prices:
                # Weighted average
                weighted_price = np.average(day_prices, weights=day_weights)
                weighted_return = (weighted_price - current_price) / current_price
                
                # Calculate ensemble confidence (average of individual confidences)
                day_confidences = []
                for model_name, pred in all_predictions.items():
                    if day <= len(pred["predictions"]):
                        day_confidences.append(pred["predictions"][day - 1]["confidence"])
                
                ensemble_confidence = np.mean(day_confidences) if day_confidences else 0.75
                
                # Calculate ensemble bounds (simple range)
                if day_prices:
                    lower_bound = min(day_prices)
                    upper_bound = max(day_prices)
                else:
                    lower_bound = weighted_price * 0.95
                    upper_bound = weighted_price * 1.05
                
                ensemble_predictions.append({
                    "day": day,
                    "predicted_close": float(weighted_price),
                    "predicted_return": float(weighted_return),
                    "confidence": float(ensemble_confidence),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound),
                    "individual_predictions": {
                        model_name: all_predictions[model_name]["predictions"][day - 1]
                        for model_name in all_predictions.keys()
                        if day <= len(all_predictions[model_name]["predictions"])
                    }
                })
        
        return {
            "current_price": float(current_price),
            "predictions": ensemble_predictions,
            "model_type": "ensemble",
            "forecast_horizon": forecast_horizon,
            "ensemble_weights": self.model_weights,
            "individual_predictions": all_predictions,
            "successful_models": len(successful_predictions)
        }
    
    def get_best_model(self) -> Optional[str]:
        """Get the name of the best performing model"""
        if not self.model_weights:
            return None
        return max(self.model_weights, key=self.model_weights.get)
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about all models in the ensemble"""
        return {
            "models": self.models,
            "weights": self.model_weights,
            "is_fitted": self.is_fitted,
            "best_model": self.get_best_model()
        }
