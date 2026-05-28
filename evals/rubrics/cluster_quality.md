# Eval rubric: cluster_quality

Score the agent's grouping of failing spans into named failure-mode clusters.

## High-scoring clustering has:
- Each cluster is semantically coherent — failures share a real root cause, not a surface keyword.
- Cluster names accurately describe contents — a reviewer can predict cluster contents from the name.
- Clean boundaries — no obvious cross-cluster overlap; no "miscellaneous" cluster > 10% of failures.
- Reasonable cardinality — typically 2–6 clusters for 20–100 failures.

## Scoring
Float in [0.0, 1.0]. Deduct for each violated criterion above; severity proportional to user impact.

## LLM-judge prompt template
See `evals/judges/cluster_quality_judge.txt`.
