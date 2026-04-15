import base64
from typing import Dict, Optional

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
settings = {"model": "Qwen/Qwen3-VL-8B-Instruct", "temperature": 0.7}


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


@cl.on_chat_start
def on_start():
    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )


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

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.send()
