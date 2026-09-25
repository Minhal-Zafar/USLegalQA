# USLegalQA

**A span-grounded question-answering dataset for US Supreme Court opinions, and what building it reveals about how such datasets are measured.**

MSc Computer Science dissertation, Gisma University of Applied Sciences. Author: Minhal Zafar. Supervisor: Prof. Dr. Muhammad Tanvir Afzal.

This README explains the whole project in plain language: the problem, what was built, how it works, what was found, and where each piece lives in the code. The dissertation itself is not included in this repository.

---

## 1. The idea in one paragraph

Large language models are increasingly used to answer questions about law, and to *create* legal training data. In law, a fluent answer that is not supported by the source is worse than no answer. This project builds a question-answering dataset from US Supreme Court opinions in which **every answer is tied to the exact passage of the opinion that supports it**, checked by a program and stored with character positions. It then uses that dataset to show that **much of what gets reported about such datasets depends on how things are measured, not on the models themselves**.

---

## 2. What problem were we trying to solve?

Three weaknesses in current practice motivate the work.

| # | Problem | Why it matters |
|---|---|---|
| 1 | **Answers are not linked to their source.** Existing free-form legal QA datasets give an answer, but not where in the document it came from. | Nobody can check whether an answer is actually supported, which is the first thing a lawyer needs. |
| 2 | **Nobody measures how reliable the generating model was.** Datasets are now built by prompting an LLM to write questions and answers, but the rate at which it invents content is not reported. | The main threat to the dataset's validity goes unexamined. |
| 3 | **Evaluation splits put the same document on both sides.** When many questions come from one document, splitting by *question* puts that document in both training and testing. | Test scores then partly reflect documents the model has already seen. |

These become three research questions:

- **RQ1:** Can a large, span-grounded, free-form QA resource be built from full Supreme Court opinions using an LLM, and how accurate is that generation when checked against the source?
- **RQ2:** How far do standard ways of verifying and evaluating such a resource misstate its quality, and by what mechanisms?
- **RQ3:** For a small open-weight model, what matters more on this task: giving it the source passage, or fine-tuning its weights?

---

## 3. What did we build?

**USLegalQA** has these properties:

| Property | Value |
|---|---|
| Opinions | **1,075** US Supreme Court opinions, 2005–2023 |
| Question–answer pairs | **15,001** (about 14 per opinion) |
| Answers with a verified supporting span | **100%**, stored with character offsets |
| Question types | legal principle 55.3%, holding 23.7%, facts 13.4%, procedural 4.3%, outcome 3.3% |
| Issue areas | expert-coded by the Supreme Court Database (criminal procedure 28.5% of opinions, economic activity 19.7%, civil rights 16.9%, …) |
| Split | by **opinion**: 860 / 107 / 108 opinions (12,101 / 1,481 / 1,419 pairs) |
| Generator | Claude Haiku 4.5, temperature 0.3 |

Each record looks like this, simplified:

```json
{
  "case_name": "Whitfield v. United States",
  "question": "What fraudulent scheme did the defendants operate ...?",
  "answer": "The defendants operated a deceptive investment program ...",
  "question_type": "facts",
  "supporting_span": "GMIC operated a \"gifting\" program that took in more than $400 million ...",
  "span_start": 1234, "span_end": 2046,
  "category": "criminal_procedure"
}
```

Slicing the opinion text at `span_start:span_end` returns the supporting span character for character. This was checked for all 15,001 pairs.

---

## 4. How was it built? The pipeline

```
 1 ACQUISITION                2 GENERATION                     3 DATASET              4 EVALUATION
 ─────────────                ────────────                     ─────────              ────────────
 SCDB case list  ─┐           chunk into 900-word windows      15,001 pairs           B0 extractive
 COLD Cases text ─┴► join ─►  label each early/middle/late ─►  split BY OPINION  ─►   B1 closed book
         segment (keep only    LLM writes Q, A + quoted span   (0% overlap)            B2 open book
         the Court's opinion)  verify span is really there ─┐                          F1 fine-tuned
         audit (wrong docs,    reject answers that copy it ─┤                          each vs. its own floor
         cut dissents)         discard failures ◄───────────┘
```

