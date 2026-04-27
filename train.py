"""Training script for EV demand forecasting model"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from utils.data_generator import generate_synthetic_charging_data, create_features_for_model, save_data
from model.forecasting_model import DemandForecaster
from configs.config import (
    SYNTHETIC_DATA_PATH, MODEL_PATH, FEATURE_SCALER_PATH,
    NUM_STATIONS, SYNTHETIC_DATA_POINTS
)


def train_model():
    """Generate data and train the forecasting model"""
    
    print("=" * 60)
    print("EV DEMAND FORECASTING - Model Training")
    print("=" * 60)
    
    # Step 1: Generate synthetic data
    print("\n[1/3] Generating synthetic charging data...")
    synthetic_data = generate_synthetic_charging_data(
        num_stations=NUM_STATIONS,
        num_hours=SYNTHETIC_DATA_POINTS
    )
    print(f"✓ Generated {len(synthetic_data)} records across {NUM_STATIONS} stations")
    
    # Step 2: Create features
    print("\n[2/3] Creating features for model...")
    featured_data = create_features_for_model(synthetic_data)
    save_data(featured_data, SYNTHETIC_DATA_PATH)
    print(f"✓ Features created and saved to {SYNTHETIC_DATA_PATH}")
    
    # Step 3: Train model
    print("\n[3/3] Training XGBoost model...")
    forecaster = DemandForecaster()
    metrics = forecaster.train(featured_data)
    
    # Save model
    os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
    forecaster.save(MODEL_PATH, FEATURE_SCALER_PATH)
    print(f"✓ Model saved to {MODEL_PATH}")
    
    # Show feature importance
    print("\n[Info] Top 10 Important Features:")
    importance = forecaster.get_feature_importance(top_n=10)
    print(importance.to_string(index=False))
    
    print("\n" + "=" * 60)
    print("Training Complete!")
    print("=" * 60)
    
    return forecaster, featured_data


if __name__ == "__main__":
    train_model()
