"""Step 2-3: look each entry up in Crossref (via research-audit MCP over stdio), arXiv and OpenAlex.
Raw responses are saved to raw/<key>.json. ~0.6 s between network requests."""
import json, subprocess, sys, time, urllib.parse, urllib.request, xml.etree.ElementTree as ET, os

entries_path, outdir, mcp = sys.argv[1:4]
os.makedirs(os.path.join(outdir, "raw"), exist_ok=True)
UA = {"User-Agent": "citation-doi-verifier-test/0.1"}

def get(url):
    time.sleep(0.6)
    req = urllib.request.Request(url, headers=UA)
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return r.status, r.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8", "replace")
    except Exception as e:
        return None, repr(e)

def mcp_call(name, args):
    time.sleep(0.6)
    line = json.dumps({"jsonrpc": "2.0", "id": 1, "method": "tools/call", "params": {"name": name, "arguments": args}})
    out = subprocess.run(["python3", "-I", mcp], input=line + "\n", capture_output=True, text=True, timeout=120).stdout
    res = json.loads(out.strip().splitlines()[-1])["result"]
    return json.loads(res["content"][0]["text"])

A = "{http://www.w3.org/2005/Atom}"; AX = "{http://arxiv.org/schemas/atom}"
def parse_arxiv(xml):
    root = ET.fromstring(xml); out = []
    for e in root.findall(A + "entry"):
        idt = (e.findtext(A + "id") or "")
        if "api/errors" in idt: continue
        out.append(dict(id=idt.rsplit("/abs/", 1)[-1], title=" ".join((e.findtext(A + "title") or "").split()),
                        authors=[a.findtext(A + "name") for a in e.findall(A + "author")],
                        published=e.findtext(A + "published"), updated=e.findtext(A + "updated"),
                        journal_ref=e.findtext(AX + "journal_ref"), doi=e.findtext(AX + "doi"),
                        comment=e.findtext(AX + "comment")))
    return out

def slim_oa(w):
    return dict(id=w.get("id"), doi=w.get("doi"), title=w.get("display_name"), year=w.get("publication_year"),
                type=w.get("type"),
                authors=[a["author"]["display_name"] for a in w.get("authorships", [])],
                primary_location=((w.get("primary_location") or {}).get("source") or {}).get("display_name"),
                locations=[dict(source=(l.get("source") or {}).get("display_name"),
                                source_type=(l.get("source") or {}).get("type"),
                                version=l.get("version"), landing=l.get("landing_page_url"))
                           for l in w.get("locations", [])])

entries = json.load(open(entries_path))
for e in entries:
    rec = {"entry": e}
    q = (e["title"] or "").replace("`", "")
    args = {"title": q, "rows": 5}
    if e["first_author_surname"]: args["author"] = e["first_author_surname"]
    if e["year"]: args["year"] = e["year"]
    rec["crossref_title_search"] = mcp_call("search_crossref_by_title", args)
    if e["doi"]:
        rec["crossref_doi"] = mcp_call("verify_doi_metadata", {"doi": e["doi"]})
    if e["arxiv"]:
        st, x = get("http://export.arxiv.org/api/query?id_list=" + e["arxiv"])
        rec["arxiv_by_id"] = {"status": st, "entries": parse_arxiv(x) if st == 200 else x[:500]}
        rec["crossref_arxiv_doi"] = mcp_call("verify_doi_metadata", {"doi": "10.48550/arXiv." + e["arxiv"]})
        st, x = get("https://api.openalex.org/works/doi:10.48550/arXiv." + e["arxiv"])
        rec["openalex_by_arxiv_doi"] = {"status": st, "work": slim_oa(json.loads(x)) if st == 200 else x[:300]}
    tq = urllib.parse.quote('"' + q.replace('"', '') + '"')
    st, x = get(f"http://export.arxiv.org/api/query?search_query=ti:{tq}&max_results=5")
    rec["arxiv_title_search"] = {"status": st, "entries": parse_arxiv(x) if st == 200 else x[:500]}
    st, x = get("https://api.openalex.org/works?per-page=5&search=" + urllib.parse.quote(q))
    rec["openalex_title_search"] = {"status": st, "results": [slim_oa(w) for w in json.loads(x)["results"]] if st == 200 else x[:300]}
    json.dump(rec, open(os.path.join(outdir, "raw", e["key"] + ".json"), "w"), indent=1)
    print(e["key"], "crossref best", rec["crossref_title_search"].get("best_title_similarity"),
          "arxiv hits", len(rec["arxiv_title_search"]["entries"]) if isinstance(rec["arxiv_title_search"]["entries"], list) else "ERR",
          "openalex hits", len(rec["openalex_title_search"]["results"]) if isinstance(rec["openalex_title_search"]["results"], list) else "ERR", flush=True)
