# Eval rubric: reviewer_comment_learnings

When a human leaves a comment on the agent's PR, the agent extracts the actionable critique.

## High-scoring extraction:
- Correctly identifies critique vs agreement vs social noise ("looks good!", emoji-only).
- Classifies critique type from fixed taxonomy: style / correctness / safety / length / scope / other.
- Extracts the specific actionable change in 1–2 sentences.
- Includes the original span ID of the PR-writeup step so the critique can be traced back to which sub-step needs improvement.

## Scoring
Float in [0.0, 1.0] based on a held-out set of 20 hand-labeled reviewer comments.
