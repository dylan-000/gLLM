import pytest
from AuthHandler.AuthHandler import AuthHandler
from PromptManager.PromptManager import PromptManager
from pathlib import Path

def test_auth_singleton():
    """TC-1.2: Verify Singleton pattern"""
    auth1 = AuthHandler()
    auth2 = AuthHandler()
    assert auth1 is auth2

def test_system_prompt_loading(dummy_prompt_file):
    """TC-1.1: Verify Prompt Loading (uses temporary prompt fixture)"""
    pm = PromptManager()
    # Point the instance to the temporary prompts directory created by the fixture
    pm.promptsDir = str(Path(dummy_prompt_file).parent)
    assert pm.getSystem().strip() == "You are a test AI."