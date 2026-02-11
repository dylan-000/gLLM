#!/bin/bash

source .env

# Set Variables
PORT=8000

# if you have any other processes running on GPU and GPU_MEMORY_UTILIZATION * TOTAL_VRAM != AVAILABLE_VRAM, then the container will not run.
# meaning, check your GPU processes with btop or nvidia-smi to see if you have something that is consuming VRAM that vLLM is trying to access
GPU_MEMORY_UTILIZATION=0.6 
LOG_FILE="./vllm-logs/vllm.log"
MAX_SEQS=256 # This defines how many requests the inference server can process at once
dtype=auto # This can effect whether a model runs or not. auto will ensure that it runs. If VRAM is low, check the supported lowest dtype (e.g. float16).

# Run the docker container with our configuration
sudo docker run --runtime nvidia --gpus all \
  -v ~/.cache/huggingface:/root/.cache/huggingface \
  --env "HUGGING_FACE_HUB_TOKEN=$HF_TOKEN" \
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
  --max-num-seqs $MAX_SEQS \
  2>&1 | tee "$LOG_FILE"
