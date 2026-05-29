"""
Sanity test for the cluster-quality judge.

Builds two clusterings of the starter seeds — one good (groups by ground-truth
failure mode), one bad (random)  — and asserts that the judge ranks the good one
higher. This is a regression test on the judge itself.
"""
import random
from evals.judges.cluster_quality import score_clustering, AgentCluster
from evals.regression_examples.starter_seeds import STARTER_SEEDS


def _good_clustering():
    """Group seeds by their ground-truth failure mode tag."""
    by_mode = {}
    for s in STARTER_SEEDS:
        by_mode.setdefault(s.failure_mode_tag, []).append(s.id)
    return [
        AgentCluster(name=f"{mode}_cluster", example_ids=ids)
        for mode, ids in by_mode.items()
    ]


def _bad_clustering():
    """Random shuffling into 3 nonsense clusters."""
    random.seed(42)
    ids = [s.id for s in STARTER_SEEDS]
    random.shuffle(ids)
    return [
        AgentCluster(name="alpha", example_ids=ids[:4]),
        AgentCluster(name="beta",  example_ids=ids[4:7]),
        AgentCluster(name="gamma", example_ids=ids[7:]),
    ]


def test_good_beats_bad():
    examples_by_id = {s.id: s for s in STARTER_SEEDS}

    good_score, good_rationale = score_clustering(_good_clustering(), examples_by_id)
    print(f"GOOD clustering: score={good_score:.2f}  reason={good_rationale}")

    bad_score, bad_rationale = score_clustering(_bad_clustering(), examples_by_id)
    print(f"BAD  clustering: score={bad_score:.2f}  reason={bad_rationale}")

    assert good_score > bad_score, (
        f"Judge should rank good clustering higher. good={good_score}, bad={bad_score}"
    )
    assert good_score > 0.6, f"Good clustering should score > 0.6, got {good_score}"
    assert bad_score < 0.6, f"Bad clustering should score < 0.6, got {bad_score}"


if __name__ == "__main__":
    test_good_beats_bad()
    print("\n✓ Judge correctly ranks good clustering above bad")
