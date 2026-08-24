"""Assess whether generated questions are legally substantive.

Two measures: automatic signals over the whole dataset (trivial patterns,
legal-term density, reasoning stems, answer-span overlap), and an LLM-as-judge
rubric on a sample, ideally using a model other than the generator.

Usage:
    python -m uslegalqa.assess_quality --auto-only
    python -m uslegalqa.assess_quality --sample 150 --judge claude-sonnet-4-6
"""

from __future__ import annotations

import argparse
import json
import os
import random
import re
import statistics
import sys
from collections import Counter
from pathlib import Path

import yaml

# --- automatic signals -----------------------------------------------------

# Questions answerable from metadata rather than the reasoning.
TRIVIAL_PATTERNS = [
    (re.compile(r"\bwhat (?:year|date|day)\b", re.I), "asks_date"),
    (re.compile(r"\bwho (?:wrote|authored|delivered)\b", re.I), "asks_author"),
    (re.compile(r"\bwhich (?:justice|judge)\b", re.I), "asks_justice"),
    (re.compile(r"\bwhat (?:is|was) the (?:case )?(?:name|citation|docket)\b", re.I),
     "asks_case_name"),
    (re.compile(r"\bhow many (?:justices|votes|pages)\b", re.I), "asks_vote_count"),
    (re.compile(r"\bwhat court\b", re.I), "asks_court"),
]

# Openings that tend to produce recall rather than reasoning.
SHALLOW_OPENERS = [
    (re.compile(r"^what does the (?:passage|text|excerpt) (?:say|state)", re.I),
     "meta_reference"),
    (re.compile(r"^according to the (?:passage|text)", re.I), "meta_reference"),
    (re.compile(r"^what (?:is|are) mentioned", re.I), "mere_mention"),
]

# Doctrinal vocabulary; its absence signals a superficial question.
LEGAL_TERMS = {
    "holding", "held", "precedent", "stare", "decisis", "statutory",
    "construction", "constitutional", "doctrine", "standard", "review",
    "burden", "proof", "jurisdiction", "remand", "reversed", "affirmed",
    "certiorari", "dissent", "concurrence", "plaintiff", "defendant",
    "petitioner", "respondent", "appellant", "appellee", "liability",
    "damages", "injunction", "remedy", "due", "process", "equal",
    "protection", "commerce", "clause", "amendment", "statute", "regulation",
    "preemption", "preempt", "deference", "chevron", "scrutiny", "rational",
    "basis", "strict", "intermediate", "test", "prong", "element",
    "intent", "negligence", "scienter", "mens", "rea", "actus", "reus",
    "immunity", "qualified", "sovereign", "standing", "mootness", "ripeness",
    "justiciable", "waiver", "estoppel", "vacated", "reasoning", "rationale",
    "interpret", "interpretation", "construe", "ambiguity", "plain", "meaning",
    "legislative", "history", "canon", "textual", "originalism", "precedential",
}

# Question stems that invite reasoning rather than retrieval.
REASONING_STEMS = [
    re.compile(r"^why\b", re.I),
    re.compile(r"\bhow did the court (?:reason|conclude|distinguish|reconcile)", re.I),
    re.compile(r"\bon what (?:basis|ground|rationale)", re.I),
    re.compile(r"\bwhat (?:principle|standard|test|doctrine)", re.I),
    re.compile(r"\bdistinguish", re.I),
    re.compile(r"\breject(?:ed)? the argument", re.I),
]

_WORD = re.compile(r"[a-z]+")


def _toks(text: str) -> list[str]:
    return _WORD.findall((text or "").lower())


def overlap_ratio(a: str, b: str) -> float:
    """Fraction of a's tokens that also appear in b."""
    ta, tb = _toks(a), set(_toks(b))
    if not ta:
        return 0.0
    return sum(1 for t in ta if t in tb) / len(ta)


def assess_one(rec: dict) -> dict:
    q, a = rec.get("question", ""), rec.get("answer", "")
    span = rec.get("supporting_span", "")

    flags: list[str] = []
    for pattern, name in TRIVIAL_PATTERNS:
        if pattern.search(q):
            flags.append(name)
    for pattern, name in SHALLOW_OPENERS:
        if pattern.search(q.strip()):
            flags.append(name)

    q_toks = _toks(q)
    legal_hits = sum(1 for t in q_toks if t in LEGAL_TERMS)
    reasoning = any(p.search(q) for p in REASONING_STEMS)

    # High answer-span overlap means the answer copies rather than synthesises.
    copy_ratio = overlap_ratio(a, span)

    return {
        "flags": flags,
        "is_trivial": bool(flags),
        "legal_term_count": legal_hits,
        "legal_term_density": round(legal_hits / max(len(q_toks), 1), 3),
        "asks_reasoning": reasoning,
        "answer_span_overlap": round(copy_ratio, 3),
        "answer_is_near_copy": copy_ratio > 0.85,
        "question_words": len(q.split()),
        "answer_words": len(a.split()),
    }


