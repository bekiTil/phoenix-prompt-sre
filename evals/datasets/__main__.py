"""
CLI: upload starter seeds to Phoenix.

Usage:
    python -m evals.datasets
"""
from evals.regression_examples.starter_seeds import STARTER_SEEDS
from evals.datasets.sync import sync_examples_to_dataset

if __name__ == "__main__":
    sync_examples_to_dataset(
        examples=STARTER_SEEDS,
        dataset_name="phoenix-prompt-sre-starter-seeds",
        description=(
            "10 hand-crafted starter regression examples for Phoenix-docs-QA. "
            "Phase 1 bootstrap dataset. Will be superseded by training/held_out/demo "
            "in Phase 3."
        ),
    )
