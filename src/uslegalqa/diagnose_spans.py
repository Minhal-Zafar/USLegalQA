"""Capture and classify rejected spans.

Classes: fabricated, paraphrase, cross_chunk (text from outside this window),
near_miss (a small edit), and matcher_gap (verbatim but rejected).

Usage:
    python -m uslegalqa.diagnose_spans --limit 5
"""

from __future__ import annotations

import argparse
import difflib
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from .chunking import chunk_opinion
from .generate import (
    build_prompt, call_model, locate_span, normalise, QUESTION_TYPES,
)

from .generate import _words


def tokens(text: str) -> list[str]:
    """Same tokenisation the matcher uses, so classes agree with decisions."""
    return _words(text)


def classify(span: str, chunk_text: str, full_text: str) -> tuple[str, float]:
    """Return (class, best_overlap_ratio) for a span that failed to locate."""
    span_toks = tokens(span)
    if not span_toks:
        return "empty", 0.0

    # Present elsewhere in the opinion but not in this window?
    if locate_span(span, full_text) is not None:
        return "cross_chunk", 1.0

    chunk_toks = tokens(chunk_text)
    if len(span_toks) > len(chunk_toks):
        return "span_exceeds_chunk", 0.0

    # Best contiguous match against the chunk, via difflib on the token stream.
    matcher = difflib.SequenceMatcher(None, span_toks, chunk_toks, autojunk=False)
    matched = sum(b.size for b in matcher.get_matching_blocks())
    ratio = matched / len(span_toks)

    if ratio >= 0.99:
        return "matcher_gap", ratio
    if ratio >= 0.90:
        return "near_miss", ratio
    if ratio >= 0.75:
        return "near_miss", ratio
    if ratio >= 0.40:
        return "paraphrase", ratio
    return "fabricated", ratio


def run(cfg: dict, limit: int, out_path: Path) -> None:
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic is required:  pip install anthropic")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    client = anthropic.Anthropic(api_key=api_key)

    g = cfg["generate"]
    records = [json.loads(l) for l in
               Path(cfg["paths"]["cleaned"]).read_text(encoding="utf-8").splitlines()
               if l.strip()][:limit]

    classes: Counter = Counter()
    examples: dict[str, list] = {}
    total = failed = 0

    for rec in records:
        chunks = chunk_opinion(rec["text"], rec["cluster_id"],
                               target_words=g["chunk_words"],
                               overlap_words=g["chunk_overlap"])
        print(f"{rec['case_name'][:56]}  ({len(chunks)} chunks)")

        for chunk in chunks:
            prompt = build_prompt(rec, chunk, g["pairs_per_chunk"])
            for pair in call_model(client, g["model"], prompt,
                                   g["max_tokens"], g["temperature"]):
                total += 1
                span = (pair.get("supporting_span") or "").strip()
                if locate_span(span, chunk.text) is not None:
                    continue

                failed += 1
                kind, ratio = classify(span, chunk.text, rec["text"])
                classes[kind] += 1
                examples.setdefault(kind, [])
                if len(examples[kind]) < 12:
                    entry = {
                        "case": rec["case_name"],
                        "chunk": f"{chunk.chunk_index + 1}/{chunk.n_chunks}",
                        "overlap": round(ratio, 2),
                        "span_full": span,
                        "span_len": len(span),
                        "question": pair.get("question") or "",
                    }
                    # Capture where the two character streams diverge.
                    from .generate import _char_stream
                    sc, _ = _char_stream(span)
                    cc, cmap = _char_stream(chunk.text)
                    entry["char_span_len"] = len(sc)
                    best_i, best_n = -1, 0
                    for probe in range(20, min(len(sc), 400), 10):
                        at = cc.find(sc[:probe])
                        if at < 0:
                            break
                        best_i, best_n = at, probe
                    if best_i >= 0 and best_n < len(sc):
                        j = best_i + best_n
                        entry["matched_prefix_chars"] = best_n
                        entry["diverge_span"] = sc[max(0, best_n - 40):best_n + 40]
                        entry["diverge_chunk"] = cc[max(0, j - 40):j + 40]
                        orig = cmap[j] if j < len(cmap) else len(chunk.text)
                        entry["diverge_source_text"] = repr(
                            chunk.text[max(0, orig - 60):orig + 60])
                    else:
                        entry["matched_prefix_chars"] = best_n
                        entry["note"] = ("no prefix matched" if best_i < 0
                                         else "full prefix matched")
                    examples[kind].append(entry)

    print(f"\n{failed} of {total} spans failed to locate "
          f"({100*failed/max(total,1):.1f}%)")
    for kind, n in classes.most_common():
        print(f"  {kind:<16} {n:>4}  {100*n/max(failed,1):>5.1f}% of failures")

    fabricated = classes["fabricated"] + classes["paraphrase"]
    print(f"\nTrue generator failure (fabricated + paraphrase): "
          f"{fabricated} = {100*fabricated/max(total,1):.1f}% of all candidates")
    if classes["matcher_gap"]:
        print(f"MATCHER GAP: {classes['matcher_gap']} spans are effectively "
              f"verbatim but were rejected -- these are recoverable.")

    for kind, items in examples.items():
        print(f"\n--- {kind} ---")
        for e in items[:6]:
            print(f"\n  [{e['case'][:34]} {e['chunk']}] overlap={e['overlap']} "
                  f"span_len={e.get('span_len')} matched="
                  f"{e.get('matched_prefix_chars')}/{e.get('char_span_len')} chars")
            if "diverge_span" in e:
                print(f"    span  ...{e['diverge_span']}")
                print(f"    chunk ...{e['diverge_chunk']}")
                print(f"    source: {e.get('diverge_source_text','')[:150]}")
            elif e.get("note"):
                print(f"    {e['note']}")

    out_path.write_text(json.dumps(
        {"total": total, "failed": failed, "classes": dict(classes),
         "examples": examples}, indent=2), encoding="utf-8")
    print(f"\nWritten to {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--limit", type=int, default=5)
    ap.add_argument("--out", default="data/dataset/span_diagnosis.json")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    run(cfg, args.limit, out)


if __name__ == "__main__":
    main()
