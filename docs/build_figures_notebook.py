"""Build USLegalQA_Figures.ipynb (restyled, reading the corrected data)."""
import json
from pathlib import Path

cells = []
def md(s): cells.append({"cell_type": "markdown", "metadata": {}, "source": s.strip("\n")})
def code(s): cells.append({"cell_type": "code", "metadata": {}, "execution_count": None,
                           "outputs": [], "source": s.strip("\n")})

md(r'''
# USLegalQA: regenerate every figure in the dissertation

This notebook rebuilds every visual artefact in the report: the architecture
diagram, the data and results figures, and the four algorithm listings.

**Where the numbers come from.** Every figure reads the corrected release:
- `data/dataset/uslegalqa_v3_audited.jsonl` and `data/cleaned/opinions_audited.jsonl`
- `data/dataset/splits/`
- `data/diagnostic/verification_report.json`
- `data/results/`

Only three inputs are not stored as result files, and each is declared where it is used:
- the pilot figures behind Table 4.3
- the training-loss log
- the design comparison coded from the papers

**Guard on stale results.** The results figures (4.5–4.8) check that
`evaluation.json` was scored on the current test split. They refuse to draw
from stale results.

**Style.** It uses a colour-blind validated categorical palette, assigned in a
fixed order: B0, B1, B2 and F1 always keep the same colour. Each system's own
floor is shown in neutral grey. Grids are hairline, bar ends are rounded, and
text is in ink colours, never series colours.

Run the cells in order. Output goes to `figures/`.
''')

code(r'''
# --- setup and style ---
import json, sys, textwrap
from collections import Counter
from pathlib import Path
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch, Rectangle

ROOT = Path(".")
sys.path.insert(0, str(ROOT / "src"))
OUT = ROOT / "figures"; OUT.mkdir(exist_ok=True)

# Categorical slots, fixed order (validated: CVD and normal-vision separation pass;
# slots 3-4 sit below 3:1 contrast, so every chart that uses them is directly labelled).
S1, S2, S3, S4 = "#2a78d6", "#eb6834", "#1baf7a", "#eda100"
SYSTEM_COLOUR = {"B0": S1, "B1": S2, "B2": S3, "F1": S4}
FLOOR = "#9a9993"                       # reference, not a series
INK, INK2, MUTED = "#0b0b0b", "#52514e", "#8a8984"
GRID, SURFACE = "#e6e5e0", "#ffffff"
BLUE_RAMP = {"250": "#86b6ef", "450": "#2a78d6", "550": "#1c5cab", "650": "#104281"}
NEUTRAL = "#f0efec"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 8.6,
    "text.color": INK, "axes.labelcolor": INK2, "axes.edgecolor": GRID,
    "xtick.color": INK2, "ytick.color": INK2, "xtick.labelsize": 8, "ytick.labelsize": 8,
    "axes.spines.top": False, "axes.spines.right": False, "axes.spines.left": False,
    "axes.grid": True, "axes.grid.axis": "y", "grid.color": GRID, "grid.linewidth": 0.8,
    "axes.axisbelow": True, "xtick.major.size": 0, "ytick.major.size": 0,
    "legend.frameon": False, "legend.fontsize": 8, "figure.dpi": 200,
    "savefig.dpi": 200, "figure.facecolor": SURFACE, "axes.facecolor": SURFACE,
})

HEADER_IN = 0.62   # inches reserved above the plot for the headline block

def frame(fig, title, subtitle=None):
    """Left-aligned headline and subtitle, then lay the axes out beneath them."""
    h = fig.get_size_inches()[1]
    fig.tight_layout(rect=[0, 0, 1, 1 - HEADER_IN / h])
    fig.text(0.012, 1 - 0.16 / h, title, ha="left", va="top", fontsize=10.8,
             fontweight="bold", color=INK)
    if subtitle:
        fig.text(0.012, 1 - 0.40 / h, subtitle, ha="left", va="top",
                 fontsize=8.2, color=INK2)

def _px_scale(ax):
    bb = ax.get_window_extent()
    (x0, x1), (y0, y1) = ax.get_xlim(), ax.get_ylim()
    return abs(bb.width / (x1 - x0)), abs(bb.height / (y1 - y0))   # inverted axes flip the sign

def rbar(ax, pos, length, width, colour, base=0.0, horizontal=False, r_px=5, z=3):
    """A bar with rounded corners at its data end and a square baseline.

    Built as an explicit outline in data units, with the corner radius converted
    from pixels on each axis, so the rounding is circular whatever the aspect.
    Call after the axes have been laid out (frame()) and their limits set.
    """
    from matplotlib.path import Path as MPath
    from matplotlib.patches import PathPatch
    if length == 0:
        return
    sx, sy = _px_scale(ax)
    s_len, s_wid = (sx, sy) if horizontal else (sy, sx)
    rl = min(r_px / s_len, abs(length))            # radius along the bar
    rw = min(r_px / s_wid, width / 2)              # radius across the bar
    sg = 1 if length > 0 else -1
    a0, a1 = pos - width / 2, pos + width / 2
    end = base + length
    pts = [(a0, base), (a1, base), (a1, end - sg * rl), (a1, end), (a1 - rw, end),
           (a0 + rw, end), (a0, end), (a0, end - sg * rl), (a0, base)]
    codes = [MPath.MOVETO, MPath.LINETO, MPath.LINETO, MPath.CURVE3, MPath.CURVE3,
             MPath.LINETO, MPath.CURVE3, MPath.CURVE3, MPath.CLOSEPOLY]
    if horizontal:
        pts = [(l, w) for w, l in pts]
    ax.add_patch(PathPatch(MPath(pts, codes), fc=colour, ec="none", zorder=z))

def floor_tick(ax, pos, value, width, z=4):
    """A system's own floor: a neutral tick across its bar."""
    ax.plot([pos - width * 0.62, pos + width * 0.62], [value, value],
            color=FLOOR, lw=2.2, solid_capstyle="round", zorder=z)

def key(ax, items, loc="upper left", ncol=1, **kw):
    """Legend with square swatches; text stays in ink."""
    from matplotlib.lines import Line2D
    handles = []
    for label, colour, kind in items:
        if kind == "line":
            handles.append(Line2D([0], [0], color=colour, lw=2.2, label=label))
        else:
            handles.append(Line2D([0], [0], marker="s", ls="", ms=7, mfc=colour,
                                  mec=colour, label=label))
    return ax.legend(handles=handles, loc=loc, ncol=ncol, handletextpad=0.5,
                     columnspacing=1.2, **kw)

def save(fig, name):
    fig.savefig(OUT / f"{name}.png", bbox_inches="tight", facecolor=SURFACE, pad_inches=0.08)
    plt.close(fig)
    print(f"  wrote figures/{name}.png")

print("style loaded")
''')