**Step 1: define the corpus properly.**
- **Which cases:** membership comes from the **Supreme Court Database (SCDB)**, the standard expert-coded list of cases. That excludes orders and cert denials, which contain no reasoning.
- **Where the text comes from:** a **dated public snapshot** (COLD Cases, Harvard Library Innovation Lab and Free Law Project), not a live website, so anyone can rebuild the corpus exactly.
- **Code:** `collect_cold.py`, `convert_cold.py`, `scdb.py`

**Step 2: keep only the law.**
- **The problem:** a Supreme Court record bundles the Reporter's syllabus, the majority opinion, and every concurrence and dissent into one document. Only the opinion of the Court (or a per curiam) states the law.
- **What we do:** `segment.py` finds the headers ("JUSTICE KAGAN delivered the opinion of the Court", "JUSTICE THOMAS, with whom … join, dissenting.", page headers like "THOMAS, J., dissenting") and keeps only the binding text.
- **Scale:** about **51% of the collected text** turns out not to be binding.

**Step 3: audit the corpus.** `audit_corpus.py` checks every record against its SCDB entry. It removes records that are the wrong document, for example a same-name case from a different year or a cert-denial statement. It also cuts the text at the first separate writing.

**Step 4: cover the whole opinion.**
- **Windows:** `chunking.py` splits each opinion into overlapping 900-word windows and labels each one early, middle or late.
- **Why:** holdings usually appear late in an opinion, so reading only the opening would miss them.

**Step 5: generate and verify.** `generate.py` sends each window to the LLM, which returns questions, answers and a *quoted supporting span*.
1. The span is **located in the source** by `locate_span`. The matcher tolerates legal quotation conventions, such as brackets, curly quotes, star pagination and footnote markers, but still rejects changed words. If the span is not found, the pair is discarded.
2. An answer that **copies more than 10 consecutive words** of its span is rejected, because the answer must explain the evidence, not transcribe it.

**Step 6: split by opinion.** `split.py` puts whole opinions in train, validation or test, never splitting one opinion across them.

**Step 7: evaluate four systems** on the test set. All are based on Llama 3.2 3B Instruct.

| System | What it gets | What it tests |
|---|---|---|
| **B0** extractive | no model; returns the passage's first sentences | what a trivial strategy scores |
| **B1** closed book | question and case name only | what the model already "knows" (a contamination check) |
| **B2** open book | question and the source passage | reading comprehension |
| **F1** fine-tuned | same as B2, after QLoRA fine-tuning (3 seeds) | what adapting the weights adds |

Each system is scored with ROUGE, METEOR, BERTScore and Sentence-BERT. Every score is compared with that system's **own floor**: its predictions scored against *unrelated* reference answers, which shows what "meaningless but fluent" scores on this data. The harness also reports bootstrap confidence intervals and paired significance tests. The code is in `baselines.py`, `evaluate.py`, `eval_sbert.py` and the two notebooks.

---

## 5. What did we find?

### RQ1: yes, it can be built, and the generator rarely invents quotes

- 15,001 pairs from 1,075 opinions, each with a verified, recoverable span.
- In a fully retained diagnostic run (903 candidates from 30 random opinions), exactly **one** quotation contained wording absent from the source: a single altered word. That is a **fabrication rate of 0.11%** (95% CI 0.003–0.62%).

### RQ2: standard measurement badly misstates quality, in three ways

**1. The verification method, not the generator, sets the "failure rate".** The same 903 candidates were run through four matching methods:

| Method | Apparent failure rate |
|---|---|
| Exact string match | **75.9%** |
| + whitespace and quote normalisation | 65.0% |
| + word-sequence matching | 53.5% |
| + publication-artefact removal (final) | 19.7% |
| **Actual fabrication (classified by hand)** | **0.11%** |

A naive pipeline would report a generator that fabricates 0.11% as failing 75.9% of the time, an overstatement of more than 600 times. The 178 remaining failures were classified by hand. Nearly all are verbatim quotes broken by legal-publishing features: omitted citations (81), page headers and footnotes of slip opinions (74), unmarked omissions of running text (13), and encoding faults (6). Only 4 were unfaithful in any sense.

**2. Prompt design and output validation govern question quality.**

| Signal | Pilot, original prompt | Released dataset |
|---|---|---|
| Answers copying their span | 45.6% | 0.8% |
| Questions requiring reasoning | 16.5% | 56.5% |

