"""Tests for intra-document segmentation of combined slip opinions.

The core guarantee: text written by a dissenting Justice must never be
classified as binding. Everything else is secondary.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.segment import (
    segment_opinion, segmentation_confident, binding_text, summarise,
    SYLLABUS, MAJORITY, PER_CURIAM, CONCURRENCE, DISSENT, MIXED, FRONT_MATTER,
)


def body(word, n=80):
    return " ".join([word] * n)


SLIP = f"""(Slip Opinion) OCTOBER TERM, 2015

Syllabus

NOTE: Where it is feasible, a syllabus (headnote) will be released.

SUPREME COURT OF THE UNITED STATES

ALPHA v. BETA

{body("syllabustext")}

JUSTICE KAGAN delivered the opinion of the Court.

{body("majoritytext")}

JUSTICE THOMAS, concurring in the judgment.

{body("concurtext")}

JUSTICE SOTOMAYOR, with whom JUSTICE JACKSON joins, dissenting.

{body("dissenttext")}
"""


def kinds(sections):
    return [s.kind for s in sections]


def test_slip_opinion_splits_into_expected_sections():
    secs = segment_opinion(SLIP)
    assert kinds(secs) == [SYLLABUS, MAJORITY, CONCURRENCE, DISSENT]


def test_dissent_text_is_never_binding():
    """The defect this module exists to prevent."""
    secs = segment_opinion(SLIP)
    bound = binding_text(secs)
    assert "majoritytext" in bound
    assert "dissenttext" not in bound
    assert "concurtext" not in bound
    assert "syllabustext" not in bound


def test_authors_are_captured():
    secs = segment_opinion(SLIP)
    by_kind = {s.kind: s.author for s in secs}
    assert by_kind[MAJORITY] == "KAGAN"
    assert by_kind[CONCURRENCE] == "THOMAS"
    assert by_kind[DISSENT] == "SOTOMAYOR"


def test_offsets_round_trip_to_source():
    """Offsets must be exact -- span grounding depends on it."""
    secs = segment_opinion(SLIP)
    for s in secs:
        assert SLIP[s.start:s.end] == s.text
    assert secs[0].start == 0
    assert secs[-1].end == len(SLIP)


def test_sections_are_contiguous_and_ordered():
    secs = segment_opinion(SLIP)
    for a, b in zip(secs, secs[1:]):
        assert a.end == b.start


def test_concurrence_in_part_and_dissent_in_part_is_mixed():
    text = (f"JUSTICE ROBERTS delivered the opinion of the Court.\n{body('maj')}\n"
            f"JUSTICE BREYER, concurring in part and dissenting in part.\n{body('mix')}")
    secs = segment_opinion(text)
    assert MIXED in kinds(secs)
    assert "mix" not in binding_text(secs)


def test_per_curiam_is_binding():
    text = f"SUPREME COURT OF THE UNITED STATES\n\nPER CURIAM\n\n{body('pc')}"
    secs = segment_opinion(text)
    assert PER_CURIAM in kinds(secs)
    assert "pc" in binding_text(secs)


def test_announced_the_judgment_counts_as_majority():
    text = (f"JUSTICE ALITO announced the judgment of the Court.\n{body('plural')}\n"
            f"JUSTICE KAGAN, dissenting.\n{body('dis')}")
    secs = segment_opinion(text)
    assert kinds(secs)[0] == MAJORITY
    assert "dis" not in binding_text(secs)


def test_chief_justice_header_is_matched():
    text = (f"CHIEF JUSTICE ROBERTS delivered the opinion of the Court.\n{body('maj')}\n"
            f"JUSTICE THOMAS, dissenting.\n{body('dis')}")
    secs = segment_opinion(text)
    assert segmentation_confident(secs)
    assert "dis" not in binding_text(secs)


def test_multiple_dissents_all_excluded():
    text = (f"JUSTICE KAGAN delivered the opinion of the Court.\n{body('maj')}\n"
            f"JUSTICE ALITO, dissenting.\n{body('dis1')}\n"
            f"JUSTICE GORSUCH, with whom JUSTICE THOMAS joins, dissenting.\n{body('dis2')}")
    secs = segment_opinion(text)
    assert kinds(secs).count(DISSENT) == 2
    bound = binding_text(secs)
    assert "dis1" not in bound and "dis2" not in bound


def test_front_matter_without_syllabus_marker():
    text = f"SUPREME COURT OF THE UNITED STATES\n\nJUSTICE KAGAN delivered the opinion of the Court.\n{body('maj')}"
    secs = segment_opinion(text)
    assert secs[0].kind == FRONT_MATTER


def test_undetectable_structure_is_flagged_not_silently_accepted():
    """A scanned or malformed document must not quietly pass as a majority."""
    text = body("unstructured", 500)
    secs = segment_opinion(text)
    assert len(secs) == 1
    assert secs[0].kind == MAJORITY
    # Confidence is True here (exactly one binding section), so callers must
    # also check that a real header was found -- see the ocr guard below.
    assert summarise(secs)["binding_words"] == 500


def test_two_majority_headers_are_not_confident():
    text = (f"JUSTICE KAGAN delivered the opinion of the Court.\n{body('a')}\n"
            f"JUSTICE ALITO delivered the opinion of the Court.\n{body('b')}")
    secs = segment_opinion(text)
    assert not segmentation_confident(secs)


def test_empty_text_returns_no_sections():
    assert segment_opinion("") == []
    assert segment_opinion("   \n  ") == []


def test_summarise_reports_structure():
    s = summarise(segment_opinion(SLIP))
    assert s["n_sections"] == 4
    assert s["confident"] is True
    assert s["kinds"][DISSENT] == 1
    assert 0 < s["binding_words"] < s["total_words"]


@pytest.mark.parametrize("descriptor,expected", [
    ("concurring", CONCURRENCE),
    ("concurring in the judgment", CONCURRENCE),
    ("dissenting", DISSENT),
    ("dissenting from the denial of certiorari", DISSENT),
    ("concurring in part and dissenting in part", MIXED),
])
def test_separate_writing_descriptors(descriptor, expected):
    text = (f"JUSTICE KAGAN delivered the opinion of the Court.\n{body('maj')}\n"
            f"JUSTICE THOMAS, {descriptor}.\n{body('sep')}")
    secs = segment_opinion(text)
    assert expected in kinds(secs)
    assert "sep" not in binding_text(secs)


# --- Reporter's syllabus summary vs the opinion proper ---------------------
#
# In plurality decisions the syllabus paraphrases the disposition using the
# same opening words as the opinion ("JUSTICE X delivered the opinion of the
# Court, except as to Parts V and VI-D-iv, concluding:") followed by a
# numbered summary written by the Reporter of Decisions. Treating that summary
# as binding attributes the Reporter's prose to the Court. Observed in Hamdan
# v. Rumsfeld, McDonald v. City of Chicago, Shady Grove and 28 other cases.


HAMDAN_SHAPE = f"""(Slip Opinion) OCTOBER TERM, 2005

