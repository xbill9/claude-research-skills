"""Third pass (OpenAlex only): gap-probing queries for loops, quantized agents, scaffolds."""
import json, time, urllib.request, urllib.parse, pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "raw"
UA = {"User-Agent": "frontier-gap-radar/0.1 (research survey script)"}
Q = {"F2_recovery": ["coding agent stuck repeated edits loop detection", "agent trajectory failure analysis SWE-bench why agents fail"],
     "F5_small": ["quantized language model agent tool use multi-turn", "small language models SWE-bench agent", "low-bit quantization agentic capabilities benchmark"],
     "F6_scaffold": ["SWE-agent agent-computer interfaces automated software engineering", "OpenHands open platform AI software developers"],
     "F1_context": ["KV cache compression long context agent"]}
log = []; allrecs = []
for f, qs in Q.items():
    for i, q in enumerate(qs):
        url = "https://api.openalex.org/works?" + urllib.parse.urlencode({"search": q, "filter": "from_publication_date:2023-01-01", "per-page": 25})
        with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: d = json.loads(r.read())
        recs = []
        for w in d["results"]:
            loc = (w.get("primary_location") or {}).get("source") or {}
            ab = w.get("abstract_inverted_index") or {}
            abstract = " ".join(k for _, k in sorted((p, k) for k, ps in ab.items() for p in ps))
            recs.append({"src": "openalex", "openalex": w["id"].rsplit("/", 1)[-1], "doi": (w.get("doi") or "").replace("https://doi.org/", "").lower() or None,
                "title": w.get("title") or "", "year": w.get("publication_year"), "venue": loc.get("display_name"), "type": w.get("type"),
                "cited_by": w.get("cited_by_count"), "abstract": abstract[:3000], "authors": [a["author"]["display_name"] for a in w.get("authorships", [])][:8], "facet": f, "query": q})
        (OUT / f"{f}__openalex3__{i}.json").write_text(json.dumps({"url": url, "records": recs}, indent=1))
        log.append({"facet": f, "src": "openalex3", "query": q, "url": url, "n": len(recs)}); allrecs += recs
        print(f, len(recs), q); [print("   ", x["year"], x["openalex"], x["title"][:95]) for x in recs[:12]]
        time.sleep(0.6)
(OUT / "query_log3.json").write_text(json.dumps(log, indent=1))
