"""
Cluster-quality LLM-as-judge.

Scores how well the SRE agent grouped a set of failing-span examples into
named failure-mode clusters. The judge looks at: cluster coherence (do the
examples in a cluster share a real root cause?), name accuracy (does the
cluster name describe the contents?), boundary cleanliness (no junk-drawer
catch-all > 10% of failures), and cardinality (2-6 clusters for 20-100
failures).

Returns a float in [0.0, 1.0] plus a short rationale.
"""
from __future__ import annotations
import json
import os
from dataclasses import dataclass
from typing import Sequence
from dotenv import load_dotenv
from google import genai

load_dotenv()

_GEMINI = genai.Client(
    vertexai=True,
    project=os.environ["GOOGLE_CLOUD_PROJECT"],
    location=os.environ["GOOGLE_CLOUD_LOCATION"],
)


@dataclass
class AgentCluster:
    """One cluster the SRE agent produced."""
    name: str
    example_ids: list[str]  # IDs of regression examples in this cluster


JUDGE_RUBRIC = """\
You are scoring the quality of a clustering produced by an automated agent.

The agent was given a list of failing question-answer pairs (regression examples)
from a documentation Q&A bot. The agent grouped them into named clusters by
failure mode. Your job is to score the clustering on these axes:

1. COHERENCE: do the examples in each cluster share a real root cause?
   - Subjective hits: cluster name describes a meaningful failure mode, not a surface keyword.

2. NAME ACCURACY: does each cluster's name describe what's actually in it?
   - A reviewer who reads only the name should predict the cluster contents.

3. BOUNDARIES: are the clusters cleanly separated?
   - No "miscellaneous" cluster larger than 10% of total examples.
   - No two clusters that obviously overlap.

4. CARDINALITY: is the number of clusters reasonable?
   - 2-6 clusters for 20-100 failures. Penalize one-giant-cluster and all-singletons.

Score from 0.0 (terrible) to 1.0 (perfect). Deduct ~0.1-0.25 per violated axis,
proportional to severity.

Respond in this exact JSON format:
{"score": <float 0..1>, "rationale": "<2-3 sentence explanation>"}

The clustering to score:
{clustering_json}

The failing examples (id, question, expected_summary, failing_output, ground_truth_failure_mode):
{examples_json}
"""


def score_clustering(
    clusters: Sequence[AgentCluster],
    examples_by_id: dict,
) -> tuple[float, str]:
    """
    Score the agent's clustering against the ground-truth failure modes.

    Args:
        clusters: the SRE agent's clusters (name + example_ids).
        examples_by_id: id -> RegressionExample (or dict) for context.

    Returns:
        (score in [0, 1], rationale string)
    """
    clustering_payload = [
        {"name": c.name, "example_ids": c.example_ids}
        for c in clusters
    ]
    examples_payload = [
        {
            "id": eid,
            "question": ex.question if hasattr(ex, "question") else ex["question"],
            "expected_summary": (
                ex.expected_answer_summary
                if hasattr(ex, "expected_answer_summary")
                else ex["expected_answer_summary"]
            ),
            "failing_output": (
                ex.failing_output if hasattr(ex, "failing_output") else ex["failing_output"]
            ),
            "ground_truth_failure_mode": (
                ex.failure_mode_tag
                if hasattr(ex, "failure_mode_tag")
                else ex["failure_mode_tag"]
            ),
        }
        for eid, ex in examples_by_id.items()
    ]

    prompt = (
        JUDGE_RUBRIC
        .replace("{clustering_json}", json.dumps(clustering_payload, indent=2))
        .replace("{examples_json}", json.dumps(examples_payload, indent=2))
    )

    resp = _GEMINI.models.generate_content(
        model="gemini-2.5-flash",
        contents=prompt,
    )
    text = resp.text.strip()

    # Extract JSON from response — sometimes wrapped in code fences
    if "```" in text:
        text = text.split("```")[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()

    try:
        parsed = json.loads(text)
        return float(parsed["score"]), str(parsed["rationale"])
    except (json.JSONDecodeError, KeyError, ValueError) as e:
        return 0.0, f"JUDGE PARSE ERROR: {e!r} on text: {text[:200]!r}"
