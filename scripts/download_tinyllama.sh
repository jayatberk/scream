#!/usr/bin/env bash
set -euo pipefail

MODEL_URL="${1:-https://huggingface.co/TheBloke/TinyLlama-1.1B-Chat-v1.0-GGUF/resolve/main/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf}"
MODEL_DIR="${HOME}/Library/Application Support/localflow/models"
TARGET_FILE="${MODEL_DIR}/tinyllama-1.1b-chat-v1.0.Q4_K_M.gguf"

mkdir -p "$MODEL_DIR"

if [[ -f "$TARGET_FILE" ]]; then
  echo "Model already exists at: $TARGET_FILE"
  exit 0
fi

echo "Downloading TinyLlama GGUF to: $TARGET_FILE"
curl -L --fail "$MODEL_URL" -o "$TARGET_FILE"
echo "Done."
