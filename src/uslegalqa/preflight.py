"""Preflight check before a paid generation run.

Runs every check that needs no API call (environment, source files, config,
corpus, chunking, prompts, resume state, existing data quality, gaps) and
projects the size and duration of the remaining run.

Usage:
    python -m uslegalqa.preflight
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

OK, WARN, FAIL = "  [OK]  ", "  [WARN]", "  [FAIL]"

_problems: list[str] = []
_warnings: list[str] = []


def ok(msg: str) -> None:
    print(f"{OK} {msg}")


def warn(msg: str) -> None:
    print(f"{WARN} {msg}")
    _warnings.append(msg)


def fail(msg: str) -> None:
    print(f"{FAIL} {msg}")
    _problems.append(msg)


def section(title: str) -> None:
    print(f"\n{title}")


# --- 1. environment --------------------------------------------------------


def check_env() -> None:
    section("1. ENVIRONMENT")
    try:
        from dotenv import load_dotenv
        load_dotenv()
        ok(".env loaded")
    except ImportError:
        warn("python-dotenv not installed; relying on shell environment")

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        fail("ANTHROPIC_API_KEY is not set. Put it in .env as "
             "ANTHROPIC_API_KEY=sk-ant-...")
        return
    if key.strip() != key:
        fail("ANTHROPIC_API_KEY has leading or trailing whitespace")
    elif key.startswith(("'", '"')):
        fail("ANTHROPIC_API_KEY is wrapped in quotes; remove them")
    elif "paste" in key.lower() or "your_" in key.lower():
        fail("ANTHROPIC_API_KEY still contains placeholder text")
    elif not key.startswith("sk-ant-"):
        warn(f"key does not start with 'sk-ant-' (starts {key[:8]!r}) -- "
             "check it is an Anthropic key")
    else:
        ok(f"ANTHROPIC_API_KEY present ({key[:12]}...{key[-4:]})")

    try:
        import anthropic  # noqa: F401
        ok("anthropic package installed")
    except ImportError:
        fail("anthropic not installed:  pip install anthropic")


# --- 2. source files -------------------------------------------------------

# Each entry: (file, marker, why it matters)
REQUIRED_MARKERS = [
    ("generate.py", "_char_stream",
     "character-stream span matching (without it, ~30% of valid pairs rejected)"),
    ("generate.py", "_STAR_PAGE",
     "star pagination handling (was 92% of span rejections)"),
    ("generate.py", "_FOOTNOTE_MARKER",
     "footnote marker handling"),
    ("generate.py", "APITimeoutError",
     "network fault tolerance (without it, one dropped connection kills the run)"),
    ("generate.py", "credit balance",
     "fail-fast on exhausted credit (without it, a billing failure silently "
     "skips every remaining chunk)"),
    ("generate.py", "_longest_shared_run",
     "answer-copying detection"),
    ("generate.py", "def sanitise",
     "text sanitisation before transport"),
    ("chunking.py", "n_late = max",
     "proportional position banding (without it, holdings fall to ~10%)"),
]


def check_sources() -> None:
    section("2. SOURCE FILES")
    src = Path(__file__).parent
    for filename, marker, why in REQUIRED_MARKERS:
        path = src / filename
        if not path.exists():
            fail(f"{filename} missing")
            continue
        text = path.read_text(encoding="utf-8", errors="ignore")
        if marker in text:
            ok(f"{filename}: {why}")
        else:
            fail(f"{filename} is MISSING {marker!r} -- {why}")


# --- 3. configuration ------------------------------------------------------


def check_config(cfg: dict) -> None:
    section("3. CONFIGURATION")
    g = cfg.get("generate", {})

    required = ["model", "temperature", "chunk_words", "chunk_overlap",
                "pairs_per_chunk", "min_span_chars", "output",
                "min_answer_words", "max_answer_words"]
    missing = [k for k in required if k not in g]
    for k in missing:
        fail(f"generate.{k} is missing from the config")
    if missing:
        return

    ok(f"model: {g['model']}")
    ok(f"temperature: {g['temperature']}")
    ok(f"chunk_words: {g['chunk_words']}, overlap: {g['chunk_overlap']}, "
       f"pairs_per_chunk: {g['pairs_per_chunk']}")

    if g.get("max_copied_run_words") is None:
        warn("max_copied_run_words not set -- answers may transcribe their "
             "span (was 45.6% before this filter)")
    else:
        ok(f"max_copied_run_words: {g['max_copied_run_words']}")

    if g.get("abort_after_empty_chunks") is None:
        warn("abort_after_empty_chunks not set -- a systemic fault will not "
             "halt the run")
    else:
        ok(f"abort_after_empty_chunks: {g['abort_after_empty_chunks']}")

    if not 0 <= g["temperature"] <= 1:
        fail(f"temperature {g['temperature']} outside [0,1]")
    if g["chunk_overlap"] >= g["chunk_words"]:
        fail("chunk_overlap >= chunk_words: chunking will not advance")
    if g["min_answer_words"] >= g["max_answer_words"]:
        fail("min_answer_words >= max_answer_words: every pair will be rejected")


# --- 4. corpus -------------------------------------------------------------


def load_corpus(cfg: dict) -> list[dict]:
    section("4. CORPUS")
    path = Path(cfg["paths"]["cleaned"])
    if not path.exists():
        fail(f"cleaned corpus not found at {path}")
        return []

    records = []
    for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            records.append(json.loads(line))
        except json.JSONDecodeError:
            fail(f"{path}: line {i} is not valid JSON")
            return []

    ok(f"{len(records)} opinions loaded from {path}")

    missing_text = sum(1 for r in records if not r.get("text", "").strip())
    if missing_text:
        fail(f"{missing_text} opinions have no text")
    else:
        ok("every opinion has text")

    # `scdb_category` is the pre-cleaning name of `category`.
    no_cat = sum(1 for r in records
                 if not (r.get("category") or r.get("scdb_category")))
    linked = sum(1 for r in records if r.get("scdb_id"))
    if no_cat:
        fail(f"{no_cat} of {len(records)} opinions have no issue area label "
             f"({linked} are SCDB-linked, so the labels are recoverable). "
             "Run: python -m uslegalqa.backfill_categories --scdb <csv>")
    else:
        ok("every opinion has an SCDB issue area")

    ids = [r.get("cluster_id") for r in records]
    if len(set(ids)) != len(ids):
        fail(f"duplicate cluster_ids: {len(ids) - len(set(ids))}")
    else:
        ok("cluster_ids unique")

    years = Counter(str(r.get("date_filed", ""))[:4] for r in records)
    span = f"{min(years)}\u2013{max(years)}" if years else "?"
    ok(f"year coverage: {span}, {len(years)} years, "
       f"{min(years.values())}\u2013{max(years.values())} per year")
    return records


# --- 5. chunking and cost --------------------------------------------------


def check_chunking(cfg: dict, records: list[dict]) -> list:
    section("5. CHUNKING AND COST PROJECTION")
    from .chunking import chunk_opinion

    g = cfg["generate"]
    all_chunks = []
    positions: Counter = Counter()
    for rec in records:
        chunks = chunk_opinion(rec["text"], rec["cluster_id"],
                               target_words=g["chunk_words"],
                               overlap_words=g["chunk_overlap"])
        all_chunks.extend((rec, c) for c in chunks)
        positions.update(c.position for c in chunks)

    n = len(all_chunks)
    ok(f"{n} chunks from {len(records)} opinions "
       f"(median {sorted(Counter(c.cluster_id for _, c in all_chunks).values())[len(records)//2]} per opinion)")

    total = sum(positions.values())
    for band in ("early", "middle", "late"):
        pct = 100 * positions[band] / total
        print(f"         {band:<8} {positions[band]:>6}  {pct:5.1f}%")

    late_pct = 100 * positions["late"] / total
    if late_pct < 15:
        fail(f"only {late_pct:.1f}% of chunks are 'late' -- holdings will be "
             "under-represented. Check the banding fix in chunking.py")
    else:
        ok(f"late band is {late_pct:.1f}% of chunks (holdings well covered)")

    return all_chunks


# --- 6. prompts ------------------------------------------------------------


def check_prompts(cfg: dict, all_chunks: list) -> None:
    section("6. PROMPT RENDERING")
    from .generate import build_prompt

    g = cfg["generate"]
    sizes = []
    for rec, chunk in all_chunks:
        try:
            p = build_prompt(rec, chunk, g["pairs_per_chunk"])
        except Exception as e:  # noqa: BLE001
            fail(f"prompt build failed for cluster {chunk.cluster_id}: {e}")
            return
        sizes.append(len(p))

    sizes.sort()
    ok(f"all {len(sizes)} prompts render")
    ok(f"prompt size: min {sizes[0]:,} / median {sizes[len(sizes)//2]:,} / "
       f"max {sizes[-1]:,} chars")

    limit = g.get("max_prompt_chars", 60000)
    over = sum(1 for s in sizes if s > limit)
    if over:
        warn(f"{over} prompts exceed max_prompt_chars ({limit:,}) and will be "
             "skipped")
    else:
        ok(f"no prompt exceeds max_prompt_chars ({limit:,})")

    # Content checks on a rendered sample.
    rec, chunk = all_chunks[0]
    sample = build_prompt(rec, chunk, g["pairs_per_chunk"])
    for needle, why in [
        ("supporting_span", "span requirement present"),
        ("MUST NOT COPY", "anti-transcription instruction present"),
        ("BAD", "worked example present"),
    ]:
        if needle in sample:
            ok(why)
        else:
            fail(f"prompt is missing {needle!r} -- {why}")


# --- 7. resume state -------------------------------------------------------


def check_resume(cfg: dict, records: list[dict], all_chunks: list) -> tuple:
    section("7. RESUME STATE")
    g = cfg["generate"]
    out = Path(g["output"])
    if not out.exists():
        ok("no existing output; this will be a fresh run")
        return set(), all_chunks

    pairs, bad = [], 0
    for line in out.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        try:
            pairs.append(json.loads(line))
        except json.JSONDecodeError:
            bad += 1
    if bad:
        warn(f"{bad} unparseable lines in {out.name} (truncated writes); "
             "they will be ignored")

    done = {p["cluster_id"] for p in pairs if p.get("generator") == g["model"]}
    other = {p.get("generator") for p in pairs} - {g["model"]}
    ok(f"{len(pairs)} pairs already generated across {len(done)} opinions")
    if other:
        warn(f"output also contains pairs from other generators: {other}. "
             "Resume only skips opinions done by the CURRENT model.")

    remaining = [(r, c) for r, c in all_chunks if r["cluster_id"] not in done]
    ok(f"{len(records) - len(done)} opinions remain "
       f"({len(remaining)} chunks)")
    return done, remaining


# --- 8. existing data quality ----------------------------------------------


def check_existing_quality(cfg: dict, dataset: Path | None = None) -> None:
    section("8. QUALITY OF EXISTING PAIRS")
    out = dataset or Path(cfg["generate"]["output"])
    print(f"         assessing {out}")
    if not out.exists():
        print("         (no existing output to assess)")
        return

    pairs = []
    for line in out.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if not pairs:
        return

    types = Counter(p.get("question_type") for p in pairs)
    total = len(pairs)
    print("         question types:")
    for t, c in types.most_common():
        print(f"           {t:<18} {c:>6}  {100*c/total:5.1f}%")

    holding_pct = 100 * types.get("holding", 0) / total
    if holding_pct < 14:
        fail(f"holdings are {holding_pct:.1f}% -- below the 11.8% baseline of "
             "the earlier pipeline. The banding fix is not taking effect.")
    else:
        ok(f"holdings at {holding_pct:.1f}% (earlier pipeline: 11.8%)")

    dominant = types.most_common(1)[0]
    if 100 * dominant[1] / total > 70:
        warn(f"{dominant[0]} is {100*dominant[1]/total:.1f}% of the dataset "
             "-- very unbalanced")

    with_span = sum(1 for p in pairs if p.get("supporting_span"))
    if with_span != total:
        fail(f"{total - with_span} pairs have no supporting span")
    else:
        ok("every pair carries a supporting span")

    # Categories are copied onto each pair, so check the pairs separately.
    no_cat = sum(1 for p in pairs if not p.get("category"))
    if no_cat:
        fail(f"{no_cat} of {total} pairs ({100*no_cat/total:.1f}%) have no "
             "issue area. Run: python -m uslegalqa.backfill_categories "
             "--scdb <csv> --dataset <dataset>")
    else:
        ok("every pair carries an issue area")

    dupes = total - len({(p["cluster_id"], p.get("question")) for p in pairs})
    if dupes:
        warn(f"{dupes} duplicate (cluster_id, question) pairs -- likely from an "
             "interrupted run; deduplicate before publishing")
    else:
        ok("no duplicate questions within an opinion")


# --- 9. generation gaps ----------------------------------------------------


def check_gaps(cfg: dict, records: list[dict], all_chunks: list,
               dataset: Path | None = None) -> None:
    section("9. INCOMPLETE OPINIONS")
    out = dataset or Path(cfg["generate"]["output"])
    if not out.exists():
        print("         (nothing generated yet)")
        return

    pairs = []
    for line in out.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                continue

    per_opinion = Counter(p["cluster_id"] for p in pairs)
    chunks_per = Counter(c.cluster_id for _, c in all_chunks)

    # Far fewer pairs than chunks suggests an interrupted or failing run.
    thin = []
    for cid, n_pairs in per_opinion.items():
        expected = chunks_per.get(cid, 0)
        if expected >= 3 and n_pairs < expected * 0.5:
            thin.append((cid, n_pairs, expected))

    if thin:
        warn(f"{len(thin)} opinions produced fewer than half the pairs their "
             "chunk count suggests")
        for cid, got, exp in sorted(thin, key=lambda t: t[1])[:8]:
            name = next((r["case_name"] for r in records
                         if r["cluster_id"] == cid), "?")
            print(f"           {name[:44]:<46} {got} pairs / {exp} chunks")
        print("         To regenerate these, remove their cluster_ids from the")
        print("         output file and rerun.")
    else:
        ok("no opinions look incompletely generated")


# --- main ------------------------------------------------------------------


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--dataset", default=None,
                    help="Dataset to assess in sections 8 and 9. Defaults to "
                         "generate.output, which is the generation target and "
                         "may differ from the deduplicated final file used for "
                         "splits and results.")
    args = ap.parse_args()

    cfg_path = Path(args.config)
    if not cfg_path.exists():
        sys.exit(f"config not found: {cfg_path}")
    cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8"))

    print("USLegalQA PREFLIGHT \u2014 no API calls are made by this script")

    check_env()
    check_sources()
    check_config(cfg)
    records = load_corpus(cfg)
    if not records:
        print("\nCannot continue without a corpus.")
        sys.exit(1)

    all_chunks = check_chunking(cfg, records)
    check_prompts(cfg, all_chunks)
    done, remaining = check_resume(cfg, records, all_chunks)
    ds = Path(args.dataset) if args.dataset else None
    check_existing_quality(cfg, ds)
    check_gaps(cfg, records, all_chunks, ds)

    section("PROJECTION FOR THE REMAINING RUN")
    g = cfg["generate"]
    n_chunks = len(remaining)
    candidates = n_chunks * g["pairs_per_chunk"]
    # Observed acceptance across tuned runs was roughly 80%.
    projected = int(candidates * 0.80)
    delay = g.get("request_delay_s", 0.5)
    hours = n_chunks * (delay + 2.5) / 3600

    print(f"  chunks to process        {n_chunks:,}")
    print(f"  candidate pairs          {candidates:,}")
    print(f"  projected verified pairs {projected:,}  (at ~80% acceptance)")
    print(f"  estimated wall time      {hours:.1f} hours")
    print(f"  input tokens (approx)    {n_chunks * 1500:,}")
    print(f"  output tokens (approx)   {n_chunks * 700:,}")

    section("VERDICT")
    if _problems:
        print(f"  {len(_problems)} BLOCKING problem(s). Do not start the run:")
        for p in _problems:
            print(f"    - {p}")
        sys.exit(1)

    if _warnings:
        print(f"  {len(_warnings)} warning(s), none blocking:")
        for w in _warnings:
            print(f"    - {w}")
        print()

    print("  All blocking checks passed.")
    print("\n  Next step \u2014 a small paid smoke test before the full run:")
    print("    python -m uslegalqa.generate --limit 5")
    print("\n  Then start the full run:")
    print("    python -m uslegalqa.generate")


if __name__ == "__main__":
    main()
