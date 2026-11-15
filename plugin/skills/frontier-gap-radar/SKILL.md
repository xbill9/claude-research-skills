---
name: frontier-gap-radar
description: >-
  Survey 18–25 recent papers on a research topic through OpenAlex, arXiv, Europe PMC and Crossref, and
  produce an A4 Frontier Gap Radar & Research Blueprint PDF: thematic synthesis, a papers × capabilities
  coverage heatmap, evidence-backed blind spots, and novelty-checked follow-up research designs. Use when
  asked for a literature gap analysis, research frontier map, related-work survey, or what to research next.
---

# Frontier Gap Radar & Research Blueprint

Synthesize recent work on a topic into an A4 **Frontier Gap Radar & Research Blueprint PDF**.

## Ground rules

- **Every paper in the matrix is a registry record from this session** (DOI, OpenAlex ID or arXiv ID).
  Never add a paper, author, venue or result from memory.
- **Counts are computed.** The coverage matrix lives in a CSV/JSON; "dimensions with ≤ 2 studies", per-cell
  counts and rankings come from a script, not from reading the table.
- Tag every remaining preprint as a preprint.

## Workflow

1. **Parallel multi-angle retrieval.** Split the topic into 5–6 orthogonal facets (theory, algorithms,
   systems constraints, benchmarks, deployment failure modes, …). Retrieve each facet in parallel — one
   **Agent** subagent per facet, or parallel WebFetch calls — using:
   - OpenAlex: `https://api.openalex.org/works?search=<q>&filter=from_publication_date:<YYYY-MM-DD>&per-page=25`
   - arXiv: `http://export.arxiv.org/api/query?search_query=all:<q>&sortBy=submittedDate&max_results=25`
   - Europe PMC (bio/med topics): `https://www.ebi.ac.uk/europepmc/webservices/rest/search?query=<q>&format=json`
   - Crossref, for venue upgrades: the `research-audit` MCP tools `verify_doi_metadata` / `search_crossref_by_title`
   - WebSearch for anything the registries miss.
   Each subagent returns structured records (ID, title, year, venue, one-line method, headline metric with
   its source). Deduplicate by DOI / normalised title in a script; upgrade preprints to published venues.
2. **Capability matrix & blind spots.** Define 7 capability dimensions for the topic and fill an
   `N papers × 7` matrix with evidence for each filled cell. Dimensions covered by ≤ 2 studies are blind
   spots `G1..G7`, each backed by exact paper IDs and metrics.
3. **Novelty-checked blueprints.** Draft follow-up designs `B1..B6` that target the blind spots. For each,
   run targeted prior-art queries; report what was searched and the closest hit, and drop or revise any
   blueprint that prior art already covers.
4. **Figures.** With `matplotlib` at 300 DPI: a capability heatmap and an impact-vs-compute chart for the
   blueprints (state that impact/compute placements are judgements).
5. **Render and inspect.** `python3 scripts/pdf_tools.py render --html Radar.html --pdf <Topic>_Gap_Radar_v1.pdf`
   (script in this skill's base directory), then open each page PNG with **Read** and fix overlaps or
   clipped tables before delivering. Also deliver the matrix CSV and the reference list with IDs.