md(r'''
## 1. Inputs
''')

code(r'''
P = {
    "dataset":      ROOT / "data/dataset/uslegalqa_v3_audited.jsonl",
    "opinions":     ROOT / "data/cleaned/opinions_audited.jsonl",
    "test":         ROOT / "data/dataset/splits/test.jsonl",
    "split_report": ROOT / "data/dataset/splits/split_report.json",
    "verification": ROOT / "data/diagnostic/verification_report.json",
    "evaluation":   ROOT / "data/results/evaluation.json",
    "sbert":        ROOT / "data/results/sbert_meteor.json",
}

def jl(path):
    return [json.loads(l) for l in path.read_text(encoding="utf-8").splitlines() if l.strip()]

pairs    = jl(P["dataset"])
opinions = jl(P["opinions"])
test     = jl(P["test"])
split    = json.loads(P["split_report"].read_text(encoding="utf-8"))
verif    = json.loads(P["verification"].read_text(encoding="utf-8"))
print(f"  {len(opinions):,} opinions, {len(pairs):,} pairs, {len(test):,} test items")

# Declared inputs that are not stored as result files.
PILOT_BEFORE = {"copying": 45.6, "reasoning": 16.5, "no_legal_vocab": 57.4}   # 333-pair pilot, original prompt (outputs not retained)
TRAINING_LOG = {   # seed 42, from the fine-tuning notebook's log
    "steps": [100, 200, 300, 400, 500, 600, 700, 800, 856],
    "train": [1.1292, 1.1238, 1.1074, 1.0703, 1.0446, 1.0655, 1.0439, 1.0444, 1.0249],
    "val":   [1.1417, 1.1134, 1.0966, 1.0773, 1.0669, 1.0561, 1.0478, 1.0457, 1.0456]}

# Results figures are drawn only if the scores belong to the current test split.
ev = json.loads(P["evaluation"].read_text(encoding="utf-8")) if P["evaluation"].exists() else None
sb = json.loads(P["sbert"].read_text(encoding="utf-8")) if P["sbert"].exists() else None
RESULTS_CURRENT = bool(ev and ev.get("b0", {}).get("n") == len(test)
                       and sb and sb.get("b0", {}).get("n") == len(test))
print("  results are current for this test split" if RESULTS_CURRENT else
      f"  results NOT current (evaluation n={ev.get('b0',{}).get('n') if ev else None}, "
      f"test n={len(test)}): figures 4.5-4.8 will be skipped")
''')

md(r'''
## 2. Figure 3.1: pipeline architecture
''')

