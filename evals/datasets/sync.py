"""
Sync regression examples to Phoenix datasets.

For Phase 1: a single dataset for the starter seeds. In Phase 3 when we have
40 training / 20 held-out / 5 demo, this module will create three separate
Phoenix datasets, with the held-out one explicitly locked.
"""
from __future__ import annotations
import os
from typing import Sequence
from dotenv import load_dotenv

from phoenix.client import Client
from evals.schema import RegressionExample

load_dotenv()


def get_phoenix_client() -> Client:
    return Client(
        base_url=os.environ["PHOENIX_COLLECTOR_ENDPOINT"],
        api_key=os.environ["PHOENIX_API_KEY"],
    )


def sync_examples_to_dataset(
    examples: Sequence[RegressionExample],
    dataset_name: str,
    description: str,
) -> None:
    """Create the dataset, or extend it with new examples if it exists."""
    client = get_phoenix_client()
    inputs = [e.to_phoenix_input() for e in examples]
    outputs = [e.to_phoenix_output() for e in examples]
    metadata = [{"id": e.id, "failure_mode": e.failure_mode_tag,
                 "captured_via": e.provenance.captured_via} for e in examples]

    try:
        ds = client.datasets.create_dataset(
            name=dataset_name,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata,
            dataset_description=description,
        )
        print(f"[+] Created dataset '{dataset_name}' with {len(examples)} examples")
    except Exception as e:
        print(f"[!] Create failed ({type(e).__name__}): {e}")
        print(f"    Falling back to add_examples_to_dataset...")
        client.datasets.add_examples_to_dataset(
            dataset=dataset_name,
            inputs=inputs,
            outputs=outputs,
            metadata=metadata,
        )
        print(f"[+] Appended {len(examples)} examples to '{dataset_name}'")
