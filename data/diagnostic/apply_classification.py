"""Apply the reviewed classification of the 178 verification failures.

Cases listed in MANUAL were read against their source window one by one. The
remaining cases take the class assigned by the automatic decomposition in
verify_diagnostic.suggest(); a random spot check of 32 of them agreed on the
decisive question (no wording absent from the source).

Classes:
  fabrication        quotation contains wording the source does not
  misquotation       verbatim words arranged misleadingly (spliced, reordered)
  from_memory        accurate text supplied from outside the window
  unmarked_omission  verbatim, in order, running text skipped without "..."
  citation_omitted   verbatim, an inline citation skipped without "..."
  page_furniture     verbatim, interrupted by a running header, page number or footnote
  encoding_artefact  verbatim, the source has a character-encoding fault

Run from the repository root:
    python data/diagnostic/apply_classification.py
    python -m uslegalqa.verify_diagnostic score
"""

import json
from pathlib import Path

REVIEW = Path("data/diagnostic/failures_for_review.jsonl")

MANUAL = {
    25: ("fabrication", 'One word altered: source "until November 9, 2012", quotation "on November 9, 2012".'),
    61: ("misquotation", 'Verbatim words spliced: "And it held that" joined to a quotation the Court introduced with "The Court wrote that, where possible,".'),
    83: ("misquotation", "Verbatim sentences joined by an ellipsis in the reverse of their order in the source."),
    97: ("from_memory", 'Source page break cuts the citation after "533 U. S."; the model completed it correctly ("289, 317 (2001)") from outside the window.'),
    6: ("unmarked_omission", "Running text and a citation skipped without an ellipsis; all quoted words verbatim and in order."),
    24: ("unmarked_omission", "A sentence of the Court's reasoning skipped without an ellipsis."),
    45: ("unmarked_omission", "Citation, star page and two sentences skipped without an ellipsis."),
    67: ("unmarked_omission", "Page header and a parenthetical passage skipped without an ellipsis."),
    77: ("unmarked_omission", "Citations and following sentences skipped without an ellipsis."),
    87: ("unmarked_omission", "A sentence and a string of record citations skipped without an ellipsis."),
    104: ("unmarked_omission", "Citations, a sentence and a footnote skipped without an ellipsis."),
    171: ("unmarked_omission", "Page header and a paragraph skipped without an ellipsis."),
    9: ("citation_omitted", "Inline citations (122 Stat. 343; 73 Fed. Reg. 6571) dropped."),
    42: ("citation_omitted", "Inline citation (2004 Almanac 1579) dropped."),
    86: ("citation_omitted", "Statutory citation dropped."),
    89: ("citation_omitted", "Citation with explanatory parenthetical dropped."),
    106: ("citation_omitted", "Law review citation and footnote marker dropped."),
    14: ("page_furniture", "Footnote body and page header interrupt the quotation; bracketed alterations in the source."),
    102: ("page_furniture", 'Footnote interrupts the quoted sentence before "UCMJ".'),
    103: ("page_furniture", 'Footnote interrupts the quoted sentence before "UCMJ".'),
    130: ("page_furniture", 'Footnote interrupts "regula-tions"; remaining elision marked with an ellipsis.'),
    149: ("page_furniture", "Page header and citations inside an ellipsis the matcher could not align."),
    159: ("page_furniture", 'Page header falls between "when" and "determining".'),
}

rows = [json.loads(l) for l in REVIEW.read_text(encoding="utf-8").splitlines() if l.strip()]
assert len(rows) == 178, len(rows)
for i, r in enumerate(rows):
    if i in MANUAL:
        r["classification"], r["classification_note"] = MANUAL[i]
        r["classified_by"] = "model review of the source window (Claude), automatic decomposition as evidence"
    else:
        r["classification"] = r["suggested"]
        r["classification_note"] = r["evidence"]
        r["classified_by"] = "automatic decomposition; 32-case random spot check agreed"
REVIEW.write_text("".join(json.dumps(r, ensure_ascii=False) + "\n" for r in rows), encoding="utf-8")
print(f"classified {len(rows)} failures ({len(MANUAL)} by individual review)")
