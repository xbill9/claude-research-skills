---
title: "Auditing a Technical Article with Claude Code Research Skills"
published: false
description: "Run the research-kit Claude Code plugin on a published article, then hand its audit to the publishing kit so any number the audit disputes fails the build until it is fixed or explained."
tags: claudecode, ai, writing, devtools
cover_image: https://raw.githubusercontent.com/xbill9/claude-research-skills/main/articles/research-kit-publishing-kit/devto-cover.79ffb8a1.jpg
---

This article provides a step by step guide to running the research-kit Claude Code plugin on a published technical article, and to handing its audit to the publishing kit. The research skills recompute the numbers the article states and mark the ones they cannot check. The publishing kit then fails the build on any number the audit disputes, until the article fixes it or the ledger explains it.

Repository: https://github.com/xbill9/claude-research-skills

Worked example: https://github.com/xbill9/claude-research-skills/tree/main/examples/publishing-kit-article

Publishing kit: https://github.com/xbill9/publishing-kit

---

#### What Is research-kit?

research-kit is a Claude Code plugin with nine skills for research-paper engineering. It is a port of Robina Mirbahar's Antigravity research kit. Each skill reads a paper and either checks it or builds something from it.

| Skill | What it does |
| --- | --- |
| `math-sandbox` | Recomputes quantitative claims in code and records a verdict on each |
| `ablation-stat-auditor` | Recomputes rates, intervals and significance tests |
| `citation-doi-verifier` | Checks every reference against Crossref, OpenAlex and arXiv |
| `figure-forensics` | Annotates the figures and checks what they show |
| `interactive-paper-studio` | Builds an offline page with sliders over the paper's model |
| `graphic-story` | Draws a comic of the paper; every number must come from it |
| `paper-number-check` | Fails any output that repeats a number the audit disputes, unless the ledger explains it |

The plugin also has `trajectory-cinematics` and `frontier-gap-radar`. They need a system that changes over time and a research literature to survey, so this run leaves them out.

---

#### What Is the Publishing Kit?

The publishing kit is a Claude Code skill that turns one markdown article into dev.to, AWS Builder Center, Medium, Substack and LinkedIn versions. Before anything ships, `preflight.py` runs its checks, the link check only with `--live`, and exits non-zero on a failure. One of those checks is `check-facts.py`, which pulls the numbers that look like claims (counts, sizes, ratios, versions, p-values) out of the article's prose and looks for each one in the article's `evidence/` folder.

---

#### How the Two Kits Work Together

research-kit produces the verdicts and the publishing kit enforces them. The hand-off is two JSON files and one folder:

| Stage | Kit | What happens |
| --- | --- | --- |
| Audit | research-kit | `math-sandbox` and `ablation-stat-auditor` write `eq_verified_numbers.json` and `stat_audit.json` |
| Stage | you | copy both files into the article's `evidence/` folder |
| Check | publishing kit | `preflight.py` runs `check-facts.py`, which reads every record with `paper_value`, `computed` and `verdict` |
| Fix | you | reword the article, or keep the number with a row under `## DISPUTED` in `CLAIMS.md` |
| Publish | publishing kit | `publish-devto.py --create` runs the same number check again, then posts the draft |
| Re-check | research-kit | `paper-number-check` runs the publishing kit's `check-facts.py` over every other output |

A number that appears in the evidence normally passes. An audit record holds the article's own number next to the recomputed one, so the verdict decides: `MISMATCH` or `NOT CHECKABLE` fails as `DISPUTED`.

---

#### Why Run It on an Article?

A paper and a technical article make the same kind of promise: every number came from somewhere. The research skills test that promise by recomputing each number in code and writing a verdict beside it: `VERIFIED`, `MISMATCH` or `NOT CHECKABLE`.

The article audited here is the publishing kit's own walk-through, *Streamline Publishing with a Claude Code Skill*. It ships with an `evidence/` directory and a `CLAIMS.md` ledger, so every skill has something to check against.

---

#### At This Point You Should Have

- Claude Code
- `python3` with `pymupdf` and `pillow`, and Chrome, Edge or Chromium for the PDF skills
- An article in a git repository, with an `evidence/` folder beside it

---

#### Step 1 — Install Both Plugins

Both repositories are plugin marketplaces. Add each one, then install its plugin:

```bash
claude plugin marketplace add xbill9/claude-research-skills
claude plugin install research-kit@claude-research-skills
claude plugin marketplace add xbill9/publishing-kit
claude plugin install publishing@publishing-kit
```

```plaintext
  ❯ publishing@publishing-kit
    Version: 0.36.2
    Scope: user
    Status: ✔ enabled
--
  ❯ research-kit@claude-research-skills
    Version: 1.3.1
    Scope: user
    Status: ✔ enabled
```

