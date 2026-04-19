import base64
from typing import Dict, Optional
import urllib.request
import urllib.error
import json
import httpx
import os
from dotenv import load_dotenv
load_dotenv()

BASE_MODEL = os.getenv("MODEL", "Qwen/Qwen2.5-7B-Instruct")
SERVED_MODEL_NAME = os.getenv("SERVED_MODEL_NAME", BASE_MODEL)

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


client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
SYSTEM_PROMPT = get_system()
settings = {"model": "Qwen/Qwen2.5-7B-Instruct", "temperature": 0.7}


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


@cl.on_chat_start
async def on_start():
    chat_profile = cl.user_session.get("chat_profile")
    
    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )
    
    if chat_profile and chat_profile != BASE_MODEL:
        print(f"Loading LoRA adapter: {chat_profile}")
        try:
            async with httpx.AsyncClient() as c:
                res = await c.post(
                    "http://localhost:8000/v1/load_lora_adapter",
                    json={
                        "lora_name": chat_profile,
                        "lora_path": chat_profile
                    },
                    timeout=30.0
                )
                if res.status_code != 200:
                    print(f"Error loading LoRA: {res.text}")
                else:
                    print(f"Successfully loaded LoRA: {chat_profile}")
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
