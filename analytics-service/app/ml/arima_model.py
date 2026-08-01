"""
ARIMA Forecaster - ARIMA implementation for time series forecasting
Uses statsmodels for autoregressive integrated moving average modeling
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger("marketmind.ml.arima")

try:
    from statsmodels.tsa.arima.model import ARIMA
    from statsmodels.tsa.stattools import adfuller
    from statsmodels.tsa.seasonal import seasonal_decompose
    STATSMODELS_AVAILABLE = True
except ImportError:
    STATSMODELS_AVAILABLE = False
    logger.warning("statsmodels not available, using fallback implementation")

class ARIMAForecaster:
    def __init__(self, p: int = 5, d: int = 1, q: int = 0):
        """
        Initialize ARIMA forecaster
        
        Args:
            p: Autoregressive order
            d: Differencing order  
            q: Moving average order
        """
        self.p = p
        self.d = d
        self.q = q
        self.model = None
        self.is_fitted = False
        self.best_order = None
        
    def _check_stationarity(self, series: pd.Series) -> bool:
        """
        Check if time series is stationary using Augmented Dickey-Fuller test
        
        Args:
            series: Time series data
            
        Returns:
            True if stationary, False otherwise
        """
        if not STATSMODELS_AVAILABLE:
            return True  # Assume stationary if statsmodels not available
        
        try:
            result = adfuller(series.dropna())
            p_value = result[1]
            return p_value < 0.05
        except Exception as e:
            logger.warning(f"Stationarity check failed: {e}")
            return True
    
    def _find_best_arima_order(self, series: pd.Series, max_p: int = 5, max_d: int = 2, max_q: int = 2) -> Tuple[int, int, int]:
        """
        Find best ARIMA order using grid search
        
        Args:
            series: Time series data
            max_p: Maximum p value to try
            max_d: Maximum d value to try  
            max_q: Maximum q value to try
            
        Returns:
            Best (p, d, q) order
        """
        if not STATSMODELS_AVAILABLE:
            return (self.p, self.d, self.q)
        
        best_aic = float('inf')
        best_order = (self.p, self.d, self.q)
        
        # Limited grid search to avoid long computation
        for p in range(1, min(max_p + 1, 4)):
            for d in range(0, min(max_d + 1, 2)):
                for q in range(0, min(max_q + 1, 2)):
                    try:
                        model = ARIMA(series, order=(p, d, q))
                        results = model.fit()
                        if results.aic < best_aic:
                            best_aic = results.aic
                            best_order = (p, d, q)
                    except:
                        continue
        
        logger.info(f"Best ARIMA order: {best_order} with AIC: {best_aic:.2f}")
        return best_order
    
    def fit(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Train ARIMA model on historical price data
        
        Args:
            df: DataFrame with columns: date, close
            forecast_horizon: Number of days to forecast ahead
            
        Returns:
            Training metrics
        """
        if not STATSMODELS_AVAILABLE:
            logger.warning("statsmodels not available, returning error")
            return {"error": "statsmodels not installed"}
        
        try:
            # Prepare time series
            series = df['close'].sort_values(df['date']).reset_index(drop=True)
            
            if len(series) < 30:
                logger.warning(f"Insufficient data for ARIMA: {len(series)} samples")
                return {"error": "Insufficient data for ARIMA (need at least 30 samples)"}
            
            # Check stationarity and find best order
            is_stationary = self._check_stationarity(series)
            if not is_stationary:
                logger.info("Series not stationary, will use differencing")
            
            # Find best ARIMA order
            self.best_order = self._find_best_arima_order(series)
            
            # Fit ARIMA model
            self.model = ARIMA(series, order=self.best_order)
            self.model_fit = self.model.fit()
            
            # Calculate in-sample predictions for evaluation
            predictions = self.model_fit.predict(start=1, end=len(series)-1)
            actual = series[1:]
            
            # Calculate metrics
            mae = np.mean(np.abs(actual - predictions))
            rmse = np.sqrt(np.mean((actual - predictions) ** 2))
            
            self.is_fitted = True
            
            metrics = {
                "mae": float(mae),
                "rmse": float(rmse),
                "training_samples": len(series),
                "forecast_horizon": forecast_horizon,
                "arima_order": self.best_order,
                "aic": float(self.model_fit.aic),
                "is_stationary": is_stationary
            }
            
            logger.info(f"ARIMA model trained: MAE={mae:.4f}, RMSE={rmse:.4f} Order={self.best_order}")
            return metrics
            
        except Exception as e:
            logger.error(f"ARIMA training failed: {e}")
            return {"error": str(e)}
    
    def predict(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Generate price predictions using trained ARIMA model
        
        Args:
            df: DataFrame with recent price data
            forecast_horizon: Number of days to forecast
            
        Returns:
            Predictions with confidence intervals
        """
        if not self.is_fitted:
            logger.warning("Model not fitted, returning baseline predictions")
            return {"error": "Model not fitted"}
        
        try:
            # Get current price
            current_price = df['close'].iloc[-1]
            
            # Make forecast
            forecast = self.model_fit.forecast(steps=forecast_horizon)
            
            # Calculate confidence intervals
            forecast_result = self.model_fit.get_forecast(steps=forecast_horizon)
            conf_int = forecast_result.conf_int()
            
            predictions = []
            for i in range(forecast_horizon):
                predicted_price = forecast.iloc[i]
                predicted_return = (predicted_price - current_price) / current_price
                
                # Confidence interval
                lower_bound = conf_int.iloc[i, 0]
                upper_bound = conf_int.iloc[i, 1]
                
                # Calculate confidence based on interval width
                interval_width = (upper_bound - lower_bound) / (2 * predicted_price)
                confidence = max(0.5, min(0.95, 1.0 - interval_width))
                
                predictions.append({
                    "day": i + 1,
                    "predicted_close": float(predicted_price),
                    "predicted_return": float(predicted_return),
                    "confidence": float(confidence),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                })
            
            return {
                "current_price": float(current_price),
                "predictions": predictions,
                "model_type": "arima",
                "forecast_horizon": forecast_horizon,
                "arima_order": self.best_order
            }
            
        except Exception as e:
            logger.error(f"ARIMA prediction failed: {e}")
            return {"error": str(e)}
    
    def get_model_summary(self) -> Dict[str, Any]:
        """Get ARIMA model summary statistics"""
        if not self.is_fitted:
            return {}
        
        return {
            "arima_order": self.best_order,
            "aic": float(self.model_fit.aic),
            "bic": float(self.model_fit.bic),
            "params": self.model_fit.params.to_dict() if hasattr(self.model_fit, 'params') else {}
        }
