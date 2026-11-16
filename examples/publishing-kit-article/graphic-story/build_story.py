"""Build Story.html: the publishing-kit article as a five-page A4 graphic story.

Every number comes from story_numbers.json through {key} placeholders. The build exits non-zero if:
  - a story string has a digit or a spelled number (two..twenty) typed outside a placeholder;
  - a number-bearing token in the rendered HTML is not in the display strings of used entries;
  - a bubble or caption overlaps a face, board, chart, table or another bubble, a tail crosses one,
    or anything leaves its panel or the page body (Page.check in story_svg_engine.py).

    python3 story_numbers_build.py && python3 build_story.py
"""

from __future__ import annotations

import html as htmlmod
import json
import re
import sys
from pathlib import Path

from story_svg_engine import (C, INK, Page, arrow, blackboard, box, diamond, explorer, gatekeeper, monster, robot,
                              scientist, sergeant, text, text_width)

HERE = Path(__file__).resolve().parent
NUM = json.loads((HERE / "story_numbers.json").read_text(encoding="utf-8"))
USED: dict[str, dict] = {}
WORDS = r"\b(two|three|four|five|six|seven|eight|nine|ten|eleven|twelve|thirteen|fourteen|fifteen|sixteen|" \
        r"seventeen|eighteen|nineteen|twenty|hundred|thousand|dozen)\b"


def V(key: str) -> str:
    e = NUM[key]
    USED[key] = {"display": e["display"], "source": e["source"], **({"caveat": e["caveat"]} if "caveat" in e else {})}
    return e["display"]


def T(s: str) -> str:
    """Fill {key} placeholders. Refuse any number typed into the story by hand."""
    bare = re.sub(r"\{[a-z_0-9]+\}", "", s)
    if re.search(r"\d", bare) or re.search(WORDS, bare, re.I):
        raise SystemExit(f"number typed into story text (use a {{key}}): {s!r}")
    return re.sub(r"\{([a-z_0-9]+)\}", lambda m: V(m.group(1)), s)


def CAV(key: str) -> str:
    V(key)
    return NUM[key]["caveat"]


L, R = 26, 768          # page body left/right
HW = 365                # half panel width
X2 = L + HW + 12        # right column x


def hbar(page, panel, x, y, w, rows, vmax, size=11, label="chart"):
    """Horizontal bars. rows: (label, key, color). Bar length from the numbers file value."""
    out = []
    lw = max(text_width(r[0], size, "bold") for r in rows) + 10
    bar_w = w - lw - 40
    yy = y
    for lab, key, col in rows:
        v = NUM[key]["value"]
        disp = V(key)
        bw = bar_w * v / vmax
        out.append(text(lab, x, yy + 14, size, "bold"))
        out.append(f'<rect x="{x + lw}" y="{yy}" width="{bar_w}" height="20" fill="#eef0f4" stroke="{INK}" stroke-width="1"/>')
        if bw > 0:
            out.append(f'<rect x="{x + lw}" y="{yy}" width="{bw:.1f}" height="20" fill="{col}" stroke="{INK}" stroke-width="1.4"/>')
        out.append(text(disp, x + lw + max(bw, 0) + 5, yy + 15, size + 1, "black"))
        yy += 32
    page.add("chart", (x, y - 2, x + w, yy - 10), label, panel, "".join(out))
    return yy


def table_html(head, rows, cls="tbl", size=11.5):
    th = "".join(f"<th>{htmlmod.escape(h)}</th>" for h in head) if head else ""
    body = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in r) + "</tr>" for r in rows)
    return f'<table class="{cls}" style="font-size:{size}px">' + (f"<thead><tr>{th}</tr></thead>" if th else "") \
        + f"<tbody>{body}</tbody></table>"


