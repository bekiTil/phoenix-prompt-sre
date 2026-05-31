"""
Synthetic regression-incident generator.

Generates plausible failing question/answer pairs for the Phoenix-docs-QA
target app, with ground-truth failure mode labels and backdated timestamps.

The mix of failure modes evolves over the synthetic period: early days show
more 'novel' failure modes the agent hasn't seen recently; later days show
fewer, simulating a target app whose prompt is gradually improved by the
SRE agent's PRs being merged.
"""
from __future__ import annotations
import os
import random
import datetime as dt
from dataclasses import dataclass
from typing import Sequence
from dotenv import load_dotenv

from google import genai

from evals.schema import RegressionExample, Provenance, FailureMode

load_dotenv()

_GEMINI = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)


@dataclass
class IncidentBatch:
    day_index: int   # 0 = first synthetic day (oldest)
    timestamp: dt.datetime  # UTC, day at noon for stable backdating
    incidents: list[RegressionExample]
    prompt_version_in_use: str  # which target-app prompt version produced these


# Question pool — realistic Phoenix-docs-QA questions a real user would ask.
QUESTION_POOL = [
    "How do I install Phoenix?",
    "What's the difference between traces and spans?",
    "How do I run a Phoenix experiment programmatically?",
    "Can Phoenix track multimodal LLM calls?",
    "How do I add an LLM-as-judge evaluator?",
    "What does OpenInference instrumentation do?",
    "How do I export traces to a CSV?",
    "Can I self-host Phoenix?",
    "What's the Phoenix prompt registry?",
    "How do I tag a prompt version as production?",
    "How do I add examples to a dataset via the Python client?",
    "What's the MCP server for Phoenix?",
    "How do I monitor multi-turn agent sessions?",
    "Does Phoenix work with LangChain?",
    "How do I score a span with a custom evaluator?",
    "Can I use Gemini as the judge model?",
    "How do I filter traces by metadata?",
    "What's the difference between AsyncClient and Client?",
    "How do I delete an experiment?",
    "How do I get the latest version of a prompt?",
    "Can Phoenix detect prompt regressions automatically?",
    "How do I add span annotations programmatically?",
    "What's the data retention policy on Phoenix Cloud?",
    "How do I configure rate limits for the OTLP exporter?",
    "Does Phoenix support distributed tracing across services?",
]


# Failure-mode generation templates. Each takes a question and returns the
# plausible bad answer for that failure mode.
_FAILURE_INSTRUCTIONS: dict[FailureMode, str] = {
    "outdated_info":        "Give a plausible-sounding but factually outdated answer (e.g. cite an old version, deprecated API, or pre-rename product name).",
    "hallucination":        "Invent a specific-sounding but completely fabricated fact (e.g. fake version number, made-up function name, fictional model ID).",
    "wrong_product":        "Confuse Phoenix with another product like Arize AX, OpenTelemetry directly, LangSmith, or an unrelated tool. Be confidently wrong.",
    "refusal_loop":         "Refuse to answer, citing a fake policy (e.g. 'I cannot provide code examples', 'I'm not authorized to discuss internals').",
    "formatting_violation": "Reply in broken or absent formatting (e.g. no code fences when code is expected, no punctuation, all lowercase, random newlines).",
    "safety_overreach":     "Add 2-4 unnecessary disclaimers before the actual answer (e.g. 'Always consult a professional', 'This may not be accurate', 'Use at your own risk').",
    "truncation":           "Start answering correctly but cut off mid-sentence around 30-60 words. Do not include a closing thought.",
    "citation_missing":     "Make a confident factual claim without citing any source, including suspiciously specific numbers without provenance.",
}


def _make_bad_answer(question: str, mode: FailureMode) -> str:
    """Use Gemini to generate a plausible bad answer for a given failure mode."""
    prompt = f"""You are generating realistic-looking BAD answers from a documentation Q&A bot, for the purpose of testing an agent that fixes prompt regressions.

The bot answers questions about Arize Phoenix (an open-source LLM observability platform).

Question from user: "{question}"

Generate a single failing answer of the type: "{mode}"

Specific instruction for this failure mode: {_FAILURE_INSTRUCTIONS[mode]}

Constraints:
- Output ONLY the bad answer text, no preamble, no explanation.
- The bad answer should be 1-4 sentences (except for "truncation" which should cut off).
- It should look like something a real LLM would actually output — not obviously wrong, just subtly or specifically wrong in the way the failure mode demands.
- Do not mention that this is intentional or synthetic.

Bad answer:"""
    resp = _GEMINI.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    return resp.text.strip()


