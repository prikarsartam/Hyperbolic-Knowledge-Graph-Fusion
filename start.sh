#!/bin/bash
set -e

echo "=== System Initialization Checks ==="

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

# 1. SLM Model check (idempotent)
bash scripts/fetch_models.sh

# 2. GROBID build check (idempotent — skips if JAR exists)
bash scripts/install_grobid.sh

# 3. Frontend node_modules check (idempotent)
if [ ! -d "frontend/node_modules" ]; then
    echo "Hydrating frontend dependencies..."
    cd frontend && npm install && cd "$SCRIPT_DIR"
fi

# 4. Frontend build (always rebuild to catch any source changes)
echo "Compiling Vite Frontend..."
cd frontend && npm run build && cd "$SCRIPT_DIR"

# 5. Python venv setup (idempotent)
if [ ! -d "venv" ]; then
    echo "Creating isolated Python environment..."
    python3 -m venv venv
fi

source venv/bin/activate

# 6. Install Python dependencies into venv (idempotent via pip's own check)
# Use python -m pip to guarantee we install into the active venv, not system
echo "Verifying Python dependencies..."
python -m pip install -r requirements.txt --quiet

# llama-cpp-python requires special CPU-only build flag
if ! python -c "import llama_cpp" 2>/dev/null; then
    echo "Installing llama-cpp-python (CPU-only build)..."
    CMAKE_ARGS="-DGGML_CPU=ON" python -m pip install llama-cpp-python
fi

echo "=== Launching Daemons ==="

# Kill any hanging previous processes
echo "Cleaning up local ports..."
pkill -f "uvicorn api.main:app" || true
pkill -f "grobid" || true

# Boot GROBID
echo "Starting GROBID server on port 8070..."
cd "$SCRIPT_DIR/grobid"
./gradlew run --no-daemon &
GROBID_PID=$!
cd "$SCRIPT_DIR"

# Poll GROBID /api/isalive — max 90s
echo "Waiting for GROBID to become ready (max 90s)..."
GROBID_READY=0
for i in $(seq 1 90); do
    if curl -sf http://localhost:8070/api/isalive > /dev/null 2>&1; then
        echo "GROBID is ready (${i}x2s elapsed)."
        GROBID_READY=1
        break
    fi
    sleep 2
done

if [ "$GROBID_READY" -eq 0 ]; then
    echo "WARNING: GROBID did not respond within 90s. Proceeding anyway."
fi

# Boot FastAPI — use python -m uvicorn to guarantee venv binary, not system PATH
echo "Starting FastAPI Backend on port 8000..."
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 &
API_PID=$!

echo "=========================================================="
echo " System Online. UI at http://localhost:8000               "
echo " GROBID API at http://localhost:8070                      "
echo " Press Ctrl+C to terminate all services.                  "
echo "=========================================================="

trap "echo 'Terminating...'; kill $GROBID_PID $API_PID 2>/dev/null; exit 0" SIGINT SIGTERM

wait
