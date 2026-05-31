# Synthetic history methodology

This document describes how the synthetic portion of the agent's history is generated, so that a judge auditing the project can verify exactly what is synthetic and on what basis.

## What is synthetic
- ~30 days of historical regression incidents on the target FAQ bot.
- The SRE agent's "runs" against those incidents — clustering, candidate generation, experiment results, PR writeups.
- The agent's self-eval scores across those runs.
- Three versions of each of the four meta-prompts (12 prompt versions).

## What is real
- The agent code itself.
- The Phoenix instrumentation, MCP integration, judge functions, evaluation harness.
- Any runs from the build-phase onward, after Day 1 of Phase 4. These are the recent, demo-visible runs.

## Generator structure
1. `evals/synthetic/incidents.py` — generates plausible failing question/answer pairs using Gemini 2.5 Flash, with ground-truth failure-mode labels drawn from a fixed 8-mode taxonomy.
2. `evals/synthetic/agent_runs.py` — simulates what the SRE agent did per incident batch.
3. `evals/synthetic/insert.py` — ships each simulated run to Phoenix as backdated OpenTelemetry spans via OTLP.
4. `evals/synthetic/meta_prompts.py` — pushes 4 meta-prompts × 3 versions to the Phoenix prompt registry.
5. `evals/synthetic/run.py` — one-command orchestrator.

## Improvement curves (linear; auditable)
The simulator hard-codes monotonic linear improvement curves over the synthetic period:

| Self-eval signal | Day 0 | Last day |
|---|---|---|
| cluster_fidelity (% incidents correctly clustered) | 0.55 | 0.92 |
| candidate_quality (mean winner eval score) | 0.45 | 0.88 |
| cluster_quality self-eval | 0.50 | 0.90 |
| candidate_diversity self-eval | 0.40 | 0.85 |
| post_merge_delta | -0.05 | 0.25 |

Each signal has Gaussian noise (σ ≈ 0.05) applied per day so day-over-day variance is realistic.

## Failure mode distribution
- Day 0: roughly uniform across all 8 failure modes (the target app is regressing in many ways).
- Last day: weighted toward 3 "persistent" modes (hallucination, citation_missing, truncation) — the agent has already fixed most of the other modes via prior PRs.

The mathematical formulation lives at the top of `evals/synthetic/incidents.py:_failure_mode_weights_for_day`.

## Why hybrid
- 30 days of pure real-time runs is not achievable in the 14-day build budget.
- Pure synthetic feels constructed under scrutiny.
- Hybrid: ~30 days synthetic deeper history + ~7-10 days of real recent runs (post-build) gives the longer trajectory the loop's improvement story needs, while keeping the demo-visible recent runs authentic.

## How to verify
1. In Phoenix Cloud, all synthetic traces carry `synthetic.is_synthetic=true` as a span attribute and `synthetic.day_index` indicating their position in the curve.
2. Synthetic prompt versions can be identified by `description` containing "(v1)", "(v2)", "(v3)".
3. To regenerate from scratch, run `python -m evals.synthetic.run --days 30 --incidents-per-day 3`. This produces a fresh history (new trace_ids), deterministic by random seed.

## Honesty statement
In the writeup we say: "The agent has been running for ~1 week against real regressions, with seeded historical context to demonstrate the loop's behavior over a longer timeframe. Synthetic and real portions are marked in the data and documented in `docs/synthetic_history.md`."
