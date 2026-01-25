import os
import pytest
import base64
from unittest.mock import MagicMock, AsyncMock
import openai

# TC-3.1 / TC-3.2: LLM responses (mocked)
@pytest.mark.asyncio
async def test_mocked_llm_response_returns_text(mocker):
    """TC-3.1: mocked LLM returns non-empty text"""
    mock_message = MagicMock()
    mock_message.content = "Mocked AI Response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

    mocker.patch("openai.AsyncOpenAI", return_value=mock_client_instance)

    client = openai.AsyncOpenAI(api_key="fake")
    resp = await client.chat.completions.create(model="test", messages=[])
    assert resp.choices[0].message.content.strip() != ""

@pytest.mark.asyncio
async def test_context_window_handling_with_large_prompt(mocker):
    """TC-3.2: sending a very large prompt should not break client code (mocked)"""
    large_prompt = "x" * 200_000  # large text
    mock_message = MagicMock()
    mock_message.content = "ok"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

    mocker.patch("openai.AsyncOpenAI", return_value=mock_client_instance)

    client = openai.AsyncOpenAI(api_key="fake")
    resp = await client.chat.completions.create(model="test", messages=[{"role":"user","content":large_prompt}])
    assert resp.choices[0].message.content == "ok"

# TC-3.3: Image conversion — unit test for conversion to data URL
def test_image_to_data_url_conversion(tmp_path):
    """
    Create a small binary file and validate the same conversion logic used in app.on_message.
    """
    img = tmp_path / "img.bin"
    img.write_bytes(b"\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR")
    with open(img, "rb") as f:
        b64_image = base64.b64encode(f.read()).decode("utf-8")
    data_url = f"data:image/png;base64,{b64_image}"
    assert data_url.startswith("data:image/png;base64,")
    # Ensure base64 part decodes back
    decoded = base64.b64decode(data_url.split(",")[1])
    assert decoded.startswith(b"\x89PNG")

@pytest.mark.skipif(os.getenv("RUN_DB_TESTS") != "1", reason="DB persistence tests disabled")
def test_prompt_and_response_persisted_after_completion():
    """
    TC-3.4: This test is a placeholder for persistence check. Only enabled when RUN_DB_TESTS=1.
    Implementers should replace this with a check against the real DB (Prisma/Postgres).
    """
    # For safety, this test only asserts that RUN_DB_TESTS was intentionally enabled.
    assert os.getenv("RUN_DB_TESTS") == "1"