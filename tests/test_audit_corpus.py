"""Tests for the corpus audit that removes records which are not the merits opinion."""

import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.audit_corpus import audit_record

DECIDED = datetime(2016, 6, 23)


def rec(**kw):
    base = {"date_filed": "2016-06-23", "text": "JUSTICE KAGAN delivered the opinion of the Court.",
            "section_kinds": ["syllabus", "majority", "dissent"], "n_secondary": 1}
    base.update(kw)
    return base


def test_sound_record_passes():
    assert audit_record(rec(), DECIDED) == []


def test_corrected_reissue_within_weeks_passes():
    assert audit_record(rec(date_filed="2016-07-20"), DECIDED) == []


def test_same_caption_different_decision_is_flagged():
    # United States v. Texas, 2023, attached to the 2016 SCDB entry.
    assert "wrong_case" in audit_record(rec(date_filed="2023-06-23"), DECIDED)


def test_cert_denial_statement_is_flagged():
    text = "The petition for a writ of certiorari is denied. Statement of JUSTICE ALITO"
    assert "not_merits" in audit_record(rec(text=text), DECIDED)


def test_unsegmented_record_with_separate_writing_is_flagged():
    assert "unsegmented" in audit_record(rec(section_kinds=["majority"]), DECIDED)


def test_unsegmented_record_without_separate_writing_passes():
    assert audit_record(rec(section_kinds=["majority"], n_secondary=0), DECIDED) == []
