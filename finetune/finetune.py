"""
Fine-tuning script using Unsloth + LoRA for gLLM.

Usage:
    python finetune.py --config config.yaml

Designed to run inside the unsloth/unsloth Docker container.
Saves LoRA adapters locally and optionally pushes to HuggingFace Hub.
"""

import argparse
import json
import logging
import os
import sys
from pathlib import Path

import torch
import yaml
from datasets import load_dataset, Dataset
from unsloth import FastLanguageModel
from trl import SFTTrainer
from transformers import TrainingArguments

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)


def load_config(config_path: str) -> dict:
    """Load training configuration from YAML file."""
    with open(config_path, "r") as f:
        config = yaml.safe_load(f)
    logger.info("Loaded config from %s", config_path)
    return config


def load_model(config: dict):
    """Load base model with Unsloth optimizations."""
    model_config = config["model"]

    logger.info("Loading model: %s", model_config["name"])
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_config["name"],
        max_seq_length=model_config.get("max_seq_length", 2048),
        dtype=None,  # auto-detect
        load_in_4bit=model_config.get("load_in_4bit", True),
    )

    # Add LoRA adapter
    lora_config = config.get("lora", {})
    model = FastLanguageModel.get_peft_model(
        model,
        r=lora_config.get("r", 16),
        target_modules=lora_config.get("target_modules", [
            "q_proj", "k_proj", "v_proj", "o_proj",
            "gate_proj", "up_proj", "down_proj",
        ]),
        lora_alpha=lora_config.get("lora_alpha", 16),
        lora_dropout=0,
        bias="none",
        use_gradient_checkpointing=True,
        random_state=lora_config.get("random_state", 3407),
        max_seq_length=model_config.get("max_seq_length", 2048),
    )

    logger.info("Model loaded with LoRA (r=%d, alpha=%d)", lora_config.get("r", 16), lora_config.get("lora_alpha", 16))
    return model, tokenizer


def prepare_dataset(config: dict, tokenizer) -> Dataset:
    """Load and format the training dataset."""
    data_config = config["dataset"]

    prompt_template = data_config.get("prompt_template", (
        "Below is an instruction that describes a task, paired with an input "
        "that provides further context. Write a response that appropriately "
        "completes the request.\n\n"
        "### Instruction:\n{instruction}\n\n"
        "### Input:\n{input}\n\n"
        "### Response:\n{output}"
    ))

    # Load from HuggingFace or local file
    source = data_config["source"]
    if source.endswith(".json") or source.endswith(".jsonl"):
        logger.info("Loading dataset from local file: %s", source)
        dataset = load_dataset("json", data_files=source, split="train")
    elif source.endswith(".csv"):
        logger.info("Loading dataset from CSV: %s", source)
        dataset = load_dataset("csv", data_files=source, split="train")
    else:
        logger.info("Loading dataset from HuggingFace: %s", source)
        split = data_config.get("split", "train")
        dataset = load_dataset(source, split=split)

    # Format with prompt template
    instruction_col = data_config.get("instruction_column", "instruction")
    input_col = data_config.get("input_column", "input")
    output_col = data_config.get("output_column", "output")

    def format_prompts(examples):
        texts = []
        for i in range(len(examples[instruction_col])):
            text = prompt_template.format(
                instruction=examples[instruction_col][i],
                input=examples[input_col][i] if input_col in examples else "",
                output=examples[output_col][i],
            )
            texts.append(text)
        return {"text": texts}

    dataset = dataset.map(format_prompts, batched=True)

    # Optionally limit dataset size
    max_samples = data_config.get("max_samples")
    if max_samples and max_samples < len(dataset):
        dataset = dataset.select(range(max_samples))

    logger.info("Dataset prepared: %d samples", len(dataset))
    return dataset


def train(model, tokenizer, dataset, config: dict):
    """Run the fine-tuning training loop."""
    train_config = config.get("training", {})
    model_config = config["model"]

    args = TrainingArguments(
        per_device_train_batch_size=train_config.get("batch_size", 2),
        gradient_accumulation_steps=train_config.get("gradient_accumulation_steps", 4),
        warmup_steps=train_config.get("warmup_steps", 5),
        max_steps=train_config.get("max_steps", -1),
        num_train_epochs=train_config.get("num_epochs", 3),
        learning_rate=float(train_config.get("learning_rate", 2e-4)),
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        logging_steps=train_config.get("logging_steps", 10),
        optim=train_config.get("optimizer", "adamw_8bit"),
        weight_decay=train_config.get("weight_decay", 0.01),
        lr_scheduler_type=train_config.get("lr_scheduler", "linear"),
        seed=train_config.get("seed", 3407),
        output_dir=train_config.get("output_dir", "./outputs"),
        save_strategy=train_config.get("save_strategy", "epoch"),
        report_to="none",
    )

    trainer = SFTTrainer(
        model=model,
        train_dataset=dataset,
        dataset_text_field="text",
        max_seq_length=model_config.get("max_seq_length", 2048),
        args=args,
    )

    logger.info("Starting training...")
    stats = trainer.train()
    logger.info("Training complete. Loss: %.4f", stats.training_loss)

    return trainer, stats


def save_adapter(model, tokenizer, config: dict):
    """Save LoRA adapter locally and optionally push to HuggingFace."""
    save_config = config.get("save", {})
    output_path = save_config.get("local_path", "./lora_adapter")

    # Save LoRA adapter locally
    logger.info("Saving LoRA adapter to %s", output_path)
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    # Optionally save merged model
    if save_config.get("save_merged", False):
        merged_path = save_config.get("merged_path", "./merged_model")
        logger.info("Saving merged 16-bit model to %s", merged_path)
        model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")

    # Optionally push to HuggingFace Hub
    hf_repo = save_config.get("hf_repo")
    hf_token = save_config.get("hf_token") or os.getenv("HF_TOKEN")

    if hf_repo and hf_token:
        logger.info("Pushing LoRA adapter to HuggingFace: %s", hf_repo)
        model.push_to_hub_merged(
            hf_repo, tokenizer,
            save_method="lora",
            token=hf_token,
        )
        logger.info("Successfully pushed to %s", hf_repo)
    elif hf_repo:
        logger.warning("HF_TOKEN not set. Skipping push to HuggingFace.")

    return output_path


def main():
    parser = argparse.ArgumentParser(description="Fine-tune an LLM with Unsloth + LoRA")
    parser.add_argument(
        "--config", type=str, default="config.yaml",
        help="Path to training configuration YAML file",
    )
    args = parser.parse_args()

    config = load_config(args.config)

    # Load model + LoRA
    model, tokenizer = load_model(config)

    # Prepare dataset
    dataset = prepare_dataset(config, tokenizer)

    # Train
    trainer, stats = train(model, tokenizer, dataset, config)

    # Save adapter
    output_path = save_adapter(model, tokenizer, config)

    # Save training metadata
    metadata = {
        "base_model": config["model"]["name"],
        "lora_r": config.get("lora", {}).get("r", 16),
        "lora_alpha": config.get("lora", {}).get("lora_alpha", 16),
        "dataset": config["dataset"]["source"],
        "training_loss": stats.training_loss,
        "epochs": config.get("training", {}).get("num_epochs", 3),
    }
    metadata_path = os.path.join(output_path, "training_metadata.json")
    with open(metadata_path, "w") as f:
        json.dump(metadata, f, indent=2)

    logger.info("Fine-tuning complete! Adapter saved to: %s", output_path)
    logger.info("Training metadata: %s", json.dumps(metadata, indent=2))


if __name__ == "__main__":
    main()
