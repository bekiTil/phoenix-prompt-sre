"""
Initial seed regression examples for the Phoenix-docs-QA target app.

These ten examples cover the eight failure modes in the taxonomy, with two
extra examples that combine modes. They are HAND-WRITTEN, not generated, and
represent the kind of failures we'd expect to see on the target FAQ bot after a
prompt regression.

These seeds bootstrap Phase 1 testing. Phase 3 will grow this to ~65 examples
(40 training + 20 held-out + 5 demo).
"""
from evals.schema import RegressionExample, Provenance, now_iso

_PROV = lambda mode_prompt_ver: Provenance(
    captured_at=now_iso(),
    captured_via="synthetic_seed",
    prompt_version_at_capture=mode_prompt_ver,
)

STARTER_SEEDS = [
    RegressionExample(
        id="regex_001",
        question="How do I install Phoenix?",
        expected_answer_summary="pip install arize-phoenix; optionally pip install arize-phoenix-otel for tracing helpers.",
        failure_mode_tag="outdated_info",
        failing_output="Install Phoenix with `npm install phoenix-observability`. It's a JavaScript library.",
        provenance=_PROV("v2-overly-formal"),
    ),
    RegressionExample(
        id="regex_002",
        question="What version of OpenTelemetry does Phoenix require?",
        expected_answer_summary="Phoenix is compatible with opentelemetry-api/sdk in the 1.40+ range; consult the docs for current pins.",
        failure_mode_tag="hallucination",
        failing_output="Phoenix requires OpenTelemetry 2.7.3, released in March 2026, and is incompatible with all other versions.",
        provenance=_PROV("v2-overly-formal"),
    ),
    RegressionExample(
        id="regex_003",
        question="Can I use Phoenix to monitor my agent?",
        expected_answer_summary="Yes — Phoenix is designed for LLM agent observability with OpenInference instrumentation.",
        failure_mode_tag="wrong_product",
        failing_output="You're thinking of Arize AX. Phoenix is for time-series forecasting, not agents.",
        provenance=_PROV("v2-overly-formal"),
    ),
    RegressionExample(
        id="regex_004",
        question="Show me a code snippet for tracing a Gemini call.",
        expected_answer_summary="A short Python example using GoogleGenAIInstrumentor with phoenix.otel.register.",
        failure_mode_tag="refusal_loop",
        failing_output="I cannot generate code examples. Please consult the Phoenix documentation directly for any code-related questions.",
        provenance=_PROV("v3-safety-heavy"),
    ),
    RegressionExample(
        id="regex_005",
        question="What's the difference between traces, spans, and sessions?",
        expected_answer_summary="A trace is a single end-to-end execution; a span is one operation within it; a session groups multiple traces from the same conversation.",
        failure_mode_tag="formatting_violation",
        failing_output="trace span session same thing all of them all monitoring data ok",
        provenance=_PROV("v4-minimal"),
    ),
    RegressionExample(
        id="regex_006",
        question="How do I list all prompts via the Python client?",
        expected_answer_summary="client.prompts.list() returns paginated prompt metadata.",
        failure_mode_tag="safety_overreach",
        failing_output="Before answering, please note: this code may produce output. Always review API responses for sensitive data. Be careful with API keys. Consult a professional before deploying. The code is: client.prompts.list().",
        provenance=_PROV("v3-safety-heavy"),
    ),
    RegressionExample(
        id="regex_007",
        question="Explain Phoenix's experiment primitive in detail.",
        expected_answer_summary="An experiment runs a task over each example in a dataset, optionally with evaluators that score each run.",
        failure_mode_tag="truncation",
        failing_output="A Phoenix experiment runs a task over each example in a dataset. Each experiment has a task function which takes",
        provenance=_PROV("v4-minimal"),
    ),
    RegressionExample(
        id="regex_008",
        question="Does Phoenix support self-hosting?",
        expected_answer_summary="Yes — Phoenix is open-source and self-hostable via Docker.",
        failure_mode_tag="citation_missing",
        failing_output="Phoenix definitely supports self-hosting on premise with full enterprise features.",
        provenance=_PROV("v2-overly-formal"),
    ),
    RegressionExample(
        id="regex_009",
        question="How do I create a new prompt version programmatically?",
        expected_answer_summary="Use the MCP upsert-prompt tool, or the Phoenix Python client's prompts.create/update methods.",
        failure_mode_tag="outdated_info",
        failing_output="Phoenix prompts can only be created through the web UI. There is no programmatic API.",
        provenance=_PROV("v2-overly-formal"),
    ),
    RegressionExample(
        id="regex_010",
        question="What models does Phoenix's LLM-as-judge support?",
        expected_answer_summary="Phoenix evals work with any model accessible via the configured client — Gemini, Claude, GPT, Llama via API.",
        failure_mode_tag="hallucination",
        failing_output="Phoenix evals only work with a custom proprietary judge model called PhoenixJudge-7B.",
        provenance=_PROV("v2-overly-formal"),
    ),
]


if __name__ == "__main__":
    # Quick sanity check
    print(f"{len(STARTER_SEEDS)} starter seeds defined")
    by_mode = {}
    for s in STARTER_SEEDS:
        by_mode.setdefault(s.failure_mode_tag, []).append(s.id)
    for mode, ids in sorted(by_mode.items()):
        print(f"  {mode}: {ids}")
