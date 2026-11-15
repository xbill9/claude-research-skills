# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Stdio MCP server for the research-kit Claude Code plugin.

Standard library only: no numpy, no scipy, nothing to install.

Tools
-----
verify_wilson_ci          Wilson score interval for k successes out of n.
verify_fisher_exact       Two-sided Fisher's exact test on a 2x2 table (method vs baseline).
verify_mcnemar_exact      Exact (binomial) McNemar test for two systems on the same tasks.
leaderboard_noise_floor   Standard error, 95% CI half-width and minimum detectable lift on N tasks.
verify_doi_metadata       Crossref lookup of one DOI: title, authors, year, venue, preprint relations.
search_crossref_by_title  Crossref title search, each candidate scored for title similarity in code.

Every number is computed here so the model quotes it instead of estimating it.
Ported from agy-research-kit by Robina Mirbahar (MIT).
"""

from __future__ import annotations

import difflib
import json
import math
import os
import re
import sys
import unicodedata
import urllib.parse
import urllib.request
from fractions import Fraction
from statistics import NormalDist

SERVER_NAME = "research-audit"
SERVER_VERSION = "1.0.0"
SUPPORTED_PROTOCOLS = ("2025-06-18", "2025-03-26", "2024-11-05")
CROSSREF = "https://api.crossref.org/works"
HTTP_TIMEOUT = 10

TOOLS = [
    {
        "name": "verify_wilson_ci",
        "description": "Wilson score confidence interval for k successes out of n tasks. "
        "Use instead of the normal approximation, which fails near 0%, 100% and at small n.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "successes": {"type": "integer", "minimum": 0, "description": "Solved or passed tasks (k)"},
                "total": {"type": "integer", "minimum": 1, "description": "Total tasks (n)"},
                "confidence": {"type": "number", "default": 0.95, "description": "Confidence level in (0, 1)"},
            },
            "required": ["successes", "total"],
        },
    },
    {
        "name": "verify_fisher_exact",
        "description": "Two-sided Fisher's exact test comparing method (k_method of n_method) with "
        "baseline (k_baseline of n_baseline) on INDEPENDENT task sets. For two systems run on the "
        "same tasks, use verify_mcnemar_exact.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "k_method": {"type": "integer", "minimum": 0},
                "n_method": {"type": "integer", "minimum": 1},
                "k_baseline": {"type": "integer", "minimum": 0},
                "n_baseline": {"type": "integer", "minimum": 1},
            },
            "required": ["k_method", "n_method", "k_baseline", "n_baseline"],
        },
    },
    {
        "name": "verify_mcnemar_exact",
        "description": "Exact McNemar test for two systems evaluated on the SAME tasks. "
        "b = tasks only the method solves, c = tasks only the baseline solves.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "b": {"type": "integer", "minimum": 0, "description": "Method right, baseline wrong"},
                "c": {"type": "integer", "minimum": 0, "description": "Method wrong, baseline right"},
            },
            "required": ["b", "c"],
        },
    },
    {
        "name": "leaderboard_noise_floor",
        "description": "Standard error, 95% CI half-width and the minimum detectable lift (two-sided "
        "alpha, given power) on an N-task benchmark at a baseline success rate.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "num_tasks": {"type": "integer", "minimum": 1, "description": "Benchmark instances (N)"},
                "baseline_rate": {"type": "number", "default": 0.25, "description": "Baseline accuracy in [0, 1]"},
                "alpha": {"type": "number", "default": 0.05},
                "power": {"type": "number", "default": 0.80},
            },
            "required": ["num_tasks"],
        },
    },
    {
        "name": "verify_doi_metadata",
        "description": "Look up one DOI in Crossref. Returns verified=false when Crossref has no record. "
        "Includes preprint relations (is-preprint-of / has-preprint) for upgrade checks.",
        "inputSchema": {
            "type": "object",
            "properties": {"doi": {"type": "string", "description": "DOI, bare or as a doi.org URL"}},
            "required": ["doi"],
        },
    },
    {
        "name": "search_crossref_by_title",
        "description": "Search Crossref for a reference by title (optionally first-author surname and year). "
        "Each candidate carries title_similarity in [0, 1], computed on normalised titles; treat >= 0.90 "
        "with a matching surname and year as a match.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "title": {"type": "string"},
                "author": {"type": "string", "description": "First author surname (optional)"},
                "year": {"type": "integer", "description": "Publication year (optional)"},
                "rows": {"type": "integer", "default": 5, "minimum": 1, "maximum": 20, "description": "Candidates returned (20 are fetched and re-ranked)"},
            },
            "required": ["title"],
        },
    },
]


class ToolError(ValueError):
    """Bad arguments: reported to the model as a tool error, not a protocol error."""


# ---------------------------------------------------------------- statistics


def wilson_ci(k: int, n: int, conf: float = 0.95) -> dict:
    if n < 1 or not 0 <= k <= n:
        raise ToolError(f"need 0 <= successes <= total and total >= 1, got {k}/{n}")
    if not 0 < conf < 1:
        raise ToolError(f"confidence must be in (0, 1), got {conf}")
    z = NormalDist().inv_cdf(1 - (1 - conf) / 2)
    p = k / n
    denom = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denom
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denom
    lo, hi = max(0.0, center - half), min(1.0, center + half)
    pct = round(conf * 100, 4)
    return {
        "successes": k,
        "total": n,
        "rate_pct": round(p * 100, 2),
        "wilson_low_pct": round(lo * 100, 2),
        "wilson_high_pct": round(hi * 100, 2),
        "z": round(z, 6),
        "formatted": f"{p * 100:.1f}% ({pct:g}% Wilson CI [{lo * 100:.1f}%, {hi * 100:.1f}%])",
    }


def fisher_exact(k1: int, n1: int, k2: int, n2: int) -> dict:
    for k, n, label in ((k1, n1, "method"), (k2, n2, "baseline")):
        if n < 1 or not 0 <= k <= n:
            raise ToolError(f"{label}: need 0 <= k <= n and n >= 1, got {k}/{n}")
    total, succ = n1 + n2, k1 + k2
    lo, hi = max(0, n1 - (total - succ)), min(n1, succ)
    denom = math.comb(total, n1)
    pmf = {x: Fraction(math.comb(succ, x) * math.comb(total - succ, n1 - x), denom) for x in range(lo, hi + 1)}
    observed = pmf[k1]
    # Same tie tolerance as scipy.stats.fisher_exact: tables as or less likely than the observed one.
    cutoff = observed * Fraction(10**7 + 1, 10**7)
    p_value = float(min(Fraction(1), sum(v for v in pmf.values() if v <= cutoff)))
    a, b, c, d = k1, n1 - k1, k2, n2 - k2
    if b * c == 0:
        odds = "undefined" if a * d == 0 else "inf"
    else:
        odds = round(a * d / (b * c), 6)
    return {
        "method": f"{k1}/{n1}",
        "baseline": f"{k2}/{n2}",
        "method_rate_pct": round(k1 / n1 * 100, 2),
        "baseline_rate_pct": round(k2 / n2 * 100, 2),
        "difference_pts": round((k1 / n1 - k2 / n2) * 100, 2),
        "odds_ratio": odds,
        "p_value": p_value,
        "significant_at_0_05": p_value < 0.05,
        "significant_at_0_01": p_value < 0.01,
    }


def mcnemar_exact(b: int, c: int) -> dict:
    if b < 0 or c < 0:
        raise ToolError("b and c must be non-negative")
    m = b + c
    if m == 0:
        p_value = 1.0
    else:
        tail = sum(Fraction(math.comb(m, i), 2**m) for i in range(min(b, c) + 1))
        p_value = float(min(Fraction(1), 2 * tail))
    return {
        "b_method_only": b,
        "c_baseline_only": c,
        "discordant": m,
        "p_value": p_value,
        "significant_at_0_05": p_value < 0.05,
        "significant_at_0_01": p_value < 0.01,
    }


def noise_floor(n: int, p: float = 0.25, alpha: float = 0.05, power: float = 0.80) -> dict:
    if n < 1:
        raise ToolError("num_tasks must be >= 1")
    if not 0 <= p <= 1 or not 0 < alpha < 1 or not 0 < power < 1:
        raise ToolError("baseline_rate in [0, 1]; alpha and power in (0, 1)")
    nd = NormalDist()
    z_a, z_b = nd.inv_cdf(1 - alpha / 2), nd.inv_cdf(power)
    se = math.sqrt(p * (1 - p) / n)
    return {
        "num_tasks": n,
        "baseline_rate_pct": round(p * 100, 2),
        "std_error_pct": round(se * 100, 2),
        "ci_95_half_width_pct": round(nd.inv_cdf(0.975) * se * 100, 2),
        "multiplier_z_alpha_plus_z_power": round(z_a + z_b, 4),
        # Lift against a fixed, known baseline rate (the original kit's definition).
        "min_detectable_lift_vs_fixed_baseline_pts": round((z_a + z_b) * se * 100, 2),
        # Lift between two independently measured runs of N tasks each.
        "min_detectable_lift_two_runs_pts": round((z_a + z_b) * math.sqrt(2) * se * 100, 2),
    }


# ---------------------------------------------------------------- Crossref


def _http_json(url: str) -> dict:
    agent = f"research-kit-mcp/{SERVER_VERSION}"
    mailto = os.environ.get("CROSSREF_MAILTO")
    if mailto:  # Crossref's "polite pool"; only sent when the user sets it.
        agent += f" (mailto:{mailto})"
    req = urllib.request.Request(url, headers={"User-Agent": agent, "Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=HTTP_TIMEOUT) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _norm_title(s: str) -> str:
    s = unicodedata.normalize("NFKD", re.sub(r"<[^>]+>", " ", s or "")).encode("ascii", "ignore").decode()
    return " ".join(re.sub(r"[^a-z0-9]+", " ", s.lower()).split())


def _summarise(item: dict) -> dict:
    authors = [
        " ".join(x for x in (a.get("given"), a.get("family")) if x) or a.get("name", "")
        for a in item.get("author", [])
    ]
    issued = (item.get("issued") or {}).get("date-parts") or [[None]]
    rel = item.get("relation") or {}
    return {
        "doi": item.get("DOI"),
        "title": (item.get("title") or [""])[0],
        "authors": authors[:10],
        "first_author_family": (item.get("author") or [{}])[0].get("family"),
        "author_count": len(authors),
        "year": issued[0][0] if issued and issued[0] else None,
        "venue": (item.get("container-title") or [""])[0],
        "type": item.get("type", ""),
        "publisher": item.get("publisher", ""),
        "is_preprint_of": [r.get("id") for r in rel.get("is-preprint-of", [])],
        "has_preprint": [r.get("id") for r in rel.get("has-preprint", [])],
    }


def verify_doi(doi: str) -> dict:
    doi = re.sub(r"^(https?://(dx\.)?doi\.org/|doi:)", "", (doi or "").strip(), flags=re.I)
    if not doi.startswith("10."):
        raise ToolError(f"not a DOI: {doi!r}")
    try:
        data = _http_json(f"{CROSSREF}/{urllib.parse.quote(doi, safe='/')}")["message"]
    except urllib.error.HTTPError as exc:
        return {"verified": False, "doi": doi, "error": f"Crossref HTTP {exc.code}"}
    except Exception as exc:  # network failure: say so, never guess
        return {"verified": False, "doi": doi, "error": f"lookup failed: {exc}"}
    return {"verified": True, **_summarise(data)}


def search_title(title: str, author: str | None = None, year: int | None = None, rows: int = 5) -> dict:
    if not (title or "").strip():
        raise ToolError("title is required")
    rows = max(1, min(20, int(rows)))
    # Crossref's relevance order buries short, generic titles; fetch wide, re-rank by similarity here.
    q = {"query.bibliographic": title, "rows": 20}
    if author:
        q["query.author"] = author
    try:
        items = _http_json(f"{CROSSREF}?{urllib.parse.urlencode(q)}")["message"]["items"]
    except Exception as exc:
        return {"query": title, "error": f"lookup failed: {exc}", "candidates": []}
    want = _norm_title(title)
    out = []
    for it in items:
        c = _summarise(it)
        c["title_similarity"] = round(difflib.SequenceMatcher(None, want, _norm_title(c["title"])).ratio(), 4)
        if author:
            fam = (c["first_author_family"] or "").lower()
            c["first_author_matches"] = bool(fam) and _norm_title(author) == _norm_title(fam)
        if year is not None:
            c["year_matches"] = c["year"] == year
        out.append(c)
    out.sort(key=lambda c: (c["title_similarity"], c.get("first_author_matches", False), c.get("year_matches", False)), reverse=True)
    out = out[:rows]
    best = out[0] if out else None
    return {
        "query": title,
        "candidates": out,
        "best_title_similarity": best["title_similarity"] if best else None,
        "best_is_match": bool(
            best
            and best["title_similarity"] >= 0.90
            and best.get("first_author_matches", True)
            and best.get("year_matches", True)
        ),
    }


# ---------------------------------------------------------------- dispatch


def call_tool(name: str, args: dict) -> dict:
    try:
        if name == "verify_wilson_ci":
            return wilson_ci(int(args["successes"]), int(args["total"]), float(args.get("confidence", 0.95)))
        if name == "verify_fisher_exact":
            return fisher_exact(
                int(args["k_method"]), int(args["n_method"]), int(args["k_baseline"]), int(args["n_baseline"])
            )
        if name == "verify_mcnemar_exact":
            return mcnemar_exact(int(args["b"]), int(args["c"]))
        if name == "leaderboard_noise_floor":
            return noise_floor(
                int(args["num_tasks"]),
                float(args.get("baseline_rate", 0.25)),
                float(args.get("alpha", 0.05)),
                float(args.get("power", 0.80)),
            )
        if name == "verify_doi_metadata":
            return verify_doi(str(args["doi"]))
        if name == "search_crossref_by_title":
            year = args.get("year")
            return search_title(
                str(args["title"]), args.get("author"), int(year) if year is not None else None, args.get("rows", 5)
            )
    except KeyError as exc:
        raise ToolError(f"missing argument: {exc.args[0]}") from None
    except (TypeError, ValueError) as exc:
        if isinstance(exc, ToolError):
            raise
        raise ToolError(f"bad argument: {exc}") from None
    raise ToolError(f"unknown tool: {name}")


def handle(msg: dict) -> dict | None:
    mid, method = msg.get("id"), msg.get("method")
    if mid is None:  # notification (e.g. notifications/initialized): no reply
        return None
    if method == "initialize":
        asked = (msg.get("params") or {}).get("protocolVersion")
        result = {
            "protocolVersion": asked if asked in SUPPORTED_PROTOCOLS else SUPPORTED_PROTOCOLS[0],
            "capabilities": {"tools": {}},
            "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
        }
    elif method == "ping":
        result = {}
    elif method == "tools/list":
        result = {"tools": TOOLS}
    elif method == "tools/call":
        params = msg.get("params") or {}
        try:
            out = call_tool(params.get("name", ""), params.get("arguments") or {})
            result = {"content": [{"type": "text", "text": json.dumps(out, indent=2)}], "isError": False}
        except ToolError as exc:
            result = {"content": [{"type": "text", "text": str(exc)}], "isError": True}
    else:
        return {"jsonrpc": "2.0", "id": mid, "error": {"code": -32601, "message": f"method not found: {method}"}}
    return {"jsonrpc": "2.0", "id": mid, "result": result}


def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            reply = {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"parse error: {exc}"}}
        else:
            reply = handle(msg)
        if reply is not None:
            sys.stdout.write(json.dumps(reply) + "\n")
            sys.stdout.flush()


if __name__ == "__main__":
    main()
