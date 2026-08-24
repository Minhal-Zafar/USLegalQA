"""Print detected section boundaries with context for specific cases.

Usage:
    python -m uslegalqa.inspect_segmentation --case "Hamdan"
    python -m uslegalqa.inspect_segmentation --low-confidence --limit 3
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yaml

from .segment import segment_opinion, segmentation_confident, summarise
from .clean import clean_text


def show(rec: dict, context: int = 110) -> None:
    text = clean_text(rec["text"]) if "text" in rec else ""
    if not text:
        subs = rec.get("sub_opinions") or []
        primary = max(subs, key=lambda s: s["word_count"]) if subs else None
        text = clean_text(primary["text"]) if primary else ""

    sections = segment_opinion(text)
    info = summarise(sections)

    print(f"\n{rec.get('case_name', '?')}  ({rec.get('date_filed', '?')})")
    print(f"confident={info['confident']}  kinds={info['kinds']}")

    for i, s in enumerate(sections):
        head = s.text[:context].replace("\n", " ")
        flag = "  <== BINDING" if s.is_binding else ""
        print(f"\n[{i}] {s.kind}  author={s.author}  "
              f"words={s.word_count}  offset={s.start}{flag}")
        print(f"    {head}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--case", default=None,
                    help="Substring of the case name to inspect.")
    ap.add_argument("--low-confidence", action="store_true",
                    help="Show cases where segmentation was not confident.")
    ap.add_argument("--limit", type=int, default=3)
    ap.add_argument("--context", type=int, default=110)
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    # Prefer raw clusters: cleaned records already have non-binding text removed.
    src = Path(cfg["paths"]["raw"])
    if not src.exists():
        src = Path(cfg["paths"]["cleaned"])

    shown = 0
    with src.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip() or shown >= args.limit:
                continue
            rec = json.loads(line)

            if args.case and args.case.lower() not in (
                    rec.get("case_name") or "").lower():
                continue

            if args.low_confidence:
                subs = rec.get("sub_opinions") or []
                if not subs:
                    continue
                primary = max(subs, key=lambda s: s["word_count"])
                if segmentation_confident(
                        segment_opinion(clean_text(primary["text"]))):
                    continue

            show(rec, args.context)
            shown += 1

    if shown == 0:
        print("No matching cases found.")


if __name__ == "__main__":
    main()
