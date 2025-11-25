from openai import AsyncOpenAI
import chainlit as cl
from PromptManager import PromptManager

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
pm = PromptManager()

SYSTEM_PROMPT = pm.getSystem()
settings = {"model": "gemma-3-12b-it", "temperature": 0.7}

@cl.on_chat_start
def on_start():
    cl.user_session.set(
        "message_history",
        [{"content": f'{SYSTEM_PROMPT}', "role": "system"}],
    )
    print(SYSTEM_PROMPT)


@cl.on_message
async def on_message(msg: cl.Message):
    message_history = cl.user_session.get("message_history")
    message_history.append({"content": msg.content, "role": "user"})

    msg = cl.Message(content="")

    stream = await client.chat.completions.create(
        messages=message_history, stream=True, **settings
    )

    async for part in stream:
        if token := part.choices[0].delta.content or "":
            await msg.stream_token(token)

    message_history.append({"role": "assistant", "content": msg.content})
    await msg.update()
