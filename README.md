# claude-research-skills

`research-kit` is a Claude Code plugin for research-paper engineering. It has eight skills, a statistics and citation MCP server that uses only the Python standard library, and a hook that stops scripts from being given names that shadow stdlib modules.

It is a Claude Code port of Robina Mirbahar's [My-antigravity-research-skills](https://github.com/RobinaMirbahar/My-antigravity-research-skills) (`agy-research-kit` for Google Antigravity), MIT licensed. The original repository has the worked example outputs (PDFs, video, interactive studio).

---

#### Install

```bash
claude plugin marketplace add xbill9/claude-research-skills
claude plugin install research-kit@claude-research-skills
```

Or try it in one session from a clone, without installing:

```bash
git clone https://github.com/xbill9/claude-research-skills
claude --plugin-dir claude-research-skills/plugin
```

Requirements: `python3` (3.10+). The skills that render PDFs or screenshots also need `pymupdf` and `pillow` installed in that interpreter, plus Chrome, Edge or Chromium. Set `RESEARCH_KIT_BROWSER` if the browser is somewhere unusual. The video skill needs `imageio`, `imageio-ffmpeg` and `matplotlib`. Every script carries a PEP 723 header, so `uv run` works too.

---

#### The eight skills

Skills load on demand. Inside the plugin each is namespaced, for example `/research-kit:ablation-stat-auditor`.

| Skill | What it does | Output |
| :--- | :--- | :--- |
| `ablation-stat-auditor` | Recomputes Wilson score intervals and Fisher, exact McNemar and Wilcoxon tests, then checks each gain against the benchmark's noise floor. | Audit table (Markdown + LaTeX), `stat_audit.json` |
| `citation-doi-verifier` | Checks every reference against Crossref, OpenAlex and arXiv, and upgrades preprints to the venue that published them. | Traffic-light bibliography report |
| `figure-forensics` | Adds numbered callouts, shaded regimes, decode cards and takeaway cards to a paper's figures. | A4 Visual Anatomy PDF + page PNGs |
| `math-sandbox` | Splits equations into colour-coded operators and checks each claim numerically and by Monte Carlo. | A4 Equation Guide PDF + `eq_verified_numbers.json` |
| `interactive-paper-studio` | Builds a single-file offline simulator with sliders over the paper's own equations. The JS is checked against Python. | `index.html` |
| `trajectory-cinematics` | Animates the system state and a 2×2 grid of live plots. | 1920×1080 H.264 `.mp4` + generator + narration |
| `graphic-story` | Draws a comic of the paper in SVG with code. Every number in it comes from the paper. | A4 graphic-novel PDF |
| `frontier-gap-radar` | Retrieves 18–25 papers in parallel, builds a capability matrix, and turns its blind spots into research designs checked for novelty. | A4 Gap Radar & Blueprint PDF + matrix CSV |

Every skill follows the same ground rules:

- Each figure traces to the source or to a script run.
- Intervals, p-values, counts and title-similarity scores are computed in code, never by the model.
- Scripts run in the active `python3`.
- Every rendered page is opened with the Read tool before the result is delivered.

---

#### MCP server: `research-audit`

`plugin/mcp/research_audit_mcp.py` is a stdio JSON-RPC server that needs nothing installed.

| Tool | Returns |
| :--- | :--- |
| `verify_wilson_ci(successes, total, confidence)` | Rate and Wilson interval |
| `verify_fisher_exact(k_method, n_method, k_baseline, n_baseline)` | Two-sided p-value, odds ratio, difference in points |
| `verify_mcnemar_exact(b, c)` | Exact binomial McNemar p-value for two systems run on the same tasks |
| `leaderboard_noise_floor(num_tasks, baseline_rate, alpha, power)` | Standard error, 95% CI half-width, and minimum detectable lift against a fixed baseline and between two runs |
| `verify_doi_metadata(doi)` | Crossref record, or DataCite when Crossref has none (arXiv `10.48550` DOIs live there): title, authors, year, venue, type, `registry`, and Crossref's `is_preprint_of` / `has_preprint` links |
| `search_crossref_by_title(title, author, year, rows)` | Crossref candidates ranked by computed title similarity, with author and year match flags and a `best_is_match` verdict |
| `search_openreview_by_title(title, rows)` | OpenReview notes with their venue label (`ICLR 2024 poster`, a workshop, `Submitted to …`) and computed title similarity; confirms the ICLR/NeurIPS/TMLR venues Crossref does not index |

Fisher's exact test uses exact rational arithmetic. It matches `scipy.stats.fisher_exact` to within 3.3e-16 over 3,000 random tables. McNemar matches `scipy.stats.binomtest` to within 1.3e-15 over 2,000 cases. Set `CROSSREF_MAILTO` to put your address in the User-Agent and use Crossref's polite pool. Without it, the server sends no contact details. Every tool rejects argument names its schema does not list, so a misspelled option returns an error instead of a default.

---

#### Hook and rules

- **`stdlib_shadow_guard.py`** runs as a `PreToolUse` hook on `Write`. It denies creating a new `numbers.py`, `math.py`, `statistics.py`, `random.py`, `types.py`, `fractions.py`, `decimal.py` or `json.py`, and suggests `verify_math.py` instead. Edits to existing files go through.
- **`rules/CLAUDE.md`** holds the kit's always-on provenance and visual QA rules as a snippet. Paste it into a project's `CLAUDE.md` to switch them on for that project.

---

#### Worked example

[`examples/gemma4-loop-breaker/`](examples/gemma4-loop-breaker/) holds all eight skills run on one paper, with each run's outputs and notes.

---

#### Mapping from the Antigravity kit

| Antigravity | Claude Code |
| :--- | :--- |
| `plugins/agy-research-kit/plugin.json` | `plugin/.claude-plugin/plugin.json` + root `.claude-plugin/marketplace.json` |
| `mcp_config.json` (`uv run`, scipy) | `plugin/.mcp.json` (`python3`, stdlib only) |
| `hooks.json` `PostToolUse` on `write_file`, scans the tree | `plugin/hooks/hooks.json` `PreToolUse` on `Write`, checks the one target path and denies |
| `rules/AGENTS.md` | `rules/CLAUDE.md` snippet, with the same rules repeated inside each skill |
| `agy-*` skills | same skills without the prefix, namespaced `research-kit:` |
| `read_file` on montages | Read tool on the page PNGs |
| `literature-search-*`, `search_web`, `run_workflow` | WebFetch on the OpenAlex / arXiv / Europe PMC / Crossref APIs, WebSearch, parallel Agent subagents |
| `agy_pdf_tools.py` | `pdf_tools.py`, with a fresh browser profile per render, a `shot` command for screenshots, and `import pymupdf` |

---

#### Tests

```bash
python3 tests/test_plugin.py                         # 130 offline checks
RESEARCH_KIT_NETWORK=1 python3 tests/test_plugin.py  # + live Crossref, DataCite and OpenReview checks (135)
claude plugin validate ./plugin
```

The tests cover:

- manifests and skill frontmatter, plus a scan for leftover Antigravity tool names;
- that the five copies of `pdf_tools.py` are identical;
- the MCP protocol (initialize, notifications, ping, unknown methods, tool errors) and its numbers checked against scipy;
- the hook's deny and allow cases;
- a real HTML → PDF → montage render and a phone-width screenshot.

---

#### License

MIT. Original work © 2026 Robina Mirbahar. Claude Code port © 2026 xbill9.
