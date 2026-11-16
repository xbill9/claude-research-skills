"""Step 1 (Extract entries): every reference-like item in the manuscript of record and links.txt.

Usage: python3 -I extract_refs.py <paper_dir> <out.json>
Rows: one per distinct URL, with every place it occurs. Also scans the manuscript and all
text files in the paper folder for DOI and arXiv-id patterns (the skill's registry inputs).
"""

import json
import pathlib
import re
import sys

paper = pathlib.Path(sys.argv[1])
out = pathlib.Path(sys.argv[2])
ms = paper / "devto-publishing-kit.md"
text = ms.read_text(encoding="utf-8")

DOI_RE = re.compile(r"\b10\.\d{4,9}/[^\s\"<>)\]]+", re.I)
ARXIV_RE = re.compile(r"(?:arxiv[:./\s]*(?:abs/)?)(\d{4}\.\d{4,5})(v\d+)?", re.I)
URL_RE = re.compile(r"https?://[^\s)\"'<>\]`]+")
MDLINK_RE = re.compile(r"\[([^\]]+)\]\((https?://[^)\s]+)\)")

entries: dict[str, dict] = {}


def add(url, source, line, context, link_text=None):
    url = url.rstrip(".,;")
    e = entries.setdefault(url, {"url": url, "link_texts": [], "occurrences": []})
    if link_text and link_text not in e["link_texts"]:
        e["link_texts"].append(link_text)
    e["occurrences"].append({"source": source, "line": line, "context": context})


in_code = False
in_front = False
for i, line in enumerate(text.splitlines(), 1):
    if i == 1 and line.strip() == "---":
        in_front = True
        continue
    if in_front and line.strip() == "---":
        in_front = False
        continue
    if line.lstrip().startswith("```"):
        in_code = not in_code
        continue
    ctx = "front matter" if in_front else ("code block" if in_code else "prose")
    seen = set()
    for m in MDLINK_RE.finditer(line):
        add(m.group(2), ms.name, i, ctx, m.group(1))
        seen.add(m.group(2))
    for m in URL_RE.finditer(line):
        if m.group(0) not in seen:
            add(m.group(0), ms.name, i, ctx)

lt = paper / "links.txt"
for i, line in enumerate(lt.read_text(encoding="utf-8").splitlines(), 1):
    m = re.match(r"^(\S+)\s*=\s*(https?://\S+)", line)
    if m:
        add(m.group(2), lt.name, i, "links.txt key " + m.group(1), m.group(1))

# Registry-style identifiers anywhere in the paper folder's text files.
id_hits = []
for p in sorted(paper.rglob("*")):
    if p.is_file() and p.suffix in {".md", ".txt", ".html", ".args"}:
        t = p.read_text(encoding="utf-8", errors="replace")
        for m in DOI_RE.finditer(t):
            id_hits.append({"file": str(p.relative_to(paper)), "kind": "doi", "match": m.group(0)})
        for m in ARXIV_RE.finditer(t):
            id_hits.append({"file": str(p.relative_to(paper)), "kind": "arxiv", "match": m.group(0)})

# Install identifiers that a reader resolves against GitHub (marketplace add <owner/repo>).
installs = [
    {"line": i, "text": line.strip()}
    for i, line in enumerate(text.splitlines(), 1)
    if line.strip().startswith("/plugin ")
]

rows = list(entries.values())
for n, r in enumerate(rows, 1):
    r["key"] = f"L{n}"
    r["host"] = re.match(r"https?://([^/]+)", r["url"]).group(1)
files_scanned = sum(
    1 for p in paper.rglob("*") if p.is_file() and p.suffix in {".md", ".txt", ".html", ".args"}
)
result = {
    "manuscript": ms.name,
    "entries": rows,
    "registry_identifiers": id_hits,
    "files_scanned_for_identifiers": files_scanned,
    "install_identifiers": installs,
    "has_reference_section": bool(re.search(r"^#+\s*(references|bibliography|works cited)\b", text, re.I | re.M)),
}
out.write_text(json.dumps(result, indent=2), encoding="utf-8")
print(f"distinct URLs: {len(rows)}")
for src in (ms.name, lt.name):
    print(f"  occurrences in {src}: {sum(1 for r in rows for o in r['occurrences'] if o['source'] == src)}")
print(f"  URLs only in links.txt: {sum(1 for r in rows if all(o['source'] == lt.name for o in r['occurrences']))}")
print(f"DOI/arXiv identifiers in {files_scanned} text files: {len(id_hits)}")
print(f"reference section heading present: {result['has_reference_section']}")
print(f"/plugin install lines: {len(installs)}")
for r in rows:
    print(f"  {r['key']} {r['url']}  [{', '.join(sorted({o['context'] for o in r['occurrences']}))}]")
