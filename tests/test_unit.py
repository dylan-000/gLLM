import os
import socket
import json
import pytest
import httpx
from pathlib import Path

from AuthHandler.AuthHandler import AuthHandler
from PromptManager.PromptManager import PromptManager

# TC-1.1 / TC-1.2: auth singleton + login callback (app uses credentials "admin"/"admin")
def test_auth_singleton():
    auth1 = AuthHandler()
    auth2 = AuthHandler()
    assert auth1 is auth2

def test_system_prompt_loading(dummy_prompt_file):
    pm = PromptManager()
    pm.promptsDir = str(Path(dummy_prompt_file).parent)
    assert pm.getSystem().strip() == "You are a test AI."

@pytest.mark.skipif(os.getenv("TEST_PROMPT_FALLBACK") != "1", reason="Fallback behaviour not enabled")
def test_system_prompt_fallback(tmp_path, monkeypatch):
    """
    TC-2.2: Only run if TEST_PROMPT_FALLBACK=1. Requires PromptManager to implement a fallback.
    """
    # Remove System.txt and expect a fallback to be returned (implementation dependent).
    d = tmp_path / "Prompts"
    d.mkdir()
    monkeypatch.setenv("SYSTEM_PROMPT_PATH", str(d))
    pm = PromptManager()
    pm.promptsDir = str(d)
    # If implementation supports fallback it should return a non-empty string
    fallback = pm.getSystem()
    assert isinstance(fallback, str)
    assert fallback.strip() != ""

def test_json_parsing_of_inference_response():
    """
    TC-2.3: Ensure system code can parse JSON responses when LLM returns JSON string.
    This is a basic unit test of json.loads usage rather than a full streaming parser test.
    """
    payload = '{"answer": "42", "confidence": 0.99}'
    parsed = json.loads(payload)
    assert parsed["answer"] == "42"
    assert parsed["confidence"] == 0.99

@pytest.mark.live
def test_vllm_connectivity_http():
    """
    TC-2.4: Verifies connectivity via HTTP.
    """
    url = "http://localhost:8000/v1/models"
    
    try:
        response = httpx.get(url, timeout=5)
        # 200 OK means the server is actually happy and running
        assert response.status_code == 200
        # Ensure we got valid JSON back
        data = response.json()
        assert "data" in data
    except httpx.RequestError as e:
        pytest.fail(f"Could not connect to vLLM: {e}")

# TC-1.3: DB connectivity (separate test)
@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="DB tests disabled")
def test_db_tcp_connectivity():
    """
    TC-1.3: Lightweight connectivity check for Database host/port parsed from DATABASE_URL.
    Set RUN_DB_TESTS=1 and ensure DATABASE_URL exists in env.
    """
    db_url = os.getenv("DATABASE_URL")
    assert db_url, "DATABASE_URL must be set to run DB connectivity test"

    # crude parse: postgres://user:pass@host:port/db
    try:
        hostport = db_url.split("@")[1].split("/")[0]
        host, port = hostport.split(":")
        port = int(port)
    except Exception as e:
        pytest.skip(f"Unable to parse DATABASE_URL: {e}")

    # attempt TCP connect to DB host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((host, port))
    except Exception as e:
        pytest.fail(f"Could not connect to DB host {host}:{port} - {e}")


# TC-1.4: S3/MinIO connectivity (separate test)
@pytest.mark.skipif(os.getenv("RUN_S3_TESTS") != "1", reason="S3 tests disabled")
def test_s3_tcp_connectivity():
    """
    TC-1.4: Lightweight connectivity check for S3 endpoint host/port.
    Set RUN_S3_TESTS=1 and ensure S3_ENDPOINT or S3_URL exists in env.
    """
    s3_endpoint = os.getenv("S3_ENDPOINT") or os.getenv("S3_URL") or os.getenv("BUCKET_ENDPOINT")
    assert s3_endpoint, "S3_ENDPOINT or S3_URL (or BUCKET_ENDPOINT) must be set to run S3 connectivity test"

    # parse s3 host:port if present
    if "://" in s3_endpoint:
        s3_hostport = s3_endpoint.split("://")[1].split("/")[0]
    else:
        s3_hostport = s3_endpoint.split("/")[0]

    try:
        s3_host, s3_port = s3_hostport.split(":")
        s3_port = int(s3_port)
    except ValueError:
        s3_host = s3_hostport
        s3_port = 9000  # default (minio) fallback

    # attempt TCP connect to S3 host
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.settimeout(3.0)
            s2.connect((s3_host, s3_port))
    except Exception as e:
        pytest.fail(f"Could not connect to S3 host {s3_host}:{s3_port} - {e}")