---
license: mit
pretty_name: DAYJOB Finance
---

# DAYJOB Overview

DAYJOB is a benchmark family created by [Surge AI](https://surgehq.ai/) designed around rich knowledge work from everyday enterprise: short, realistic workplace requests that require professional judgment, large working environments that require exploration, and much more for agents to figure out.

Instead of telling models exactly what to do, DAYJOB asks whether they can exercise professional judgment.

## DAYJOB: Finance

DAYJOB: Finance tests whether AI agents can carry out professional financial work from a brief request. It contains 80 expert-designed assignments that require agents to investigate supporting materials, reconcile conflicting information, and produce work that holds up to detailed review.

The assignments represent work estimated to take a human professional 16.6 hours on average. Tasks are packaged in Harbor format, with setup and evaluation instructions available in the accompanying GitHub repository.

## Links

- GitHub: [link](https://github.com/surge-ai/dayjob)
- Blog: [link](https://surgehq.ai/blog/dayjob)
- Leaderboard: [link](https://surgeai.webflow.io/benchmarks/dayjob-finance)

## What it tests

Financial assignments often arrive without instructions for which sources to trust or how to approach the analysis. DAYJOB asks agents to make those decisions themselves.

Prompts average 81 words, and each assignment includes an average of 25.7 input files. Agents must establish the scope of the work, connect information across documents and spreadsheets, and determine how their findings affect the final recommendation or deliverable.

## Why it’s hard

A financial analysis can look internally consistent while relying on the wrong source or an unchecked assumption. Finding those problems requires tracing figures back to their origins and understanding how they were used.

DAYJOB assignments require that scrutiny across work spanning many files and analytical steps. Agents must keep track of dependencies as the analysis develops and carry corrections through to the finished work. Detailed rubrics make omissions consequential, even when much of the assignment is done correctly.

## Overview of full set 

| Measure | DAYJOB: Finance |
| --- | --- |
| Tasks | 80 |
| Average prompt length | 81 words |
| Average input files per task | 25.7 |
| Average estimated human completion time | 16.6 hours |
| Median rubric criteria per task | 57.5 |
| Task completion threshold | 100% of rubric criteria satisfied |
| Task format | Harbor |

## How the tasks were built

Assignments were created by finance experts with firsthand experience doing the work being evaluated, including professionals with backgrounds in institutional asset management, quantitative investing, and infrastructure finance.

Tasks are grounded in the problems, source materials, decisions, and deliverables these professionals encounter on the job. Every task went through three layers of review for correctness, completeness, and solvability, and has a detailed rubric specifying the requirements for successful completion.

## Task format

Tasks are packaged in [Harbor format](https://www.harborframework.com/docs/tasks), which brings together the assignment instructions, working environment, and evaluation code.

## Running the benchmark

Start with the DAYJOB GitHub repository. It provides the setup and evaluation workflow, including dependencies, model configuration, and instructions for running the benchmark and collecting results.

Once the required setup is complete, an individual task can be run through Harbor:

```bash
harbor run \
  -p "<path/to/task>" \
  -a "<agent>" \
  -m "<model>"
```

Replace the placeholders with the local task directory, agent, and model you want to evaluate. Use the configurations documented in the DAYJOB repository when comparing results with the published leaderboard.

For details on Harbor’s execution model and supported agents, see the [Harbor documentation](https://www.harborframework.com/docs).

## Evaluation

Each assignment is evaluated against a detailed, task-specific rubric.

The benchmark score is the percentage of tasks passed with 100% rubric satisfaction.


## Intended use

DAYJOB: Finance is intended for held-out evaluation. Please exclude its tasks, supporting materials, rubrics, and derivatives from training, fine-tuning, reinforcement learning, and distillation datasets. Do not use it to select checkpoints during training. This dataset includes a benchmark canary for provenance tracking.

This HuggingFace repo contains 3 sample tasks. Please contact benchmarks@surgehq.ai to evaluate your models on the full set. 

Built by the Surge AI team. For evaluation inquiries or benchmarks in your own domain, contact benchmarks@surgehq.ai.
