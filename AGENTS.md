---
last_updated: 2026-11-18T23-30
---

# Publishing

Currently Gilad is the only user, so just publish when work is done.

# Benchmark updates

- Add relatively serious new benchmarks and rankings when researching models. The current chart count is not a limit. Backfill their published results for models already supported by the project.
- Prefer a benchmark's newer version when it supersedes an older one. Preserve historical results and provenance in `sources/`; do not relabel old scores as the new version.
- Prefer partial knowledge to neatly aligned plots. Include valid results even when they cannot currently be compared with another model; label the limitation instead of withholding the result. Missing model, effort or cost coverage must not suppress available scores. Leave gaps absent, label unspecified effort explicitly, and never infer a curve from a single score.
- Keep genuinely different task sets, versions, scoring rules and harnesses distinguishable. Label lab-reported comparisons and methodological caveats; never invent equivalence or fill gaps with another setting's result.
- Download, read and view all information in each research resource, including anything embedded: images, charts, tables, interactive data widgets and anything else that holds data. Aggressively and recursively download to disk and unbundle the data. Do not stop at the prose or a text-only extraction. Visually cross-check the source figures as well as the generated charts.
- `charts.py` defines the data and renders `docs/index.html` and `docs/data.csv` with `uv run charts.py`. Keep source URLs, retrieval dates, effort settings, units and any transformations in `sources/` snapshots.
