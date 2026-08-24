"""Collect SCOTUS opinions via CourtListener's batch citation-lookup endpoint.

SCDB supplies the target list (and issue areas); citations are resolved to
clusters in batches. `010combined` records are segmented later by segment.py.

Usage:
    python -m uslegalqa.collect_scdb --scdb SCDB_2025_01_caseCentered_Citation.csv --limit 50
    python -m uslegalqa.collect_scdb --scdb SCDB_2025_01_caseCentered_Citation.csv
"""

from __future__ import annotations

import argparse
import csv
import json
import os
import re
import sys
import time
from pathlib import Path

import requests
import yaml

from .collect import CourtListener, API_ROOT, extract_text, author_of, QuotaExhausted
from .schema import Cluster, SubOpinion
from .scdb import ISSUE_AREAS

_CITE_PARTS = re.compile(r"(\d+)\s+U\.?\s?S\.?\s+(\d+)")


def load_targets(path: Path, year_from: int, year_to: int) -> list[dict]:
    """SCDB rows in range that carry a parseable U.S. Reports citation."""
    targets, no_cite = [], 0
    with path.open(encoding="latin-1", newline="") as f:
        for row in csv.DictReader(f):
            m = re.search(r"/(\d{4})$", row.get("dateDecision") or "")
            if not m:
                continue
            year = int(m.group(1))
            if not (year_from <= year <= year_to):
                continue

            raw = (row.get("usCite") or "").replace("U. S.", "U.S.")
            cm = _CITE_PARTS.search(raw)
            if not cm:
                no_cite += 1
                continue

            area = (row.get("issueArea") or "").strip()
            targets.append({
                "scdb_id": row.get("caseId"),
                "case_name": row.get("caseName"),
                "us_cite": f"{cm.group(1)} U.S. {cm.group(2)}",
                "year": year,
                "issue_area_code": area,
                "category": ISSUE_AREAS.get(area),
                "decision_direction": row.get("decisionDirection"),
                "majority_votes": row.get("majVotes"),
                "minority_votes": row.get("minVotes"),
                "term": row.get("term"),
            })

    targets.sort(key=lambda t: (t["year"], t["us_cite"]))
    if no_cite:
        print(f"  {no_cite} SCDB cases in range have no citation yet; skipped")
    return targets


def lookup_batch(api: CourtListener, citations: list[str],
                 timeout: int = 120) -> dict[str, dict]:
    """Resolve many citations in one POST. Returns {citation: cluster}."""
    url = f"{API_ROOT}/citation-lookup/"
    text = "\n".join(citations)

    for attempt in range(api.max_retries):
        try:
            r = api.session.post(url, data={"text": text}, timeout=timeout)
        except requests.RequestException as e:
            wait = min(2 ** attempt, 60)
            print(f"    network error ({e.__class__.__name__}), retry in {wait}s",
                  file=sys.stderr)
            time.sleep(wait)
            continue

        api.n_requests += 1

        if r.status_code == 429:
            api.n_throttled += 1
            wait = int(r.headers.get("Retry-After", 60))
            if wait > api.max_wait:
                raise QuotaExhausted(
                    f"Quota exhausted; server asks for {wait}s "
                    f"({wait // 60} min). Progress is saved -- rerun to resume."
                )
            print(f"    throttled; waiting {wait}s", file=sys.stderr)
            time.sleep(wait)
            continue

        if r.status_code >= 400:
            raise RuntimeError(f"HTTP {r.status_code}: {r.text[:200]}")

        time.sleep(api.delay)
        out: dict[str, dict] = {}
        for item in r.json():
            clusters = item.get("clusters") or []
            if not clusters:
                continue
            # Prefer the entry with the most sub-opinions.
            best = max(clusters, key=lambda c: len(c.get("sub_opinions") or []))
            out[item.get("citation")] = best
        return out

    raise RuntimeError("citation-lookup: retries exhausted")


def fetch_opinions(api: CourtListener, cluster: dict) -> list[SubOpinion]:
    """Fetch every sub-opinion for a cluster in one request."""
    lean = ("id,cluster_id,type,author_str,author_id,per_curiam,"
            "extracted_by_ocr,page_count,plain_text")
    r = api.get(f"{API_ROOT}/opinions/",
                {"cluster__id": str(cluster["id"]), "fields": lean})

    subs: list[SubOpinion] = []
    for op in r.get("results") or []:
        text = extract_text(op)
        if not text:
            try:
                text = extract_text(api.get(f"{API_ROOT}/opinions/{op['id']}/"))
            except RuntimeError:
                text = ""
        if not text:
            continue
        subs.append(SubOpinion(
            opinion_id=op.get("id", -1),
            type=op.get("type") or "unknown",
            author=author_of(op),
            text=text,
            word_count=len(text.split()),
            per_curiam=bool(op.get("per_curiam", False)),
            extracted_by_ocr=bool(op.get("extracted_by_ocr", False)),
            page_count=op.get("page_count"),
        ))
    return subs


