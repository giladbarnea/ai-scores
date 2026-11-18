#!/usr/bin/env -S uv run
# /// script
# requires-python = "==3.12.*"
# dependencies = ["matplotlib"]
# ///
"""Render benchmark scores by reasoning effort as one interactive HTML page: HTML, CSS and inline SVG, no JavaScript."""

import csv
import html
import io
import itertools
import json
import math
import re
from collections.abc import Iterable, Iterator
from dataclasses import dataclass
from pathlib import Path
from string import Template

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager
from matplotlib.artist import Artist
from matplotlib.axes import Axes
from matplotlib.backend_bases import RendererBase
from matplotlib.lines import Line2D
from matplotlib.path import Path as MatplotlibPath
from matplotlib.text import Annotation, Text
from matplotlib.transforms import Bbox

OUTPUT_DIRECTORY = Path(__file__).parent / "docs"  # GitHub Pages serves this folder


@dataclass(frozen=True)
class Color:
    """A themeable color: the SVG is drawn in the light value, then each light value becomes var(--variable)."""
    variable: str
    light: str
    dark: str


SURFACE = Color("surface", "#fcfcfb", "#1a1a19")
PAGE = Color("page", "#f9f9f7", "#0d0d0d")
TEXT_PRIMARY = Color("ink-1", "#0b0b0b", "#ffffff")
TEXT_SECONDARY = Color("ink-2", "#52514e", "#c3c2b7")
TEXT_MUTED = Color("ink-3", "#898781", "#898781")
GRIDLINE = Color("grid", "#e1e0d9", "#2c2c2a")
BASELINE = Color("baseline", "#c3c2b7", "#383835")
BORDER = Color("border", "rgba(11,11,11,0.10)", "rgba(255,255,255,0.10)")

EFFORT_LEVELS = ["low", "medium", "high", "xhigh", "max"]


def slugify(text: str) -> str:
    """
    >>> slugify("GPT-5.6 Sol")
    'gpt-5-6-sol'
    """
    return re.sub(r"[^a-z0-9]+", "-", text.lower()).strip("-")


@dataclass(frozen=True)
class Model:
    name: str
    color: Color

    @property
    def slug(self) -> str:
        return slugify(self.name)


GPT_6_ASTRA = Model("GPT-6 Astra", Color("series-2", "#eb6834", "#d95926"))
GPT_6_2_ASTRA = Model("GPT-6.2 Astra", Color("series-8", "#bd3535", "#f07770"))
CLAUDE_FABLE_5_2 = Model("Fable 5.2", Color("series-4", "#eda100", "#c98500"))
CLAUDE_OPUS_5_5 = Model("Opus 5.5", Color("series-5", "#e87ba4", "#d55181"))
GPT_6_1_SOL = Model("GPT-6.1 Sol", Color("series-6", "#008300", "#008300"))
GPT_6_2_SOL = Model("GPT-6.2 Sol", Color("series-9", "#75940c", "#a5c93d"))
CLAUDE_SONNET_5_5 = Model("Sonnet 5.5", Color("series-7", "#4a3aa7", "#9085e9"))
GEMINI_4_ARGON = Model("Gemini 4 Argon", Color("series-3", "#1a73e8", "#5b9cf0"))
GEMINI_4_CARBON = Model("Gemini 4 Carbon", Color("series-1", "#0e9384", "#2bb5a4"))
GEMINI_4_HYDROGEN = Model("Gemini 4 Hydrogen", Color("series-10", "#725c41", "#ba9d79"))
MODELS = [GPT_6_ASTRA, GPT_6_2_ASTRA, GPT_6_1_SOL, GPT_6_2_SOL, CLAUDE_FABLE_5_2, CLAUDE_OPUS_5_5, CLAUDE_SONNET_5_5, GEMINI_4_ARGON, GEMINI_4_CARBON, GEMINI_4_HYDROGEN]
COLORS = [SURFACE, PAGE, TEXT_PRIMARY, TEXT_SECONDARY, TEXT_MUTED, GRIDLINE, BASELINE, BORDER,
          *(model.color for model in MODELS)]

Scores = list[float | None]


@dataclass(frozen=True)
class Metric:
    name: str
    unit_and_source: str
    scores: dict[Model, Scores]
    y_range: tuple[float, float]
    tick_step: float
    decimals: int = 1
    estimated: frozenset[tuple[Model, str]] = frozenset()

    @property
    def models(self) -> list[Model]:
        return [model for model in MODELS if model in self.scores]

    def label(self, score: float) -> str:
        return f"{score:.{self.decimals}f}"

    @property
    def costs(self) -> dict[Model, Scores] | None:
        return COSTS.get(self.name)

    @property
    def cost_unit(self) -> str:
        return COST_UNITS.get(self.name, DEFAULT_COST_UNIT)


INTELLIGENCE = [
    Metric("AA Intelligence Index", "v5.0.1 · Artificial Analysis", {
        GPT_6_ASTRA: [43.3, 51.6, 54.8, 55.3, 56.9],
        GPT_6_1_SOL: [34.8, 46.3, 50.3, 52.5, 54.6],
        CLAUDE_FABLE_5_2: [53.9, 56.4, 61.8, 62.2, 64.6],
        CLAUDE_OPUS_5_5: [34.8, 48.2, 51.8, 57.4, 59.1],
        CLAUDE_SONNET_5_5: [25.6, 30.8, 41.5, 49.9, 54.5],
        GEMINI_4_ARGON: [None, 47.6, 50.4, None, None],
        GEMINI_4_CARBON: [54.2, 58.3, 60.0, None, None],
        GPT_6_2_ASTRA: [45.7, 57.0, 60.1, 61.6, 62.1],
        GPT_6_2_SOL: [40.6, 52.7, 54.9, 55.7, 57.3],
        GEMINI_4_HYDROGEN: [26.9, 41.2, 50.8, 53.9, None],
    }, (20, 70), 10),
    Metric("HLE-Diamond", "% · Humanity's Last Exam, AA's 1,000-question set · Artificial Analysis", {
        GPT_6_ASTRA: [45.1, 52.7, 59.3, 61.5, 63.8],
        GPT_6_1_SOL: [38.2, 46.0, 51.9, 55.8, 58.8],
        CLAUDE_FABLE_5_2: [60.8, 66.3, 73.8, 75.8, 80.2],
        CLAUDE_OPUS_5_5: [41.7, 51.4, 55.6, 64.0, 67.9],
        CLAUDE_SONNET_5_5: [20.6, 23.8, 33.8, 44.1, 53.3],
        GEMINI_4_ARGON: [None, 42.5, 56.7, None, None],
        GEMINI_4_CARBON: [61.9, 67.4, 69.1, None, None],
        GPT_6_2_ASTRA: [47.7, 56.0, 65.9, 67.3, 72.2],
        GPT_6_2_SOL: [34.5, 50.7, 58.3, 61.8, 64.0],
        GEMINI_4_HYDROGEN: [32.2, 47.7, 54.9, 58.8, None],
    }, (10, 90), 10),
    Metric("CritPt v2", "% · hard subset · Artificial Analysis", {
        GPT_6_ASTRA: [63.0, 72.0, 71.5, 71.0, 70.5],
        GPT_6_1_SOL: [62.5, 67.0, 68.5, 69.5, 69.5],
        CLAUDE_FABLE_5_2: [60.0, 61.5, 73.0, 73.5, 76.5],
        CLAUDE_OPUS_5_5: [36.0, 54.0, 59.5, 67.5, 68.0],
        CLAUDE_SONNET_5_5: [26.0, 33.5, 51.5, 57.5, 59.0],
        GEMINI_4_ARGON: [None, 53.5, 52.5, None, None],
        GEMINI_4_CARBON: [65.0, 69.0, 69.0, None, None],
        GPT_6_2_ASTRA: [61.0, 67.5, 71.5, 70.5, 71.5],
        GPT_6_2_SOL: [58.0, 64.0, 61.5, 62.5, 62.5],
        GEMINI_4_HYDROGEN: [48.0, 61.0, 61.5, 66.0, None],
    }, (20, 90), 10),
    Metric("ARC-AGI-2", "% semi-private · ARC Prize", {
        GPT_6_ASTRA: [85.4, 92.1, 92.1, 93.3, 95.0],
        GPT_6_1_SOL: [76.7, 86.7, 91.7, 91.7, 94.2],
        CLAUDE_FABLE_5_2: [86.7, 89.6, 90.4, 93.8, 92.5],
        CLAUDE_OPUS_5_5: [70.1, 87.5, 93.3, 92.5, 91.7],
        CLAUDE_SONNET_5_5: [24.0, 32.8, 67.4, 83.9, None],
        GEMINI_4_ARGON: [42.1, 87.1, 91.3, None, None],
        GEMINI_4_CARBON: [49.6, 94.2, 92.1, None, None],
        GPT_6_2_ASTRA: [91.7, 93.3, 94.6, 95.8, 95.8],
        GPT_6_2_SOL: [57.9, 82.9, 85.8, 85.8, 85.8],
    }, (20, 100), 20),
    Metric("AA-Omniscience Index", "v1.1 · −100 to 100 · Artificial Analysis", {
        GPT_6_ASTRA: [40.3, 41.4, 44.6, 43.7, 42.4],
        GPT_6_1_SOL: [38, 40.2, 41, 42.4, 42.0],
        CLAUDE_FABLE_5_2: [62.9, 63.5, 64.0, 64.8, 66.8],
        CLAUDE_OPUS_5_5: [39.0, 39.8, 42.4, 43.1, 48.1],
        CLAUDE_SONNET_5_5: [20.3, 18.6, 18.7, 20.6, 30.5],
        GEMINI_4_ARGON: [None, 41.1, 46.1, None, None],
        GEMINI_4_CARBON: [39.2, 46.8, 53.5, None, None],
        GPT_6_2_ASTRA: [38.7, 44.8, 46.8, 48.3, 50.0],
        GPT_6_2_SOL: [24.8, 34.2, 38.3, 38.6, 40.4],
        GEMINI_4_HYDROGEN: [36.1, 41.9, 43.7, 46.3, None],
    }, (10, 70), 10),
    Metric("GDPval-AA", "Elo · Artificial Analysis", {
        GPT_6_ASTRA: [1404, 1501, 1538, 1572, 1587],
        GPT_6_1_SOL: [1322, 1463, 1521, 1563, 1607],
        CLAUDE_FABLE_5_2: [1546, 1591, 1718, 1751, 1831],
        CLAUDE_OPUS_5_5: [1239, 1590, 1709, 1836, 1866],
        CLAUDE_SONNET_5_5: [1182, 1326, 1551, 1743, 1838],
        GEMINI_4_ARGON: [None, 1578, 1634, None, None],
        GEMINI_4_CARBON: [None, None, 1733, None, None],
    }, (1100, 1900), 200, decimals=0),
    Metric("AA-Briefcase", "Elo · long-horizon knowledge work · Artificial Analysis", {
        GPT_6_ASTRA: [1256, 1462, 1503, 1544, 1569],
        GPT_6_2_ASTRA: [1039, 1408, 1570, 1594, 1644],
        GPT_6_1_SOL: [1115, 1361, 1469, 1504, 1557],
        GPT_6_2_SOL: [1230, 1495, 1541, 1580, 1612],
        CLAUDE_FABLE_5_2: [1563, 1622, 1677, 1737, 1785],
        CLAUDE_OPUS_5_5: [1278, 1617, 1682, 1760, 1800],
        CLAUDE_SONNET_5_5: [1268, 1438, 1634, 1739, 1815],
        GEMINI_4_ARGON: [None, 1467, 1485, None, None],
        GEMINI_4_CARBON: [1567, 1602, 1611, None, None],
        GEMINI_4_HYDROGEN: [947, 1296, 1497, 1568, None],
    }, (800, 2000), 200, decimals=0),
    Metric("AutomationBench-AA", "% · Artificial Analysis", {
        GPT_6_ASTRA: [59.1, 64.6, 66.6, 67.2, 68.5],
        GPT_6_1_SOL: [52.6, 62.6, 64.5, 66.6, 64.9],
        CLAUDE_FABLE_5_2: [68.0, 68.8, 71.4, 74.2, 76.4],
        CLAUDE_OPUS_5_5: [52.9, 61.2, 63.2, 65.0, 69.5],
        CLAUDE_SONNET_5_5: [49.4, 54.9, 59.4, 65.5, 71.8],
        GEMINI_4_ARGON: [None, 75.8, 77.5, None, None],
        GEMINI_4_CARBON: [63.5, 77.6, 77.8, None, None],
        GPT_6_2_ASTRA: [68.6, 72.8, 76.0, 76.1, 77.2],
        GPT_6_2_SOL: [63.2, 70.3, 69.9, 70.6, 71.3],
        GEMINI_4_HYDROGEN: [60.5, 72.0, 74.4, 76.1, None],
    }, (40, 80), 10),
    Metric("AA-LCR", "% · v1.1 long-context reasoning · Artificial Analysis", {
        GPT_6_ASTRA: [80.0, 79.7, 80.0, 80.0, 80.7],
        GPT_6_1_SOL: [84.0, 83.3, 82.3, 79.7, 83.0],
        CLAUDE_FABLE_5_2: [80.0, 80.0, 83.3, 82.7, 83.3],
        CLAUDE_OPUS_5_5: [80.7, 84.3, 82.7, 84.7, 84.7],
        CLAUDE_SONNET_5_5: [76.0, 76.3, 78.0, 79.7, 82.7],
        GEMINI_4_ARGON: [None, 78.3, 79.7, None, None],
        GEMINI_4_CARBON: [None, None, 79.3, None, None],
    }, (70, 90), 5),
    Metric("GDP.pdf", "% all-pass · Q&A over complex PDFs · Artificial Analysis", {
        GPT_6_ASTRA: [30.4, 30.4, 31.0, 32.2, 31.0],
        GPT_6_1_SOL: [27.0, 30.0, 32.0, 31.8, 31.0],
        CLAUDE_FABLE_5_2: [26.8, 23.8, 21.8, 21.4, 24.2],
        CLAUDE_OPUS_5_5: [25.6, 25.6, 28.8, 26.6, 26.2],
        CLAUDE_SONNET_5_5: [16.0, 20.2, 25.2, 24.6, 25.8],
        GEMINI_4_ARGON: [None, 25.6, 21.8, None, None],
        GEMINI_4_CARBON: [28.6, 29.6, 28.4, None, None],
        GPT_6_2_ASTRA: [28.0, 28.4, 28.6, 28.0, 29.8],
        GPT_6_2_SOL: [28.6, 29.2, 28.8, 28.4, 30.0],
        GEMINI_4_HYDROGEN: [28.2, 32.8, 30.0, 27.6, None],
    }, (10, 35), 5),
    Metric("AA-AnalystAgent", "% correct in all five runs · Artificial Analysis", {
        GPT_6_ASTRA: [None, None, None, None, 51.3],
        GPT_6_2_ASTRA: [56.3, 52.5, 61.3, 62.5, 62.5],
        GPT_6_1_SOL: [None, None, None, None, 50.0],
        GPT_6_2_SOL: [38.8, 50.0, 52.5, 53.8, 53.8],
        CLAUDE_OPUS_5_5: [None, None, None, None, 56.3],
        CLAUDE_SONNET_5_5: [None, None, None, None, 57.5],
        GEMINI_4_ARGON: [None, None, 48.8, None, None],
    }, (30, 70), 10),
    Metric("Harvey LAB-AA v1.1", "% all-pass · Artificial Analysis; costs reported by OpenAI", {
        GPT_6_ASTRA: [None, None, None, None, 8.6],
        GPT_6_2_ASTRA: [2.2, 8.1, 13.3, 12.8, 15.0],
        GPT_6_1_SOL: [None, None, None, None, 6.9],
        GPT_6_2_SOL: [3.1, 5.0, 5.8, 6.1, 11.1],
        CLAUDE_FABLE_5_2: [4.2, 6.4, 4.7, 3.9, 7.2],
        CLAUDE_OPUS_5_5: [None, None, None, None, 4.2],
        CLAUDE_SONNET_5_5: [None, None, None, None, 2.8],
        GEMINI_4_ARGON: [None, None, 3.9, None, None],
    }, (0, 20), 5),
    Metric("MLCR-AA", "% medical long-context reasoning · Artificial Analysis", {
        GPT_6_ASTRA: [33.9, 38.3, 32.8, 36.1, 41.7],
        GPT_6_2_ASTRA: [30.6, 32.8, 35.6, 37.8, 39.4],
        GPT_6_1_SOL: [26.7, 32.2, 31.7, 35.6, 38.3],
        GPT_6_2_SOL: [32.2, 31.7, 33.9, 35.0, 37.2],
        CLAUDE_FABLE_5_2: [None, None, None, None, 43.9],
        CLAUDE_OPUS_5_5: [19.4, 22.2, 15.0, 25.0, 27.8],
        CLAUDE_SONNET_5_5: [19.4, 17.8, 18.9, 20.6, 41.7],
        GEMINI_4_ARGON: [None, None, 13.9, None, None],
        GEMINI_4_CARBON: [None, None, 19.4, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 21.1, None],
    }, (0, 50), 10),
    Metric("GPQA Diamond (AA)", "% · no tools · Artificial Analysis", {
        GPT_6_ASTRA: [93.1, 93.9, 94.9, 96.3, 96.1],
    }, (90, 100), 2),
    Metric("tau3-Banking", "% · Sierra banking workflow, AA's implementation", {
        GPT_6_ASTRA: [32.0, 35.5, 40.0, 43.1, 41.4],
    }, (20, 50), 10),
    Metric("MMMU-Pro", "% · visual reasoning · Artificial Analysis", {
        GPT_6_ASTRA: [84.6, 85.1, 86.4, 86.2, 86.9],
        GPT_6_2_ASTRA: [85.1, 86.1, 87.7, 87.9, 89.5],
        GPT_6_1_SOL: [83.1, 83.9, 84.9, 85.1, 86.0],
        CLAUDE_OPUS_5_5: [84.7, 85.7, 85.8, 86.6, 87.7],
        GEMINI_4_ARGON: [None, 88.3, None, None, None],
        GEMINI_4_CARBON: [None, 89.2, None, None, None],
    }, (80, 95), 5),
    Metric("HealthBench Professional (AA)", "% length-adjusted score · Artificial Analysis", {
        GPT_6_ASTRA: [None, None, None, None, 66.0],
        GPT_6_1_SOL: [None, None, None, None, 65.1],
        CLAUDE_FABLE_5_2: [66.9, 67.0, 67.6, 68.1, 67.7],
        CLAUDE_OPUS_5_5: [None, None, None, None, 59.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 63.0],
        GEMINI_4_ARGON: [None, None, 55.1, None, None],
    }, (50, 75), 5),
    Metric("EnterpriseOps-Gym-AA", "% strict task success · ServiceNow workflows, AA's implementation", {
        GPT_6_2_ASTRA: [21.8, 22.6, 25.2, 25.3, 29.9],
        GPT_6_2_SOL: [19.9, 21.4, 23.4, 26.3, 28.9],
    }, (10, 40), 10),
    Metric("Agents' Last Exam v1.1", "% · OpenAI launch comparison; Fable omits nine fallback tasks", {
        GPT_6_ASTRA: [67.9, 71.2, 71.0, 71.7, 73.1],
        GPT_6_2_ASTRA: [65.8, 72.1, 76.0, 78.3, 77.6],
        GPT_6_1_SOL: [61.0, 68.8, 72.3, 71.9, 72.5],
        GPT_6_2_SOL: [66.7, 70.3, 72.0, 72.5, 73.0],
        CLAUDE_FABLE_5_2: [None, None, None, None, 72.8],
        CLAUDE_OPUS_5_5: [None, None, None, None, 71.6],
        GEMINI_4_CARBON: [None, None, 77.4, None, None],
    }, (50, 85), 10),
    Metric("LifeVal", "% · everyday agentic tasks · OpenAI's own evaluation", {
        GPT_6_ASTRA: [67.5, 74.3, 76.0, 77.5, 79.8],
        GPT_6_2_ASTRA: [46.3, 78.9, 83.1, 83.7, 86.1],
        GPT_6_1_SOL: [66.8, 75.5, 77.1, 77.8, 79.5],
        GPT_6_2_SOL: [25.3, 70.3, 80.8, 82.6, 83.8],
    }, (20, 90), 10),
    Metric("GDPval v2 (Internal)", "% · professional workflows · OpenAI's internal evaluation", {
        GPT_6_ASTRA: [30.8, 37.5, 42.0, 42.0, 44.2],
        GPT_6_2_ASTRA: [28.9, 39.3, 45.0, 47.8, 50.4],
        GPT_6_1_SOL: [28.8, 35.1, 40.2, 40.0, 41.5],
        GPT_6_2_SOL: [23.1, 34.8, 42.7, 45.0, 46.9],
        CLAUDE_FABLE_5_2: [39.5, 40.3, 41.5, 44.1, 44.8],
        CLAUDE_OPUS_5_5: [26.6, 35.2, 37.0, 41.6, 43.5],
        GEMINI_4_CARBON: [45.1, 48.0, 48.8, None, None],
    }, (20, 55), 10),
    Metric("Vals Science Index v1", "% · Vals Science, as reported by OpenAI", {
        GPT_6_ASTRA: [None, None, None, None, 65.1],
        GPT_6_2_ASTRA: [59.5, 67.6, 68.1, 64.8, 68.4],
        GPT_6_1_SOL: [None, None, None, None, 59.6],
        GPT_6_2_SOL: [46.3, 56.5, 57.6, 58.5, 57.8],
        CLAUDE_FABLE_5_2: [None, None, 63.7, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 58.7],
    }, (40, 75), 10),
    Metric("BenchCAD 2.1 Core", "% · hardware engineering · OpenAI launch comparison", {
        GPT_6_ASTRA: [20.3, 38.7, 51.1, 53.9, 62.6],
        GPT_6_2_ASTRA: [42.6, 68.5, 74.6, 77.6, 82.5],
        GPT_6_1_SOL: [13.5, 31.2, 42.1, 45.6, 52.6],
        GPT_6_2_SOL: [23.9, 41.2, 64.0, 70.4, 73.1],
        CLAUDE_FABLE_5_2: [26.9, 32.4, 61.0, 74.1, 83.5],
        CLAUDE_OPUS_5_5: [6.3, 19.1, 29.7, 54.5, 65.3],
    }, (0, 90), 10),
    Metric("AutomationBench 1.0.6", "% · Zapier · OpenAI launch comparison, not AutomationBench-AA", {
        GPT_6_ASTRA: [30.3, 34.1, 37.1, 39.0, 41.4],
        GPT_6_2_ASTRA: [37.1, 43.8, 47.9, 47.2, 52.4],
        GPT_6_1_SOL: [24.7, 31.7, 33.2, 35.5, 36.1],
        GPT_6_2_SOL: [31.2, 40.2, 41.2, 40.6, 41.1],
        CLAUDE_FABLE_5_2: [39.7, 40.2, 44.3, 47.9, 51.4],
        CLAUDE_OPUS_5_5: [24.2, 29.5, 33.0, 35.8, 42.5],
        GEMINI_4_CARBON: [31.5, 53.0, 53.9, None, None],
    }, (20, 60), 10),
]

