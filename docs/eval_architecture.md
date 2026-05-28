# Eval architecture — Phoenix Prompt SRE

## Dataset split

| Set | Size | Visibility | Purpose |
|---|---|---|---|
| Training | 40 | Agent sees it | Normal operation: clustering, experiments, self-tuning |
| Held-out | 20 | Agent NEVER sees it | Verify self-tune wins generalize; defense against Goodhart |
| Demo    | 5  | Frozen, hand-picked | Video recording, reproducible |

## Why this split
- 40 training: enough for LLM-judge variance to average out; cheap on Gemini Flash.
- 20 held-out: standard "small but enough" eval-set size; locked at project start; never modified.
- 5 demo: reproducible video footage; keeps demo run-to-run identical.

## Locking rule
The held-out set is committed to git on day one with `git add evals/datasets/held_out.jsonl && git commit`. Any agent code or self-tune job that reads from `held_out.jsonl` outside the post-merge-delta check is a bug.

## Decision rule for accepting a self-tune win
A meta-prompt revision v_new is committed to the Phoenix prompt registry only if:
1. v_new wins on training set vs v_current (by ≥ 0.05 average eval score), AND
2. v_new does not regress on the held-out set (by more than 0.02 average eval score).

If condition 2 fails despite condition 1, the agent logs an OVERFIT event and does not commit.
