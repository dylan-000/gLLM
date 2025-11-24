from openai import AsyncOpenAI
import chainlit as cl

client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="empty")
cl.instrument_openai()
settings = {"model": "gemma-3-12b-it", "temperature": 0.7}

@cl.on_message
async def on_message(msg: cl.Message):
    response = await client.chat.completions.create(
        messages=[
            {
                "content": "You are a helpful research assistant whose job is to assist with research activities",
                "role": "system",
            },
            {"content": msg.content, "role": "user"},
        ],
        **settings,
    )
    await cl.Message(content=response.choices[0].message.content).send()
