"""Facet retrieval from OpenAlex and arXiv. Writes raw/<facet>__<src>__<i>.json and raw/records.json."""
import json, time, urllib.request, urllib.parse, xml.etree.ElementTree as ET, pathlib, sys
OUT = pathlib.Path(__file__).resolve().parent.parent / "raw"
UA = {"User-Agent": "frontier-gap-radar/0.1 (research survey script)"}
FACETS = {
 "F1_context": ["context management coding agent long horizon software engineering",
                "context compression LLM agent observation pruning SWE-bench",
                "memory summarization coding agent repository repair"],
 "F2_recovery": ["LLM agent loop repetitive actions failure recovery software engineering",
                 "self-debugging large language model test feedback repair",
                 "backtracking tree search coding agent SWE-bench"],
 "F3_graph": ["code graph retrieval repository level issue localization LLM",
              "repository knowledge graph LLM agent code repair",
              "graph-guided code search agent SWE-bench localization"],
 "F4_bench": ["SWE-bench resolve GitHub issues language models benchmark",
              "repository-level code repair benchmark LLM agents evaluation",
              "SWE-bench verified contamination evaluation agents"],
 "F5_small": ["open-weight small language model software engineering agent training SWE-bench",
              "quantization large language model code generation accuracy",
              "fine-tuning open source LLM software engineering agent trajectories"],
 "F6_scaffold": ["agent-computer interface software engineering agent",
                 "agentless localization repair LLM",
                 "autonomous program improvement agent GitHub issues"],
}
def get(url):
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r: return r.read()
def openalex(q):
    url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "filter": "from_publication_date:2023-01-01", "per-page": 25})
    d = json.loads(get(url)); recs = []
    for w in d.get("results", []):
        loc = (w.get("primary_location") or {}).get("source") or {}
        ab = w.get("abstract_inverted_index") or {}
        words = sorted(((p, k) for k, ps in ab.items() for p in ps)); abstract = " ".join(k for _, k in words)
        recs.append({"src": "openalex", "openalex": w["id"].rsplit("/", 1)[-1], "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower() or None,
                     "title": w.get("title") or "", "year": w.get("publication_year"), "venue": loc.get("display_name"),
                     "type": w.get("type"), "cited_by": w.get("cited_by_count"), "abstract": abstract[:3000],
                     "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:8]})
    return url, recs
def arxiv(q):
    terms = " AND ".join(f"all:{t}" for t in q.split())
    url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": terms, "sortBy": "relevance", "max_results": 25})
    root = ET.fromstring(get(url)); ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
    recs = []
    for e in root.findall("a:entry", ns):
        aid = e.find("a:id", ns).text.rsplit("/abs/", 1)[-1]; aid_base = aid.split("v")[0] if "v" in aid else aid
        doi = e.find("x:doi", ns); jr = e.find("x:journal_ref", ns)
        recs.append({"src": "arxiv", "arxiv": aid_base, "doi": doi.text.lower() if doi is not None else None,
                     "title": " ".join(e.find("a:title", ns).text.split()), "year": int(e.find("a:published", ns).text[:4]),
                     "venue": jr.text if jr is not None else "arXiv (preprint)", "abstract": " ".join(e.find("a:summary", ns).text.split())[:3000],
                     "authors": [a.find("a:name", ns).text for a in e.findall("a:author", ns)][:8]})
    return url, recs
log = []; allrecs = []
for f, qs in FACETS.items():
    for i, q in enumerate(qs):
        for name, fn in (("openalex", openalex), ("arxiv", arxiv)):
            for attempt in range(3):
                try: url, recs = fn(q); break
                except Exception as ex: print("retry", f, name, ex, file=sys.stderr); time.sleep(5)
            else: url, recs = "FAILED", []
            for r in recs: r["facet"] = f; r["query"] = q
            (OUT / f"{f}__{name}__{i}.json").write_text(json.dumps({"url": url, "records": recs}, indent=1))
            log.append({"facet": f, "src": name, "query": q, "url": url, "n": len(recs)}); allrecs += recs
            print(f, name, len(recs), q, flush=True); time.sleep(3.1 if name == "arxiv" else 0.6)
(OUT / "records.json").write_text(json.dumps(allrecs, indent=1)); (OUT / "query_log.json").write_text(json.dumps(log, indent=1))