Even with the revised prompt, the copy filter still rejects 7.8% of candidates. Without such controls, a "generative" dataset silently turns into a span-extraction one.

**3. Splitting by question leaks almost everything.** With about 14 questions per opinion, a random question-level split puts the source opinion of **99.9%** of test questions in training. Splitting by opinion gives 0%.

### RQ3: the passage matters more than fine-tuning

| System | ROUGE-1 F | BERTScore (rescaled) |
|---|---|---|
| B0 extractive | 0.237 | −0.040 |
| B1 closed book | 0.209 | 0.076 |
| B2 open book | 0.455 | 0.373 |
| **F1 fine-tuned** (3 seeds) | **0.555** | **0.475** (SD 0.0008) |

- **The passage vs the weights:** giving the model the passage adds far more than fine-tuning. Depending on the measure, it adds **2.4 to 8.1 times** as much. Fine-tuning still adds a significant +0.10 for every seed.
- **Answer length:** part of the fine-tuning gain comes from answer length. B2 writes 1.57 times the reference length, F1 writes 1.02 times, and this shows up as higher precision.
- **Where the measures disagree:** all four measures agree on the big differences. On the smallest one, B0 against B1, the verdict depends on which measure you use and how you read it. That is the RQ2 lesson again.
- **Contamination:** the closed-book model shows **no evidence of contamination** strong enough to explain the results.

### The overall conclusion

Reported performance for LLM-generated legal QA datasets depends heavily on measurement choices that are rarely reported: **how quotes are verified, how prompts and filters are designed, and how data is split**. Such datasets are valuable and affordable, but they should be released together with measurements of their own reliability. This project does that.

---

## 6. Corrections made before release

Before release, every reported figure was checked line by line against the code and data. The audit found and fixed real problems:

- **Wrong documents:** 19 records held the wrong document, such as a same-name case from another year or a cert-denial statement. They were removed.
- **Missed dissents:** the segmenter had missed dissents whose opening lists several Justices, or is hyphenated across a line. In 603 opinions, concurrences and dissents were being kept as "the Court's" text. The segmenter was fixed, and the affected text and pairs (2,500) were removed.
- **Unrepresentative verification sample:** the verification comparison had been measured on 2005 opinions only, which are unusually clean, and the raw data was not kept. It was re-measured on a random sample with every candidate retained, and the failures were classified by hand.
- **Mislabelled floor:** one system's floor had been reported as if it were a single "corpus floor". Now every system is shown against its own.
- **Split not really stratified:** the split was intended to be stratified by issue area, but was drawn before the issue areas had been added to the records. It is kept as drawn and documented in `split_report.json`.
- **Re-scoring:** all results were re-scored on the corrected test set. Every conclusion held. Two claims were weakened to match the evidence: the passage's advantage is 2.4–8.1 times depending on the measure, not "three times", and the contamination evidence is weaker than first stated.

The records removed by the audit, and why, are in `data/dataset/excluded_opinions.json` and `trimmed_opinions.json`.

---

## 7. Limitations, stated honestly

- **One generator.** Questions and reference answers come from a single model, so scores may partly reward matching its style.
- **Grounded is not the same as correct.** A verified span proves the answer is anchored in the text, not that it is legally right. There was no expert legal annotation.
- **Selection by verification.** About one candidate in five was discarded, mostly genuine quotes broken by page layout, so the released pairs are a selected subset.
- **Fine-tuned on uncorrected data.** F1 was trained before the corpus corrections; 15% of its training pairs were later removed.
- **Scope.** One court, 2005–2023. The segmentation relies on US Reports conventions.

---

## 8. Where things are in the repository

