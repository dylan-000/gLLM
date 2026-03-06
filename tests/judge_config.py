import os
from deepeval.models import DeepEvalBaseLLM
from groq import Groq, AsyncGroq

class GroqJudge(DeepEvalBaseLLM):
    def __init__(self):
        self.api_key = os.getenv("GROQ_API_KEY")
        if self.api_key:
             self.client = Groq(api_key=self.api_key)
             self.aclient = AsyncGroq(api_key=self.api_key)
        self.model_name = "llama-3.3-70b-versatile"

    def load_model(self):
        return self.client

    def generate(self, prompt: str) -> str:
        return self.client.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_name, temperature=0
        ).choices[0].message.content

    async def a_generate(self, prompt: str) -> str:
        res = await self.aclient.chat.completions.create(
            messages=[{"role": "user", "content": prompt}],
            model=self.model_name, temperature=0
        )
        return res.choices[0].message.content

    def get_model_name(self):
        return self.model_name

def get_judge():
    return GroqJudge()