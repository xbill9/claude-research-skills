#!/usr/bin/env python3
"""Embed preset_values.json and Figure 1 into index.src.html -> index.html (single offline file)."""
import base64
import json
import os

here = os.path.dirname(os.path.abspath(__file__))
src = open(os.path.join(here, "index.src.html"), encoding="utf-8").read()
data = json.load(open(os.path.join(here, "preset_values.json")))
# json.dumps output is safe inside <script type="application/json"> once "</" is escaped
payload = json.dumps(data, separators=(",", ":")).replace("</", "<\\/")
fig = base64.b64encode(open(os.path.join(here, "fig1_framework.jpg"), "rb").read()).decode()
out = src.replace("__PRESETS_JSON__", payload).replace("__FIG1__", "data:image/jpeg;base64," + fig)
assert "__PRESETS_JSON__" not in out and "__FIG1__" not in out
open(os.path.join(here, "index.html"), "w", encoding="utf-8").write(out)
print("wrote index.html", len(out.encode()), "bytes")
