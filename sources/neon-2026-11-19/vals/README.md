---
last_updated: 2026-11-19T08-33
retrieved: 2026-11-19
sources:
  - https://www.vals.ai/models/google_gemini-4-neon
  - https://www.vals.ai/blogs/reasoning-effort
  - https://www.vals.ai/methodology
---

# Vals provenance: keep task sets and scoring rules separate

`audit.json` preserves exact scores, costs, effort settings, versions, harnesses, secondary metrics, source URLs and methodology for the fourteen boards linked from Gemini 4 Neon. It contains132 available full-test target-model rows, eight explicit absences and113 reasoning-study points. Scores are percentages; costs are the original `cost_per_test` values in API US dollars per benchmark task, not token prices or the expense of the whole suite. No missing score was inferred.

Neon's internal source ID is `google/cobalt-c-high-1p00`; every reported Neon row uses xhigh. The public model page is `/models/google_gemini-4-neon`; `/models/gemini-4-neon-xhigh` returned404. Carbon and Hydrogen have no rows on Science Index, MysteryMechanism, BioMysteryBench or Terminal-Bench-Science.

## The reasoning curves use approximately half the tasks

The [reasoning-study methodology](https://www.vals.ai/blogs/reasoning-effort) says each effort setting uses the same fixed approximately half-task subset. Many leaderboard-setting runs are older full runs rescored on that subset. A full-test bar and a reasoning-study point at the same effort are therefore **different observations**, not alternatives to reconcile by averaging.

`discrepancies.json` records two examples on Vals Index at max:

| Model | Full-test score / US$ per test | Study subset score / US$ per test |
|---|---|---|
| GPT-6 Astra |65.023 /21.277828 |65.2 /22.1665 |
| Claude Opus5.5 |70.143 /24.772748 |69.6 /26.4926 |

`reasoning-effort-widgets.json` retains the complete decoded source widgets, including records for other models, their dates, default/partial flags and cost-basis notes. The original study covered seven older models; newer Astra6.2/Fable5.2 records were subsequently added to the widgets without a separate description of their subset selection.

## Published Claude scores can include fallback answers

`fallback-summary.json` lists nonzero target-model cases. Each audit row also retains its source refusal/fallback record: responding models, counts, published score and `noFallbackScorePct`. For example, Vals Index Fable71.309 becomes69.483 if fallback tasks score zero; Opus70.143→68.148; Sonnet70.854→69.028. BioMystery Opus79.259→69.259. Keep these variants distinguishable rather than silently replacing a published score. Neon has no fallback tasks.

## Versions and denominators matter

- Vals Index2.2 uses GDP weights8.0/5.6/1.2/0.5 over Finance/Coding/Legal/Tax. Cost is the plain mean of eight component costs, not the GDP-weighted score formula.
- Finance Index1 combines FAB2.1, EMB1.1 and Tax all-pass. Legal Index1 instead uses practice-area LegalResearch all-pass, HLAB **criteria** pass and Tax **weighted** pass; its reference to Tax weighted pass also being the current Vals Index input is stale. Science Index1.0 equally averages BioMystery, MysteryMechanism and TBScience.
- EMB1.1 uses51 financial models in Template/Scratch modes (102 task-mode instances), category-mean grading and GPT-6 Luna for Scratch rubrics. FAB2.1 uses449 questions with dealbreaker-gated partial credit, not secondary all-pass.
- LegalResearch1 uses208 questions and strict all-required-checks pass. TaxAgent1 uses193 questions and all-pass×(0.7+0.3×citation quality); its weighted-pass secondary metric is different. MysteryMechanism1 uses222 binary functional-recovery tasks.
- VibeCode1.1 costs are per generated app (50 apps), not individual UI checks. Its score averages each app's share of tests with≥90% successful substeps. The separate prose estimate for evaluator expense is not model API cost.
- BioMystery1 uses90 tasks, Terminus2 and a binary answer judge, averaged over three independent full runs. HLAB-Vals1.1 uses120 tasks and averages two judges' strict task-pass rates; criteria pass rate is secondary.
- TB4.0 uses66 tasks, Mini-SWE-agent and avg@3 over strict verifier pass@1 runs. TBScience0.1 uses70 tasks and one pass@1 run; infrastructure/provider errors were retried, graded tasks were not. Its board mixes harnesses, but all eight available target rows use Mini-SWE-agent. Costs are per task over the full70-task suite, not divided by a domain's task count.

Full scoring and tool/harness details are in each audit board's `scoring_method`, `harness_methodology` and `cost_denominator_notes`; extracted source sections are in `methodology-excerpts.json`.

## Code Migration has two valid, unequal task sets

`code-migration.json` is the normalized integration export (`benchmarks[].records[]` has explicit model, effort, score, cost, denominator and measured-task count):

- **Vals Index subset:**50 of120 CLI migrations plus all10 COBOL tasks, weighted75:25. All ten target models, including Neon75.762%,xhigh,$18.093695/test.
- **Standalone full test:**120 CLI migrations (30 repositories×4 target languages) plus10 COBOL, with CLI repository means and75:25 CLI/COBOL weighting. Five target models: Sonnet,Fable,Opus,Astra and Sol6.1. No Neon,Carbon,Hydrogen or6.2 rows.

Both use v1.1's Pi agent, offline sandbox, hidden behavior tests and anti-cheat checks. V1.1 changed harness and hidden tests; do not relabel older results or mix the60-task and130-task sets.

## The source payloads are preserved, not reconstructed

`primary/` contains15 complete original benchmark-view JSON payloads, fourteen refusal/fallback data modules, the original study article, general methodology page and standalone Code Migration page. They are individually gzip-compressed, without giant JS bundles or screenshots. `manifest.json` records each URL, retrieval date, uncompressed byte count and SHA-256; decompressing recovers the original downloaded bytes. `audit.json` paths resolve relative to this directory.

`validation.txt` records132 score-and-cost checks against rendered tables, fourteen independent Neon checks and five standalone Code Migration checks. All fourteen primary source figures and the additional Code Migration figure were also viewed. Raw screenshots and the larger working download remain outside the repository at `/tmp/neon-vals/`.

Vals Index and VibeCode default rows extend the site's existing Vals series. Vals TB4, TBScience and HLAB must stay distinguishable from AA runs; native Vals Science Index must stay distinguishable from the OpenAI launch comparison, even where rounded scores agree.