The publishing kit needs 0.36.0 or later to read audit records, 0.36.1 to stop a single shared number from counting as a match, and 0.36.2 for `publish-devto.py` to run the number check. Its scripts live under a version-numbered path, and older versions stay in the cache, so take the path from the installed plugin:

```bash
KIT=$(claude plugin list --json | python3 -c "import json,sys; print(next(p['installPath'] for p in json.load(sys.stdin) if p['id']=='publishing@publishing-kit'))")/skills/publishing
echo $KIT
```

```plaintext
/home/xbill/.claude/plugins/cache/publishing-kit/publishing/0.36.2/skills/publishing
```

From a clone it is `publishing-kit/skills/publishing`.

---

#### Step 2 — Lay Out the Article Folder

The publishing kit reads everything relative to the article. The audit records go in `evidence/`, and the ledger sits beside the article, outside it:

```plaintext
articles/publishing-kit-skill/
├── devto-publishing-kit.md        the article
├── CLAIMS.md                      the ledger: ## DISPUTED rows live here
└── evidence/                      preflight.py reads this folder
    ├── devto-hardwrap.txt         run output the article cites
    ├── eq_verified_numbers.json   staged from math-sandbox
    └── stat_audit.json            staged from ablation-stat-auditor
```

`check-facts.py` refuses a ledger inside `evidence/`, because a ledger restates every number and would trace them all to itself.

For the audits, copy the article folder somewhere the skills can write beside it:

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
...
crop: ratio 1000/420 = 2.380952 ; rows kept at width 1376 = 577.92 ; lost per side from 768 = 95.04
```

The article says dev.to shows covers through a 2.381:1 crop, so a 1376x768 cover loses 95px off the top and bottom. The arithmetic holds.

The 95px loss assumes a centre crop. The proxy URL in the evidence says `gravity=auto`, so the split between top and bottom is unmeasured.

---

#### Step 4 — Check the Counts

`ablation-stat-auditor` recomputes every count as a rate with a 95% Wilson interval, and runs the matching significance test where two counts are compared:

```plaintext
ablation-stat-auditor claim records: 16 {'VERIFIED': 7, 'MISMATCH': 6, 'NOT CHECKABLE': 3}
...
tests: {'medium_hosted_vs_embed_fisher_unpaired': (0.02857142857142857, None, None), 'medium_hosted_vs_embed_mcnemar_paired': (0.125, 4, 0), ...}
```

The article's headline figure, 47 of 62 paragraphs with a stray break on dev.to, matches its evidence file: 75.8%, with a 95% interval of 63.8% to 84.8%. Elsewhere the article said "a stray break in every paragraph", and 15 of the 62 had none.

The Medium figure, 0 of 4 images surviving a paste against 4 of 4, compares two pastes. If the same four images went into both, the paired test gives p = 0.125, and with all-or-none results it first drops below 0.05 at six images; treated as two separate samples, Fisher's test gives p = 0.0286. The evidence does not record which images were pasted. If the editor behaves the same way every time, one archived paste would support the claim, and the ledger carries it from a log dated 2026-08-30 with no artifact.

---

#### Step 5 — Check the Figures

`figure-forensics` opens every image, measures it, and annotates it into a PDF. The measurements:

```plaintext
image cover-builder.80aa6ca5.jpg 1200x675
image cover-builder.cabd79f3.jpg 1200x675
image cover.77acc7c4.jpg 1376x578
image cover.ae4d639e.jpg 1376x578
image linkedin-devto-publishing-kit-cover.jpg 1200x627
image advocu-devto-publishing-kit-cover.webp 1376x578
```

Every dev.to cover in the article's directory is 1376x578, which the 2.381:1 crop leaves whole. The kit made 1376x768 covers before `--mode devto` changed, so the article's example describes those older covers, and its sentence now says so.

The article also said "the two numbers on the cover are real". Both covers carry no numbers. On the current one figure-forensics counts five destination shapes and no text, while the article describes four destinations.

---

#### Step 6 — Check the Links

`citation-doi-verifier` looks every reference up in Crossref, OpenAlex and arXiv. The article cites no scholarly work:

```plaintext
citation links: 10 of 11 resolving and identified
citation dois/arxiv in paper text: 0
```

All 11 links were fetched, and 10 were matched to a second source: the GitHub API for the repository, the dev.to API for the article copies, and a byte comparison for the cover. Medium answers scripts with HTTP 403, so its copy needs a check in a browser.

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

#### Step 8 — Stage the Audit Records

Copy the two audit files into the article's `evidence/` folder. Nothing else needs configuring: `preflight.py` defaults its evidence to `<article folder>/evidence`.

```bash
cp math-sandbox/eq_verified_numbers.json ablation-stat-auditor/stat_audit.json \
   ~/publishing-kit/articles/publishing-kit-skill/evidence/
