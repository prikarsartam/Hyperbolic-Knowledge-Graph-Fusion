#!/bin/bash
set -e

echo "=== System Initialization Checks ==="

# 1. Check and download SLM Models (Idempotent: skips if exists)
bash scripts/fetch_models.sh

# 2. Check and configure GROBID Backend (Idempotent: skips if mapped)
bash scripts/install_grobid.sh

# 3. Check and install Frontend packages
if [ ! -d "frontend/node_modules" ]; then
    echo "Hydrating frontend dependencies..."
    cd frontend
    npm install
    cd ..
fi

echo "Compiling Vite Frontend..."
cd frontend
npm run build
cd ..

# 4. Check and install Python Subsystem
if [ ! -d "venv" ]; then
    echo "Creating isolated Python environment..."
    python3 -m venv venv
fi

source venv/bin/activate
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing backend dependencies (this maps PyTorch and execution blocks)..."
    pip install -r requirements.txt
    CMAKE_ARGS="-DGGML_CPU=ON" pip install llama-cpp-python
fi

echo "=== Launching Daemons ==="

# Kill hanging previous processes to free ports
echo "Cleaning up local ports..."
pkill -f "uvicorn api.main:app" || true
pkill -f "grobid" || true

# Boot GROBID
echo "Starting GROBID server on port 8070..."
cd /home/naturalis/programs/hyperbolic_KG/grobid
./gradlew run &
GROBID_PID=$!
cd ..

# Delay allowing the massive JVM memory array to hydrate
sleep 15

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
