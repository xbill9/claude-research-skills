# Citation & DOI verification — Breaking the 15-Minute Cliff (Gemma 4 loop breaker)

Source: `paper/PAPER.md` reference list (12 entries; the PDF list has the same 12 titles). No entry carries a DOI; 6 carry arXiv IDs.
Every value below comes from a registry response saved in `raw/`. Similarity = difflib ratio on normalised titles.

| Key | Status | Evidence (DOI / ID, similarity) | Action |
|---|---|---|---|
| ref1 [1] | 🔴 `UNVERIFIED / MISMATCH` | OpenAlex `10.48550/arxiv.2607.02770`, sim 0.4; arXiv 2607.02770 comment: "17 pages, 2 figures, technical report, updated"; **mismatched:** title (sim 0.4); first author (entry 'Google DeepMind', registry 'Gemma Team') | Registry has arXiv 2607.02770 'Gemma 4 Technical Report' by 'Gemma Team' (2026). The cited subtitle and 'Google DeepMind' author do not appear in that record. Human review: if this is the intended work, cite the registry title and author. |
| ref2 [2] | 🔴 `UNVERIFIED / MISMATCH` | no record: Crossref best sim 0.3857; OpenAlex best sim 0.5085; arXiv title search 200 | No record in Crossref, OpenAlex or arXiv. Human review: supply a DOI/URL or remove. |
| ref3 [3] | 🟢 `VERIFIED (peer-reviewed)` | Crossref `10.52202/079017-2490`, sim 1.0; venue: Advances in Neural Information Processing Systems 37; arXiv 2405.18512 comment: "43 pages, 8 figures" | Add DOI 10.52202/079017-2490. |
| ref4 [4] | 🟢 `VERIFIED (peer-reviewed)` | Crossref `10.18653/v1/2024.acl-long.665`, sim 1.0; venue: Proceedings of the 62nd Annual Meeting of the Association for Computational Linguistics (Volume 1: Long Papers); arXiv 2407.21358 comment: "Accepted for publication at the ACL 2024 Conference" | Add DOI 10.18653/v1/2024.acl-long.665. |
| ref5 [5] | 🟡 `VERIFIED (preprint only)` | OpenAlex `10.48550/arxiv.2310.04560`, sim 1.0; year entry 2024 vs registry 2023; claimed venue ICLR not found in Crossref/OpenAlex (only preprint record) | Registry holds the arXiv preprint only (2023). 'ICLR, 2024' is not backed by any registry record; confirm on OpenReview or cite as arXiv 2023. |
| ref6 [6] | 🟡 `VERIFIED (preprint only)` | OpenAlex `10.48550/arxiv.2402.05862`, sim 1.0 | Cite as arXiv preprint (matches entry). |
| ref7 [7] | 🟡 `VERIFIED (preprint only)` | OpenAlex `10.48550/arxiv.2310.04562`, sim 0.9483; arXiv 2310.04562 comment: "ICLR 2024"; year entry 2024 vs registry 2023; claimed venue ICLR not found in Crossref/OpenAlex (only preprint record) | Registry title has no '(ULTRA)'. arXiv author comment says 'ICLR 2024'; no registry venue record. Confirm on OpenReview or cite as arXiv 2023. |
| ref8 [8] | 🟢 `VERIFIED (peer-reviewed)` | Crossref `10.1145/3340531.3412757`, sim 1.0; venue: Proceedings of the 29th ACM International Conference on Information & Knowledge Management | Add DOI 10.1145/3340531.3412757. |
| ref9 [9] | 🔴 `UNVERIFIED / MISMATCH` | OpenAlex `10.48550/arxiv.2601.18044`, sim 1.0; arXiv 2601.18044 comment: "23 pages, 5 figures"; **mismatched:** first author (entry 'Taherkhani', registry 'Melika Sepidband'); author count (entry 3, registry 4) | Author list differs: registry is Sepidband, Taherkhani, Pham, Hemmati (arXiv and OpenAlex agree). Human review: fix author order and add H. V. Pham. |
| ref10 [10] | 🟡 `VERIFIED (preprint only)` | OpenAlex `10.48550/arxiv.2410.14684`, sim 1.0; arXiv 2410.14684 comment: "ICLR 2025"; year entry 2025 vs registry 2024; claimed venue ICLR not found in Crossref/OpenAlex (only preprint record) | Add arXiv:2410.14684. arXiv author comment says 'ICLR 2025'; no registry venue record. Registry year 2024. |
| ref11 [11] | 🟡 `VERIFIED (preprint only)` | OpenAlex `10.48550/arxiv.2310.06770`, sim 1.0; arXiv 2310.06770 comment: "Data, code, and leaderboard are available at https://www.swebench.com ICLR 2024, https://openreview.net/forum?id=VTF8yNQM66"; year entry 2024 vs registry 2023; claimed venue ICLR not found in Crossref/OpenAlex (only preprint record) | Add arXiv:2310.06770. arXiv author comment says 'ICLR 2024' (openreview VTF8yNQM66); no registry venue record. Registry year 2023. |
| ref12 [12] | 🔴 `UNVERIFIED / MISMATCH` | no record: Crossref best sim 0.4051; OpenAlex best sim None; arXiv title search 429 | Blog post; no record in Crossref or OpenAlex (arXiv title search was refused with HTTP 429 on every try, so arXiv is unchecked). Human review: give the URL, or drop it if it cannot be found. |

## Counts (computed in `classify_refs.py`)

- 🟢 VERIFIED (peer-reviewed): **3**
- 🟡 VERIFIED (preprint only): **5**
- 🟡 UPGRADE AVAILABLE (preprint → venue): **0**
- 🔴 UNVERIFIED / MISMATCH: **4**
- Peer-reviewed citation ratio: **3/12 = 0.250** (of verified entries: 3/8 = 0.375)

## Notes

- ref1: the part of the cited title before the colon ('Gemma 4 technical report') has similarity 1.0000 to the registry title; the full cited title has 0.4.
- ref2: 5 of its 10 listed author surnames (Markowitz, Perozzi, Rozemberczki, Hemmati, Galkin) are authors of other references in this same list; no registry record exists for the title.
- ref8: Crossref stores the title of 10.1145/3340531.3412757 as just 'Karate Club', so `search_crossref_by_title` did not surface it (best sim 0.5223). OpenAlex has the full title (sim 1.0) on the same DOI; Crossref authors and year match.
- Four entries claim ICLR (ref5, ref7, ref10, ref11). Crossref and OpenAlex hold only arXiv records for them, so they are classed preprint-only. ICLR proceedings carry no DOIs; OpenReview was not queried.
- No `UPGRADE AVAILABLE`: no Crossref `is_preprint_of` relation and no OpenAlex journal/proceedings record was found for any preprint.
