"""Assemble Radar.html from data/*.json, matrix.csv and references.csv. All counts come from data/analysis.json."""
import json, csv, html, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
A = json.loads((ROOT / "data/analysis.json").read_text()); cod = json.loads((ROOT / "data/coding.json").read_text())
bp = json.loads((ROOT / "data/blueprints.json").read_text()); refs = list(csv.DictReader(open(ROOT / "references.csv")))
pa = json.loads((ROOT / "data/prior_art.json").read_text())
ql = json.loads((ROOT / "raw/query_log.json").read_text()) + json.loads((ROOT / "raw/query_log3.json").read_text())
R = {r["openalex"]: r for r in refs}
pa_titles = {h["openalex"]: (h["title"], h["year"], h["doi"]) for b in pa.values() for q in b for h in q["hits"]}
S = cod["short"]; D = list(cod["dimensions"]); e = html.escape
def cite(pid):
    if pid in R: return f'<span class="cite">{e(R[pid]["short"])} [{pid}]</span>'
    t, y, d = pa_titles[pid]; return f'<span class="cite">{e(t[:60])}{"…" if len(t) > 60 else ""} ({y}) [{pid}]</span>'
n_oa = sum(1 for q in ql if q["src"].startswith("openalex")); n_ax = sum(1 for q in ql if q["src"] == "arxiv"); n_ax_ok = sum(1 for q in ql if q["src"] == "arxiv" and q["n"] > 0)
n_pa = sum(len(b) for b in pa.values())
gap_rows = []
for g in A["gaps"]:
    dims = " × ".join(f"{d} {S[d]}" for d in g["dims"])
    if g["kind"] == "single_repo":
        what = "Studies with this dimension that also evaluate on a repository-repair task"
        exp = "—"; pool = A["pool_counts_swe"][g["dims"][0]]
    else:
        what = "Retained papers filling both dimensions"; exp = g["expected_indep"]; pool = A["pool_pairs_swe"]["x".join(g["dims"])]
    ev = ", ".join(cite(p) for p in g["papers"]) or "none in retained set"
    marg = "; ".join(f'{d}: ' + ", ".join(p for p in A["covers"][d]) for d in g["dims"])
    gap_rows.append(f'<tr><td><b>{g["id"]}</b></td><td>{e(dims)}<div class="sub">{what}</div></td><td class="num">{g["observed"]}</td><td class="num">{exp}</td><td class="num">{pool}</td><td>{ev}<div class="sub ids">Marginals — {e(marg)}</div></td></tr>')
bp_rows = []
for b in bp:
    cls = "dropped" if b["status"] == "dropped" else ""
    qs = "; ".join(f'“{e(q)}”' for q in b["prior_art_queries"])
    bp_rows.append(f'<tr class="{cls}"><td><b>{b["id"]}</b><div class="tag {b["status"]}">{b["status"]}</div></td><td><b>{e(b["title"])}</b><div>{e(b["design"])}</div><div class="sub">Targets {", ".join(b["gaps"])}</div></td>'
                   f'<td><div class="sub">Searched (OpenAlex, from 2023): {qs}</div><div>Closest: {", ".join(cite(c) for c in b["closest"])}</div><div>{e(b["verdict"])}</div></td></tr>')
dim_rows = "".join(f'<tr><td><b>{d}</b></td><td>{e(S[d])}</td><td>{e(cod["dimensions"][d])}</td><td class="num">{A["counts"][d]}</td><td class="num">{A["repo_counts"][d]}</td><td class="num">{A["pool_counts_swe"][d]}</td></tr>' for d in D)
ref_rows = "".join(f'<tr><td>{e(r["short"])}</td><td>{e(r["title"])}<div class="sub">{e(r["first_author"])} et al., {r["year"]} · {e(r["venue"])}{" · <b>PREPRINT</b>" if r["status"]=="preprint" else ""}</div></td>'
                   f'<td class="ids">{r["openalex"]}<br>{("arXiv:" + r["arxiv"]) if r["arxiv"] else ""}<br>{e(r["doi"])}</td><td class="sub">{e(r["venue_source"])}</td></tr>' for r in refs)
