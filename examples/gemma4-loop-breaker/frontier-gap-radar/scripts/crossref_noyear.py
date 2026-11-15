"""Re-run Crossref title search WITHOUT the year filter for retained preprints still unresolved (best similarity < 0.95)."""
import json, subprocess, time, pathlib
ROOT = pathlib.Path(__file__).resolve().parent.parent
MCP = "/home/xbill/claude-research-skills/plugin/mcp/research_audit_mcp.py"
cr = json.loads((ROOT / "data/crossref.json").read_text()); kept = {p["openalex"]: p for p in json.loads((ROOT / "data/retained_raw.json").read_text())}
for i, (k, v) in enumerate(cr.items()):
    ts = v.get("title_search")
    if not ts or max((c.get("title_similarity") or 0) for c in ts["candidates"]) >= 0.95: continue
    msg = json.dumps({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "search_crossref_by_title", "arguments": {"title": kept[k]["title"]}}})
    out = subprocess.run(["python3", "-I", MCP], input=msg + "\n", capture_output=True, text=True, timeout=90).stdout
    v["title_search_noyear"] = json.loads(json.loads(out.splitlines()[0])["result"]["content"][0]["text"])
    best = max(v["title_search_noyear"]["candidates"], key=lambda c: c.get("title_similarity") or 0, default={"doi": None})
    print(k, kept[k]["title"][:50], "| best:", best.get("title_similarity"), best["doi"], best.get("venue"), best.get("type")); time.sleep(0.6)
(ROOT / "data/crossref.json").write_text(json.dumps(cr, indent=1))
