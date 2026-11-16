# RUN_NOTES — citation-doi-verifier on `examples/publishing-kit-article/paper`

Run date 2026-11-16. Python 3.14.7 (pyenv), standard library only; `gh` for the GitHub API. `CROSSREF_MAILTO` unset, so no contact address was sent; web requests used the User-Agent `research-kit-citation-verifier/1.0`. All scripts and raw responses (37 files, 4.2 MB) are in this directory.

## 1. Commands and requests

| Step | Command | Key output |
|---|---|---|
| Extract | `python3 -I extract_refs.py ../paper entries.json` | `distinct URLs: 11`; 8 occurrences in the manuscript, 7 in links.txt; 6 URLs only in links.txt; `DOI/arXiv identifiers in 25 text files: 0`; `reference section heading present: False`; 2 `/plugin` install lines |
| Lookup | `python3 -I lookup_refs.py . ../paper plugin/mcp/research_audit_mcp.py` (output in `lookup_output.txt`) | 11 HTTP GETs: 10 × 200, 1 × 403 (Medium, Cloudflare "Just a moment..."). Cover: served bytes equal local file (44650 B), name hash = SHA-256 prefix. `gh api`: 4 calls, all rc=0; licence `Apache-2.0`; marketplace `publishing-kit`, plugins `['publishing']`. dev.to API: both articles 200, title sim 1.0, published 2026-09-01. MCP `search_crossref_by_title` × 3 and OpenAlex `works?search=` × 3: best sims 0.4127 / 0.5946 / 0.5, `match=False` for all three |
| Medium retry | WebFetch of the Medium URL | `HTTP 403 Forbidden` |
| Medium feed | `python3 -I medium_feed.py .` (output in `medium_feed_output.txt`) | both feed URLs 200, 10 items each, article absent; items span 11–15 Nov 2026 |
| Classify | `python3 -I classify_refs.py .` (output in `classify_output.txt`) | Registry: 🔴 11, 🟢 0, 🟡 0, 🟡 0; peer-reviewed ratio `0/11 = 0.000`. Web: RESOLVES+IDENTIFIED 10, RESOLVES 0, BLOCKED 1 |
| Report | `python3 -I make_report.py .` | `REPORT.md` (11 rows), `verified_references.bib` (4 `@misc` entries) |

`verify_doi_metadata` was called 0 times: the input has no DOI.

## 2. Headline findings

- The manuscript cites no scholarly work. It has no reference section, and the 25 text files in the paper folder contain 0 DOI or arXiv identifiers. Its references are 5 web links (repo, SKILL.md, article directory, claude.com, cover image) plus 6 syndication URLs in links.txt.
- Applied as written, the skill marks all 11 entries 🔴 `UNVERIFIED / MISMATCH` and gives a peer-reviewed ratio of 0/11. The highest registry title similarity for any cited work was 0.5946 (threshold 0.90). This means "no scholarly record", which is expected for these sources; it says nothing about whether the links work.
- On the web check, 10 of 11 links return HTTP 200 and each matches an independent field: GitHub API (repo, file and directory exist; licence Apache-2.0 as the article states; marketplace name and plugin match the install command), dev.to API (title identical, URL canonical), served cover bytes identical to the local file, page titles on Builder Center, Substack and LinkedIn.
- All 5 links in the manuscript itself resolve and are identified.
- The Medium URL (links.txt only) returns 403 to scripts and to WebFetch, and the article is outside the 10-item RSS feed window. It stays unverified and needs a browser check.
- links.txt labels the dev.to URLs "Draft locations", and the article front matter has `published: false`; the dev.to API returns both as published on 2026-09-01. The URLs are correct; the label is stale.
- The LinkedIn post's link card is the GitHub repo, and the page also carries the article title (6 occurrences).

## 3. Where SKILL.md fell short for this input

1. **No path for a document with no bibliography.** The pipeline starts from "keys, titles, authors, years, DOIs and arXiv IDs". This article has none: no reference section, no titles or authors attached to links. I treated each distinct URL as an entry and assigned each a "work title" (repo name, product name, article title) to feed the title search. That choice is mine, not the skill's.
2. **No status for web sources.** The four statuses all describe registry records. A working GitHub link and a dead one both land in 🔴 `UNVERIFIED / MISMATCH`, so the skill's report cannot tell a reader which links are broken. I added a separate web status (resolves and identified / resolves / blocked).
3. **No instruction to fetch URLs.** The skill never says to check that a cited URL resolves or that it serves what the citation claims. For this input that is the only check with any signal.
4. **The peer-reviewed ratio is meaningless here.** `0/11` is computed as instructed, but for a blog post citing software and its own syndicated copies the number reads as a defect where there is none. The skill gives no rule for when to omit or qualify it.
5. **The title-search match rule needs a title, author and year.** `best_is_match` with no author or year falls back to title similarity alone. Short generic titles like "publishing-kit" and "Claude Code" return unrelated records (an 18th-century publishing history; a "Sessionmaxxing Claude Code" item). Nothing in the skill says when a title search is not worth running.
6. **No metadata sources for software or web pages.** Crossref, OpenAlex and arXiv do not cover GitHub repos or vendor pages. The sources that do hold checkable metadata here (GitHub API for licence and paths, dev.to API for title and canonical URL, Software Heritage or Zenodo for archived software) are not mentioned.
7. **No rule for sites that block scripts.** Medium answers with a Cloudflare 403 to both a script and WebFetch. The skill says to flag what cannot be verified, but gives no fallback order (feed, archive.org, browser) or a status distinguishing "blocked" from "not found".
8. **Which file is the reference list is undefined.** The task named links.txt alongside the manuscript; 6 of the 11 URLs exist only there. The skill does not say whether side files (link lists, social posts) count as part of the bibliography.
9. **BibTeX output assumes registry records.** "Provide the upgraded BibTeX from the registry record" yields nothing when no registry record exists. The `@misc` entries in `verified_references.bib` were built from GitHub and dev.to API responses, which the skill does not cover.
10. **Live web content has no date or snapshot rule.** Registry records are stable; web pages change. The skill does not ask for an access date or a stored copy, which a link check needs to be reproducible. Bodies and headers from this run are in `raw/http_<key>.*`.

## 4. Not done or not verified

- The Medium article (L9) was not reached; whether it exists at that URL is unverified.
- The cited pages' content beyond the identity field was not compared with the article's claims.
- The article's statements about destination behaviour (dev.to hard breaks, cover crop, Medium data URIs, LinkedIn API states) are claims, not references, and are outside this skill.
