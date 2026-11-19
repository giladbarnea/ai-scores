---
license: mit
pretty_name: DAYJOB Healthcare
---

# DAYJOB Overview

DAYJOB is a benchmark family created by [Surge AI](https://surgehq.ai/) designed around rich knowledge work from everyday enterprise: short, realistic workplace requests that require professional judgment, large working environments that require exploration, and much more for agents to figure out.

Instead of telling models exactly what to do, DAYJOB asks whether they can exercise professional judgment.

## DAYJOB: Healthcare

DAYJOB: Healthcare tests whether AI agents can handle professional healthcare work from a brief handoff. It contains 50 expert-designed assignments that require agents to interpret substantial supporting materials, identify what matters, and exercise clinical judgment.

The assignments represent work estimated to take a human professional 13.6 hours on average. Tasks are packaged in Harbor format, with setup and evaluation instructions available in the accompanying GitHub repository.

## Links

- GitHub: [link](https://github.com/surge-ai/dayjob)
- Blog: [link](https://surgehq.ai/blog/dayjob)
- Leaderboard: [link](https://surgeai.webflow.io/benchmarks/dayjob-healthcare)

## What it tests

Healthcare work often starts with a colleague’s request that assumes shared context. Answering it well requires understanding the record and recognizing when something in it should change the plan.

DAYJOB leaves that responsibility with the agent. Prompts average 49 words, while the supporting materials average nearly 20 files per assignment. Agents must determine what the request requires and work through the relevant information to complete it.

## Why it’s hard

The initial request may leave important questions unasked. Relevant details can be scattered across records, and an incomplete examination or conflicting information may warrant reconsidering an otherwise reasonable plan.

Completing these assignments requires judgment about what to trust, what needs further investigation, and when to challenge an assumption in the handoff. Detailed rubrics check whether the agent follows through on those decisions.

## Overview of full set

| Measure | DAYJOB: Healthcare |
| --- | --- |
| Tasks | 50 |
| Average prompt length | 49 words |
| Average input files per task | 19.8 |
| Average estimated human completion time | 13.6 hours |
| Median rubric criteria per task | 47.5 |
| Task completion threshold | 100% of rubric criteria satisfied |
| Task format | Harbor |

## How the tasks were built

Assignments were created by experts with firsthand experience doing the work being evaluated, using the problems, source materials, decisions, and deliverables they encounter professionally.

Every task went through three layers of review for correctness, completeness, and solvability. Each has a detailed rubric specifying the requirements for successful completion.

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

DAYJOB: Healthcare is intended for held-out evaluation. Please exclude its tasks, supporting materials, rubrics, and derivatives from training, fine-tuning, reinforcement learning, and distillation datasets. Do not use it to select checkpoints during training. This dataset includes a benchmark canary for provenance tracking.

This HuggingFace repo contains 3 sample tasks. Please contact benchmarks@surgehq.ai to evaluate your models on the full set.

Built by the Surge AI team. For evaluation inquiries or benchmarks in your own domain, contact benchmarks@surgehq.ai.


