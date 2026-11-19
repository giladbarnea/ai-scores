# Chartography Benchmark Tasks

Chartography is a benchmark for professional visual reasoning: reading the charts that professionals stake decisions on, the way they're read on the job. Each task pairs a real chart image with an expert-written question and golden answer, spanning STEM (including five engineering subfields), Finance / Investing, Manufacturing / Supply Chain, and Healthcare.

### What it tests

Chartography uses domain-native formats rather than standard bar and line charts: Kaplan-Meier curves, candlesticks, contour maps, Sankeys, Bode plots, and more. The questions mirror real professional reads, such as pulling a design wind speed off a contour map or reading a child's height percentile off a growth chart. Answering requires genuinely working the figure, from estimating values against sparsely labeled axes to tracing overlapping flows, using nothing beyond the chart and domain knowledge.

### Why it's hard

Every task was written by someone who reads these charts for a living, with an explicit walkthrough of the calculation path, then independently verified by three additional experts. Golden answers carry expert-set acceptable ranges calibrated to the precision readable in each chart, so grading rewards genuine chart reading rather than lucky rounding. During curation, all 100 tasks defeated at least one of two frontier models. No frontier model scores above 45%.

Read more in the [blog post](https://surgehq.ai/blog/chartography) and see how models perform on the [leaderboard](https://surgehq.ai/benchmarks/chartography).

Built by the [Surge AI](https://www.surgehq.ai) evals team. To evaluate your models on Chartography or build expert-grade benchmarks in your own domains, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

## Overview

- `src/chartography/` — eval harness, built with the [Inspect AI](https://inspect.aisi.org.uk) framework.
- `task_packs/sample_charts/` — two dummy tasks for local dry runs; they demonstrate the dataset format but are not part of the released set (that's on Hugging Face at [`surgeai/chartography`](https://huggingface.co/datasets/surgeai/chartography)). Each YAML spec mirrors the dataset columns (`task_id`, `prompt`, `golden_answer`, `chart_path`, `domain_combined`, `source_type`, `source_url`), with chart images under `charts/`.
- `tests/` — offline structural tests (no network, no keys).

## Quick start

```bash
# 1. Set provider API keys (can also go in `.env`)
export ANTHROPIC_API_KEY=...
export GEMINI_API_KEY=...

# 2. Run the eval on the sample task pack (chart attached inline, no tools)
uv run inspect eval src/chartography/task.py --model anthropic/claude-opus-4-8

# Pick the judge, cap tasks, and raise concurrency
uv run inspect eval src/chartography/task.py \
  --model anthropic/claude-opus-4-8 \
  -T judge_model=google/gemini-3.5-flash \
  -T limit=1 \
  --max-connections 8
```

Pass `-T hf_repo=surgeai/chartography` to run the full task set from Hugging Face instead of the committed sample pack, or `-T task_pack=<dir>` for another local pack.

The scorer reports `accuracy/mean`: the fraction of responses whose final answer matches the golden answer, judged by one model-graded call per sample (the judge sees the question, golden answer, and response — never the chart).

## Pass@K / Pass^K

Run multiple epochs with Inspect's score reducers to compute Pass@K and Pass^K in the same run:

```bash
uv run inspect eval src/chartography/task.py --model ... \
  --epochs 5 --epochs-reducer "mean,pass_at_5,at_least_5"
```

This reports `accuracy/mean` (Pass@1), `accuracy/pass_at_5` (Pass@5, the unbiased [Codex-paper estimator](https://arxiv.org/pdf/2107.03374)), and `accuracy/at_least_5` (Pass^5 — all 5 runs pass).

## Leaderboard Configuration

To match the configuration used in the leaderboard, run the complete task set
with ten runs per task and Gemini 3.5 Flash as the judge:

```bash
uv run inspect eval src/chartography/task.py \
  --model ... \
  --epochs 10 \
  --epochs-reducer "mean,pass_at_10,at_least_10" \
  -T judge_model=google/gemini-3.5-flash
```

For supported models, optionally set the reasoning effort with
`--reasoning-effort ...`.

## Offline checks

Smoke-test the full pipeline without keys using Inspect's mock model (samples report as unscored — the point is exercising the loader/scorer plumbing):

```bash
uv run inspect eval src/chartography/task.py \
  -T limit=2 --model mockllm/model -T judge_model=mockllm/model
```

Structural tests run via:

```bash
uv run python tests/test_offline.py
```

