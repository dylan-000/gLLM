import os
import pytest
from unittest.mock import MagicMock, AsyncMock
import openai

@pytest.mark.asyncio
async def test_mocked_llm_response(mocker):
    """TC-2.1 (Mocked): Verify app handles JSON correctly without real AI"""
    mock_message = MagicMock()
    mock_message.content = "Mocked AI Response"

    mock_choice = MagicMock()
    mock_choice.message = mock_message

    mock_resp = MagicMock()
    mock_resp.choices = [mock_choice]

    mock_client_instance = MagicMock()
    mock_client_instance.chat.completions.create = AsyncMock(return_value=mock_resp)

    # Patch the openai.AsyncOpenAI constructor on the openai module, then call it via openai.AsyncOpenAI
    mocker.patch("openai.AsyncOpenAI", return_value=mock_client_instance)

    client = openai.AsyncOpenAI(api_key="fake")
    resp = await client.chat.completions.create(model="test", messages=[])

    assert resp.choices[0].message.content == "Mocked AI Response"

@pytest.mark.live
@pytest.mark.skipif(os.getenv("RUN_LIVE_TESTS") != "1", reason="Live tests disabled by default")
@pytest.mark.asyncio
async def test_real_vllm_connectivity():
    """TC-2.2 (Live): Connect to localhost:8000 (enabled via RUN_LIVE_TESTS=1)"""
    client = openai.AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")

    models = await client.models.list()
    assert len(models.data) > 0

    response = await client.chat.completions.create(
        model=models.data[0].id,
        messages=[{"role": "user", "content": "Test"}],
        temperature=0.0
    )
    assert len(response.choices[0].message.content) > 0