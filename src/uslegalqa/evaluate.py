"""Score system predictions against the USLegalQA test set.

Reports ROUGE (F1, precision, recall) and raw and rescaled BERTScore with
bootstrap CIs, a corpus floor (each prediction scored against an unrelated
reference from the same test set), and paired bootstrap comparisons.

Input: JSONL, one object per test item, with at least:
    {"cluster_id": ..., "question": ..., "answer": <reference>,
     "prediction": <system output>, "question_type": ..., "category": ...,
     "system": "<system name>"}

Usage:
    pip install rouge-score bert-score
    python -m uslegalqa.evaluate --preds preds/b1_closed_book.jsonl \\
                                 --preds preds/b2_open_book.jsonl \\
                                 --preds preds/f1_finetuned.jsonl \\
                                 --reference b2_open_book
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import defaultdict
from pathlib import Path
from typing import Any

import numpy as np

METRICS = ("rouge1_f", "rouge1_p", "rouge1_r", "rougeL_f",
           "bertscore_raw", "bertscore_rescaled")


def load(path: Path) -> list[dict]:
    records = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                records.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not records:
        sys.exit(f"{path} contains no usable records")
    missing = [f for f in ("answer", "prediction") if f not in records[0]]
    if missing:
        sys.exit(f"{path}: records are missing {missing}")
    return records


def item_key(rec: dict) -> tuple:
    """Identity of a test item, for aligning systems."""
    return (rec.get("cluster_id"), rec.get("question"))


def rouge_scores(refs: list[str], hyps: list[str]) -> dict[str, np.ndarray]:
    try:
        from rouge_score import rouge_scorer
    except ImportError:
        sys.exit("rouge-score is required:  pip install rouge-score")

    scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
    out = {k: [] for k in ("rouge1_f", "rouge1_p", "rouge1_r", "rougeL_f")}
    for ref, hyp in zip(refs, hyps):
        s = scorer.score(ref, hyp)
        out["rouge1_f"].append(s["rouge1"].fmeasure)
        out["rouge1_p"].append(s["rouge1"].precision)
        out["rouge1_r"].append(s["rouge1"].recall)
        out["rougeL_f"].append(s["rougeL"].fmeasure)
    return {k: np.array(v) for k, v in out.items()}


def bert_scores(refs: list[str], hyps: list[str], rescale: bool,
                batch_size: int) -> np.ndarray:
    try:
        from bert_score import score as bs
    except ImportError:
        sys.exit("bert-score is required:  pip install bert-score")
    _, _, f1 = bs(hyps, refs, lang="en", rescale_with_baseline=rescale,
                  batch_size=batch_size, verbose=False)
    return f1.numpy()


def bootstrap_ci(values: np.ndarray, n_boot: int = 2000,
                 alpha: float = 0.05, seed: int = 0) -> dict:
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"mean": float("nan"), "ci95": [float("nan")] * 2, "n": 0}
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    lo, hi = np.percentile(means, [100 * alpha / 2, 100 * (1 - alpha / 2)])
    return {"mean": round(float(values.mean()), 4),
            "ci95": [round(float(lo), 4), round(float(hi), 4)],
            "n": n}


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int = 2000,
                     seed: int = 0) -> dict:
    """Compare two systems on the SAME items.

    Pairing removes the item-difficulty variance the systems share, which
    independent confidence intervals would ignore.
    """
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    n = len(d)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    p_better = float((means > 0).mean())
    return {
        "mean_difference": round(float(d.mean()), 4),
        "ci95": [round(float(np.percentile(means, 2.5)), 4),
                 round(float(np.percentile(means, 97.5)), 4)],
        # Two-sided bootstrap p-value.
        "p_value": round(2 * min(p_better, 1 - p_better), 4),
    }


def diagnostics(refs: list[str], hyps: list[str]) -> dict:
    """Detect degenerate output (empty, runaway or duplicated predictions)."""
    ref_len = np.array([len(r.split()) for r in refs])
    hyp_len = np.array([len(h.split()) for h in hyps])
    empty = int((hyp_len == 0).sum())
    notes = []
    if empty:
        notes.append(f"{empty} empty predictions")
    ratio = float(hyp_len.mean() / max(ref_len.mean(), 1e-9))
    if ratio > 2.0:
        notes.append(f"predictions average {ratio:.1f}x reference length "
                     "-- check the end-of-sequence token")
    elif ratio < 0.5:
        notes.append(f"predictions average {ratio:.1f}x reference length "
                     "-- output may be truncated")
    dupes = len(hyps) - len(set(hyps))
    if dupes > len(hyps) * 0.1:
        notes.append(f"{dupes} duplicate predictions -- possible mode collapse")
    return {
        "empty_predictions": empty,
        "mean_prediction_words": round(float(hyp_len.mean()), 1),
        "mean_reference_words": round(float(ref_len.mean()), 1),
        "length_ratio": round(ratio, 2),
        "duplicate_predictions": dupes,
        "warnings": notes,
    }


def score_system(records: list[dict], batch_size: int, seed: int,
                 with_floor: bool) -> tuple[dict, dict]:
    refs = [r["answer"] for r in records]
    hyps = [r.get("prediction") or "" for r in records]

    per_item: dict[str, np.ndarray] = {}
    per_item.update(rouge_scores(refs, hyps))
    per_item["bertscore_raw"] = bert_scores(refs, hyps, False, batch_size)
    per_item["bertscore_rescaled"] = bert_scores(refs, hyps, True, batch_size)

    report: dict[str, Any] = {
        "n": len(records),
        "overall": {m: bootstrap_ci(per_item[m], seed=seed) for m in METRICS},
        "diagnostics": diagnostics(refs, hyps),
    }

    report["by"] = {}
    for field in ("question_type", "category"):
        groups: dict[str, list[int]] = defaultdict(list)
        for i, r in enumerate(records):
            groups[r.get(field) or "unknown"].append(i)
        report["by"][field] = {
            g: {"n": len(idx),
                **{m: bootstrap_ci(per_item[m][idx], seed=seed) for m in
                   ("rouge1_f", "bertscore_rescaled")}}
            for g, idx in sorted(groups.items())
        }

    if with_floor:
        # Floor: score each prediction against a different reference from the
        # same test set, i.e. what an unrelated in-domain answer scores.
        rng = random.Random(seed)
        shuffled = refs[:]
        for _ in range(10):
            rng.shuffle(shuffled)
            if all(a != b for a, b in zip(shuffled, refs)):
                break
        floor_rouge = rouge_scores(shuffled, hyps)
        report["floor"] = {
            "note": ("each prediction scored against an unrelated reference "
                     "from the same test set"),
            "rouge1_f": bootstrap_ci(floor_rouge["rouge1_f"], seed=seed),
            "bertscore_raw": bootstrap_ci(
                bert_scores(shuffled, hyps, False, batch_size), seed=seed),
            "bertscore_rescaled": bootstrap_ci(
                bert_scores(shuffled, hyps, True, batch_size), seed=seed),
        }

    return report, per_item


def fmt(ci: dict) -> str:
    return f"{ci['mean']:.4f} [{ci['ci95'][0]:.4f}, {ci['ci95'][1]:.4f}]"


def print_report(name: str, report: dict) -> None:
    print(f"\n{name}   (n = {report['n']})")

    print(f"  {'metric':<24}{'mean [95% CI]':<30}{'floor':>16}")
    floor = report.get("floor", {})
    for m in METRICS:
        line = f"  {m:<24}{fmt(report['overall'][m]):<30}"
        if m in floor:
            line += f"{floor[m]['mean']:>16.4f}"
        print(line)

    if floor:
        headline = report["overall"]["bertscore_rescaled"]["mean"]
        base = floor["bertscore_rescaled"]["mean"]
        print(f"\n  rescaled BERTScore is {headline - base:+.4f} above the "
              f"corpus floor")

    p = report["overall"]["rouge1_p"]["mean"]
    r = report["overall"]["rouge1_r"]["mean"]
    if r > 0 and p / max(r, 1e-9) < 0.6:
        print(f"  ROUGE-1 precision ({p:.3f}) far below recall ({r:.3f}): "
              "output is verbose relative to the reference")

    d = report["diagnostics"]
    print(f"\n  prediction length {d['mean_prediction_words']} words vs "
          f"reference {d['mean_reference_words']} (ratio {d['length_ratio']})")
    for w in d["warnings"]:
        print(f"  WARNING: {w}")


def print_breakdown(name: str, report: dict, field: str) -> None:
    print(f"\n  {name} by {field}:")
    print(f"    {'group':<24}{'n':>7}{'ROUGE-1 F':>12}{'BERTScore':>12}")
    for g, s in report["by"][field].items():
        print(f"    {g:<24}{s['n']:>7}{s['rouge1_f']['mean']:>12.4f}"
              f"{s['bertscore_rescaled']['mean']:>12.4f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preds", action="append", required=True,
                    help="Prediction file. Repeat for each system.")
    ap.add_argument("--reference", default=None,
                    help="System name to compare others against in paired tests.")
    ap.add_argument("--out", default="data/results/evaluation.json")
    ap.add_argument("--batch-size", type=int, default=32)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--no-floor", action="store_true",
                    help="Skip the floor control (faster, but scores lose "
                         "their reference point).")
    ap.add_argument("--breakdowns", action="store_true",
                    help="Print per-question-type and per-category tables.")
    args = ap.parse_args()

    results: dict[str, dict] = {}
    per_item: dict[str, dict] = {}
    keys: dict[str, list] = {}

    for path_str in args.preds:
        path = Path(path_str)
        records = load(path)
        name = records[0].get("system") or path.stem
        print(f"[scoring] {name}: {len(records)} items from {path.name}")
        report, items = score_system(records, args.batch_size, args.seed,
                                     not args.no_floor)
        results[name] = report
        per_item[name] = items
        keys[name] = [item_key(r) for r in records]

    for name in results:
        print_report(name, results[name])
        if args.breakdowns:
            print_breakdown(name, results[name], "question_type")
            print_breakdown(name, results[name], "category")

    names = list(results)
    ref_name = args.reference if args.reference in results else names[0]
    others = [n for n in names if n != ref_name]

    if others:
        print(f"\nPAIRED COMPARISONS vs {ref_name}")
        comparisons: dict[str, dict] = {}
        for other in others:
            if keys[other] != keys[ref_name]:
                print(f"  {other}: SKIPPED -- evaluated on different items. "
                      "Paired testing requires identical test sets.")
                comparisons[other] = {"skipped": "test items not aligned"}
                continue
            comparisons[other] = {}
            print(f"\n  {other} - {ref_name}")
            for m in ("rouge1_f", "bertscore_rescaled"):
                res = paired_bootstrap(per_item[other][m], per_item[ref_name][m],
                                       seed=args.seed)
                comparisons[other][m] = res
                sig = "significant" if res["p_value"] < 0.05 else "not significant"
                print(f"    {m:<22}{res['mean_difference']:+.4f} "
                      f"[{res['ci95'][0]:+.4f}, {res['ci95'][1]:+.4f}]  "
                      f"p={res['p_value']:.3f}  ({sig})")
        results["_paired_vs_" + ref_name] = comparisons

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
