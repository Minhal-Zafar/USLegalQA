"""Tests for the evaluation harness.

The harness exists to prevent three specific reporting failures observed in
the earlier evaluation: absolute scores without a reference point, ROUGE F1
concealing a verbosity failure, and comparisons made between point estimates.
"""

import sys
from pathlib import Path

import numpy as np
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.evaluate import (
    bootstrap_ci, paired_bootstrap, diagnostics, rouge_scores, item_key,
)


# --- bootstrap -------------------------------------------------------------


def test_bootstrap_ci_brackets_the_mean():
    v = np.random.default_rng(0).normal(0.5, 0.1, 300)
    ci = bootstrap_ci(v, seed=0)
    assert ci["ci95"][0] < ci["mean"] < ci["ci95"][1]
    assert abs(ci["mean"] - 0.5) < 0.05


def test_bootstrap_ci_widens_on_small_samples():
    rng = np.random.default_rng(0)
    wide = bootstrap_ci(rng.normal(0.5, 0.1, 20), seed=0)
    narrow = bootstrap_ci(rng.normal(0.5, 0.1, 2000), seed=0)
    width = lambda c: c["ci95"][1] - c["ci95"][0]
    assert width(wide) > width(narrow)


def test_bootstrap_handles_empty_input():
    assert bootstrap_ci(np.array([])) ["n"] == 0


# --- paired comparison -----------------------------------------------------


def test_paired_bootstrap_detects_a_real_difference():
    rng = np.random.default_rng(0)
    base = rng.normal(0.5, 0.1, 400)
    better = base + 0.08
    res = paired_bootstrap(better, base, seed=0)
    assert res["mean_difference"] > 0
    assert res["p_value"] < 0.05


def test_paired_bootstrap_finds_no_difference_when_there_is_none():
    rng = np.random.default_rng(0)
    a = rng.normal(0.5, 0.1, 400)
    b = a + rng.normal(0, 0.01, 400)
    assert paired_bootstrap(a, b, seed=0)["p_value"] > 0.05


def test_paired_test_is_more_sensitive_than_separate_intervals():
    """Systems evaluated on the same items share difficulty. Comparing
    independent intervals discards that and understates significance."""
    rng = np.random.default_rng(0)
    difficulty = rng.normal(0, 0.25, 300)     # shared item difficulty
    a = 0.5 + difficulty + rng.normal(0, 0.02, 300)
    b = a + 0.03
    separate_overlap = (bootstrap_ci(a, seed=0)["ci95"][1]
                        > bootstrap_ci(b, seed=0)["ci95"][0])
    assert separate_overlap, "intervals should overlap in this setup"
    assert paired_bootstrap(b, a, seed=0)["p_value"] < 0.05


# --- ROUGE precision and recall -------------------------------------------


def test_verbose_output_collapses_precision_not_recall():
    """The v2 failure: ROUGE-1 F1 of 0.26 alongside BERTScore of 0.87 was a
    verbosity artifact, invisible when only F1 is reported."""
    ref = ["The Court held that the statute preempts state law claims."]
    concise = ["The Court held that the statute preempts state law claims."]
    verbose = [concise[0] + " " + "padding " * 80]

    c = rouge_scores(ref, concise)
    v = rouge_scores(ref, verbose)

    assert c["rouge1_r"][0] == pytest.approx(v["rouge1_r"][0], abs=0.01)
    assert v["rouge1_p"][0] < c["rouge1_p"][0] * 0.2
    assert v["rouge1_f"][0] < c["rouge1_f"][0] * 0.5


def test_wrong_answer_lowers_both_precision_and_recall():
    """Both drop together, unlike the verbosity case where only precision does.

    ROUGE does not reach zero for an unrelated legal sentence: function words
    and domain terms ("the", "court") overlap between any two. That residual
    is exactly why the corpus floor is reported alongside every score."""
    ref = ["The Court held that the statute preempts state law claims."]
    correct = ["The Court held that the statute preempts state law claims."]
    wrong = ["The defendant filed an appeal in the circuit court last year."]

    c, w = rouge_scores(ref, correct), rouge_scores(ref, wrong)
    assert w["rouge1_p"][0] < c["rouge1_p"][0] * 0.5
    assert w["rouge1_r"][0] < c["rouge1_r"][0] * 0.5
    # Both fall together, distinguishing this from the verbosity failure.
    assert abs(w["rouge1_p"][0] - w["rouge1_r"][0]) < 0.15


# --- diagnostics -----------------------------------------------------------


def test_diagnostics_flags_runaway_generation():
    refs = ["short reference answer here"] * 10
    hyps = ["short reference answer here " + "more " * 100] * 10
    d = diagnostics(refs, hyps)
    assert d["length_ratio"] > 2
    assert any("end-of-sequence" in w for w in d["warnings"])


def test_diagnostics_flags_empty_predictions():
    d = diagnostics(["a reference"] * 5, ["", "", "x", "", ""])
    assert d["empty_predictions"] == 4


def test_diagnostics_flags_mode_collapse():
    d = diagnostics([f"reference {i}" for i in range(20)], ["same answer"] * 20)
    assert any("duplicate" in w for w in d["warnings"])


def test_diagnostics_silent_on_healthy_output():
    refs = [f"reference answer number {i} with some words" for i in range(20)]
    hyps = [f"predicted answer number {i} with other words" for i in range(20)]
    assert diagnostics(refs, hyps)["warnings"] == []


# --- alignment -------------------------------------------------------------


def test_item_key_identifies_a_test_item():
    a = {"cluster_id": 1, "question": "q", "prediction": "x"}
    b = {"cluster_id": 1, "question": "q", "prediction": "y"}
    c = {"cluster_id": 2, "question": "q", "prediction": "x"}
    assert item_key(a) == item_key(b)
    assert item_key(a) != item_key(c)
