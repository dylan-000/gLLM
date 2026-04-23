import base64
from typing import Dict, Optional
import urllib.request
import urllib.error
import json
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

import chainlit as cl
from chainlit.types import ThreadDict
from openai import AsyncOpenAI
from jwt.exceptions import InvalidTokenError
from fastapi import Request, Response
import http
import jwt

from src.services.promptservice import get_system
from src.services.adminservice import get_user_from_identifier
from src.db.database import get_db
from src.core.config import Settings
from src.models.auth import TokenData
from src.schema.models import UserRole
from src.services.ragutils import ingestion
from src.services.ragutils import retrieval
from datetime import datetime, timezone

from huggingface_hub import snapshot_download
from safetensors.torch import load_file, save_file
import asyncio
import shutil

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
SYSTEM_PROMPT = get_system()
settings = {"model": "gLLM Default", "temperature": 0.7}
BASE_MODEL = settings["model"]


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):
    cl.user_session.set("message_history", [])

    for message in thread["steps"]:
        if message["type"] == "user_message":
            cl.user_session.get("message_history").append(
                {"role": "user", "content": message["output"]}
            )
        elif message["type"] == "assistant_message":
            cl.user_session.get("message_history").append(
                {"role": "assistant", "content": message["output"]}
            )


@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:
    """
    Authenticates user from HttpOnly cookie containing JWT.
    The browser automatically sends the auth_token cookie with requests.

    This callback is called when a user accesses the Chainlit app.
    """
    try:
        cookie_header = headers.get("Cookie")

        if not cookie_header:
            print("No Cookie header found")
            return None

        auth_token = None
        for cookie in cookie_header.split(";"):
            cookie = cookie.strip()
            if cookie.startswith("auth_token="):
                auth_token = cookie.split("=", 1)[1]
                break

        if not auth_token:
            print("auth_token not found in cookies")
            return None

        settings = Settings()
        try:
            payload = jwt.decode(
                auth_token, settings.AUTH_SECRET, algorithms=[settings.HASH_ALGORITHM]
            )
        except jwt.ExpiredSignatureError:
            print("Token has expired")
            return None
        except jwt.InvalidTokenError as e:
            print(f"Invalid token: {e}")
            return None

        username = payload.get("sub")
        expire_at = payload.get("exp")

        if not username:
            print("Username (sub) not found in token payload")
            return None
        if datetime.now(timezone.utc) > datetime.fromtimestamp(expire_at, timezone.utc):
            print("Token has expired")
            return None

        try:
            db_generator = get_db()
            db = next(db_generator)
            user = get_user_from_identifier(identifier=username, db=db)

            if not user:
                print(f"User {username} not found in database")
                return None

            if user.role == UserRole.unauthorized:
                print(f"User {username} is unauthorized")
                return None

            print(f"User {username} authenticated with role {user.role}")
            return cl.User(
                identifier=username,
                metadata={"role": user.role.value, "email": user.email},
            )
        except Exception as e:
            print(f"Error fetching user from database: {e}")
            return None

    except Exception as e:
        print(f"Unexpected error in header_auth_callback: {e}")
        return None


@cl.on_logout
def logout(request: Request, response: Response):
    response.delete_cookie("my_cookie")


@cl.set_chat_profiles
async def chat_profile(current_user: Optional[cl.User] = None):
    profiles = [
        cl.ChatProfile(
            name=SERVED_MODEL_NAME,
            markdown_description=f"Base model ({BASE_MODEL}) with no LoRA adapter.",
        )
    ]
    
    url = "https://huggingface.co/api/collections/nateenglert04/gllm-lora-adapaters-69e30bddbcc2181a634a925f"
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(url, headers={'User-Agent': 'Chainlit-App'}, timeout=5.0)
            if response.status_code == 200:
                data = response.json()
                items = data.get('items', [])
                for item in items:
                    if item.get("type") == "model":
                        repo_id = item.get("id")
                        if repo_id:
                            profiles.append(
                                cl.ChatProfile(
                                    name=repo_id,
                                    markdown_description=f"LoRA Adapter: **{repo_id}** dynamically loaded from Hugging Face.",
                                )
                            )
    except Exception as e:
        print(f"Error fetching HF collection: {e}")
        

        
    return profiles


lora_download_locks = {}

