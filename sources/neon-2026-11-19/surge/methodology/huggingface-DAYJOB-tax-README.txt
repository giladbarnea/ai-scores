---
license: mit
pretty_name: DAYJOB Tax
language:
- en
size_categories:
- n<1K
tags:
- benchmark
- evaluation
- agents
- tax
- dayjob
---

# DAYJOB Overview

DAYJOB is [Surge AI](https://surgehq.ai/)'s benchmark family for long-horizon professional agents. It is designed around rich knowledge work from everyday enterprise: short, realistic workplace requests that require professional judgment, large working environments that require exploration, and much more for agents to figure out.

## DAYJOB: Tax

DAYJOB: Tax evaluates whether AI agents can take a tax engagement from an initial request to a completed deliverable. The full benchmark contains 50 expert-created assignments spanning individual and family tax, small businesses, partnerships, property and investments, estates and trusts, international tax, corporate transactions, and tax review and disputes.

Agents investigate client records, reconcile conflicting information, identify consequential issues, and produce returns, workpapers, technical reviews, and client advice.

**This repository contains 2 sample tasks from the full 50-task benchmark.** To evaluate your models on the full set, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

## Links

- GitHub: [Evaluation harness and setup](https://github.com/surge-ai/dayjob)
- Blog: [Introducing DAYJOB: Tax](https://surgehq.ai/blog/dayjob-tax)
- Leaderboard: [DAYJOB: Tax](https://surgehq.ai/benchmarks/dayjob-tax)

## What it tests

Tax assignments often begin with a brief client request or a handoff from another adviser. Agents must establish the scope of the engagement, determine which records matter, and investigate issues the client may not know to raise.

Across the full set, assignments include tracing cryptocurrency transactions across exchanges and wallets for a cross-border household, allocating losses through layered partnerships, reviewing executive compensation after an acquisition, and reconstructing a tax position in response to an IRS notice.

The supporting materials extend beyond returns and accounting records. Operating agreements, stock ledgers, debt guarantees, dispatch records, vessel-use logs, and client correspondence can all change the analysis. Agents must connect that evidence to their calculations and carry the results into usable deliverables.

## Why it’s hard

A plausible tax answer can still miss the fact that determines the outcome. A prior return may contain an error, a confident staff draft may rely on an unsupported assumption, or an operational log may reveal obligations absent from the client's description.

The tasks require agents to reconcile records across years, entities, and jurisdictions; distinguish established facts from assumptions; and recognize when information is insufficient. Corrections must remain consistent across linked schedules, returns, and advice. Detailed rubrics assess both the analysis and the finished work.

## Overview of full set

The figures below describe the **full benchmark**, not just the two public samples.

| Measure | DAYJOB: Tax |
| --- | --- |
| Tasks in the full benchmark | 50 |
| Public sample tasks in this repository | 2 |
| Total workspace files | 1,789 |
| Average input files per task | 35.8 |
| Median input files per task | 30 |
| Input files per task, range | 12–123 |
| Median rubric criteria per task | 30.5 |
| Published pass threshold | At least 95% of rubric criteria satisfied |
| Task format | Harbor |

File counts include reference materials and files repeated across tasks. The full set contains 1,487 PDFs, 117 Excel workbooks, 38 Word documents, and additional emails, CSVs, JSON records, images, and text documents.

## How the tasks were built

Tax professionals created the assignments from workflows and decisions encountered in practice, developing the supporting records, expected outcomes, and grading criteria. The materials include synthetic documents modeled on the forms and records practitioners use in their work.

As described in the [release post](https://surgehq.ai/blog/dayjob-tax), each task underwent three layers of expert review for correctness, completeness, and solvability. Contributors bring experience in corporate and private-equity taxation, partnership allocations, real estate, individual returns, trusts, and multistate compliance.

## Task format

Tasks use [Harbor format](https://www.harborframework.com/), with assignment instructions, a containerized working environment, and evaluation code. Each task directory contains `instruction.md`, `task.toml`, `environment/`, and `tests/`.

Agents work with local files in a Linux environment equipped for document and spreadsheet processing. During task execution, network access is restricted to explicitly allowed model API hosts; browsing and package downloads are blocked.

## Running the benchmark

Follow the [DAYJOB GitHub setup instructions](https://github.com/surge-ai/dayjob) to install the harness and configure the model endpoint and grading credentials.

After completing that setup, run an individual sample from the harness directory:

```bash
uv run harbor run \
  -p "<path/to/sample-task>" \
  -a harbor_agents:HarborInstalledAgent \
  -m "<litellm-model>" \
  --allow-agent-host "$LLM_HOST" \
  --ve REWARDKIT_MODEL=anthropic/claude-opus-4-8 \
  --ve ANTHROPIC_API_KEY="$ANTHROPIC_API_KEY"
```

Replace the task path and model placeholders, and set `LLM_HOST` and the required API credentials as documented in the harness. For comparisons with published results, use the full benchmark and the documented evaluation configuration, including five attempts per task.

See the [Harbor documentation](https://www.harborframework.com/docs) for additional execution options.

## Evaluation

Each task has a detailed rubric covering the required analysis and deliverables. The [published tax evaluation](https://surgehq.ai/blog/dayjob-tax) reports pass@1 at a 95% rubric threshold: an attempt passes when it satisfies at least 95% of the task's criteria.

The two public samples illustrate the task format and workflow. Results on these samples alone do not constitute a score on the full benchmark.

## Intended use

DAYJOB: Tax is for held-out evaluation. Please keep the tasks, supporting files, rubrics, and derived materials out of training, fine-tuning, reinforcement learning, and distillation datasets, and do not use them for training-time checkpoint selection.

For access to the full 50-task benchmark, evaluation inquiries, or benchmarks in your own domain, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

Built by Surge AI.