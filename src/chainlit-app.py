import base64
from typing import Dict, Optional

import os
from dotenv import load_dotenv

# 1. Force load the .env file BEFORE importing Chainlit
load_dotenv()

# 2. Diagnostic Check (Watch your terminal for this line!)
print(f"CHAINLIT AUTH STATUS: {'ENABLED' if os.environ.get('CHAINLIT_AUTH_SECRET') else 'DISABLED - SECRET NOT FOUND'}")

import chainlit as cl
from chainlit.types import ThreadDict
import langfuse.openai  # noqa: F401 — registers OpenAI completion wrappers for tracing
from langfuse import Langfuse
from langfuse.openai import AsyncOpenAI
from jwt.exceptions import InvalidTokenError
from fastapi import Request, Response
import http
import jwt

from src.services.promptservice import get_system
from src.services.adminservice import get_user_from_identifier
from src.db.database import SessionLocal, get_db
from src.core.config import Settings
from src.models.auth import TokenData
from src.schema.models import UserRole
from src.services.ragutils import ingestion
from src.services.ragutils import retrieval
from datetime import datetime, timezone


# client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
# cl.instrument_openai()
SYSTEM_PROMPT = get_system()
settings = {"model": "gLLM Default", "temperature": 0.7}

VLLM_BASE_URL = os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1")


def _langfuse_keys_for_identifier(identifier: str) -> tuple[str, str]:
    """Load keys from DB. Chainlit does not reliably persist custom fields on cl.User.metadata."""
    with SessionLocal() as db:
        row = get_user_from_identifier(identifier=identifier, db=db)
        if not row:
            return "", ""
        pk = (row.langfuse_public_key or "").strip()
        sk = (row.langfuse_secret_key or "").strip()
        return pk, sk


def setup_session_client(user: Optional[cl.User]):
    """Creates an LLM client; registers a per-user Langfuse project for OpenAI wrappers (SDK v4)."""

    identifier = getattr(user, "identifier", None) if user else None
    pk, sk = ("", "")
    if identifier:
        pk, sk = _langfuse_keys_for_identifier(identifier)

    print("\n--- DEBUG: SESSION SETUP ---")
    print(f"User identifier: {identifier!r}")
    print(f"Langfuse keys present (from DB): public={bool(pk)}, secret={bool(sk)}")
    print("----------------------------\n")

    host = Settings().LANGFUSE_HOST

    if pk and sk:
        # Registers LangfuseResourceManager for this public_key so get_client() can export traces
        Langfuse(public_key=pk, secret_key=sk, host=host)
        client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key="empty")
        cl.user_session.set("is_langfuse_enabled", True)
        cl.user_session.set("langfuse_public_key", pk)
    else:
        print("⚠️ No Langfuse keys in DB for this user. Using OpenAI client without Langfuse export.")
        client = AsyncOpenAI(base_url=VLLM_BASE_URL, api_key="empty")
        cl.user_session.set("is_langfuse_enabled", False)
        cl.user_session.set("langfuse_public_key", None)

    cl.user_session.set("llm_client", client)


@cl.on_chat_resume
async def on_chat_resume(thread: ThreadDict):

    user = cl.user_session.get("user")
    setup_session_client(user)

    steps = sorted(thread["steps"], key=lambda msg: msg.get("created_at", 0))
    cl.user_session.set(
        "message_history",
        [{"role": "system", "content": SYSTEM_PROMPT}],
    )

    for message in thread["steps"]:
        if message["type"] == "user_message":
            cl.user_session.get("message_history").append(
                {"role": "user", "content": message["output"]}
            )
        elif message["type"] == "assistant_message":
            cl.user_session.get("message_history").append(
                {"role": "assistant", "content": message["output"]}
            )


