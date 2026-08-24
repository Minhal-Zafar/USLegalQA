"""Convert cached COLD Cases rows into the pipeline's Cluster schema.

Runs entirely locally against the parquet cache produced by
`collect_cold.py --extract`. No network, no rate limit.

Mapping (COLD -> Cluster):
    id                      -> cluster_id
    case_name               -> case_name
    date_filed              -> date_filed
    citations[]             -> citation (first U.S. Reports entry)
    opinions[].type         -> SubOpinion.type
    opinions[].opinion_text -> SubOpinion.text
    opinions[].author_str   -> SubOpinion.author
    opinions[].per_curiam   -> SubOpinion.per_curiam
    opinions[].ocr          -> SubOpinion.extracted_by_ocr
    syllabus                -> Cluster.syllabus

SCDB supplies the category and defines corpus membership: records are joined by
U.S. Reports citation (falling back to case name) and unmatched ones are dropped.

Usage:
    python -m uslegalqa.convert_cold --scdb SCDB_2025_01_caseCentered_Citation.csv
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

from .schema import Cluster, SubOpinion
from .scdb import ISSUE_AREAS, norm_citation, name_key

_US_CITE = re.compile(r"^\s*\d+\s+U\.?\s?S\.?\s+\d+\s*$")


def pick_us_citation(citations) -> str | None:
    """First U.S. Reports citation from COLD's parallel citation list."""
    if not citations:
        return None
    for c in citations:
        if c and _US_CITE.match(str(c)):
            return str(c).strip()
    return None


def load_scdb_index(path: Path, year_from: int, year_to: int) -> tuple[dict, dict]:
    by_cite: dict[str, dict] = {}
    by_name: dict[str, dict] = {}
    with path.open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            m = re.search(r"/(\d{4})$", row.get("dateDecision") or "")
            if not m or not (year_from <= int(m.group(1)) <= year_to):
                continue
            area = (row.get("issueArea") or "").strip()
            entry = {
                "scdb_id": row.get("caseId"),
                "category": ISSUE_AREAS.get(area),
                "issue_area_code": area,
                "decision_direction": row.get("decisionDirection"),
                "majority_votes": row.get("majVotes"),
                "minority_votes": row.get("minVotes"),
                "term": row.get("term"),
            }
            cite = norm_citation(row.get("usCite"))
            if cite:
                by_cite.setdefault(cite, entry)
            nk = name_key(row.get("caseName"))
            if nk:
                by_name.setdefault(nk, entry)
    return by_cite, by_name


