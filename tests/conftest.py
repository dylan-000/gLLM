import pytest
import os
import sys
from dotenv import load_dotenv

# 1. Add 'src' to the python path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../src'))
sys.path.insert(0, src_path)

# 2. Load the .env file explicitly
env_path = os.path.join(src_path, '.env')
load_dotenv(env_path)

@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """
    Sets defaults for tests, but allows real .env values to override if present.
    """
    if not os.getenv("APP_USER"):
        monkeypatch.setenv("APP_USER", "test_admin")
    if not os.getenv("APP_PASS"):
        monkeypatch.setenv("APP_PASS", "test_pass")
        
    # Always force a dummy prompt path for unit tests
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", "./tests/dummy_prompt.txt")

@pytest.fixture
def dummy_prompt_file(tmp_path):
    """
    Creates a temporary system prompt file for testing PromptManager.
    """
    d = tmp_path / "Prompts"
    d.mkdir()
    p = d / "System.txt"
    p.write_text("You are a test AI.")
    return str(p)