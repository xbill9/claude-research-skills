#!/usr/bin/env python3
"""PreToolUse hook: refuse to create a new .py file that shadows a stdlib module numpy/scipy import.

A `numbers.py` or `statistics.py` next to a script breaks `import numpy` with an opaque
circular-import error. This hook denies a Write that would create one and tells Claude to
pick another name (verify_math.py, audit_stats.py). Editing a file that already exists is allowed.

Reads the hook payload on stdin; standard library only.
Ported from agy-research-kit by Robina Mirbahar (MIT).
"""

from __future__ import annotations

import json
import os
import sys

SHADOWED = {"numbers", "math", "statistics", "random", "types", "fractions", "decimal", "json"}


def main() -> int:
    try:
        payload = json.load(sys.stdin)
    except (json.JSONDecodeError, ValueError):
        return 0  # never block on a payload we cannot read
    tool_input = payload.get("tool_input") or {}
    path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
    stem, ext = os.path.splitext(os.path.basename(path))
    if ext != ".py" or stem not in SHADOWED:
        return 0
    if not os.path.isabs(path):
        path = os.path.join(payload.get("cwd") or os.getcwd(), path)
    if os.path.exists(path):
        return 0
    reason = (
        f"research-kit: '{stem}.py' would shadow Python's stdlib '{stem}' module and break "
        f"numpy/scipy imports in that directory. Use a different name, e.g. verify_math.py or audit_stats.py."
    )
    json.dump(
        {
            "hookSpecificOutput": {
                "hookEventName": "PreToolUse",
                "permissionDecision": "deny",
                "permissionDecisionReason": reason,
            }
        },
        sys.stdout,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