CODING = [
    Metric("AA Index coding category", "FrontierCode-AA 2.0 at 15%, Terminal-Bench 4.0 at 10% · derived from AA", {
        GPT_6_ASTRA: [32.5, 41.7, 45.7, 48.7, 49.1],
        GPT_6_1_SOL: [24.4, 39.2, 42.6, 44.7, 46.8],
        CLAUDE_FABLE_5_2: [44.9, 46.8, 53.3, 53.2, 53.1],
        CLAUDE_OPUS_5_5: [22.0, 40.9, 44.2, 50.1, 51.7],
        CLAUDE_SONNET_5_5: [12.6, 18.5, 33.0, 44.2, 50.5],
        GEMINI_4_ARGON: [None, 37, 38.3, None, None],
        GEMINI_4_CARBON: [42.8, 47.9, 50.4, None, None],
        GPT_6_2_ASTRA: [40.0, 51.4, 52.3, 55.0, 52.9],
        GPT_6_2_SOL: [34.0, 47.3, 47.6, 48.1, 50.7],
        GEMINI_4_HYDROGEN: [8.2, 30.6, 43.4, 44.8, None],
    }, (0, 60), 10),
    Metric("Terminal-Bench 4.0", "% · Artificial Analysis", {
        GPT_6_ASTRA: [41.9, 49.5, 54.0, 59.6, 59.1],
        GPT_6_1_SOL: [30.8, 48.0, 51.5, 54.0, 56.1],
        CLAUDE_FABLE_5_2: [54.5, 55.1, 59.6, 61.6, 59.6],
        CLAUDE_OPUS_5_5: [31.3, 52.5, 56.6, 59.6, 59.6],
        CLAUDE_SONNET_5_5: [20.7, 29.8, 43.9, 57.1, 63.6],
        GEMINI_4_ARGON: [None, 55.1, 57.1, None, None],
        GEMINI_4_CARBON: [62.6, 60.6, 65.2, None, None],
        GPT_6_2_ASTRA: [51.0, 58.6, 60.1, 64.1, 64.1],
        GPT_6_2_SOL: [37.9, 56.1, 58.6, 56.1, 60.1],
        GEMINI_4_HYDROGEN: [6.6, 29.3, 54.0, 53.5, None],
    }, (0, 70), 10),
    Metric("FrontierCode-AA 2.0", "score · Cognition's tasks, AA's harness · Artificial Analysis", {
        GPT_6_ASTRA: [26.2, 36.6, 40.1, 41.4, 42.4],
        GPT_6_1_SOL: [20.2, 33.4, 36.7, 38.5, 40.6],
        CLAUDE_FABLE_5_2: [38.4, 41.3, 49.1, 47.6, 48.8],
        CLAUDE_OPUS_5_5: [15.8, 33.1, 35.9, 43.8, 46.4],
        CLAUDE_SONNET_5_5: [7.1, 11.0, 25.7, 35.6, 41.7],
        GEMINI_4_ARGON: [None, 25, 25.7, None, None],
        GEMINI_4_CARBON: [29.6, 39.5, 40.6, None, None],
        GPT_6_2_ASTRA: [32.7, 46.6, 47.1, 49.0, 45.4],
        GPT_6_2_SOL: [31.4, 41.4, 40.2, 42.8, 44.4],
        GEMINI_4_HYDROGEN: [9.3, 31.5, 36.3, 39.0, None],
    }, (0, 60), 10),
    Metric("Terminal-Bench Science 0.1", "% · Artificial Analysis", {
        GPT_6_ASTRA: [37.1, 53.3, 59.5, 54.8, 63.3],
        GPT_6_1_SOL: [11.0, 37.1, 46.2, 50.5, 58.1],
        CLAUDE_FABLE_5_2: [53.8, 60.5, 70.0, 67.6, 73.3],
        CLAUDE_OPUS_5_5: [24.3, 43.3, 49.0, 61.9, 59.0],
        CLAUDE_SONNET_5_5: [10.5, 16.2, 34.3, 52.4, 53.3],
        GEMINI_4_ARGON: [None, 48.6, 52.9, None, None],
        GEMINI_4_CARBON: [61.9, 62.4, 64.8, None, None],
        GPT_6_2_ASTRA: [51.0, 74.8, 75.2, 78.6, 78.1],
        GPT_6_2_SOL: [37.1, 60.5, 67.6, 66.7, 67.6],
        GEMINI_4_HYDROGEN: [2.4, 15.2, 41.4, 49.5, None],
    }, (0, 80), 10),
    Metric("DeepSWE v1.1", "% · reported by each lab", {
        GPT_6_ASTRA: [67.0, 72.8, 73.2, 74.1, 73.2],
        GPT_6_1_SOL: [64.4, 73.0, 75.2, 71.9, 71.9],
        CLAUDE_SONNET_5_5: [None, None, None, None, 71.0],
        GEMINI_4_ARGON: [None, None, 77.9, None, None],
    }, (60, 80), 5),
    Metric("CursorBench 4.0", "% · Cursor leaderboard", {
        GEMINI_4_CARBON: [58.6, 60.1, 60.4, None, None],
        CLAUDE_FABLE_5_2: [53.2, 54.8, 56.9, 56.3, 60.0],
        CLAUDE_OPUS_5_5: [43.7, 52.5, 56.0, 56.0, 57.8],
        GEMINI_4_HYDROGEN: [27.9, 46.7, 54.3, 57.8, None],
        CLAUDE_SONNET_5_5: [35.8, 39.2, 47.8, 53.1, 55.5],
        GEMINI_4_ARGON: [50.6, 52.8, 52.9, None, None],
    }, (20, 70), 10),
    Metric("SciCode", "% · Artificial Analysis", {
        GPT_6_ASTRA: [54.1, 54.2, 55.4, 55.7, 56.5],
        GPT_6_1_SOL: [53.2, 53.2, 55.8, 55.7, 54.2],
        CLAUDE_FABLE_5_2: [57.8, 59.7, 59.5, 65.6, 67.7],
        CLAUDE_OPUS_5_5: [58.6, 59.3, 60.4, 65.0, 66.9],
        CLAUDE_SONNET_5_5: [49.1, 52.9, 53.7, 57.3, 61.0],
        GEMINI_4_ARGON: [None, 58.9, 61.8, None, None],
    }, (45, 70), 5),
    Metric("FrontierCode 2.0", "% · OpenAI launch comparison, not AA's harness", {
        GPT_6_ASTRA: [31.1, 36.8, 38.3, 41.4, 42.8],
        GPT_6_2_ASTRA: [38.1, 42.2, 43.6, 44.1, 44.2],
        GPT_6_1_SOL: [25.6, 29.6, 34.8, 32.3, 39.0],
        GPT_6_2_SOL: [33.1, 38.3, 39.7, 39.8, 43.8],
        CLAUDE_FABLE_5_2: [34.2, 37.6, 45.3, 49.1, 45.7],
        CLAUDE_OPUS_5_5: [14.7, 30.1, 34.5, 43.4, 45.5],
        GEMINI_4_CARBON: [32.4, 41.1, 38.4, None, None],
    }, (10, 55), 10),
    Metric("SecureSWE", "% · secure implementation · OpenAI's internal evaluation, cyber safeguards off", {
        GPT_6_ASTRA: [41.3, 45.7, 47.9, 48.7, 46.5],
        GPT_6_2_ASTRA: [54.5, 57.7, 61.7, 63.8, 65.7],
        GPT_6_1_SOL: [36.2, 46.5, 44.4, 46.0, 49.7],
        GPT_6_2_SOL: [43.1, 47.1, 51.9, 54.0, 55.6],
    }, (30, 70), 10),
    Metric("PatchBench", "% · security patches · OpenAI's evaluation, cyber safeguards off", {
        GPT_6_ASTRA: [63.0, 67.5, 68.8, 70.5, 70.9],
        GPT_6_2_ASTRA: [71.1, 75.6, 78.8, 79.7, 79.7],
        GPT_6_1_SOL: [62.0, 64.5, 67.8, 69.4, 71.0],
        GPT_6_2_SOL: [65.6, 70.5, 74.1, 74.2, 75.6],
    }, (60, 85), 5),
    Metric("ExploitBench – Internal Port (June–August 2026)", "% · OpenAI's internal cyber evaluation, safeguards off", {
        GPT_6_ASTRA: [0.0, 19.5, 24.5, 29.0, 31.5],
        GPT_6_2_ASTRA: [19.5, 46.5, 48.0, 53.0, 53.5],
        GPT_6_1_SOL: [2.0, 8.5, 14.5, 18.0, 21.5],
        GPT_6_2_SOL: [0.0, 24.5, 47.0, 45.5, 50.5],
    }, (0, 60), 10),
]

