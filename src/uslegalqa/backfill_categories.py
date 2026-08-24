"""Backfill SCDB issue areas into the corpus and the generated dataset.

Recovers missing issue-area labels by rejoining records to the SCDB release
on the SCDB case identifier. No API calls are made.

Usage:
    python -m uslegalqa.backfill_categories --scdb SCDB_2025_01_caseCentered_Citation.csv
    python -m uslegalqa.backfill_categories --scdb SCDB.csv --dry-run
"""

from __future__ import annotations

import argparse
import csv
import json
import shutil
import sys
from collections import Counter
from pathlib import Path

import yaml

from .scdb import ISSUE_AREAS


def load_scdb_by_id(path: Path) -> dict[str, dict]:
    """Index SCDB rows by caseId."""
    index: dict[str, dict] = {}
    with path.open(encoding="latin-1", newline="") as f:
        reader = csv.DictReader(f)
        if "caseId" not in (reader.fieldnames or []):
            sys.exit(f"{path.name} has no caseId column. Use the case-centered CSV.")
        for row in reader:
            case_id = (row.get("caseId") or "").strip()
            if not case_id:
                continue
            area = (row.get("issueArea") or "").strip()
            index[case_id] = {
                "category": ISSUE_AREAS.get(area),
                "issue_area_code": area,
                "term": row.get("term"),
                "decision_direction": row.get("decisionDirection"),
            }
    return index


def backfill_file(path: Path, key_field: str, lookup: dict,
                  dry_run: bool) -> tuple[int, int, Counter]:
    """Set `category` on every record whose key resolves. Returns counts."""
    if not path.exists():
        print(f"  {path} not found; skipping")
        return 0, 0, Counter()

    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    filled = unresolved = already = 0
    categories: Counter = Counter()

    for rec in records:
        had = bool(rec.get("category"))
        key = rec.get(key_field)
        hit = lookup.get(key) if key else None
        if hit and hit["category"]:
            rec["category"] = hit["category"]
            rec["scdb_issue_area_code"] = hit["issue_area_code"]
            if had:
                already += 1
            else:
                filled += 1
            categories[hit["category"]] += 1
        elif not rec.get("category"):
            unresolved += 1

    if not dry_run:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(path, backup)
            print(f"  backup written to {backup.name}")
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    return filled, unresolved, categories, already


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--scdb", required=True)
    ap.add_argument("--dataset", default=None,
                    help="Dataset file to repair. Defaults to the configured "
                         "generate.output, which may not be the deduplicated "
                         "final file.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Report what would change without writing.")
    args = ap.parse_args()

    scdb_path = Path(args.scdb)
    if not scdb_path.exists():
        sys.exit(f"SCDB file not found: {scdb_path}")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    cleaned = Path(cfg["paths"]["cleaned"])
    dataset = Path(args.dataset) if args.dataset else Path(cfg["generate"]["output"])

    by_id = load_scdb_by_id(scdb_path)
    print(f"SCDB: {len(by_id):,} cases indexed by caseId\n")

    # --- opinions: keyed by scdb_id ---
    print(f"Corpus  {cleaned}")
    filled, unresolved, cats, already = backfill_file(cleaned, "scdb_id", by_id,
                                                      args.dry_run)
    print(f"  {already} opinions already had a category; {filled} were MISSING "
          f"and were filled; {unresolved} unresolved")
    if cats:
        total = sum(cats.values())
        print("  issue areas:")
        for cat, n in cats.most_common():
            print(f"    {cat:<24} {n:>5}  {100*n/total:5.1f}%")

    # --- generated pairs: keyed by cluster_id, resolved via the corpus ---
    print(f"\nDataset {dataset}")
    if dataset.exists():
        cluster_to_cat: dict[int, dict] = {}
        for line in cleaned.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                rec = json.loads(line)
            except json.JSONDecodeError:
                continue
            if rec.get("category"):
                cluster_to_cat[rec["cluster_id"]] = {
                    "category": rec["category"],
                    "issue_area_code": rec.get("scdb_issue_area_code"),
                }
        p_filled, p_unresolved, p_cats, p_already = backfill_file(
            dataset, "cluster_id", cluster_to_cat, args.dry_run)
        print(f"  {p_already} pairs already had a category; {p_filled} were "
              f"MISSING and were filled; {p_unresolved} unresolved")
        if p_cats:
            total = sum(p_cats.values())
            print("  issue areas:")
            for cat, n in p_cats.most_common():
                print(f"    {cat:<24} {n:>6}  {100*n/total:5.1f}%")
    else:
        print("  not found; nothing to backfill")

    if args.dry_run:
        print("\n[dry run] nothing written. Rerun without --dry-run to apply.")
    else:
        print("\nDone. Rerun preflight to confirm.")


if __name__ == "__main__":
    main()
