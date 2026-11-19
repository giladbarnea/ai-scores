---
last_updated: 2026-11-19T08-34
retrieved: 2026-11-19
---

# Neon results use native boards where available

This snapshot supports Gemini 4 Neon, existing-model backfills and one approved MAI Code 2 point. `charts.py` is the live dataset; `integrated/` records the imported values before rendering. Original results remain here even when a different version, harness or uncertain attribution excludes them from the page.

## Sources and transformations

| Directory | Primary source | Interpretation |
| --- | --- | --- |
| `aa/` | [Artificial Analysis Neon](https://artificialanalysis.ai/models/gemini-4-neon), plus `/models/<slug>` for each record | Embedded records retain explicit effort, raw scores and weighted costs. Neon low/medium/high/xhigh only; no invented max. Fractions become percent, half-up rounding normally to one decimal. Costs use three significant figures: whole-suite total for the Index; weighted benchmark task cost divided by its index weight elsewhere. Coding uses FrontierCode:Terminal-Bench weights 15:10 for scores and costs. Null fields remain absent. MKA uses native Climb weighted rubric scores. |
| `cursor/` | [CursorBench](https://cursor.com/en/cursorbench) | Embedded 4.1 score/cost pairs, effort-specific. Costs are published USD/task. 4.1 supersedes 4.0 without relabeling historical points; older snapshots elsewhere in `sources/` retain 4.0. |
| `google/` | [Google DeepMind post](https://x.com/GoogleDeepMind/status/2123167884411077030), [six-page methodology](https://deepmind.google/models/evals-methodology/gemini-4-neon) | Original image/PDF and transcribed rows. Google-only runs stay distinct from native boards: both SWE-sweep harnesses, no-tools Chartography, vision-only LVBench with unequal frame budgets, GraphWalks 256k–1M, and five-attempt vision Mini-SWE Science. Neon TB4.1 is AA via Google (Antigravity CLI 1.5.9); Neon ALE is Google Antigravity CLI 1.4.8. No borrowed prices. Competitor efforts remain not stated when the source cannot establish the exact setting. |
| `nyt/` | [Lech Mazur Extended Connections](https://github.com/lechmazur/nyt-connections) | 940-puzzle and newest-100 datasets stay separate. Quadratic-v1 = mean((exact groups / 4)^2) × 100, one attempt, up to four trick words. README tables give Neon 99.11/99.56 and Carbon 99.30/99.56, more precise than the initial image transcription. Full-puzzle cost estimates use recorded tokens at standard prices; failed requests excluded. No newest-100 cost inferred. |
| `surge/` | Native Surge benchmark pages, linked datasets and articles | See its manifest and README for all 14 boards, 111 scores, versions, thresholds, missing models and stale cost-scatter exclusions. |
| `vals/` | [Vals](https://www.vals.ai/) native boards and embedded widgets | See its audit/methodology for default headline scores, fixed approximately half-task reasoning studies, costs per test, separate Code Migration subset/full sets, and fallback variants. |
| `public/` | Native Terminal-Bench, Cognition, Zapier, ALE, Science, CWE, SEC, WebExploit, AutoBax and ExploitGym boards | `observations-final.json` retains 163 rows, original rows, URLs, retrieval date, exact efforts, costs and denominators. `REPORT.txt` explains each board. Costs from aggregate totals are divided by native trials/tasks as documented; scores are rounded to chart precision, not silently substituted from Google’s rounded copies. |
| `microsoft/` | [Microsoft announcement](https://microsoft.ai/news/introducing-mai-code-2-and-mai-code-2-flash/) | Sole approved point: MAI Code 2, DeepSWE v1.1, max, 73.2%, USD0.618/task, Copilot CLI 1.0.102. The embedded figure explicitly uses 50% promotional pricing. Other Microsoft results were not approved for import. |

## Attribution conflicts are preserved, not plotted

Google labels MKA 52.7 as GPT-6.2 Sol. AA assigns the exact 52.6747547 value to GPT-6.2 Astra and has no Sol score. Google labels Science 68.0 as GPT-6.2 Sol; the native board has GPT-6 Astra 68.095238 and no Sol row. The native observations are used; neither conflicting Google-copy point gets its own chart. The original Google rows remain in `google/official-table-scores.json`.

## Missing coverage does not imply zero

No native Neon was found on TB4.1, ALE, public Science, ExploitGym, ARC Prize v2, or SEC 260617. The separately attributed Google Neon results remain available where sourced. SEC's live supported-model series is explicitly 260505/183 tasks, not the newer 260617/344 tasks. Opaque ALE `Hy4` is not Neon. Gray Swan's public challenge provides no reliably attributable Neon transfer score. Surge Antidote/Hemingway have no supported models. Secondary social-media reproductions are archived, not independent evidence.

Vals published headline values retain its fallback policy; no-fallback variants remain in sources, not companion charts. For example, Opus Vals Index is 70.1 with published fallback answers versus 68.1 without; BioMystery is 79.3 versus 69.3. Zapier also uses provider-default Claude fallbacks. The reasoning studies are not full-board measurements. Code Migration v1.1 uses Pi and weights CLI:COBOL 75:25; Neon is only in the 50+10 task Index subset, not the 120+10 full set.

AutoBax functional and functional+secure scores stay separate for easy/medium/hard. Exact highest effort is unspecified; Fable/Opus context-limit tasks were rerun at high. ExploitGym counts remain separated by two-hour, six-hour and token-budgeted settings; provider-derived token-budget counts are approximate, not controlled-time comparisons.

## Existing filter chips require explicit judgment calls

Exact nonstandard labels remain on bars and in CSV. `none`, `between tools`, and `highest (level not stated)` group under **Not stated**; `highest/high mixed` groups under **max**. These mappings keep the existing controls, not assert equivalence. Nonstandard priced rows use explicit bar prices rather than fabricated effort curves. No chart is hidden for sparse or currently filtered-out coverage.
