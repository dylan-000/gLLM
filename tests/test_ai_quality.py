import pytest
from openai import AsyncOpenAI
from deepeval import assert_test
from deepeval.metrics import AnswerRelevancyMetric, FaithfulnessMetric
from deepeval.test_case import LLMTestCase
from judge_config import get_judge

# Initialize the Groq Judge once
JUDGE = get_judge()

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_answer_relevancy():
    """
    1. Sends a prompt to the LOCAL vLLM container.
    2. Gets the response.
    3. Uses Groq (Judge) to grade if the answer is relevant.
    """
    # --- STEP 1: DEFINE INPUT ---
    input_text = "In 50 words, how do solar cells convert sunlight into electricity?"
    
    # --- STEP 2: GET LIVE RESPONSE FROM LOCAL LLM ---
    # Connect to your Docker container
    client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
    
    # Get model name dynamically or hardcode it
    models = await client.models.list()
    model_id = models.data[0].id

    print(f"\n[vLLM] Generating response using {model_id}...")
    
    response = await client.chat.completions.create(
        model=model_id,
        messages=[{"role": "user", "content": input_text}],
        temperature=0.7
    )
    actual_output = response.choices[0].message.content
    print(f"[vLLM] Response: {actual_output[:100]}...") # Print preview

    # --- STEP 3: EVALUATE WITH GROQ JUDGE ---
    test_case = LLMTestCase(
        input=input_text,
        actual_output=actual_output
    )
    
    # Metric: Is the answer relevant to the prompt?
    metric = AnswerRelevancyMetric(
        threshold=0.7,
        model=JUDGE,
        include_reason=True
    )
    
    # Run the grading
    assert_test(test_case, [metric])

@pytest.mark.live
@pytest.mark.asyncio
async def test_live_faithfulness():
    """
    Checks if the Local LLM hallucinates facts.
    """
    input_text = "What is the capital of France?"
    # We provide context to see if the LLM sticks to it
    context = ["Paris is the capital and most populous city of France."]
    
    client = AsyncOpenAI(base_url="http://localhost:8000/v1", api_key="EMPTY")
    models = await client.models.list()
    
    response = await client.chat.completions.create(
        model=models.data[0].id,
        messages=[
            {"role": "system", "content": "Answer based only on the provided context."},
            {"role": "user", "content": f"Context: {context[0]}\nQuestion: {input_text}"}
        ]
    )
    actual_output = response.choices[0].message.content

    test_case = LLMTestCase(
        input=input_text,
        actual_output=actual_output,
        retrieval_context=context # DeepEval checks if output matches this
    )
    
    metric = FaithfulnessMetric(
        threshold=0.8,
        model=JUDGE,
        include_reason=True
    )
    
    assert_test(test_case, [metric])