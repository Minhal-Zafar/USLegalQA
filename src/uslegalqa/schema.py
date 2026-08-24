"""Record schemas for the USLegalQA pipeline (JSONL records per stage)."""

from __future__ import annotations

from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class SubOpinion:
    """A single opinion document within a cluster (case).

    `010combined` records hold every opinion in one document and must be run
    through `segment.segment_opinion()` before use.
    """

    opinion_id: int
    type: str                 # CourtListener code, e.g. "020lead", "040dissent"
    author: str | None
    text: str
    word_count: int
    per_curiam: bool = False
    extracted_by_ocr: bool = False
    page_count: int | None = None

    @property
    def is_primary(self) -> bool:
        return self.type in {"010combined", "015unamimous", "020lead", "025plurality"}


@dataclass
class Cluster:
    """One case, keyed by CourtListener's stable `cluster_id`.

    The unit of deduplication and of train/test splitting.
    """

    cluster_id: int
    case_name: str
    date_filed: str           # ISO date. NOT date_created.
    court: str
    precedential_status: str | None
    citation: str | None
    sub_opinions: list[SubOpinion] = field(default_factory=list)

    # Supreme Court Database linkage (empty for cases SCDB has not coded yet).
    scdb_id: str | None = None
    scdb_decision_direction: int | None = None
    scdb_votes_majority: int | None = None
    scdb_votes_minority: int | None = None

    docket_id: int | None = None
    judges: str | None = None
    syllabus: str | None = None       # official headnote, when CourtListener has it

    def primary(self) -> SubOpinion | None:
        """The authoritative opinion, or None if the cluster has only
        separate writings. Longest primary wins when several qualify."""
        candidates = [o for o in self.sub_opinions if o.is_primary]
        if not candidates:
            return None
        return max(candidates, key=lambda o: o.word_count)

    def secondary(self) -> list[SubOpinion]:
        return [o for o in self.sub_opinions if not o.is_primary]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    # Downstream fields preserved on disk but ignored on load.
    _EXTRA_KEYS = frozenset({
        "scdb_category", "scdb_issue_area_code", "scdb_term", "scdb_match",
    })

    @classmethod
    def from_dict(cls, d: dict[str, Any]) -> "Cluster":
        subs = [SubOpinion(**s) for s in d.get("sub_opinions", [])]
        known = {f for f in cls.__dataclass_fields__}
        kwargs = {k: v for k, v in d.items() if k in known}
        return cls(**{**kwargs, "sub_opinions": subs})


@dataclass
class CleanedOpinion:
    """Post-cleaning record: one per case, carrying the full binding text."""

    cluster_id: int
    case_name: str
    date_filed: str
    court: str
    citation: str | None
    primary_type: str
    primary_author: str | None
    text: str                 # BINDING text only (majority / per curiam)
    word_count: int           # words in `text`
    n_secondary: int
    secondary_types: list[str] = field(default_factory=list)
    category: str | None = None       # filled by the classifier stage

    # Segmentation metadata: what was removed to leave the binding `text`.
    source_word_count: int = 0        # words in the original full document
    section_kinds: dict = field(default_factory=dict)
    segmentation_confident: bool = True
    syllabus_text: str | None = None
    scdb_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


REQUIRED_CLEANED_FIELDS = (
    "cluster_id", "case_name", "date_filed", "text", "word_count", "primary_type"
)


def validate_cleaned(rec: dict[str, Any]) -> list[str]:
    """Return a list of problems; empty means valid."""
    problems = []
    for f in REQUIRED_CLEANED_FIELDS:
        if f not in rec or rec[f] in (None, "", []):
            problems.append(f"missing field: {f}")

    date = rec.get("date_filed", "")
    if date and not (len(date) == 10 and date[4] == "-" and date[7] == "-"):
        problems.append(f"date_filed not ISO format: {date!r}")

    if rec.get("word_count") and rec.get("text"):
        actual = len(rec["text"].split())
        if abs(actual - rec["word_count"]) > 1:
            problems.append(
                f"word_count {rec['word_count']} disagrees with text ({actual})"
            )

    ptype = rec.get("primary_type")
    if ptype and ptype in {"030concurrence", "035concurrenceinpart", "040dissent"}:
        problems.append(
            f"primary_type is a separate writing ({ptype}) -- this record would "
            "attribute non-binding reasoning to the Court"
        )
    return problems
