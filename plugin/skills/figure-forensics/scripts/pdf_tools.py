# /// script
# requires-python = ">=3.10"
# dependencies = [
#   "pymupdf>=1.24.0",
#   "pillow>=10.0.0",
# ]
# ///
"""HTML -> A4 PDF via headless Chrome/Edge/Chromium, plus PyMuPDF page montages for visual QA.

    python3 pdf_tools.py render  --html Anatomy.html --pdf Paper_Figure_Anatomy_v1.pdf
    python3 pdf_tools.py montage --pdf Paper.pdf --out-dir preview/
    python3 pdf_tools.py shot    --html index.html --png shot.png --width 1440 --height 900

`render` writes the PDF, one PNG per page and a montage sheet; open the PNGs with the Read
tool to check for overlapping callouts, clipped tables and orphan headings before delivery.
`shot` screenshots an HTML page (for checking interactive studios at desktop and phone width).

Needs: pymupdf and pillow in the active python3, and a Chromium-based browser
(set RESEARCH_KIT_BROWSER to its path if it is not found).
Ported from agy-research-kit by Robina Mirbahar (MIT).
"""

from __future__ import annotations

import argparse
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

BROWSER_CANDIDATES = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "google-chrome",
    "google-chrome-stable",
    "chromium",
    "chromium-browser",
    "microsoft-edge",
    "msedge",
]


def find_browser() -> str:
    for var in ("RESEARCH_KIT_BROWSER", "AGY_PDF_BROWSER"):
        env_bin = os.environ.get(var)
        if env_bin and (Path(env_bin).exists() or shutil.which(env_bin)):
            return env_bin
    for cand in BROWSER_CANDIDATES:
        if Path(cand).exists():
            return cand
        resolved = shutil.which(cand)
        if resolved:
            return resolved
    raise RuntimeError(
        "No Chromium-based browser (Chrome/Edge/Chromium) found. Set RESEARCH_KIT_BROWSER to its binary path."
    )


def _run_browser(args: list[str], out: Path) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()  # a stale file must never pass for a fresh render
    with tempfile.TemporaryDirectory(prefix="research-kit-chrome-") as profile:
        cmd = [find_browser(), "--headless=new", "--disable-gpu", f"--user-data-dir={profile}", *args]
        proc = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=180)
    if not out.exists() or out.stat().st_size == 0:
        raise RuntimeError(f"Headless browser produced no output ({proc.returncode}):\n{proc.stderr[-2000:]}")


def html_to_pdf(html_path: Path, pdf_path: Path, wait_ms: int = 1800) -> Path:
    pdf_path = pdf_path.resolve()
    _run_browser(
        [
            "--no-pdf-header-footer",
            f"--virtual-time-budget={wait_ms}",
            f"--print-to-pdf={pdf_path}",
            html_path.resolve().as_uri(),
        ],
        pdf_path,
    )
    return pdf_path


MIN_WINDOW_WIDTH = 500  # headless Chrome lays out at >= 500 CSS px whatever --window-size says


def html_to_png(html_path: Path, png_path: Path, width: int, height: int, wait_ms: int = 1800) -> Path:
    """Screenshot `html_path` with a true `width` x `height` CSS-pixel viewport.

    The page is loaded in an iframe of exactly that size inside a window at least
    MIN_WINDOW_WIDTH wide, then cropped, so phone-width media queries really apply.
    """
    from PIL import Image

    png_path = png_path.resolve()
    with tempfile.TemporaryDirectory(prefix="research-kit-shot-") as tmp:
        wrapper = Path(tmp, "viewport.html")
        wrapper.write_text(
            '<!doctype html><html><body style="margin:0;background:#fff">'
            f'<iframe src="{html_path.resolve().as_uri()}" '
            f'style="display:block;width:{width}px;height:{height}px;border:0"></iframe></body></html>',
            encoding="utf-8",
        )
        _run_browser(
            [
                "--hide-scrollbars",
                "--allow-file-access-from-files",
                f"--window-size={max(width, MIN_WINDOW_WIDTH)},{height}",
                f"--virtual-time-budget={wait_ms}",
                f"--screenshot={png_path}",
                wrapper.as_uri(),
            ],
            png_path,
        )
    with Image.open(png_path) as im:
        cropped = im.crop((0, 0, width, height))
    cropped.save(png_path)
    return png_path


