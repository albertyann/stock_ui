#!/bin/bash
# Startup script for Stock Watchlist Backend
# Uses wsproto instead of websockets to avoid compatibility issues

echo "Starting Stock Watchlist Backend..."
echo "WebSocket Protocol: wsproto (websockets package disabled)"

# Set Python path to include parent directory for stock_picker imports
export PYTHONPATH="/Users/yann/workspace/trading:${PYTHONPATH}"

# Start uvicorn with wsproto explicitly
cd /Users/yann/workspace/trading/stock_watchlist/backend
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 8000 \
    --ws wsproto \
    --reload \
    --log-level info
