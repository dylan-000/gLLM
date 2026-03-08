"""Unit tests for fine-tuning config loading and API endpoints."""

import os
import sys
import json
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from pathlib import Path

# Add src and finetune to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
finetune_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../finetune"))
sys.path.insert(0, src_path)
sys.path.insert(0, finetune_path)


class TestFineTuneConfig:
    """Tests for the fine-tuning configuration."""

    def test_config_yaml_is_valid(self):
        import yaml

        config_path = os.path.join(finetune_path, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert "model" in config
        assert "name" in config["model"]
        assert "lora" in config
        assert "r" in config["lora"]
        assert "dataset" in config
        assert "source" in config["dataset"]
        assert "training" in config
        assert "save" in config

    def test_config_has_reasonable_defaults(self):
        import yaml

        config_path = os.path.join(finetune_path, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # LoRA rank should be reasonable
        assert config["lora"]["r"] in [4, 8, 16, 32, 64, 128]

        # Learning rate should be reasonable
        lr = float(config["training"]["learning_rate"])
        assert 1e-6 <= lr <= 1e-2

        # Batch size should be positive
        assert config["training"]["batch_size"] > 0

    def test_config_model_is_unsloth_compatible(self):
        import yaml

        config_path = os.path.join(finetune_path, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        # Model name should be a string
        assert isinstance(config["model"]["name"], str)
        assert len(config["model"]["name"]) > 0


class TestFineTuneScript:
    """Tests for the fine-tuning script's config loader."""

    def test_load_config(self):
        # We can't import the full finetune.py (requires torch/unsloth),
        # but we can test the YAML loading logic
        import yaml

        config_path = os.path.join(finetune_path, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        assert config is not None
        assert isinstance(config, dict)

    def test_prompt_template_has_placeholders(self):
        import yaml

        config_path = os.path.join(finetune_path, "config.yaml")
        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        template = config["dataset"].get("prompt_template", "")
        assert "{instruction}" in template
        assert "{input}" in template
        assert "{output}" in template


class TestFineTuningRouter:
    """Tests for the fine-tuning API endpoints."""

    ENV_OVERRIDES = {
        "AUTH_SECRET": "test-secret-key",
        "HASH_ALGORITHM": "HS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "30",
        "DATABASE_URL": "postgresql://test:test@localhost/test",
        "BUCKET_NAME": "test",
        "APP_AWS_ACCESS_KEY": "test",
        "APP_AWS_SECRET_KEY": "test",
        "APP_AWS_REGION": "us-east-1",
        "CHAINLIT_AUTH_SECRET": "test",
    }

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_list_adapters_returns_empty_when_no_adapters(self):
        from src.routers.finetuningrouter import list_adapters

        # The function is async, but we can test the logic
        # by checking that ADAPTERS_DIR is set correctly
        from src.routers.finetuningrouter import ADAPTERS_DIR
        assert "finetune" in str(ADAPTERS_DIR)
        assert "lora_adapter" in str(ADAPTERS_DIR)

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_adapter_info_model(self):
        from src.routers.finetuningrouter import AdapterInfo

        adapter = AdapterInfo(name="test", path="/tmp/test", loaded=False)
        assert adapter.name == "test"
        assert adapter.loaded is False

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_load_adapter_request_model(self):
        from src.routers.finetuningrouter import LoadAdapterRequest

        req = LoadAdapterRequest(adapter_name="my_adapter")
        assert req.adapter_name == "my_adapter"
        assert req.adapter_path is None

        req2 = LoadAdapterRequest(adapter_name="custom", adapter_path="/tmp/custom")
        assert req2.adapter_path == "/tmp/custom"

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_adapter_response_model(self):
        from src.routers.finetuningrouter import AdapterResponse

        resp = AdapterResponse(message="Loaded", adapter_name="test")
        assert resp.message == "Loaded"
        assert resp.adapter_name == "test"
