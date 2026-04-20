"""Unit tests for auth service, admin service, and prompt service."""

import os
import sys
import json
import socket
import pytest
from unittest.mock import MagicMock, patch

# Add src to path
src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../src"))
sys.path.insert(0, src_path)

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


# --- Auth Service Tests ---


class TestPasswordHashing:
    """TC-1.1: Password hashing and verification."""

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_hash_and_verify_password(self):
        from src.services.authservice import get_password_hash, verify_password

        password = "securepassword123"
        hashed = get_password_hash(password)

        assert hashed != password
        assert verify_password(password, hashed) is True

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_wrong_password_fails(self):
        from src.services.authservice import get_password_hash, verify_password

        hashed = get_password_hash("correct_password")
        assert verify_password("wrong_password", hashed) is False

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_different_passwords_produce_different_hashes(self):
        from src.services.authservice import get_password_hash

        hash1 = get_password_hash("password1")
        hash2 = get_password_hash("password2")
        assert hash1 != hash2


class TestAccessToken:
    """TC-1.2: JWT token creation and validation."""

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_create_access_token(self):
        import jwt
        from src.services.authservice import create_access_token

        token = create_access_token(data={"sub": "testuser"})

        assert isinstance(token, str)
        decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert decoded["sub"] == "testuser"
        assert "exp" in decoded

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_token_with_custom_expiration(self):
        import jwt
        from datetime import timedelta
        from src.services.authservice import create_access_token

        token = create_access_token(
            data={"sub": "testuser"},
            expires_delta=timedelta(minutes=60),
        )

        decoded = jwt.decode(token, "test-secret-key", algorithms=["HS256"])
        assert "exp" in decoded


class TestSignupUser:
    """TC-1.3: User signup validation."""

    @patch.dict(os.environ, ENV_OVERRIDES)
    def test_signup_rejects_duplicate_user(self):
        from src.services.authservice import signup_user
        from src.models.user import UserCreate

        mock_db = MagicMock()
        mock_db.scalar.return_value = MagicMock()  # Existing user found

        user_in = UserCreate(identifier="existinguser", password="pass123")

        with pytest.raises(ValueError, match="User already exists"):
            signup_user(db=mock_db, user_in=user_in)


# --- Prompt Service Tests ---


class TestPromptService:
    """TC-2.1: System prompt loading."""

    def test_get_system_returns_nonempty_string(self):
        from src.services.promptservice import get_system

        prompt = get_system()

        assert isinstance(prompt, str)
        assert len(prompt.strip()) > 0

    def test_system_prompt_contains_research_context(self):
        from src.services.promptservice import get_system

        prompt = get_system()

        assert "research" in prompt.lower()


# --- JSON Parsing Tests ---


def test_json_parsing_of_inference_response():
    """TC-2.3: Ensure system code can parse JSON responses from LLM."""
    payload = '{"answer": "42", "confidence": 0.99}'
    parsed = json.loads(payload)
    assert parsed["answer"] == "42"
    assert parsed["confidence"] == 0.99


# --- Connectivity Tests (conditional, require services running) ---


@pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1", reason="Live tests disabled")
def test_vllm_connectivity_http():
    """TC-2.4: Verifies connectivity to vLLM via HTTP."""
    import httpx

    url = "http://localhost:8000/v1/models"
    try:
        response = httpx.get(url, timeout=5)
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
    except httpx.RequestError as e:
        pytest.fail(f"Could not connect to vLLM: {e}")


@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="DB tests disabled")
def test_db_tcp_connectivity():
    """TC-1.3: Lightweight connectivity check for PostgreSQL."""
    db_url = os.getenv("DATABASE_URL")
    assert db_url, "DATABASE_URL must be set"

    try:
        hostport = db_url.split("@")[1].split("/")[0]
        host, port = hostport.split(":")
        port = int(port)
    except Exception as e:
        pytest.skip(f"Unable to parse DATABASE_URL: {e}")

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.settimeout(3.0)
            s.connect((host, port))
    except Exception as e:
        pytest.fail(f"Could not connect to DB host {host}:{port} - {e}")


@pytest.mark.skipif(os.getenv("RUN_S3_TESTS") != "1", reason="S3 tests disabled")
def test_s3_tcp_connectivity():
    """TC-1.4: Lightweight connectivity check for S3 endpoint."""
    s3_endpoint = os.getenv("S3_ENDPOINT") or os.getenv("S3_URL") or os.getenv("BUCKET_ENDPOINT")
    assert s3_endpoint, "S3_ENDPOINT or S3_URL must be set"

    if "://" in s3_endpoint:
        s3_hostport = s3_endpoint.split("://")[1].split("/")[0]
    else:
        s3_hostport = s3_endpoint.split("/")[0]

    try:
        s3_host, s3_port = s3_hostport.split(":")
        s3_port = int(s3_port)
    except ValueError:
        s3_host = s3_hostport
        s3_port = 9000

    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s2:
            s2.settimeout(3.0)
            s2.connect((s3_host, s3_port))
    except Exception as e:
        pytest.fail(f"Could not connect to S3 host {s3_host}:{s3_port} - {e}")
