"""Export the files needed to demonstrate grounding by opening them.

Writes a small demo folder for one pair: line numbers in the real files, the
raw dataset line, the record pretty printed, the opinion with the span marked,
and the slice at the stored offsets compared with the span.

Usage:
    python -m uslegalqa.export_demo --case "Baze v. Rees" --type holding
    python -m uslegalqa.export_demo --index 0
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

START_MARK = ">>>>>>>>>> SUPPORTING SPAN BEGINS HERE >>>>>>>>>>"
END_MARK = "<<<<<<<<<< SUPPORTING SPAN ENDS HERE <<<<<<<<<<"


def case_matches(query: str, *names: str) -> bool:
    hay = " ".join(n or "" for n in names).lower()
    words = re.findall(r"\w+", query.lower())
    return bool(words) and all(
        re.search(r"\b" + re.escape(w) + r"\b", hay) for w in words)


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--dataset", default="data/dataset/uslegalqa_v3_final.jsonl")
    ap.add_argument("--opinions", default="data/cleaned/opinions.jsonl")
    ap.add_argument("--outdir", default="demo")
    ap.add_argument("--case", default=None)
    ap.add_argument("--type", default=None)
    ap.add_argument("--index", type=int, default=None)
    args = ap.parse_args()

    ds_path = Path(args.dataset)
    raw_lines = ds_path.read_text(encoding="utf-8").splitlines()

    records = []
    for lineno, line in enumerate(raw_lines, start=1):
        if line.strip():
            try:
                records.append((lineno, line, json.loads(line)))
            except json.JSONDecodeError:
                continue

    opinions = {}
    op_lines = Path(args.opinions).read_text(encoding="utf-8").splitlines()
    for lineno, line in enumerate(op_lines, start=1):
        if line.strip():
            try:
                o = json.loads(line)
                opinions[o["cluster_id"]] = (lineno, o)
            except (json.JSONDecodeError, KeyError):
                continue

    pool = records
    if args.case:
        pool = [r for r in pool
                if case_matches(args.case, r[2].get("case_name"),
                                opinions.get(r[2].get("cluster_id"), (0, {}))[1]
                                .get("case_name"))]
    if args.type:
        pool = [r for r in pool if r[2].get("question_type") == args.type]
    if args.index is not None:
        pool = [r for r in records if r[0] == args.index + 1]
    if not pool:
        raise SystemExit("No pair matched those filters.")

    ds_lineno, raw_line, pair = pool[0]
    cid = pair["cluster_id"]
    if cid not in opinions:
        raise SystemExit(f"Opinion {cid} not found in {args.opinions}")
    op_lineno, opinion = opinions[cid]
    text = opinion.get("text", "")
    start, end = pair["span_start"], pair["span_end"]
    span = pair["supporting_span"]
    sliced = text[start:end]

    out = Path(args.outdir)
    out.mkdir(parents=True, exist_ok=True)

    (out / "01_raw_dataset_line.txt").write_text(raw_line, encoding="utf-8")

    (out / "02_pair_record.json").write_text(
        json.dumps(pair, indent=2, ensure_ascii=False), encoding="utf-8")

    marked = (text[:start] + "\n" + START_MARK + "\n" + sliced + "\n"
              + END_MARK + "\n" + text[end:])
    (out / "03_opinion_marked.txt").write_text(
        f"{opinion.get('case_name','')}  {opinion.get('citation','')}\n"
        f"Source: data/cleaned/opinions.jsonl, line {op_lineno}\n"
        f"The span runs from character {start} to {end} of {len(text)}.\n"
        f"Search this file for SUPPORTING SPAN BEGINS to find it.\n"
        + "=" * 78 + "\n\n" + marked, encoding="utf-8")

    identical = sliced == span
    (out / "04_proof.txt").write_text(
        "GROUNDING PROOF\n" + "=" * 78 + "\n\n"
        f"case            {opinion.get('case_name','')}\n"
        f"citation        {opinion.get('citation','')}\n"
        f"SCDB case id    {opinion.get('scdb_id', pair.get('scdb_id',''))}\n"
        f"cluster id      {cid}\n\n"
        f"QUESTION\n{pair.get('question','')}\n\n"
        f"ANSWER\n{pair.get('answer','')}\n\n"
        f"STORED OFFSETS  span_start = {start}, span_end = {end}\n\n"
        f"SUPPORTING SPAN as stored with the answer\n{span}\n\n"
        f"OPINION TEXT sliced at [{start}:{end}]\n{sliced}\n\n"
        + "=" * 78 + "\n"
        f"IDENTICAL: {identical}\n", encoding="utf-8")

    (out / "00_where_to_look.txt").write_text(
        "WHERE TO LOOK IN THE REAL FILES\n" + "=" * 78 + "\n\n"
        f"Case: {opinion.get('case_name','')}  {opinion.get('citation','')}\n\n"
        "1. THE DATASET RECORD\n"
        f"   File: {ds_path}\n"
        f"   Line: {ds_lineno}\n"
        "   In VS Code, open the file, press Ctrl+G, type the line number.\n"
        "   That line is the complete record, including span_start and\n"
        "   span_end. The same line is copied to 01_raw_dataset_line.txt and\n"
        "   pretty printed in 02_pair_record.json.\n\n"
        "2. THE OPINION TEXT\n"
        f"   File: {args.opinions}\n"
        f"   Line: {op_lineno}\n"
        "   This line holds the full text of the opinion as a JSON string.\n"
        "   Because it is one long line, character offsets into the text are\n"
        "   not the same as editor columns, which is why the marked copy in\n"
        "   03_opinion_marked.txt exists.\n\n"
        "3. THE SPAN IN PLACE\n"
        "   Open 03_opinion_marked.txt and search for:\n"
        "       SUPPORTING SPAN BEGINS\n"
        "   The text between the two markers is exactly the characters at\n"
        f"   positions {start} to {end} of the opinion.\n\n"
        "4. THE PROOF\n"
        "   Open 04_proof.txt. It shows the stored span and the slice taken\n"
        "   from the opinion at those offsets, and whether they are identical.\n"
        f"   Result for this pair: IDENTICAL = {identical}\n\n"
        "5. TO CHECK WITHOUT ANY OF THIS TOOLING\n"
        "   python -c \"import json;d=[json.loads(l) for l in "
        "open('" + str(ds_path).replace("\\", "/") + "',encoding='utf-8')];"
        f"p=d[{ds_lineno - 1}];"
        "o=[json.loads(l) for l in open('"
        + args.opinions.replace("\\", "/") + "',encoding='utf-8')];"
        "t=[x for x in o if x['cluster_id']==p['cluster_id']][0]['text'];"
        "print(t[p['span_start']:p['span_end']]==p['supporting_span'])\"\n",
        encoding="utf-8")

    print(f"Demo files written to {out.resolve()}\n")
    print(f"  case            {opinion.get('case_name','')} "
          f"{opinion.get('citation','')}")
    print(f"  dataset line    {ds_lineno}  of {ds_path}")
    print(f"  opinion line    {op_lineno}  of {args.opinions}")
    print(f"  span offsets    {start} to {end} of {len(text)} characters")
    print(f"  IDENTICAL       {identical}")
    print("\n  Open demo/00_where_to_look.txt first.")


if __name__ == "__main__":
    main()
