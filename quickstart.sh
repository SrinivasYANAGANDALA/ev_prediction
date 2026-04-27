#!/bin/bash
# Quick start script for EV Demand Forecasting Dashboard

echo "=========================================="
echo "EV Charging Demand Forecasting Setup"
echo "=========================================="
echo ""

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

echo "✓ Python detected"
echo ""

# Install dependencies
echo "[1/3] Installing dependencies..."
pip install -q -r requirements.txt
echo "✓ Dependencies installed"
echo ""

# Train model
echo "[2/3] Training forecasting model..."
python train.py > /dev/null 2>&1
echo "✓ Model trained (see train.py for details)"
echo ""

# Start server
echo "[3/3] Starting Flask dashboard..."
echo ""
echo "🚀 Dashboard is running at: http://localhost:5000"
echo ""
echo "Features:"
echo "  📊 Real-time demand forecasts"
echo "  🚨 Overload alerts & warnings"
echo "  💰 Dynamic pricing recommendations"
echo "  📍 Station status & utilization"
echo ""
echo "Press Ctrl+C to stop the server"
echo ""

python app.py
