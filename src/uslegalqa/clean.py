"""Clean collected clusters into one record per case, keeping only binding text.

The primary sub-opinion is selected per cluster, then segmented so that only
majority / per curiam sections are kept. The syllabus is stored separately.

Usage:
    python -m uslegalqa.clean
"""

from __future__ import annotations

import argparse
import json
import re
import unicodedata
from collections import Counter
from pathlib import Path

import yaml

from .schema import Cluster, CleanedOpinion, validate_cleaned
from .segment import (
    segment_opinion, segmentation_confident, binding_text, summarise, SYLLABUS,
)

_PAGE_MARKER = re.compile(r"\n\s*\*?\d{1,4}\s*\n")
_FOOTNOTE_MARK = re.compile(r"\[\s*[Ff]ootnote\s+\d+\s*\]")
_MULTISPACE = re.compile(r"[ \t]{2,}")
_MULTINEWLINE = re.compile(r"\n{3,}")
_CONTROL = re.compile(r"[\x00-\x08\x0b-\x0c\x0e-\x1f\x7f]")


def clean_text(text: str) -> str:
    """Normalise whitespace and strip pagination furniture.

    No character whitelist, so legal symbols (section signs etc.) survive.
    """
    text = unicodedata.normalize("NFKC", text)
    text = _CONTROL.sub("", text)
    text = _FOOTNOTE_MARK.sub(" ", text)
    text = _PAGE_MARKER.sub("\n", text)
    text = _MULTISPACE.sub(" ", text)
    text = _MULTINEWLINE.sub("\n\n", text)
    return text.strip()


def clean(cfg: dict) -> None:
    cl_cfg, paths = cfg["clean"], cfg["paths"]
    raw_path, out_path = Path(paths["raw"]), Path(paths["cleaned"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    do_segment = cl_cfg.get("segment_combined", True)
    drop_unconfident = cl_cfg.get("drop_if_unconfident", False)

    stats = Counter()
    seen: set[int] = set()
    kept: list[CleanedOpinion] = []
    primary_types = Counter()
    kind_totals = Counter()
    words_removed = 0
    unconfident_examples: list[str] = []
    dropped_examples: list[str] = []

    with raw_path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            stats["read"] += 1
            raw = json.loads(line)
            cluster = Cluster.from_dict(raw)
            # SCDB labels are not Cluster fields, so read them from the raw dict.
            scdb_category = raw.get("scdb_category")
            scdb_issue_area = raw.get("scdb_issue_area_code")
            scdb_term = raw.get("scdb_term")

            if cluster.cluster_id in seen:
                stats["duplicate_cluster"] += 1
                continue
            seen.add(cluster.cluster_id)

            primary = cluster.primary()
            if primary is None:
                stats["no_primary_opinion"] += 1
                if len(dropped_examples) < 5:
                    types = ", ".join(o.type for o in cluster.sub_opinions)
                    dropped_examples.append(f"{cluster.case_name} [{types}]")
                continue

            full = clean_text(primary.text)
            source_wc = len(full.split())
            syllabus = None
            kinds: dict = {}
            confident = True

            if do_segment:
                sections = segment_opinion(full)
                info = summarise(sections)
                kinds = info["kinds"]
                confident = segmentation_confident(sections)
                kind_totals.update(kinds)

                syl = [s.text for s in sections if s.kind == SYLLABUS]
                syllabus = clean_text(syl[0]) if syl else None

                text = binding_text(sections)
                if not text:
                    stats["no_binding_text"] += 1
                    continue

                if not confident:
                    stats["low_confidence_segmentation"] += 1
                    if len(unconfident_examples) < 8:
                        unconfident_examples.append(
                            f"{cluster.case_name[:45]} kinds={kinds}")
                    if drop_unconfident:
                        continue
            else:
                text = full

            wc = len(text.split())
            words_removed += max(0, source_wc - wc)

            if wc < cl_cfg["min_words"]:
                stats["too_short"] += 1
                continue
            if wc > cl_cfg["max_words"]:
                stats["too_long"] += 1
                continue
            if not cluster.date_filed:
                stats["missing_date"] += 1
                continue

            secondary = cluster.secondary()
            rec = CleanedOpinion(
                cluster_id=cluster.cluster_id,
                case_name=cluster.case_name,
                date_filed=cluster.date_filed,
                court=cluster.court,
                citation=cluster.citation,
                primary_type=primary.type,
                primary_author=primary.author,
                text=text,
                word_count=wc,
                n_secondary=len(secondary),
                secondary_types=[o.type for o in secondary],
                source_word_count=source_wc,
                section_kinds=kinds,
                segmentation_confident=confident,
                syllabus_text=syllabus,
                scdb_id=cluster.scdb_id,
                category=scdb_category,
            )

            problems = validate_cleaned(rec.to_dict())
            if problems:
                stats["failed_validation"] += 1
                print(f"  INVALID {cluster.case_name}: {problems}")
                continue

            primary_types[primary.type] += 1
            kept.append(rec)
            stats["kept"] += 1

    with out_path.open("w", encoding="utf-8") as out:
        for rec in kept:
            out.write(json.dumps(rec.to_dict(), ensure_ascii=False) + "\n")

    print("Cleaning summary:")
    for k, v in stats.most_common():
        print(f"  {k:<28} {v:>6}")

    if dropped_examples:
        print("\nDropped for having no primary opinion:")
        for e in dropped_examples:
            print(f"  - {e}")

    if do_segment and kind_totals:
        print("\nSections found across all documents:")
        for k, n in kind_totals.most_common():
            print(f"  {k:<40} {n:>6}")
        print(f"\nNon-binding words removed: {words_removed:,}")
        if kept:
            total_src = sum(r.source_word_count for r in kept)
            pct = 100 * words_removed / total_src if total_src else 0
            print(f"  ({pct:.1f}% of collected text was syllabus, "
                  f"concurrence or dissent)")

    if unconfident_examples:
        print(f"\nLow-confidence segmentation ({stats['low_confidence_segmentation']} "
              f"cases):")
        for e in unconfident_examples:
            print(f"  - {e}")

    if kept:
        wcs = [r.word_count for r in kept]
        years = Counter(r.date_filed[:4] for r in kept)
        n_scdb = sum(1 for r in kept if r.scdb_id)
        n_cat = sum(1 for r in kept if r.category)
        n_syl = sum(1 for r in kept if r.syllabus_text)
        print(f"\nBinding text word count: min {min(wcs)}, "
              f"median {sorted(wcs)[len(wcs)//2]}, max {max(wcs)}")
        print(f"SCDB-linked: {n_scdb}/{len(kept)} "
              f"({100*n_scdb/len(kept):.1f}%)")
        print(f"Issue area label present: {n_cat}/{len(kept)} "
              f"({100*n_cat/len(kept):.1f}%)")
        if n_cat < n_scdb:
            print("  WARNING: cases are SCDB-linked but carry no issue area.")
            print("  Run: python -m uslegalqa.backfill_categories --scdb <csv>")
        print(f"Syllabus captured: {n_syl}/{len(kept)}")
        print("\nPrimary opinion types retained:")
        for t, n in primary_types.most_common():
            print(f"  {t:<28} {n:>6}")
        print("\nYear coverage:")
        for y, n in sorted(years.items()):
            print(f"  {y}: {n}")

    print(f"\nWrote {len(kept)} opinions -> {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--no-segment", action="store_true",
                    help="Disable intra-document segmentation (not recommended).")
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.no_segment:
        cfg["clean"]["segment_combined"] = False
    clean(cfg)


if __name__ == "__main__":
    main()
