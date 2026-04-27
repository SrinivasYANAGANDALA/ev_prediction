# EV Charging Forecasting - API Documentation

## Base URL
```
http://localhost:5000
```

---

## Endpoints

### 1. GET /api/stations
Get metadata for all charging stations.

**Parameters:** None

**Response:**
```json
[
  {
    "id": 1,
    "location": "Urban",
    "capacity": 250.5,
    "connectors": 8,
    "charger_type": "DC",
    "current_demand": 185.3
  },
  {
    "id": 2,
    "location": "Suburban",
    "capacity": 150.0,
    "connectors": 4,
    "charger_type": "AC",
    "current_demand": 45.2
  }
]
```

**Status Codes:**
- 200: Success
- 500: Server error

---

### 2. GET /api/forecast
Get demand forecast for stations.

**Parameters:**
- `hours` (optional): Number of hours to forecast (1-168, default: 24)

**Example:**
```bash
curl "http://localhost:5000/api/forecast?hours=24"
```

**Response:**
```json
[
  {
    "station_id": 1,
    "forecasts": [
      {
        "timestamp": "2024-04-22T10:00:00",
        "hour": 10,
        "predicted_demand": 195.3
      },
      {
        "timestamp": "2024-04-22T11:00:00",
        "hour": 11,
        "predicted_demand": 210.5
      }
    ]
  },
  {
    "station_id": 2,
    "forecasts": [
      {
        "timestamp": "2024-04-22T10:00:00",
        "hour": 10,
        "predicted_demand": 75.2
      }
    ]
  }
]
```

**Response Fields:**
- `station_id`: Integer, station identifier (1-10)
- `timestamp`: ISO 8601 format datetime
- `hour`: Hour of day (0-23)
- `predicted_demand`: Float, forecasted kWh demand

---

### 3. GET /api/alerts
Get current alerts and recommended actions.

**Parameters:** None

**Response:**
```json
{
  "evaluations": [
    {
      "station_id": 3,
      "utilization_percent": 92.5,
      "status": "critical",
      "status_color": "red",
      "alerts": [
        "CRITICAL: Station 3 predicted at 92.5% capacity"
      ],
      "recommendations": [
        "Increase pricing by 30-50% to reduce demand",
        "Send notifications to redirect users to nearby stations",
        "Consider temporary closure if approaching hard limits"
      ],
      "forecasted_demand": 231.25,
      "capacity": 250.0
    },
    {
      "station_id": 5,
      "utilization_percent": 78.0,
      "status": "warning",
      "status_color": "yellow",
      "alerts": [
        "WARNING: Station 5 predicted at 78.0% capacity"
      ],
      "recommendations": [
        "Increase pricing by 15-25% to moderate demand",
        "Monitor usage closely for next 2 hours"
      ],
      "forecasted_demand": 117.0,
      "capacity": 150.0
    }
  ],
  "summary": {
    "total_stations": 10,
    "critical_count": 1,
    "warning_count": 2,
    "normal_count": 7,
    "total_alerts": 3,
    "alerts": [
      "CRITICAL: Station 3 predicted at 92.5% capacity",
      "WARNING: Station 5 predicted at 78.0% capacity",
      "WARNING: Station 7 predicted at 76.5% capacity"
    ],
    "unique_recommendations": [
      "Increase pricing by 30-50% to reduce demand",
      "Send notifications to redirect users to nearby stations",
      "Increase pricing by 15-25% to moderate demand",
      "Monitor usage closely for next 2 hours"
    ]
  }
}
```

**Alert Status Levels:**
- `normal`: <75% utilization (green)
- `warning`: 75-90% utilization (yellow)
- `critical`: >90% utilization (red)

---

### 4. GET /api/pricing
Get dynamic pricing recommendations per station.

**Parameters:** None

**Response:**
```json
[
  {
    "station_id": 1,
    "utilization": 0.742,
    "current_price": 0.50,
    "recommended_price": 0.625,
    "multiplier": 1.25,
    "tier": "Premium",
    "tier_color": "orange"
  },
  {
    "station_id": 2,
    "utilization": 0.301,
    "current_price": 0.50,
    "recommended_price": 0.35,
    "multiplier": 0.70,
    "tier": "Economy",
    "tier_color": "green"
  }
]
```

