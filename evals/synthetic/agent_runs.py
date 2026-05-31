"""
Simulate what the SRE agent did for each batch of incidents.

For each IncidentBatch we generate a SimulatedAgentRun: the clusters the
agent formed, the candidate prompts it produced, the experiment results,
the PR writeup, and self-eval scores on the agent's own work.

Improvement curve: the quality of the simulated runs IMPROVES as day_index
grows — modeling the weekly self-tune wins. Specifically:
  - cluster fidelity:  0.55 → 0.92  (% of incidents grouped correctly)
  - candidate quality: 0.45 → 0.88  (mean eval score of winning candidate)
  - cluster_quality self-eval:    0.50 → 0.90
  - candidate_diversity self-eval: 0.40 → 0.85
  - post_merge_delta:             -0.05 → 0.25

These curves are LINEAR for simplicity. In a fancier model they'd be a step
function aligned to specific self-tune events. Linear keeps the synthetic
methodology transparent and easy to audit.
"""
from __future__ import annotations
import random
import datetime as dt
from dataclasses import dataclass
from typing import Sequence

from evals.schema import FailureMode
from evals.synthetic.incidents import IncidentBatch


@dataclass
class SimulatedCluster:
    name: str
    incident_ids: list[str]
    suspected_mode: FailureMode


@dataclass
class SimulatedCandidate:
    cluster_name: str
    text: str          # short description of the prompt change
    eval_score: float  # in [0, 1]


@dataclass
class SimulatedAgentRun:
    day_index: int
    timestamp: dt.datetime
    incident_batch: IncidentBatch
    clusters: list[SimulatedCluster]
    candidates: list[SimulatedCandidate]
    winning_candidate_idx: int
    pr_writeup: str
    self_evals: dict[str, float]


def _curve(day_index: int, total_days: int, start: float, end: float) -> float:
    """Linear interpolation start → end across the synthetic period."""
    if total_days <= 1:
        return end
    return start + (end - start) * (day_index / (total_days - 1))


def simulate_agent_run(
    batch: IncidentBatch,
    total_days: int,
    rng: random.Random,
) -> SimulatedAgentRun:
    d = batch.day_index

    # Clustering: each incident is assigned to its TRUE mode-cluster with
    # probability `cluster_fidelity`, else to a random other mode.
    cluster_fidelity = _curve(d, total_days, 0.55, 0.92)
    by_mode: dict[FailureMode, list[str]] = {}
    for inc in batch.incidents:
        if rng.random() < cluster_fidelity:
            by_mode.setdefault(inc.failure_mode_tag, []).append(inc.id)
        else:
            # mis-clustered — fake a noisy alternative
            all_modes = list({i.failure_mode_tag for i in batch.incidents})
            others = [m for m in all_modes if m != inc.failure_mode_tag]
            wrong_mode = rng.choice(others) if others else inc.failure_mode_tag
            by_mode.setdefault(wrong_mode, []).append(inc.id)

    clusters = [
        SimulatedCluster(
            name=f"{mode}_d{d:02d}",
            incident_ids=ids,
            suspected_mode=mode,
        )
        for mode, ids in by_mode.items()
    ]

    # Candidate generation: 3 candidates per cluster, eval score noisy around
    # the curve.
    target_quality = _curve(d, total_days, 0.45, 0.88)
    candidates: list[SimulatedCandidate] = []
    for c in clusters:
        for i in range(3):
            score = max(0.0, min(1.0, rng.gauss(target_quality, 0.08)))
            candidates.append(SimulatedCandidate(
                cluster_name=c.name,
                text=(f"Candidate {i+1} for {c.suspected_mode}: "
                      f"refine the prompt to better handle this failure mode."),
                eval_score=score,
            ))

    winning_idx = max(range(len(candidates)), key=lambda i: candidates[i].eval_score)
    winner = candidates[winning_idx]

    pr_writeup = (
        f"# Prompt fix proposed by Phoenix Prompt SRE\n\n"
        f"**Detected:** {len(batch.incidents)} failing examples on "
        f"{batch.timestamp.date().isoformat()}.\n"
        f"**Clusters:** {len(clusters)} ({', '.join(c.suspected_mode for c in clusters)}).\n"
        f"**Winning candidate:** {winner.cluster_name}, eval score "
        f"{winner.eval_score:.2f}.\n\n"
        f"_Synthetic historical incident — generated for demo continuity._"
    )

    self_evals = {
        "cluster_quality": max(0.0, min(1.0,
            _curve(d, total_days, 0.50, 0.90) + rng.gauss(0, 0.05))),
        "candidate_diversity": max(0.0, min(1.0,
            _curve(d, total_days, 0.40, 0.85) + rng.gauss(0, 0.05))),
        "post_merge_delta": max(-1.0, min(1.0,
            _curve(d, total_days, -0.05, 0.25) + rng.gauss(0, 0.04))),
    }

    return SimulatedAgentRun(
        day_index=d,
        timestamp=batch.timestamp,
        incident_batch=batch,
        clusters=clusters,
        candidates=candidates,
        winning_candidate_idx=winning_idx,
        pr_writeup=pr_writeup,
        self_evals=self_evals,
    )


def simulate_all_runs(
    batches: Sequence[IncidentBatch],
    seed: int = 20260528,
) -> list[SimulatedAgentRun]:
    total_days = len(batches)
    rng = random.Random(seed)
    return [simulate_agent_run(b, total_days, rng) for b in batches]


if __name__ == "__main__":
    from evals.synthetic.incidents import generate_history
    print("Generating 7 days x 3 incidents and simulating agent runs...\n")
    batches = generate_history(total_days=7, incidents_per_day=3)
    runs = simulate_all_runs(batches)
    print(f"\n{'Day':<5} {'ClusterQ':<10} {'CandDiv':<10} {'PostMergeΔ':<12} {'#clusters':<10} {'Winner':<8}")
    print("-" * 60)
    for r in runs:
        winner = r.candidates[r.winning_candidate_idx]
        print(f"{r.day_index:<5} "
              f"{r.self_evals['cluster_quality']:<10.2f} "
              f"{r.self_evals['candidate_diversity']:<10.2f} "
              f"{r.self_evals['post_merge_delta']:<12.2f} "
              f"{len(r.clusters):<10} "
              f"{winner.eval_score:<8.2f}")
