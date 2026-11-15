"""Re-fetch arXiv calls that returned non-200 (HTTP 429 at 0.6 s spacing), 5 s apart, up to 3 tries."""
import json, sys, time, glob, urllib.parse, urllib.request, importlib.util
spec = importlib.util.spec_from_file_location("lk", sys.argv[2])  # reuse parse_arxiv only
src = open(sys.argv[2]).read().split("entries = json.load")[0].replace("entries_path, outdir, mcp = sys.argv[1:4]", "").replace('os.makedirs(os.path.join(outdir, "raw"), exist_ok=True)', "")
ns = {}; exec(src, ns)
def get(url):
    for i in range(3):
        time.sleep(5 * (i + 1))
        st, x = ns["get"](url)
        if st == 200: return st, x
        print("  retry", url, st)
    return st, x
for p in sorted(glob.glob(sys.argv[1] + "/raw/*.json")):
    rec = json.load(open(p)); e = rec["entry"]; q = (e["title"] or "").replace("`", "")
    if "arxiv_by_id" in rec and rec["arxiv_by_id"]["status"] != 200:
        st, x = get("http://export.arxiv.org/api/query?id_list=" + e["arxiv"])
        rec["arxiv_by_id"] = {"status": st, "entries": ns["parse_arxiv"](x) if st == 200 else x[:500]}
    if rec["arxiv_title_search"]["status"] != 200:
        tq = urllib.parse.quote('"' + q.replace('"', '') + '"')
        st, x = get(f"http://export.arxiv.org/api/query?search_query=ti:{tq}&max_results=5")
        rec["arxiv_title_search"] = {"status": st, "entries": ns["parse_arxiv"](x) if st == 200 else x[:500]}
    json.dump(rec, open(p, "w"), indent=1)
    print(e["key"], "by_id", rec.get("arxiv_by_id", {}).get("status"), "title", rec["arxiv_title_search"]["status"], len(rec["arxiv_title_search"]["entries"]), flush=True)