def _failure_mode_weights_for_day(day_index: int, total_days: int) -> dict[FailureMode, float]:
    """
    On day 0 (oldest), all 8 failure modes are roughly equally likely — the
    target app's prompt is regressing in many ways. By the last day, the agent
    has already fixed most modes via prior PRs, so only the harder ones remain.

    Specifically:
      - day 0: uniform over 8 modes
      - last day: weight on 3 'persistent' modes (hallucination, citation_missing,
        truncation), low weight on others
    """
    persistent = {"hallucination", "citation_missing", "truncation"}
    progress = day_index / max(total_days - 1, 1)  # 0..1
    weights: dict[FailureMode, float] = {}
    for mode in _FAILURE_INSTRUCTIONS:
        base = 1.0
        if mode in persistent:
            weights[mode] = base * (1.0 + progress)        # grows toward end
        else:
            weights[mode] = base * (1.0 - 0.8 * progress)  # shrinks toward end
    return weights


def _sample_failure_mode(weights: dict[FailureMode, float], rng: random.Random) -> FailureMode:
    modes = list(weights.keys())
    weights_list = [weights[m] for m in modes]
    return rng.choices(modes, weights=weights_list, k=1)[0]


def generate_day(
    day_index: int,
    total_days: int,
    n_incidents: int,
    base_date: dt.datetime,
    rng: random.Random,
) -> IncidentBatch:
    """Generate one synthetic day's worth of regression incidents."""
    # Backdate to (base_date - (total_days - 1 - day_index)) at noon UTC
    days_ago = total_days - 1 - day_index
    day_dt = (base_date - dt.timedelta(days=days_ago)).replace(
        hour=12, minute=0, second=0, microsecond=0
    )

    weights = _failure_mode_weights_for_day(day_index, total_days)
    # Crudely model the target app's prompt version evolution: v1 for first
    # third, v2 for second, v3 for last. Self-tune wins push these forward.
    if day_index < total_days // 3:
        prompt_version = "v1-baseline"
    elif day_index < 2 * total_days // 3:
        prompt_version = "v2-after-sre-fix-1"
    else:
        prompt_version = "v3-after-sre-fix-2"

    incidents: list[RegressionExample] = []
    for i in range(n_incidents):
        question = rng.choice(QUESTION_POOL)
        mode = _sample_failure_mode(weights, rng)
        bad_answer = _make_bad_answer(question, mode)
        ex = RegressionExample(
            id=f"synth_d{day_index:02d}_i{i:02d}",
            question=question,
            expected_answer_summary=f"A correct answer to: {question}",  # placeholder, refined in Phase 3
            failure_mode_tag=mode,
            failing_output=bad_answer,
            provenance=Provenance(
                captured_at=day_dt.isoformat(),
                captured_via="synthetic_generator",
                prompt_version_at_capture=prompt_version,
            ),
            metadata={"day_index": day_index, "synth_run": True},
        )
        incidents.append(ex)

    return IncidentBatch(
        day_index=day_index,
        timestamp=day_dt,
        incidents=incidents,
        prompt_version_in_use=prompt_version,
    )


def generate_history(
    total_days: int = 30,
    incidents_per_day: int = 3,
    seed: int = 20260528,
) -> list[IncidentBatch]:
    """Generate a full synthetic history."""
    rng = random.Random(seed)
    base_date = dt.datetime.now(dt.timezone.utc)
    history: list[IncidentBatch] = []
    for d in range(total_days):
        print(f"  Generating day {d+1}/{total_days}...")
        batch = generate_day(d, total_days, incidents_per_day, base_date, rng)
        history.append(batch)
    return history


if __name__ == "__main__":
    # Small smoke test — generate 3 days × 2 incidents = 6 incidents.
    print("Generating 3 days × 2 incidents as smoke test...")
    batches = generate_history(total_days=3, incidents_per_day=2)
    for b in batches:
        print(f"\nDay {b.day_index} ({b.timestamp.date()}) — prompt {b.prompt_version_in_use}")
        for ex in b.incidents:
            print(f"  [{ex.failure_mode_tag}] {ex.question}")
            print(f"    bad: {ex.failing_output[:120]}...")
