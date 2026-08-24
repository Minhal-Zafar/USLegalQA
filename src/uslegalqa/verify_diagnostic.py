"""Re-measure span verification (Table 4.2) and the copy filter on retained output.

Regenerates a fixed random sample with the production prompt, model and
temperature, keeps every candidate pair verbatim, and scores it.

Four cumulative verification methods (a span located by an earlier method
counts as located by every later one):

  exact       the quotation occurs verbatim in the window
  normalised  + whitespace, curly quotes, dashes and Reports abbreviation
              spacing normalised on both sides
  word        + word-sequence matching: the span's words, punctuation and
              brackets ignored, appear contiguously and in order (elided
              quotations matched part by part)
  artefact    + the production matcher (generate.locate_span): alphanumeric
              character stream, with footnote and star-pagination markers
              removed

Candidates the production matcher rejects are written to a review file for
hand classification. Every validate() rejection reason is also reported.

Usage:
    python -m uslegalqa.verify_diagnostic generate --opinions 30 --seed 7
    python -m uslegalqa.verify_diagnostic score
    python -m uslegalqa.verify_diagnostic classify   # evidence-based suggestions
    # then fill "classification" in the review file by hand, and re-run score
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
from collections import Counter
from pathlib import Path

import yaml

from .chunking import chunk_opinion
from .generate import (build_prompt, call_model, locate_span, normalise,
                       validate, _words, _elided_parts)

OUT_DIR = Path("data/diagnostic")
RAW = OUT_DIR / "candidates.jsonl"
REPORT = OUT_DIR / "verification_report.json"
REVIEW = OUT_DIR / "failures_for_review.jsonl"

METHODS = ("exact", "normalised", "word", "artefact")


def m_exact(span: str, text: str) -> bool:
    return bool(span) and span in text


def m_normalised(span: str, text: str) -> bool:
    s = normalise(span)
    return bool(s) and s in normalise(text)


def _word_seq(span: str, text: str) -> bool:
    sw = _words(span)
    if not sw:
        return False
    return f" {' '.join(sw)} " in f" {' '.join(_words(text))} "


def m_word(span: str, text: str) -> bool:
    if _word_seq(span, text):
        return True
    parts = _elided_parts(span)
    if not parts:
        return False
    # Each elided part must appear, in order.
    tw = " " + " ".join(_words(text)) + " "
    cursor = 0
    for part in parts:
        needle = " " + " ".join(_words(part)) + " "
        if needle.strip() == "":
            return False
        pos = tw.find(needle, cursor)
        if pos < 0:
            return False
        cursor = pos + len(needle) - 1
    return True


def m_artefact(span: str, text: str) -> bool:
    return locate_span(span, text) is not None


def cumulative(span: str, text: str) -> dict[str, bool]:
    out, hit = {}, False
    for name, fn in zip(METHODS, (m_exact, m_normalised, m_word, m_artefact)):
        hit = hit or fn(span, text)
        out[name] = hit
    return out


# Scoring must re-create the windows the seed-7 sample was cut from, so the
# corpus is frozen at that state (wrong-document exclusions only).
_SAMPLE_EXCLUSIONS = {"wrong_case", "not_merits", "unsegmented"}


def load_corpus(cfg: dict) -> list[dict]:
    excluded_path = Path("data/dataset/excluded_opinions.json")
    excluded = ({int(k) for k, v in json.loads(excluded_path.read_text()).items()
                 if set(v["reasons"]) & _SAMPLE_EXCLUSIONS}
                if excluded_path.exists() else set())
    recs = [json.loads(l) for l in
            Path(cfg["paths"]["cleaned"]).read_text(encoding="utf-8").splitlines()
            if l.strip()]
    return [r for r in recs if r["cluster_id"] not in excluded]


def windows(cfg: dict, rec: dict):
    g = cfg["generate"]
    return chunk_opinion(rec["text"], rec["cluster_id"],
                         target_words=g["chunk_words"],
                         overlap_words=g["chunk_overlap"])


def generate(cfg: dict, n_opinions: int, seed: int) -> None:
    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass
    import anthropic
    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    client = anthropic.Anthropic(api_key=key)
    g = cfg["generate"]

    corpus = load_corpus(cfg)
    sample = random.Random(seed).sample(corpus, n_opinions)

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    done = set()
    if RAW.exists():
        for line in RAW.read_text(encoding="utf-8").splitlines():
            d = json.loads(line)
            done.add((d["cluster_id"], d["chunk_index"]))

    jobs = [(r, c) for r in sample for c in windows(cfg, r)
            if (r["cluster_id"], c.chunk_index) not in done]
    print(f"{n_opinions} opinions (seed {seed}); {len(jobs)} windows to generate "
          f"with {g['model']} at T={g['temperature']}")

    with RAW.open("a", encoding="utf-8") as out:
        for i, (rec, chunk) in enumerate(jobs, 1):
            prompt = build_prompt(rec, chunk, g["pairs_per_chunk"])
            if len(prompt) > g.get("max_prompt_chars", 60000):
                continue
            pairs = call_model(client, g["model"], prompt,
                               g["max_tokens"], g["temperature"])
            # Record the window even when it yielded nothing, so resume works.
            out.write(json.dumps({
                "cluster_id": rec["cluster_id"], "case_name": rec["case_name"],
                "chunk_index": chunk.chunk_index, "model": g["model"],
                "temperature": g["temperature"], "seed": seed,
                "pairs": pairs}, ensure_ascii=False) + "\n")
            out.flush()
            if i % 10 == 0 or i == len(jobs):
                print(f"  [{i}/{len(jobs)}] {rec['case_name'][:50]}")


def _clopper_pearson(k: int, n: int, alpha: float = 0.05) -> tuple[float, float]:
    from scipy.stats import beta
    lo = 0.0 if k == 0 else beta.ppf(alpha / 2, k, n - k + 1)
    hi = 1.0 if k == n else beta.ppf(1 - alpha / 2, k + 1, n - k)
    return float(lo), float(hi)


def score(cfg: dict) -> None:
    corpus = {r["cluster_id"]: r for r in load_corpus(cfg)}
    rows = [json.loads(l) for l in RAW.read_text(encoding="utf-8").splitlines()
            if l.strip()]

    candidates, located = 0, Counter()
    reasons: Counter = Counter()
    review = []
    opinions = set()
    for row in rows:
        rec = corpus[row["cluster_id"]]
        chunk = next(c for c in windows(cfg, rec)
                     if c.chunk_index == row["chunk_index"])
        opinions.add(row["cluster_id"])
        for pair in row["pairs"]:
            span = (pair.get("supporting_span") or "").strip()
            if not span:
                reasons["no_span"] += 1
                continue
            candidates += 1
            hits = cumulative(span, chunk.text)
            for m in METHODS:
                located[m] += hits[m]
            if not hits["artefact"]:
                review.append({
                    "cluster_id": row["cluster_id"], "case_name": row["case_name"],
                    "chunk_index": row["chunk_index"],
                    "question": pair.get("question"), "span": span,
                    "window": chunk.text,
                    "classification": None})   # to be filled by hand
            _, reason = validate(pair, rec, chunk, cfg)
            reasons[reason] += 1

    report = {
        "opinions": len(opinions),
        "windows": len(rows),
        "candidates_with_span": candidates,
        "apparent_failure_pct": {
            m: round(100 * (candidates - located[m]) / candidates, 1)
            for m in METHODS},
        "validate_outcomes": dict(reasons.most_common()),
        "review_file": str(REVIEW),
        "failures_to_classify": len(review),
    }
    review = _merge_review(review)
    REVIEW.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n"
                              for r in review), encoding="utf-8")
    # Report a fabrication rate only once a human has classified every failure.
    if review and all(r.get("classification") for r in review):
        report.update(_classified(candidates))
    else:
        report["fabrication"] = "pending classification"
    REPORT.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(json.dumps(report, indent=2))


# Evidence-based pre-classification: a failed span is split into maximal
# verbatim in-order pieces; the source text between pieces suggests the class.

_BRACKETED = re.compile(r"\[[^\]]*\]")
_FURNITURE = re.compile(
    r"Cite as:|Opinion of the Court|OPINION OF THE COURT|——|^\s*\d{1,3}\s*$"
    r"|\b[A-Z][A-Z.&' ]+ v\. [A-Z]|Syllabus|SUPREME COURT OF THE UNITED STATES",
    re.MULTILINE)
_CITATION = re.compile(
    r"\bU\. ?S\.|\bF\. ?(?:\d?d|Supp)|S\. ?Ct\.|L\. ?Ed\.|\bsupra\b|\bid\.|\bIbid\b"
    r"|\bStat\.|\bApp\.|\bslip op\b|\bn\. \d|\bat \d|§|\bet seq\b|\bv\. |\bcert\. denied"
    r"|\(\d{4}\)|\bCFR\b|\bU\. ?S\. ?C\.|\bFed\. ?Appx|\bquoting\b|\bcitation",
    re.IGNORECASE)
MIN_PIECE = 12


def _pieces(span: str, text: str) -> tuple[list[tuple[int, int]], int]:
    """Greedy in-order cover of span chars by source substrings.

    Returns source (start, end) offsets of each piece, in ORIGINAL text
    coordinates, and the number of span characters no piece covers.
    """
    from .generate import _char_stream
    s, _ = _char_stream(_BRACKETED.sub(" ", span), strip_footnotes=True)
    t, tmap = _char_stream(text, strip_footnotes=True)
    i, cursor, pieces, uncovered = 0, 0, [], 0
    while i < len(s):
        lo, hi, best = MIN_PIECE, len(s) - i, None
        while lo <= hi:
            m = (lo + hi) // 2
            pos = t.find(s[i:i + m], cursor)
            if pos >= 0:
                best, lo = (pos, m), m + 1
            else:
                hi = m - 1
        if best is None:
            uncovered += 1
            i += 1
            continue
        pos, m = best
        pieces.append((tmap[pos], tmap[pos + m - 1] + 1))
        cursor, i = pos + m, i + m
    return pieces, uncovered


_EDITORIAL = re.compile(r"\[[^\]]{0,40}\]")
_ENCODING = re.compile(r"[\x80-\x9f]|Ã|Ô|â€|&amp;|&[a-z]+;")
_FOOTNOTE_BODY = re.compile(r"\n\s*\d{1,3} (?:[A-Z]|See|The|In|This|Id)")


def _gap_kind(g: str) -> str:
    """What occupies a gap between two verbatim pieces of a quotation."""
    residue = _EDITORIAL.sub("", g)
    if "[" in g and len(re.sub(r"[\W_]", "", residue)) <= 6:
        return "editorial_brackets"      # [T]he, [the IDEA]: quoting convention
    if _ENCODING.search(g) and len(re.sub(r"[\W_]", "", g)) <= 6:
        return "encoding_artefact"       # \x9e for §, mojibake dashes, &amp;
    if _FURNITURE.search(g) or _FOOTNOTE_BODY.search(g):
        return "page_furniture"
    if _CITATION.search(g) and len(g) < 400:
        return "citation_omitted"
    return "prose_omitted"


def suggest(span: str, window: str) -> tuple[str, str]:
    pieces, uncovered = _pieces(span, window)
    marked_elisions = len(re.findall(r"\.\s*\.\s*\.|…", span))
    # Short verbatim pieces below MIN_PIECE can leave a few characters
    # uncovered; only a longer run suggests wording absent from the window.
    if uncovered > 12:
        return "review_possible_fabrication", f"{uncovered} span characters occur nowhere in order in the window"
    gaps = [window[a_end:b_start] for (_, a_end), (b_start, _) in zip(pieces, pieces[1:])
            if b_start - a_end > 2]
    kinds = [_gap_kind(g) for g in gaps]
    unmarked_prose = max(0, kinds.count("prose_omitted") - marked_elisions)
    if unmarked_prose:
        return "unmarked_omission_of_prose", f"{unmarked_prose} unmarked gap(s) of running text; first: {gaps[kinds.index('prose_omitted')][:160]!r}"
    if "citation_omitted" in kinds:
        return "citation_omitted", f"{kinds.count('citation_omitted')} inline citation(s) dropped without marking"
    if "page_furniture" in kinds:
        return "page_furniture", "running header, page number or footnote text interrupts the quoted prose"
    if "encoding_artefact" in kinds:
        return "encoding_artefact", "source text has a character-encoding fault the model quoted correctly"
    if "editorial_brackets" in kinds:
        return "editorial_brackets", "source quotation carries bracketed alterations the model reproduced differently"
    return "matcher_gap_other", f"verbatim in order; {uncovered} uncovered chars"


def classify() -> None:
    rows = _existing_review()
    counts = Counter()
    for r in rows:
        r["suggested"], r["evidence"] = suggest(r["span"], r["window"])
        counts[r["suggested"]] += 1
    REVIEW.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                      encoding="utf-8")
    print(dict(counts.most_common()))


def _existing_review() -> list[dict]:
    if not REVIEW.exists():
        return []
    return [json.loads(l) for l in REVIEW.read_text(encoding="utf-8").splitlines()
            if l.strip()]


def _merge_review(fresh: list[dict]) -> list[dict]:
    """Keep hand classifications already entered for the same failure."""
    old = {(r["cluster_id"], r["chunk_index"], r["span"]): r
           for r in _existing_review()}
    for r in fresh:
        prev = old.get((r["cluster_id"], r["chunk_index"], r["span"]), {})
        for k in ("classification", "suggested", "evidence",
                  "classification_note", "classified_by"):
            r[k] = prev.get(k)
    return fresh


# Classes in which the quotation is not faithful to the source window;
# "fabrication" alone is the strict sense (wording the source does not contain).
UNFAITHFUL = ("fabrication", "misquotation", "from_memory")


def _rate(k: int, n: int) -> dict:
    lo, hi = _clopper_pearson(k, n)
    return {"count": k, "pct": round(100 * k / n, 2),
            "ci95_pct": [round(100 * lo, 2), round(100 * hi, 2)]}


def _classified(candidates: int) -> dict:
    cls = Counter(r["classification"] for r in _existing_review())
    return {"classification": dict(cls.most_common()),
            "fabrication": _rate(cls.get("fabrication", 0), candidates),
            "unfaithful_quotation": _rate(sum(cls.get(c, 0) for c in UNFAITHFUL),
                                          candidates),
            "unmarked_omission": _rate(cls.get("unmarked_omission", 0), candidates)}


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("step", choices=("generate", "score", "classify"))
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--opinions", type=int, default=30)
    ap.add_argument("--seed", type=int, default=7)
    args = ap.parse_args()
    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.step == "generate":
        generate(cfg, args.opinions, args.seed)
    elif args.step == "score":
        score(cfg)
    else:
        classify()


if __name__ == "__main__":
    main()
