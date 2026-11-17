---
last_updated: 2026-11-17T14-43
description: Rough performance peers across Sol, Astra, Opus and Fable; API cache prices versus subscription usage
based_on:
  - ../docs/data.csv
  - ../sources/carbon_fable52.json
  - 2026-11-17-effort-equivalence.csv
confidence: Descriptive benchmark comparison, not a controlled experiment in Pi or a statistical equivalence test
---

# Sol's upper levels overlap Opus high; Fable needs a level-specific rule

The requested comparison is **performance, not performance per dollar**. The scores below are the project's **13 November 2026 snapshot**, not a new benchmark run on 17 November. General and ordinary coding benchmarks have equal weight; specialized domains receive a modest discount.

My assessment of the three draft rules:

- **“Opus high = Astra high” is reasonable shorthand, but too exact.** High–xhigh is the useful Astra range. Opus is stronger in scientific coding and professional deliverables; Astra is stronger in the physics tasks, and usually in PDF Q&A. Neither is simply the other at a different setting.
- **“Opus medium = Sol xhigh or max” overstates the Sol effort needed on these benchmarks.** Medium–high is closer, usually high. Sol xhigh is a conservative replacement, not the central estimate. **Sol xhigh–max overlaps Opus high**, rather than merely Opus medium.
- **“Fable has no Codex equal” needs an effort qualifier.** Fable low overlaps upper Sol/Astra levels on several relevant tasks; Fable medium overlaps Astra's top range. **Fable high and above has no convincing all-round GPT counterpart in this snapshot.** This does not mean Fable wins every benchmark.

## Use ranges as a routing guide, not an equality sign

The table is anchored on Opus. “Peer” means a plausible replacement for a mixed workload, **not equal scores on every benchmark, identical failure modes, or a guaranteed result on our work**. Ranges reflect both benchmark disagreement and sensitivity to aggregation choices; they are not confidence intervals.

| Opus 5.5 effort | GPT-6.1 Sol rough peer | GPT-6 Astra rough peer | Fable 5.2 rough peer |
|---|---|---|---|
| low | low | No close level: Astra low is generally stronger | No close level: Fable low is much stronger |
| medium | medium–high; start with high | medium | Fable low is already above this band on the principal general/coding tests |
| high | xhigh–max | high–xhigh | low–medium, depending on task mix |
| xhigh | No convincing mixed-workload peer; max is the nearest ceiling | max on the principal general/coding tests; weaker in several specialist tasks | medium–high; high is closest in the discounted-specialist aggregate |
| max | No convincing mixed-workload peer | max is nearest, but is not a blanket substitute | high is closest in the discounted-specialist aggregate; a different strengths profile |

Fable **xhigh and max** extend beyond the GPT options in the mixed comparison. Opus max remains a plausible task-specific alternative, especially where Fable is not improving with effort, but I would not label it an unconditional equivalent.

Read the lower rows in both directions: **Sol high ≈ Astra medium ≈ Opus medium**; **Sol xhigh–max ≈ Astra high–xhigh ≈ Opus high**. Astra max sits near Opus xhigh on the principal tests, but scientific coding and professional work can move the choice toward Opus.

Fable low/medium deserve particular caution: their strong knowledge/hallucination result can offset weaknesses elsewhere in an average. That is a reason to keep task-specific exceptions, not to prohibit every substitution.

## The raw scores show why the ranges cannot be exact

Each cell lists **low / medium / high / xhigh / max**. Scores are percentages except the AA indices; larger is better. The coding category is shown for interpretation, **not counted again in the custom comparison**.

