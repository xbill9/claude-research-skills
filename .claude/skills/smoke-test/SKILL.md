---
name: smoke-test
description: Verify the research-kit plugin end to end — offline and live test suites, plugin and marketplace validation, and a headless Claude Code session that calls an MCP tool and triggers the stdlib-shadow hook. Use after changing anything under plugin/ or scripts/, and before pushing.
---

Run each step and report its result verbatim (pass counts, skips, validator output). Do not summarise a failure as a pass.

0. `ruff check . && ruff format --check .` — must report no findings.
1. `python3 tests/test_plugin.py` then `RESEARCH_KIT_NETWORK=1 python3 tests/test_plugin.py`. Report the `OK: N checks passed` line and every `skip:` line; a skip means that area was not tested.
2. `claude plugin validate ./plugin` and `claude plugin validate .`. Both must print `✔ Validation passed`.
3. Headless end to end, in a fresh empty directory under the scratchpad (never the repo):

   ```bash
   claude -p --plugin-dir /home/xbill/claude-research-skills/plugin \
     --allowedTools "mcp__plugin_research-kit_research-audit__verify_wilson_ci,Write" \
     --output-format json \
     "Call the research-audit MCP tool verify_wilson_ci with successes=51, total=129. Then use the Write tool to create numbers.py in the current directory containing print(1). Report the tool's exact JSON output and the exact result of the Write call."
   ```

   Pass when the result shows `wilson_low_pct: 31.52`, `wilson_high_pct: 48.16`, the Write is denied by the `PreToolUse:Write` hook, and `numbers.py` does not exist in that directory afterwards. Do not use `--permission-mode bypassPermissions`.
4. Check that the version in `plugin/.claude-plugin/plugin.json` equals `metadata.version` in `.claude-plugin/marketplace.json`, and that it is higher than the version at `origin/main` if `plugin/` changed since then (`git diff --quiet origin/main -- plugin/`).

End with one line per step: ✅ / ❌ and the deciding output.