pa_ids = sorted({c for b in bp for c in b["closest"] if c not in R})
pa_rows = "".join(f'<tr><td class="ids">{c}</td><td>{e(pa_titles[c][0])} ({pa_titles[c][1]})</td><td class="ids">{e((pa_titles[c][2] or "").replace("https://doi.org/",""))}</td></tr>' for c in pa_ids)
c = A["counts"]; N = A["N"]
synth = f"""
<p><b>1. Context management became a trained policy.</b> Six of {N} retained papers manage the agent's context during a run (D1). The 2025–26 work moves the decision of when and what to compact into the policy itself: {cite("W7117557793")} trains a model that compacts at milestones and reports 57.6% on SWE-bench Verified; {cite("W7215726049")} trains when to compact and reports +9.2 points on SWE-bench Verified, holding at 256K and 16K windows. Pruning methods cut tokens with equal or better success: 23–54% fewer tokens ({cite("W7125680675")}), 39.9–59.7% fewer input tokens ({cite("W4415332588")}). {cite("W7154351780")} prunes the KV cache with code-property-graph priors, the only retained paper joining D1 to a code graph at the inference layer.</p>
<p><b>2. Loop and stall recovery is moving online.</b> Four papers intervene while the episode runs (D2). {cite("W7167425954")} reports misbehaviours, loops among them, in about 30% of production trajectories; {cite("W4416711632")} raises SWE-bench Verified resolution from 40.0% to 50.6% with a process reward model that course-corrects mid-run; {cite("W7172523833")} predicts failure from trajectory prefixes with a 0.6B monitor and restarts (66.6% → 71.8% for Qwen3.6-27B); {cite("W7131676563")} trains a 7B model to recognise stalled states and reaches 42.4% Pass@1. {cite("W4415935825")} gives the motivating observation: failed trajectories are longer and more variable, and 72–81% of trajectories locate the right file even when they fail.</p>
<p><b>3. Search and restart are the main alternatives to fixing a run in place.</b> D3 covers MCTS ({cite("W4404342086")}, 23% relative gain across five models), verifier-ranked rollouts ({cite("W4405957747")}), restart ({cite("W7172523833")}) and between-attempt recovery guidance ({cite("W7160926458")}).</p>
<p><b>4. Graph-guided retrieval is well developed for localization.</b> D4 is the second-most covered dimension ({c["D4"]} papers). {cite("W4415101712")} reaches 92.7% file-level localization with a fine-tuned 32B model; {cite("W7125926949")} reports 43.3% / 44.6% Top-1 function localization on SWE-bench Lite / Verified with a 32B model; {cite("W4416453608")} puts the graph into attention and reaches 43.00% on SWE-bench Lite with Qwen2.5-72B. {cite("W7223971351")} measures the gain for small models: structured tools add 17–21 points at 1.7–4B and 4–5 points at 32B, and agents chain graph expansions in only 12–14% of episodes.</p>
<p><b>5. Open-weight policies are common; quantized ones are rare.</b> D5 is the most covered dimension ({c["D5"]} papers, from SWE-Llama in {cite("W4387561453")} to SWE-agent-LM-32B at 40.2% in {cite("W4417525566")}). Reduced precision (D6) appears in {c["D6"]} papers, and only {A["repo_counts"]["D6"]} of them evaluate on a repository-repair task: an FP8 control in {cite("W7223971351")} and energy per completed task at 4 and 8 bits in {cite("W7223657872")}, which finds 4-bit can use up to 3.5× the energy per completed task. Off-agent evidence points the other way for single-turn code generation: 4-bit post-training quantization shows no significant loss there ({cite("W7171740466")}), while {cite("W7225790577")} finds quantized agents “overlook task requirements” and recovers most of the gap with teacher steering (within one point of BF16 at W4A16).</p>
<p><b>6. Budgets are rarely varied.</b> Only {c["D7"]} papers report results at two or more explicit resource budgets ({cite("W7215726049")}, {cite("W4404342086")}, {cite("W7223657872")}). Most report a single scaffold configuration, so the interaction between budget caps and the failure modes in themes 1–2 is mostly unmeasured.</p>"""
doc = f"""<!doctype html><html lang="en"><head><meta charset="utf-8"><title>Frontier Gap Radar</title>
<style>
@page {{ size: A4; margin: 14mm 13mm 14mm 13mm; }}
:root {{ --ink:#0b0b0b; --ink2:#52514e; --rule:#d9d8d3; --blue:#2a78d6; --bg:#fcfcfb; --soft:#f0efec; }}
body {{ font-family: "DejaVu Sans", Helvetica, Arial, sans-serif; font-size: 8.6pt; line-height: 1.38; color: var(--ink); background: #fff; margin: 0; }}
h1 {{ font-size: 17pt; margin: 0 0 2mm; letter-spacing: -0.2px; }} h2 {{ font-size: 11.5pt; margin: 5mm 0 2mm; border-bottom: 1.5px solid var(--blue); padding-bottom: 1mm; break-after: avoid; }}
.lede {{ color: var(--ink2); font-size: 9pt; }} .box {{ background: var(--soft); border-radius: 4px; padding: 2.5mm 3.5mm; margin: 2mm 0; }}
.kpis {{ display: flex; gap: 3mm; margin: 3mm 0; }} .kpi {{ flex: 1; border: 1px solid var(--rule); border-radius: 4px; padding: 2mm; }} .kpi b {{ font-size: 15pt; display: block; }} .kpi span {{ color: var(--ink2); font-size: 7.4pt; }}
table {{ border-collapse: collapse; width: 100%; margin: 2mm 0; font-size: 7.6pt; }} th {{ text-align: left; background: var(--soft); font-weight: 600; }}
th, td {{ border-bottom: 1px solid var(--rule); padding: 1.2mm 1.5mm; vertical-align: top; }} tr {{ break-inside: avoid; }}
td.num {{ text-align: right; font-variant-numeric: tabular-nums; }} .sub {{ color: var(--ink2); font-size: 7pt; }} .ids {{ white-space: normal; font-family: "DejaVu Sans Mono", monospace; font-size: 6.5pt; word-break: break-all; }}
.cite {{ white-space: nowrap; color: #184f95; }} figure {{ margin: 2mm 0; break-inside: avoid; }} figure img {{ width: 100%; }} figcaption {{ color: var(--ink2); font-size: 7.4pt; }}
tr.dropped td {{ color: var(--ink2); }} .tag {{ display: inline-block; font-size: 6.5pt; padding: 0.3mm 1.2mm; border-radius: 3px; margin-top: 1mm; }} .tag.kept {{ background:#cde2fb; }} .tag.revised {{ background:#fde6c4; }} .tag.dropped {{ background: var(--soft); }}
.pb {{ break-before: page; }} p {{ margin: 1.5mm 0; }}
</style></head><body>
<h1>Frontier Gap Radar &amp; Research Blueprint</h1>
<div class="lede">Context management, loop and failure recovery, and graph-guided retrieval for LLM coding agents on repository-repair benchmarks (SWE-bench family), including small and quantized models. Papers from 2023 onward; retrieved 2026-11-15.</div>
<div class="kpis"><div class="kpi"><b>{A["pool_total"]}</b><span>deduplicated records retrieved</span></div><div class="kpi"><b>{N}</b><span>papers retained in the matrix ({A["n_published"]} published, {A["n_preprint"]} preprints)</span></div>
<div class="kpi"><b>{A["quotes_verified"]}</b><span>filled cells, each backed by a quote verified verbatim against the abstract</span></div><div class="kpi"><b>{len(A["gaps"])}</b><span>blind spots G1–G{len(A["gaps"])}</span></div><div class="kpi"><b>{sum(b["status"]!="dropped" for b in bp)} / {len(bp)}</b><span>blueprints surviving the prior-art check</span></div></div>
<div class="box"><b>Method.</b> Six facets (context management, failure recovery, graph retrieval, benchmarks, small/quantized models, scaffolds) were queried in OpenAlex ({n_oa} queries, 25 results each) and arXiv ({n_ax} queries; {n_ax_ok} returned records, the rest hit HTTP 429 rate limits). Records were deduplicated by DOI and normalised title in a script. {N} papers were retained by hand for direct relevance to repository-repair agents; venues were upgraded through Crossref (research-audit MCP) and, for ICLR/ICML papers without Crossref records, through the conference pages. Each matrix cell is coded from the registry abstract only, and a script checks that every quoted evidence string appears verbatim in that abstract. Counts, co-coverage and the gap ranking are computed in <code>scripts/analyze.py</code>. As a cross-check, regex rules for each dimension were run over all {A["pool_swe"]} retrieved records that mention SWE-bench or issue resolution (“pool” columns).</div>
<h2>1. Thematic synthesis</h2>{synth}
<h2>2. Capability matrix</h2>
<table><tr><th>ID</th><th>Dimension</th><th>Coding rule</th><th>Papers</th><th>…with repo-repair eval</th><th>Pool (regex, of {A["pool_swe"]})</th></tr>{dim_rows}</table>
<figure><img style="width:80%;display:block;margin:0 auto" src="figures/fig1_capability_heatmap.png" alt="Heatmap of {N} papers by 7 capability dimensions, with a 7 by 7 co-coverage matrix marking blind spots G2 to G7"><figcaption>Figure 1. Left: retained papers × dimensions; a filled cell has a verified abstract quote (see matrix.csv). Right: number of papers filling both dimensions; G2–G7 mark the pair blind spots. G1 is a single-dimension gap restricted to repository-repair evaluations (Section 3). Two papers fill no dimension (Trajectory study, Agentless); they are kept as baselines.</figcaption></figure>
<h2 class="pb">3. Blind spots</h2>
<p>No dimension has ≤ 2 studies across all {N} papers (minimum: D7 with {c["D7"]}), so the single-dimension rule alone yields no gap. Two extensions were applied, both computed: (a) the same rule restricted to the {A["n_repo_repair"]} papers with a repository-repair evaluation, and (b) dimension pairs with ≤ 2 papers, ranked by shortfall against the count expected if the two dimensions were independent (expected = n<sub>a</sub>·n<sub>b</sub>/{N}; a ranking heuristic, not a statistical test). The pool column re-counts each gap over all {A["pool_swe"]} SWE-related retrieved records with regex rules; it is coarse (keyword matches, no reading) and shows where the retained set understates prior work.</p>
<table><colgroup><col style="width:4%"><col style="width:22%"><col style="width:8%"><col style="width:9%"><col style="width:7%"><col style="width:50%"></colgroup><tr><th></th><th>Gap</th><th>Observed</th><th>Expected if independent</th><th>Pool (regex)</th><th>Evidence (paper IDs)</th></tr>{"".join(gap_rows)}</table>
<p><b>Reading the gaps.</b> G1 and G7 hold in both the retained set and the pool: across {A["pool_swe"]} SWE-related records, the regex finds reduced precision in {A["pool_counts_swe"]["D6"]} and its overlap with context management in {A["pool_pairs_swe"]["D1xD6"]}. G3–G6 are empty in the retained set but have 1–3 pool hits each. The prior-art check (Section 4) read those hits: LingmaAgent [W4413267850] already pairs a repository knowledge graph with MCTS (G4), and CAPYBALA [W7225137459, preprint] couples loop detection with context pruning (G5, G6). Those gaps are therefore thin, not empty. G2 (context management × open-weight policy) is understated by the abstract-only coding, since several context-management papers train open models without naming them in the abstract.</p>
<h2 class="pb">4. Novelty-checked blueprints</h2>
<p>Six designs were drafted against G1–G7, and {n_pa} OpenAlex queries (three per blueprint) were run for prior art. Closest hits were read at abstract level.</p>
<table><colgroup><col style="width:7%"><col style="width:40%"><col style="width:53%"></colgroup><tr><th></th><th>Design</th><th>Prior-art search and verdict</th></tr>{"".join(bp_rows)}</table>
<figure><img src="figures/fig2_blueprint_impact_compute.png" alt="Scatter of blueprints by judged compute and judged impact" style="width:78%"><figcaption>Figure 2. Impact and compute placements are the surveyor's judgements, not measurements.</figcaption></figure>
<h2>5. Limits of this radar</h2>
<p>Coding uses abstracts only; a capability present in a paper's body but absent from its abstract is coded empty, which biases counts downward (most visibly for D5 and D7). The retained set was chosen by one reader; the pool cross-check is the guard against that choice. arXiv returned records for {n_ax_ok} of {n_ax} queries because of rate limiting, so arXiv-only preprints are under-sampled; OpenAlex returned arXiv-hosted records in every facet, but its arXiv coverage was not measured. Many retained and prior-art records are 2026 preprints without peer review; they are tagged. Reported metrics are quoted from abstracts and were not re-derived.</p>
<h2 class="pb">References (retained papers)</h2>
<table><tr><th>Short</th><th>Title · venue</th><th>IDs</th><th>Venue source</th></tr>{ref_rows}</table>
<h2>Prior-art records cited in Section 4</h2>
<table><colgroup><col style="width:14%"><col style="width:64%"><col style="width:22%"></colgroup><tr><th>OpenAlex</th><th>Title</th><th>DOI</th></tr>{pa_rows}</table>
</body></html>"""
(ROOT / "Radar.html").write_text(doc); print("written", len(doc))
