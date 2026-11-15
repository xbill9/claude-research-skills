"""Write REPORT.md and verified_references.bib from results.json + raw registry responses."""
import json, re, sys, collections, difflib, unicodedata
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())
O = sys.argv[1]
rows = json.load(open(O + "/results.json")); ents = {e["key"]: e for e in json.load(open(O + "/entries.json"))}
ax = {r["id"].split("v")[0]: r for r in json.load(open(O + "/raw/arxiv_batch.json"))}
for k in ["ref3", "ref4", "ref5", "ref6"]:
    for r in json.load(open(f"{O}/raw/{k}.json"))["arxiv_by_id"]["entries"]: ax[r["id"].split("v")[0]] = r
icon = {"VERIFIED (peer-reviewed)": "🟢", "VERIFIED (preprint only)": "🟡", "UPGRADE AVAILABLE (preprint → venue)": "🟡", "UNVERIFIED / MISMATCH": "🔴"}
def arxiv_id(r):
    c = r.get("candidate") or {}
    d = (c.get("doi") or "")
    return d.split("arxiv.")[-1] if "10.48550" in d else ents[r["key"]]["arxiv"]
action = {
 "ref1": "Registry has arXiv 2607.02770 'Gemma 4 Technical Report' by 'Gemma Team' (2026). The cited subtitle and 'Google DeepMind' author do not appear in that record. Human review: if this is the intended work, cite the registry title and author.",
 "ref2": "No record in Crossref, OpenAlex or arXiv. Human review: supply a DOI/URL or remove.",
 "ref3": "Add DOI 10.52202/079017-2490.",
 "ref4": "Add DOI 10.18653/v1/2024.acl-long.665.",
 "ref5": "Registry holds the arXiv preprint only (2023). 'ICLR, 2024' is not backed by any registry record; confirm on OpenReview or cite as arXiv 2023.",
 "ref6": "Cite as arXiv preprint (matches entry).",
 "ref7": "Registry title has no '(ULTRA)'. arXiv author comment says 'ICLR 2024'; no registry venue record. Confirm on OpenReview or cite as arXiv 2023.",
 "ref8": "Add DOI 10.1145/3340531.3412757.",
 "ref9": "Author list differs: registry is Sepidband, Taherkhani, Pham, Hemmati (arXiv and OpenAlex agree). Human review: fix author order and add H. V. Pham.",
 "ref10": "Add arXiv:2410.14684. arXiv author comment says 'ICLR 2025'; no registry venue record. Registry year 2024.",
 "ref11": "Add arXiv:2310.06770. arXiv author comment says 'ICLR 2024' (openreview VTF8yNQM66); no registry venue record. Registry year 2023.",
 "ref12": "Blog post; no record in Crossref or OpenAlex (arXiv title search was refused with HTTP 429 on every try, so arXiv is unchecked). Human review: give the URL, or drop it if it cannot be found.",
}
L = ["# Citation & DOI verification — Breaking the 15-Minute Cliff (Gemma 4 loop breaker)", "",
     "Source: `paper/PAPER.md` reference list (12 entries; the PDF list has the same 12 titles). No entry carries a DOI; 6 carry arXiv IDs.",
     "Every value below comes from a registry response saved in `raw/`. Similarity = difflib ratio on normalised titles.", "",
     "| Key | Status | Evidence (DOI / ID, similarity) | Action |", "|---|---|---|---|"]
for r in rows:
    k = r["key"]; e = ents[k]; c = r.get("candidate")
    if c:
        ev = f"{c['src']} `{(c.get('doi') or c['id']).replace('https://doi.org/','')}`, sim {r['sim']}"
        if c["src"] == "Crossref": ev += f"; venue: {c['venue']}"
        a = arxiv_id(r)
        if a and a in ax and ax[a].get("comment"): ev += f"; arXiv {a} comment: \"{ax[a]['comment']}\""
        if r["fields"]: ev += "; **mismatched:** " + "; ".join(r["fields"])
        nn = [n for n in r.get("notes") or [] if not n.startswith("add arXiv")]
        if nn: ev += "; " + "; ".join(nn)
    else:
        ev = r["evidence"]
    L.append(f"| {k} [{e['n']}] | {icon[r['status']]} `{r['status']}` | {ev} | {action[k]} |")
cnt = collections.Counter(r["status"] for r in rows); n = len(rows)
L += ["", "## Counts (computed in `classify_refs.py`)", ""]
for st in icon: L.append(f"- {icon[st]} {st}: **{cnt.get(st,0)}**")
pr = cnt["VERIFIED (peer-reviewed)"]; ver = n - cnt["UNVERIFIED / MISMATCH"]
L += [f"- Peer-reviewed citation ratio: **{pr}/{n} = {pr/n:.3f}** (of verified entries: {pr}/{ver} = {pr/ver:.3f})", "",
      "## Notes", "",
      "- ref1: the part of the cited title before the colon ('Gemma 4 technical report') has similarity "
      f"{difflib.SequenceMatcher(None, norm(ents['ref1']['title'].split(':')[0]), norm([r for r in rows if r['key']=='ref1'][0]['candidate']['title'])).ratio():.4f} to the registry title; the full cited title has {[r for r in rows if r['key']=='ref1'][0]['sim']}.",
      "- ref2: 5 of its 10 listed author surnames (Markowitz, Perozzi, Rozemberczki, Hemmati, Galkin) are authors of other references in this same list; no registry record exists for the title.",
      "- ref8: Crossref stores the title of 10.1145/3340531.3412757 as just 'Karate Club', so `search_crossref_by_title` did not surface it (best sim 0.5223). OpenAlex has the full title (sim 1.0) on the same DOI; Crossref authors and year match.",
      "- Four entries claim ICLR (ref5, ref7, ref10, ref11). Crossref and OpenAlex hold only arXiv records for them, so they are classed preprint-only. ICLR proceedings carry no DOIs; OpenReview was not queried.",
      "- No `UPGRADE AVAILABLE`: no Crossref `is_preprint_of` relation and no OpenAlex journal/proceedings record was found for any preprint.", ""]
open(O + "/REPORT.md", "w").write("\n".join(L))
# BibTeX from registry records only (verified entries)
B = []
for r in rows:
    if r["status"] == "UNVERIFIED / MISMATCH": continue
    c = r["candidate"]; k = r["key"]; au = " and ".join(c["authors"])
    if c["src"] == "Crossref":
        title = c.get("title_openalex_same_doi") or c["title"]
        B.append(f"@inproceedings{{{k},\n  title = {{{title}}},\n  author = {{{au}}},\n  booktitle = {{{c['venue']}}},\n  year = {{{c['year']}}},\n  doi = {{{c['id']}}}\n}}")
    else:
        a = arxiv_id(r)
        B.append(f"@misc{{{k},\n  title = {{{c['title']}}},\n  author = {{{au}}},\n  year = {{{c['year']}}},\n  eprint = {{{a}}},\n  archivePrefix = {{arXiv}},\n  doi = {{10.48550/arXiv.{a}}},\n  note = {{OpenAlex {c['id']}}}\n}}")
open(O + "/verified_references.bib", "w").write("% Generated from Crossref/OpenAlex records fetched in this session. ref1, ref2, ref9, ref12 omitted (unverified).\n\n" + "\n\n".join(B) + "\n")
print(open(O + "/REPORT.md").read())
