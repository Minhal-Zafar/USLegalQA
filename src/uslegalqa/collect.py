"""Collect SCOTUS opinions from CourtListener REST API v4.

  Pass 1: paginate /clusters/  -> case metadata, keyed by cluster_id
  Pass 2: paginate /opinions/  -> opinion text, carrying cluster_id
  Pass 3: join locally

Usage:
    python -m uslegalqa.collect --probe
    python -m uslegalqa.collect --max-clusters 25
    python -m uslegalqa.collect --delay 2.0
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from collections import defaultdict
from pathlib import Path
from typing import Any, Iterator

import requests
import yaml

from .schema import Cluster, SubOpinion

API_ROOT = "https://www.courtlistener.com/api/rest/v4"

_REVISION_RE = re.compile(r"\bRevisions?\s*:", re.IGNORECASE)


class QuotaExhausted(RuntimeError):
    """Raised when the server asks for a wait longer than --max-wait."""
_TAG_RE = re.compile(r"<[^>]+>")


class CourtListener:
    """HTTP client that honours Retry-After and backs off its base delay on 429."""

    def __init__(self, token: str, delay: float = 1.0,
                 max_retries: int = 8, timeout: int = 60,
                 max_delay: float = 8.0, max_wait: int = 300):
        self.session = requests.Session()
        self.session.headers.update({
            "Authorization": f"Token {token}",
            "User-Agent": "USLegalQA/3.0 (academic research)",
        })
        self.delay = delay
        self.max_delay = max_delay
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_wait = max_wait
        self.n_requests = 0
        self.n_throttled = 0
        self._reported_headers = False

    def _report_limits(self, r: requests.Response) -> None:
        """Print rate-limit headers once, so the real quota is visible."""
        if self._reported_headers:
            return
        self._reported_headers = True
        interesting = {k: v for k, v in r.headers.items()
                       if any(w in k.lower()
                              for w in ("rate", "retry", "throttl", "limit"))}
        if interesting:
            print("  [rate-limit headers] " + json.dumps(interesting), file=sys.stderr)
        else:
            print("  [server returned no rate-limit headers]", file=sys.stderr)

    def get(self, url: str, params: dict | None = None) -> dict[str, Any]:
        for attempt in range(self.max_retries):
            try:
                r = self.session.get(url, params=params, timeout=self.timeout)
            except requests.exceptions.ReadTimeout:
                # Usually an oversized payload, so shrink the page first.
                if params and int(params.get("page_size", 0)) > 1:
                    params = dict(params)
                    params["page_size"] = max(1, int(params["page_size"]) // 2)
                    print(f"    read timeout; halving page_size to "
                          f"{params['page_size']}", file=sys.stderr)
                    continue
                wait = min(2 ** attempt, 60)
                print(f"    read timeout, retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue
            except requests.RequestException as e:
                wait = min(2 ** attempt, 60)
                print(f"    network error ({e.__class__.__name__}), retry in {wait}s",
                      file=sys.stderr)
                time.sleep(wait)
                continue

            self.n_requests += 1

            if r.status_code == 200:
                time.sleep(self.delay)
                return r.json()

            if r.status_code == 429:
                self.n_throttled += 1
                self._report_limits(r)
                wait = int(r.headers.get("Retry-After", min(30 * (attempt + 1), 120)))
                self.delay = min(self.delay * 1.5, self.max_delay)
                if wait > self.max_wait:
                    raise QuotaExhausted(
                        f"Quota exhausted; server asks for {wait}s "
                        f"({wait // 60} min). Progress has been saved -- rerun the "
                        f"same command later to resume, or pass "
                        f"--max-wait {wait + 60} to sit it out."
                    )
                print(f"    throttled; waiting {wait}s "
                      f"(base delay now {self.delay:.1f}s)", file=sys.stderr)
                time.sleep(wait)
                continue

            if r.status_code in (401, 403):
                raise RuntimeError(
                    f"HTTP {r.status_code}: token rejected. "
                    f"Check COURTLISTENER_TOKEN.\n{r.text[:200]}"
                )

            if 500 <= r.status_code < 600:
                wait = min(2 ** attempt, 60)
                print(f"    server {r.status_code}, retry in {wait}s", file=sys.stderr)
                time.sleep(wait)
                continue

            raise RuntimeError(f"HTTP {r.status_code} for {url}: {r.text[:300]}")

        raise RuntimeError(f"exhausted {self.max_retries} retries for {url}")

    def paginate(self, endpoint: str, params: dict,
                 label: str = "") -> Iterator[dict[str, Any]]:
        url, first, page = f"{API_ROOT}/{endpoint}/", True, 0
        while url:
            payload = self.get(url, params=params if first else None)
            first = False
            page += 1
            results = payload.get("results", [])
            print(f"  {label} page {page}: {len(results)} records "
                  f"[{self.n_requests} requests, {self.n_throttled} throttled]")
            for item in results:
                yield item
            url = payload.get("next")


def extract_text(op: dict[str, Any]) -> str:
    for key in ("plain_text", "xml_harvard", "html_with_citations",
                "html_columbia", "html_lawbox", "html"):
        raw = op.get(key)
        if raw and raw.strip():
            text = _TAG_RE.sub(" ", raw) if key != "plain_text" else raw
            text = re.sub(r"[ \t]{2,}", " ", text)
            text = re.sub(r"\n{3,}", "\n\n", text)
            if len(text.split()) >= 50:
                return text.strip()
    return ""


def author_of(op: dict[str, Any]) -> str | None:
    a = op.get("author_str") or op.get("author_id")
    return str(a) if a else None


def _cluster_meta(cl: dict[str, Any], court: str) -> dict[str, Any]:
    citations = cl.get("citations") or []
    cite = None
    if citations and isinstance(citations[0], dict):
        cc = citations[0]
        cite = f"{cc.get('volume')} {cc.get('reporter')} {cc.get('page')}"
    return dict(
        cluster_id=cl["id"],
        case_name=(cl.get("case_name") or "").strip(),
        date_filed=cl.get("date_filed") or "",
        court=court,
        precedential_status=cl.get("precedential_status"),
        citation=cite,
        scdb_id=(cl.get("scdb_id") or None),
        scdb_decision_direction=cl.get("scdb_decision_direction"),
        scdb_votes_majority=cl.get("scdb_votes_majority"),
        scdb_votes_minority=cl.get("scdb_votes_minority"),
        docket_id=cl.get("docket_id"),
        judges=(cl.get("judges") or None),
        syllabus=(cl.get("syllabus") or None),
    )


def collect(cfg: dict, token: str, max_clusters: int | None = None,
            max_wait: int = 300, refresh: bool = False) -> None:
    c, paths = cfg["collect"], cfg["paths"]
    raw_path = Path(paths["raw"])
    ops_path = raw_path.with_name("_opinions_stage.jsonl")
    raw_path.parent.mkdir(parents=True, exist_ok=True)

    api = CourtListener(token, c["request_delay_s"], c["max_retries"],
                        c["timeout_s"], max_wait=max_wait)
    opinion_page_size = c.get("opinion_page_size", 5)
    # A persistent failure for one year is skipped rather than aborting the run.
    tolerate_year_failures = c.get("tolerate_year_failures", True)
    limit = max_clusters if max_clusters is not None else c.get("max_clusters")
    meta_path = raw_path.with_name("_clusters_meta.json")

    print("PASS 1/3 -- cluster metadata")
    meta: dict[int, dict[str, Any]] = {}
    revisions_skipped = 0

    if meta_path.exists() and not refresh:
        cached = json.loads(meta_path.read_text(encoding="utf-8"))
        meta = {int(k): v for k, v in cached.items()}
        print(f"  reusing cached metadata for {len(meta)} clusters "
              f"(delete {meta_path.name} or pass --refresh to refetch)")

    cluster_params = {
        "docket__court": c["court"],
        "date_filed__gte": c["date_from"],
        "date_filed__lte": c["date_to"],
        "page_size": c["page_size"],
    }
    if c.get("precedential_status"):
        cluster_params["precedential_status"] = c["precedential_status"]

    if not meta:
        # Per-year windows: `order_by` is not reliably honoured, so a single
        # query would return an arbitrary slice of the range.
        y0, y1 = int(c["date_from"][:4]), int(c["date_to"][:4])
        try:
            for year in range(y0, y1 + 1):
                if limit is not None and len(meta) >= limit:
                    break
                year_params = dict(cluster_params)
                year_params["date_filed__gte"] = max(f"{year}-01-01", c["date_from"])
                year_params["date_filed__lte"] = min(f"{year}-12-31", c["date_to"])
                before = len(meta)
                for cl in api.paginate("clusters", year_params, f"clusters {year}"):
                    if _REVISION_RE.search(cl.get("case_name") or ""):
                        revisions_skipped += 1
                        continue
                    meta[cl["id"]] = _cluster_meta(cl, c["court"])
                    if limit is not None and len(meta) >= limit:
                        break
                print(f"    {year}: +{len(meta) - before} clusters "
                      f"({len(meta)} total)")
        finally:
            if meta:
                meta_path.write_text(
                    json.dumps({str(k): v for k, v in meta.items()},
                               ensure_ascii=False),
                    encoding="utf-8")
                print(f"  saved metadata for {len(meta)} clusters")

    print(f"  -> {len(meta)} clusters "
          f"({revisions_skipped} revision reposts skipped)")
    if not meta:
        print("No clusters returned. Check the court code and date range.")
        return

    # Full opinion records (with every HTML variant) are large enough to time
    # out, so request a lean field set and refetch empty ones individually.
    print("\nPASS 2/3 -- opinion text")
    wanted = set(meta)
    lean_fields = ",".join([
        "id", "cluster_id", "type", "author_str", "author_id",
        "per_curiam", "extracted_by_ocr", "page_count", "plain_text",
    ])
    dates = [m["date_filed"] for m in meta.values() if m["date_filed"]]
    opinion_params = {
        "cluster__docket__court": c["court"],
        "cluster__date_filed__gte": min(dates) if dates else c["date_from"],
        "cluster__date_filed__lte": max(dates) if dates else c["date_to"],
        "page_size": opinion_page_size,
        "fields": lean_fields,
    }

    staged: set[int] = set()
    staged_clusters: set[int] = set()
    if ops_path.exists():
        with ops_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    staged.add(d["opinion_id"])
                    staged_clusters.add(d["cluster_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
        if staged:
            print(f"  resuming: {len(staged)} opinions already staged")

    cluster_filter = c.get("cluster_filter")   # discovered via --probe-filters

    def opinion_stream():
        """Yield opinion records for the wanted clusters.

        Uses targeted cluster queries when cheaper, else scans the date window.
        """
        ids = sorted(c for c in wanted if c not in staged_clusters)
        batched = bool(cluster_filter) and cluster_filter.endswith("__in")

        # Rough request-cost estimates for targeted queries vs a date scan.
        per_cluster_cost = len(ids) if not batched else -(-len(ids) // 20)
        scan_cost_estimate = max(8, -(-len(ids) * 3 // 20))

        if cluster_filter and per_cluster_cost <= scan_cost_estimate:
            print(f"  targeted: {per_cluster_cost} requests via {cluster_filter} "
                  f"(scan would cost ~{scan_cost_estimate})")
            step = 20 if batched else 1
            try:
                for i in range(0, len(ids), step):
                    chunk = ids[i:i + step]
                    params = {
                        "fields": lean_fields,
                        cluster_filter: ",".join(str(x) for x in chunk),
                    }
                    yield from api.paginate("opinions", params,
                                            f"opinions {i + len(chunk)}/{len(ids)}")
                return
            except RuntimeError as e:
                if "400" not in str(e):
                    raise
                print(f"  {cluster_filter} rejected mid-run; switching to scan",
                      file=sys.stderr)
        elif cluster_filter:
            print(f"  scanning date window: {per_cluster_cost} targeted requests "
                  f"would exceed the ~{scan_cost_estimate} a scan needs")
        else:
            print("  scanning date window (run --probe-filters to avoid this)",
                  file=sys.stderr)

        # Per-year windows let the early-exit guard fire between years.
        years = sorted({m["date_filed"][:4] for m in meta.values()
                        if m["date_filed"]})
        for y in years:
            if len(satisfied) >= len(wanted):
                return
            yp = dict(opinion_params)
            yp["cluster__date_filed__gte"] = f"{y}-01-01"
            yp["cluster__date_filed__lte"] = f"{y}-12-31"
            try:
                yield from api.paginate("opinions", yp, f"opinions {y}")
            except RuntimeError as e:
                if not tolerate_year_failures:
                    raise
                print(f"    {y} failed ({str(e)[:60]}); continuing -- "
                      f"rerun later to fill the gap", file=sys.stderr)
                continue

    satisfied: set[int] = set(staged_clusters)
    n_ops = len(staged)
    with ops_path.open("a", encoding="utf-8") as f:
        for op in opinion_stream():
            if len(satisfied) >= len(wanted):
                print(f"  every cluster satisfied after {api.n_requests} requests; "
                      f"stopping scan early")
                break
            cid = op.get("cluster_id")
            if cid not in wanted or op.get("id") in staged:
                continue
            text = extract_text(op)
            if not text:
                # Lean field set omits the HTML variants; refetch in full.
                try:
                    full = api.get(f"{API_ROOT}/opinions/{op.get('id')}/")
                    text = extract_text(full)
                except RuntimeError:
                    text = ""
            if not text:
                continue
            f.write(json.dumps({
                "cluster_id": cid,
                "opinion_id": op.get("id", -1),
                "type": op.get("type") or "unknown",
                "author": author_of(op),
                "per_curiam": bool(op.get("per_curiam", False)),
                "extracted_by_ocr": bool(op.get("extracted_by_ocr", False)),
                "page_count": op.get("page_count"),
                "text": text,
            }, ensure_ascii=False) + "\n")
            satisfied.add(cid)
            n_ops += 1
            if n_ops % 100 == 0:
                print(f"    {n_ops} opinions staged, "
                      f"{len(satisfied)}/{len(wanted)} clusters satisfied")
            if n_ops >= len(wanted) * 6:      # safety valve
                break
    print(f"  -> {n_ops} opinions staged")

    print("\nPASS 3/3 -- joining")
    offsets: dict[int, list[int]] = defaultdict(list)
    with ops_path.open("rb") as f:
        while True:
            pos = f.tell()
            line = f.readline()
            if not line:
                break
            try:
                offsets[json.loads(line)["cluster_id"]].append(pos)
            except (json.JSONDecodeError, KeyError):
                continue

    type_counter: dict[str, int] = defaultdict(int)
    kept = scdb_linked = no_primary = no_text = 0

    with raw_path.open("w", encoding="utf-8") as out, ops_path.open("rb") as src:
        for cid, m in meta.items():
            subs: list[SubOpinion] = []
            for pos in offsets.get(cid, []):
                src.seek(pos)
                d = json.loads(src.readline())
                type_counter[d["type"]] += 1
                subs.append(SubOpinion(
                    opinion_id=d["opinion_id"], type=d["type"], author=d["author"],
                    text=d["text"], word_count=len(d["text"].split()),
                    per_curiam=d["per_curiam"],
                    extracted_by_ocr=d["extracted_by_ocr"],
                    page_count=d["page_count"],
                ))
            if not subs:
                no_text += 1
                continue

            cluster = Cluster(sub_opinions=subs, **m)
            if cluster.primary() is None:
                no_primary += 1
            if cluster.scdb_id:
                scdb_linked += 1

            out.write(json.dumps(cluster.to_dict(), ensure_ascii=False) + "\n")
            kept += 1

    ops_path.unlink(missing_ok=True)
    meta_path.unlink(missing_ok=True)

    print(f"\nCollected {kept} clusters -> {raw_path}")
    print(f"HTTP requests: {api.n_requests} (throttled {api.n_throttled} times)")
    print(f"Clusters with no usable text:     {no_text}")
    print(f"Clusters with no primary opinion: {no_primary}")
    if kept:
        print(f"SCDB-linked: {scdb_linked}/{kept} ({100*scdb_linked/kept:.1f}%)")

    print("\nOpinion type distribution:")
    for t, n in sorted(type_counter.items(), key=lambda kv: -kv[1]):
        marker = "PRIMARY" if t in c["primary_types"] else (
            "secondary" if t in c["secondary_types"] else "*** UNCONFIGURED ***")
        print(f"  {t:<28} {n:>6}   {marker}")


def probe(cfg: dict, token: str) -> None:
    c = cfg["collect"]
    api = CourtListener(token, c["request_delay_s"], c["max_retries"], c["timeout_s"])
    payload = api.get(f"{API_ROOT}/clusters/", {
        "docket__court": c["court"],
        "date_filed__gte": c["date_from"],
        "date_filed__lte": c["date_to"],
        "page_size": 1,
    })
    results = payload.get("results", [])
    if not results:
        print("No clusters returned. Check the token and the court code.")
        return

    cl = results[0]
    print("=== CLUSTER keys ===")
    for k in sorted(cl):
        print(f"  {k:<28} {type(cl[k]).__name__:<8} {str(cl[k])[:70]}")

    subs = cl.get("sub_opinions") or []
    print(f"\nsub_opinions: {len(subs)}")
    if subs:
        op = api.get(subs[0]) if isinstance(subs[0], str) else subs[0]
        print("\n=== OPINION keys ===")
        for k in sorted(op):
            print(f"  {k:<28} {type(op[k]).__name__:<8} {str(op[k])[:70]}")
        print(f"\ntype        = {op.get('type')!r}")
        print(f"cluster_id  = {op.get('cluster_id')!r}")
        print(f"extracted   = {len(extract_text(op).split())} words")


# Candidate /opinions/ cluster filters; the working spelling is found at runtime.
CLUSTER_FILTER_CANDIDATES = [
    "cluster__id__in", "cluster_id__in", "cluster__id", "cluster_id",
    "cluster", "id__in",
]


def probe_filters(cfg: dict, token: str) -> None:
    """Find which cluster filter the /opinions/ endpoint accepts."""
    c = cfg["collect"]
    api = CourtListener(token, c["request_delay_s"], c["max_retries"], c["timeout_s"])

    payload = api.get(f"{API_ROOT}/clusters/", {
        "docket__court": c["court"],
        "date_filed__gte": c["date_from"],
        "date_filed__lte": c["date_to"],
    })
    results = payload.get("results", [])
    if not results:
        print("No clusters returned; cannot probe.")
        return
    cid = results[0]["id"]
    name = results[0].get("case_name", "")[:50]
    print(f"Testing against cluster {cid} ({name})\n")

    working = []
    for f in CLUSTER_FILTER_CANDIDATES:
        params = {f: str(cid), "fields": "id,cluster_id,type"}
        try:
            r = api.get(f"{API_ROOT}/opinions/", params)
        except RuntimeError as e:
            print(f"  {f:<22} ERROR  {str(e)[:70]}")
            continue
        res = r.get("results", [])
        n = len(res)
        matched = sum(1 for o in res if o.get("cluster_id") == cid)
        count = r.get("count")
        if n and matched == n:
            print(f"  {f:<22} OK     {n} records, all from cluster {cid}")
            working.append(f)
        elif n:
            print(f"  {f:<22} IGNORED  {n} records, only {matched} matched "
                  f"(count={count}) -- filter had no effect")
        else:
            print(f"  {f:<22} EMPTY  no records")

    print()
    if working:
        print(f"Use: {working[0]}")
        print(f"Set  collect.cluster_filter: \"{working[0]}\"  in config/default.yaml")
    else:
        print("None worked; collection will fall back to a date-window scan.")


def probe_years(cfg: dict, token: str) -> None:
    """Sample one page of clusters per year; check date filtering and SCDB coverage."""
    c = cfg["collect"]
    api = CourtListener(token, c["request_delay_s"], c["max_retries"], c["timeout_s"])

    y0 = int(c["date_from"][:4])
    y1 = int(c["date_to"][:4])
    years = list(range(y0, y1 + 1))

    print(f"{'year':<6} {'returned':>8} {'right yr':>9} {'scdb':>6} {'total':>10}")
    totals = {}
    for y in years:
        try:
            r = api.get(f"{API_ROOT}/clusters/", {
                "docket__court": c["court"],
                "date_filed__gte": f"{y}-01-01",
                "date_filed__lte": f"{y}-12-31",
                "precedential_status": c.get("precedential_status") or None,
                "fields": "id,case_name,date_filed,scdb_id",
                "count": "on",
            })
        except RuntimeError as e:
            print(f"{y:<6} ERROR {str(e)[:50]}")
            continue
        res = r.get("results", [])
        right = sum(1 for x in res if (x.get("date_filed") or "").startswith(str(y)))
        scdb = sum(1 for x in res if x.get("scdb_id"))
        count = r.get("count")
        if isinstance(count, str):      # v4 returns a URL, not an integer
            count = "?"
        totals[y] = count if isinstance(count, int) else None
        flag = "" if right == len(res) else "  <-- FILTER NOT APPLIED"
        print(f"{y:<6} {len(res):>8} {right:>9} {scdb:>6} {str(count):>10}{flag}")

    known = [v for v in totals.values() if isinstance(v, int)]
    if known:
        print(f"\nEstimated corpus size {y0}-{y1}: {sum(known):,} clusters")
    else:
        print("\n(v4 reports counts via a separate URL; corpus size not shown)")


def load_config(path: str = "config/default.yaml") -> dict:
    return yaml.safe_load(Path(path).read_text(encoding="utf-8"))


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--probe", action="store_true")
    ap.add_argument("--probe-filters", action="store_true",
                    help="Discover which cluster filter /opinions/ accepts.")
    ap.add_argument("--probe-years", action="store_true",
                    help="Sample each year: check date filtering and SCDB coverage.")
    ap.add_argument("--max-clusters", type=int, default=None)
    ap.add_argument("--delay", type=float, default=None,
                    help="Override request_delay_s. Raise this if throttled.")
    ap.add_argument("--max-wait", type=int, default=300,
                    help="Exit instead of sleeping longer than this on a 429.")
    ap.add_argument("--refresh", action="store_true",
                    help="Refetch cluster metadata instead of using the cache.")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    token = os.getenv("COURTLISTENER_TOKEN")
    if not token:
        sys.exit(
            "COURTLISTENER_TOKEN is not set.\n"
            "Copy .env.example to .env and add your token, or export it:\n"
            "  export COURTLISTENER_TOKEN=...    (macOS/Linux)\n"
            "  $env:COURTLISTENER_TOKEN='...'    (Windows PowerShell)"
        )

    cfg = load_config(args.config)
    if args.delay is not None:
        cfg["collect"]["request_delay_s"] = args.delay

    if args.probe:
        probe(cfg, token)
        return

    if args.probe_filters:
        probe_filters(cfg, token)
        return

    if args.probe_years:
        probe_years(cfg, token)
        return

    try:
        collect(cfg, token, args.max_clusters, args.max_wait, args.refresh)
    except QuotaExhausted as e:
        print(f"\n{e}", file=sys.stderr)
        sys.exit(2)


if __name__ == "__main__":
    main()