def collect(cfg: dict, token: str, scdb_path: Path, year_from: int, year_to: int,
            limit: int | None, batch_size: int, max_wait: int) -> None:
    raw_path = Path(cfg["paths"]["raw"])
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    print(f"Loading targets from {scdb_path.name} ({year_from}-{year_to})")
    targets = load_targets(scdb_path, year_from, year_to)
    print(f"  {len(targets)} cases with citations")

    done: set[str] = set()
    if raw_path.exists():
        with raw_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("scdb_id"):
                        done.add(d["scdb_id"])
                except json.JSONDecodeError:
                    continue
        if done:
            print(f"  resuming: {len(done)} already collected")

    todo = [t for t in targets if t["scdb_id"] not in done]
    if limit:
        todo = todo[:limit]

    n_batches = -(-len(todo) // batch_size)
    print(f"  fetching {len(todo)} cases: {n_batches} lookup request(s) "
          f"+ 1 request per resolved case\n")

    api = CourtListener(token, cfg["collect"]["request_delay_s"],
                        cfg["collect"]["max_retries"], cfg["collect"]["timeout_s"],
                        max_wait=max_wait)

    kept = not_found = no_text = 0
    split_records = combined_records = 0

    try:
        with raw_path.open("a", encoding="utf-8") as out:
            for bi in range(0, len(todo), batch_size):
                chunk = todo[bi:bi + batch_size]
                print(f"--- batch {bi // batch_size + 1}/{n_batches} "
                      f"({len(chunk)} citations) ---")

                resolved = lookup_batch(api, [t["us_cite"] for t in chunk],
                                        cfg["collect"]["timeout_s"])
                print(f"    resolved {len(resolved)}/{len(chunk)}")

                for t in chunk:
                    cl = resolved.get(t["us_cite"])
                    if not cl:
                        not_found += 1
                        continue

                    try:
                        subs = fetch_opinions(api, cl)
                    except QuotaExhausted:
                        raise
                    except RuntimeError as e:
                        print(f"    {t['us_cite']} opinion fetch failed: "
                              f"{str(e)[:60]}")
                        continue

                    if not subs:
                        no_text += 1
                        continue

                    if len(subs) > 1:
                        split_records += 1
                    elif subs[0].type == "010combined":
                        combined_records += 1

                    cluster = Cluster(
                        cluster_id=cl["id"],
                        case_name=(cl.get("case_name")
                                   or t["case_name"] or "").strip(),
                        date_filed=cl.get("date_filed") or "",
                        court="scotus",
                        precedential_status=cl.get("precedential_status"),
                        citation=t["us_cite"],
                        sub_opinions=subs,
                        scdb_id=t["scdb_id"],
                        scdb_decision_direction=t["decision_direction"],
                        scdb_votes_majority=t["majority_votes"],
                        scdb_votes_minority=t["minority_votes"],
                        docket_id=cl.get("docket_id"),
                        judges=cl.get("judges") or None,
                        syllabus=cl.get("syllabus") or None,
                    )
                    rec = cluster.to_dict()
                    rec["scdb_category"] = t["category"]
                    rec["scdb_issue_area_code"] = t["issue_area_code"]
                    rec["scdb_term"] = t["term"]

                    out.write(json.dumps(rec, ensure_ascii=False) + "\n")
                    out.flush()
                    kept += 1

                    types = "/".join(sorted({o.type for o in subs}))
                    print(f"    [{kept}] {t['year']} "
                          f"{cluster.case_name[:44]:<46} {len(subs)} op ({types})")

    except QuotaExhausted as e:
        print(f"\n{e}", file=sys.stderr)
        print(f"Collected {kept} this session; rerun to continue.", file=sys.stderr)
        sys.exit(2)
    except KeyboardInterrupt:
        print(f"\nInterrupted. {kept} collected this session; progress saved.")

    print(f"\nCollected {kept}  |  not found {not_found}  |  no text {no_text}")
    print(f"HTTP requests: {api.n_requests} (throttled {api.n_throttled})")
    print(f"  clusters with split sub-opinions:    {split_records}")
    print(f"  clusters as single '010combined':    {combined_records}")
    print(f"Total in {raw_path}: {len(done) + kept}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--scdb", required=True)
    ap.add_argument("--year-from", type=int, default=2005)
    ap.add_argument("--year-to", type=int, default=2025)
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--batch-size", type=int, default=100,
                    help="Citations per lookup request.")
    ap.add_argument("--delay", type=float, default=None)
    ap.add_argument("--max-wait", type=int, default=900)
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    token = os.getenv("COURTLISTENER_TOKEN")
    if not token:
        sys.exit("COURTLISTENER_TOKEN is not set (see .env.example)")

    scdb_path = Path(args.scdb)
    if not scdb_path.exists():
        sys.exit(f"SCDB file not found: {scdb_path}")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.delay is not None:
        cfg["collect"]["request_delay_s"] = args.delay

    collect(cfg, token, scdb_path, args.year_from, args.year_to,
            args.limit, args.batch_size, args.max_wait)


if __name__ == "__main__":
    main()
