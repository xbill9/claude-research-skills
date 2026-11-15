#!/usr/bin/env python3
"""Fail when a story, narration, studio page or article repeats a number the paper's audit disputes.

    python3 check_outputs.py --audit audit/ -- Story.html Narration.md article.md
    python3 check_outputs.py --audit eq_verified_numbers.json stat_audit.json -- Comic.pdf

Runs the publishing kit's check-facts.py on each output with the audit JSON as evidence,
after proving that copy of check-facts.py flags a known disputed number (a copy older than
publishing-kit 0.36.0 traces it as ok, which would read as a clean pass). PDFs are converted
to text with PyMuPDF first. Exit 0 when nothing is disputed, 1 when something is, 2 when no
working check-facts.py or no audit record was found.

Untraced claims are counted but do not fail this check: an output's numbers usually come
from the paper itself, which is not passed as evidence here. Pass it with --evidence to trace them.
Stdlib only, apart from PyMuPDF for PDF outputs.
"""

from __future__ import annotations

import argparse
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path

AUDIT_NAMES = ("eq_verified_numbers.json", "stat_audit.json")
DISPUTED_VERDICTS = ("MISMATCH", "NOT CHECKABLE")


def candidates(explicit: str | None) -> list[Path]:
    found: list[str] = [explicit] if explicit else []
    if os.environ.get("PUBLISHING_KIT_CHECK_FACTS"):
        found.append(os.environ["PUBLISHING_KIT_CHECK_FACTS"])
    home = Path.home()
    cached = glob.glob(str(home / ".claude/plugins/cache/*/publishing/*/skills/publishing/scripts/check-facts.py"))

    def ver(p: str) -> tuple[int, ...]:
        m = re.search(r"/publishing/(\d+(?:\.\d+)*)/", p)
        return tuple(int(x) for x in m.group(1).split(".")) if m else ()

    found += sorted(cached, key=ver, reverse=True)
    found += glob.glob(str(home / "*publishing-kit*/skills/publishing/scripts/check-facts.py"))
    seen, out = set(), []
    for f in found:
        p = Path(f).expanduser().resolve()
        if p.is_file() and p not in seen:
            seen.add(p)
            out.append(p)
    return out


def run_facts(cf: Path, article: Path, evidence: list[Path]) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(cf), str(article), "--evidence", *map(str, evidence)],
        capture_output=True,
        text=True,
        timeout=300,
    )


def passes_control(cf: Path) -> bool:
    """A disputed p-value must fail and a verified one must pass."""
    record = {
        "claims": [
            {"id": "control", "paper_value": 4.2e-09, "computed": 7.18e-09, "verdict": "MISMATCH"},
            {"id": "ok", "paper_value": 31.5, "computed": 31.52, "verdict": "VERIFIED"},
        ]
    }
    with tempfile.TemporaryDirectory(prefix="paper-number-check-") as t:
        d = Path(t)
        (d / "ev").mkdir()
        (d / "ev" / "audit.json").write_text(json.dumps(record))
        (d / "bad.md").write_text("Fisher p = 4.2 × 10⁻⁹.\n")
        (d / "good.md").write_text("The lower bound is 31.5%.\n")
        try:
            bad = run_facts(cf, d / "bad.md", [d / "ev"])
            good = run_facts(cf, d / "good.md", [d / "ev"])
        except (OSError, subprocess.TimeoutExpired):
            return False
    return bad.returncode == 1 and "DISPUTED" in bad.stdout and good.returncode == 0


def audit_files(paths: list[str]) -> list[Path]:
    out = []
    for p in map(Path, paths):
        if p.is_dir():
            out += sorted(f for n in AUDIT_NAMES for f in p.rglob(n))
        elif p.is_file():
            out.append(p)
        else:
            sys.exit(f"audit path does not exist: {p}")
    return out


