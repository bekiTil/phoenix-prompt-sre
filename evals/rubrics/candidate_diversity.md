# Eval rubric: candidate_diversity

Score whether the agent's three candidate prompt revisions are meaningfully different from each other and from the baseline.

## High-scoring candidate set has:
- Each candidate makes a different kind of change (formatting, preamble, few-shot, instruction).
- Each candidate preserves the original prompt's contract (input/output shape).
- No candidate is a no-op or whitespace-only diff vs baseline.
- Pairwise embedding cosine distance ≥ 0.15 between any two candidates (calibrate threshold after 20 real runs).

## Scoring
Float in [0.0, 1.0]. Compute embedding distances programmatically; combine with structural diff for final score.