code(r'''
BAND = {"acq": "#eef4fc", "gen": "#eaf7f2", "data": "#fdf5e3", "eval": "#f3f2ef"}

def node(ax, x, y, w, h, title, sub=None, accent=S1, fs=8.6, subfs=6.9, fill="white"):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0,rounding_size=0.07",
                                fc=fill, ec="#dcdbd5", lw=0.8, zorder=2))
    ax.add_patch(FancyBboxPatch((x, y), 0.07, h, boxstyle="round,pad=0,rounding_size=0.03",
                                fc=accent, ec="none", zorder=3))
    cx = x + w / 2 + 0.03
    if sub:
        ax.text(cx, y + h * 0.66, title, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=INK, zorder=4)
        ax.text(cx, y + h * 0.30, sub, ha="center", va="center", fontsize=subfs,
                color=INK2, zorder=4, linespacing=1.3)
    else:
        ax.text(cx, y + h / 2, title, ha="center", va="center", fontsize=fs,
                fontweight="bold", color=INK, zorder=4)

def link(ax, p1, p2, colour=MUTED, style="-|>", ls="-"):
    ax.add_patch(FancyArrowPatch(p1, p2, arrowstyle=style, mutation_scale=10, color=colour,
                                 lw=1.1, ls=ls, zorder=1, shrinkA=2, shrinkB=2))

def note(ax, x, y, text, colour=INK2, weight="normal", size=7.0):
    ax.text(x, y, text, ha="center", va="center", fontsize=size, color=colour, fontweight=weight)

n_op, n_pairs = len(opinions), len(pairs)
src_words = sum(o["source_word_count"] for o in opinions)
bind_words = sum(len(o["text"].split()) for o in opinions)
nonbinding = 100 * (1 - bind_words / src_words)
sp = {s["split"]: s for s in split["splits"]}
contam = 100 * split["leakage"]["pair_level_contamination"]

fig, ax = plt.subplots(figsize=(13.8, 5.0))
ax.set_xlim(0, 13.8); ax.set_ylim(0.05, 4.9); ax.axis("off")
for x0, x1, lab, fill in [(0.05, 3.2, "1  ACQUISITION", BAND["acq"]),
                          (3.3, 8.6, "2  GENERATION", BAND["gen"]),
                          (8.7, 11.0, "3  DATASET", BAND["data"]),
                          (11.1, 13.75, "4  EVALUATION", BAND["eval"])]:
    ax.add_patch(FancyBboxPatch((x0, 0.12), x1 - x0, 4.72, boxstyle="round,pad=0,rounding_size=0.12",
                                fc=fill, ec="none", zorder=0))
    ax.text(x0 + 0.16, 4.62, lab, ha="left", va="center", fontsize=8.4,
            fontweight="bold", color=INK2)

# stage 1
node(ax, 0.22, 3.62, 1.36, 0.72, "SCDB", "9,341 cases,\nexpert coded", accent=S1)
node(ax, 1.72, 3.62, 1.36, 0.72, "COLD Cases", "dated public\nsnapshot", accent=S1)
link(ax, (0.9, 3.62), (1.4, 3.3)); link(ax, (2.4, 3.62), (1.9, 3.3))
node(ax, 0.55, 2.58, 2.2, 0.7, "Join and deduplicate", "by citation, then\nnormalised name key", accent=S1)
link(ax, (1.65, 2.58), (1.65, 2.32))
node(ax, 0.55, 1.6, 2.2, 0.7, "Segment", "keep the opinion of the Court\nand per curiam text", accent=S1)
link(ax, (1.65, 1.6), (1.65, 1.34))
node(ax, 0.55, 0.66, 2.2, 0.66, "Audit", "wrong documents out;\ncut at first separate writing", accent=S2)
note(ax, 1.65, 0.38, f"{n_op:,} opinions", INK, "bold", 7.4)
note(ax, 1.65, 0.21, f"{nonbinding:.1f}% of collected text is not binding", INK2, "normal", 6.6)
link(ax, (2.75, 0.97), (3.48, 1.4))

# stage 2
node(ax, 3.48, 1.05, 1.2, 0.72, "Chunk", "900 words,\n150 overlap", accent=S3)
note(ax, 4.08, 0.8, "8,920 windows")
link(ax, (4.08, 1.77), (4.08, 2.28))
node(ax, 3.48, 2.28, 1.2, 0.72, "Band", "early, middle\nor late", accent=S3)
link(ax, (4.68, 2.64), (5.12, 2.64))
node(ax, 5.12, 2.2, 1.34, 0.88, "Generate", "question, answer\nand a quoted span", accent=S3)
link(ax, (6.46, 2.64), (6.9, 2.64))
node(ax, 6.9, 2.2, 1.34, 0.88, "Verify span", "is the quotation\nin the opinion?", accent=S2)
note(ax, 7.8, 1.95, "no", INK2, "bold")
link(ax, (7.57, 2.2), (7.57, 1.72), colour=S2)
node(ax, 6.93, 1.08, 1.28, 0.6, "discard", accent=S2, fs=8.0, fill="#fdf1ec")
link(ax, (7.57, 3.08), (7.57, 3.5))
node(ax, 6.78, 3.5, 1.58, 0.72, "Answer check", "reject if it copies\nthe span", accent=S2)
link(ax, (8.36, 3.86), (8.92, 4.02), colour=INK2)

# stage 3
node(ax, 8.86, 3.62, 1.98, 0.8, "USLegalQA", f"{n_pairs:,} pairs, each with\na span and offsets",
     accent=S4, fs=9.2)
link(ax, (9.85, 3.62), (9.85, 3.3))
node(ax, 8.86, 2.54, 1.98, 0.74, "Split by opinion",
     f"{sp['train']['opinions']} / {sp['val']['opinions']} / {sp['test']['opinions']} opinions", accent=S4)
note(ax, 9.85, 2.3, "overlap 0%", INK, "bold")
note(ax, 9.85, 2.08, f"by question it would be {contam:.1f}%")
link(ax, (9.85, 1.98), (9.85, 1.7))
node(ax, 8.86, 0.94, 1.98, 0.74, "Train / val / test",
     f"{sp['train']['pairs']:,} / {sp['val']['pairs']:,} / {sp['test']['pairs']:,}\npairs", accent=S4)
link(ax, (10.84, 1.31), (11.3, 1.31))

# stage 4
for i, (lab, sub, col) in enumerate([("B0  extractive", "no model at all", S1),
                                      ("B1  closed book", "no passage given", S2),
                                      ("B2  open book", "passage given", S3),
                                      ("F1  fine tuned", "QLoRA, three seeds", S4)]):
    node(ax, 11.3, 3.72 - i * 0.7, 2.3, 0.6, lab, sub, accent=col, fs=8.2, subfs=6.6)
node(ax, 11.3, 0.62, 2.3, 0.78, "Evaluation harness",
     "each system against its own floor;\nCIs and paired bootstrap", accent=MUTED, fs=8.3, subfs=6.5)
for i in range(4):
    ax.plot([12.45, 12.45], [3.72 - i * 0.7, 3.62 - i * 0.7], color=GRID, lw=0.9, zorder=1)
save(fig, "architecture")
''')

md(r'''
## 3. Figure 3.2: composition of the collected text
''')

code(r'''
binding = 100 * bind_words / src_words
fig, ax = plt.subplots(figsize=(6.6, 1.95))
ax.set_xlim(0, 100); ax.set_ylim(-0.6, 0.6); ax.set_yticks([]); ax.grid(False)
ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
frame(fig, f"Only {binding:.1f} per cent of the collected text states the law",
      f"{src_words/1e6:.2f} million words collected across {n_op:,} opinions")
rbar(ax, 0, binding, 0.5, S1, horizontal=True)
ax.add_patch(Rectangle((binding, -0.25), 100 - binding, 0.5, fc="#d9d8d2", ec="none", zorder=3))
ax.plot([binding, binding], [-0.25, 0.25], color=SURFACE, lw=2.2, zorder=4)   # surface gap
ax.text(binding / 2, 0, f"{binding:.1f}%  opinion of the Court and per curiam",
        ha="center", va="center", color="white", fontsize=8.2, fontweight="bold", zorder=5)
ax.text(binding + (100 - binding) / 2, 0, f"{100-binding:.1f}%  syllabus, concurrences, dissents",
        ha="center", va="center", color=INK, fontsize=8.2, fontweight="bold", zorder=5)
save(fig, "coverage")
''')

md(r'''
## 4. Figure 4.1: dataset composition
''')

