"""Step 2 (Look each one up), adapted to web references.

Usage: python3 -I lookup_refs.py <outdir> <paper_dir> <research_audit_mcp.py>

For every extracted URL: HTTP GET (generic User-Agent, redirects followed), saving status, final URL,
headers, body sha256 and the page <title>/og:title to raw/http_<key>.json (body in raw/http_<key>.body).
Registry side, as the skill specifies for entries without a DOI: search_crossref_by_title (MCP) and an
OpenAlex works?search= for each distinct cited work title, raw responses in raw/.
Plus metadata sources that do exist for these links: GitHub REST API (via `gh api`) and the dev.to
public API for the two dev.to URLs.
"""

import difflib
import hashlib
import html
import json
import pathlib
import re
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

outdir = pathlib.Path(sys.argv[1])
paper = pathlib.Path(sys.argv[2])
mcp = sys.argv[3]
raw = outdir / "raw"
raw.mkdir(exist_ok=True)
entries = json.loads((outdir / "entries.json").read_text())["entries"]
UA = "research-kit-citation-verifier/1.0"
SPACING = 0.6
MS_TITLE = "Streamline Publishing with a Claude Code Skill"


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def sim(a, b):
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 4)


def get(url, accept="*/*"):
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": accept})
    t0 = time.time()
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body = r.read()
            return {"status": r.status, "final_url": r.geturl(), "headers": dict(r.headers)}, body, time.time() - t0
    except urllib.error.HTTPError as e:
        body = e.read()
        return {"status": e.code, "final_url": e.geturl(), "headers": dict(e.headers)}, body, time.time() - t0
    except Exception as e:
        return {"status": None, "error": repr(e)}, b"", time.time() - t0


def page_titles(body, ctype):
    if "html" not in (ctype or ""):
        return None, None
    t = body.decode("utf-8", "replace")
    m = re.search(r"<title[^>]*>(.*?)</title>", t, re.S | re.I)
    og = re.search(r'<meta[^>]+property="og:title"[^>]+content="([^"]*)"', t, re.I) or re.search(
        r'<meta[^>]+content="([^"]*)"[^>]+property="og:title"', t, re.I
    )
    return (html.unescape(m.group(1).strip()) if m else None, html.unescape(og.group(1)) if og else None)


results = {}
for e in entries:
    meta, body, dt = get(e["url"])
    ctype = (meta.get("headers") or {}).get("Content-Type", "")
    title, og = page_titles(body, ctype)
    rec = {
        "key": e["key"],
        "url": e["url"],
        **meta,
        "content_type": ctype,
        "bytes": len(body),
        "sha256": hashlib.sha256(body).hexdigest(),
        "elapsed_s": round(dt, 3),
        "html_title": title,
        "og_title": og,
        "title_similarity_to_manuscript": {
            "html_title": sim(title, MS_TITLE) if title else None,
            "og_title": sim(og, MS_TITLE) if og else None,
        },
    }
    (raw / f"http_{e['key']}.body").write_bytes(body)
    (raw / f"http_{e['key']}.json").write_text(json.dumps(rec, indent=2))
    results[e["key"]] = {"http": rec}
    print(f"{e['key']} {rec['status']} {ctype[:30]:30} {len(body):>8}B title={title!r:.70} og={og!r:.60}")
    time.sleep(SPACING)

# Cover image: compare served bytes with the local copy, and the hash in the file name.
cover_key = next(e["key"] for e in entries if e["url"].endswith("cover.ae4d639e.jpg"))
local = (paper / "cover.ae4d639e.jpg").read_bytes()
served = (raw / f"http_{cover_key}.body").read_bytes()
name_hash = "ae4d639e"
digests = {a: hashlib.new(a, local).hexdigest() for a in ("md5", "sha1", "sha256")}
results[cover_key]["cover_check"] = {
    "local_bytes": len(local),
    "served_bytes": len(served),
    "served_equals_local": served == local,
    "local_digests": digests,
    "name_hash_is_prefix_of": [a for a, d in digests.items() if d.startswith(name_hash)],
}
print("cover:", json.dumps(results[cover_key]["cover_check"]))

# GitHub REST API: the repo record and the cited paths.
gh_calls = {
    "repo": "repos/xbill9/publishing-kit",
    "skill_md": "repos/xbill9/publishing-kit/contents/skills/publishing/SKILL.md",
    "article_dir": "repos/xbill9/publishing-kit/contents/articles/publishing-kit-skill",
    "marketplace": "repos/xbill9/publishing-kit/contents/.claude-plugin/marketplace.json",
}
gh = {}
for name, path in gh_calls.items():
    p = subprocess.run(["gh", "api", path], capture_output=True, text=True)
    (raw / f"gh_{name}.json").write_text(p.stdout or p.stderr)
    try:
        gh[name] = {"ok": p.returncode == 0, "data": json.loads(p.stdout)}
    except Exception:
        gh[name] = {"ok": False, "error": (p.stderr or p.stdout)[:500]}
    print(f"gh {name}: rc={p.returncode}")
    time.sleep(SPACING)
repo = gh["repo"]["data"] if gh["repo"]["ok"] else {}
article_files = [x["name"] for x in gh["article_dir"]["data"]] if gh["article_dir"]["ok"] else []
mk = {}
if gh["marketplace"]["ok"]:
    import base64

    mk = json.loads(base64.b64decode(gh["marketplace"]["data"]["content"]))
