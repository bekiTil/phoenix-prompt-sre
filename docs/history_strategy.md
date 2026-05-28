# History strategy: hybrid

## Decision
We use a HYBRID approach to populate the agent's historical trace data:
1. A synthetic-history generator script seeds ~30 days of plausible historical regression incidents into Phoenix at the start of the build.
2. From Day 1 of the build phase onward, the agent runs against REAL deliberately-introduced regressions on the target app, accumulating real history.

By demo day: ~30 days of synthetic historical context + ~7-10 days of real recent runs.

## What the demo video shows
- Real recent runs (last ~7 days) prominently, including live action during recording.
- Synthetic deeper history (30 days) visible in Phoenix dashboards as longer-term context.
- The synthetic/real boundary is explicitly documented in this file and surfaced in the writeup.

## Why hybrid
- Pure real-time (~7-10 days available) is too thin to show a believable self-improvement curve.
- Pure synthetic feels constructed under scrutiny.
- Hybrid gives the longer trajectory the loop needs while keeping the demo-visible recent runs authentic.

## Honesty rules
- The synthetic generator's methodology is documented in detail.
- The synthetic-vs-real boundary is shown in Phoenix as a clear timestamp.
- In the writeup we say: "The agent has been running for ~1 week against real regressions, with seeded historical context to demonstrate the loop's behavior over a longer timeframe."

## Files
- evals/synthetic_history_generator.py — the generator
- docs/synthetic_history.md — full methodology, calibration, statistical properties