```

---

#### Step 9 — Run the Pre-flight

```bash
cd ~/publishing-kit/articles/publishing-kit-skill
python3 $KIT/scripts/preflight.py devto-publishing-kit.md
```

On the article as it was published:

```plaintext
check-facts.py — every number traces to an artifact
==============================================================
devto-publishing-kit.md: 7 claim(s) against 15 evidence file(s), 15 dated log row(s)

  DISPUTED count     0 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
  ok    dimensions   1376x768                     <- devto-cover-crop.txt
  ok    ratio        2.381:1                      <- devto-cover-crop.txt
  DISPUTED pixels    320px                        <- NOT CHECKABLE in eq_verified_numbers.json (D3_card_width_is_devto)
  DISPUTED count     4 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
  ok    count        47 of 62                     <- devto-hardwrap.txt
  ok    pixels       95px                         <- devto-cover-crop.txt

4 traced, 0 cited from the log, 0 untraced, 3 disputed
...
  FAIL  facts
  PASS  prose
  PASS  article
  PASS  linkedin

1 check(s) failed: facts
```

It exits 1. The 15 evidence files are the 13 the article already had plus the two audit records.

The wording problems the audits found do not show up here, because they carry no number for `check-facts.py` to match: "every paragraph", "on the cover", the footer date. Those come from reading the audit reports.

---

#### Step 10 — Fix the Article, Then Explain What Stays

Each finding is either fixed in the article or kept with its reason. The fixes, all in the publishing kit's walk-through:

| Was | Now |
| --- | --- |
| a stray break in every paragraph | in most paragraphs |
| a 1376x768 cover loses 95px | would lose 95px; the kit renders dev.to covers at 1376x578 |
| The two numbers on the cover are real | These two numbers are real |
| measured on 2026-08-31 | measured between 2026-08-30 and 2026-09-16 |
| readable at 95 columns | keeps its line wrapping |

What stays goes under `## DISPUTED` in `CLAIMS.md`, one row per claim with the reason:

```plaintext
| 0 of 4 | E3_medium_data_uri_0_of_4, NOT CHECKABLE | no archived artifact; the article labels it "kit log, 2026-08-30" |
| 4 of 4 | E3_medium_data_uri_0_of_4, NOT CHECKABLE | same row as 0 of 4 |
| 320px | D3_card_width_is_devto, NOT CHECKABLE | `CARD_W` in make-cover.py; no archived measurement of dev.to's card width |
...
```

The pre-flight again, with live link checks:

```plaintext
  NOTED count        0 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json, caveat in CLAIMS.md
  ok    dimensions   1376x578                     <- devto-cover-crop.txt
  ok    dimensions   1376x768                     <- devto-cover-crop.txt
  ok    ratio        2.381:1                      <- devto-cover-crop.txt
  NOTED pixels       320px                        <- NOT CHECKABLE in eq_verified_numbers.json, caveat in CLAIMS.md
  NOTED count        4 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json, caveat in CLAIMS.md
  ok    count        47 of 62                     <- devto-hardwrap.txt
  ok    pixels       95px                         <- devto-cover-crop.txt

5 traced, 0 cited from the log, 0 untraced, 0 disputed, 3 disputed with a caveat
...
  PASS  facts
  PASS  prose
  PASS  article
  PASS  links
  PASS  linkedin
all checks passed
```

It exits 0. The audit records stay in `evidence/`, so every later pre-flight checks the article against them.

---

#### Step 11 — Publish the Draft

From publishing kit 0.36.2, `publish-devto.py` runs the cover and front matter checks and the number check itself, and refuses to post on a failure. On the article as published, with the audits staged:

```plaintext
  DISPUTED count     0 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
  DISPUTED pixels    320px                        <- NOT CHECKABLE in eq_verified_numbers.json (D3_card_width_is_devto)
  DISPUTED count     4 of 4                       <- NOT CHECKABLE in eq_verified_numbers.json (E3_medium_data_uri_0_of_4)
4 traced, 0 cited from the log, 0 untraced, 3 disputed
...
refusing to publish: check-facts failed. --force overrides.
```

Nothing reaches dev.to. Once the pre-flight passes, create the draft and confirm it from the listing:

```bash
python3 $KIT/scripts/preflight.py devto-research-kit-publishing-kit.md --live
python3 $KIT/scripts/publish-devto.py --create devto-research-kit-publishing-kit.md
python3 $KIT/scripts/publish-devto.py --list
```