Syllabus

NOTE: Where it is feasible, a syllabus (headnote) will be released.

{body("syllabusintro", 100)}

JUSTICE STEVENS delivered the opinion of the Court, except as to Parts V and VI-D-iv, concluding:

1. The Government's motion to dismiss is denied. {body("reportersummary", 300)}

JUSTICE STEVENS announced the judgment of the Court and delivered the opinion of the Court with respect to Parts I through IV.

{body("realopinion", 800)}

JUSTICE SCALIA, with whom JUSTICE THOMAS and JUSTICE ALITO join, dissenting.

{body("scaliadissent", 500)}
"""


def test_reporter_summary_is_not_binding():
    bound = binding_text(segment_opinion(HAMDAN_SHAPE))
    assert "realopinion" in bound
    assert "reportersummary" not in bound
    assert "scaliadissent" not in bound


def test_plurality_with_reporter_summary_is_confident():
    """Two 'delivered the opinion' matches must not defeat confidence when one
    of them is the syllabus summary."""
    secs = segment_opinion(HAMDAN_SHAPE)
    assert segmentation_confident(secs)
    assert sum(1 for s in secs if s.kind == MAJORITY) == 1


@pytest.mark.parametrize("tail", ["concluding:", "holding:", "CONCLUDING:"])
def test_summary_tails_recognised(tail):
    text = (f"JUSTICE KAGAN delivered the opinion of the Court, except as to "
            f"Part III, {tail}\n1. {body('summary', 200)}\n"
            f"JUSTICE KAGAN announced the judgment of the Court and delivered "
            f"the opinion of the Court.\n{body('opinion', 400)}")
    bound = binding_text(segment_opinion(text))
    assert "opinion" in bound
    assert "summary" not in bound


def test_ordinary_majority_header_still_binding():
    """The fix must not reclassify normal opinions as syllabus."""
    text = (f"JUSTICE KAGAN delivered the opinion of the Court.\n\n"
            f"{body('normalopinion', 400)}")
    secs = segment_opinion(text)
    assert segmentation_confident(secs)
    assert "normalopinion" in binding_text(secs)


@pytest.mark.parametrize("tail", [
    "concluding:",
    "concluding that section 901(b) does not apply",
    "holding:",
    "holding that the statute preempts",
])
def test_reporter_summary_tail_variants(tail):
    """Both the numbered-list form ('concluding:') and the running-text form
    ('concluding that ...') introduce the Reporter's summary. Observed in
    Hamdan and Shady Grove respectively."""
    text = (f"JUSTICE SCALIA delivered the opinion of the Court with respect to "
            f"PARTS I and II-A, {tail}. {body('summary', 200)}\n"
            f"JUSTICE SCALIA announced the judgment of the Court and delivered "
            f"the opinion of the Court.\n{body('opinion', 400)}")
    secs = segment_opinion(text)
    assert segmentation_confident(secs)
    bound = binding_text(secs)
    assert "opinion" in bound
    assert "summary" not in bound


# --- Real slip-opinion forms that the earlier pattern missed ---------------
#
# In 144 opinions every separate writing was kept as binding text, because the
# joiner list contains commas and the descriptor is hyphenated across lines.

from uslegalqa.segment import first_separate_boundary

CAPTION = """ Cite as: 555 U. S. ____ (2008) 1

 THOMAS, J., dissenting