def auto_report(records: list[dict]) -> dict:
    results = [assess_one(r) for r in records]
    n = len(results)
    if not n:
        return {}

    flag_counts: Counter = Counter()
    for r in results:
        flag_counts.update(r["flags"])

    by_type: dict[str, list] = {}
    for rec, res in zip(records, results):
        by_type.setdefault(rec.get("question_type", "?"), []).append(res)

    return {
        "n": n,
        "trivial_pct": round(100 * sum(r["is_trivial"] for r in results) / n, 1),
        "trivial_flags": dict(flag_counts),
        "asks_reasoning_pct": round(100 * sum(r["asks_reasoning"] for r in results) / n, 1),
        "no_legal_terms_pct": round(
            100 * sum(1 for r in results if r["legal_term_count"] == 0) / n, 1),
        "median_legal_terms": statistics.median(r["legal_term_count"] for r in results),
        "near_copy_answers_pct": round(
            100 * sum(r["answer_is_near_copy"] for r in results) / n, 1),
        "median_answer_span_overlap": statistics.median(
            r["answer_span_overlap"] for r in results),
        "by_question_type": {
            t: {
                "n": len(rs),
                "asks_reasoning_pct": round(100 * sum(r["asks_reasoning"] for r in rs) / len(rs), 1),
                "median_legal_terms": statistics.median(r["legal_term_count"] for r in rs),
                "near_copy_pct": round(100 * sum(r["answer_is_near_copy"] for r in rs) / len(rs), 1),
            }
            for t, rs in sorted(by_type.items())
        },
    }


# --- LLM judge -------------------------------------------------------------

JUDGE_PROMPT = """You are evaluating the quality of a question-answer pair generated from a US Supreme Court opinion. You are NOT answering the question; you are judging whether it is a good question for a legal question-answering benchmark.

CASE: {case_name}

SUPPORTING PASSAGE FROM THE OPINION:
\"\"\"
{span}
\"\"\"

QUESTION: {question}

ANSWER: {answer}

Score each criterion from 1 to 5.

legal_substance
  1 = answerable from metadata or common sense, no legal understanding needed
  3 = requires reading the passage but not legal reasoning
  5 = requires understanding legal doctrine, statutory construction, or judicial reasoning

specificity
  1 = generic, could apply to almost any case
  3 = somewhat tied to this case
  5 = specific to this case's facts, statute, or doctrinal question

answerability
  1 = the answer is not supported by the passage
  3 = partially supported, requires outside knowledge
  5 = fully and precisely supported by the passage

difficulty
  1 = answerable by copying one sentence verbatim
  3 = requires locating and rephrasing
  5 = requires synthesising across the passage or understanding an implication

Also judge:
  is_trivial: true if this question tests no legal understanding
  answer_is_copied: true if the answer merely reproduces the passage rather than stating the point in its own words

Return ONLY this JSON:
{{"legal_substance": N, "specificity": N, "answerability": N, "difficulty": N,
  "is_trivial": true/false, "answer_is_copied": true/false,
  "comment": "one short sentence"}}"""


