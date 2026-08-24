"""Generate span-grounded QA pairs from chunked opinion text.

Generation runs over every chunk, steered by the chunk's position in the
opinion. Every answer carries a supporting span verified against the chunk,
and every record names the model that produced it.

Usage:
    python -m uslegalqa.generate --limit 5 --dry-run     # inspect prompts
    python -m uslegalqa.generate --limit 20              # small live run
    python -m uslegalqa.generate                         # full corpus
    python -m uslegalqa.generate --model claude-sonnet-4-6 --subset 200
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

import yaml

from .chunking import chunk_opinion, POSITION_EARLY, POSITION_MIDDLE, POSITION_LATE

QUESTION_TYPES = ["facts", "procedural", "legal_principle", "holding", "outcome"]

# Which question types suit which part of an opinion.
POSITION_GUIDANCE = {
    POSITION_EARLY: {
        # Opinions usually announce the holding in the opening paragraph.
        "types": ["facts", "procedural", "holding"],
        "hint": ("This passage is from the beginning of the opinion. It most "
                 "likely covers the facts of the dispute, the procedural "
                 "history, and the question presented. Supreme Court opinions "
                 "usually also state the holding in the opening paragraph -- "
                 "if this passage announces what the Court held, generate a "
                 "holding question for it."),
    },
    POSITION_MIDDLE: {
        # Long opinions state intermediate holdings at the end of each Part.
        "types": ["legal_principle", "holding", "facts"],
        "hint": ("This passage is from the body of the opinion. It most likely "
                 "covers the Court's reasoning, statutory or constitutional "
                 "construction, and the legal principles applied. Long opinions "
                 "also resolve sub-issues as they go: if this passage states "
                 "what the Court concludes on a particular point, generate a "
                 "holding question for that conclusion."),
    },
    POSITION_LATE: {
        "types": ["holding", "outcome", "legal_principle"],
        "hint": ("This passage is from the end of the opinion. It most likely "
                 "states the Court's holding, its disposition of the case, and "
                 "any remedy or remand instruction. Prefer questions about "
                 "what the Court decided and why."),
    },
}

PROMPT = """You are a legal expert analysing an opinion of the Supreme Court of the United States.

Generate {n} question-answer pairs from the passage below.

CASE: {case_name}
DECIDED: {date_filed}
CITATION: {citation}
PASSAGE: part {part} of {n_parts}

{position_hint}

REQUIREMENTS
1. Every question must be answerable from this passage alone. Do not use outside knowledge of the case.
2. Every answer must be supported by a span of text quoted EXACTLY from the passage, character for character.
3. Prefer these question types for this passage: {preferred_types}
4. Questions: 10-40 words. Answers: 20-100 words.
5. No yes/no questions.
6. Do not ask about dates, case names, or which Justice wrote the opinion.

7. THE ANSWER MUST NOT COPY THE SUPPORTING SPAN.
   The span is your evidence; the answer is your explanation of it. Write the
   answer as a legal analyst would explain the point to a colleague -- restate
   the reasoning in different words, and where the passage gives a rule and its
   justification, state both.

   BAD  (copies the span)
     span:   "a vessel is any watercraft practically capable of maritime
              transportation, regardless of its primary purpose"
     answer: "A vessel is any watercraft practically capable of maritime
              transportation, regardless of its primary purpose."

   GOOD (explains the span)
     span:   "a vessel is any watercraft practically capable of maritime
              transportation, regardless of its primary purpose"
     answer: "The Court adopted a capability-based test: what matters is
              whether the craft can be used for transportation on water, not
              what it was built for or whether it was moving at the time.
              This replaced the narrower purpose-driven approach."

8. Prefer questions that require understanding WHY the Court reached a result,
   not merely WHAT it said. Questions beginning "Why did the Court...",
   "On what basis...", "How did the Court distinguish..." are better than
   questions answerable by locating one sentence.

9. If the passage is procedural boilerplate, a table of authorities, or
   otherwise has no substantive legal content, return an empty list.

PASSAGE
\"\"\"
{chunk_text}
\"\"\"