```plaintext
   5049183  draft      org=-               Auditing a Technical Article with Claude Code Resear
            https://dev.to/xbill/auditing-a-technical-article-with-claude-code-research-skills-118b-temp-slug-6830794
```

The front matter carries the title, tags and cover, and `published: false` keeps it a draft.

---

#### Step 12 — Check Everything Built From the Article

The studio page and the comic repeat numbers too. `paper-number-check` finds the installed publishing kit's `check-facts.py`, proves it flags a known disputed number, then runs it over every output at once:

```bash
python3 check_outputs.py --audit math-sandbox/eq_verified_numbers.json ablation-stat-auditor/stat_audit.json \
  -- interactive-paper-studio/index.html graphic-story/Story.html
```

```plaintext
check-facts: ~/.claude/plugins/cache/publishing-kit/publishing/0.36.2/skills/publishing/scripts/check-facts.py (control passed)
audit: 2 file(s), 20 disputed record(s)
interactive-paper-studio/index.html: 0 disputed, 4 noted, 7 traced, 15 untraced
graphic-story/Story.html: 0 disputed, 2 noted, 8 traced, 4 untraced

0 disputed claim(s) across 2 output(s)
```

Each noted number has a row in a `CLAIMS.md` beside its output.

---

#### 🔎 Tip: Read the Record Behind Each Disputed Number

Open the record named after each `DISPUTED` line before changing the article. In publishing-kit 0.36.0 one shared number was enough for a match, and on an HTML page the stylesheet was read too. From 0.36.1 a claim's numbers must match a record's as a sequence, a number with a unit must carry that unit in the record's statement, and `<style>` is skipped. Over the five outputs in this run that took the flags from 34 to 12, and the 12 are the Medium counts and the 320px card width.

---

#### 🔎 Tip: Keep the Old Claim Visible

The publishing kit writes a reversal as a **Correction** paragraph that keeps the retracted claim in view. The fixes in Step 10 went into the ledger as a table of was, now and evidence, so a reader of the repository can see what changed and why.

---

#### Compare and Contrast

| Skill | Fit for a technical article | What it found here |
| --- | --- | --- |
| `math-sandbox` | 🥇 every quantitative claim | 6 mismatches, 5 not checkable |
| `ablation-stat-auditor` | 🥇 any count or rate | 6 mismatches, 3 not checkable |
| `figure-forensics` | 🥈 covers and diagrams | a cover sentence with no number on the cover |
| `paper-number-check` | 🥈 anything built from the article | 0 disputed after the ledger rows |
| `citation-doi-verifier` | 🥉 links only | 10 of 11 links confirmed |
| `interactive-paper-studio` | 🥉 when the article has a model | a threshold its own comment misstates |

---

#### So, Which One?

Start with `math-sandbox` and `ablation-stat-auditor`. They write the audit records that the pre-flight and `paper-number-check` read. Stage the records in the article's `evidence/` folder once, and every `preflight.py` run after that holds the article to them. Run `paper-number-check` over anything else built from the article.

---

#### Summary

The goal of this article was to check every number in a published technical article and stop the disputed ones from shipping again. The key to the solution was a verdict beside every recomputed number, staged in the article's `evidence/` folder and enforced by the publishing kit's pre-flight. The results on the publishing kit's walk-through were:

- 🟢 26 claims checked: 15 verified, 6 mismatches, 5 not checkable
- 🟢 47 of 62 matches its evidence: 75.8%, 95% interval 63.8% to 84.8%
- ❌ "every paragraph", "on the cover" and the footer date overstated their evidence; all three fixed
- ⚠️ 0 of 4 against 4 of 4 on Medium has no archived artifact; kept with its caveat
- 🟢 pre-flight went from 3 disputed numbers to 0, with all 3 explained in the ledger

Scope: one article, audited on 2026-11-16 with research-kit 1.3.1 and publishing kit 0.36.2. Each skill ran as a separate agent, as the example's README records. The comic run stopped before its final page review. Live pages were fetched by the link check, `preflight.py --live` and the dev.to API calls.

The strategy for auditing a technical article with Claude Code research skills was validated with an incremental step by step approach.

#### References

- [research-kit on GitHub](https://github.com/xbill9/claude-research-skills)
- [The worked example](https://github.com/xbill9/claude-research-skills/tree/main/examples/publishing-kit-article)
- [publishing-kit on GitHub](https://github.com/xbill9/publishing-kit)
- [The audited article](https://dev.to/gde/streamline-publishing-with-a-claude-code-skill-1bdn)
- [Robina Mirbahar's Antigravity research kit](https://github.com/RobinaMirbahar/My-antigravity-research-skills)
- [Claude Code plugins](https://docs.claude.com/en/docs/claude-code/plugins)
