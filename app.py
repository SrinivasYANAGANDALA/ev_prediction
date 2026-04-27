"""Flask web dashboard for EV charging demand forecasting"""

import os
import sys
from datetime import datetime, timedelta

import numpy as np
import pandas as pd
from flask import Flask, render_template, jsonify, request
from flask_cors import CORS

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from model.forecasting_model import DemandForecaster
from utils.alerts import AlertManager, PricingRecommender
from utils.data_generator import create_features_for_model
from configs.config import (
    MODEL_PATH, FEATURE_SCALER_PATH, SYNTHETIC_DATA_PATH,
    NUM_STATIONS, HOST, PORT, DEBUG,
    UTILIZATION_WARNING, UTILIZATION_CRITICAL, PRICE_SURGE_THRESHOLD
)

# Initialize Flask app
app = Flask(__name__)
CORS(app)

# Global variables
forecaster = None
alert_manager = None
pricing_recommender = None
training_data = None
current_forecasts = None


def initialize_models():
    """Load trained models and managers"""
    global forecaster, alert_manager, pricing_recommender, training_data
    
    print("Initializing models...")
    
    try:
        # Load forecaster
        forecaster = DemandForecaster(MODEL_PATH, FEATURE_SCALER_PATH)
        
        # Initialize managers
        alert_manager = AlertManager(
            utilization_warning=UTILIZATION_WARNING,
            utilization_critical=UTILIZATION_CRITICAL,
            price_surge_threshold=PRICE_SURGE_THRESHOLD
        )
        pricing_recommender = PricingRecommender(base_price=0.50)
        
        # Load training data for context
        if os.path.exists(SYNTHETIC_DATA_PATH):
            training_data = pd.read_csv(SYNTHETIC_DATA_PATH)
            training_data['timestamp'] = pd.to_datetime(training_data['timestamp'])
        
        print("✓ Models initialized successfully")
        return True
    
    except Exception as e:
        print(f"✗ Error initializing models: {e}")
        return False


def get_latest_station_data():
    """Get latest station data from training set"""
    
    if training_data is None:
        return None
    
    # Get latest hour for each station
    latest_data = training_data.loc[training_data.groupby('station_id')['timestamp'].idxmax()]
    return latest_data.sort_values('station_id')


def _risk_from_utilization(utilization):
    if utilization >= UTILIZATION_CRITICAL:
        return 'critical'
    if utilization >= UTILIZATION_WARNING:
        return 'warning'
    return 'normal'


def _risk_color(risk_level):
    return {
        'critical': 'red',
        'warning': 'yellow',
        'normal': 'green',
    }.get(risk_level, 'green')


def _serialize_timestamp(value):
    if isinstance(value, pd.Timestamp):
        return value.isoformat()
    if isinstance(value, datetime):
        return value.isoformat()
    return str(value)