code(r'''
qt = Counter(p["question_type"] for p in pairs)
order = ["legal_principle", "holding", "facts", "procedural", "outcome"]
qt_vals = [100 * qt[o] / len(pairs) for o in order]
qt_labels = ["legal\nprinciple", "holding", "facts", "proce-\ndural", "outcome"]
cat = Counter(o["category"] for o in opinions)
top = cat.most_common(6)
cat_labels = [k.replace("_", " ") for k, _ in top] + ["other"]
cat_vals = [100 * v / n_op for _, v in top]
cat_vals.append(100 - sum(cat_vals))

fig, (a1, a2) = plt.subplots(1, 2, figsize=(8.0, 3.2), gridspec_kw={"width_ratios": [1.1, 1.15]})
a1.set_xlim(-0.6, 4.6); a1.set_ylim(0, 66); a1.set_xticks(range(5)); a1.set_xticklabels(qt_labels)
a1.set_yticks([0, 20, 40, 60]); a1.set_yticklabels(["0%", "20%", "40%", "60%"])
a1.set_title("Question type, share of pairs", loc="left", fontsize=8.6, color=INK2)
a2.set_ylim(-0.6, len(cat_labels) - 0.4); a2.set_xlim(0, 34); a2.invert_yaxis()
a2.set_yticks(range(len(cat_labels))); a2.set_yticklabels(cat_labels)
a2.grid(axis="x"); a2.grid(axis="y", visible=False)
a2.set_xticks([0, 10, 20, 30]); a2.set_xticklabels(["0%", "10%", "20%", "30%"])
a2.set_title("SCDB issue area, share of opinions", loc="left", fontsize=8.6, color=INK2)
frame(fig, "Composition of the released dataset",
      f"{len(pairs):,} pairs from {n_op:,} opinions; issue areas as coded by the Supreme Court Database")
for i, v in enumerate(qt_vals):
    rbar(a1, i, v, 0.56, S1)
    a1.text(i, v + 1.6, f"{v:.1f}%", ha="center", fontsize=7.8, color=INK, fontweight="bold")
for i, v in enumerate(cat_vals):
    rbar(a2, i, v, 0.6, S1 if cat_labels[i] != "other" else "#c9c8c2", horizontal=True)
    a2.text(v + 0.6, i, f"{v:.1f}%", va="center", fontsize=7.8, color=INK)
save(fig, "composition")
''')

md(r'''
## 5. Figures 4.2 to 4.4: the RQ2 measurements
''')

code(r'''
# --- Figure 4.2: apparent failure by verification method, against fabrication ---
af = verif["apparent_failure_pct"]
methods = ["exact", "normalised", "word", "artefact"]
labels = ["Exact\nstring", "+ whitespace\nand quotes", "+ word\nsequence", "+ artefact\nremoval"]
vals = [af[m] for m in methods]
fab = verif["fabrication"]["pct"]; fab_hi = verif["fabrication"]["ci95_pct"][1]
n_cand = verif["candidates_with_span"]

fig, ax = plt.subplots(figsize=(6.6, 3.3))
ax.set_xlim(-0.6, 3.6); ax.set_ylim(0, 88); ax.set_xticks(range(4)); ax.set_xticklabels(labels)
ax.set_yticks([0, 20, 40, 60, 80]); ax.set_yticklabels(["0%", "20%", "40%", "60%", "80%"])
frame(fig, "The verification method, not the generator, sets the apparent failure rate",
      f"{n_cand} retained candidates from 30 random opinions; fabrication classified by the author")
for i, v in enumerate(vals):
    rbar(ax, i, v, 0.5, S1)
    ax.text(i, v + 2.2, f"{v:.1f}%", ha="center", fontsize=8.4, fontweight="bold", color=INK)
ax.plot(range(4), [fab] * 4, color=S2, lw=2.2, zorder=5, solid_capstyle="round")
ax.scatter(range(4), [fab] * 4, s=46, color=S2, edgecolor=SURFACE, linewidth=1.8, zorder=6)
key(ax, [("Apparent failure rate", S1, "sq"),
         (f"Classified fabrication: {fab:.2f}% (95% CI up to {fab_hi:.2f}%)", S2, "line")],
    loc="upper right")
save(fig, "verification")

# --- Figure 4.2b: what the failures are ---
cls = verif["classification"]
order = [("citation_omitted", "Citation omitted, no ellipsis"),
         ("page_furniture", "Page header or footnote interrupts"),
         ("unmarked_omission", "Running text omitted, no ellipsis"),
         ("encoding_artefact", "Encoding fault in the source"),
         ("misquotation", "Verbatim words spliced or reordered"),
         ("from_memory", "Accurate text from outside the passage"),
         ("fabrication", "Wording absent from the source")]
names = [lab for _, lab in order]; counts = [cls.get(k, 0) for k, _ in order]
benign = {"citation_omitted", "page_furniture", "unmarked_omission", "encoding_artefact"}
fig, ax = plt.subplots(figsize=(6.6, 3.1))
ax.set_ylim(-0.6, len(order) - 0.4); ax.invert_yaxis(); ax.set_xlim(0, 100)
ax.set_yticks(range(len(order))); ax.set_yticklabels(names)
ax.grid(axis="x"); ax.grid(axis="y", visible=False)
frame(fig, f"What the {sum(counts)} rejected quotations actually are",
      "Verbatim quotation (blue) or unfaithful to the source (orange); each classified by hand")
for i, ((k, _), c) in enumerate(zip(order, counts)):
    rbar(ax, i, c, 0.6, S1 if k in benign else S2, horizontal=True)
    ax.text(c + 1.2, i, f"{c}", va="center", fontsize=8.2, color=INK, fontweight="bold")
save(fig, "failures")
''')

