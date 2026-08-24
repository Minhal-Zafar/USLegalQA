"""Segment a SCOTUS slip opinion into its constituent writings.

`010combined` records concatenate the syllabus, majority, concurrences and
dissents into one document. Sections carry character offsets into the source
text so generated answers can be traced to an exact span.

Reference structure of a slip opinion:

    (Slip Opinion)  OCTOBER TERM, 2025
    Syllabus
    NOTE: Where it is feasible, a syllabus (headnote) will be released...
    SUPREME COURT OF THE UNITED STATES
    ...
    JUSTICE KAGAN delivered the opinion of the Court.
    ...
    JUSTICE THOMAS, concurring.
    ...
    JUSTICE SOTOMAYOR, with whom JUSTICE JACKSON joins, dissenting.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, asdict
from typing import Any

# Section kinds. Only MAJORITY (and PER_CURIAM) state the law.
SYLLABUS = "syllabus"
MAJORITY = "majority"
PER_CURIAM = "per_curiam"
CONCURRENCE = "concurrence"
DISSENT = "dissent"
MIXED = "concurrence_in_part_dissent_in_part"
FRONT_MATTER = "front_matter"

BINDING_KINDS = frozenset({MAJORITY, PER_CURIAM})

_JUSTICE = r"(?:THE\s+)?(?:CHIEF\s+)?JUSTICE\s+([A-Z][A-Za-z'\u2019\-]+)"

# "JUSTICE KAGAN delivered the opinion of the Court."
# "JUSTICE ALITO announced the judgment of the Court and delivered an opinion."
_MAJORITY_RE = re.compile(
    rf"{_JUSTICE}\s*,?\s+(?:delivered|announced)\s+the\s+(?:opinion|judgment)\s+of\s+the\s+Court",
    re.IGNORECASE,
)

_PER_CURIAM_RE = re.compile(r"^\s*PER\s+CURIAM\s*\.?\s*$", re.MULTILINE)

# The syllabus repeats the majority header but follows it with "concluding:"
# or "holding that..."; the opinion proper never does, so this tail marks it.
_SYLLABUS_SUMMARY_TAIL = re.compile(
    r"\b(?:conclud(?:ing|ed)|hold(?:ing|s)?)\s*(?::|that\b)", re.IGNORECASE)

# "JUSTICE SOTOMAYOR, with whom JUSTICE JACKSON joins, dissenting."
# "JUSTICE THOMAS, concurring in the judgment."
# "JUSTICE BREYER, concurring in part and dissenting in part."
# "JUSTICE THOMAS, with whom THE CHIEF JUSTICE, JUSTICE SCALIA, and
#  JUSTICE ALITO join, dissent-\ning."
#
# Joiner lists span commas and line breaks, and PDFs hyphenate the descriptor
# across lines ("con-\ncurring", "dissent­\ning").
_BREAK = r"[\s\-­]*"
_DESCRIPTOR = rf"(?:con{_BREAK}cur{_BREAK}ring|dis{_BREAK}sent{_BREAK}ing)"
# The descriptor must close its own line with no commas or quotes in its tail,
# so running prose ("JUSTICE SCALIA, dissenting on standing, berates...") is
# not read as a header.
_SEPARATE_RE = re.compile(
    rf"{_JUSTICE}\s*,\s*(?:with\s+whom\b[\s\S]{{0,400}}?\bjoins?\b[^.]{{0,160}}?,\s*)?"
    rf"({_DESCRIPTOR}[^.,“”\"]{{0,160}})\.[ \t]*$",
    re.IGNORECASE | re.MULTILINE,
)

# Slip-opinion page header of a separate writing, e.g.
#   "Cite as: 573 U. S. ____ (2014) 1\n\n SCALIA, J., concurring in judgment"
# Marks the boundary even where the opening formula is unreadable.
_RUNNING_HEADER_RE = re.compile(
    r"(?:^[^\n]*Cite as:[^\n]*\n\s*)?^[ \t]*[A-Z][A-Z'’\-]+, (?:C\. )?J\., "
    # Must stand alone on its line; excludes in-text "(KAGAN, J., dissenting)".
    rf"({_DESCRIPTOR}[^\n()“”\"]{{0,80}})[ \t]*$",
    re.MULTILINE,
)

_SYLLABUS_RE = re.compile(
    r"NOTE:\s*Where\s+it\s+is\s+feasible|^\s*Syllabus\s*$",
    re.IGNORECASE | re.MULTILINE,
)


@dataclass
class Section:
    kind: str
    author: str | None
    start: int          # character offset into the source text
    end: int
    text: str

    @property
    def word_count(self) -> int:
        return len(self.text.split())

    @property
    def is_binding(self) -> bool:
        return self.kind in BINDING_KINDS

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["word_count"] = self.word_count
        return d


def _classify(descriptor: str) -> str:
    d = re.sub(r"[\s\-­]+", "", descriptor.lower())
    has_dissent = "dissenting" in d
    has_concur = "concurring" in d
    if has_dissent and has_concur:
        return MIXED
    if has_dissent:
        return DISSENT
    return CONCURRENCE


def _headers(text: str, binding_from_start: bool = False
             ) -> list[tuple[int, str, str | None]]:
    """Collect (offset, kind, author) for every writing boundary.

    `binding_from_start` treats the text as already inside the Court's opinion.
    """
    found: list[tuple[int, str, str | None]] = []

    for m in _MAJORITY_RE.finditer(text):
        # A "concluding:" tail marks the syllabus summary, not the opinion.
        lookahead = text[m.end():m.end() + 160]
        kind = SYLLABUS if _SYLLABUS_SUMMARY_TAIL.search(lookahead) else MAJORITY
        found.append((m.start(), kind, m.group(1) if kind == MAJORITY else None))

    for m in _PER_CURIAM_RE.finditer(text):
        found.append((m.start(), PER_CURIAM, None))

    for m in _SEPARATE_RE.finditer(text):
        # Where it overlaps a majority header, the majority match wins.
        if any(abs(m.start() - o) < 5 for o, _, _ in found):
            continue
        found.append((m.start(), _classify(m.group(2)), m.group(1)))

    # Only the first running header of each writing is a boundary; the rest
    # repeat on every page.
    separate = (CONCURRENCE, DISSENT, MIXED)
    for m in _RUNNING_HEADER_RE.finditer(text):
        start = m.start()
        preceding = [h for h in sorted(found) if h[0] <= start]
        if not binding_from_start and not any(k in BINDING_KINDS for _, k, _ in preceding):
            continue   # before the Court's opinion: syllabus furniture
        if preceding and preceding[-1][1] in separate:
            continue   # a repeat header inside a writing already found
        if any(0 <= o - start < 2500 for o, k, _ in found if k in separate):
            continue   # the opening formula follows shortly and marks it
        found.append((start, _classify(m.group(1)), None))

    return sorted(found, key=lambda t: t[0])


def first_separate_boundary(text: str, binding_from_start: bool = False) -> int | None:
    """Offset where the first separate writing begins after the Court's opinion.

    Uses the earlier of the page header and the opening formula.
    """
    headers = _headers(text, binding_from_start)
    seen_binding = binding_from_start
    for offset, kind, _ in headers:
        if kind in BINDING_KINDS:
            seen_binding = True
        elif seen_binding and kind in (CONCURRENCE, DISSENT, MIXED):
            # Back up over the page header if one sits just before the formula.
            window = text[max(0, offset - 2500):offset]
            h = list(_RUNNING_HEADER_RE.finditer(window))
            return max(0, offset - 2500) + h[-1].start() if h else offset
    return None


def segment_opinion(text: str) -> list[Section]:
    """Split a slip opinion into ordered sections.

    With no detectable boundary the whole text is one MAJORITY section; check
    `segmentation_confident()` before trusting it.
    """
    if not text.strip():
        return []

    headers = _headers(text)

    if not headers:
        return [Section(MAJORITY, None, 0, len(text), text)]

    sections: list[Section] = []

    # Everything before the first writing: syllabus and caption furniture.
    first = headers[0][0]
    if first > 0:
        head = text[:first]
        kind = SYLLABUS if _SYLLABUS_RE.search(head) else FRONT_MATTER
        sections.append(Section(kind, None, 0, first, head))

    for i, (offset, kind, author) in enumerate(headers):
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        sections.append(Section(kind, author, offset, end, text[offset:end]))

    return sections


def segmentation_confident(sections: list[Section]) -> bool:
    """True when exactly one binding section was identified."""
    return sum(1 for s in sections if s.is_binding) == 1


def binding_text(sections: list[Section]) -> str:
    """Concatenated text of the sections that state the law."""
    return "\n\n".join(s.text for s in sections if s.is_binding).strip()


def summarise(sections: list[Section]) -> dict[str, Any]:
    counts: dict[str, int] = {}
    for s in sections:
        counts[s.kind] = counts.get(s.kind, 0) + 1
    return {
        "n_sections": len(sections),
        "kinds": counts,
        "binding_words": len(binding_text(sections).split()),
        "total_words": sum(s.word_count for s in sections),
        "confident": segmentation_confident(sections),
    }
