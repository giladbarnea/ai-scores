---
license: apache-2.0
language:
- en
task_categories:
- question-answering
tags:
- code
- software-engineering
- coding-agents
- benchmark
- rubric-evaluation
- swe-atlas
pretty_name: SWE-Atlas-QnA-AA
size_categories:
- n<1K
configs:
- config_name: default
  data_files:
  - split: test
    path: data/test-*.parquet
dataset_info:
  config_name: default
  splits:
  - name: test
    num_examples: 124
---

# SWE-Atlas-QnA-AA

SWE-Atlas-QnA-AA is Scale AI's [SWE-Atlas-QnA](https://huggingface.co/datasets/ScaleAI/SWE-Atlas-QnA)
as graded in the [Artificial Analysis Coding Agent Index](https://artificialanalysis.ai/agents/coding-agents).
The task set is the same as upstream (same questions, repos and pinned commits). The grading
changes are there to improve the stability and consistency of verdicts.

Scale's paper: [SWE Atlas: Benchmarking Coding Agents Beyond Issue Resolution](https://arxiv.org/abs/2605.08366).
Code and task packages: [github.com/scaleapi/SWE-Atlas](https://github.com/scaleapi/SWE-Atlas).

## Unchanged from upstream

- The 124 tasks: questions, repositories, pinned base commits, Docker images and reference answers.
- The 1,306 rubric criteria: ids, order, polarity and importance.
- Scoring: a task is resolved only if every criterion is met (Task Resolve Rate). No partial credit.

## Grading methodology

- **Judge:** GPT-6 Luna (xhigh) instead of Claude Opus 4.5.
- **5 votes per criterion**, majority vote wins. A negative criterion's polarity is applied after
  the vote.
- **Structured outputs:** the judge replies in a fixed JSON format (`reason`, `evidence`,
  `verdict`), giving its reasoning and supporting quotes from the answer before the YES/NO verdict.
- **Answer date** in the prompt, so "latest"/"fresh" are judged as of the run.
- **Observed results:** where a criterion asks for observed or measured results, results inferred
  from reading the code don't count; results the answer reports from running something do.

The full configuration (model, voting, output schema, prompts) is in
[`rubric_evaluation_config.yaml`](rubric_evaluation_config.yaml). Scale's original is the previous
version of that file in the commit history.

## Criteria

127 of 1,306 reworded or adjusted:

- **Stability (75):** clearer wording where judges often split votes or read the criteria
  differently.
- **Precision (52):** small tweaks so the wording better aligns with the code at the pinned commit.

These changes came from several rounds of audits on our rollouts and re-testing against the code
and real answers. We kept the original wording where the evidence wasn't clear-cut.

This dataset also includes a fix from Scale's GitHub repo:
[`9acc18e`](https://github.com/scaleapi/SWE-Atlas/commit/9acc18e73b2990306ceb7018a41adc0ee1e6cfa6)
("Fix inverted QnA rubric polarity", 16 July 2026) corrects two negative criteria in the grafana/k6
task (`6905333b74f22949d97baa22`) that were phrased as "Avoids ...", which inverts their meaning
under the negative-criterion rule. These two items are marked `scale-correction`.

Each rubric item records Scale's text and the kind of change (below).

## Schema

Columns are Scale's, unchanged.

| Column | Type | Description |
|---|---|---|
| `task_id` | string | Unique 24-char hex identifier |
| `prompt` | string | The question presented to the agent |
| `reference_answer` | string | Expert-written reference answer |
| `repository_url` | string | GitHub repository (`owner/name`) |
| `repository_base_commit` | string | 40-char commit SHA the environment is pinned to |
| `language` | string | `go`, `python`, `c` or `ts` |
| `category` | string | Task category |
| `rubric` | string (JSON) | Evaluation criteria (see below) |
| `docker_image` | string | Docker image for the sandboxed environment, with the repository at `/app` |

### Rubric format

`rubric` is a JSON array. Each item keeps Scale's `id`, `title` and `annotations` and adds
`original_title` and `change`:

```json
{
  "id": "4ca20ef4bbf52c6414a7478d688d08c3",
  "title": "1.7: States that kitty sets environment variables KITTY_PID, KITTY_LISTEN_ON, and KITTY_WINDOW_ID for child processes.",
  "annotations": {
    "type": "positive hli verifier",
    "importance": "must have"
  },
  "original_title": "1.7: States that shell integration works through environment variables KITTY_PID, KITTY_LISTEN_ON, and KITTY_WINDOW_ID that kitty sets for child processes.",
  "change": "precision"
}
```

- `title`: the criterion text we grade (the judge gets it without the `1.7: ` numbering).
- `original_title`: Scale's text. Equal to `title` when unchanged.
- `change`: `null`, `stability`, `precision` or `scale-correction`.
- `annotations.type`: `positive hli verifier` (the answer must make the claim) or
  `negative hli verifier` (it must not). A negative criterion is met when the judge's verdict is NO.
- `annotations.importance`: always `must have`.

## Running

Each `docker_image` holds the repository and its dependencies at `/app`. Reset to the pinned
commit before the agent starts:

```bash
cd /app
git config --global --add safe.directory /app
git restore .
git reset --hard <repository_base_commit>
git clean -fdq
```

We run each coding agent through its own harness on the task `prompt` and grade its written answer
with the judge above. See the
[Coding Agent Index methodology](https://artificialanalysis.ai/methodology/coding-agents-benchmarking).
Scale's SWE-Agent config, [`default_qa_config.yaml`](default_qa_config.yaml), is kept for
reference; we don't use it.

## Files

- `data/test-00000-of-00001.parquet`: the 124 tasks with the SWE-Atlas-QnA-AA rubric text.
- `rubric_evaluation_config.yaml`: judge configuration.
- `default_qa_config.yaml`: Scale's SWE-Agent config, unchanged.
- `LICENSE`, `NOTICE`.

## Citation

SWE-Atlas-QnA is by Scale AI. Please cite their paper, and credit Artificial Analysis for the
SWE-Atlas-QnA-AA grading.

```bibtex
@misc{raghavendra2026sweatlasbenchmarkingcoding,
      title={SWE Atlas: Benchmarking Coding Agents Beyond Issue Resolution},
      author={Mohit Raghavendra and Soham Dan and Miguel Romero Calvo and Yannis Yiming He and Johannes Baptist Mols and Gautam Anand and Cole McCollum and Edgar Arakelyan and Vijay Bharadwaj and Andrew Park and Jeff Da and MohammadHossein Rezaei and Bing Liu and Brad Kenstler and Yunzhong He},
      year={2026},
      eprint={2605.08366},
      archivePrefix={arXiv},
      primaryClass={cs.LG},
      url={https://arxiv.org/abs/2605.08366},
}
```

## License

Apache 2.0, same as upstream. See `LICENSE` and `NOTICE`.
