# How the verification failures were classified

Date of author review: 2026-09-24

1. **Generation.** `python -m uslegalqa.verify_diagnostic generate --opinions 30 --seed 7`
   regenerated 30 randomly drawn opinions (298 windows) with the production
   prompt, model and temperature. Every candidate was retained: 903 carried a
   supporting span.
2. **Verification.** Four cumulative matching methods were applied to each
   candidate. The production matcher rejected 178.
3. **Decomposition as a reading aid.** `python -m uslegalqa.verify_diagnostic classify`
   split each rejected quotation into pieces that occur verbatim and in order
   in the source window, and showed the source text between the pieces, so
   that each failure could be read against the source.
4. **Author classification.** The author classified all 178 failures by
   hand against the source window (`review_sheet.md`, `review_sheet_155.md`;
   verdicts in `author_review.csv` and `author_review_155.csv`). The author
   changed the suggested class in 7 of the 178 cases.
5. **Assistance.** The decomposition code, the review sheets and a suggested
   class for each case were prepared with the help of an AI coding assistant
   (Claude). The final classification is the author's.

Final counts: {'citation_omitted': 81, 'page_furniture': 74, 'unmarked_omission': 13, 'encoding_artefact': 6, 'misquotation': 2, 'fabrication': 1, 'from_memory': 1}