def pdf_to_montage(pdf_path: Path, out_dir: Path, dpi: int = 110, cols: int = 3) -> tuple[list[Path], Path | None]:
    try:
        import pymupdf as fitz
    except ImportError:  # PyMuPDF < 1.24.3
        import fitz
    from PIL import Image, ImageDraw

    out_dir = out_dir.resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    zoom = dpi / 72.0
    pages: list[Path] = []
    imgs = []
    with fitz.open(str(pdf_path)) as doc:
        for idx, page in enumerate(doc):
            pix = page.get_pixmap(matrix=fitz.Matrix(zoom, zoom), alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ImageDraw.Draw(img).rectangle([0, 0, img.width - 1, img.height - 1], outline=(180, 190, 205), width=2)
            page_file = out_dir / f"page_{idx + 1:02d}.png"
            img.save(page_file)
            pages.append(page_file)
            imgs.append(img)
    if not imgs:
        return [], None
    w = max(i.width for i in imgs)
    h = max(i.height for i in imgs)
    pad, cols = 16, max(1, min(cols, len(imgs)))
    rows = math.ceil(len(imgs) / cols)
    sheet = Image.new("RGB", (cols * w + (cols + 1) * pad, rows * h + (rows + 1) * pad), (241, 245, 249))
    for idx, im in enumerate(imgs):
        r, c = divmod(idx, cols)
        sheet.paste(im, (pad + c * (w + pad), pad + r * (h + pad)))
    montage = out_dir / f"{Path(pdf_path).stem}_montage.png"
    sheet.save(montage)
    return pages, montage


def main() -> int:
    ap = argparse.ArgumentParser(description="Render HTML to A4 PDF and build a PyMuPDF QA montage.")
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("render", help="HTML -> PDF, then per-page PNGs and a montage")
    p.add_argument("--html", type=Path, required=True)
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--montage-dir", type=Path, default=None)
    p.add_argument("--dpi", type=int, default=110)
    p.add_argument("--cols", type=int, default=3)
    p.add_argument("--wait-ms", type=int, default=1800, help="time for fonts/KaTeX/JS to settle")

    p = sub.add_parser("montage", help="Per-page PNGs and a montage from an existing PDF")
    p.add_argument("--pdf", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--dpi", type=int, default=110)
    p.add_argument("--cols", type=int, default=3)

    p = sub.add_parser("shot", help="Screenshot an HTML page at a given viewport")
    p.add_argument("--html", type=Path, required=True)
    p.add_argument("--png", type=Path, required=True)
    p.add_argument("--width", type=int, default=1440)
    p.add_argument("--height", type=int, default=900)
    p.add_argument("--wait-ms", type=int, default=1800)

    a = ap.parse_args()
    if a.cmd == "render":
        pdf = html_to_pdf(a.html, a.pdf, a.wait_ms)
        pages, montage = pdf_to_montage(pdf, a.montage_dir or pdf.parent / f"{pdf.stem}_preview", a.dpi, a.cols)
        print(f"OK PDF: {pdf} ({pdf.stat().st_size:,} bytes, {len(pages)} pages)")
        print(f"   pages: {[str(x) for x in pages]}")
        print(f"   montage: {montage}")
    elif a.cmd == "montage":
        pages, montage = pdf_to_montage(a.pdf, a.out_dir, a.dpi, a.cols)
        print(f"OK {len(pages)} pages | montage: {montage}")
    else:
        png = html_to_png(a.html, a.png, a.width, a.height, a.wait_ms)
        print(f"OK screenshot: {png} ({a.width}x{a.height})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