SECTIONS = [("Intelligence", INTELLIGENCE), ("Coding", CODING)]


@dataclass(frozen=True)
class ReportedMetric:
    """A benchmark with one reported score per model, at whatever effort its reporter ran; drawn as bars."""
    name: str
    unit_and_source: str
    scores: dict[Model, tuple[float, str]]  # score, and the effort level the reporter ran it at
    x_max: float = 100
    tick_step: float = 25
    decimals: int = 1

    @property
    def models(self) -> list[Model]:
        return [model for model in MODELS if model in self.scores]

    @property
    def missing(self) -> list[Model]:
        return [model for model in MODELS if model not in self.scores]

    @property
    def costs(self) -> dict[Model, Scores] | None:
        return COSTS.get(self.name)

    @property
    def cost_unit(self) -> str:
        return COST_UNITS.get(self.name, DEFAULT_COST_UNIT)


# One score per model, at the effort level its reporter ran; sources in sources/*.json.
REPORTED = {"Intelligence": [
    ReportedMetric("Vals Index", "% · v2.2 · Vals AI, one harness for all models", {
        GPT_6_ASTRA: (65.02, "max"),
        GPT_6_1_SOL: (63.94, "max"),
        CLAUDE_FABLE_5_2: (71.31, "high"),
        CLAUDE_OPUS_5_5: (70.14, "max"),
        CLAUDE_SONNET_5_5: (70.85, "max"),
        GEMINI_4_ARGON: (69.39, "high"),
        GEMINI_4_CARBON: (70.45, "high"),
        GPT_6_2_ASTRA: (67.66, 'max'),
        GPT_6_2_SOL: (66.06, 'max'),
        GEMINI_4_HYDROGEN: (68.49, 'xhigh'),
    }),
    ReportedMetric("MKA", "% weighted rubric score · multimodal knowledge-work agent · AA’s own run for all models", {
        GPT_6_ASTRA: (50.2, "max"),
        GPT_6_1_SOL: (47.7, "max"),
        CLAUDE_FABLE_5_2: (56.6, "max"),
        CLAUDE_OPUS_5_5: (53.0, "max"),
        CLAUDE_SONNET_5_5: (52.0, "max"),
        GEMINI_4_ARGON: (51.3, "high"),
        GEMINI_4_CARBON: (54.3, "high"),
    }),
    ReportedMetric("GPQA Diamond (OpenAI)", "% · no tools · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (96.0, 'not stated'),
        GPT_6_2_ASTRA: (97.0, 'not stated'),
        GPT_6_2_SOL: (96.0, 'not stated'),
    }),
    ReportedMetric("HealthBench Professional (OpenAI)", "length-adjusted score · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (64.7, 'not stated'),
        GPT_6_2_ASTRA: (66.3, 'not stated'),
        GPT_6_1_SOL: (64.2, 'not stated'),
        GPT_6_2_SOL: (65.9, 'not stated'),
    }),
    ReportedMetric("MentalHealthBench", "% overall rubric score · OpenAI system card, max effort", {
        GPT_6_ASTRA: (58.7, 'max'),
        GPT_6_2_ASTRA: (53.3, 'max'),
        GPT_6_1_SOL: (57.9, 'max'),
        GPT_6_2_SOL: (50.9, 'max'),
    }),
    ReportedMetric("VIALS-AA", "% correct in all three runs · scientific images · Artificial Analysis", {
        GPT_6_ASTRA: (62.7, 'max'),
        GPT_6_1_SOL: (59.0, 'max'),
        CLAUDE_FABLE_5_2: (67.1, 'max'),
        CLAUDE_OPUS_5_5: (61.5, 'max'),
        CLAUDE_SONNET_5_5: (59.6, 'max'),
        GEMINI_4_ARGON: (59.6, 'high'),
        GEMINI_4_CARBON: (64.0, 'high'),
    }),
], "Coding": [
    ReportedMetric("Vibe Code Bench v1.1", "% · Vals AI, OpenHands harness for all models", {
        GPT_6_ASTRA: (89.59, "max"),
        GPT_6_1_SOL: (88.93, "max"),
        CLAUDE_FABLE_5_2: (93.77, "high"),
        CLAUDE_OPUS_5_5: (90.29, "max"),
        CLAUDE_SONNET_5_5: (92.39, "max"),
        GEMINI_4_ARGON: (91.91, "high"),
        GEMINI_4_CARBON: (89.06, "high"),
        GPT_6_2_ASTRA: (89.9, 'max'),
        GPT_6_2_SOL: (87.62, 'max'),
        GEMINI_4_HYDROGEN: (87.78, 'xhigh'),
    }),
    ReportedMetric("SWE-Bench Pro", "% resolved · each lab’s own run on its own agent harness", {
        CLAUDE_OPUS_5_5: (89.9, "max"),
        CLAUDE_SONNET_5_5: (81.3, "max"),
    }),
    ReportedMetric("Internal Research Debugging", "% mean rubric credit · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (78.05, 'not stated'),
        GPT_6_2_ASTRA: (81.85, 'not stated'),
        GPT_6_2_SOL: (74.66, 'not stated'),
    }),
    ReportedMetric("KernelGen 1P", "% mean rubric credit · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (66.72, 'not stated'),
        GPT_6_2_ASTRA: (76.92, 'not stated'),
        GPT_6_2_SOL: (74.71, 'not stated'),
    }),
    ReportedMetric("NanoGPT v5", "% baseline training time saved · OpenAI system card, effort not stated", {
        GPT_6_2_ASTRA: (42.87, 'not stated'),
        GPT_6_2_SOL: (14.59, 'not stated'),
    }),
    ReportedMetric("PostTrainBench Lite", "% performance gap closed · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (76.97, 'not stated'),
        GPT_6_2_ASTRA: (74.79, 'not stated'),
        GPT_6_2_SOL: (44.89, 'not stated'),
    }),
    ReportedMetric("MLE-Bench Revised", "mean reference percentile · OpenAI system card, effort not stated", {
        GPT_6_ASTRA: (93.8, 'not stated'),
        GPT_6_2_ASTRA: (96.06, 'not stated'),
        GPT_6_2_SOL: (91.38, 'not stated'),
    }),
    ReportedMetric("ITBench-AA", "% precision at full recall · Kubernetes root-cause analysis · Artificial Analysis", {
        GPT_6_ASTRA: (48.6, 'max'),
        CLAUDE_OPUS_5_5: (38.2, 'max'),
    }),
    ReportedMetric("AA-3D", "Elo · human preference for generated 3D experiences · Artificial Analysis", {
        GPT_6_ASTRA: (1168.398, 'not stated'),
        GPT_6_2_ASTRA: (1317.6168, 'not stated'),
        GPT_6_1_SOL: (1121.0821, 'not stated'),
        GPT_6_2_SOL: (1259.2763, 'not stated'),
        CLAUDE_FABLE_5_2: (1271.4151, 'not stated'),
        CLAUDE_OPUS_5_5: (1202.4312, 'not stated'),
        CLAUDE_SONNET_5_5: (1203.6913, 'not stated'),
        GEMINI_4_ARGON: (1146.6893, 'not stated'),
    }, x_max=1500, tick_step=250, decimals=0),
]}