def _build_forecast_bundle(hours_ahead=24):
    forecasts = generate_forecast(hours_ahead=hours_ahead)
    if not forecasts or training_data is None:
        return None

    latest_data = get_latest_station_data()
    if latest_data is None:
        return None

    capacity_map = latest_data.set_index('station_id')['station_capacity'].to_dict()
    station_map = {}
    matrix = []
    station_labels = []
    hour_labels = [(datetime.now() + timedelta(hours=idx + 1)).strftime('%a %H:%M') for idx in range(hours_ahead)]

    for forecast_group in forecasts:
        station_id = forecast_group['station_id']
        capacity = float(capacity_map.get(station_id, 250))
        series = []
        total_demand = 0.0
        peak_demand = 0.0
        peak_utilization = 0.0
        peak_hour = None

        for record in forecast_group['forecasts']:
            predicted_demand = float(record['predicted_demand'])
            utilization = predicted_demand / capacity if capacity else 0
            risk_level = _risk_from_utilization(utilization)
            series.append({
                'timestamp': _serialize_timestamp(record['timestamp']),
                'hour': int(record['hour']),
                'predicted_demand': predicted_demand,
                'predicted_utilization': utilization,
                'risk_level': risk_level,
                'risk_color': _risk_color(risk_level),
            })
            total_demand += predicted_demand
            if predicted_demand > peak_demand:
                peak_demand = predicted_demand
                peak_utilization = utilization
                peak_hour = _serialize_timestamp(record['timestamp'])

        station_map[station_id] = {
            'station_id': station_id,
            'forecasts': series,
            'next_24h_total': total_demand,
            'peak_demand': peak_demand,
            'peak_utilization': peak_utilization,
            'peak_hour': peak_hour,
            'average_demand': total_demand / len(series) if series else 0,
        }
        station_labels.append(f'Station {station_id}')
        matrix.append([record['predicted_demand'] for record in series])

    hourly_totals = []
    total_capacity = float(latest_data['station_capacity'].sum()) if len(latest_data) else 0
    for hour_idx in range(hours_ahead):
        hour_total = sum(station['forecasts'][hour_idx]['predicted_demand'] for station in station_map.values())
        hourly_totals.append({
            'hour_index': hour_idx,
            'label': hour_labels[hour_idx],
            'total_demand': hour_total,
            'fleet_utilization': hour_total / total_capacity if total_capacity else 0,
        })

    peak_hour_record = max(hourly_totals, key=lambda item: item['total_demand']) if hourly_totals else None
    return {
        'stations': station_map,
        'matrix': matrix,
        'station_labels': station_labels,
        'hour_labels': hour_labels,
        'hourly_totals': hourly_totals,
        'peak_hour': peak_hour_record,
    }


def _build_station_status(latest_data, forecasts_by_station):
    stations = []

    for _, row in latest_data.iterrows():
        station_id = int(row['station_id'])
        capacity = float(row['station_capacity'])
        current_demand = float(row['kWh_used'])
        current_utilization = current_demand / capacity if capacity else 0
        forecast_info = forecasts_by_station.get(station_id, {})
        next_24h_total = float(forecast_info.get('next_24h_total', current_demand))
        peak_utilization = float(forecast_info.get('peak_utilization', current_utilization))
        risk_level = _risk_from_utilization(max(current_utilization, peak_utilization))
        price = pricing_recommender.recommend_price(max(current_utilization, peak_utilization)) if pricing_recommender else 0.50
        tier, tier_color = pricing_recommender.get_pricing_tier(max(current_utilization, peak_utilization)) if pricing_recommender else ('Standard', 'yellow')

        stations.append({
            'station_id': station_id,
            'location_type': str(row['location_type']).title(),
            'charger_type': str(row['charger_type']),
            'connector_count': int(row['connector_count']),
            'capacity': capacity,
            'current_demand': current_demand,
            'current_utilization': current_utilization,
            'avg_charging_duration': float(row['avg_charging_duration']),
            'sessions_count': int(row['sessions_count']),
            'temperature': float(row['temperature']),
            'event_flag': int(row['event_flag']),
            'local_traffic': float(row['local_traffic']),
            'area_activity': float(row['area_activity']),
            'next_24h_total': next_24h_total,
            'peak_utilization': peak_utilization,
            'risk_level': risk_level,
            'risk_color': _risk_color(risk_level),
            'recommended_price': float(price),
            'pricing_tier': tier,
            'pricing_color': tier_color,
        })

    stations.sort(key=lambda item: (item['peak_utilization'], item['next_24h_total']), reverse=True)
    return stations


