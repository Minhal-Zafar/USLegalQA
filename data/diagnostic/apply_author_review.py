"""Record the author's classification of the verification failures.

Two sheets:
  author_review.csv      the 23 cases the automatic decomposition could not resolve
  author_review_155.csv  the other 155 (see review_sheet_155.md)

Fill in `author_class` for every row, then run from the repository root:

    python data/diagnostic/apply_author_review.py
    python -m uslegalqa.verify_diagnostic score

The first sheet must be complete; the second is applied only when fully
filled in. classification_method.md records which cases the author classified.
"""

import csv
import json
import sys
from collections import Counter
from datetime import date
from pathlib import Path

DIR = Path("data/diagnostic")
VALID = {"fabrication", "misquotation", "from_memory", "unmarked_omission",
         "citation_omitted", "page_furniture", "encoding_artefact"}


def read_sheet(name: str, required: bool) -> list[dict]:
    path = DIR / name
    if not path.exists():
        return []
    rows = list(csv.DictReader(path.open(encoding="utf-8")))
    filled = [r for r in rows if r["author_class"].strip()]
    if not filled and not required:
        return []
    blank = [r["case"] for r in rows if not r["author_class"].strip()]
    if blank:
        sys.exit(f"{name}: {len(blank)} cases have no author_class yet "
                 f"(first: {', '.join(blank[:10])})")
    bad = [r["case"] for r in rows if r["author_class"].strip() not in VALID]
    if bad:
        sys.exit(f"{name}: unrecognised class in cases {', '.join(bad)}; "
                 f"use one of {sorted(VALID)}")
    return rows


first = read_sheet("author_review.csv", required=True)
second = read_sheet("author_review_155.csv", required=False)
verdicts = first + second

path = DIR / "failures_for_review.jsonl"
rows = [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]
changed = 0
for v in verdicts:
    r = rows[int(v["case"])]
    new = v["author_class"].strip()
    changed += new != r["classification"]
    r["classification"] = new
    if v["author_note"].strip():
        r["classification_note"] = v["author_note"].strip()
    r["classified_by"] = "author, by hand against the source window"
path.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows),
                encoding="utf-8")

counts = Counter(r["classification"] for r in rows)
all_by_author = len(verdicts) == len(rows)
if all_by_author:
    step3 = ("3. **Decomposition as a reading aid.** `python -m uslegalqa.verify_diagnostic classify`\n"
             "   split each rejected quotation into pieces that occur verbatim and in order\n"
             "   in the source window, and showed the source text between the pieces, so\n"
             "   that each failure could be read against the source.\n"
             f"4. **Author classification.** The author classified all {len(rows)} failures by\n"
             "   hand against the source window (`review_sheet.md`, `review_sheet_155.md`;\n"
             "   verdicts in `author_review.csv` and `author_review_155.csv`). The author\n"
             f"   changed the suggested class in {changed} of the {len(rows)} cases.\n")
else:
    step3 = ("3. **Automatic decomposition.** `python -m uslegalqa.verify_diagnostic classify`\n"
             "   split each rejected quotation into pieces that occur verbatim and in order\n"
             "   in the source window, and typed the source text between the pieces. This\n"
             f"   resolved {len(rows) - len(verdicts)} of the {len(rows)} failures, which are verbatim\n"
             "   quotation interrupted only by page layout, citations or encoding faults.\n"
             f"4. **Author classification.** The {len(verdicts)} failures the decomposition could\n"
             "   not resolve were classified by the author by hand against the source window\n"
             "   (`review_sheet.md`, `author_review.csv`). The author changed the suggested\n"
             f"   class in {changed} of the {len(verdicts)} cases.\n")

(DIR / "classification_method.md").write_text(f"""# How the verification failures were classified

Date of author review: {date.today().isoformat()}

1. **Generation.** `python -m uslegalqa.verify_diagnostic generate --opinions 30 --seed 7`
   regenerated 30 randomly drawn opinions (298 windows) with the production
   prompt, model and temperature. Every candidate was retained: 903 carried a
   supporting span.
2. **Verification.** Four cumulative matching methods were applied to each
   candidate. The production matcher rejected {len(rows)}.
{step3}5. **Assistance.** The decomposition code, the review sheets and a suggested
   class for each case were prepared with the help of an AI coding assistant
   (Claude). The final classification is the author's.

Final counts: {dict(counts.most_common())}
""", encoding="utf-8")
print(f"Recorded {len(verdicts)} author verdicts ({changed} changed); "
      f"all failures classified by author: {all_by_author}. "
      f"Wrote {DIR / 'classification_method.md'}. Now run the score step.")
