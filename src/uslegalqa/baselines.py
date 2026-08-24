"""Run baseline systems over the test split and write prediction files.

Systems:
  B0  extractive    Leading sentences of the source passage. No model.
  B1  closed-book   Question only; measures recall from pre-training.
  B2  open-book     Question plus the source passage; measures comprehension.
  B3  few-shot      B1 with three worked examples.

A large B1/B2 gap means the dataset tests comprehension rather than recall.

Backends:
  --backend hf       local or Kaggle GPU via transformers
  --backend anthropic  API model, for the ceiling reference

Usage:
    python -m uslegalqa.baselines --system b0
    python -m uslegalqa.baselines --system b1 --backend hf --model meta-llama/Llama-3.2-3B-Instruct
    python -m uslegalqa.baselines --system b2 --backend hf --model meta-llama/Llama-3.2-3B-Instruct
    python -m uslegalqa.baselines --system b1 --backend anthropic --model claude-haiku-4-5-20251001 --limit 200
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

import yaml

SYSTEMS = ("b0", "b1", "b2", "b3")

CLOSED_BOOK = """You are a US legal expert. Answer the question about the Supreme Court case below.

CASE: {case_name} ({date_filed})
QUESTION: {question}

Answer in 20-100 words. State what the Court held or reasoned. Do not speculate; if you do not know, say so."""

OPEN_BOOK = """You are a US legal expert. Answer the question using ONLY the passage below.

CASE: {case_name} ({date_filed})

PASSAGE:
\"\"\"
{passage}
\"\"\"

QUESTION: {question}

Answer in 20-100 words, based only on the passage. State the point in your own words rather than quoting at length."""

FEWSHOT_PREFIX = """You are a US legal expert. Answer questions about Supreme Court cases.

QUESTION: What standard did the Court apply to determine whether a search was reasonable?
ANSWER: The Court applied a totality-of-the-circumstances test, weighing the intrusion on the individual's privacy against the government's legitimate interests, rather than requiring a warrant in every case.

QUESTION: Why did the Court reject the petitioner's reading of the statute?
ANSWER: The Court found the reading inconsistent with the statute's text and structure: the provision's plain language covered the conduct at issue, and adopting the narrower construction would render a neighbouring clause superfluous.

QUESTION: What was the Court's disposition of the case?
ANSWER: The Court reversed the judgment of the Court of Appeals and remanded the case for further proceedings consistent with its opinion, leaving the remaining questions to the lower court in the first instance.

