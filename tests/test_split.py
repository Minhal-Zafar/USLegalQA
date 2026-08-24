"""Tests for dataset partitioning.

The guarantee: no opinion appears in more than one split. With ~16 pairs per
opinion, a pair-level split places essentially every test opinion in training,
so any performance measured that way reflects memorisation of documents
already seen rather than generalisation.
"""

import json
import sys
from collections import Counter
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.split import stratified_opinion_split, measure_leakage, require_categories


def make_pairs(n_opinions=200, pairs_each=16, n_cats=6):
    cats = [f"cat{i}" for i in range(n_cats)]
    return [
        {"cluster_id": 1000 + i, "category": cats[i % n_cats],
         "question": f"q{i}_{j}", "question_type": "holding" if j % 4 == 0
         else "legal_principle"}
        for i in range(n_opinions) for j in range(pairs_each)
    ]


def test_splits_are_disjoint_by_opinion():
    tr, va, te = stratified_opinion_split(make_pairs(), (0.8, 0.1, 0.1), 42)
    assert not (tr & va) and not (tr & te) and not (va & te)


def test_every_opinion_is_assigned():
    pairs = make_pairs()
    tr, va, te = stratified_opinion_split(pairs, (0.8, 0.1, 0.1), 42)
    assert tr | va | te == {p["cluster_id"] for p in pairs}


def test_pair_level_splitting_leaks_almost_everything():
    """The defect this module exists to prevent."""
    m = measure_leakage(make_pairs(), (0.8, 0.1, 0.1), 42, n_trials=5)
    assert m["pair_level_contamination"] > 0.95
    assert m["opinion_level_contamination"] == 0.0


def test_leakage_scales_with_pairs_per_opinion():
    """One pair per opinion cannot leak; many pairs leak almost always."""
    sparse = measure_leakage(make_pairs(pairs_each=1), (0.8, 0.1, 0.1), 42, 5)
    dense = measure_leakage(make_pairs(pairs_each=20), (0.8, 0.1, 0.1), 42, 5)
    assert sparse["pair_level_contamination"] < dense["pair_level_contamination"]


def test_split_is_deterministic_given_a_seed():
    a = stratified_opinion_split(make_pairs(), (0.8, 0.1, 0.1), 7)
    b = stratified_opinion_split(make_pairs(), (0.8, 0.1, 0.1), 7)
    assert a == b


def test_different_seeds_give_different_splits():
    a = stratified_opinion_split(make_pairs(), (0.8, 0.1, 0.1), 1)
    b = stratified_opinion_split(make_pairs(), (0.8, 0.1, 0.1), 2)
    assert a[2] != b[2]


def test_categories_are_represented_across_splits():
    pairs = make_pairs(n_opinions=300, n_cats=5)
    tr, va, te = stratified_opinion_split(pairs, (0.8, 0.1, 0.1), 42)
    by_op = {p["cluster_id"]: p["category"] for p in pairs}
    for split in (tr, va, te):
        assert len({by_op[c] for c in split}) == 5


def test_rare_categories_go_to_training():
    """A category with too few opinions to divide must not appear in test,
    where performance would be reported on one or two cases."""
    pairs = make_pairs(n_opinions=100, n_cats=4)
    pairs += [{"cluster_id": 9000 + i, "category": "rare",
               "question": f"r{i}", "question_type": "holding"} for i in range(3)]
    tr, va, te = stratified_opinion_split(pairs, (0.8, 0.1, 0.1), 42)
    rare = {9000, 9001, 9002}
    assert rare <= tr
    assert not (rare & te)


@pytest.mark.parametrize("ratios", [(0.8, 0.1, 0.1), (0.7, 0.15, 0.15), (0.9, 0.05, 0.05)])
def test_split_proportions_are_approximately_respected(ratios):
    pairs = make_pairs(n_opinions=400)
    tr, va, te = stratified_opinion_split(pairs, ratios, 42)
    total = len(tr) + len(va) + len(te)
    assert abs(len(tr) / total - ratios[0]) < 0.05


def test_splitting_refuses_uncoded_opinions():
    """The v1 split was drawn before the issue-area backfill and so was not
    stratified at all for most opinions."""
    pairs = make_pairs()
    pairs[0]["category"] = None
    with pytest.raises(ValueError):
        require_categories(pairs)
    require_categories(make_pairs())


def test_released_split_has_no_uncoded_pairs():
    splits = Path(__file__).resolve().parents[1] / "data" / "dataset" / "splits"
    if not (splits / "test.jsonl").exists():
        pytest.skip("split not built")
    for name in ("train", "val", "test"):
        for line in (splits / f"{name}.jsonl").read_text(encoding="utf-8").splitlines():
            if line.strip():
                assert json.loads(line).get("category"), name
