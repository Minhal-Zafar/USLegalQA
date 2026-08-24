"""Tests for QA generation: span grounding and validation.

Span verification is the mechanism that makes faithfulness measurable. A model
that fabricates a quotation must be caught, and a model that reproduces the
text with different line breaks must not be falsely rejected.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.chunking import chunk_opinion
from uslegalqa.generate import (
    locate_span, normalise, parse_response, validate, build_prompt,
    QUESTION_TYPES, POSITION_GUIDANCE,
)
from uslegalqa.chunking import POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE


CFG = {"generate": {
    "model": "test-model", "temperature": 0.3,
    "min_question_words": 8, "max_question_words": 45,
    "min_answer_words": 15, "max_answer_words": 90,
    "min_span_chars": 40,
}}

CHUNK_TEXT = (
    "The Court holds that 42 U.S.C. \u00a7 1983 provides a remedy against state "
    "officials acting under colour of law.\n\n"
    "We therefore reverse the judgment of the Court of Appeals and remand for "
    "further proceedings consistent with this opinion."
)

REC = {"cluster_id": 1, "case_name": "Alpha v. Beta", "date_filed": "2015-06-01",
       "citation": "576 U.S. 644", "scdb_category": "civil_rights",
       "scdb_id": "2014-055", "text": CHUNK_TEXT}


def a_chunk():
    return chunk_opinion(CHUNK_TEXT, 1)[0]


# --- span location ---------------------------------------------------------


def test_exact_span_is_located():
    span = "The Court holds that 42 U.S.C. \u00a7 1983 provides a remedy"
    found = locate_span(span, CHUNK_TEXT)
    assert found is not None
    assert CHUNK_TEXT[found[0]:found[1]] == span


def test_span_with_different_whitespace_is_located():
    """Models reproduce wording reliably but not line breaks."""
    span = "colour of law.  We therefore reverse the judgment"
    assert locate_span(span, CHUNK_TEXT) is not None


def test_fabricated_span_is_rejected():
    """The core faithfulness check: invented quotations must not pass."""
    assert locate_span("The Court holds that the statute is void for vagueness",
                       CHUNK_TEXT) is None


def test_empty_span_is_rejected():
    assert locate_span("", CHUNK_TEXT) is None
    assert locate_span("   ", CHUNK_TEXT) is None


def test_located_offsets_round_trip():
    span = "remand for further proceedings"
    start, end = locate_span(span, CHUNK_TEXT)
    assert normalise(CHUNK_TEXT[start:end]) == normalise(span)


# --- response parsing ------------------------------------------------------


@pytest.mark.parametrize("wrapper", [
    '{}',
    '```json\n{}\n```',
    '```\n{}\n```',
    'Here are the pairs:\n{}\nLet me know if you need more.',
])
def test_parse_response_handles_wrappers(wrapper):
    payload = ('{"qa_pairs": [{"question": "q", "answer": "a", '
               '"question_type": "holding", "supporting_span": "s"}]}')
    assert len(parse_response(wrapper.format(payload))) == 1


def test_parse_response_rejects_non_json():
    with pytest.raises(ValueError):
        parse_response("I cannot generate questions from this passage.")


def test_parse_empty_list_is_allowed():
    """Boilerplate passages legitimately yield nothing."""
    assert parse_response('{"qa_pairs": []}') == []


# --- validation ------------------------------------------------------------


def good_pair(**over):
    pair = {
        "question": "What remedy did the Court hold that section 1983 provides here?",
        "answer": ("The Court held that section 1983 provides a remedy against "
                   "state officials who act under colour of law, and reversed "
                   "the judgment below."),
        "question_type": "holding",
        "supporting_span": ("The Court holds that 42 U.S.C. \u00a7 1983 provides a "
                            "remedy against state officials"),
    }
    pair.update(over)
    return pair


def test_valid_pair_is_accepted():
    rec, reason = validate(good_pair(), REC, a_chunk(), CFG)
    assert reason == "ok"
    assert rec["question_type"] == "holding"
    assert rec["generator"] == "test-model"
    assert rec["category"] == "civil_rights"


def test_span_offsets_are_absolute_to_the_opinion():
    rec, _ = validate(good_pair(), REC, a_chunk(), CFG)
    assert CHUNK_TEXT[rec["span_start"]:rec["span_end"]] == rec["supporting_span"]


@pytest.mark.parametrize("over,expected", [
    ({"question": "Too short?"}, "question_length"),
    ({"answer": "Brief answer."}, "answer_length"),
    ({"answer": ("Yes, the Court so held. It reversed the judgment of the "
                 "Court of Appeals and remanded the case for further "
                 "proceedings consistent with its opinion on the statute.")},
     "yes_no_answer"),
    ({"question_type": "invented_type"}, "bad_question_type"),
    ({"supporting_span": "the Court invented this quotation entirely from nothing"},
     "span_not_found"),
    ({"supporting_span": "The Court holds"}, "span_too_short"),
    ({"question": ""}, "empty_field"),
])
def test_invalid_pairs_are_rejected_with_reason(over, expected):
    rec, reason = validate(good_pair(**over), REC, a_chunk(), CFG)
    assert rec is None
    assert reason == expected


# --- prompting -------------------------------------------------------------


def test_position_guidance_covers_all_bands():
    assert set(POSITION_GUIDANCE) == {POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE}
    for band in POSITION_GUIDANCE.values():
        assert set(band["types"]) <= set(QUESTION_TYPES)


def test_holdings_are_requested_from_every_band():
    """Holdings must be requested from all three position bands.

    A SCOTUS opinion states its holding in the opening paragraph ("We hold
    that it does not"), develops it at the end, and in long opinions resolves
    sub-issues Part by Part throughout the body.

    An earlier design excluded the middle band, on the theory that it carries
    reasoning rather than conclusions. That held on a 20-opinion sample of
    short 2005 cases but failed on the full corpus: long opinions are
    overwhelmingly middle-banded, so holdings fell to 10.4% of generated
    questions -- below even the truncated v2 pipeline's 11.8%."""
    for band in (POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE):
        assert "holding" in POSITION_GUIDANCE[band]["types"], band


def test_each_band_still_has_a_distinct_emphasis():
    """Requesting holdings everywhere must not collapse the bands into one."""
    early = POSITION_GUIDANCE[POSITION_EARLY]["types"]
    middle = POSITION_GUIDANCE[POSITION_MIDDLE]["types"]
    late = POSITION_GUIDANCE[POSITION_LATE]["types"]
    assert "procedural" in early and "procedural" not in late
    assert "outcome" in late and "outcome" not in early
    assert early != middle != late


def test_prompt_contains_chunk_and_metadata():
    prompt = build_prompt(REC, a_chunk(), 3)
    assert "Alpha v. Beta" in prompt
    assert "576 U.S. 644" in prompt
    assert CHUNK_TEXT[:50] in prompt
    assert "supporting_span" in prompt


# --- Typographic tolerance vs fabrication ----------------------------------
#
# A model asked to quote legal text reproduces the WORDS reliably but not the
# punctuation: curly quotes, dashes, and Reports-style abbreviation spacing
# ("21 U. S. C." vs "21 U.S.C.") all vary. Rejecting those inflates the
# apparent hallucination rate, which is the number this pipeline exists to
# measure honestly. Fabricated or reordered text must still be caught.

LEGAL_CHUNK = (
    'Section 1956(h) provides: "Any person who conspires to commit any offense '
    'defined in [\u00a7 1956] or section 1957 shall be subject to the same penalties."\n'
    'In Shabani, we addressed whether the nearly identical language of the drug '
    'conspiracy statute, 21 U. S. C. \u00a7 846, requires proof of an overt act.'
)


@pytest.mark.parametrize("span", [
    'In Shabani, we addressed whether the nearly identical language',
    '\u201cAny person who conspires to commit any offense defined in [\u00a7 1956]\u201d',
    '"Any person who conspires to commit any offense"',
    '21 U.S.C. \u00a7 846, requires proof of an overt act',
    'Any person who conspires ... shall be subject to the same penalties',
])
def test_typographic_variants_are_accepted(span):
    assert locate_span(span, LEGAL_CHUNK) is not None


@pytest.mark.parametrize("span", [
    'The Court concluded that Congress intended to eliminate the requirement',
    'In Shabani, we addressed whether the drug statute requires an overt act',
    'requires proof of an overt act in Shabani we addressed',
])
def test_fabricated_spans_are_still_rejected(span):
    assert locate_span(span, LEGAL_CHUNK) is None


def test_accepted_span_maps_back_to_real_source_text():
    """Whatever offsets are returned must point at genuine source text."""
    span = '21 U.S.C. \u00a7 846, requires proof of an overt act'
    start, end = locate_span(span, LEGAL_CHUNK)
    assert normalise(LEGAL_CHUNK[start:end]) == normalise(span)
    assert "846" in LEGAL_CHUNK[start:end]


# --- Legal quotation conventions -------------------------------------------
#
# Spans taken from a live run on Whitfield v. United States and Clark v.
# Martinez. All 15 rejected spans in that run were verbatim text refused by a
# string matcher -- 0% fabrication, 23.4% apparent failure. Verification is by
# word sequence for this reason: legal quotation alters punctuation
# (bracketed letters, nested quotes, ellipses, Reports abbreviation spacing)
# while preserving wording exactly.

YESKEY = (
    'Nor do we find it significant that Congress chose to label \u00a7 1956(h) a '
    '"penalty" rather than an "offense" provision. See Pennsylvania Dept. of '
    'Corrections v. Yeskey, 524 U. S. 206, 212 (1998) ("\u2018[T]he title of a '
    'statute \u2026 cannot limit the plain meaning of the text\u2019").'
)


@pytest.mark.parametrize("span,why", [
    ('("\u2018[T]he title of a statute', "nested single-in-double quotes"),
    ("the title of a statute", "bracketed letter alteration [T]he"),
    ("524 U.S. 206, 212 (1998)", "Reports abbreviation spacing"),
    ("Nor do we find it significant that Congress chose to label",
     "plain verbatim prefix"),
])
def test_legal_quotation_conventions_are_accepted(span, why):
    assert locate_span(span, YESKEY) is not None, why


@pytest.mark.parametrize("span,why", [
    ("Congress plainly intended to abolish the overt act requirement",
     "fabricated content"),
    ("The Court said titles cannot restrict statutory meaning", "paraphrase"),
    ("title of a statute the cannot limit", "words reordered"),
    ("the title of a statute may limit the plain meaning", "word substituted"),
])
def test_word_level_alterations_are_still_rejected(span, why):
    assert locate_span(span, YESKEY) is None, why


def test_matched_span_slices_back_to_source():
    """Offsets must index the ORIGINAL text, including its punctuation."""
    start, end = locate_span("the title of a statute", YESKEY)
    sliced = YESKEY[start:end]
    assert "title of a statute" in sliced
    assert sliced in YESKEY


# --- PDF extraction artifacts ----------------------------------------------
#
# COLD's opinion text comes from PDF extraction, which intermittently loses
# spaces: "conspicuousand", "dogone", "707during", "Alabama 18...Alaska".
# The model quotes these correctly spaced, so word-level matching fails even
# though the text is character-identical once separators are removed. This
# class was 91% of remaining rejections across 20 opinions.

FUSED = (
    'the use of a well-trained narcotics-detection dogone that "does not expose '
    'noncontraband items" Place, 462 U. S., at 707during a lawful traffic stop, '
    'making the failure to specify any such effect conspicuousand more likely '
    'intentional.'
)


@pytest.mark.parametrize("span,artifact", [
    ("a well-trained narcotics-detection dog one that", "dogone"),
    ("at 707 during a lawful traffic stop", "707during"),
    ("conspicuous and more likely intentional", "conspicuousand"),
])
def test_fused_words_from_pdf_extraction_are_matched(span, artifact):
    assert locate_span(span, FUSED) is not None, artifact


def test_table_formatting_is_matched():
    """Appendix tables extract without spaces around ellipses."""
    table = "STATE AGE STATUTE\nAlabama 18...Alaska 18...Arizona 18...Arkansas 18"
    assert locate_span("Alabama 18 Alaska 18 Arizona 18", table) is not None


@pytest.mark.parametrize("span,why", [
    ("Congress plainly intended to abolish the requirement entirely", "fabricated"),
    ("The Court said titles cannot restrict statutory meaning", "paraphrase"),
    ("title of a statute the cannot limit plain", "reordered"),
    ("the title of a statute may limit the plain meaning", "word substituted"),
])
def test_character_matching_still_rejects_alterations(span, why):
    """Separator-insensitivity must not become content-insensitivity."""
    assert locate_span(span, YESKEY) is None, why


# --- Footnote reference markers --------------------------------------------
#
# Extracted opinion text carries footnote digits attached to the preceding
# sentence: "when it wishes to do so.5 See Brief for United States". A model
# quoting the passage omits the marker, so the character streams diverge at
# that digit. Longer spans fail disproportionately because they are likelier
# to cross one. Measured across 20 opinions, this was 94% of remaining
# rejections -- 66 of 70 failures, all verbatim text.

FOOTNOTED = (
    "Congress has included an express overt-act requirement in at least 22 "
    "other current conspiracy statutes, clearly demonstrating that it knows "
    "how to impose such a requirement when it wishes to do so.5 See Brief for "
    'United States 18-19. The canon raises serious constitutional doubts."12 '
    "The canon is thus a means of giving effect to congressional intent."
)


@pytest.mark.parametrize("span,why", [
    ("when it wishes to do so. See Brief for United States 18-19",
     "footnote marker after a period"),
    ('raises serious constitutional doubts." The canon is thus a means',
     "footnote marker after a closing quote"),
    ("in at least 22 other current conspiracy statutes",
     "a genuine number, not a footnote marker"),
])
def test_footnote_markers_do_not_block_matching(span, why):
    assert locate_span(span, FOOTNOTED) is not None, why


@pytest.mark.parametrize("span,why", [
    ("Congress deliberately removed the overt-act requirement", "fabricated"),
    ("it knows how to impose such a requirement when it declines to do so",
     "word substituted"),
    ("in at least 33 other current conspiracy statutes", "number altered"),
])
def test_footnote_tolerance_does_not_admit_alterations(span, why):
    assert locate_span(span, FOOTNOTED) is None, why


def test_long_spans_crossing_footnotes_are_matched():
    """The failure was length-correlated: longer quotations cross more
    markers, so the class was invisible in short test fixtures."""
    span = (
        "Congress has included an express overt-act requirement in at least 22 "
        "other current conspiracy statutes, clearly demonstrating that it knows "
        "how to impose such a requirement when it wishes to do so. See Brief for "
        "United States 18-19."
    )
    found = locate_span(span, FOOTNOTED)
    assert found is not None
    assert "Congress has included" in FOOTNOTED[found[0]:found[1]]


# --- Star pagination -------------------------------------------------------
#
# U.S. Reports page-break markers appear MID-SENTENCE in the extracted text:
#
#   source:  "its language appears permissive rather *218 than exclusive"
#   quoted:  "its language appears permissive rather than exclusive"
#
# A model quoting the passage omits them. Unlike footnote markers these are
# not preceded by punctuation, so a punctuation-anchored pattern misses them.
# Measured across 20 opinions, this class was ~92% of remaining rejections.
# All examples below are real source text from that diagnostic run.

STARRED = (
    "we note that its language appears permissive rather *218 than exclusive; "
    "the petitions for habeas corpus should have been *387 granted. "
    'This is because the expectation *409 "that certain facts" and the removal '
    "options presented in the *342 other six are impracticable. The statute "
    "applies in at least 22 other current conspiracy statutes.[2]"
)


@pytest.mark.parametrize("span,why", [
    ("its language appears permissive rather than exclusive", "star mid-sentence"),
    ("habeas corpus should have been granted", "star after a verb"),
    ('the expectation "that certain facts"', "star before a quotation"),
    ("options presented in the other six are impracticable", "star inside a phrase"),
    ("in at least 22 other current conspiracy statutes.", "bracketed footnote"),
])
def test_star_pagination_does_not_block_matching(span, why):
    assert locate_span(span, STARRED) is not None, why


@pytest.mark.parametrize("span,why", [
    ("its language appears mandatory rather than permissive", "word substituted"),
    ("in at least 33 other current conspiracy statutes", "number altered"),
    ("habeas corpus should have been denied", "outcome reversed"),
])
def test_pagination_tolerance_does_not_admit_alterations(span, why):
    """Stripping page markers must not make content digits meaningless.

    An earlier version also removed bare mid-sentence numbers, which deleted
    substantive figures ("at least 22 other statutes") and would have let an
    altered number pass verification. Only explicitly marked forms are
    stripped."""
    assert locate_span(span, STARRED) is None, why


def test_substantive_numbers_are_still_matched():
    assert locate_span("in at least 22 other current conspiracy statutes",
                       STARRED) is not None


# --- Answers must explain, not transcribe ----------------------------------
#
# Measured on 333 pairs: 45.6% of answers were near-copies of their supporting
# span (median token overlap 0.838). A dataset whose answers reproduce the
# source teaches extraction rather than legal reasoning, and collapses the
# distinction between this resource and span-extraction datasets.

COPY_CFG = {"generate": {**CFG["generate"], "max_copied_run_words": 10}}

VESSEL_CHUNK = (
    "Under \u00a7 3, a vessel is any watercraft practically capable of maritime "
    "transportation, regardless of its primary purpose or state of transit at "
    "a particular moment. The question remains in all cases whether the "
    "watercraft is capable of being used for transportation on water."
)


def vessel_pair(answer):
    return {
        "question": "What test did the Court adopt for determining vessel status here?",
        "answer": answer,
        "question_type": "holding",
        "supporting_span": ("a vessel is any watercraft practically capable of "
                            "maritime transportation, regardless of its primary purpose"),
    }


def vessel_chunk():
    return chunk_opinion(VESSEL_CHUNK, 1)[0]


def test_answer_that_copies_the_span_is_rejected():
    copied = ("A vessel is any watercraft practically capable of maritime "
              "transportation, regardless of its primary purpose or state of transit.")
    rec, reason = validate(vessel_pair(copied), {**REC, "text": VESSEL_CHUNK},
                           vessel_chunk(), COPY_CFG)
    assert rec is None
    assert reason == "answer_copies_span"


def test_answer_that_explains_the_span_is_accepted():
    explained = ("The Court adopted a capability-based test: what matters is "
                 "whether the craft can be used to carry things over water, not "
                 "what it was built for or whether it happened to be moving.")
    rec, reason = validate(vessel_pair(explained), {**REC, "text": VESSEL_CHUNK},
                           vessel_chunk(), COPY_CFG)
    assert reason == "ok", reason
    assert rec is not None


def test_partial_quotation_of_terms_of_art_is_allowed():
    """Quoting a defined term is normal legal writing and must not be rejected."""
    partial = ("The Court held that a watercraft qualifies as a vessel when it is "
               "practically capable of maritime transportation. Its purpose at the "
               "time is irrelevant to that inquiry.")
    rec, reason = validate(vessel_pair(partial), {**REC, "text": VESSEL_CHUNK},
                           vessel_chunk(), COPY_CFG)
    assert reason == "ok", reason


def test_copy_check_is_optional():
    """Without the threshold configured, the check must not fire."""
    copied = ("A vessel is any watercraft practically capable of maritime "
              "transportation, regardless of its primary purpose or state of transit.")
    rec, reason = validate(vessel_pair(copied), {**REC, "text": VESSEL_CHUNK},
                           vessel_chunk(), CFG)
    assert reason == "ok"


def test_prompt_forbids_copying_and_shows_an_example():
    prompt = build_prompt(REC, a_chunk(), 3)
    assert "MUST NOT COPY" in prompt
    assert "BAD" in prompt and "GOOD" in prompt