# =================================================================================================
def page1():
    p = Page(f"One Article, {T('{dest_count}').title()} Destinations",
             T("The ceremony behind publishing one article to {dest_count} places"),
             "devto-publishing-kit.md, opening and “What it does”.")
    # -- a: the ceremony
    a = p.panel(L, 92, R - L, 300)
    p.caption(a, T("Publishing one technical article to {dest_count} places involves a lot of ceremony."), L + 10, 102, 330)
    au = scientist(L + 40, 200, 1.1, "worried", "shrug")
    p.put(au, a)
    p.bubble(a, "A cover at whatever size each destination wants. Tables rendered to images because Medium's "
                "importer eats them. Emoji stripped for AWS. Every number checked against a real run.",
             L + 180, 152, 250, to=au)
    dests = [("dev.to", C["devto"]), ("AWS Builder Center", C["builder"]), ("Medium", C["medium"]),
             ("LinkedIn", C["linkedin"])]
    for i, (name, col) in enumerate(dests):
        bx, by = 470 + (i % 2) * 145, 112 + (i // 2) * 82
        box(p, a, bx, by, 132, 64, name, fill=col, color="#fff", size=12.5)
    p.bubble(a, "Then a long markdown file into a browser editor with no API, the right organization to route to, "
                "and the announcement post afterwards.",
             L + 180, 300, 330, to=au)
    # -- b: the rigid baseline
    b = p.panel(L, 404, HW, 330)
    sg = sergeant(L + 30, 560, 1.05, "stern", "stand")
    p.put(sg, b)
    for i, lab in enumerate(["dev.to\ncopy", "Builder\ncopy", "Medium\ncopy", "LinkedIn\ncopy"]):
        fx, fy = L + 185 + (i % 2) * 88, 590 + (i // 2) * 62
        box(p, b, fx, fy, 80, 50, lab + "?", fill="#f6efe0", size=10.5)
    p.bubble(b, "Copy. Paste. Edit for this one. Copy again. Which file is the current one?", L + 140, 470, 200, to=sg)
    p.caption(b, T("By hand: {dest_count} slightly different files and no idea which one is current."), L + 10, 414, 330)
    # -- c: the system arrives
    c = p.panel(X2, 404, HW, 330)
    kit = robot(X2 + 230, 560, 1.05, "happy", "wave")
    p.put(kit, c)
    au2 = scientist(X2 + 30, 575, 0.95, "neutral", "think")
    p.put(au2, c)
    p.bubble(c, "A Claude Code skill and a set of small scripts. You just ask Claude to publish.", X2 + 175, 430, 175,
             to=kit)
    p.bubble(c, "Write one markdown file, and you build the rest?", X2 + 15, 470, 150, to=au2)
    # -- d: architecture
    d = p.panel(L, 746, R - L, 331)
    p.caption(d, "One source file becomes every version. The skill decides when each script runs; the scripts do "
                 "the parts a language model should not be doing by hand.", L + 10, 756, 720, size=11)
    box(p, d, L + 20, 880, 120, 70, "article.md (one source)", fill="#fff7dc", size=12)
    outs = [
        ("make-builder.py", "Builder Center: emoji stripped, AWS disclaimer appended", C["builder"]),
        ("make-medium.py", "Medium HTML, every table rendered to a PNG", C["medium"]),
        ("make-linkedin.py", "LinkedIn post", C["linkedin"]),
        ("publish-devto.py", "dev.to draft over the API; front matter is the payload", C["devto"]),
    ]
    for i, (script, dest, col) in enumerate(outs):
        yy = 810 + i * 62
        box(p, d, L + 210, yy, 150, 46, script, fill="#e9f1f8", size=11.5)
        box(p, d, L + 410, yy, 210, 46, dest, fill=col, color="#fff", size=10.5)
        arrow(p, L + 140, 915, L + 208, yy + 23)
        arrow(p, L + 360, yy + 23, L + 408, yy + 23)
    kit2 = robot(L + 632, 880, 0.78, "happy", "point")
    p.put(kit2, d)
    p.bubble(d, "Then I check them all.", L + 625, 820, 100, to=kit2, size=11)
    return p


# =================================================================================================
def page2():
    p = Page("The Mangler", "What the destinations do to your file, each one measured or documented",
             "devto-publishing-kit.md, “What it does” and “Dogfooding”; evidence/devto-hardwrap.txt; "
             "evidence/devto-cover-crop.txt; CLAIMS.md (LOG and DOCUMENTED rows).")
    # -- a: hard breaks
    a = p.panel(L, 92, R - L, 250)
    mg = monster(L + 560, 150, 1.05, "angry", flip=True)
    p.put(mg, a)
    au = scientist(L + 40, 160, 0.95, "surprised", "shrug")
    p.put(au, a)
    p.bubble(a, T("Your source is hard-wrapped? On dev.to I render markdown with hard breaks ON. "
                  "Stray breaks in {hw_blocks} of your {hw_total} blocks!"), L + 330, 104, 220, to=mg)
    p.bubble(a, "It has been happening to my articles for months.", L + 150, 130, 150, to=au)
    p.caption(a, "dev.to", L + 10, 102, 60, fill="#e6e6e6")
    # -- b: hard-wrap chart
    b = p.panel(L, 354, HW, 330)
    p.caption(b, T("Measured on a published article: paragraph-level blocks carrying a stray break"), L + 10, 364, 340)
    hbar(p, b, L + 18, 420, HW - 36, [
        ("all blocks", "hw_total", "#c9d3e3"),
        ("with a stray <br>", "hw_blocks", C["bad"]),
    ], vmax=NUM["hw_total"]["value"], label="hard-wrap bars")
    p.note(b, T("{hw_total} blocks = {hw_p} <p> + {hw_li} <li>. {hw_br} <br> in all, because a block can wrap more "
                "than once. That is {hw_pct} of blocks. Re-measured {hw_date} on the live article."),
           L + 18, 500, HW - 40, size=9.5)
    kit = robot(L + 250, 590, 0.55, "worried", "stand")
    p.put(kit, b)
    p.bubble(b, T("Source lines ending in {two_spaces} spaces: {hw_twospace}. Every break is dev.to's."), L + 18, 600, 215,
             to=kit, size=11)
    # -- c: cover crop
    c = p.panel(X2, 354, HW, 330)
    p.caption(c, T("dev.to proxies the cover at {crop_ratio} instead of hosting it"), X2 + 10, 364, 340)
    cx0, cy0, cw, ch = X2 + 55, 408, 250, 250 * 768 / 1376
    band = ch * 95 / 768
    p.add("chart", (cx0 - 2, cy0 - 2, cx0 + cw + 2, cy0 + ch + 2), "crop diagram", c,
          f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{ch:.1f}" fill="#cfe3f1" stroke="{INK}" stroke-width="2"/>'
          f'<rect x="{cx0}" y="{cy0}" width="{cw}" height="{band:.1f}" fill="{C["bad"]}" fill-opacity="0.75"/>'
          f'<rect x="{cx0}" y="{cy0 + ch - band:.1f}" width="{cw}" height="{band:.1f}" fill="{C["bad"]}" fill-opacity="0.75"/>'
          + text(T("{crop_px} lost off the top"), cx0 + cw / 2, cy0 + band / 2 + 4, 11, "bold", fill="#fff", anchor="middle")
          + text(T("{crop_px} lost off the bottom"), cx0 + cw / 2, cy0 + ch - band / 2 + 4, 11, "bold", fill="#fff",
                 anchor="middle")
          + text(T("{cover_dims} cover"), cx0 + cw / 2, cy0 + ch / 2 + 4, 13, "black", anchor="middle"))
    p.note(c, T("dev.to displays it at {crop_display}, fit=cover, a {crop_ratio} centre crop."),
           X2 + 30, cy0 + ch + 8, 300, size=9.5)
    kit = robot(X2 + 255, 580, 0.55, "happy", "point")
    p.put(kit, c)
    p.bubble(c, T("So the kit renders a {crop_fixed} cover. Nothing gets cropped."), X2 + 20, 600, 220, to=kit, size=11)
    # -- d: Medium data URIs
    d = p.panel(L, 696, HW, 381)
    p.caption(d, "Medium, pasting the self-contained build", L + 10, 706, 340)
    p.svg.append(text(T("as data: URIs, {med_embed_ok} of {med_embed_n} survive"), L + 22, 752, 12, "bold"))
    p.svg.append(text(T("from real URLs, {med_hosted_ok} of {med_embed_n}"), L + 22, 838, 12, "bold"))
    frames = []
    for i in range(4):
        fx = L + 22 + i * 62
        frames.append(f'<rect x="{fx}" y="762" width="52" height="44" fill="#fff" stroke="{C["muted"]}" '
                      f'stroke-width="2" stroke-dasharray="4 3"/>'
                      f'<line x1="{fx + 8}" y1="770" x2="{fx + 44}" y2="798" stroke="{C["bad"]}" stroke-width="2.5"/>'
                      f'<line x1="{fx + 44}" y1="770" x2="{fx + 8}" y2="798" stroke="{C["bad"]}" stroke-width="2.5"/>')
        frames.append(f'<rect x="{fx}" y="848" width="52" height="44" fill="#cfe9da" stroke="{INK}" stroke-width="2"/>'
                      f'<polygon points="{fx + 6},{886} {fx + 22},{864} {fx + 34},{878} {fx + 40},{870} {fx + 48},{886}" '
                      f'fill="{C["good"]}"/><circle cx="{fx + 40}" cy="858" r="4" fill="{C["warn"]}"/>')
    p.add("chart", (L + 20, 740, L + 270, 894), "medium frames", d, "".join(frames))
    mg2 = monster(L + 240, 905, 0.6, "happy")
    p.put(mg2, d)
    p.bubble(d, "Pictures inside the HTML? I drop them on paste.", L + 22, 925, 190, to=mg2, size=11)
    p.note(d, "Paste -hosted.html and commit the images first. " + CAV("med_embed_ok"), L + 18, 1010, 330, size=9.5)
    # -- e: LinkedIn
    e = p.panel(X2, 696, HW, 381)
    p.caption(e, "LinkedIn, the Posts API", X2 + 10, 706, 340)
    mg3 = monster(X2 + 200, 790, 0.75, "angry", flip=True)
    p.put(mg3, e)
    stamp = (f'<g transform="rotate(-10 {X2 + 95} 840)"><rect x="{X2 + 25}" y="815" width="150" height="46" rx="6" '
             f'fill="none" stroke="{C["bad"]}" stroke-width="4"/>'
             + text("PUBLISHED", X2 + 100, 846, 21, "black", fill=C["bad"], anchor="middle") + "</g>")
    p.add("chart", (X2 + 20, 800, X2 + 182, 878), "stamp", e, stamp)
    p.bubble(e, "Drafts? Not here. PUBLISHED is the only state I accept on creation.", X2 + 18, 740, 175, to=mg3, size=11)
    p.bubble(e, "So the kit writes the post and stops. Publishing is your keystroke.", X2 + 18, 905, 160,
             size=11, kind="whisper")
    p.note(e, "Documented in LinkedIn's own developer docs (Posts API, lifecycleState); CLAIMS.md files it as "
              "DOCUMENTED, not measured.", X2 + 18, 1010, 330, size=9.5)
    return p


# =================================================================================================
def page3():
    p = Page("The Gate", "Pre-flight runs the lot and exits non-zero; check-facts names what you assert from memory",
             "devto-publishing-kit.md, “What it does” and “Debugging”; evidence/linkedin-run.txt; "
             "evidence/builder-payload.txt; CLAIMS.md (DOCUMENTED and third-party rows).")
    # -- a: preflight decision
    a = p.panel(L, 92, R - L, 360)
    gk = gatekeeper(L + 30, 250, 1.1, "stern", "stop", lamp="red")
    p.put(gk, a)
    p.bubble(a, "preflight.py --live. Nobody posts until every check passes.", L + 30, 140, 200, to=gk)
    blackboard(p, a, L + 235, 104, 225, 236, [
        "cover committed and matching HEAD",
        "geometry right",
        "front matter complete",
        "no hard-wrapped paragraphs",
        "every published URL fetched and compared byte for byte against your disk",
    ], title="Pre-flight checks", size=11.5, label="preflight board")
    diamond(p, a, L + 545, 190, 150, 110, "every check passes?", size=11.5)
    arrow(p, L + 462, 190, L + 468, 190)
    arrow(p, L + 545, 246, L + 545, 282, color=C["good"])
    box(p, a, L + 480, 286, 130, 46, "post as a draft", fill=C["good"], color="#fff", size=11.5)
    arrow(p, L + 621, 190, L + 640, 190, color=C["bad"])
    box(p, a, L + 642, 150, 92, 80, "exit non-zero and say what failed", fill=C["bad"], color="#fff", size=11)
    p.svg.append(text("yes", L + 553, 272, 11, "bold", fill=C["good"]))
    p.svg.append(text("no", L + 622, 182, 11, "bold", fill=C["bad"]))
    p.note(a, "From “What it looks like in practice”: it stops at draft on every destination and hands back links.",
           L + 235, 418, 490, size=9.5)
    # -- b: check-facts
    b = p.panel(L, 464, HW, 330)
    p.caption(b, "check-facts.py traces every number", L + 10, 474, 340)
    blackboard(p, b, L + 15, 505, 335, 128, [
        T("Every untraced claim is one of {untraced_kinds} things:"),
        "• measured but never archived",
        "• arithmetic that should be labelled as arithmetic",
        "• asserted from memory",
    ], size=11.5, label="facts board")
    kit = robot(L + 255, 640, 0.62, "neutral", "point")
    p.put(kit, b)
    au = scientist(L + 25, 660, 0.66, "worried", "think")
    p.put(au, b)
    p.bubble(b, "And it is always the third one that is wrong.", L + 95, 650, 130, to=au, size=10.5)
    p.note(b, "It cannot tell you a figure is true. It tells you which ones you are asserting from memory.",
           L + 100, 735, 135, size=9)
    # -- c: LinkedIn generator checks
    c = p.panel(X2, 464, HW, 330)
    p.caption(c, "The LinkedIn generator checks its own post", X2 + 10, 474, 340)
    tbl = table_html(["check", "result"], [
        ["post length", f'<b>{T("{li_post}")}</b> chars of {T("{li_limit}")}'],
        ["hook fits the fold", f'<b>{T("{li_hook}")}</b> chars (fold {T("{li_fold}")})'],
        ["links still PENDING", f'<b class="bad">FAIL</b>, {T("{li_pending}")} links'],
        ["markdown left over", "none"],
    ], size=11.5)
    p.html_box(c, X2 + 15, 506, 335, 128, tbl, "linkedin table")
    gk2 = gatekeeper(X2 + 255, 640, 0.6, "stern", "stop", lamp="red")
    p.put(gk2, c)
    p.bubble(c, "One FAIL is enough. The file is readable, and it is not postable.", X2 + 15, 650, 175, to=gk2, size=10.5)
    CAV("li_limit"), CAV("li_fold")
    p.note(c, "The limit and the fold are third-party figures, per CLAIMS.md; LinkedIn documents only "
              "FIELD_LENGTH_TOO_LONG.", X2 + 15, 740, 215, size=9)
    # -- d: the browser route
    d = p.panel(L, 806, R - L, 271)
    p.caption(d, "Builder Center and Medium have no publishing API, so they are Chrome work. The skill knows the route:",
              L + 10, 816, 720, size=11)
    steps = ["payload through window.name", "a checksum on both sides", "an emptiness assertion before the paste",
             "a landmark count after it"]
    for i, s in enumerate(steps):
        bx = L + 20 + i * 145
        box(p, d, bx, 860, 125, 58, s, fill="#e9f1f8", size=11)
        if i:
            arrow(p, bx - 20, 889, bx - 2, 889)
    kit3 = robot(L + 620, 935, 0.8, "happy", "wave")
    p.put(kit3, d)
    p.note(d, T("The payload measured for Builder Center: {payload_chars} characters, {payload_lines_before} lines "
                "before unwrapping and {payload_lines_after} after ({unwrap_removed} hard-wrapped lines joined)."),
           L + 20, 935, 560, size=10.5, style="bold", fill=INK)
    p.bubble(d, "Then I stop at draft and hand you the link.", L + 596, 856, 140, to=kit3, size=11)
    p.note(d, "Source: evidence/builder-payload.txt (serve-body.py payload).", L + 20, 1000, 360, size=9)
    return p


# =================================================================================================
def page4():
    p = Page("Fetch What They Serve", "Debugging a publish that went sideways",
             "devto-publishing-kit.md, “Debugging a publish that went sideways” (check-links.py output quoted "
             "verbatim); evidence/devto-roundtrip.txt.")
    # -- a: sergeant vs scout
    a = p.panel(L, 92, R - L, 300)
    p.caption(a, "The page does not look like the file.", L + 10, 102, 300)
    sg = sergeant(L + 40, 220, 1.05, "stern", "shrug")
    p.put(sg, a)
    sc = explorer(L + 590, 220, 1.05, "happy", "point", flip=True)
    p.put(sc, a)
    p.bubble(a, "I pushed it. The file is there. It is tracked. So the page must be right.", L + 150, 150, 210, to=sg)
    p.bubble(a, "Every one of those checks reasons about local state, and each can pass while the published URL "
                "serves something else. Fetch what the destination serves.", L + 370, 120, 210, to=sc)
    # -- b: verbatim check-links output
    b = p.panel(L, 404, R - L, 236)
    p.caption(b, "check-links.py article.md, output quoted from the article", L + 10, 414, 400)
    out = "\n".join([T("{checklinks_block}"), "  ok    " + T("{checklinks_cover}"),
                     "  ok    " + T("{checklinks_imgcover}"), "  ok    " + T("{checklinks_table}")])
    p.html_box(b, L + 15, 448, 585, 100, f'<pre class="term">{htmlmod.escape(out)}</pre>', "check-links output")
    sc2 = explorer(L + 625, 470, 0.85, "happy", "stand", flip=True)
    p.put(sc2, b)
    p.note(b, T("A FAIL there reads “{http_ok} but the served bytes differ from disk”, usually an image "
                "regenerated after its commit."), L + 15, 562, 520, size=11, style="bold", fill=INK)
    p.note(b, "Untested here: this run quoted the output, it did not re-run check-links.py.", L + 15, 610, 520, size=9)
    # -- c: symptom table
    c = p.panel(L, 652, R - L, 425)
    p.caption(c, "Symptoms and the tool that names them", L + 10, 662, 400)
    rows = [
        ["The paragraphs look ragged", "check-article.py reports hard-wrapped paragraphs with the line number of the "
         "first one; publish-devto.py unwraps on the way out, so the repo copy stays readable."],
        ["An image is missing on Medium", "You pasted -embed.html. Paste -hosted.html, which references real URLs "
         "Medium re-hosts, and commit the images first."],
        ["A number has no artifact behind it", "check-facts.py will name it."],
        ["The page does not look like the file", "check-links.py fetches every published URL and compares bytes "
         "with disk."],
    ]
    p.html_box(c, L + 15, 696, 520, 250, table_html(["symptom", "what the kit does"], rows, size=11.5), "symptom table")
    kit = robot(L + 590, 820, 0.95, "happy", "cheer")
    p.put(kit, c)
    p.bubble(c, "This half surprised the author most. Most of my value ended up here.", L + 560, 700, 165, to=kit, size=11)
    p.note(c, T("Round trip, measured: dev.to stores the front matter inside body_markdown, and {fences_open} of "
                "{fences_open} opening code fences in a stored body carry a language label ({fences_bare} bare)."),
           L + 15, 960, 520, size=10)
    p.note(c, "Source: evidence/devto-roundtrip.txt.", L + 15, 1010, 300, size=9)
    return p


# =================================================================================================
def page5():
    p = Page("Dogfooding", "The kit published the article about itself, and found its own faults",
             "devto-publishing-kit.md, “Dogfooding”, “Install” and closing note; "
             "evidence/devto-hardwrap.txt; evidence/install-is-a-snapshot.txt; CLAIMS.md (LOG rows).")
    # -- a: the cover scoreboard (verbatim table)
    a = p.panel(L, 92, R - L, 300)
    p.caption(a, "The article's dogfooding table, quoted as printed", L + 10, 102, 400)
    rows = [
        ["dev.to, hard-wrapped paragraphs", f'<b>{T("{hw_blocks} of {hw_total}")}</b> in a published article carried '
                                            "a stray break"],
        ["Medium, images pasted as data URIs", f'<b>{T("{med_embed_ok} of {med_embed_n}")}</b> survived; from real '
                                               f'URLs, {T("{med_hosted_ok} of {med_embed_n}")}'],
    ]
    p.html_box(a, L + 15, 136, 500, 108, table_html(["", "as the article reports it"], rows, size=12), "scoreboard")
    p.note(a, T("First row re-measured {hw_date} against the live article (evidence/devto-hardwrap.txt). "
                "Second row: ") + CAV("med_embed_ok") + ".", L + 15, 254, 500, size=9.5)
    au = scientist(L + 600, 220, 1.0, "happy", "wave", flip=True)
    p.put(au, a)
    p.bubble(a, "Both are missing from the destinations' docs. Both are now checks.", L + 545, 112, 190, to=au, size=11)
    # -- b: the five faults
    b = p.panel(L, 404, R - L, 215)
    p.caption(b, T("The run also found {faults} faults in the kit itself"), L + 10, 414, 400)
    blackboard(p, b, L + 15, 448, 520, 158, [
        "• make-medium.py had another project's repo hardcoded as its default image base",
        "• check-article.py passed a cover that was tracked but regenerated",
        "• make-cover.py lost a --tile value beginning with a hyphen to argparse",
        "• " + T("check-facts.py read {localhost} as a version number"),
        "• " + T("unwrap() skipped block quotes, so the article's own TL;DR posted as {tldr_lines} separate "
                      "lines, and the check that should have caught it skipped block quotes too, and agreed"),
    ], size=11.5, label="faults board")
    kit = robot(L + 625, 470, 0.8, "worried", "shrug")
    p.put(kit, b)
    p.bubble(b, "That is the point of eating your own cooking.", L + 545, 414, 135, to=kit, size=10.5)
    # -- c: install snapshot
    c = p.panel(L, 631, HW, 446)
    p.caption(c, "Hacking on the skill itself", L + 10, 641, 340)
    box(p, c, L + 15, 674, 335, 46, "skill-footprint.py --where prints the skill directory; a marketplace install "
        "sits under a version-numbered cache path.", fill="#e9f1f8", size=10.5, style="regular")
    kit2 = robot(L + 20, 770, 0.9, "neutral", "point")
    p.put(kit2, c)
    p.bubble(c, "Installing takes a snapshot, and claude plugin update compares version strings. Edits under the "
                "same version never reach your session.", L + 140, 730, 210, to=kit2, size=11)
    au2 = scientist(L + 235, 870, 0.8, "happy", "stand")
    p.put(au2, c)
    p.bubble(c, "Symlink while you are iterating.", L + 40, 945, 140, to=au2, size=11)
    p.note(c, T("Measured at {snap_version}: a marker written to the worktree copy did not reach the installed copy "
                "(evidence/install-is-a-snapshot.txt)."), L + 15, 1030, 335, size=9)
    # -- d: closing
    d = p.panel(X2, 631, HW, 446)
    p.caption(d, "Before you trust any of it", X2 + 10, 641, 340)
    box(p, d, X2 + 15, 674, 335, 46, "Fetch what each destination serves and compare it with disk, every time.",
        fill="#e9f1f8", size=10.5, style="regular")
    gk = gatekeeper(X2 + 30, 770, 0.9, "happy", "wave", flip=True, lamp="green")
    p.put(gk, d)
    p.bubble(d, T("The article dates these behaviours {measured_on}. Check them again."), X2 + 160, 730,
             185, to=gk, size=11)
    p.note(d, CAV("measured_on") + ".", X2 + 15, 985, 205, size=9)
    sc = explorer(X2 + 235, 870, 0.8, "happy", "stand")
    p.put(sc, d)
    p.bubble(d, "Fetch, compare, re-measure.", X2 + 40, 920, 120, to=sc, size=11)
    p.note(d, "Third-party community project, not affiliated with dev.to, Medium, AWS or LinkedIn.",
           X2 + 15, 1030, 335, size=9)
    return p


# =================================================================================================
CSS = """
@font-face { font-family: 'Lato'; font-weight: 400; src: local('Lato Regular'), local('Lato-Regular'),
  url('file:///usr/share/fonts/truetype/lato/Lato-Regular.ttf'); }
@font-face { font-family: 'Lato'; font-weight: 400; font-style: italic; src: local('Lato Italic'),
  url('file:///usr/share/fonts/truetype/lato/Lato-Italic.ttf'); }
@font-face { font-family: 'Lato'; font-weight: 700; src: local('Lato Bold'), local('Lato-Bold'),
  url('file:///usr/share/fonts/truetype/lato/Lato-Bold.ttf'); }
@font-face { font-family: 'Lato'; font-weight: 900; src: local('Lato Black'), local('Lato-Black'),
  url('file:///usr/share/fonts/truetype/lato/Lato-Black.ttf'); }
@page { size: A4; margin: 0; }
html, body { margin: 0; padding: 0; background: #fbf8f1; }
.page { position: relative; width: 210mm; height: 297mm; overflow: hidden; break-after: page; }
.page:last-child { break-after: auto; }
.pg { position: absolute; left: 0; top: 0; width: 210mm; height: 297mm; }
.hbox { position: absolute; font-family: 'Lato', sans-serif; color: #22252e; overflow: hidden; }
.tbl { border-collapse: collapse; width: 100%; background: #fff; border: 2px solid #22252e; }
.tbl th { background: #22252e; color: #fff; text-align: left; padding: 4px 7px; font-weight: 700; }
.tbl td { border-top: 1px solid #b9c0cc; padding: 4px 7px; vertical-align: top; line-height: 1.25; }
.tbl td:first-child { font-weight: 700; width: 36%; }
.tbl .bad { color: #c6403a; }
.term { margin: 0; background: #0f2230; color: #7ff0c5; font: 12px/1.5 'DejaVu Sans Mono', monospace;
  padding: 10px 12px; border-radius: 6px; height: 100%; box-sizing: border-box; white-space: pre; }
"""

PX_PER_MM = 794 / 210  # page boxes are 794 px wide; .hbox positions are in those px, scaled below


def audit_rendered(doc: str) -> list[str]:
    """Every number-bearing token in the visible text must come from a used entry's display string."""
    body = re.sub(r"<style.*?</style>", "", doc, flags=re.S)
    visible = htmlmod.unescape(re.sub(r"<[^>]+>", " ", body))
    tok = re.compile(r"[\w./:,~%+<>-]*\d[\w./:,~%+<>-]*")

    def toks(s):
        return {t.strip(".,:;()") for t in tok.findall(s)}

    allowed = set()
    for k in USED:
        allowed |= toks(str(NUM[k]["display"])) | toks(NUM[k].get("caveat", ""))
    errs = [f"number {t!r} in the rendered story is not in story_numbers.json displays" for t in sorted(toks(visible))
            if t not in allowed]
    words = {w.lower() for w in re.findall(WORDS, visible, re.I)}
    allowed_words = {str(NUM[k]["display"]).lower() for k in USED}
    errs += [f"spelled number {w!r} not from story_numbers.json" for w in sorted(words - allowed_words)]
    flat = re.sub(r"\s+", " ", visible).lower()
    for ph in NUM.get("_audit_phrases", []):
        if ph["phrase"].lower() in flat:
            errs.append(f"phrase {ph['phrase']!r} is disputed ({ph['record']}): {ph['why']}")
    for k in USED:
        if NUM[k].get("disputed") and NUM[k]["caveat"].lower() not in flat:
            errs.append(f"{k!r} is disputed by the audit and its caveat is not printed on the page")
    return errs


def main() -> int:
    pages = [page1(), page2(), page3(), page4(), page5()]
    errs = []
    for i, pg in enumerate(pages, 1):
        errs += [f"page {i}: {e}" for e in pg.check()]
    body = "".join(pg.render() for pg in pages)
    # .hbox coordinates are page px; the section is 210mm wide = 794 px at 96 dpi, so they line up.
    doc = (f"<!doctype html><html><head><meta charset='utf-8'><title>Publishing Kit Graphic Story</title>"
           f"<style>{CSS}</style></head><body>{body}</body></html>")
    errs += audit_rendered(doc)
    (HERE / "Story.html").write_text(doc, encoding="utf-8")
    (HERE / "story_numbers_used.json").write_text(json.dumps(dict(sorted(USED.items())), indent=1, ensure_ascii=False)
                                                  + "\n", encoding="utf-8")
    print(f"Story.html: {len(pages)} pages, {len(USED)} numbers used from story_numbers.json")
    for e in errs:
        print("ERROR", e)
    return 1 if errs else 0


if __name__ == "__main__":
    sys.exit(main())
