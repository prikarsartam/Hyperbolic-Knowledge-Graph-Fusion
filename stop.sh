#!/bin/bash

echo "Forcibly terminating all Knowledge Graph background daemons..."

# Kill Uvicorn (FastAPI)
echo "Stopping Python Uvicorn servers..."
pkill -f "uvicorn api.main:app" || echo "Uvicorn was already stopped."

# Kill GROBID (Java Gradle Daemon & background processes)
echo "Stopping GROBID parsing agents..."
pkill -f "grobid" || echo "GROBID was already stopped."

# Final sweep of rogue python inference
pkill -f "llama_cpp" || true

echo "All graph services have been successfully completely halted."