def build_dashboard_payload(hours_ahead=24):
    if training_data is None or forecaster is None or alert_manager is None or pricing_recommender is None:
        return None

    latest_data = get_latest_station_data()
    forecast_bundle = _build_forecast_bundle(hours_ahead=hours_ahead)
    if latest_data is None or forecast_bundle is None:
        return None

    stations = _build_station_status(latest_data, forecast_bundle['stations'])
    capacity_total = float(latest_data['station_capacity'].sum()) if len(latest_data) else 0
    current_total_demand = float(latest_data['kWh_used'].sum()) if len(latest_data) else 0
    current_avg_utilization = current_total_demand / capacity_total if capacity_total else 0

    forecast_rows = []
    for station in stations:
        series = forecast_bundle['stations'][station['station_id']]['forecasts']
        forecast_rows.append({
            'station_id': station['station_id'],
            'forecasted_demand': series[0]['predicted_demand'] if series else station['current_demand'],
        })

    forecast_df = pd.DataFrame(forecast_rows)
    evaluations = alert_manager.batch_evaluate(forecast_df, latest_data.set_index('station_id')['station_capacity'].to_dict()) if len(forecast_df) else []
    alerts_summary = alert_manager.get_summary(evaluations) if evaluations else {}

    pricing_data = []
    for station in stations:
        pricing_data.append({
            'station_id': station['station_id'],
            'utilization': max(station['current_utilization'], station['peak_utilization']),
            'current_price': 0.50,
            'recommended_price': station['recommended_price'],
            'multiplier': station['recommended_price'] / 0.50 if 0.50 else 1.0,
            'tier': station['pricing_tier'],
            'tier_color': station['pricing_color'],
        })

    location_mix = latest_data.groupby('location_type').size().reset_index(name='count')
    charger_mix = latest_data.groupby('charger_type').size().reset_index(name='count')
    top_risk_stations = stations[:5]
    top_demand_stations = sorted(stations, key=lambda item: item['current_demand'], reverse=True)[:5]
    avg_temperature = float(latest_data['temperature'].mean()) if len(latest_data) else 0
    rain_share = float(latest_data['is_raining'].mean()) if len(latest_data) else 0
    event_rate = float(latest_data['event_flag'].mean()) if len(latest_data) else 0

    summary = {
        'total_stations': int(len(latest_data)),
        'total_records': int(len(training_data)),
        'current_total_demand': current_total_demand,
        'current_average_demand': float(latest_data['kWh_used'].mean()) if len(latest_data) else 0,
        'current_average_utilization': current_avg_utilization,
        'critical_count': int(alerts_summary.get('critical_count', 0)),
        'warning_count': int(alerts_summary.get('warning_count', 0)),
        'normal_count': int(alerts_summary.get('normal_count', 0)),
        'peak_forecast_hour': forecast_bundle['peak_hour']['label'] if forecast_bundle['peak_hour'] else None,
        'peak_forecast_demand': float(forecast_bundle['peak_hour']['total_demand']) if forecast_bundle['peak_hour'] else 0,
        'peak_station': stations[0]['station_id'] if stations else None,
        'forecast_horizon': hours_ahead,
        'avg_temperature': avg_temperature,
        'rain_share': rain_share,
        'event_rate': event_rate,
    }

    return {
        'summary': summary,
        'stations': stations,
        'forecast': {
            'hours_ahead': hours_ahead,
            'hour_labels': forecast_bundle['hour_labels'],
            'hourly_totals': forecast_bundle['hourly_totals'],
            'matrix': forecast_bundle['matrix'],
            'station_labels': forecast_bundle['station_labels'],
            'peak_hour': forecast_bundle['peak_hour'],
        },
        'alerts': {
            'evaluations': evaluations,
            'summary': alerts_summary,
        },
        'pricing': pricing_data,
        'insights': {
            'top_risk_stations': top_risk_stations,
            'top_demand_stations': top_demand_stations,
            'location_mix': location_mix.to_dict('records'),
            'charger_mix': charger_mix.to_dict('records'),
        },
        'stats': {
            'total_stations': int(len(latest_data)),
            'total_records': int(len(training_data)),
            'time_range': {
                'start': _serialize_timestamp(training_data['timestamp'].min()),
                'end': _serialize_timestamp(training_data['timestamp'].max()),
            },
            'model': {
                'type': 'XGBoost',
                'status': 'trained' if forecaster and forecaster.model is not None else 'not_trained',
            },
            'context': {
                'avg_temperature': avg_temperature,
                'rain_share': rain_share,
                'event_rate': event_rate,
            },
        },
    }