def convert(cfg: dict, scdb_path: Path, parquet_path: Path,
            year_from: int, year_to: int) -> None:
    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb is required:  pip install duckdb")

    if not parquet_path.exists():
        sys.exit(f"Cache not found: {parquet_path}\n"
                 "Run: python -m uslegalqa.collect_cold --extract")

    print(f"SCDB index from {scdb_path.name} ({year_from}-{year_to})")
    by_cite, by_name = load_scdb_index(scdb_path, year_from, year_to)
    print(f"  {len(by_cite)} by citation, {len(by_name)} by name")

    con = duckdb.connect()
    cur = con.execute(f"""
        SELECT id, case_name, date_filed, citations, syllabus,
               precedential_status, judges, opinions
        FROM read_parquet('{parquet_path.as_posix()}')
        WHERE date_filed >= DATE '{year_from}-01-01'
          AND date_filed <= DATE '{year_to}-12-31'
        ORDER BY date_filed
    """)

    raw_path = Path(cfg["paths"]["raw"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    stats = Counter()
    categories: Counter = Counter()
    type_counts: Counter = Counter()
    seen: set[int] = set()
    unmatched_examples: list[str] = []

    # SCDB case id -> (total words, record); COLD has several documents per
    # case and the one with the most text is the merits decision.
    best_by_scdb: dict[str, tuple[int, dict]] = {}

    if True:
        while True:
            batch = cur.fetchmany(500)
            if not batch:
                break
            for (cid, case_name, date_filed, citations, syllabus,
                 prec_status, judges, opinions) in batch:
                stats["read"] += 1

                if cid in seen:
                    stats["duplicate_id"] += 1
                    continue
                seen.add(cid)

                us_cite = pick_us_citation(citations)
                hit = None
                match_by = None
                key = norm_citation(us_cite)
                if key and key in by_cite:
                    hit, match_by = by_cite[key], "citation"
                elif not key:
                    nk = name_key(case_name)
                    if nk and nk in by_name:
                        hit, match_by = by_name[nk], "case_name"
                else:
                    # No name fallback here: cert-grant orders share the case
                    # name but carry a different citation.
                    stats["citation_mismatch"] += 1

                if not hit:
                    stats["no_scdb_match"] += 1
                    if len(unmatched_examples) < 8:
                        unmatched_examples.append(
                            f"{date_filed}  {str(case_name)[:52]}  [{us_cite}]")
                    continue

                subs: list[SubOpinion] = []
                for op in (opinions or []):
                    text = (op.get("opinion_text") or "").strip()
                    if not text:
                        continue
                    otype = op.get("type") or "unknown"
                    subs.append(SubOpinion(
                        opinion_id=op.get("opinion_id") or -1,
                        type=otype,
                        author=op.get("author_str") or None,
                        text=text,
                        word_count=len(text.split()),
                        per_curiam=bool(op.get("per_curiam")),
                        extracted_by_ocr=bool(op.get("ocr")),
                        page_count=op.get("page_count"),
                    ))

                if not subs:
                    stats["no_opinion_text"] += 1
                    continue

                cluster = Cluster(
                    cluster_id=int(cid),
                    case_name=(case_name or "").strip(),
                    date_filed=str(date_filed),
                    court="scotus",
                    precedential_status=prec_status,
                    citation=us_cite,
                    sub_opinions=subs,
                    scdb_id=hit["scdb_id"],
                    scdb_decision_direction=hit["decision_direction"],
                    scdb_votes_majority=hit["majority_votes"],
                    scdb_votes_minority=hit["minority_votes"],
                    judges=judges or None,
                    syllabus=syllabus or None,
                )

                if cluster.primary() is None:
                    stats["no_primary_opinion"] += 1
                    continue

                rec = cluster.to_dict()
                rec["scdb_category"] = hit["category"]
                rec["scdb_issue_area_code"] = hit["issue_area_code"]
                rec["scdb_term"] = hit["term"]
                rec["scdb_match"] = match_by

                total_words = sum(o.word_count for o in subs)
                prev = best_by_scdb.get(hit["scdb_id"])
                if prev is None:
                    best_by_scdb[hit["scdb_id"]] = (total_words, rec)
                else:
                    stats["duplicate_scdb_case"] += 1
                    if total_words > prev[0]:
                        best_by_scdb[hit["scdb_id"]] = (total_words, rec)

    with raw_path.open("w", encoding="utf-8") as out:
        for _, rec in best_by_scdb.values():
            out.write(json.dumps(rec, ensure_ascii=False) + "\n")
            stats["kept"] += 1
            categories[rec.get("scdb_category") or "uncoded"] += 1
            for so in rec["sub_opinions"]:
                type_counts[so["type"]] += 1

    print("\nConversion summary:")
    for k, v in stats.most_common():
        print(f"  {k:<24} {v:>7}")

    total = stats["kept"]
    if total:
        print(f"\nSCDB issue areas ({total} cases):")
        for cat, n in categories.most_common():
            print(f"  {cat or 'uncoded':<24} {n:>5}  {100*n/total:>5.1f}%")

    if type_counts:
        print("\nSub-opinion types retained:")
        for t, n in type_counts.most_common():
            print(f"  {t:<28} {n:>7}")

    if stats["duplicate_scdb_case"]:
        print(f"\n{stats['duplicate_scdb_case']} duplicate documents collapsed "
              f"(kept the longest per SCDB case)")

    if unmatched_examples:
        print("\nExamples with no SCDB match (excluded):")
        for e in unmatched_examples:
            print(f"  - {e}")

    print(f"\nWrote {total} clusters -> {raw_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--scdb", required=True)
    ap.add_argument("--parquet", default=None,
                    help="Cached SCOTUS parquet (defaults from config).")
    ap.add_argument("--year-from", type=int, default=2005)
    ap.add_argument("--year-to", type=int, default=2023)
    args = ap.parse_args()

    scdb_path = Path(args.scdb)
    if not scdb_path.exists():
        sys.exit(f"SCDB file not found: {scdb_path}")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    pq = Path(args.parquet) if args.parquet else \
        Path(cfg["paths"]["raw"]).with_suffix(".parquet")

    convert(cfg, scdb_path, pq, args.year_from, args.year_to)


if __name__ == "__main__":
    main()
