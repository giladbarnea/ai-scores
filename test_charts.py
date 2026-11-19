"""Regression checks for sparse benchmarks, rankings and complete score exports."""
import csv
import html
import json
import re
import tempfile
import unittest
from pathlib import Path

import charts


class ChartCoverageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        charts.configure_fonts()

    def test_single_model_with_partial_effort_coverage_renders(self) -> None:
        metric = charts.Metric("Sparse benchmark", "% · example", {
            charts.GPT_6_ASTRA: [91.0, None, 93.0, None, 94.0],
        }, (80, 100), 5)
        rendered = charts.plot_html(metric, charts.LAYOUTS[0], "effort")
        self.assertIn("GPT-6 Astra", rendered)
        self.assertIn("94.0", rendered)

    def test_sparse_chart_points_expose_their_actual_thinking_levels(self) -> None:
        metric = charts.Metric("Sparse benchmark", "% · example", {
            charts.GPT_6_ASTRA: [91.0, None, 93.0, None, 94.0],
        }, (80, 100), 5)
        rendered = charts.plot_html(metric, charts.LAYOUTS[1], "effort")
        levels = re.findall(r'<g class="marker[^\"]*" data-level="([^\"]+)"', rendered)
        self.assertEqual(set(levels), {"low", "high", "max"},
                         "A level filter must distinguish the three actual points without inventing missing efforts")

    def test_dense_elo_chart_renders_with_the_full_model_name_column(self) -> None:
        metric = next(metric for metric in charts.CURVES if metric.name == "AA-Briefcase")
        rendered = charts.plot_html(metric, charts.LAYOUTS[0], "effort")
        self.assertIn("1469", rendered, "A crowded nearest-score label must find a farther placement, not abort the build")

    def test_reported_ranking_can_use_an_elo_scale(self) -> None:
        metric = charts.ReportedMetric("Example ranking", "Elo", {
            charts.GPT_6_ASTRA: (1318.0, "not stated"),
        }, x_max=1500, tick_step=250, decimals=0)
        rendered = charts.bar_plot_html(metric, charts.LAYOUTS[0])
        self.assertIn("1318", rendered)
        self.assertIn("1500", rendered)
        self.assertIn("not stated", rendered)

    def test_csv_includes_reported_scores_at_their_actual_effort(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data.csv"
            charts.write_table(destination)
            with destination.open() as file:
                rows = list(csv.DictReader(file))
        matches = [row for row in rows if row["metric"] == "Vals Index" and row["model"] == "GPT-6 Astra" and row["measure"] == "score"]
        self.assertEqual(len(matches), 1, "The Vals bar must also be present in the downloadable data")
        self.assertEqual(float(matches[0]["max"]), 65.02)
        self.assertTrue(all(matches[0][level] == "" for level in ["low", "medium", "high", "xhigh"]))

    def test_every_supported_snapshot_point_is_available_to_the_page(self) -> None:
        snapshot = json.loads((Path(__file__).parent / "sources/gpt62.json").read_text())
        data = charts.chart_data()
        model_names = {model["slug"]: model["name"] for model in data["models"]}
        metrics = {metric["name"]: metric for metric in data["metrics"].values()}
        for name, scores in snapshot["scores"].items():
            if name == "CursorBench 4.0":
                continue
            actual = {model_names[slug]: values for slug, values in metrics[name]["scores"].items()}
            for model, values in scores.items():
                if model not in model_names.values():
                    continue
                with self.subTest(metric=name, model=model):
                    self.assertEqual(actual.get(model), values, "Published sparse points must not be dropped")

    def test_reported_benchmark_prices_are_available_in_cost_view_and_csv(self) -> None:
        metric = next(metric for metric in charts.REPORTED if metric.name == "Vals Index")
        rendered = charts.bar_panel_html(metric)
        self.assertIn("cost-point", rendered, "Published Vals prices must be usable in cost view")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data.csv"
            charts.write_table(destination)
            with destination.open() as file:
                rows = list(csv.DictReader(file))
        row = next(row for row in rows if row["metric"] == "Vals Index" and row["model"] == "GPT-6.2 Sol" and row["measure"] == "cost_usd")
        self.assertEqual(float(row["max"]), 3.18)
        self.assertIn("per test", row["unit_and_source"])

    def test_argon_is_absent_from_the_live_dataset_and_exports(self) -> None:
        self.assertNotIn("Gemini 4 Argon", [model["name"] for model in charts.chart_data()["models"]],
                         "Retired Argon must not remain selectable or plotted")
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data.csv"
            charts.write_table(destination)
            self.assertNotIn("Gemini 4 Argon", destination.read_text(), "The export must retire Argon too")

    def test_page_groups_every_chart_once_by_what_its_task_asks(self) -> None:
        page = charts.page_html()
        sections = re.findall(r"<section><h2>(.*?)</h2>(.*?)</section>", page, flags=re.DOTALL)
        charts_by_section = {html.unescape(heading): [html.unescape(name) for name in re.findall(r"<h3>(.*?)</h3>", body)]
                             for heading, body in sections}
        self.assertEqual(list(charts_by_section), ["Aggregates", "Intelligence & knowledge", "Coding & security",
                                                   "Science & engineering", "Machine-learning research",
                                                   "Professional work", "Health", "Multimodal tasks"])
        placed = [name for names in charts_by_section.values() for name in names]
        self.assertEqual(sorted(placed), sorted(metric.name for metric in [*charts.CURVES, *charts.REPORTED]),
                         "Every declared chart must appear exactly once")
        self.assertGreater(len(placed), 50, "New benchmarks must not be limited to the historical chart count")
        for heading, name in [("Aggregates", "Vals Index"), ("Intelligence & knowledge", "ARC-AGI-2"),
                              ("Professional work", "AutomationBench 1.0.6"), ("Professional work", "MKA"),
                              ("Science & engineering", "SciCode"), ("Health", "MentalHealthBench"),
                              ("Coding & security", "ExploitBench \u2013 Internal Port (June\u2013August 2026)"),
                              ("Machine-learning research", "MLE-Bench Revised"), ("Multimodal tasks", "AA-3D")]:
            self.assertIn(name, charts_by_section[heading], f"{name} belongs under {heading}")

    def test_neon_preserves_real_aa_efforts_and_costs(self) -> None:
        metric = next(metric for metric in charts.CURVES if metric.name == "AA Intelligence Index")
        self.assertEqual(metric.scores[charts.GEMINI_4_NEON], [44.1, 54.9, 59.6, 61.4, None])
        self.assertEqual(metric.costs[charts.GEMINI_4_NEON], [830.0, 1870.0, 3690.0, 7790.0, None])
        self.assertEqual(len(charts.cost_points(metric, charts.GEMINI_4_NEON)), 4)

    def test_cursor_41_replaces_40_without_relabeling_old_scores(self) -> None:
        metric = next(metric for metric in charts.CURVES if metric.name == "CursorBench 4.1")
        self.assertEqual(metric.scores[charts.GEMINI_4_NEON], [45.5, 57.7, 63.7, 65.4, None])
        self.assertEqual(metric.costs[charts.GEMINI_4_NEON], [1.26, 3.07, 6.54, 10.67, None])
        self.assertEqual(metric.scores[charts.CLAUDE_OPUS_5_5][-1], 58.1)
        self.assertNotIn("CursorBench 4.0", [metric.name for metric in charts.CURVES])
        historical = json.loads((Path(__file__).parent / "sources/gpt62.json").read_text())
        self.assertEqual(historical["scores"]["CursorBench 4.0"]["Opus 5.5"][-1], 57.8)

    def test_mai_code_2_has_only_the_approved_deepswe_point(self) -> None:
        points = [(metric.name, metric.scores[charts.MAI_CODE_2]) for metric in charts.CURVES
                  if charts.MAI_CODE_2 in metric.scores]
        self.assertEqual(points, [("DeepSWE v1.1", [None, None, None, None, 73.2])])
        self.assertFalse(any(charts.MAI_CODE_2 in metric.scores for metric in charts.REPORTED))
        metric = next(metric for metric in charts.CURVES if metric.name == "DeepSWE v1.1")
        self.assertEqual(metric.costs[charts.MAI_CODE_2], [None, None, None, None, 0.618])
        self.assertIn("Copilot CLI 1.0.102", metric.unit_and_source)

    def test_distinct_google_runs_do_not_borrow_costs(self) -> None:
        metric = next(metric for metric in charts.REPORTED if metric.name == "LVBench (Google)")
        self.assertEqual(metric.scores[charts.GEMINI_4_NEON], (89.0, "xhigh"))
        self.assertIsNone(metric.costs)
        self.assertIn("vision-only", metric.unit_and_source)

    def test_nonstandard_reported_effort_keeps_its_price_and_filter(self) -> None:
        metric = next(metric for metric in charts.REPORTED if metric.name == "AutomationBench 1.0.6 (nonstandard efforts)")
        self.assertEqual(metric.scores[charts.GPT_6_ASTRA], (25.27, "none"))
        rendered = charts.bar_panel_html(metric)
        self.assertIn('data-level="not-stated"', rendered)
        self.assertIn("between tools", rendered)
        self.assertIn("none", rendered)
        self.assertIn("$1.28", rendered)
        self.assertNotIn("cost-point", rendered, "Nonstandard efforts retain labeled bars, not an invented effort curve")
        self.assertEqual(charts.filter_level("none"), "not-stated")
        self.assertEqual(charts.filter_level("highest/high mixed"), "max")

    def test_a_chart_left_out_of_every_section_fails_the_build(self) -> None:
        with self.assertRaisesRegex(ValueError, "Missing: .*AA Intelligence Index"):
            charts.sections_from({"Only": [metric.name for metric in charts.CURVES[1:]]})

    def test_csv_names_each_metric_section(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data.csv"
            charts.write_table(destination)
            with destination.open() as file:
                rows = list(csv.DictReader(file))
        categories = {row["metric"]: row["category"] for row in rows}
        self.assertEqual(categories["SciCode"], "science & engineering")
        self.assertEqual(categories["NanoGPT v5"], "machine-learning research")
        self.assertEqual(len(set(categories.values())), 8)

    def test_csv_preserves_scores_with_an_unspecified_effort(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "data.csv"
            charts.write_table(destination)
            with destination.open() as file:
                rows = list(csv.DictReader(file))
        row = next(row for row in rows if row["metric"] == "GPQA Diamond (OpenAI)" and row["model"] == "GPT-6.2 Astra")
        self.assertEqual(float(row["reported_score"]), 97.0)
        self.assertEqual(row["reported_effort"], "not stated")
        self.assertTrue(all(row[level] == "" for level in charts.EFFORT_LEVELS), "Unknown effort must not become max")


if __name__ == "__main__":
    unittest.main()