code(r'''
# --- Figure 4.3: pilot against the released dataset ---
from uslegalqa.assess_quality import auto_report
after = auto_report(pairs)
AFTER = {"copying": after["near_copy_answers_pct"], "reasoning": after["asks_reasoning_pct"],
         "no_legal_vocab": after["no_legal_terms_pct"]}
copy_rej = 100 * verif["validate_outcomes"].get("answer_copies_span", 0) / n_cand

keys_ = ["copying", "reasoning", "no_legal_vocab"]
labels = ["Answers reproducing\nthe span", "Questions requiring\nreasoning", "Questions with no\nlegal vocabulary"]
fig, ax = plt.subplots(figsize=(6.6, 3.3))
ax.set_xlim(-0.6, 2.6); ax.set_ylim(0, 84); ax.set_xticks(range(3)); ax.set_xticklabels(labels)
ax.set_yticks([0, 20, 40, 60]); ax.set_yticklabels(["0%", "20%", "40%", "60%"])
frame(fig, "Prompt design and output validation govern question quality",
      f"Generation model held constant; the copy constraint still rejects {copy_rej:.1f}% of candidates under the revised prompt")
w = 0.34
for i, k in enumerate(keys_):
    rbar(ax, i - w / 2 - 0.01, PILOT_BEFORE[k], w, S1)
    rbar(ax, i + w / 2 + 0.01, AFTER[k], w, S2)
    ax.text(i - w / 2, PILOT_BEFORE[k] + 1.8, f"{PILOT_BEFORE[k]:.1f}%", ha="center", fontsize=7.8, color=INK)
    ax.text(i + w / 2, AFTER[k] + 1.8, f"{AFTER[k]:.1f}%", ha="center", fontsize=7.8, color=INK, fontweight="bold")
key(ax, [("Pilot, original prompt (n = 333)", S1, "sq"),
         (f"Released, revised prompt and copy constraint (n = {len(pairs):,})", S2, "sq")],
    loc="upper left", ncol=2)
save(fig, "quality")

# --- Figure 4.4: partition overlap ---
fig, ax = plt.subplots(figsize=(6.6, 2.2))
ax.set_ylim(-0.6, 1.6); ax.set_xlim(0, 108); ax.invert_yaxis()
ax.set_yticks([0, 1]); ax.set_yticklabels(["Split by question\n(conventional)", "Split by opinion\n(this work)"])
ax.grid(axis="x"); ax.grid(axis="y", visible=False)
ax.set_xticks([0, 25, 50, 75, 100]); ax.set_xticklabels(["0%", "25%", "50%", "75%", "100%"])
frame(fig, "Splitting by question puts almost every test opinion in training",
      f"Share of test questions whose source opinion is also in training; mean of "
      f"{split['leakage']['pair_level_trials']} random question-level splits")
rbar(ax, 0, contam, 0.5, S2, horizontal=True)
ax.text(contam - 2, 0, f"{contam:.1f}%", ha="right", va="center", color="white", fontweight="bold", fontsize=9)
ax.text(1.8, 1, "0.0%  no test opinion appears in training", va="center", color=INK, fontweight="bold", fontsize=8.6)
save(fig, "leakage")
''')

md(r'''
## 6. Figures 4.5 to 4.8: the RQ3 comparison

Drawn only when `evaluation.json` and `sbert_meteor.json` were scored on the
current test split. F1 is the mean of seeds 42, 1 and 2. Every system is shown
against its own floor, meaning its own predictions scored against unrelated
references.
''')