@cl.on_chat_start
async def on_start():
    chat_profile = cl.user_session.get("chat_profile")
    
    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )
    
    if chat_profile and chat_profile != BASE_MODEL:
        # Create a lock for this specific model if it doesn't exist yet
        if chat_profile not in lora_download_locks:
            lora_download_locks[chat_profile] = asyncio.Lock()
        
        async with lora_download_locks[chat_profile]:
            print(f"Loading LoRA adapter: {chat_profile}")
            try:
                def filter_safetensors(path):
                    try:
                        tensors = load_file(path)
                        unsupported_layers = ["embed_tokens", "lm_head"]
                        filtered_tensors = {}
                        for key, tensor in tensors.items():
                            if "lora" in key and not any(bad_layer in key for bad_layer in unsupported_layers):
                                filtered_tensors[key] = tensor
                                
                        # If we successfully removed the bad layers, save the file back
                        if len(filtered_tensors) < len(tensors):
                            save_file(filtered_tensors, path)
                            print(f"Successfully stripped unsupported layers from {os.path.basename(path)}")
                            
                    except Exception as e:
                        print(f"Error filtering safetensors {path}: {e}")

                def patch_lora():
                    local_dir = snapshot_download(repo_id=chat_profile)
                    patched_dir = os.path.expanduser(f"~/.cache/huggingface/patched_loras/{chat_profile.replace('/', '_')}")
                    os.makedirs(patched_dir, exist_ok=True)
                    for item in os.listdir(local_dir):
                        s = os.path.join(local_dir, item)
                        d = os.path.join(patched_dir, item)
                        if os.path.isdir(s) and not os.path.exists(d):
                            shutil.copytree(s, d)
                        elif not os.path.isdir(s) and not os.path.exists(d):
                            shutil.copy2(s, d)
                    
                    config_path = os.path.join(patched_dir, "adapter_config.json")
                    if os.path.exists(config_path):
                        with open(config_path, "r") as f:
                            config = json.load(f)
                        
                        # Nullify modules_to_save
                        if config.get("modules_to_save") is not None:
                            config["modules_to_save"] = None
                            
                        # Filter target_modules to only include what vLLM supports
                        if isinstance(config.get("target_modules"), list):
                            supported_modules = {'k_proj', 'up_proj', 'down_proj', 'gate_proj', 'q_proj', 'v_proj', 'o_proj'}
                            config["target_modules"] = [m for m in config["target_modules"] if m in supported_modules]

                        with open(config_path, "w") as f:
                            json.dump(config, f, indent=2)

                    for item in os.listdir(patched_dir):
                        if item.endswith(".safetensors"):
                            safetensors_path = os.path.join(patched_dir, item)
                            try:
                                filter_safetensors(safetensors_path)
                            except Exception as e:
                                print(f"Error filtering safetensors {item}: {e}")

                    return f"/root/.cache/huggingface/patched_loras/{chat_profile.replace('/', '_')}"

                lora_path_container = await asyncio.to_thread(patch_lora)

                async with httpx.AsyncClient() as c:
                    res = await c.post(
                        "http://localhost:8000/v1/load_lora_adapter",
                        json={
                            "lora_name": chat_profile,
                            "lora_path": lora_path_container
                        },
                        timeout=30.0
                    )
                    
                    # Check for successful load OR if it's already loaded
                    if res.status_code == 200:
                        print(f"Successfully loaded LoRA: {chat_profile}")
                    elif res.status_code == 400 and "already been loaded" in res.text:
                        print(f"LoRA {chat_profile} is already active in vLLM.")
                    else:
                        print(f"Error loading LoRA: {res.text}")
            except Exception as e:
                print(f"Failed to trigger LoRA load: {e}")


@cl.on_message
async def on_message(cl_msg: cl.Message):

    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"

    IMAGES = []
    DOCS = []

    for file in cl_msg.elements:
        if "image" in file.mime:
            IMAGES.append(file)
        else:
            DOCS.append(file)

    if DOCS:
        for doc in DOCS:
            ingestion.ingest_file(
                file_path=doc.path,
                file_id=doc.id,
                file_name=doc.name,
                file_type=doc.mime,
                user_id=user_id,
            )

    context_str = retrieval.get_context(cl_msg.content, user_id)

    final_query = cl_msg.content
    if context_str:
        final_query = f"Document Context: {context_str}\n\nUser Query: {cl_msg.content}"

    message = {"role": "user", "content": [{"type": "text", "text": final_query}]}

    for image in IMAGES:
        with open(image.path, "rb") as image_file:
            b64_image = base64.b64encode(image_file.read()).decode("utf-8")
        message["content"].append(
            {
                "type": "image_url",
                "image_url": {"url": f"data:image/png;base64,{b64_image}"},
            },
        )

    message_history = cl.user_session.get("message_history")
    message_history.append(message)

    msg = cl.Message(content="")

    profile_name = cl.user_session.get("chat_profile")
    target_model = profile_name if profile_name and profile_name != SERVED_MODEL_NAME else SERVED_MODEL_NAME
    
    current_settings = settings.copy()
    current_settings["model"] = target_model

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **current_settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.send()
