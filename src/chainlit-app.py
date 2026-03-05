import base64
from typing import Dict, Optional

import chainlit as cl
from chainlit.types import ThreadDict
from openai import AsyncOpenAI
from jwt.exceptions import InvalidTokenError
from fastapi import Request, Response
import http
import jwt

from src.services.promptservice import PromptService
from src.services.adminservice import AdminService
from src.db.database import get_db
from src.core.config import Settings
from src.models.auth import TokenData
from src.schema.models import UserRole
from src.services.ragutils import ingestion
from src.services.ragutils import retrieval
from sqlalchemy.orm import Session
from fastapi import Depends

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
pm = PromptService()
SYSTEM_PROMPT = pm.get_system()
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
    print(f'Incoing headers: {headers}\n')
    token = headers.get("bearer")

    if not token:
        print("DEBUG: No token found.")
        return None
    else:
        print("Found Token")
    app_settings = Settings()

    try:
        db_generator = get_db()
        db = next(db_generator)
        admin_service = AdminService()
        payload = jwt.decode(
            token, app_settings.AUTH_SECRET, algorithms=[app_settings.HASH_ALGORITHM]
        )
        username = payload.get("sub")
        if username is None:
            raise Exception("Invalid Token. No username.")
        else:
            print(f"Username: {username}")
        token_data = TokenData(username=username)
        user = admin_service.get_user_from_identifier( # This is returning an error
            identifier=token_data.username, db=db
        )
    except InvalidTokenError:
        raise Exception("Invalid Token Error")
    except Exception as e:
        print(f'ERROR OCCURRED DURING CHAINLIT HEADER AUTH VALIDATION:\n{e}\n')
        return None

    if user is None:
        print('no user actually found')
        return None
    elif user.role == UserRole.unauthorized:
        print('User is a scrub and is unauthorized')
        return None

    print(f'success. user {user.identifier} allowed in')
    return cl.User(
        identifier=f"{user.identifier}",
        metadata={"role": f"{user.role}", "provider": "header"},
    )


@cl.on_logout
def main(request: Request, response: Response):
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

    # Call RAG_utils retrieval module to get context
    context_str = retrieval.get_context(cl_msg.content, user_id)

    # Combine user query with retrieved context (if any)
    final_query = cl_msg.content
    if context_str:
        final_query = f"Document Context: {context_str}\n\nUser Query: {cl_msg.content}"

    # Construct the openAI-format message with the final_query
    message = {"role": "user", "content": [{"type": "text", "text": final_query}]}

    # Now process images (if any), which will be appended to message["content"]
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
