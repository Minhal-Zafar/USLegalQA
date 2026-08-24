"""Tests for the baseline systems.

The contamination diagnostic depends on B1 genuinely withholding the opinion
text. If a prompt intended as closed-book leaked the passage, the B1/B2 gap
would be meaningless and the contamination question would go unanswered.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.baselines import (
    build_prompt, extractive_answer, passage_for, SYSTEMS,
)

OPINION_TEXT = (
    "The Court granted certiorari to resolve a conflict among the Circuits. "
    "Petitioner argued the statute does not reach this conduct. "
    "We hold that Section 1983 provides a remedy against state officials "
    "acting under colour of law. The judgment is reversed and remanded."
)
OPINION = {"cluster_id": 1, "case_name": "Alpha v. Beta",
           "date_filed": "2015-06-01", "text": OPINION_TEXT}
PAIR = {"cluster_id": 1, "question": "What remedy does Section 1983 provide?",
        "answer": "A remedy against state officials acting under colour of law.",
        "span_start": OPINION_TEXT.index("We hold"),
        "span_end": OPINION_TEXT.index("We hold") + 90}


# --- the closed/open-book distinction --------------------------------------


@pytest.mark.parametrize("system", ["b1", "b3"])
def test_closed_book_prompts_withhold_the_opinion(system):
    """B1 and B3 must not contain the source text in any form."""
    prompt = build_prompt(system, PAIR, OPINION)
    assert "Section 1983 provides a remedy" not in prompt
    assert "granted certiorari to resolve" not in prompt
    assert PAIR["question"] in prompt


def test_open_book_prompt_supplies_the_passage():
    prompt = build_prompt("b2", PAIR, OPINION)
    assert "Section 1983 provides a remedy" in prompt
    assert PAIR["question"] in prompt


def test_closed_and_open_book_differ_only_in_the_passage():
    """The gap between them must be attributable to the passage, not to
    unrelated differences in instruction."""
    b1, b2 = build_prompt("b1", PAIR, OPINION), build_prompt("b2", PAIR, OPINION)
    assert len(b2) > len(b1)
    for prompt in (b1, b2):
        assert PAIR["question"] in prompt
        assert "20-100 words" in prompt


def test_few_shot_adds_examples_but_stays_closed_book():
    b1, b3 = build_prompt("b1", PAIR, OPINION), build_prompt("b3", PAIR, OPINION)
    assert len(b3) > len(b1)
    assert b3.count("QUESTION:") >= 4          # three examples plus the item
    assert "Section 1983 provides a remedy" not in b3


# --- passage selection -----------------------------------------------------


def test_passage_contains_the_supporting_span():
    p = passage_for(PAIR, OPINION)
    assert "Section 1983 provides a remedy" in p


def test_passage_falls_back_when_offsets_are_absent():
    p = passage_for({"cluster_id": 1}, OPINION)
    assert p.startswith("The Court granted certiorari")


def test_passage_is_bounded_for_long_opinions():
    long_opinion = {"text": "word " * 50000}
    pair = {"span_start": 100000, "span_end": 100050}
    assert len(passage_for(pair, long_opinion, window=1800)) <= 2000


# --- B0 extractive ---------------------------------------------------------


def test_extractive_returns_leading_sentences():
    out = extractive_answer(OPINION_TEXT, target_words=15)
    assert out.startswith("The Court granted certiorari")
    assert "reversed and remanded" not in out


def test_extractive_respects_the_length_target():
    short = extractive_answer(OPINION_TEXT, target_words=10)
    long_ = extractive_answer(OPINION_TEXT, target_words=40)
    assert len(short.split()) < len(long_.split())


def test_extractive_handles_text_without_sentence_breaks():
    assert extractive_answer("no punctuation here at all", 40).strip()


def test_extractive_handles_empty_input():
    assert extractive_answer("", 40) == ""


# --- coverage --------------------------------------------------------------


def test_every_named_system_builds_a_prompt():
    for system in SYSTEMS:
        if system == "b0":
            continue                                  # no model, no prompt
        assert build_prompt(system, PAIR, OPINION).strip()