| Path | What it is |
|---|---|
| `src/uslegalqa/` | the pipeline code (see below) |
| `data/dataset/uslegalqa_v3_audited.jsonl` | **the released dataset** (15,001 pairs) |
| `data/dataset/splits/` | train / val / test by opinion, plus `split_report.json` |
| `data/dataset/excluded_opinions.json`, `trimmed_opinions.json` | what the audit removed, and why |
| `data/cleaned/opinions_audited.jsonl` | the binding text of each opinion |
| `data/predictions/` | B0, B1, B2 and F1 (3 seeds) predictions on the test set |
| `data/results/evaluation.json`, `sbert_meteor.json` | all scores, floors, CIs and paired tests |
| `data/diagnostic/` | the retained verification diagnostic: candidates, review sheets, the author's classifications, `classification_method.md` |
| `f1test (1).ipynb` | QLoRA fine-tuning and F1 inference (Kaggle) |
| `b1b2testing (1).ipynb` | B1 and B2 inference (Kaggle) |
| `USLegalQA_Figures.ipynb` | regenerates every figure and algorithm card into `figures/` |
| `docs/build_figures_notebook.py` | generates `USLegalQA_Figures.ipynb` |
| `.env.example` | the API key names the generation scripts expect |
| `tests/` | 225 automated tests |

**Main modules in `src/uslegalqa/`:**

| Module | Role |
|---|---|
| `collect_cold.py`, `convert_cold.py`, `scdb.py` | get the corpus and join it to the Supreme Court Database |
| `segment.py` | separate the Court's opinion from syllabus, concurrences and dissents |
| `clean.py`, `audit_corpus.py` | clean the corpus; remove wrong documents and cut at separate writings |
| `chunking.py` | 900-word windows with early / middle / late bands |
| `generate.py` | prompt the LLM, verify each span (`locate_span`), reject copied answers |
| `split.py` | split by opinion; measure what a question-level split would leak |
| `baselines.py` | run B0, B1 and B2 |
| `evaluate.py`, `eval_sbert.py` | scoring, floors, bootstrap CIs, paired tests |
| `verify_diagnostic.py` | the retained re-measurement behind Table 4.2 |
| `assess_quality.py` | automatic question-quality signals |

---

## 9. How to reproduce

The Supreme Court Database file is not included. Download the case-centred, citation-organised file of **Version 2025 Release 01** (`SCDB_2025_01_caseCentered_Citation.csv`) from https://scdb.la.psu.edu/data/ and place it in the repository root. Later releases may differ slightly. To regenerate data, copy `.env.example` to `.env` and fill in the keys.

```bash
# rebuild the audited dataset and check the split
python -m uslegalqa.audit_corpus --scdb SCDB_2025_01_caseCentered_Citation.csv
python -m uslegalqa.split --measure-leakage

# score the predictions (CPU, a couple of hours)
python -m uslegalqa.evaluate --preds data/predictions/b0.jsonl --preds data/predictions/b1.jsonl \
  --preds data/predictions/b2.jsonl --preds data/predictions/f1_seed42.jsonl \
  --preds data/predictions/f1_seed1.jsonl --preds data/predictions/f1_seed2.jsonl --reference b2 --breakdowns
python -m uslegalqa.eval_sbert --preds ... (same files)

# the verification re-measurement (Table 4.2)
python -m uslegalqa.verify_diagnostic score

# all figures
jupyter nbconvert --to notebook --execute --inplace USLegalQA_Figures.ipynb

# tests
python -m pytest tests -q
```

Generating new data (`generate.py`, `verify_diagnostic generate`) needs an Anthropic API key in `.env`. B1, B2 and F1 need a GPU; the Kaggle notebooks were used.

---

## 10. Glossary

- **Span / supporting span:** the exact passage of the opinion quoted as evidence for an answer.
- **Binding text:** the part of an opinion that states the law: the opinion of the Court, or a per curiam.
- **Syllabus:** the Reporter of Decisions' summary at the top of an opinion. It is not law.
- **Concurrence / dissent:** separate opinions by individual Justices. They are not law.
- **Slip opinion:** the first printed version of an opinion, whose page headers ("Cite as: …") end up in extracted text.
- **Star pagination:** markers like `*218` showing where a printed page breaks.
- **SCDB:** the Supreme Court Database, the expert-coded list of every case since 1946.
- **Closed / open book:** answering without or with the source passage.
- **QLoRA:** a cheap way to fine-tune a large model: freeze it in 4-bit precision and train small adapter matrices.
- **Floor:** a system's score against *unrelated* references. It shows what meaningless but fluent text scores, so real scores can be read against it.
- **Pair-level vs opinion-level split:** splitting by individual questions vs by whole documents. Only the second prevents the same opinion from appearing in both training and test data.
