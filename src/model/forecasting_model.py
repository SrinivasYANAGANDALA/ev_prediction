"""XGBoost forecasting model for EV charging demand"""

import numpy as np
import pandas as pd
import xgboost as xgb
import joblib
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
import os


class DemandForecaster:
    """XGBoost model for predicting EV charging demand"""
    
    def __init__(self, model_path=None, scaler_path=None):
        """
        Initialize the forecaster.
        
        Args:
            model_path: Path to saved model
            scaler_path: Path to saved feature scaler
        """
        self.model = None
        self.scaler = None
        self.feature_names = None
        self.model_path = model_path
        self.scaler_path = scaler_path
        
        if model_path and os.path.exists(model_path):
            self.load(model_path, scaler_path)
    
    def prepare_features(self, df):
        """Prepare features for model training/prediction"""
        
        # Select feature columns (exclude target and identifiers)
        exclude_cols = ['timestamp', 'station_id', 'kWh_used', 'charger_type', 'location_type']
        feature_cols = [col for col in df.columns if col not in exclude_cols]
        
        self.feature_names = feature_cols
        X = df[feature_cols].copy()
        
        # Handle categorical features if needed
        categorical_features = []
        for col in feature_cols:
            if df[col].dtype == 'object':
                categorical_features.append(col)
        
        return X, feature_cols
    
    def train(self, df, test_size=0.2, random_state=42):
        """
        Train the XGBoost model.
        
        Args:
            df: DataFrame with features (must include 'kWh_used' as target)
            test_size: Fraction of data for testing
            random_state: For reproducibility
        
        Returns:
            dict: Training metrics
        """
        
        # Prepare features
        X, feature_names = self.prepare_features(df)
        y = df['kWh_used'].values
        
        # Split data
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=random_state
        )
        
        # Scale features
        self.scaler = StandardScaler()
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # Train XGBoost model
        self.model = xgb.XGBRegressor(
            n_estimators=200,
            max_depth=7,
            learning_rate=0.05,
            subsample=0.8,
            colsample_bytree=0.8,
            random_state=random_state,
            verbosity=1
        )
        
        self.model.fit(
            X_train_scaled, y_train,
            eval_set=[(X_test_scaled, y_test)],
            verbose=False
        )
        
        # Evaluate
        y_pred = self.model.predict(X_test_scaled)
        
        metrics = {
            'mae': mean_absolute_error(y_test, y_pred),
            'rmse': np.sqrt(mean_squared_error(y_test, y_pred)),
            'r2': r2_score(y_test, y_pred),
            'train_size': len(X_train),
            'test_size': len(X_test)
        }
        
        print(f"\n=== Model Training Metrics ===")
        print(f"MAE: {metrics['mae']:.2f} kWh")
        print(f"RMSE: {metrics['rmse']:.2f} kWh")
        print(f"R² Score: {metrics['r2']:.4f}")
        
        return metrics
    
    def predict(self, df):
        """
        Make predictions for stations.
        
        Args:
            df: DataFrame with features
        
        Returns:
            np.array: Predicted demand values
        """
        
        if self.model is None:
            raise ValueError("Model not trained or loaded")
        
        X, _ = self.prepare_features(df)
        X_scaled = self.scaler.transform(X)
        predictions = self.model.predict(X_scaled)
        
        return np.maximum(predictions, 0)  # Ensure non-negative
    
    def save(self, model_path, scaler_path):
        """Save model and scaler"""
        os.makedirs(os.path.dirname(model_path), exist_ok=True)
        joblib.dump(self.model, model_path)
        joblib.dump(self.scaler, scaler_path)
        print(f"Model saved to {model_path}")
        print(f"Scaler saved to {scaler_path}")
    
    def load(self, model_path, scaler_path):
        """Load pre-trained model and scaler"""
        if os.path.exists(model_path) and os.path.exists(scaler_path):
            self.model = joblib.load(model_path)
            self.scaler = joblib.load(scaler_path)
            print(f"Model loaded from {model_path}")
        else:
            raise FileNotFoundError(f"Model files not found at {model_path} or {scaler_path}")
    
    def get_feature_importance(self, top_n=10):
        """Get top N important features"""
        if self.model is None:
            return None
        
        importance_df = pd.DataFrame({
            'feature': self.feature_names,
            'importance': self.model.feature_importances_
        }).sort_values('importance', ascending=False)
        
        return importance_df.head(top_n)
