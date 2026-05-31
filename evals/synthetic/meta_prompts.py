"""
Push the four agent meta-prompts into the Phoenix prompt registry, each in
three versions (v1 -> v2 -> v3), simulating wins from weekly self-tune.
"""
from __future__ import annotations
import os
from dataclasses import dataclass
from dotenv import load_dotenv

from phoenix.client import Client
from phoenix.client.types import PromptVersion

load_dotenv()


@dataclass
class MetaPromptSpec:
    name: str
    description: str
    versions: list[str]


META_PROMPTS = [
    MetaPromptSpec(
        name="meta_cluster",
        description="How the SRE agent groups failing target-app spans into named failure-mode clusters.",
        versions=[
            "Group the following failing examples into clusters by failure mode. Output JSON with cluster names and member IDs.",
            "Group failures by mode using this taxonomy: outdated_info, hallucination, wrong_product, refusal_loop, formatting_violation, safety_overreach, truncation, citation_missing. If a failure doesn't fit, name a new cluster. Output JSON: [{\"name\": str, \"member_ids\": [str]}].",
            "Group failures by mode using this taxonomy: outdated_info, hallucination, wrong_product, refusal_loop, formatting_violation, safety_overreach, truncation, citation_missing. Cluster names must be SPECIFIC (e.g. 'outdated_install_instructions' beats 'outdated_info'). Aim for 2-6 clusters; avoid singletons unless genuinely unique. Output JSON: [{\"name\": str, \"member_ids\": [str], \"taxonomy_tag\": str}].",
        ],
    ),
    MetaPromptSpec(
        name="meta_candidate",
        description="How the SRE agent generates candidate prompt revisions per cluster.",
        versions=[
            "Given a cluster of failing examples and the current target-app prompt, propose a revision that addresses the failure. Output the revised prompt text.",
            "Given a cluster of failures and the current prompt, propose THREE candidate revisions taking different structural approaches (tighten instruction, add few-shot, add guardrail). Output JSON: [{\"approach\": str, \"prompt_text\": str}].",
            "Given a cluster of failures and the current prompt, propose THREE candidate revisions. Each must (a) take a different structural approach, (b) preserve the prompt's input/output contract, (c) be meaningfully different (target cosine distance >= 0.15 in embedding space). Output JSON: [{\"approach\": str, \"prompt_text\": str, \"preserves_contract\": bool}].",
        ],
    ),
    MetaPromptSpec(
        name="meta_judge_rubric",
        description="The LLM-as-judge rubric used to score candidates during experiments.",
        versions=[
            "Given question, expected answer, and model output, score correctness 0..1. Reply with just the number.",
            "Given question, expected, and output, score 0..1 considering factual accuracy, completeness, and formatting. JSON: {\"score\": float, \"reasoning\": str}.",
            "Score on three dimensions 0..1: factual_accuracy, completeness, formatting. Overall = mean. JSON: {\"factual_accuracy\": float, \"completeness\": float, \"formatting\": float, \"overall\": float, \"reasoning\": str}.",
        ],
    ),
    MetaPromptSpec(
        name="meta_pr_writeup",
        description="How the agent writes the PR description proposing a prompt fix.",
        versions=[
            "Write a brief PR description for a prompt fix. Include what was wrong and what was changed.",
            "Write a PR description with sections: ## Problem, ## Root cause, ## Fix, ## Evidence (eval scores before/after).",
            "Write a PR description with: ## Problem, ## Root cause, ## Fix, ## Evidence, ## Reproduce (commands to rerun locally). Include placeholder links to Phoenix experiment and traces. Under 400 words.",
        ],
    ),
]


def _build_version(text: str, description: str) -> PromptVersion:
    """prompt is positional-only; model_name is required."""
    messages = [{"role": "system", "content": text}]
    return PromptVersion(
        messages,
        model_name="gemini-2.5-flash",
        model_provider="GOOGLE",
        description=description,
    )


def push_meta_prompts() -> None:
    client = Client(
        base_url=os.environ["PHOENIX_COLLECTOR_ENDPOINT"],
        api_key=os.environ["PHOENIX_API_KEY"],
    )
    print(f"Pushing {len(META_PROMPTS)} meta-prompts x 3 versions each...\n")
    for spec in META_PROMPTS:
        print(f"  {spec.name}:")
        for v_idx, text in enumerate(spec.versions, start=1):
            version = _build_version(text, description=f"{spec.description} (v{v_idx})")
            result = client.prompts.create(name=spec.name, version=version)
            short = getattr(result, "id", None) or "ok"
            print(f"    v{v_idx} -> {short}")
    print("\nDone. Phoenix Cloud -> Prompts -> see 4 meta-prompts with 3 versions each.")


if __name__ == "__main__":
    push_meta_prompts()
