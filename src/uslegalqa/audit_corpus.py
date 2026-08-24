"""Audit the corpus for records whose text is not the SCDB case's merits opinion.

  wrong_case   filing date far from SCDB's decision date (name-join mismatch)
  not_merits   cert-denial statements, stay writings, or non-opinions
  unsegmented  no writing header matched, so any dissent was kept as majority

Flagged opinions are excluded and listed in a report.

Usage:
    python -m uslegalqa.audit_corpus --scdb SCDB_2025_01_caseCentered_Citation.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path

import yaml

from .segment import first_separate_boundary

MAX_DATE_GAP_DAYS = 60

_NOT_MERITS = re.compile(
    r"petition for (?:a )?writ of certiorari is denied"
    r"|application for (?:a )?stay"
    r"|dissenting from the denial"
    r"|respecting the denial"
    r"|Statement of JUSTICE"
    r"|Differences exist between documents",
    re.IGNORECASE,
)


def scdb_decision_dates(path: Path) -> dict[str, datetime]:
    with path.open(encoding="latin-1", newline="") as f:
        return {row["caseId"]: datetime.strptime(row["dateDecision"], "%m/%d/%Y")
                for row in csv.DictReader(f) if row.get("dateDecision")}


def audit_record(rec: dict, decided: datetime | None) -> list[str]:
    """Reasons this record should not be in the corpus; empty if it is sound."""
    reasons = []
    if decided is not None and rec.get("date_filed"):
        filed = datetime.strptime(rec["date_filed"], "%Y-%m-%d")
        if abs((filed - decided).days) > MAX_DATE_GAP_DAYS:
            reasons.append("wrong_case")
    if _NOT_MERITS.search(rec.get("text", "")[:3000]):
        reasons.append("not_merits")
    if tuple(rec.get("section_kinds") or ()) == ("majority",) and rec.get("n_secondary"):
        reasons.append("unsegmented")
    return reasons


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--scdb", required=True)
    ap.add_argument("--dataset", default="data/dataset/uslegalqa_v3_final.jsonl",
                    help="Generated pairs to filter (the pre-audit release).")
    ap.add_argument("--out", default="data/dataset/uslegalqa_v3_audited.jsonl")
    ap.add_argument("--corpus-out", default="data/cleaned/opinions_audited.jsonl")
    ap.add_argument("--report", default="data/dataset/excluded_opinions.json")
    ap.add_argument("--trim-report", default="data/dataset/trimmed_opinions.json")
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    min_words = cfg["clean"]["min_words"]
    dates = scdb_decision_dates(Path(args.scdb))

    excluded: dict[int, dict] = {}
    trimmed: dict[int, dict] = {}
    cut_at: dict[int, int] = {}
    corpus_out = []
    for line in Path(cfg["paths"]["cleaned"]).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        rec = json.loads(line)
        reasons = audit_record(rec, dates.get(rec.get("scdb_id")))

        # Cut at the first separate writing segmentation missed; earlier
        # offsets are unchanged.
        cut = first_separate_boundary(rec["text"], binding_from_start=True)
        if cut is not None and not reasons:
            kept_words = len(rec["text"][:cut].split())
            trimmed[rec["cluster_id"]] = {
                "case_name": rec.get("case_name"), "cut_at": cut,
                "words_removed": len(rec["text"][cut:].split()),
                "words_kept": kept_words}
            if kept_words < min_words:
                reasons.append("below_min_words_after_trim")
            else:
                cut_at[rec["cluster_id"]] = cut
                rec = dict(rec, text=rec["text"][:cut].rstrip(), word_count=kept_words)

        if reasons:
            excluded[rec["cluster_id"]] = {
                "case_name": rec.get("case_name"), "scdb_id": rec.get("scdb_id"),
                "date_filed": rec.get("date_filed"), "reasons": reasons}
        else:
            corpus_out.append(json.dumps(rec, ensure_ascii=False))

    kept, dropped, past_cut = [], Counter(), Counter()
    for line in Path(args.dataset).read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        pair = json.loads(line)
        cid = pair["cluster_id"]
        if cid in excluded:
            dropped[cid] += 1
        elif cid in cut_at and pair["span_end"] > cut_at[cid]:
            past_cut[cid] += 1
        else:
            kept.append(line)

    for cid, n in dropped.items():
        excluded[cid]["pairs"] = n
    for cid, n in past_cut.items():
        trimmed[cid]["pairs_removed"] = n

    Path(args.out).write_text("\n".join(kept) + "\n", encoding="utf-8")
    Path(args.corpus_out).write_text("\n".join(corpus_out) + "\n", encoding="utf-8")
    Path(args.report).write_text(json.dumps(
        {str(k): v for k, v in excluded.items()}, indent=2), encoding="utf-8")
    Path(args.trim_report).write_text(json.dumps(
        {str(k): v for k, v in trimmed.items()}, indent=2), encoding="utf-8")

    reasons = Counter(r for v in excluded.values() for r in v["reasons"])
    print(f"Excluded {len(excluded)} opinions, {sum(dropped.values())} pairs")
    for r, n in reasons.most_common():
        print(f"  {r:<28}{n}")
    print(f"Trimmed {len(cut_at)} opinions at their first separate writing: "
          f"{sum(v['words_removed'] for k, v in trimmed.items() if k in cut_at):,} "
          f"words and {sum(past_cut.values())} pairs removed")
    print(f"Kept {len(corpus_out)} opinions, {len(kept)} pairs -> {args.out}")


if __name__ == "__main__":
    main()