# US dollars per task of each benchmark at each effort level, from the same AA records (ARC Prize for ARC-AGI-2).
# AA weightedCostPerTask divided by its index weight; the coding category uses the same 15:10 weights as its score.
COSTS: dict[str, dict[Model, Scores]] = {
    "Vibe Code Bench v1.1": {
        CLAUDE_FABLE_5_2: [None, None, 22.13, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 19.73],
        GEMINI_4_ARGON: [None, None, 8.11, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 35.77],
        GPT_6_2_ASTRA: [None, None, None, None, 7.92],
        GPT_6_ASTRA: [None, None, None, None, 38.51],
        GEMINI_4_CARBON: [None, None, 8.25, None, None],
        GPT_6_1_SOL: [None, None, None, None, 6.23],
        GEMINI_4_HYDROGEN: [None, None, None, 4.55, None],
        GPT_6_2_SOL: [None, None, None, None, 3.23],
    },
    "Vals Index": {
        CLAUDE_FABLE_5_2: [None, None, 17.94, None, None],
        CLAUDE_SONNET_5_5: [None, None, None, None, 16.18],
        GEMINI_4_CARBON: [None, None, 10.51, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 24.77],
        GEMINI_4_ARGON: [None, None, 13.37, None, None],
        GEMINI_4_HYDROGEN: [None, None, None, 9.84, None],
        GPT_6_2_ASTRA: [None, None, None, None, 10.68],
        GPT_6_2_SOL: [None, None, None, None, 3.18],
        GPT_6_ASTRA: [None, None, None, None, 21.28],
        GPT_6_1_SOL: [None, None, None, None, 3.61],
    },
    "CursorBench 4.0": {
        GEMINI_4_CARBON: [11.89, 8.49, 9.22, None, None],
        CLAUDE_FABLE_5_2: [3.94, 4.66, 9.7, 15.48, 32.79],
        CLAUDE_OPUS_5_5: [1.17, 2.91, 3.97, 6.98, 13.43],
        GEMINI_4_HYDROGEN: [0.28, 1.76, 5.59, 5.86, None],
        CLAUDE_SONNET_5_5: [0.37, 0.52, 1.2, 2.81, 7.05],
        GEMINI_4_ARGON: [4.09, 4.39, 4.57, None, None],
    },
    "Harvey LAB-AA v1.1": {
        GPT_6_ASTRA: [None, None, None, None, 13.7],
        GPT_6_2_ASTRA: [0.86, 2.49, 3.86, 4.31, 6.35],
        GPT_6_1_SOL: [None, None, None, None, 2.48],
        GPT_6_2_SOL: [0.25, 0.71, 1.03, 1.23, 1.92],
        CLAUDE_FABLE_5_2: [9.16, 9.67, 15.9, 24.3, 39.8],
        CLAUDE_OPUS_5_5: [None, None, None, None, 17.9],
    },
    "AA Intelligence Index": {
        GPT_6_ASTRA: [1650.0, 2640.0, 3200.0, 3750.0, 5660.0],
        GPT_6_1_SOL: [238.0, 389.0, 573.0, 718.0, 1120.0],
        CLAUDE_FABLE_5_2: [2860.0, 3360.0, 7110.0, 11700.0, 22200.0],
        CLAUDE_OPUS_5_5: [980.0, 2030.0, 2720.0, 4770.0, 8910.0],
        CLAUDE_SONNET_5_5: [499.0, 679.0, 1270.0, 2900.0, 7980.0],
        GEMINI_4_ARGON: [None, 3110, 3810, None, None],
        GEMINI_4_CARBON: [4050.0, 4000.0, 5330.0, None, None],
        GPT_6_2_ASTRA: [794.0, 1460.0, 2010.0, 2480.0, 4530.0],
        GPT_6_2_SOL: [224.0, 405.0, 553.0, 698.0, 1110.0],
        GEMINI_4_HYDROGEN: [332.0, 804.0, 1770.0, 4090.0, None],
    },
    "HLE-Diamond": {
        GPT_6_ASTRA: [0.05, 0.12, 0.257, 0.37, 0.551],
        GPT_6_1_SOL: [0.00863, 0.0185, 0.0433, 0.0663, 0.109],
        CLAUDE_FABLE_5_2: [0.128, 0.183, 0.464, 0.876, 1.73],
        CLAUDE_OPUS_5_5: [0.0351, 0.13, 0.194, 0.47, 1.2],
        CLAUDE_SONNET_5_5: [0.015, 0.0327, 0.107, 0.246, 0.804],
        GEMINI_4_ARGON: [None, 0.0223, 0.242, None, None],
        GEMINI_4_CARBON: [0.343, 0.393, 0.814, None, None],
        GPT_6_2_ASTRA: [0.0178, 0.0433, 0.147, 0.234, 0.657],
        GPT_6_2_SOL: [0.00451, 0.0187, 0.0422, 0.076, 0.149],
        GEMINI_4_HYDROGEN: [0.026, 0.144, 0.373, 1.29, None],
    },
    "CritPt v2": {
        GPT_6_ASTRA: [0.237, 0.407, 0.714, 0.849, 1.14],
        GPT_6_1_SOL: [0.0433, 0.0714, 0.134, 0.167, 0.23],
        CLAUDE_FABLE_5_2: [0.313, 0.367, 1.05, 2.47, 6.35],
        CLAUDE_OPUS_5_5: [0.119, 0.251, 0.384, 0.966, 2.58],
        CLAUDE_SONNET_5_5: [0.0731, 0.0926, 0.181, 0.448, 1.93],
        GEMINI_4_ARGON: [None, 0.782, 1.17, None, None],
        GEMINI_4_CARBON: [1.91, 1.93, 2.44, None, None],
        GPT_6_2_ASTRA: [0.0937, 0.193, 0.447, 0.607, 1.28],
        GPT_6_2_SOL: [0.0306, 0.0852, 0.145, 0.196, 0.314],
        GEMINI_4_HYDROGEN: [0.122, 0.374, 0.878, 1.9, None],
    },
    "ARC-AGI-2": {
        GPT_6_ASTRA: [0.416, 0.48, 0.668, 0.829, 1.12],
        GPT_6_1_SOL: [0.0855, 0.1, 0.135, 0.178, 0.254],
        CLAUDE_FABLE_5_2: [0.516, 0.627, 0.908, 0.983, 2.81],
        CLAUDE_OPUS_5_5: [0.241, 0.337, 0.408, 0.671, 1.85],
        CLAUDE_SONNET_5_5: [0.109, 0.155, 0.277, 0.546, None],
        GEMINI_4_ARGON: [0.0738, 0.137, 0.325, None, None],
        GEMINI_4_CARBON: [0.0985, 0.375, 0.684, None, None],
        GPT_6_2_ASTRA: [0.275, 0.309, 0.408, 0.5, 0.97],
        GPT_6_2_SOL: [0.0758, 0.103, 0.133, 0.174, 0.261],
    },
    "AA-Omniscience Index": {
        GPT_6_ASTRA: [0.00697, 0.0109, 0.028, 0.0518, 0.0988],
        GPT_6_1_SOL: [0.00149, 0.00215, 0.00493, 0.00918, 0.0183],
        CLAUDE_FABLE_5_2: [0.0138, 0.0153, 0.0196, 0.0326, 0.219],
        CLAUDE_OPUS_5_5: [0.00627, 0.00824, 0.00931, 0.0148, 0.187],
        CLAUDE_SONNET_5_5: [0.00291, 0.00312, 0.00567, 0.00883, 0.152],
        GEMINI_4_ARGON: [None, 0.00108, 0.00911, None, None],
        GEMINI_4_CARBON: [0.00076, 0.0126, 0.123, None, None],
        GPT_6_2_ASTRA: [0.00285, 0.00673, 0.0245, 0.0467, 0.256],
        GPT_6_2_SOL: [0.000538, 0.00212, 0.00662, 0.0197, 0.0528],
        GEMINI_4_HYDROGEN: [0.00331, 0.0087, 0.0141, 0.168, None],
    },
    "GDPval-AA": {
        GPT_6_ASTRA: [0.855, 1.82, 2.43, 3.04, 4.53],
        GPT_6_1_SOL: [0.105, 0.231, 0.428, 0.558, 0.894],
        CLAUDE_OPUS_5_5: [0.214, 0.856, 1.54, 4.21, 8.92],
        CLAUDE_SONNET_5_5: [0.209, 0.318, 0.688, 1.95, 6.84],
        GEMINI_4_ARGON: [None, None, 1.82, None, None],
    },
    "AA-Briefcase": {
        GPT_6_ASTRA: [1.44, 3.94, 4.76, 6.56, 9.5],
        GPT_6_1_SOL: [0.177, 0.464, 0.837, 1.04, 2.31],
        CLAUDE_FABLE_5_2: [5.62, 6.84, 15.5, 28.6, 59.4],
        CLAUDE_OPUS_5_5: [1.15, 4.4, 6.27, 12.3, 21.0],
        CLAUDE_SONNET_5_5: [0.802, 1.39, 3.27, 6.98, 20.5],
        GEMINI_4_ARGON: [None, 4.75, 5.83, None, None],
        GEMINI_4_CARBON: [5.33, 5.06, 5.85, None, None],
        GPT_6_2_ASTRA: [0.42, 1.26, 2.79, 3.54, 5.49],
        GPT_6_2_SOL: [0.181, 0.525, 0.793, 1.01, 1.57],
        GEMINI_4_HYDROGEN: [0.21, 0.651, 1.73, 3.19, None],
    },
    "AutomationBench-AA": {
        GPT_6_ASTRA: [0.999, 1.18, 1.3, 1.41, 1.6],
        GPT_6_1_SOL: [0.159, 0.196, 0.226, 0.251, 0.297],
        CLAUDE_FABLE_5_2: [1.28, 1.33, 1.69, 2.27, 4.45],
        CLAUDE_OPUS_5_5: [0.493, 0.638, 0.699, 0.878, 1.43],
        CLAUDE_SONNET_5_5: [0.241, 0.262, 0.313, 0.422, 1.03],
        GEMINI_4_ARGON: [None, 0.566, 0.609, None, None],
        GEMINI_4_CARBON: [0.676, 1.12, 1.28, None, None],
        GPT_6_2_ASTRA: [0.449, 0.57, 0.676, 0.759, 0.948],
        GPT_6_2_SOL: [0.131, 0.18, 0.209, 0.237, 0.271],
        GEMINI_4_HYDROGEN: [0.168, 0.243, 0.375, 0.716, None],
    },
    "AA-LCR": {
        GPT_6_ASTRA: [0.95, 0.953, 0.96, 0.97, 0.997],
        GPT_6_1_SOL: [0.19, 0.19, 0.191, 0.193, 0.199],
        CLAUDE_OPUS_5_5: [0.587, 0.59, 0.592, 0.599, 0.677],
        CLAUDE_SONNET_5_5: [0.291, 0.292, 0.294, 0.297, 0.339],
        GEMINI_4_ARGON: [None, None, 0.236, None, None],
    },
    "GDP.pdf": {
        GPT_6_ASTRA: [1.7, 1.72, 1.79, 1.91, 2.08],
        GPT_6_1_SOL: [0.334, 0.337, 0.349, 0.368, 0.42],
        CLAUDE_FABLE_5_2: [1.53, 1.56, 1.64, 1.85, 2.52],
        CLAUDE_OPUS_5_5: [0.764, 0.795, 0.825, 0.964, 1.55],
        CLAUDE_SONNET_5_5: [0.372, 0.381, 0.409, 0.46, 0.794],
        GEMINI_4_ARGON: [None, 0.19, 0.259, None, None],
        GEMINI_4_CARBON: [0.191, 0.24, 0.424, None, None],
        GPT_6_2_ASTRA: [1.32, 1.33, 1.36, 1.4, 1.67],
        GPT_6_2_SOL: [0.331, 0.334, 0.341, 0.359, 0.396],
        GEMINI_4_HYDROGEN: [0.153, 0.174, 0.201, 0.437, None],
    },
    "AA Index coding category": {
        GPT_6_ASTRA: [1.7, 3.45, 3.88, 4.77, 7.32],
        GPT_6_1_SOL: [0.274, 0.492, 0.709, 0.832, 1.41],
        CLAUDE_FABLE_5_2: [3.01, 3.71, 11.2, 21.2, 38.7],
        CLAUDE_OPUS_5_5: [1.21, 2.64, 3.54, 7.41, 13.3],
        CLAUDE_SONNET_5_5: [0.664, 0.825, 1.33, 4.06, 12.0],
        GEMINI_4_ARGON: [None, 7.19, 8.33, None, None],
        GEMINI_4_CARBON: [8.5, 6.96, 8.17, None, None],
        GPT_6_2_ASTRA: [0.803, 1.85, 2.85, 3.4, 5.38],
        GPT_6_2_SOL: [0.274, 0.546, 0.703, 0.854, 1.3],
        GEMINI_4_HYDROGEN: [0.49, 1.21, 2.67, 4.14, None],
    },
    "Terminal-Bench 4.0": {
        GPT_6_ASTRA: [2.25, 4.43, 4.05, 5.86, 8.5],
        GPT_6_1_SOL: [0.383, 0.614, 0.828, 1.03, 1.82],
        CLAUDE_FABLE_5_2: [4.34, 5.25, 13.5, 20.8, 31.6],
        CLAUDE_OPUS_5_5: [2.08, 4.04, 5.12, 8.78, 13.1],
        CLAUDE_SONNET_5_5: [1.28, 1.58, 2.19, 6.08, 12.6],
        GEMINI_4_ARGON: [None, 6.42, 6.78, None, None],
        GEMINI_4_CARBON: [6.05, 6.24, 7.11, None, None],
        GPT_6_2_ASTRA: [0.795, 1.75, 2.5, 2.88, 4.66],
        GPT_6_2_SOL: [0.35, 0.677, 0.771, 0.934, 1.29],
        GEMINI_4_HYDROGEN: [0.526, 1.58, 2.8, 3.66, None],
    },
    "FrontierCode-AA 2.0": {
        GPT_6_ASTRA: [1.34, 2.8, 3.77, 4.04, 6.54],
        GPT_6_1_SOL: [0.201, 0.411, 0.63, 0.703, 1.13],
        CLAUDE_FABLE_5_2: [2.12, 2.69, 9.64, 21.4, 43.4],
        CLAUDE_OPUS_5_5: [0.627, 1.71, 2.49, 6.49, 13.5],
        CLAUDE_SONNET_5_5: [0.25, 0.324, 0.76, 2.71, 11.6],
        GEMINI_4_ARGON: [None, 7.7, 9.37, None, None],
        GEMINI_4_CARBON: [10.1, 7.44, 8.88, None, None],
        GPT_6_2_ASTRA: [0.808, 1.91, 3.08, 3.75, 5.87],
        GPT_6_2_SOL: [0.224, 0.458, 0.658, 0.801, 1.3],
        GEMINI_4_HYDROGEN: [0.467, 0.962, 2.58, 4.47, None],
    },
    "Terminal-Bench Science 0.1": {
        GPT_6_ASTRA: [4.12, 7.2, 8.66, 7.91, 17.5],
        GPT_6_1_SOL: [0.242, 0.872, 1.61, 2.3, 3.34],
        CLAUDE_FABLE_5_2: [8.78, 11.0, 24.3, 31.4, 45.2],
        CLAUDE_OPUS_5_5: [2.81, 6.8, 10.0, 14.1, 20.0],
        CLAUDE_SONNET_5_5: [1.23, 2.14, 4.98, 12.8, 23.8],
        GEMINI_4_ARGON: [None, 11.2, 12.2, None, None],
        GEMINI_4_CARBON: [13.5, 12.5, 14.2, None, None],
        GPT_6_2_ASTRA: [1.99, 5.64, 5.19, 6.27, 9.78],
        GPT_6_2_SOL: [0.408, 1.03, 1.48, 1.49, 2.45],
        GEMINI_4_HYDROGEN: [0.712, 2.16, 5.27, 8.3, None],
    },
    "SciCode": {
        GPT_6_ASTRA: [0.0425, 0.0509, 0.0696, 0.122, 0.232],
        GPT_6_1_SOL: [0.00842, 0.00931, 0.013, 0.022, 0.0434],
        CLAUDE_OPUS_5_5: [0.0264, 0.0355, 0.0402, 0.0676, 0.469],
        CLAUDE_SONNET_5_5: [0.0129, 0.0135, 0.016, 0.0237, 0.278],
        GEMINI_4_ARGON: [None, None, 0.106, None, None],
    },
    "Agents' Last Exam v1.1": {
        GPT_6_ASTRA: [5.4, 6.21, 6.87, 7.56, 8.99],
        GPT_6_2_ASTRA: [0.469, 1.06, 2.05, 2.89, 4.47],
        GPT_6_1_SOL: [0.206, 0.456, 0.976, 0.98, 2.02],
        GPT_6_2_SOL: [0.265, 0.57, 0.69, 0.863, 1.32],
        CLAUDE_FABLE_5_2: [None, None, None, None, 60.1],
        CLAUDE_OPUS_5_5: [None, None, None, None, 17.6],
        GEMINI_4_CARBON: [None, None, 4.6, None, None],
    },
    "FrontierCode 2.0": {
        GPT_6_ASTRA: [2.44, 3.49, 4.28, 4.54, 6.68],
        GPT_6_2_ASTRA: [1.41, 2.47, 3.95, 4.29, 5.97],
        GPT_6_1_SOL: [0.34, 0.49, 0.65, 0.7, 1.03],
        GPT_6_2_SOL: [0.4, 0.68, 0.88, 0.98, 1.29],
        CLAUDE_FABLE_5_2: [2.1, 2.48, 6.72, 14.2, 44.7],
        CLAUDE_OPUS_5_5: [0.75, 1.7, 2.42, 5.18, 12.8],
        GEMINI_4_CARBON: [5.49, 5.16, 5.83, None, None],
    },
    "LifeVal": {
        GPT_6_ASTRA: [3.51, 5.3, 6.52, 6.94, 9.04],
        GPT_6_2_ASTRA: [0.59, 1.56, 2.41, 2.94, 4.23],
        GPT_6_1_SOL: [0.52, 0.73, 0.88, 0.96, 1.27],
        GPT_6_2_SOL: [0.089, 0.38, 0.65, 0.88, 1.27],
    },
    "SecureSWE": {
        GPT_6_ASTRA: [1.1, 1.91, 2.88, 3.21, 4.91],
        GPT_6_2_ASTRA: [0.78, 1.4, 2.5, 3.12, 5.26],
        GPT_6_1_SOL: [0.13, 0.3, 0.47, 0.58, 0.87],
        GPT_6_2_SOL: [0.16, 0.25, 0.45, 0.62, 0.99],
    },
    "Vals Science Index v1": {
        GPT_6_ASTRA: [None, None, None, None, 8.03],
        GPT_6_2_ASTRA: [1.05, 1.88, 2.25, 2.47, 4.17],
        GPT_6_1_SOL: [None, None, None, None, 1.36],
        GPT_6_2_SOL: [0.19, 0.44, 0.63, 0.71, 1.03],
        CLAUDE_FABLE_5_2: [None, None, 8.79, None, None],
        CLAUDE_OPUS_5_5: [None, None, None, None, 8.71],
    },
    "BenchCAD 2.1 Core": {
        GPT_6_ASTRA: [1.14, 3.73, 5.38, 6.32, 9.71],
        GPT_6_2_ASTRA: [0.98, 1.94, 2.89, 3.36, 5.43],
        GPT_6_1_SOL: [0.19, 0.55, 0.87, 1.05, 1.61],
        GPT_6_2_SOL: [0.15, 0.29, 0.75, 1.0, 1.6],
        CLAUDE_FABLE_5_2: [1.89, 2.66, 9.99, 23.2, 50.8],
        CLAUDE_OPUS_5_5: [0.17, 1.2, 2.7, 9.0, 20.0],
    },
    "AutomationBench 1.0.6": {
        GPT_6_ASTRA: [1.08, 1.27, 1.44, 1.5, 1.73],
        GPT_6_2_ASTRA: [0.44, 0.55, 0.67, 0.7, 0.83],
        GPT_6_1_SOL: [0.16, 0.19, 0.23, 0.25, 0.3],
        GPT_6_2_SOL: [0.13, 0.18, 0.21, 0.23, 0.27],
        CLAUDE_FABLE_5_2: [1.3, 1.35, 1.69, 2.29, 4.64],
        CLAUDE_OPUS_5_5: [0.51, 0.65, 0.71, 0.89, 1.44],
        GEMINI_4_CARBON: [1.02, 1.65, 2.12, None, None],
    },
    "PatchBench": {
        GPT_6_ASTRA: [0.79, 1.35, 2.15, 2.45, 4.18],
        GPT_6_2_ASTRA: [0.38, 0.85, 1.79, 2.45, 4.18],
        GPT_6_1_SOL: [0.12, 0.22, 0.37, 0.45, 0.74],
        GPT_6_2_SOL: [0.085, 0.17, 0.36, 0.51, 0.85],
    },
}
COST_UNITS = {"AA Intelligence Index": "US$ to run the whole index, log scale",
              "Vals Index": "US$ per test, log scale", "Vibe Code Bench v1.1": "US$ per test, log scale"}
