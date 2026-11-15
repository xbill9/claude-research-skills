---
name: citation-doi-verifier
description: >-
  Verify every reference in a .bib, .tex, Markdown or PDF manuscript against live Crossref, OpenAlex and
  arXiv metadata, upgrade arXiv/bioRxiv preprints to their peer-reviewed venues, and flag citations that
  cannot be verified. Use when auditing a bibliography, checking for hallucinated or broken references,
  fixing DOIs, or preparing a manuscript for submission.
---

# Citation & DOI Integrity Verifier

Check every reference against scholarly registries so no invented title, broken DOI or stale preprint
reaches a submission.

## Ground rules

- **Never invent or "fix" a citation from memory.** Every corrected field comes from a registry response
  in this session, with its DOI or OpenAlex/arXiv ID. An entry you cannot verify is flagged, not repaired.
- **Matching is computed.** Title similarity, author and year agreement come from
  `search_crossref_by_title` (or a script using `difflib`), not from eyeballing.
- Be polite to the APIs: at most ~2 requests per second; batch by DOI where possible.

## Pipeline

1. **Extract entries.** Parse keys, titles, authors, years, DOIs and arXiv IDs. For `.bib` write a small
   parser script; for PDFs extract text first (`pdftotext`, or PyMuPDF). Output a table with one row per entry.
2. **Look each one up.**
   - Has a DOI → `verify_doi_metadata` (MCP tool `research-audit`). Compare title/authors/year to the entry.
   - No DOI → `search_crossref_by_title` with title, first-author surname and year. A match is
     `title_similarity >= 0.90` plus matching surname and year (`best_is_match`).
   - Not in Crossref (common for arXiv-only work) → WebFetch
     `https://api.openalex.org/works?search=<title>` or `http://export.arxiv.org/api/query?search_query=ti:"<title>"`,
     and compute similarity in a script.
3. **Preprint → published upgrade.** For each arXiv/bioRxiv entry, check Crossref `is_preprint_of`,
   OpenAlex `locations` / `primary_location`, and a title search restricted to proceedings and journals
   (NeurIPS, ICLR, ICML, ACL, IEEE, Nature, …). Provide the upgraded BibTeX from the registry record.
4. **Traffic-light report**

   | Key | Status | Evidence (DOI / ID, similarity) | Action |
   |---|---|---|---|

   - 🟢 `VERIFIED (peer-reviewed)` — registry match in a journal or proceedings.
   - 🟡 `UPGRADE AVAILABLE (preprint → venue)` — valid preprint with a newer peer-reviewed record; give the new BibTeX.
   - 🟡 `VERIFIED (preprint only)` — real preprint, no published version found.
   - 🔴 `UNVERIFIED / MISMATCH` — not found, or fields disagree; list which fields. For human review only.

   Finish with counts per status and the **peer-reviewed citation ratio**, both computed in a script.
