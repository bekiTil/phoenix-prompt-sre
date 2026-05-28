import os
from dotenv import load_dotenv
from phoenix.otel import register
from openinference.instrumentation.google_adk import GoogleADKInstrumentor

from google.adk.agents import Agent
from datetime import datetime, timezone

load_dotenv()

# Register Phoenix as the OpenTelemetry destination
tracer_provider = register(
    project_name="phoenix-prompt-sre",
    endpoint=f"{os.environ['PHOENIX_COLLECTOR_ENDPOINT']}/v1/traces",
    headers={"api_key": os.environ["PHOENIX_API_KEY"]},
)

# Auto-instrument every ADK agent operation
GoogleADKInstrumentor().instrument(tracer_provider=tracer_provider)


def get_current_time() -> dict:
    """Returns the current UTC time as an ISO 8601 string."""
    return {"current_time": datetime.now(timezone.utc).isoformat()}


root_agent = Agent(
    name="time_agent",
    model="gemini-2.5-pro",
    description="A tiny agent that knows the time.",
    instruction=(
        "You are a helpful assistant. "
        "When asked about the time, always use the get_current_time tool. "
        "Otherwise answer normally."
    ),
    tools=[get_current_time],
)