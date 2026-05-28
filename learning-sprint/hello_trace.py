import os
from dotenv import load_dotenv
from phoenix.otel import register
from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
from google import genai

load_dotenv()

# Register Phoenix as the trace destination
tracer_provider = register(
    project_name="phoenix-prompt-sre",
    endpoint=f"{os.environ['PHOENIX_COLLECTOR_ENDPOINT']}/v1/traces",
    headers={"api_key": os.environ["PHOENIX_API_KEY"]},
)

# Auto-instrument every Google GenAI call
GoogleGenAIInstrumentor().instrument(tracer_provider=tracer_provider)

# Make a Gemini call — this will produce a trace
client = genai.Client(api_key=os.environ["GOOGLE_API_KEY"])
response = client.models.generate_content(
    model="gemini-2.5-flash",
    contents="What is the capital of France? Answer in one word.",
)
print("Answer:", response.text.strip())
print("Now check Phoenix Cloud — your trace should be there.")