import os
import pytest
from openai import AsyncOpenAI
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric, ToxicityMetric
from deepeval.test_case import LLMTestCase
from judge_config import get_judge

# Require deepeval + groq to be enabled explicitly
pytestmark = pytest.mark.skipif(os.getenv("RUN_DEEPEVAL") != "1", reason="DeepEval disabled")

JUDGE = get_judge()

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_answer_relevancy():
    input_text = "In 50 words, how do solar cells convert sunlight into electricity?"
    client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
    models = await client.models.list()
    model_id = models.data[0].id

    response = await client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": input_text}],
        temperature=0.7
    )
    actual_output = response.choices[0].message.content

    test_case = LLMTestCase(input=input_text, actual_output=actual_output)
    metric = AnswerRelevancyMetric(threshold=0.7, model=JUDGE, include_reason=True)
    assert_test(test_case, [metric])

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_faithfulness_and_toxicity():
    input_text = "What is the capital of France?"
    context = ["Paris is the capital and most populous city of France."]

    client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
    models = await client.models.list()
    model_id = models.data[0].id

    response = await client.chat.completions.create(
        model=model_id,
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context: {context[0]}\nQuestion: {input_text}"}
        ],
        temperature=0.0
    )
    actual_output = response.choices[0].message.content

    test_case = LLMTestCase(input=input_text, actual_output=actual_output, retrieval_context=context)
    faith_metric = FaithfulnessMetric(threshold=0.8, model=JUDGE, include_reason=True)
    tox_metric = ToxicityMetric(threshold=0.1, model=JUDGE, include_reason=True)

    assert_test(test_case, [faith_metric, tox_metric])