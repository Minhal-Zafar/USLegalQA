"""Prepare a minimal upload for running baselines on Kaggle.

Writes the test split with each item's source passage precomputed, so the
notebook needs no corpus and uses the same passage selection as local runs.

Usage:
    python -m uslegalqa.prepare_kaggle
    python -m uslegalqa.prepare_kaggle --limit 200      # smaller trial upload
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .baselines import passage_for


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--test", default="data/dataset/splits/test.jsonl")
    ap.add_argument("--outdir", default="data/kaggle_upload")
    ap.add_argument("--limit", type=int, default=None,
                    help="Include only the first N test items.")
    ap.add_argument("--window", type=int, default=1800,
                    help="Characters of context around the supporting span.")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))

    pairs = []
    for line in Path(args.test).read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if args.limit:
        pairs = pairs[:args.limit]

    opinions = {}
    for line in Path(cfg["paths"]["cleaned"]).read_text(
            encoding="utf-8").splitlines():
        if line.strip():
            try:
                rec = json.loads(line)
                opinions[rec["cluster_id"]] = rec
            except (json.JSONDecodeError, KeyError):
                continue

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    out = outdir / "test_with_passages.jsonl"

    missing = 0
    with out.open("w", encoding="utf-8") as f:
        for p in pairs:
            opinion = opinions.get(p["cluster_id"])
            if opinion is None:
                missing += 1
                continue
            f.write(json.dumps({
                "cluster_id": p["cluster_id"],
                "case_name": p.get("case_name") or opinion.get("case_name", ""),
                "date_filed": p.get("date_filed") or opinion.get("date_filed", ""),
                "question": p["question"],
                "answer": p["answer"],
                "question_type": p.get("question_type"),
                "category": p.get("category"),
                "passage": passage_for(p, opinion, window=args.window),
            }, ensure_ascii=False) + "\n")

    size_mb = out.stat().st_size / 1e6
    n_opinions = len({p["cluster_id"] for p in pairs})
    print(f"Wrote {len(pairs) - missing} items ({n_opinions} opinions) "
          f"-> {out}  [{size_mb:.1f} MB]")
    if missing:
        print(f"WARNING: {missing} test items had no matching opinion")


if __name__ == "__main__":
    main()
