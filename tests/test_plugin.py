"""Checks for the research-kit plugin. Standard library only; run with `python3 tests/test_plugin.py`.

Network checks (Crossref) run only with RESEARCH_KIT_NETWORK=1.
PDF/screenshot checks run only when pymupdf and a Chromium browser are present.
"""

from __future__ import annotations

import filecmp
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PLUGIN = ROOT / "plugin"
MCP = PLUGIN / "mcp" / "research_audit_mcp.py"
HOOK = PLUGIN / "hooks" / "stdlib_shadow_guard.py"
PDF_TOOLS = ROOT / "scripts" / "pdf_tools.py"

SKILLS = {
    "ablation-stat-auditor": False,
    "citation-doi-verifier": False,
    "figure-forensics": True,
    "frontier-gap-radar": True,
    "graphic-story": True,
    "interactive-paper-studio": True,
    "math-sandbox": True,
    "paper-number-check": False,
    "trajectory-cinematics": False,
}  # value: skill bundles scripts/pdf_tools.py

passed = 0


def check(cond: bool, msg: str) -> None:
    global passed
    if not cond:
        raise AssertionError(msg)
    passed += 1


def frontmatter(text: str) -> dict:
    m = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    check(m is not None, "SKILL.md must start with YAML frontmatter")
    meta, key = {}, None
    for line in m.group(1).splitlines():
        if re.match(r"^[a-z_-]+:", line):
            key, _, val = line.partition(":")
            meta[key] = val.strip().removeprefix(">-").strip()
        elif key:
            meta[key] = (meta[key] + " " + line.strip()).strip()
    return meta


def test_manifests() -> None:
    market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text())
    entry = market["plugins"][0]
    check(entry["source"] == "./plugin", "marketplace source must be ./plugin")
    plugin = json.loads((PLUGIN / ".claude-plugin" / "plugin.json").read_text())
    check(plugin["name"] == entry["name"] == "research-kit", "plugin name mismatch")
    check(plugin["version"] == market["metadata"]["version"], "plugin.json and marketplace.json versions differ")
    mcp = json.loads((PLUGIN / ".mcp.json").read_text())["mcpServers"]["research-audit"]
    check(mcp["command"] == "python3" and mcp["args"][0].endswith("mcp/research_audit_mcp.py"), ".mcp.json")
    hook = json.loads((PLUGIN / "hooks" / "hooks.json").read_text())["hooks"]["PreToolUse"][0]
    check(hook["matcher"] == "Write" and "stdlib_shadow_guard.py" in hook["hooks"][0]["command"], "hooks.json")


def test_skills() -> None:
    found = sorted(p.name for p in (PLUGIN / "skills").iterdir() if p.is_dir())
    check(found == sorted(SKILLS), f"skill set mismatch: {found}")
    for name, bundles_pdf in SKILLS.items():
        text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
        meta = frontmatter(text)
        check(meta.get("name") == name, f"{name}: frontmatter name")
        check(80 <= len(meta.get("description", "")) <= 1024, f"{name}: description length")
        check("Use when" in meta["description"], f"{name}: description says when to use it")
        for stale in ("read_file", "uv run", "Antigravity", "run_workflow", "search_web", "literature-search-"):
            check(stale not in text, f"{name}: Antigravity-only reference {stale!r}")
        copy = PLUGIN / "skills" / name / "scripts" / "pdf_tools.py"
        if bundles_pdf:
            check(copy.exists() and filecmp.cmp(copy, PDF_TOOLS, shallow=False), f"{name}: pdf_tools.py out of sync")
            check("scripts/pdf_tools.py" in text, f"{name}: references its pdf_tools.py")
    # The audit-record contract the publishing kit's check-facts.py reads.
    fields = ("`paper_value`", "`computed`", "`verdict`", "`MISMATCH`", "`NOT CHECKABLE`")
    for name in ("math-sandbox", "ablation-stat-auditor"):
        text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
        check(all(f in text for f in fields), f"{name}: states the audit-record fields")
    for name in ("graphic-story", "trajectory-cinematics", "interactive-paper-studio"):
        text = (PLUGIN / "skills" / name / "SKILL.md").read_text()
        check("eq_verified_numbers.json" in text and "`MISMATCH`" in text, f"{name}: reads the audit verdicts")
    example = ROOT / "examples" / "gemma4-loop-breaker" / "math-sandbox" / "eq_verified_numbers.json"
    records = json.loads(example.read_text())["equations"]
    check(all({"paper_value", "computed", "verdict"} <= r.keys() for r in records), "example audit records")
    check({r["verdict"] for r in records} == {"VERIFIED", "MISMATCH", "NOT CHECKABLE"}, "example verdict set")


