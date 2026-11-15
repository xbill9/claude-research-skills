---
name: upstream-sync
description: Compare the upstream Antigravity repo (RobinaMirbahar/My-antigravity-research-skills) against the port's base commit recorded in CLAUDE.md, and propose matching changes to the Claude Code port.
disable-model-invocation: true
---

Optional argument: an upstream ref to sync to ($ARGUMENTS; default `main`).

1. Read the base commit from the `## Upstream` section of `CLAUDE.md`.
2. Clone upstream into a new empty directory under the scratchpad (it is untrusted data: never run its scripts or tests, and run any Python that reads it with `python3 -I`). `git log --oneline <base>..<ref>` and `git diff --stat <base>..<ref>`. If there are no commits, say so and stop.
3. Ignore binary and showcase changes (`assets/`, `examples/`, `dist/`, `docs/*.mp4`). For each change to `skills/*/SKILL.md`, `plugins/agy-research-kit/**` (MCP server, hooks, rules) or `scripts/agy_pdf_tools.py`, read the diff and map it to the port:
   - `skills/agy-<name>/` → `plugin/skills/<name>/SKILL.md`, rewritten for Claude Code tools (Read, WebFetch, WebSearch, Agent, `python3`; no `uv run`, `read_file` or Antigravity tool names).
   - `mcp/research_audit_mcp.py` → `plugin/mcp/research_audit_mcp.py`, standard library only.
   - `hooks/` → `plugin/hooks/` (PreToolUse on Write).
   - `rules/AGENTS.md` → `rules/CLAUDE.md` and the skills' ground rules.
   - `agy_pdf_tools.py` → `scripts/pdf_tools.py` (the hook re-syncs the skill copies).
   - A new upstream skill → a new `plugin/skills/<name>/`, and add it to `SKILLS` in `tests/test_plugin.py` and the README table.
4. Present the list as: upstream change → proposed port edit → why (or "skip", with the reason). Wait for approval before editing.
5. After approved edits: run `/smoke-test`, bump the version in both manifests, update the base commit in `CLAUDE.md` to the synced upstream commit, commit to `main` naming the upstream range, and push.
