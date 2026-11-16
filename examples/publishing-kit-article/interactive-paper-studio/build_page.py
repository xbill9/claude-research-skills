#!/usr/bin/env python3
"""Embed preset_values.json into index.src.html -> index.html (single file, no external URLs)."""

import json
import pathlib

HERE = pathlib.Path(__file__).resolve().parent
data = json.loads((HERE / "preset_values.json").read_text())
blob = json.dumps(data, separators=(",", ":"), ensure_ascii=False).replace("</", "<\\/")
html = (HERE / "index.src.html").read_text().replace("__DATA__", blob)
(HERE / "index.html").write_text(html)
print(f"wrote index.html {len(html.encode())} bytes")
