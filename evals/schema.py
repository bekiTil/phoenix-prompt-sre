"""
Schema for a single regression example.

A regression example is one row in the Phoenix dataset that the SRE agent reads.
Each row represents: a user question to the target FAQ bot, what a good answer
looks like, what the *failing* answer looked like, and metadata about how/when
the failure was captured.
"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Literal, Optional
import json
import datetime as dt

# Initial taxonomy of failure modes. Keep stable across the project.
# Used by:
#   - Synthetic history generator to label generated failures
#   - SRE agent's clustering step (the agent should rediscover these tags)
#   - Cluster-quality judge to verify the agent's clusters match the ground truth
FailureMode = Literal[
    "outdated_info",        # Answer reflects an older API or product version
    "hallucination",        # Answer invents facts not in Phoenix docs
    "wrong_product",        # Confuses Phoenix with another Arize product or unrelated tool
    "refusal_loop",         # Bot refuses to answer a benign question
    "formatting_violation", # Output breaks expected format (e.g. missing code fence)
    "safety_overreach",     # Bot adds unnecessary disclaimers / warnings
    "truncation",           # Answer cut off mid-sentence
    "citation_missing",     # Answer makes claim without doc citation when required
]

CaptureSource = Literal["synthetic_seed", "synthetic_generator", "real_run"]


@dataclass
class Provenance:
    captured_at: str  # ISO 8601 UTC
    captured_via: CaptureSource
    prompt_version_at_capture: str  # e.g. "v1", "v2-overly-formal"
    target_app_commit: Optional[str] = None  # git SHA of target app at capture


@dataclass
class RegressionExample:
    id: str  # stable identifier, e.g. "regex_001"
    question: str  # what the user asked the FAQ bot
    expected_answer_summary: str  # 1-2 sentences of what a good answer should contain
    failure_mode_tag: FailureMode  # ground truth failure mode
    failing_output: str  # what the bot actually said (the regression)
    provenance: Provenance
    metadata: dict = field(default_factory=dict)  # freeform extension point

    def to_phoenix_input(self) -> dict:
        """The 'input' half that goes into Phoenix dataset."""
        return {"question": self.question}

    def to_phoenix_output(self) -> dict:
        """The 'expected' half that goes into Phoenix dataset."""
        return {
            "expected_summary": self.expected_answer_summary,
            "failure_mode": self.failure_mode_tag,
            "failing_output": self.failing_output,
        }

    def to_dict(self) -> dict:
        return asdict(self)


def now_iso() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()