results["github"] = {
    "repo_full_name": repo.get("full_name"),
    "private": repo.get("private"),
    "archived": repo.get("archived"),
    "license_spdx": (repo.get("license") or {}).get("spdx_id"),
    "default_branch": repo.get("default_branch"),
    "pushed_at": repo.get("pushed_at"),
    "skill_md_exists": gh["skill_md"]["ok"],
    "skill_md_sha": gh["skill_md"]["data"].get("sha") if gh["skill_md"]["ok"] else None,
    "article_dir_exists": gh["article_dir"]["ok"],
    "article_dir_file_count": len(article_files),
    "article_dir_has_cover_ae4d639e": "cover.ae4d639e.jpg" in article_files,
    "article_dir_has_devto_md": "devto-publishing-kit.md" in article_files,
    "marketplace_name": mk.get("name"),
    "marketplace_plugins": [p.get("name") for p in mk.get("plugins", [])],
}
print("github:", json.dumps(results["github"]))

# dev.to public API for the dev.to URLs (path = /<org-or-user>/<slug>).
for e in entries:
    if e["host"] == "dev.to":
        path = urllib.parse.urlparse(e["url"]).path.strip("/")
        meta, body, _ = get(f"https://dev.to/api/articles/{path}", "application/json")
        (raw / f"devto_api_{e['key']}.json").write_bytes(body)
        try:
            d = json.loads(body)
        except Exception:
            d = {}
        results[e["key"]]["devto_api"] = {
            "status": meta.get("status"),
            "title": d.get("title"),
            "title_similarity_to_manuscript": sim(d.get("title"), MS_TITLE) if d.get("title") else None,
            "published_at": d.get("published_at"),
            "organization": (d.get("organization") or {}).get("username"),
            "canonical_url": d.get("canonical_url"),
            "url": d.get("url"),
        }
        print(f"devto api {e['key']}:", json.dumps(results[e["key"]]["devto_api"]))
        time.sleep(SPACING)

# Registry lookups the skill prescribes for entries without a DOI.
works = {
    "W1": {"title": "publishing-kit", "author": None, "keys": ["L1", "L2", "L3", "L4"]},
    "W2": {"title": "Claude Code", "author": None, "keys": ["L5"]},
    "W3": {"title": MS_TITLE, "author": None, "keys": ["L6", "L7", "L8", "L9", "L10", "L11"]},
}
req_id = 0
msgs = [
    {"jsonrpc": "2.0", "id": 0, "method": "initialize", "params": {"protocolVersion": "2025-06-18", "capabilities": {}, "clientInfo": {"name": "cdv", "version": "1"}}},
    {"jsonrpc": "2.0", "method": "notifications/initialized"},
]
for i, (wk, w) in enumerate(works.items(), 1):
    msgs.append({"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": "search_crossref_by_title", "arguments": {"title": w["title"], "rows": 5}}})
p = subprocess.run(["python3", "-I", mcp], input="\n".join(json.dumps(m) for m in msgs) + "\n", capture_output=True, text=True, timeout=300)
replies = {}
for line in p.stdout.splitlines():
    r = json.loads(line)
    if r.get("id"):
        replies[r["id"]] = json.loads(r["result"]["content"][0]["text"])
for i, (wk, w) in enumerate(works.items(), 1):
    cr = replies.get(i, {})
    (raw / f"crossref_{wk}.json").write_text(json.dumps(cr, indent=2))
    meta, body, _ = get("https://api.openalex.org/works?" + urllib.parse.urlencode({"search": w["title"], "per-page": 10}), "application/json")
    (raw / f"openalex_{wk}.json").write_bytes(body)
    oa = json.loads(body).get("results", []) if meta.get("status") == 200 else []
    oa_best = max((sim(x.get("title") or "", w["title"]) for x in oa), default=None)
    oa_best_rec = max(oa, key=lambda x: sim(x.get("title") or "", w["title"])) if oa else None
    w["crossref_best_similarity"] = cr.get("best_title_similarity")
    w["crossref_best_is_match"] = cr.get("best_is_match")
    w["crossref_best_title"] = (cr.get("candidates") or [{}])[0].get("title")
    w["crossref_best_doi"] = (cr.get("candidates") or [{}])[0].get("doi")
    w["openalex_status"] = meta.get("status")
    w["openalex_count"] = (json.loads(body).get("meta") or {}).get("count") if meta.get("status") == 200 else None
    w["openalex_best_similarity"] = oa_best
    w["openalex_best_title"] = oa_best_rec.get("title") if oa_best_rec else None
    w["openalex_best_id"] = oa_best_rec.get("id") if oa_best_rec else None
    w["openalex_best_type"] = oa_best_rec.get("type") if oa_best_rec else None
    print(f"{wk} {w['title']!r}: crossref best {w['crossref_best_similarity']} match={w['crossref_best_is_match']} "
          f"({w['crossref_best_title']!r:.60}); openalex count {w['openalex_count']} best {oa_best} ({w['openalex_best_title']!r:.60})")
    time.sleep(SPACING)
results["works"] = works
(outdir / "results.json").write_text(json.dumps(results, indent=2))
