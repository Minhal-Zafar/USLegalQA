"""Score predictions with Sentence-BERT similarity and METEOR.

Complements evaluate.py. SBERT uses the model IndicLegalQA reports, for
context rather than a like-for-like comparison. Both metrics are reported
against the same corpus floor as evaluate.py.

Usage:
    pip install sentence-transformers nltk
    python -m uslegalqa.eval_sbert --preds data/predictions/b2.jsonl \\
                                   --preds data/predictions/f1_seed42.jsonl
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from pathlib import Path

import numpy as np

# The model IndicLegalQA reports using.
SBERT_MODEL = "sentence-transformers/paraphrase-MiniLM-L6-v2"


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
    return records


def bootstrap_ci(values: np.ndarray, n_boot: int = 2000, seed: int = 0) -> dict:
    values = np.asarray(values, dtype=float)
    n = len(values)
    if n == 0:
        return {"mean": float("nan"), "ci95": [float("nan")] * 2}
    rng = np.random.default_rng(seed)
    means = values[rng.integers(0, n, size=(n_boot, n))].mean(axis=1)
    return {"mean": round(float(values.mean()), 4),
            "ci95": [round(float(np.percentile(means, 2.5)), 4),
                     round(float(np.percentile(means, 97.5)), 4)]}


def paired_bootstrap(a: np.ndarray, b: np.ndarray, n_boot: int = 2000,
                     seed: int = 0) -> dict:
    d = np.asarray(a, dtype=float) - np.asarray(b, dtype=float)
    rng = np.random.default_rng(seed)
    means = d[rng.integers(0, len(d), size=(n_boot, len(d)))].mean(axis=1)
    p_better = float((means > 0).mean())
    return {"mean_difference": round(float(d.mean()), 4),
            "p_value": round(2 * min(p_better, 1 - p_better), 4)}


def sbert_similarity(model, refs: list[str], hyps: list[str],
                     batch_size: int = 64) -> np.ndarray:
    """Cosine similarity between sentence embeddings of reference and answer."""
    import torch
    e_ref = model.encode(refs, batch_size=batch_size, convert_to_tensor=True,
                         normalize_embeddings=True, show_progress_bar=False)
    e_hyp = model.encode(hyps, batch_size=batch_size, convert_to_tensor=True,
                         normalize_embeddings=True, show_progress_bar=False)
    # Embeddings are normalised, so the dot product is the cosine.
    return torch.sum(e_ref * e_hyp, dim=1).cpu().numpy()


def meteor_scores(refs: list[str], hyps: list[str]) -> np.ndarray:
    try:
        import nltk
        from nltk.translate.meteor_score import meteor_score
    except ImportError:
        sys.exit("nltk is required:  pip install nltk")
    for pkg in ("wordnet", "omw-1.4", "punkt"):
        try:
            nltk.download(pkg, quiet=True)
        except Exception:  # noqa: BLE001
            pass
    out = []
    for ref, hyp in zip(refs, hyps):
        try:
            out.append(meteor_score([ref.split()], hyp.split()))
        except Exception:  # noqa: BLE001
            out.append(0.0)
    return np.array(out)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--preds", action="append", required=True,
                    help="Prediction file. Repeat for each system.")
    ap.add_argument("--out", default="data/results/sbert_meteor.json")
    ap.add_argument("--model", default=SBERT_MODEL)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--batch-size", type=int, default=64)
    ap.add_argument("--no-meteor", action="store_true")
    args = ap.parse_args()

    try:
        from sentence_transformers import SentenceTransformer
    except ImportError:
        sys.exit("sentence-transformers is required:  "
                 "pip install sentence-transformers")

    print(f"loading {args.model}")
    model = SentenceTransformer(args.model)

    results: dict[str, dict] = {}
    per_item: dict[str, np.ndarray] = {}
    keys: dict[str, list] = {}

    for path_str in args.preds:
        path = Path(path_str)
        records = load(path)
        name = records[0].get("system") or path.stem
        refs = [r["answer"] for r in records]
        hyps = [r.get("prediction") or "" for r in records]
        print(f"[scoring] {name}: {len(records)} items")

        sims = sbert_similarity(model, refs, hyps, args.batch_size)

        # Floor: sentence embeddings score unrelated in-domain text highly,
        # so compare against predictions scored on shuffled references.
        rng = random.Random(args.seed)
        shuffled = refs[:]
        for _ in range(10):
            rng.shuffle(shuffled)
            if all(a != b for a, b in zip(shuffled, refs)):
                break
        floor = sbert_similarity(model, shuffled, hyps, args.batch_size)

        entry = {"n": len(records),
                 "sbert": bootstrap_ci(sims, seed=args.seed),
                 "sbert_floor": bootstrap_ci(floor, seed=args.seed)}
        entry["sbert_above_floor"] = round(
            entry["sbert"]["mean"] - entry["sbert_floor"]["mean"], 4)

        if not args.no_meteor:
            met = meteor_scores(refs, hyps)
            entry["meteor"] = bootstrap_ci(met, seed=args.seed)
            entry["meteor_floor"] = bootstrap_ci(
                meteor_scores(shuffled, hyps), seed=args.seed)

        results[name] = entry
        per_item[name] = sims
        keys[name] = [(r.get("cluster_id"), r.get("question")) for r in records]

    print(f"\n{'system':<22}{'SBERT':>10}{'floor':>10}{'above':>9}{'METEOR':>10}")
    for name, e in results.items():
        met = f"{e['meteor']['mean']:.4f}" if "meteor" in e else "n/a"
        print(f"{name:<22}{e['sbert']['mean']:>10.4f}"
              f"{e['sbert_floor']['mean']:>10.4f}"
              f"{e['sbert_above_floor']:>9.4f}{met:>10}")

    names = list(results)
    if len(names) > 1:
        ref_name = names[0]
        print(f"\nPaired comparisons of SBERT similarity against {ref_name}")
        for other in names[1:]:
            if keys[other] != keys[ref_name]:
                print(f"  {other}: skipped, test items not aligned")
                continue
            r = paired_bootstrap(per_item[other], per_item[ref_name],
                                 seed=args.seed)
            sig = "significant" if r["p_value"] < 0.05 else "not significant"
            print(f"  {other:<22}{r['mean_difference']:+.4f}  "
                  f"p={r['p_value']:.3f}  ({sig})")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(results, indent=2), encoding="utf-8")
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
