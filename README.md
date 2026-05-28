# Phoenix Prompt SRE

A self-improving agent that fixes prompt regressions in production LLM apps.

Built for the **Arize track** of the Google Cloud Rapid Agent Hackathon, June 2026.

## What it does

Phoenix Prompt SRE watches your production LLM app's Phoenix traces, detects when a prompt change causes a quality regression, designs and tests candidate fixes via Phoenix experiments, and opens a GitHub PR with the winning prompt — and gets measurably better at this job over time by learning from which PRs you accept, which you reject, and what your reviewers comment.

## Architecture (high level)

- **Target app** — a small RAG/FAQ bot, separately versioned, instrumented with OpenInference.
- **SRE agent** — Google ADK on Cloud Run, Gemini 2.5 Pro brain, uses Phoenix MCP as its primary sensory surface and the Phoenix Python SDK for experiment execution and self-eval annotations.
- **Self-improvement layer** — agent's own steps are Phoenix-instrumented, scored by 4 LLM-as-judge evals, and a weekly self-tune job uses Phoenix experiments to revise the agent's own meta-prompts.

## Status

Currently under active development for the June 11, 2026 submission deadline.

## Hackathon write-up

See `docs/` for: architecture, eval architecture, history strategy, the four self-eval rubrics, and the demo script.
