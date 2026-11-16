---
title: "Auditing a Technical Article with Claude Code Research Skills"
published: false
description: "Run the research-kit Claude Code plugin on a published article, then hand its audit to the publishing kit so any number the audit disputes fails the build until it is fixed or explained."
tags: claudecode, ai, writing, devtools
cover_image: https://raw.githubusercontent.com/xbill9/claude-research-skills/main/articles/research-kit-publishing-kit/devto-cover.79ffb8a1.jpg
---

This article provides a step by step guide to running the research-kit Claude Code plugin on a published technical article, and to handing its audit to the publishing kit. The research skills recompute every number the article states. The publishing kit then fails the build on any number the audit disputes, until the article fixes it or the ledger explains it.

Repository: https://github.com/xbill9/claude-research-skills

Worked example: https://github.com/xbill9/claude-research-skills/tree/main/examples/publishing-kit-article

---

#### What Is research-kit?

research-kit is a Claude Code plugin with nine skills for research-paper engineering. It is a port of Robina Mirbahar's Antigravity research kit. Each skill reads a paper and either checks it or builds something from it.

| Skill | What it does |
| --- | --- |
| `math-sandbox` | Recomputes each quantitative claim in code and records a verdict |
| `ablation-stat-auditor` | Recomputes rates, intervals and significance tests |
| `citation-doi-verifier` | Checks every reference against Crossref, OpenAlex and arXiv |
| `figure-forensics` | Annotates the figures and checks what they show |
| `interactive-paper-studio` | Builds an offline page with sliders over the paper's model |
| `graphic-story` | Draws a comic of the paper; every number must come from it |
| `paper-number-check` | Fails any output that repeats a number the audit disputes |

The plugin also has `trajectory-cinematics` and `frontier-gap-radar`. They need a system that changes over time and a research literature to survey, so this run leaves them out.

---

#### Why Run It on an Article?

A paper and a technical article make the same kind of promise: every number came from somewhere. The research skills test that promise by recomputing each number in code and writing a verdict beside it: `VERIFIED`, `MISMATCH` or `NOT CHECKABLE`.

The article audited here is the publishing kit's own walk-through, *Streamline Publishing with a Claude Code Skill*. It ships with an `evidence/` directory and a `CLAIMS.md` ledger, so every skill has something to check against.

---

#### At This Point You Should Have

- Claude Code
- `python3` with `pymupdf` and `pillow`, and Chrome, Edge or Chromium for the PDF skills
- The publishing kit at 0.36.0 or later, for `check-facts.py`
- An article with its evidence files beside it

---

#### Step 1 — Install research-kit

The repository is a plugin marketplace. Add it, then install the plugin:

```bash
claude plugin marketplace add xbill9/claude-research-skills
claude plugin install research-kit@claude-research-skills
```

```plaintext
  ❯ research-kit@claude-research-skills
    Version: 1.3.1
    Scope: user
    Status: ✔ enabled
```

Inside a session, each skill is namespaced, for example `/research-kit:math-sandbox`.

---

#### Step 2 — Hand It the Article

Copy the article and its evidence into a folder of its own, so every skill reads the same files and writes beside them:

```bash
mkdir -p examples/publishing-kit-article
cp -r ~/publishing-kit/articles/publishing-kit-skill examples/publishing-kit-article/paper
```

Each skill then gets its own output folder next to `paper/`. In the worked example each skill ran as a separate agent given only its `SKILL.md`, the paper and that folder.

---

#### Step 3 — Check the Arithmetic

`math-sandbox` pulls every quantitative claim out of the article and its evidence, recomputes it, and writes `eq_verified_numbers.json`:

```plaintext
math-sandbox claims: 26 {'VERIFIED': 15, 'NOT CHECKABLE': 5, 'MISMATCH': 6}
crop: ratio 1000/420 = 2.380952 ; rows kept at width 1376 = 577.92 ; lost per side from 768 = 95.04
```

The article says dev.to shows covers through a 2.381:1 crop, so a 1376x768 cover loses 95px off the top and bottom. The arithmetic holds.

The 95px loss assumes a centre crop. The proxy URL in the evidence says `gravity=auto`, so the split between top and bottom is unmeasured.

---

#### Step 4 — Check the Counts

`ablation-stat-auditor` recomputes every count as a rate with a 95% Wilson interval, and runs the matching significance test where two counts are compared:

```plaintext
ablation-stat-auditor claim records: 16 {'VERIFIED': 7, 'MISMATCH': 6, 'NOT CHECKABLE': 3}
tests: {'medium_hosted_vs_embed_fisher_unpaired': (0.02857142857142857, None, None), 'medium_hosted_vs_embed_mcnemar_paired': (0.125, 4, 0), ...}
```