DEFAULT_COST_UNIT = "US$ per task, log scale"

TITLE = "AI scores"
SUBTITLE = ("Tap a model to hide or show it. Show exactly two models to see where they come closest: "
            "a dashed line joins their nearest scores at different effort levels. Hover a level to read every score. "
            "To zoom in on some points, drag across them with a mouse, or press and hold a finger for a second, then drag. "
            "Switch the x axis to cost to see what each effort level costs: the best models sit top left. "
            "There, a faded point is beaten outright: a shown model scores at least as high for no more money. "
            "The grey line joins the points nothing shown beats.")

FOOTNOTES = {
    "Intelligence": "Scores checked on 18 November 2026. Every published effort level is shown; gaps mean no score, not zero. "
                    "The Claude models use adaptive reasoning; Argon and Carbon stop at high, Hydrogen at xhigh. AA now covers Argon at medium and high. "
                    "ARC Prize has no Sonnet max run. GDPval-AA and AA-Briefcase are relative Elo ratings, refreshed together. "
                    "AA Intelligence Index is v5.0.1; its costs are for the whole index, while other cost axes are US dollars per task. "
                    "AA publishes weighted task costs: we divide by its benchmark weights to recover per-task costs. "
                    "Argon and Carbon's AA prices use Google's introductory US$2/US$10 per million tokens; Hydrogen is US$1.50/US$7.50. "
                    "Missing costs do not remove scores: the effort chart remains available. OpenAI launch comparisons are labeled "
                    "separately from AA runs. On Agents' Last Exam, Fable excludes nine fallback tasks, so it is not a perfectly "
                    "matched-task comparison. HealthBench Professional replaces the older HealthBench; AA and OpenAI runs stay separate. "
                    "System-card results without a stated effort are bars marked “not stated”, never assigned to max.",
    "Coding": "FrontierCode 2.0 replaces the 1.1 Main chart. FrontierCode-AA 2.0 uses AA's harness; the other 2.0 chart "
              "is OpenAI's published comparison and must not be treated as the same run. Neither GPT-6.2 model has a published "
              "DeepSWE, SciCode or SWE-Bench Pro score in the checked sources. DeepSWE's Argon point is Google's high-effort run; "
              "its GPT points are OpenAI's. SWE-Bench Pro bars are each lab's own harness, so compare cautiously. "
              "The coding category uses FrontierCode-AA and Terminal-Bench 4.0 with 15:10 weights, including their costs. "
              "SecureSWE, PatchBench and ExploitBench are internal cyber evaluations with safeguards disabled, not ordinary "
              "deployment results. NanoGPT v5 omits older Astra's v4 score rather than mixing versions. AA-3D is human-preference "
              "Elo, not percent accuracy; its reported effort is not specified. No benchmark is omitted just for sparse coverage. "
              "The cost frontier compares the plotted point estimates, not statistical significance or differing harnesses.",
}

LINE_WIDTH = 1.8
MARKER_SIZE = 6.5
MARKER_RING = 1.6
LABEL_FONT_SIZE = 9.5
END_LABEL_MIN_GAP_POINTS = 12
NAME_FONT_SIZE = 7.5
NAME_FONT_FAMILY = "Menlo"  # ships with macOS and iOS, so the SVG renders the font it was measured in
NAME_GAP_POINTS = 5



@dataclass(frozen=True)
class Layout:
    """One render of every chart, shown while the viewport is at least min_viewport pixels wide (up to the next layout).

    The SVG scales to its column, so the figure size in inches sets the text size: each layout's figure is about as
    wide as its column divided by 1.4 to 1.9, which keeps chart text at about 12 to 17px. Wider layouts widen the plot.
    """
    name: str
    min_viewport: int
    figure_size: tuple[float, float]


LAYOUTS = [
    Layout("phone", 0, (4.55, 3.9)),  # 3.8 plot inches plus the name column
    Layout("desktop", 700, (5.0, 4.6)),
    Layout("wide", 1600, (7.0, 4.8)),
    Layout("wider", 2100, (9.5, 5.0)),
    Layout("widest", 2800, (12.5, 5.2)),
]
AXES_LEFT = 0.42
# The right margin holds the model-name column beside the end labels, outside the plot, so names never meet plot labels.
AXES_RIGHT = 0.75
AXES_TOP = 0.22
AXES_BOTTOM = 0.32
COST_AXIS_LABEL_HEIGHT = 0.2  # the cost charts name their x-axis unit
COST_AXES_RIGHT = 0.1  # cost charts have no name column; their end labels sit inside the plot
X_LIMITS = (-0.85, len(EFFORT_LEVELS) - 1 + 0.9)


def configure_fonts() -> None:
    font_manager.fontManager.addfont("/System/Library/Fonts/HelveticaNeue.ttc")
    font_manager.fontManager.addfont("/System/Library/Fonts/Menlo.ttc")
    plt.rcParams.update({
        "font.family": "Helvetica Neue",
        "font.size": 9,
        "svg.fonttype": "none",
        "axes.edgecolor": BASELINE.light,
        "xtick.color": TEXT_MUTED.light,
        "ytick.color": TEXT_MUTED.light,
        "figure.facecolor": "none",
        "axes.facecolor": "none",
        "savefig.facecolor": "none",
    })


def present_points(scores: Scores) -> list[tuple[int, float]]:
    """Keep only the effort levels that have a score.

    >>> present_points([None, 1.0, 2.5])
    [(1, 1.0), (2, 2.5)]
    """
    return [(index, score) for index, score in enumerate(scores) if score is not None]


def labeled_levels(scores: Scores) -> set[int]:
    """The levels that always carry a label: the lowest (start label) and the highest (end label).

    >>> sorted(labeled_levels([None, 1.0, 2.0, 3.0]))
    [1, 3]
    """
    points = present_points(scores)
    return {points[0][0], points[-1][0]}


def spread_label_positions(positions: list[float], minimum_gap: float) -> list[float]:
    """Spread sorted positions so neighbors sit at least minimum_gap apart, each crowded group centered on its mean.

    >>> spread_label_positions([10.0, 12.0], 6.0)
    [8.0, 14.0]
    >>> spread_label_positions([0.0, 20.0], 6.0)
    [0.0, 20.0]
    >>> spread_label_positions([10.0, 11.0, 12.0], 6.0)
    [5.0, 11.0, 17.0]
    """
    def layout(group: list[float]) -> list[float]:
        center = sum(group) / len(group)
        return [center + (offset - (len(group) - 1) / 2) * minimum_gap for offset in range(len(group))]

    groups: list[list[float]] = []
    for position in sorted(positions):
        groups.append([position])
        while len(groups) > 1 and layout(groups[-1])[0] - layout(groups[-2])[-1] < minimum_gap:
            groups[-2:] = [groups[-2] + groups[-1]]
    return [placed for group in groups for placed in layout(group)]


def closest_meeting_levels(first: Scores, second: Scores) -> tuple[int, int]:
    """Find the two models' effort levels whose scores are closest; without overlap, that is the facing extremes.

    Ties go to the pair that adds fewer labels beyond each model's lowest and highest levels.

    >>> closest_meeting_levels([10.0, 20.0, 30.0], [None, 21.0, 40.0])
    (1, 1)
    >>> closest_meeting_levels([10.0, 20.0], [None, 50.0, 60.0])
    (1, 1)
    >>> closest_meeting_levels([10.0, 30.0, 25.0], [None, 55.0, 50.0, 60.0])
    (1, 2)
    """
    first_labeled = labeled_levels(first)
    second_labeled = labeled_levels(second)

    def rank(pair: tuple[tuple[int, float], tuple[int, float]]) -> tuple[float, int]:
        (first_index, first_score), (second_index, second_score) = pair
        added_labels = (first_index not in first_labeled) + (second_index not in second_labeled)
        return round(abs(first_score - second_score), 1), added_labels

    (first_index, _), (second_index, _) = min(itertools.product(present_points(first), present_points(second)), key=rank)
    return first_index, second_index


def nearest_score(scores: Scores, index: int) -> float:
    """Score at the given effort level, or at the nearest level that has one.

    >>> nearest_score([None, 5.0, 9.0], 0)
    5.0
    """
    return min(present_points(scores), key=lambda point: abs(point[0] - index))[1]


Meeting = tuple[tuple[Model, int], tuple[Model, int]]


def cross_level_meetings(metric: Metric) -> list[Meeting]:
    """Each model pair's closest points, skipping pairs that meet at the same effort level, where their lines already touch."""
    meetings = []
    for first, second in itertools.combinations(metric.models, 2):
        first_index, second_index = closest_meeting_levels(metric.scores[first], metric.scores[second])
        meetings.append(((first, first_index), (second, second_index)))
    return [meeting for meeting in meetings if meeting[0][1] != meeting[1][1]]


def element_id(role: str, *models: Model) -> str:
    """Tag an artist with its role and models. The page shows it only while all its models are visible.

    >>> element_id("meeting", GPT_6_ASTRA, GPT_6_1_SOL)
    'meeting__gpt-6-astra__gpt-6-1-sol'
    """
    return "__".join([role, *(model.slug for model in models)])


GATE_PREFIX = "by-"


def gated_id(role: str, models: list[Model], gates: Iterable[Model]) -> str:
    """Like element_id, plus the models whose showing changes the artist: it fades (marker) or hides (frontier) then.

    >>> gated_id("marker", [GPT_6_ASTRA], [GPT_6_1_SOL])
    'marker__gpt-6-astra__by-gpt-6-1-sol'
    """
    return "__".join([element_id(role, *models), *(GATE_PREFIX + model.slug for model in gates)])


def element_models(artist: Artist) -> set[str]:
    return {part for part in artist.get_gid().split("__")[1:] if not part.startswith(GATE_PREFIX)}


# Meeting and frontier lines are faint references, like gridlines: labels may sit over them.
MEETING_LINE = "meeting-line"
FRONTIER = "frontier"

Placement = tuple[float, float, str, str]

ABOVE: Placement = (0, 7, "center", "bottom")
BELOW: Placement = (0, -7, "center", "top")
ABOVE_LEFT: Placement = (-6, 6, "right", "bottom")
ABOVE_RIGHT: Placement = (6, 6, "left", "bottom")
BELOW_LEFT: Placement = (-6, -6, "right", "top")
BELOW_RIGHT: Placement = (6, -6, "left", "top")
LEFT: Placement = (-7, 0, "right", "center")
RIGHT: Placement = (7, 0, "left", "center")

# Keyed by (label role, whether the side away from the nearest other model is above).
PLACEMENT_ORDERS: dict[tuple[str, bool], list[Placement]] = {
    ("meeting", True): [ABOVE, ABOVE_RIGHT, ABOVE_LEFT, BELOW, BELOW_RIGHT, BELOW_LEFT, RIGHT, LEFT],
    ("meeting", False): [BELOW, BELOW_RIGHT, BELOW_LEFT, ABOVE, ABOVE_RIGHT, ABOVE_LEFT, RIGHT, LEFT],
    ("start", True): [LEFT, ABOVE_LEFT, ABOVE, BELOW_LEFT, BELOW, ABOVE_RIGHT, BELOW_RIGHT, RIGHT],
    ("start", False): [LEFT, BELOW_LEFT, BELOW, ABOVE_LEFT, ABOVE, BELOW_RIGHT, ABOVE_RIGHT, RIGHT],
}

LABEL_HALO = {"boxstyle": "round,pad=0.12", "facecolor": SURFACE.light, "edgecolor": "none"}
POINT_LABEL_STYLE = {"fontsize": LABEL_FONT_SIZE, "fontweight": "medium", "color": TEXT_PRIMARY.light, "zorder": 5,
                     "bbox": LABEL_HALO}
DIM_LABEL_STYLE = {"fontsize": NAME_FONT_SIZE, "family": NAME_FONT_FAMILY, "color": TEXT_MUTED.light, "zorder": 5,
                   "bbox": LABEL_HALO}

LabelPart = tuple[str, dict[str, object]]

# (x, y) unit direction and the text alignment that keeps the label on that side of its point.
DIRECTIONS: list[tuple[float, float, str, str]] = [
    (1, 0, "left", "center"), (0.8, 0.8, "left", "bottom"), (0.8, -0.8, "left", "top"), (0, 1, "center", "bottom"),
    (0, -1, "center", "top"), (-0.8, 0.8, "right", "bottom"), (-0.8, -0.8, "right", "top"), (-1, 0, "right", "center"),
]
# Cost charts crowd their line ends unevenly, so their labels search outward ring by ring; far rings get a leader line.
COST_END_PLACEMENTS: list[Placement] = [(x * radius, y * radius, horizontal, vertical)
                                        for radius in (7, 14, 22, 32, 44, 58) for x, y, horizontal, vertical in DIRECTIONS]
LEADER_MIN_DISTANCE_POINTS = 12



def line_hits(axes: Axes, line: Line2D, box: Bbox) -> bool:
    points = axes.transData.transform(line.get_xydata())
    marker_radius = (line.get_markersize() / 2 + line.get_markeredgewidth() / 2) * axes.figure.dpi / 72
    path_hit = len(points) >= 2 and MatplotlibPath(points).intersects_bbox(box, filled=False)
    marker_hit = line.get_marker() != "None" and any(
        Bbox.from_bounds(x - marker_radius, y - marker_radius, 2 * marker_radius, 2 * marker_radius).overlaps(box)
        for x, y in points)
    return path_hit or marker_hit