**Pricing Tiers:**
| Utilization | Tier | Multiplier | Color |
|---|---|---|---|
| < 50% | Economy | 0.70x | green |
| 50-75% | Standard | 1.00x | green |
| 75-85% | Premium | 1.25x | orange |
| 85-95% | Peak | 1.75x | red |
| > 95% | Critical | 2.00x | darkred |

**Response Fields:**
- `station_id`: Integer
- `utilization`: Float (0-1), percentage as decimal
- `current_price`: Float, base price in $/kWh
- `recommended_price`: Float, suggested price in $/kWh
- `multiplier`: Float, price multiplier
- `tier`: String, pricing tier name
- `tier_color`: String, color code

---

### 5. GET /api/stats
Get system statistics and model information.

**Parameters:** None

**Response:**
```json
{
  "total_stations": 10,
  "total_records": 20160,
  "time_range": {
    "start": "2023-01-01T00:00:00",
    "end": "2023-03-26T23:00:00"
  },
  "model": {
    "type": "XGBoost",
    "status": "trained"
  }
}
```

**Response Fields:**
- `total_stations`: Integer, number of stations
- `total_records`: Integer, training data points
- `time_range.start`: ISO 8601 datetime
- `time_range.end`: ISO 8601 datetime
- `model.type`: String, ML algorithm used
- `model.status`: String, "trained" or "not_trained"

---

## Error Responses

### 404 Not Found
```json
{
  "error": "Endpoint not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error"
}
```

---

## Example Workflows

### Workflow 1: Check for Alerts
```bash
# 1. Get current alerts
curl http://localhost:5000/api/alerts

# 2. If critical alerts exist, get forecast for that station
curl "http://localhost:5000/api/forecast?hours=24" | jq '.[] | select(.station_id==3)'

# 3. Get pricing to recommend
curl http://localhost:5000/api/pricing | jq '.[] | select(.station_id==3)'
```

### Workflow 2: 7-Day Forecast Planning
```bash
# Get 168-hour (7-day) forecast
curl "http://localhost:5000/api/forecast?hours=168"

# Process and analyze peak hours
# Adjust pricing strategy based on patterns
```

### Workflow 3: Load Balancing
```bash
# 1. Get all stations and current demand
curl http://localhost:5000/api/stations

# 2. Get alerts to identify stressed stations
curl http://localhost:5000/api/alerts

# 3. Get nearby stations with spare capacity
curl http://localhost:5000/api/pricing | jq '.[] | select(.tier=="Economy")'
```

---

## Rate Limiting
No rate limiting currently implemented. For production, consider adding:
- 100 requests per minute per IP
- Caching responses for 30 seconds

---

## Authentication
No authentication currently implemented. For production, add:
- JWT tokens
- API key validation
- Role-based access control

---

## CORS
CORS is enabled for all origins. For production, restrict to specific domains:
```python
CORS(app, origins=["https://yourdomain.com"])
```

---

## Versioning
Current API Version: **v1.0**

Future versions will be available at:
- `/api/v1/...` (current)
- `/api/v2/...` (future)

---

## Performance Notes

### Response Times
- `/api/stations`: ~50ms
- `/api/forecast`: ~200ms (24 hours)
- `/api/alerts`: ~300ms
- `/api/pricing`: ~150ms
- `/api/stats`: ~50ms

### Data Refresh
- All endpoints refresh every 30 seconds
- Real-time data (not cached)

---

## Integration Examples

### Python
```python
import requests

url = "http://localhost:5000/api/alerts"
response = requests.get(url)
alerts = response.json()

for alert in alerts['evaluations']:
    if alert['status'] == 'critical':
        print(f"ALERT: {alert['alerts']}")
```

### JavaScript
```javascript
async function getAlerts() {
    const response = await fetch('/api/alerts');
    const data = await response.json();
    return data.evaluations;
}

getAlerts().then(alerts => {
    alerts.forEach(alert => {
        console.log(`Station ${alert.station_id}: ${alert.status}`);
    });
});
```

### CURL
```bash
# Get all data
curl http://localhost:5000/api/alerts | jq '.summary'

# Filter specific station
curl http://localhost:5000/api/forecast?hours=48 | jq '.[] | select(.station_id==1)'
```

---

## Changelog

### v1.0.0 (April 2024)
- Initial release
- XGBoost forecasting model
- Real-time alerts
- Dynamic pricing engine
- 6 REST API endpoints

---

**Last Updated:** April 2024
