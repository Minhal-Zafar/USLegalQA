"""Tests for the collection and cleaning stages.

The dissent-attribution test is the important one: it encodes the v2 defect as
an explicit regression test so the bug cannot silently return.
"""

import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.schema import Cluster, SubOpinion, CleanedOpinion, validate_cleaned
from uslegalqa.clean import clean_text, clean
from uslegalqa.collect import extract_text


def make_sub(otype, words=600, opinion_id=1, author="Roberts"):
    return SubOpinion(
        opinion_id=opinion_id, type=otype, author=author,
        text=" ".join(["word"] * words), word_count=words,
    )


# --- primary opinion selection --------------------------------------------


def test_primary_selected_over_dissent():
    """The v2 bug: dedup by case name kept whichever opinion came first,
    so a dissent could become the text used to answer 'what did the Court
    hold'. Ordering must not determine the outcome."""
    dissent_first = Cluster(
        cluster_id=1, case_name="A v. B", date_filed="2015-01-01", court="scotus",
        precedential_status="Published", citation=None,
        sub_opinions=[make_sub("040dissent", opinion_id=9),
                      make_sub("020lead", opinion_id=10)],
    )
    assert dissent_first.primary().type == "020lead"
    assert dissent_first.primary().opinion_id == 10

    lead_first = Cluster(**{**dissent_first.__dict__,
                            "sub_opinions": list(reversed(dissent_first.sub_opinions))})
    assert lead_first.primary().type == "020lead"


def test_cluster_with_only_separate_writings_has_no_primary():
    c = Cluster(
        cluster_id=2, case_name="C v. D", date_filed="2016-01-01", court="scotus",
        precedential_status="Published", citation=None,
        sub_opinions=[make_sub("040dissent"), make_sub("030concurrence")],
    )
    assert c.primary() is None
    assert len(c.secondary()) == 2


def test_longest_primary_wins_when_several_qualify():
    c = Cluster(
        cluster_id=3, case_name="E v. F", date_filed="2017-01-01", court="scotus",
        precedential_status="Published", citation=None,
        sub_opinions=[make_sub("020lead", words=200, opinion_id=1),
                      make_sub("010combined", words=900, opinion_id=2)],
    )
    assert c.primary().opinion_id == 2


@pytest.mark.parametrize("otype,expected", [
    ("010combined", True), ("020lead", True), ("025plurality", True),
    ("030concurrence", False), ("040dissent", False), ("unknown", False),
])
def test_is_primary_classification(otype, expected):
    assert make_sub(otype).is_primary is expected


# --- text cleaning ---------------------------------------------------------


def test_section_symbol_survives_cleaning():
    """v2 used a character whitelist that stripped section signs, corrupting
    every statutory citation in the corpus."""
    text = "The Court construes 42 U.S.C. \u00a7 1983 and \u00a7\u00a7 2000e-2(a)."
    out = clean_text(text)
    assert "\u00a7" in out
    assert "1983" in out and "2000e-2(a)" in out


def test_legal_punctuation_preserved():
    text = 'Held\u2014the "reasonable person" standard applies; see id. at 42.'
    out = clean_text(text)
    for frag in ("\u2014", '"reasonable person"', ";", "id. at 42"):
        assert frag in out


def test_whitespace_and_page_markers_normalised():
    text = "First part.\n\n  123  \n\nSecond    part.\n\n\n\n\nThird."
    out = clean_text(text)
    assert "\n\n\n" not in out
    assert "    " not in out
    assert "First part." in out and "Second part." in out


def test_control_characters_removed():
    assert "\x00" not in clean_text("clean\x00text\x07here")


# --- text extraction -------------------------------------------------------


def test_extract_prefers_plain_text():
    op = {"plain_text": " ".join(["opinion"] * 60), "html": "<p>ignored</p>"}
    assert extract_text(op).startswith("opinion")


def test_extract_falls_back_and_strips_html():
    op = {"plain_text": "", "html": "<p>" + " ".join(["word"] * 60) + "</p>"}
    out = extract_text(op)
    assert "<p>" not in out and out.split()[0] == "word"


