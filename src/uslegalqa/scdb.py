"""Attach Supreme Court Database (SCDB) issue areas to collected opinions.

Records are joined on U.S. Reports citation, with case name as a fallback.

Download (free, no registration):
    https://scdb.la.psu.edu/data/
    Choose: Modern Database -> Case Centered -> Citation  ->  CSV

Usage:
    python -m uslegalqa.scdb --scdb SCDB_2024_01_caseCentered_Citation.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

# SCDB issueArea codes -> readable labels.
# Source: SCDB online codebook, variable `issueArea`.
ISSUE_AREAS = {
    "1": "criminal_procedure",
    "2": "civil_rights",
    "3": "first_amendment",
    "4": "due_process",
    "5": "privacy",
    "6": "attorneys",
    "7": "unions",
    "8": "economic_activity",
    "9": "judicial_power",
    "10": "federalism",
    "11": "interstate_relations",
    "12": "federal_taxation",
    "13": "miscellaneous",
    "14": "private_action",
}

_CITE_RE = re.compile(r"(\d+)\s+U\.?\s?S\.?\s+(\d+)")


def norm_citation(cite: str | None) -> str | None:
    """Normalise a U.S. Reports citation to 'volume-page'."""
    if not cite:
        return None
    m = _CITE_RE.search(cite.replace("U. S.", "U.S."))
    return f"{m.group(1)}-{m.group(2)}" if m else None


_NOISE = re.compile(
    r"\b(v|vs|et|al|inc|llc|co|corp|corporation|ltd|lp|llp|"
    r"the|of|and|a|an|dba|petitioner|respondent|"
    # Official titles: SCDB spells these out, CourtListener frequently omits.
    r"attorney|general|secretary|commissioner|director|administrator|"
    r"warden|superintendent|sheriff|governor|president|board|department|"
    r"county|city|state|states|united|us|dept|comm|bureau|agency|"
    r"office|officer|acting|interim)\b")


def norm_name(name: str | None) -> str:
    """Reduce a case name to its significant tokens for fallback matching."""
    if not name:
        return ""
    n = name.lower()
    n = re.sub(r"[^a-z0-9 ]", " ", n)
    n = _NOISE.sub(" ", n)
    return re.sub(r"\s+", " ", n).strip()


_TAIL = re.compile(
    r",?\s*(et al\.?|doing business as|dba|d/b/a|individually|"
    r"on behalf of|as trustee|trustee)\b.*$", re.IGNORECASE)


def name_key(name: str | None) -> str:
    """Order-independent key from the leading party tokens either side of 'v.'."""
    if not name:
        return ""
    # Split before stripping tails, so an 'et al.' before the 'v.' is harmless.
    parts = re.split(r"\bv[s]?\.?\b", name, maxsplit=1, flags=re.IGNORECASE)
    sides = []
    for part in parts[:2]:
        toks = [t for t in norm_name(_TAIL.sub("", part)).split() if len(t) > 2]
        # Deeper tokens are usually descriptive and differ between sources.
        sides.extend(toks[:2])
    return " ".join(sorted(sides))


def load_scdb(path: Path) -> tuple[dict, dict]:
    """Index SCDB rows by normalised citation and by normalised case name."""
    by_cite: dict[str, dict] = {}
    by_name: dict[str, dict] = {}

    # SCDB ships as latin-1; utf-8 will raise on older rows.
    with path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        required = {"usCite", "caseName", "issueArea"}
        missing = required - set(reader.fieldnames or [])
        if missing:
            sys.exit(
                f"SCDB file is missing columns: {sorted(missing)}\n"
                f"Found: {reader.fieldnames}\n"
                "Download the *Case Centered / Citation* CSV from "
                "https://scdb.la.psu.edu/data/"
            )

        for row in reader:
            area = (row.get("issueArea") or "").strip()
            entry = {
                "scdb_id": row.get("caseId"),
                "issue_area_code": area,
                "category": ISSUE_AREAS.get(area),
                "scdb_case_name": row.get("caseName"),
                "decision_direction": row.get("decisionDirection"),
                "majority_votes": row.get("majVotes"),
                "minority_votes": row.get("minVotes"),
                "term": row.get("term"),
            }
            cite = norm_citation(row.get("usCite"))
            if cite:
                by_cite.setdefault(cite, entry)
            nm = name_key(row.get("caseName"))
            if nm:
                by_name.setdefault(nm, entry)

    return by_cite, by_name


def annotate(cfg: dict, scdb_path: Path, out_path: Path | None = None) -> None:
    cleaned = Path(cfg["paths"]["cleaned"])
    out_path = out_path or cleaned

    by_cite, by_name = load_scdb(scdb_path)
    print(f"SCDB: {len(by_cite):,} cases indexed by citation, "
          f"{len(by_name):,} by name")

    records = [json.loads(l) for l in cleaned.read_text(encoding="utf-8").splitlines()
               if l.strip()]

    matched_cite = matched_name = unmatched = 0
    categories: Counter = Counter()
    unmatched_examples: list[str] = []

    for rec in records:
        hit = None
        cite = norm_citation(rec.get("citation"))
        if cite and cite in by_cite:
            hit = by_cite[cite]
            matched_cite += 1
        else:
            nm = name_key(rec.get("case_name"))
            if nm and nm in by_name:
                hit = by_name[nm]
                matched_name += 1

        if hit:
            rec["category"] = hit["category"]
            rec["scdb_id"] = hit["scdb_id"]
            rec["scdb_issue_area_code"] = hit["issue_area_code"]
            rec["scdb_decision_direction"] = hit["decision_direction"]
            rec["scdb_majority_votes"] = hit["majority_votes"]
            rec["scdb_minority_votes"] = hit["minority_votes"]
            rec["scdb_match"] = "citation" if (cite and cite in by_cite) else "case_name"
            categories[hit["category"] or "uncoded"] += 1
        else:
            rec["category"] = None
            rec["scdb_match"] = None
            unmatched += 1
            if len(unmatched_examples) < 10:
                unmatched_examples.append(
                    f"{rec.get('date_filed')}  {rec.get('case_name', '')[:55]}  "
                    f"[{rec.get('citation')}]")

    with out_path.open("w", encoding="utf-8") as f:
        for rec in records:
            f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    total = len(records)
    print("SCDB annotation:")
    print(f"  matched by citation   {matched_cite:>6}")
    print(f"  matched by case name  {matched_name:>6}")
    print(f"  unmatched             {unmatched:>6}")
    if total:
        print(f"  coverage              {100*(total-unmatched)/total:>5.1f}%")

    print("\nIssue area distribution:")
    for cat, n in categories.most_common():
        print(f"  {cat or 'uncoded':<24} {n:>5}  {100*n/max(total,1):>5.1f}%")

    if records:
        yrs = sorted({r.get("date_filed", "")[:4] for r in records
                      if r.get("date_filed")})
        miss_by_year: Counter = Counter(
            r.get("date_filed", "")[:4] for r in records if not r.get("scdb_match"))
        if miss_by_year:
            print("\nUnmatched by year:")
            for y in yrs:
                if miss_by_year.get(y):
                    print(f"  {y}: {miss_by_year[y]}")

    if unmatched_examples:
        print("\nUnmatched examples:")
        for e in unmatched_examples:
            print(f"  - {e}")

    print(f"\nWrote {total} annotated records -> {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--scdb", required=True,
                    help="Path to the SCDB case-centered CSV.")
    ap.add_argument("--out", default=None,
                    help="Output path (defaults to overwriting the cleaned file).")
    args = ap.parse_args()

    scdb_path = Path(args.scdb)
    if not scdb_path.exists():
        sys.exit(f"SCDB file not found: {scdb_path}\n"
                 "Download from https://scdb.la.psu.edu/data/ "
                 "(Modern Database -> Case Centered -> Citation, CSV)")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    annotate(cfg, scdb_path, Path(args.out) if args.out else None)


if __name__ == "__main__":
    main()
