"""
Insert simulated agent runs into Phoenix as backdated OpenTelemetry traces.

Each SimulatedAgentRun becomes one Phoenix trace with backdated timestamps.
Structure per trace:
  Root  (AGENT): sre_agent_run
    Child (CHAIN): fetch_failing_spans
    Child (CHAIN): cluster_failures
    Child (CHAIN): generate_candidates
    Child (CHAIN): run_experiment_and_pick_winner
    Child (CHAIN): open_pr

All clusters/candidates/scores/PR writeup are attached as span attributes
so they appear in the Phoenix UI when you click into a span.
"""
from __future__ import annotations
import os
import json
import datetime as dt
from typing import Sequence
from dotenv import load_dotenv

from opentelemetry.trace import set_tracer_provider
from phoenix.otel import register

from evals.synthetic.agent_runs import SimulatedAgentRun

load_dotenv()


def _make_tracer():
    """Configure a Phoenix-aware tracer for the synthetic-history project."""
    tracer_provider = register(
        project_name="phoenix-prompt-sre",
        endpoint=f"{os.environ['PHOENIX_COLLECTOR_ENDPOINT']}/v1/traces",
        headers={"api_key": os.environ["PHOENIX_API_KEY"]},
        set_global_tracer_provider=False,  # don't pollute other modules' tracers
    )
    return tracer_provider, tracer_provider.get_tracer("synthetic-history")


def _to_nanos(dt_obj: dt.datetime) -> int:
    return int(dt_obj.timestamp() * 1_000_000_000)


def insert_run_as_trace(run: SimulatedAgentRun, tracer) -> str:
    """Create one Phoenix trace per simulated run; return trace_id hex."""
    start_ns = _to_nanos(run.timestamp)
    # Step durations modelled in seconds. Fictional but realistic.
    step_specs = [
        ("fetch_failing_spans",              1),
        ("cluster_failures",                 8),
        ("generate_candidates",              4),
        ("run_experiment_and_pick_winner",  30),
        ("open_pr",                          2),
    ]
    total_duration_ns = sum(s for _, s in step_specs) * 1_000_000_000
    winner = run.candidates[run.winning_candidate_idx]

    with tracer.start_as_current_span(
        "sre_agent_run",
        start_time=start_ns,
        end_on_exit=False,
        attributes={
            "openinference.span.kind": "AGENT",
            "synthetic.day_index": run.day_index,
            "synthetic.timestamp_iso": run.timestamp.isoformat(),
            "synthetic.is_synthetic": True,
            "input.value": (
                f"Phoenix alert: regression detected on "
                f"{run.timestamp.date().isoformat()} — "
                f"{len(run.incident_batch.incidents)} failing examples"
            ),
            "output.value": run.pr_writeup,
            "self_eval.cluster_quality":     run.self_evals["cluster_quality"],
            "self_eval.candidate_diversity": run.self_evals["candidate_diversity"],
            "self_eval.post_merge_delta":    run.self_evals["post_merge_delta"],
        },
    ) as root_span:
        cursor_ns = start_ns
        for step_name, duration_sec in step_specs:
            step_start = cursor_ns
            step_end = step_start + duration_sec * 1_000_000_000
            attrs = {
                "openinference.span.kind": "CHAIN",
                "synthetic.step": step_name,
            }
            if step_name == "cluster_failures":
                attrs["output.value"] = json.dumps([
                    {"name": c.name, "mode": c.suspected_mode,
                     "n_examples": len(c.incident_ids)}
                    for c in run.clusters
                ], indent=2)
            elif step_name == "generate_candidates":
                attrs["output.value"] = json.dumps([
                    {"cluster": c.cluster_name, "preview": c.text[:120]}
                    for c in run.candidates
                ], indent=2)
            elif step_name == "run_experiment_and_pick_winner":
                attrs["output.value"] = json.dumps({
                    "winning_idx": run.winning_candidate_idx,
                    "winning_score": winner.eval_score,
                    "all_scores": [c.eval_score for c in run.candidates],
                }, indent=2)
            elif step_name == "open_pr":
                attrs["output.value"] = run.pr_writeup

            child = tracer.start_span(step_name, start_time=step_start, attributes=attrs)
            child.end(end_time=step_end)
            cursor_ns = step_end

        root_span.end(end_time=start_ns + total_duration_ns)
        trace_id = root_span.get_span_context().trace_id
        return format(trace_id, "032x")


def insert_all_runs(runs: Sequence[SimulatedAgentRun]) -> list[tuple[SimulatedAgentRun, str]]:
    provider, tracer = _make_tracer()
    out = []
    for r in runs:
        tid = insert_run_as_trace(r, tracer)
        out.append((r, tid))
        print(f"  Day {r.day_index} ({r.timestamp.date()}): trace {tid[:16]}...")
    # Force flush so spans are actually sent before process exits
    provider.shutdown()
    return out


if __name__ == "__main__":
    from evals.synthetic.incidents import generate_history
    from evals.synthetic.agent_runs import simulate_all_runs
    print("Smoke: 3 days × 2 incidents, simulate runs, insert as backdated Phoenix traces\n")
    batches = generate_history(total_days=3, incidents_per_day=2)
    runs = simulate_all_runs(batches)
    results = insert_all_runs(runs)
    print(f"\nInserted {len(results)} traces.")
    print("Open Phoenix Cloud → phoenix-prompt-sre project → Traces tab → look for entries with old dates and synthetic.is_synthetic=true.")
