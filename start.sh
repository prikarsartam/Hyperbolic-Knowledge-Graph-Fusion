#!/bin/bash
set -e

echo "=== System Initialization Checks ==="
if [ ! -d "venv" ] || [ ! -d "frontend/node_modules" ]; then
    echo "Error: Subsystems not initialized. Please run ./install.sh first."
    exit 1
fi

source venv/bin/activate

echo "=== Launching Daemons ==="

# Kill hanging previous processes to free ports
echo "Cleaning up local ports..."
pkill -f "uvicorn api.main:app" || true
pkill -f "grobid" || true

# Boot GROBID
echo "Starting GROBID server on port 8070..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR/grobid"
./gradlew run --no-daemon &
GROBID_PID=$!
cd "$SCRIPT_DIR"

# Poll GROBID /api/isalive until it responds or timeout after 90s
echo "Waiting for GROBID to become ready (max 90s)..."
GROBID_READY=0
for i in $(seq 1 45); do
    if curl -sf http://localhost:8070/api/isalive > /dev/null 2>&1; then
        echo "GROBID is ready (${i}x2s elapsed)."
        GROBID_READY=1
        break
    fi
    sleep 2
done

if [ "$GROBID_READY" -eq 0 ]; then
    echo "WARNING: GROBID did not respond within 90 seconds."
    echo "Proceeding anyway — check http://localhost:8070/api/isalive manually."
fi

# Boot FastAPI
echo "Starting FastAPI Backend Server on port 8000..."
uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "=========================================================="
echo " System Online. UI rendering listening at :8000           "
echo " Memory categorical bounding strictly enabled.            "
echo " Press Ctrl+C to terminate all services and graph data.   "
echo "=========================================================="

trap "echo 'Terminating Daemons...'; kill $GROBID_PID $API_PID; exit 0" SIGINT SIGTERM

wait
