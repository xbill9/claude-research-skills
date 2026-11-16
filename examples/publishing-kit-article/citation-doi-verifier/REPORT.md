# Citation & DOI verification — Streamline Publishing with a Claude Code Skill

Source: `paper/devto-publishing-kit.md` (manuscript of record) and `paper/links.txt`. 11 distinct URLs: 5 in the manuscript, 6 only in links.txt. The manuscript has no reference section; its references are inline links and the Links section. DOI or arXiv identifiers in the paper folder's text files: 0.

Two verdicts per entry. **Registry** is the skill's status, applied as written (no DOI, so a Crossref title search through the MCP tool plus OpenAlex). **Web** is the check that applies to a link: fetched, status recorded, and one field compared against an independent source (GitHub API, dev.to API, file bytes, page title).

| Key | URL | Registry status | Web status | Evidence | Action |
|---|---|---|---|---|---|
| L1 | https://raw.githubusercontent.com/xbill9/publishing-kit/main/articles/publishing-kit-skill/cover.ae4d639e.jpg | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | served bytes == paper/cover.ae4d639e.jpg: True (44650 B); name hash = sha256 prefix: True. Registry: W1 'publishing-kit': Crossref best sim 0.4127 ('Publishing Business in Eighteenth-Century England'), OpenAlex best sim 0.4912 | None. Cover URL serves the committed file. |
| L2 | https://github.com/xbill9/publishing-kit | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | GitHub API: xbill9/publishing-kit, private=False, archived=False, license Apache-2.0 (article says Apache-2.0); marketplace.json name 'publishing-kit', plugins ['publishing'] (article installs publishing@publishing-kit). Registry: W1 'publishing-kit': Crossref best sim 0.4127 ('Publishing Business in Eighteenth-Century England'), OpenAlex best sim 0.4912 | None. Keep as a web link; no registry identifier exists. |
| L3 | https://github.com/xbill9/publishing-kit/blob/main/skills/publishing/SKILL.md | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | GitHub API contents skills/publishing/SKILL.md exists: True (blob 34badb408839). Registry: W1 'publishing-kit': Crossref best sim 0.4127 ('Publishing Business in Eighteenth-Century England'), OpenAlex best sim 0.4912 | None. |
| L4 | https://github.com/xbill9/publishing-kit/tree/main/articles/publishing-kit-skill | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | GitHub API: directory has 19 entries; devto-publishing-kit.md present: True; cover.ae4d639e.jpg present: True. Registry: W1 'publishing-kit': Crossref best sim 0.4127 ('Publishing Business in Eighteenth-Century England'), OpenAlex best sim 0.4912 | None. |
| L5 | https://claude.com/claude-code | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | page title 'Claude Code by Anthropic / AI coding agent and assistant'. Registry: W2 'Claude Code': Crossref best sim 0.5946 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.5946 | None. Vendor product page; cite as a web link. |
| L6 | https://dev.to/gde/streamline-publishing-with-a-claude-code-skill-1bdn | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | dev.to API: title sim 1.0, org 'gde', published_at 2026-09-01T14:37:08Z, canonical https://dev.to/gde/streamline-publishing-with-a-claude-code-skill-1bdn. Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | None. links.txt calls it a draft location; dev.to API reports it published. |
| L7 | https://dev.to/aws-builders/streamline-publishing-with-a-claude-code-skill-an4 | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | dev.to API: title sim 1.0, org 'aws-builders', published_at 2026-09-01T14:37:19Z, canonical https://dev.to/aws-builders/streamline-publishing-with-a-claude-code-skill-an4. Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | None. links.txt calls it a draft location; dev.to API reports it published. |
| L8 | https://builder.aws.com/content/3IhAZMOLRPqp4a5USEUtdq6s2d2/streamline-publishing-with-a-claude-code-skill | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | og:title 'Streamline Publishing with a Claude Code Skill / AWS Builder Center' (title part sim 1.0). Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | None. |
| L9 | https://xbill999.medium.com/streamline-publishing-with-a-claude-code-skill-af03e6658c0b | 🔴 `UNVERIFIED / MISMATCH` | 🔴 `BLOCKED` (HTTP 403) | HTTP 403, page title 'Just a moment...' (Cloudflare challenge); WebFetch also 403; author RSS feed: 10 items, article present: False. Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | Human review: open in a browser. Scripts and WebFetch get a Cloudflare 403; RSS feed holds only the 10 newest posts. |
| L10 | https://www.linkedin.com/feed/update/urn:li:activity:7500566496419397632/ | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | page title 'GitHub - xbill9/publishing-kit: Claude Code skill + toolchai...' (the post's link card is the repo); activity id in body: True; 'xbill9/publishing-kit' occurrences: 6; article title occurrences: 6. Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | None. The post's link card is the repo, and the page carries the article title. |
| L11 | https://xbill9.substack.com/p/streamline-publishing-with-a-claude | 🔴 `UNVERIFIED / MISMATCH` | 🟢 `RESOLVES+IDENTIFIED` (HTTP 200) | og:title sim 1.0. Registry: W3 'Streamline Publishing with a Claude Code Skill': Crossref best sim 0.5 ('Sessionmaxxing Claude Code'), OpenAlex best sim 0.416 | None. |

## Registry searches (one per cited work)

| Work | Query title | Entries | Crossref best sim (title) | OpenAlex hits / best sim (title) |
|---|---|---|---|---|
| W1 | publishing-kit | L1, L2, L3, L4 | 0.4127 (Publishing Business in Eighteenth-Century England) | 328669 / 0.4912 (The Ultimate Desktop Publishing Starter Kit) |
| W2 | Claude Code | L5 | 0.5946 (Sessionmaxxing Claude Code) | 231109 / 0.5946 (Sessionmaxxing Claude Code) |
| W3 | Streamline Publishing with a Claude Code Skill | L6, L7, L8, L9, L10, L11 | 0.5 (Sessionmaxxing Claude Code) | 1372 / 0.416 (Streamlining evidence based clinical recommendations with large language models) |

## Counts (computed in `classify_refs.py`)

- Registry VERIFIED (peer-reviewed): **0**
- Registry UPGRADE AVAILABLE (preprint → venue): **0**
- Registry VERIFIED (preprint only): **0**
- Registry UNVERIFIED / MISMATCH: **11**
- Web RESOLVES+IDENTIFIED: **10**
- Web RESOLVES: **0**
- Web BLOCKED: **1**
- HTTP 200: **10 of 11**; manuscript links: {'RESOLVES+IDENTIFIED': 5}
- Peer-reviewed citation ratio: **0/11 = 0.000**
- Highest registry title similarity for any work: **0.5946** (match threshold 0.90)
- `verify_doi_metadata` calls: **0** (no DOI in the input)

## Notes

- The 🔴 registry status on every row means *no scholarly record*, which is expected for a repo, a product page and the article's own syndicated copies. It does not mean the links are broken; the Web column carries that.
- The article states the repo licence as Apache-2.0; the GitHub API reports `Apache-2.0`. The install line `publishing@publishing-kit` matches marketplace.json (name `publishing-kit`, plugins ['publishing']).
- The cover file name `cover.ae4d639e.jpg` is the first 8 hex digits of the file's SHA-256, and the served bytes equal `paper/cover.ae4d639e.jpg`.
- Pages are live and change; every status above is as fetched on this run. Bodies and headers are in `raw/http_<key>.*`.
