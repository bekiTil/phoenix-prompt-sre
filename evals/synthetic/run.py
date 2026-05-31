"""
One-command synthetic history runner.

Usage:
    python -m evals.synthetic.run --days 30 --incidents-per-day 3

Pipeline:
    1. Generate N days of synthetic regression incidents (Gemini)
    2. Simulate the SRE agent's run for each day (with improving quality curve)
    3. Insert each run as a backdated Phoenix trace
    4. Push the 4 meta-prompts in 3 versions each to the Phoenix prompt registry

Safe to re-run. Phoenix prompt registry just stacks new versions; traces are
de-duped by Phoenix's trace_id (each run generates fresh IDs).
"""
from __future__ import annotations
import argparse
import time

from evals.synthetic.incidents import generate_history
from evals.synthetic.agent_runs import simulate_all_runs
from evals.synthetic.insert import insert_all_runs
from evals.synthetic.meta_prompts import push_meta_prompts


def main():
    p = argparse.ArgumentParser(description="Generate Phoenix Prompt SRE synthetic history.")
    p.add_argument("--days", type=int, default=30,
                   help="Number of synthetic days to generate (default 30)")
    p.add_argument("--incidents-per-day", type=int, default=3,
                   help="Synthetic incidents per day (default 3)")
    p.add_argument("--skip-meta-prompts", action="store_true",
                   help="Skip pushing the 4x3 meta-prompt versions (they're idempotent-ish but skip if already done)")
    args = p.parse_args()

    t0 = time.time()
    print(f"\n=== Phoenix Prompt SRE: synthetic history runner ===")
    print(f"days={args.days}  incidents_per_day={args.incidents_per_day}")
    print(f"Estimated Gemini calls: {args.days * args.incidents_per_day} (~{args.days * args.incidents_per_day * 3} seconds)\n")

    print("[1/4] Generating regression incidents...")
    batches = generate_history(total_days=args.days, incidents_per_day=args.incidents_per_day)
    n_incidents = sum(len(b.incidents) for b in batches)
    print(f"      → {n_incidents} incidents across {len(batches)} days\n")

    print("[2/4] Simulating SRE agent runs...")
    runs = simulate_all_runs(batches)
    print(f"      → {len(runs)} agent runs simulated\n")

    print("[3/4] Inserting backdated traces into Phoenix...")
    inserted = insert_all_runs(runs)
    print(f"      → {len(inserted)} traces in Phoenix\n")

    if not args.skip_meta_prompts:
        print("[4/4] Pushing meta-prompt versions to Phoenix prompt registry...")
        push_meta_prompts()
    else:
        print("[4/4] Skipped meta-prompt push (--skip-meta-prompts)\n")

    elapsed = time.time() - t0
    print(f"\nDone in {elapsed:.1f}s.")
    print("Open Phoenix Cloud → phoenix-prompt-sre project to inspect.")


if __name__ == "__main__":
    main()
