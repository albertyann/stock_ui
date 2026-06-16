#!/bin/bash
# Startup script for Stock Watchlist Backend
# Uses wsproto instead of websockets to avoid compatibility issues

echo "Starting Stock Watchlist Backend..."
echo "WebSocket Protocol: wsproto (websockets package disabled)"

# Start uvicorn with wsproto explicitly
exec uvicorn app.main:app \
    --host 0.0.0.0 \
    --port 9000 \
    --ws wsproto \
    --reload \
    --log-level info
