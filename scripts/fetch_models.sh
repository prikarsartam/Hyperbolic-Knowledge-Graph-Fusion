#!/bin/bash
set -e

MODEL_DIR="/home/naturalis/programs/hyperbolic_KG/data/models"
MODEL_FILE="DeepSeek-R1-1.5B-Q4_K_M.gguf"
# URL using a huggingface resolution mechanism for the file
URL="https://huggingface.co/unsloth/DeepSeek-R1-1.5B-GGUF/resolve/main/DeepSeek-R1-1.5B-Q4_K_M.gguf"

mkdir -p "$MODEL_DIR"

if [ ! -f "$MODEL_DIR/$MODEL_FILE" ]; then
    echo "Downloading $MODEL_FILE (~1GB)..."
    curl -L --fail --show-error -o "$MODEL_DIR/$MODEL_FILE" "$URL"
    echo "Download completed."
else
    echo "Model already exists at $MODEL_DIR/$MODEL_FILE"
fi
