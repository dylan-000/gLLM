"""API endpoints for managing LoRA adapters and fine-tuning."""

import logging
import os
from pathlib import Path
from typing import Annotated, Optional

import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel

from src.schema.models import User
from src.services.authservice import get_current_active_user

logger = logging.getLogger(__name__)

FineTuningRouter = APIRouter(prefix="/finetune", tags=["fine-tuning"])

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000")
ADAPTERS_DIR = Path(__file__).resolve().parent.parent.parent / "finetune" / "lora_adapter"


# --- Models ---

class AdapterInfo(BaseModel):
    name: str
    path: str
    loaded: bool = False


class LoadAdapterRequest(BaseModel):
    adapter_name: str
    adapter_path: Optional[str] = None  # defaults to finetune/lora_adapter


class AdapterResponse(BaseModel):
    message: str
    adapter_name: str


# --- Endpoints ---

@FineTuningRouter.get("/adapters", response_model=list[AdapterInfo])
async def list_adapters(
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """List available LoRA adapters on disk."""
    adapters = []
    base_dir = ADAPTERS_DIR.parent

    if not base_dir.exists():
        return adapters

    # Check for adapter directories (contain adapter_config.json)
    for item in base_dir.iterdir():
        if item.is_dir() and (item / "adapter_config.json").exists():
            adapters.append(AdapterInfo(
                name=item.name,
                path=str(item),
                loaded=False,
            ))

    # Also check the default lora_adapter path
    if ADAPTERS_DIR.exists() and (ADAPTERS_DIR / "adapter_config.json").exists():
        if not any(a.path == str(ADAPTERS_DIR) for a in adapters):
            adapters.append(AdapterInfo(
                name="lora_adapter",
                path=str(ADAPTERS_DIR),
                loaded=False,
            ))

    return adapters


@FineTuningRouter.post("/adapters/load", response_model=AdapterResponse)
async def load_adapter(
    request: LoadAdapterRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Load a LoRA adapter into the running vLLM server."""
    adapter_path = request.adapter_path or str(ADAPTERS_DIR)

    if not Path(adapter_path).exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Adapter path not found: {adapter_path}",
        )

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VLLM_BASE_URL}/v1/load_lora_adapter",
                json={
                    "lora_name": request.adapter_name,
                    "lora_path": adapter_path,
                },
                timeout=30.0,
            )

        if resp.status_code == 200:
            logger.info("Loaded LoRA adapter '%s' from %s", request.adapter_name, adapter_path)
            return AdapterResponse(
                message=f"Adapter '{request.adapter_name}' loaded successfully.",
                adapter_name=request.adapter_name,
            )
        else:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"vLLM error: {resp.text}",
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to vLLM server. Is it running with --enable-lora?",
        )


@FineTuningRouter.post("/adapters/unload", response_model=AdapterResponse)
async def unload_adapter(
    request: LoadAdapterRequest,
    current_user: Annotated[User, Depends(get_current_active_user)],
):
    """Unload a LoRA adapter from the running vLLM server."""
    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{VLLM_BASE_URL}/v1/unload_lora_adapter",
                json={"lora_name": request.adapter_name},
                timeout=30.0,
            )

        if resp.status_code == 200:
            logger.info("Unloaded LoRA adapter '%s'", request.adapter_name)
            return AdapterResponse(
                message=f"Adapter '{request.adapter_name}' unloaded successfully.",
                adapter_name=request.adapter_name,
            )
        else:
            raise HTTPException(
                status_code=resp.status_code,
                detail=f"vLLM error: {resp.text}",
            )
    except httpx.ConnectError:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cannot connect to vLLM server.",
        )
