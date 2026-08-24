"""Partition USLegalQA into train, validation and test sets by opinion.

Splitting is by opinion, not by QA pair: each opinion yields ~16 pairs, so a
pair-level split would put nearly every test opinion in training too. This
module writes the opinion-level split and measures pair-level leakage.

Usage:
    python -m uslegalqa.split --measure-leakage
    python -m uslegalqa.split
    python -m uslegalqa.split --ratios 0.8 0.1 0.1 --seed 42

The released split in data/dataset/splits/ is the v1 assignment, drawn before
SCDB categories were backfilled (audited opinions later removed); re-running now
stratifies on the backfilled labels and produces a different split.
"""

from __future__ import annotations

import argparse
import json
import random
from collections import Counter, defaultdict
from pathlib import Path

import yaml


def load_pairs(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return records


def require_categories(pairs: list[dict]) -> None:
    """Refuse to stratify on missing labels."""
    missing = {p["cluster_id"] for p in pairs if not p.get("category")}
    if missing:
        raise ValueError(
            f"{len(missing)} opinions have no issue area; run "
            f"uslegalqa.backfill_categories before splitting")


def stratified_opinion_split(pairs: list[dict], ratios: tuple[float, float, float],
                             seed: int) -> tuple[set, set, set]:
    """Assign opinions to splits, stratified by SCDB issue area.

    Categories with too few opinions to divide are assigned to training.
    """
    by_opinion: dict[int, str] = {}
    for p in pairs:
        by_opinion.setdefault(p["cluster_id"], p.get("category") or "uncoded")

    buckets: dict[str, list[int]] = defaultdict(list)
    for cid, cat in by_opinion.items():
        buckets[cat].append(cid)

    rng = random.Random(seed)
    train, val, test = set(), set(), set()

    for cat in sorted(buckets):
        members = sorted(buckets[cat])
        rng.shuffle(members)
        n = len(members)
        if n < 5:
            # Too few to divide; never report test results on a tiny category.
            train.update(members)
            continue
        n_train = int(round(ratios[0] * n))
        n_val = int(round(ratios[1] * n))
        train.update(members[:n_train])
        val.update(members[n_train:n_train + n_val])
        test.update(members[n_train + n_val:])

    return train, val, test


def measure_leakage(pairs: list[dict], ratios: tuple[float, float, float],
                    seed: int, n_trials: int = 20) -> dict:
    """Compare opinion-level and pair-level splitting.

    Reports the proportion of test pairs whose source opinion also appears in
    the training set under each scheme.
    """
    rng = random.Random(seed)
    n = len(pairs)
    n_train = int(ratios[0] * n)
    n_val = int(ratios[1] * n)

    pair_level = []
    for t in range(n_trials):
        idx = list(range(n))
        random.Random(seed + t).shuffle(idx)
        train_ids = {pairs[i]["cluster_id"] for i in idx[:n_train]}
        test = [pairs[i] for i in idx[n_train + n_val:]]
        contaminated = sum(1 for p in test if p["cluster_id"] in train_ids)
        pair_level.append(contaminated / len(test))

    tr, va, te = stratified_opinion_split(pairs, ratios, seed)
    test_pairs = [p for p in pairs if p["cluster_id"] in te]
    opinion_level = sum(1 for p in test_pairs if p["cluster_id"] in tr) / max(
        len(test_pairs), 1)

    per_opinion = Counter(p["cluster_id"] for p in pairs)
    return {
        "pairs": n,
        "opinions": len(per_opinion),
        "mean_pairs_per_opinion": round(n / len(per_opinion), 1),
        "pair_level_contamination": round(sum(pair_level) / len(pair_level), 4),
        "pair_level_trials": n_trials,
        "opinion_level_contamination": round(opinion_level, 4),
    }


def describe(name: str, pairs: list[dict], opinions: set) -> dict:
    types = Counter(p.get("question_type") for p in pairs)
    cats = Counter(p.get("category") or "uncoded" for p in pairs)
    return {
        "split": name,
        "pairs": len(pairs),
        "opinions": len(opinions),
        "question_types": dict(types.most_common()),
        "categories": dict(cats.most_common()),
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--outdir", default="data/dataset/splits")
    ap.add_argument("--ratios", type=float, nargs=3, default=[0.8, 0.1, 0.1])
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--measure-leakage", action="store_true",
                    help="Report the leakage comparison and exit.")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    # Use the deduplicated, backfilled release, not raw generation output.
    path = Path(args.dataset) if args.dataset else Path(cfg["generate"]["final"])
    pairs = load_pairs(path)
    ratios = tuple(args.ratios)

    print(f"Loaded {len(pairs):,} pairs from {path}\n")

    print("LEAKAGE: OPINION-LEVEL vs PAIR-LEVEL SPLITTING")
    m = measure_leakage(pairs, ratios, args.seed)
    print(f"  pairs per opinion (mean)      {m['mean_pairs_per_opinion']}")
    print(f"  pair-level contamination      "
          f"{100 * m['pair_level_contamination']:.1f}%  "
          f"(mean of {m['pair_level_trials']} random splits)")
    print(f"  opinion-level contamination   "
          f"{100 * m['opinion_level_contamination']:.1f}%")

    if args.measure_leakage:
        return

    require_categories(pairs)
    train_ops, val_ops, test_ops = stratified_opinion_split(pairs, ratios, args.seed)
    splits = {
        "train": [p for p in pairs if p["cluster_id"] in train_ops],
        "val":   [p for p in pairs if p["cluster_id"] in val_ops],
        "test":  [p for p in pairs if p["cluster_id"] in test_ops],
    }
    op_sets = {"train": train_ops, "val": val_ops, "test": test_ops}

    assert not (train_ops & val_ops), "train and val share opinions"
    assert not (train_ops & test_ops), "train and test share opinions"
    assert not (val_ops & test_ops), "val and test share opinions"

    outdir = Path(args.outdir)
    outdir.mkdir(parents=True, exist_ok=True)
    for name, recs in splits.items():
        out = outdir / f"{name}.jsonl"
        with out.open("w", encoding="utf-8") as f:
            for r in recs:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    print("\nOPINION-LEVEL SPLIT")
    print(f"  {'split':<8}{'pairs':>8}{'opinions':>10}{'% pairs':>10}")
    for name in ("train", "val", "test"):
        n = len(splits[name])
        print(f"  {name:<8}{n:>8}{len(op_sets[name]):>10}"
              f"{100 * n / len(pairs):>9.1f}%")

    print("\n  Question types by split:")
    all_types = sorted({p.get("question_type") for p in pairs})
    print(f"    {'type':<18}" + "".join(f"{s:>10}" for s in ("train", "val", "test")))
    for t in all_types:
        row = f"    {t:<18}"
        for name in ("train", "val", "test"):
            c = sum(1 for p in splits[name] if p.get("question_type") == t)
            row += f"{100 * c / max(len(splits[name]), 1):>9.1f}%"
        print(row)

    report = {
        "seed": args.seed,
        "ratios": list(ratios),
        "leakage": m,
        "splits": [describe(n, splits[n], op_sets[n]) for n in ("train", "val", "test")],
    }
    (outdir / "split_report.json").write_text(
        json.dumps(report, indent=2), encoding="utf-8")

    print(f"\n  Written to {outdir}/  (train.jsonl, val.jsonl, test.jsonl, "
          f"split_report.json)")


if __name__ == "__main__":
    main()
