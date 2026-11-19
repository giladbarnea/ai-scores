---
last_updated: 2026-11-19T05-44
based_on:
  - https://labs.scale.com/leaderboard/swe-atlas
  - https://labs.scale.com/embeds/swe-atlas-index.html
  - https://github.com/scaleapi/SWE-Atlas
  - https://microsoft.ai/pdf/MAI-Code-2-And-MAI-Code-2-Flash-Model-Card.pdf
limits: Microsoft benchmark version, judge, and category aggregation are unspecified; do not equate its runs with Scale v1.1.
---
# Add SWE Atlas v1.1, but keep Microsoft's runs separate

SWE Atlas is a serious complementary coding benchmark from Scale AI. It measures professional engineering beyond implementing features or fixing issues: runtime-grounded Codebase Q&A (124 tasks), Test Writing (90), and Refactoring (70). The live v1.1 leaderboard covers 284 expert-authored tasks from 15 repositories in six languages. It differs from charted DeepSWE and SWE-Bench Pro by directly testing codebase comprehension, adversarial test creation, and behavior-preserving structural changes rather than primarily issue resolution. CursorBench covers broader user coding requests, Vibe Code Bench product/app construction, ITBench-AA operational work, and the internal cyber lanes security tasks; none is this same task set or scoring protocol.

## The version change matters more than the headline name

Scale's November 2026 update says v1.1 uses the same 284 tasks as v1.0, but EVERY model was re-evaluated with GPT-6.1 Sol as judge (high effort; majority of three votes), refined criteria, and restricted network access. Scale explicitly says v1.1 and v1.0 scores are NOT directly comparable. Original paper and legacy pages use Opus 4.5 as judge. The paper and Microsoft describe 18 repositories; live Scale page says 15. Preserve that discrepancy rather than treating it as proof of a different task set.

Overall v1.1 is the equal-weight mean of Q&A, Test Writing, and Refactoring, NOT a task-count-weighted mean across 284 tasks. Each task is binary: all mandatory rubrics must pass. Test Writing additionally requires a faithful test manifest and tests that pass on the real implementation but fail on a broken implementation; Refactoring requires behavior-preservation regression checks, hidden interface checks, and no test-file modifications. Nice-to-have conventions/documentation are qualitative signals, not mandatory correctness gates.

Scale operates the leaderboard and publishes tasks, verifier code, and harness configs. Harbor orchestrates containerized runs on Modal. Native harnesses differ by provider: Claude Code, Codex CLI, and (currently) Antigravity CLI for Gemini 4 Carbon. This is a MODEL+HARNESS ranking, not a controlled common-harness model comparison. Current configs document Claude Code 2.1.293 and Codex CLI 0.142.1; versions for Fable 5.2, GPT-6.2 variants, and Antigravity are not separately published in configs. Current metadata gives their harness and effort, which should not be discarded just because harness version is absent.

The landing-page sentence 'one attempt per task' describes pass@1, whereas published configs use n_attempts: 3 and README defines the score as mean single-attempt success over attempts. Do not call it best-of-three/pass@3. Exact trial counts for later-added models are not separately documented.

## Backfill the eight available supported models

All values below are Scale SWE Atlas v1.1 pass@1 percentages. Source: https://labs.scale.com/embeds/swe-atlas-index.html (embedded by the official leaderboard). `selected-models.json` preserves full values, uncertainty, metadata, costs per category; `selected-models.csv` provides import-ready columns. `lb-data.json` preserves ALL leaderboard models.

| Model | Overall | Q&A | Tests | Refactor | Harness / effort | USD full 284-task run | Derived USD/task |
|---|---:|---:|---:|---:|---|---:|---:|
| Claude Fable 5.2 | 80.5496 | 83.8710 | 77.7778 | 80.0000 | Claude Code / max | 4382.60 | 15.431690 |
| Claude Opus 5.5 | 77.4467 | 77.4194 | 77.7778 | 77.1429 | Claude Code / max | 1298.86 | 4.573451 |
| Gemini 4 Carbon | 71.4465 | 73.3871 | 76.6667 | 64.2857 | Antigravity CLI / high | 949.11 | 3.341937 |
| GPT-6 Astra | 69.4188 | 70.1613 | 66.6667 | 71.4286 | Codex CLI / max | 1023.60 | 3.604225 |
| Claude Sonnet 5.5 | 68.2762 | 74.1935 | 67.7778 | 62.8571 | Claude Code / max | 992.45 | 3.494542 |
| GPT-6.1 Sol | 65.8781 | 70.9677 | 66.6667 | 60.0000 | Codex CLI / max | 168.50 | 0.593310 |
| GPT-6.2 Sol | 60.4830 | 61.2903 | 64.4444 | 55.7143 | Codex CLI / max | 194.83 | 0.686021 |
| GPT-6.2 Astra | 60.4642 | 67.7419 | 62.2222 | 51.4286 | Codex CLI / max | 855.29 | 3.011585 |

