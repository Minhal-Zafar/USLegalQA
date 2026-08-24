"""Tests for opinion chunking.

The critical guarantees: full coverage of the opinion (v2 covered ~13%), exact
character offsets (span grounding depends on them), and position banding that
lets holdings be targeted where they actually appear.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from uslegalqa.chunking import (
    chunk_opinion, coverage_report, POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE,
)


def make_text(n_words: int, marker: str = "w") -> str:
    """Paragraphed text withuniquely identifiable words."""
    words = [f"{marker}{i}" for i in range(n_words)]
    out, i = [], 0
    while i < n_words:
        out.append(" ".join(words[i:i + 60]) + ".")
        i += 60
    return "\n\n".join(out)


def test_empty_text_yields_no_chunks():
    assert chunk_opinion("", 1) == []
    assert chunk_opinion("   \n ", 1) == []


def test_short_opinion_is_single_chunk():
    text = make_text(400)
    chunks = chunk_opinion(text, 1, target_words=900)
    assert len(chunks) == 1
    assert chunks[0].text == text
    assert chunks[0].position == POSITION_LATE
    assert chunks[0].is_final


def test_long_opinion_is_split():
    chunks = chunk_opinion(make_text(5000), 1, target_words=900, overlap_words=150)
    assert len(chunks) > 4
    assert all(c.n_chunks == len(chunks) for c in chunks)
    assert [c.chunk_index for c in chunks] == list(range(len(chunks)))


def test_offsets_round_trip_exactly():
    """Span grounding stores character offsets; they must be exact."""
    text = make_text(3000)
    for c in chunk_opinion(text, 1):
        assert text[c.char_start:c.char_end] == c.text


def test_full_document_is_covered():
    """v2 saw only the first ~650 words of each opinion. Chunking must reach
    the end, where holdings live."""
    text = make_text(5000, "word")
    chunks = chunk_opinion(text, 1, target_words=900, overlap_words=150)
    assert chunks[-1].end_word == 5000
    assert "word4999" in chunks[-1].text
    assert "word0" in chunks[0].text


def test_chunks_overlap():
    chunks = chunk_opinion(make_text(4000), 1, target_words=900, overlap_words=150)
    for a, b in zip(chunks, chunks[1:]):
        assert b.start_word < a.end_word, "consecutive chunks must overlap"


def test_positions_span_all_three_bands():
    chunks = chunk_opinion(make_text(8000), 1, target_words=900)
    positions = {c.position for c in chunks}
    assert positions == {POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE}
    assert chunks[0].position == POSITION_EARLY
    assert chunks[-1].position == POSITION_LATE


def test_short_tail_is_merged_not_emitted():
    chunks = chunk_opinion(make_text(1600), 1, target_words=900,
                           overlap_words=150, min_final_words=200)
    assert all(c.word_count >= 200 for c in chunks)


def test_no_content_lost_between_chunks():
    """Every word of the source must appear in at least one chunk."""
    text = make_text(3000, "tok")
    chunks = chunk_opinion(text, 1, target_words=800, overlap_words=100)
    seen = set()
    for c in chunks:
        seen.update(c.text.split())
    missing = [w for w in text.split() if w not in seen]
    assert not missing, f"{len(missing)} words lost, e.g. {missing[:5]}"


def test_cluster_id_propagates():
    chunks = chunk_opinion(make_text(2000), 4242)
    assert all(c.cluster_id == 4242 for c in chunks)


def test_coverage_report_shape():
    records = [
        {"cluster_id": 1, "text": make_text(5000)},
        {"cluster_id": 2, "text": make_text(800)},
    ]
    report = coverage_report(records, target_words=900)
    assert report["opinions"] == 2
    assert report["chunks"] > 2
    assert report["coverage_pct"] == 100.0
    assert set(report["positions"]) <= {POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE}


@pytest.mark.parametrize("n_words", [901, 1500, 2400, 9000, 51149])
def test_various_lengths_are_fully_covered(n_words):
    """51,149 is the longest binding opinion in the corpus."""
    text = make_text(n_words)
    chunks = chunk_opinion(text, 1)
    assert chunks[-1].end_word == n_words
    assert chunks[0].start_word == 0


def test_middle_chunks_are_not_labelled_early():
    """A 4-chunk opinion under fraction-based banding put index 1 at 0.33,
    labelling a passage of legal reasoning as 'beginning of the opinion' and
    prompting it for facts and procedural history."""
    chunks = chunk_opinion(make_text(3200), 1, target_words=900, overlap_words=150)
    assert chunks[0].position == POSITION_EARLY
    assert all(c.position != POSITION_EARLY for c in chunks[1:])


@pytest.mark.parametrize("n_chunks,expected", [
    (1, ["late"]),
    (2, ["early", "late"]),
    (3, ["early", "late", "late"]),
    (4, ["early", "middle", "late", "late"]),
])
def test_position_banding_short_opinions(n_chunks, expected):
    from uslegalqa.chunking import _position
    assert [_position(i, n_chunks) for i in range(n_chunks)] == expected


@pytest.mark.parametrize("n_chunks", [15, 30, 68])
def test_long_opinions_get_proportional_late_coverage(n_chunks):
    """A fixed late-chunk count does not survive long opinions: at 68 chunks,
    two late chunks is 3% of the document. Holdings are requested from the
    late band, so this drove holding questions to 10.4% of a full corpus run
    -- below even the truncated v2 pipeline."""
    from uslegalqa.chunking import _position
    bands = [_position(i, n_chunks) for i in range(n_chunks)]
    late_frac = bands.count("late") / n_chunks
    assert 0.15 <= late_frac <= 0.30, f"{late_frac:.2f} late in {n_chunks} chunks"
    assert bands[0] == "early"
    assert bands[-1] == "late"
