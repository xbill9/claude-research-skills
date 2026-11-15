"""Build the coverage matrix from data/coding.json, verify each evidence quote is a verbatim substring of the
registry abstract, compute per-dimension counts, pairwise co-coverage, ranked blind spots and a pool-level
keyword cross-check. Outputs: matrix.csv, references.csv, data/analysis.json."""
import json, csv, re, itertools, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
cod = json.loads((ROOT / "data/coding.json").read_text())
kept = {p["openalex"]: p for p in json.loads((ROOT / "data/retained_raw.json").read_text())}
cr = json.loads((ROOT / "data/crossref.json").read_text())
web_venues = json.loads((ROOT / "data/web_venues.json").read_text())
D = list(cod["dimensions"]); P = list(cod["papers"])
assert set(P) == set(kept), set(P) ^ set(kept)
def squash(s): return re.sub(r"\s+", " ", s).strip()
bad = []
for pid in P:
    ab = squash(kept[pid]["abstract"])
    for dm in D:
        q = cod["papers"][pid].get(dm)
        if q and squash(q) not in ab: bad.append((pid, dm, q))
    q = cod["repo_repair_task"].get(pid)
    if q and q not in ab: bad.append((pid, "repo", q))
assert not bad, bad
M = {pid: {dm: int(dm in cod["papers"][pid]) for dm in D} for pid in P}
N = len(P)
counts = {dm: sum(M[p][dm] for p in P) for dm in D}
covers = {dm: [p for p in P if M[p][dm]] for dm in D}
single_blind = [dm for dm in D if counts[dm] <= 2]
pairs = []
for a, b in itertools.combinations(D, 2):
    both = [p for p in P if M[p][a] and M[p][b]]
    exp = counts[a] * counts[b] / N
    pairs.append({"pair": f"{a}x{b}", "a": a, "b": b, "observed": len(both), "expected_indep": round(exp, 2),
                  "shortfall": round(exp - len(both), 2), "papers": both})
pair_blind = sorted([x for x in pairs if x["observed"] <= 2], key=lambda x: (-x["shortfall"], x["observed"], x["pair"]))
repo = set(cod["repo_repair_task"])
repo_counts = {dm: sum(1 for p in P if M[p][dm] and p in repo) for dm in D}
# pool-level cross-check on all deduplicated retrieved records (title+abstract regex; coarse, reported as a sanity check)
pool = json.loads((ROOT / "data/pool_dedup.json").read_text())
RX = {"D1": r"context (management|compression|pruning|compaction)|compact(ion|s)? |trajectory reduction|kv cache compression",
      "D2": r"loop(ing|s)?\b|stuck|stall|misbehavio|course-correct",
      "D3": r"tree search|mcts|backtrack|restart",
      "D4": r"code graph|call graph|knowledge graph|dependency graph|abstract syntax tree|property graph",
      "D5": r"open-weight|open-source (llm|model)|qwen|llama|gemma|deepseek",
      "D6": r"quantiz|w4a16|4-bit|int4|fp8|low-bit",
      "D7": r"budget"}
SWE = r"swe-bench|issue resol|repository-level (program )?repair|github issue"
pool_hits = {}
for r in pool:
    t = (r["title"] + " " + (r.get("abstract") or "")).lower()
    pool_hits[r.get("openalex") or r.get("arxiv") or r["title"]] = {dm: bool(re.search(rx, t)) for dm, rx in RX.items()} | {"SWE": bool(re.search(SWE, t))}