def judge_sample(records: list[dict], model: str, delay: float = 0.4) -> dict:
    try:
        import anthropic
    except ImportError:
        sys.exit("anthropic is required:  pip install anthropic")
    import time

    key = os.getenv("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set")
    client = anthropic.Anthropic(api_key=key)

    scores: dict[str, list[int]] = {
        "legal_substance": [], "specificity": [], "answerability": [], "difficulty": []}
    trivial = copied = failed = 0
    worst: list[dict] = []

    for i, rec in enumerate(records, 1):
        prompt = JUDGE_PROMPT.format(
            case_name=rec.get("case_name", ""),
            span=rec.get("supporting_span", "")[:2000],
            question=rec.get("question", ""),
            answer=rec.get("answer", ""),
        )
        try:
            resp = client.messages.create(
                model=model, max_tokens=400, temperature=0,
                messages=[{"role": "user", "content": prompt}])
            text = resp.content[0].text
            start, end = text.find("{"), text.rfind("}")
            verdict = json.loads(text[start:end + 1])
        except Exception as e:
            failed += 1
            print(f"  [{i}/{len(records)}] judge failed: {str(e)[:60]}",
                  file=sys.stderr)
            continue

        for k in scores:
            v = verdict.get(k)
            if isinstance(v, (int, float)):
                scores[k].append(int(v))
        trivial += bool(verdict.get("is_trivial"))
        copied += bool(verdict.get("answer_is_copied"))

        mean = statistics.mean(
            [verdict.get(k, 3) for k in scores if isinstance(verdict.get(k), (int, float))]
            or [3])
        if mean <= 2.5 and len(worst) < 10:
            worst.append({"question": rec.get("question"),
                          "type": rec.get("question_type"),
                          "scores": {k: verdict.get(k) for k in scores},
                          "comment": verdict.get("comment", "")})

        if i % 25 == 0:
            print(f"  judged {i}/{len(records)}")
        time.sleep(delay)

    n = len(scores["legal_substance"]) or 1
    return {
        "judged": n,
        "failed": failed,
        "judge_model": model,
        "means": {k: round(statistics.mean(v), 2) for k, v in scores.items() if v},
        "pct_scoring_4_or_5": {
            k: round(100 * sum(1 for x in v if x >= 4) / len(v), 1)
            for k, v in scores.items() if v},
        "trivial_pct": round(100 * trivial / n, 1),
        "answer_copied_pct": round(100 * copied / n, 1),
        "worst_examples": worst,
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--dataset", default=None)
    ap.add_argument("--auto-only", action="store_true",
                    help="Automatic signals only; no API calls.")
    ap.add_argument("--sample", type=int, default=150,
                    help="How many pairs to send to the judge.")
    ap.add_argument("--judge", default="claude-sonnet-4-6",
                    help="Judge model. Use a DIFFERENT model from the generator.")
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--out", default="data/dataset/quality_report.json")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    path = Path(args.dataset) if args.dataset else Path(cfg["generate"]["output"])
    records = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines()
               if l.strip()]
    print(f"Loaded {len(records)} QA pairs from {path}\n")

    report = {"automatic": auto_report(records)}

    a = report["automatic"]
    print("AUTOMATIC QUALITY SIGNALS")
    print(f"  pairs assessed              {a['n']}")
    print(f"  trivial (metadata) questions {a['trivial_pct']}%")
    if a["trivial_flags"]:
        for f, c in sorted(a["trivial_flags"].items(), key=lambda kv: -kv[1]):
            print(f"      {f:<22} {c}")
    print(f"  ask for reasoning            {a['asks_reasoning_pct']}%")
    print(f"  contain no legal vocabulary  {a['no_legal_terms_pct']}%")
    print(f"  median legal terms/question  {a['median_legal_terms']}")
    print(f"  answers that copy the span   {a['near_copy_answers_pct']}%")
    print(f"  median answer-span overlap   {a['median_answer_span_overlap']}")

    print("\n  By question type:")
    print(f"    {'type':<18}{'n':>6}{'reasoning%':>12}{'legal terms':>13}{'copied%':>9}")
    for t, s in a["by_question_type"].items():
        print(f"    {t:<18}{s['n']:>6}{s['asks_reasoning_pct']:>12}"
              f"{s['median_legal_terms']:>13}{s['near_copy_pct']:>9}")

    if not args.auto_only:
        rng = random.Random(args.seed)
        sample = rng.sample(records, min(args.sample, len(records)))
        gen_models = {r.get("generator") for r in sample}
        if args.judge in gen_models:
            print(f"\nWARNING: judge model {args.judge} also generated these pairs.")
        print(f"\nJudging {len(sample)} pairs with {args.judge}...")
        report["judge"] = judge_sample(sample, args.judge)

        j = report["judge"]
        print(f"\nLLM JUDGE ({j['judge_model']}, n={j['judged']})")
        for k, v in j["means"].items():
            pct = j["pct_scoring_4_or_5"].get(k, 0)
            print(f"  {k:<20} mean {v}/5    {pct}% scored 4-5")
        print(f"  judged trivial       {j['trivial_pct']}%")
        print(f"  answer copies span   {j['answer_copied_pct']}%")
        if j["worst_examples"]:
            print("\n  Lowest-scoring questions:")
            for w in j["worst_examples"][:6]:
                print(f"    [{w['type']}] {w['question'][:78]}")
                print(f"      {w['scores']}  {w['comment'][:70]}")

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(report, indent=2), encoding="utf-8")
    print(f"\nWritten to {out}")


if __name__ == "__main__":
    main()
