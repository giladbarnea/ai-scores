---
license: mit
pretty_name: DAYJOB Law
language:
- en
size_categories:
- n<1K
tags:
- benchmark
- evaluation
- agents
- law
- legal
- dayjob
---

# DAYJOB Overview

DAYJOB is [Surge AI](https://surgehq.ai/)'s benchmark family for long-horizon professional agents. It is designed around rich knowledge work from everyday enterprise: short, realistic workplace requests that require professional judgment, large working environments that require exploration, and much more for agents to figure out.

## DAYJOB: Law

DAYJOB: Law evaluates whether AI agents can take a legal matter from a brief request to a finished work product. The full benchmark contains 71 assignments created by practicing lawyers, spanning corporate transactions, litigation, criminal defense, employment disputes, intellectual property, estate matters, and more.

Agents investigate case and deal files, apply the governing law, reconcile contradictory evidence, and produce memos, opinion letters, briefs, agreements, and client advice that a lawyer could actually use.

**This repository contains 2 sample tasks from the full 71-task benchmark.** To evaluate your models on the full set, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

## Links

- GitHub: [Evaluation harness and setup](https://github.com/surge-ai/dayjob)
- Blog: [DAYJOB: Law | Can AI do a lawyer’s job?](https://surgehq.ai/blog/dayjob-law)
- Leaderboard: [DAYJOB: Law](https://surgehq.ai/benchmarks/dayjob-law)

## What it tests

Legal assignments often arrive as a one-line request from a partner or client. A prompt can be as short as "Can you draft the sentencing exposure memo for Whitfield?" Agents must work out which questions to ask, which evidence to investigate, and which legal issues matter, without a step-by-step checklist.

Across the full set, assignments include pricing an investment against a company's conflicting ownership records, estimating a client's sentencing exposure across several related charges, determining whether a donor owned the copyrights she purported to transfer, and investigating whether a pet trust's beneficiary was quietly replaced.

The case files extend well beyond the core documents. Contracts, court filings, stock ledgers, wills, deeds of gift, emails, receipts, and text messages can all change the analysis. Agents must connect that evidence to the law and carry the result into a usable work product.

## Why it’s hard

Knowing black-letter law is rarely the bottleneck. Agents often identify the right issues but still reach the wrong conclusions: spotting a disputed block of shares and then ignoring it when pricing a deal, or recognizing the correct charges and then overstating how the sentences combine.

The files also contain outdated records, irrelevant documents, and misleading clues. Agents must distinguish genuine risks from distractions, reconcile contradictory evidence, and recognize when critical information is missing or a fact remains unproven. Detailed rubrics assess both the analysis and the finished work.

## Overview of full set

The figures below describe the **full benchmark**, not just the two public samples.

| Measure | DAYJOB: Law |
| --- | --- |
| Tasks in the full benchmark | 71 |
| Public sample tasks in this repository | 2 |
| Total workspace files | 2,638 |
| Total workspace size | 903 MB |
| Average input files per task | 37.2 |
| Median input files per task | 28 |
| Input files per task, range | 6–160 |
| Median rubric criteria per task | 67 |
| Published pass threshold | At least 95% of rubric criteria satisfied |
| Task format | Harbor |

File counts include reference materials and files repeated across tasks. The full set contains 2,098 PDFs, 273 Word documents, 109 Excel workbooks, and 97 emails, along with images, CSVs, text documents, and archives.

## How the tasks were built

Experienced lawyers wrote the assignments to reflect substantive legal work, developing the case files, expected outcomes, and grading criteria. The materials are synthetic documents modeled on the records practitioners handle in their work.

Contributors bring experience in intellectual property and corporate transactions, immigration and worker-rights advocacy, and criminal defense and appellate litigation, among other practice areas.

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

Each task has a detailed rubric covering the required analysis and deliverables. The [published law evaluation](https://surgehq.ai/blog/dayjob-law) reports pass@1 at a 95% rubric threshold: an attempt passes when it satisfies at least 95% of the task's criteria.

The two public samples are assignments discussed in the release post: a sentencing exposure memo for a client facing retail-theft and robbery charges, and a copyright demand that turns on whether the donor owned the rights she gave away. They illustrate the task format and workflow. Results on these samples alone do not constitute a score on the full benchmark.

## Intended use

DAYJOB: Law is for held-out evaluation. Please keep the tasks, supporting files, rubrics, and derived materials out of training, fine-tuning, reinforcement learning, and distillation datasets, and do not use them for training-time checkpoint selection.

For access to the full 71-task benchmark, evaluation inquiries, or benchmarks in your own domain, contact [benchmarks@surgehq.ai](mailto:benchmarks@surgehq.ai).

Built by Surge AI.