The article's headline figure, 47 of 62 paragraphs with a stray break on dev.to, matches its evidence file: 75.8%, with a 95% interval of 63.8% to 84.8%. The same sentence in the article said "a stray break in every paragraph", and 15 of the 62 had none.

The Medium figure, 0 of 4 images surviving a paste against 4 of 4, is a paired comparison of the same four images. The paired test gives p = 0.125. With all-or-none results it first drops below 0.05 at six images. The claim describes fixed editor behaviour, so what supports it is one archived paste, and the ledger carries it from a log dated 2026-08-30 with no artifact.

---

#### Step 5 — Check the Figures

`figure-forensics` opens every image, measures it, and annotates it into a PDF. The measurements:

```plaintext
image cover.77acc7c4.jpg 1376x578
image cover.ae4d639e.jpg 1376x578
image advocu-devto-publishing-kit-cover.webp 1376x578
image cover-builder.cabd79f3.jpg 1200x675
```

Every dev.to cover the kit made is 1376x578, which the 2.381:1 crop leaves whole. The article's 1376x768 example describes a size the kit does not ship.

The article also said "the two numbers on the cover are real". Both covers carry no numbers, and the current one has no text at all and five destination shapes, while the article describes four destinations.

---

#### Step 6 — Check the Links

`citation-doi-verifier` looks every reference up in Crossref, OpenAlex and arXiv. The article cites no scholarly work:

```plaintext
citation dois/arxiv in paper text: 0
citation links: 10 of 11 resolving and identified
```

Each of the 11 links was fetched instead and matched to a second source: the GitHub API for the repository, the dev.to API for the article copies, and a byte comparison for the cover. Medium answers scripts with HTTP 403, so its copy needs a check in a browser.

---

#### Step 7 — Build the Studio and the Comic

`interactive-paper-studio` builds a single offline `index.html` with sliders for cover size, type size, feed-card width and wrap column. The page's JavaScript model is checked value by value against a Python model:

```plaintext
studio check: 130 values, 0 mismatches, worst abs error 0.00e+0
```

The sliders show one more finding. A comment in the kit's `make-cover.py` said type below about 40pt disappears in a 320px feed card. Its own threshold is `LEGIBLE_PX = 10` pixels, and on a 1376-wide cover that is 43pt, which the comment now says:

```plaintext
legibility: LEGIBLE_PX*1376/CARD_W = 43.0 ; 40pt at 320/1376 = 9.3 px
```

`graphic-story` draws a 5-page comic of the article. Its build fails on any number that is missing from its sourced numbers file.

---

#### Step 8 — Feed the Audit to check-facts

This is where the two kits meet. The publishing kit's `check-facts.py` reads any JSON object with `paper_value`, `computed` and `verdict` as an audit record. Pass the two audit files as evidence:

```bash
check-facts.py paper/devto-publishing-kit.md \
  --evidence math-sandbox/eq_verified_numbers.json ablation-stat-auditor/stat_audit.json
```

```plaintext
  DISPUTED count     0 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
  ok    dimensions   1376x768                     <- eq_verified_numbers.json
  DISPUTED ratio     2.381:1                      <- MISMATCH in eq_verified_numbers.json (M5_substack_source_shape)
  DISPUTED pixels    320px                        <- NOT CHECKABLE in eq_verified_numbers.json (D3_card_width_is_devto)
  DISPUTED count     4 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
  ok    count        47 of 62                     <- eq_verified_numbers.json
  DISPUTED pixels    95px                         <- NOT CHECKABLE in eq_verified_numbers.json (M1_own_source_95_columns)

2 traced, 0 cited from the log, 0 untraced, 5 disputed
```

It exits 1. Both `ok` lines and all five `DISPUTED` lines match a number in the same audit files; the verdict on each record decides which is which.

---

#### Step 9 — Fix the Article, Then Explain What Stays

Each disputed number is either fixed in the article or kept with its reason. The fixes, all in the publishing kit's walk-through:

| Was | Now |
| --- | --- |
| a stray break in every paragraph | in most paragraphs |
| a 1376x768 cover loses 95px | would lose 95px; the kit renders dev.to covers at 1376x578 |
| The two numbers on the cover are real | These two numbers are real |
| measured on 2026-08-31 | measured between 2026-08-30 and 2026-09-16 |
| readable at 95 columns | keeps its line wrapping |

What stays goes under `## DISPUTED` in the article's `CLAIMS.md`, one row per claim with the reason:

```plaintext
| 0 of 4 | E3_medium_data_uri_0_of_4, NOT CHECKABLE | no archived artifact; the article labels it "kit log, 2026-08-30" |
| 320px | D3_card_width_is_devto, NOT CHECKABLE | `CARD_W` in make-cover.py; no archived measurement of dev.to's card width |
```

The same run against the corrected article:

```plaintext
  NOTED count        0 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json, caveat in CLAIMS.md
  ok    dimensions   1376x578                     <- eq_verified_numbers.json
  ok    count        47 of 62                     <- eq_verified_numbers.json

3 traced, 0 cited from the log, 0 untraced, 0 disputed, 5 disputed with a caveat
```

It exits 0.

---

#### Step 10 — Check Everything Built From the Article

The studio page and the comic repeat numbers too. `paper-number-check` runs `check-facts.py` over every output at once, after first proving the copy it found flags a known disputed number:

```bash
python3 check_outputs.py --audit math-sandbox/eq_verified_numbers.json ablation-stat-auditor/stat_audit.json \
  -- interactive-paper-studio/index.html graphic-story/Story.html
```

```plaintext
interactive-paper-studio/index.html: 0 disputed, 11 noted, 5 traced, 30 untraced
graphic-story/Story.html: 0 disputed, 9 noted, 7 traced, 20 untraced

0 disputed claim(s) across 2 output(s)
```

Each noted number has a row in a `CLAIMS.md` beside its output.

---

#### 🔎 Tip: Read the Record Behind Each Disputed Number

Two of the five disputed claims in Step 8 are number collisions. `2.381:1` matched the digit 1 in a record of code-block line counts, and `95px` matched a record about a 95-column source wrap. The crop ratio itself is `VERIFIED` in another record.

Open the record named after each `DISPUTED` line before changing the article. A record that stores a whole table in `paper_value` matches every small number it contains. On an HTML page the check also reads the stylesheet, so `1px` and `4px` can match.

---

#### 🔎 Tip: Keep the Old Claim Visible

The publishing kit writes a reversal as a **Correction** paragraph that keeps the retracted claim in view. The fixes in Step 9 went into the ledger as a table of was, now and evidence, so a reader of the repository can see what changed and why.

---

#### Compare and Contrast

| Skill | Fit for a technical article | What it found here |
| --- | --- | --- |
| `math-sandbox` | 🥇 every quantitative claim | 6 mismatches, 5 not checkable |
| `ablation-stat-auditor` | 🥇 any count or rate | an overstatement and an unsupported comparison |
| `figure-forensics` | 🥈 covers and diagrams | a cover size the kit does not ship |
| `paper-number-check` | 🥈 anything built from the article | 0 disputed after the ledger rows |
| `citation-doi-verifier` | 🥉 links only | 10 of 11 links confirmed |
| `interactive-paper-studio` | 🥉 when the article has a model | a threshold its own comment misstates |

---

#### So, Which One?

Start with `math-sandbox` and `ablation-stat-auditor`. They write the audit records, and every other step reads them. Then run `check-facts.py` with those records as evidence before every publish, and `paper-number-check` over anything else built from the article.

---

#### Summary

The goal of this article was to check every number in a published technical article and stop the disputed ones from shipping again. The key to the solution was a verdict beside every recomputed number, read by the publishing kit's `check-facts.py`. The results on the publishing kit's walk-through were:

- 🟢 26 claims recomputed: 15 verified, 6 mismatches, 5 not checkable
- 🟢 47 of 62 matches its evidence: 75.8%, 95% interval 63.8% to 84.8%
- ❌ "every paragraph", "on the cover" and the footer date overstated their evidence; all three fixed
- ⚠️ 0 of 4 against 4 of 4 on Medium has no archived artifact; kept with its caveat
- 🟢 check-facts went from 5 disputed to 0, with 5 explained in the ledger

Scope: one article, audited on 2026-11-16 with research-kit 1.3.1 and the publishing kit's `check-facts.py` from 0.36.0. Each skill ran once, as a separate agent. The comic run stopped before its final page review. Live pages were fetched only by the link check.

The strategy for auditing a technical article with Claude Code research skills was validated with an incremental step by step approach.

#### References

- [research-kit on GitHub](https://github.com/xbill9/claude-research-skills)
- [The worked example](https://github.com/xbill9/claude-research-skills/tree/main/examples/publishing-kit-article)
- [publishing-kit on GitHub](https://github.com/xbill9/publishing-kit)
- [The audited article](https://dev.to/gde/streamline-publishing-with-a-claude-code-skill-1bdn)
- [Robina Mirbahar's Antigravity research kit](https://github.com/RobinaMirbahar/My-antigravity-research-skills)
- [Claude Code plugins](https://docs.claude.com/en/docs/claude-code/plugins)