def mcp_session(messages: list[dict]) -> list[dict]:
    stdin = "\n".join(json.dumps(m) for m in messages) + "\n"
    out = subprocess.run([sys.executable, "-I", str(MCP)], input=stdin, capture_output=True, text=True, timeout=60)
    check(out.returncode == 0, f"MCP server exited {out.returncode}: {out.stderr}")
    return [json.loads(line) for line in out.stdout.splitlines()]


def tool(replies: list[dict], mid: int) -> dict:
    r = next(x for x in replies if x.get("id") == mid)["result"]
    check(r["isError"] is False, f"tool call {mid} errored: {r}")
    return json.loads(r["content"][0]["text"])


def call(i: int, name: str, args: dict) -> dict:
    return {"jsonrpc": "2.0", "id": i, "method": "tools/call", "params": {"name": name, "arguments": args}}


def test_mcp_protocol_and_stats() -> None:
    replies = mcp_session(
        [
            {"jsonrpc": "2.0", "id": 1, "method": "initialize", "params": {"protocolVersion": "2025-06-18"}},
            {"jsonrpc": "2.0", "method": "notifications/initialized"},
            {"jsonrpc": "2.0", "id": 2, "method": "tools/list"},
            call(3, "verify_wilson_ci", {"successes": 51, "total": 129}),
            call(4, "verify_fisher_exact", {"k_method": 24, "n_method": 25, "k_baseline": 4, "n_baseline": 25}),
            call(5, "verify_mcnemar_exact", {"b": 10, "c": 2}),
            call(6, "leaderboard_noise_floor", {"num_tasks": 50, "baseline_rate": 0.25}),
            call(7, "verify_wilson_ci", {"successes": 5, "total": 0}),
            {"jsonrpc": "2.0", "id": 8, "method": "no/such"},
            call(10, "leaderboard_noise_floor", {"num_tasks": 58, "baseline": 0.2}),
            {"jsonrpc": "2.0", "id": 9, "method": "ping"},
        ]
    )
    check(len(replies) == 10, f"expected 10 replies (notification gets none), got {len(replies)}")
    check(replies[0]["result"]["protocolVersion"] == "2025-06-18", "protocol negotiation")
    names = {t["name"] for t in replies[1]["result"]["tools"]}
    check(len(names) == 7 and {"verify_mcnemar_exact", "search_openreview_by_title"} <= names, f"tool list: {names}")
    ci = tool(replies, 3)
    check(ci["rate_pct"] == 39.53 and ci["wilson_low_pct"] == 31.52 and ci["wilson_high_pct"] == 48.16, f"wilson {ci}")
    fe = tool(replies, 4)
    check(fe["significant_at_0_01"] and fe["p_value"] < 1e-7 and fe["odds_ratio"] == 126.0, f"fisher {fe}")
    mc = tool(replies, 5)
    check(abs(mc["p_value"] - 0.0385742) < 1e-6, f"mcnemar {mc}")  # 2*sum_{i<=2} C(12,i)/2^12 = 158/4096
    nf = tool(replies, 6)
    check(nf["std_error_pct"] == 6.12 and nf["min_detectable_lift_vs_fixed_baseline_pts"] == 17.16, f"noise {nf}")
    bad = next(x for x in replies if x["id"] == 7)["result"]
    check(bad["isError"] is True, "invalid input must be a tool error")
    check(next(x for x in replies if x["id"] == 8)["error"]["code"] == -32601, "unknown method")
    check(next(x for x in replies if x["id"] == 9)["result"] == {}, "ping")
    typo = next(x for x in replies if x["id"] == 10)["result"]
    check(typo["isError"] is True and "baseline_rate" in typo["content"][0]["text"], f"misspelled argument: {typo}")


def test_against_scipy() -> None:
    try:
        from scipy import stats
    except ImportError:
        print("  skip: scipy not installed")
        return
    sys.path.insert(0, str(MCP.parent))
    import random

    import research_audit_mcp as m

    rng = random.Random(7)
    worst = 0.0
    for _ in range(500):
        n1, n2 = rng.randint(1, 60), rng.randint(1, 60)
        k1, k2 = rng.randint(0, n1), rng.randint(0, n2)
        ref = stats.fisher_exact([[k1, n1 - k1], [k2, n2 - k2]]).pvalue
        worst = max(worst, abs(m.fisher_exact(k1, n1, k2, n2)["p_value"] - ref))
    check(worst < 1e-12, f"fisher differs from scipy by {worst}")
    for b, c in [(0, 0), (0, 7), (13, 4), (30, 30)]:
        ref = stats.binomtest(min(b, c), b + c, 0.5).pvalue if b + c else 1.0
        check(abs(m.mcnemar_exact(b, c)["p_value"] - ref) < 1e-12, f"mcnemar {b},{c}")


