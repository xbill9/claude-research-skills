"""Medium's article page answers scripts with a Cloudflare 403. Check the author's RSS feed instead.

Usage: python3 -I medium_feed.py <outdir>
"""

import json
import pathlib
import re
import sys
import urllib.error
import urllib.request

outdir = pathlib.Path(sys.argv[1])
TARGET = "af03e6658c0b"
out = {}
for name, url in (("feed_user", "https://xbill999.medium.com/feed"), ("feed_at", "https://medium.com/feed/@xbill999")):
    req = urllib.request.Request(url, headers={"User-Agent": "research-kit-citation-verifier/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            body, status = r.read(), r.status
    except urllib.error.HTTPError as e:
        body, status = e.read(), e.code
    (outdir / "raw" / f"medium_{name}.xml").write_bytes(body)
    t = body.decode("utf-8", "replace")
    items = re.findall(r"<item>(.*?)</item>", t, re.S)
    hit = [i for i in items if TARGET in i]
    rec = {"url": url, "status": status, "items": len(items), "target_found": bool(hit)}
    if hit:
        g = lambda tag: (re.search(rf"<{tag}>(?:<!\[CDATA\[)?(.*?)(?:\]\]>)?</{tag}>", hit[0], re.S) or [None, None])[1]
        rec.update(title=g("title"), link=g("link"), pubDate=g("pubDate"), creator=g("dc:creator"))
    out[name] = rec
    print(json.dumps(rec))
(outdir / "raw" / "medium_feed_summary.json").write_text(json.dumps(out, indent=2))