SUPREME COURT OF THE UNITED STATES
 _________________

 No. 07-562
 _________________

 ALTRIA GROUP, INC., ET AL., PETITIONERS v. STEPHANIE GOOD ET AL.

 [December 15, 2008]

"""


def slip_with(separate_opening):
    majority = f"JUSTICE STEVENS delivered the opinion of the Court.\n{body('majoritytext')}\n It is so ordered.\n"
    return majority + CAPTION + separate_opening + "\n" + body("dissenttext") + "\n"


@pytest.mark.parametrize("opening", [
    "JUSTICE THOMAS, with whom THE CHIEF JUSTICE, JUSTICE SCALIA, and\nJUSTICE ALITO join, dissenting.",
    "JUSTICE KENNEDY, with whom JUSTICE GINSBURG,\nJUSTICE BREYER, and JUSTICE SOTOMAYOR join, dissent\ning.",
    "JUSTICE BREYER, with whom JUSTICE ALITO joins, con\ncurring in the judgment.",
    "JUSTICE SCALIA, with whom JUSTICE ALITO joins, con-\ncurring.",
])
def test_multi_joiner_and_hyphenated_openings_are_not_binding(opening):
    secs = segment_opinion(slip_with(opening))
    assert "dissenttext" not in binding_text(secs)
    assert "majoritytext" in binding_text(secs)
    assert segmentation_confident(secs)


def test_page_header_alone_marks_the_boundary():
    """Even with an unreadable opening formula, the page header ends the majority."""
    text = slip_with("The opening formula of this writing was lost in extraction.")
    assert "dissenttext" not in binding_text(segment_opinion(text))


def test_boundary_excludes_the_separate_writings_caption():
    text = slip_with("JUSTICE THOMAS, with whom JUSTICE SCALIA joins, dissenting.")
    cut = first_separate_boundary(text)
    assert cut is not None
    assert "majoritytext" in text[:cut] and "It is so ordered" in text[:cut]
    assert "SUPREME COURT" not in text[:cut] and "THOMAS, J." not in text[:cut]


def test_repeated_page_headers_do_not_split_a_writing():
    page = "\n Cite as: 555 U. S. ____ (2008) 2\n\n THOMAS, J., dissenting\n\n"
    text = slip_with("JUSTICE THOMAS, dissenting.") + page + body("moredissent")
    secs = segment_opinion(text)
    assert sum(s.kind == DISSENT for s in secs) == 1


def test_opinion_with_no_separate_writing_has_no_boundary():
    text = f"JUSTICE KAGAN delivered the opinion of the Court.\n{body('majoritytext')}\n"
    assert first_separate_boundary(text) is None


def test_majority_prose_naming_a_dissent_is_not_a_boundary():
    """Arizona State Legislature: the majority discusses the dissent by name."""
    text = (f"JUSTICE GINSBURG delivered the opinion of the Court.\n{body('majoritytext')}\n"
            "JUSTICE SCALIA, dissenting on standing, berates the\n\n"
            "Court for “treading upon the powers of state legislatures.” Post, at 6.\n"
            f"{body('moremajority')}\n")
    assert first_separate_boundary(text) is None
    assert "moremajority" in binding_text(segment_opinion(text))


def test_in_text_citation_at_line_start_is_not_a_page_header():
    """Buck v. Davis: a citation parenthetical wraps to the start of a line."""
    text = (f"JUSTICE ROBERTS delivered the opinion of the Court.\n{body('majoritytext')}\n"
            "KAGAN, J., dissenting from denial of certiorari) (“Especially\n"
            f"{body('moremajority')}\n")
    assert first_separate_boundary(text) is None
