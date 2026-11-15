"""Step 1: extract the reference list from PAPER.md and cross-check against the PDF."""
import json, re, sys
import pymupdf

md_path, pdf_path, out = sys.argv[1:4]
md = open(md_path, encoding="utf-8-sig").read()
refs_md = md.split("### References", 1)[1]
rows = []
for m in re.finditer(r"^(\d+)\.\s+(.*)$", refs_md, re.M):
    n, line = int(m.group(1)), m.group(2)
    tm = re.search(r"\*(.+?)\*", line)
    title = tm.group(1).strip() if tm else None
    authors = line[: tm.start()].strip().rstrip(".") if tm else None
    rest = line[tm.end():] if tm else line
    years = re.findall(r"\b(19|20)\d{2}\b", rest)
    year = int(re.findall(r"\b((?:19|20)\d{2})\b", rest)[-1]) if years else None
    arx = re.search(r"arXiv:(\d{4}\.\d{4,5})", rest)
    doi = re.search(r"\b(10\.\d{4,9}/\S+)", line)
    venue = re.sub(r"[`().,]|arXiv:\S+|\b(19|20)\d{2}\b", " ", rest).strip() or None
    first = None
    if authors:
        a0 = re.split(r",| and ", authors.replace(" et al.", "").replace(" et al", ""))[0].strip()
        corporate = not re.match(r"^([A-Z]\.\s*)+\S", a0)  # no initials -> corporate author
        first = None if corporate else a0.split()[-1]
    rows.append(dict(key=f"ref{n}", n=n, authors=authors, first_author_surname=first,
                     title=title, year=year, venue_claimed=venue,
                     arxiv=arx.group(1) if arx else None, doi=doi.group(1) if doi else None))
# PDF cross-check: each title should appear in the PDF reference text
doc = pymupdf.open(pdf_path)
pdf = " ".join(p.get_text() for p in doc)
pdf_refs = re.sub(r"\s+", " ", pdf[pdf.rfind("References"):])
for r in rows:
    t = re.sub(r"[`]", "", r["title"] or "")
    r["title_in_pdf"] = re.sub(r"\s+", " ", t) in pdf_refs
json.dump(rows, open(out, "w"), indent=1)
print(f"{len(rows)} entries; with DOI: {sum(1 for r in rows if r['doi'])}; with arXiv id: {sum(1 for r in rows if r['arxiv'])}; titles found in PDF: {sum(r['title_in_pdf'] for r in rows)}")
for r in rows:
    print(r["key"], r["first_author_surname"], r["year"], r["arxiv"], r["venue_claimed"], "|", r["title"])
