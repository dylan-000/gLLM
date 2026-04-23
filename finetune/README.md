# Fine-Tuning with Unsloth + LoRA

Fine-tune LLMs using [Unsloth](https://unsloth.ai/) with LoRA adapters, then serve them via vLLM.

## Prerequisites

- Docker with NVIDIA Container Toolkit
- NVIDIA GPU (16GB+ VRAM recommended)
- `HF_TOKEN` environment variable (for downloading gated models / pushing adapters)

## Quick Start

1. **Edit the config** — copy `config.yaml` and adjust model, dataset, and training params:
   ```bash
   cp config.yaml my_config.yaml
   # Edit my_config.yaml
   ```

2. **Run fine-tuning**:
   ```bash
   ./run_finetune.sh my_config.yaml
   ```

3. **Serve with LoRA** — start vLLM with adapter support:
   ```bash
   ../vllmconfig/vllminit_lora.sh ./lora_adapter
   ```

4. **Or load adapters at runtime** via the API:
   ```bash
   # Start vLLM with LoRA enabled (no adapter loaded yet)
   ../vllmconfig/vllminit_lora.sh

   # Load adapter via API
   curl -X POST http://localhost:8000/v1/load_lora_adapter \
     -H "Content-Type: application/json" \
     -d '{"lora_name": "my_adapter", "lora_path": "/adapters/default"}'

   # Use the adapter in chat
   curl http://localhost:8000/v1/chat/completions \
     -H "Content-Type: application/json" \
     -d '{"model": "my_adapter", "messages": [{"role": "user", "content": "Hello"}]}'
   ```

## Configuration

See `config.yaml` for all available options:

| Section | Key Options |
|---------|-------------|
| `model` | `name`, `max_seq_length`, `load_in_4bit` |
| `lora` | `r` (rank), `lora_alpha`, `target_modules` |
| `dataset` | `source` (HF name or local file), column mappings, `prompt_template` |
| `training` | `batch_size`, `num_epochs`, `learning_rate`, `optimizer` |
| `save` | `local_path`, `hf_repo` (push to HuggingFace), `save_merged` |

## Backend API

The gLLM backend exposes endpoints for managing adapters (requires `fine_tuner` or `admin` role):

- `GET /finetune/adapters` — list available adapters on disk
- `POST /finetune/adapters/load` — load an adapter into vLLM
- `POST /finetune/adapters/unload` — unload an adapter from vLLM

## Custom Datasets

Prepare your dataset as JSON with `instruction`, `input`, `output` fields:

```json
[
  {
    "instruction": "Summarize the following text",
    "input": "Long text here...",
    "output": "Summary here..."
  }
]
```

Then set `source: "path/to/your_data.json"` in the config.