Gemini 4 Hydrogen: no result in the current official leaderboard or the three preserved legacy leaderboards, and targeted search found no primary-source SWE Atlas result. Leave absent, not zero. Search's PostTrainBench result is unrelated and must not be used.

Cost caption explicitly says ONE full 284-task run, API cost excluding the judge. Derived USD/task is cost_usd / 284, not / 852. GPT-6.2 Sol and Astra costs are estimates from token usage × OpenAI list prices (metadata says 2026-11-18); others are harness-reported. The caption notes a few models have tasks without logged usage estimated at list price. Do not represent all costs as equally audited measurements. These costs do not imply an effort curve: only one effort is available per model.

## Keep historical GPT-6 Astra scores as v1.0

Legacy primary pages publish GPT-6 Astra / Codex / xhigh: Q&A 59.14%, Test Writing 50.74%, Refactoring 59.05%. No cost for these particular runs is published. Source URLs:
- https://labs.scale.com/leaderboard/sweatlas-qna
- https://labs.scale.com/leaderboard/sweatlas-tw
- https://labs.scale.com/leaderboard/sweatlas-refactoring

These legacy pages contain none of the other requested models. Do not relabel these xhigh scores as max or merge with v1.1. They are preserved in legacy-*.html/.txt and legacy-*-selected.json; selected JSON also includes some unrelated fuzzy-name matches, so filter on exact GPT 6 Astra names.

## Microsoft's 43.1% is usable, but not against Scale's v1.1 numbers

Microsoft's public article embedded data publishes a separate, internally controlled comparison, ALL Copilot CLI / max:

| Model | SWE Atlas % | USD/task |
|---|---:|---:|
| MAI Code 2 (NOT Flash) | 43.1 | 0.228 |
| GPT-6.1 Sol | 47.4 | 0.605 |
| Claude Opus 5.5 | 57.5 | 4.234 |

Source: https://microsoft.ai/news/introducing-mai-code-2-and-mai-code-2-flash/ ; saved exact chart payload in microsoft-embed-0.json and microsoft-swe-atlas.json. Article footnote: all max; DeepSWE, TerminalBench and SWE Atlas on MSBench, Copilot CLI, subagents disabled. MAI cost shown at 50% promotional price. Model card p6 specifies Copilot CLI 1.0.102, three independent runs/task averaged as single-attempt success, infrastructure errors counted as failures. Scale configs instead retry infrastructure failures and exclude them from score until rerun. Model card p7 describes hybrid checks/rubrics and 124/90/70 tasks but gives NO benchmark version, judge identity, or category aggregation formula.

Therefore Microsoft's own 43.1 vs 47.4 vs 57.5 and costs may share a clearly named 'Microsoft-reported / Copilot CLI / version unspecified' lane. They must NOT be placed as directly comparable peers of Scale v1.1's 65.88% Sol / 77.45% Opus. Different harness is already material; unknown judge/version/aggregation prevents equivalence even if tasks match. The large score gap does not prove MAI is worse by that amount on v1.1.

Important additional inconsistency: the same model card's advanced-autonomy table p18 gives MAI Code 2 SWE Atlas 80.9% (Flash 65.2%), versus the quality table p6's Code 2 43.1% (Flash 44.8%). No explanation of this discrepancy appears in adjacent methodology. Do not silently substitute 80.9%; preserve as separate unexplained safety-section result rather than conflating with the quality comparison.

## Suggested addition

Add four Scale v1.1 panels (overall plus three category lanes) and backfill all eight supported models above. Separately add/retain Microsoft's SWE Atlas comparison with version unspecified and explicit reporting/harness caveat, including its published Sol and Opus baselines. Preserve v1.0 provenance without inventing a composite. No code changes were made.

## Evidence and verification

`leaderboard-current.html` embeds `interactive.html`. `lb-data.json`, `selected-models.json`, `d-updates.json`, four model YAMLs, GitHub README/tree/repo metadata, paper PDF/text, legacy category pages/text/data, original snapshots, and Microsoft article/chart/model-card text are saved beside this report. GitHub tree revision: b3cdddf44414c0ccca50c6e89fe978bb4d844d26. Retrieval timestamp is in retrieved-at.txt.

Visually checked the live overall ranking and methodology in overview-readable.png against extracted scores. Rendered/read all 27 paper pages in paper-sheet-{1,2,3}.jpg; the paper is launch-era evidence, not a source for current v1.1 model scores. Browser screenshots retain full original figures; no generated project chart was changed. Search files are leads only, not score evidence.
