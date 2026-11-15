"""Targeted prior-art queries for blueprints B1..B6 (OpenAlex, from 2023). Writes data/prior_art.json; prints top hits."""
import json, time, urllib.request, urllib.parse, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
UA = {"User-Agent": "frontier-gap-radar/0.1 (research survey script)"}
Q = {"B1": ["quantization coding agent SWE-bench resolve rate precision", "4-bit quantized model software engineering agent repository repair", "quantized LLM agent looping repeated actions"],
     "B2": ["context reset recovery coding agent loop", "counterfactual context rebuild agent stuck repeated failure", "context pruning loop avoidance backtracking coding agent"],
     "B3": ["code graph loop detection coding agent", "repository graph coverage agent exploration stall", "graph-guided recovery issue resolution agent"],
     "B4": ["Monte Carlo tree search repository knowledge graph issue resolution", "backtracking over code graph localization hypotheses agent", "tree search localization candidates SWE-bench"],
     "B5": ["restart with summary of failed attempt coding agent", "compaction restart software engineering agent trajectory", "learning from failed attempt memory SWE agent retry"],
     "B6": ["context compaction small language model coding agent", "context management 7B open-weight SWE agent small context window", "context window size ablation SWE-bench small model"]}
out = {}
for b, qs in Q.items():
    out[b] = []
    for q in qs:
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "filter": "from_publication_date:2023-01-01", "per-page": 8})
        d = json.loads(urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60).read())
        hits = []
        for w in d["results"]:
            ab = w.get("abstract_inverted_index") or {}
            hits.append({"openalex": w["id"].rsplit("/", 1)[-1], "doi": w.get("doi"), "year": w["publication_year"], "title": w["title"],
                         "abstract": " ".join(k for _, k in sorted((p, k) for k, ps in ab.items() for p in ps))[:1500]})
        out[b].append({"query": q, "url": url, "hits": hits}); time.sleep(0.6)
        print(b, "|", q); [print("    ", h["year"], h["openalex"], h["title"][:95]) for h in hits[:6]]
(ROOT / "data/prior_art.json").write_text(json.dumps(out, indent=1))
