#!/bin/bash
set -e

MODEL_DIR="/home/naturalis/programs/hyperbolic_KG/data/models"
MODEL_FILE="DeepSeek-R1-1.5B-Q4_K_M.gguf"
MODEL_PATH="$MODEL_DIR/$MODEL_FILE"
URL="https://huggingface.co/unsloth/DeepSeek-R1-1.5B-GGUF/resolve/main/DeepSeek-R1-1.5B-Q4_K_M.gguf"
# Valid GGUF magic bytes (hex): 47 47 55 46
GGUF_MAGIC="47475546"

mkdir -p "$MODEL_DIR"

needs_download=0

if [ ! -f "$MODEL_PATH" ]; then
    echo "Model file not found. Will download."
    needs_download=1
else
    # Validate magic bytes of existing file
    actual_magic=$(xxd -p -l 4 "$MODEL_PATH" 2>/dev/null | tr '[:lower:]' '[:upper:]')
    if [ "$actual_magic" != "$GGUF_MAGIC" ]; then
        echo "Model file exists but is corrupt (magic: $actual_magic, expected: $GGUF_MAGIC)."
        echo "Removing corrupt file and re-downloading..."
        rm -f "$MODEL_PATH"
        needs_download=1
    else
        echo "Model already exists and is valid: $MODEL_PATH"
    fi
fi

if [ "$needs_download" -eq 1 ]; then
    echo "Downloading $MODEL_FILE (~900MB)..."
    curl -L \
        --fail \
        --show-error \
        --progress-bar \
        -H "Accept: application/octet-stream" \
        -o "$MODEL_PATH" \
        "$URL"

    # Verify magic bytes after download
    actual_magic=$(xxd -p -l 4 "$MODEL_PATH" 2>/dev/null | tr '[:lower:]' '[:upper:]')
    if [ "$actual_magic" != "$GGUF_MAGIC" ]; then
        echo "ERROR: Downloaded file failed GGUF validation (magic: $actual_magic)."
        echo "The URL may be returning an HTML error page or rate-limit response."
        echo "Try downloading manually: $URL"
        rm -f "$MODEL_PATH"
        exit 1
    fi
    echo "Model downloaded and verified successfully."
fi
