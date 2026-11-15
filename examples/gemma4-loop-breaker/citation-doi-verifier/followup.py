"""Follow-up lookups: verify candidate DOIs in Crossref, fetch full OpenAlex records for the arXiv
candidates found by title search, and search OpenAlex for peer-reviewed versions (upgrade check)."""
import json, sys, time, urllib.parse, urllib.request, subprocess
outdir, mcp = sys.argv[1:3]
UA = {"User-Agent": "citation-doi-verifier-test/0.1"}
def get(url):
    time.sleep(0.6)
    with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
        return json.loads(r.read())
def mcp_call(name, args):
    time.sleep(0.6)
    line = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})
    out = subprocess.run(["python3", "-I", mcp], input=line + "\n", capture_output=True, text=True).stdout
    return json.loads(json.loads(out.strip().splitlines()[-1])["result"]["content"][0]["text"])
res = {"crossref_doi": {}, "openalex_work": {}, "openalex_versions": {}}
# DOIs surfaced by registry searches in lookup_refs.py (raw/*.json)
for k, doi in [("ref3", "10.52202/079017-2490"), ("ref4", "10.18653/v1/2024.acl-long.665"),
               ("ref8", "10.1145/3340531.3412757"), ("ref7_crossref_top", "10.52202/079017-1715")]:
    res["crossref_doi"][k] = mcp_call("verify_doi_metadata", {"doi": doi}); print(k, doi, res["crossref_doi"][k].get("verified"), res["crossref_doi"][k].get("title"))
for k, wid in [("ref1", "W7167604932"), ("ref9", "W7125804068"), ("ref10", "W4404087993"), ("ref11", "W4387561453"),
               ("ref5", "W4387559176"), ("ref6", "W4391710060"), ("ref7", "W4387559172"), ("ref8", "W3093943311")]:
    w = get("https://api.openalex.org/works/" + wid)
    res["openalex_work"][k] = dict(id=w["id"], doi=w.get("doi"), title=w["display_name"], year=w["publication_year"],
        type=w["type"], authors=[a["author"]["display_name"] for a in w["authorships"]],
        locations=[((l.get("source") or {}).get("display_name"), l.get("version"), l.get("landing_page_url")) for l in w["locations"]])
    print(k, wid, w["display_name"], [a["author"]["display_name"] for a in w["authorships"]][:12])
# Upgrade check: every OpenAlex work whose title matches, any type (catches separate venue records)
titles = {"ref5": "Talk like a graph: Encoding graphs for large language models",
          "ref6": "Let your graph do the talking: Encoding structured data for LLMs",
          "ref7": "Towards foundation models for knowledge graph reasoning",
          "ref9": "RGFL: Reasoning guided fault localization for automated program repair",
          "ref10": "RepoGraph: Enhancing AI software engineering with repository-level code graph",
          "ref11": "SWE-bench: Can language models resolve real-world GitHub issues",
          "ref1": "Gemma 4 technical report"}
for k, t in titles.items():
    q = urllib.parse.quote(t.replace(":", " ").replace(",", " "))
    r = get(f"https://api.openalex.org/works?per-page=25&filter=title.search:{q}")
    res["openalex_versions"][k] = [dict(id=w["id"], doi=w.get("doi"), title=w["display_name"], year=w["publication_year"], type=w["type"],
                                        primary=((w.get("primary_location") or {}).get("source") or {}).get("display_name")) for w in r["results"]]
    print(k, "versions:", [(v["type"], v["year"], v["primary"], v["doi"]) for v in res["openalex_versions"][k]][:8])
json.dump(res, open(outdir + "/raw/followup.json", "w"), indent=1)
