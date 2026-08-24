"""Split binding opinion text into overlapping windows for QA generation.

Each window records its position in the document (early/middle/late) and its
character offsets, which anchor span grounding. Windows are sized in words,
overlap so reasoning crossing a boundary is not lost, and prefer paragraph
then sentence boundaries as split points.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any, Iterator

# Position bands steer question generation toward the material in a window.
POSITION_EARLY = "early"      # facts, procedural history, question presented
POSITION_MIDDLE = "middle"    # analysis, doctrine, statutory construction
POSITION_LATE = "late"        # holding, disposition, remedy

_PARA_BREAK = re.compile(r"\n\s*\n")
_SENT_END = re.compile(r"(?<=[.?!])\s+(?=[A-Z“\"'(])")


@dataclass
class Chunk:
    """One window of an opinion, with provenance back to the source text."""

    cluster_id: int
    chunk_index: int
    n_chunks: int
    start_word: int
    end_word: int
    char_start: int
    char_end: int
    position: str
    text: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def is_final(self) -> bool:
        return self.chunk_index == self.n_chunks - 1

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["word_count"] = self.word_count
        return d


def _position(index: int, n_chunks: int) -> str:
    """Band a chunk by where it falls in the document.

    A single-chunk opinion is LATE: short per curiam decisions state their
    holding directly.
    """
    if n_chunks == 1:
        return POSITION_LATE
    if n_chunks == 2:
        return POSITION_EARLY if index == 0 else POSITION_LATE

    # Bands scale with length (floor: one early, two late chunks); roughly the
    # closing fifth of an opinion states and applies the holding.
    n_early = max(1, round(n_chunks * 0.15))
    n_late = max(2, round(n_chunks * 0.20))

    if index < n_early:
        return POSITION_EARLY
    if index >= n_chunks - n_late:
        return POSITION_LATE
    return POSITION_MIDDLE


def _snap_backwards(text: str, target: int, window: int = 600) -> int:
    """Move a character offset back to the nearest clean break.

    Prefers a paragraph break, then a sentence end, then the target itself.
    """
    if target >= len(text):
        return len(text)
    lo = max(0, target - window)
    segment = text[lo:target]

    breaks = list(_PARA_BREAK.finditer(segment))
    if breaks:
        return lo + breaks[-1].end()

    sentences = list(_SENT_END.finditer(segment))
    if sentences:
        return lo + sentences[-1].end()

    return target


def chunk_opinion(text: str, cluster_id: int, target_words: int = 900,
                  overlap_words: int = 150,
                  min_final_words: int = 200) -> list[Chunk]:
    """Split `text` into overlapping windows.

    Args:
        target_words: nominal window size.
        overlap_words: shared context between consecutive windows.
        min_final_words: a trailing remnant shorter than this is merged into
            the previous window rather than emitted as a stub.

    Returns an empty list for empty input.
    """
    text = (text or "").strip()
    if not text:
        return []

    words = text.split()
    total = len(words)

    if total <= target_words:
        return [Chunk(
            cluster_id=cluster_id, chunk_index=0, n_chunks=1,
            start_word=0, end_word=total, char_start=0, char_end=len(text),
            position=POSITION_LATE, text=text,
        )]

    # Map word index -> character offset, so chunks can carry exact spans.
    offsets: list[int] = []
    pos = 0
    for w in words:
        pos = text.index(w, pos)
        offsets.append(pos)
        pos += len(w)

    stride = max(1, target_words - overlap_words)
    bounds: list[tuple[int, int]] = []
    start = 0
    while start < total:
        end = min(start + target_words, total)
        bounds.append((start, end))
        if end >= total:
            break
        start += stride

    # Fold a short tail into its predecessor.
    if len(bounds) > 1 and (bounds[-1][1] - bounds[-1][0]) < min_final_words:
        prev_start, _ = bounds[-2]
        bounds[-2] = (prev_start, bounds[-1][1])
        bounds.pop()

    n_chunks = len(bounds)
    chunks: list[Chunk] = []
    for i, (ws, we) in enumerate(bounds):
        char_start = offsets[ws] if i == 0 else _snap_backwards(text, offsets[ws])
        char_end = (len(text) if we >= total
                    else offsets[we - 1] + len(words[we - 1]))
        chunks.append(Chunk(
            cluster_id=cluster_id, chunk_index=i, n_chunks=n_chunks,
            start_word=ws, end_word=we,
            char_start=char_start, char_end=char_end,
            position=_position(i, n_chunks),
            text=text[char_start:char_end],
        ))
    return chunks


def iter_chunks(records: list[dict], **kwargs) -> Iterator[tuple[dict, Chunk]]:
    """Yield (opinion_record, chunk) for a list of cleaned opinions."""
    for rec in records:
        for chunk in chunk_opinion(rec["text"], rec["cluster_id"], **kwargs):
            yield rec, chunk


def coverage_report(records: list[dict], **kwargs) -> dict[str, Any]:
    """Summarise what chunking will cost and cover, before spending on an API."""
    n_chunks = 0
    per_opinion: list[int] = []
    positions: dict[str, int] = {}
    covered_words = 0
    source_words = 0

    for rec in records:
        chunks = chunk_opinion(rec["text"], rec["cluster_id"], **kwargs)
        per_opinion.append(len(chunks))
        n_chunks += len(chunks)
        source_words += len(rec["text"].split())
        for c in chunks:
            positions[c.position] = positions.get(c.position, 0) + 1
        if chunks:
            covered_words += chunks[-1].end_word

    per_opinion.sort()
    return {
        "opinions": len(records),
        "chunks": n_chunks,
        "chunks_per_opinion_median": (per_opinion[len(per_opinion) // 2]
                                      if per_opinion else 0),
        "chunks_per_opinion_max": max(per_opinion) if per_opinion else 0,
        "positions": positions,
        "source_words": source_words,
        "coverage_pct": round(100 * covered_words / source_words, 1)
        if source_words else 0.0,
    }
