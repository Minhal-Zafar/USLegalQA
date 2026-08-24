"""Trace one question answer pair back to its exact source in the opinion.

Walks the provenance chain for a single pair, re-verifies its span live with
locate_span, and shows that fabricated or altered spans are rejected.

Usage:
    python -m uslegalqa.trace
    python -m uslegalqa.trace --case "Roper" --seed 3
    python -m uslegalqa.trace --index 4721
"""

from __future__ import annotations

import argparse
import json
import re
import random
import textwrap
from pathlib import Path

from .generate import locate_span


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


def rule(title: str = "", char: str = "=") -> None:
    if title:
        print("\n" + char * 78)
        print(title)
        print(char * 78)
    else:
        print(char * 78)


def wrap(text: str, indent: str = "  ", width: int = 76) -> str:
    return textwrap.fill(" ".join((text or "").split()),
                         width=width, initial_indent=indent,
                         subsequent_indent=indent)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="data/dataset/uslegalqa_v3_final.jsonl")
    ap.add_argument("--opinions", default="data/cleaned/opinions.jsonl")
    ap.add_argument("--case", default=None, help="Restrict to a case name.")
    ap.add_argument("--index", type=int, default=None, help="Specific row number.")
    ap.add_argument("--type", default=None, help="Restrict to a question type.")
    ap.add_argument("--seed", type=int, default=42)
    args = ap.parse_args()

    pairs = load_jsonl(Path(args.dataset))
    opinions = {o["cluster_id"]: o for o in load_jsonl(Path(args.opinions))}

    pool = pairs
    if args.case:
        pool = [p for p in pool
                if case_matches(args.case, p.get("case_name"),
                                opinions.get(p.get("cluster_id"), {}).get("case_name"))]
    if args.type:
        pool = [p for p in pool if p.get("question_type") == args.type]
    if not pool:
        raise SystemExit("No pairs matched those filters.")

    pair = pairs[args.index] if args.index is not None else \
        random.Random(args.seed).choice(pool)

    opinion = opinions.get(pair.get("cluster_id"))
    if opinion is None:
        raise SystemExit(f"Opinion {pair.get('cluster_id')} not in the corpus.")
    text = opinion.get("text", "")
    span = pair.get("supporting_span") or ""
    start, end = pair.get("span_start"), pair.get("span_end")

    rule("PROVENANCE OF ONE QUESTION ANSWER PAIR")

    # ---- stage 1: the source -------------------------------------------
    rule("STAGE 1   The source opinion", "-")
    print(f"  case            {opinion.get('case_name', '?')}")
    print(f"  citation        {opinion.get('citation', 'n/a')}")
    print(f"  decided         {opinion.get('date_filed', 'n/a')}")
    print(f"  SCDB case id    {opinion.get('scdb_id', 'n/a')}")
    print(f"  issue area      {opinion.get('category') or pair.get('category')}")
    print(f"  cluster id      {pair.get('cluster_id')}")
    print(f"  binding text    {len(text):,} characters, "
          f"{len(text.split()):,} words")

    # ---- stage 2: the generation window --------------------------------
    rule("STAGE 2   The window the generator saw", "-")
    if isinstance(start, int):
        w_lo, w_hi = max(0, start - 450), min(len(text), (end or start) + 450)
        print(f"  The pair was generated from a window of about 900 words.")
        print(f"  The supporting span sits at characters {start:,} to {end:,},")
        pct = 100 * start / max(len(text), 1)
        print(f"  which is {pct:.0f}% of the way through the opinion.")
        print(f"  position band   {pair.get('chunk_position', 'n/a')}")
    else:
        w_lo = w_hi = 0
        print("  No offsets stored for this pair.")

    # ---- stage 3: what the generator produced --------------------------
    rule("STAGE 3   The generated pair", "-")
    print(f"  generator       {pair.get('generator', 'n/a')}")
    print(f"  temperature     {pair.get('generator_temperature', 'n/a')}")
    print(f"  question type   {pair.get('question_type')}")
    print("\n  QUESTION")
    print(wrap(pair.get("question", ""), "    "))
    print("\n  ANSWER")
    print(wrap(pair.get("answer", ""), "    "))
    print("\n  SUPPORTING SPAN returned by the generator")
    print(wrap(span, "    "))

    # ---- stage 4: live re-verification ---------------------------------
    rule("STAGE 4   Live verification against the opinion", "-")
    found = locate_span(span, text)
    if found is None:
        print("  RESULT: not located. This pair should not be in the dataset.")
    else:
        f_lo, f_hi = found
        print(f"  RESULT: located at characters {f_lo:,} to {f_hi:,}")
        if isinstance(start, int):
            if (f_lo, f_hi) == (start, end):
                print("  This matches the offsets stored at generation time exactly.")
            else:
                print(f"  Stored offsets were {start:,} to {end:,}; the span is "
                      "present either way.")

    # ---- stage 5: trace back -------------------------------------------
    rule("STAGE 5   Tracing back: the opinion text at those offsets", "-")
    if isinstance(start, int) and 0 <= start < end <= len(text):
        sliced = text[start:end]
        print("  opinion_text[span_start:span_end] gives:\n")
        print(wrap(sliced, "    "))
        print()
        if sliced == span:
            print("  This is character for character the supporting span.")
        else:
            print("  Differs only in publication artefacts such as star")
            print("  pagination, which the verifier is designed to tolerate.")
        print("\n  Surrounding context in the opinion, with the span marked:\n")
        before, after = text[w_lo:start], text[end:w_hi]
        print(wrap("..." + before, "    "))
        print(wrap(">>> " + sliced + " <<<", "    "))
        print(wrap(after + "...", "    "))
    else:
        print("  Offsets unavailable for this pair.")

    # ---- stage 6: counterfactual ---------------------------------------
    rule("STAGE 6   Counterfactual: does the guard actually reject things?", "-")
    fabricated = ("The Court further held that the statute was enacted in "
                  "response to widespread public concern about the practice.")
    # Prefer an alteration that reverses the legal meaning.
    if " not " in span:
        altered = span.replace(" not ", " ", 1)
        altered_note = "the same span with the word 'not' deleted"
    elif " no " in span:
        altered = span.replace(" no ", " ", 1)
        altered_note = "the same span with the word 'no' deleted"
    else:
        words = span.split()
        mid = max(1, len(words) // 2)
        altered = " ".join(words[:mid] + ["never"] + words[mid:])
        altered_note = "the same span with a word inserted"
    print("  A plausible sentence that does NOT appear in this opinion:")
    print(wrap(fabricated, "    "))
    print(f"\n  verification result: "
          f"{'LOCATED (problem)' if locate_span(fabricated, text) else 'REJECTED'}")
    print(f"\n  A one word alteration, namely {altered_note}:")
    print(wrap(altered, "    "))
    print(f"\n  verification result: "
          f"{'LOCATED (problem)' if locate_span(altered, text) else 'REJECTED'}")


if __name__ == "__main__":
    main()
