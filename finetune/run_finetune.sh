#!/bin/bash
# Run fine-tuning inside the Unsloth Docker container.
#
# Usage:
#   ./run_finetune.sh                    # Use default config.yaml
#   ./run_finetune.sh my_config.yaml     # Use custom config
#
# Prerequisites:
#   - Docker with NVIDIA Container Toolkit
#   - NVIDIA GPU with sufficient VRAM (16GB+ recommended)
#   - HF_TOKEN env var set (if pushing to HuggingFace)

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CONFIG_FILE="${1:-config.yaml}"

# Load HF_TOKEN from .env if it exists
if [ -f "$SCRIPT_DIR/../src/.env" ]; then
    source "$SCRIPT_DIR/../src/.env"
fi

echo "========================================"
echo "  gLLM Fine-Tuning with Unsloth + LoRA"
echo "========================================"
echo "Config: $CONFIG_FILE"
echo "GPU:    $(nvidia-smi --query-gpu=name --format=csv,noheader 2>/dev/null || echo 'not detected')"
echo ""

# Run fine-tuning in Unsloth container
sudo docker run --rm \
    --runtime nvidia \
    --gpus all \
    -v "$SCRIPT_DIR":/workspace/finetune \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    -e "HF_TOKEN=${HF_TOKEN:-}" \
    -w /workspace/finetune \
    --ipc=host \
    unsloth/unsloth:latest \
    python finetune.py --config "$CONFIG_FILE"

echo ""
echo "Fine-tuning complete!"
echo "LoRA adapter saved to: $SCRIPT_DIR/lora_adapter/"
