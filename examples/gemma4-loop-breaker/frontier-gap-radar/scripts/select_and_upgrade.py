"""Dedupe all retrieved records, pick the retained set, and query Crossref (research-audit MCP over stdio)
for venue upgrades of preprints and DOI verification of published records. Writes data/retained_raw.json, data/crossref.json."""
import json, glob, re, subprocess, time, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
MCP = "/home/xbill/claude-research-skills/plugin/mcp/research_audit_mcp.py"
def norm(t): return re.sub(r"[^a-z0-9]+", " ", t.lower()).strip()
pool = {}
for f in sorted(glob.glob(str(ROOT / "raw" / "*__*.json"))):
    for r in json.load(open(f))["records"]:
        key = r.get("doi") or norm(r["title"])
        k2 = norm(r["title"])
        hit = next((p for p in pool.values() if (r.get("doi") and p.get("doi") == r["doi"]) or norm(p["title"]) == k2), None)
        if hit:
            hit["facets"] = sorted(set(hit["facets"]) | {r["facet"]})
            for idk in ("openalex", "arxiv"):
                if r.get(idk) and not hit.get(idk): hit[idk] = r[idk]
            if hit["src"] == "arxiv" and r["src"] == "openalex":  # prefer OpenAlex metadata (venue, citations)
                for k in ("venue", "type", "cited_by", "doi"): hit[k] = r.get(k) or hit.get(k)
            continue
        r = dict(r); r["facets"] = [r["facet"]]; pool[key] = r
(ROOT / "data").mkdir(exist_ok=True)
(ROOT / "data" / "pool_dedup.json").write_text(json.dumps(list(pool.values()), indent=1))
print("raw files:", len(glob.glob(str(ROOT / "raw" / "*__*.json"))), "deduplicated pool:", len(pool))
KEEP = ["W7117557793","W7125680675","W7215726049","W4415332588","W7154351780","W7167425954","W7172523833","W4416711632",
        "W4404342086","W4415935825","W7160926458","W4415101712","W4404087993","W4416453608","W7125926949","W7223971351",
        "W4387561453","W4405957747","W4417525566","W7131676563","W7171740466","W7225790577","W7223657872","W4411449940","W4402442868"]
byoa = {p["openalex"]: p for p in pool.values() if p.get("openalex")}
kept = [byoa[k] for k in KEEP]
def call(name, args, i):
    msg = json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}})
    out = subprocess.run(["python3", "-I", MCP], input=msg + "\n", capture_output=True, text=True, timeout=90).stdout
    res = json.loads(out.splitlines()[0])["result"]
    return json.loads(res["content"][0]["text"]) if res.get("content") else res
cr = {}
for i, p in enumerate(kept):
    entry = {}
    if p.get("doi") and not p["doi"].startswith("10.48550"):
        entry["verify_doi"] = call("verify_doi_metadata", {"doi": p["doi"]}, i)
    else:
        entry["title_search"] = call("search_crossref_by_title", {"title": p["title"], "year": p["year"]}, i)
        if p.get("doi"): entry["verify_doi"] = call("verify_doi_metadata", {"doi": p["doi"]}, i)
    cr[p["openalex"]] = entry; time.sleep(0.6)
    print(p["openalex"], p["title"][:60], "->", json.dumps(entry)[:300])
(ROOT / "data" / "retained_raw.json").write_text(json.dumps(kept, indent=1))
(ROOT / "data" / "crossref.json").write_text(json.dumps(cr, indent=1))
