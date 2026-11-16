"""Write REPORT.md and verified_references.bib from classified.json and results.json.

Usage: python3 -I make_report.py <outdir>
BibTeX: no registry record exists for any entry, so there is no upgraded BibTeX. The .bib holds @misc
entries for links that resolved and were identified, every field copied from a response in raw/.
"""

import json
import pathlib
import sys

out = pathlib.Path(sys.argv[1])
c = json.loads((out / "classified.json").read_text())
res = json.loads((out / "results.json").read_text())
ent = json.loads((out / "entries.json").read_text())
rows, k = c["rows"], c["counts"]
ICON = {"UNVERIFIED / MISMATCH": "🔴", "VERIFIED (peer-reviewed)": "🟢"}
WICON = {"RESOLVES+IDENTIFIED": "🟢", "RESOLVES": "🟡", "BLOCKED": "🔴"}
ACTION = {
    "L1": "None. Cover URL serves the committed file.",
    "L2": "None. Keep as a web link; no registry identifier exists.",
    "L3": "None.",
    "L4": "None.",
    "L5": "None. Vendor product page; cite as a web link.",
    "L6": "None. links.txt calls it a draft location; dev.to API reports it published.",
    "L7": "None. links.txt calls it a draft location; dev.to API reports it published.",
    "L8": "None.",
    "L9": "Human review: open in a browser. Scripts and WebFetch get a Cloudflare 403; RSS feed holds only the 10 newest posts.",
    "L10": "None. The post's link card is the repo, and the page carries the article title.",
    "L11": "None.",
}
L = [
    "# Citation & DOI verification — Streamline Publishing with a Claude Code Skill",
    "",
    f"Source: `paper/devto-publishing-kit.md` (manuscript of record) and `paper/links.txt`. "
    f"{k['entries']} distinct URLs: {k['entries_in_manuscript']} in the manuscript, "
    f"{k['entries_only_in_links_txt']} only in links.txt. The manuscript has no reference section; its references are inline links "
    f"and the Links section. DOI or arXiv identifiers in the paper folder's text files: {k['registry_identifiers_found']}.",
    "",
    "Two verdicts per entry. **Registry** is the skill's status, applied as written (no DOI, so a Crossref title search "
    "through the MCP tool plus OpenAlex). **Web** is the check that applies to a link: fetched, status recorded, and one "
    "field compared against an independent source (GitHub API, dev.to API, file bytes, page title).",
    "",
    "| Key | URL | Registry status | Web status | Evidence | Action |",
    "|---|---|---|---|---|---|",
]
for r in rows:
    L.append(f"| {r['key']} | {r['url']} | {ICON[r['registry_status']]} `{r['registry_status']}` | "
             f"{WICON[r['web_status']]} `{r['web_status']}` (HTTP {r['http_status']}) | "
             f"{r['web_evidence'].replace('|', '/')}. Registry: {r['registry_evidence']} | {ACTION[r['key']]} |")
L += [
    "",
    "## Registry searches (one per cited work)",
    "",
    "| Work | Query title | Entries | Crossref best sim (title) | OpenAlex hits / best sim (title) |",
    "|---|---|---|---|---|",
]
for wk, w in res["works"].items():
    L.append(f"| {wk} | {w['title']} | {', '.join(w['keys'])} | {w['crossref_best_similarity']} ({w['crossref_best_title']}) | "
             f"{w['openalex_count']} / {w['openalex_best_similarity']} ({w['openalex_best_title']}) |")
L += [
    "",
    "## Counts (computed in `classify_refs.py`)",
    "",
]
for s, n in k["registry_status"].items():
    L.append(f"- Registry {s}: **{n}**")
for s, n in k["web_status"].items():
    L.append(f"- Web {s}: **{n}**")
L += [
    f"- HTTP 200: **{k['http_200']} of {k['entries']}**; manuscript links: {k['web_status_manuscript_only']}",
    f"- Peer-reviewed citation ratio: **{k['peer_reviewed_ratio']}**",
    f"- Highest registry title similarity for any work: **{k['registry_best_similarity_max']}** (match threshold 0.90)",
    f"- `verify_doi_metadata` calls: **{k['verify_doi_metadata_calls']}** (no DOI in the input)",
    "",
    "## Notes",
    "",
    "- The 🔴 registry status on every row means *no scholarly record*, which is expected for a repo, a product page and "
    "the article's own syndicated copies. It does not mean the links are broken; the Web column carries that.",
    "- The article states the repo licence as Apache-2.0; the GitHub API reports `"
    f"{res['github']['license_spdx']}`. The install line `publishing@publishing-kit` matches marketplace.json "
    f"(name `{res['github']['marketplace_name']}`, plugins {res['github']['marketplace_plugins']}).",
    "- The cover file name `cover.ae4d639e.jpg` is the first 8 hex digits of the file's SHA-256, and the served bytes equal `paper/cover.ae4d639e.jpg`.",
    "- Pages are live and change; every status above is as fetched on this run. Bodies and headers are in `raw/http_<key>.*`.",
]
(out / "REPORT.md").write_text("\n".join(L) + "\n", encoding="utf-8")

# @misc entries, fields from responses only.
bib = []
gh = res["github"]
if gh["repo_full_name"]:
    bib.append("@misc{publishing_kit_repo,\n  title = {" + gh["repo_full_name"] + "},\n  howpublished = {GitHub repository},\n"
               "  url = {https://github.com/" + gh["repo_full_name"] + "},\n  note = {License " + str(gh["license_spdx"]) + "}\n}")
for key in ("L6", "L7"):
    d = res[key]["devto_api"]
    bib.append("@misc{devto_" + d["organization"].replace("-", "_") + ",\n  title = {" + d["title"] + "},\n  howpublished = {DEV Community, "
               + d["organization"] + "},\n  year = {" + d["published_at"][:4] + "},\n  url = {" + d["url"] + "}\n}")
h = res["L5"]["http"]
bib.append("@misc{claude_code,\n  title = {" + h["html_title"] + "},\n  url = {" + h["url"] + "}\n}")
(out / "verified_references.bib").write_text("\n\n".join(bib) + "\n", encoding="utf-8")
print(f"REPORT.md: {len(rows)} rows; verified_references.bib: {len(bib)} @misc entries")