Return ONLY valid JSON, with no surrounding text or code fences:
{{
  "qa_pairs": [
    {{
      "question": "...",
      "answer": "...",
      "question_type": "facts|procedural|legal_principle|holding|outcome",
      "supporting_span": "exact quotation from the passage"
    }}
  ]
}}"""


# --- span verification -----------------------------------------------------

_WS = re.compile(r"\s+")

# Typographic variants (curly quotes, dashes, "U. S. C." spacing) are not
# fabrication, so they are normalised before comparison.
_PUNCT_MAP = str.maketrans({
    "\u201c": '"', "\u201d": '"', "\u2018": "'", "\u2019": "'",
    "\u2013": "-", "\u2014": "-", "\u2212": "-", "\u00a0": " ",
})
# Collapse spaces inside abbreviations: "U. S. C." -> "U.S.C."
_ABBREV = re.compile(r"\b([A-Z])\.\s+(?=[A-Z]\.)")
_ELLIPSIS = re.compile(r"\s*(?:\.\s*\.\s*\.|\u2026)\s*")


def normalise(text: str) -> str:
    """Collapse whitespace and typographic variants for tolerant comparison."""
    t = (text or "").translate(_PUNCT_MAP)
    t = _WS.sub(" ", t).strip()
    t = _ABBREV.sub(r"\1.", t)
    return t


_WORD_RE = re.compile(r"[A-Za-z0-9\u00a7]+")
# Editorial brackets are removed rather than treated as separators, so that
# "[T]he" is the word "the", not the tokens "t" and "he".
_BRACKET = re.compile(r"[\[\]]")


def _words(text: str) -> list[str]:
    """Lowercased word tokens, ignoring all punctuation."""
    return _WORD_RE.findall(_BRACKET.sub("", (text or "").lower()))


def _words_with_offsets(text: str) -> list[tuple[str, int, int]]:
    """(token, char_start, char_end) for each word, bracket-insensitive.

    Offsets refer to the ORIGINAL text, so a matched span can be sliced back
    out of the source exactly as written.
    """
    text = text or ""
    out: list[tuple[str, int, int]] = []
    buf: list[str] = []
    start = None
    for i, ch in enumerate(text):
        if _BRACKET.match(ch):
            continue
        if _WORD_RE.match(ch):
            if start is None:
                start = i
            buf.append(ch.lower())
        elif buf:
            out.append(("".join(buf), start, i))
            buf, start = [], None
    if buf:
        out.append(("".join(buf), start, len(text)))
    return out


# Footnote markers attached after punctuation ("do so.5 See ...") that a
# model correctly omits when quoting.
_FOOTNOTE_MARKER = re.compile(r"(?<=[.,;:\u201d\"\'])\d{1,3}(?=\s|$)")

# Star pagination markers embedded mid-sentence ("rather *218 than", "[218]").
# Only explicitly marked forms are stripped: bare numbers may be substantive
# figures, and removing them would let an altered number pass verification.
_STAR_PAGE = re.compile(r"\*\s?\d{1,4}|\[\s?\d{1,4}\s?\]")


def _strip_footnote_markers(text: str) -> str:
    """Blank out footnote and star-pagination digits.

    Replacement preserves length so character offsets remain valid and a
    matched span can still be sliced out of the original source text.
    """
    text = _FOOTNOTE_MARKER.sub(lambda m: " " * len(m.group(0)), text or "")
    return _STAR_PAGE.sub(lambda m: " " * len(m.group(0)), text)


def _char_stream(text: str, strip_footnotes: bool = False) -> tuple[str, list[int]]:
    """Lowercased alphanumeric characters, with a map back to original offsets.

    Separators are dropped, but character order is still enforced, so
    paraphrase, substitution and reordering all fail.
    """
    source = _strip_footnote_markers(text) if strip_footnotes else (text or "")
    chars: list[str] = []
    offsets: list[int] = []
    for i, ch in enumerate(source):
        if ch.isalnum() or ch == "\u00a7":
            chars.append(ch.lower())
            offsets.append(i)
    return "".join(chars), offsets


def _elided_parts(span: str) -> list[str] | None:
    """Split a span on ellipsis, if it contains one.

    Each part is verified separately and in order.
    """
    if not _ELLIPSIS.search(span):
        return None
    parts = [p.strip() for p in _ELLIPSIS.split(span) if p.strip()]
    return parts if len(parts) > 1 else None


def locate_span(span: str, chunk_text: str) -> tuple[int, int] | None:
    """Find `span` in `chunk_text`, returning character offsets or None.

    Tries an exact match, then per-part matching across ellipses, then an
    alphanumeric character-stream match that tolerates punctuation, bracket
    and spacing differences while still rejecting paraphrase and reordering.
    """
    if not span or not span.strip():
        return None

    idx = chunk_text.find(span)
    if idx >= 0:
        return idx, idx + len(span)

    parts = _elided_parts(span)
    if parts:
        spans = []
        cursor = 0
        ok = True
        for part in parts:
            found = locate_span(part, chunk_text[cursor:])
            if found is None:
                ok = False
                break
            spans.append((cursor + found[0], cursor + found[1]))
            cursor += found[1]
        if ok:
            return spans[0][0], spans[-1][1]
        # Elision alignment failed -- fall through to character matching.

    # Final fallback: compare alphanumeric character streams, which tolerates
    # extraction artifacts where the source lost a space ("conspicuousand").
    span_chars, _ = _char_stream(span)
    if not span_chars:
        return None

    chunk_chars, chunk_map = _char_stream(chunk_text)
    pos = chunk_chars.find(span_chars)

    if pos < 0:
        # Retry with footnote markers removed from BOTH sides.
        span_chars, _ = _char_stream(span, strip_footnotes=True)
        chunk_chars, chunk_map = _char_stream(chunk_text, strip_footnotes=True)
        pos = chunk_chars.find(span_chars)

    if pos < 0 or not span_chars:
        return None

    start = chunk_map[pos]
    end = chunk_map[pos + len(span_chars) - 1] + 1
    return start, end


# --- generation ------------------------------------------------------------


_BAD_UNICODE = re.compile(
    r"[\ud800-\udfff]"           # unpaired surrogates
    r"|[\x00-\x08\x0b\x0c\x0e-\x1f]"   # control characters
    r"|\ufffe|\uffff"             # non-characters
)


def sanitise(text: str) -> str:
    """Remove characters that cannot survive JSON transport.

    Unpaired surrogates and control characters cause the API to reject the
    request with HTTP 400.
    """
    text = _BAD_UNICODE.sub(" ", text or "")
    return text.encode("utf-8", "ignore").decode("utf-8", "ignore")


def build_prompt(rec: dict, chunk, n_pairs: int) -> str:
    guidance = POSITION_GUIDANCE[chunk.position]
    return PROMPT.format(
        n=n_pairs,
        case_name=sanitise(rec.get("case_name", "Unknown")),
        date_filed=rec.get("date_filed", "Unknown"),
        citation=rec.get("citation") or "not available",
        part=chunk.chunk_index + 1,
        n_parts=chunk.n_chunks,
        position_hint=guidance["hint"],
        preferred_types=", ".join(guidance["types"]),
        chunk_text=sanitise(chunk.text),
    )


def parse_response(raw: str) -> list[dict]:
    """Extract the qa_pairs list from a model response."""
    text = raw.strip()
    if "```" in text:
        parts = text.split("```")
        for part in parts:
            candidate = part[4:] if part.startswith("json") else part
            candidate = candidate.strip()
            if candidate.startswith("{"):
                text = candidate
                break
    start, end = text.find("{"), text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("no JSON object in response")
    return json.loads(text[start:end + 1]).get("qa_pairs", [])


def call_model(client, model: str, prompt: str, max_tokens: int,
               temperature: float, max_retries: int = 6) -> list[dict]:
    """Call the generation model, returning parsed pairs or an empty list.

    Transient faults are retried with exponential backoff; permanent ones
    return immediately.
    """
    import anthropic

    for attempt in range(max_retries):
        try:
            resp = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[{"role": "user", "content": prompt}],
            )
            return parse_response(resp.content[0].text)

        except (json.JSONDecodeError, ValueError) as e:
            print(f"      parse error ({str(e)[:60]}); retry {attempt + 1}",
                  file=sys.stderr)
            time.sleep(2)

        except anthropic.RateLimitError:
            wait = min(20 * (attempt + 1), 120)
            print(f"      rate limited; waiting {wait}s", file=sys.stderr)
            time.sleep(wait)

        except (anthropic.APITimeoutError, anthropic.APIConnectionError) as e:
            wait = min(2 ** attempt * 5, 120)
            print(f"      connection problem ({e.__class__.__name__}); "
                  f"retry {attempt + 1} in {wait}s", file=sys.stderr)
            time.sleep(wait)

        except anthropic.APIStatusError as e:
            status = getattr(e, "status_code", None)
            if status == 400:
                detail = str(getattr(e, "message", "") or e)
                # Account-level faults will fail every request, so stop.
                low = detail.lower()
                if "credit balance" in low or "billing" in low or "quota" in low:
                    raise SystemExit(
                        "\nStopped: the API account is out of credit.\n"
                        "  " + detail[:200] + "\n"
                        "Top up at https://console.anthropic.com/settings/billing\n"
                        "then rerun the same command -- completed opinions are "
                        "skipped automatically."
                    )
                print(f"      HTTP 400 [{len(prompt)} chars]: {detail[:250]}",
                      file=sys.stderr)
                return []
            if status in (401, 403):
                raise SystemExit(f"Authentication failed (HTTP {status}). "
                                 "Check ANTHROPIC_API_KEY.")
            wait = min(2 ** attempt * 5, 120)
            print(f"      API error {status}; retry {attempt + 1} in {wait}s",
                  file=sys.stderr)
            time.sleep(wait)

        except Exception as e:  # noqa: BLE001 - a long run must not die here
            wait = min(2 ** attempt * 5, 120)
            print(f"      unexpected error ({e.__class__.__name__}: "
                  f"{str(e)[:60]}); retry {attempt + 1} in {wait}s",
                  file=sys.stderr)
            time.sleep(wait)

    print("      giving up on this chunk after "
          f"{max_retries} attempts", file=sys.stderr)
    return []


def _longest_shared_run(answer: str, span: str) -> int:
    """Longest run of consecutive words the answer shares with the span.

    Run length, unlike bag-of-words overlap, separates copied answers from
    explanatory ones that quote a few terms of art.
    """
    a, s = _words(answer), _words(span)
    if not a or not s:
        return 0
    # Longest common substring over word tokens.
    prev = [0] * (len(s) + 1)
    best = 0
    for i in range(1, len(a) + 1):
        cur = [0] * (len(s) + 1)
        for j in range(1, len(s) + 1):
            if a[i - 1] == s[j - 1]:
                cur[j] = prev[j - 1] + 1
                best = max(best, cur[j])
        prev = cur
    return best


def validate(pair: dict, rec: dict, chunk, cfg: dict) -> tuple[dict | None, str]:
    """Turn a raw generated pair into a dataset record, or reject it."""
    g = cfg["generate"]
    question = (pair.get("question") or "").strip()
    answer = (pair.get("answer") or "").strip()
    span = (pair.get("supporting_span") or "").strip()
    qtype = (pair.get("question_type") or "").strip().lower()

    if not question or not answer:
        return None, "empty_field"

    qw, aw = len(question.split()), len(answer.split())
    if not (g["min_question_words"] <= qw <= g["max_question_words"]):
        return None, "question_length"
    if not (g["min_answer_words"] <= aw <= g["max_answer_words"]):
        return None, "answer_length"
    # Strip punctuation so "Yes, the Court held..." is caught.
    first = re.sub(r"[^a-z]", "", answer.lower().split()[0])
    if first in {"yes", "no", "true", "false"}:
        return None, "yes_no_answer"
    if qtype not in QUESTION_TYPES:
        return None, "bad_question_type"

    located = locate_span(span, chunk.text)
    if located is None:
        return None, "span_not_found"

    # Reject answers that merely reproduce the span.
    max_run = g.get("max_copied_run_words")
    if max_run is not None and _longest_shared_run(answer, span) > max_run:
        return None, "answer_copies_span"

    rel_start, rel_end = located
    if (rel_end - rel_start) < g["min_span_chars"]:
        return None, "span_too_short"

    # Offsets relative to the full opinion, not just the chunk.
    abs_start = chunk.char_start + rel_start
    abs_end = chunk.char_start + rel_end

    return {
        "cluster_id": rec["cluster_id"],
        "case_name": rec["case_name"],
        "date_filed": rec["date_filed"],
        "citation": rec.get("citation"),
        # "scdb_category" is the pre-cleaning name of the same field.
        "category": rec.get("category") or rec.get("scdb_category"),
        "scdb_id": rec.get("scdb_id"),
        "question": question,
        "answer": answer,
        "question_type": qtype,
        "supporting_span": chunk.text[rel_start:rel_end],
        # The model's own quotation, kept so verification can be recomputed.
        "generated_span": span,
        "span_start": abs_start,
        "span_end": abs_end,
        "chunk_index": chunk.chunk_index,
        "n_chunks": chunk.n_chunks,
        "chunk_position": chunk.position,
        "generator": cfg["generate"]["model"],
        "generator_temperature": cfg["generate"]["temperature"],
    }, "ok"


def run(cfg: dict, limit: int | None, subset: int | None,
        dry_run: bool, seed: int) -> None:
    g = cfg["generate"]
    cleaned = Path(cfg["paths"]["cleaned"])
    out_path = Path(g["output"])
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records = [json.loads(l) for l in cleaned.read_text(encoding="utf-8").splitlines()
               if l.strip()]

    if subset:
        rng = random.Random(seed)
        records = rng.sample(records, min(subset, len(records)))
        print(f"Random subset of {len(records)} opinions (seed {seed})")
    if limit:
        records = records[:limit]

    # Resume: skip opinions already generated by THIS model.
    done: set[int] = set()
    if out_path.exists():
        with out_path.open(encoding="utf-8") as f:
            for line in f:
                try:
                    d = json.loads(line)
                    if d.get("generator") == g["model"]:
                        done.add(d["cluster_id"])
                except (json.JSONDecodeError, KeyError):
                    continue
        if done:
            print(f"Resuming: {len(done)} opinions already done for {g['model']}")

    todo = [r for r in records if r["cluster_id"] not in done]
    all_chunks = [(r, c) for r in todo
                  for c in chunk_opinion(r["text"], r["cluster_id"],
                                         target_words=g["chunk_words"],
                                         overlap_words=g["chunk_overlap"])]
    print(f"{len(todo)} opinions -> {len(all_chunks)} chunks "
          f"(~{len(all_chunks) * g['pairs_per_chunk']} candidate pairs)\n")

    if dry_run:
        for rec, chunk in all_chunks[:3]:
            print("=" * 74)
            print(build_prompt(rec, chunk, g["pairs_per_chunk"])[:1800])
            print()
        print(f"[dry run] {len(all_chunks)} chunks would be sent to "
              f"{g['model']}")
        return

    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic is required:  pip install anthropic")

    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        sys.exit("ANTHROPIC_API_KEY is not set (see .env.example)")
    client = anthropic.Anthropic(api_key=api_key)

    rejects: Counter = Counter()
    types: Counter = Counter()
    positions: Counter = Counter()
    kept = 0
    current_id = None
    consecutive_empty = 0
    empty_limit = g.get("abort_after_empty_chunks", 25)

    with out_path.open("a", encoding="utf-8") as out:
        for i, (rec, chunk) in enumerate(all_chunks, 1):
            if rec["cluster_id"] != current_id:
                current_id = rec["cluster_id"]
                print(f"[{i}/{len(all_chunks)}] {rec['case_name'][:52]}")

            prompt = build_prompt(rec, chunk, g["pairs_per_chunk"])

            # Oversized prompts come from unsplittable runs (e.g. appendices)
            # and would be rejected by the API, so skip them.
            max_chars = g.get("max_prompt_chars", 60000)
            if len(prompt) > max_chars:
                rejects["prompt_too_long"] += 1
                print(f"      skipping oversized chunk "
                      f"({len(prompt):,} chars > {max_chars:,})", file=sys.stderr)
                continue

            pairs = call_model(client, g["model"], prompt,
                               g["max_tokens"], g["temperature"])

            if pairs:
                consecutive_empty = 0
            else:
                consecutive_empty += 1
                if consecutive_empty >= empty_limit:
                    raise SystemExit(
                        f"\nStopped: {consecutive_empty} consecutive chunks "
                        f"produced nothing.\nThis indicates a systemic fault "
                        f"rather than a data problem -- check the errors above.\n"
                        f"Progress is saved; rerun to resume."
                    )

            for pair in pairs:
                record, reason = validate(pair, rec, chunk, cfg)
                if record is None:
                    rejects[reason] += 1
                    continue
                out.write(json.dumps(record, ensure_ascii=False) + "\n")
                kept += 1
                types[record["question_type"]] += 1
                positions[record["chunk_position"]] += 1

            out.flush()
            time.sleep(g["request_delay_s"])

    print(f"\nGenerated {kept} verified QA pairs -> {out_path}")
    if types:
        print("\nQuestion types:")
        for t, n in types.most_common():
            print(f"  {t:<20} {n:>6}  {100*n/kept:>5.1f}%")
    if positions:
        print("\nBy position in opinion:")
        for p, n in positions.most_common():
            print(f"  {p:<20} {n:>6}  {100*n/kept:>5.1f}%")
    if rejects:
        total_rej = sum(rejects.values())
        print(f"\nRejected {total_rej} candidates "
              f"({100*total_rej/(total_rej+kept):.1f}%):")
        for r, n in rejects.most_common():
            print(f"  {r:<20} {n:>6}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--limit", type=int, default=None,
                    help="Only the first N opinions.")
    ap.add_argument("--subset", type=int, default=None,
                    help="Random sample of N opinions (for a second generator).")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--model", default=None, help="Override the model.")
    ap.add_argument("--output", default=None, help="Override the output path.")
    ap.add_argument("--dry-run", action="store_true",
                    help="Print prompts without calling the API.")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    if args.model:
        cfg["generate"]["model"] = args.model
    if args.output:
        cfg["generate"]["output"] = args.output

    run(cfg, args.limit, args.subset, args.dry_run, args.seed)


if __name__ == "__main__":
    main()
