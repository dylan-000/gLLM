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
import json
from mcp import ClientSession

from src.services.promptservice import get_system
from src.services.adminservice import get_user_from_identifier
from src.db.database import SessionLocal, get_db
from src.core.config import Settings
from src.models.auth import TokenData
from src.schema.models import UserRole
from src.services.ragutils import ingestion
from src.services.ragutils import retrieval
from datetime import datetime, timezone
from src.tools.core_tools import TOOL_REGISTRY, get_regular_tools


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
    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )
    cl.user_session.set("regular_tools", get_regular_tools())
    cl.user_session.set("mcp_tools", {})

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
        else:
            try:
                output = json.loads(message.get("output") or "{}")
                if (
                    isinstance(output, dict)
                    and output.get("status") == "rendered"
                    and output.get("url")
                ):
                    pdf_element = cl.Pdf(
                        name=output["name"], url=output["url"], display="side"
                    )
                    await cl.Message(
                        content=f"Rendering PDF: **{output['name']}**",
                        elements=[pdf_element],
                    ).send()
            except (json.JSONDecodeError, TypeError):
                pass


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


@cl.on_chat_start
def on_start():

    user = cl.user_session.get("user")
    setup_session_client(user)

    cl.user_session.set(
        "message_history",
        [{"content": f"{SYSTEM_PROMPT}", "role": "system"}],
    )
    cl.user_session.set("regular_tools", get_regular_tools())
    cl.user_session.set("mcp_tools", {})


@cl.on_logout
def logout(request: Request, response: Response):
    response.delete_cookie("my_cookie")


def flatten(xss):
    return [x for xs in xss for x in xs]


@cl.on_message
async def on_message(cl_msg: cl.Message):
    user = cl.user_session.get("user")
    user_id = user.identifier if user else "anonymous"
    thread_id = cl.context.session.thread_id

    regular_tools = cl.user_session.get("regular_tools", [])
    mcp_tools = cl.user_session.get("mcp_tools", {})
    flat_tools = flatten([tools for _, tools in mcp_tools.items()]) + regular_tools

    openai_tools = []
    if flat_tools:
        openai_tools = [
            {
                "type": "function",
                "function": {
                    "name": t["name"],
                    "description": t["description"],
                    "parameters": t["input_schema"],
                },
            }
            for t in flat_tools
        ]

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
    await msg.send()

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

    tool_calls = []

    async for part in stream:
        delta = part.choices[0].delta

        if delta.tool_calls:
            for tc_chunk in delta.tool_calls:
                if len(tool_calls) <= tc_chunk.index:
                    tool_calls.append(
                        {
                            "id": tc_chunk.id,
                            "type": "function",
                            "function": {
                                "name": tc_chunk.function.name,
                                "arguments": "",
                            },
                        }
                    )
                if tc_chunk.function.arguments:
                    tool_calls[tc_chunk.index]["function"]["arguments"] += (
                        tc_chunk.function.arguments
                    )

        elif delta.content:
            await msg.stream_token(delta.content)

    if tool_calls:
        message_history.append(
            {"role": "assistant", "content": None, "tool_calls": tool_calls}
        )

        for tool_call in tool_calls:
            function_name = tool_call["function"]["name"]
            try:
                arguments = json.loads(tool_call["function"]["arguments"])
            except json.JSONDecodeError:
                arguments = {}

            class ToolUseRequest:
                def __init__(self, name, input_args):
                    self.name = name
                    self.input = input_args

            tool_use_obj = ToolUseRequest(name=function_name, input_args=arguments)
            tool_output = await call_tool(tool_use_obj)

            message_history.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call["id"],
                    "name": function_name,
                    "content": str(tool_output),
                }
            )

        second_stream = await client.chat.completions.create(
            messages=message_history, stream=True, **kwargs
        )

        async for part in second_stream:
            if token := part.choices[0].delta.content or "":
                await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()


@cl.on_mcp_connect
async def on_mcp_connect(connection, session: ClientSession):
    """Called when an MCP connection is established"""
    result = await session.list_tools()
    tools = [
        {
            "name": t.name,
            "description": t.description,
            "input_schema": t.inputSchema,
        }
        for t in result.tools
    ]

    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_tools[connection.name] = tools
    cl.user_session.set("mcp_tools", mcp_tools)


@cl.on_mcp_disconnect
async def on_mcp_disconnect(name: str, session: ClientSession):
    """Called when an MCP connection is terminated"""
    pass


@cl.step(type="tool")
async def call_tool(tool_use):
    tool_name = tool_use.name
    tool_input = tool_use.input

    current_step = cl.context.current_step
    current_step.name = tool_name
    current_step.input = json.dumps(tool_input)

    if tool_name in TOOL_REGISTRY:
        try:
            tool_function = TOOL_REGISTRY[tool_name]["function"]
            result = await tool_function(**tool_input)
            current_step.output = result
            return current_step.output
        except Exception as e:
            current_step.output = json.dumps(
                {"error": f"Error executing {tool_name}: {str(e)}"}
            )
            return current_step.output

    mcp_tools = cl.user_session.get("mcp_tools", {})
    mcp_name = None

    for connection_name, tools in mcp_tools.items():
        if any(tool.get("name") == tool_name for tool in tools):
            mcp_name = connection_name
            break

    if not mcp_name:
        current_step.output = json.dumps(
            {"error": f"Tool {tool_name} not found in any MCP connection"}
        )
        return current_step.output

    mcp_session, _ = cl.context.session.mcp_sessions.get(mcp_name)

    if not mcp_session:
        current_step.output = json.dumps(
            {"error": f"MCP {mcp_name} not found in any MCP connection"}
        )
        return current_step.output

    try:
        current_step.output = await mcp_session.call_tool(tool_name, tool_input)
    except Exception as e:
        current_step.output = json.dumps({"error": str(e)})

    return current_step.output
