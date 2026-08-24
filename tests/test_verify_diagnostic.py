"""Tests for the four cumulative verification methods behind Table 4.2."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.verify_diagnostic import cumulative

SOURCE = ("The statute applies to “any person” who acts. See 21 U. S. C. § 841. "
          "Its language appears permissive rather *218 than exclusive, and "
          "the title of a statute cannot limit the plain meaning of the text.")


def test_verbatim_quote_passes_every_method():
    assert all(cumulative("The statute applies to", SOURCE).values())


def test_curly_quotes_and_abbreviation_spacing_need_normalisation():
    h = cumulative('applies to "any person" who acts. See 21 U.S.C.', SOURCE)
    assert not h["exact"] and h["normalised"] and h["artefact"]


def test_bracketed_alteration_needs_word_matching():
    h = cumulative("[T]he title of a statute cannot limit", SOURCE)
    assert not h["normalised"] and h["word"]


def test_star_pagination_needs_artefact_removal():
    h = cumulative("appears permissive rather than exclusive", SOURCE)
    assert not h["word"] and h["artefact"]


def test_paraphrase_fails_every_method():
    assert not any(cumulative("the statute covers every person", SOURCE).values())


def test_methods_are_cumulative():
    h = cumulative("[T]he title of a statute cannot limit", SOURCE)
    order = ["exact", "normalised", "word", "artefact"]
    first = next(i for i, m in enumerate(order) if h[m])
    assert all(h[m] for m in order[first:])
