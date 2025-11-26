from openai import AsyncOpenAI
import base64
import chainlit as cl
from PromptManager import PromptManager

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
pm = PromptManager()

SYSTEM_PROMPT = pm.getSystem()
settings = {"model": "gemma-3-12b-it", "temperature": 0.7}

@cl.on_chat_resume
async def on_chat_resume(thread):
    pass


# TODO: Implment real authentication callback
@cl.password_auth_callback
def auth_callback(username: str, password: str):
    if (username, password) == ("admin", "admin"):
        return cl.User(
            identifier="admin", metadata={"role": "admin", "provider": "credentials"}
        )
    else:
        return None
    
    
@cl.on_chat_start
def on_start():
    cl.user_session.set(
        "message_history",
        [{"content": f'{SYSTEM_PROMPT}', "role": "system"}],
    )

# TODO: Add the image from the chainlit "Message" object to the proper input type that the OpenAI API accepts
@cl.on_message
async def on_message(cl_msg: cl.Message):
    message = {
        "role": "user",
        "content" : [
            {"type": "text", "text": cl_msg.content}
        ]
    }
    
    IMAGES = [file for file in cl_msg.elements if "image" in file.mime]
    
    for image in IMAGES:
        with open(image.path, "rb") as image_file:
            b64_image = base64.b64encode(image_file.read()).decode("utf-8")  
        message["content"].append({"type": "image_url", "image_url": { "url" : f"data:image/png;base64,{b64_image}" } },)
        
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
    await msg.update()
