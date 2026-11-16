# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

Claude Code plugin `research-kit`, ported from Robina Mirbahar's Antigravity kit (MIT). The repo root is a marketplace (`.claude-plugin/marketplace.json` → `./plugin`); everything that ships is under `plugin/`.

## Commands

`make test`, `make lint`, `make validate`, `make check` (all three) and `make format` wrap the commands below; `make help` lists every target.

- `python3 tests/test_plugin.py` — offline checks. `RESEARCH_KIT_NETWORK=1 python3 tests/test_plugin.py` adds live Crossref checks. The PDF checks skip themselves when pymupdf or Chrome is missing, so a pass with a skip has not exercised rendering.
- `claude plugin validate ./plugin` and `claude plugin validate .` (marketplace).
- `ruff check . && ruff format --check .` (config in `ruff.toml`, line length 120). After `ruff format` via Bash, re-copy `scripts/pdf_tools.py` into the skills: the sync hook only fires on Write/Edit.
- Load without installing: `claude --plugin-dir ./plugin`. MCP tools appear as `mcp__plugin_research-kit_research-audit__<tool>`.
- `/smoke-test` runs all of the above plus a headless end-to-end session.

## Rules

- `scripts/pdf_tools.py` is the master copy. Five skills ship an identical copy in `skills/<name>/scripts/`; a hook re-syncs them after an edit and the test fails on drift. Never edit a skill's copy directly.
- `plugin/mcp/research_audit_mcp.py` and `plugin/hooks/stdlib_shadow_guard.py` use only the standard library; they run in whatever `python3` the user has. Fisher and McNemar results are tested against scipy; keep that test passing after any change to the statistics.
- Skill text uses Claude Code tools (Read, WebFetch, WebSearch, Agent) and `python3`. The test rejects `read_file`, `uv run`, `Antigravity`, `run_workflow`, `search_web` and `literature-search-` in any SKILL.md.
- Never name a new script after a stdlib module (`numbers.py`, `statistics.py`, …); the plugin's own hook denies it.
- The Crossref User-Agent carries a contact address only from `CROSSREF_MAILTO`; don't hard-code one.
- Every pushed change to `plugin/` bumps the version in both `plugin/.claude-plugin/plugin.json` and `.claude-plugin/marketplace.json` (`metadata.version`), kept equal.

## Upstream

Port base: `RobinaMirbahar/My-antigravity-research-skills` at `4aea8e9`. Use `/upstream-sync` to diff later upstream commits against it, and update this commit id after a sync. Keep the original copyright line in `LICENSE`.