def text_box(text: Text, renderer: RendererBase) -> Bbox:
    """The text's own box: an annotation's extent would also span its leader line, which is not an obstacle."""
    if isinstance(text, Annotation):
        text.update_positions(renderer)  # applies the offset that Annotation.get_window_extent would apply
    return Text.get_window_extent(text, renderer)


def label_is_clear(axes: Axes, label: Annotation, renderer: RendererBase, scene: set[str], ignored_ids: set[str],
                   own_parts: list[Annotation]) -> bool:
    """A label is clear when it stays off the axes' sides and baseline and touches no line, marker or other label of its scene.

    The scene is the set of model slugs visible together with the label. The top is open. Meeting lines,
    artists whose gid is in ignored_ids, and the label's own other parts do not count.
    """
    def blocks(artist: Artist) -> bool:
        gid = artist.get_gid()
        return artist not in own_parts and gid not in ignored_ids and not gid.startswith((MEETING_LINE, FRONTIER)) \
            and element_models(artist) <= scene

    box = text_box(label, renderer).padded(2)
    plot = axes.get_window_extent(renderer)
    inside = plot.x0 <= box.x0 and box.x1 <= plot.x1 and plot.y0 <= box.y0
    hits_line = any(line_hits(axes, line, box) for line in axes.lines if blocks(line))
    hits_text = any(text_box(text, renderer).overlaps(box) for text in axes.texts if blocks(text))
    return inside and not hits_line and not hits_text


def annotate_parts(axes: Axes, point: tuple[float, float], parts: list[LabelPart], placement: Placement,
                   gid: str) -> list[Annotation]:
    """Annotate the first part at the placement and chain the others beside it, on the side away from the point."""
    renderer = axes.figure.canvas.get_renderer()
    dx, dy, horizontal, vertical = placement
    (first_text, first_style), *others = parts
    leader = {"arrowprops": {"arrowstyle": "-", "color": BASELINE.light, "linewidth": 0.6, "shrinkA": 1, "shrinkB": 4}} \
        if math.hypot(dx, dy) > LEADER_MIN_DISTANCE_POINTS else {}
    annotations = [axes.annotate(first_text, point, xytext=(dx, dy), textcoords="offset points",
                                 ha=horizontal, va=vertical, gid=gid, **first_style, **leader)]
    if leader:
        annotations[0].arrow_patch.set_gid(gid)  # the leader draws outside the text's SVG group, so tag it too
    point_x, point_y = axes.transData.transform(point)
    points_per_pixel = 72 / axes.figure.dpi
    leftward = horizontal == "right"
    for text, style in others:
        box = text_box(annotations[-1], renderer)
        edge = box.x0 - point_x if leftward else box.x1 - point_x
        offset = (edge * points_per_pixel + (-NAME_GAP_POINTS if leftward else NAME_GAP_POINTS),
                  ((box.y0 + box.y1) / 2 - point_y) * points_per_pixel)
        annotations.append(axes.annotate(text, point, xytext=offset, textcoords="offset points",
                                         ha="right" if leftward else "left", va="center", gid=gid, **style))
    return annotations


def place_label(axes: Axes, metric: Metric, point: tuple[float, float], parts: list[LabelPart],
                placements: list[Placement], gid: str, owner: Model, scene: list[Model], required: bool = True) -> None:
    """Put the label at the first clear placement, relaxing the rules pass by pass in crowded spots.

    The passes: touch no series line; then cover only its owner's line; then cover any line, with its halo.
    Markers and other labels always block. When no pass finds a spot, a required label raises ValueError
    and an optional one is left out; its score stays in the hover tooltip and the table.
    """
    renderer = axes.figure.canvas.get_renderer()
    scene_slugs = {model.slug for model in scene}
    passes = [set(), {element_id("series", owner)}, {element_id("series", model) for model in scene}]
    for ignored_ids, placement in itertools.product(passes, placements):
        annotations = annotate_parts(axes, point, parts, placement, gid)
        if all(label_is_clear(axes, annotation, renderer, scene_slugs, ignored_ids, annotations)
               for annotation in annotations):
            return
        for annotation in annotations:
            annotation.remove()
    if not required:
        return
    raise ValueError(f"{metric.name}: no clear spot for {owner.name}'s label {' '.join(text for text, _ in parts)}")


def value_part(metric: Metric, score: float) -> LabelPart:
    return metric.label(score), POINT_LABEL_STYLE


def away_is_above(metric: Metric, model: Model, index: int, scene: list[Model]) -> bool:
    """Prefer the side away from the nearest other model's line, or above for a single-model scene."""
    score = metric.scores[model][index]
    neighbor = min((nearest_score(metric.scores[other], index) for other in scene if other is not model),
                   key=lambda other_score: abs(other_score - score), default=score)
    return score >= neighbor


def draw_start_labels(axes: Axes, metric: Metric) -> None:
    """Label each model's lowest effort level, clear of every model's lines and labels, where crowding allows.

    A model with a single point skips it: its end label already shows that score."""
    for model in (model for model in metric.models if len(present_points(metric.scores[model])) > 1):
        index = present_points(metric.scores[model])[0][0]
        score = metric.scores[model][index]
        placements = PLACEMENT_ORDERS[("start", away_is_above(metric, model, index, metric.models))]
        place_label(axes, metric, (index, score), [value_part(metric, score)], placements, element_id("start", model),
                    model, metric.models, required=False)


def draw_meetings(axes: Axes, metric: Metric) -> None:
    """Draw each cross-level meeting: a faint dashed line at the lower of the two scores, and labels on its points.

    A meeting shows only while its two models are the only visible ones, so its labels need to clear only their lines.
    """
    for meeting in cross_level_meetings(metric):
        (first, first_index), (second, second_index) = meeting
        height = min(metric.scores[first][first_index], metric.scores[second][second_index])
        axes.plot([first_index, second_index], [height, height], color=TEXT_MUTED.light, linewidth=0.9,
                  linestyle=(0, (2.5, 2.5)), alpha=0.8, zorder=2.5, gid=element_id(MEETING_LINE, first, second))
        for model, index in meeting:
            if index in labeled_levels(metric.scores[model]):
                continue
            score = metric.scores[model][index]
            placements = PLACEMENT_ORDERS[("meeting", away_is_above(metric, model, index, [first, second]))]
            place_label(axes, metric, (index, score), [value_part(metric, score)], placements,
                        element_id("meeting", first, second), model, [first, second])


def draw_end_labels(axes: Axes, metric: Metric) -> None:
    """Label each series' last score to the right of its end point, with a leader line when displaced.

    A dim model name follows each end label, in one column past the widest end label, so no one has to decode colors.
    """
    ends = sorted(((model, *present_points(metric.scores[model])[-1]) for model in metric.models), key=lambda end: end[2])
    to_display = axes.transData.transform
    from_display = axes.transData.inverted().transform
    minimum_gap_pixels = END_LABEL_MIN_GAP_POINTS * axes.figure.dpi / 72
    label_heights = spread_label_positions([to_display((index, score))[1] for _, index, score in ends], minimum_gap_pixels)
    label_x = len(EFFORT_LEVELS) - 1 + 0.32
    label_ys = [from_display((0, label_height))[1] for label_height in label_heights]
    for (model, index, score), label_y in zip(ends, label_ys):
        if abs(label_y - score) > 1e-9:
            axes.plot([index + 0.1, label_x - 0.06], [score, label_y], color=BASELINE.light, linewidth=0.6,
                      solid_capstyle="round", zorder=2, gid=element_id("leader", model))
        axes.text(label_x, label_y, metric.label(score), color=TEXT_PRIMARY.light, fontsize=LABEL_FONT_SIZE,
                  fontweight="medium", va="center", ha="left", gid=element_id("end", model))
    renderer = axes.figure.canvas.get_renderer()
    widest_end = max(text.get_window_extent(renderer).x1 for text in axes.texts)
    name_x = from_display((widest_end + NAME_GAP_POINTS * axes.figure.dpi / 72, 0))[0]
    for (model, _, _), label_y in zip(ends, label_ys):
        axes.text(name_x, label_y, model.name, color=TEXT_MUTED.light, fontsize=NAME_FONT_SIZE, family=NAME_FONT_FAMILY,
                  va="center", ha="left", gid=element_id("name", model))


def draw_series(axes: Axes, metric: Metric, model: Model, points: list[tuple[int, float, float]],
                gates: dict[int, Iterable[Model]] | None = None) -> None:
    """Draw one model's line and markers through (level, x, score) points, hollow where AA estimated the score.

    A marker fades while any of its level's gate models is shown.
    """
    axes.plot([x for _, x, _ in points], [score for _, _, score in points], color=model.color.light,
              linewidth=LINE_WIDTH, solid_joinstyle="round", solid_capstyle="round", zorder=3,
              gid=element_id("series", model))
    for index, x, score in points:
        is_estimated = (model, EFFORT_LEVELS[index]) in metric.estimated
        axes.plot(x, score, marker="o", markersize=MARKER_SIZE,
                  markerfacecolor=SURFACE.light if is_estimated else model.color.light,
                  markeredgecolor=model.color.light if is_estimated else SURFACE.light,
                  markeredgewidth=MARKER_RING, zorder=4, gid=gated_id("marker", [model], (gates or {}).get(index, ())))


def style_axes(axes: Axes, metric: Metric) -> None:
    axes.set_ylim(*metric.y_range)
    axes.yaxis.set_major_locator(matplotlib.ticker.MultipleLocator(metric.tick_step))
    axes.grid(axis="y", color=GRIDLINE.light, linewidth=0.7)
    axes.set_axisbelow(True)
    for side in ("top", "right", "left"):
        axes.spines[side].set_visible(False)
    axes.spines["bottom"].set_color(BASELINE.light)
    axes.spines["bottom"].set_linewidth(0.8)
    axes.tick_params(axis="both", which="both", length=0, labelsize=9, pad=5)


def draw_panel(axes: Axes, metric: Metric) -> None:
    for model in metric.models:
        draw_series(axes, metric, model, [(index, index, score) for index, score in present_points(metric.scores[model])])
    style_axes(axes, metric)
    axes.set_xlim(*X_LIMITS)
    axes.set_xticks(range(len(EFFORT_LEVELS)), EFFORT_LEVELS)
    axes.spines["bottom"].set_bounds(-0.35, len(EFFORT_LEVELS) - 1 + 0.35)
    axes.figure.canvas.draw()
    draw_end_labels(axes, metric)
    draw_start_labels(axes, metric)
    draw_meetings(axes, metric)


def cost_points(metric: Metric, model: Model) -> list[tuple[int, float, float]]:
    """The (level, cost, score) points where the model has both a score and a cost.

    >>> cost_points(INTELLIGENCE[0], GPT_6_1_SOL)[0]
    (0, 238.0, 34.8)
    """
    costs = metric.costs.get(model, [None] * len(EFFORT_LEVELS))
    return [(index, cost, score) for index, (score, cost) in enumerate(zip(metric.scores[model], costs))
            if score is not None and cost is not None]


CostPoint = tuple[Model, int, float, float]  # model, level index, cost, score


def all_cost_points(metric: Metric) -> list[CostPoint]:
    return [(model, index, cost, score) for model in metric.models for index, cost, score in cost_points(metric, model)]


def beats(winner: CostPoint, loser: CostPoint) -> bool:
    """Whether winner scores at least as high for no more money, and is not the same deal.

    >>> beats((GPT_6_ASTRA, 0, 1.0, 50.0), (GPT_6_1_SOL, 1, 2.0, 50.0))
    True
    >>> beats((GPT_6_ASTRA, 0, 1.0, 50.0), (GPT_6_1_SOL, 1, 1.0, 50.0))
    False
    """
    _, _, winner_cost, winner_score = winner
    _, _, loser_cost, loser_score = loser
    return winner_cost <= loser_cost and winner_score >= loser_score \
        and (winner_cost, winner_score) != (loser_cost, loser_score)


def beaters(metric: Metric) -> dict[CostPoint, dict[Model, CostPoint]]:
    """For each point, each model's cheapest point that beats it, the point's own model included.

    A point is beaten outright while any of these models is shown.
    """
    points = all_cost_points(metric)
    by_cost_descending = sorted(points, key=lambda point: -point[2])
    return {point: {winner[0]: winner for winner in by_cost_descending if beats(winner, point)} for point in points}


def frontier_segments(metric: Metric) -> list[tuple[CostPoint, CostPoint, set[Model]]]:
    """Every segment that joins two unbeaten points for some set of shown models, with the models whose showing hides it.

    A segment from a cheaper, lower point to a dearer, higher one lies on the frontier while both its models are shown
    and none of its blockers is: the models that beat either end, and those with a point priced between the ends
    that scores above the cheaper end.
    """
    points = all_cost_points(metric)
    beaten_by = beaters(metric)
    rising = [(cheap, dear) for cheap, dear in itertools.permutations(points, 2) if cheap[2] < dear[2] and cheap[3] < dear[3]]
    segments = []
    for cheap, dear in rising:
        between = {model for model, _, cost, score in points if cheap[2] < cost < dear[2] and score > cheap[3]}
        blockers = set(beaten_by[cheap]) | set(beaten_by[dear]) | between
        segments.append((cheap, dear, blockers))
    return [(cheap, dear, blockers) for cheap, dear, blockers in segments
            if cheap[0] not in blockers and dear[0] not in blockers]


def cost_label(value: float) -> str:
    """
    >>> [cost_label(value) for value in (0.002, 0.05, 1.5, 20, 1000, 12500)]
    ['$0.002', '$0.05', '$1.5', '$20', '$1k', '$12.5k']
    """
    return f"${value / 1000:.3g}k" if value >= 1000 else f"${value:.3g}"