"""@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:
    '''
    Authenticates user from HttpOnly cookie containing JWT.
    The browser automatically sends the auth_token cookie with requests.

    This callback is called when a user accesses the Chainlit app.
    '''
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
        payload = jwt.decode(
            auth_token, settings.AUTH_SECRET, algorithms=[settings.HASH_ALGORITHM]
        )

        username = payload.get("sub")
        expire_at = payload.get("exp")

        if not username:
            print("Username (sub) not found in token payload")
            return None
        
        if datetime.now(timezone.utc) > datetime.fromtimestamp(expire_at, timezone.utc):
            print("Token has expired")
            return None

        # Fetch user from database
        db_generator = get_db()
        db = next(db_generator)
        user = get_user_from_identifier(identifier=username, db=db)

        print(f"\n--- DEBUG: HEADER AUTH ---")
        print(f"1. Fetched User: {user.identifier}")
        print(f"2. Raw DB Public Key: {getattr(user, 'langfuse_public_key', 'ATTRIBUTE MISSING')}")
        print(f"3. Raw DB Secret Key: {'[HIDDEN]' if getattr(user, 'langfuse_secret_key', None) else 'ATTRIBUTE MISSING'}")
        print(f"--------------------------\n")

        if not user:
            print(f"User {username} not found in database")
            return None

        if user.role == UserRole.unauthorized:
            print(f"User {username} is unauthorized")
            return None

        print(f"User {username} authenticated with role {user.role}")
        return cl.User(
            identifier=username,
            metadata={"role": user.role.value,
                      "email": user.email,
                      "langfuse_public_key": getattr(user, "langfuse_public_key", ""),
                      "langfuse_secret_key": getattr(user, "langfuse_secret_key", "")
                    },
        )

    except jwt.ExpiredSignatureError:
        print("Token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid token: {e}")
        return None
    except Exception as e:
        print(f"Unexpected error in header_auth_callback: {e}")
        return None
    
"""

@cl.header_auth_callback
def header_auth_callback(headers: Dict) -> Optional[cl.User]:
    # 1. Extract the HttpOnly cookie set by your React app
    cookie_header = headers.get("cookie") or headers.get("Cookie") or ""
    token = None
    for cookie in cookie_header.split(";"):
        if "auth_token=" in cookie:
            token = cookie.split("auth_token=")[1].strip()
            break

    if not token:
        print("DEBUG: No auth_token cookie found in browser request.")
        return None

    # 2. Decode the JWT to get the username
    try:
        payload = jwt.decode(
            token, Settings().AUTH_SECRET, algorithms=[Settings().HASH_ALGORITHM]
        )
        username = payload.get("sub")
        if not username:
            print("DEBUG: JWT missing 'sub' claim.")
            return None
    except Exception as e:
        print(f"DEBUG: JWT Decode failed: {e}")
        return None

    # 3. Fetch the user and their Langfuse keys from the database
    try:
        db_generator = get_db()
        db = next(db_generator)
        user = get_user_from_identifier(identifier=username, db=db)
        
        if not user or user.role == UserRole.unauthorized:
            print(f"DEBUG: User {username} unauthorized or not found.")
            return None
    except Exception as e:
        print(f"DEBUG: Database fetch failed: {e}")
        return None

    # 4. Print our success milestone!
    print(f"\n--- DEBUG: HEADER AUTH ---")
    print(f"1. Fetched User: {user.identifier}")
    print(f"2. DB Public Key: {getattr(user, 'langfuse_public_key', 'MISSING')}")
    print(f"--------------------------\n")

    # 5. Lock the keys into the Chainlit Session
    return cl.User(
        identifier=username,
        metadata={
            "role": user.role.value, 
            "email": user.email,
            "langfuse_public_key": getattr(user, "langfuse_public_key", ""),
            "langfuse_secret_key": getattr(user, "langfuse_secret_key", "")
        }
    )

@cl.on_logout
def logout(request: Request, response: Response):
    response.delete_cookie("my_cookie")


@cl.on_chat_start
def on_start():

    user = cl.user_session.get("user")
    setup_session_client(user)

    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )


@cl.on_message
async def on_message(cl_msg: cl.Message):

    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    thread_id = cl.context.session.thread_id

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
                thread_id=thread_id,
            )

    context_str = retrieval.get_context(cl_msg.content, user_id, thread_id)

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

    client = cl.user_session.get("llm_client")
    is_langfuse_enabled = cl.user_session.get("is_langfuse_enabled")
    lf_pk = cl.user_session.get("langfuse_public_key")

    kwargs = {
        "messages": message_history,
        "stream": True,
        **settings,
    }

    # Langfuse OpenAI integration reads these on chat.completions.create (not on the client ctor)
    if is_langfuse_enabled and lf_pk:
        kwargs.update(
            {
                "langfuse_public_key": lf_pk,
                "name": "RAG_Generation",
                "metadata": {
                    "session_id": thread_id,
                    "user_id": user_id,
                    "tags": ["rag-pipeline"],
                },
            }
        )

    stream = await client.chat.completions.create(**kwargs)

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.send()
