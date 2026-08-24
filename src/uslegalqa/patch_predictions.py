"""Repair missing category labels in prediction files.

Fills null `category` fields by joining on cluster_id against the cleaned
corpus. No API calls are made.

Usage:
    python -m uslegalqa.patch_predictions --dry-run
    python -m uslegalqa.patch_predictions
    python -m uslegalqa.patch_predictions --preds data/predictions/b1.jsonl
"""

from __future__ import annotations

import argparse
import json
import shutil
from collections import Counter
from pathlib import Path

import yaml


def load_category_index(cleaned: Path) -> dict[int, str]:
    """cluster_id -> issue area, from the cleaned corpus."""
    index: dict[int, str] = {}
    for line in cleaned.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        cat = rec.get("category") or rec.get("scdb_category")
        if cat:
            index[rec["cluster_id"]] = cat
    return index


def patch(path: Path, index: dict[int, str], dry_run: bool) -> dict:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    before = Counter(r.get("category") or "unknown" for r in records)
    filled = unresolved = 0

    for rec in records:
        if rec.get("category"):
            continue
        cat = index.get(rec.get("cluster_id"))
        if cat:
            rec["category"] = cat
            filled += 1
        else:
            unresolved += 1

    if not dry_run and filled:
        backup = path.with_suffix(path.suffix + ".bak")
        if not backup.exists():
            shutil.copy2(path, backup)
        with path.open("w", encoding="utf-8") as f:
            for rec in records:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")

    after = Counter(r.get("category") or "unknown" for r in records)
    return {"n": len(records), "filled": filled, "unresolved": unresolved,
            "before_unknown": before.get("unknown", 0),
            "after_unknown": after.get("unknown", 0),
            "categories": after}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--preds", action="append", default=None,
                    help="Prediction file. Repeat, or omit to patch them all.")
    ap.add_argument("--predictions-dir", default="data/predictions")
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    cleaned = Path(cfg["paths"]["cleaned"])
    if not cleaned.exists():
        raise SystemExit(f"cleaned corpus not found: {cleaned}")

    index = load_category_index(cleaned)
    print(f"{len(index)} opinions carry an issue area\n")

    paths = ([Path(p) for p in args.preds] if args.preds
             else sorted(Path(args.predictions_dir).glob("*.jsonl")))
    if not paths:
        raise SystemExit("no prediction files found")

    for path in paths:
        if not path.exists():
            print(f"{path.name}: not found")
            continue
        r = patch(path, index, args.dry_run)
        print(f"{path.name}: {r['n']} records, "
              f"{r['before_unknown']} unknown -> {r['after_unknown']} "
              f"({r['filled']} filled)")
        if r["unresolved"]:
            print(f"  {r['unresolved']} could not be resolved "
                  "(cluster_id absent from the corpus)")
        if r["after_unknown"] == 0:
            top = [f"{c} {n}" for c, n in r["categories"].most_common(4)]
            print(f"  {', '.join(top)}")

    if args.dry_run:
        print("\n[dry run] nothing written.")
    else:
        print("\nRe-score with:\n"
              "  python -m uslegalqa.evaluate --preds data/predictions/b1.jsonl "
              "--breakdowns")


if __name__ == "__main__":
    main()