def generate_forecast(hours_ahead=24):
    """Generate demand forecast for next N hours"""
    
    if training_data is None or forecaster is None:
        return None
    
    latest_data = get_latest_station_data()
    forecasts = []
    
    for station_id in range(1, NUM_STATIONS + 1):
        station_data = latest_data[latest_data['station_id'] == station_id]
        
        if len(station_data) == 0:
            continue
        
        # Create hourly forecast
        station_forecasts = []
        for hour in range(hours_ahead):
            # Create feature row for prediction
            feature_row = station_data.copy()
            
            # Update time features for future hour
            future_time = station_data['timestamp'].iloc[0] + timedelta(hours=hour+1)
            feature_row['hour'] = future_time.hour
            feature_row['day_of_week'] = future_time.weekday()
            feature_row['is_weekend'] = 1 if future_time.weekday() >= 5 else 0
            
            # Make prediction
            try:
                predicted_demand = forecaster.predict(feature_row)[0]
            except:
                # Fallback to average if prediction fails
                predicted_demand = station_data['kWh_used'].mean()
            
            station_forecasts.append({
                'timestamp': future_time,
                'hour': future_time.hour,
                'predicted_demand': predicted_demand
            })
        
        forecasts.append({
            'station_id': station_id,
            'forecasts': station_forecasts
        })
    
    return forecasts


@app.route('/')
def index():
    """Main dashboard page"""
    return render_template('dashboard.html')


@app.route('/api/dashboard')
def get_dashboard():
    """Get the complete dashboard payload"""

    hours = request.args.get('hours', 24, type=int)
    hours = min(max(hours, 1), 168)
    payload = build_dashboard_payload(hours_ahead=hours)

    if payload is None:
        return jsonify({'error': 'Failed to build dashboard payload'}), 500

    return jsonify(payload)


@app.route('/api/stations')
def get_stations():
    """Get all stations"""
    payload = build_dashboard_payload(hours_ahead=24)

    if payload is None:
        return jsonify({'error': 'No training data available'}), 500

    return jsonify(payload['stations'])


@app.route('/api/forecast')
def get_forecast():
    """Get demand forecast"""
    
    hours = request.args.get('hours', 24, type=int)
    hours = min(hours, 168)  # Max 7 days

    payload = build_dashboard_payload(hours_ahead=hours)

    if payload is None:
        return jsonify({'error': 'Failed to generate forecast'}), 500

    return jsonify(payload['forecast'])


@app.route('/api/alerts')
def get_alerts():
    """Get current alerts and recommendations"""

    payload = build_dashboard_payload(hours_ahead=24)

    if payload is None:
        return jsonify({'error': 'Models not initialized'}), 500

    return jsonify(payload['alerts'])


@app.route('/api/pricing')
def get_pricing():
    """Get pricing recommendations"""

    payload = build_dashboard_payload(hours_ahead=24)

    if payload is None:
        return jsonify({'error': 'Models not initialized'}), 500

    return jsonify(payload['pricing'])


@app.route('/api/stats')
def get_stats():
    """Get system statistics"""

    payload = build_dashboard_payload(hours_ahead=24)

    if payload is None:
        return jsonify({'error': 'No data available'}), 500

    return jsonify(payload['stats'])


@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    print("=" * 60)
    print("EV DEMAND FORECASTING - Web Dashboard")
    print("=" * 60)
    
    # Initialize models
    if not initialize_models():
        print("Failed to initialize models. Please train the model first.")
        sys.exit(1)
    
    print(f"\nStarting server at http://{HOST}:{PORT}")
    print("Press Ctrl+C to stop")
    
    app.run(host=HOST, port=PORT, debug=DEBUG)
