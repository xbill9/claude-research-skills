# RUN_NOTES — citation-doi-verifier on `examples/gemma4-loop-breaker/paper`

Run date 2026-11-15. Python 3.14.7 (pyenv). No packages installed. All scripts and raw registry responses are in this directory.

## 1. Commands and requests

| Step | Command | Key output |
|---|---|---|
| Extract | `python3 -I extract_refs.py paper/PAPER.md paper/<pdf> entries.json` | `12 entries; with DOI: 0; with arXiv id: 6; titles found in PDF: 12` |
| MCP schema | `initialize` + `tools/list` piped to `research_audit_mcp.py` | `search_crossref_by_title(title, author?, year?, rows)`, `verify_doi_metadata(doi)` |
| Lookup | `python3 -I lookup_refs.py entries.json . plugin/mcp/research_audit_mcp.py` | Per entry: MCP `search_crossref_by_title` (12 calls), MCP `verify_doi_metadata` on `10.48550/arXiv.<id>` (6 calls), arXiv `id_list` (6), arXiv `ti:"<title>"` (12), OpenAlex `works/doi:10.48550/arXiv.<id>` (6), OpenAlex `works?search=` (12). Crossref best similarity ≥ 0.90 only for ref3 and ref4 (1.0 each). |
| arXiv retry | `python3 -I retry_arxiv.py . lookup_refs.py` (5/10/15 s back-off, 3 tries) | arXiv returned HTTP 429 at 0.6 s spacing and kept doing so. Final: title search 200 for ref1–5 (ref1, ref2: 0 hits); 429 for ref6–12. |
| arXiv batch | one `id_list=2601.18044,2310.04562,2607.02770,2410.14684,2310.06770` request | 200. ref9 authors: Sepidband, Taherkhani, Pham, Hemmati. Comments: 2310.04562 "ICLR 2024", 2410.14684 "ICLR 2025", 2310.06770 "... ICLR 2024, openreview ...". |
| Follow-up | `python3 -I followup.py . plugin/mcp/research_audit_mcp.py` | `verify_doi_metadata`: 10.52202/079017-2490 True (NeurIPS 37), 10.18653/v1/2024.acl-long.665 True (ACL 2024), 10.1145/3340531.3412757 True, title "Karate Club" (CIKM 2020). 8 full OpenAlex works; OpenAlex `filter=title.search` returned only arXiv records for ref5/6/7/9/10/11. |
| Classify | `python3 -I classify_refs.py .` (output in `classify_output.txt`) | 🟢 3, 🟡 upgrade 0, 🟡 preprint-only 5, 🔴 4; peer-reviewed ratio 3/12 = 0.250 |
| Report | `python3 -I make_report.py .` | `REPORT.md`, `verified_references.bib` (8 entries) |

All 6 `verify_doi_metadata` calls on arXiv DOIs returned `verified: false, "Crossref HTTP 404"`.

## 2. Problems with SKILL.md