"""


class HFBackend:
    """Local or Kaggle GPU inference via transformers, greedy decoding only."""

    def __init__(self, model_id: str, max_new_tokens: int = 160,
                 load_in_4bit: bool = True):
        try:
            import torch
            from transformers import AutoTokenizer, AutoModelForCausalLM
        except ImportError:
            sys.exit("transformers and torch are required for --backend hf")

        print(f"[hf] loading {model_id}")
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)
        kwargs = {"device_map": "auto"}
        if load_in_4bit:
            try:
                from transformers import BitsAndBytesConfig
                kwargs["quantization_config"] = BitsAndBytesConfig(
                    load_in_4bit=True, bnb_4bit_quant_type="nf4",
                    bnb_4bit_compute_dtype=torch.float16)
            except Exception as e:  # noqa: BLE001
                print(f"[hf] 4-bit unavailable ({e}); loading in fp16",
                      file=sys.stderr)
                kwargs["torch_dtype"] = torch.float16
        else:
            kwargs["torch_dtype"] = torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(model_id, **kwargs)
        self.model.eval()
        self.max_new_tokens = max_new_tokens
        self.torch = torch

    def generate(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        if hasattr(self.tokenizer, "apply_chat_template"):
            text = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True)
        else:
            text = prompt
        inputs = self.tokenizer(text, return_tensors="pt").to(self.model.device)
        with self.torch.no_grad():
            out = self.model.generate(
                **inputs, max_new_tokens=self.max_new_tokens,
                do_sample=False,
                pad_token_id=self.tokenizer.eos_token_id,
            )
        # Slice off the prompt so only generated tokens are scored.
        generated = out[0][inputs["input_ids"].shape[-1]:]
        return self.tokenizer.decode(generated, skip_special_tokens=True).strip()


class AnthropicBackend:
    def __init__(self, model_id: str, max_tokens: int = 300):
        try:
            import anthropic
        except ImportError:
            sys.exit("anthropic is required for --backend anthropic")
        key = os.getenv("ANTHROPIC_API_KEY")
        if not key:
            sys.exit("ANTHROPIC_API_KEY is not set")
        self.client = anthropic.Anthropic(api_key=key)
        self.model_id = model_id
        self.max_tokens = max_tokens
        self.anthropic = anthropic

    def generate(self, prompt: str) -> str:
        for attempt in range(5):
            try:
                resp = self.client.messages.create(
                    model=self.model_id, max_tokens=self.max_tokens,
                    temperature=0,
                    messages=[{"role": "user", "content": prompt}])
                return resp.content[0].text.strip()
            except self.anthropic.RateLimitError:
                time.sleep(20 * (attempt + 1))
            except Exception as e:  # noqa: BLE001
                print(f"    error ({str(e)[:60]}); retry {attempt + 1}",
                      file=sys.stderr)
                time.sleep(5 * (attempt + 1))
        return ""


_SENT = re.compile(r"(?<=[.?!])\s+(?=[A-Z\u201c\"'(])")


def extractive_answer(passage: str, target_words: int = 40) -> str:
    """Leading sentences of the passage, to roughly the reference length."""
    sentences = _SENT.split(passage.strip())
    out, count = [], 0
    for s in sentences:
        out.append(s)
        count += len(s.split())
        if count >= target_words:
            break
    return " ".join(out)


def load_opinions(path: Path) -> dict[int, dict]:
    index = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                rec = json.loads(line)
                index[rec["cluster_id"]] = rec
            except (json.JSONDecodeError, KeyError):
                continue
    return index


def passage_for(pair: dict, opinion: dict, window: int = 1800) -> str:
    """The region of the opinion around the answer's stored span offsets."""
    text = opinion.get("text", "")
    start = pair.get("span_start")
    end = pair.get("span_end")
    if start is None or end is None:
        return text[:window]
    lo = max(0, start - window // 2)
    hi = min(len(text), end + window // 2)
    return text[lo:hi]


def build_prompt(system: str, pair: dict, opinion: dict) -> str:
    case_name = pair.get("case_name") or opinion.get("case_name", "")
    date = pair.get("date_filed") or opinion.get("date_filed", "")
    if system == "b2":
        return OPEN_BOOK.format(case_name=case_name, date_filed=date,
                                passage=passage_for(pair, opinion),
                                question=pair["question"])
    closed = CLOSED_BOOK.format(case_name=case_name, date_filed=date,
                                question=pair["question"])
    return FEWSHOT_PREFIX + closed if system == "b3" else closed


def run(cfg: dict, system: str, backend, test_path: Path, out_path: Path,
        limit: int | None, delay: float) -> None:
    pairs = []
    for line in test_path.read_text(encoding="utf-8").splitlines():
        if line.strip():
            try:
                pairs.append(json.loads(line))
            except json.JSONDecodeError:
                continue
    if limit:
        pairs = pairs[:limit]

    opinions = load_opinions(Path(cfg["paths"]["cleaned"]))
    missing = {p["cluster_id"] for p in pairs} - set(opinions)
    if missing:
        print(f"WARNING: {len(missing)} test opinions not found in the corpus",
              file=sys.stderr)

    done = set()
    if out_path.exists():
        for line in out_path.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    d = json.loads(line)
                    done.add((d["cluster_id"], d["question"]))
                except (json.JSONDecodeError, KeyError):
                    continue
        if done:
            print(f"Resuming: {len(done)} predictions already written")

    todo = [p for p in pairs if (p["cluster_id"], p["question"]) not in done]
    print(f"{system}: {len(todo)} items to predict "
          f"({len(pairs) - len(todo)} already done)\n")

    out_path.parent.mkdir(parents=True, exist_ok=True)
    empty = 0
    with out_path.open("a", encoding="utf-8") as f:
        for i, pair in enumerate(todo, 1):
            opinion = opinions.get(pair["cluster_id"], {})

            if system == "b0":
                prediction = extractive_answer(passage_for(pair, opinion))
            else:
                prediction = backend.generate(build_prompt(system, pair, opinion))
                if delay:
                    time.sleep(delay)

            if not prediction.strip():
                empty += 1

            f.write(json.dumps({
                "cluster_id": pair["cluster_id"],
                "question": pair["question"],
                "answer": pair["answer"],
                "prediction": prediction,
                "question_type": pair.get("question_type"),
                "category": pair.get("category"),
                "system": system,
            }, ensure_ascii=False) + "\n")
            f.flush()

            if i % 25 == 0 or i == len(todo):
                print(f"  [{i}/{len(todo)}] {empty} empty so far")

    print(f"\nWritten to {out_path}")
    if empty:
        print(f"WARNING: {empty} empty predictions "
              f"({100 * empty / max(len(todo), 1):.1f}%)")
    print(f"\nScore with:\n  python -m uslegalqa.evaluate --preds {out_path}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--config", default="config/default.yaml")
    ap.add_argument("--system", required=True, choices=SYSTEMS)
    ap.add_argument("--test", default="data/dataset/splits/test.jsonl")
    ap.add_argument("--out", default=None)
    ap.add_argument("--backend", default="hf", choices=("hf", "anthropic"))
    ap.add_argument("--model", default="meta-llama/Llama-3.2-3B-Instruct")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--delay", type=float, default=0.0)
    ap.add_argument("--no-4bit", action="store_true")
    args = ap.parse_args()

    try:
        from dotenv import load_dotenv
        load_dotenv()
    except ImportError:
        pass

    cfg = yaml.safe_load(Path(args.config).read_text(encoding="utf-8"))
    test_path = Path(args.test)
    if not test_path.exists():
        sys.exit(f"test split not found: {test_path}\n"
                 "Run: python -m uslegalqa.split")

    out = Path(args.out) if args.out else Path(
        f"data/predictions/{args.system}.jsonl")

    backend = None
    if args.system != "b0":
        backend = (AnthropicBackend(args.model) if args.backend == "anthropic"
                   else HFBackend(args.model, load_in_4bit=not args.no_4bit))

    run(cfg, args.system, backend, test_path, out, args.limit, args.delay)


if __name__ == "__main__":
    main()