def test_extract_rejects_stub_text():
    """Short fragments are per curiam denials, not opinions."""
    assert extract_text({"plain_text": "Certiorari denied."}) == ""


# --- validation ------------------------------------------------------------


def valid_record(**overrides):
    base = dict(
        cluster_id=1, case_name="A v. B", date_filed="2015-06-01", court="scotus",
        citation="576 U.S. 644", primary_type="020lead", primary_author="Roberts",
        text=" ".join(["word"] * 600), word_count=600,
        n_secondary=1, secondary_types=["040dissent"],
    )
    base.update(overrides)
    return CleanedOpinion(**base).to_dict()


def test_valid_record_passes():
    assert validate_cleaned(valid_record()) == []


def test_dissent_as_primary_is_rejected():
    problems = validate_cleaned(valid_record(primary_type="040dissent"))
    assert any("separate writing" in p for p in problems)


def test_word_count_mismatch_detected():
    problems = validate_cleaned(valid_record(word_count=999))
    assert any("word_count" in p for p in problems)


def test_bad_date_format_detected():
    problems = validate_cleaned(valid_record(date_filed="06/01/2015"))
    assert any("ISO format" in p for p in problems)


# --- end-to-end cleaning ---------------------------------------------------


def test_clean_stage_drops_dissent_only_clusters(tmp_path):
    raw = tmp_path / "clusters.jsonl"
    out = tmp_path / "opinions.jsonl"

    clusters = [
        Cluster(cluster_id=1, case_name="Good v. Case", date_filed="2015-01-01",
                court="scotus", precedential_status="Published", citation=None,
                sub_opinions=[make_sub("020lead", 600), make_sub("040dissent", 300)]),
        Cluster(cluster_id=2, case_name="Dissent v. Only", date_filed="2016-01-01",
                court="scotus", precedential_status="Published", citation=None,
                sub_opinions=[make_sub("040dissent", 600)]),
        # Duplicate cluster id -- must be dropped even though the name differs.
        Cluster(cluster_id=1, case_name="Good v. Case (dup)", date_filed="2015-01-01",
                court="scotus", precedential_status="Published", citation=None,
                sub_opinions=[make_sub("020lead", 600)]),
        Cluster(cluster_id=3, case_name="Too v. Short", date_filed="2017-01-01",
                court="scotus", precedential_status="Published", citation=None,
                sub_opinions=[make_sub("020lead", 100)]),
    ]
    with raw.open("w") as f:
        for c in clusters:
            f.write(json.dumps(c.to_dict()) + "\n")

    cfg = {
        "clean": {"min_words": 500, "max_words": 80000, "drop_if_no_primary": True},
        "paths": {"raw": str(raw), "cleaned": str(out)},
    }
    clean(cfg)

    records = [json.loads(l) for l in out.read_text().splitlines() if l.strip()]
    assert len(records) == 1
    assert records[0]["cluster_id"] == 1
    assert records[0]["primary_type"] == "020lead"
    assert records[0]["secondary_types"] == ["040dissent"]


def test_full_text_is_not_truncated(tmp_path):
    """v2 sent only the first 4,000 characters to the generator, so QA pairs
    described the opening of each opinion and never its holding."""
    raw, out = tmp_path / "c.jsonl", tmp_path / "o.jsonl"
    long_op = Cluster(
        cluster_id=1, case_name="Long v. Opinion", date_filed="2015-01-01",
        court="scotus", precedential_status="Published", citation=None,
        sub_opinions=[make_sub("020lead", words=12000)],
    )
    raw.write_text(json.dumps(long_op.to_dict()) + "\n")

    clean({"clean": {"min_words": 500, "max_words": 80000, "drop_if_no_primary": True},
           "paths": {"raw": str(raw), "cleaned": str(out)}})

    rec = json.loads(out.read_text().strip())
    assert rec["word_count"] == 12000
    assert len(rec["text"]) > 4000
