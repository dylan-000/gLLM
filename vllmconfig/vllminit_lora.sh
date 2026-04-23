#!/bin/bash
# Start vLLM with LoRA adapter support enabled.
#
# Usage:
#   ./vllminit_lora.sh                           # Base model only, LoRA ready
#   ./vllminit_lora.sh /path/to/lora_adapter     # Load a LoRA adapter at startup
#
# At runtime, you can load/unload LoRA adapters via the API:
#   curl -X POST http://localhost:8000/v1/load_lora_adapter \
#     -H "Content-Type: application/json" \
#     -d '{"lora_name": "my_adapter", "lora_path": "/adapters/my_adapter"}'

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

# Load env vars
if [ -f "$SCRIPT_DIR/../src/.env" ]; then
    source "$SCRIPT_DIR/../src/.env"
fi

PORT=8000
GPU_MEMORY_UTILIZATION=0.9
dtype=auto
LOG_FILE="$SCRIPT_DIR/vllm-logs/vllm.log"
LORA_ADAPTER_PATH="${1:-}"
ADAPTERS_DIR="$SCRIPT_DIR/../finetune/lora_adapter"

mkdir -p "$SCRIPT_DIR/vllm-logs"

# Build LoRA arguments
LORA_ARGS=""
if [ -n "$LORA_ADAPTER_PATH" ]; then
    ADAPTER_NAME=$(basename "$LORA_ADAPTER_PATH")
    LORA_ARGS="--enable-lora --max-loras 4 --max-lora-rank 64 --lora-modules {\"name\":\"$ADAPTER_NAME\",\"path\":\"/adapters/$ADAPTER_NAME\",\"base_model_name\":\"$MODEL\"}"
    VOLUME_ARGS="-v $LORA_ADAPTER_PATH:/adapters/$ADAPTER_NAME"
else
    LORA_ARGS="--enable-lora --max-loras 4 --max-lora-rank 64"
    VOLUME_ARGS=""
    # Mount default adapters directory if it exists
    if [ -d "$ADAPTERS_DIR" ]; then
        VOLUME_ARGS="-v $ADAPTERS_DIR:/adapters/default"
    fi
fi

echo "========================================"
echo "  vLLM with LoRA Support"
echo "========================================"
echo "Model:   $MODEL"
echo "Port:    $PORT"
echo "LoRA:    enabled (max 4 adapters, max rank 64)"
echo "Adapter: ${LORA_ADAPTER_PATH:-none (load at runtime via API)}"
echo ""

# Allow runtime LoRA loading/unloading
export VLLM_ALLOW_RUNTIME_LORA_UPDATING=True

sudo docker run --runtime nvidia --gpus all \
    -v ~/.cache/huggingface:/root/.cache/huggingface \
    $VOLUME_ARGS \
    --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
    --env "VLLM_ALLOW_RUNTIME_LORA_UPDATING=True" \
    -p $PORT:8000 \
    --ipc=host \
    vllm/vllm-openai:latest \
    --model $MODEL \
    --host 0.0.0.0 \
    --trust-remote-code \
    --served-model-name $MODEL \
    --swap-space 0 \
    --dtype $dtype \
    --gpu-memory-utilization $GPU_MEMORY_UTILIZATION \
    --max-model-len 32768 \
    $LORA_ARGS \
    2>&1 | tee "$LOG_FILE"