code(r'''
SYS = ["B0", "B1", "B2", "F1"]
SYS_LABEL = {"B0": "B0\nextractive", "B1": "B1\nclosed book", "B2": "B2\nopen book", "F1": "F1\nfine tuned"}
SEEDS = ["f1_seed42", "f1_seed1", "f1_seed2"]

def metric(sys_, m, part="overall"):
    """Mean (and seed SD for F1) of an evaluation.json metric."""
    keys_ = SEEDS if sys_ == "F1" else [sys_.lower()]
    v = [ev[k][part][m]["mean"] for k in keys_]
    return float(np.mean(v)), (float(np.std(v, ddof=1)) if len(v) > 1 else 0.0)

def sbm(sys_, m):
    keys_ = SEEDS if sys_ == "F1" else [sys_.lower()]
    v = [sb[k][m]["mean"] if isinstance(sb[k][m], dict) else sb[k][m] for k in keys_]
    return float(np.mean(v)), (float(np.std(v, ddof=1)) if len(v) > 1 else 0.0)

if not RESULTS_CURRENT:
    print("  skipped: re-run this section once the re-scoring on the current test split has finished")
else:
    # --- Figure 4.5: systems against their own floors ---
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(7.6, 3.4))
    panels = [(a1, "rouge1_f", "ROUGE-1 F"), (a2, "bertscore_rescaled", "BERTScore, baseline rescaled")]
    lims = {}
    for ax, m, title in panels:
        v = [metric(s, m)[0] for s in SYS]; f = [metric(s, m, "floor")[0] for s in SYS]
        lo = min(0, min(v + f)) - 0.06; hi = max(v + f) * 1.2
        ax.set_xlim(-0.6, 3.6); ax.set_ylim(lo, hi); ax.set_xticks(range(4))
        ax.set_xticklabels([SYS_LABEL[s] for s in SYS]); ax.set_title(title, loc="left", fontsize=8.6, color=INK2)
        ax.axhline(0, color="#c9c8c2", lw=0.9, zorder=2)
        lims[m] = (v, f)
    frame(fig, "Supplying the passage matters most; fine-tuning adds a further gain",
          f"Test split, n = {len(test):,}. Grey tick: the system's own floor. F1: mean of three seeds, bar shows seed SD")
    for ax, m, _ in panels:
        v, f = lims[m]
        for i, s in enumerate(SYS):
            rbar(ax, i, v[i], 0.52, SYSTEM_COLOUR[s])
            floor_tick(ax, i, f[i], 0.52)
            sd = metric(s, m)[1]
            if sd:
                ax.errorbar(i, v[i], yerr=sd, color=INK, capsize=3, lw=1, zorder=6)
            pad = (ax.get_ylim()[1] - ax.get_ylim()[0]) * 0.035
            y = max(v[i], f[i], 0) + pad          # negative bars: label sits above the zero line
            ax.text(i, y, f"{v[i]:.3f}", ha="center", fontsize=7.8, color=INK, fontweight="bold")
    save(fig, "systems")

    # --- Figure 4.6: precision and recall separated ---
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    prec = [metric(s, "rouge1_p")[0] for s in SYS]; rec = [metric(s, "rouge1_r")[0] for s in SYS]
    ratio = [np.mean([ev[k]["diagnostics"]["length_ratio"] for k in (SEEDS if s == "F1" else [s.lower()])]) for s in SYS]
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(0, max(prec + rec) * 1.3); ax.set_xticks(range(4))
    ax.set_xticklabels([SYS_LABEL[s] for s in SYS])
    frame(fig, "Part of the fine-tuning gain is answer length, not content",
          "ROUGE-1 precision and recall reported separately; label: generated length / reference length")
    w = 0.34
    for i in range(4):
        rbar(ax, i - w / 2 - 0.01, prec[i], w, S1); rbar(ax, i + w / 2 + 0.01, rec[i], w, S2)
        ax.text(i, max(prec[i], rec[i]) + 0.025, f"length {ratio[i]:.2f}×", ha="center", fontsize=7.8, color=INK2)
    key(ax, [("ROUGE-1 precision", S1, "sq"), ("ROUGE-1 recall", S2, "sq")], loc="upper left")
    save(fig, "precrecall")

    # --- Figure 4.7: four measures, each above its own floor ---
    four = {
        "ROUGE-1 F": [metric(s, "rouge1_f")[0] - metric(s, "rouge1_f", "floor")[0] for s in SYS],
        "METEOR": [sbm(s, "meteor")[0] - sbm(s, "meteor_floor")[0] for s in SYS],
        "Sentence-BERT": [sbm(s, "sbert")[0] - sbm(s, "sbert_floor")[0] for s in SYS],
        "BERTScore rescaled": [metric(s, "bertscore_rescaled")[0] - metric(s, "bertscore_rescaled", "floor")[0] for s in SYS],
    }
    fig, ax = plt.subplots(figsize=(7.2, 3.5))
    allv = [x for v in four.values() for x in v]
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(min(0, min(allv)) - 0.03, max(allv) * 1.22)
    ax.set_xticks(range(4)); ax.set_xticklabels([SYS_LABEL[s] for s in SYS])
    ax.axhline(0, color="#c9c8c2", lw=0.9, zorder=2)
    frame(fig, "Every measure agrees on the large differences",
          "Score above each measure's own floor; the B0 against B1 ordering depends on the measure")
    w = 0.19
    for j, (name, vals) in enumerate(four.items()):
        for i, v in enumerate(vals):
            rbar(ax, i + (j - 1.5) * (w + 0.015), v, w, [S1, S2, S3, S4][j], r_px=3)
    key(ax, [(n, c, "sq") for n, c in zip(four, [S1, S2, S3, S4])], loc="upper left", ncol=2)
    save(fig, "metrics")

    # --- Figure 4.8: per issue area, closed against open book ---
    ops_by_cat = Counter({r["cluster_id"]: r["category"] for r in test}.values())
    cats = [c for c, n in ops_by_cat.most_common() if n >= 5]
    b1 = [ev["b1"]["by"]["category"][c]["rouge1_f"]["mean"] for c in cats]
    b2 = [ev["b2"]["by"]["category"][c]["rouge1_f"]["mean"] for c in cats]
    fig, ax = plt.subplots(figsize=(6.6, 3.3))
    ax.set_xlim(-0.4, len(cats) - 0.6); ax.set_ylim(0, max(b2) * 1.25)
    ax.set_xticks(range(len(cats))); ax.set_xticklabels([c.replace("_", "\n") for c in cats])
    frame(fig, "Supplying the passage narrows the gap between issue areas",
          f"ROUGE-1 F by issue area; areas with at least five test opinions ({sum(ops_by_cat[c] for c in cats)} opinions)")
    for vals, col, lab in [(b1, S2, "B1 closed book"), (b2, S3, "B2 open book")]:
        ax.plot(range(len(cats)), vals, color=col, lw=2, zorder=4, solid_capstyle="round")
        ax.scatter(range(len(cats)), vals, s=46, color=col, edgecolor=SURFACE, linewidth=1.8, zorder=5)
        ax.text(len(cats) - 0.55, vals[-1], f"{lab}\nspread {max(vals)-min(vals):.3f}",
                va="center", fontsize=7.6, color=INK)
    ax.set_xlim(-0.4, len(cats) + 0.6)
    save(fig, "contamination")

    # --- seed stability ---
    names = ["B2 open book", "F1 seed 42", "F1 seed 1", "F1 seed 2"]
    vals = [ev["b2"]["overall"]["bertscore_rescaled"]["mean"]] + \
           [ev[k]["overall"]["bertscore_rescaled"]["mean"] for k in SEEDS]
    fig, ax = plt.subplots(figsize=(6.2, 3.0))
    ax.set_xlim(-0.6, 3.6); ax.set_ylim(0, max(vals) * 1.22); ax.set_xticks(range(4)); ax.set_xticklabels(names)
    sd = float(np.std(vals[1:], ddof=1))
    frame(fig, f"The fine-tuning gain is stable across seeds (SD {sd:.4f})",
          "BERTScore, baseline rescaled, on the test split")
    for i, v in enumerate(vals):
        rbar(ax, i, v, 0.5, S3 if i == 0 else S4)
        ax.text(i, v + 0.012, f"{v:.4f}", ha="center", fontsize=8, fontweight="bold", color=INK)
    save(fig, "seeds")
''')

md(r'''
## 7. Design comparison and training convergence
''')