pool_swe = [k for k, v in pool_hits.items() if v["SWE"]]
pool_counts = {dm: sum(pool_hits[k][dm] for k in pool_swe) for dm in RX}
pool_pairs = {f"{a}x{b}": sum(1 for k in pool_swe if pool_hits[k][a] and pool_hits[k][b]) for a, b in itertools.combinations(D, 2)}
# references with venue upgrade
refs = []
for pid in P:
    p = kept[pid]; c = cr.get(pid, {}); venue = p.get("venue") or ""; vdoi = p.get("doi"); status = "published"
    best = None
    for key in ("title_search", "title_search_noyear"):
        for cand in (c.get(key) or {}).get("candidates", []):
            if (cand.get("title_similarity") or 0) >= 0.95 and cand.get("type") != "posted-content":
                best = cand; break
        if best: break
    vd = c.get("verify_doi") or {}
    if vd.get("verified") and vd.get("type") != "posted-content": venue = vd.get("venue") or venue; src = "Crossref verify_doi_metadata"
    elif best: venue = best["venue"]; vdoi = best["doi"]; src = "Crossref search_crossref_by_title (similarity %.2f)" % best["title_similarity"]
    elif pid in web_venues: venue = web_venues[pid]["venue"]; src = "WebSearch: " + web_venues[pid]["url"]
    else:
        status = "preprint"; src = "OpenAlex only" if not vd.get("verified") else "Crossref posted-content"
        venue = (venue or (vd.get("publisher", "") + " posted content")) + " [preprint]"
    arx = None
    if (p.get("doi") or "").startswith("10.48550/arxiv."): arx = p["doi"].split("arxiv.")[1]
    refs.append({"openalex": pid, "arxiv": arx or p.get("arxiv") or "", "doi": vdoi or "", "status": status, "venue": venue,
                 "venue_source": src, "year": p["year"], "title": p["title"], "first_author": (p.get("authors") or ["?"])[0],
                 "short": cod["papers"][pid]["short"], "cited_by_openalex": p.get("cited_by"), "facets": ";".join(p["facets"])})
with open(ROOT / "matrix.csv", "w", newline="") as f:
    w = csv.writer(f); w.writerow(["openalex_id", "short", "year", "status", "repo_repair_eval"] + [f"{dm}_{cod['short'][dm]}" for dm in D] + [f"{dm}_evidence" for dm in D])
    for r in refs:
        pid = r["openalex"]
        w.writerow([pid, r["short"], r["year"], r["status"], int(pid in repo)] + [M[pid][dm] for dm in D] + [cod["papers"][pid].get(dm, "") for dm in D])
with open(ROOT / "references.csv", "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=list(refs[0])); w.writeheader(); w.writerows(refs)
out = {"N": N, "n_preprint": sum(r["status"] == "preprint" for r in refs), "n_published": sum(r["status"] == "published" for r in refs),
       "n_repo_repair": len(repo), "counts": counts, "covers": covers, "repo_counts": repo_counts, "single_dim_blind_spots": single_blind,
       "zero_rows": [p for p in P if not any(M[p].values())], "row_sums": {p: sum(M[p].values()) for p in P},
       "pairs": pairs, "pair_blind_ranked": pair_blind, "pool_total": len(pool), "pool_swe": len(pool_swe), "pool_counts_swe": pool_counts,
       "pool_pairs_swe": pool_pairs, "quotes_verified": sum(len([k for k in cod["papers"][p] if k in D]) for p in P),
       "year_counts": {y: sum(1 for r in refs if r["year"] == y) for y in sorted({r["year"] for r in refs})}}
# G1..G7: single dimensions with <=2 studies (all papers, then repo-repair subset), then pairs ranked by shortfall
gaps = [{"kind": "single", "dims": [dm], "observed": counts[dm], "papers": covers[dm]} for dm in single_blind]
gaps += [{"kind": "single_repo", "dims": [dm], "observed": repo_counts[dm], "papers": [p for p in covers[dm] if p in repo]} for dm in D if repo_counts[dm] <= 2 and dm not in single_blind]
for x in pair_blind:
    if len(gaps) >= 7: break
    gaps.append({"kind": "pair", "dims": [x["a"], x["b"]], "observed": x["observed"], "expected_indep": x["expected_indep"], "papers": x["papers"], "pool_swe": pool_pairs[x["pair"]]})
for i, g in enumerate(gaps): g["id"] = f"G{i+1}"
out["gaps"] = gaps
(ROOT / "data/analysis.json").write_text(json.dumps(out, indent=1))
print(json.dumps({k: out[k] for k in ("N", "n_preprint", "n_published", "n_repo_repair", "counts", "repo_counts", "single_dim_blind_spots", "zero_rows", "pool_total", "pool_swe", "pool_counts_swe", "quotes_verified", "year_counts")}, indent=0))
for x in pair_blind[:12]: print(x["pair"], cod["short"][x["a"]], "x", cod["short"][x["b"]], "obs", x["observed"], "exp", x["expected_indep"], "pool", pool_pairs[x["pair"]], x["papers"])
for r in refs: print(r["short"][:22].ljust(22), r["status"], r["venue"][:60], "|", r["venue_source"][:50])
