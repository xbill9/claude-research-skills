"""Audit the rendered PDF: every number-bearing token in its text must come from story_numbers.json.

Uses the same token rule as build_story.audit_rendered, applied to the text PyMuPDF extracts from the
PDF that is delivered, so a number that slipped in after the HTML audit (or that Chrome rendered
differently) still fails the build. Also checks the page count and that every page is A4.

    python3 verify_pdf.py PublishingKit_Comic_v1.pdf
"""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pymupdf

HERE = Path(__file__).resolve().parent
TOK = re.compile(r"[\w./:,~%+<>-]*\d[\w./:,~%+<>-]*")


def toks(s: str) -> set[str]:
    return {t.strip(".,:;()") for t in TOK.findall(s)}


def main(pdf: str) -> int:
    num = json.loads((HERE / "story_numbers.json").read_text(encoding="utf-8"))
    used = json.loads((HERE / "story_numbers_used.json").read_text(encoding="utf-8"))
    allowed: set[str] = set()
    for k in used:
        allowed |= toks(str(num[k]["display"])) | toks(num[k].get("caveat", ""))
    errs = []
    with pymupdf.open(pdf) as doc:
        n = doc.page_count
        for i, page in enumerate(doc, 1):
            w, h = page.rect.width, page.rect.height
            if abs(w - 595.3) > 1.5 or abs(h - 841.9) > 1.5:
                errs.append(f"page {i} is {w:.1f} x {h:.1f} pt, not A4")
            for t in sorted(toks(page.get_text())):
                if t not in allowed:
                    errs.append(f"page {i}: number {t!r} not in story_numbers.json displays")
    print(f"{pdf}: {n} pages, {len(used)} sourced numbers allowed, {len(errs)} problems")
    for e in errs:
        print("ERROR", e)
    return 1 if errs or not (4 <= n <= 6) else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else str(HERE / "PublishingKit_Comic_v1.pdf")))