code(r'''
# --- design properties across resources (coded from each paper; matches Table 4.7) ---
res = ["CaseHOLD\n(2021)", "CUAD\n(2021)", "ILDC\n(2021)", "IndicLegalQA\n(2025)", "USLegalQA\n(this work)"]
props = ["Free-form answers", "Full document source", "Answer linked to a span",
         "Generator error rate reported", "Document-level split reported",
         "Baseline grid with floors", "Expert annotation"]
M = [[0, 0, 0, 1, 1],
     [0, 1, 1, 1, 1],
     [0, 1, 0, 0, 1],
     [0, 0, 0, 0, 1],
     [0, 0, 0, 0, 1],
     [0, 0, 0, 0, 1],
     [0, 1, 0.5, 0, 0]]
fig, ax = plt.subplots(figsize=(6.8, 3.7))
cmap = mcolors.ListedColormap([NEUTRAL, BLUE_RAMP["250"], BLUE_RAMP["450"]])
norm = mcolors.BoundaryNorm([-0.01, 0.25, 0.75, 1.01], cmap.N)
ax.imshow(M, cmap=cmap, norm=norm, aspect="auto")
ax.set_xticks(range(len(res))); ax.set_xticklabels(res)
ax.set_yticks(range(len(props))); ax.set_yticklabels(props)
ax.xaxis.tick_top(); ax.grid(False)
for i in range(len(props)):
    for j in range(len(res)):
        v = M[i][j]
        ax.text(j, i, "yes" if v == 1 else ("partly" if v == 0.5 else "–"), ha="center", va="center",
                fontsize=7.8, color="white" if v == 1 else INK2, fontweight="bold" if v == 1 else "normal")
ax.set_xticks([x - 0.5 for x in range(1, len(res))], minor=True)
ax.set_yticks([y - 0.5 for y in range(1, len(props))], minor=True)
ax.grid(which="minor", color=SURFACE, lw=2.5); ax.tick_params(which="both", length=0)
frame(fig, "What each resource provides", "Coded from each paper; the last row is where this work is weaker")
save(fig, "comparison")

# --- fine-tuning convergence (from the training log) ---
tr = TRAINING_LOG
fig, ax = plt.subplots(figsize=(6.2, 3.0))
ax.set_xlim(60, 900); ax.set_ylim(1.0, 1.16)
ax.set_xlabel("Optimisation step")
frame(fig, "Fine-tuning converges within one epoch", "Cross-entropy loss, seed 42, from the training log")
for vals, col, lab in [(tr["train"], S1, "training"), (tr["val"], S2, "validation")]:
    ax.plot(tr["steps"], vals, color=col, lw=2, solid_capstyle="round", zorder=4)
    ax.scatter(tr["steps"], vals, s=30, color=col, edgecolor=SURFACE, linewidth=1.5, zorder=5)
    ax.text(tr["steps"][-1] + 12, vals[-1], lab, va="center", fontsize=7.8, color=INK)
save(fig, "training")
''')

md(r'''
## 8. The four algorithms

Held as text so the report and the notebook cannot drift apart. Each is written
to `figures/` as a `.txt` file and rendered as a card: numbered gutter,
highlighted keywords, muted comments.
''')