| Benchmark | Sol | Astra | Opus | Fable |
|---|---|---|---|---|
| AA Intelligence Index v5.0.1 | 34.8 / 46.3 / 50.3 / 52.5 / 54.6 | 43.3 / 51.6 / 54.8 / 55.3 / 56.9 | 34.8 / 48.2 / 51.8 / 57.4 / 59.1 | 53.9 / 56.4 / 61.8 / 62.2 / 64.6 |
| AA coding category | 24.4 / 39.2 / 42.6 / 44.7 / 46.8 | 32.5 / 41.7 / 45.7 / 48.7 / 49.1 | 22.0 / 40.9 / 44.2 / 50.1 / 51.7 | 44.9 / 46.8 / 53.3 / 53.2 / 53.1 |
| Terminal-Bench 4.0 | 30.8 / 48.0 / 51.5 / 54.0 / 56.1 | 41.9 / 49.5 / 54.0 / 59.6 / 59.1 | 31.3 / 52.5 / 56.6 / 59.6 / 59.6 | 54.5 / 55.1 / 59.6 / 61.6 / 59.6 |
| FrontierCode-AA 2.0 | 20.2 / 33.4 / 36.7 / 38.5 / 40.6 | 26.2 / 36.6 / 40.1 / 41.4 / 42.4 | 15.8 / 33.1 / 35.9 / 43.8 / 46.4 | 38.4 / 41.3 / 49.1 / 47.6 / 48.8 |
| HLE-Diamond | 38.2 / 46.0 / 51.9 / 55.8 / 58.8 | 45.1 / 52.7 / 59.3 / 61.5 / 63.8 | 41.7 / 51.4 / 55.6 / 64.0 / 67.9 | 60.8 / 66.3 / 73.8 / 75.8 / 80.2 |
| AA-Omniscience v1.1 | 38.0 / 40.2 / 41.0 / 42.4 / 42.0 | 40.3 / 41.4 / 44.6 / 43.7 / 42.4 | 39.0 / 39.8 / 42.4 / 43.1 / 48.1 | 62.9 / 63.5 / 64.0 / 64.8 / 66.8 |
| ARC-AGI-2 | 76.7 / 86.7 / 91.7 / 91.7 / 94.2 | 85.4 / 92.1 / 92.1 / 93.3 / 95.0 | 70.1 / 87.5 / 93.3 / 92.5 / 91.7 | 86.7 / 89.6 / 90.4 / 93.8 / 92.5 |
| SciCode | 53.2 / 53.2 / 55.8 / 55.7 / 54.2 | 54.1 / 54.2 / 55.4 / 55.7 / 56.5 | 58.6 / 59.3 / 60.4 / 65.0 / 66.9 | 57.8 / 59.7 / 59.5 / 65.6 / 67.7 |

Specific counterexamples matter more than a decimal-place composite:

- **Opus medium versus Sol high:** HLE **51.4 vs 51.9**, terminal **52.5 vs 51.5**, FrontierCode **33.1 vs 36.7**. These support a rough peer band. But Opus leads Briefcase **1620 vs 1469 Elo**, while Sol leads CritPt **68.5 vs 54.0**. Neither “same model” nor “Sol must run max” follows.
- **Fable low versus Sol max:** terminal **54.5 vs 56.1**, FrontierCode **38.4 vs 40.6**, HLE **60.8 vs 58.8**: substantial overlap. Omniscience **62.9 vs 42.0**, however, is not remotely equal. ARC goes the other way, **86.7 vs 94.2**.
- **Opus xhigh versus Astra max:** HLE **64.0 vs 63.8**, terminal **59.6 vs 59.1**, FrontierCode **43.8 vs 42.4**, Omniscience **43.1 vs 42.4**. A useful principal-test match, but SciCode is **65.0 vs 56.5**, and Briefcase is **1760 vs 1569 Elo**.
- **Fable high versus the GPT ceilings:** FrontierCode **49.1**, against Astra max **42.4** and Sol max **40.6**; HLE **73.8**, against **63.8 / 58.8**. On terminal tasks Fable high merely ties Astra xhigh at **59.6**. The “no broad GPT equal” statement is supported; “always better” is not.

Full scores for all **13 × 20 = 260** benchmark/configuration observations and their weights are in [the CSV](2026-11-17-effort-equivalence.csv).

## The weights are explicit, modest, and not a second AA index

I operationalized “subtle weights” as **1.00 per principal benchmark and 0.75 per specialist benchmark**. These exact numbers are my analysis choice, not numbers specified by Gilad.

| Weight | Benchmarks | Reason |
|---|---|---|
| 1.00 | HLE-Diamond, ARC-AGI-2, AA-Omniscience v1.1 | General reasoning/knowledge; same weight as ordinary coding |
| 1.00 | Terminal-Bench 4.0, FrontierCode-AA 2.0 | Ordinary terminal/repository coding |
| 0.75 | CritPt v2, Terminal-Bench Science 0.1, SciCode | Physics/scientific tasks, including specialized scientific coding |
| 0.75 | GDPval-AA, AA-Briefcase, AutomationBench-AA, GDP.pdf, AA-LCR | Professional deliverables, SaaS workflow automation, PDF and long-document tasks |

All thirteen have a score for all four models at all five efforts, so comparisons use the same evidence. **AA Intelligence Index and its coding category are excluded from the aggregate** because their components are already present. CursorBench, DeepSWE, FrontierCode 1.1 and single-effort bars are excluded from the common aggregate because four-model/five-level coverage is incomplete. They must not be filled in with a different effort's score.

For each benchmark, standardize its twenty observations using the population mean and standard deviation. Then average those standardized scores with the listed weights. Thus a 150-Elo difference does not numerically swamp a 5-percentage-point coding difference. This is a descriptive composite, **not calibrated units of real-world capability**.

