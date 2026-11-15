"""Second arXiv pass: phrase queries (abs:"..."), 6 s pacing, 30 s back-off on HTTP 429."""
import json, time, sys, urllib.request, urllib.parse, xml.etree.ElementTree as ET, pathlib
OUT = pathlib.Path(__file__).resolve().parent.parent / "raw"
UA = {"User-Agent": "frontier-gap-radar/0.1 (research survey script)"}
Q = {
 "F1_context": ['abs:"SWE-bench" AND abs:context', 'abs:"coding agent" AND abs:"context management"', 'abs:"software engineering agent" AND abs:memory'],
 "F2_recovery": ['abs:"SWE-bench" AND abs:backtracking', 'abs:"coding agent" AND abs:loop', 'abs:"SWE-bench" AND abs:"tree search"', 'abs:"self-debugging"'],
 "F3_graph": ['abs:"SWE-bench" AND abs:graph', 'abs:"code graph" AND abs:"issue localization"', 'abs:"repository-level" AND abs:"knowledge graph" AND abs:code'],
 "F4_bench": ['abs:"SWE-bench" AND abs:benchmark', 'abs:"SWE-bench Verified"'],
 "F5_small": ['abs:"SWE-bench" AND abs:"open-weight"', 'abs:"SWE-bench" AND abs:"small language model"', 'abs:quantization AND abs:"code generation" AND abs:LLM', 'abs:"SWE-bench" AND abs:trajectories AND abs:"fine-tun"'],
 "F6_scaffold": ['abs:"SWE-bench" AND abs:agent AND abs:interface', 'abs:"SWE-bench" AND abs:localization AND abs:repair'],
}
ns = {"a": "http://www.w3.org/2005/Atom", "x": "http://arxiv.org/schemas/atom"}
log = json.loads((OUT / "query_log.json").read_text()); allrecs = json.loads((OUT / "records.json").read_text())
for f, qs in Q.items():
    for i, q in enumerate(qs):
        url = "http://export.arxiv.org/api/query?" + urllib.parse.urlencode({"search_query": q, "sortBy": "relevance", "max_results": 25})
        recs = []
        for attempt in range(4):
            try:
                with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r: root = ET.fromstring(r.read())
                break
            except Exception as ex: print("retry", q, ex, file=sys.stderr, flush=True); time.sleep(30)
        else: root = None
        if root is not None:
            for e in root.findall("a:entry", ns):
                aid = e.find("a:id", ns).text.rsplit("/abs/", 1)[-1]; base = aid.rsplit("v", 1)[0]
                yr = int(e.find("a:published", ns).text[:4])
                if yr < 2023: continue
                doi = e.find("x:doi", ns); jr = e.find("x:journal_ref", ns)
                recs.append({"src": "arxiv", "arxiv": base, "doi": doi.text.lower() if doi is not None else None,
                    "title": " ".join(e.find("a:title", ns).text.split()), "year": yr,
                    "venue": jr.text if jr is not None else "arXiv (preprint)", "abstract": " ".join(e.find("a:summary", ns).text.split())[:3000],
                    "authors": [a.find("a:name", ns).text for a in e.findall("a:author", ns)][:8], "facet": f, "query": q})
        (OUT / f"{f}__arxiv2__{i}.json").write_text(json.dumps({"url": url, "records": recs}, indent=1))
        log.append({"facet": f, "src": "arxiv2", "query": q, "url": url, "n": len(recs)}); allrecs += recs
        print(f, len(recs), q, flush=True); time.sleep(6)
(OUT / "records.json").write_text(json.dumps(allrecs, indent=1)); (OUT / "query_log.json").write_text(json.dumps(log, indent=1))
