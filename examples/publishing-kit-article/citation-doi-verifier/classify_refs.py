"""Step 4 (traffic-light report) for a web-only reference list, plus the counts the skill asks for.

Usage: python3 -I classify_refs.py <outdir>
Writes classified.json; prints the table rows and the counts (tee'd to classify_output.txt).

Two verdicts per entry:
  registry_status  - the skill's four statuses, applied as written. Each entry's work title was searched in
                     Crossref (MCP search_crossref_by_title) and OpenAlex; best_is_match decides.
  web_status       - added for this input: RESOLVES+IDENTIFIED (HTTP 200 and an independent field matches
                     the citation), RESOLVES (200, identity not confirmed), BLOCKED (non-200 to a script).
"""

import difflib
import json
import pathlib
import re
import sys
from collections import Counter

out = pathlib.Path(sys.argv[1])
ent = json.loads((out / "entries.json").read_text())
res = json.loads((out / "results.json").read_text())
med = json.loads((out / "raw" / "medium_feed_summary.json").read_text())
gh = res["github"]
MS_TITLE = "Streamline Publishing with a Claude Code Skill"


def norm(s):
    return " ".join(re.sub(r"[^a-z0-9]+", " ", (s or "").lower()).split())


def sim(a, b):
    return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 4)


work_of = {k: wk for wk, w in res["works"].items() for k in w["keys"]}
rows = []
for e in ent["entries"]:
    k = e["key"]
    h = res[k]["http"]
    w = res["works"][work_of[k]]
    ev, ident = [], None
    if k == "L1":
        c = res[k]["cover_check"]
        ident = c["served_equals_local"] and c["name_hash_is_prefix_of"] == ["sha256"]
        ev.append(f"served bytes == paper/cover.ae4d639e.jpg: {c['served_equals_local']} ({c['served_bytes']} B); "
                  f"name hash = sha256 prefix: {'sha256' in c['name_hash_is_prefix_of']}")
    elif k == "L2":
        lic_claim = "Apache-2.0"
        ident = gh["repo_full_name"] == "xbill9/publishing-kit" and gh["license_spdx"] == lic_claim
        ev.append(f"GitHub API: {gh['repo_full_name']}, private={gh['private']}, archived={gh['archived']}, "
                  f"license {gh['license_spdx']} (article says {lic_claim}); marketplace.json name "
                  f"'{gh['marketplace_name']}', plugins {gh['marketplace_plugins']} (article installs publishing@publishing-kit)")
    elif k == "L3":
        ident = gh["skill_md_exists"]
        ev.append(f"GitHub API contents skills/publishing/SKILL.md exists: {gh['skill_md_exists']} (blob {gh['skill_md_sha'][:12]})")
    elif k == "L4":
        ident = gh["article_dir_exists"] and gh["article_dir_has_devto_md"]
        ev.append(f"GitHub API: directory has {gh['article_dir_file_count']} entries; devto-publishing-kit.md present: "
                  f"{gh['article_dir_has_devto_md']}; cover.ae4d639e.jpg present: {gh['article_dir_has_cover_ae4d639e']}")
    elif k == "L5":
        ident = "claude code" in norm(h["html_title"])
        ev.append(f"page title '{h['html_title']}'")
    elif k in ("L6", "L7"):
        d = res[k]["devto_api"]
        ident = d["status"] == 200 and d["title_similarity_to_manuscript"] == 1.0 and d["url"] == e["url"]
        ev.append(f"dev.to API: title sim {d['title_similarity_to_manuscript']}, org '{d['organization']}', "
                  f"published_at {d['published_at']}, canonical {d['canonical_url']}")
    elif k == "L8":
        s = sim((h["og_title"] or "").split(" | ")[0], MS_TITLE)
        ident = s == 1.0
        ev.append(f"og:title '{h['og_title']}' (title part sim {s})")
    elif k == "L9":
        ident = False
        f = med["feed_at"]
        ev.append(f"HTTP {h['status']}, page title '{h['html_title']}' (Cloudflare challenge); WebFetch also 403; "
                  f"author RSS feed: {f['items']} items, article present: {f['target_found']}")
    elif k == "L10":
        body = (out / "raw" / "http_L10.body").read_text(encoding="utf-8", errors="replace")
        act = re.search(r"activity:(\d+)", e["url"]).group(1)
        n_repo = body.count("xbill9/publishing-kit")
        n_title = body.count(MS_TITLE)
        ident = act in body and n_repo > 0 and n_title > 0
        ev.append(f"page title '{h['html_title'][:60]}...' (the post's link card is the repo); activity id in body: "
                  f"{act in body}; 'xbill9/publishing-kit' occurrences: {n_repo}; article title occurrences: {n_title}")
    elif k == "L11":
        s = sim(h["og_title"], MS_TITLE)
        ident = s == 1.0
        ev.append(f"og:title sim {s}")
    if h["status"] != 200:
        web = "BLOCKED"
    elif ident:
        web = "RESOLVES+IDENTIFIED"
    else:
        web = "RESOLVES"
    reg = "UNVERIFIED / MISMATCH"  # no DOI; title search below decides
    if w["crossref_best_is_match"]:
        reg = "VERIFIED (peer-reviewed)"
    reg_ev = (f"{work_of[k]} '{w['title']}': Crossref best sim {w['crossref_best_similarity']} "
              f"('{w['crossref_best_title']}'), OpenAlex best sim {w['openalex_best_similarity']}")
    rows.append({"key": k, "url": e["url"], "where": sorted({o["source"] for o in e["occurrences"]}),
                 "http_status": h["status"], "web_status": web, "web_evidence": "; ".join(ev),
                 "registry_status": reg, "registry_evidence": reg_ev})

for r in rows:
    print(f"{r['key']:4} HTTP {r['http_status']}  {r['web_status']:20} registry: {r['registry_status']}")
n = len(rows)
reg_c = Counter(r["registry_status"] for r in rows)
web_c = Counter(r["web_status"] for r in rows)
peer = reg_c.get("VERIFIED (peer-reviewed)", 0)
ms_rows = [r for r in rows if "devto-publishing-kit.md" in r["where"]]
counts = {
    "entries": n,
    "entries_in_manuscript": len(ms_rows),
    "entries_only_in_links_txt": n - len(ms_rows),
    "registry_identifiers_found": len(ent["registry_identifiers"]),
    "verify_doi_metadata_calls": 0,
    "registry_status": {s: reg_c.get(s, 0) for s in ("VERIFIED (peer-reviewed)", "UPGRADE AVAILABLE (preprint → venue)",
                                                      "VERIFIED (preprint only)", "UNVERIFIED / MISMATCH")},
    "web_status": {s: web_c.get(s, 0) for s in ("RESOLVES+IDENTIFIED", "RESOLVES", "BLOCKED")},
    "web_status_manuscript_only": dict(Counter(r["web_status"] for r in ms_rows)),
    "http_200": sum(r["http_status"] == 200 for r in rows),
    "peer_reviewed_ratio": f"{peer}/{n} = {peer / n:.3f}",
    "registry_best_similarity_max": max(max(w["crossref_best_similarity"] or 0, w["openalex_best_similarity"] or 0)
                                        for w in res["works"].values()),
}
print(json.dumps(counts, indent=2, ensure_ascii=False))
(out / "classified.json").write_text(json.dumps({"rows": rows, "counts": counts}, indent=2, ensure_ascii=False))