def draw_cost_panel(axes: Axes, metric: Metric) -> None:
    """Plot score against the benchmark's own cost, log scale; each model's line still runs through its effort levels.

    Only each line's last point carries a label: its value and dim model name, plus its level if not max. Points
    crowd here, and the x axis is not effort levels, so a first-point label would anchor nothing; hover shows every point.
    Where points pile up (on narrow layouts), a label with no clear spot is left out; hover still shows its point.
    A point that a shown model beats outright fades, and a grey line joins the points no shown model beats.
    """
    models = [model for model in metric.models if cost_points(metric, model)]
    beaten_by = beaters(metric)
    for model in models:
        gates = {index: beaten_by[(model, index, cost, score)] for index, cost, score in cost_points(metric, model)}
        draw_series(axes, metric, model, cost_points(metric, model), gates)
    for cheap, dear, blockers in frontier_segments(metric):
        axes.plot([cheap[2], dear[2]], [cheap[3], dear[3]], color=TEXT_SECONDARY.light, linewidth=1.5, alpha=0.6,
                  solid_capstyle="round", zorder=2.5, gid=gated_id(FRONTIER, [cheap[0], dear[0]], blockers))
    style_axes(axes, metric)
    costs = [cost for model in models for _, cost, _ in cost_points(metric, model)]
    decades = math.log10(max(costs) / min(costs))
    axes.set_xscale("log")
    axes.set_xlim(min(costs) / 10 ** (0.12 * decades + 0.1), max(costs) * 10 ** (0.35 * decades + 0.2))
    tick_multiples = (1, 2, 5) if decades <= 1.5 else (1, 3) if decades <= 2.5 else (1,)
    axes.xaxis.set_major_locator(matplotlib.ticker.LogLocator(base=10, subs=tick_multiples))
    axes.xaxis.set_minor_locator(matplotlib.ticker.NullLocator())
    axes.xaxis.set_major_formatter(matplotlib.ticker.FuncFormatter(lambda value, _: cost_label(value)))
    axes.grid(axis="x", color=GRIDLINE.light, linewidth=0.7)
    axes.set_xlabel(metric.cost_unit, fontsize=8.5, color=TEXT_MUTED.light, labelpad=6)
    axes.figure.canvas.draw()
    for model in models:
        index, cost, score = cost_points(metric, model)[-1]
        level = "" if EFFORT_LEVELS[index] == "max" else f" · {EFFORT_LEVELS[index]}"  # most lines end at max
        parts = [value_part(metric, score), (f"{model.name}{level}", DIM_LABEL_STYLE)]
        place_label(axes, metric, (cost, score), parts, COST_END_PLACEMENTS, element_id("end", model), model, models,
                    required=False)


def inline_svg(svg: str) -> str:
    """Make matplotlib's SVG fit inline in the page: no fixed size, theme colors as CSS variables, gids as CSS classes.

    >>> inline_svg('<?xml?>\\n<svg width="9pt" height="9pt" viewBox="0 0 9 9"><g id="end__gpt-6-sol" style="fill: #0b0b0b"/></svg>')
    '<svg class="chart" viewBox="0 0 9 9"><g class="end m-gpt-6-sol" style="fill: var(--ink-1)"/></svg>'
    """
    svg = svg[svg.index("<svg"):]
    # matplotlib's global "*" rule and metadata would leak into, or bloat, the page.
    svg = re.sub(r"<metadata>.*?</metadata>|<style[^>]*>.*?</style>", "", svg, flags=re.DOTALL)
    svg = re.sub(r' width="[\d.]+pt" height="[\d.]+pt"', ' class="chart"', svg, count=1)
    for color in COLORS:
        svg = svg.replace(color.light, f"var(--{color.variable})")
    return re.sub(r'id="([a-z-]+)((?:__[a-z0-9-]+)+)"',
                  lambda match: 'class="' + " ".join([match[1], *(f"m-{slug}" for slug in match[2].split("__")[1:])]) + '"',
                  svg)


def level_column_html(axes: Axes, metric: Metric, index: int) -> str:
    """A hover column over one effort level: a crosshair, rings on its points, and a tooltip with every model's score."""
    width, height = axes.figure.bbox.size
    left, top = axes.transData.transform((index - 0.5, metric.y_range[1]))
    right, bottom = axes.transData.transform((index + 0.5, metric.y_range[0]))
    rows, rings = [], []
    present = [(model, metric.scores[model][index]) for model in metric.models if metric.scores[model][index] is not None]
    for model, score in sorted(present, key=lambda item: -item[1]):
        estimated = " <i>est.</i>" if (model, EFFORT_LEVELS[index]) in metric.estimated else ""
        rows.append(f'<span class="row m-{model.slug}" style="--series: var(--{model.color.variable})">'
                    f'<b>{metric.label(score)}</b>{html.escape(model.name)}{estimated}</span>')
        ring_top = 100 * (top - axes.transData.transform((index, score))[1]) / (top - bottom)
        rings.append(f'<span class="ring m-{model.slug}" style="top:{ring_top:.2f}%"></span>')
    side = "tip-left" if index >= len(EFFORT_LEVELS) - 2 else "tip-right"
    return (f'<span class="column" style="left:{100 * left / width:.2f}%;width:{100 * (right - left) / width:.2f}%;'
            f'top:{100 * (1 - top / height):.2f}%;height:{100 * (top - bottom) / height:.2f}%">'
            f'{"".join(rings)}<span class="tip {side}"><span class="level">{EFFORT_LEVELS[index]}</span>{"".join(rows)}</span></span>')


def cost_point_html(axes: Axes, metric: Metric, model: Model, index: int, cost: float, score: float) -> str:
    """A hover target on one cost-chart point: a ring and a tooltip with its level, score and cost."""
    width, height = axes.figure.bbox.size
    x, y = axes.transData.transform((cost, score))
    estimated = " <i>est.</i>" if (model, EFFORT_LEVELS[index]) in metric.estimated else ""
    side = "tip-left" if x / width > 0.6 else "tip-right"
    beaten = "".join(f'<span class="beaten m-{winner.slug}">beaten by {html.escape(winner.name)} '
                     f'{EFFORT_LEVELS[winner_index]}: {metric.label(winner_score)} at {cost_label(winner_cost)}</span>'
                     for winner, (_, winner_index, winner_cost, winner_score)
                     in beaters(metric)[(model, index, cost, score)].items())
    return (f'<span class="cost-point m-{model.slug}" style="left:{100 * x / width:.2f}%;top:{100 * (1 - y / height):.2f}%">'
            f'<span class="tip {side}"><span class="level">{EFFORT_LEVELS[index]}</span>'
            f'<span class="row" style="--series: var(--{model.color.variable})"><b>{metric.label(score)}</b>'
            f'{html.escape(model.name)}{estimated}</span><span class="cost">{cost_label(cost)} · {metric.cost_unit.split(",")[0]}</span>'
            f'{beaten}</span></span>')


# A chart without cost data shows its effort chart in both modes.
Mode = str


def plot_html(metric: Metric, layout: Layout, mode: Mode) -> str:
    """One layout's chart in one x-axis mode: the inline SVG plus its hover targets."""
    width, height = layout.figure_size
    bottom = AXES_BOTTOM + (COST_AXIS_LABEL_HEIGHT if mode == "cost" else 0)
    right = COST_AXES_RIGHT if mode == "cost" else AXES_RIGHT
    plt.rcParams["svg.hashsalt"] = f"{metric.name} {layout.name} {mode}"  # keeps SVG ids unique across the page
    figure = plt.figure(figsize=(width, height), dpi=72)
    axes = figure.add_axes((AXES_LEFT / width, bottom / height,
                            1 - (AXES_LEFT + right) / width, 1 - (AXES_TOP + bottom) / height))
    if mode == "cost":
        draw_cost_panel(axes, metric)
        hover = "".join(cost_point_html(axes, metric, model, index, cost, score) for model in metric.models
                        for index, cost, score in cost_points(metric, model))
        attributes = ""
    else:
        draw_panel(axes, metric)
        hover = "".join(level_column_html(axes, metric, index) for index in range(len(EFFORT_LEVELS))
                        if any(metric.scores[model][index] is not None for model in metric.models))
        box = axes.get_position()
        axes_percent = ",".join(f"{100 * value:.3f}" for value in (box.x0, 1 - box.y1, box.width, box.height))
        attributes = f' data-metric="{slugify(metric.name)}" data-axes="{axes_percent}"'
    svg = io.StringIO()
    figure.savefig(svg, format="svg", metadata={"Date": None})
    plt.close(figure)
    modes = mode if metric.costs else "effort cost"
    plot = f'<div class="plot {layout.name} {modes}"{attributes}>{inline_svg(svg.getvalue())}{hover}</div>'
    return layout_html(plot, layout)


def layout_html(plot: str, layout: Layout) -> str:
    """Keep inactive layouts inert, with a compact static chart when scripting is disabled.

    >>> layout_html("<svg/>", LAYOUTS[1])
    '<template data-layout="desktop"><svg/></template>'
    """
    fallback = f"<noscript>{plot}</noscript>" if layout is LAYOUTS[0] else ""
    return f'<template data-layout="{layout.name}">{plot}</template>{fallback}'


def panel_html(metric: Metric) -> str:
    modes = ["effort", "cost"] if metric.costs else ["effort"]
    note = "" if metric.costs else '<p class="no-cost">No cost data for this benchmark. Showing scores by effort level.</p>'
    return (f'<figure class="panel"><figcaption><h3>{html.escape(metric.name)}</h3>'
            f'<p>{html.escape(metric.unit_and_source)}</p>{note}</figcaption>'
            f'{"".join(plot_html(metric, layout, mode) for layout in LAYOUTS for mode in modes)}</figure>')


BAR_ROW_HEIGHT = 0.42
BAR_THICKNESS = 0.56  # of a row
BAR_AXES_LEFT = 0.95  # holds the model names
BAR_AXES_BOTTOM = 0.32


def draw_bars(axes: Axes, metric: ReportedMetric) -> None:
    """One horizontal bar per reported model, top to bottom in model order, labeled with its score and effort level."""
    rows = list(reversed(metric.models))
    for row, model in enumerate(rows):
        score, effort = metric.scores[model]
        axes.barh(row, score, height=BAR_THICKNESS, color=model.color.light, zorder=3, gid=element_id("bar", model))
        axes.annotate(model.name, (0, row), xytext=(-8, 0), textcoords="offset points", ha="right", va="center",
                      fontsize=LABEL_FONT_SIZE, color=TEXT_PRIMARY.light, annotation_clip=False, gid=element_id("name", model))
    axes.set_xlim(0, metric.x_max)
    axes.set_ylim(-0.6, len(rows) - 0.4)
    axes.set_yticks([])
    axes.xaxis.set_major_locator(matplotlib.ticker.MultipleLocator(metric.tick_step))
    axes.grid(axis="x", color=GRIDLINE.light, linewidth=0.7)
    axes.set_axisbelow(True)
    for side in ("top", "right", "bottom"):
        axes.spines[side].set_visible(False)
    axes.spines["left"].set_color(BASELINE.light)
    axes.tick_params(axis="both", length=0, labelsize=9, pad=5)
    axes.figure.canvas.draw()
    for row, model in enumerate(rows):
        score, effort = metric.scores[model]
        for part in annotate_parts(axes, (score, row), [(f"{score:.{metric.decimals}f}", POINT_LABEL_STYLE), (effort, DIM_LABEL_STYLE)],
                                   RIGHT, element_id("end", model)):
            part.set_annotation_clip(False)


def bar_plot_html(metric: ReportedMetric, layout: Layout) -> str:
    width = layout.figure_size[0]
    height = AXES_TOP + BAR_AXES_BOTTOM + BAR_ROW_HEIGHT * len(metric.models)
    plt.rcParams["svg.hashsalt"] = f"{metric.name} {layout.name}"
    figure = plt.figure(figsize=(width, height), dpi=72)
    axes = figure.add_axes((BAR_AXES_LEFT / width, BAR_AXES_BOTTOM / height,
                            1 - (BAR_AXES_LEFT + AXES_RIGHT) / width, 1 - (AXES_TOP + BAR_AXES_BOTTOM) / height))
    draw_bars(axes, metric)
    svg = io.StringIO()
    figure.savefig(svg, format="svg", metadata={"Date": None})
    plt.close(figure)
    modes = "effort" if metric.costs else "effort cost"
    return layout_html(f'<div class="plot {layout.name} {modes}">{inline_svg(svg.getvalue())}</div>', layout)


def reported_cost_metric(metric: ReportedMetric) -> Metric:
    """Shape reported scores at their known efforts for the existing cost-plot renderer.

    >>> reported_cost_metric(ReportedMetric("example", "%", {GPT_6_ASTRA: (80.0, "high")})).scores[GPT_6_ASTRA]
    [None, None, 80.0, None, None]
    """
    return Metric(metric.name, metric.unit_and_source,
                  {model: [score if level == effort else None for level in EFFORT_LEVELS]
                   for model, (score, effort) in metric.scores.items()},
                  (0, metric.x_max), metric.tick_step, decimals=metric.decimals)


def bar_panel_html(metric: ReportedMetric) -> str:
    missing = ", ".join(model.name for model in metric.missing)
    missing_note = f'<p class="missing">No reported score: {html.escape(missing)}</p>' if missing else ""
    plots = "".join(bar_plot_html(metric, layout) for layout in LAYOUTS)
    if metric.costs:
        plots += "".join(plot_html(reported_cost_metric(metric), layout, "cost") for layout in LAYOUTS)
    return (f'<figure class="panel"><figcaption><h3>{html.escape(metric.name)}</h3>'
            f'<p>{html.escape(metric.unit_and_source)}</p>{missing_note}</figcaption>'
            f'{plots}</figure>')


def table_rows() -> Iterator[tuple[str, Metric, Model]]:
    for category, metrics in SECTIONS:
        for metric in metrics:
            for model in metric.models:
                yield category, metric, model


def table_html() -> str:
    head = "".join(f"<th>{level}</th>" for level in EFFORT_LEVELS)
    rows = []
    for category, metric, model in table_rows():
        is_first = model is metric.models[0]
        cells = "".join(f"<td>{'' if score is None else metric.label(score)}</td>" for score in metric.scores[model])
        rows.append(f'<tr class="m-{model.slug}{" first" if is_first else ""}">'
                    f'<th scope="row">{html.escape(metric.name) if is_first else ""}</th>'
                    f'<td class="model">{html.escape(model.name)}</td>{cells}</tr>')
        if metric.costs and model in metric.costs:
            costs = "".join(f"<td>{'' if cost is None else cost_label(cost)}</td>" for cost in metric.costs[model])
            rows.append(f'<tr class="cost-row m-{model.slug}"><th scope="row"></th><td class="model">cost</td>{costs}</tr>')
    reported_rows = [f'<tr class="m-{model.slug}"><th scope="row">{html.escape(metric.name)}</th>'
                     f'<td class="model">{html.escape(model.name)}</td><td>{score:.{metric.decimals}f}</td>'
                     f'<td>{html.escape(effort)}</td><td>{html.escape(metric.unit_and_source)}</td>'
                     f'<td>{cost_label(next(cost for cost in metric.costs[model] if cost is not None)) if metric.costs and model in metric.costs else ""}</td></tr>'
                     for metrics in REPORTED.values() for metric in metrics
                     for model, (score, effort) in metric.scores.items()]
    return (f'<table><thead><tr><th>Metric</th><th>Model</th>{head}</tr></thead><tbody>{"".join(rows)}</tbody></table>'
            f'<h3>Reported benchmarks and rankings</h3><table><thead><tr><th>Metric</th><th>Model</th>'
            f'<th>Score</th><th>Effort</th><th>Unit and source</th><th>Reported cost</th></tr></thead><tbody>{"".join(reported_rows)}</tbody></table>')


