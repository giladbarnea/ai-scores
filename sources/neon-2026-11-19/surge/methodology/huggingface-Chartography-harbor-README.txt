---
license: cc-by-4.0
pretty_name: Chartography
language:
- en
size_categories:
- n<1K
tags:
- benchmark
- evaluation
- chart-understanding
- visual-reasoning
---

# Chartography

Chartography is a benchmark from [Surge AI](https://surgehq.ai/) that measures professional visual reasoning over the charts professionals stake decisions on: Sankey diagrams, candlestick charts, contour maps, back-trajectories, Bode plots, and more.

The full benchmark contains 100 real-world prompts and chart images spanning 12 professional domains, including Finance & Investing, Healthcare, Manufacturing & Supply Chain, and STEM fields from Chemistry to Geosciences to Electrical Engineering.

**This repository contains 2 sample tasks from the full 100-task benchmark.** To evaluate your models on the full set, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

## Links

- Blog: [Chartography](https://surgehq.ai/blog/chartography)
- Leaderboard: [Chartography](https://surgehq.ai/benchmarks/chartography)

## What it tests

Existing chart benchmarks are largely saturated because direct extraction of labeled data points is essentially solved. Chartography targets what remains hard: estimating values against sparsely labeled axes, tracing overlapping flows to their sources, reading 3D surface plots through their projected gridlines, and multi-part calculations where each step depends on a separate visual read.

Answering requires no outside data, only the chart and the chart literacy a domain specialist carries with them.

## Why it's hard

Every task was written by a working professional in the relevant field and reviewed by several more. Questions demand careful visual reads rather than lookups, and errors compound across multi-step calculations.

When Chartography was first released, no frontier model scored above 45%.

## Overview of full set

The figures below describe the **full benchmark**, not just the two public samples.

| Measure | Chartography |
| --- | --- |
| Tasks in the full benchmark | 100 |
| Public sample tasks in this repository | 2 |
| Unique charts | 100 |
| Professional domains | 12 |
| Task format | Harbor |

## How the tasks were built

Authors submitted explicit walkthroughs of the calculation path to each answer. Numerical answers carry expert-set acceptable ranges (for example, "150 mph, acceptable 140–150 mph"), so grading rewards genuine chart reading rather than pixel-perfect luck. Charts were either sourced from publicly available material or created by the expert task author.

## Task format

Tasks use [Harbor format](https://www.harborframework.com/), with the prompt, a containerized environment containing the chart image, and evaluation code. Each task directory contains `instruction.md`, `task.toml`, `environment/`, and `tests/`.

## Running the benchmark

Tasks can be run with the [Harbor](https://www.harborframework.com/docs) CLI. Use a vision-capable model, and see the Harbor documentation for agent, model, and execution options. For comparisons with published results, use the full benchmark and the documented evaluation configuration.

## Evaluation

Each task has an expert-written golden answer. A judge compares the model's answer with the golden answer; where the golden answer specifies an acceptable range, any value within that range is scored as correct.

The two public samples illustrate the task format and workflow. Results on these samples alone do not constitute a score on the full benchmark.

## Licensing

Prompts, golden answers, metadata, and expert-created charts are released under CC BY 4.0. Charts sourced from publicly available material remain the property of their original authors or publishers, are not covered by that license, and are included only for non-commercial research and evaluation of chart-understanding systems. Rights holders who want an image removed can open a discussion on this repository.

## Intended use

Chartography is for held-out evaluation. Please keep the tasks, supporting files, answers, and derived materials out of training, fine-tuning, reinforcement learning, and distillation datasets, and do not use them for training-time checkpoint selection.

For access to the full 100-task benchmark, evaluation inquiries, or benchmarks in your own domain, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

Built by Surge AI.
