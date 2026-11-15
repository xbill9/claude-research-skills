"""Build Story.html: a 6-page A4 graphic story of the Loop-Breaker paper.

    python3 story_numbers_build.py   # writes story_numbers.json
    python3 build_story.py           # writes Story.html, runs the overlap and number checks

Every number in the text is a {key} placeholder filled from story_numbers.json; charts and tables
read the same file. T() refuses any digit typed straight into the script unless it is part of a
name (Gemma 4, Trap-25, M3, Call-12, ...).
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import story_svg_engine as E
from story_svg_engine import Panel, bubble, caption, blackboard, bar_chart, diamond, box, arrow, sfx, put, PALETTE as P

HERE = Path(__file__).resolve().parent
NUM = json.loads((HERE / "story_numbers.json").read_text())["numbers"]
DISPLAY = {k: v["display"] for k, v in NUM.items()}
USED: set[str] = set()
LINT: list[str] = []

ALLOWED = [r"gemma-4-31b-it-qat-w4a16-ct", r"requests-trap-10", r"sci-trap-2[1-5]", r"G4-31B", r"Gemma 4", r"31B",
           r"W4A16", r"INT4", r"4-bit", r"Trap-25", r"Lean-6", r"Call-12", r"\bM[0-6]\b", r"Stage-1", r"1-hop",
           r"Turn-1", r"Recall@3", r"\bL4\b", r"Laws? [1-4]", r"& 3\b", r"6-Relation", r"\bD1\b", r"Proposition [12]",
           r"Table [123]", r"p\.[1-5]", r"§3\.[1-4]", r"§[45]", r"-vv", r"[Pp]age [1-6]"]


def V(key):
    USED.add(key)
    return NUM[key]["value"]


def T(s: str) -> str:
    stripped = re.sub(r"\{[a-zA-Z0-9_]+\}", "", s)
    for pat in ALLOWED:
        stripped = re.sub(pat, "", stripped)
    if re.search(r"\d", stripped):
        LINT.append(f"typed number in: {s!r} -> {stripped!r}")
    for k in re.findall(r"\{([a-zA-Z0-9_]+)\}", s):
        USED.add(k)
    return s.format_map(DISPLAY)


PAGE_W, PAGE_H = 794, 1123
PROBLEMS: list[str] = []


class Page:
    def __init__(self, num, title, subtitle, sources):
        self.num, self.title, self.subtitle, self.sources = num, title, subtitle, sources
        self.items: list[str] = []

    def panel(self, x, y, panel: Panel):
        PROBLEMS.extend(panel.check())
        if x + panel.w > PAGE_W - 20 or y + panel.h > PAGE_H - 28:
            PROBLEMS.append(f"page {self.num}: panel {panel.name} runs off the page")
        self.items.append(f'<div class="panel" style="left:{x}px;top:{y}px;width:{panel.w}px;height:{panel.h}px">{panel.svg()}</div>')

    def html_panel(self, x, y, w, h, inner, name):
        self.items.append(f'<div class="panel htmlp" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px" id="{name}">{inner}</div>')

    def html(self):
        return (f'<section class="page"><header><span class="pn">{self.num}/6</span><h1>{E.esc(self.title)}</h1>'
                f'<span class="sub">{E.esc(self.subtitle)}</span></header>{"".join(self.items)}'
                f'<footer>Numbers: story_numbers.json &middot; {E.esc(self.sources)}</footer></section>')


L, R_, FULL, HALF, G = 22, 403, 750, 369, 12  # left x, right x, full width, half width, gutter


# =================================================================================================
# Page 1 - the problem
# =================================================================================================
def page1():
    pg = Page(1, "Minute 15", "The setup: a 4-bit coding agent in a strict harness", "PDF p.1 Abstract, §1")
    p = Panel("1a", FULL, 262)
    caption(p, T("A 4-bit quantized Gemma 4 coding agent repairs real Python repositories inside a Docker harness."), 10, 10, 728)
    st = put(p, "scientist", 70, 250, .85, pose="point")
    rt = put(p, "robot", 300, 250, .9, expr="happy", pose="wave")
    bubble(p, T("Meet G4-31B: gemma-4-31b-it-qat-w4a16-ct on {gpus} NVIDIA L4 GPUs, {vram_gb} of VRAM."), 10, 48, 205, tail=st)
    bubble(p, T("Hand me the right file and I write a clean patch!"), 228, 52, 170, tail=rt)
    p.add(f'<rect x="436" y="52" width="300" height="196" rx="10" fill="{P["screen"]}"/>')
    p.add(E.text_block(["BREAKING THE", "15-MINUTE CLIFF"], 586, 66, 27, "black", "#ffe58a", "middle", 1.15))
    p.add(E.text_block(E.wrap("A graphic story of Mirbahar (2026): thinking-mode calibration, co-change graphs and counterfactual context reset.", 270, 12.5),
                       450, 140, 12.5, "regular", "#e6ecff"))
    p.add(E.text_block([T("max_model_len = {max_model_len} tokens")], 586, 214, 12, "mono", "#7df9c1", "middle"))
    pg.panel(L, 62, p)

    p = Panel("1b", HALF, 300)
    caption(p, "Rule book of the harness", 10, 10, 200)
    blackboard(p, 10, 46, 349, 150, [
        (T("• {call_cap} tool calls per episode"), 13, "bold", "#fff"),
        (T("• {time_cap_lo} to {time_cap_hi} seconds per task"), 13, "bold", "#fff"),
        (T("• {global_hours} global wall-clock budget"), 13, "bold", "#fff"),
        (T("• history over {compaction_cliff} tokens is compacted ({output_reserve} kept for output)"), 13, "bold", "#ffd27a"),
    ], label="rules")
    st = put(p, "scientist", 300, 292, .62, expr="worried", pose="point_left")
    bubble(p, T("{file_reads_trip} unwindowed file reads trip the summary, and exact line numbers are erased."), 10, 210, 220, tail=st)
    pg.panel(L, 336, p)

    p = Panel("1c", HALF, 300)
    caption(p, "Two containers grade every patch", 10, 10, 260)
    box(p, 12, 52, 140, 62, "Container A  /workspace  (agent edits here)", 11, "#e6eeff", label="A")
    box(p, 214, 52, 143, 62, "Container B  clean copy, hidden tests", 11, "#e7f7ee", label="B")
    arrow(p, 154, 83, 211, 83, text=None)
    p.add(E.text_block(["submit_patch"], 183, 90, 9.5, "mono", E.INK, "middle"))
    box(p, 12, 128, 345, 52, "Stripped before grading: tests/, test_*.py, conftest.py, pytest.ini, pyproject.toml", 10.5, "#fff1f0", "regular", label="strip")
    box(p, 214, 192, 143, 40, "FAIL_TO_PASS + PASS_TO_PASS", 10, "#e7f7ee", label="tests")
    rt = put(p, "robot", 60, 292, .6, expr="neutral", pose="point")
    bubble(p, T("Edits to the tests never reach the grader."), 104, 240, 104, tail=rt, size=11)
    pg.panel(R_, 336, p)

    p = Panel("1d", 440, 444)
    caption(p, T("The benchmark: {tasks} swegemma repair tasks from four GitHub repos, plus a {traps}-trap suite"), 10, 10, 420)
    bar_chart(p, 16, 74, 410, 170, [
        ("fastapi", V("repo_fastapi"), DISPLAY["repo_fastapi"], P["robot"]),
        ("rich", V("repo_rich"), DISPLAY["repo_rich"], P["robot"]),
        ("requests", V("repo_requests"), DISPLAY["repo_requests"], P["robot"]),
        ("httpx", V("repo_httpx"), DISPLAY["repo_httpx"], P["robot"]),
    ], vmax=V("repo_fastapi"), horizontal=True, label="repos", size=12)
    st = put(p, "scientist", 380, 432, .9, expr="neutral", pose="point_left")
    bubble(p, T("I traced {turns} turns of live telemetry. On Trap-25, each of the {traps} bugs is seeded with a plausible wrong first guess."),
           12, 262, 270, tail=st)
    pg.panel(L, 648, p)

    p = Panel("1e", 298, 444, bg="#f3eee2")
    caption(p, "Minute 15 of a repair session...", 10, 10, 278)
    sfx(p, "FAILED", 70, 78, 22)
    sfx(p, "FAILED", 220, 96, 18, rotate=8)
    sfx(p, "FAILED", 120, 128, 16, rotate=-3)
    mt = put(p, "monster", 215, 430, .8, expr="grin", label_name="monster")
    rt = put(p, "robot", 75, 430, .85, expr="stuck", pose="slump")
    bubble(p, "Same edit... again?", 10, 150, 150, tail=rt, kind="thought", size=12)
    bubble(p, "I grow with every failed test!", 168, 160, 120, tail=mt, kind="shout", size=12)
    pg.panel(474, 648, p)
    return pg


# =================================================================================================
# Page 2 - the failure
# =================================================================================================
def page2():
    pg = Page(2, "The Loop Monster", "Failed tracebacks crowd out the issue", "PDF p.2 §3.1; p.3 §3.3, Table 2")
    p = Panel("2a", FULL, 300)
    caption(p, "Proposition 1, softmax dilution: the context splits into A (the issue contract plus a 1-hop code slice) and B (the growing pile of failed tracebacks and rejected diffs).",
            10, 10, 730)
    blackboard(p, 230, 64, 508, 160, [
        ("Attn = (Z_A·e^L_A + Z_B·e^L_B) / (e^L_A + e^L_B)", 14, "mono", "#fff"),
        ("As |B| swells, e^L_B dominates the denominator.", 13, "bold", "#ffd27a"),
        ("Attention on Z_A drops below the Ω(r / log N) threshold that multi-hop reachability needs.", 13, "regular", "#e6ffe9"),
    ], title="Bounded-capacity transformer (Lemma 39 of Sanford et al.)", label="prop1")
    st = put(p, "scientist", 70, 290, .85, pose="point")
    bubble(p, "The issue text is still there. The model just stops looking at it.", 12, 88, 200, tail=st)
    caption(p, "Every new traceback adds weight to B; nothing new reaches A.", 230, 236, 508, size=11, style="regular", fill="#ffffff")
    pg.panel(L, 62, p)

    p = Panel("2b", HALF, 360)
    caption(p, "The compaction cliff", 10, 10, 160)
    cliff, mx = V("compaction_cliff"), V("max_model_len")
    gx, gy, gw = 20, 60, 330
    xc = gx + gw * cliff / mx
    p.add(f'<rect x="{gx}" y="{gy}" width="{gw}" height="26" fill="#e9edf5" stroke="{E.INK}" stroke-width="2"/>'
          f'<rect x="{gx}" y="{gy}" width="{xc - gx:.1f}" height="26" fill="#a9c1f0"/>'
          f'<line x1="{xc:.1f}" y1="{gy - 8}" x2="{xc:.1f}" y2="{gy + 34}" stroke="{P["bad"]}" stroke-width="3"/>')
    p.boxes.append(("chart", "gauge", (gx, gy - 8, gx + gw, gy + 34)))
    p.add(E.text_block([T("compaction at {compaction_cliff}")], xc, gy + 36, 11, "black", P["bad"], "middle"))
    p.add(E.text_block([T("{max_model_len}")], gx + gw, gy + 36, 11, "bold", E.INK, "end"))
    p.add(E.text_block(["0"], gx, gy + 36, 11, "bold", E.INK, "start"))  # axis origin, not a paper number
    rt = put(p, "robot", 90, 350, .8, expr="worried", pose="shrug")
    mt = put(p, "monster", 265, 350, .72, expr="grin", label_name="monster")
    bubble(p, "Where was that line number?", 12, 140, 140, tail=rt, size=12)
    bubble(p, "Summarized it away!", 200, 140, 156, tail=mt, kind="shout", size=12)
    pg.panel(L, 374, p)

    p = Panel("2c", HALF, 360)
    caption(p, T("Same checkpoint, two protocols: the Localization-Trajectory Tax"), 10, 10, 349)
    bar_chart(p, 24, 64, 200, 200, [
        ("Stage-1: file given", V("t1_calib_rate"), DISPLAY["t1_calib_rate"], P["good"]),
        ("End-to-end: find it (M2)", V("t2_M2_rate"), DISPLAY["t2_M2_rate"], P["bad"]),
    ], vmax=45, label="tax", size=12)
    sg = put(p, "scientist", 295, 350, .8, expr="worried", pose="point_left")
    bubble(p, T("A {tax_pts} tax: {tax_tasks} solvable tasks lost to dilution and schema bloat."), 220, 70, 140, tail=sg, size=11.5)
    caption(p, T("Calibrated row of Table 1 vs row M2 of Table 2: {t1_calib_solved} vs {t2_M2_solved}."), 10, 300, 210, size=10.5, style="regular", fill="#fff")
    pg.panel(R_, 374, p)

    p = Panel("2d", FULL, 330, bg="#f6f1ff")
    caption(p, "Why the loop starts on Turn 1: schema noise", 10, 10, 330)
    box(p, 24, 60, 300, 120, "agent.yaml lists unindexed graph tools: get_code_neighbors, search_similar_code, get_code_subgraph", 12, "#fff1f0", "regular", label="tools")
    arrow(p, 330, 120, 400, 120, P["bad"])
    box(p, 406, 60, 320, 120, T("build_agent_prompt injects a verbose schema block, and {turns_1_4} go to low-recall lookups"), 12, "#fff1f0", "regular", label="prompt")
    rt = put(p, "robot", 120, 320, .82, expr="dizzy", pose="shrug")
    gt = put(p, "scientist", 560, 320, .82, expr="worried", pose="point_left")
    bubble(p, T("Recall@3 = {recall_before}."), 190, 200, 110, tail=rt)
    bubble(p, T("Compaction fires on {t2_M0_comp} of episodes in the default template."), 330, 196, 190, tail=gt)
    pg.panel(L, 746, p)
    return pg


# =================================================================================================
# Page 3 - Law 1, calibrated thinking
# =================================================================================================
def page3():
    pg = Page(3, "Law 1: Sergeant vs Explorer", "Calibrated thinking, file slice given (Stage-1)", "PDF p.2 §3.1, §3.2, Table 1; p.4 §4")
    p = Panel("3a", FULL, 300)
    caption(p, "INT4 weight rounding adds a small error ε to every logit. Low temperature magnifies it over long thought chains.", 10, 10, 730)
    sg = put(p, "sergeant", 80, 290, .9, expr="stern", pose="point", label="τ=0.2")
    ex = put(p, "explorer", 670, 290, .9, expr="happy", pose="wave", label="T=1.0")
    blackboard(p, 200, 60, 350, 130, [
        ("p(v) ∝ exp( (z_v + ε_v) / τ )", 16, "mono", "#fff"),
        (T("τ = {greedy_tau}: the rounding bias is multiplied, and the trace locks in."), 12.5, "bold", "#ffb3a8"),
        (T("τ = {calib_T}, top-p {calib_top_p}, top-k {calib_top_k}: the bias is averaged out."), 12.5, "bold", "#b8ffd0"),
    ], label="temp")
    bubble(p, "Lowest temperature! Always pick the top token!", 12, 52, 170, tail=sg, kind="shout", size=12)
    bubble(p, T("Thinking budget {budget_full}, and keep the thoughts in context."), 570, 52, 170, tail=ex, size=12)
    pg.panel(L, 62, p)

    p = Panel("3b", HALF, 340)
    caption(p, T("Table 1: solved out of {tasks} with the file slice given"), 10, 10, 349)
    bar_chart(p, 16, 52, 337, 230, [
        (f"No thinking, {DISPLAY['t1_base_tempk']}", V("t1_base_rate"), DISPLAY["t1_base_rate"], P["sergeant"]),
        (f"Hidden thoughts, {DISPLAY['t1_hidden_tempk']}", V("t1_hidden_rate"), DISPLAY["t1_hidden_rate"], P["muted"]),
        (f"Calibrated, {DISPLAY['t1_calib_tempk']}", V("t1_calib_rate"), DISPLAY["t1_calib_rate"], P["explorer"]),
    ], vmax=45, label="t1", size=12)
    caption(p, T("{t1_gain_pts}, McNemar paired p = {t1_mcnemar}"), 10, 300, 349, size=12, fill="#e7f7ee")
    pg.panel(L, 374, p)

    rows = [("t1_base", "1. Non-Thinking Low-Temp Baseline"), ("t1_hidden", "2. Low-Temp Thinking (Hidden Thoughts)"),
            ("t1_calib", "3. Calibrated Thinking Mode (My Method)")]
    tr = "".join(
        f'<tr class="{"win" if k == "t1_calib" else ""}"><td>{E.esc(lab)}</td><td>{E.esc(DISPLAY[k + "_think"])}</td>'
        f'<td>{E.esc(DISPLAY[k + "_tempk"])}</td><td>{E.esc(DISPLAY[k + "_solved"])}</td>'
        f'<td>{E.esc(DISPLAY[k + "_rate"])} {E.esc(DISPLAY[k + "_ci"])}</td></tr>' for k, lab in rows)
    for k, _ in rows:
        USED.update({k + s for s in ("_think", "_tempk", "_solved", "_rate", "_ci")})
    inner = (f'<div class="cap">Table 1 (Stage-1 Isolated Patch Synthesis), verbatim. 31B Dense W4A16, all {DISPLAY["tasks"]} tasks.</div>'
             '<table><thead><tr><th>Configuration</th><th>Think budget / thoughts</th><th>Temp / top-k</th><th>Solved</th><th>Rate (95% Wilson CI)</th></tr></thead>'
             f'<tbody>{tr}</tbody></table>')
    USED.add("tasks")
    pg.html_panel(R_, 374, HALF, 340, inner, "t1table")

    p = Panel("3c", FULL, 360, bg="#fbf6ea")
    caption(p, "Proposition 2: match the thinking budget to how far the answer is in the code graph", 10, 10, 600)
    xs = [40, 290, 540]
    data = [("D1: single-hop read", T("{budget_d1} tokens, cut {budget_cut_pct} from {budget_full}"), "#dfe8ff"),
            ("LDP: co-change edit", T("{budget_ldp_lo} to {budget_full} tokens"), "#fff1c9"),
            ("LDW: after a reset", T("{budget_ldw}-token burst"), "#ffe0dc")]
    for x0, (h1, h2, col) in zip(xs, data):
        box(p, x0, 56, 200, 46, h1, 13, col, label=h1)
        box(p, x0, 108, 200, 40, h2, 11.5, "#ffffff", "regular", label=h1 + "b")
    arrow(p, 242, 79, 288, 79)
    arrow(p, 492, 79, 538, 79)
    ex = put(p, "explorer", 120, 350, .9, expr="happy", pose="point", label="T=1.0")
    sg = put(p, "sergeant", 640, 350, .9, expr="surprised", pose="shrug", label="τ=0.2")
    bubble(p, "Short trips get a small pack. Deep searches get the big one.", 185, 190, 220, tail=ex)
    bubble(p, "Different budgets for different reads?", 440, 196, 150, tail=sg)
    pg.panel(L, 726, p)
    return pg


# =================================================================================================
# Page 4 - Laws 2 and 3, Lean-6 and co-change
# =================================================================================================
def page4():
    pg = Page(4, "Laws 2 & 3: Travel Light, Check the Twins", "End-to-end discovery, modules M0 to M6", "PDF p.3 §3.3, Table 2, Figure 2 caption; p.1 Abstract")
    p = Panel("4a", HALF, 350)
    caption(p, "M1: the Lean-6 toolbox", 10, 10, 200)
    tools = ["run_command", "read_file", "edit_file", "write_file", "get_status", "submit_patch"]
    for i, t in enumerate(tools):
        p.add(f'<rect x="{18 + (i % 2) * 168}" y="{52 + (i // 2) * 34}" width="160" height="26" rx="5" fill="#e6eeff" stroke="{E.INK}" stroke-width="1.5"/>'
              + E.text_block([t], 98 + (i % 2) * 168, 56 + (i // 2) * 34, 12, "mono", E.INK, "middle"))
    p.boxes.append(("chart", "tools", (18, 52, 346, 156)))
    rt = put(p, "robot", 80, 340, .78, expr="happy", pose="cheer")
    bubble(p, T("M3: a Turn-1 contract parser over six relation types, then {window_lines} reads. Recall@3 = {recall_after}."), 140, 176, 215, tail=rt, size=11.5)
    pg.panel(L, 62, p)

    p = Panel("4b", HALF, 350)
    caption(p, "M4 and M5: deadline and twins", 10, 10, 250)
    box(p, 16, 50, 160, 54, "M4: first source edit by Call-12", 12, "#fff1c9", label="m4")
    for i, (a, b) in enumerate([("Client", "AsyncClient"), ("@overload", "__all__"), ("source", "docs_src/")]):
        y0 = 118 + i * 34
        box(p, 16, y0, 74, 26, a, 10.5, "#e7f7ee", "regular", label=a)
        box(p, 102, y0, 74, 26, b, 10.5, "#e7f7ee", "regular", label=b)
    ex = put(p, "explorer", 285, 340, .8, expr="happy", pose="point_left", label="T=1.0")
    bubble(p, "Fix one twin, check the other.", 190, 52, 168, tail=ex, size=12)
    pg.panel(R_, 62, p)

    p = Panel("4c", FULL, 330)
    caption(p, T("Table 2, cumulative: each module is added on top of the last ({tasks} tasks, {call_cap} calls)"), 10, 10, 560)
    mods = ["M0", "M1", "M2", "M3", "M4", "M5", "M6"]
    bar_chart(p, 16, 46, 360, 274, [(m, V(f"t2_{m}_rate"), DISPLAY[f"t2_{m}_rate"], P["good"] if m == "M6" else P["robot"]) for m in mods],
              vmax=30, title="Solved", label="solved", size=11)
    bar_chart(p, 384, 46, 356, 274, [(m, V(f"t2_{m}_comp"), DISPLAY[f"t2_{m}_comp"], P["bad"] if m == "M0" else P["warn"]) for m in mods],
              vmax=80, title=T("Episodes compacted (over {compaction_cliff})"), label="comp", size=11)
    pg.panel(L, 424, p)

    hdr = "<tr><th>Module</th><th>Calls</th><th>Peak KV</th><th>Compacted</th><th>Solved</th><th>Held-out</th></tr>"
    trs = []
    for m in mods:
        trs.append(f'<tr class="{"win" if m == "M6" else ""}"><td>{m}: {E.esc(DISPLAY[f"t2_{m}_label"])}</td>'
                   + "".join(f"<td>{E.esc(DISPLAY[f't2_{m}_{c}'])}</td>" for c in ("calls", "kv", "comp", "solved", "held")) + "</tr>")
        USED.update({f"t2_{m}_{c}" for c in ("label", "calls", "kv", "comp", "solved", "held")})
    inner = (f'<div class="cap">Table 2 (End-to-End Autonomous Multi-Turn Discovery). Row labels shortened; values verbatim.</div>'
             f'<table class="t2"><thead>{hdr}</thead><tbody>{"".join(trs)}</tbody></table>')
    pg.html_panel(L, 766, 470, 326, inner, "t2table")

    p = Panel("4d", 268, 326, bg="#eef8f1")
    sc = put(p, "scientist", 70, 316, .8, expr="happy", pose="cheer")
    rt = put(p, "robot", 195, 316, .8, expr="proud", pose="wave")
    bubble(p, T("{t2_M0_solved} to {t2_M6_solved}: {t2_ratio} as many solves (McNemar p = {t2_mcnemar})."), 10, 10, 160, tail=sc, size=12)
    bubble(p, T("Compaction {t2_M0_comp} to {t2_M6_comp}, that is {compaction_cut_quoted}. Active context peaks at {peak_active_k}."), 110, 116, 148, tail=rt, size=12)
    pg.panel(504, 766, p)
    return pg


# =================================================================================================
# Page 5 - Law 4, the gatekeeper and G-CCR
# =================================================================================================
def page5():
    pg = Page(5, "Law 4: The Gatekeeper", "LoopBreakerEngine and Counterfactual Context Reset (G-CCR)", "PDF p.2 §3.1; p.3 §3.4")
    p = Panel("5a", FULL, 380)
    caption(p, "Every turn, three cheap loop detectors watch the trajectory since the last reset. Any one firing triggers a reset.", 10, 10, 730)
    gk = put(p, "gatekeeper", 80, 370, 1.0, expr="stern", lamps=(True, False, True), label_name="gatekeeper")
    cx0 = 270
    det = [T("Same error signature, count {det_err}?"), T("Diff similarity (LCS) {det_lcs} on the same symbol?"),
           T("Action entropy {det_entropy}, {det_window}?")]
    for i, t in enumerate(det):
        diamond(p, cx0 + i * 170, 130, 158, 120, t, 10.5, label=f"d{i}")
    for i in range(3):
        arrow(p, cx0 + i * 170, 192, cx0 + i * 170, 238, P["bad"], text="yes")
    box(p, 200, 242, 480, 46, "ANY detector fires: run G-CCR, a graph Backtrack step", 13, "#ffe0dc", label="any")
    bubble(p, "Three lamps. One is enough to stop you.", 160, 300, 220, tail=gk)
    pg.panel(L, 62, p)

    p = Panel("5b", FULL, 330, bg="#f6f1ff")
    caption(p, "G-CCR in three moves", 10, 10, 200)
    steps = [("1. Prune", "Drop the polluted turns B: old tracebacks and rejected diffs.", "#ffe0dc"),
             ("2. Ledger", T("Insert a {ledger_tokens} <NEGATIVE_CONSTRAINT_LEDGER> naming the invariant that failed."), "#fff1c9"),
             ("3. Burst", T("A {budget_ldw}-token thinking burst ({burst_tau}) inspects the 1-hop neighbors."), "#e7f7ee")]
    for i, (h, t, col) in enumerate(steps):
        x0 = 20 + i * 245
        box(p, x0, 48, 220, 32, h, 14, col, label=h)
        box(p, x0, 84, 220, 74, t, 11.5, "#fff", "regular", label=h + "b")
        if i < 2:
            arrow(p, x0 + 222, 64, x0 + 243, 64)
    mt = put(p, "monster", 560, 320, .7, expr="shrink", label_name="monster", size_k=.7)
    rt = put(p, "robot", 360, 320, .82, expr="happy", pose="point")
    gk = put(p, "gatekeeper", 110, 320, .82, expr="happy", lamps=(False, False, False), label_name="gatekeeper")
    bubble(p, "The ledger remembers what failed, so I skip it.", 405, 176, 190, tail=rt, size=11.5)
    bubble(p, "No...", 600, 214, 60, tail=mt, kind="shout", size=12)
    bubble(p, "Lamps dark. Carry on.", 150, 190, 140, tail=gk, size=11.5)
    pg.panel(L, 454, p)

    p = Panel("5c", FULL, 296)
    caption(p, T("Back to Proposition 1: {serializations} controlled serializations, keeping a {window_lines} 1-hop window"), 10, 10, 640)
    bar_chart(p, 30, 50, 300, 236, [
        ("before G-CCR", V("dilution_before"), DISPLAY["dilution_before"], P["bad"]),
        ("after G-CCR", V("dilution_after"), DISPLAY["dilution_after"], P["good"]),
    ], vmax=.8, title="Softmax dilution", label="dil", size=12)
    sc = put(p, "scientist", 640, 286, .9, expr="happy", pose="point_left")
    bubble(p, T("Dilution {dilution_before} to {dilution_after}: {bits_gain} of effective attention back on the issue."), 360, 60, 230, tail=sc)
    pg.panel(L, 796, p)
    return pg


# =================================================================================================
# Page 6 - results
# =================================================================================================
def page6():
    pg = Page(6, "The Scoreboard", "Trap-25 loop recovery and what is left", "PDF p.4 Table 3, §4, §5; p.1 Abstract")
    cfgs = ["baseline_static", "naive_subagent", "ccr_only", "ccr_adaptive"]
    cols = {"baseline_static": P["sergeant"], "naive_subagent": P["muted"], "ccr_only": P["warn"], "ccr_adaptive": P["good"]}
    p = Panel("6a", HALF, 330)
    caption(p, T("Escape rate on Trap-25 ({episodes} AST-verified episodes)"), 10, 10, 349)
    bar_chart(p, 12, 48, 345, 190, [(c, V(f"t3_{c}_esc"), DISPLAY[f"t3_{c}_esc"], cols[c]) for c in cfgs], vmax=100,
              horizontal=True, label="esc", size=11.5)
    caption(p, T("{t3_ccr_adaptive_solved} vs {t3_baseline_static_solved}: {trap_gain_pts_quoted}, Fisher's exact p = {fisher_p}"), 10, 256, 349, size=12, fill="#e7f7ee")
    pg.panel(L, 62, p)

    p = Panel("6b", HALF, 330)
    caption(p, "Active post-reset KV tokens", 10, 10, 260)
    bar_chart(p, 12, 48, 345, 190, [(c, V(f"t3_{c}_kv"), DISPLAY[f"t3_{c}_kv"], cols[c]) for c in cfgs], vmax=V("t3_naive_subagent_kv") * 1.05,
              horizontal=True, label="kv", size=11.5)
    caption(p, T("{t3_ccr_adaptive_kvpct} against the unpruned baseline, Wilcoxon {wilcoxon}"), 10, 256, 349, size=12, fill="#e7f7ee")
    pg.panel(R_, 62, p)

    hdr = "<tr><th>Configuration</th><th>Solved</th><th>Escape (95% CI)</th><th>Avg turns</th><th>Avg think tok</th><th>Post-reset KV</th><th>Peak KV</th></tr>"
    trs = []
    for c in cfgs:
        trs.append(f'<tr class="{"win" if c == "ccr_adaptive" else ""}"><td>{c} ({E.esc(DISPLAY[f"t3_{c}_tag"])})</td>'
                   f'<td>{DISPLAY[f"t3_{c}_solved"]}</td><td>{DISPLAY[f"t3_{c}_esc"]} {DISPLAY[f"t3_{c}_ci"]}</td>'
                   f'<td>{DISPLAY[f"t3_{c}_turns"]}</td><td>{DISPLAY[f"t3_{c}_think"]}</td>'
                   f'<td>{DISPLAY[f"t3_{c}_kv"]} ({DISPLAY[f"t3_{c}_kvpct"]})</td><td>{DISPLAY[f"t3_{c}_peak"]}</td></tr>')
        USED.update({f"t3_{c}_{s}" for s in ("tag", "solved", "esc", "ci", "turns", "think", "kv", "kvpct", "peak")})
    inner = (f'<div class="cap">Table 3, verbatim: controlled loop-recovery evaluation on Trap-25.</div>'
             f'<table class="t3"><thead>{hdr}</thead><tbody>{"".join(trs)}</tbody></table>')
    pg.html_panel(L, 404, FULL, 196, inner, "t3table")

    p = Panel("6c", HALF, 480, bg="#fbf6ea")
    caption(p, "The one that got away: requests-trap-10", 10, 10, 349)
    mt = put(p, "monster", 270, 470, .7, expr="grin", label_name="monster", size_k=.8)
    rt = put(p, "robot", 90, 470, .85, expr="worried", pose="shrug")
    caption(p, T("The sole Trap-25 timeout: a NO_PROXY bypass bundles {fail_invariants} proxy invariants behind one bare AssertionError."), 10, 46, 349, size=11.5, style="regular", fill="#fff")
    bubble(p, T("That is {fail_invariants} checks in one assert. Which one failed?"), 128, 290, 112, tail=rt, size=11.5)
    blackboard(p, 12, 118, 345, 110, [
        ("pytest -vv --tb=short", 14, "mono", "#fff"),
        (T("on {turn_1_fix} splits the compound assertion into its parts."), 12.5, "bold", "#b8ffd0"),
    ], title="The fix the paper proposes", label="fix")
    bubble(p, "Still here.", 252, 340, 90, tail=mt, kind="shout", size=12)
    pg.panel(L, 612, p)

    p = Panel("6d", HALF, 480, bg="#eef8f1")
    caption(p, "Epilogue", 10, 10, 120)
    sc = put(p, "scientist", 70, 470, .82, expr="happy", pose="stand")
    rt = put(p, "robot", 190, 470, .82, expr="happy", pose="cheer")
    gk = put(p, "gatekeeper", 300, 470, .82, expr="happy", lamps=(False, False, False), label_name="gatekeeper")
    bubble(p, T("Scientific traps sci-trap-21 to sci-trap-25: {sci_ccr} recovered with G-CCR, {sci_base} for the baseline."), 10, 46, 345, size=12)
    bubble(p, T("Serving: {lora_adapters} QLoRA adapters hot-swapped on one Gemma 4 base, {lora_vram}, {lora_swap_ms} swap, GPU memory cut {lora_mem_cut}, pass rate {lora_pass_before} to {lora_pass_after}."),
           10, 112, 345, size=12)
    bubble(p, T("Check it yourself: {tests_passed} in {tests_time}, under {verify_budget_s} offline."), 10, 206, 220, tail=sc, size=12)
    bubble(p, "Clean context, clear head!", 236, 236, 120, tail=rt, size=12)
    pg.panel(R_, 612, p)
    return pg


CSS = """
@page { size: A4; margin: 0; }
* { box-sizing: border-box; }
html, body { margin: 0; padding: 0; background: #fff; }
body { font-family: Lato, sans-serif; color: #1f2430; -webkit-print-color-adjust: exact; print-color-adjust: exact; }
.page { position: relative; width: 210mm; height: 297mm; overflow: hidden; page-break-after: always; break-after: page; background: #fffaf0; }
.page:last-child { page-break-after: auto; break-after: auto; }
header { position: absolute; left: 22px; top: 14px; width: 750px; height: 40px; display: flex; align-items: baseline; gap: 12px; border-bottom: 3px solid #1f2430; }
header h1 { font-weight: 900; font-size: 24px; margin: 0; }
header .sub { font-size: 12.5px; color: #4a5263; }
header .pn { font-weight: 900; font-size: 13px; background: #1f2430; color: #ffe58a; padding: 2px 8px; border-radius: 4px; }
footer { position: absolute; left: 22px; bottom: 8px; width: 750px; font-size: 9.5px; color: #5a6274; }
.panel { position: absolute; overflow: hidden; }
.panel svg { display: block; }
.htmlp { border: 3px solid #1f2430; background: #fff; padding: 10px; }
.htmlp .cap { font-weight: 900; font-size: 12px; background: #fff1b8; border: 2px solid #1f2430; padding: 4px 7px; margin-bottom: 8px; }
.htmlp table { border-collapse: collapse; width: 100%; font-size: 11px; }
.htmlp th { background: #1f2430; color: #fff; text-align: left; padding: 4px 5px; font-size: 10.5px; }
.htmlp td { border-bottom: 1px solid #c9cfdb; padding: 5px 5px; vertical-align: top; }
.htmlp tr.win td { background: #e7f7ee; font-weight: 700; }
.htmlp table.t2 td, .htmlp table.t2 th { padding: 6px 5px; }
.htmlp table.t3 { font-size: 11px; }
"""


AUDIT_ALLOWED = ALLOWED + [r"\b[1-3]\. (Prune|Ledger|Burst|Non-Thinking|Low-Temp|Calibrated)", r"\b[1-6]/6\b",
                           r"Mirbahar \(2026\)", r"15-MINUTE", r"Minute 15", r"95% (Wilson )?CI", r"Lemma 39", r"10⁻⁶"]


def audit_rendered_text(doc: str):
    """Every numeric token visible in the finished HTML must be part of a display string in story_numbers.json."""
    import html as H
    allowed_tokens = set()
    for k in USED:
        allowed_tokens.update(re.findall(r"\d+(?:[.,]\d+)*", str(DISPLAY[k])))
    body = re.sub(r"<style>.*?</style>|<title>.*?</title>", "", doc, flags=re.S)
    texts = [H.unescape(t) for t in re.findall(r">([^<>]+)<", body)]
    for t in texts:
        s = t
        for pat in AUDIT_ALLOWED:
            s = re.sub(pat, "", s)
        for tok in re.findall(r"\d+(?:[.,]\d+)*", s):
            if tok not in allowed_tokens:
                LINT.append(f"rendered number {tok!r} not in story_numbers.json displays: {t!r}")


def main():
    pages = [page1(), page2(), page3(), page4(), page5(), page6()]
    doc = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Loop Breaker Comic</title>'
           f'<style>{CSS}</style></head><body>{"".join(p.html() for p in pages)}</body></html>')
    (HERE / "Story.html").write_text(doc)
    unknown = [k for k in USED if k not in NUM]
    audit_rendered_text(doc)
    print(f"Story.html: {len(pages)} pages, {len(USED)} numbers used from story_numbers.json")
    for msg in LINT:
        print("LINT", msg)
    for msg in PROBLEMS:
        print("LAYOUT", msg)
    if unknown:
        print("UNKNOWN KEYS", unknown)
    (HERE / "story_numbers_used.json").write_text(json.dumps(
        {k: {"display": NUM[k]["display"], "source": NUM[k]["source"]} for k in sorted(USED)}, indent=1, ensure_ascii=False))
    return 1 if (LINT or PROBLEMS or unknown) else 0


if __name__ == "__main__":
    sys.exit(main())