code(r'''
ALGORITHMS = {
"algorithm_1_construct": ("Algorithm 1", "Construct a span-grounded resource", "RQ1", [
"Input   S, a release of the case database",
"        C, a dated snapshot of opinion text",
"        M, a generating model;  k, pairs requested per window",
"Output  D, verified question answer pairs with source offsets",
"",
"D <- empty",
"for each case s in S within the period of interest do",
"    R <- records in C whose citation, or failing that name, matches s",
"    if R is empty or a record's citation disagrees with s then continue",
"    r <- the record in R with the most opinion text",
"    if r was filed > 60 days from s's decision or is not a merits opinion then continue",
"    T <- segment(r)                       // Reports headers, formulas, page headers",
"    if T has no unique binding section then continue",
"    t <- binding text of T, cut at the first separate writing",
"    if |t| < 500 words then continue",
"    W <- chunk(t, 900 words, 150 overlap)",
"    for each window w in W do",
"        b <- band(index of w, |W|)        // early, middle or late",
"        P <- M(prompt(w, b, k))           // each p carries a quoted span",
"        for each pair p in P do",
"            loc <- locate(p.span, w)      // Algorithm 2",
"            if loc is undefined then reject span_not_found; continue",
"            if longest_common_run(p.answer, p.span) > 10 then",
"                reject answer_copies_span; continue",
"            p.start <- w.offset + loc.start;  p.end <- w.offset + loc.end",
"            append p to D",
"return D",
]),
"algorithm_2_locate": ("Algorithm 2", "Locate a quoted span in its source", "RQ1", [
"Input   span, the quotation;  text, the source window",
"Output  character offsets of span in text, or undefined",
"",
"if text contains span exactly then return that position",
"if span contains an ellipsis then",
"    locate each part in order with a moving cursor",
"    if every part is located then return first start, last end",
"x <- alphanumeric characters of span, lowercased",
"y, map <- alphanumeric characters of text, with offsets",
"if x occurs in y then return map of that occurrence",
"repeat the two lines above with star-pagination and footnote",
"    markers blanked in both                // explicitly marked forms only",
"return undefined",
]),
"algorithm_3_rq2": ("Algorithm 3", "Measure what standard practice would report", "RQ2", [
"3a  verification method against fabrication",
"G <- 30 opinions drawn at random;  generate as in Algorithm 1, retaining every candidate",
"for each method m in {exact, normalised, word sequence, artefact removal} do",
"    f[m] <- fraction of candidates that m fails to locate",
"classify by hand every candidate the final method rejects",
"F <- fraction of all candidates classified as fabricated, with a 95% interval",
"report f[m] for every m against the single value F",
"",
"3b  prompt and validation",
"hold the model and its temperature constant",
"q[pilot] <- quality signals under the original prompt",
"q[release] <- quality signals of the released dataset",
"c <- fraction of retained candidates rejected by the copy constraint",
"report q[pilot] against q[release], with c",
"",
"3c  partition overlap",
"for trial = 1 to 20 do",
"    assign pairs at random to train, validation and test, 80 / 10 / 10",
"    o[trial] <- fraction of test pairs whose opinion is in train",
"assign whole opinions instead",
"o_opinion <- the same fraction under that assignment",
"report the mean of o against o_opinion",
]),
"algorithm_4_rq3": ("Algorithm 4", "Compare the systems", "RQ3", [
"Input   D_test, the test split;  A, the reference answers",
"Output  per-system scores with intervals and floors, and paired comparisons",
"",
"G <- shuffle(A) so that no item keeps its own reference",
"for each system in {B0, B1, B2, F1} do",
"    H <- predictions of the system on D_test",
"    diagnose(H)                           // empty, length ratio, duplicates",
"    for each measure m in {ROUGE, METEOR, BERTScore, SBERT} do",
"        v[m] <- m(A, H)                   // per-item scores",
"        floor[m] <- m(G, H)               // this system against unrelated references",
"        report mean of v[m], its bootstrap interval, and floor[m]",
"for each system other than B2 do",
"    d <- per-item difference against B2",
"    resample d 2,000 times; report the mean and a two-sided p value",
"repeat for training seeds 42, 1 and 2; report mean and SD across seeds",
]),
}

KEYWORDS = {"for", "each", "do", "if", "then", "else", "return", "continue", "repeat",
            "report", "append", "reject", "in", "to", "and", "or", "Input", "Output",
            "classify", "assign", "resample", "generate", "locate", "hold"}
MONO = "DejaVu Sans Mono"

def render_card(name, number, title, rq, lines):
    fs = 7.6
    ch_in = fs * 0.6021 / 72                          # monospace advance, inches
    width_chars = max(len(l) for l in lines) + 8
    W = max(7.2, width_chars * ch_in + 0.5)
    line_h = fs * 1.62 / 72
    H = 0.62 + len(lines) * line_h + 0.22
    fig = plt.figure(figsize=(W, H)); ax = fig.add_axes([0, 0, 1, 1]); ax.axis("off")
    ax.set_xlim(0, W); ax.set_ylim(0, H)
    ax.add_patch(FancyBboxPatch((0.04, 0.04), W - 0.08, H - 0.08, boxstyle="round,pad=0,rounding_size=0.1",
                                fc="#fbfbfa", ec="#dcdbd5", lw=0.9))
    ax.add_patch(FancyBboxPatch((0.04, H - 0.52), W - 0.08, 0.48, boxstyle="round,pad=0,rounding_size=0.1",
                                fc=BLUE_RAMP["650"], ec="none"))
    ax.add_patch(Rectangle((0.04, H - 0.52), W - 0.08, 0.14, fc=BLUE_RAMP["650"], ec="none"))
    ax.text(0.22, H - 0.28, number, fontsize=9.6, fontweight="bold", color="white", va="center")
    ax.text(0.22 + 1.02, H - 0.28, title, fontsize=9.6, color="#dce9fb", va="center")
    ax.add_patch(FancyBboxPatch((W - 0.72, H - 0.39), 0.5, 0.22, boxstyle="round,pad=0,rounding_size=0.08",
                                fc=S4, ec="none"))
    ax.text(W - 0.47, H - 0.28, rq, fontsize=7.4, fontweight="bold", color=INK, ha="center", va="center")
    gutter_x = 0.52; code_x = 0.66
    ax.plot([0.58, 0.58], [0.12, H - 0.6], color="#e6e5e0", lw=0.8)
    n = 0
    for i, ln in enumerate(lines):
        y = H - 0.62 - (i + 0.62) * line_h
        head = ln[:3] in {"3a ", "3b ", "3c "}
        io = ln.startswith(("Input", "Output")) or (ln.startswith("        ") and i < 4 and not head)
        if ln.strip() and not head and not io:
            n += 1
            ax.text(gutter_x, y, str(n), fontsize=fs - 0.6, color=MUTED, ha="right", va="center", family=MONO)
        if head:
            ax.text(code_x, y, ln, fontsize=fs, fontweight="bold", color=BLUE_RAMP["550"], va="center", family=MONO)
            continue
        body, _, comment = ln.replace("<-", "←").partition("//")
        col = 0
        for tok in _tokens(body):
            is_kw = tok in KEYWORDS
            ax.text(code_x + col * ch_in, y, tok, fontsize=fs, family=MONO, va="center",
                    color=BLUE_RAMP["550"] if is_kw else INK, fontweight="bold" if is_kw else "normal")
            col += len(tok)
        if comment:
            ax.text(code_x + col * ch_in, y, "//" + comment, fontsize=fs, family=MONO, va="center",
                    color=MUTED, style="italic")
    fig.savefig(OUT / f"{name}.png", facecolor="white", dpi=220)
    plt.close(fig)
    print(f"  wrote figures/{name}.png")

def _tokens(s):
    import re
    return [t for t in re.split(r"(\s+|[^\w\s])", s) if t]

for name, (number, title, rq, lines) in ALGORITHMS.items():
    (OUT / f"{name}.txt").write_text(f"{number}  {title}  ({rq})\n\n" + "\n".join(lines), encoding="utf-8")
    render_card(name, number, title, rq, lines)

# Retire the listings from the earlier three-algorithm appendix.
for old in ["algorithm_1_rq1", "algorithm_2_rq2", "algorithm_3_rq3"]:
    for ext in (".png", ".txt"):
        p = OUT / f"{old}{ext}"
        if p.exists():
            p.unlink(); print(f"  removed superseded figures/{p.name}")
''')

md(r'''
## 9. What was produced
''')

code(r'''
expected = ["architecture", "coverage", "composition", "verification", "failures", "quality",
            "leakage", "comparison", "training",
            "algorithm_1_construct", "algorithm_2_locate", "algorithm_3_rq2", "algorithm_4_rq3"]
results = ["systems", "precrecall", "metrics", "contamination", "seeds"]
for f in sorted(OUT.glob("*.png")):
    print(f"  {f.name:<32}{f.stat().st_size/1024:>8.1f} KB")
missing = [e for e in expected + (results if RESULTS_CURRENT else []) if not (OUT / f"{e}.png").exists()]
print(f"\nmissing: {missing}" if missing else "\nEvery expected artefact was produced.")
if not RESULTS_CURRENT:
    print("Results figures (systems, precrecall, metrics, contamination, seeds) wait for the re-scoring.")
''')

nb = {"cells": cells, "metadata": {"kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
                                   "language_info": {"name": "python"}},
      "nbformat": 4, "nbformat_minor": 5}
Path("USLegalQA_Figures.ipynb").write_text(json.dumps(nb, indent=1, ensure_ascii=False), encoding="utf-8")
print("notebook written:", len(cells), "cells")