| Model | low | medium | high | xhigh | max |
|---|---:|---:|---:|---:|---:|
| Sol | -1.519 | -0.505 | -0.117 | -0.050 | 0.196 |
| Astra | -0.910 | -0.229 | 0.061 | 0.202 | 0.321 |
| Opus | -1.808 | -0.301 | 0.106 | 0.609 | 0.795 |
| Fable | 0.024 | 0.216 | 0.744 | 0.949 | 1.214 |

An important check: there are eight specialist benchmarks and only five principal ones. Even discounted, specialists supply **6 of 11 total weight units**. I therefore also inspected the five principal tests alone, rather than presenting the full mean as the only answer:

| Model | low | medium | high | xhigh | max |
|---|---:|---:|---:|---:|---:|
| Sol | -1.900 | -0.675 | -0.228 | -0.029 | 0.199 |
| Astra | -1.041 | -0.241 | 0.130 | 0.352 | 0.436 |
| Opus | -2.125 | -0.461 | 0.021 | 0.414 | 0.619 |
| Fable | 0.316 | 0.606 | 1.065 | 1.242 | 1.301 |

This exposes the profile issue rather than hiding it: Fable's knowledge advantage matters more in the principal-only comparison; Opus's specialist strengths matter more in the full comparison. AA-LCR's narrow score spread can also amplify noise when standardized, so it should not decide a switch by itself.

Sensitivity checks used three normalizations (standard scores, min–max scores, average ranks), four specialist weights (**0.5 / 0.75 / 0.9 / 1.0**), and the full set plus each single-benchmark omission: **168 choices per comparison**. This is robustness to analysis choices, not 168 independent experiments.

- The nearest Sol level to **Opus high** was **max in 121 cases, xhigh in 47**.
- The nearest Sol level to **Opus medium** was **high in 98, medium in 52, xhigh in 18; never max**.
- The nearest Astra level to **Opus high** was **high in 108, xhigh in 57, max in 3**.
- **Opus xhigh → Astra max** was the nearest endpoint in all 168 choices. A nearest ceiling is not automatically an equal.
- **Fable high → Opus xhigh/max** depended on weighting (64 / 104), supporting a range rather than an exact label.

The peer table is a judgment from these checks **and the raw profiles**, not an automatic nearest-neighbor output. Most benchmarks provide no uncertainty estimate in our snapshot. Tiny score differences, noisy effort reversals and near-saturated ARC results should not be turned into confident model rankings. There are no controlled evaluations here of Pi's long-running Lead work, instruction adherence, communication judgment, or million-token reliability.

## Above 272k, the API cache rates match—but the subscription rule is different

As checked on **17 November 2026**, standard first-party API prices in dollars per million tokens are:

| API model/tier | Input | Cache read | 5-minute cache write | Output |
|---|---:|---:|---:|---:|
| Sol, at most 272k input tokens | 2 | 0.10 | 2.50 | 10 |
| Sol, more than 272k input tokens | 4 | 0.20 | 5 | 15 |
| Opus 5.5, full context | 4 | 0.20 | 5 | 20 |
| Fable 5.2, full context | 8 | 0.20 | 10 | 40 |

**Yes: Sol's long-context API cache reads are exactly the same listed rate as Opus's—and Fable's.** The higher tier prices the **full API request**, not only tokens beyond the threshold. At fixed token counts its output is still cheaper than Opus's, but by 25%, not several-fold. Tokenization, generated volume, cache lifetime and misses can still differ.

However, OpenAI explicitly states on both its [Sol model page](https://platform.openai.com/docs/models/gpt-6.1-sol.md) and [Codex pricing page](https://developers.openai.com/codex/pricing/):

> GPT-6.1 Sol usage drawn from your subscription has no long-context surcharge in Codex or ChatGPT Work.

Codex pricing also says that API token prices are separate from subscription usage and should not be used to estimate included tasks. Therefore **matching API/cache dollar rates do not establish matching depletion of the two subscriptions**. A giant cached context still consumes resources; the specific >272k API multiplier must not simply be treated as a Codex-subscription multiplier.

The installed Pi registry on this machine declares Sol's API-style tier under **both `openai` and `openai-codex`**. Consequently its displayed API-equivalent dollar amount can increase at 272k even when the official subscription rule says no surcharge. This needs a separate provider-accounting investigation if that displayed dollar number is converted into quota points. No model, provider or quota configuration was changed for this report.

Anthropic's matching prices and full-context standard pricing are documented in [Claude API pricing](https://platform.claude.com/docs/en/about-claude/pricing).
