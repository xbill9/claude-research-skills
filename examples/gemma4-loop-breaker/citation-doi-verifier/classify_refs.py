"""Step 4: compute matches and statuses from saved registry responses; write report table, counts, ratio, BibTeX.
All similarities are difflib ratios on normalised titles (same normalisation idea as the MCP tool)."""
import json, re, difflib, unicodedata, sys, collections
O = sys.argv[1]
entries = json.load(open(O + "/entries.json"))
raw = {e["key"]: json.load(open(f"{O}/raw/{e['key']}.json")) for e in entries}
fu = json.load(open(O + "/raw/followup.json"))
def norm(s):
    s = unicodedata.normalize("NFKD", s or "").encode("ascii", "ignore").decode().lower()
    return " ".join(re.sub(r"[^a-z0-9 ]", " ", s).split())
def sim(a, b): return round(difflib.SequenceMatcher(None, norm(a), norm(b)).ratio(), 4)
def fam(name):  # family name from "First Last" or "Last, First"
    name = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode()
    return (name.split(",")[0] if "," in name else name.split()[-1]).lower()

# Registry record chosen per entry: Crossref DOI record where one matched, else full OpenAlex work.
cand = {}
for k, c in fu["crossref_doi"].items():
    if k.startswith("ref") and "_" not in k:
        cand[k] = dict(src="Crossref", id=c["doi"], title=c["title"], authors=c["authors"], year=c["year"],
                       venue=c["venue"].replace("&amp;", "&"), type=c["type"], peer_reviewed=c["type"] in ("proceedings-article", "journal-article"))
for k, w in fu["openalex_work"].items():
    if k == "ref8":  # Crossref stores this title as "Karate Club" only; keep the OpenAlex full title alongside
        cand[k]["title_openalex_same_doi"] = w["title"]; continue
    cand[k] = dict(src="OpenAlex", id=w["id"].rsplit("/", 1)[-1], doi=w["doi"], title=w["title"], authors=w["authors"],
                   year=w["year"], venue=w["locations"][0][0], type=w["type"], peer_reviewed=w["type"] not in ("preprint",))
rows = []
for e in entries:
    k = e["key"]; c = cand.get(k); fields = []; notes = []
    best_cr = raw[k]["crossref_title_search"]["best_title_similarity"]
    if not c:
        oa = raw[k]["openalex_title_search"]["results"]
        best_oa = max([sim(e["title"], w["title"]) for w in oa], default=None)
        rows.append(dict(key=k, status="UNVERIFIED / MISMATCH", match=None, sim=None,
                         evidence=f"no record: Crossref best sim {best_cr}; OpenAlex best sim {best_oa}; arXiv title search {raw[k]['arxiv_title_search']['status']}",
                         fields=["not found"], candidate=None)); continue
    s = sim(e["title"], c["title"])
    if "title_openalex_same_doi" in c: s = max(s, sim(e["title"], c["title_openalex_same_doi"]))
    fam_ok = e["first_author_surname"] is not None and fam(c["authors"][0]) == e["first_author_surname"].lower()
    year_ok = e["year"] == c["year"]
    if s < 0.90: fields.append(f"title (sim {s})")
    if not fam_ok: fields.append(f"first author (entry {e['first_author_surname'] or e['authors']!r}, registry {c['authors'][0]!r})")
    # listed co-authors not in registry
    listed = [a.strip() for a in re.split(r",| and ", re.sub(r"\s+et al\.?$", "", e["authors"] or "")) if a.strip()]
    reg = {fam(a) for a in c["authors"]}
    if e["first_author_surname"]:
        missing = [a for a in listed if a.split()[-1].lower() not in reg]
        if missing: fields.append(f"authors not in registry: {missing}")
        if not re.search(r"et al\.?$", e["authors"] or "") and len(listed) != len(c["authors"]):
            fields.append(f"author count (entry {len(listed)}, registry {len(c['authors'])})")
    venue_claim = e["venue_claimed"]
    if not year_ok: notes.append(f"year entry {e['year']} vs registry {c['year']}")
    if venue_claim and not c["peer_reviewed"]: notes.append(f"claimed venue {venue_claim} not found in Crossref/OpenAlex (only preprint record)")
    if not e["arxiv"] and not c["peer_reviewed"] and c.get("doi", "").startswith("https://doi.org/10.48550"):
        notes.append("add arXiv id " + c["doi"].split("arxiv.")[-1])
    # title / author are hard mismatches; year disagreement is only soft when it is explained by an unconfirmed venue claim
    hard = [f for f in fields]
    if not year_ok and not (venue_claim and not c["peer_reviewed"] and abs(e["year"] - c["year"]) == 1): hard.append(notes[0])
    if hard: status = "UNVERIFIED / MISMATCH"
    elif c["peer_reviewed"]: status = "VERIFIED (peer-reviewed)"
    else: status = "VERIFIED (preprint only)"
    rows.append(dict(key=k, status=status, sim=s, first_author_match=fam_ok, year_match=year_ok, fields=hard, notes=notes,
                     evidence=f"{c['src']} {c.get('doi') or c['id']} ({c['id']}), sim {s}", candidate=c))
# ref2 diagnostic: overlap of its author surnames with authors of the other references in this bibliography
others = set()
for e in entries:
    if e["key"] != "ref2" and e["authors"]:
        others |= {a.strip().split()[-1] for a in re.split(r",| and ", re.sub(r"\s+et al\.?$", "", e["authors"])) if a.strip()}
r2 = [a.strip().split()[-1] for a in re.split(r",| and ", entries[1]["authors"]) if a.strip()]
ov = [a for a in r2 if a in others]
json.dump(rows, open(O + "/results.json", "w"), indent=1, default=str)
cnt = collections.Counter(r["status"] for r in rows)
for st in ["VERIFIED (peer-reviewed)", "UPGRADE AVAILABLE (preprint → venue)", "VERIFIED (preprint only)", "UNVERIFIED / MISMATCH"]:
    print(f"{st}: {cnt.get(st, 0)}")
n_pr = cnt.get("VERIFIED (peer-reviewed)", 0)
print(f"peer-reviewed citation ratio: {n_pr}/{len(rows)} = {n_pr/len(rows):.3f}")
n_ver = sum(1 for r in rows if r["status"] != "UNVERIFIED / MISMATCH")
print(f"peer-reviewed among verified: {n_pr}/{n_ver} = {n_pr/n_ver:.3f}")
print(f"ref2 author surnames also authoring other refs here: {len(ov)}/{len(r2)} {ov}")
for r in rows: print(r["key"], r["status"], r.get("sim"), r["fields"], r.get("notes"))
