"""Configuration settings for EV demand forecasting system"""

# Model settings
MODEL_TYPE = "xgboost"  # Options: xgboost, lstm, hybrid
FORECAST_HORIZON = 24  # hours ahead to forecast
LOOKBACK_WINDOW = 168  # 7 days of history for features

# Station settings
NUM_STATIONS = 10
STATION_CAPACITY_MIN = 50  # kW
STATION_CAPACITY_MAX = 500  # kW

# Alert thresholds
UTILIZATION_WARNING = 0.75  # 75% capacity
UTILIZATION_CRITICAL = 0.90  # 90% capacity
PRICE_SURGE_THRESHOLD = 0.80  # Increase pricing at 80% utilization

# Data generation (for demo/testing)
SYNTHETIC_DATA_POINTS = 2016  # 84 days of hourly data per station

# Dashboard settings
HOST = "0.0.0.0"
PORT = 5000
DEBUG = True

# Model paths
MODEL_PATH = "models/xgboost_model.pkl"
FEATURE_SCALER_PATH = "models/scaler.pkl"

# Data paths
TRAINING_DATA_PATH = "data/training_data.csv"
SYNTHETIC_DATA_PATH = "data/synthetic_data.csv"
