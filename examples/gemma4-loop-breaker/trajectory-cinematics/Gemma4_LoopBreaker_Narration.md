# Gemma 4 Loop-Breaker - Narration

Video: `Gemma4_LoopBreaker_Explainer.mp4` (1440 frames at 30 fps = 48.0 s). Timestamps are computed from milestone frame indices in `make_explainer.py`.

Data note: panel A (per-turn KV) uses illustrative curves read off Fig. 2b with the turn-12 peaks pinned to Table 3; panel B applies Proposition 1 to those curves under equal per-token logits. Panels C and D are the paper's measured Table 2 and Table 3 values.

**00:00** (frame 0) - A 4-bit quantized Gemma 4 31B coding agent runs on four L4 GPUs with a 32,768-token context. Once the dialogue passes 14,336 tokens, the runner compacts it and exact file paths and line numbers are lost (Section 1).

> On-screen banner: Setup (Sec. 1): gemma-4-31b-it-qat-w4a16-ct on 4x NVIDIA L4, max_model_len 32,768; ADK compaction fires above 14,336 tokens.

**00:03** (frame 90) - Each curve is the active context at each agent turn. The shapes are illustrative, read off Figure 2b; only the peaks are tabulated in the paper.

> On-screen banner: Act 1 - per-turn active KV context. Curve shapes are illustrative (read off Fig. 2b); turn-12 peaks are Table 3 values.

**00:07** (frame 232) - Without pruning, failed test logs pile up. On these curves the baseline crosses the compaction cliff at about turn 3.9, the naive sub-agent at about turn 3.4.

> On-screen banner: Baseline static crosses the 14,336-token compaction cliff at turn 3.9 (on the illustrative curve; naive sub-agent at 3.4).

**00:09** (frame 287) - When a loop detector fires (a repeated error signature, diff similarity at least 0.82, or action entropy below 0.55 bits), Counterfactual Context Reset prunes the failed turns, writes a 150-token ledger of what failed, and starts a 6,144-token thinking burst (Section 3.4).

> On-screen banner: Loop detector fires -> G-CCR prunes B_t, inserts a 150-token NEGATIVE_CONSTRAINT_LEDGER, 6144-token thinking burst at tau=0.75 (Sec. 3.4).

**00:21** (frame 630) - By turn 12 the peaks match Table 3: 31,067 tokens for the naive sub-agent, 24,821 for the baseline, and 10,563 for G-CCR with adaptive thinking, which stays under the cliff.

> On-screen banner: Peak KV (Table 3): naive 31,067 | baseline 24,821 | G-CCR + adaptive 10,563 - below the 14,336 cliff.

**00:23** (frame 705) - Act two is the cumulative ablation on 129 repository tasks. The default template solves 15 of 129, 11.6 percent, and hits compaction on 68.2 percent of episodes (Table 2).

> On-screen banner: Act 2 - Table 2 cumulative ablation, 129 swegemma tasks: M0 solves 15/129 (11.6%), compaction on 68.2% of episodes.

**00:32** (frame 975) - With all six modules the agent solves 31 of 129, 24.0 percent, and compaction falls to 4.7 percent, a 93% cut. File-isolated synthesis reaches 39.5 percent, so a gap remains (Tables 1 and 2).

> On-screen banner: M6 solves 31/129 (24.0%); compaction 4.7% (-93% vs M0). Stage-1 isolated ceiling 39.5% (Table 1).

**00:34** (frame 1035) - Act three is the 25-trap fault-injection suite. The unpruned baseline escapes 4 of 25 traps, 16 percent (Table 3).

> On-screen banner: Act 3 - Trap-25 loop recovery (Table 3): baseline static escapes 4/25 traps (16.0%).

**00:41** (frame 1251) - Counterfactual Context Reset with adaptive thinking escapes 24 of 25, 96 percent, Fisher's exact p of 4.2 times ten to the minus nine, and cuts active post-reset KV tokens from 159,816 to 46,689, 70.8% (Table 3).

> On-screen banner: G-CCR + adaptive: 24/25 (96.0%), Fisher p = 4.2e-9; post-reset KV 159,816 -> 46,689 (-70.8%) (Table 3).

**00:45** (frame 1350) - Under a hard compaction limit, context hygiene decides whether a quantized agent escapes a loop. Panels A and B are illustrations; panels C and D are the paper's measured tables.

> On-screen banner: Takeaway: under a 14,336-token limit, pruning failed turns keeps the agent below the cliff. Panels A-B illustrative; C-D measured.
