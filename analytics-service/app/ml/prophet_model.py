"""
Prophet Forecaster - Facebook Prophet implementation for time series forecasting
Handles seasonality, holidays, and trend changes for stock price prediction
"""

import logging
import numpy as np
import pandas as pd
from typing import Dict, Any, List, Optional
from datetime import datetime, timedelta

logger = logging.getLogger("marketmind.ml.prophet")

try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
except ImportError:
    PROPHET_AVAILABLE = False
    logger.warning("Prophet not available, using fallback implementation")

class ProphetForecaster:
    def __init__(self, yearly_seasonality: bool = True, weekly_seasonality: bool = False, daily_seasonality: bool = False):
        """
        Initialize Prophet forecaster
        
        Args:
            yearly_seasonality: Enable yearly seasonality
            weekly_seasonality: Enable weekly seasonality  
            daily_seasonality: Enable daily seasonality
        """
        self.yearly_seasonality = yearly_seasonality
        self.weekly_seasonality = weekly_seasonality
        self.daily_seasonality = daily_seasonality
        self.model = None
        self.is_fitted = False
        
    def _prepare_prophet_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Prepare data in Prophet format (ds, y columns)
        
        Args:
            df: DataFrame with date and close columns
            
        Returns:
            DataFrame in Prophet format
        """
        df_prophet = df.copy()
        df_prophet = df_prophet.rename(columns={'date': 'ds', 'close': 'y'})
        df_prophet = df_prophet[['ds', 'y']].sort_values('ds')
        return df_prophet
    
    def fit(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Train Prophet model on historical price data
        
        Args:
            df: DataFrame with columns: date, close
            forecast_horizon: Number of days to forecast ahead
            
        Returns:
            Training metrics
        """
        if not PROPHET_AVAILABLE:
            logger.warning("Prophet not available, returning error")
            return {"error": "Prophet not installed"}
        
        try:
            # Prepare data
            df_prophet = self._prepare_prophet_data(df)
            
            if len(df_prophet) < 30:
                logger.warning(f"Insufficient data for Prophet: {len(df_prophet)} samples")
                return {"error": "Insufficient data for Prophet (need at least 30 samples)"}
            
            # Initialize Prophet model
            self.model = Prophet(
                yearly_seasonality=self.yearly_seasonality,
                weekly_seasonality=self.weekly_seasonality,
                daily_seasonality=self.daily_seasonality,
                changepoint_prior_scale=0.05,  # Less flexible trend for financial data
                seasonality_prior_scale=10.0,   # Stronger seasonality
                holidays_prior_scale=10.0,
                interval_width=0.8,            # 80% confidence intervals
                mcmc_samples=0                 # Faster sampling
            )
            
            # Fit model
            self.model.fit(df_prophet)
            
            # Make in-sample predictions for evaluation
            df_forecast = self.model.predict(df_prophet)
            
            # Calculate metrics
            y_true = df_prophet['y'].values
            y_pred = df_forecast['yhat'].values
            
            mae = np.mean(np.abs(y_true - y_pred))
            rmse = np.sqrt(np.mean((y_true - y_pred) ** 2))
            
            self.is_fitted = True
            
            metrics = {
                "mae": float(mae),
                "rmse": float(rmse),
                "training_samples": len(df_prophet),
                "forecast_horizon": forecast_horizon,
                "changepoints": len(self.model.changepoints)
            }
            
            logger.info(f"Prophet model trained: MAE={mae:.4f}, RMSE={rmse:.4f}")
            return metrics
            
        except Exception as e:
            logger.error(f"Prophet training failed: {e}")
            return {"error": str(e)}
    
    def predict(self, df: pd.DataFrame, forecast_horizon: int = 3) -> Dict[str, Any]:
        """
        Generate price predictions using trained Prophet model
        
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
            # Prepare data
            df_prophet = self._prepare_prophet_data(df)
            
            # Create future dataframe
            future = self.model.make_future_dataframe(periods=forecast_horizon)
            
            # Make predictions
            forecast = self.model.predict(future)
            
            # Get the forecasted values (last forecast_horizon rows)
            forecast_values = forecast.tail(forecast_horizon)
            
            current_price = df['close'].iloc[-1]
            
            predictions = []
            for i, row in forecast_values.iterrows():
                day_num = i - len(forecast) + forecast_horizon + 1
                predicted_price = row['yhat']
                predicted_return = (predicted_price - current_price) / current_price
                
                # Confidence interval
                lower_bound = row['yhat_lower']
                upper_bound = row['yhat_upper']
                confidence = 0.8  # Prophet's default interval width
                
                predictions.append({
                    "day": day_num,
                    "predicted_close": float(predicted_price),
                    "predicted_return": float(predicted_return),
                    "confidence": float(confidence),
                    "lower_bound": float(lower_bound),
                    "upper_bound": float(upper_bound)
                })
            
            return {
                "current_price": float(current_price),
                "predictions": predictions,
                "model_type": "prophet",
                "forecast_horizon": forecast_horizon
            }
            
        except Exception as e:
            logger.error(f"Prophet prediction failed: {e}")
            return {"error": str(e)}
    
    def get_components(self) -> Dict[str, Any]:
        """Get decomposition of time series components"""
        if not self.is_fitted:
            return {}
        
        # Return component information
        return {
            "trend": "enabled",
            "yearly_seasonality": self.yearly_seasonality,
            "weekly_seasonality": self.weekly_seasonality,
            "daily_seasonality": self.daily_seasonality
        }