1. **No guidance on the input format this paper uses.** "For `.bib` write a small parser script; for PDFs extract text first". The paper is Markdown with a numbered reference list, which the description lists ("Markdown") but the pipeline never covers. When both a .md and a PDF exist, which is authoritative? I parsed the .md and checked every title against the PDF text. Wanted: a rule for numbered free-text lists (italic title, "et al.", corporate authors) and for picking/cross-checking the source.
2. **The match rule cannot handle corporate or "et al." authors.** "A match is `title_similarity >= 0.90` plus matching surname". ref1 ("Google DeepMind") vs registry "Gemma Team", and ref12 ("Google Developers Blog") have no surname. Wanted: what to do with organisational authors.
3. **The year rule clashes with preprint-vs-venue years.** "plus matching surname and year". ref5, ref7, ref11 cite ICLR 2024 and ref10 ICLR 2025; the only registry records are arXiv, one year earlier. A strict rule makes all four 🔴, which seems wrong for real papers. I treated a 1-year difference as soft *only* when the entry claims a venue that the registry lacks, and reported it in the evidence. Wanted: an explicit rule.
4. **No status for "real work, but claimed venue not confirmed".** The four statuses assume a venue is either found (🟢/🟡 upgrade) or absent. Four entries say "ICLR" and the registries hold only arXiv. I classed them 🟡 preprint-only, which loses the fact that the cited venue is unsupported. Wanted: a status or required flag for "venue claim unverified".
5. **ICLR, the most common ML venue, cannot be verified with the listed sources.** Step 3 lists ICLR among venues to search, but ICLR has no DOIs and is absent from Crossref, and here OpenAlex had no ICLR records either. arXiv author comments ("ICLR 2024") were the only venue evidence, and those are self-reported. Wanted: name OpenReview (or DBLP) as the source for ICLR, or say plainly that ICLR claims stay unverified.
6. **Step 3's Crossref `is_preprint_of` check cannot work for arXiv.** "check Crossref `is_preprint_of`". arXiv DOIs (10.48550) are DataCite: all 6 `verify_doi_metadata` calls returned "Crossref HTTP 404". The relation only exists on the *published* record (as `has_preprint`), or for bioRxiv. Wanted: say that, and point to OpenAlex locations or DataCite for arXiv.
7. **Title search misses records whose Crossref title is truncated.** ref8's DOI is stored in Crossref with title "Karate Club" only (the subtitle is elsewhere), so `search_crossref_by_title` best was 0.5223 and the real record was not among candidates. OpenAlex found it at 1.0. Wanted: always fall through to OpenAlex when Crossref fails, even for venue papers ("Not in Crossref (common for arXiv-only work)" suggests the fallback is only for arXiv), and compare against title + subtitle.
8. **The arXiv endpoint and rate are wrong for arXiv.** "at most ~2 requests per second" and `http://export.arxiv.org/api/query?search_query=ti:"<title>"`. At 0.6 s spacing arXiv returned HTTP 429, and with 5–15 s back-off it continued 429 for 7 of 12 title searches. arXiv asks for ~3 s between calls. Wanted: a per-service rate (arXiv ≥ 3 s), batch `id_list=` for known IDs (one batched request worked), and prefer OpenAlex for arXiv metadata.
9. **"Compare title/authors/year" has no author rule beyond the first surname.** ref9 has the right first-listed names but in the wrong order and missing one author (registry: Sepidband, Taherkhani, Pham, Hemmati; entry: Taherkhani, Sepidband, Hemmati). I flagged first-author mismatch and author-count difference as 🔴. Wanted: say whether author order/count mismatches are 🔴 or a correction.
10. **Peer-reviewed ratio denominator undefined.** "the peer-reviewed citation ratio". I report both 3/12 (all entries) and 3/8 (verified entries).
11. **Grey literature not covered.** ref12 is a blog post; registries cannot hold it, so it can only be 🔴. Wanted: a note that web sources need a URL check and are a separate category.
12. **BibTeX only for upgrades.** "Provide the upgraded BibTeX". With 0 upgrades that output would be empty; the useful output here was DOIs/arXiv IDs to add to verified entries. I wrote BibTeX from registry records for all 8 verified entries. Wanted: say whether corrected BibTeX for all verified entries is a deliverable.
13. **MCP tool name is ambiguous.** "`verify_doi_metadata` (MCP tool `research-audit`)" reads as if the tool is named `research-audit`; that is the server name.
14. **No guidance on where outputs go or which raw responses to keep.** I saved every response in `raw/` so each report value can be traced.

## 3. Not done or not verified

- arXiv title search returned HTTP 429 for ref6–ref12 after retries. ref6, ref7, ref9, ref10, ref11 have arXiv metadata from the `id_list` request and OpenAlex; **ref12 was not checked on arXiv** (unlikely to be there, but unchecked).
- OpenReview and DBLP were not queried, so the four ICLR venue claims (ref5, ref7, ref10, ref11) are neither confirmed nor refuted.
- ref1: the arXiv record 2607.02770 "Gemma 4 Technical Report" may be the intended work, but the cited subtitle and author do not match it; left for human review.
- ref2 and ref12: no record found in Crossref or OpenAlex. Whether they exist outside these registries was not established.
