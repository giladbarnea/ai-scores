---
retrieved: 2026-11-19
based_on:
  - https://labs.scale.com/leaderboard/swe-atlas
  - https://labs.scale.com/embeds/swe-atlas-index.html
---

# SWE Atlas v1.1 (Scale AI)

The chart "SWE Atlas v1.1" uses the overall score from Scale's leaderboard embed (`lb-data.json`). Overall is the equal-weight mean of Codebase Q&A (124 tasks), Test Writing (90) and Refactoring (70). Each model ran in its maker's agent (Claude Code, Codex CLI, Antigravity CLI), judged by GPT-6.1 Sol (high, majority of three).

Transformations: scores rounded to one decimal. Price per task = Scale's full 284-task run cost (judge excluded) divided by 284, three significant figures. GPT-6.2 Sol and GPT-6.2 Astra costs are Scale's own estimates from token usage at list prices.

Not charted: Gemini 4 Neon and Hydrogen (absent from the leaderboard on Nov 19 recheck). Microsoft's Copilot CLI SWE Atlas run (MAI Code 2 43.1, GPT-6.1 Sol 47.4, Opus 5.5 57.5) is not comparable and was not approved. Legacy v1.0 GPT-6 Astra category scores stay in `REPORT.md` only. `REPORT.md` is the full research report.
