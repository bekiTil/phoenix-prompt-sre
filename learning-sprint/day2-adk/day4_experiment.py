"""
Day 4 — Run one Phoenix experiment by hand.
Compares two prompt variants on a tiny trivia dataset, scored by an LLM-as-judge.
"""
import os
from dotenv import load_dotenv

from phoenix.client import Client
from google import genai

load_dotenv()

# 1. Phoenix client
client = Client(
    base_url=os.environ["PHOENIX_COLLECTOR_ENDPOINT"],
    api_key=os.environ["PHOENIX_API_KEY"],
)

# 2. Dataset — create or reuse
DATASET_NAME = "day4-trivia-mini"
inputs = [
    {"question": "What is the capital of France?"},
    {"question": "Who wrote 'Hamlet'?"},
    {"question": "What is 2 + 2?"},
    {"question": "What is H2O?"},
    {"question": "In what year did WWII end?"},
]
outputs = [
    {"expected": "Paris"},
    {"expected": "William Shakespeare"},
    {"expected": "4"},
    {"expected": "Water"},
    {"expected": "1945"},
]

try:
    dataset = client.datasets.create_dataset(
        name=DATASET_NAME,
        inputs=inputs,
        outputs=outputs,
        dataset_description="Day 4 trivia mini for hello-world experiment",
    )
    print(f"Created dataset: {DATASET_NAME}")
except Exception as e:
    print(f"Create failed ({type(e).__name__}), falling back to get_dataset...")
    dataset = client.datasets.get_dataset(dataset=DATASET_NAME)
    print(f"Using existing dataset: {DATASET_NAME}")

# 3. Vertex Gemini
gemini = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)

def ask(prompt_template: str, question: str) -> str:
    resp = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt_template.format(question=question),
    )
    return resp.text.strip()

# 4. Two tasks under test — same questions, different prompts.
#    Phoenix passes the example's "input" dict to the task.
def task_baseline(input):
    return ask("Answer this question: {question}", input["question"])

def task_concise(input):
    return ask("Answer in one word only: {question}", input["question"])

# 5. LLM-as-judge evaluator.
#    Phoenix inspects the signature and passes input/output/expected by name.
def correctness(input, output, expected):
    judge = gemini.models.generate_content(
        model="gemini-2.5-flash",
        contents=(
            f'Question: {input["question"]}\n'
            f'Expected: {expected["expected"]}\n'
            f'Given: {output}\n\n'
            'Is the given answer essentially correct? Reply only "yes" or "no".'
        ),
    )
    return 1.0 if "yes" in judge.text.lower() else 0.0

# 6. Run both experiments
print("\n→ BASELINE experiment...")
client.experiments.run_experiment(
    dataset=dataset,
    task=task_baseline,
    evaluators=[correctness],
    experiment_name="day4-baseline",
)

print("\n→ CONCISE experiment...")
client.experiments.run_experiment(
    dataset=dataset,
    task=task_concise,
    evaluators=[correctness],
    experiment_name="day4-concise",
)

print("\nDone. Open Phoenix Cloud → Datasets → day4-trivia-mini → see both experiments.")