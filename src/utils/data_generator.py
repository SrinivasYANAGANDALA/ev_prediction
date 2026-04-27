"""Synthetic data generator for EV charging demand"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import os

def generate_synthetic_charging_data(
    num_stations=10,
    num_hours=2016,  # 84 days
    random_seed=42
):
    """
    Generate realistic synthetic EV charging demand data.
    
    Args:
        num_stations: Number of charging stations
        num_hours: Number of hourly records
        random_seed: For reproducibility
    
    Returns:
        pd.DataFrame with charging data
    """
    np.random.seed(random_seed)
    
    start_date = datetime(2023, 1, 1)
    data = []
    
    for station_id in range(1, num_stations + 1):
        # Station characteristics
        base_capacity = np.random.uniform(100, 500)  # kW
        connector_count = np.random.randint(4, 20)
        location_type = np.random.choice(['urban', 'highway', 'suburban'])
        
        for hour_offset in range(num_hours):
            timestamp = start_date + timedelta(hours=hour_offset)
            hour_of_day = timestamp.hour
            day_of_week = timestamp.weekday()
            is_weekend = 1 if day_of_week >= 5 else 0
            is_holiday = 1 if timestamp.month in [12, 1] and timestamp.day in [25, 1] else 0
            
            # Demand patterns based on time and location
            hourly_demand = base_capacity * _get_demand_multiplier(
                hour_of_day, location_type, is_weekend
            )
            
            # Add realistic variability
            noise = np.random.normal(0, hourly_demand * 0.15)
            hourly_demand = max(0, hourly_demand + noise)
            
            # Sessions count and duration
            sessions_count = max(1, int(hourly_demand / 30 + np.random.poisson(2)))
            avg_charging_duration = np.random.uniform(1.5, 4)  # hours
            
            # Weather simulation
            temperature = 15 + 15 * np.sin(2 * np.pi * hour_offset / 8760) + np.random.normal(0, 5)
            rain_prob = 0.3 if temperature < 10 else 0.2
            is_raining = 1 if np.random.random() < rain_prob else 0
            wind_speed = np.random.exponential(8)
            
            # Events/context
            event_flag = 1 if np.random.random() < 0.05 else 0
            local_traffic = np.random.uniform(30, 100)
            area_activity = np.random.uniform(20, 100)
            
            data.append({
                'timestamp': timestamp,
                'station_id': station_id,
                'hour': hour_of_day,
                'day_of_week': day_of_week,
                'is_weekend': is_weekend,
                'is_holiday': is_holiday,
                'sessions_count': sessions_count,
                'kWh_used': hourly_demand,
                'avg_charging_duration': avg_charging_duration,
                'temperature': temperature,
                'is_raining': is_raining,
                'wind_speed': wind_speed,
                'event_flag': event_flag,
                'local_traffic': local_traffic,
                'area_activity': area_activity,
                'connector_count': connector_count,
                'charger_type': np.random.choice(['DC', 'AC']),
                'station_capacity': base_capacity,
                'location_type': location_type,
            })
    
    df = pd.DataFrame(data)
    return df.sort_values(['station_id', 'timestamp']).reset_index(drop=True)


def _get_demand_multiplier(hour_of_day, location_type, is_weekend):
    """Calculate hourly demand multiplier based on time and location"""
    
    if location_type == 'urban':
        if is_weekend:
            # Weekend: peak mid-day
            multiplier = 0.3 + 0.6 * np.sin(2 * np.pi * (hour_of_day - 6) / 24)
        else:
            # Weekday: peak morning and evening
            morning_peak = 0.7 if 6 <= hour_of_day <= 9 else 0.2
            evening_peak = 0.8 if 17 <= hour_of_day <= 20 else morning_peak
            multiplier = evening_peak
    
    elif location_type == 'highway':
        # Highway: steady throughout day, slight peak during travel hours
        multiplier = 0.5 + 0.3 * (1 if 8 <= hour_of_day <= 10 or 15 <= hour_of_day <= 18 else 0)
    
    else:  # suburban
        # Suburban: peaks at morning commute, evening, and weekends
        if is_weekend:
            multiplier = 0.6
        else:
            multiplier = 0.7 if 7 <= hour_of_day <= 9 or 17 <= hour_of_day <= 19 else 0.4
    
    # Night-time reduction
    if hour_of_day < 5 or hour_of_day > 23:
        multiplier *= 0.2
    
    return max(0.1, min(1.0, multiplier))


def create_features_for_model(df):
    """Create features for ML model from raw data"""
    
    features_df = df.copy()
    
    # Time-based features
    features_df['hour_sin'] = np.sin(2 * np.pi * features_df['hour'] / 24)
    features_df['hour_cos'] = np.cos(2 * np.pi * features_df['hour'] / 24)
    features_df['day_sin'] = np.sin(2 * np.pi * features_df['day_of_week'] / 7)
    features_df['day_cos'] = np.cos(2 * np.pi * features_df['day_of_week'] / 7)
    
    # Lag features (previous hours demand)
    for lag in [1, 7, 24, 168]:  # 1h, 7h, 1 day, 1 week ago
        features_df[f'demand_lag_{lag}'] = features_df.groupby('station_id')['kWh_used'].shift(lag)
    
    # Rolling statistics
    for window in [6, 24, 168]:
        features_df[f'demand_rolling_mean_{window}'] = (
            features_df.groupby('station_id')['kWh_used']
            .transform(lambda x: x.rolling(window=window, min_periods=1).mean())
        )
    
    # Fill NaN values from lag and rolling operations
    features_df = features_df.fillna(features_df.mean(numeric_only=True))
    
    return features_df


def save_data(df, filepath):
    """Save dataframe to CSV"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    df.to_csv(filepath, index=False)
    print(f"Data saved to {filepath}")


if __name__ == "__main__":
    # Generate and save synthetic data
    print("Generating synthetic EV charging data...")
    synthetic_data = generate_synthetic_charging_data(num_stations=10, num_hours=2016)
    
    print(f"Generated {len(synthetic_data)} records")
    print(f"Date range: {synthetic_data['timestamp'].min()} to {synthetic_data['timestamp'].max()}")
    print(f"\nFirst few records:\n{synthetic_data.head()}")
    print(f"\nData shape: {synthetic_data.shape}")
    print(f"\nData types:\n{synthetic_data.dtypes}")
    
    # Save to data folder
    save_data(synthetic_data, 'data/synthetic_data.csv')