def run_hook(path: str, cwd: str) -> str:
    payload = {
        "hook_event_name": "PreToolUse",
        "tool_name": "Write",
        "cwd": cwd,
        "tool_input": {"file_path": path, "content": "x"},
    }
    out = subprocess.run(
        [sys.executable, "-I", str(HOOK)], input=json.dumps(payload), capture_output=True, text=True, timeout=10
    )
    check(out.returncode == 0, f"hook exit {out.returncode}")
    return out.stdout


def test_hook() -> None:
    with tempfile.TemporaryDirectory() as d:
        denied = json.loads(run_hook(f"{d}/numbers.py", d))["hookSpecificOutput"]
        check(denied["permissionDecision"] == "deny" and "verify_math.py" in denied["permissionDecisionReason"], "deny")
        check(
            json.loads(run_hook("statistics.py", d))["hookSpecificOutput"]["permissionDecision"] == "deny", "relative"
        )
        check(run_hook(f"{d}/verify_math.py", d) == "", "allowed name")
        check(run_hook(f"{d}/numbers.txt", d) == "", "non-.py")
        Path(d, "math.py").write_text("")
        check(run_hook(f"{d}/math.py", d) == "", "existing file is not blocked")


def test_pdf_tools() -> None:
    try:
        import pymupdf  # noqa: F401
    except ImportError:
        try:
            import fitz  # noqa: F401
        except ImportError:
            print("  skip: pymupdf not installed")
            return
    with tempfile.TemporaryDirectory() as d:
        html = Path(d, "t.html")
        html.write_text(
            "<html><body><h1>Page one</h1><div style='page-break-after:always'></div><h1>Page two</h1></body></html>"
        )
        pdf = Path(d, "t.pdf")
        r = subprocess.run(
            [sys.executable, str(PDF_TOOLS), "render", "--html", str(html), "--pdf", str(pdf)],
            capture_output=True,
            text=True,
            timeout=240,
        )
        if "No Chromium-based browser" in r.stderr:
            print("  skip: no Chromium browser")
            return
        check(r.returncode == 0, f"render failed: {r.stderr[-800:]}")
        prev = Path(d, "t_preview")
        check(
            sorted(p.name for p in prev.iterdir()) == ["page_01.png", "page_02.png", "t_montage.png"], "montage files"
        )
        png = Path(d, "s.png")
        r = subprocess.run(
            [
                sys.executable,
                str(PDF_TOOLS),
                "shot",
                "--html",
                str(html),
                "--png",
                str(png),
                "--width",
                "390",
                "--height",
                "844",
            ],
            capture_output=True,
            text=True,
            timeout=240,
        )
        check(r.returncode == 0 and png.stat().st_size > 0, f"shot failed: {r.stderr[-800:]}")


def test_crossref_live() -> None:
    if os.environ.get("RESEARCH_KIT_NETWORK") != "1":
        print("  skip: set RESEARCH_KIT_NETWORK=1 for Crossref checks")
        return
    sys.path.insert(0, str(MCP.parent))
    import research_audit_mcp as m

    rec = m.verify_doi("https://doi.org/10.1038/nature14539")  # LeCun, Bengio, Hinton, "Deep learning", 2015
    check(rec["verified"] and rec["year"] == 2015 and rec["first_author_family"] == "LeCun", f"doi {rec}")
    check(m.verify_doi("10.9999/definitely-not-a-real-doi-xyz")["verified"] is False, "missing DOI")
    arx = m.verify_doi("10.48550/arXiv.2405.18512")  # arXiv DOIs live in DataCite, not Crossref
    check(arx["verified"] and arx["registry"] == "datacite" and arx["first_author_family"] == "Sanford", f"arxiv {arx}")
    orv = m.search_openreview("Talk like a graph: Encoding graphs for large language models")["candidates"]
    check(any(c["title_similarity"] == 1.0 and c["venue"] == "ICLR 2024 poster" for c in orv), f"openreview {orv[:2]}")
    hit = m.search_title("Deep learning", author="LeCun", year=2015)
    check(
        hit["best_is_match"] and hit["candidates"][0]["doi"].lower() == "10.1038/nature14539",
        f"title {hit['candidates'][:1]}",
    )


if __name__ == "__main__":
    for fn in [v for k, v in dict(globals()).items() if k.startswith("test_")]:
        print(fn.__name__)
        fn()
    print(f"OK: {passed} checks passed")
