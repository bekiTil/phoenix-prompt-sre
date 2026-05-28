# Eval rubric: post_merge_eval_delta

After the agent's PR merges, measure whether the new prompt actually improved quality.

## Procedure
1. Wait a defined window: 24h of traffic OR 100 production traces, whichever first.
2. Compute average LLM-judge score on post-merge production traces.
3. Compute the same average on the equal-size window immediately before merge.
4. Run the new prompt against the held-out set; compare to pre-merge held-out baseline.

## High-scoring outcome:
- Post-merge production score ≥ pre-merge baseline.
- Held-out set score ≥ pre-merge held-out baseline.
- No regression on any previously-passing held-out example (no whack-a-mole).

## Scoring
Signed delta on held-out, clamped to [-1.0, 1.0]. Positive = real improvement.
