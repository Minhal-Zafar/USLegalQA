"""Demonstrate that every answer is grounded in its source opinion.

Checks that stored offsets resolve to each pair's supporting span across the
whole dataset, then displays a few worked examples.

Usage:
    python -m uslegalqa.show_grounding
    python -m uslegalqa.show_grounding --n 5 --seed 7
    python -m uslegalqa.show_grounding --case "Roper"
"""

from __future__ import annotations

import argparse
import json
import random
import re
from pathlib import Path

_ALNUM = re.compile(r"[a-z0-9\u00a7]")

# Reuse the pipeline's artefact stripping so this check agrees with the verifier.
try:
    from .generate import _strip_footnote_markers as _strip
except ImportError:  # pragma: no cover
    _STAR = re.compile(r"\*\s?\d{1,4}|\[\s?\d{1,4}\s?\]")
    _FOOT = re.compile(r"(?<=[.,;:\u201d\"'])\d{1,3}(?=\s|$)")

    def _strip(text: str) -> str:
        return _STAR.sub(" ", _FOOT.sub(" ", text or ""))


def stream(text: str) -> str:
    """Letters and digits only, lowercased, with publication artefacts removed."""
    return "".join(_ALNUM.findall(_strip(text or "").lower()))


def case_matches(query: str, *names: str) -> bool:
    """Match a case name on whole words ("Roper" must not match "Property")."""
    hay = " ".join(n or "" for n in names).lower()
    words = re.findall(r"\w+", query.lower())
    return bool(words) and all(
        re.search(r"\b" + re.escape(w) + r"\b", hay) for w in words)


def load_jsonl(path: Path) -> list[dict]:
    out = []
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    return out


def check(pair: dict, opinion_text: str) -> tuple[str, str]:
    """Classify how the stored offsets relate to the source opinion.

    Returns (status, sliced_text). Status is one of:
      exact     the slice at [span_start:span_end] is the supporting span
      located   the slice differs only in spacing or punctuation
      found     the offsets do not point at it, but the span is in the opinion
      missing   the span cannot be found in the opinion at all
    """
    span = pair.get("supporting_span") or ""
    s, e = pair.get("span_start"), pair.get("span_end")
    sliced = ""
    if isinstance(s, int) and isinstance(e, int) and 0 <= s < e <= len(opinion_text):
        sliced = opinion_text[s:e]
        if sliced == span:
            return "exact", sliced
        if stream(sliced) and stream(span) and (
                stream(span) in stream(sliced) or stream(sliced) in stream(span)):
            return "located", sliced
    if stream(span) and stream(span)[:200] in stream(opinion_text):
        return "found", sliced
    return "missing", sliced


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="data/dataset/uslegalqa_v3_final.jsonl")
    ap.add_argument("--opinions", default="data/cleaned/opinions.jsonl")
    ap.add_argument("--n", type=int, default=3, help="Examples to display.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--case", default=None, help="Only show pairs from this case.")
    args = ap.parse_args()

    pairs = load_jsonl(Path(args.dataset))
    opinions = {o["cluster_id"]: o for o in load_jsonl(Path(args.opinions))}
    print(f"{len(pairs):,} pairs, {len(opinions):,} opinions\n")

    # --- whole dataset check ---
    counts = {"exact": 0, "located": 0, "found": 0, "missing": 0, "no opinion": 0}
    for p in pairs:
        op = opinions.get(p.get("cluster_id"))
        if op is None:
            counts["no opinion"] += 1
            continue
        counts[check(p, op.get("text", ""))[0]] += 1

    total = len(pairs)
    print("WHOLE DATASET")
    labels = {
        "exact": "offsets point exactly at the span",
        "located": "offsets point at it (spacing/punctuation differs)",
        "found": "span is in the opinion, offsets point elsewhere",
        "missing": "span not found in the opinion",
        "no opinion": "source opinion not in corpus",
    }
    for k, v in counts.items():
        print(f"  {labels[k]:<52} {v:>6}  {100*v/max(total,1):5.1f}%")
    grounded = counts["exact"] + counts["located"] + counts["found"]
    print(f"\n  grounded in source opinion: {grounded:,} of {total:,} "
          f"({100*grounded/max(total,1):.1f}%)")

    # Span/answer length ratio: a short span anchors an answer without
    # necessarily justifying all of it.
    ratios, thin = [], 0
    for p in pairs:
        a = len((p.get("answer") or "").split())
        sp = len((p.get("supporting_span") or "").split())
        if a:
            r = sp / a
            ratios.append(r)
            if r < 0.5:
                thin += 1
    if ratios:
        ratios.sort()
        q = lambda f: ratios[int(len(ratios) * f)]
        print("\n  Span length relative to answer length (words):")
        print(f"    p10 {q(0.10):.2f}   median {q(0.50):.2f}   "
              f"p90 {q(0.90):.2f}   mean {sum(ratios)/len(ratios):.2f}")
        print(f"    spans shorter than half their answer: {thin:,} "
              f"({100*thin/len(ratios):.1f}%)")
    if counts["found"] > total * 0.05:
        print("\n  NOTE: many offsets do not point at the span. They may be stored")
        print("  relative to the generation window rather than the full opinion.")

    # --- worked examples ---
    pool = pairs
    if args.case:
        pool = [p for p in pairs
                if case_matches(args.case, p.get("case_name"),
                                opinions.get(p.get("cluster_id"), {}).get("case_name"))]
        if not pool:
            print(f"\nNo pairs found for case matching {args.case!r}")
            return
    rng = random.Random(args.seed)
    sample = rng.sample(pool, min(args.n, len(pool)))

    for i, p in enumerate(sample, 1):
        op = opinions.get(p.get("cluster_id"), {})
        text = op.get("text", "")
        status, sliced = check(p, text)
        s, e = p.get("span_start"), p.get("span_end")
        print(f"\nEXAMPLE {i}: {op.get('case_name', p.get('case_name', '?'))}  "
              f"[{p.get('question_type')}, {p.get('category')}]")
        print(f"QUESTION\n  {p.get('question')}\n")
        print(f"ANSWER\n  {p.get('answer')}\n")
        print(f"SUPPORTING SPAN (stored with the answer)\n  {p.get('supporting_span')}\n")
        print(f"OPINION TEXT at characters {s} to {e} of {len(text):,}")
        print(f"  {sliced[:600] if sliced else '(offsets do not resolve)'}\n")
        print(f"RESULT: {labels.get(status, status)}")


if __name__ == "__main__":
    main()
