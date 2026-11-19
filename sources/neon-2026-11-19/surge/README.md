---
last_updated: 2026-11-19T06-32
description: Primary Surge leaderboard evidence and methodology for the Gemini 4 Neon update.
---

# Surge leaderboard snapshots

Retrieved **2026-11-19**. `normalized.json` contains 111 current scores across 14 audited boards, with canonical model names, effort, units, task counts, methodology and explicit omissions. `manifest.json` maps retained evidence to its original URL and records transformations and exclusions.

`leaderboards/*.html.gz` retains each main leaderboard's original field contents for **all** listed models, excluding repeated recommendation cards and page chrome. Five original inline scripts preserve visible v1.1 badges and changelogs. `methodology/` retains relevant upstream README snapshots verbatim as text, plus article/paper evidence.

All 14 rendered boards and their linked articles' figures were visually checked. Screenshots and redundant full-page bundles are intentionally not included.

## Keep changed protocols separate

- **Chartography v1.1 is agentic:** Neon's 86.6 at High is not Google's 73.5 without tools. The old GitHub README and static cost/token scatter describe the previous no-tools protocol; neither establishes current v1.1 costs or trial count.
- **ComplexConstraints v1.1 is also agentic:** its current versioned Hugging Face card specifies Harbor/OpenHands tools, 75 tasks and 10 attempts. The GitHub README still describes the old no-tools harness. The visible changelog records rubric changes on ten tasks.
- **GDP.pdf v1.1** converts to Harbor agentic evaluation and clarifies rubrics. Its GitHub README still describes the earlier no-tools protocol.
- **HANDBOOK.md v1.1** recalculates scores after grading changes. Its current card specifies 65 tasks, five attempts and GPT-5.6 Sol High judging; older documentation describes four attempts and deterministic grading.
- **Riemann-bench v1.1** corrects four answer keys. Its blog correction removes the earlier one-hour limit; current trial count is not established. Do not infer it from score granularity.

DAYJOB Law/Tax report pass@1 at **95% rubric satisfaction**, whereas Finance/Healthcare cards specify **100%**. The shared harness emits mean criterion rewards, not necessarily the headline thresholded pass rate. GDP.xlsx's headline threshold is not explicitly documented: preserve its published score without claiming it equals raw mean criterion reward.

## Missing is not zero

Antidote and Hemingway have none of the ten requested models. Chartography lacks GPT-6.1 Sol and Sonnet 5.5; Riemann lacks Hydrogen. CoreCraft contains only GPT-6 Astra, GPT-6.1 Sol, Opus 5.5 and Sonnet 5.5 among the requested models. Its paper's training-held-out split is not the current leaderboard denominator.

No exact attributable current costs were found, so every normalized cost is null. Old raster cost frontiers and approximate historical costs are not paired with current scores. Each available model has one published effort setting per board; these are points, not inferred effort curves.