def count_disputed_records(files: list[Path]) -> int:
    n = 0

    def walk(x):
        nonlocal n
        if isinstance(x, list):
            for y in x:
                walk(y)
        elif isinstance(x, dict):
            if "paper_value" in x and str(x.get("verdict", "")).upper() in DISPUTED_VERDICTS:
                n += 1
            for y in x.values():
                walk(y)

    for f in files:
        try:
            walk(json.loads(f.read_text()))
        except (OSError, ValueError):
            pass
    return n


def as_text(output: Path, tmp: Path) -> Path:
    """check-facts reads text; a PDF becomes a .md beside nothing (no ledger is picked up)."""
    if output.suffix.lower() != ".pdf":
        return output
    try:
        import pymupdf as fitz
    except ImportError:
        try:
            import fitz
        except ImportError:
            sys.exit(f"{output}: PDF outputs need PyMuPDF in this python3 (python3 -m pip install pymupdf)")
    with fitz.open(str(output)) as doc:
        text = "\n".join(page.get_text() for page in doc)
    dest = tmp / (output.stem + ".pdf.md")
    dest.write_text(text)
    return dest


LINE = re.compile(r"^\s+(DISPUTED|NOTED|TRACE|ok)\s+(\S+)\s+(.+?)\s+<-\s+(.*)$")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--audit", nargs="+", required=True, help="audit JSON files or directories to search")
    ap.add_argument("--evidence", nargs="*", default=[], help="extra evidence (the paper, data files)")
    ap.add_argument("--check-facts", default=None, help="path to the publishing kit's check-facts.py")
    ap.add_argument("outputs", nargs="+", help="story HTML/PDF, narration .md, studio index.html, article .md")
    a = ap.parse_args()

    audits = audit_files(a.audit)
    n_records = count_disputed_records(audits)
    if not audits or n_records == 0:
        print(f"FAIL  no disputed audit record in {[str(x) for x in audits] or a.audit}")
        print("      Run math-sandbox / ablation-stat-auditor first; a check against no verdicts proves nothing.")
        return 2

    # A path given on purpose is the only one tried: falling back would check with a copy nobody chose.
    tried = [Path(a.check_facts)] if a.check_facts else candidates(None)
    cf = None
    for c in tried:
        if c.is_file() and passes_control(c):
            cf = c
            break
        print(f"skip  {c}: does not flag a disputed number (older than publishing-kit 0.36.0?)")
    if cf is None:
        print("FAIL  no check-facts.py that flags a disputed number was found. Tried:")
        for c in tried or ["(none found)"]:
            print(f"        {c}")
        print("      Install or update the publishing kit to 0.36.0 or later, or pass --check-facts.")
        return 2
    print(f"check-facts: {cf} (control passed)")
    print(f"audit: {len(audits)} file(s), {n_records} disputed record(s)\n")

    evidence = audits + [Path(e) for e in a.evidence]
    total_disputed = 0
    rows = []
    with tempfile.TemporaryDirectory(prefix="paper-number-check-") as t:
        for out in map(Path, a.outputs):
            if not out.is_file():
                print(f"FAIL  output does not exist: {out}")
                return 2
            r = run_facts(cf, as_text(out, Path(t)), evidence)
            counts = {"DISPUTED": 0, "NOTED": 0, "TRACE": 0, "ok": 0}
            disputed = []
            for ln in r.stdout.splitlines():
                m = LINE.match(ln)
                if m:
                    counts[m.group(1)] += 1
                    if m.group(1) == "DISPUTED":
                        disputed.append((m.group(3), m.group(4)))
            total_disputed += counts["DISPUTED"]
            rows.append((out, counts))
            print(
                f"{out}: {counts['DISPUTED']} disputed, {counts['NOTED']} noted, "
                f"{counts['ok']} traced, {counts['TRACE']} untraced"
            )
            for claim, src in disputed:
                print(f"    DISPUTED  {claim}  <- {src}")
    print(f"\n{total_disputed} disputed claim(s) across {len(rows)} output(s)")
    if total_disputed:
        print("Fix each: show the recomputed value, or keep the paper's with its caveat and add a row containing")
        print("the claim under `## DISPUTED` in a CLAIMS.md beside that output.")
    return 1 if total_disputed else 0


if __name__ == "__main__":
    sys.exit(main())
