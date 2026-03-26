#!/bin/bash
set -e

echo "=== System Installation & Initialization ==="

# 1. Check and download SLM Models (Idempotent: skips if exists)
bash scripts/fetch_models.sh

# 2. Check and configure GROBID Backend (Idempotent: skips if JAR exists)
bash scripts/install_grobid.sh

# 3. Check and install Frontend packages
if [ ! -d "frontend/node_modules" ]; then
    echo "Hydrating frontend dependencies..."
    cd frontend
    npm install
    cd ..
else
    echo "Frontend dependencies are already hydrated."
fi

echo "Compiling Vite Frontend..."
cd frontend
npm run build
cd ..

# 4. Check and install Python Subsystem
if [ ! -d "venv" ]; then
    echo "Creating isolated Python environment..."
    python3 -m venv venv
else
    echo "Python environment already exists."
fi

source venv/bin/activate
if [ ! -f "venv/bin/uvicorn" ]; then
    echo "Installing backend dependencies..."
    pip install -r requirements.txt
    CMAKE_ARGS="-DGGML_CPU=ON" pip install llama-cpp-python
else
    echo "Backend dependencies are already installed."
fi

echo "=== Installation Complete ==="
echo "You can now run ./start.sh to launch the application."
