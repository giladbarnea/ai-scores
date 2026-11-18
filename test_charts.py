"""Regression checks for sparse benchmarks, rankings and complete score exports."""
import csv
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
        metric = next(metric for metric in charts.INTELLIGENCE if metric.name == "AA-Briefcase")
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

    def test_every_published_snapshot_point_is_available_to_the_page(self) -> None:
        snapshot = json.loads((Path(__file__).parent / "sources/gpt62.json").read_text())
        data = charts.chart_data()
        model_names = {model["slug"]: model["name"] for model in data["models"]}
        metrics = {metric["name"]: metric for metric in data["metrics"].values()}
        for name, scores in snapshot["scores"].items():
            actual = {model_names[slug]: values for slug, values in metrics[name]["scores"].items()}
            for model, values in scores.items():
                with self.subTest(metric=name, model=model):
                    self.assertEqual(actual.get(model), values, "Published sparse points must not be dropped")

    def test_reported_benchmark_prices_are_available_in_cost_view_and_csv(self) -> None:
        metric = next(metric for metric in charts.REPORTED["Intelligence"] if metric.name == "Vals Index")
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
