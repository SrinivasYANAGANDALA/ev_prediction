# 🚀 EV Charging Demand Forecasting - Getting Started

## Installation & First Run (5 minutes)

### Step 1: Install Dependencies
```bash
cd /workspaces/ev_prediction
pip install -r requirements.txt
```

### Step 2: Generate Data & Train Model
```bash
python train.py
```

**Expected Output:**
```
[1/3] Generating synthetic charging data... ✓ (20,160 records)
[2/3] Creating features for model... ✓
[3/3] Training XGBoost model... ✓
Model Accuracy: R² = 0.96+
```

### Step 3: Launch Dashboard
```bash
python app.py
```

**Visit:** http://localhost:5000

---

## 📊 Dashboard Overview

The dashboard has **4 main sections:**

### 1. **KPI Cards** (Top)
- Total Stations
- Critical Alerts
- Warning Alerts
- Active Alerts

### 2. **Alerts & Recommendations** 
Shows:
- Red (Critical): >90% capacity
- Yellow (Warning): 75-90% capacity
- Suggested actions (pricing, load balancing)

### 3. **24-Hour Forecast**
Interactive line chart showing predicted demand for all stations

### 4. **Station Status Table**
Real-time data:
- Station ID & Location
- Current demand & capacity
- Connector count & charger type

### 5. **Pricing Recommendations**
Dynamic pricing tiers:
- Economy (0.7x) - Low utilization
- Standard (1.0x) - Normal
- Premium (1.25x) - High
- Peak (1.75x) - Very High
- Critical (2.0x) - >95% capacity

---

## 🔌 API Reference

### Get All Stations
```bash
curl http://localhost:5000/api/stations
```

### Get 24-Hour Forecast
```bash
curl http://localhost:5000/api/forecast?hours=24
```

### Get Current Alerts
```bash
curl http://localhost:5000/api/alerts
```

### Get Pricing Recommendations
```bash
curl http://localhost:5000/api/pricing
```

### Get System Statistics
```bash
curl http://localhost:5000/api/stats
```

---

## ⚙️ Customization

Edit `configs/config.py` to change:

```python
NUM_STATIONS = 10              # Number of charging stations
FORECAST_HORIZON = 24          # Hours to forecast ahead
UTILIZATION_WARNING = 0.75     # 75% capacity = yellow alert
UTILIZATION_CRITICAL = 0.90    # 90% capacity = red alert
PORT = 5000                    # Dashboard port
```

---

## 📈 Understanding the Model

**Input Features:**
- Time of day (hour, day_of_week)
- Historical demand (last 1h, 7h, 24h, 1 week)
- Weather (temperature, rain, wind)
- Station info (capacity, connectors, location)
- External signals (events, traffic)

**Output:**
- Predicted kWh demand for next hour(s)

**Accuracy:**
- R² Score: 0.962 (96.2% variance explained)
- RMSE: 19.31 kWh
- MAE: 13.63 kWh

---

## 🐛 Troubleshooting

| Issue | Solution |
|-------|----------|
| "Models not found" | Run `python train.py` first |
| Port 5000 in use | Change PORT in `configs/config.py` |
| Dashboard shows errors | Check Flask console for stack trace |
| Slow predictions | Reduce FORECAST_HORIZON in config |

---

## 📁 Project Structure

```
ev_prediction/
├── train.py                  # Run this first to train
├── app.py                    # Run this to start dashboard
├── requirements.txt          # Dependencies
├── README.md                 # Full documentation
├── configs/
│   └── config.py            # Customization settings
├── src/
│   ├── model/
│   │   └── forecasting_model.py    # XGBoost wrapper
│   └── utils/
│       ├── data_generator.py       # Data synthesis
│       ├── alerts.py               # Alert logic
│       └── helpers.py              # Utilities
├── templates/
│   └── index.html            # Web UI
├── data/
│   └── synthetic_data.csv    # Training dataset
└── models/
    ├── xgboost_model.pkl     # Trained model
    └── scaler.pkl            # Feature scaler
```

---

## 🎯 What Happens Next?

After running `python app.py`:

1. **Synthetic data loads** - 20,160 hourly records across 10 stations
2. **Model initializes** - XGBoost predictor loads from disk
3. **Dashboard starts** - Flask server listens on port 5000
4. **Real-time forecast** - Every station gets next-24-hour predictions
5. **Alerts generated** - Compare forecasts vs capacity, flag risks
6. **Pricing suggested** - Dynamic multipliers based on utilization

**The dashboard auto-refreshes every 30 seconds** with new forecasts and alerts.

---

## 💡 Key Features Explained

### Dynamic Pricing
The system recommends prices based on predicted demand:
- If 50% full: Reduce price → encourage usage
- If 75% full: Raise price 25% → moderate demand
- If 90% full: Raise price 50% → discourage usage
- If 95% full: Max pricing → emergency mode

### Alert Levels
- 🟢 **Green**: Normal operation (<75%)
- 🟡 **Yellow**: Monitor closely (75-90%)
- 🔴 **Red**: Immediate action needed (>90%)

### Forecast Accuracy
The model is trained on 84 days of synthetic data with realistic patterns:
- Urban stations peak morning & evening
- Highway stations steady throughout day
- Suburban stations have morning/evening peaks
- Weather affects demand
- Random events create variability

---

## 🚀 Production Deployment

To deploy to production:

```bash
# Using Gunicorn (recommended)
gunicorn -w 4 -b 0.0.0.0:8000 app:app

# Or with Docker
docker build -t ev-forecasting .
docker run -p 5000:5000 ev-forecasting
```

For more details, see README.md

---

**Status**: ✅ Ready to Use  
**Version**: 1.0.0  
**Last Updated**: April 2024
