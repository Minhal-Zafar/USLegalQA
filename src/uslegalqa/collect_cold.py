"""Collect SCOTUS opinions from the COLD Cases parquet dataset.

COLD Cases (Harvard LIL / Free Law Project) is a CC0 bulk export of
CourtListener with opinions already split by type. DuckDB reads the remote
parquet with pushdown, so only SCOTUS rows are downloaded.

Setup:
    pip install duckdb

Usage:
    python -m uslegalqa.collect_cold --inspect          # show schema first
    python -m uslegalqa.collect_cold --scdb SCDB.csv --limit 50
    python -m uslegalqa.collect_cold --scdb SCDB.csv
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

import yaml

HF_REPO = "harvard-lil/cold-cases"
HF_BASE = f"https://huggingface.co/datasets/{HF_REPO}/resolve/main"

# The dataset is split into numbered parquet parts sharing one UUID stem.
PART_STEM = "part-{n:05d}-bd7b5d85-e1bd-440b-8817-95ec234884f3-c000.gz.parquet"


def part_urls(n_parts: int) -> list[str]:
    return [f"{HF_BASE}/{PART_STEM.format(n=i)}" for i in range(n_parts)]


def connect(cache_dir: Path):
    try:
        import duckdb
    except ImportError:
        sys.exit("duckdb is required:  pip install duckdb")

    cache_dir.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(cache_dir / "cold.duckdb"))
    con.execute("INSTALL httpfs; LOAD httpfs;")
    con.execute("SET enable_progress_bar = true;")
    con.execute("SET http_timeout = 300000;")
    return con


def inspect(cache_dir: Path) -> None:
    """Print the schema, court values, a sample row and opinion type counts
    from a single parquet part."""
    con = connect(cache_dir)
    url = part_urls(1)[0]
    print(f"Reading schema from:\n  {url}\n")

    try:
        cols = con.execute(f"DESCRIBE SELECT * FROM read_parquet('{url}')").fetchall()
    except Exception as e:
        sys.exit(f"Failed to read remote parquet: {e}\n"
                 "If the filename pattern has changed, check\n"
                 f"https://huggingface.co/datasets/{HF_REPO}/tree/main")

    print(f"{'column':<34} type")
    for name, dtype, *_ in cols:
        print(f"  {name:<32} {dtype}")

    names = {c[0] for c in cols}
    print("\nFields this pipeline needs:")
    for want, why in [
        ("id", "cluster identity"),
        ("date_filed", "year range"),
        ("case_name", "SCDB join fallback"),
        ("citations", "SCDB join key"),
        ("opinions", "opinion text and type (struct array)"),
        ("syllabus", "official headnote"),
        ("court_full_name", "filter to SCOTUS"),
    ]:
        mark = "found" if want in names else "MISSING"
        print(f"  {want:<18} {mark:<8} ({why})")

    # COLD has no court_id; discover how the Supreme Court is named.
    print("\nCourt values in this part:")
    try:
        rows = con.execute(f"""
            SELECT court_full_name, court_type, court_jurisdiction, count(*) AS n
            FROM read_parquet('{url}')
            GROUP BY 1, 2, 3 ORDER BY n DESC LIMIT 15
        """).fetchall()
        for full, ctype, juris, n in rows:
            flag = "  <-- SCOTUS?" if full and "supreme court of the united" in \
                str(full).lower() else ""
            print(f"  {str(full)[:44]:<46} {str(ctype):<10} "
                  f"{str(juris):<8} {n:>7}{flag}")
    except Exception as e:
        print(f"  could not group: {e}")

    print("\nSample SCOTUS row:")
    try:
        cur = con.execute(f"""
            SELECT id, case_name, date_filed, citations, syllabus,
                   precedential_status, len(opinions) AS n_opinions
            FROM read_parquet('{url}')
            WHERE lower(court_full_name) LIKE '%supreme court of the united%'
              AND date_filed >= DATE '2005-01-01'
            LIMIT 1
        """)
        names = [d[0] for d in cur.description]
        row = cur.fetchone()
        if not row:
            print("  (none in this part in range)")
        else:
            for name, val in zip(names, row):
                print(f"  {name:<22} {str(val)[:86]}")
    except Exception as e:
        print(f"  could not sample: {e}")

    print("\nOpinion types:")
    try:
        ops = con.execute(f"""
            SELECT op.type AS t, count(*) AS n
            FROM (
                SELECT unnest(opinions) AS op
                FROM read_parquet('{url}')
                WHERE lower(court_full_name) LIKE '%supreme court of the united%'
            )
            GROUP BY 1 ORDER BY n DESC LIMIT 12
        """).fetchall()
        for t, n in ops:
            print(f"  {str(t):<32} {n:>8}")
    except Exception as e:
        print(f"  could not unnest: {e}")


def extract_scotus(cache_dir: Path, n_parts: int, year_from: int,
                   year_to: int, out_path: Path) -> int:
    """Pull all SCOTUS rows in range into a local parquet cache."""
    con = connect(cache_dir)
    urls = part_urls(n_parts)
    url_list = ", ".join(f"'{u}'" for u in urls)

    print(f"Scanning {n_parts} parquet parts for SCOTUS {year_from}-{year_to}\n")

    con.execute(f"""
        CREATE OR REPLACE TABLE scotus AS
        SELECT *
        FROM read_parquet([{url_list}], union_by_name = true)
        WHERE lower(court_full_name) LIKE '%supreme court of the united%'
          AND date_filed >= DATE '{year_from}-01-01'
          AND date_filed <= DATE '{year_to}-12-31'
    """)
    n = con.execute("SELECT count(*) FROM scotus").fetchone()[0]
    print(f"\n{n} SCOTUS decisions cached")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    con.execute(f"COPY scotus TO '{out_path}' (FORMAT PARQUET)")
    print(f"Written to {out_path}")
    return n


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--inspect", action="store_true",
                    help="Print the remote schema and exit (cheap).")
    ap.add_argument("--extract", action="store_true",
                    help="Download and cache all SCOTUS rows in range.")
    ap.add_argument("--parts", type=int, default=28,
                    help="Number of parquet parts to scan.")
    ap.add_argument("--year-from", type=int, default=2005)
    ap.add_argument("--year-to", type=int, default=2023)
    ap.add_argument("--cache", default="data/cold_cache")
    args = ap.parse_args()

    cache = Path(args.cache)

    if args.inspect:
        inspect(cache)
        return

    if not args.extract:
        sys.exit("Choose one:  --inspect  (schema, cheap)  "
                 "or  --extract  (download SCOTUS rows)")

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    out = Path(cfg["paths"]["raw"]).with_suffix(".parquet")
    extract_scotus(cache, args.parts, args.year_from, args.year_to, out)


if __name__ == "__main__":
    main()