def layout_css() -> str:
    """Show each layout's charts only inside its viewport range, in the x-axis mode the switch selects.

    >>> print(layout_css().splitlines()[0])
    @media (min-width: 0px) and (max-width: 699.98px) { body:has(#x-effort:checked) .plot.phone.effort, body:has(#x-cost:checked) .plot.phone.cost { display: block; } }
    """
    ends = [f" and (max-width: {following.min_viewport - 0.02}px)" for following in LAYOUTS[1:]] + [""]
    return "\n".join(f"@media (min-width: {layout.min_viewport}px){end} {{ "
                     + ", ".join(f"body:has(#x-{mode}:checked) .plot.{layout.name}.{mode}" for mode in ("effort", "cost"))
                     + " { display: block; } }"
                     for layout, end in zip(LAYOUTS, ends))


def toggle_css() -> str:
    """Rules that hide a model everywhere when its checkbox is off, show a meeting only when its two models alone are on,
    and, while a model is on, fade the cost points it beats and hide the frontier segments it blocks."""
    rules = []
    for model in MODELS:
        off = f"body:has(#show-{model.slug}:not(:checked))"
        rules.append(f"{off} .m-{model.slug} {{ display: none; }}")
        rules.append(f"{off} label[for=show-{model.slug}] {{ opacity: .45; text-decoration: line-through; }}")
        rules.append(f"body:has(#show-{model.slug}:checked) .marker.m-by-{model.slug} {{ opacity: .22; }}")
        rules.append(f"body:has(#show-{model.slug}:checked) .frontier.m-by-{model.slug} {{ display: none; }}")
        rules.append(f"body:has(#show-{model.slug}:focus-visible) label[for=show-{model.slug}] "
                     f"{{ outline: 2px solid var(--ink-2); outline-offset: 2px; }}")
    for pair in itertools.combinations(MODELS, 2):
        states = "".join(f":has(#show-{model.slug}:{'checked' if model in pair else 'not(:checked)'})" for model in MODELS)
        rules.append(f"body{states} :is(.meeting, .meeting-line)"
                     f"{''.join(f'.m-{model.slug}' for model in pair)} {{ display: inline; }}")
    return "\n".join(rules)


PAGE_TEMPLATE = Template("""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>$title</title>
<noscript><style>
body:has(#x-effort:checked) .plot.phone.effort, body:has(#x-cost:checked) .plot.phone.cost { display: block; }
</style></noscript>
<style>
:root { color-scheme: light; $light }
@media (prefers-color-scheme: dark) { :root { color-scheme: dark; $dark } }
* { box-sizing: border-box; }
body { margin: 0; background: var(--page); color: var(--ink-1);
  font: 15px/1.45 "Helvetica Neue", system-ui, -apple-system, sans-serif; -webkit-text-size-adjust: 100%; }
.shell { padding: 0 clamp(16px, 2vw, 40px); }
header { padding: 28px 0 12px; }
h1 { margin: 0 0 6px; font-size: 24px; letter-spacing: -0.01em; }
.subtitle { margin: 0; max-width: 72ch; color: var(--ink-2); }
.legend { position: sticky; top: 0; z-index: 10; background: var(--page); border-bottom: 1px solid var(--border); }
.legend .shell { display: flex; flex-wrap: wrap; gap: 6px 18px; padding-top: 10px; padding-bottom: 10px; }
.legend label { display: inline-flex; align-items: center; gap: 8px; cursor: pointer; user-select: none;
  -webkit-user-select: none; padding: 4px 0; font-weight: 500; }
.legend label.model::before { content: ""; width: 18px; height: 3px; border-radius: 2px; background: var(--series); }
.axis-switch { display: inline-flex; align-items: center; gap: 0; margin-left: auto; color: var(--ink-3); font-size: 13px; }
.axis-switch span { margin-right: 8px; }
.legend .axis-switch label { padding: 3px 12px; border: 1px solid var(--baseline); font-weight: 500; font-size: 13px; color: var(--ink-2); }
.axis-switch label:first-of-type { border-radius: 6px 0 0 6px; }
.axis-switch label:last-of-type { border-radius: 0 6px 6px 0; border-left: 0; }
body:has(#x-effort:checked) label[for=x-effort], body:has(#x-cost:checked) label[for=x-cost] {
  background: var(--ink-1); border-color: var(--ink-1); color: var(--surface); }
body:has(#x-effort:focus-visible) label[for=x-effort], body:has(#x-cost:focus-visible) label[for=x-cost] {
  outline: 2px solid var(--ink-2); outline-offset: 2px; }
.missing { color: var(--ink-3); }
.no-cost { display: none; }
body:has(#x-cost:checked) .no-cost { display: block; }
.cost-row { display: none; color: var(--ink-3); }
body:has(#x-cost:checked) .cost-row { display: table-row; }
.toggle { position: absolute; opacity: 0; pointer-events: none; }
h2 { margin: 32px 0 12px; font-size: 13px; letter-spacing: .08em; text-transform: uppercase; color: var(--ink-2); }
.grid { display: grid; grid-template-columns: 1fr; gap: 16px; }
@media (min-width: 960px) { .grid { grid-template-columns: 1fr 1fr; } }
.panel { margin: 0; padding: 16px 16px 8px; background: var(--surface); border: 1px solid var(--border); border-radius: 10px; }
figcaption h3 { margin: 0; font-size: 16px; }
figcaption p { margin: 2px 0 0; font-size: 13px; color: var(--ink-3); }
.plot { position: relative; display: none; }
@media (max-width: 699.98px) { .panel { padding: 12px 10px 6px; } }
$layouts
.chart { display: block; width: 100%; height: auto; overflow: visible; }
.meeting, .meeting-line { display: none; }
.column { position: absolute; }
.column::before { content: ""; position: absolute; left: 50%; top: 0; bottom: 0; border-left: 1px solid var(--baseline); opacity: 0; }
.ring { position: absolute; left: 50%; width: 16px; height: 16px; margin: -8px 0 0 -8px; border-radius: 50%;
  box-shadow: 0 0 0 1.5px var(--ink-1); opacity: 0; }
.tip { position: absolute; top: 0; z-index: 5; display: grid; gap: 2px; padding: 7px 10px; min-width: 150px;
  background: var(--surface); border: 1px solid var(--border); border-radius: 8px; box-shadow: 0 4px 14px rgba(0,0,0,.14);
  font-size: 12.5px; white-space: nowrap; color: var(--ink-2); pointer-events: none; }
/* Hidden tips take no space, so they cannot widen the page on phones. */
.column:not(:hover) .tip { display: none; }
.tip-right { left: calc(50% + 10px); }
.tip-left { right: calc(50% + 10px); }
.tip .level { font-weight: 600; color: var(--ink-3); text-transform: uppercase; font-size: 11px; letter-spacing: .06em; }
.tip .row { display: flex; align-items: center; gap: 8px; }
.tip .row::before { content: ""; width: 12px; height: 2.5px; border-radius: 2px; background: var(--series); flex: none; }
.tip b { min-width: 3.2em; color: var(--ink-1); font-variant-numeric: tabular-nums; }
.tip i { color: var(--ink-3); }
.cost-point { position: absolute; width: 24px; height: 24px; margin: -12px 0 0 -12px; border-radius: 50%; }
.cost-point::after { content: ""; position: absolute; inset: 4px; border-radius: 50%; box-shadow: 0 0 0 1.5px var(--ink-1); opacity: 0; }
.cost-point:not(:hover) .tip { display: none; }
.cost-point .tip { top: -8px; }
.cost-point .tip-right { left: calc(100% + 4px); }
.cost-point .tip-left { right: calc(100% + 4px); }
.tip .cost, .tip .beaten { color: var(--ink-3); }
.cost-point:hover { z-index: 4; }
.cost-point:hover::after { opacity: 1; }
.column:hover { z-index: 4; }
.column:hover::before, .column:hover .ring { opacity: 1; }
.footnote { margin: 12px 0 0; max-width: 90ch; font-size: 12.5px; color: var(--ink-3); }
details { margin: 32px 0 48px; }
summary { cursor: pointer; font-weight: 600; color: var(--ink-2); }
.table-wrap { overflow-x: auto; margin-top: 12px; }
table { border-collapse: collapse; font-size: 13px; font-variant-numeric: tabular-nums; }
th, td { padding: 4px 10px; text-align: right; white-space: nowrap; }
thead th { color: var(--ink-3); font-weight: 500; border-bottom: 1px solid var(--baseline); }
tbody th, td.model { text-align: left; }
tr.first > * { border-top: 1px solid var(--grid); }
.zoomable .plot[data-metric] { cursor: crosshair; user-select: none; -webkit-user-select: none; -webkit-touch-callout: none; }
.dragging .tip, .dragging .column::before, .dragging .ring { display: none; }
.selection { position: absolute; z-index: 6; pointer-events: none; border: 1px solid var(--ink-2);
  background: color-mix(in srgb, var(--ink-2) 10%, transparent); }
#zoom { width: 100vw; height: 100vh; max-width: none; max-height: none; margin: 0; padding: 24px 32px 16px; border: 0;
  background: var(--surface); color: var(--ink-1); }
#zoom[open] { display: flex; flex-direction: column; }
#zoom::backdrop { background: rgba(0, 0, 0, .45); }
@media (max-width: 699.98px) { #zoom { padding: 16px 16px 12px; } }
#zoom:focus { outline: none; }
.zoom-head { display: flex; justify-content: space-between; align-items: flex-start; gap: 16px; }
.zoom-head h3 { margin: 0; font-size: 22px; }
.zoom-head p { margin: 2px 0 0; color: var(--ink-3); }
.zoom-head button { font: 28px/1 system-ui, sans-serif; color: var(--ink-2); background: none; border: 0; cursor: pointer; padding: 0 4px; }
.zoom-legend { display: flex; flex-wrap: wrap; gap: 6px 18px; margin: 12px 0 4px; font-weight: 500; }
.zoom-legend span { display: inline-flex; align-items: center; gap: 8px; }
.zoom-legend span::before { content: ""; width: 18px; height: 3px; border-radius: 2px; background: var(--series); }
.zoom-plot { flex: 1; min-height: 0; }
.zoom-plot svg { display: block; width: 100%; height: 100%; overflow: visible; }
$toggles
</style>
</head>
<body>
$inputs
<header class="shell"><h1>$title</h1><p class="subtitle">$subtitle</p></header>
<nav class="legend" aria-label="Models"><div class="shell">$legend</div></nav>
<main class="shell">
$sections
<details><summary>Data table</summary><div class="table-wrap">$table</div></details>
</main>
<dialog id="zoom" aria-label="Zoomed chart" tabindex="-1">
<div class="zoom-head"><div><h3></h3><p class="zoom-unit"></p><p class="zoom-range"></p></div>
<form method="dialog"><button aria-label="Close">×</button></form></div>
<div class="zoom-legend"></div>
<div class="zoom-plot"></div>
</dialog>
<script type="application/json" id="chart-data">$data</script>
<script>
$script
</script>
</body>
</html>
""")


def page_html() -> str:
    sections = []
    for name, metrics in SECTIONS:
        panels = "".join(panel_html(metric) for metric in metrics) \
            + "".join(bar_panel_html(metric) for metric in REPORTED.get(name, []))
        sections.append(f'<section><h2>{name}</h2><div class="grid">{panels}</div>'
                        f'<p class="footnote">{html.escape(FOOTNOTES[name])}</p></section>')
    return PAGE_TEMPLATE.substitute(
        title=TITLE,
        subtitle=html.escape(SUBTITLE),
        light=" ".join(f"--{color.variable}: {color.light};" for color in COLORS),
        dark=" ".join(f"--{color.variable}: {color.dark};" for color in COLORS),
        toggles=toggle_css(),
        layouts=layout_css(),
        inputs="".join(f'<input type="checkbox" class="toggle" id="show-{model.slug}" checked>' for model in MODELS)
               + '<input type="radio" class="toggle" name="x-axis" id="x-effort" checked>'
               + '<input type="radio" class="toggle" name="x-axis" id="x-cost">',
        legend="".join(f'<label class="model" for="show-{model.slug}" style="--series: var(--{model.color.variable})">'
                       f'{html.escape(model.name)}</label>' for model in MODELS)
               + '<span class="axis-switch" role="group" aria-label="X axis"><span>X axis</span>'
                 '<label for="x-effort">Effort level</label><label for="x-cost">Cost</label></span>',
        sections="\n".join(sections),
        table=table_html(),
        data=json.dumps(chart_data(), ensure_ascii=False).replace("</", "<\\/"),
        script=(Path(__file__).parent / "zoom.js").read_text(),
    )


def chart_data() -> dict[str, object]:
    """The scores the zoom script redraws from, keyed by the same slugs the page uses."""
    return {
        "levels": EFFORT_LEVELS,
        "layouts": [{"name": layout.name, "minViewport": layout.min_viewport} for layout in LAYOUTS],
        "xLimits": X_LIMITS,
        "models": [{"slug": model.slug, "name": model.name, "color": model.color.variable} for model in MODELS],
        "metrics": {slugify(metric.name): {
            "name": metric.name,
            "unit": metric.unit_and_source,
            "yRange": metric.y_range,
            "decimals": metric.decimals,
            "scores": {model.slug: metric.scores[model] for model in metric.models},
            "estimated": [[model.slug, EFFORT_LEVELS.index(level)] for model, level in metric.estimated],
        } for _, metrics in SECTIONS for metric in metrics},
    }


def write_table(path: Path) -> None:
    with path.open("w", newline="") as file:
        writer = csv.writer(file)
        writer.writerow(["category", "metric", "unit_and_source", "model", "measure", *EFFORT_LEVELS,
                         "reported_score", "reported_effort"])
        for category, metric, model in table_rows():
            writer.writerow([category.lower(), metric.name, metric.unit_and_source, model.name, "score",
                             *("" if score is None else score for score in metric.scores[model]), "", ""])
            if metric.costs and model in metric.costs:
                writer.writerow([category.lower(), metric.name, metric.cost_unit, model.name, "cost_usd",
                                 *("" if cost is None else cost for cost in metric.costs[model]), "", ""])
        for category, metrics in REPORTED.items():
            for metric in metrics:
                for model, (score, effort) in metric.scores.items():
                    writer.writerow([category.lower(), metric.name, metric.unit_and_source, model.name, "score",
                                     *(score if effort == level else "" for level in EFFORT_LEVELS), score, effort])
                    if metric.costs and model in metric.costs:
                        writer.writerow([category.lower(), metric.name, metric.cost_unit, model.name, "cost_usd",
                                         *("" if cost is None else cost for cost in metric.costs[model]), "", effort])


def main() -> None:
    configure_fonts()
    OUTPUT_DIRECTORY.mkdir(exist_ok=True)
    (OUTPUT_DIRECTORY / "index.html").write_text(page_html())
    write_table(OUTPUT_DIRECTORY / "data.csv")


if __name__ == "__main__":
    main()
