import base64
from typing import Dict, Optional

import chainlit as cl
from chainlit.types import ThreadDict
from openai import AsyncOpenAI

from src.services.promptservice import PromptService

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
pm = PromptService()
SYSTEM_PROMPT = pm.get_system()
settings = {"model": "Kimi-VL-A3B-Thinking", "temperature": 0.7}  # Kimi-VL-A3B-Thinking


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
    return None


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

    # Lists for images and documents (will be parsed differently)
    IMAGES = []
    DOCS = []

    # Separate images and documents
    for file in cl_msg.elements:
        if "image" in file.mime:
            IMAGES.append(file)
        else:
            DOCS.append(file)

    # If documents are present, ingest them into the vector database
    if DOCS:
        # Send user a cue that documents are being processed
        await cl.Message(content="Processing documents...").send()

        for doc in DOCS:
            ingestion.ingest_file(
                file_path=doc.path,
                file_id=doc.id, 
                file_name=doc.name, 
                file_type=doc.mime, 
                user_id=user_id
            )

        # Notify user that documents have been processed
        await cl.Message(content="Documents processed!").send()

    
    # Call RAG_utils retrieval module to get context
    context_str = retrieval.get_context(cl_msg.content, user_id)

    # Combine user query with retrieved context (if any)
    final_query = cl_msg.content
    if context_str:
        final_query = f"Document Context: {context_str}\n\nUser Query: {cl_msg.content}"

    # Construct the openAI-format message with the final_query
    message = {"role": "user", "content": [{"type": "text", "text": final_query}]}

    # Now process images (if any), which will be appended to message["content"]
    if IMAGES:
        # Notify user that images are being processed
        await cl.Message(content="Processing images...").send()

        for image in IMAGES:
            with open(image.path, "rb") as image_file:
                # Convert image to base64 string for embedding in the message
                b64_image = base64.b64encode(image_file.read()).decode("utf-8")
            
            # Append the image to message["content"]
            message["content"].append(
                {
                    "type": "image_url",
                    "image_url": {"url": f"data:image/png;base64,{b64_image}"},
                },
            )
        # Notify user that images have been processed
        await cl.Message(content="Images processed!").send()


    # Append the new user message (with context and images) to the message history
    message_history = cl.user_session.get("message_history")
    message_history.append(message)

    # Initialize an empty assistant message ready to stream tokens into
    msg = cl.Message(content="")

    # Stream the response from the LLM
    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    # As tokens stream in, append them to the assistant message and update the UI
    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.send()
